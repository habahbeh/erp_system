# apps/purchases/views/contract_views.py
"""
Views for Purchase Contracts (Long-term contracts)
Complete CRUD operations + Approval Workflow + Status Management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Sum, Count, F, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, timedelta

from ..models import PurchaseContract, PurchaseContractItem
from ..forms import (
    PurchaseContractForm,
    PurchaseContractItemForm,
    PurchaseContractItemFormSet,
    ContractApprovalForm,
    ContractStatusChangeForm,
)
from apps.core.models import BusinessPartner, Item


class PurchaseContractListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """قائمة عقود الشراء"""
    model = PurchaseContract
    template_name = 'purchases/contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 50
    permission_required = 'purchases.view_purchasecontract'

    def dispatch(self, request, *args, **kwargs):
        """فحص وتحديث العقود المنتهية تلقائياً عند كل تحميل للصفحة"""
        # فحص العقود المنتهية وتحديث حالتها (النشطة والمعلقة)
        expired_contracts = PurchaseContract.objects.filter(
            company=request.current_company,
            status__in=['active', 'suspended'],
            end_date__lt=date.today()
        )
        for contract in expired_contracts:
            contract.status = 'expired'
            contract.save()

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = PurchaseContract.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'currency', 'approved_by', 'created_by'
        ).prefetch_related('items').order_by('-contract_date', '-number')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(supplier__name__icontains=search)
            )

        # فلترة حسب المورد
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(contract_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(contract_date__lte=date_to)

        # فلترة العقود المنتهية صلاحيتها
        expiring = self.request.GET.get('expiring')
        if expiring:
            days = int(expiring)
            expiry_date = date.today() + timedelta(days=days)
            queryset = queryset.filter(
                status='active',
                end_date__lte=expiry_date,
                end_date__gte=date.today()
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('عقود الشراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': ''},
        ]

        # الإحصائيات
        contracts = self.get_queryset()
        context['stats'] = {
            'total_count': contracts.count(),
            'draft_count': contracts.filter(status='draft').count(),
            'active_count': contracts.filter(status='active').count(),
            'suspended_count': contracts.filter(status='suspended').count(),
            'completed_count': contracts.filter(status='completed').count(),
            'expired_count': contracts.filter(status='expired').count(),
            'total_value': contracts.aggregate(
                total=Sum('contract_value')
            )['total'] or Decimal('0.000'),
            'total_ordered': contracts.aggregate(
                total=Sum('total_ordered')
            )['total'] or Decimal('0.000'),
            'expiring_soon': contracts.filter(
                status='active',
                end_date__lte=date.today() + timedelta(days=30),
                end_date__gte=date.today()
            ).count(),
        }

        # قائمة الموردين للفلترة
        context['suppliers'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both'],
            is_active=True
        ).order_by('name')

        # الصلاحيات
        context['can_add'] = self.request.user.has_perm('purchases.add_purchasecontract')
        context['can_edit'] = self.request.user.has_perm('purchases.change_purchasecontract')
        context['can_delete'] = self.request.user.has_perm('purchases.delete_purchasecontract')
        context['can_approve'] = self.request.user.has_perm('purchases.approve_purchasecontract')

        return context


class PurchaseContractDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل عقد الشراء"""
    model = PurchaseContract
    template_name = 'purchases/contracts/contract_detail.html'
    context_object_name = 'contract'
    permission_required = 'purchases.view_purchasecontract'

    def get_queryset(self):
        return PurchaseContract.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'currency', 'approved_by', 'created_by'
        ).prefetch_related('items__item', 'items__unit')

    def get_object(self, queryset=None):
        """فحص انتهاء العقد تلقائياً عند عرضه"""
        obj = super().get_object(queryset)
        # فحص انتهاء صلاحية العقد
        obj.check_expiry()
        # إعادة تحميل الكائن من قاعدة البيانات للحصول على الحالة المحدثة
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contract = self.object
        context['title'] = f'{_("عقد شراء")} {contract.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': contract.number, 'url': ''},
        ]

        # حساب نسبة الاستخدام
        context['utilization_percentage'] = contract.get_utilization_percentage()
        context['remaining_value'] = contract.get_remaining_value()

        # حساب الأيام المتبقية
        if contract.end_date:
            days_remaining = (contract.end_date - date.today()).days
            context['days_remaining'] = max(0, days_remaining)
            context['is_expiring_soon'] = 0 < days_remaining <= 30

        # الصلاحيات
        context['can_edit'] = (
            self.request.user.has_perm('purchases.change_purchasecontract') and
            contract.status == 'draft'
        )
        context['can_delete'] = (
            self.request.user.has_perm('purchases.delete_purchasecontract') and
            contract.status == 'draft'
        )
        context['can_approve'] = (
            self.request.user.has_perm('purchases.approve_purchasecontract') and
            contract.status == 'draft' and
            not contract.approved
        )
        context['can_activate'] = (
            self.request.user.has_perm('purchases.change_purchasecontract') and
            contract.status == 'draft' and
            contract.approved
        )
        context['can_suspend'] = (
            self.request.user.has_perm('purchases.change_purchasecontract') and
            contract.status == 'active'
        )
        context['can_terminate'] = (
            self.request.user.has_perm('purchases.change_purchasecontract') and
            contract.status in ['active', 'suspended']
        )

        return context


class PurchaseContractCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء عقد شراء جديد"""
    model = PurchaseContract
    form_class = PurchaseContractForm
    template_name = 'purchases/contracts/contract_form.html'
    permission_required = 'purchases.add_purchasecontract'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة عقد شراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': _('إضافة عقد'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseContractItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseContractItemFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # تعيين الشركة والفرع
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                _('تم إضافة عقد الشراء بنجاح: %(number)s') % {'number': self.object.number}
            )
            return redirect('purchases:contract_detail', pk=self.object.pk)
        else:
            messages.error(self.request, _('يوجد أخطاء في البيانات. يرجى التحقق والمحاولة مرة أخرى.'))
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseContractUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عقد الشراء"""
    model = PurchaseContract
    form_class = PurchaseContractForm
    template_name = 'purchases/contracts/contract_form.html'
    permission_required = 'purchases.change_purchasecontract'

    def get_queryset(self):
        return PurchaseContract.objects.filter(
            company=self.request.current_company,
            status='draft'  # يمكن تعديل العقود في حالة المسودة فقط
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تعديل عقد الشراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': self.object.number, 'url': reverse('purchases:contract_detail', kwargs={'pk': self.object.pk})},
            {'title': _('تعديل'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseContractItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseContractItemFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                _('تم تعديل عقد الشراء بنجاح: %(number)s') % {'number': self.object.number}
            )
            return redirect('purchases:contract_detail', pk=self.object.pk)
        else:
            messages.error(self.request, _('يوجد أخطاء في البيانات. يرجى التحقق والمحاولة مرة أخرى.'))
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseContractDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف عقد الشراء"""
    model = PurchaseContract
    template_name = 'purchases/contracts/contract_confirm_delete.html'
    success_url = reverse_lazy('purchases:contract_list')
    permission_required = 'purchases.delete_purchasecontract'

    def get_queryset(self):
        return PurchaseContract.objects.filter(
            company=self.request.current_company,
            status='draft'  # يمكن حذف العقود في حالة المسودة فقط
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('حذف عقد الشراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': self.object.number, 'url': reverse('purchases:contract_detail', kwargs={'pk': self.object.pk})},
            {'title': _('حذف'), 'url': ''},
        ]

        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        contract_number = self.object.number

        try:
            self.object.delete()
            messages.success(
                self.request,
                _('تم حذف عقد الشراء: %(number)s') % {'number': contract_number}
            )
        except Exception as e:
            messages.error(
                self.request,
                _('خطأ في حذف العقد: %(error)s') % {'error': str(e)}
            )
            return redirect('purchases:contract_detail', pk=self.object.pk)

        return redirect(self.success_url)


# ==================== Workflow Actions ====================

@login_required
@permission_required('purchases.approve_purchasecontract', raise_exception=True)
@transaction.atomic
def contract_approve(request, pk):
    """اعتماد عقد الشراء"""
    contract = get_object_or_404(
        PurchaseContract,
        pk=pk,
        company=request.current_company
    )

    if contract.status != 'draft':
        messages.error(request, _('يمكن اعتماد العقود في حالة المسودة فقط'))
        return redirect('purchases:contract_detail', pk=pk)

    if contract.approved:
        messages.warning(request, _('العقد معتمد مسبقاً'))
        return redirect('purchases:contract_detail', pk=pk)

    if request.method == 'POST':
        form = ContractApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data.get('notes', '')

            if action == 'approve':
                contract.approved = True
                contract.approved_by = request.user
                contract.approved_at = timezone.now()
                if notes:
                    contract.notes = f"{contract.notes}\n\nملاحظات الاعتماد: {notes}"
                contract.save()

                messages.success(request, _('تم اعتماد العقد بنجاح'))
            else:
                if notes:
                    contract.notes = f"{contract.notes}\n\nسبب الرفض: {notes}"
                    contract.save()
                messages.info(request, _('تم رفض العقد'))

            return redirect('purchases:contract_detail', pk=pk)
    else:
        form = ContractApprovalForm()

    return render(request, 'purchases/contracts/contract_approve.html', {
        'contract': contract,
        'form': form,
        'title': _('اعتماد عقد الشراء'),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': contract.number, 'url': reverse('purchases:contract_detail', kwargs={'pk': pk})},
            {'title': _('اعتماد'), 'url': ''},
        ],
    })


@login_required
@permission_required('purchases.change_purchasecontract', raise_exception=True)
@transaction.atomic
def contract_change_status(request, pk):
    """تغيير حالة العقد (تفعيل، تعليق، إنهاء)"""
    contract = get_object_or_404(
        PurchaseContract,
        pk=pk,
        company=request.current_company
    )

    if request.method == 'POST':
        form = ContractStatusChangeForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            reason = form.cleaned_data.get('reason', '')

            try:
                if action == 'activate':
                    contract.activate(user=request.user)
                    messages.success(request, _('تم تفعيل العقد بنجاح'))
                elif action == 'suspend':
                    contract.suspend(reason=reason, user=request.user)
                    messages.success(request, _('تم تعليق العقد بنجاح'))
                elif action == 'terminate':
                    contract.terminate(reason=reason, user=request.user)
                    messages.success(request, _('تم إنهاء العقد بنجاح'))

                return redirect('purchases:contract_detail', pk=pk)
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect('purchases:contract_detail', pk=pk)
    else:
        form = ContractStatusChangeForm()

    return render(request, 'purchases/contracts/contract_change_status.html', {
        'contract': contract,
        'form': form,
        'title': _('تغيير حالة العقد'),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('عقود الشراء'), 'url': reverse('purchases:contract_list')},
            {'title': contract.number, 'url': reverse('purchases:contract_detail', kwargs={'pk': pk})},
            {'title': _('تغيير الحالة'), 'url': ''},
        ],
    })


@login_required
@permission_required('purchases.view_purchasecontract', raise_exception=True)
def contract_check_expiry(request):
    """فحص العقود المنتهية صلاحيتها وتحديث حالتها"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    expired_count = 0
    contracts = PurchaseContract.objects.filter(
        company=request.current_company,
        status__in=['active', 'suspended'],
        end_date__lt=date.today()
    )

    for contract in contracts:
        if contract.check_expiry():
            expired_count += 1

    if expired_count == 0:
        message = _('لا توجد عقود منتهية الصلاحية تحتاج إلى تحديث')
    else:
        message = _('تم تحديث حالة %(count)s عقد منتهي الصلاحية') % {'count': expired_count}

    return JsonResponse({
        'success': True,
        'expired_count': expired_count,
        'message': message
    })


@login_required
@permission_required('purchases.add_purchasecontract', raise_exception=True)
@transaction.atomic
def contract_copy_or_renew(request, pk):
    """نسخ العقد أو تجديده"""
    original_contract = get_object_or_404(
        PurchaseContract,
        pk=pk,
        company=request.current_company
    )

    # حساب مدة العقد الأصلي بالأيام
    contract_duration_days = (original_contract.end_date - original_contract.start_date).days

    # إنشاء نسخة جديدة من العقد
    new_contract = PurchaseContract()

    # نسخ الحقول الأساسية
    new_contract.company = request.current_company
    new_contract.branch = request.current_branch
    new_contract.created_by = request.user

    # نسخ بيانات المورد والعملة
    new_contract.supplier = original_contract.supplier
    new_contract.currency = original_contract.currency

    # تحديث التواريخ
    new_contract.contract_date = date.today()
    new_contract.start_date = date.today()
    new_contract.end_date = date.today() + timedelta(days=contract_duration_days)

    # نسخ الشروط
    new_contract.payment_terms = original_contract.payment_terms
    new_contract.delivery_terms = original_contract.delivery_terms
    new_contract.quality_standards = original_contract.quality_standards
    new_contract.penalty_terms = original_contract.penalty_terms
    new_contract.termination_terms = original_contract.termination_terms
    new_contract.renewal_terms = original_contract.renewal_terms

    # إعداد الملاحظات
    new_contract.notes = f"نسخة من العقد: {original_contract.number}\nتاريخ النسخ: {date.today()}"
    if original_contract.notes:
        new_contract.notes += f"\n\nالملاحظات الأصلية:\n{original_contract.notes}"

    # الحالة والاعتماد (مسودة جديدة)
    new_contract.status = 'draft'
    new_contract.approved = False
    new_contract.approved_by = None
    new_contract.approved_at = None

    # القيم المالية (صفر للعقد الجديد)
    new_contract.total_ordered = Decimal('0.000')
    new_contract.total_received = Decimal('0.000')
    new_contract.total_invoiced = Decimal('0.000')
    new_contract.contract_value = Decimal('0.000')  # سيتم حسابه تلقائياً عند حفظ الأصناف

    # حفظ العقد الجديد لتوليد الرقم
    new_contract.save()

    # نسخ أصناف العقد
    for original_item in original_contract.items.all():
        new_item = PurchaseContractItem()
        new_item.contract = new_contract
        new_item.item = original_item.item
        new_item.item_description = original_item.item_description
        new_item.specifications = original_item.specifications
        new_item.unit = original_item.unit
        new_item.contracted_quantity = original_item.contracted_quantity
        new_item.unit_price = original_item.unit_price
        new_item.min_order_quantity = original_item.min_order_quantity
        new_item.max_order_quantity = original_item.max_order_quantity
        new_item.discount_percentage = original_item.discount_percentage
        new_item.notes = original_item.notes

        # القيم التنفيذية (صفر للعقد الجديد)
        new_item.ordered_quantity = Decimal('0.000')
        new_item.received_quantity = Decimal('0.000')

        new_item.save()

    messages.success(
        request,
        _('تم نسخ العقد بنجاح. العقد الجديد: %(number)s') % {'number': new_contract.number}
    )

    return redirect('purchases:contract_detail', pk=new_contract.pk)

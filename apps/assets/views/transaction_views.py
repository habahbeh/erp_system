# apps/assets/views/transaction_views.py
"""
Views معاملات الأصول (شراء، بيع، استبعاد، تحويل)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.db.models import Q, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
import json
from datetime import date, timedelta
from decimal import Decimal

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import AssetTransaction, AssetTransfer, Asset
from apps.core.models import BusinessPartner


class AssetTransactionListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة معاملات الأصول"""

    model = AssetTransaction
    template_name = 'assets/transaction/transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'assets.view_assettransaction'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetTransaction.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'business_partner',
            'created_by', 'approved_by', 'journal_entry'
        )

        # الفلترة
        transaction_type = self.request.GET.get('transaction_type')
        status = self.request.GET.get('status')
        asset = self.request.GET.get('asset')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        if status:
            queryset = queryset.filter(status=status)

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search) |
                Q(asset__asset_number__icontains=search) |
                Q(asset__name__icontains=search) |
                Q(reference_number__icontains=search)
            )

        return queryset.order_by('-transaction_date', '-transaction_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title': _('معاملات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assettransaction'),
            'can_edit': self.request.user.has_perm('assets.change_assettransaction'),
            'can_delete': self.request.user.has_perm('assets.delete_assettransaction'),
            'transaction_types': AssetTransaction.TRANSACTION_TYPES,
            'status_choices': AssetTransaction.STATUS_CHOICES,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('معاملات الأصول'), 'url': ''},
            ]
        })
        return context


class AssetTransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء معاملة أصل"""

    model = AssetTransaction
    template_name = 'assets/transaction/transaction_form.html'
    permission_required = 'assets.add_assettransaction'
    fields = [
        'transaction_date', 'transaction_type', 'asset',
        'amount', 'sale_price', 'payment_method',
        'business_partner', 'reference_number',
        'description', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        form.fields['business_partner'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company
        )

        form.fields['transaction_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء المعاملة {self.object.transaction_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:transaction_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة معاملة أصل'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('معاملات الأصول'), 'url': reverse('assets:transaction_list')},
                {'title': _('إضافة معاملة'), 'url': ''},
            ]
        })
        return context


class AssetTransactionDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل معاملة الأصل"""

    model = AssetTransaction
    template_name = 'assets/transaction/transaction_detail.html'
    context_object_name = 'transaction'
    permission_required = 'assets.view_assettransaction'

    def get_queryset(self):
        return AssetTransaction.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'business_partner',
            'created_by', 'approved_by', 'journal_entry'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'المعاملة {self.object.transaction_number}',
            'can_edit': self.request.user.has_perm('assets.change_assettransaction') and self.object.status == 'draft',
            'can_delete': self.request.user.has_perm(
                'assets.delete_assettransaction') and self.object.status == 'draft',
            'can_approve': self.request.user.has_perm(
                'assets.change_assettransaction') and self.object.status == 'draft',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('معاملات الأصول'), 'url': reverse('assets:transaction_list')},
                {'title': self.object.transaction_number, 'url': ''},
            ]
        })
        return context


class AssetTransactionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل معاملة أصل"""

    model = AssetTransaction
    template_name = 'assets/transaction/transaction_form.html'
    permission_required = 'assets.change_assettransaction'
    fields = [
        'transaction_date', 'transaction_type', 'asset',
        'amount', 'sale_price', 'payment_method',
        'business_partner', 'reference_number',
        'description', 'notes'
    ]

    def get_queryset(self):
        return AssetTransaction.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company
        )

        form.fields['business_partner'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث المعاملة {self.object.transaction_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:transaction_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل المعاملة {self.object.transaction_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('معاملات الأصول'), 'url': reverse('assets:transaction_list')},
                {'title': self.object.transaction_number,
                 'url': reverse('assets:transaction_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class AssetTransactionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف معاملة أصل"""

    model = AssetTransaction
    template_name = 'assets/transaction/transaction_confirm_delete.html'
    permission_required = 'assets.delete_assettransaction'
    success_url = reverse_lazy('assets:transaction_list')

    def get_queryset(self):
        return AssetTransaction.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status != 'draft':
            messages.error(request, _('لا يمكن حذف معاملة معتمدة'))
            return redirect('assets:transaction_detail', pk=self.object.pk)

        messages.success(request, f'تم حذف المعاملة {self.object.transaction_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Specific Transaction Types ====================

class SellAssetView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """بيع أصل"""

    template_name = 'assets/transaction/sell_asset.html'
    permission_required = 'assets.can_sell_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asset_id = self.request.GET.get('asset_id') or self.kwargs.get('asset_id')
        asset = None

        if asset_id:
            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=self.request.current_company,
                status='active'
            )

        context.update({
            'title': _('بيع أصل'),
            'asset': asset,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('بيع أصل'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            asset_id = request.POST.get('asset_id')
            sale_price = Decimal(request.POST.get('sale_price', 0))
            buyer_id = request.POST.get('buyer_id')

            if not asset_id or not sale_price or not buyer_id:
                messages.error(request, 'يجب إدخال جميع البيانات المطلوبة')
                return redirect('assets:sell_asset')

            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=request.current_company
            )

            buyer = get_object_or_404(
                BusinessPartner,
                pk=buyer_id,
                company=request.current_company
            )

            # بيع الأصل
            transaction_obj = asset.sell(
                sale_price=sale_price,
                buyer=buyer,
                user=request.user
            )

            messages.success(
                request,
                f'تم بيع الأصل {asset.asset_number} بنجاح بمبلغ {sale_price:,.2f}'
            )

            return redirect('assets:transaction_detail', pk=transaction_obj.pk)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('assets:sell_asset')

        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('assets:asset_list')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'خطأ في بيع الأصل: {str(e)}')
            return redirect('assets:sell_asset')


class DisposeAssetView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """استبعاد أصل"""

    template_name = 'assets/transaction/dispose_asset.html'
    permission_required = 'assets.can_dispose_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asset_id = self.request.GET.get('asset_id') or self.kwargs.get('asset_id')
        asset = None

        if asset_id:
            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=self.request.current_company,
                status='active'
            )

        context.update({
            'title': _('استبعاد أصل'),
            'asset': asset,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('استبعاد أصل'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            asset_id = request.POST.get('asset_id')
            reason = request.POST.get('reason', '')

            if not asset_id or not reason:
                messages.error(request, 'يجب تحديد الأصل وسبب الاستبعاد')
                return redirect('assets:dispose_asset')

            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=request.current_company
            )

            # استبعاد الأصل
            transaction_obj = asset.dispose(
                reason=reason,
                user=request.user
            )

            messages.success(
                request,
                f'تم استبعاد الأصل {asset.asset_number} بنجاح'
            )

            return redirect('assets:transaction_detail', pk=transaction_obj.pk)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('assets:dispose_asset')

        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('assets:asset_list')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'خطأ في استبعاد الأصل: {str(e)}')
            return redirect('assets:dispose_asset')


class RevalueAssetView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """إعادة تقييم أصل"""

    template_name = 'assets/transaction/revalue_asset.html'
    permission_required = 'assets.can_revalue_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asset_id = self.request.GET.get('asset_id') or self.kwargs.get('asset_id')
        asset = None

        if asset_id:
            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=self.request.current_company
            )

        context.update({
            'title': _('إعادة تقييم أصل'),
            'asset': asset,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('إعادة تقييم أصل'), 'url': ''},
            ]
        })
        return context


# ==================== Asset Transfers ====================

class AssetTransferListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة تحويلات الأصول"""

    model = AssetTransfer
    template_name = 'assets/transfer/transfer_list.html'
    context_object_name = 'transfers'
    permission_required = 'assets.view_assettransfer'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetTransfer.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'from_branch', 'to_branch',
            'from_cost_center', 'to_cost_center',
            'requested_by', 'approved_by'
        )

        # الفلترة
        status = self.request.GET.get('status')
        asset = self.request.GET.get('asset')
        from_branch = self.request.GET.get('from_branch')
        to_branch = self.request.GET.get('to_branch')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if from_branch:
            queryset = queryset.filter(from_branch_id=from_branch)

        if to_branch:
            queryset = queryset.filter(to_branch_id=to_branch)

        if search:
            queryset = queryset.filter(
                Q(transfer_number__icontains=search) |
                Q(asset__asset_number__icontains=search) |
                Q(asset__name__icontains=search)
            )

        return queryset.order_by('-transfer_date', '-transfer_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title': _('تحويلات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assettransfer'),
            'can_edit': self.request.user.has_perm('assets.change_assettransfer'),
            'can_approve': self.request.user.has_perm('assets.can_transfer_asset'),
            'status_choices': AssetTransfer.STATUS_CHOICES,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تحويلات الأصول'), 'url': ''},
            ]
        })
        return context


class AssetTransferCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء تحويل أصل"""

    model = AssetTransfer
    template_name = 'assets/transfer/transfer_form.html'
    permission_required = 'assets.add_assettransfer'
    fields = [
        'transfer_date', 'asset',
        'from_branch', 'from_cost_center', 'from_employee',
        'to_branch', 'to_cost_center', 'to_employee',
        'reason', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        form.fields['transfer_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.requested_by = self.request.user
        form.instance.status = 'pending'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء طلب التحويل {self.object.transfer_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:transfer_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('طلب تحويل أصل'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تحويلات الأصول'), 'url': reverse('assets:transfer_list')},
                {'title': _('طلب تحويل'), 'url': ''},
            ]
        })
        return context


class AssetTransferDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل تحويل الأصل"""

    model = AssetTransfer
    template_name = 'assets/transfer/transfer_detail.html'
    context_object_name = 'transfer'
    permission_required = 'assets.view_assettransfer'

    def get_queryset(self):
        return AssetTransfer.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'from_branch', 'to_branch',
            'from_cost_center', 'to_cost_center',
            'from_employee', 'to_employee',
            'requested_by', 'approved_by', 'delivered_by', 'received_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'التحويل {self.object.transfer_number}',
            'can_edit': self.request.user.has_perm('assets.change_assettransfer') and self.object.status == 'pending',
            'can_approve': self.request.user.has_perm('assets.can_transfer_asset') and self.object.status == 'pending',
            'can_complete': self.request.user.has_perm(
                'assets.can_transfer_asset') and self.object.status == 'approved',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تحويلات الأصول'), 'url': reverse('assets:transfer_list')},
                {'title': self.object.transfer_number, 'url': ''},
            ]
        })
        return context


class AssetTransferUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل تحويل أصل"""

    model = AssetTransfer
    template_name = 'assets/transfer/transfer_form.html'
    permission_required = 'assets.change_assettransfer'
    fields = [
        'transfer_date', 'asset',
        'from_branch', 'from_cost_center', 'from_employee',
        'to_branch', 'to_cost_center', 'to_employee',
        'reason', 'notes'
    ]

    def get_queryset(self):
        return AssetTransfer.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث طلب التحويل {self.object.transfer_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:transfer_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل التحويل {self.object.transfer_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تحويلات الأصول'), 'url': reverse('assets:transfer_list')},
                {'title': self.object.transfer_number, 'url': reverse('assets:transfer_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.can_transfer_asset')
@require_http_methods(["POST"])
def approve_transfer(request, pk):
    """اعتماد تحويل أصل"""

    try:
        transfer = get_object_or_404(
            AssetTransfer,
            pk=pk,
            company=request.current_company,
            status='pending'
        )

        from django.utils import timezone

        transfer.status = 'approved'
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.save()

        return JsonResponse({
            'success': True,
            'message': f'تم اعتماد التحويل {transfer.transfer_number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في اعتماد التحويل: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_transfer_asset')
@require_http_methods(["POST"])
def complete_transfer(request, pk):
    """إكمال تحويل أصل"""

    try:
        transfer = get_object_or_404(
            AssetTransfer,
            pk=pk,
            company=request.current_company,
            status='approved'
        )

        from django.utils import timezone

        with transaction.atomic():
            # تحديث التحويل
            transfer.status = 'completed'
            transfer.received_by = request.user
            transfer.received_at = timezone.now()
            transfer.save()

            # تحديث الأصل
            asset = transfer.asset
            asset.branch = transfer.to_branch
            asset.cost_center = transfer.to_cost_center
            asset.responsible_employee = transfer.to_employee
            asset.save()

        return JsonResponse({
            'success': True,
            'message': f'تم إكمال التحويل {transfer.transfer_number} بنجاح'
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إكمال التحويل: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_assettransaction')
@require_http_methods(["GET"])
def transaction_datatable_ajax(request):
    """Ajax endpoint لجدول المعاملات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = AssetTransaction.objects.filter(
            company=request.current_company
        ).select_related('asset', 'business_partner', 'journal_entry')

        if search_value:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-transaction_date', '-transaction_number')

        total_records = AssetTransaction.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_view = request.user.has_perm('assets.view_assettransaction')

        for trans in queryset:
            status_map = {
                'draft': '<span class="badge bg-secondary">مسودة</span>',
                'approved': '<span class="badge bg-info">معتمد</span>',
                'completed': '<span class="badge bg-success">مكتمل</span>',
                'cancelled': '<span class="badge bg-danger">ملغي</span>',
            }
            status_badge = status_map.get(trans.status, trans.status)

            type_display = dict(AssetTransaction.TRANSACTION_TYPES).get(trans.transaction_type, trans.transaction_type)

            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('assets:transaction_detail', args=[trans.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                trans.transaction_number,
                trans.transaction_date.strftime('%Y-%m-%d'),
                type_display,
                trans.asset.asset_number,
                trans.asset.name,
                f"{trans.amount:,.2f}",
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_assettransfer')
@require_http_methods(["GET"])
def transfer_datatable_ajax(request):
    """Ajax endpoint لجدول التحويلات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = AssetTransfer.objects.filter(
            company=request.current_company
        ).select_related('asset', 'from_branch', 'to_branch')

        if search_value:
            queryset = queryset.filter(
                Q(transfer_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-transfer_date', '-transfer_number')

        total_records = AssetTransfer.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for transfer in queryset:
            status_map = {
                'pending': '<span class="badge bg-warning">معلق</span>',
                'approved': '<span class="badge bg-info">معتمد</span>',
                'completed': '<span class="badge bg-success">مكتمل</span>',
                'rejected': '<span class="badge bg-danger">مرفوض</span>',
                'cancelled': '<span class="badge bg-secondary">ملغي</span>',
            }
            status_badge = status_map.get(transfer.status, transfer.status)

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:transfer_detail', args=[transfer.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                transfer.transfer_number,
                transfer.transfer_date.strftime('%Y-%m-%d'),
                transfer.asset.asset_number,
                f"{transfer.from_branch.name} → {transfer.to_branch.name}",
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.change_assettransaction')
@require_http_methods(["POST"])
def post_transaction(request, pk):
    """ترحيل معاملة أصل"""

    try:
        trans = get_object_or_404(
            AssetTransaction,
            pk=pk,
            company=request.current_company,
            status='approved'
        )

        with transaction.atomic():
            trans.status = 'completed'
            trans.save()

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل المعاملة {trans.transaction_number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل المعاملة: {str(e)}'
        }, status=500)
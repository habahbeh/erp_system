# apps/assets/views/transaction_views.py
"""
Transaction Views - العمليات على الأصول والتحويلات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, FormView
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from decimal import Decimal
import datetime

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import AssetTransaction, AssetTransfer, Asset, AssetValuation
from ..forms import (
    AssetTransactionForm, AssetPurchaseForm, AssetSaleForm,
    AssetDisposalForm, AssetTransferForm, AssetRevaluationForm,
    AssetCapitalImprovementForm, AssetDonationForm
)


# =============================================================================
# Transaction List View
# =============================================================================

class AssetTransactionListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة العمليات على الأصول"""

    template_name = 'assets/transactions/transaction_list.html'
    permission_required = 'assets.view_assettransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        company = self.request.user.company
        stats = AssetTransaction.objects.filter(company=company).aggregate(
            total=Count('id'),
            purchases=Count('id', filter=Q(transaction_type='purchase')),
            sales=Count('id', filter=Q(transaction_type='sale')),
            disposals=Count('id', filter=Q(transaction_type='disposal')),
            total_amount=Sum('amount')
        )

        context.update({
            'title': _('العمليات على الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assettransaction'),
            'can_purchase': self.request.user.has_perm('assets.can_purchase_asset'),
            'can_sell': self.request.user.has_perm('assets.can_sell_asset'),
            'can_dispose': self.request.user.has_perm('assets.can_dispose_asset'),
            'stats': stats,
            'transaction_types': AssetTransaction.TRANSACTION_TYPES,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Purchase (استخدام Model method)
# =============================================================================

class AssetPurchaseView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """شراء أصل جديد"""

    model = AssetTransaction
    form_class = AssetPurchaseForm
    template_name = 'assets/transactions/purchase_form.html'
    permission_required = 'assets.can_purchase_asset'
    success_url = reverse_lazy('assets:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.transaction_type = 'purchase'
        form.instance.status = 'approved'

        response = super().form_valid(form)

        # توليد القيد المحاسبي
        try:
            from ..utils import generate_asset_purchase_journal_entry
            journal_entry = generate_asset_purchase_journal_entry(
                self.object,
                self.request.user.company,
                self.request.user
            )
            self.object.journal_entry = journal_entry
            self.object.save()

            messages.success(
                self.request,
                f'تم تسجيل عملية الشراء بنجاح - القيد رقم: {journal_entry.number}'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'تم تسجيل العملية ولكن فشل توليد القيد المحاسبي: {str(e)}'
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('شراء أصل ثابت'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('شراء أصل'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Sale (استخدام Model method)
# =============================================================================

class AssetSaleView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """بيع أصل - استخدام Asset.sell() method"""

    form_class = AssetSaleForm
    template_name = 'assets/transactions/sale_form.html'
    permission_required = 'assets.can_sell_asset'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        asset = form.cleaned_data['asset']
        sale_price = form.cleaned_data['sale_price']
        buyer = form.cleaned_data.get('buyer')

        # التحقق من الصلاحية
        if not asset.can_user_sell(self.request.user):
            raise PermissionDenied(_('ليس لديك صلاحية بيع هذا الأصل'))

        try:
            # استخدام Model method
            transaction = asset.sell(
                sale_price=sale_price,
                buyer=buyer,
                user=self.request.user
            )

            gain_loss_text = (
                f'ربح: {transaction.gain_loss:,.3f}'
                if transaction.gain_loss > 0
                else f'خسارة: {abs(transaction.gain_loss):,.3f}'
            )

            messages.success(
                self.request,
                f'تم تسجيل عملية البيع بنجاح - {gain_loss_text} - القيد رقم: {transaction.journal_entry.number}'
            )

            return redirect('assets:asset_detail', pk=asset.pk)

        except Exception as e:
            messages.error(self.request, f'خطأ في عملية البيع: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('بيع أصل ثابت'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('بيع أصل'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Disposal (استخدام Model method)
# =============================================================================

class AssetDisposalView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """استبعاد/إتلاف أصل - استخدام Asset.dispose() method"""

    form_class = AssetDisposalForm
    template_name = 'assets/transactions/disposal_form.html'
    permission_required = 'assets.can_dispose_asset'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        asset = form.cleaned_data['asset']
        reason = form.cleaned_data['description']

        # التحقق من الصلاحية
        if not asset.can_user_dispose(self.request.user):
            raise PermissionDenied(_('ليس لديك صلاحية استبعاد هذا الأصل'))

        try:
            # استخدام Model method
            transaction = asset.dispose(
                reason=reason,
                user=self.request.user
            )

            messages.success(
                self.request,
                f'تم استبعاد الأصل {asset.asset_number} بنجاح - القيد رقم: {transaction.journal_entry.number}'
            )

            return redirect('assets:asset_detail', pk=asset.pk)

        except Exception as e:
            messages.error(self.request, f'خطأ في عملية الاستبعاد: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('استبعاد/إتلاف أصل'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('استبعاد أصل'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Revaluation (إعادة تقييم)
# =============================================================================

class AssetRevaluationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إعادة تقييم أصل"""

    model = AssetTransaction
    form_class = AssetRevaluationForm
    template_name = 'assets/transactions/revaluation_form.html'
    permission_required = 'assets.can_revalue_asset'
    success_url = reverse_lazy('assets:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        asset = form.cleaned_data['asset']
        new_value = form.cleaned_data['amount']

        # التحقق من الصلاحية
        if not asset.can_user_revalue(self.request.user):
            raise PermissionDenied(_('ليس لديك صلاحية إعادة تقييم هذا الأصل'))

        # إنشاء سجل التقييم
        valuation = AssetValuation.objects.create(
            asset=asset,
            valuation_date=form.cleaned_data['transaction_date'],
            old_value=asset.book_value,
            new_value=new_value,
            reason=form.cleaned_data['description'],
            valuator_name=form.cleaned_data.get('valuator_name', ''),
            created_by=self.request.user,
            is_approved=False  # يحتاج موافقة
        )

        # إنشاء Transaction
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.transaction_type = 'revaluation'
        form.instance.status = 'draft'  # مسودة حتى الموافقة

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم إنشاء طلب إعادة تقييم للأصل {asset.asset_number} - يحتاج موافقة'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إعادة تقييم أصل'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('إعادة تقييم'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Capital Improvement (تحسينات رأسمالية)
# =============================================================================

class AssetCapitalImprovementView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """تحسينات رأسمالية على أصل"""

    model = AssetTransaction
    form_class = AssetCapitalImprovementForm
    template_name = 'assets/transactions/capital_improvement_form.html'
    permission_required = 'assets.change_asset'
    success_url = reverse_lazy('assets:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        asset = form.cleaned_data['asset']
        improvement_cost = form.cleaned_data['amount']

        # إنشاء Transaction
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.transaction_type = 'capital_improvement'
        form.instance.status = 'approved'

        response = super().form_valid(form)

        # زيادة قيمة الأصل
        asset.original_cost += improvement_cost
        asset.book_value += improvement_cost
        asset.save()

        # توليد القيد المحاسبي
        try:
            from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod

            fiscal_year = FiscalYear.objects.get(
                company=self.request.user.company,
                start_date__lte=form.instance.transaction_date,
                end_date__gte=form.instance.transaction_date,
                is_closed=False
            )

            period = AccountingPeriod.objects.filter(
                fiscal_year=fiscal_year,
                start_date__lte=form.instance.transaction_date,
                end_date__gte=form.instance.transaction_date,
                is_closed=False
            ).first()

            journal_entry = JournalEntry.objects.create(
                company=self.request.user.company,
                branch=self.request.user.branch,
                fiscal_year=fiscal_year,
                period=period,
                entry_date=form.instance.transaction_date,
                entry_type='auto',
                description=f"تحسينات رأسمالية - {asset.name}",
                reference=self.object.transaction_number,
                created_by=self.request.user
            )

            # من حـ/ الأصل
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=1,
                account=asset.category.asset_account,
                description=f"تحسينات رأسمالية - {asset.name}",
                debit_amount=improvement_cost,
                credit_amount=0,
                currency=self.request.user.company.base_currency
            )

            # إلى حـ/ البنك أو النقدية
            from apps.accounting.models import Account
            cash_account = Account.objects.get(company=self.request.user.company, code='110100')

            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=2,
                account=cash_account,
                description=f"دفع تحسينات - {asset.name}",
                debit_amount=0,
                credit_amount=improvement_cost,
                currency=self.request.user.company.base_currency
            )

            journal_entry.post(user=self.request.user)

            self.object.journal_entry = journal_entry
            self.object.save()

            messages.success(
                self.request,
                f'تم تسجيل التحسينات الرأسمالية بنجاح - القيد رقم: {journal_entry.number}'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'تم تسجيل العملية ولكن فشل توليد القيد المحاسبي: {str(e)}'
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تحسينات رأسمالية'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('تحسينات رأسمالية'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Donations (الهبات)
# =============================================================================

class AssetDonationInView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """هبة مستلمة"""

    model = AssetTransaction
    form_class = AssetDonationForm
    template_name = 'assets/transactions/donation_form.html'
    permission_required = 'assets.add_assettransaction'
    success_url = reverse_lazy('assets:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['donation_type'] = 'in'
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.transaction_type = 'donation_in'
        form.instance.status = 'approved'

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم تسجيل الهبة المستلمة بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('هبة مستلمة'),
            'donation_type': 'in',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('هبة مستلمة'), 'url': ''}
            ],
        })
        return context


class AssetDonationOutView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """هبة معطاة"""

    model = AssetTransaction
    form_class = AssetDonationForm
    template_name = 'assets/transactions/donation_form.html'
    permission_required = 'assets.can_dispose_asset'
    success_url = reverse_lazy('assets:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['donation_type'] = 'out'
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        asset = form.cleaned_data['asset']

        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.transaction_type = 'donation_out'
        form.instance.status = 'approved'

        response = super().form_valid(form)

        # تحديث حالة الأصل
        asset.status = 'disposed'
        asset.save()

        messages.success(
            self.request,
            f'تم تسجيل الهبة المعطاة بنجاح - الأصل {asset.asset_number}'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('هبة معطاة'),
            'donation_type': 'out',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('العمليات'), 'url': reverse('assets:transaction_list')},
                {'title': _('هبة معطاة'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Asset Transfer CRUD
# =============================================================================

class AssetTransferListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة تحويلات الأصول"""

    template_name = 'assets/transfers/transfer_list.html'
    permission_required = 'assets.view_assettransfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        stats = AssetTransfer.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            completed=Count('id', filter=Q(status='completed'))
        )

        context.update({
            'title': _('تحويلات الأصول'),
            'can_add': self.request.user.has_perm('assets.can_transfer_asset'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('التحويلات'), 'url': ''}
            ],
        })
        return context


class AssetTransferCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء تحويل أصل"""

    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfers/transfer_form.html'
    permission_required = 'assets.can_transfer_asset'
    success_url = reverse_lazy('assets:transfer_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.requested_by = self.request.user
        form.instance.status = 'pending'  # يحتاج موافقة

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم إنشاء طلب التحويل {self.object.transfer_number} - في انتظار الموافقة'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تحويل أصل'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('التحويلات'), 'url': reverse('assets:transfer_list')},
                {'title': _('تحويل جديد'), 'url': ''}
            ],
        })
        return context


class AssetTransferDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل تحويل أصل"""

    model = AssetTransfer
    template_name = 'assets/transfers/transfer_detail.html'
    permission_required = 'assets.view_assettransfer'
    context_object_name = 'transfer'

    def get_queryset(self):
        return AssetTransfer.objects.filter(
            company=self.request.user.company
        ).select_related(
            'asset', 'from_branch', 'to_branch',
            'from_cost_center', 'to_cost_center',
            'from_employee', 'to_employee',
            'requested_by', 'approved_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = self.object

        context.update({
            'title': f'تحويل الأصل: {transfer.transfer_number}',
            'can_edit': self.request.user.has_perm('assets.change_assettransfer') and transfer.status == 'pending',
            'can_approve': self.request.user.has_perm('assets.can_transfer_asset') and transfer.status == 'pending',
            'can_delete': self.request.user.has_perm('assets.delete_assettransfer') and transfer.status == 'pending',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('التحويلات'), 'url': reverse('assets:transfer_list')},
                {'title': transfer.transfer_number, 'url': ''}
            ],
        })
        return context


class AssetTransferUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل تحويل أصل"""

    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfers/transfer_form.html'
    permission_required = 'assets.change_assettransfer'

    def get_queryset(self):
        return AssetTransfer.objects.filter(
            company=self.request.user.company,
            status='pending'  # فقط المعلقة
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث التحويل {self.object.transfer_number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('assets:transfer_detail', kwargs={'pk': self.object.pk})


class AssetTransferDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف تحويل أصل"""

    model = AssetTransfer
    template_name = 'assets/transfers/transfer_confirm_delete.html'
    permission_required = 'assets.delete_assettransfer'
    success_url = reverse_lazy('assets:transfer_list')

    def get_queryset(self):
        return AssetTransfer.objects.filter(
            company=self.request.user.company,
            status='pending'
        )

    def delete(self, request, *args, **kwargs):
        transfer = self.get_object()
        transfer_number = transfer.transfer_number

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'تم حذف التحويل {transfer_number} بنجاح')
        return response


# =============================================================================
# Transfer Actions
# =============================================================================

@login_required
@permission_required_with_message('assets.can_transfer_asset')
@require_http_methods(["POST"])
def AssetTransferApproveView(request, pk):
    """الموافقة على تحويل أصل"""

    transfer = get_object_or_404(
        AssetTransfer,
        pk=pk,
        company=request.user.company,
        status='pending'
    )

    with db_transaction.atomic():
        # تحديث حالة التحويل
        transfer.status = 'approved'
        transfer.approved_by = request.user
        transfer.approved_at = datetime.datetime.now()
        transfer.save()

        # تحديث بيانات الأصل
        asset = transfer.asset
        asset.branch = transfer.to_branch
        asset.cost_center = transfer.to_cost_center
        asset.responsible_employee = transfer.to_employee
        asset.save()

        messages.success(
            request,
            f'تم الموافقة على التحويل {transfer.transfer_number} وتحديث بيانات الأصل'
        )

    return redirect('assets:transfer_detail', pk=transfer.pk)


@login_required
@permission_required_with_message('assets.can_transfer_asset')
@require_http_methods(["POST"])
def AssetTransferRejectView(request, pk):
    """رفض تحويل أصل"""

    transfer = get_object_or_404(
        AssetTransfer,
        pk=pk,
        company=request.user.company,
        status='pending'
    )

    transfer.status = 'rejected'
    transfer.approved_by = request.user
    transfer.approved_at = datetime.datetime.now()
    transfer.save()

    messages.warning(
        request,
        f'تم رفض التحويل {transfer.transfer_number}'
    )

    return redirect('assets:transfer_detail', pk=transfer.pk)


# =============================================================================
# Transaction Actions
# =============================================================================

@login_required
@permission_required_with_message('assets.delete_assettransaction')
@require_http_methods(["POST"])
def cancel_transaction(request, pk):
    """إلغاء عملية"""

    transaction = get_object_or_404(
        AssetTransaction,
        pk=pk,
        company=request.user.company
    )

    if transaction.status == 'cancelled':
        return JsonResponse({
            'success': False,
            'message': 'العملية ملغاة مسبقاً'
        })

    transaction.status = 'cancelled'
    transaction.save()

    return JsonResponse({
        'success': True,
        'message': f'تم إلغاء العملية {transaction.transaction_number}'
    })


@login_required
@permission_required_with_message('assets.delete_assettransaction')
@require_http_methods(["POST"])
def reverse_transaction(request, pk):
    """عكس قيد عملية"""

    transaction = get_object_or_404(
        AssetTransaction,
        pk=pk,
        company=request.user.company
    )

    if not transaction.journal_entry:
        return JsonResponse({
            'success': False,
            'message': 'لا يوجد قيد محاسبي لعكسه'
        })

    try:
        with db_transaction.atomic():
            # عكس القيد المحاسبي
            original_entry = transaction.journal_entry

            # إنشاء قيد عكسي
            from apps.accounting.models import JournalEntry, JournalEntryLine

            reverse_entry = JournalEntry.objects.create(
                company=request.user.company,
                branch=request.user.branch,
                fiscal_year=original_entry.fiscal_year,
                period=original_entry.period,
                entry_date=datetime.date.today(),
                entry_type='auto',
                description=f"عكس قيد - {original_entry.description}",
                reference=f"REV-{original_entry.number}",
                created_by=request.user
            )

            # نسخ السطور معكوسة
            for line in original_entry.lines.all():
                JournalEntryLine.objects.create(
                    journal_entry=reverse_entry,
                    line_number=line.line_number,
                    account=line.account,
                    description=f"عكس - {line.description}",
                    debit_amount=line.credit_amount,  # عكس
                    credit_amount=line.debit_amount,  # عكس
                    currency=line.currency
                )

            reverse_entry.post(user=request.user)

            # إلغاء العملية
            transaction.status = 'cancelled'
            transaction.save()

            return JsonResponse({
                'success': True,
                'message': f'تم عكس القيد بنجاح - رقم القيد العكسي: {reverse_entry.number}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في عكس القيد: {str(e)}'
        })


# =============================================================================
# Ajax DataTables
# =============================================================================

@login_required
@permission_required('assets.view_assettransaction', raise_exception=True)
def asset_transaction_datatable_ajax(request):
    """Ajax endpoint لجدول العمليات"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    transaction_type = request.GET.get('transaction_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    queryset = AssetTransaction.objects.filter(
        company=request.user.company
    ).select_related('asset', 'branch', 'business_partner')

    if search_value:
        queryset = queryset.filter(
            Q(transaction_number__icontains=search_value) |
            Q(asset__asset_number__icontains=search_value) |
            Q(asset__name__icontains=search_value)
        )

    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)
    if status:
        queryset = queryset.filter(status=status)
    if date_from:
        queryset = queryset.filter(transaction_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(transaction_date__lte=date_to)

    total_records = AssetTransaction.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('-transaction_date', '-transaction_number')[start:start + length]

    data = []
    for trans in queryset:
        # النوع
        type_colors = {
            'purchase': 'success',
            'sale': 'info',
            'disposal': 'danger',
            'revaluation': 'warning',
            'capital_improvement': 'primary',
            'donation_in': 'secondary',
            'donation_out': 'dark'
        }
        type_badge = f'<span class="badge bg-{type_colors.get(trans.transaction_type, "secondary")}">{trans.get_transaction_type_display()}</span>'

        # الحالة
        status_colors = {
            'draft': 'secondary',
            'approved': 'success',
            'completed': 'primary',
            'cancelled': 'danger'
        }
        status_badge = f'<span class="badge bg-{status_colors.get(trans.status, "secondary")}">{trans.get_status_display()}</span>'

        # الإجراءات
        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="#" class="btn btn-info" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if trans.status != 'cancelled' and request.user.has_perm('assets.delete_assettransaction'):
            actions += f'''
                <button type="button" class="btn btn-danger" 
                        onclick="cancelTransaction({trans.pk})" title="إلغاء">
                    <i class="fas fa-times"></i>
                </button>
            '''

        actions += '</div>'

        data.append([
            trans.transaction_number,
            trans.transaction_date.strftime('%Y-%m-%d'),
            type_badge,
            f'<strong>{trans.asset.asset_number}</strong><br><small>{trans.asset.name}</small>',
            f'{trans.amount:,.3f}',
            status_badge,
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


@login_required
@permission_required('assets.view_assettransfer', raise_exception=True)
def asset_transfer_datatable_ajax(request):
    """Ajax endpoint لجدول التحويلات"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = AssetTransfer.objects.filter(
        company=request.user.company
    ).select_related('asset', 'from_branch', 'to_branch')

    if search_value:
        queryset = queryset.filter(
            Q(transfer_number__icontains=search_value) |
            Q(asset__asset_number__icontains=search_value) |
            Q(asset__name__icontains=search_value)
        )

    total_records = AssetTransfer.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('-transfer_date')[start:start + length]

    data = []
    for transfer in queryset:
        # الحالة
        status_colors = {
            'pending': 'warning',
            'approved': 'success',
            'completed': 'primary',
            'rejected': 'danger',
            'cancelled': 'secondary'
        }
        status_badge = f'<span class="badge bg-{status_colors.get(transfer.status, "secondary")}">{transfer.get_status_display()}</span>'

        # الإجراءات
        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="{reverse("assets:transfer_detail", args=[transfer.pk])}" 
                   class="btn btn-info" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if transfer.status == 'pending':
            if request.user.has_perm('assets.change_assettransfer'):
                actions += f'''
                    <a href="{reverse("assets:transfer_update", args=[transfer.pk])}" 
                       class="btn btn-primary" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            if request.user.has_perm('assets.can_transfer_asset'):
                actions += f'''
                    <button type="button" class="btn btn-success" 
                            onclick="approveTransfer({transfer.pk})" title="موافقة">
                        <i class="fas fa-check"></i>
                    </button>
                    <button type="button" class="btn btn-danger" 
                            onclick="rejectTransfer({transfer.pk})" title="رفض">
                        <i class="fas fa-times"></i>
                    </button>
                '''

        actions += '</div>'

        data.append([
            transfer.transfer_number,
            transfer.transfer_date.strftime('%Y-%m-%d'),
            f'<strong>{transfer.asset.asset_number}</strong><br><small>{transfer.asset.name}</small>',
            f'{transfer.from_branch.name} → {transfer.to_branch.name}',
            status_badge,
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })
# apps/assets/views/transaction_views.py
"""
Views العمليات على الأصول
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, TemplateView
from django.db.models import Q
from django.db import transaction as db_transaction

from ..models import AssetTransaction, AssetTransfer, Asset
from ..forms import (
    AssetTransactionForm, AssetPurchaseForm, AssetSaleForm,
    AssetDisposalForm, AssetTransferForm
)
from ..utils import generate_asset_purchase_journal_entry, generate_asset_sale_journal_entry
from apps.core.mixins import CompanyMixin, AuditLogMixin


class AssetTransactionListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة العمليات على الأصول"""

    template_name = 'assets/transactions/transaction_list.html'
    permission_required = 'assets.view_assettransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'العمليات على الأصول',
            'can_add': self.request.user.has_perm('assets.add_assettransaction'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'العمليات', 'url': ''}
            ],
        })
        return context


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
            journal_entry = generate_asset_purchase_journal_entry(
                self.object,
                self.request.user.company
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
            'title': 'شراء أصل ثابت',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'العمليات', 'url': reverse('assets:transaction_list')},
                {'title': 'شراء أصل', 'url': ''}
            ],
        })
        return context


class AssetSaleView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """بيع أصل"""

    model = AssetTransaction
    form_class = AssetSaleForm
    template_name = 'assets/transactions/sale_form.html'
    permission_required = 'assets.can_sell_asset'
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
        form.instance.transaction_type = 'sale'
        form.instance.status = 'approved'

        # حساب القيمة الدفترية والربح/الخسارة
        asset = form.instance.asset
        form.instance.book_value_at_sale = asset.book_value
        form.instance.gain_loss = form.instance.sale_price - asset.book_value
        form.instance.amount = form.instance.sale_price

        response = super().form_valid(form)

        # تحديث حالة الأصل
        asset.status = 'sold'
        asset.save()

        # توليد القيد المحاسبي
        try:
            journal_entry = generate_asset_sale_journal_entry(
                self.object,
                self.request.user.company
            )
            self.object.journal_entry = journal_entry
            self.object.save()

            gain_loss_text = f'ربح: {self.object.gain_loss:,.3f}' if self.object.gain_loss > 0 else f'خسارة: {abs(self.object.gain_loss):,.3f}'

            messages.success(
                self.request,
                f'تم تسجيل عملية البيع بنجاح - {gain_loss_text} - القيد رقم: {journal_entry.number}'
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
            'title': 'بيع أصل ثابت',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'العمليات', 'url': reverse('assets:transaction_list')},
                {'title': 'بيع أصل', 'url': ''}
            ],
        })
        return context


class AssetDisposalView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """استبعاد/إتلاف أصل"""

    model = AssetTransaction
    form_class = AssetDisposalForm
    template_name = 'assets/transactions/disposal_form.html'
    permission_required = 'assets.can_dispose_asset'
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
        form.instance.transaction_type = 'disposal'
        form.instance.status = 'approved'
        form.instance.amount = 0

        response = super().form_valid(form)

        # تحديث حالة الأصل
        asset = form.instance.asset
        asset.status = 'disposed'
        asset.save()

        messages.success(
            self.request,
            f'تم تسجيل استبعاد الأصل {asset.asset_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'استبعاد/إتلاف أصل',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'العمليات', 'url': reverse('assets:transaction_list')},
                {'title': 'استبعاد أصل', 'url': ''}
            ],
        })
        return context


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

    queryset = AssetTransaction.objects.filter(
        company=request.user.company
    ).select_related('asset', 'branch', 'counterpart_account')

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

    total_records = AssetTransaction.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('-transaction_date')[start:start + length]

    data = []
    for trans in queryset:
        # النوع مع لون
        type_colors = {
            'purchase': 'success',
            'sale': 'info',
            'disposal': 'danger',
            'revaluation': 'warning',
            'capital_improvement': 'primary'
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

        data.append([
            trans.transaction_number,
            trans.transaction_date.strftime('%Y-%m-%d'),
            type_badge,
            f'<strong>{trans.asset.asset_number}</strong><br><small>{trans.asset.name}</small>',
            f'{trans.amount:,.3f}',
            status_badge,
            f'<a href="#" class="btn btn-sm btn-info"><i class="fas fa-eye"></i></a>'
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


# ═══════════════════════════════════════════════════════════
# التحويلات
# ═══════════════════════════════════════════════════════════

class AssetTransferListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة تحويلات الأصول"""

    template_name = 'assets/transfers/transfer_list.html'
    permission_required = 'assets.view_assettransfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'تحويلات الأصول',
            'can_add': self.request.user.has_perm('assets.can_transfer_asset'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التحويلات', 'url': ''}
            ],
        })
        return context


class AssetTransferCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """تحويل أصل"""

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
        form.instance.status = 'approved'  # أو 'pending' إذا كان يتطلب موافقة

        response = super().form_valid(form)

        # تحديث بيانات الأصل
        asset = form.instance.asset
        asset.branch = form.instance.to_branch
        asset.cost_center = form.instance.to_cost_center
        asset.responsible_employee = form.instance.to_employee
        asset.save()

        messages.success(
            self.request,
            f'تم تحويل الأصل {asset.asset_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'تحويل أصل',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التحويلات', 'url': reverse('assets:transfer_list')},
                {'title': 'تحويل جديد', 'url': ''}
            ],
        })
        return context
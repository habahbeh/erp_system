# apps/accounting/views/voucher_views.py
"""
Voucher Views - إدارة السندات (القبض والصرف)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import PaymentVoucher, ReceiptVoucher
from ..forms.voucher_forms import PaymentVoucherForm, ReceiptVoucherForm


# ========== Payment Voucher Views ==========

class PaymentVoucherListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سندات الصرف"""

    model = PaymentVoucher
    template_name = 'accounting/vouchers/payment_voucher_list.html'
    context_object_name = 'vouchers'
    permission_required = 'accounting.view_paymentvoucher'
    paginate_by = 25

    def get_queryset(self):
        queryset = PaymentVoucher.objects.filter(
            company=self.request.current_company
        ).select_related('cash_account', 'expense_account', 'currency', 'created_by').order_by('-date', '-number')

        # الفلترة
        status = self.request.GET.get('status')
        payment_method = self.request.GET.get('payment_method')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(beneficiary_name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        company = self.request.current_company
        stats = PaymentVoucher.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            posted=Count('id', filter=Q(status='posted')),
            total_amount=Sum('amount', filter=Q(status='posted'))
        )

        context.update({
            'title': _('سندات الصرف'),
            'can_add': self.request.user.has_perm('accounting.add_paymentvoucher'),
            'can_edit': self.request.user.has_perm('accounting.change_paymentvoucher'),
            'can_delete': self.request.user.has_perm('accounting.delete_paymentvoucher'),
            'status_choices': PaymentVoucher.STATUS_CHOICES,
            'payment_method_choices': PaymentVoucher.PAYMENT_METHODS,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات الصرف'), 'url': ''},
            ]
        })
        return context


class PaymentVoucherCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سند صرف جديد"""

    model = PaymentVoucher
    form_class = PaymentVoucherForm
    template_name = 'accounting/vouchers/payment_voucher_form.html'
    permission_required = 'accounting.add_paymentvoucher'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء سند الصرف {self.object.number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:payment_voucher_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء سند صرف جديد'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات الصرف'), 'url': reverse('accounting:payment_voucher_list')},
                {'title': _('إنشاء جديد'), 'url': ''},
            ]
        })
        return context


class PaymentVoucherDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل سند الصرف"""

    model = PaymentVoucher
    template_name = 'accounting/vouchers/payment_voucher_detail.html'
    context_object_name = 'voucher'
    permission_required = 'accounting.view_paymentvoucher'

    def get_queryset(self):
        return PaymentVoucher.objects.filter(
            company=self.request.current_company
        ).select_related('cash_account', 'expense_account', 'currency', 'created_by', 'posted_by', 'journal_entry')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'سند الصرف {self.object.number}',
            'can_edit': self.request.user.has_perm('accounting.change_paymentvoucher') and self.object.can_edit(),
            'can_delete': self.request.user.has_perm('accounting.delete_paymentvoucher') and self.object.can_delete(),
            'can_post': self.request.user.has_perm('accounting.change_paymentvoucher') and self.object.can_post(),
            'can_unpost': self.request.user.has_perm('accounting.change_paymentvoucher') and self.object.can_unpost(),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات الصرف'), 'url': reverse('accounting:payment_voucher_list')},
                {'title': self.object.number, 'url': ''},
            ]
        })
        return context


class PaymentVoucherUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سند الصرف"""

    model = PaymentVoucher
    form_class = PaymentVoucherForm
    template_name = 'accounting/vouchers/payment_voucher_form.html'
    permission_required = 'accounting.change_paymentvoucher'

    def get_queryset(self):
        return PaymentVoucher.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if not self.object.can_edit():
            messages.error(self.request, _('لا يمكن تعديل سند مرحل'))
            return redirect('accounting:payment_voucher_detail', pk=self.object.pk)

        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث سند الصرف {self.object.number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:payment_voucher_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل سند الصرف {self.object.number}',
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات الصرف'), 'url': reverse('accounting:payment_voucher_list')},
                {'title': f'تعديل {self.object.number}', 'url': ''},
            ]
        })
        return context


class PaymentVoucherDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف سند الصرف"""

    model = PaymentVoucher
    template_name = 'accounting/vouchers/payment_voucher_confirm_delete.html'
    permission_required = 'accounting.delete_paymentvoucher'
    success_url = reverse_lazy('accounting:payment_voucher_list')

    def get_queryset(self):
        return PaymentVoucher.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if not self.object.can_delete():
            messages.error(request, _('لا يمكن حذف سند مرحل'))
            return redirect('accounting:payment_voucher_detail', pk=self.object.pk)

        voucher_number = self.object.number
        messages.success(request, f'تم حذف سند الصرف {voucher_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# ========== Receipt Voucher Views ==========

class ReceiptVoucherListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سندات القبض"""

    model = ReceiptVoucher
    template_name = 'accounting/vouchers/receipt_voucher_list.html'
    context_object_name = 'vouchers'
    permission_required = 'accounting.view_receiptvoucher'
    paginate_by = 25

    def get_queryset(self):
        queryset = ReceiptVoucher.objects.filter(
            company=self.request.current_company
        ).select_related('cash_account', 'income_account', 'currency', 'created_by').order_by('-date', '-number')

        # الفلترة
        status = self.request.GET.get('status')
        receipt_method = self.request.GET.get('receipt_method')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if receipt_method:
            queryset = queryset.filter(receipt_method=receipt_method)

        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(received_from__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        company = self.request.current_company
        stats = ReceiptVoucher.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            posted=Count('id', filter=Q(status='posted')),
            total_amount=Sum('amount', filter=Q(status='posted'))
        )

        context.update({
            'title': _('سندات القبض'),
            'can_add': self.request.user.has_perm('accounting.add_receiptvoucher'),
            'can_edit': self.request.user.has_perm('accounting.change_receiptvoucher'),
            'can_delete': self.request.user.has_perm('accounting.delete_receiptvoucher'),
            'status_choices': ReceiptVoucher.STATUS_CHOICES,
            'receipt_method_choices': ReceiptVoucher.RECEIPT_METHODS,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات القبض'), 'url': ''},
            ]
        })
        return context


class ReceiptVoucherCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سند قبض جديد"""

    model = ReceiptVoucher
    form_class = ReceiptVoucherForm
    template_name = 'accounting/vouchers/receipt_voucher_form.html'
    permission_required = 'accounting.add_receiptvoucher'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء سند القبض {self.object.number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:receipt_voucher_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء سند قبض جديد'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات القبض'), 'url': reverse('accounting:receipt_voucher_list')},
                {'title': _('إنشاء جديد'), 'url': ''},
            ]
        })
        return context


class ReceiptVoucherDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل سند القبض"""

    model = ReceiptVoucher
    template_name = 'accounting/vouchers/receipt_voucher_detail.html'
    context_object_name = 'voucher'
    permission_required = 'accounting.view_receiptvoucher'

    def get_queryset(self):
        return ReceiptVoucher.objects.filter(
            company=self.request.current_company
        ).select_related('cash_account', 'income_account', 'currency', 'created_by', 'posted_by', 'journal_entry')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'سند القبض {self.object.number}',
            'can_edit': self.request.user.has_perm('accounting.change_receiptvoucher') and self.object.can_edit(),
            'can_delete': self.request.user.has_perm('accounting.delete_receiptvoucher') and self.object.can_delete(),
            'can_post': self.request.user.has_perm('accounting.change_receiptvoucher') and self.object.can_post(),
            'can_unpost': self.request.user.has_perm('accounting.change_receiptvoucher') and self.object.can_unpost(),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات القبض'), 'url': reverse('accounting:receipt_voucher_list')},
                {'title': self.object.number, 'url': ''},
            ]
        })
        return context


class ReceiptVoucherUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سند القبض"""

    model = ReceiptVoucher
    form_class = ReceiptVoucherForm
    template_name = 'accounting/vouchers/receipt_voucher_form.html'
    permission_required = 'accounting.change_receiptvoucher'

    def get_queryset(self):
        return ReceiptVoucher.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if not self.object.can_edit():
            messages.error(self.request, _('لا يمكن تعديل سند مرحل'))
            return redirect('accounting:receipt_voucher_detail', pk=self.object.pk)

        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث سند القبض {self.object.number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:receipt_voucher_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل سند القبض {self.object.number}',
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('سندات القبض'), 'url': reverse('accounting:receipt_voucher_list')},
                {'title': f'تعديل {self.object.number}', 'url': ''},
            ]
        })
        return context


class ReceiptVoucherDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف سند القبض"""

    model = ReceiptVoucher
    template_name = 'accounting/vouchers/receipt_voucher_confirm_delete.html'
    permission_required = 'accounting.delete_receiptvoucher'
    success_url = reverse_lazy('accounting:receipt_voucher_list')

    def get_queryset(self):
        return ReceiptVoucher.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if not self.object.can_delete():
            messages.error(request, _('لا يمكن حذف سند مرحل'))
            return redirect('accounting:receipt_voucher_detail', pk=self.object.pk)

        voucher_number = self.object.number
        messages.success(request, f'تم حذف سند القبض {voucher_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# ========== Ajax Functions للترحيل ==========

@login_required
@permission_required_with_message('accounting.change_paymentvoucher')
@require_http_methods(["POST"])
def post_payment_voucher(request, pk):
    """ترحيل سند الصرف"""
    try:
        voucher = get_object_or_404(
            PaymentVoucher,
            pk=pk,
            company=request.current_company
        )

        if not voucher.can_post():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن ترحيل هذا السند'
            })

        voucher.status = 'confirmed'  # تأكيد السند أولاً
        voucher.save()

        voucher.post(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل سند الصرف {voucher.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل السند: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_paymentvoucher')
@require_http_methods(["POST"])
def unpost_payment_voucher(request, pk):
    """إلغاء ترحيل سند الصرف"""
    try:
        voucher = get_object_or_404(
            PaymentVoucher,
            pk=pk,
            company=request.current_company
        )

        if not voucher.can_unpost():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن إلغاء ترحيل هذا السند'
            })

        voucher.unpost()

        return JsonResponse({
            'success': True,
            'message': f'تم إلغاء ترحيل سند الصرف {voucher.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إلغاء ترحيل السند: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_receiptvoucher')
@require_http_methods(["POST"])
def post_receipt_voucher(request, pk):
    """ترحيل سند القبض"""
    try:
        voucher = get_object_or_404(
            ReceiptVoucher,
            pk=pk,
            company=request.current_company
        )

        if not voucher.can_post():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن ترحيل هذا السند'
            })

        voucher.status = 'confirmed'  # تأكيد السند أولاً
        voucher.save()

        voucher.post(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل سند القبض {voucher.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل السند: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_receiptvoucher')
@require_http_methods(["POST"])
def unpost_receipt_voucher(request, pk):
    """إلغاء ترحيل سند القبض"""
    try:
        voucher = get_object_or_404(
            ReceiptVoucher,
            pk=pk,
            company=request.current_company
        )

        if not voucher.can_unpost():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن إلغاء ترحيل هذا السند'
            })

        voucher.unpost()

        return JsonResponse({
            'success': True,
            'message': f'تم إلغاء ترحيل سند القبض {voucher.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إلغاء ترحيل السند: {str(e)}'
        })
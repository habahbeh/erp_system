# apps/sales/views/payment_views.py
"""
Views لأقساط الدفع
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from apps.sales.models import PaymentInstallment, SalesInvoice
from apps.sales.forms import (
    PaymentInstallmentForm,
    RecordPaymentForm,
    CreateInstallmentPlanForm,
    InstallmentPlanFormSet
)
from apps.accounting.models import ReceiptVoucher, Account
from apps.core.models import Currency


class InstallmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة أقساط الدفع"""
    model = PaymentInstallment
    template_name = 'sales/installments/installment_list.html'
    context_object_name = 'installments'
    permission_required = 'sales.view_paymentinstallment'
    paginate_by = 50

    def get_queryset(self):
        """الحصول على أقساط الدفع للشركة الحالية"""
        queryset = PaymentInstallment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'invoice',
            'invoice__customer',
            'receipt_voucher',
            'created_by'
        ).prefetch_related('invoice__lines')

        # الفلاتر
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)

        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(invoice__customer_id=customer_id)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(due_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(due_date__lte=date_to)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(invoice__number__icontains=search) |
                models.Q(invoice__customer__name__icontains=search) |
                models.Q(notes__icontains=search)
            )

        return queryset.order_by('due_date', 'invoice')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('أقساط الدفع')

        # إحصائيات
        installments = self.get_queryset()
        context['total_installments'] = installments.count()
        context['pending_installments'] = installments.filter(status='pending').count()
        context['paid_installments'] = installments.filter(status='paid').count()
        context['overdue_installments'] = installments.filter(status='overdue').count()

        # المبالغ
        context['total_amount'] = installments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        context['paid_amount'] = installments.aggregate(
            total=models.Sum('paid_amount')
        )['total'] or Decimal('0')

        context['remaining_amount'] = context['total_amount'] - context['paid_amount']

        return context


class CreateInstallmentPlanView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """إنشاء خطة أقساط للفاتورة"""
    template_name = 'sales/installments/installment_plan_form.html'
    form_class = CreateInstallmentPlanForm
    permission_required = 'sales.add_paymentinstallment'

    def dispatch(self, request, *args, **kwargs):
        """الحصول على الفاتورة"""
        self.invoice = get_object_or_404(
            SalesInvoice,
            pk=kwargs.get('invoice_pk'),
            company=request.current_company
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """إضافة الفاتورة للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['invoice'] = self.invoice
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إنشاء خطة أقساط للفاتورة {}').format(self.invoice.number)
        context['invoice'] = self.invoice

        # حساب المبلغ المتبقي للتقسيط
        existing_installments_total = self.invoice.installments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        context['remaining_for_installments'] = (
            self.invoice.total_with_tax - existing_installments_total
        )

        if self.request.POST:
            context['formset'] = InstallmentPlanFormSet(
                self.request.POST,
                instance=self.invoice
            )
        else:
            # إذا تم إنشاء خطة تلقائية
            if self.request.GET.get('auto') == 'true':
                form = self.get_form()
                if form.is_valid():
                    installments_data = form.generate_installments()
                    # إنشاء formset بالبيانات المولدة
                    initial_data = installments_data
                    context['formset'] = InstallmentPlanFormSet(
                        instance=self.invoice,
                        initial=initial_data
                    )
                else:
                    context['formset'] = InstallmentPlanFormSet(instance=self.invoice)
            else:
                context['formset'] = InstallmentPlanFormSet(instance=self.invoice)

        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ خطة الأقساط"""
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # حفظ الأقساط
            formset.instance = self.invoice
            installments = formset.save(commit=False)

            # تعيين الشركة والفرع للأقساط الجديدة
            for installment in installments:
                if not installment.pk:
                    installment.company = self.request.current_company
                    installment.branch = self.request.current_branch
                    installment.created_by = self.request.user
                installment.save()

            # حذف الأقساط المحددة للحذف
            for obj in formset.deleted_objects:
                obj.delete()

            # تحديث حالة الدفع في الفاتورة
            self.invoice.update_payment_status()
            self.invoice.save()

            messages.success(
                self.request,
                _('تم إنشاء خطة الأقساط للفاتورة {} بنجاح').format(self.invoice.number)
            )
            return redirect('sales:invoice_detail', pk=self.invoice.pk)
        else:
            messages.error(self.request, _('يرجى تصحيح الأخطاء في النموذج'))
            return self.form_invalid(form)


class InstallmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل قسط الدفع"""
    model = PaymentInstallment
    template_name = 'sales/installments/installment_detail.html'
    context_object_name = 'installment'
    permission_required = 'sales.view_paymentinstallment'

    def get_queryset(self):
        """الحصول على أقساط الدفع للشركة الحالية فقط"""
        return PaymentInstallment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'invoice',
            'invoice__customer',
            'receipt_voucher',
            'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('قسط رقم {} - فاتورة {}').format(
            self.object.installment_number,
            self.object.invoice.number
        )

        # حساب التفاصيل
        context['remaining_amount'] = self.object.remaining_amount
        context['is_overdue'] = self.object.is_overdue
        context['can_record_payment'] = (
            self.object.status != 'paid' and
            self.object.status != 'cancelled' and
            self.object.remaining_amount > 0
        )

        return context


class RecordPaymentView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """تسجيل دفعة على قسط"""
    template_name = 'sales/installments/payment_record_form.html'
    form_class = RecordPaymentForm
    permission_required = 'sales.change_paymentinstallment'

    def dispatch(self, request, *args, **kwargs):
        """الحصول على القسط"""
        self.installment = get_object_or_404(
            PaymentInstallment,
            pk=kwargs.get('pk'),
            company=request.current_company
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """إضافة القسط والشركة للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['installment'] = self.installment
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تسجيل دفعة - قسط رقم {}').format(
            self.installment.installment_number
        )
        context['installment'] = self.installment
        context['invoice'] = self.installment.invoice
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الدفعة وإنشاء سند قبض"""
        # التحقق من أن القسط قابل للدفع
        if self.installment.status == 'cancelled':
            messages.error(self.request, _('لا يمكن تسجيل دفعة على قسط ملغي'))
            return redirect('sales:installment_detail', pk=self.installment.pk)

        if self.installment.status == 'paid':
            messages.error(self.request, _('القسط مدفوع بالكامل'))
            return redirect('sales:installment_detail', pk=self.installment.pk)

        # تحديث بيانات الدفع
        payment_date = form.cleaned_data['payment_date']
        paid_amount = form.cleaned_data['paid_amount']
        payment_method = form.cleaned_data['payment_method']
        reference_number = form.cleaned_data.get('reference_number', '')

        self.installment.paid_amount += paid_amount
        self.installment.payment_date = payment_date

        # حفظ الملاحظات
        if form.cleaned_data.get('notes'):
            if self.installment.notes:
                self.installment.notes += f"\n---\n{form.cleaned_data['notes']}"
            else:
                self.installment.notes = form.cleaned_data['notes']

        # تحديث الحالة
        self.installment.update_status()

        # إنشاء سند القبض
        try:
            # الحصول على العملة الافتراضية
            currency = Currency.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).first()

            if not currency:
                raise ValidationError(_('لا توجد عملة نشطة في الشركة'))

            # الحصول على حساب الصندوق/البنك الافتراضي من طريقة الدفع
            # يمكن تحسين هذا لاحقاً بربطه بحساب محدد من PaymentMethod
            cash_account = Account.objects.filter(
                company=self.request.current_company,
                account_type='asset',
                is_active=True,
                accept_entries=True
            ).first()

            if not cash_account:
                raise ValidationError(_('لا يوجد حساب صندوق/بنك نشط'))

            # الحصول على حساب العميل (حساب الإيراد)
            # يمكن أن يكون من الفاتورة أو العميل
            income_account = None
            if hasattr(self.installment.invoice.customer, 'account') and self.installment.invoice.customer.account:
                income_account = self.installment.invoice.customer.account
            else:
                # استخدام حساب إيراد افتراضي
                income_account = Account.objects.filter(
                    company=self.request.current_company,
                    account_type='revenue',
                    is_active=True,
                    accept_entries=True
                ).first()

            # إنشاء سند القبض
            receipt_voucher = ReceiptVoucher.objects.create(
                company=self.request.current_company,
                branch=self.request.current_branch,
                date=payment_date,
                status='confirmed',
                received_from=self.installment.invoice.customer.name,
                payer_type='customer',
                payer_id=self.installment.invoice.customer.pk,
                amount=paid_amount,
                currency=currency,
                exchange_rate=Decimal('1.0'),
                receipt_method=payment_method.code if hasattr(payment_method, 'code') else 'cash',
                cash_account=cash_account,
                income_account=income_account,
                description=f'دفعة على القسط رقم {self.installment.installment_number} من الفاتورة {self.installment.invoice.number}',
                check_number=reference_number if payment_method.code in ['check', 'transfer'] else '',
                notes=form.cleaned_data.get('notes', ''),
                created_by=self.request.user
            )

            # ربط سند القبض بالقسط
            self.installment.receipt_voucher = receipt_voucher
            self.installment.save()

            # ترحيل سند القبض تلقائياً
            try:
                receipt_voucher.post(user=self.request.user)
                messages.success(
                    self.request,
                    _('تم تسجيل دفعة بمبلغ {} بنجاح وإنشاء سند قبض رقم {}').format(
                        paid_amount, receipt_voucher.number
                    )
                )
            except ValidationError as e:
                # إذا فشل الترحيل، نترك السند بحالة confirmed
                messages.warning(
                    self.request,
                    _('تم تسجيل الدفعة وإنشاء سند قبض رقم {} ولكن لم يتم ترحيله: {}').format(
                        receipt_voucher.number, str(e)
                    )
                )

        except ValidationError as e:
            # إذا فشل إنشاء سند القبض، نحفظ الدفعة فقط
            self.installment.save()
            messages.warning(
                self.request,
                _('تم تسجيل الدفعة بنجاح ولكن لم يتم إنشاء سند القبض: {}').format(str(e))
            )
        except Exception as e:
            # أي خطأ آخر
            self.installment.save()
            messages.warning(
                self.request,
                _('تم تسجيل الدفعة بنجاح ولكن حدث خطأ أثناء إنشاء سند القبض: {}').format(str(e))
            )

        # تحديث حالة الدفع في الفاتورة
        self.installment.invoice.update_payment_status()
        self.installment.invoice.save()

        return redirect('sales:installment_detail', pk=self.installment.pk)


class CancelInstallmentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """إلغاء قسط دفع"""
    permission_required = 'sales.delete_paymentinstallment'

    @transaction.atomic
    def post(self, request, pk):
        """إلغاء القسط"""
        installment = get_object_or_404(
            PaymentInstallment,
            pk=pk,
            company=request.current_company
        )

        # التحقق من إمكانية الإلغاء
        if installment.status == 'paid':
            messages.error(request, _('لا يمكن إلغاء قسط مدفوع'))
            return redirect('sales:installment_detail', pk=installment.pk)

        if installment.receipt_voucher:
            messages.error(request, _('لا يمكن إلغاء قسط مرتبط بسند قبض'))
            return redirect('sales:installment_detail', pk=installment.pk)

        # إلغاء القسط
        installment.cancel()

        # تحديث حالة الدفع في الفاتورة
        installment.invoice.update_payment_status()
        installment.invoice.save()

        messages.success(
            request,
            _('تم إلغاء القسط رقم {} بنجاح').format(installment.installment_number)
        )
        return redirect('sales:invoice_detail', pk=installment.invoice.pk)


class UpdateInstallmentStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """تحديث حالات الأقساط (للأقساط المتأخرة)"""
    permission_required = 'sales.change_paymentinstallment'

    @transaction.atomic
    def post(self, request):
        """تحديث حالات جميع الأقساط"""
        from django.utils import timezone

        # الحصول على الأقساط غير المدفوعة وغير الملغاة
        installments = PaymentInstallment.objects.filter(
            company=request.current_company,
            status__in=['pending', 'overdue']
        )

        updated_count = 0
        for installment in installments:
            old_status = installment.status
            installment.update_status()

            if old_status != installment.status:
                installment.save()
                updated_count += 1

        messages.success(
            request,
            _('تم تحديث حالة {} قسط').format(updated_count)
        )

        return redirect('sales:installment_list')

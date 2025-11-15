# apps/sales/views/commission_views.py
"""
Views لعمولات المندوبين
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime

from apps.sales.models import SalespersonCommission, SalesInvoice
from apps.sales.forms import SalespersonCommissionForm, RecordCommissionPaymentForm


class CommissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة عمولات المندوبين"""
    model = SalespersonCommission
    template_name = 'sales/commissions/commission_list.html'
    context_object_name = 'commissions'
    permission_required = 'sales.view_salespersoncommission'
    paginate_by = 50

    def get_queryset(self):
        """الحصول على العمولات للشركة الحالية"""
        queryset = SalespersonCommission.objects.filter(
            company=self.request.current_company
        ).select_related(
            'salesperson',
            'invoice',
            'invoice__customer',
            'payment_voucher'
        )

        # الفلاتر
        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)

        payment_status = self.request.GET.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(calculation_date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(calculation_date__lte=date_to)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(invoice__number__icontains=search) |
                Q(salesperson__first_name__icontains=search) |
                Q(salesperson__last_name__icontains=search)
            )

        return queryset.order_by('-calculation_date', '-invoice__date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('عمولات المندوبين')

        # إحصائيات
        commissions = self.get_queryset()

        context['total_commissions'] = commissions.count()

        # إجمالي المبالغ
        totals = commissions.aggregate(
            total_commission_amount=Sum('commission_amount'),
            total_paid_amount=Sum('paid_amount'),
            total_remaining_amount=Sum('remaining_amount')
        )

        context['total_commission_amount'] = totals['total_commission_amount'] or Decimal('0')
        context['total_paid_amount'] = totals['total_paid_amount'] or Decimal('0')
        context['total_remaining_amount'] = totals['total_remaining_amount'] or Decimal('0')

        # عدد العمولات حسب الحالة
        context['unpaid_commissions'] = commissions.filter(payment_status='unpaid').count()
        context['partial_commissions'] = commissions.filter(payment_status='partial').count()
        context['paid_commissions'] = commissions.filter(payment_status='paid').count()

        # قائمة المندوبين للفلتر
        from apps.hr.models import Employee
        context['salespersons'] = Employee.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('first_name', 'last_name')

        return context


class CommissionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء عمولة جديدة"""
    model = SalespersonCommission
    form_class = SalespersonCommissionForm
    template_name = 'sales/commissions/commission_form.html'
    permission_required = 'sales.add_salespersoncommission'
    success_url = reverse_lazy('sales:commission_list')

    def get_form_kwargs(self):
        """إضافة company للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة عمولة جديدة')
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ العمولة"""
        self.object = form.save(commit=False)
        self.object.company = self.request.current_company
        self.object.branch = self.request.current_branch
        self.object.created_by = self.request.user
        self.object.save()

        messages.success(
            self.request,
            _('تم إنشاء العمولة للمندوب "{}" بنجاح').format(self.object.salesperson)
        )
        return redirect(self.success_url)


class CommissionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عمولة"""
    model = SalespersonCommission
    form_class = SalespersonCommissionForm
    template_name = 'sales/commissions/commission_form.html'
    permission_required = 'sales.change_salespersoncommission'
    success_url = reverse_lazy('sales:commission_list')

    def get_queryset(self):
        """الحصول على العمولات للشركة الحالية فقط"""
        return SalespersonCommission.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        """إضافة company للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل العمولة')
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ التعديلات"""
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تعديل العمولة بنجاح')
        )
        return redirect(self.success_url)


class CommissionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل العمولة"""
    model = SalespersonCommission
    template_name = 'sales/commissions/commission_detail.html'
    context_object_name = 'commission'
    permission_required = 'sales.view_salespersoncommission'

    def get_queryset(self):
        """الحصول على العمولات للشركة الحالية فقط"""
        return SalespersonCommission.objects.filter(
            company=self.request.current_company
        ).select_related(
            'salesperson',
            'invoice',
            'invoice__customer',
            'payment_voucher'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('عمولة المندوب: {}').format(self.object.salesperson)

        # حساب نسبة الدفع
        if self.object.commission_amount > 0:
            context['payment_percentage'] = (
                self.object.paid_amount / self.object.commission_amount * 100
            )
        else:
            context['payment_percentage'] = 0

        # التحقق من إمكانية تسجيل دفعة
        context['can_record_payment'] = (
            self.object.payment_status != 'paid' and
            self.object.remaining_amount > 0
        )

        return context


class CommissionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف عمولة"""
    model = SalespersonCommission
    template_name = 'sales/commissions/commission_confirm_delete.html'
    permission_required = 'sales.delete_salespersoncommission'
    success_url = reverse_lazy('sales:commission_list')

    def get_queryset(self):
        """الحصول على العمولات للشركة الحالية فقط"""
        return SalespersonCommission.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        """التحقق قبل الحذف"""
        self.object = self.get_object()

        # التحقق من وجود مدفوعات
        if self.object.paid_amount > 0:
            messages.warning(
                request,
                _('تحذير: تم دفع مبلغ {} من هذه العمولة. تأكد من إلغاء الدفعات أولاً.').format(
                    self.object.paid_amount
                )
            )

        messages.success(
            request,
            _('تم حذف العمولة بنجاح')
        )
        return super().delete(request, *args, **kwargs)


class RecordCommissionPaymentView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تسجيل دفعة عمولة"""
    model = SalespersonCommission
    form_class = RecordCommissionPaymentForm
    template_name = 'sales/commissions/record_commission_payment.html'
    permission_required = 'sales.change_salespersoncommission'

    def get_queryset(self):
        """الحصول على العمولات للشركة الحالية فقط"""
        return SalespersonCommission.objects.filter(
            company=self.request.current_company,
            payment_status__in=['unpaid', 'partial']  # فقط العمولات غير المدفوعة بالكامل
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تسجيل دفعة عمولة')
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الدفعة"""
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تسجيل دفعة العمولة بنجاح')
        )
        return redirect('sales:commission_detail', pk=self.object.pk)


class CommissionReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """تقرير عمولات المندوبين"""
    template_name = 'sales/commissions/commission_report.html'
    permission_required = 'sales.view_salespersoncommission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تقرير عمولات المندوبين')

        # الحصول على الفلاتر
        salesperson_id = self.request.GET.get('salesperson')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        payment_status = self.request.GET.get('payment_status')

        # الاستعلام الأساسي
        commissions = SalespersonCommission.objects.filter(
            company=self.request.current_company
        ).select_related('salesperson', 'invoice', 'invoice__customer')

        # تطبيق الفلاتر
        if salesperson_id:
            commissions = commissions.filter(salesperson_id=salesperson_id)

        if date_from:
            commissions = commissions.filter(calculation_date__gte=date_from)

        if date_to:
            commissions = commissions.filter(calculation_date__lte=date_to)

        if payment_status:
            commissions = commissions.filter(payment_status=payment_status)

        # تجميع البيانات حسب المندوب
        from apps.hr.models import Employee
        salespersons_data = []

        salespersons = Employee.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('first_name', 'last_name')

        if salesperson_id:
            salespersons = salespersons.filter(id=salesperson_id)

        for salesperson in salespersons:
            salesperson_commissions = commissions.filter(salesperson=salesperson)

            if salesperson_commissions.exists():
                totals = salesperson_commissions.aggregate(
                    total_commissions=Count('id'),
                    total_base_amount=Sum('base_amount'),
                    total_commission_amount=Sum('commission_amount'),
                    total_paid_amount=Sum('paid_amount'),
                    total_remaining_amount=Sum('remaining_amount')
                )

                salespersons_data.append({
                    'salesperson': salesperson,
                    'commissions': salesperson_commissions.order_by('-calculation_date'),
                    'total_commissions': totals['total_commissions'] or 0,
                    'total_base_amount': totals['total_base_amount'] or Decimal('0'),
                    'total_commission_amount': totals['total_commission_amount'] or Decimal('0'),
                    'total_paid_amount': totals['total_paid_amount'] or Decimal('0'),
                    'total_remaining_amount': totals['total_remaining_amount'] or Decimal('0'),
                })

        context['salespersons_data'] = salespersons_data

        # إجمالي عام
        grand_totals = commissions.aggregate(
            total_commissions=Count('id'),
            total_base_amount=Sum('base_amount'),
            total_commission_amount=Sum('commission_amount'),
            total_paid_amount=Sum('paid_amount'),
            total_remaining_amount=Sum('remaining_amount')
        )

        context['grand_totals'] = {
            'total_commissions': grand_totals['total_commissions'] or 0,
            'total_base_amount': grand_totals['total_base_amount'] or Decimal('0'),
            'total_commission_amount': grand_totals['total_commission_amount'] or Decimal('0'),
            'total_paid_amount': grand_totals['total_paid_amount'] or Decimal('0'),
            'total_remaining_amount': grand_totals['total_remaining_amount'] or Decimal('0'),
        }

        # قائمة المندوبين للفلتر
        context['all_salespersons'] = Employee.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('first_name', 'last_name')

        # تمرير معاملات الفلتر
        context['filter_salesperson'] = salesperson_id
        context['filter_date_from'] = date_from
        context['filter_date_to'] = date_to
        context['filter_payment_status'] = payment_status

        return context

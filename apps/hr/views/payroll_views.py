# apps/hr/views/payroll_views.py
"""
عروض الرواتب - المرحلة الثالثة
Payroll Views - Phase 3
"""

from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date
from calendar import monthrange

from ..models import (
    Payroll, PayrollDetail, Employee, Attendance, Overtime,
    Advance, AdvanceInstallment, HRSettings, EmployeeContract
)
from ..forms.payroll_forms import (
    PayrollForm, PayrollDetailForm, PayrollProcessForm,
    PayrollApproveForm, PayrollPaymentForm, BulkPayrollDetailForm
)


class PayrollListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة كشوفات الرواتب"""
    template_name = 'hr/payroll/payroll_list.html'
    permission_required = 'hr.view_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات
        stats = Payroll.objects.filter(company=company).aggregate(
            total_count=Count('id'),
            draft_count=Count('id', filter=Q(status='draft')),
            approved_count=Count('id', filter=Q(status='approved')),
            paid_count=Count('id', filter=Q(status='paid')),
            total_net=Sum('total_net', filter=Q(status__in=['approved', 'paid'])),
        )

        context.update({
            'title': _('كشوفات الرواتب'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': None},
            ],
        })
        return context


class PayrollCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء كشف راتب جديد"""
    model = Payroll
    form_class = PayrollForm
    template_name = 'hr/payroll/payroll_form.html'
    permission_required = 'hr.add_payroll'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _('تم إنشاء مسير الرواتب بنجاح'))
        return response

    def get_success_url(self):
        return reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء كشف راتب جديد'),
            'submit_text': _('إنشاء'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': _('إنشاء'), 'url': None},
            ],
        })
        return context


class PayrollDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل مسير الرواتب"""
    model = Payroll
    template_name = 'hr/payroll/payroll_detail.html'
    permission_required = 'hr.view_payroll'
    context_object_name = 'payroll'

    def get_queryset(self):
        return Payroll.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = self.object

        # تفاصيل الرواتب
        details = payroll.details.select_related('employee').order_by('employee__first_name')

        # إحصائيات التفاصيل
        stats = details.aggregate(
            count=Count('id'),
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('total_allowances'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary'),
        )

        context.update({
            'title': f"مسير {payroll.number}",
            'details': details,
            'stats': stats,
            'process_form': PayrollProcessForm(company=self.request.current_company),
            'approve_form': PayrollApproveForm(),
            'payment_form': PayrollPaymentForm(),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': payroll.number, 'url': None},
            ],
        })
        return context


class PayrollUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل مسير الرواتب"""
    model = Payroll
    form_class = PayrollForm
    template_name = 'hr/payroll/payroll_form.html'
    permission_required = 'hr.change_payroll'

    def get_queryset(self):
        return Payroll.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم تحديث مسير الرواتب بنجاح'))
        return response

    def get_success_url(self):
        return reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل مسير الرواتب'),
            'submit_text': _('حفظ التعديلات'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': self.object.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': None},
            ],
        })
        return context


class PayrollDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف مسير الرواتب"""
    model = Payroll
    template_name = 'hr/payroll/payroll_confirm_delete.html'
    permission_required = 'hr.delete_payroll'
    success_url = reverse_lazy('hr:payroll_list')

    def get_queryset(self):
        return Payroll.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف مسير الرواتب بنجاح'))
        return super().delete(request, *args, **kwargs)


class PayrollProcessView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """معالجة مسير الرواتب - إضافة الموظفين وحساب الرواتب"""
    template_name = 'hr/payroll/payroll_process.html'
    permission_required = 'hr.change_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=self.request.current_company,
            status='draft'
        )

        context.update({
            'title': _('معالجة مسير الرواتب'),
            'payroll': payroll,
            'process_form': PayrollProcessForm(company=self.request.current_company),
            'bulk_form': BulkPayrollDetailForm(
                company=self.request.current_company,
                payroll=payroll
            ),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': payroll.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': payroll.pk})},
                {'title': _('معالجة'), 'url': None},
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=request.current_company,
            status='draft'
        )

        action = request.POST.get('action')

        if action == 'add_all':
            # إضافة جميع الموظفين
            employees = Employee.objects.filter(
                company=request.current_company,
                is_active=True,
                status='active'
            ).exclude(
                id__in=payroll.details.values_list('employee_id', flat=True)
            )

            count = 0
            for emp in employees:
                self._create_payroll_detail(payroll, emp)
                count += 1

            payroll.calculate_totals()
            messages.success(request, _(f'تم إضافة {count} موظف إلى المسير'))

        elif action == 'add_selected':
            # إضافة موظفين محددين
            form = BulkPayrollDetailForm(
                request.POST,
                company=request.current_company,
                payroll=payroll
            )
            if form.is_valid():
                employees = form.cleaned_data['employees']
                count = 0
                for emp in employees:
                    self._create_payroll_detail(payroll, emp)
                    count += 1
                payroll.calculate_totals()
                messages.success(request, _(f'تم إضافة {count} موظف إلى المسير'))

        elif action == 'recalculate':
            # إعادة حساب جميع الرواتب
            for detail in payroll.details.all():
                self._calculate_detail(detail, payroll)
            payroll.calculate_totals()
            messages.success(request, _('تم إعادة حساب جميع الرواتب'))

        return redirect('hr:payroll_detail', pk=payroll.pk)

    def _create_payroll_detail(self, payroll, employee):
        """إنشاء تفاصيل راتب للموظف"""
        # الحصول على العقد النشط
        contract = EmployeeContract.objects.filter(
            employee=employee,
            status='active'
        ).first()

        if not contract:
            return None

        detail = PayrollDetail.objects.create(
            payroll=payroll,
            employee=employee,
            basic_salary=contract.basic_salary,
            housing_allowance=contract.housing_allowance or 0,
            transport_allowance=contract.transport_allowance or 0,
            phone_allowance=contract.phone_allowance or 0,
            working_days=30,
            actual_days=30,
        )

        self._calculate_detail(detail, payroll)
        return detail

    def _calculate_detail(self, detail, payroll):
        """حساب تفاصيل الراتب"""
        company = payroll.company
        employee = detail.employee

        # الحصول على إعدادات HR
        try:
            hr_settings = HRSettings.objects.get(company=company)
        except HRSettings.DoesNotExist:
            hr_settings = None

        # حساب الحضور والغياب
        attendance = Attendance.objects.filter(
            employee=employee,
            date__range=[payroll.from_date, payroll.to_date]
        ).aggregate(
            total_days=Count('id'),
            absent_days=Count('id', filter=Q(status='absent')),
            late_minutes=Sum('late_minutes'),
        )

        detail.actual_days = attendance['total_days'] or detail.working_days
        detail.absent_days = attendance['absent_days'] or 0

        # حساب خصم الغياب
        if detail.absent_days > 0 and detail.working_days > 0:
            daily_rate = detail.basic_salary / Decimal(detail.working_days)
            detail.absence_deduction = daily_rate * Decimal(detail.absent_days)

        # حساب العمل الإضافي
        overtime = Overtime.objects.filter(
            employee=employee,
            date__range=[payroll.from_date, payroll.to_date],
            status='approved'
        ).aggregate(
            total_hours=Sum('hours'),
            total_amount=Sum('amount'),
        )

        detail.overtime_hours = overtime['total_hours'] or 0
        detail.overtime_amount = overtime['total_amount'] or 0

        # حساب أقساط السلف
        loan_deduction = Decimal('0')
        pending_installments = AdvanceInstallment.objects.filter(
            advance__employee=employee,
            advance__status='disbursed',
            status='pending',
            due_date__lte=payroll.to_date
        )

        for installment in pending_installments:
            loan_deduction += installment.amount

        detail.loan_deduction = loan_deduction

        # حساب الضمان الاجتماعي
        if hr_settings and hr_settings.social_security_enabled:
            gross = detail.basic_salary + detail.total_allowances
            detail.social_security_employee = gross * (hr_settings.employee_ss_rate / Decimal('100'))
            detail.social_security_company = gross * (hr_settings.company_ss_rate / Decimal('100'))

        detail.save()


class PayrollApproveView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """اعتماد مسير الرواتب"""
    template_name = 'hr/payroll/payroll_approve.html'
    permission_required = 'hr.approve_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=self.request.current_company,
            status='calculated'
        )

        context.update({
            'title': _('اعتماد مسير الرواتب'),
            'payroll': payroll,
            'form': PayrollApproveForm(),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': payroll.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': payroll.pk})},
                {'title': _('اعتماد'), 'url': None},
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=request.current_company,
            status='calculated'
        )

        form = PayrollApproveForm(request.POST)
        if form.is_valid():
            payroll.status = 'approved'
            payroll.approved_by = request.user
            payroll.approval_date = timezone.now()
            payroll.save()

            # إنشاء قيد محاسبي
            if form.cleaned_data.get('create_journal_entry'):
                self._create_journal_entry(payroll)

            messages.success(request, _('تم اعتماد مسير الرواتب بنجاح'))
            return redirect('hr:payroll_detail', pk=payroll.pk)

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

    def _create_journal_entry(self, payroll):
        """إنشاء القيد المحاسبي للرواتب"""
        # TODO: تنفيذ إنشاء القيد المحاسبي
        pass


class PayrollPaymentView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """صرف الرواتب"""
    template_name = 'hr/payroll/payroll_payment.html'
    permission_required = 'hr.pay_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=self.request.current_company,
            status='approved'
        )

        context.update({
            'title': _('صرف الرواتب'),
            'payroll': payroll,
            'form': PayrollPaymentForm(),
            'unpaid_details': payroll.details.filter(is_paid=False),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': payroll.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': payroll.pk})},
                {'title': _('صرف'), 'url': None},
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=request.current_company,
            status='approved'
        )

        form = PayrollPaymentForm(request.POST)
        if form.is_valid():
            payment_date = form.cleaned_data['payment_date']
            payment_method = form.cleaned_data['payment_method']
            payment_reference = form.cleaned_data.get('payment_reference', '')

            # تحديث تفاصيل الرواتب
            updated = payroll.details.filter(is_paid=False).update(
                is_paid=True,
                paid_date=payment_date,
                payment_method=payment_method,
                payment_reference=payment_reference
            )

            # تحديث حالة المسير
            if not payroll.details.filter(is_paid=False).exists():
                payroll.status = 'paid'
                payroll.save()

            # تحديث أقساط السلف
            for detail in payroll.details.all():
                AdvanceInstallment.objects.filter(
                    advance__employee=detail.employee,
                    advance__status='disbursed',
                    status='pending',
                    due_date__lte=payroll.to_date
                ).update(
                    status='paid',
                    paid_date=payment_date
                )

            messages.success(request, _(f'تم صرف {updated} راتب بنجاح'))
            return redirect('hr:payroll_detail', pk=payroll.pk)

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class PayrollDetailEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل تفاصيل راتب موظف"""
    model = PayrollDetail
    form_class = PayrollDetailForm
    template_name = 'hr/payroll/payroll_detail_form.html'
    permission_required = 'hr.change_payrolldetail'

    def get_queryset(self):
        return PayrollDetail.objects.filter(
            payroll__company=self.request.current_company,
            payroll__status='draft'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['payroll'] = self.object.payroll
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.payroll.calculate_totals()
        messages.success(self.request, _('تم تحديث تفاصيل الراتب بنجاح'))
        return response

    def get_success_url(self):
        return reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.payroll.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل راتب الموظف'),
            'submit_text': _('حفظ التعديلات'),
            'payroll': self.object.payroll,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': self.object.payroll.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.payroll.pk})},
                {'title': str(self.object.employee), 'url': None},
            ],
        })
        return context


class PayrollDetailDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف تفاصيل راتب موظف من الكشف"""
    model = PayrollDetail
    template_name = 'hr/payroll/payroll_detail_confirm_delete.html'
    permission_required = 'hr.delete_payrolldetail'

    def get_queryset(self):
        return PayrollDetail.objects.filter(
            payroll__company=self.request.current_company,
            payroll__status='draft'
        )

    def get_success_url(self):
        return reverse_lazy('hr:payroll_detail', kwargs={'pk': self.object.payroll.pk})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        payroll = self.object.payroll
        response = super().delete(request, *args, **kwargs)
        payroll.calculate_totals()
        messages.success(request, _('تم حذف الموظف من الكشف بنجاح'))
        return response


class PayslipView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض كشف راتب الموظف"""
    model = PayrollDetail
    template_name = 'hr/payroll/payslip.html'
    permission_required = 'hr.view_payrolldetail'
    context_object_name = 'payslip'

    def get_queryset(self):
        return PayrollDetail.objects.filter(
            payroll__company=self.request.current_company
        ).select_related('payroll', 'employee')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = self.object

        context.update({
            'title': _('كشف الراتب'),
            'company': self.request.current_company,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('كشوفات الرواتب'), 'url': reverse_lazy('hr:payroll_list')},
                {'title': detail.payroll.number, 'url': reverse_lazy('hr:payroll_detail', kwargs={'pk': detail.payroll.pk})},
                {'title': _('كشف الراتب'), 'url': None},
            ],
        })
        return context


class PayrollReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """تقارير الرواتب"""
    template_name = 'hr/payroll/payroll_report.html'
    permission_required = 'hr.view_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سنوية
        current_year = date.today().year
        yearly_stats = Payroll.objects.filter(
            company=company,
            period_year=current_year,
            status__in=['approved', 'paid']
        ).aggregate(
            total_basic=Sum('total_basic'),
            total_allowances=Sum('total_allowances'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('total_net'),
            total_employees=Sum('employee_count'),
        )

        # إحصائيات شهرية
        monthly_data = Payroll.objects.filter(
            company=company,
            period_year=current_year,
            status__in=['approved', 'paid']
        ).values('period_month').annotate(
            total=Sum('total_net'),
            count=Count('id')
        ).order_by('period_month')

        context.update({
            'title': _('تقارير الرواتب'),
            'yearly_stats': yearly_stats,
            'monthly_data': list(monthly_data),
            'current_year': current_year,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('تقارير الرواتب'), 'url': None},
            ],
        })
        return context

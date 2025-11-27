# apps/hr/views/self_service_views.py
"""
بوابة الخدمة الذاتية للموظفين
Employee Self-Service Portal Views
"""

from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import datetime, timedelta

from ..models import (
    Employee, Attendance, LeaveRequest, LeaveBalance, LeaveType,
    Payroll, PayrollDetail, EmployeeContract, Advance, AdvanceInstallment
)


class EmployeeSelfServiceMixin:
    """Mixin للتحقق من أن المستخدم موظف"""

    def get_employee(self):
        """الحصول على سجل الموظف للمستخدم الحالي"""
        try:
            # أولاً: البحث عن موظف مرتبط بالمستخدم
            return Employee.objects.get(
                user=self.request.user,
                company=self.request.current_company,
                is_active=True
            )
        except Employee.DoesNotExist:
            # ثانياً: للمدراء - البحث عن أي موظف للعرض
            if self.request.user.is_superuser or self.request.user.is_staff:
                employee = Employee.objects.filter(
                    company=self.request.current_company,
                    is_active=True
                ).first()
                return employee
            return None

    def dispatch(self, request, *args, **kwargs):
        if not self.get_employee():
            messages.error(request, 'لا يوجد سجل موظف مرتبط بحسابك. يرجى ربط حسابك بموظف من صفحة الموظفين.')
            return redirect('hr:employee_list')
        return super().dispatch(request, *args, **kwargs)


class SelfServiceDashboardView(LoginRequiredMixin, EmployeeSelfServiceMixin, TemplateView):
    """لوحة معلومات الخدمة الذاتية"""
    template_name = 'hr/self_service/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month

        context['title'] = 'الخدمة الذاتية'
        context['employee'] = employee
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': None}
        ]

        # معلومات الحضور لهذا الشهر
        month_start = today.replace(day=1)
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__gte=month_start,
            date__lte=today
        )
        context['attendance_stats'] = {
            'present_days': attendance_records.filter(status='present').count(),
            'absent_days': attendance_records.filter(status='absent').count(),
            'late_days': attendance_records.filter(late_minutes__gt=0).count(),
            'total_work_hours': attendance_records.aggregate(
                total=Sum('working_hours')
            )['total'] or 0
        }

        # أرصدة الإجازات
        leave_balances = LeaveBalance.objects.filter(
            employee=employee,
            year=current_year
        ).select_related('leave_type')
        context['leave_balances'] = leave_balances

        # طلبات الإجازات الأخيرة
        context['recent_leave_requests'] = LeaveRequest.objects.filter(
            employee=employee
        ).order_by('-created_at')[:5]

        # معلومات العقد
        context['current_contract'] = EmployeeContract.objects.filter(
            employee=employee,
            status='active'
        ).first()

        # السلف النشطة
        context['active_advances'] = Advance.objects.filter(
            employee=employee,
            status__in=['approved', 'partially_paid']
        )

        # آخر كشف راتب
        try:
            latest_payroll = PayrollDetail.objects.filter(
                employee=employee,
                payroll__status='paid'
            ).order_by('-payroll__year', '-payroll__month').first()
            context['latest_payroll'] = latest_payroll
        except:
            context['latest_payroll'] = None

        return context


class SelfServiceAttendanceView(LoginRequiredMixin, EmployeeSelfServiceMixin, ListView):
    """سجل حضور الموظف"""
    template_name = 'hr/self_service/attendance.html'
    context_object_name = 'attendance_records'
    paginate_by = 31

    def get_queryset(self):
        employee = self.get_employee()
        year = self.request.GET.get('year', timezone.now().year)
        month = self.request.GET.get('month', timezone.now().month)

        return Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        context['title'] = 'سجل الحضور'
        context['employee'] = employee
        context['current_year'] = year
        context['current_month'] = month
        context['years'] = range(timezone.now().year - 2, timezone.now().year + 1)
        context['months'] = [
            (1, 'يناير'), (2, 'فبراير'), (3, 'مارس'), (4, 'أبريل'),
            (5, 'مايو'), (6, 'يونيو'), (7, 'يوليو'), (8, 'أغسطس'),
            (9, 'سبتمبر'), (10, 'أكتوبر'), (11, 'نوفمبر'), (12, 'ديسمبر')
        ]
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'سجل الحضور', 'url': None}
        ]

        # إحصائيات
        records = self.get_queryset()
        context['stats'] = {
            'total_days': records.count(),
            'present': records.filter(status='present').count(),
            'absent': records.filter(status='absent').count(),
            'late': records.filter(late_minutes__gt=0).count(),
            'total_hours': records.aggregate(total=Sum('working_hours'))['total'] or 0,
            'overtime_hours': records.aggregate(total=Sum('overtime_hours'))['total'] or 0,
        }

        return context


class SelfServiceLeaveBalanceView(LoginRequiredMixin, EmployeeSelfServiceMixin, TemplateView):
    """أرصدة إجازات الموظف"""
    template_name = 'hr/self_service/leave_balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        year = int(self.request.GET.get('year', timezone.now().year))

        context['title'] = 'أرصدة الإجازات'
        context['employee'] = employee
        context['current_year'] = year
        context['years'] = range(timezone.now().year - 2, timezone.now().year + 1)
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'أرصدة الإجازات', 'url': None}
        ]

        # أرصدة الإجازات
        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=year
        ).select_related('leave_type')

        balance_data = []
        for balance in balances:
            total = (balance.opening_balance or 0) + (balance.carried_forward or 0) + (balance.adjustment or 0)
            used = balance.used or 0
            remaining = total - used
            balance_data.append({
                'leave_type': balance.leave_type,
                'total': total,
                'used': used,
                'remaining': remaining,
                'percentage': (used / total * 100) if total > 0 else 0
            })

        context['balances'] = balance_data

        return context


class SelfServiceLeaveRequestListView(LoginRequiredMixin, EmployeeSelfServiceMixin, ListView):
    """طلبات إجازات الموظف"""
    template_name = 'hr/self_service/leave_requests.html'
    context_object_name = 'leave_requests'
    paginate_by = 20

    def get_queryset(self):
        employee = self.get_employee()
        return LeaveRequest.objects.filter(
            employee=employee
        ).select_related('leave_type').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'طلبات الإجازات'
        context['employee'] = self.get_employee()
        context['leave_types'] = LeaveType.objects.filter(
            company=self.request.current_company,
            is_active=True
        )
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'طلبات الإجازات', 'url': None}
        ]
        return context


class SelfServiceLeaveRequestCreateView(LoginRequiredMixin, EmployeeSelfServiceMixin, CreateView):
    """تقديم طلب إجازة"""
    model = LeaveRequest
    template_name = 'hr/self_service/leave_request_form.html'
    fields = ['leave_type', 'start_date', 'end_date', 'reason']
    success_url = reverse_lazy('hr:self_service_leave_requests')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['leave_type'].queryset = LeaveType.objects.filter(
            company=self.request.current_company,
            is_active=True
        )
        return form

    def form_valid(self, form):
        employee = self.get_employee()
        form.instance.employee = employee
        form.instance.company = self.request.current_company
        form.instance.status = 'pending'
        form.instance.created_by = self.request.user

        # حساب عدد الأيام
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        form.instance.days = (end_date - start_date).days + 1

        messages.success(self.request, 'تم تقديم طلب الإجازة بنجاح')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'طلب إجازة جديد'
        context['employee'] = self.get_employee()
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'طلبات الإجازات', 'url': '/hr/self-service/leave-requests/'},
            {'title': 'طلب جديد', 'url': None}
        ]
        return context


class SelfServicePayslipListView(LoginRequiredMixin, EmployeeSelfServiceMixin, ListView):
    """كشوف رواتب الموظف"""
    template_name = 'hr/self_service/payslips.html'
    context_object_name = 'payslips'
    paginate_by = 12

    def get_queryset(self):
        employee = self.get_employee()
        return PayrollDetail.objects.filter(
            employee=employee,
            payroll__status__in=['approved', 'paid']
        ).select_related('payroll').order_by('-payroll__year', '-payroll__month')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'كشوف الرواتب'
        context['employee'] = self.get_employee()
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'كشوف الرواتب', 'url': None}
        ]
        return context


class SelfServicePayslipDetailView(LoginRequiredMixin, EmployeeSelfServiceMixin, DetailView):
    """تفاصيل كشف الراتب"""
    model = PayrollDetail
    template_name = 'hr/self_service/payslip_detail.html'
    context_object_name = 'payslip'

    def get_queryset(self):
        employee = self.get_employee()
        return PayrollDetail.objects.filter(
            employee=employee,
            payroll__status__in=['approved', 'paid']
        ).select_related('payroll')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payslip = self.object
        context['title'] = f'كشف راتب {payslip.payroll.get_month_display()} {payslip.payroll.year}'
        context['employee'] = self.get_employee()
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'كشوف الرواتب', 'url': '/hr/self-service/payslips/'},
            {'title': context['title'], 'url': None}
        ]
        return context


class SelfServiceAdvanceListView(LoginRequiredMixin, EmployeeSelfServiceMixin, ListView):
    """سلف الموظف"""
    template_name = 'hr/self_service/advances.html'
    context_object_name = 'advances'
    paginate_by = 10

    def get_queryset(self):
        employee = self.get_employee()
        return Advance.objects.filter(
            employee=employee
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()

        context['title'] = 'السلف'
        context['employee'] = employee
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'السلف', 'url': None}
        ]

        # إجمالي السلف النشطة
        active_advances = Advance.objects.filter(
            employee=employee,
            status__in=['approved', 'partially_paid']
        )
        context['total_active_advances'] = active_advances.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # إجمالي المتبقي
        total_remaining = 0
        for advance in active_advances:
            paid = AdvanceInstallment.objects.filter(
                advance=advance,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or 0
            total_remaining += (advance.amount - paid)
        context['total_remaining'] = total_remaining

        return context


class SelfServiceProfileView(LoginRequiredMixin, EmployeeSelfServiceMixin, TemplateView):
    """الملف الشخصي للموظف"""
    template_name = 'hr/self_service/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()

        context['title'] = 'الملف الشخصي'
        context['employee'] = employee
        context['breadcrumbs'] = [
            {'title': 'الخدمة الذاتية', 'url': '/hr/self-service/'},
            {'title': 'الملف الشخصي', 'url': None}
        ]

        # العقد الحالي
        context['current_contract'] = EmployeeContract.objects.filter(
            employee=employee,
            status='active'
        ).first()

        return context


__all__ = [
    'SelfServiceDashboardView',
    'SelfServiceAttendanceView',
    'SelfServiceLeaveBalanceView',
    'SelfServiceLeaveRequestListView',
    'SelfServiceLeaveRequestCreateView',
    'SelfServicePayslipListView',
    'SelfServicePayslipDetailView',
    'SelfServiceAdvanceListView',
    'SelfServiceProfileView',
]

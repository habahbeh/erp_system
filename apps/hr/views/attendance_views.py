# apps/hr/views/attendance_views.py
"""
عروض الحضور والانصراف - Attendance Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Count, Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta

from ..models import Attendance, Employee, Department
from ..forms import AttendanceForm, BulkAttendanceForm


class AttendanceListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة سجلات الحضور"""
    template_name = 'hr/attendance/attendance_list.html'
    permission_required = 'hr.view_attendance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات اليوم
        today = date.today()
        today_stats = Attendance.objects.filter(
            company=company,
            date=today
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
            leave=Count('id', filter=Q(status='leave')),
        )

        # عدد الموظفين النشطين
        active_employees = Employee.objects.filter(
            company=company,
            is_active=True,
            status='active'
        ).count()

        context.update({
            'title': _('سجلات الحضور'),
            'today_stats': today_stats,
            'active_employees': active_employees,
            'departments': Department.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': ''}
            ],
        })
        return context


class AttendanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """تسجيل حضور"""
    model = Attendance
    form_class = AttendanceForm
    template_name = 'hr/attendance/attendance_form.html'
    permission_required = 'hr.add_attendance'
    success_url = reverse_lazy('hr:attendance_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم تسجيل الحضور بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تسجيل حضور'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': reverse('hr:attendance_list')},
                {'title': _('تسجيل'), 'url': ''}
            ],
        })
        return context


class AttendanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل سجل حضور"""
    model = Attendance
    form_class = AttendanceForm
    template_name = 'hr/attendance/attendance_form.html'
    permission_required = 'hr.change_attendance'
    success_url = reverse_lazy('hr:attendance_list')

    def get_queryset(self):
        return Attendance.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث سجل الحضور بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل سجل حضور'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': reverse('hr:attendance_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class AttendanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف سجل حضور"""
    model = Attendance
    template_name = 'hr/attendance/attendance_confirm_delete.html'
    permission_required = 'hr.delete_attendance'
    success_url = reverse_lazy('hr:attendance_list')

    def get_queryset(self):
        return Attendance.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف سجل الحضور بنجاح'))
        return super().delete(request, *args, **kwargs)


class BulkAttendanceView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """تسجيل حضور جماعي"""
    template_name = 'hr/attendance/bulk_attendance.html'
    permission_required = 'hr.add_attendance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        context.update({
            'title': _('تسجيل حضور جماعي'),
            'form': BulkAttendanceForm(company=company),
            'employees': Employee.objects.filter(
                company=company,
                is_active=True,
                status='active'
            ).select_related('department', 'job_title').order_by('department', 'first_name'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': reverse('hr:attendance_list')},
                {'title': _('تسجيل جماعي'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        company = request.current_company
        attendance_date = request.POST.get('date')
        employees_data = request.POST.getlist('employees')

        created_count = 0
        updated_count = 0

        for emp_id in employees_data:
            check_in = request.POST.get(f'check_in_{emp_id}')
            check_out = request.POST.get(f'check_out_{emp_id}')
            status = request.POST.get(f'status_{emp_id}', 'present')

            if check_in:
                attendance, created = Attendance.objects.update_or_create(
                    company=company,
                    employee_id=emp_id,
                    date=attendance_date,
                    defaults={
                        'check_in': check_in if check_in else None,
                        'check_out': check_out if check_out else None,
                        'status': status,
                        'branch': request.current_branch,
                        'created_by': request.user,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        messages.success(
            request,
            _('تم تسجيل %(created)s سجل جديد وتحديث %(updated)s سجل') % {
                'created': created_count,
                'updated': updated_count
            }
        )
        return redirect('hr:attendance_list')


class AttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """تقرير الحضور"""
    template_name = 'hr/attendance/attendance_report.html'
    permission_required = 'hr.view_attendance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # الفترة الافتراضية: الشهر الحالي
        today = date.today()
        from_date_str = self.request.GET.get('from_date', today.replace(day=1).isoformat())
        to_date_str = self.request.GET.get('to_date', today.isoformat())
        department_id = self.request.GET.get('department')

        # Convert strings to date objects
        from datetime import datetime
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

        # Calculate total working days
        total_days = (to_date - from_date).days + 1

        # Base queryset for attendance
        attendance_qs = Attendance.objects.filter(
            company=company,
            date__gte=from_date,
            date__lte=to_date
        )

        # Filter by department if selected
        if department_id:
            attendance_qs = attendance_qs.filter(employee__department_id=department_id)

        # Report statistics
        report_stats = {
            'total_days': total_days,
            'present_count': attendance_qs.filter(status='present').count(),
            'absent_count': attendance_qs.filter(status='absent').count(),
            'late_count': attendance_qs.filter(status='late').count(),
            'leave_count': attendance_qs.filter(status='leave').count(),
        }

        # Calculate total hours
        total_hours = 0
        for att in attendance_qs.filter(check_in__isnull=False, check_out__isnull=False):
            if att.check_in and att.check_out:
                # Calculate hours between check_in and check_out
                check_in_datetime = datetime.combine(att.date, att.check_in)
                check_out_datetime = datetime.combine(att.date, att.check_out)
                hours = (check_out_datetime - check_in_datetime).total_seconds() / 3600
                total_hours += hours

        report_stats['total_hours'] = round(total_hours, 1)

        # Daily attendance data for chart
        from collections import defaultdict
        daily_counts = defaultdict(int)

        for att in attendance_qs.filter(status='present'):
            daily_counts[att.date.isoformat()] += 1

        # Generate all dates in range
        current_date = from_date
        daily_labels = []
        daily_data = []

        while current_date <= to_date:
            date_str = current_date.isoformat()
            daily_labels.append(date_str)
            daily_data.append(daily_counts.get(date_str, 0))
            current_date += timedelta(days=1)

        # Employee summary
        from django.db.models import Case, When, IntegerField, F, ExpressionWrapper, fields

        # Get all employees with attendance in the period
        employee_ids = attendance_qs.values_list('employee_id', flat=True).distinct()

        employee_summary = []
        for emp_id in employee_ids:
            emp_attendance = attendance_qs.filter(employee_id=emp_id)
            employee = Employee.objects.get(id=emp_id)

            present_days = emp_attendance.filter(status='present').count()
            absent_days = emp_attendance.filter(status='absent').count()
            late_days = emp_attendance.filter(status='late').count()
            leave_days = emp_attendance.filter(status='leave').count()

            # Calculate total hours for this employee
            emp_hours = 0
            for att in emp_attendance.filter(check_in__isnull=False, check_out__isnull=False):
                if att.check_in and att.check_out:
                    check_in_datetime = datetime.combine(att.date, att.check_in)
                    check_out_datetime = datetime.combine(att.date, att.check_out)
                    hours = (check_out_datetime - check_in_datetime).total_seconds() / 3600
                    emp_hours += hours

            employee_summary.append({
                'employee__full_name': employee.full_name,
                'employee__employee_number': employee.employee_number,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'leave_days': leave_days,
                'total_hours': round(emp_hours, 1),
                'total_days': total_days,
            })

        import json
        context.update({
            'title': _('تقرير الحضور'),
            'from_date': from_date_str,
            'to_date': to_date_str,
            'departments': Department.objects.filter(company=company, is_active=True),
            'report_stats': report_stats,
            'daily_labels': json.dumps(daily_labels),
            'daily_data': json.dumps(daily_data),
            'employee_summary': employee_summary,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': reverse('hr:attendance_list')},
                {'title': _('التقرير'), 'url': ''}
            ],
        })
        return context

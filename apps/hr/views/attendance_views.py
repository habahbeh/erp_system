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
        start_date = self.request.GET.get('start_date', today.replace(day=1).isoformat())
        end_date = self.request.GET.get('end_date', today.isoformat())

        context.update({
            'title': _('تقرير الحضور'),
            'start_date': start_date,
            'end_date': end_date,
            'departments': Department.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الحضور'), 'url': reverse('hr:attendance_list')},
                {'title': _('التقرير'), 'url': ''}
            ],
        })
        return context

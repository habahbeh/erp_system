# apps/hr/views/employee_views.py
"""
عروض الموظفين
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q, Count, Sum
from django.utils.translation import gettext_lazy as _

from ..models import (
    Department, JobGrade, JobTitle, Employee,
    EmployeeContract, SalaryIncrement, EmployeeDocument
)
from ..forms import EmployeeForm


class EmployeeListView(LoginRequiredMixin, TemplateView):
    """قائمة الموظفين"""
    template_name = 'hr/employees/employee_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = Employee.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            inactive=Count('id', filter=Q(status='inactive')),
            on_leave=Count('id', filter=Q(status='on_leave')),
            terminated=Count('id', filter=Q(status='terminated')),
            total_salaries=Sum('basic_salary', filter=Q(status='active')),
        )

        # الأقسام للفلترة
        departments = Department.objects.filter(
            company=company,
            is_active=True
        )

        context.update({
            'title': _('الموظفين'),
            'can_add': self.request.user.has_perm('hr.add_employee'),
            'can_edit': self.request.user.has_perm('hr.change_employee'),
            'can_delete': self.request.user.has_perm('hr.delete_employee'),
            'can_view': self.request.user.has_perm('hr.view_employee'),
            'stats': stats,
            'departments': departments,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الموظفين'), 'url': ''}
            ],
        })
        return context


class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء موظف جديد"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employees/employee_form.html'
    permission_required = 'hr.add_employee'
    success_url = reverse_lazy('hr:employee_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة الموظف بنجاح'))
        return super().form_valid(form)

    def get_success_url(self):
        if 'save_and_add' in self.request.POST:
            return reverse('hr:employee_create')
        return reverse('hr:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة موظف جديد'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الموظفين'), 'url': reverse('hr:employee_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل موظف"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employees/employee_form.html'
    permission_required = 'hr.change_employee'
    success_url = reverse_lazy('hr:employee_list')

    def get_queryset(self):
        return Employee.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث بيانات الموظف بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل بيانات الموظف'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الموظفين'), 'url': reverse('hr:employee_list')},
                {'title': f'تعديل: {self.object.get_full_name()}', 'url': ''}
            ],
        })
        return context


class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف موظف"""
    model = Employee
    template_name = 'hr/employees/employee_confirm_delete.html'
    permission_required = 'hr.delete_employee'
    success_url = reverse_lazy('hr:employee_list')

    def get_queryset(self):
        return Employee.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود عقود أو سجلات مرتبطة
        if self.object.contracts.exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف الموظف لوجود عقود مرتبطة'
                }, status=400)
            messages.error(request, 'لا يمكن حذف الموظف لوجود عقود مرتبطة')
            return redirect('hr:employee_list')

        employee_name = self.object.get_full_name()
        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف الموظف {employee_name} بنجاح'
            })

        messages.success(request, f'تم حذف الموظف {employee_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف الموظف')
        return context


class EmployeeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل الموظف"""
    model = Employee
    template_name = 'hr/employees/employee_detail.html'
    context_object_name = 'employee'
    permission_required = 'hr.view_employee'

    def get_queryset(self):
        return Employee.objects.filter(
            company=self.request.current_company
        ).select_related('department', 'job_title', 'job_grade', 'branch', 'manager', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object

        # إحصائيات الموظف
        employee_stats = {
            'contracts_count': employee.contracts.count(),
            'documents_count': employee.documents.count() if hasattr(employee, 'documents') else 0,
            'increments_count': employee.salary_increments.count(),
            'total_increments': employee.salary_increments.filter(status='applied').aggregate(
                total=Sum('increment_amount')
            )['total'] or 0,
        }

        context.update({
            'title': f'{employee.get_full_name()}',
            'can_edit': self.request.user.has_perm('hr.change_employee'),
            'can_delete': self.request.user.has_perm('hr.delete_employee'),
            'employee_stats': employee_stats,
            'contracts': employee.contracts.all().order_by('-start_date')[:5],
            'documents': employee.documents.all().order_by('-created_at')[:5] if hasattr(employee, 'documents') else [],
            'increments': employee.salary_increments.all().order_by('-effective_date')[:5],
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الموظفين'), 'url': reverse('hr:employee_list')},
                {'title': employee.get_full_name(), 'url': ''}
            ],
        })
        return context

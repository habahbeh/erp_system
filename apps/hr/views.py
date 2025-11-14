# apps/hr/views.py
"""
عروض الموارد البشرية
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Department, Employee
from .forms import EmployeeForm
from apps.core.models import User


# ============================================
# عروض الأقسام
# ============================================

class DepartmentListView(LoginRequiredMixin, ListView):
    """قائمة الأقسام"""
    model = Department
    template_name = 'hr/departments/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Department.objects.filter(
            company=self.request.current_company
        ).select_related('parent', 'manager').order_by('code')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الأقسام')
        context['search'] = self.request.GET.get('search', '')
        return context


class DepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء قسم جديد"""
    model = Department
    template_name = 'hr/departments/department_form.html'
    fields = ['code', 'name', 'parent', 'manager']
    permission_required = 'hr.add_department'
    success_url = reverse_lazy('hr:department_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تصفية الأقسام الأب حسب الشركة
        form.fields['parent'].queryset = Department.objects.filter(
            company=self.request.current_company,
            is_active=True
        )
        form.fields['parent'].required = False

        # تصفية المديرين حسب الشركة
        # ملاحظة: سنجعل حقل المدير اختياري لأن Employee قد لا يكون معرف بعد
        form.fields['manager'].required = False
        form.fields['manager'].queryset = form.fields['manager'].queryset.none()  # سنعطله مؤقتاً

        # إضافة classes للحقول
        for field_name, field in form.fields.items():
            if field_name != 'manager':  # نخفي حقل المدير مؤقتاً
                field.widget.attrs.update({
                    'class': 'form-control'
                })

        return form

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            _('تم إضافة القسم بنجاح')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة قسم جديد')
        context['submit_text'] = _('حفظ')
        return context


class DepartmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل قسم"""
    model = Department
    template_name = 'hr/departments/department_form.html'
    fields = ['code', 'name', 'parent', 'manager', 'is_active']
    permission_required = 'hr.change_department'
    success_url = reverse_lazy('hr:department_list')

    def get_queryset(self):
        return Department.objects.filter(
            company=self.request.current_company
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تصفية الأقسام الأب حسب الشركة (ومنع اختيار نفسه)
        form.fields['parent'].queryset = Department.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).exclude(pk=self.object.pk)
        form.fields['parent'].required = False

        # تصفية المديرين حسب الشركة
        form.fields['manager'].required = False
        form.fields['manager'].queryset = form.fields['manager'].queryset.none()  # سنعطله مؤقتاً

        # إضافة classes للحقول
        for field_name, field in form.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
            elif field_name != 'manager':
                field.widget.attrs.update({
                    'class': 'form-control'
                })

        return form

    def form_valid(self, form):
        messages.success(
            self.request,
            _('تم تحديث القسم بنجاح')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل القسم')
        context['submit_text'] = _('تحديث')
        return context


class DepartmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف قسم"""
    model = Department
    template_name = 'hr/departments/department_confirm_delete.html'
    permission_required = 'hr.delete_department'
    success_url = reverse_lazy('hr:department_list')

    def get_queryset(self):
        return Department.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        messages.success(
            self.request,
            _('تم حذف القسم بنجاح')
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف القسم')
        return context


# ============================================
# عروض الموظفين
# ============================================

class EmployeeListView(LoginRequiredMixin, ListView):
    """قائمة الموظفين"""
    model = Employee
    template_name = 'hr/employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = Employee.objects.filter(
            company=self.request.current_company
        ).select_related('department', 'job_title', 'user').order_by('-created_at')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee_number__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(national_id__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search)
            )

        # تصفية حسب القسم
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # تصفية حسب الحالة الوظيفية
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(employment_status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الموظفين')
        context['search'] = self.request.GET.get('search', '')
        context['departments'] = Department.objects.filter(
            company=self.request.current_company,
            is_active=True
        )
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_status'] = self.request.GET.get('status', '')
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
        messages.success(
            self.request,
            _('تم إضافة الموظف بنجاح')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة موظف جديد')
        context['submit_text'] = _('حفظ')
        return context


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل موظف"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employees/employee_form.html'
    permission_required = 'hr.change_employee'
    success_url = reverse_lazy('hr:employee_list')

    def get_queryset(self):
        return Employee.objects.filter(
            company=self.request.current_company
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            _('تم تحديث بيانات الموظف بنجاح')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل بيانات الموظف')
        context['submit_text'] = _('تحديث')
        return context


class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف موظف"""
    model = Employee
    template_name = 'hr/employees/employee_confirm_delete.html'
    permission_required = 'hr.delete_employee'
    success_url = reverse_lazy('hr:employee_list')

    def get_queryset(self):
        return Employee.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        messages.success(
            self.request,
            _('تم حذف الموظف بنجاح')
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف الموظف')
        return context

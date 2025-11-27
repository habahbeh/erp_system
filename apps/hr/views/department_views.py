# apps/hr/views/department_views.py
"""
عروض الأقسام والدرجات والمسميات الوظيفية
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _

from ..models import Department, JobGrade, JobTitle, Employee
from ..forms import JobGradeForm, JobTitleForm


# ============================================
# عروض الأقسام
# ============================================

class DepartmentListView(LoginRequiredMixin, TemplateView):
    """قائمة الأقسام"""
    template_name = 'hr/departments/department_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = Department.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            inactive=Count('id', filter=Q(is_active=False)),
            with_manager=Count('id', filter=Q(manager__isnull=False)),
        )

        context.update({
            'title': _('الأقسام'),
            'can_add': self.request.user.has_perm('hr.add_department'),
            'can_edit': self.request.user.has_perm('hr.change_department'),
            'can_delete': self.request.user.has_perm('hr.delete_department'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الأقسام'), 'url': ''}
            ],
        })
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
        form.fields['manager'].required = False
        form.fields['manager'].queryset = Employee.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        # إضافة classes للحقول
        for field_name, field in form.fields.items():
            if field_name == 'manager':
                field.widget.attrs.update({'class': 'form-select select2'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        return form

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة القسم بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة قسم جديد'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الأقسام'), 'url': reverse('hr:department_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class DepartmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل قسم"""
    model = Department
    template_name = 'hr/departments/department_form.html'
    fields = ['code', 'name', 'parent', 'manager', 'is_active']
    permission_required = 'hr.change_department'
    success_url = reverse_lazy('hr:department_list')

    def get_queryset(self):
        return Department.objects.filter(company=self.request.current_company)

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
        form.fields['manager'].queryset = Employee.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        # إضافة classes للحقول
        for field_name, field in form.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif field_name == 'manager':
                field.widget.attrs.update({'class': 'form-select select2'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        return form

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث القسم بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل القسم'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الأقسام'), 'url': reverse('hr:department_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''}
            ],
        })
        return context


class DepartmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف قسم"""
    model = Department
    template_name = 'hr/departments/department_confirm_delete.html'
    permission_required = 'hr.delete_department'
    success_url = reverse_lazy('hr:department_list')

    def get_queryset(self):
        return Department.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود أقسام فرعية أو موظفين
        if self.object.children.exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف القسم لوجود أقسام فرعية'
                }, status=400)
            messages.error(request, 'لا يمكن حذف القسم لوجود أقسام فرعية')
            return redirect('hr:department_list')

        if self.object.employees.exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف القسم لوجود موظفين مرتبطين'
                }, status=400)
            messages.error(request, 'لا يمكن حذف القسم لوجود موظفين مرتبطين')
            return redirect('hr:department_list')

        department_name = self.object.name
        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف القسم {department_name} بنجاح'
            })

        messages.success(request, f'تم حذف القسم {department_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف القسم')
        return context


# ============================================
# عروض الدرجات الوظيفية
# ============================================

class JobGradeListView(LoginRequiredMixin, TemplateView):
    """قائمة الدرجات الوظيفية"""
    template_name = 'hr/job_grades/job_grade_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = JobGrade.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
        )

        context.update({
            'title': _('الدرجات الوظيفية'),
            'can_add': self.request.user.has_perm('hr.add_jobgrade'),
            'can_edit': self.request.user.has_perm('hr.change_jobgrade'),
            'can_delete': self.request.user.has_perm('hr.delete_jobgrade'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الدرجات الوظيفية'), 'url': ''}
            ],
        })
        return context


class JobGradeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء درجة وظيفية جديدة"""
    model = JobGrade
    form_class = JobGradeForm
    template_name = 'hr/job_grades/job_grade_form.html'
    permission_required = 'hr.add_jobgrade'
    success_url = reverse_lazy('hr:job_grade_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة الدرجة الوظيفية بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة درجة وظيفية جديدة'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الدرجات الوظيفية'), 'url': reverse('hr:job_grade_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class JobGradeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل درجة وظيفية"""
    model = JobGrade
    form_class = JobGradeForm
    template_name = 'hr/job_grades/job_grade_form.html'
    permission_required = 'hr.change_jobgrade'
    success_url = reverse_lazy('hr:job_grade_list')

    def get_queryset(self):
        return JobGrade.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الدرجة الوظيفية بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل الدرجة الوظيفية'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الدرجات الوظيفية'), 'url': reverse('hr:job_grade_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''}
            ],
        })
        return context


class JobGradeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف درجة وظيفية"""
    model = JobGrade
    template_name = 'hr/job_grades/job_grade_confirm_delete.html'
    permission_required = 'hr.delete_jobgrade'
    success_url = reverse_lazy('hr:job_grade_list')

    def get_queryset(self):
        return JobGrade.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود موظفين مرتبطين
        if self.object.employees.exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف الدرجة الوظيفية لوجود موظفين مرتبطين'
                }, status=400)
            messages.error(request, 'لا يمكن حذف الدرجة الوظيفية لوجود موظفين مرتبطين')
            return redirect('hr:job_grade_list')

        grade_name = self.object.name
        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف الدرجة الوظيفية {grade_name} بنجاح'
            })

        messages.success(request, f'تم حذف الدرجة الوظيفية {grade_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف الدرجة الوظيفية')
        return context


# ============================================
# عروض المسميات الوظيفية
# ============================================

class JobTitleListView(LoginRequiredMixin, TemplateView):
    """قائمة المسميات الوظيفية"""
    template_name = 'hr/job_titles/job_title_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = JobTitle.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
        )

        # الأقسام للفلترة
        departments = Department.objects.filter(
            company=company,
            is_active=True
        )

        context.update({
            'title': _('المسميات الوظيفية'),
            'can_add': self.request.user.has_perm('hr.add_jobtitle'),
            'can_edit': self.request.user.has_perm('hr.change_jobtitle'),
            'can_delete': self.request.user.has_perm('hr.delete_jobtitle'),
            'stats': stats,
            'departments': departments,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المسميات الوظيفية'), 'url': ''}
            ],
        })
        return context


class JobTitleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء مسمى وظيفي جديد"""
    model = JobTitle
    form_class = JobTitleForm
    template_name = 'hr/job_titles/job_title_form.html'
    permission_required = 'hr.add_jobtitle'
    success_url = reverse_lazy('hr:job_title_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة المسمى الوظيفي بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة مسمى وظيفي جديد'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المسميات الوظيفية'), 'url': reverse('hr:job_title_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class JobTitleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل مسمى وظيفي"""
    model = JobTitle
    form_class = JobTitleForm
    template_name = 'hr/job_titles/job_title_form.html'
    permission_required = 'hr.change_jobtitle'
    success_url = reverse_lazy('hr:job_title_list')

    def get_queryset(self):
        return JobTitle.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث المسمى الوظيفي بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل المسمى الوظيفي'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المسميات الوظيفية'), 'url': reverse('hr:job_title_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''}
            ],
        })
        return context


class JobTitleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف مسمى وظيفي"""
    model = JobTitle
    template_name = 'hr/job_titles/job_title_confirm_delete.html'
    permission_required = 'hr.delete_jobtitle'
    success_url = reverse_lazy('hr:job_title_list')

    def get_queryset(self):
        return JobTitle.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود موظفين مرتبطين
        if self.object.employees.exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف المسمى الوظيفي لوجود موظفين مرتبطين'
                }, status=400)
            messages.error(request, 'لا يمكن حذف المسمى الوظيفي لوجود موظفين مرتبطين')
            return redirect('hr:job_title_list')

        title_name = self.object.name
        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف المسمى الوظيفي {title_name} بنجاح'
            })

        messages.success(request, f'تم حذف المسمى الوظيفي {title_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف المسمى الوظيفي')
        return context

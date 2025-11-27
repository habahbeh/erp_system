# apps/hr/views/contract_views.py
"""
عروض العقود والعلاوات وأنواع الإجازات
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
from django.utils import timezone
from datetime import timedelta

from ..models import (
    Employee, EmployeeContract, SalaryIncrement, LeaveType
)
from ..forms import EmployeeContractForm, SalaryIncrementForm, LeaveTypeForm


# ============================================
# عروض العقود
# ============================================

class ContractListView(LoginRequiredMixin, TemplateView):
    """قائمة عقود العمل"""
    template_name = 'hr/contracts/contract_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # حساب العقود التي ستنتهي خلال 30 يوم
        today = timezone.now().date()
        expiring_date = today + timedelta(days=30)

        # إحصائيات سريعة
        stats = EmployeeContract.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            draft=Count('id', filter=Q(status='draft')),
            expired=Count('id', filter=Q(status='expired')),
            terminated=Count('id', filter=Q(status='terminated')),
        )

        # العقود قاربت على الانتهاء
        stats['expiring_soon'] = EmployeeContract.objects.filter(
            company=company,
            status='active',
            end_date__gte=today,
            end_date__lte=expiring_date
        ).count()

        context.update({
            'title': _('عقود العمل'),
            'can_add': self.request.user.has_perm('hr.add_employeecontract'),
            'can_edit': self.request.user.has_perm('hr.change_employeecontract'),
            'can_delete': self.request.user.has_perm('hr.delete_employeecontract'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('عقود العمل'), 'url': ''}
            ],
        })
        return context


class ContractCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء عقد عمل جديد"""
    model = EmployeeContract
    form_class = EmployeeContractForm
    template_name = 'hr/contracts/contract_form.html'
    permission_required = 'hr.add_employeecontract'
    success_url = reverse_lazy('hr:contract_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # إذا تم تمرير employee_id من URL
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(
                    pk=employee_id,
                    company=self.request.current_company
                )
                initial['employee'] = employee
            except Employee.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة العقد بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة عقد عمل جديد'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('عقود العمل'), 'url': reverse('hr:contract_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class ContractUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عقد عمل"""
    model = EmployeeContract
    form_class = EmployeeContractForm
    template_name = 'hr/contracts/contract_form.html'
    permission_required = 'hr.change_employeecontract'
    success_url = reverse_lazy('hr:contract_list')

    def get_queryset(self):
        return EmployeeContract.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث العقد بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل عقد العمل'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('عقود العمل'), 'url': reverse('hr:contract_list')},
                {'title': f'تعديل: {self.object.contract_number or self.object.pk}', 'url': ''}
            ],
        })
        return context


class ContractDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف عقد عمل"""
    model = EmployeeContract
    template_name = 'hr/contracts/contract_confirm_delete.html'
    permission_required = 'hr.delete_employeecontract'
    success_url = reverse_lazy('hr:contract_list')

    def get_queryset(self):
        return EmployeeContract.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        contract_number = self.object.contract_number or str(self.object.pk)

        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف العقد {contract_number} بنجاح'
            })

        messages.success(request, f'تم حذف العقد {contract_number} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف عقد العمل')
        return context


class ContractDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل العقد"""
    model = EmployeeContract
    template_name = 'hr/contracts/contract_detail.html'
    context_object_name = 'contract'
    permission_required = 'hr.view_employeecontract'

    def get_queryset(self):
        return EmployeeContract.objects.filter(
            company=self.request.current_company
        ).select_related('employee', 'employee__department', 'employee__job_title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تفاصيل العقد: {self.object.contract_number or self.object.pk}',
            'can_edit': self.request.user.has_perm('hr.change_employeecontract'),
            'can_delete': self.request.user.has_perm('hr.delete_employeecontract'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('عقود العمل'), 'url': reverse('hr:contract_list')},
                {'title': self.object.contract_number or str(self.object.pk), 'url': ''}
            ],
        })
        return context


# ============================================
# عروض العلاوات
# ============================================

class IncrementListView(LoginRequiredMixin, TemplateView):
    """قائمة العلاوات"""
    template_name = 'hr/increments/increment_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = SalaryIncrement.objects.filter(company=company).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            applied=Count('id', filter=Q(status='applied')),
            rejected=Count('id', filter=Q(status='rejected')),
            total_amount=Sum('increment_amount', filter=Q(status='applied')),
        )

        context.update({
            'title': _('العلاوات'),
            'can_add': self.request.user.has_perm('hr.add_salaryincrement'),
            'can_edit': self.request.user.has_perm('hr.change_salaryincrement'),
            'can_delete': self.request.user.has_perm('hr.delete_salaryincrement'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العلاوات'), 'url': ''}
            ],
        })
        return context


class IncrementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء علاوة جديدة"""
    model = SalaryIncrement
    form_class = SalaryIncrementForm
    template_name = 'hr/increments/increment_form.html'
    permission_required = 'hr.add_salaryincrement'
    success_url = reverse_lazy('hr:increment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # إذا تم تمرير employee_id من URL
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(
                    pk=employee_id,
                    company=self.request.current_company
                )
                initial['employee'] = employee
            except Employee.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة العلاوة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة علاوة جديدة'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العلاوات'), 'url': reverse('hr:increment_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class IncrementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل علاوة"""
    model = SalaryIncrement
    form_class = SalaryIncrementForm
    template_name = 'hr/increments/increment_form.html'
    permission_required = 'hr.change_salaryincrement'
    success_url = reverse_lazy('hr:increment_list')

    def get_queryset(self):
        return SalaryIncrement.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث العلاوة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل العلاوة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العلاوات'), 'url': reverse('hr:increment_list')},
                {'title': f'تعديل', 'url': ''}
            ],
        })
        return context


class IncrementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف علاوة"""
    model = SalaryIncrement
    template_name = 'hr/increments/increment_confirm_delete.html'
    permission_required = 'hr.delete_salaryincrement'
    success_url = reverse_lazy('hr:increment_list')

    def get_queryset(self):
        return SalaryIncrement.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # لا يمكن حذف علاوة مطبقة
        if self.object.status == 'applied':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لا يمكن حذف علاوة تم تطبيقها'
                }, status=400)
            messages.error(request, 'لا يمكن حذف علاوة تم تطبيقها')
            return redirect('hr:increment_list')

        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'تم حذف العلاوة بنجاح'
            })

        messages.success(request, 'تم حذف العلاوة بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف العلاوة')
        return context


# ============================================
# عروض أنواع الإجازات
# ============================================

class LeaveTypeListView(LoginRequiredMixin, TemplateView):
    """قائمة أنواع الإجازات"""
    template_name = 'hr/leave_types/leave_type_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات سريعة
        stats = LeaveType.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            paid=Count('id', filter=Q(is_paid=True)),
            unpaid=Count('id', filter=Q(is_paid=False)),
        )

        context.update({
            'title': _('أنواع الإجازات'),
            'can_add': self.request.user.has_perm('hr.add_leavetype'),
            'can_edit': self.request.user.has_perm('hr.change_leavetype'),
            'can_delete': self.request.user.has_perm('hr.delete_leavetype'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أنواع الإجازات'), 'url': ''}
            ],
        })
        return context


class LeaveTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء نوع إجازة جديد"""
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'hr/leave_types/leave_type_form.html'
    permission_required = 'hr.add_leavetype'
    success_url = reverse_lazy('hr:leave_type_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        messages.success(self.request, _('تم إضافة نوع الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة نوع إجازة جديد'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أنواع الإجازات'), 'url': reverse('hr:leave_type_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class LeaveTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل نوع إجازة"""
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'hr/leave_types/leave_type_form.html'
    permission_required = 'hr.change_leavetype'
    success_url = reverse_lazy('hr:leave_type_list')

    def get_queryset(self):
        return LeaveType.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث نوع الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل نوع الإجازة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أنواع الإجازات'), 'url': reverse('hr:leave_type_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''}
            ],
        })
        return context


class LeaveTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف نوع إجازة"""
    model = LeaveType
    template_name = 'hr/leave_types/leave_type_confirm_delete.html'
    permission_required = 'hr.delete_leavetype'
    success_url = reverse_lazy('hr:leave_type_list')

    def get_queryset(self):
        return LeaveType.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        leave_type_name = self.object.name

        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف نوع الإجازة {leave_type_name} بنجاح'
            })

        messages.success(request, f'تم حذف نوع الإجازة {leave_type_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف نوع الإجازة')
        return context

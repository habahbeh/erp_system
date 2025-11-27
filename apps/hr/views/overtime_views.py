# apps/hr/views/overtime_views.py
"""
عروض العمل الإضافي والمغادرات - Overtime & Early Leave Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q, Count, Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date

from ..models import Overtime, EarlyLeave, Employee
from ..forms import OvertimeForm, EarlyLeaveForm


# ========================= Overtime Views =========================

class OvertimeListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة العمل الإضافي"""
    template_name = 'hr/overtime/overtime_list.html'
    permission_required = 'hr.view_overtime'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات
        stats = Overtime.objects.filter(company=company).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            total_hours=Sum('hours', filter=Q(status='approved')),
            total_amount=Sum('amount', filter=Q(status='approved')),
        )

        context.update({
            'title': _('العمل الإضافي'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العمل الإضافي'), 'url': ''}
            ],
        })
        return context


class OvertimeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """تسجيل عمل إضافي"""
    model = Overtime
    form_class = OvertimeForm
    template_name = 'hr/overtime/overtime_form.html'
    permission_required = 'hr.add_overtime'
    success_url = reverse_lazy('hr:overtime_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, _('تم تسجيل العمل الإضافي بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تسجيل عمل إضافي'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العمل الإضافي'), 'url': reverse('hr:overtime_list')},
                {'title': _('تسجيل'), 'url': ''}
            ],
        })
        return context


class OvertimeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عمل إضافي"""
    model = Overtime
    form_class = OvertimeForm
    template_name = 'hr/overtime/overtime_form.html'
    permission_required = 'hr.change_overtime'
    success_url = reverse_lazy('hr:overtime_list')

    def get_queryset(self):
        return Overtime.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث العمل الإضافي بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل عمل إضافي'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العمل الإضافي'), 'url': reverse('hr:overtime_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class OvertimeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف عمل إضافي"""
    model = Overtime
    template_name = 'hr/overtime/overtime_confirm_delete.html'
    permission_required = 'hr.delete_overtime'
    success_url = reverse_lazy('hr:overtime_list')

    def get_queryset(self):
        return Overtime.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف العمل الإضافي بنجاح'))
        return super().delete(request, *args, **kwargs)


class OvertimeApproveView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """الموافقة على العمل الإضافي"""
    template_name = 'hr/overtime/overtime_approve.html'
    permission_required = 'hr.change_overtime'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        pending_overtime = Overtime.objects.filter(
            company=company,
            status='pending'
        ).select_related('employee').order_by('-date')

        context.update({
            'title': _('الموافقة على العمل الإضافي'),
            'pending_overtime': pending_overtime,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('العمل الإضافي'), 'url': reverse('hr:overtime_list')},
                {'title': _('الموافقات'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        overtime_ids = request.POST.getlist('overtime_ids')

        if overtime_ids:
            overtimes = Overtime.objects.filter(
                id__in=overtime_ids,
                company=request.current_company,
                status='pending'
            )

            if action == 'approve':
                overtimes.update(
                    status='approved',
                    approved_by=request.user,
                    approved_at=timezone.now()
                )
                messages.success(request, _('تمت الموافقة على العمل الإضافي المحدد'))

            elif action == 'reject':
                overtimes.update(status='rejected')
                messages.warning(request, _('تم رفض العمل الإضافي المحدد'))

        return redirect('hr:overtime_approve')


# ========================= Early Leave Views =========================

class EarlyLeaveListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة المغادرات"""
    template_name = 'hr/early_leaves/early_leave_list.html'
    permission_required = 'hr.view_earlyleave'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات
        stats = EarlyLeave.objects.filter(company=company).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            total_minutes=Sum('minutes', filter=Q(status='approved')),
        )

        context.update({
            'title': _('المغادرات'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المغادرات'), 'url': ''}
            ],
        })
        return context


class EarlyLeaveCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """تسجيل مغادرة"""
    model = EarlyLeave
    form_class = EarlyLeaveForm
    template_name = 'hr/early_leaves/early_leave_form.html'
    permission_required = 'hr.add_earlyleave'
    success_url = reverse_lazy('hr:early_leave_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, _('تم تسجيل المغادرة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تسجيل مغادرة'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المغادرات'), 'url': reverse('hr:early_leave_list')},
                {'title': _('تسجيل'), 'url': ''}
            ],
        })
        return context


class EarlyLeaveUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل مغادرة"""
    model = EarlyLeave
    form_class = EarlyLeaveForm
    template_name = 'hr/early_leaves/early_leave_form.html'
    permission_required = 'hr.change_earlyleave'
    success_url = reverse_lazy('hr:early_leave_list')

    def get_queryset(self):
        return EarlyLeave.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث المغادرة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل مغادرة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المغادرات'), 'url': reverse('hr:early_leave_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class EarlyLeaveDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف مغادرة"""
    model = EarlyLeave
    template_name = 'hr/early_leaves/early_leave_confirm_delete.html'
    permission_required = 'hr.delete_earlyleave'
    success_url = reverse_lazy('hr:early_leave_list')

    def get_queryset(self):
        return EarlyLeave.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف المغادرة بنجاح'))
        return super().delete(request, *args, **kwargs)


class EarlyLeaveApproveView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """الموافقة على المغادرات"""
    template_name = 'hr/early_leaves/early_leave_approve.html'
    permission_required = 'hr.change_earlyleave'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        pending_leaves = EarlyLeave.objects.filter(
            company=company,
            status='pending'
        ).select_related('employee').order_by('-date')

        context.update({
            'title': _('الموافقة على المغادرات'),
            'pending_leaves': pending_leaves,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('المغادرات'), 'url': reverse('hr:early_leave_list')},
                {'title': _('الموافقات'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        leave_ids = request.POST.getlist('leave_ids')

        if leave_ids:
            leaves = EarlyLeave.objects.filter(
                id__in=leave_ids,
                company=request.current_company,
                status='pending'
            )

            if action == 'approve':
                leaves.update(
                    status='approved',
                    approved_by=request.user,
                    approved_at=timezone.now()
                )
                messages.success(request, _('تمت الموافقة على المغادرات المحددة'))

            elif action == 'reject':
                leaves.update(status='rejected')
                messages.warning(request, _('تم رفض المغادرات المحددة'))

        return redirect('hr:early_leave_approve')

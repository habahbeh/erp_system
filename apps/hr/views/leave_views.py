# apps/hr/views/leave_views.py
"""
عروض الإجازات - Leave Views
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

from ..models import LeaveRequest, LeaveBalance, LeaveType, Employee
from ..forms import LeaveRequestForm, LeaveBalanceForm, LeaveApprovalForm


# ========================= Leave Request Views =========================

class LeaveRequestListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة طلبات الإجازات"""
    template_name = 'hr/leaves/leave_request_list.html'
    permission_required = 'hr.view_leaverequest'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات
        stats = LeaveRequest.objects.filter(company=company).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
        )

        context.update({
            'title': _('طلبات الإجازات'),
            'stats': stats,
            'leave_types': LeaveType.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('طلبات الإجازات'), 'url': ''}
            ],
        })
        return context


class LeaveRequestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء طلب إجازة"""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leaves/leave_request_form.html'
    permission_required = 'hr.add_leaverequest'
    success_url = reverse_lazy('hr:leave_request_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, _('تم إنشاء طلب الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('طلب إجازة جديد'),
            'submit_text': _('إرسال الطلب'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('طلبات الإجازات'), 'url': reverse('hr:leave_request_list')},
                {'title': _('طلب جديد'), 'url': ''}
            ],
        })
        return context


class LeaveRequestDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل طلب الإجازة"""
    model = LeaveRequest
    template_name = 'hr/leaves/leave_request_detail.html'
    permission_required = 'hr.view_leaverequest'
    context_object_name = 'leave_request'

    def get_queryset(self):
        return LeaveRequest.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        # رصيد الموظف
        try:
            balance = LeaveBalance.objects.get(
                employee=obj.employee,
                leave_type=obj.leave_type,
                year=obj.start_date.year
            )
        except LeaveBalance.DoesNotExist:
            balance = None

        context.update({
            'title': f'طلب إجازة #{obj.pk}',
            'balance': balance,
            'approval_form': LeaveApprovalForm() if obj.status == 'pending' else None,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('طلبات الإجازات'), 'url': reverse('hr:leave_request_list')},
                {'title': f'طلب #{obj.pk}', 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        """معالجة الموافقة/الرفض"""
        self.object = self.get_object()
        form = LeaveApprovalForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']

            if action == 'approve':
                self.object.status = 'approved'
                self.object.approved_by = request.user
                self.object.approval_date = timezone.now()

                # خصم من الرصيد
                try:
                    balance = LeaveBalance.objects.get(
                        employee=self.object.employee,
                        leave_type=self.object.leave_type,
                        year=self.object.start_date.year
                    )
                    balance.used += self.object.days
                    balance.save()
                except LeaveBalance.DoesNotExist:
                    pass

                messages.success(request, _('تمت الموافقة على طلب الإجازة'))

            elif action == 'reject':
                self.object.status = 'rejected'
                self.object.rejection_reason = form.cleaned_data['rejection_reason']
                self.object.approved_by = request.user
                self.object.approval_date = timezone.now()
                messages.warning(request, _('تم رفض طلب الإجازة'))

            self.object.save()

        return redirect('hr:leave_request_detail', pk=self.object.pk)


class LeaveRequestUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل طلب إجازة"""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leaves/leave_request_form.html'
    permission_required = 'hr.change_leaverequest'
    success_url = reverse_lazy('hr:leave_request_list')

    def get_queryset(self):
        # فقط الطلبات التي في حالة draft أو pending
        return LeaveRequest.objects.filter(
            company=self.request.current_company,
            status__in=['draft', 'pending']
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث طلب الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل طلب إجازة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('طلبات الإجازات'), 'url': reverse('hr:leave_request_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class LeaveRequestDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف طلب إجازة"""
    model = LeaveRequest
    template_name = 'hr/leaves/leave_request_confirm_delete.html'
    permission_required = 'hr.delete_leaverequest'
    success_url = reverse_lazy('hr:leave_request_list')

    def get_queryset(self):
        return LeaveRequest.objects.filter(
            company=self.request.current_company,
            status__in=['draft', 'pending']
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف طلب الإجازة بنجاح'))
        return super().delete(request, *args, **kwargs)


# ========================= Leave Balance Views =========================

class LeaveBalanceListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة أرصدة الإجازات"""
    template_name = 'hr/leaves/leave_balance_list.html'
    permission_required = 'hr.view_leavebalance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company
        current_year = date.today().year

        context.update({
            'title': _('أرصدة الإجازات'),
            'current_year': current_year,
            'years': range(current_year - 2, current_year + 2),
            'leave_types': LeaveType.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أرصدة الإجازات'), 'url': ''}
            ],
        })
        return context


class LeaveBalanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إضافة رصيد إجازة"""
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'hr/leaves/leave_balance_form.html'
    permission_required = 'hr.add_leavebalance'
    success_url = reverse_lazy('hr:leave_balance_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        messages.success(self.request, _('تم إضافة رصيد الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة رصيد إجازة'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أرصدة الإجازات'), 'url': reverse('hr:leave_balance_list')},
                {'title': _('إضافة'), 'url': ''}
            ],
        })
        return context


class LeaveBalanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل رصيد إجازة"""
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'hr/leaves/leave_balance_form.html'
    permission_required = 'hr.change_leavebalance'
    success_url = reverse_lazy('hr:leave_balance_list')

    def get_queryset(self):
        return LeaveBalance.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث رصيد الإجازة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل رصيد إجازة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أرصدة الإجازات'), 'url': reverse('hr:leave_balance_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class InitializeBalancesView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """تهيئة أرصدة الإجازات للموظفين"""
    template_name = 'hr/leaves/initialize_balances.html'
    permission_required = 'hr.add_leavebalance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company
        current_year = date.today().year

        context.update({
            'title': _('تهيئة أرصدة الإجازات'),
            'current_year': current_year,
            'employees_count': Employee.objects.filter(
                company=company, is_active=True, status='active'
            ).count(),
            'leave_types': LeaveType.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('أرصدة الإجازات'), 'url': reverse('hr:leave_balance_list')},
                {'title': _('تهيئة'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        company = request.current_company
        year = int(request.POST.get('year', date.today().year))

        employees = Employee.objects.filter(
            company=company,
            is_active=True,
            status='active'
        )

        leave_types = LeaveType.objects.filter(
            company=company,
            is_active=True
        )

        created_count = 0
        for employee in employees:
            for leave_type in leave_types:
                balance, created = LeaveBalance.objects.get_or_create(
                    company=company,
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        'opening_balance': leave_type.default_days,
                        'earned': 0,
                    }
                )
                if created:
                    created_count += 1

        messages.success(
            request,
            _('تم إنشاء %(count)s رصيد إجازة للموظفين') % {'count': created_count}
        )
        return redirect('hr:leave_balance_list')

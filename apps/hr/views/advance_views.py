# apps/hr/views/advance_views.py
"""
عروض السلف والقروض - Advance Views
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
from dateutil.relativedelta import relativedelta

from ..models import Advance, AdvanceInstallment, Employee
from ..forms import AdvanceForm, AdvanceApprovalForm


class AdvanceListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة السلف"""
    template_name = 'hr/advances/advance_list.html'
    permission_required = 'hr.view_advance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # إحصائيات
        stats = Advance.objects.filter(company=company).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            disbursed=Count('id', filter=Q(status='disbursed')),
            total_amount=Sum('amount', filter=Q(status__in=['approved', 'disbursed', 'partially_paid'])),
            remaining_amount=Sum('remaining_amount', filter=Q(status__in=['disbursed', 'partially_paid'])),
        )

        context.update({
            'title': _('السلف'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': ''}
            ],
        })
        return context


class AdvanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء طلب سلفة"""
    model = Advance
    form_class = AdvanceForm
    template_name = 'hr/advances/advance_form.html'
    permission_required = 'hr.add_advance'
    success_url = reverse_lazy('hr:advance_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, _('تم إنشاء طلب السلفة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('طلب سلفة جديد'),
            'submit_text': _('إرسال الطلب'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': reverse('hr:advance_list')},
                {'title': _('طلب جديد'), 'url': ''}
            ],
        })
        return context


class AdvanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل السلفة"""
    model = Advance
    template_name = 'hr/advances/advance_detail.html'
    permission_required = 'hr.view_advance'
    context_object_name = 'advance'

    def get_queryset(self):
        return Advance.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        context.update({
            'title': f'سلفة - {obj.advance_number}',
            'installments': obj.installment_records.all().order_by('installment_number'),
            'approval_form': AdvanceApprovalForm() if obj.status == 'pending' else None,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': reverse('hr:advance_list')},
                {'title': obj.advance_number, 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        """معالجة الموافقة/الرفض"""
        self.object = self.get_object()
        form = AdvanceApprovalForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']

            if action == 'approve':
                self.object.status = 'approved'
                self.object.approved_by = request.user
                self.object.approved_at = timezone.now()
                messages.success(request, _('تمت الموافقة على السلفة'))

                # إنشاء جدول الأقساط
                self._create_installments()

            elif action == 'reject':
                self.object.status = 'rejected'
                self.object.rejection_reason = form.cleaned_data['rejection_reason']
                self.object.approved_by = request.user
                self.object.approved_at = timezone.now()
                messages.warning(request, _('تم رفض السلفة'))

            self.object.save()

        return redirect('hr:advance_detail', pk=self.object.pk)

    def _create_installments(self):
        """إنشاء جدول الأقساط"""
        advance = self.object

        # تاريخ بدء الخصم
        start_date = advance.start_deduction_date or (date.today() + relativedelta(months=1))
        start_date = start_date.replace(day=1)  # أول الشهر

        for i in range(advance.installments):
            due_date = start_date + relativedelta(months=i)

            AdvanceInstallment.objects.create(
                advance=advance,
                installment_number=i + 1,
                due_date=due_date,
                amount=advance.installment_amount,
                status='pending'
            )


class AdvanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل سلفة"""
    model = Advance
    form_class = AdvanceForm
    template_name = 'hr/advances/advance_form.html'
    permission_required = 'hr.change_advance'
    success_url = reverse_lazy('hr:advance_list')

    def get_queryset(self):
        return Advance.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث السلفة بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل سلفة'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': reverse('hr:advance_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class AdvanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف سلفة"""
    model = Advance
    template_name = 'hr/advances/advance_confirm_delete.html'
    permission_required = 'hr.delete_advance'
    success_url = reverse_lazy('hr:advance_list')

    def get_queryset(self):
        return Advance.objects.filter(
            company=self.request.current_company,
            status='pending'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف السلفة بنجاح'))
        return super().delete(request, *args, **kwargs)


class DisburseAdvanceView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """صرف السلفة"""
    template_name = 'hr/advances/disburse_advance.html'
    permission_required = 'hr.change_advance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        advance = get_object_or_404(
            Advance,
            pk=self.kwargs['pk'],
            company=self.request.current_company,
            status='approved'
        )

        context.update({
            'title': _('صرف سلفة'),
            'advance': advance,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': reverse('hr:advance_list')},
                {'title': _('صرف'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        advance = get_object_or_404(
            Advance,
            pk=kwargs['pk'],
            company=request.current_company,
            status='approved'
        )

        advance.status = 'disbursed'
        advance.disbursed_at = timezone.now()
        advance.save()

        messages.success(request, _('تم صرف السلفة بنجاح'))
        return redirect('hr:advance_detail', pk=advance.pk)


class AdvanceInstallmentsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة أقساط السلف المستحقة"""
    template_name = 'hr/advances/installments_list.html'
    permission_required = 'hr.view_advanceinstallment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # الأقساط المستحقة هذا الشهر
        today = date.today()
        current_month_start = today.replace(day=1)
        next_month_start = (current_month_start + relativedelta(months=1))

        due_installments = AdvanceInstallment.objects.filter(
            advance__company=company,
            status='pending',
            due_date__gte=current_month_start,
            due_date__lt=next_month_start
        ).select_related('advance', 'advance__employee')

        # إحصائيات
        stats = AdvanceInstallment.objects.filter(
            advance__company=company,
            status='pending'
        ).aggregate(
            total_count=Count('id'),
            total_amount=Sum('amount'),
        )

        context.update({
            'title': _('أقساط السلف المستحقة'),
            'due_installments': due_installments,
            'stats': stats,
            'current_month': today.strftime('%Y-%m'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('السلف'), 'url': reverse('hr:advance_list')},
                {'title': _('الأقساط المستحقة'), 'url': ''}
            ],
        })
        return context

# apps/hr/views/settings_views.py
"""
عروض إعدادات الموارد البشرية
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

from ..models import HRSettings, SocialSecuritySettings, PayrollAccountMapping
from ..forms import HRSettingsForm, SocialSecuritySettingsForm, PayrollAccountMappingForm


class HRSettingsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """صفحة إعدادات الموارد البشرية"""
    template_name = 'hr/settings/hr_settings.html'
    permission_required = 'hr.change_hrsettings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # الحصول على إعدادات HR أو إنشاؤها
        hr_settings, created = HRSettings.objects.get_or_create(company=company)
        ss_settings, created = SocialSecuritySettings.objects.get_or_create(company=company)

        context.update({
            'title': _('إعدادات الموارد البشرية'),
            'hr_settings': hr_settings,
            'ss_settings': ss_settings,
            'hr_form': HRSettingsForm(instance=hr_settings, company=company),
            'ss_form': SocialSecuritySettingsForm(instance=ss_settings, company=company),
            'payroll_mappings': PayrollAccountMapping.objects.filter(company=company),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الإعدادات'), 'url': ''}
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        company = request.current_company
        form_type = request.POST.get('form_type')

        if form_type == 'hr_settings':
            hr_settings, created = HRSettings.objects.get_or_create(company=company)
            form = HRSettingsForm(request.POST, instance=hr_settings, company=company)
            if form.is_valid():
                form.save()
                messages.success(request, _('تم حفظ إعدادات الموارد البشرية بنجاح'))
            else:
                messages.error(request, _('خطأ في حفظ الإعدادات'))

        elif form_type == 'ss_settings':
            ss_settings, created = SocialSecuritySettings.objects.get_or_create(company=company)
            form = SocialSecuritySettingsForm(request.POST, instance=ss_settings, company=company)
            if form.is_valid():
                form.save()
                messages.success(request, _('تم حفظ إعدادات الضمان الاجتماعي بنجاح'))
            else:
                messages.error(request, _('خطأ في حفظ الإعدادات'))

        return redirect('hr:hr_settings')


class PayrollMappingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إضافة ربط حساب راتب"""
    model = PayrollAccountMapping
    form_class = PayrollAccountMappingForm
    template_name = 'hr/settings/payroll_mapping_form.html'
    permission_required = 'hr.add_payrollaccountmapping'
    success_url = reverse_lazy('hr:hr_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        messages.success(self.request, _('تم إضافة ربط الحساب بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة ربط حساب راتب'),
            'submit_text': _('حفظ'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الإعدادات'), 'url': reverse('hr:hr_settings')},
                {'title': _('إضافة ربط حساب'), 'url': ''}
            ],
        })
        return context


class PayrollMappingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل ربط حساب راتب"""
    model = PayrollAccountMapping
    form_class = PayrollAccountMappingForm
    template_name = 'hr/settings/payroll_mapping_form.html'
    permission_required = 'hr.change_payrollaccountmapping'
    success_url = reverse_lazy('hr:hr_settings')

    def get_queryset(self):
        return PayrollAccountMapping.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث ربط الحساب بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل ربط حساب راتب'),
            'submit_text': _('تحديث'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الموارد البشرية'), 'url': '#'},
                {'title': _('الإعدادات'), 'url': reverse('hr:hr_settings')},
                {'title': _('تعديل ربط حساب'), 'url': ''}
            ],
        })
        return context


class PayrollMappingDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف ربط حساب راتب"""
    model = PayrollAccountMapping
    template_name = 'hr/settings/payroll_mapping_confirm_delete.html'
    permission_required = 'hr.delete_payrollaccountmapping'
    success_url = reverse_lazy('hr:hr_settings')

    def get_queryset(self):
        return PayrollAccountMapping.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        component_name = self.object.get_component_display()

        response = super().delete(request, *args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'تم حذف ربط الحساب {component_name} بنجاح'
            })

        messages.success(request, f'تم حذف ربط الحساب {component_name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف ربط حساب راتب')
        return context

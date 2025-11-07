# apps/assets/views/accounting_config_views.py
"""
عرض إعدادات الحسابات المحاسبية للأصول
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from apps.core.mixins import CompanyMixin
from apps.assets.models import AssetAccountingConfiguration
from apps.assets.forms.accounting_config_forms import AssetAccountingConfigurationForm


class AccountingConfigListView(LoginRequiredMixin, CompanyMixin, ListView):
    """قائمة إعدادات الحسابات المحاسبية"""
    model = AssetAccountingConfiguration
    template_name = 'assets/accounting_config/config_list.html'
    context_object_name = 'configs'
    paginate_by = 10

    def get_queryset(self):
        return AssetAccountingConfiguration.objects.filter(
            company=self.request.current_company
        ).select_related('company')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('إعدادات الحسابات المحاسبية'), 'url': ''},
        ]
        return context


class AccountingConfigDetailView(LoginRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل إعدادات الحسابات المحاسبية"""
    model = AssetAccountingConfiguration
    template_name = 'assets/accounting_config/config_detail.html'
    context_object_name = 'config'

    def get_queryset(self):
        return AssetAccountingConfiguration.objects.filter(
            company=self.request.current_company
        ).select_related('company')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('إعدادات الحسابات المحاسبية'), 'url': reverse('assets:accounting_config_list')},
            {'title': _('التفاصيل'), 'url': ''},
        ]
        return context


class AccountingConfigCreateView(LoginRequiredMixin, CompanyMixin, CreateView):
    """إنشاء إعدادات حسابات محاسبية جديدة"""
    model = AssetAccountingConfiguration
    form_class = AssetAccountingConfigurationForm
    template_name = 'assets/accounting_config/config_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        # Check if config already exists for this company
        existing = AssetAccountingConfiguration.objects.filter(
            company=self.request.current_company
        ).first()

        if existing:
            messages.warning(
                self.request,
                _('توجد إعدادات محاسبية بالفعل لهذه الشركة. سيتم تحويلك لتعديلها.')
            )
            return redirect('assets:accounting_config_update', pk=existing.pk)

        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _('✅ تم إنشاء إعدادات الحسابات المحاسبية بنجاح'))
        return response

    def get_success_url(self):
        return reverse('assets:accounting_config_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('إعدادات الحسابات المحاسبية'), 'url': reverse('assets:accounting_config_list')},
            {'title': _('إنشاء جديد'), 'url': ''},
        ]
        context['title'] = _('إنشاء إعدادات حسابات محاسبية')
        context['submit_text'] = _('حفظ')
        return context


class AccountingConfigUpdateView(LoginRequiredMixin, CompanyMixin, UpdateView):
    """تعديل إعدادات الحسابات المحاسبية"""
    model = AssetAccountingConfiguration
    form_class = AssetAccountingConfigurationForm
    template_name = 'assets/accounting_config/config_form.html'

    def get_queryset(self):
        return AssetAccountingConfiguration.objects.filter(
            company=self.request.current_company
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('✅ تم تحديث إعدادات الحسابات المحاسبية بنجاح'))
        return response

    def get_success_url(self):
        return reverse('assets:accounting_config_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('إعدادات الحسابات المحاسبية'), 'url': reverse('assets:accounting_config_list')},
            {'title': self.object.company.name, 'url': reverse('assets:accounting_config_detail', kwargs={'pk': self.object.pk})},
            {'title': _('تعديل'), 'url': ''},
        ]
        context['title'] = _('تعديل إعدادات الحسابات المحاسبية')
        context['submit_text'] = _('حفظ التعديلات')
        return context

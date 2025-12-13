# apps/core/views/settings_views.py
"""
إعدادات النظام - System Settings Views
"""

from django.views.generic import UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from apps.core.models import SystemSettings
from apps.accounting.models import Account


class SuperuserRequiredMixin(UserPassesTestMixin):
    """التحقق من صلاحيات المدير"""
    def test_func(self):
        return self.request.user.is_superuser


class AccountSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """صفحة إعدادات الحسابات الافتراضية"""
    model = SystemSettings
    template_name = 'core/settings/account_settings.html'
    fields = [
        # حسابات المشتريات
        'default_inventory_account',
        'default_purchase_account',
        'default_purchase_vat_account',
        'default_purchase_discount_account',
        # حسابات المبيعات
        'default_sales_account',
        'default_sales_vat_account',
        'default_cost_of_goods_account',
    ]
    success_url = reverse_lazy('core:account_settings')

    def get_object(self, queryset=None):
        """جلب إعدادات الشركة الحالية أو إنشائها"""
        settings, created = SystemSettings.objects.get_or_create(
            company=self.request.current_company
        )
        return settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إعدادات الحسابات الافتراضية')
        context['accounts'] = Account.objects.filter(
            company=self.request.current_company,
            is_active=True,
            accept_entries=True
        ).order_by('code')
        return context

    def form_valid(self, form):
        messages.success(self.request, _('تم حفظ إعدادات الحسابات بنجاح'))
        return super().form_valid(form)


class SystemSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """صفحة الإعدادات العامة للنظام"""
    model = SystemSettings
    template_name = 'core/settings/system_settings.html'
    fields = [
        'negative_stock_allowed',
        'stock_valuation_method',
        'customer_credit_check',
        'credit_restore_on_check_date',
        'auto_create_journal_entries',
        'session_timeout',
    ]
    success_url = reverse_lazy('core:system_settings')

    def get_object(self, queryset=None):
        """جلب إعدادات الشركة الحالية أو إنشائها"""
        settings, created = SystemSettings.objects.get_or_create(
            company=self.request.current_company
        )
        return settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إعدادات النظام العامة')
        return context

    def form_valid(self, form):
        messages.success(self.request, _('تم حفظ الإعدادات بنجاح'))
        return super().form_valid(form)

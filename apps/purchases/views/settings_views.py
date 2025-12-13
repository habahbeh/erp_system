# apps/purchases/views/settings_views.py
"""
إعدادات المشتريات - Purchase Settings Views
"""

from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from apps.core.models import SystemSettings
from apps.accounting.models import Account


class PurchaseSettingsView(LoginRequiredMixin, UpdateView):
    """صفحة إعدادات المشتريات"""
    model = SystemSettings
    template_name = 'purchases/settings/purchase_settings.html'
    fields = [
        'default_inventory_account',
        'default_purchase_account',
        'default_purchase_vat_account',
        'default_purchase_discount_account',
    ]
    success_url = reverse_lazy('purchases:purchase_settings')

    def get_object(self, queryset=None):
        """جلب إعدادات الشركة الحالية أو إنشائها"""
        settings, created = SystemSettings.objects.get_or_create(
            company=self.request.current_company
        )
        return settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إعدادات المشتريات')
        context['accounts'] = Account.objects.filter(
            company=self.request.current_company,
            is_active=True,
            accept_entries=True
        ).order_by('code')
        return context

    def form_valid(self, form):
        messages.success(self.request, _('تم حفظ الإعدادات بنجاح'))
        return super().form_valid(form)

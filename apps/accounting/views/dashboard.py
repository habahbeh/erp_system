# apps/accounting/views/dashboard.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.core.mixins import CompanyMixin


class AccountingDashboardView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """لوحة المحاسبة"""
    template_name = 'accounting/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'لوحة المحاسبة',
        })
        return context
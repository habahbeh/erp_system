# apps/core/views/pricing_dashboard_view.py
"""
Pricing Dashboard View
Main dashboard for pricing management with charts and statistics
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count

from apps.core.models import (
    PricingRule, PriceList, Item, ItemCategory
)


class PricingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main pricing dashboard with charts and statistics
    """
    template_name = 'core/pricing/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Add context data for the dashboard
        """
        context = super().get_context_data(**kwargs)

        company = self.request.current_company

        # Get active price lists
        context['price_lists'] = PriceList.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')[:10]  # Limit to 10 for dropdown

        # Get active rules count
        context['active_rules_count'] = PricingRule.objects.filter(
            company=company,
            is_active=True
        ).count()

        # Get total items count
        context['total_items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).count()

        # Get categories count
        context['categories_count'] = ItemCategory.objects.filter(
            company=company,
            is_active=True
        ).count()

        return context

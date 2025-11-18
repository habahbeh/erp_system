# apps/core/views/pricing_list_views.py
"""
Pricing List Views with DataTables
Enhanced list views using DataTables for better UX
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Q

from apps.core.models import (
    PricingRule, PriceList, PriceListItem
)


class PricingRuleListDTView(LoginRequiredMixin, TemplateView):
    """
    Pricing rules list view with DataTables
    """
    template_name = 'core/pricing/rule_list_dt.html'

    def get_context_data(self, **kwargs):
        """
        Add statistics to context
        """
        context = super().get_context_data(**kwargs)

        company = self.request.current_company

        # Get statistics
        all_rules = PricingRule.objects.filter(company=company)

        context['total_rules'] = all_rules.count()
        context['active_rules'] = all_rules.filter(is_active=True).count()
        context['inactive_rules'] = all_rules.filter(is_active=False).count()
        context['discount_rules'] = all_rules.filter(
            Q(rule_type='DISCOUNT_PERCENTAGE') | Q(rule_type='DISCOUNT_AMOUNT') | Q(rule_type='BULK_DISCOUNT')
        ).count()

        return context


class PriceListItemsDTView(LoginRequiredMixin, TemplateView):
    """
    Price list items view with DataTables
    """
    template_name = 'core/pricing/price_list_items_dt.html'

    def get_context_data(self, **kwargs):
        """
        Add price lists to context
        """
        context = super().get_context_data(**kwargs)

        company = self.request.current_company

        # Get active price lists
        context['price_lists'] = PriceList.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        return context

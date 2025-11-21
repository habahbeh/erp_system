# apps/core/views/pricing_dashboard_view.py
"""
Pricing Dashboard View
Main dashboard for pricing management with charts and statistics
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta

from apps.core.models import (
    PricingRule, PriceList, PriceListItem, PriceHistory, Item, ItemCategory
)


class PricingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main pricing dashboard with Material Design
    """
    template_name = 'core/pricing/pricing_dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Add context data for the dashboard with statistics
        """
        context = super().get_context_data(**kwargs)

        company = self.request.current_company
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Statistics
        context['total_price_lists'] = PriceList.objects.filter(
            company=company
        ).count()

        context['total_price_items'] = PriceListItem.objects.filter(
            price_list__company=company
        ).count()

        context['active_rules'] = PricingRule.objects.filter(
            company=company,
            is_active=True
        ).count()

        context['monthly_changes'] = PriceHistory.objects.filter(
            price_list_item__price_list__company=company,
            changed_at__gte=month_ago
        ).count()

        # Recent changes
        recent_changes = PriceHistory.objects.filter(
            price_list_item__price_list__company=company
        ).select_related(
            'price_list_item',
            'price_list_item__price_list',
            'price_list_item__item'
        ).order_by('-changed_at')[:5]

        context['recent_changes'] = [
            {
                'title': f"{change.price_list_item.item.name} - {change.price_list_item.price_list.name}",
                'description': f"تم تغيير السعر من {change.old_price} إلى {change.new_price}",
                'date': change.changed_at.strftime('%Y-%m-%d %H:%M')
            }
            for change in recent_changes
        ]

        return context

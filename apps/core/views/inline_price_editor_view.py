# apps/core/views/inline_price_editor_view.py
"""
Inline Price Editor View
Provides interactive inline price editing functionality
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.models import PriceListItem, PriceList


class InlinePriceEditorView(LoginRequiredMixin, TemplateView):
    """
    Inline price editor with AJAX updates
    """
    template_name = 'core/pricing/inline_price_editor.html'

    def get_context_data(self, **kwargs):
        """
        Add price items and price lists to context
        """
        context = super().get_context_data(**kwargs)

        company = self.request.current_company

        # Get price list filter
        price_list_id = self.request.GET.get('price_list_id')

        # Get price items
        price_items = PriceListItem.objects.filter(
            item__company=company
        ).select_related('item', 'price_list', 'uom', 'item__category')

        if price_list_id:
            price_items = price_items.filter(price_list_id=price_list_id)

        # Limit to 100 items for performance
        price_items = price_items.order_by('item__code')[:100]

        context['price_items'] = price_items

        # Get price lists for filter
        context['price_lists'] = PriceList.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        # Currency symbol
        context['currency_symbol'] = company.currency.symbol if company.currency else ''

        return context

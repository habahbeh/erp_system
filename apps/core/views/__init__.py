# apps/core/views/__init__.py
"""
استيراد جميع الـ Views
"""

from .base_views import dashboard, switch_branch
from .item_views import (
    ItemListView, ItemCreateView, ItemUpdateView, ItemDeleteView, ItemDetailView,
    ItemCategoryListView, ItemCategoryCreateView, ItemCategoryUpdateView, ItemCategoryDeleteView
)
from .ajax_views import item_datatable_ajax
# from .ajax_views import item_datatable_ajax, partner_autocomplete, item_autocomplete, get_item_details, check_barcode

__all__ = [
    # Base Views
    'dashboard',
    'switch_branch',
    # Item Views
    'ItemListView',
    'ItemCreateView',
    'ItemUpdateView',
    'ItemDeleteView',
    'ItemDetailView',
    # Category Views
    'ItemCategoryListView',
    'ItemCategoryCreateView',
    'ItemCategoryUpdateView',
    'ItemCategoryDeleteView',
    # Ajax Views
    'item_datatable_ajax',
    'partner_autocomplete',
    'item_autocomplete',
    'get_item_details',
    'check_barcode',
]
# apps/core/views/__init__.py
"""
استيراد جميع الـ Views
"""

from .base_views import dashboard, switch_branch
from .item_views import (
    ItemListView, ItemCreateView, ItemUpdateView, ItemDeleteView, ItemDetailView,
    ItemCategoryListView, ItemCategoryCreateView, ItemCategoryUpdateView, ItemCategoryDeleteView
)
from .partner_views import (
    BusinessPartnerListView, BusinessPartnerCreateView, BusinessPartnerUpdateView,
    BusinessPartnerDeleteView, BusinessPartnerDetailView
)
from .warehouse_views import (
    WarehouseListView, WarehouseCreateView, WarehouseUpdateView,
    WarehouseDeleteView, WarehouseDetailView
)
from .ajax_views import item_datatable_ajax, partner_datatable_ajax, warehouse_datatable_ajax

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
    # Partner Views
    'BusinessPartnerListView',
    'BusinessPartnerCreateView',
    'BusinessPartnerUpdateView',
    'BusinessPartnerDeleteView',
    'BusinessPartnerDetailView',
    # Warehouse Views
    'WarehouseListView',
    'WarehouseCreateView',
    'WarehouseUpdateView',
    'WarehouseDeleteView',
    'WarehouseDetailView',
    # Ajax Views
    'item_datatable_ajax',
    'partner_datatable_ajax',
    'warehouse_datatable_ajax',
]
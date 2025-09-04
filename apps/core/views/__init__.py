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

from .ajax_views import (
    item_datatable_ajax, partner_datatable_ajax, warehouse_datatable_ajax,
    brand_datatable_ajax, unit_datatable_ajax, currency_datatable_ajax
)

from .brand_views import (
    BrandListView, BrandCreateView, BrandUpdateView,
    BrandDeleteView, BrandDetailView
)

from .unit_views import (
    UnitOfMeasureListView, UnitOfMeasureCreateView, UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView, UnitOfMeasureDetailView
)
from .currency_views import (
    CurrencyListView, CurrencyCreateView, CurrencyUpdateView,
    CurrencyDeleteView, CurrencyDetailView
)

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
    # Brand Views
    'BrandListView',
    'BrandCreateView',
    'BrandUpdateView',
    'BrandDeleteView',
    'BrandDetailView',
    # Unit Views
    'UnitOfMeasureListView',
    'UnitOfMeasureCreateView',
    'UnitOfMeasureUpdateView',
    'UnitOfMeasureDeleteView',
    'UnitOfMeasureDetailView',
    # Currency Views
    'CurrencyListView',
    'CurrencyCreateView',
    'CurrencyUpdateView',
    'CurrencyDeleteView',
    'CurrencyDetailView',
    # Ajax Views
    'item_datatable_ajax',
    'partner_datatable_ajax',
    'warehouse_datatable_ajax',
    'brand_datatable_ajax',
    'unit_datatable_ajax',
    'currency_datatable_ajax',
]
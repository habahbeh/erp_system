# apps/base_data/views/__init__.py
"""
Views لوحدة البيانات الأساسية
"""

from .customer_views import (
    CustomerListView, CustomerCreateView,
    CustomerDetailView, CustomerUpdateView, CustomerDeleteView
)
from .supplier_views import (
    SupplierListView, SupplierCreateView,
    SupplierDetailView, SupplierUpdateView, SupplierDeleteView
)
from .item_views import (
    ItemListView, ItemCreateView,
    ItemDetailView, ItemUpdateView, ItemDeleteView
)
from .warehouse_views import (
    WarehouseListView, WarehouseCreateView,
    WarehouseDetailView, WarehouseUpdateView, WarehouseDeleteView
)
from .unit_views import (
    UnitListView, UnitCreateView,
    UnitUpdateView, UnitDeleteView
)
from .category_views import (
    CategoryListView, CategoryCreateView,
    CategoryUpdateView, CategoryDeleteView
)

__all__ = [
    # العملاء
    'CustomerListView', 'CustomerCreateView',
    'CustomerDetailView', 'CustomerUpdateView', 'CustomerDeleteView',

    # الموردين
    'SupplierListView', 'SupplierCreateView',
    'SupplierDetailView', 'SupplierUpdateView', 'SupplierDeleteView',

    # الأصناف
    'ItemListView', 'ItemCreateView',
    'ItemDetailView', 'ItemUpdateView', 'ItemDeleteView',

    # المستودعات
    'WarehouseListView', 'WarehouseCreateView',
    'WarehouseDetailView', 'WarehouseUpdateView', 'WarehouseDeleteView',

    # وحدات القياس
    'UnitListView', 'UnitCreateView',
    'UnitUpdateView', 'UnitDeleteView',

    'CategoryListView', 'CategoryCreateView',
    'CategoryUpdateView', 'CategoryDeleteView',
]
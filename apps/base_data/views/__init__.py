# apps/base_data/views/__init__.py
"""
Views لتطبيق البيانات الأساسية
منظمة في ملفات منفصلة لسهولة الصيانة
"""

# Item Views
from .item_views import (
    # الأصناف
    ItemListView,
    ItemDetailView,
    ItemCreateView,
    ItemUpdateView,
    ItemDeleteView,
    ItemDataTableView,
    ItemQuickAddView,
    ItemImportView,
    ItemExportView,

    # التصنيفات
    ItemCategoryListView,
    ItemCategoryCreateView,
    ItemCategoryUpdateView,
    ItemCategoryDeleteView,
    ItemCategoryDataTableView,

    # معدلات التحويل
    ItemConversionListView,
    ItemConversionCreateView,
    ItemConversionUpdateView,
    ItemConversionDeleteView,

    # مكونات المواد
    ItemComponentListView,
    ItemComponentCreateView,
    ItemComponentUpdateView,
    ItemComponentDeleteView,
)

# Partner Views
from .partner_views import (
    # الشركاء التجاريين
    BusinessPartnerListView,
    BusinessPartnerDetailView,
    BusinessPartnerCreateView,
    BusinessPartnerUpdateView,
    BusinessPartnerDeleteView,
    BusinessPartnerDataTableView,
    BusinessPartnerQuickAddView,

    # العملاء
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,

    # الموردين
    SupplierListView,
    SupplierCreateView,
    SupplierUpdateView,
)

# Warehouse Views
from .warehouse_views import (
    # المستودعات
    WarehouseListView,
    WarehouseDetailView,
    WarehouseCreateView,
    WarehouseUpdateView,
    WarehouseDeleteView,
    WarehouseDataTableView,

    # وحدات القياس
    UnitOfMeasureListView,
    UnitOfMeasureCreateView,
    UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView,
    UnitOfMeasureDataTableView,
)

# API Views
from .api_views import (
    # API endpoints للاستخدام مع AJAX
    ItemSearchAPIView,
    BusinessPartnerSearchAPIView,
    WarehouseSearchAPIView,
    CheckBarcodeAPIView,
    CheckCodeAPIView,
)

__all__ = [
    # Items
    'ItemListView',
    'ItemDetailView',
    'ItemCreateView',
    'ItemUpdateView',
    'ItemDeleteView',
    'ItemDataTableView',
    'ItemQuickAddView',
    'ItemImportView',
    'ItemExportView',

    # Categories
    'ItemCategoryListView',
    'ItemCategoryCreateView',
    'ItemCategoryUpdateView',
    'ItemCategoryDeleteView',
    'ItemCategoryDataTableView',

    # Conversions
    'ItemConversionListView',
    'ItemConversionCreateView',
    'ItemConversionUpdateView',
    'ItemConversionDeleteView',

    # Components
    'ItemComponentListView',
    'ItemComponentCreateView',
    'ItemComponentUpdateView',
    'ItemComponentDeleteView',

    # Partners
    'BusinessPartnerListView',
    'BusinessPartnerDetailView',
    'BusinessPartnerCreateView',
    'BusinessPartnerUpdateView',
    'BusinessPartnerDeleteView',
    'BusinessPartnerDataTableView',
    'BusinessPartnerQuickAddView',

    # Customers
    'CustomerListView',
    'CustomerCreateView',
    'CustomerUpdateView',

    # Suppliers
    'SupplierListView',
    'SupplierCreateView',
    'SupplierUpdateView',

    # Warehouses
    'WarehouseListView',
    'WarehouseDetailView',
    'WarehouseCreateView',
    'WarehouseUpdateView',
    'WarehouseDeleteView',
    'WarehouseDataTableView',

    # Units
    'UnitOfMeasureListView',
    'UnitOfMeasureCreateView',
    'UnitOfMeasureUpdateView',
    'UnitOfMeasureDeleteView',
    'UnitOfMeasureDataTableView',

    # APIs
    'ItemSearchAPIView',
    'BusinessPartnerSearchAPIView',
    'WarehouseSearchAPIView',
    'CheckBarcodeAPIView',
    'CheckCodeAPIView',
]
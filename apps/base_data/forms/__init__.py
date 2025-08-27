# apps/base_data/forms/__init__.py
"""
استيراد جميع النماذج لسهولة الوصول - محدث 100%
جميع النماذج متطابقة مع models.py + Bootstrap 5 + RTL
"""

# نماذج الأصناف
from .item_forms import (
    ItemForm,
    ItemCategoryForm,
    ItemConversionForm,
    ItemComponentForm,
    ItemQuickAddForm,
    ItemCategoryQuickAddForm,
    ItemConversionFormSet,
    ItemComponentFormSet,
    ItemImportForm
)

# نماذج الشركاء التجاريين
from .partner_forms import (
    BusinessPartnerForm,
    CustomerForm,
    SupplierForm,
    PartnerQuickAddForm,
    ContactInfoForm,
    PartnerImportForm,
    PartnerExportForm
)

# نماذج المستودعات ووحدات القياس
from .warehouse_forms import (
    WarehouseForm,
    UnitOfMeasureForm,
    WarehouseItemForm,
    WarehouseTransferForm,
    WarehouseQuickAddForm,
    UnitQuickAddForm,
    WarehouseImportForm,
    InventoryAdjustmentForm,
    StockReportForm
)

# نماذج الفلترة والبحث
from .filter_forms import (
    BaseFilterForm,
    ItemFilterForm,
    BusinessPartnerFilterForm,
    WarehouseFilterForm,
    GlobalSearchForm,
    ExportForm,
    DataTablesFilterForm,
    QuickSearchForm
)

__all__ = [
    # Items
    'ItemForm',
    'ItemCategoryForm',
    'ItemConversionForm',
    'ItemComponentForm',
    'ItemQuickAddForm',
    'ItemCategoryQuickAddForm',
    'ItemConversionFormSet',
    'ItemComponentFormSet',
    'ItemImportForm',

    # Partners
    'BusinessPartnerForm',
    'CustomerForm',
    'SupplierForm',
    'PartnerQuickAddForm',
    'ContactInfoForm',
    'PartnerImportForm',
    'PartnerExportForm',

    # Warehouse & Units
    'WarehouseForm',
    'UnitOfMeasureForm',
    'WarehouseItemForm',
    'WarehouseTransferForm',
    'WarehouseQuickAddForm',
    'UnitQuickAddForm',
    'WarehouseImportForm',
    'InventoryAdjustmentForm',
    'StockReportForm',

    # Filters & Search
    'BaseFilterForm',
    'ItemFilterForm',
    'BusinessPartnerFilterForm',
    'WarehouseFilterForm',
    'GlobalSearchForm',
    'ExportForm',
    'DataTablesFilterForm',
    'QuickSearchForm',
]
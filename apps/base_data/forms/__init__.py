# apps/base_data/forms/__init__.py
"""
استيراد جميع النماذج لسهولة الوصول
"""

# نماذج الأصناف
from .item_forms import (
    ItemForm,
    ItemCategoryForm,
    ItemConversionForm,
    ItemComponentForm,
    ItemQuickAddForm,
    ItemImportForm
)

# نماذج الشركاء التجاريين
from .partner_forms import (
    BusinessPartnerForm,
    CustomerForm,
    SupplierForm,
    PartnerQuickAddForm
)

# نماذج المستودعات ووحدات القياس
from .warehouse_forms import (
    WarehouseForm,
    UnitOfMeasureForm,
    WarehouseTransferForm
)

# نماذج الفلترة والبحث
from .filter_forms import (
    ItemFilterForm,
    BusinessPartnerFilterForm,
    WarehouseFilterForm,
    GlobalSearchForm
)

__all__ = [
    # Items
    'ItemForm',
    'ItemCategoryForm',
    'ItemConversionForm',
    'ItemComponentForm',
    'ItemQuickAddForm',
    'ItemImportForm',

    # Partners
    'BusinessPartnerForm',
    'CustomerForm',
    'SupplierForm',
    'PartnerQuickAddForm',

    # Warehouse & Units
    'WarehouseForm',
    'UnitOfMeasureForm',
    'WarehouseTransferForm',

    # Filters
    'ItemFilterForm',
    'BusinessPartnerFilterForm',
    'WarehouseFilterForm',
    'GlobalSearchForm',
]
# apps/core/models/__init__.py
"""
استيراد جميع النماذج الأساسية للنظام

هذا الملف يستورد جميع النماذج من الملفات المنظمة
ويجعلها متاحة كـ: from apps.core.models import Item, ...
"""

# Base Models
from .base_models import (
    BaseModel,
    DocumentBaseModel,
    Currency,
    PaymentMethod,
)

# Company Models
from .company_models import (
    Company,
    Branch,
    Warehouse,
)

# User Models
from .user_models import (
    User,
    UserProfile,
    CustomPermission,
    PermissionGroup,
)

# Item Models
from .item_models import (
    ItemCategory,
    Brand,
    Item,
    VariantAttribute,
    VariantValue,
    ItemVariant,
    ItemVariantAttributeValue,
)

# Partner Models
from .partner_models import (
    BusinessPartner,
    PartnerRepresentative,
)

# UoM Models (NEW - Updated Week 2)
from .uom_models import (
    UoMGroup,          # ⭐ NEW Week 2
    UnitOfMeasure,
    UoMConversion,
)

# Pricing Models (includes NEW models)
from .pricing_models import (
    PriceList,
    PriceListItem,
    PricingRule,        # NEW
    PriceHistory,       # NEW
    get_item_price,     # helper function
)

# Template Models (NEW)
from .template_models import (
    ItemTemplate,       # NEW
    BulkImportJob,      # NEW
)

# Audit Models (includes NEW models)
from .audit_models import (
    AuditLog,
    VariantLifecycleEvent,  # NEW
)

# System Models
from .system_models import (
    NumberingSequence,
    SystemSettings,
)


__all__ = [
    # Base models
    'BaseModel', 'DocumentBaseModel', 'Currency', 'PaymentMethod',

    # Company models
    'Company', 'Branch', 'Warehouse',

    # User models
    'User', 'UserProfile', 'CustomPermission', 'PermissionGroup',

    # Item models
    'ItemCategory', 'Brand', 'Item',
    'VariantAttribute', 'VariantValue', 'ItemVariant', 'ItemVariantAttributeValue',

    # Partner models
    'BusinessPartner', 'PartnerRepresentative',

    # UoM models (NEW - Updated Week 2)
    'UoMGroup', 'UnitOfMeasure', 'UoMConversion',

    # Pricing models
    'PriceList', 'PriceListItem', 'PricingRule', 'PriceHistory',
    'get_item_price',  # helper function

    # Template models (NEW)
    'ItemTemplate', 'BulkImportJob',

    # Audit models
    'AuditLog', 'VariantLifecycleEvent',

    # System models
    'NumberingSequence', 'SystemSettings',
]

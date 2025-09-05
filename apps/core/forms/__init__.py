# apps/core/forms/__init__.py
"""
استيراد جميع النماذج
"""

from .item_forms import ItemForm, ItemCategoryForm
from .partner_forms import BusinessPartnerForm
from .warehouse_forms import WarehouseForm
from .brand_forms import BrandForm
from .unit_forms import UnitOfMeasureForm
from .currency_forms import CurrencyForm
from .company_forms import CompanyForm
from .branch_forms import BranchForm  # إضافة جديد
from .numbering_forms import NumberingSequenceForm  # إضافة جديد
from .variant_forms import (
    VariantAttributeForm, VariantValueForm,
    VariantAttributeWithValuesForm, VariantValueFormSet
)
__all__ = [
    'ItemForm',
    'ItemCategoryForm',
    'BusinessPartnerForm',
    'WarehouseForm',
    'BrandForm',
    'UnitOfMeasureForm',
    'CurrencyForm',
    'CompanyForm',
    'BranchForm',  # إضافة جديد
    'NumberingSequenceForm',  # إضافة جديد
    # Variant forms - إضافة جديد
    'VariantAttributeForm',
    'VariantValueForm',
    'VariantAttributeWithValuesForm',
    'VariantValueFormSet',
]
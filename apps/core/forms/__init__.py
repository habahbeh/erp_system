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
from .branch_forms import BranchForm
from .numbering_forms import NumberingSequenceForm
from .variant_forms import (
    VariantAttributeForm, VariantValueForm,
    VariantAttributeWithValuesForm, VariantValueFormSet
)

from .user_forms import UserForm, UserUpdateForm, ChangePasswordForm  # إضافة جديد

from .user_profile_forms import (  # إضافة جديد
    UserProfileForm, BulkUserProfileForm, UserPermissionsForm
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
    'BranchForm',
    'NumberingSequenceForm',
    # Variant forms
    'VariantAttributeForm',
    'VariantValueForm',
    'VariantAttributeWithValuesForm',
    'VariantValueFormSet',
    # User forms - إضافة جديد
    'UserForm',
    'UserUpdateForm',
    'ChangePasswordForm',
    # User Profile Forms - إضافة جديد
    'UserProfileForm',
    'BulkUserProfileForm',
    'UserPermissionsForm',
]
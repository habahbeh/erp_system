# apps/core/forms/__init__.py
"""
استيراد جميع النماذج
"""

from .item_forms import ItemForm, ItemCategoryForm
from .partner_forms import BusinessPartnerForm, PartnerRepresentativeForm
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

from .price_forms import PriceListForm, PriceListItemForm, BulkPriceUpdateForm

from django import forms

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة CSS classes تلقائياً
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})

__all__ = [
    'ItemForm',
    'ItemCategoryForm',
    'BusinessPartnerForm',
    'PartnerRepresentativeForm',
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

    'PriceListForm', 'PriceListItemForm', 'BulkPriceUpdateForm'
]
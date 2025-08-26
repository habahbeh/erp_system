# apps/base_data/forms/item_forms.py
"""
النماذج الخاصة بالبيانات الأساسية - الأصناف والتصنيفات
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import (
    Item, ItemCategory, ItemConversion, ItemComponent, UnitOfMeasure
)


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'code', 'name', 'name_en', 'barcode', 'category', 'unit',
            'purchase_price', 'sale_price', 'tax_rate', 'manufacturer',
            'specifications', 'weight', 'image', 'notes',
            'minimum_quantity', 'maximum_quantity', 'substitute_items'
        ]
        widgets = {
            'specifications': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'substitute_items': forms.CheckboxSelectMultiple(),
        }


class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['code', 'name', 'name_en', 'parent']


class ItemConversionForm(forms.ModelForm):
    class Meta:
        model = ItemConversion
        fields = ['from_unit', 'to_unit', 'factor']


class ItemComponentForm(forms.ModelForm):
    class Meta:
        model = ItemComponent
        fields = ['component_item', 'quantity', 'unit', 'waste_percentage', 'notes']


class ItemQuickAddForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['code', 'name', 'name_en', 'category', 'unit']


class ItemFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'البحث في الكود أو الاسم...',
        'class': 'form-control'
    }))
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        empty_label="كل التصنيفات",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_inactive = forms.BooleanField(
        required=False,
        label="غير نشط فقط",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            )
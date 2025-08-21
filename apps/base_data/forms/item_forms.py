# apps/base_data/forms/item_forms.py
"""
نماذج الأصناف والتصنيفات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import ItemCategory, Item, UnitOfMeasure


class ItemCategoryForm(forms.ModelForm):
    """نموذج تصنيف الأصناف"""

    class Meta:
        model = ItemCategory
        fields = ['parent', 'code', 'name', 'name_en', 'is_active']
        widgets = {
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة التصنيفات الأب حسب الشركة
            self.fields['parent'].queryset = ItemCategory.objects.filter(
                company=company,
                is_active=True,
                level__lt=4  # الحد الأقصى 4 مستويات
            )

            # منع اختيار نفسه كأب
            if self.instance.pk:
                self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                    pk=self.instance.pk
                )

    def clean(self):
        """التحقق من المستوى"""
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')

        if parent and parent.level >= 4:
            raise forms.ValidationError(_('لا يمكن إضافة أكثر من 4 مستويات للتصنيف'))

        return cleaned_data


class ItemForm(forms.ModelForm):
    """نموذج الصنف"""

    class Meta:
        model = Item
        fields = [
            'code', 'name', 'name_en', 'barcode',
            'category', 'unit', 'manufacturer',
            'purchase_price', 'sale_price', 'tax_rate',
            'minimum_quantity', 'maximum_quantity',
            'weight', 'image', 'notes', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '16'
            }),
            'minimum_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'maximum_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة حسب الشركة
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company,
                is_active=True
            )
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            )

    def clean(self):
        """التحقق من البيانات"""
        cleaned_data = super().clean()

        # التحقق من أن سعر البيع أكبر من سعر الشراء
        purchase_price = cleaned_data.get('purchase_price', 0)
        sale_price = cleaned_data.get('sale_price', 0)

        if sale_price and purchase_price and sale_price < purchase_price:
            self.add_error('sale_price', _('سعر البيع يجب أن يكون أكبر من أو يساوي سعر الشراء'))

        # التحقق من حدود المخزون
        min_qty = cleaned_data.get('minimum_quantity', 0)
        max_qty = cleaned_data.get('maximum_quantity')

        if max_qty and min_qty and max_qty < min_qty:
            self.add_error('maximum_quantity', _('الحد الأعلى يجب أن يكون أكبر من الحد الأدنى'))

        return cleaned_data
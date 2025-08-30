# apps/core/forms/item_forms.py
"""
نماذج الأصناف والتصنيفات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Item, ItemCategory, Brand, UnitOfMeasure, Warehouse, Currency, ItemVariant, ItemVariantAttributeValue
from django.forms import inlineformset_factory


class ItemForm(forms.ModelForm):
    """نموذج إضافة/تعديل الصنف"""

    class Meta:
        model = Item
        fields = [
            'code', 'name', 'name_en', 'sku', 'barcode', 'category', 'brand',
            'unit_of_measure', 'currency', 'default_warehouse',
            'sales_account', 'purchase_account', 'inventory_account', 'cost_of_goods_account',
            'tax_rate', 'short_description', 'description',
            'has_variants', 'weight', 'length', 'width', 'height',
            'manufacturer', 'model_number', 'image', 'attachment',
            'attachment_name', 'notes', 'additional_notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('سيتم توليده تلقائياً')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الصنف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Item Name')
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('SKU')
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الباركود')
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'default_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '16.0'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'maxlength': 300
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'has_variants': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الشركة المصنعة')
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموديل')
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'attachment_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المرفق')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'sales_account': forms.Select(attrs={'class': 'form-select'}),
            'purchase_account': forms.Select(attrs={'class': 'form-select'}),
            'inventory_account': forms.Select(attrs={'class': 'form-select'}),
            'cost_of_goods_account': forms.Select(attrs={'class': 'form-select'}),

        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = self.request.current_company

            from apps.accounting.models import Account
            accounts_queryset = Account.objects.filter(company=company, is_active=True)

            self.fields['sales_account'].queryset = accounts_queryset.filter(account_type__type_category='revenue')
            self.fields['purchase_account'].queryset = accounts_queryset.filter(account_type__type_category='expenses')
            self.fields['inventory_account'].queryset = accounts_queryset.filter(account_type__type_category='assets')
            self.fields['cost_of_goods_account'].queryset = accounts_queryset.filter(account_type__type_category='expenses')

            # فلترة الخيارات حسب الشركة
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            )
            self.fields['brand'].queryset = Brand.objects.filter(
                company=company, is_active=True
            )
            self.fields['unit_of_measure'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            )
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
            self.fields['default_warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            )

        # جعل بعض الحقول اختيارية في العرض
        self.fields['brand'].required = False
        self.fields['default_warehouse'].required = False
        self.fields['code'].required = False

    def clean_barcode(self):
        """التحقق من عدم تكرار الباركود"""
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            queryset = Item.objects.filter(barcode=barcode)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الباركود مستخدم مسبقاً'))
        return barcode

    def clean_sku(self):
        """التحقق من عدم تكرار SKU"""
        sku = self.cleaned_data.get('sku')
        if sku:
            queryset = Item.objects.filter(sku=sku)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الـ SKU مستخدم مسبقاً'))
        return sku

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price', 0)
        sale_price = cleaned_data.get('sale_price', 0)

        if sale_price > 0 and purchase_price > sale_price:
            raise ValidationError(_('سعر البيع لا يمكن أن يكون أقل من سعر الشراء'))

        return cleaned_data


class ItemCategoryForm(forms.ModelForm):
    """نموذج تصنيفات الأصناف"""

    class Meta:
        model = ItemCategory
        fields = ['parent', 'code', 'name', 'name_en', 'description']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز التصنيف')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم التصنيف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Category Name')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = self.request.current_company

            # فلترة التصنيفات الأب حسب الشركة
            self.fields['parent'].queryset = ItemCategory.objects.filter(
                company=company, level__lt=4, is_active=True
            )

        self.fields['parent'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار رمز التصنيف"""
        code = self.cleaned_data.get('code')
        if self.request:
            company = self.request.current_company
            queryset = ItemCategory.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code


class ItemVariantForm(forms.ModelForm):
    """نموذج متغير الصنف"""

    class Meta:
        model = ItemVariant
        fields = ['code', 'sku', 'barcode', 'weight', 'image', 'notes']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'sku': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }


class ItemVariantAttributeValueForm(forms.ModelForm):
    """نموذج قيم خصائص المتغير"""

    class Meta:
        model = ItemVariantAttributeValue
        fields = ['attribute', 'value']
        widgets = {
            'attribute': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'value': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


# FormSets
ItemVariantFormSet = inlineformset_factory(
    Item, ItemVariant,
    form=ItemVariantForm,
    extra=1,
    can_delete=True,
    min_num=0
)

ItemVariantAttributeFormSet = inlineformset_factory(
    ItemVariant, ItemVariantAttributeValue,
    form=ItemVariantAttributeValueForm,
    extra=1,
    can_delete=True,
    min_num=0
)
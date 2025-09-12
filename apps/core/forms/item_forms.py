# apps/core/forms/item_forms.py
"""
نماذج الأصناف والتصنيفات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Item, ItemCategory, Brand, UnitOfMeasure, Warehouse, Currency, ItemVariant, \
    ItemVariantAttributeValue
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

            # الحسابات المحاسبية
            'sales_account': forms.Select(attrs={'class': 'form-select'}),
            'purchase_account': forms.Select(attrs={'class': 'form-select'}),
            'inventory_account': forms.Select(attrs={'class': 'form-select'}),
            'cost_of_goods_account': forms.Select(attrs={'class': 'form-select'}),

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
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # التأكد من وجود الشركة
        company = None
        if self.request:
            if hasattr(self.request, 'current_company') and self.request.current_company:
                company = self.request.current_company
            elif hasattr(self.request.user, 'company') and self.request.user.company:
                company = self.request.user.company
            else:
                # استخدام أول شركة متاحة
                from ..models import Company
                company = Company.objects.filter(is_active=True).first()

        # تشخيص المشكلة - طباعة للتأكد (أزل في الإنتاج)
        print(f"Form company: {company}")

        if company:
            try:
                from apps.accounting.models import Account
                accounts_queryset = Account.objects.filter(company=company, is_active=True)

                self.fields['sales_account'].queryset = accounts_queryset.filter(account_type__type_category='revenue')
                self.fields['purchase_account'].queryset = accounts_queryset.filter(
                    account_type__type_category='expenses')
                self.fields['inventory_account'].queryset = accounts_queryset.filter(
                    account_type__type_category='assets')
                self.fields['cost_of_goods_account'].queryset = accounts_queryset.filter(
                    account_type__type_category='expenses')
            except ImportError:
                # في حالة عدم وجود تطبيق المحاسبة
                self.fields['sales_account'].queryset = self.fields['sales_account'].queryset.none()
                self.fields['purchase_account'].queryset = self.fields['purchase_account'].queryset.none()
                self.fields['inventory_account'].queryset = self.fields['inventory_account'].queryset.none()
                self.fields['cost_of_goods_account'].queryset = self.fields['cost_of_goods_account'].queryset.none()

            # فلترة الخيارات حسب الشركة
            categories = ItemCategory.objects.filter(company=company, is_active=True)
            brands = Brand.objects.filter(company=company, is_active=True)
            units = UnitOfMeasure.objects.filter(company=company, is_active=True)
            warehouses = Warehouse.objects.filter(company=company, is_active=True)

            # تشخيص إضافي
            print(f"Categories found: {categories.count()}")
            print(f"Brands found: {brands.count()}")
            print(f"Units found: {units.count()}")
            print(f"Warehouses found: {warehouses.count()}")

            self.fields['category'].queryset = categories
            self.fields['brand'].queryset = brands
            self.fields['unit_of_measure'].queryset = units
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
            self.fields['default_warehouse'].queryset = warehouses
        else:
            # إذا لم توجد شركة، أجعل كل الحقول فارغة
            self.fields['category'].queryset = ItemCategory.objects.none()
            self.fields['brand'].queryset = Brand.objects.none()
            self.fields['unit_of_measure'].queryset = UnitOfMeasure.objects.none()
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
            self.fields['default_warehouse'].queryset = Warehouse.objects.none()

            # معالجة الحسابات المحاسبية
            self.fields['sales_account'].queryset = self.fields['sales_account'].queryset.none()
            self.fields['purchase_account'].queryset = self.fields['purchase_account'].queryset.none()
            self.fields['inventory_account'].queryset = self.fields['inventory_account'].queryset.none()
            self.fields['cost_of_goods_account'].queryset = self.fields['cost_of_goods_account'].queryset.none()

        # جعل بعض الحقول اختيارية في العرض
        self.fields['brand'].required = False
        self.fields['default_warehouse'].required = False
        self.fields['code'].required = False
        self.fields['sales_account'].required = False
        self.fields['purchase_account'].required = False
        self.fields['inventory_account'].required = False
        self.fields['cost_of_goods_account'].required = False

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
        """التحقق من عدم تكرار SKU - سيتم التحقق الكامل في clean()"""
        return self.cleaned_data.get('sku')

    def clean(self):
        """التحقق الشامل من عدم تكرار القيم"""
        cleaned_data = super().clean()

        # الحصول على الشركة الحالية من الـ request
        if hasattr(self, 'request') and hasattr(self.request, 'current_company'):
            company = self.request.current_company
        else:
            from .models import Company
            company = Company.objects.first()

        if not company:
            raise ValidationError(_('لم يتم تحديد الشركة'))

        # التحقق من SKU
        sku = cleaned_data.get('sku')
        if sku:
            queryset = Item.objects.filter(company=company, sku=sku)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError({
                    'sku': _('هذا الـ SKU موجود مسبقاً في هذه الشركة')
                })

        # التحقق من الكود
        code = cleaned_data.get('code')
        if code:
            queryset = Item.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError({
                    'code': _('هذا الكود موجود مسبقاً في هذه الشركة')
                })

        # التحقق من الباركود
        barcode = cleaned_data.get('barcode')
        if barcode:
            queryset = Item.objects.filter(company=company, barcode=barcode)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError({
                    'barcode': _('هذا الباركود موجود مسبقاً في هذه الشركة')
                })

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
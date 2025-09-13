# apps/core/forms/item_forms.py
"""
نماذج الأصناف والتصنيفات والعلامات التجارية
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory

from ..models import Item, ItemCategory, Brand, ItemVariant


class ItemForm(forms.ModelForm):
    """نموذج إضافة/تعديل الصنف"""

    class Meta:
        model = Item
        fields = [
            # المعلومات الأساسية
            'code', 'name', 'name_en', 'sku', 'barcode',
            'category', 'brand', 'unit_of_measure', 'currency',
            'default_warehouse', 'tax_rate',
            # حذف الحسابات المحاسبية مؤقتاً لحل المشاكل
            # 'sales_account', 'purchase_account', 'inventory_account', 'cost_of_goods_account',
            'short_description', 'description', 'has_variants',
            'weight', 'length', 'width', 'height',
            'manufacturer', 'model_number',
            'image', 'attachment', 'attachment_name',
            'notes', 'additional_notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الصنف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الإنجليزي')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الصنف (سيتم توليده تلقائياً)')
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('SKU')
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الباركود')
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit_of_measure': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'default_warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16.0',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف مختصر')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('الوصف التفصيلي')
            }),
            'has_variants': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': _('الوزن بالكيلو جرام')
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('الطول بالسنتيمتر')
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('العرض بالسنتيمتر')
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('الارتفاع بالسنتيمتر')
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الشركة المصنعة')
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموديل')
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'attachment_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المرفق')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات عامة')
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # إصلاح مشكلة current_company
        if self.request:
            if hasattr(self.request, 'current_company') and self.request.current_company:
                company = self.request.current_company
            else:
                # استخدم أول شركة متاحة كـ fallback
                from apps.core.models import Company
                company = Company.objects.first()
        else:
            from apps.core.models import Company
            company = Company.objects.first()

        if company:
            # فلترة الخيارات حسب الشركة
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'name')

            self.fields['brand'].queryset = Brand.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            from ..models import UnitOfMeasure, Currency, Warehouse

            self.fields['unit_of_measure'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            ).order_by('name')

            self.fields['default_warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

        # إضافة empty_label للخيارات الاختيارية
        self.fields['brand'].empty_label = _('اختر العلامة التجارية')
        self.fields['default_warehouse'].empty_label = _('اختر المستودع')


class ItemCategoryForm(forms.ModelForm):
    """نموذج إضافة/تعديل تصنيف الأصناف"""

    class Meta:
        model = ItemCategory
        fields = ['parent', 'code', 'name', 'name_en', 'description']
        widgets = {
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز التصنيف'),
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم التصنيف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الإنجليزي')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('وصف التصنيف')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة التصنيفات الأب حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company
            if company:
                self.fields['parent'].queryset = ItemCategory.objects.filter(
                    company=company, is_active=True
                ).order_by('level', 'name')

        self.fields['parent'].empty_label = _('تصنيف رئيسي')

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')

        # التحقق من عدم تجاوز 4 مستويات
        if parent and parent.level >= 4:
            raise forms.ValidationError(_('لا يمكن تجاوز 4 مستويات للتصنيفات'))

        return cleaned_data


class ItemVariantForm(forms.ModelForm):
    """نموذج متغير الصنف المحسن"""

    # إضافة حقول للخصائص
    variant_attributes = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label=_('الخصائص المطلوبة')
    )

    class Meta:
        model = ItemVariant
        fields = ['code', 'sku', 'barcode', 'weight', 'image', 'notes']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('سيتم توليده تلقائياً')
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('SKU المتغير')
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('باركود المتغير')
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
                'placeholder': _('الوزن الخاص')
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control form-control-sm',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': _('ملاحظات المتغير')
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            from ..models import VariantAttribute
            self.fields['variant_attributes'].queryset = VariantAttribute.objects.filter(
                company=company,
                is_active=True
            ).order_by('sort_order', 'name')


# FormSet محدث للمتغيرات
ItemVariantFormSet = inlineformset_factory(
    Item,
    ItemVariant,
    form=ItemVariantForm,
    fields=['code', 'sku', 'barcode', 'weight', 'image', 'notes'],
    extra=0,  # لن نضيف متغيرات فارغة
    can_delete=True,
    max_num=50,  # حد أقصى 50 متغير
)


class VariantAttributeSelectionForm(forms.Form):
    """نموذج اختيار خصائص المتغيرات"""

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            from ..models import VariantAttribute
            attributes = VariantAttribute.objects.filter(
                company=company,
                is_active=True
            ).prefetch_related('values').order_by('sort_order', 'name')

            for attribute in attributes:
                field_name = f'attribute_{attribute.id}'
                self.fields[field_name] = forms.ModelMultipleChoiceField(
                    queryset=attribute.values.filter(is_active=True).order_by('sort_order', 'value'),
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'form-check-input attribute-values',
                        'data-attribute-id': attribute.id,
                        'data-attribute-name': attribute.name
                    }),
                    required=False,
                    label=attribute.display_name or attribute.name
                )
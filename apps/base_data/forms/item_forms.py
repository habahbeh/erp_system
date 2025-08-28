# apps/base_data/forms/item_forms.py
"""
النماذج الخاصة بالبيانات الأساسية - الأصناف والتصنيفات
محدث 100% حسب models.py + Bootstrap 5 + RTL
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import (
    Item, ItemCategory, ItemConversion, ItemComponent,
    UnitOfMeasure, Warehouse
)
from apps.core.models import User


class ItemForm(forms.ModelForm):
    """نموذج الصنف الكامل - محدث 100%"""

    class Meta:
        model = Item
        fields = [
            'code', 'name', 'name_en', 'barcode', 'category', 'unit',
            'purchase_price', 'sale_price', 'tax_rate',
            'sales_account', 'purchase_account', 'inventory_account', 'cost_of_goods_account',
            'manufacturer', 'specifications', 'weight', 'image', 'notes',
            'minimum_quantity', 'maximum_quantity', 'substitute_items',
            'is_inactive'  # الحقل الناقص
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود الصنف'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الصنف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الباركود'),
                'dir': 'ltr'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر التصنيف')
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر وحدة القياس')
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '16.0',
                'dir': 'ltr'
            }),
            # الحسابات المحاسبية
            'sales_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب المبيعات')
            }),
            'purchase_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب المشتريات')
            }),
            'inventory_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب المخزون')
            }),
            'cost_of_goods_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب تكلفة البضاعة')
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الشركة المصنعة')
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('مواصفات الصنف')
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'dir': 'ltr'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات')
            }),
            'minimum_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'maximum_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'substitute_items': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'is_inactive': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            })
        }
        labels = {
            'code': _('رمز الصنف'),
            'name': _('اسم الصنف'),
            'name_en': _('الاسم بالإنجليزية'),
            'barcode': _('الباركود'),
            'category': _('التصنيف'),
            'unit': _('وحدة القياس'),
            'purchase_price': _('سعر الشراء'),
            'sale_price': _('سعر البيع'),
            'tax_rate': _('نسبة الضريبة %'),
            'sales_account': _('حساب المبيعات'),
            'purchase_account': _('حساب المشتريات'),
            'inventory_account': _('حساب المخزون'),
            'cost_of_goods_account': _('حساب تكلفة البضاعة'),
            'manufacturer': _('الشركة المصنعة'),
            'specifications': _('المواصفات'),
            'weight': _('الوزن'),
            'image': _('صورة الصنف'),
            'notes': _('ملاحظات'),
            'minimum_quantity': _('الحد الأدنى'),
            'maximum_quantity': _('الحد الأعلى'),
            'substitute_items': _('المواد البديلة'),
            'is_inactive': _('غير فعال')
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة التصنيفات والوحدات
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'code')

            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            # فلترة الحسابات المحاسبية
            try:
                from accounting.models import Account
                accounts = Account.objects.filter(
                    company=company, is_active=True
                ).order_by('code')

                self.fields['sales_account'].queryset = accounts
                self.fields['purchase_account'].queryset = accounts
                self.fields['inventory_account'].queryset = accounts
                self.fields['cost_of_goods_account'].queryset = accounts
            except ImportError:
                # في حالة عدم وجود app المحاسبة
                pass

            # فلترة المواد البديلة
            if self.instance.pk:
                self.fields['substitute_items'].queryset = Item.objects.filter(
                    company=company, is_active=True
                ).exclude(pk=self.instance.pk)
            else:
                self.fields['substitute_items'].queryset = Item.objects.filter(
                    company=company, is_active=True
                )

        # جعل بعض الحقول اختيارية
        optional_fields = [
            'code', 'name_en', 'barcode', 'manufacturer', 'specifications',
            'weight', 'image', 'notes', 'maximum_quantity', 'substitute_items',
            'sales_account', 'purchase_account', 'inventory_account', 'cost_of_goods_account'
        ]
        for field in optional_fields:
            self.fields[field].required = False

    def clean_code(self):
        """التحقق من تفرد الكود"""
        code = self.cleaned_data.get('code')
        if code:
            queryset = Item.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))
        return code

    def clean_barcode(self):
        """التحقق من تفرد الباركود"""
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            queryset = Item.objects.filter(barcode=barcode)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الباركود مستخدم من قبل'))
        return barcode

    def clean(self):
        cleaned_data = super().clean()
        sale_price = cleaned_data.get('sale_price', 0)
        purchase_price = cleaned_data.get('purchase_price', 0)
        min_qty = cleaned_data.get('minimum_quantity', 0)
        max_qty = cleaned_data.get('maximum_quantity')

        # التحقق من الأسعار
        if sale_price and purchase_price and sale_price < purchase_price:
            self.add_error('sale_price', _('سعر البيع لا يمكن أن يكون أقل من سعر الشراء'))

        # التحقق من الكميات
        if max_qty and min_qty and max_qty < min_qty:
            self.add_error('maximum_quantity', _('الحد الأعلى لا يمكن أن يكون أقل من الحد الأدنى'))

        return cleaned_data


class ItemCategoryForm(forms.ModelForm):
    """نموذج تصنيف الأصناف"""

    class Meta:
        model = ItemCategory
        fields = ['code', 'name', 'name_en', 'parent']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز التصنيف'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم التصنيف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('التصنيف الأب (اختياري)')
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # منع التصنيف من كونه أباً لنفسه
            queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'code')

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            self.fields['parent'].queryset = queryset

        self.fields['code'].required = False
        self.fields['name_en'].required = False
        self.fields['parent'].required = False


class ItemConversionForm(forms.ModelForm):
    """نموذج معدلات التحويل"""

    class Meta:
        model = ItemConversion
        fields = ['from_unit', 'to_unit', 'factor']
        widgets = {
            'from_unit': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2'
            }),
            'to_unit': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2'
            }),
            'factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001',
                'dir': 'ltr'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            units = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['from_unit'].queryset = units
            self.fields['to_unit'].queryset = units

    def clean(self):
        cleaned_data = super().clean()
        from_unit = cleaned_data.get('from_unit')
        to_unit = cleaned_data.get('to_unit')

        if from_unit and to_unit and from_unit == to_unit:
            raise ValidationError(_('لا يمكن التحويل من وحدة إلى نفسها'))

        return cleaned_data


class ItemComponentForm(forms.ModelForm):
    """نموذج مستهلكات المادة"""

    class Meta:
        model = ItemComponent
        fields = ['component_item', 'quantity', 'unit', 'waste_percentage', 'notes']
        widgets = {
            'component_item': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001',
                'dir': 'ltr'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2'
            }),
            'waste_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات')
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        parent_item = kwargs.pop('parent_item', None)
        super().__init__(*args, **kwargs)

        if company:
            # استبعاد المادة الأساسية من المكونات
            items_queryset = Item.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            if parent_item:
                items_queryset = items_queryset.exclude(pk=parent_item.pk)

            self.fields['component_item'].queryset = items_queryset

            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

        self.fields['notes'].required = False


# النماذج السريعة
class ItemQuickAddForm(forms.ModelForm):
    """نموذج الإضافة السريعة للصنف"""

    class Meta:
        model = Item
        fields = ['code', 'name', 'name_en', 'category', 'unit']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('كود الصنف'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم الصنف'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-control': 'select2'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-control': 'select2'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'code')

            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

        self.fields['code'].required = False
        self.fields['name_en'].required = False


class ItemCategoryQuickAddForm(forms.ModelForm):
    """نموذج الإضافة السريعة للتصنيف"""

    class Meta:
        model = ItemCategory
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم التصنيف'),
                'required': True
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-control': 'select2'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['parent'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True, level__lt=4
            ).order_by('level', 'code')

        self.fields['parent'].required = False


# Formsets للمكونات والمعدلات
ItemConversionFormSet = forms.inlineformset_factory(
    Item, ItemConversion,
    form=ItemConversionForm,
    extra=1,
    can_delete=True,
    fields=['from_unit', 'to_unit', 'factor']
)

ItemComponentFormSet = forms.inlineformset_factory(
    Item, ItemComponent,
    form=ItemComponentForm,
    fk_name='parent_item',
    extra=1,
    can_delete=True,
    fields=['component_item', 'quantity', 'unit', 'waste_percentage', 'notes']
)


# استيراد البيانات
class ItemImportForm(forms.Form):
    """نموذج استيراد الأصناف"""

    file = forms.FileField(
        label=_('ملف البيانات'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        }),
        help_text=_('يدعم Excel وCSV فقط')
    )

    update_existing = forms.BooleanField(
        label=_('تحديث الموجود'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('تحديث البيانات في حالة وجود كود مطابق')
    )

    import_images = forms.BooleanField(
        label=_('استيراد الصور'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('استيراد صور الأصناف من مجلد منفصل')
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise ValidationError(_('نوع الملف غير مدعوم'))
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError(_('حجم الملف كبير جداً'))
        return file
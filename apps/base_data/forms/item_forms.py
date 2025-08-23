# apps/base_data/forms/item_forms.py
"""
نماذج الأصناف والمواد
يتضمن: الأصناف، التصنيفات، التحويلات، المكونات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import permission_required
from decimal import Decimal

from ..models import Item, ItemCategory, ItemConversion, ItemComponent, UnitOfMeasure
from accounting.models import Account


class ItemCategoryForm(forms.ModelForm):
    """نموذج تصنيف الأصناف - يدعم 4 مستويات"""

    class Meta:
        model = ItemCategory
        fields = ['parent', 'code', 'name', 'name_en']
        widgets = {
            'parent': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر التصنيف الأب (اختياري)'),
                'data-allow-clear': 'true',
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: 001, ELEC, FOOD'),
                'required': True,
                'autofocus': True,
                'maxlength': '20',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: إلكترونيات، مواد غذائية'),
                'required': True,
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Category Name'),
                'dir': 'ltr',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة التصنيفات الأب حسب الشركة
        if self.instance.company_id:
            self.fields['parent'].queryset = ItemCategory.objects.filter(
                company=self.instance.company,
                level__lt=4  # الحد الأقصى 4 مستويات
            ).order_by('level', 'code')

        # منع اختيار نفسه كأب
        if self.instance.pk:
            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                pk=self.instance.pk
            )

        # تعطيل الحقول حسب الصلاحيات
        if self.user and not self.user.has_perm('base_data.change_itemcategory'):
            for field in self.fields:
                self.fields[field].disabled = True

    def clean_code(self):
        """التحقق من عدم تكرار الرمز"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # التحقق من التكرار
            qs = ItemCategory.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الرمز مستخدم بالفعل'))
        return code

    def clean(self):
        """التحقق من عدم تجاوز 4 مستويات"""
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')

        if parent and parent.level >= 4:
            raise ValidationError({
                'parent': _('لا يمكن إنشاء أكثر من 4 مستويات للتصنيفات')
            })

        # التحقق من عدم إنشاء دائرة في التصنيفات
        if parent and self.instance.pk:
            current = parent
            while current:
                if current.pk == self.instance.pk:
                    raise ValidationError({
                        'parent': _('لا يمكن جعل التصنيف تابعاً لأحد فروعه')
                    })
                current = current.parent

        return cleaned_data


class ItemForm(forms.ModelForm):
    """نموذج الصنف/المادة - النموذج الرئيسي"""

    # حقول إضافية للبحث السريع
    substitute_items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'data-control': 'select2',
            'data-placeholder': _('اختر المواد البديلة'),
            'multiple': 'multiple',
        })
    )

    class Meta:
        model = Item
        fields = [
            # معلومات أساسية
            'code', 'name', 'name_en', 'barcode',
            'category', 'unit',

            # الأسعار والضرائب
            'purchase_price', 'sale_price', 'tax_rate',

            # الحسابات المحاسبية
            'sales_account', 'purchase_account',
            'inventory_account', 'cost_of_goods_account',

            # معلومات إضافية
            'manufacturer', 'specifications', 'weight',
            'image', 'notes',

            # حدود المخزون
            'minimum_quantity', 'maximum_quantity',

            # الحالة
            'is_inactive'
        ]

        widgets = {
            # معلومات أساسية
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الصنف'),
                'required': True,
                'autofocus': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الصنف'),
                'required': True,
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Item Name'),
                'dir': 'ltr',
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الباركود (اختياري)'),
                'data-inputmask': "'mask': '9999999999999'",
            }),

            # التصنيف والوحدة
            'category': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر التصنيف'),
                'required': True,
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر وحدة القياس'),
                'required': True,
            }),

            # الأسعار والضرائب
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '16',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '16',
            }),

            # الحسابات المحاسبية
            'sales_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب المبيعات'),
            }),
            'purchase_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب المشتريات'),
            }),
            'inventory_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب المخزون'),
            }),
            'cost_of_goods_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب تكلفة البضاعة'),
            }),

            # معلومات إضافية
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الشركة المصنعة'),
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('المواصفات الفنية للصنف'),
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.000',
                'step': '0.001',
                'min': '0',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات إضافية'),
            }),

            # حدود المخزون
            'minimum_quantity': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
            }),
            'maximum_quantity': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': _('اختياري'),
                'step': '0.01',
                'min': '0',
            }),

            # الحالة
            'is_inactive': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة البيانات حسب الشركة
        if hasattr(self.instance, 'company') and self.instance.company:
            company = self.instance.company

            # التصنيفات
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company,
                is_active=True
            ).order_by('level', 'code')

            # وحدات القياس
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            # الحسابات المحاسبية
            accounts = Account.objects.filter(
                company=company,
                accept_entries=True,
                is_active=True
            ).order_by('code')

            self.fields['sales_account'].queryset = accounts
            self.fields['purchase_account'].queryset = accounts
            self.fields['inventory_account'].queryset = accounts
            self.fields['cost_of_goods_account'].queryset = accounts

            # المواد البديلة
            substitute_qs = Item.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            if self.instance.pk:
                substitute_qs = substitute_qs.exclude(pk=self.instance.pk)
                # تحميل المواد البديلة الحالية
                self.fields['substitute_items'].initial = self.instance.substitute_items.all()

            self.fields['substitute_items'].queryset = substitute_qs

        # تخصيص الحقول حسب الصلاحيات
        if self.user:
            # حقول القراءة فقط للمستخدمين بدون صلاحية التعديل
            if not self.user.has_perm('base_data.change_item'):
                for field in self.fields:
                    self.fields[field].disabled = True

            # إخفاء الحسابات المحاسبية لغير المحاسبين
            if not self.user.has_perm('accounting.view_account'):
                account_fields = [
                    'sales_account', 'purchase_account',
                    'inventory_account', 'cost_of_goods_account'
                ]
                for field in account_fields:
                    self.fields[field].widget = forms.HiddenInput()

    def clean_barcode(self):
        """التحقق من عدم تكرار الباركود"""
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            barcode = barcode.strip()
            qs = Item.objects.filter(barcode=barcode)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الباركود مستخدم بالفعل'))
        return barcode

    def clean_code(self):
        """التحقق من عدم تكرار رمز الصنف"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            qs = Item.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الرمز مستخدم بالفعل'))
        return code

    def clean(self):
        """التحقق من منطقية البيانات"""
        cleaned_data = super().clean()

        # التحقق من الأسعار
        purchase_price = cleaned_data.get('purchase_price', 0) or 0
        sale_price = cleaned_data.get('sale_price', 0) or 0

        if self.user and self.user.has_perm('base_data.validate_prices'):
            if purchase_price > 0 and sale_price > 0:
                if sale_price < purchase_price:
                    # تحذير فقط، ليس خطأ
                    self.add_error('sale_price',
                                   _('تنبيه: سعر البيع أقل من سعر الشراء!')
                                   )

                # حساب هامش الربح
                profit_margin = ((sale_price - purchase_price) / purchase_price) * 100
                if profit_margin < 10:  # أقل من 10%
                    self.add_error(None,
                                   _('تنبيه: هامش الربح %(margin).1f%% قد يكون منخفضاً') % {
                                       'margin': profit_margin
                                   }
                                   )

        # التحقق من حدود المخزون
        min_qty = cleaned_data.get('minimum_quantity', 0) or 0
        max_qty = cleaned_data.get('maximum_quantity')

        if max_qty and min_qty > max_qty:
            raise ValidationError({
                'maximum_quantity': _('الحد الأعلى يجب أن يكون أكبر من الحد الأدنى')
            })

        return cleaned_data

    def save(self, commit=True):
        """حفظ الصنف والمواد البديلة"""
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # حفظ المواد البديلة
            if 'substitute_items' in self.cleaned_data:
                instance.substitute_items.set(self.cleaned_data['substitute_items'])

        return instance


class ItemQuickAddForm(forms.ModelForm):
    """نموذج إضافة سريعة للأصناف - للاستخدام في النوافذ المنبثقة"""

    class Meta:
        model = Item
        fields = ['code', 'name', 'category', 'unit', 'sale_price']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('رمز الصنف'),
                'required': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم الصنف'),
                'required': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'required': True,
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'required': True,
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
        }


class ItemConversionForm(forms.ModelForm):
    """نموذج معدل تحويل المادة"""

    class Meta:
        model = ItemConversion
        fields = ['item', 'from_unit', 'to_unit', 'factor']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر المادة'),
                'required': True,
            }),
            'from_unit': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('من وحدة'),
                'required': True,
            }),
            'to_unit': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('إلى وحدة'),
                'required': True,
            }),
            'factor': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '1.0000',
                'step': '0.0001',
                'min': '0.0001',
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة حسب الشركة
        if hasattr(self.instance, 'company') and self.instance.company:
            company = self.instance.company

            self.fields['item'].queryset = Item.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            units = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            self.fields['from_unit'].queryset = units
            self.fields['to_unit'].queryset = units

    def clean(self):
        """التحقق من صحة التحويل"""
        cleaned_data = super().clean()
        from_unit = cleaned_data.get('from_unit')
        to_unit = cleaned_data.get('to_unit')
        item = cleaned_data.get('item')

        # التحقق من عدم تحويل الوحدة لنفسها
        if from_unit and to_unit and from_unit == to_unit:
            raise ValidationError({
                'to_unit': _('لا يمكن تحويل الوحدة إلى نفسها')
            })

        # التحقق من عدم تكرار التحويل
        if item and from_unit and to_unit:
            qs = ItemConversion.objects.filter(
                item=item,
                from_unit=from_unit,
                to_unit=to_unit
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا التحويل موجود بالفعل'))

        return cleaned_data


class ItemComponentForm(forms.ModelForm):
    """نموذج مكونات المادة - للمنتجات المركبة"""

    class Meta:
        model = ItemComponent
        fields = [
            'parent_item', 'component_item',
            'quantity', 'unit', 'waste_percentage', 'notes'
        ]
        widgets = {
            'parent_item': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('المنتج الرئيسي'),
                'required': True,
            }),
            'component_item': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('المادة المكونة'),
                'required': True,
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '1.000',
                'step': '0.001',
                'min': '0.001',
                'required': True,
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('الوحدة'),
                'required': True,
            }),
            'waste_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات حول المكون'),
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة حسب الشركة
        if hasattr(self.instance, 'company') and self.instance.company:
            company = self.instance.company

            items = Item.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            self.fields['parent_item'].queryset = items
            self.fields['component_item'].queryset = items

            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

    def clean(self):
        """التحقق من صحة المكونات"""
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent_item')
        component = cleaned_data.get('component_item')

        # التحقق من عدم إضافة المادة كمكون لنفسها
        if parent and component and parent == component:
            raise ValidationError({
                'component_item': _('لا يمكن إضافة المادة كمكون لنفسها')
            })

        # التحقق من عدم إنشاء دائرة في المكونات
        if parent and component:
            # التحقق من أن المكون ليس له الأصل كمكون
            if ItemComponent.objects.filter(
                    parent_item=component,
                    component_item=parent
            ).exists():
                raise ValidationError({
                    'component_item': _('لا يمكن إنشاء دائرة في المكونات')
                })

        return cleaned_data


class ItemImportForm(forms.Form):
    """نموذج استيراد الأصناف من ملف Excel/CSV"""

    IMPORT_FORMATS = [
        ('excel', _('Excel (xlsx/xls)')),
        ('csv', _('CSV')),
    ]

    file_format = forms.ChoiceField(
        label=_('صيغة الملف'),
        choices=IMPORT_FORMATS,
        initial='excel',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

    import_file = forms.FileField(
        label=_('الملف'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv',
            'required': True,
        })
    )

    update_existing = forms.BooleanField(
        label=_('تحديث الأصناف الموجودة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch',
        }),
        help_text=_('في حالة وجود صنف بنفس الرمز، هل تريد تحديث بياناته؟')
    )

    def clean_import_file(self):
        """التحقق من صحة الملف"""
        file = self.cleaned_data.get('import_file')
        if file:
            # التحقق من حجم الملف (أقصى 5 ميجا)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('حجم الملف كبير جداً. الحد الأقصى 5 ميجابايت'))

            # التحقق من نوع الملف
            ext = file.name.split('.')[-1].lower()
            if ext not in ['xlsx', 'xls', 'csv']:
                raise ValidationError(_('صيغة الملف غير مدعومة'))

        return file
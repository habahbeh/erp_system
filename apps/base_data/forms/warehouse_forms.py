# apps/base_data/forms/warehouse_forms.py
"""
النماذج الخاصة بالمستودعات ووحدات القياس - محدث 100%
Bootstrap 5 + RTL + جميع الحقول من models.py
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import (
    Warehouse, WarehouseItem, UnitOfMeasure, Item
)
from core.models import Branch, User


class WarehouseForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المستودع - محدث 100%"""

    class Meta:
        model = Warehouse
        fields = [
            'code', 'name', 'location', 'keeper', 'warehouse_type', 'branch'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود المستودع'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستودع'),
                'required': True
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('موقع المستودع')
            }),
            'keeper': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر أمين المستودع')
            }),
            'warehouse_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر الفرع')
            })
        }
        labels = {
            'code': _('رمز المستودع'),
            'name': _('اسم المستودع'),
            'location': _('الموقع'),
            'keeper': _('أمين المستودع'),
            'warehouse_type': _('نوع المستودع'),
            'branch': _('الفرع')
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة الفروع والمستخدمين حسب الشركة
            branches = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            # فلترة حسب صلاحيات المستخدم
            if user and not user.is_superuser:
                if hasattr(user, 'profile') and hasattr(user.profile, 'allowed_branches'):
                    allowed_branches = user.profile.allowed_branches.all()
                    if allowed_branches.exists():
                        branches = branches.filter(
                            id__in=allowed_branches.values_list('id', flat=True)
                        )

            self.fields['branch'].queryset = branches

            self.fields['keeper'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

        # جعل الحقول الاختيارية
        self.fields['code'].required = False
        self.fields['location'].required = False
        self.fields['keeper'].required = False
        self.fields['branch'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار الكود"""
        code = self.cleaned_data.get('code')
        if code:
            queryset = Warehouse.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))
        return code

    def clean(self):
        cleaned_data = super().clean()
        warehouse_type = cleaned_data.get('warehouse_type')
        branch = cleaned_data.get('branch')

        # التحقق من وجود الفرع للمستودعات الفرعية
        if warehouse_type == 'branch' and not branch:
            self.add_error('branch', _('يجب تحديد الفرع للمستودعات الفرعية'))

        return cleaned_data


class UnitOfMeasureForm(forms.ModelForm):
    """نموذج إنشاء وتعديل وحدة القياس - محدث 100%"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود الوحدة'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الوحدة'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الإنجليزي'),
                'dir': 'ltr'
            })
        }
        labels = {
            'code': _('رمز الوحدة'),
            'name': _('اسم الوحدة'),
            'name_en': _('الاسم الإنجليزي')
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['code'].required = False
        self.fields['name_en'].required = False

        # تخزين الشركة للاستخدام في clean_code
        self.company = company

    def clean_code(self):
        """التحقق من عدم تكرار الكود"""
        code = self.cleaned_data.get('code')
        if code and self.company:
            queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                code=code
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))
        return code


class WarehouseItemForm(forms.ModelForm):
    """نموذج تعديل رصيد الصنف في المستودع - محدث 100%"""

    class Meta:
        model = WarehouseItem
        fields = ['quantity', 'average_cost']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'dir': 'ltr'
            }),
            'average_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'dir': 'ltr'
            })
        }
        labels = {
            'quantity': _('الكمية'),
            'average_cost': _('متوسط التكلفة')
        }

    def clean_quantity(self):
        """التحقق من صحة الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError(_('الكمية لا يمكن أن تكون سالبة'))
        return quantity

    def clean_average_cost(self):
        """التحقق من صحة التكلفة"""
        cost = self.cleaned_data.get('average_cost')
        if cost is not None and cost < 0:
            raise ValidationError(_('التكلفة لا يمكن أن تكون سالبة'))
        return cost


class WarehouseTransferForm(forms.Form):
    """نموذج التحويل بين المستودعات - محدث"""

    from_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('من مستودع'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2',
            'data-placeholder': _('اختر المستودع المصدر')
        })
    )

    to_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('إلى مستودع'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2',
            'data-placeholder': _('اختر المستودع المستقبل')
        })
    )

    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        label=_('الصنف'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2',
            'data-placeholder': _('اختر الصنف')
        })
    )

    quantity = forms.DecimalField(
        label=_('الكمية'),
        min_value=Decimal('0.001'),
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0.001',
            'dir': 'ltr'
        })
    )

    transfer_date = forms.DateField(
        label=_('تاريخ التحويل'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=lambda: forms.DateField().to_python(forms.DateField().widget.value_from_datadict({}, {}, 'transfer_date'))
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('ملاحظات على التحويل')
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة المستودعات والأصناف حسب الشركة
            warehouses = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            # فلترة حسب صلاحيات المستخدم
            if user and not user.is_superuser:
                if hasattr(user, 'profile') and hasattr(user.profile, 'allowed_warehouses'):
                    allowed_warehouses = user.profile.allowed_warehouses.all()
                    if allowed_warehouses.exists():
                        warehouses = warehouses.filter(
                            id__in=allowed_warehouses.values_list('id', flat=True)
                        )

            self.fields['from_warehouse'].queryset = warehouses
            self.fields['to_warehouse'].queryset = warehouses

            self.fields['item'].queryset = Item.objects.filter(
                company=company, is_active=True, is_inactive=False
            ).order_by('name')

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()
        from_warehouse = cleaned_data.get('from_warehouse')
        to_warehouse = cleaned_data.get('to_warehouse')
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')

        # التحقق من عدم تساوي المستودعات
        if from_warehouse and to_warehouse and from_warehouse == to_warehouse:
            raise ValidationError(_('لا يمكن التحويل إلى نفس المستودع'))

        # التحقق من توفر الكمية في المستودع المصدر
        if from_warehouse and item and quantity:
            try:
                warehouse_item = WarehouseItem.objects.get(
                    warehouse=from_warehouse,
                    item=item
                )
                if warehouse_item.quantity < quantity:
                    raise ValidationError(
                        _('الكمية المطلوبة (%(requested)s) أكبر من المتوفر في المستودع (%(available)s)') % {
                            'requested': quantity,
                            'available': warehouse_item.quantity
                        }
                    )
            except WarehouseItem.DoesNotExist:
                raise ValidationError(_('الصنف غير موجود في المستودع المصدر'))

        return cleaned_data


# النماذج السريعة
class WarehouseQuickAddForm(forms.ModelForm):
    """نموذج إضافة سريعة للمستودع"""

    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'warehouse_type', 'branch']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('كود المستودع'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم المستودع'),
                'required': True
            }),
            'warehouse_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-control': 'select2'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['branch'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

        # جعل بعض الحقول اختيارية
        self.fields['code'].required = False
        self.fields['branch'].required = False


class UnitQuickAddForm(forms.ModelForm):
    """نموذج إضافة سريعة لوحدة القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('كود الوحدة'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم الوحدة'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الاسم الإنجليزي'),
                'dir': 'ltr'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['code'].required = False
        self.fields['name_en'].required = False


# فورم الاستيراد والتصدير
class WarehouseImportForm(forms.Form):
    """نموذج استيراد بيانات المستودعات"""

    IMPORT_TYPE_CHOICES = [
        ('warehouses', _('المستودعات')),
        ('inventory', _('الأرصدة')),
        ('units', _('وحدات القياس')),
    ]

    import_type = forms.ChoiceField(
        choices=IMPORT_TYPE_CHOICES,
        label=_('نوع البيانات'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    file = forms.FileField(
        label=_('ملف البيانات'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        }),
        help_text=_('يدعم Excel وCSV فقط')
    )

    update_existing = forms.BooleanField(
        label=_('تحديث البيانات الموجودة'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('تحديث البيانات في حالة وجود كود مطابق')
    )

    skip_errors = forms.BooleanField(
        label=_('تجاهل الأخطاء والمتابعة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('متابعة الاستيراد حتى مع وجود أخطاء')
    )

    validate_data = forms.BooleanField(
        label=_('التحقق من البيانات'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('التحقق من صحة البيانات قبل الاستيراد')
    )

    def clean_file(self):
        """التحقق من صحة الملف"""
        file = self.cleaned_data.get('file')
        if file:
            # التحقق من نوع الملف
            if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise ValidationError(_('نوع الملف غير مدعوم. يجب أن يكون Excel أو CSV'))

            # التحقق من حجم الملف (أقل من 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError(_('حجم الملف كبير جداً. يجب أن يكون أقل من 10MB'))

        return file


class InventoryAdjustmentForm(forms.Form):
    """نموذج تسوية المخزون"""

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('المستودع'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2'
        })
    )

    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        label=_('الصنف'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2'
        })
    )

    current_quantity = forms.DecimalField(
        label=_('الكمية الحالية'),
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': True,
            'dir': 'ltr'
        })
    )

    actual_quantity = forms.DecimalField(
        label=_('الكمية الفعلية'),
        decimal_places=3,
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0',
            'dir': 'ltr'
        })
    )

    adjustment_date = forms.DateField(
        label=_('تاريخ التسوية'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    reason = forms.ChoiceField(
        label=_('سبب التسوية'),
        choices=[
            ('damage', _('تلف')),
            ('loss', _('فقدان')),
            ('theft', _('سرقة')),
            ('expired', _('انتهاء صلاحية')),
            ('count_error', _('خطأ في الجرد')),
            ('other', _('أخرى')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('ملاحظات على التسوية')
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['item'].queryset = Item.objects.filter(
                company=company, is_active=True, is_inactive=False
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        current_qty = cleaned_data.get('current_quantity', 0)
        actual_qty = cleaned_data.get('actual_quantity', 0)

        # حساب الفرق
        difference = actual_qty - current_qty
        cleaned_data['adjustment_quantity'] = difference
        cleaned_data['adjustment_type'] = 'increase' if difference > 0 else 'decrease'

        return cleaned_data


class StockReportForm(forms.Form):
    """نموذج تقارير المخزون"""

    report_type = forms.ChoiceField(
        label=_('نوع التقرير'),
        choices=[
            ('current_stock', _('المخزون الحالي')),
            ('low_stock', _('المخزون المنخفض')),
            ('zero_stock', _('المخزون الصفري')),
            ('movements', _('حركات المخزون')),
            ('valuation', _('تقييم المخزون')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        required=False,
        empty_label=_('جميع المستودعات'),
        label=_('المستودع'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2'
        })
    )

    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label=_('جميع التصنيفات'),
        label=_('تصنيف الأصناف'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2'
        })
    )

    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    export_format = forms.ChoiceField(
        label=_('صيغة التصدير'),
        choices=[
            ('html', _('عرض على الشاشة')),
            ('pdf', _('PDF')),
            ('excel', _('Excel')),
        ],
        initial='html',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            # استيراد ItemCategory
            from ..models import ItemCategory
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'name')

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))

        return cleaned_data
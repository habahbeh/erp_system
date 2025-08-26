# apps/base_data/forms/warehouse_forms.py
"""
النماذج الخاصة بالمستودعات ووحدات القياس
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import (
    Warehouse, WarehouseItem, UnitOfMeasure, Item,
    Branch, User
)


class WarehouseForm(forms.ModelForm):
    """نموذج إنشاء وتعديل المستودع"""

    class Meta:
        model = Warehouse
        fields = [
            'code', 'name', 'warehouse_type', 'branch',
            'keeper', 'location', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'كود المستودع'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المستودع'
            }),
            'warehouse_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select'
            }),
            'keeper': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موقع المستودع'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة الفروع والمستخدمين حسب الشركة
            self.fields['branch'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['keeper'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

        # جعل الحقول اختيارية
        self.fields['branch'].required = False
        self.fields['keeper'].required = False
        self.fields['location'].required = False
        self.fields['notes'].required = False
        self.fields['code'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار الكود"""
        code = self.cleaned_data.get('code')
        if code:
            # التحقق من التكرار
            queryset = Warehouse.objects.filter(
                company=self.instance.company if self.instance.pk else None,
                code=code
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))

        return code


class UnitOfMeasureForm(forms.ModelForm):
    """نموذج إنشاء وتعديل وحدة القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'كود الوحدة'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الوحدة'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الإنجليزي'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['code'].required = False
        self.fields['name_en'].required = False
        self.fields['notes'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار الكود"""
        code = self.cleaned_data.get('code')
        if code and self.user:
            # التحقق من التكرار
            queryset = UnitOfMeasure.objects.filter(
                company=self.user.company,
                code=code
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))

        return code


class WarehouseItemForm(forms.ModelForm):
    """نموذج تعديل رصيد الصنف في المستودع"""

    class Meta:
        model = WarehouseItem
        fields = ['quantity', 'average_cost']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'average_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['last_purchase_cost'].required = False
        self.fields['last_sale_cost'].required = False
        self.fields['notes'].required = False

    def clean_quantity(self):
        """التحقق من صحة الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError(_('الكمية لا يمكن أن تكون سالبة'))
        return quantity


class WarehouseFilterForm(forms.Form):
    """نموذج فلترة المستودعات"""

    WAREHOUSE_TYPE_CHOICES = [
        ('', 'جميع الأنواع'),
        ('main', 'مستودع رئيسي'),
        ('branch', 'مستودع فرع'),
        ('transit', 'مستودع ترانزيت'),
        ('damaged', 'مستودع تالف'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'البحث في الكود أو الاسم أو الموقع...',
            'class': 'form-control'
        })
    )

    warehouse_type = forms.ChoiceField(
        choices=WAREHOUSE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        empty_label="جميع الفروع",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    keeper = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="جميع الأمناء",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_active = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[
                ('', 'الكل'),
                ('true', 'نشط'),
                ('false', 'غير نشط')
            ],
            attrs={'class': 'form-select'}
        )
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['branch'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['keeper'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')


class WarehouseTransferForm(forms.Form):
    """نموذج التحويل بين المستودعات"""

    from_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('من مستودع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    to_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('إلى مستودع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        label=_('الصنف'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    quantity = forms.DecimalField(
        label=_('الكمية'),
        min_value=Decimal('0.01'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات على التحويل'
        })
    )

    transfer_date = forms.DateField(
        label=_('تاريخ التحويل'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة المستودعات والأصناف حسب الشركة
            active_warehouses = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['from_warehouse'].queryset = active_warehouses
            self.fields['to_warehouse'].queryset = active_warehouses

            self.fields['item'].queryset = Item.objects.filter(
                company=company, is_active=True
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
                        _('الكمية المطلوبة أكبر من المتوفر في المستودع (متوفر: %(available)s)') % {
                            'available': warehouse_item.quantity
                        }
                    )
            except WarehouseItem.DoesNotExist:
                raise ValidationError(_('الصنف غير موجود في المستودع المصدر'))

        return cleaned_data


class WarehouseImportForm(forms.Form):
    """نموذج استيراد بيانات المستودعات"""

    IMPORT_TYPE_CHOICES = [
        ('warehouses', 'المستودعات'),
        ('inventory', 'الأرصدة'),
        ('units', 'وحدات القياس'),
    ]

    import_type = forms.ChoiceField(
        choices=IMPORT_TYPE_CHOICES,
        label=_('نوع البيانات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    file = forms.FileField(
        label=_('ملف البيانات'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    update_existing = forms.BooleanField(
        label=_('تحديث البيانات الموجودة'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    skip_errors = forms.BooleanField(
        label=_('تجاهل الأخطاء والمتابعة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        """التحقق من صحة الملف"""
        file = self.cleaned_data.get('file')
        if file:
            # التحقق من نوع الملف
            if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise ValidationError(_('نوع الملف غير مدعوم. يجب أن يكون Excel أو CSV'))

            # التحقق من حجم الملف (أقل من 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('حجم الملف كبير جداً. يجب أن يكون أقل من 5MB'))

        return file


class WarehouseQuickAddForm(forms.ModelForm):
    """نموذج إضافة سريعة للمستودع"""

    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'warehouse_type', 'branch']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'كود المستودع'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'اسم المستودع'
            }),
            'warehouse_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select form-select-sm'
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
                'placeholder': 'كود الوحدة'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'اسم الوحدة'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'الاسم الإنجليزي'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['code'].required = False
        self.fields['name_en'].required = False
# apps/assets/forms/asset_forms.py
"""
نماذج الأصول الثابتة
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

from ..models import (
    AssetCategory,
    DepreciationMethod,
    AssetCondition,
    Asset,
    AssetAttachment,
    AssetValuation,
)
from apps.accounting.models import Account, CostCenter


class AssetCategoryForm(forms.ModelForm):
    """نموذج فئة الأصول"""

    class Meta:
        model = AssetCategory
        fields = [
            'code', 'name', 'name_en', 'parent',
            'asset_account', 'accumulated_depreciation_account',
            'depreciation_expense_account',
            'default_depreciation_method', 'default_useful_life_months',
            'default_salvage_value_rate', 'description'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: BLDG, VEH, FURN'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: مباني، سيارات، أثاث'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Buildings, Vehicles, Furniture'
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'asset_account': forms.Select(attrs={'class': 'form-select'}),
            'accumulated_depreciation_account': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'default_depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'default_useful_life_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'بالأشهر - مثال: 60'
            }),
            'default_salvage_value_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0-100',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الحسابات حسب الشركة
            self.fields['asset_account'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='assets',
                is_active=True
            )
            self.fields['accumulated_depreciation_account'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='assets',
                is_active=True
            )
            self.fields['depreciation_expense_account'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='expenses',
                is_active=True
            )
            self.fields['parent'].queryset = AssetCategory.objects.filter(
                company=self.company,
                is_active=True
            )

            # استبعاد الفئة نفسها من قائمة الآباء
            if self.instance.pk:
                self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                    pk=self.instance.pk
                )


class DepreciationMethodForm(forms.ModelForm):
    """نموذج طريقة الإهلاك"""

    class Meta:
        model = DepreciationMethod
        fields = ['code', 'name', 'name_en', 'method_type', 'rate_percentage', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'method_type': forms.Select(attrs={'class': 'form-select'}),
            'rate_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'للقسط المتناقص فقط - مثال: 200'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AssetConditionForm(forms.ModelForm):
    """نموذج حالة الأصل"""

    class Meta:
        model = AssetCondition
        fields = ['name', 'name_en', 'color_code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'color_code': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AssetForm(forms.ModelForm):
    """نموذج الأصل الثابت - شامل"""

    class Meta:
        model = Asset
        fields = [
            'name', 'name_en', 'category', 'condition', 'status', 'depreciation_status',
            'purchase_date', 'purchase_invoice_number', 'supplier', 'currency',
            'original_cost', 'salvage_value',
            'depreciation_method', 'useful_life_months', 'depreciation_start_date',
            'total_expected_units', 'unit_name',
            'cost_center', 'responsible_employee', 'physical_location',
            'serial_number', 'model', 'manufacturer', 'barcode',
            'warranty_start_date', 'warranty_end_date', 'warranty_provider',
            'insurance_status', 'is_leased',
            'description', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: سيارة هيونداي أزيرا 2023'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hyundai Azera 2023'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_status': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاتورة'
            }),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'original_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'salvage_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'useful_life_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'بالأشهر - مثال: 60'
            }),
            'depreciation_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_expected_units': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'لوحدات الإنتاج فقط'
            }),
            'unit_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'كيلومتر، ساعة، قطعة'
            }),
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'responsible_employee': forms.Select(attrs={'class': 'form-select'}),
            'physical_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مبنى أ - طابق 3 - مكتب 305'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرقم التسلسلي'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الموديل'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الشركة المصنعة'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الباركود'
            }),
            'warranty_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warranty_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warranty_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مزود الضمان'
            }),
            'insurance_status': forms.Select(attrs={'class': 'form-select'}),
            'is_leased': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية حسب الشركة
            self.fields['category'].queryset = AssetCategory.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['supplier'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='liabilities',
                is_active=True
            )

            # تصفية العملات
            from apps.core.models import Currency
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)

            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['responsible_employee'].queryset = self.company.user_set.filter(
                is_active=True
            )

        # إضافة علامة * للحقول المطلوبة
        required_fields = [
            'name', 'category', 'purchase_date', 'original_cost', 'currency',
            'depreciation_method', 'useful_life_months', 'depreciation_start_date'
        ]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = True

    def clean(self):
        cleaned_data = super().clean()

        salvage_value = cleaned_data.get('salvage_value')
        original_cost = cleaned_data.get('original_cost')
        depreciation_method = cleaned_data.get('depreciation_method')
        total_expected_units = cleaned_data.get('total_expected_units')
        warranty_start_date = cleaned_data.get('warranty_start_date')
        warranty_end_date = cleaned_data.get('warranty_end_date')

        # التحقق من القيمة المتبقية
        if salvage_value and original_cost:
            if salvage_value >= original_cost:
                raise ValidationError({
                    'salvage_value': _('القيمة المتبقية يجب أن تكون أقل من التكلفة الأصلية')
                })

        # التحقق من وحدات الإنتاج
        if depreciation_method and depreciation_method.method_type == 'units_of_production':
            if not total_expected_units:
                raise ValidationError({
                    'total_expected_units': _('يجب تحديد إجمالي الوحدات المتوقعة لطريقة وحدات الإنتاج')
                })

        # التحقق من تواريخ الضمان
        if warranty_start_date and warranty_end_date:
            if warranty_end_date < warranty_start_date:
                raise ValidationError({
                    'warranty_end_date': _('تاريخ انتهاء الضمان يجب أن يكون بعد تاريخ البداية')
                })

        return cleaned_data


class AssetAttachmentForm(forms.ModelForm):
    """نموذج مرفق الأصل"""

    class Meta:
        model = AssetAttachment
        fields = ['title', 'attachment_type', 'file', 'issue_date', 'expiry_date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان المرفق'
            }),
            'attachment_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')

        if issue_date and expiry_date:
            if expiry_date < issue_date:
                raise ValidationError({
                    'expiry_date': _('تاريخ الانتهاء يجب أن يكون بعد تاريخ الإصدار')
                })

        return cleaned_data


class AssetValuationForm(forms.ModelForm):
    """نموذج إعادة تقييم الأصل"""

    class Meta:
        model = AssetValuation
        fields = [
            'valuation_date', 'new_value', 'reason',
            'valuator_name', 'valuation_report', 'notes'
        ]
        widgets = {
            'valuation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'new_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'سبب إعادة التقييم'
            }),
            'valuator_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المُقيّم'
            }),
            'valuation_report': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class AssetFilterForm(forms.Form):
    """نموذج فلترة الأصول"""

    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.none(),
        required=False,
        empty_label='جميع الفئات',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'جميع الحالات')] + Asset.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.none(),
        required=False,
        empty_label='جميع مراكز التكلفة',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    purchase_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )
    purchase_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'بحث برقم الأصل أو الاسم أو الباركود'
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['category'].queryset = AssetCategory.objects.filter(
                company=company,
                is_active=True
            )
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=company,
                is_active=True
            )


class AssetDepreciationCalculationForm(forms.Form):
    """نموذج احتساب الإهلاك"""

    calculation_date = forms.DateField(
        label=_('تاريخ الاحتساب'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=datetime.date.today
    )

    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        label=_('أصول محددة (اتركه فارغاً لجميع الأصول النشطة)'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '10'
        })
    )

    units_used = forms.IntegerField(
        required=False,
        label=_('الوحدات المستخدمة (لوحدات الإنتاج فقط)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'عدد الوحدات'
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['assets'].queryset = Asset.objects.filter(
                company=company,
                status='active',
                is_active=True
            ).select_related('category')
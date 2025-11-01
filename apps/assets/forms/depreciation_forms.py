# apps/assets/forms/depreciation_forms.py
"""
نماذج الإهلاك
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

from ..models import AssetDepreciation, Asset, DepreciationMethod
from apps.accounting.models import FiscalYear, AccountingPeriod


class AssetDepreciationForm(forms.ModelForm):
    """نموذج عرض قيد الإهلاك - معظم الحقول للقراءة فقط"""

    class Meta:
        model = AssetDepreciation
        fields = [
            'asset', 'depreciation_date',
            'fiscal_year', 'period', 'depreciation_amount',
            'accumulated_depreciation_before', 'accumulated_depreciation_after',
            'book_value_after', 'units_used_in_period',
            'journal_entry', 'is_posted', 'notes'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select', 'disabled': True}),
            'depreciation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'readonly': True
            }),
            'fiscal_year': forms.Select(attrs={'class': 'form-select', 'disabled': True}),
            'period': forms.Select(attrs={'class': 'form-select', 'disabled': True}),
            'depreciation_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'readonly': True
            }),
            'accumulated_depreciation_before': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'readonly': True
            }),
            'accumulated_depreciation_after': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'readonly': True
            }),
            'book_value_after': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'readonly': True
            }),
            'units_used_in_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'لوحدات الإنتاج فقط'
            }),
            'journal_entry': forms.Select(attrs={'class': 'form-select', 'disabled': True}),
            'is_posted': forms.CheckboxInput(attrs={'class': 'form-check-input', 'disabled': True}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'readonly': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جميع الحقول للقراءة فقط ما عدا units_used_in_period و notes
        for field_name in self.fields:
            if field_name not in ['units_used_in_period', 'notes']:
                self.fields[field_name].disabled = True


class BulkDepreciationCalculationForm(forms.Form):
    """نموذج احتساب الإهلاك الجماعي"""

    period_year = forms.IntegerField(
        label=_('السنة'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2099'
        }),
        help_text=_('سنة الفترة المالية')
    )

    period_month = forms.IntegerField(
        label=_('الشهر'),
        widget=forms.Select(choices=[
            (1, _('يناير')), (2, _('فبراير')), (3, _('مارس')),
            (4, _('أبريل')), (5, _('مايو')), (6, _('يونيو')),
            (7, _('يوليو')), (8, _('أغسطس')), (9, _('سبتمبر')),
            (10, _('أكتوبر')), (11, _('نوفمبر')), (12, _('ديسمبر'))
        ], attrs={'class': 'form-select'}),
        help_text=_('شهر الفترة المالية')
    )

    calculation_date = forms.DateField(
        required=False,
        label=_('تاريخ الاحتساب'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text=_('تاريخ احتساب الإهلاك')
    )

    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        label=_('أصول محددة'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '10',
            'data-placeholder': 'اتركه فارغاً لجميع الأصول النشطة'
        }),
        help_text=_('اتركه فارغاً لاحتساب إهلاك جميع الأصول النشطة')
    )

    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('فئة محددة'),
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('احتساب الإهلاك لفئة معينة فقط')
    )

    location = forms.CharField(
        required=False,
        label=_('الموقع الفعلي'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث عن موقع'
        }),
        help_text=_('تصفية حسب الموقع الفعلي (نص)')
    )

    department = forms.CharField(
        required=False,
        label=_('القسم'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث عن قسم'
        }),
        help_text=_('تصفية حسب القسم (نص)')
    )

    depreciation_method = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('طريقة الإهلاك'),
        empty_label=_('جميع الطرق'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('تصفية حسب طريقة الإهلاك')
    )

    force_recalculate = forms.BooleanField(
        required=False,
        initial=False,
        label=_('إعادة الحساب القسري'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('إعادة احتساب الإهلاك حتى لو كان محسوباً مسبقاً لهذه الفترة')
    )

    auto_post = forms.BooleanField(
        required=False,
        initial=False,
        label=_('ترحيل القيود تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('ترحيل القيود المحاسبية للإهلاك تلقائياً بعد الاحتساب')
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # فقط الأصول النشطة القابلة للإهلاك
            self.fields['assets'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            ).select_related('category', 'depreciation_method').order_by('asset_number')

            # الفئات
            from ..models import AssetCategory
            self.fields['category'].queryset = AssetCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

        # طرق الإهلاك (system-wide, no company filter)
        from ..models import DepreciationMethod
        self.fields['depreciation_method'].queryset = DepreciationMethod.objects.filter(
            is_active=True
        ).order_by('name')

        # تعيين التاريخ الافتراضي لنهاية الشهر الماضي
        today = datetime.date.today()
        last_month_end = (today.replace(day=1) - datetime.timedelta(days=1))
        self.fields['calculation_date'].initial = last_month_end

        # تعيين السنة والشهر الافتراضي
        self.fields['period_year'].initial = last_month_end.year
        self.fields['period_month'].initial = last_month_end.month

    def clean(self):
        cleaned_data = super().clean()
        calculation_date = cleaned_data.get('calculation_date')
        assets = cleaned_data.get('assets')
        category = cleaned_data.get('category')

        # التحقق من التاريخ
        if calculation_date:
            if calculation_date > datetime.date.today():
                raise ValidationError({
                    'calculation_date': _('لا يمكن احتساب الإهلاك لتاريخ مستقبلي')
                })

        # التحقق من وجود أصول
        if self.company:
            if assets and assets.count() == 0 and not category:
                raise ValidationError(
                    _('يجب اختيار أصول أو فئة محددة')
                )

        return cleaned_data


class SingleAssetDepreciationCalculationForm(forms.Form):
    """نموذج احتساب إهلاك أصل واحد"""

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        label=_('الأصل'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    calculation_date = forms.DateField(
        label=_('تاريخ الاحتساب'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
    )

    units_used = forms.IntegerField(
        required=False,
        label=_('الوحدات المستخدمة'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'لوحدات الإنتاج فقط'
        }),
        help_text=_('لطريقة وحدات الإنتاج فقط')
    )

    auto_post = forms.BooleanField(
        required=False,
        initial=False,
        label=_('ترحيل القيد تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            ).select_related('category', 'depreciation_method')

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        calculation_date = cleaned_data.get('calculation_date')
        units_used = cleaned_data.get('units_used')

        if calculation_date and calculation_date > datetime.date.today():
            raise ValidationError({
                'calculation_date': _('لا يمكن احتساب الإهلاك لتاريخ مستقبلي')
            })

        # التحقق من وحدات الإنتاج
        if asset and asset.depreciation_method.method_type == 'units_of_production':
            if not units_used:
                raise ValidationError({
                    'units_used': _('يجب تحديد الوحدات المستخدمة لطريقة وحدات الإنتاج')
                })
            if units_used <= 0:
                raise ValidationError({
                    'units_used': _('يجب أن تكون الوحدات المستخدمة أكبر من صفر')
                })

        return cleaned_data


class ReverseDepreciationForm(forms.Form):
    """نموذج عكس قيد إهلاك"""

    depreciation_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    reversal_date = forms.DateField(
        label=_('تاريخ العكس'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.date.today
    )

    reason = forms.CharField(
        label=_('سبب العكس'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'اذكر سبب عكس قيد الإهلاك'
        })
    )

    auto_recalculate = forms.BooleanField(
        required=False,
        initial=True,
        label=_('إعادة الحساب تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('إعادة احتساب الإهلاك بعد العكس بالقيم الصحيحة')
    )

    def __init__(self, *args, **kwargs):
        self.depreciation = kwargs.pop('depreciation', None)
        super().__init__(*args, **kwargs)

        if self.depreciation:
            self.fields['depreciation_id'].initial = self.depreciation.id

    def clean(self):
        cleaned_data = super().clean()
        reversal_date = cleaned_data.get('reversal_date')
        reason = cleaned_data.get('reason')

        # التحقق من التاريخ
        if reversal_date:
            if reversal_date > datetime.date.today():
                raise ValidationError({
                    'reversal_date': _('لا يمكن عكس القيد بتاريخ مستقبلي')
                })

            # التحقق من أن تاريخ العكس ليس قبل تاريخ القيد الأصلي
            if self.depreciation and reversal_date < self.depreciation.period_date:
                raise ValidationError({
                    'reversal_date': _('تاريخ العكس لا يمكن أن يكون قبل تاريخ القيد الأصلي')
                })

        # التحقق من السبب
        if not reason or len(reason.strip()) < 10:
            raise ValidationError({
                'reason': _('يجب إدخال سبب مفصل للعكس (10 أحرف على الأقل)')
            })

        return cleaned_data


class DepreciationFilterForm(forms.Form):
    """نموذج فلترة الإهلاكات"""

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label=_('جميع الأصول'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    fiscal_year = forms.ModelChoiceField(
        queryset=FiscalYear.objects.none(),
        required=False,
        empty_label=_('جميع السنوات المالية'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    period = forms.ModelChoiceField(
        queryset=AccountingPeriod.objects.none(),
        required=False,
        empty_label=_('جميع الفترات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )

    is_reversed = forms.ChoiceField(
        choices=[
            ('', _('الكل')),
            ('yes', _('معكوسة فقط')),
            ('no', _('غير معكوسة فقط'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    posted_only = forms.BooleanField(
        required=False,
        label=_('المرحّلة فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category').order_by('asset_number')

            self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(
                company=self.company
            ).order_by('-start_date')

            # الفترات تعتمد على السنة المحددة
            self.fields['period'].queryset = AccountingPeriod.objects.filter(
                fiscal_year__company=self.company
            ).select_related('fiscal_year').order_by('-start_date')

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to:
            if date_to < date_from:
                raise ValidationError({
                    'date_to': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        return cleaned_data

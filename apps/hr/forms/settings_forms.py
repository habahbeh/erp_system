# apps/hr/forms/settings_forms.py
"""
نماذج إعدادات الموارد البشرية
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import LeaveType, HRSettings, SocialSecuritySettings, PayrollAccountMapping
from apps.accounting.models import Account


class LeaveTypeForm(forms.ModelForm):
    """نموذج نوع الإجازة"""

    class Meta:
        model = LeaveType
        fields = [
            'code', 'name', 'name_en', 'is_paid', 'affects_salary',
            'requires_approval', 'requires_attachment', 'default_days',
            'max_consecutive_days', 'allow_negative_balance', 'carry_forward',
            'description', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز نوع الإجازة...',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم نوع الإجازة...',
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave Type Name...',
                'dir': 'ltr',
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'affects_salary': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'requires_attachment': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'default_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'max_consecutive_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'allow_negative_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'carry_forward': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'وصف نوع الإجازة...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # الحقول الاختيارية
        optional_fields = ['name_en', 'description']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['is_paid'].initial = True
            self.fields['requires_approval'].initial = True
            self.fields['default_days'].initial = 0
            self.fields['max_consecutive_days'].initial = 0

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.company:
            qs = LeaveType.objects.filter(company=self.company, code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رمز نوع الإجازة موجود مسبقاً'))
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class HRSettingsForm(forms.ModelForm):
    """نموذج إعدادات الموارد البشرية"""

    class Meta:
        model = HRSettings
        fields = [
            'default_working_hours_per_day', 'default_working_days_per_month',
            'overtime_regular_rate', 'overtime_holiday_rate',
            'default_annual_leave_days', 'default_sick_leave_days',
            'carry_forward_leave', 'max_carry_forward_days',
            'sick_leave_medical_certificate_days',
            'default_probation_days', 'default_notice_period_days',
            'max_advance_percentage', 'max_installments',
            'fiscal_year_start_month', 'auto_create_journal_entries'
        ]
        widgets = {
            'default_working_hours_per_day': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '1',
                'max': '24',
            }),
            'default_working_days_per_month': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'max': '31',
            }),
            'overtime_regular_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '1',
            }),
            'overtime_holiday_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '1',
            }),
            'default_annual_leave_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'default_sick_leave_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'carry_forward_leave': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'max_carry_forward_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'sick_leave_medical_certificate_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'default_probation_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'default_notice_period_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'max_advance_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'max_installments': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
            }),
            'fiscal_year_start_month': forms.Select(attrs={
                'class': 'form-select',
            }, choices=[
                (1, 'يناير'), (2, 'فبراير'), (3, 'مارس'), (4, 'أبريل'),
                (5, 'مايو'), (6, 'يونيو'), (7, 'يوليو'), (8, 'أغسطس'),
                (9, 'سبتمبر'), (10, 'أكتوبر'), (11, 'نوفمبر'), (12, 'ديسمبر')
            ]),
            'auto_create_journal_entries': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)


class SocialSecuritySettingsForm(forms.ModelForm):
    """نموذج إعدادات الضمان الاجتماعي"""

    class Meta:
        model = SocialSecuritySettings
        fields = [
            'employee_contribution_rate', 'company_contribution_rate',
            'minimum_insurable_salary', 'maximum_insurable_salary',
            'is_active', 'effective_date'
        ]
        widgets = {
            'employee_contribution_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'company_contribution_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'minimum_insurable_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
            }),
            'maximum_insurable_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # الحقول الاختيارية
        optional_fields = ['minimum_insurable_salary', 'maximum_insurable_salary', 'effective_date']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('minimum_insurable_salary')
        max_salary = cleaned_data.get('maximum_insurable_salary')

        if min_salary and max_salary and min_salary > max_salary:
            raise ValidationError({
                'maximum_insurable_salary': _('الحد الأقصى يجب أن يكون أكبر من الحد الأدنى')
            })

        return cleaned_data


class PayrollAccountMappingForm(forms.ModelForm):
    """نموذج ربط حسابات الرواتب"""

    class Meta:
        model = PayrollAccountMapping
        fields = ['component', 'account', 'is_active', 'notes']
        widgets = {
            'component': forms.Select(attrs={
                'class': 'form-select',
            }),
            'account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الحساب المحاسبي...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الحسابات حسب الشركة
            self.fields['account'].queryset = Account.objects.filter(
                company=self.company,
                is_suspended=False,
                accept_entries=True
            ).order_by('code')

        # الحقول الاختيارية
        self.fields['notes'].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        component = cleaned_data.get('component')

        if component and self.company:
            qs = PayrollAccountMapping.objects.filter(
                company=self.company,
                component=component
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({
                    'component': _('هذا المكون مربوط بحساب محاسبي مسبقاً')
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance

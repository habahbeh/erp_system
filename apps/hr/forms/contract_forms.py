# apps/hr/forms/contract_forms.py
"""
نماذج العقود والعلاوات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date

from ..models import EmployeeContract, SalaryIncrement, Employee


class EmployeeContractForm(forms.ModelForm):
    """نموذج عقد العمل"""

    class Meta:
        model = EmployeeContract
        fields = [
            'employee', 'contract_type', 'start_date', 'end_date',
            'contract_salary', 'probation_period', 'notice_period',
            'status', 'contract_file', 'terms_and_conditions',
            'signed_date', 'notes', 'is_active'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الموظف...',
            }),
            'contract_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'contract_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'probation_period': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'notice_period': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'contract_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }),
            'terms_and_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'الشروط والأحكام...',
            }),
            'signed_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الموظفين حسب الشركة
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                status='active'
            ).order_by('first_name', 'last_name')

        # الحقول الاختيارية
        optional_fields = [
            'end_date', 'contract_file', 'terms_and_conditions',
            'signed_date', 'notes'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['status'].initial = 'draft'
            self.fields['start_date'].initial = date.today()
            self.fields['probation_period'].initial = 90
            self.fields['notice_period'].initial = 30

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        contract_type = cleaned_data.get('contract_type')

        # التحقق من التواريخ
        if start_date and end_date and end_date <= start_date:
            raise ValidationError({
                'end_date': _('تاريخ نهاية العقد يجب أن يكون بعد تاريخ البداية')
            })

        # إذا كان العقد محدد المدة يجب أن يكون له تاريخ انتهاء
        if contract_type == 'fixed_term' and not end_date:
            raise ValidationError({
                'end_date': _('العقود محددة المدة يجب أن يكون لها تاريخ انتهاء')
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if self.user and not instance.pk:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class SalaryIncrementForm(forms.ModelForm):
    """نموذج العلاوة"""

    class Meta:
        model = SalaryIncrement
        fields = [
            'employee', 'increment_type', 'is_percentage',
            'increment_amount', 'effective_date', 'reason', 'notes', 'is_active'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الموظف...',
            }),
            'increment_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_percentage': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'increment_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'سبب العلاوة...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الموظفين حسب الشركة
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                status='active'
            ).order_by('first_name', 'last_name')

        # الحقول الاختيارية
        optional_fields = ['reason', 'notes']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['effective_date'].initial = date.today()
            self.fields['increment_type'].initial = 'annual'

    def clean_increment_amount(self):
        amount = self.cleaned_data.get('increment_amount')
        is_percentage = self.data.get('is_percentage') == 'on'

        if amount and amount <= 0:
            raise ValidationError(_('قيمة العلاوة يجب أن تكون أكبر من صفر'))

        if is_percentage and amount and amount > 100:
            raise ValidationError(_('النسبة المئوية لا يمكن أن تتجاوز 100%'))

        return amount

    def clean(self):
        cleaned_data = super().clean()
        effective_date = cleaned_data.get('effective_date')

        # التحقق من تاريخ السريان
        if effective_date and effective_date < date.today():
            self.add_error('effective_date', _('تحذير: تاريخ السريان في الماضي'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if self.user and not instance.pk:
            instance.created_by = self.user

        # حساب الراتب القديم والجديد
        if instance.employee:
            instance.old_salary = instance.employee.basic_salary
            if instance.is_percentage:
                increment_value = (instance.old_salary * instance.increment_amount) / 100
            else:
                increment_value = instance.increment_amount
            instance.new_salary = instance.old_salary + increment_value

        if commit:
            instance.save()
        return instance

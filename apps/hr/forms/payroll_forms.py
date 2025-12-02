# apps/hr/forms/payroll_forms.py
"""
نماذج الرواتب - المرحلة الثالثة
Payroll Forms - Phase 3
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from calendar import monthrange

from ..models import (
    Payroll, PayrollDetail, PayrollAllowance, PayrollDeduction,
    Employee, Advance, AdvanceInstallment
)


class PayrollForm(forms.ModelForm):
    """نموذج مسير الرواتب"""

    class Meta:
        model = Payroll
        fields = [
            'branch', 'period_year', 'period_month',
            'from_date', 'to_date', 'notes'
        ]
        widgets = {
            'branch': forms.Select(attrs={
                'class': 'form-select',
            }),
            'period_year': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': 2020,
                'max': 2100,
            }),
            'period_month': forms.Select(attrs={
                'class': 'form-select',
            }),
            'from_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'to_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تعيين السنة والشهر الافتراضي
        today = date.today()
        if not self.instance.pk:
            self.fields['period_year'].initial = today.year
            self.fields['period_month'].initial = today.month
            # حساب التواريخ
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month, monthrange(today.year, today.month)[1])
            self.fields['from_date'].initial = first_day
            self.fields['to_date'].initial = last_day

        if self.company:
            from apps.core.models import Branch
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )

        self.fields['notes'].required = False
        self.fields['branch'].required = False

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('period_year')
        month = cleaned_data.get('period_month')
        branch = cleaned_data.get('branch')

        if year and month and self.company:
            # التحقق من عدم وجود مسير سابق لنفس الفترة
            existing = Payroll.objects.filter(
                company=self.company,
                period_year=year,
                period_month=month,
                branch=branch
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    _('يوجد كشف راتب مسبق لهذه الفترة')
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
            # توليد رقم المسير
            if not instance.number:
                from apps.core.models import NumberingSequence
                instance.number = NumberingSequence.get_next_number(
                    self.company, 'payroll'
                )
        if commit:
            instance.save()
        return instance


class PayrollDetailForm(forms.ModelForm):
    """نموذج تفاصيل راتب الموظف"""

    class Meta:
        model = PayrollDetail
        fields = [
            'employee', 'basic_salary', 'working_days', 'actual_days', 'absent_days',
            'housing_allowance', 'transport_allowance', 'phone_allowance',
            'food_allowance', 'other_allowances',
            'overtime_hours', 'overtime_amount',
            'absence_deduction', 'late_deduction', 'loan_deduction',
            'social_security_employee', 'income_tax', 'other_deductions',
            'payment_method', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'working_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
            }),
            'actual_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
            }),
            'absent_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
            }),
            'housing_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'transport_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'phone_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'food_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'other_allowances': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'overtime_hours': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.25',
            }),
            'overtime_amount': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'absence_deduction': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'late_deduction': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'loan_deduction': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'social_security_employee': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'income_tax': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'other_deductions': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.payroll = kwargs.pop('payroll', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

        self.fields['notes'].required = False


class PayrollProcessForm(forms.Form):
    """نموذج معالجة مسير الرواتب"""

    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('القسم'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    include_inactive = forms.BooleanField(
        required=False,
        initial=False,
        label=_('تضمين الموظفين غير النشطين'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    recalculate = forms.BooleanField(
        required=False,
        initial=False,
        label=_('إعادة الحساب للموظفين الموجودين'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            from ..models import Department
            self.fields['department'].queryset = Department.objects.filter(
                company=self.company,
                is_active=True
            )


class PayrollApproveForm(forms.Form):
    """نموذج اعتماد مسير الرواتب"""

    confirm = forms.BooleanField(
        required=True,
        label=_('أؤكد اعتماد هذا المسير'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    create_journal_entry = forms.BooleanField(
        required=False,
        initial=True,
        label=_('إنشاء قيد محاسبي'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class PayrollPaymentForm(forms.Form):
    """نموذج صرف الرواتب"""

    payment_date = forms.DateField(
        label=_('تاريخ الصرف'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    payment_method = forms.ChoiceField(
        label=_('طريقة الدفع'),
        choices=PayrollDetail.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    payment_reference = forms.CharField(
        required=False,
        max_length=100,
        label=_('مرجع الدفع'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('رقم الشيك أو التحويل...'),
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_date'].initial = date.today()


class BulkPayrollDetailForm(forms.Form):
    """نموذج إضافة جماعية لتفاصيل الرواتب"""

    employees = forms.ModelMultipleChoiceField(
        queryset=None,
        label=_('الموظفين'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'multiple': 'multiple',
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.payroll = kwargs.pop('payroll', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # الموظفين غير الموجودين في المسير
            existing_employees = []
            if self.payroll:
                existing_employees = self.payroll.details.values_list('employee_id', flat=True)

            self.fields['employees'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).exclude(
                id__in=existing_employees
            ).order_by('first_name')

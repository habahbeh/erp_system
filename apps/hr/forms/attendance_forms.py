# apps/hr/forms/attendance_forms.py
"""
نماذج الحضور والإجازات والسلف - المرحلة الثانية
Phase 2 Forms: Attendance, Leave, Advances, Overtime
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date

from ..models import (
    Attendance, LeaveBalance, LeaveRequest, EarlyLeave,
    Overtime, Advance, AdvanceInstallment, Employee, LeaveType
)


class AttendanceForm(forms.ModelForm):
    """نموذج الحضور والانصراف"""

    class Meta:
        model = Attendance
        fields = [
            'employee', 'date', 'check_in', 'check_out', 'status',
            'working_hours', 'overtime_hours', 'late_minutes',
            'early_leave_minutes', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'check_in': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'check_out': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'working_hours': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
                'readonly': 'readonly',
            }),
            'overtime_hours': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'late_minutes': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'early_leave_minutes': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

        # الحقول الاختيارية
        optional = ['check_out', 'overtime_hours', 'late_minutes', 'early_leave_minutes', 'notes']
        for field in optional:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        attendance_date = cleaned_data.get('date')

        if employee and attendance_date:
            qs = Attendance.objects.filter(employee=employee, date=attendance_date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('يوجد سجل حضور لهذا الموظف في هذا التاريخ'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class BulkAttendanceForm(forms.Form):
    """نموذج تسجيل حضور جماعي"""

    date = forms.DateField(
        label=_('التاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    department = forms.ModelChoiceField(
        label=_('القسم'),
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': _('جميع الأقسام'),
        })
    )

    default_check_in = forms.TimeField(
        label=_('وقت الحضور الافتراضي'),
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
        })
    )

    default_check_out = forms.TimeField(
        label=_('وقت الانصراف الافتراضي'),
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
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


class LeaveBalanceForm(forms.ModelForm):
    """نموذج رصيد الإجازات"""

    class Meta:
        model = LeaveBalance
        fields = [
            'employee', 'leave_type', 'year', 'opening_balance',
            'adjustment', 'carried_forward', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'leave_type': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر نوع الإجازة...'),
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '2020',
                'max': '2050',
            }),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
            }),
            'adjustment': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
            }),
            'carried_forward': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('first_name')

            self.fields['leave_type'].queryset = LeaveType.objects.filter(
                company=self.company,
                is_active=True
            )

        # الحقول الاختيارية
        optional = ['adjustment', 'carried_forward', 'notes']
        for field in optional:
            self.fields[field].required = False

        # القيمة الافتراضية للسنة
        if not self.instance.pk:
            self.fields['year'].initial = date.today().year

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        leave_type = cleaned_data.get('leave_type')
        year = cleaned_data.get('year')

        if employee and leave_type and year:
            qs = LeaveBalance.objects.filter(
                employee=employee,
                leave_type=leave_type,
                year=year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('يوجد رصيد لهذا النوع من الإجازات لهذا الموظف في هذه السنة'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class LeaveRequestForm(forms.ModelForm):
    """نموذج طلب الإجازة"""

    class Meta:
        model = LeaveRequest
        fields = [
            'employee', 'leave_type', 'start_date', 'end_date',
            'days', 'reason', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'leave_type': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر نوع الإجازة...'),
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'readonly': 'readonly',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('سبب الإجازة...'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

            self.fields['leave_type'].queryset = LeaveType.objects.filter(
                company=self.company,
                is_active=True
            )

        # الحقول الاختيارية
        optional = ['reason', 'notes']
        for field in optional:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee')
        leave_type = cleaned_data.get('leave_type')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

            # حساب عدد الأيام
            days = (end_date - start_date).days + 1
            cleaned_data['days'] = days

            # التحقق من الرصيد
            if employee and leave_type:
                current_year = start_date.year
                try:
                    balance = LeaveBalance.objects.get(
                        employee=employee,
                        leave_type=leave_type,
                        year=current_year
                    )
                    if not leave_type.allow_negative_balance:
                        if balance.remaining_balance < days:
                            raise ValidationError(
                                _('رصيد الإجازات غير كافٍ. الرصيد المتاح: %(balance)s يوم') % {
                                    'balance': balance.remaining_balance
                                }
                            )
                except LeaveBalance.DoesNotExist:
                    if not leave_type.allow_negative_balance:
                        raise ValidationError(
                            _('لا يوجد رصيد إجازات لهذا الموظف لهذا النوع')
                        )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company

        if commit:
            instance.save()
        return instance


class EarlyLeaveForm(forms.ModelForm):
    """نموذج المغادرة المبكرة"""

    class Meta:
        model = EarlyLeave
        fields = [
            'employee', 'date', 'leave_type', 'from_time', 'to_time',
            'reason', 'is_deductible', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'leave_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'from_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'to_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('سبب المغادرة...'),
            }),
            'is_deductible': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

        # الحقول الاختيارية
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        if from_time and to_time and to_time <= from_time:
            raise ValidationError({
                'to_time': _('وقت النهاية يجب أن يكون بعد وقت البداية')
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class OvertimeForm(forms.ModelForm):
    """نموذج العمل الإضافي"""

    class Meta:
        model = Overtime
        fields = [
            'employee', 'date', 'overtime_type', 'start_time', 'end_time',
            'hours', 'rate', 'reason', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'overtime_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.25',
                'readonly': 'readonly',
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('سبب العمل الإضافي...'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

            # تحديد المعامل الافتراضي من الإعدادات
            try:
                from ..models import HRSettings
                hr_settings = HRSettings.objects.get(company=self.company)
                self.fields['rate'].initial = hr_settings.overtime_regular_rate
            except HRSettings.DoesNotExist:
                self.fields['rate'].initial = Decimal('1.25')

        # الحقول الاختيارية
        self.fields['notes'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class AdvanceForm(forms.ModelForm):
    """نموذج السلفة"""

    class Meta:
        model = Advance
        fields = [
            'employee', 'advance_type', 'request_date', 'amount',
            'reason', 'installments', 'start_deduction_date', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر الموظف...'),
            }),
            'advance_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'request_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('سبب السلفة...'),
            }),
            'installments': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'max': '24',
            }),
            'start_deduction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True,
                status='active'
            ).order_by('first_name')

        # الحقول الاختيارية
        optional = ['start_deduction_date', 'notes']
        for field in optional:
            self.fields[field].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['request_date'].initial = date.today()
            self.fields['installments'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        amount = cleaned_data.get('amount')

        if employee and amount and self.company:
            # التحقق من الحد الأقصى للسلفة
            try:
                from ..models import HRSettings
                hr_settings = HRSettings.objects.get(company=self.company)
                max_percentage = hr_settings.max_advance_percentage / 100
                max_amount = employee.basic_salary * max_percentage

                if amount > max_amount:
                    raise ValidationError({
                        'amount': _('المبلغ يتجاوز الحد الأقصى المسموح (%(max)s)') % {
                            'max': max_amount
                        }
                    })

                # التحقق من عدد الأقساط
                installments = cleaned_data.get('installments')
                if installments and installments > hr_settings.max_installments:
                    raise ValidationError({
                        'installments': _('عدد الأقساط يتجاوز الحد الأقصى (%(max)s)') % {
                            'max': hr_settings.max_installments
                        }
                    })

            except HRSettings.DoesNotExist:
                pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company

        # توليد رقم السلفة
        if not instance.advance_number:
            from apps.core.models import NumberingSequence
            instance.advance_number = NumberingSequence.get_next_number(
                self.company, 'advance'
            ) or f"ADV-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        # حساب قيمة القسط
        if instance.amount and instance.installments:
            instance.installment_amount = instance.amount / instance.installments
            instance.remaining_amount = instance.amount

        if commit:
            instance.save()
        return instance


class AdvanceApprovalForm(forms.Form):
    """نموذج الموافقة على السلفة"""

    action = forms.ChoiceField(
        choices=[
            ('approve', _('موافقة')),
            ('reject', _('رفض')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

    rejection_reason = forms.CharField(
        label=_('سبب الرفض'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')

        if action == 'reject' and not rejection_reason:
            raise ValidationError({
                'rejection_reason': _('يجب إدخال سبب الرفض')
            })

        return cleaned_data


class LeaveApprovalForm(forms.Form):
    """نموذج الموافقة على الإجازة"""

    action = forms.ChoiceField(
        choices=[
            ('approve', _('موافقة')),
            ('reject', _('رفض')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

    rejection_reason = forms.CharField(
        label=_('سبب الرفض'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')

        if action == 'reject' and not rejection_reason:
            raise ValidationError({
                'rejection_reason': _('يجب إدخال سبب الرفض')
            })

        return cleaned_data

# apps/hr/forms/employee_forms.py
"""
نماذج الموظفين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date

from ..models import Employee, Department, JobTitle
from apps.core.models import User


class EmployeeForm(forms.ModelForm):
    """نموذج الموظف"""

    class Meta:
        model = Employee
        fields = [
            'employee_number', 'user', 'first_name', 'last_name', 'father_name',
            'gender', 'birth_date', 'national_id', 'marital_status',
            'phone', 'mobile', 'email', 'address',
            'department', 'job_title', 'hire_date', 'contract_type',
            'employment_status', 'is_active'
        ]
        widgets = {
            'employee_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الموظف (مثال: EMP001)',
            }),
            'user': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المستخدم (اختياري)...',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الأول...',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم العائلة...',
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الأب...',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهوية الوطنية...',
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف الأرضي...',
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الجوال...',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني...',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'العنوان...',
            }),
            'department': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر القسم...',
            }),
            'job_title': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المسمى الوظيفي...',
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'contract_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.current_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الأقسام حسب الشركة
            self.fields['department'].queryset = Department.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            # تصفية المسميات الوظيفية حسب الشركة
            self.fields['job_title'].queryset = JobTitle.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

        # تصفية المستخدمين النشطين
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

        # جعل بعض الحقول اختيارية
        self.fields['user'].required = False
        self.fields['father_name'].required = False
        self.fields['birth_date'].required = False
        self.fields['national_id'].required = False
        self.fields['marital_status'].required = False
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['address'].required = False
        self.fields['job_title'].required = False
        self.fields['contract_type'].required = False

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['hire_date'].initial = date.today()
            self.fields['employment_status'].initial = 'active'
            self.fields['is_active'].initial = True

    def clean_employee_number(self):
        employee_number = self.cleaned_data.get('employee_number')
        if employee_number:
            # التحقق من عدم تكرار رقم الموظف
            qs = Employee.objects.filter(employee_number=employee_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رقم الموظف موجود مسبقاً'))
        return employee_number

    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # التحقق من عدم تكرار رقم الهوية
            qs = Employee.objects.filter(national_id=national_id)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رقم الهوية الوطنية موجود مسبقاً'))
        return national_id

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من تاريخ الميلاد
        birth_date = cleaned_data.get('birth_date')
        if birth_date and birth_date >= date.today():
            raise ValidationError({
                'birth_date': _('تاريخ الميلاد يجب أن يكون في الماضي')
            })

        # التحقق من تاريخ التوظيف
        hire_date = cleaned_data.get('hire_date')
        if hire_date and birth_date:
            age_at_hire = (hire_date - birth_date).days / 365.25
            if age_at_hire < 16:
                raise ValidationError({
                    'hire_date': _('عمر الموظف عند التوظيف يجب أن يكون 16 سنة على الأقل')
                })

        return cleaned_data

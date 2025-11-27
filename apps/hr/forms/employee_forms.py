# apps/hr/forms/employee_forms.py
"""
نماذج الموظفين - المرحلة 1
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date

from ..models import Employee, Department, JobTitle, JobGrade
from apps.core.models import User, Branch, Currency


class EmployeeForm(forms.ModelForm):
    """نموذج الموظف"""

    class Meta:
        model = Employee
        fields = [
            # لا نضع employee_number لأنه editable=False
            'user', 'first_name', 'middle_name', 'last_name', 'full_name_en',
            'national_id', 'date_of_birth', 'nationality', 'gender', 'marital_status',
            'mobile', 'phone', 'email', 'address',
            'department', 'job_title', 'job_grade', 'branch', 'manager',
            'social_security_number', 'hire_date', 'employment_status', 'status',
            'basic_salary', 'fuel_allowance', 'other_allowances', 'social_security_salary',
            'currency', 'working_hours_per_day', 'working_days_per_month',
            'annual_leave_balance', 'sick_leave_balance',
            'bank_name', 'bank_branch', 'bank_account', 'iban',
            'photo', 'notes', 'is_active'
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المستخدم (اختياري)...',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الأول...',
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الأب...',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم العائلة...',
            }),
            'full_name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name in English...',
                'dir': 'ltr',
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرقم الوطني...',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'nationality': forms.Select(attrs={
                'class': 'form-select',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الموبايل...',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف الأرضي...',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني...',
                'dir': 'ltr',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
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
            'job_grade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select',
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المدير المباشر...',
            }),
            'social_security_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الضمان الاجتماعي...',
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'fuel_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'other_allowances': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'social_security_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'working_hours_per_day': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '1',
                'max': '24',
            }),
            'working_days_per_month': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'max': '31',
            }),
            'annual_leave_balance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '0',
            }),
            'sick_leave_balance': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '0',
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم البنك...',
            }),
            'bank_branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'فرع البنك...',
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الحساب البنكي...',
                'dir': 'ltr',
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم IBAN...',
                'dir': 'ltr',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات...',
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

            # تصفية الدرجات الوظيفية حسب الشركة
            self.fields['job_grade'].queryset = JobGrade.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('level', 'name')

            # تصفية الفروع حسب الشركة
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            # تصفية المدراء (موظفين الشركة)
            self.fields['manager'].queryset = Employee.objects.filter(
                company=self.company,
                status='active'
            ).exclude(pk=self.instance.pk if self.instance.pk else None).order_by('first_name', 'last_name')

        # تصفية المستخدمين النشطين
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

        # العملات
        self.fields['currency'].queryset = Currency.objects.filter(
            is_active=True
        ).order_by('code')

        # جعل بعض الحقول اختيارية
        optional_fields = [
            'user', 'middle_name', 'full_name_en', 'date_of_birth',
            'nationality', 'gender', 'marital_status', 'phone', 'email',
            'address', 'job_title', 'job_grade', 'branch', 'manager',
            'social_security_number', 'fuel_allowance', 'other_allowances',
            'social_security_salary', 'currency', 'bank_name', 'bank_branch',
            'bank_account', 'iban', 'photo', 'notes'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # تعيين القيم الافتراضية للسجلات الجديدة
        if not self.instance.pk:
            self.fields['hire_date'].initial = date.today()
            self.fields['employment_status'].initial = 'full_time'
            self.fields['status'].initial = 'active'
            self.fields['is_active'].initial = True
            self.fields['working_hours_per_day'].initial = 8
            self.fields['working_days_per_month'].initial = 30

    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')
        if national_id and self.company:
            # التحقق من عدم تكرار رقم الهوية في نفس الشركة
            qs = Employee.objects.filter(
                company=self.company,
                national_id=national_id
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رقم الهوية الوطنية موجود مسبقاً'))
        return national_id

    def clean(self):
        cleaned_data = super().clean()

        # التحقق من تاريخ الميلاد
        date_of_birth = cleaned_data.get('date_of_birth')
        if date_of_birth and date_of_birth >= date.today():
            raise ValidationError({
                'date_of_birth': _('تاريخ الميلاد يجب أن يكون في الماضي')
            })

        # التحقق من تاريخ التوظيف
        hire_date = cleaned_data.get('hire_date')
        if hire_date and date_of_birth:
            age_at_hire = (hire_date - date_of_birth).days / 365.25
            if age_at_hire < 16:
                raise ValidationError({
                    'hire_date': _('عمر الموظف عند التوظيف يجب أن يكون 16 سنة على الأقل')
                })

        # التحقق من راتب الضمان
        basic_salary = cleaned_data.get('basic_salary') or 0
        social_security_salary = cleaned_data.get('social_security_salary') or 0
        if social_security_salary > basic_salary:
            raise ValidationError({
                'social_security_salary': _('راتب الضمان لا يمكن أن يتجاوز الراتب الأساسي')
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if self.current_user:
            if not instance.pk:
                instance.created_by = self.current_user
        if commit:
            instance.save()
        return instance

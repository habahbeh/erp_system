# apps/hr/forms/organization_forms.py
"""
نماذج الهيكل التنظيمي - الدرجات والمسميات الوظيفية
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ..models import JobGrade, JobTitle, Department


class JobGradeForm(forms.ModelForm):
    """نموذج الدرجة الوظيفية"""

    class Meta:
        model = JobGrade
        fields = [
            'code', 'name', 'name_en', 'level',
            'min_salary', 'max_salary',
            'annual_leave_days', 'sick_leave_days',
            'description', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز الدرجة...',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الدرجة...',
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Grade Name...',
                'dir': 'ltr',
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'max': '20',
            }),
            'min_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'max_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'annual_leave_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'sick_leave_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'وصف الدرجة...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # الحقول الاختيارية
        optional_fields = ['name_en', 'min_salary', 'max_salary', 'description']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['level'].initial = 1
            self.fields['annual_leave_days'].initial = 14
            self.fields['sick_leave_days'].initial = 14

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.company:
            qs = JobGrade.objects.filter(company=self.company, code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رمز الدرجة موجود مسبقاً'))
        return code

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('min_salary') or 0
        max_salary = cleaned_data.get('max_salary') or 0

        if min_salary and max_salary and min_salary > max_salary:
            raise ValidationError({
                'max_salary': _('الحد الأقصى للراتب يجب أن يكون أكبر من الحد الأدنى')
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance


class JobTitleForm(forms.ModelForm):
    """نموذج المسمى الوظيفي"""

    class Meta:
        model = JobTitle
        fields = [
            'code', 'name', 'name_en', 'department', 'job_grade',
            'description', 'responsibilities', 'requirements', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز المسمى...',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المسمى الوظيفي...',
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job Title...',
                'dir': 'ltr',
            }),
            'department': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر القسم...',
            }),
            'job_grade': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الدرجة الوظيفية...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'وصف المسمى...',
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'المسؤوليات...',
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'المتطلبات...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الأقسام حسب الشركة
            self.fields['department'].queryset = Department.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            # تصفية الدرجات حسب الشركة
            self.fields['job_grade'].queryset = JobGrade.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('level', 'name')

        # الحقول الاختيارية
        optional_fields = ['name_en', 'department', 'job_grade', 'description', 'responsibilities', 'requirements']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.company:
            qs = JobTitle.objects.filter(company=self.company, code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('رمز المسمى الوظيفي موجود مسبقاً'))
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.company:
            instance.company = self.company
        if commit:
            instance.save()
        return instance

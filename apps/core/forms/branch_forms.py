# apps/core/forms/branch_forms.py
"""
نماذج الفروع
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Branch, Warehouse


class BranchForm(forms.ModelForm):
    """نموذج إضافة/تعديل الفرع"""

    class Meta:
        model = Branch
        fields = [
            'code', 'name', 'phone', 'email', 'address',
            'default_warehouse', 'is_main'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الفرع'),
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الفرع'),
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('عنوان الفرع')
            }),
            'default_warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['address'].required = False
        self.fields['default_warehouse'].required = False

        # فلترة المستودعات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company
            self.fields['default_warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')
        else:
            self.fields['default_warehouse'].queryset = Warehouse.objects.none()

        # إضافة خيار فارغ للمستودع
        self.fields['default_warehouse'].empty_label = _('اختر المستودع الافتراضي')

    def clean_code(self):
        """التحقق من عدم تكرار رمز الفرع"""
        code = self.cleaned_data.get('code')
        if code and self.request:
            company = self.request.current_company
            queryset = Branch.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code

    def clean_name(self):
        """التحقق من عدم تكرار اسم الفرع"""
        name = self.cleaned_data.get('name')
        if name and self.request:
            company = self.request.current_company
            queryset = Branch.objects.filter(company=company, name=name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الاسم مستخدم مسبقاً'))
        return name

    def save(self, commit=True):
        """حفظ مع إضافة الشركة"""
        instance = super().save(commit=False)

        if self.request:
            if getattr(instance, 'company_id', None) is None:
                instance.company = self.request.current_company

        if commit:
            instance.save()
        return instance
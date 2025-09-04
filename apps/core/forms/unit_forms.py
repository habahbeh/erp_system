# apps/core/forms/unit_forms.py
"""
نماذج وحدات القياس
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import UnitOfMeasure


class UnitOfMeasureForm(forms.ModelForm):
    """نموذج إضافة/تعديل وحدة القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الوحدة (مثال: KG, M, L)'),
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم وحدة القياس'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Unit Name')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['name_en'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار رمز الوحدة"""
        code = self.cleaned_data.get('code')
        if code and self.request:
            company = self.request.current_company
            queryset = UnitOfMeasure.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code.upper() if code else code

    def clean_name(self):
        """التحقق من عدم تكرار اسم الوحدة"""
        name = self.cleaned_data.get('name')
        if name and self.request:
            company = self.request.current_company
            queryset = UnitOfMeasure.objects.filter(company=company, name=name)
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
            if getattr(instance, 'created_by_id', None) is None:
                instance.created_by = self.request.user

        if commit:
            instance.save()
        return instance
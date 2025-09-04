# apps/core/forms/warehouse_forms.py
"""
نماذج المستودعات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Warehouse, User


class WarehouseForm(forms.ModelForm):
    """نموذج إضافة/تعديل المستودع"""

    class Meta:
        model = Warehouse
        fields = [
            'code', 'name', 'name_en', 'address', 'phone',
            'is_main', 'allow_negative_stock', 'manager', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز المستودع')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستودع'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Warehouse Name')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('عنوان المستودع')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_negative_stock': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = self.request.current_company

            # فلترة المدراء حسب الشركة
            self.fields['manager'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

        # جعل بعض الحقول اختيارية
        self.fields['manager'].required = False
        self.fields['manager'].empty_label = _('-- اختر مدير المستودع --')

    def clean_code(self):
        """التحقق من عدم تكرار رمز المستودع"""
        code = self.cleaned_data.get('code')
        if code and self.request:
            company = self.request.current_company
            queryset = Warehouse.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code

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
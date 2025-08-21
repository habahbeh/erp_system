# apps/base_data/forms/customer_forms.py
"""
نماذج العملاء
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from ..models import Customer

User = get_user_model()


class CustomerForm(forms.ModelForm):
    """نموذج العميل"""

    class Meta:
        model = Customer
        fields = [
            'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email', 'website',
            'address', 'city', 'region',
            'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'discount_percentage',
            'salesperson', 'notes', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: 064027888')
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: 0791234567')
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('example@domain.com')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('https://www.example.com')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tax_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': _('عدد الأيام')
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'salesperson': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة مندوبي المبيعات حسب الشركة
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company,
                is_active=True,
                groups__name__in=['موظفو المبيعات', 'المدراء']
            ).distinct()

            # إضافة خيار فارغ
            self.fields['salesperson'].empty_label = _('-- اختر مندوب المبيعات --')

    def clean_phone(self):
        """التحقق من رقم الهاتف"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # إزالة المسافات والشرطات
            phone = phone.replace(' ', '').replace('-', '')
            # التحقق من أن الرقم يحتوي على أرقام فقط
            if not phone.isdigit():
                raise forms.ValidationError(_('رقم الهاتف يجب أن يحتوي على أرقام فقط'))
        return phone

    def clean_mobile(self):
        """التحقق من رقم الموبايل"""
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            mobile = mobile.replace(' ', '').replace('-', '')
            if not mobile.isdigit():
                raise forms.ValidationError(_('رقم الموبايل يجب أن يحتوي على أرقام فقط'))
            # التحقق من أن الرقم يبدأ بـ 07
            if not mobile.startswith('07'):
                raise forms.ValidationError(_('رقم الموبايل يجب أن يبدأ بـ 07'))
        return mobile

    def clean_discount_percentage(self):
        """التحقق من نسبة الخصم"""
        discount = self.cleaned_data.get('discount_percentage', 0)
        if discount < 0 or discount > 100:
            raise forms.ValidationError(_('نسبة الخصم يجب أن تكون بين 0 و 100'))
        return discount
# apps/core/forms/currency_forms.py
"""
نماذج العملات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Currency


class CurrencyForm(forms.ModelForm):
    """نموذج إضافة/تعديل العملة"""

    class Meta:
        model = Currency
        fields = ['code', 'name', 'name_en', 'symbol', 'exchange_rate', 'is_base']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز العملة (مثال: USD, EUR, JOD)'),
                'required': True,
                'maxlength': '3'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العملة'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Currency Name')
            }),
            'symbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز العملة ($, €, د.أ)'),
                'required': True
            }),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001',
                'value': '1.0000',
                'placeholder': _('سعر الصرف مقابل العملة الأساسية')
            }),
            'is_base': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['name_en'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار رمز العملة"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            queryset = Currency.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code

    def clean_name(self):
        """التحقق من عدم تكرار اسم العملة"""
        name = self.cleaned_data.get('name')
        if name:
            queryset = Currency.objects.filter(name=name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الاسم مستخدم مسبقاً'))
        return name

    def clean(self):
        """تحققات شاملة"""
        cleaned_data = super().clean()
        is_base = cleaned_data.get('is_base')
        exchange_rate = cleaned_data.get('exchange_rate')

        # إذا كانت العملة الأساسية، يجب أن يكون سعر الصرف 1
        if is_base and exchange_rate != 1.0000:
            cleaned_data['exchange_rate'] = 1.0000
            self.add_error('exchange_rate', _('سعر الصرف للعملة الأساسية يجب أن يكون 1'))

        return cleaned_data

    def save(self, commit=True):
        """حفظ مع معالجة العملة الأساسية"""
        instance = super().save(commit=False)

        # إذا كانت هذه العملة الأساسية، ألغِ الأساسية للعملات الأخرى
        if instance.is_base:
            Currency.objects.filter(is_base=True).exclude(pk=instance.pk).update(is_base=False)
            instance.exchange_rate = 1.0000

        if commit:
            instance.save()
        return instance
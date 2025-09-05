# apps/core/forms/company_forms.py - تصحيح الكود

"""
نماذج الشركة
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Company, Currency


class CompanyForm(forms.ModelForm):
    """نموذج تعديل بيانات الشركة"""

    # تعريف حقل شهر بداية السنة المالية كـ ChoiceField
    fiscal_year_start_month = forms.ChoiceField(
        label=_('شهر بداية السنة المالية'),
        choices=[
            (1, _('يناير')), (2, _('فبراير')), (3, _('مارس')),
            (4, _('أبريل')), (5, _('مايو')), (6, _('يونيو')),
            (7, _('يوليو')), (8, _('أغسطس')), (9, _('سبتمبر')),
            (10, _('أكتوبر')), (11, _('نوفمبر')), (12, _('ديسمبر'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Company
        fields = [
            'name', 'name_en', 'tax_number', 'commercial_register',
            'phone', 'email', 'address', 'city', 'country',
            'logo', 'fiscal_year_start_month', 'fiscal_year_start_day',
            'base_currency', 'default_tax_rate'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الشركة'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Company Name')
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي')
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري')
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
                'placeholder': _('العنوان التفصيلي')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الدولة')
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'fiscal_year_start_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 31
            }),
            'base_currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.01,
                'min': 0,
                'max': 100
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # العملات المتاحة
        self.fields['base_currency'].queryset = Currency.objects.filter(is_active=True)

        # تخصيص التسميات
        self.fields['name'].label = _('اسم الشركة')
        self.fields['name_en'].label = _('الاسم الإنجليزي')
        self.fields['tax_number'].label = _('الرقم الضريبي')
        self.fields['commercial_register'].label = _('السجل التجاري')
        self.fields['phone'].label = _('الهاتف')
        self.fields['email'].label = _('البريد الإلكتروني')
        self.fields['address'].label = _('العنوان')
        self.fields['city'].label = _('المدينة')
        self.fields['country'].label = _('الدولة')
        self.fields['logo'].label = _('شعار الشركة')
        self.fields['fiscal_year_start_day'].label = _('يوم بداية السنة المالية')
        self.fields['base_currency'].label = _('العملة الأساسية')
        self.fields['default_tax_rate'].label = _('نسبة الضريبة الافتراضية %')

        # جعل بعض الحقول اختيارية
        self.fields['name_en'].required = False
        self.fields['commercial_register'].required = False
        self.fields['logo'].required = False

        # تعيين القيمة الحالية لشهر بداية السنة المالية
        if self.instance and self.instance.pk:
            self.fields['fiscal_year_start_month'].initial = self.instance.fiscal_year_start_month

    def clean_tax_number(self):
        """التحقق من عدم تكرار الرقم الضريبي"""
        tax_number = self.cleaned_data.get('tax_number')
        if tax_number:
            queryset = Company.objects.filter(tax_number=tax_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرقم الضريبي مستخدم مسبقاً'))
        return tax_number

    def clean_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            # يمكن إضافة المزيد من التحقق هنا إذا لزم الأمر
            pass
        return email

    def clean_default_tax_rate(self):
        """التحقق من نسبة الضريبة"""
        rate = self.cleaned_data.get('default_tax_rate')
        if rate is not None and (rate < 0 or rate > 100):
            raise ValidationError(_('نسبة الضريبة يجب أن تكون بين 0 و 100'))
        return rate

    def clean_fiscal_year_start_month(self):
        """التحقق من شهر بداية السنة المالية"""
        month = self.cleaned_data.get('fiscal_year_start_month')
        if month:
            try:
                month = int(month)
                if month < 1 or month > 12:
                    raise ValidationError(_('شهر بداية السنة المالية يجب أن يكون بين 1 و 12'))
            except (ValueError, TypeError):
                raise ValidationError(_('قيمة غير صالحة لشهر بداية السنة المالية'))
        return month

    def clean_fiscal_year_start_day(self):
        """التحقق من يوم بداية السنة المالية"""
        day = self.cleaned_data.get('fiscal_year_start_day')
        if day is not None and (day < 1 or day > 31):
            raise ValidationError(_('يوم بداية السنة المالية يجب أن يكون بين 1 و 31'))
        return day
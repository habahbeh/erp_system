# apps/core/forms/partner_forms.py
"""
نماذج العملاء (العملاء والموردين)
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import BusinessPartner, User


class BusinessPartnerForm(forms.ModelForm):
    """نموذج إضافة/تعديل الشريك التجاري"""

    class Meta:
        model = BusinessPartner
        fields = [
            'partner_type', 'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email',
            'sales_representative', 'address', 'city', 'region',
            'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'notes'
        ]
        widgets = {
            'partner_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'togglePartnerTypeFields()'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('سيتم توليده تلقائياً')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الشريك التجاري'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Partner Name')
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),

            # معلومات الاتصال
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموبايل')
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الفاكس')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني')
            }),

            # المندوب
            'sales_representative': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_sales_representative'
            }),

            # العنوان
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('العنوان التفصيلي')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة/المحافظة')
            }),

            # المعلومات الضريبية
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي')
            }),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري')
            }),

            # حدود الائتمان
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '365',
                'value': '30'
            }),

            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات عامة')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = self.request.current_company

            # فلترة المندوبين حسب الشركة
            self.fields['sales_representative'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

        # جعل بعض الحقول اختيارية في العرض
        self.fields['code'].required = False
        self.fields['sales_representative'].required = False
        self.fields['contact_person'].required = False
        self.fields['tax_number'].required = False

        # إضافة empty_label للحقول الاختيارية
        self.fields['sales_representative'].empty_label = _('-- اختر المندوب --')

    def clean_code(self):
        """التحقق من عدم تكرار رمز الشريك"""
        code = self.cleaned_data.get('code')
        if code and self.request:
            company = self.request.current_company
            queryset = BusinessPartner.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code

    def clean_tax_number(self):
        """التحقق من تفرد الرقم الضريبي"""
        tax_number = self.cleaned_data.get('tax_number')
        if tax_number and self.request:
            company = self.request.current_company
            queryset = BusinessPartner.objects.filter(company=company, tax_number=tax_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرقم الضريبي مستخدم مسبقاً'))
        return tax_number

    def clean_email(self):
        """التحقق من البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email and self.request:
            company = self.request.current_company
            queryset = BusinessPartner.objects.filter(company=company, email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا البريد الإلكتروني مستخدم مسبقاً'))
        return email

    def clean(self):
        """تحققات شاملة للنموذج"""
        cleaned_data = super().clean()
        partner_type = cleaned_data.get('partner_type')
        sales_representative = cleaned_data.get('sales_representative')

        # التأكد من وجود مندوب للعملاء
        if partner_type in ['customer', 'both'] and not sales_representative:
            # تحذير فقط، ليس خطأ إجباري
            pass

        return cleaned_data

    def save(self, commit=True):
        """حفظ مع إضافة الشركة والفرع"""
        instance = super().save(commit=False)

        # إضافة الشركة والفرع من الطلب
        if self.request:
            # استخدم getattr للتحقق الآمن
            if getattr(instance, 'company_id', None) is None:
                instance.company = self.request.current_company
            if getattr(instance, 'branch_id', None) is None:
                instance.branch = self.request.current_branch
            if getattr(instance, 'created_by_id', None) is None:
                instance.created_by = self.request.user

        # توليد الكود بعد إضافة الشركة
        if not instance.code and instance.company:
            instance.code = instance.generate_code()

        if commit:
            instance.save()
        return instance
# في apps/core/forms/partner_forms.py - استبدال بالكامل

"""
نماذج العملاء (العملاء والموردين) مع المرفقات والمندوبين المتعددين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from ..models import BusinessPartner, User, PartnerRepresentative


class BusinessPartnerForm(forms.ModelForm):
    """نموذج إضافة/تعديل العميل مع المرفقات"""

    class Meta:
        model = BusinessPartner
        fields = [
            'partner_type', 'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email',
            'address', 'city', 'region',
            'tax_number', 'tax_status', 'commercial_register',
            'tax_exemption_start_date', 'tax_exemption_end_date', 'tax_exemption_reason',
            'credit_limit', 'credit_period',
            'commercial_register_file', 'payment_letter_file', 'tax_exemption_file', 'other_attachments',
            'notes'
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
                'placeholder': _('اسم العميل'),
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
            'tax_status': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleTaxExemptionFields()'
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري')
            }),

            # فترة الإعفاء الضريبي
            'tax_exemption_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tax_exemption_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tax_exemption_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('سبب الإعفاء الضريبي')
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

            # المرفقات
            'commercial_register_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'payment_letter_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'tax_exemption_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'other_attachments': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
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

        # جعل بعض الحقول اختيارية في العرض
        self.fields['code'].required = False
        self.fields['tax_number'].required = False

    def clean_code(self):
        """التحقق من عدم تكرار رمز العميل"""
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
        tax_status = cleaned_data.get('tax_status')
        tax_exemption_start_date = cleaned_data.get('tax_exemption_start_date')
        tax_exemption_end_date = cleaned_data.get('tax_exemption_end_date')

        # التحقق من تواريخ الإعفاء الضريبي
        if tax_status == 'non_taxable':
            if not tax_exemption_start_date or not tax_exemption_end_date:
                raise ValidationError(_('يجب تحديد فترة الإعفاء الضريبي للحالة "غير خاضع"'))

            if tax_exemption_start_date >= tax_exemption_end_date:
                raise ValidationError(_('تاريخ نهاية الإعفاء يجب أن يكون بعد تاريخ البداية'))

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


class PartnerRepresentativeForm(forms.ModelForm):
    """نموذج إضافة مندوب للعميل"""

    class Meta:
        model = PartnerRepresentative
        fields = ['representative_name', 'phone', 'is_primary', 'notes']
        widgets = {
            'representative_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المندوب'),
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('هاتف المندوب')
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات خاصة بالمندوب')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل اسم المندوب مطلوب
        self.fields['representative_name'].required = True


# إنشاء FormSet للمندوبين المتعددين بطريقة مبسطة
PartnerRepresentativeFormSet = inlineformset_factory(
    BusinessPartner,
    PartnerRepresentative,
    fields=['representative_name', 'phone', 'is_primary', 'notes'],
    extra=2,  # عدد النماذج الفارغة الافتراضي
    can_delete=True,
    min_num=0,
    max_num=10,
    widgets={
        'representative_name': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المندوب'
        }),
        'phone': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'هاتف المندوب'
        }),
        'is_primary': forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        'notes': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'ملاحظات'
        }),
    }
)
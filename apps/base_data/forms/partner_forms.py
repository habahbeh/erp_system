# apps/base_data/forms/partner_forms.py
"""
نماذج الشركاء التجاريين
يتضمن: العملاء، الموردين، نموذج موحد للشركاء
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from ..models import BusinessPartner, Customer, Supplier
from accounting.models import Account
from core.models import User


class BusinessPartnerForm(forms.ModelForm):
    """نموذج الشريك التجاري الموحد (عميل/مورد)"""

    # حقول إضافية للتحكم في العرض
    show_customer_fields = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.HiddenInput()
    )

    show_supplier_fields = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = BusinessPartner
        fields = [
            # النوع والمعلومات الأساسية
            'partner_type', 'code', 'name', 'name_en', 'account_type',

            # معلومات الاتصال
            'contact_person', 'phone', 'mobile', 'fax',
            'email', 'website', 'address', 'city', 'region',

            # معلومات ضريبية وقانونية
            'tax_number', 'tax_status', 'commercial_register',

            # حدود الائتمان
            'credit_limit', 'credit_period',

            # الحسابات المحاسبية
            'customer_account', 'supplier_account',

            # حقول خاصة بالعملاء
            'salesperson', 'discount_percentage', 'customer_category',

            # حقول خاصة بالموردين
            'payment_terms', 'supplier_category', 'rating',

            # ملاحظات
            'notes'
        ]

        widgets = {
            # النوع والمعلومات الأساسية
            'partner_type': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True,
                'data-bs-toggle': 'partner-type',
                'onchange': 'togglePartnerFields(this)',
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الشريك'),
                'required': True,
                'autofocus': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الكامل'),
                'required': True,
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Full Name'),
                'dir': 'ltr',
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True,
            }),

            # معلومات الاتصال
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الشخص المسؤول'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('06-1234567'),
                'dir': 'ltr',
                'data-inputmask': "'mask': '99-9999999'",
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('079-1234567'),
                'dir': 'ltr',
                'data-inputmask': "'mask': '999-9999999'",
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('06-1234567'),
                'dir': 'ltr',
                'data-inputmask': "'mask': '99-9999999'",
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('example@domain.com'),
                'dir': 'ltr',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('https://www.example.com'),
                'dir': 'ltr',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('العنوان التفصيلي'),
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة'),
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة/المحافظة'),
            }),

            # معلومات ضريبية
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي'),
                'dir': 'ltr',
            }),
            'tax_status': forms.Select(attrs={
                'class': 'form-control form-select',
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري'),
                'dir': 'ltr',
            }),

            # حدود الائتمان
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '30',
                'min': '0',
                'max': '365',
            }),

            # الحسابات المحاسبية
            'customer_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب العميل'),
                'data-partner-field': 'customer',
            }),
            'supplier_account': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('حساب المورد'),
                'data-partner-field': 'supplier',
            }),

            # حقول العملاء
            'salesperson': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('مندوب المبيعات'),
                'data-partner-field': 'customer',
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'data-partner-field': 'customer',
            }),
            'customer_category': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-partner-field': 'customer',
            }),

            # حقول الموردين
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('نقدي، 30 يوم، 60 يوم...'),
                'data-partner-field': 'supplier',
            }),
            'supplier_category': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-partner-field': 'supplier',
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-partner-field': 'supplier',
            }),

            # ملاحظات
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية'),
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # إضافة خيارات التقييم
        self.fields['rating'].widget.choices = [
            (1, '⭐'),
            (2, '⭐⭐'),
            (3, '⭐⭐⭐'),
            (4, '⭐⭐⭐⭐'),
            (5, '⭐⭐⭐⭐⭐'),
        ]

        # فلترة حسب الشركة
        if hasattr(self.instance, 'company') and self.instance.company:
            company = self.instance.company

            # الحسابات المحاسبية
            accounts = Account.objects.filter(
                company=company,
                accept_entries=True,
                is_active=True
            ).order_by('code')

            # حسابات العملاء (عادة من الذمم المدينة)
            customer_accounts = accounts.filter(
                account_type__type_category='assets'
            )
            self.fields['customer_account'].queryset = customer_accounts

            # حسابات الموردين (عادة من الذمم الدائنة)
            supplier_accounts = accounts.filter(
                account_type__type_category='liabilities'
            )
            self.fields['supplier_account'].queryset = supplier_accounts

            # مندوبي المبيعات
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company,
                is_active=True,
                groups__permissions__codename='can_sell'  # صلاحية البيع
            ).distinct().order_by('first_name', 'last_name')

        # تعيين الحقول المطلوبة حسب نوع الشريك
        if self.instance.pk:
            partner_type = self.instance.partner_type
            self._configure_required_fields(partner_type)

        # تطبيق الصلاحيات
        self._apply_permissions()

    def _configure_required_fields(self, partner_type):
        """تعيين الحقول المطلوبة حسب نوع الشريك"""
        if partner_type == 'customer':
            self.fields['customer_account'].required = True
            self.fields['salesperson'].required = True
            # إخفاء حقول الموردين
            for field in ['supplier_account', 'payment_terms', 'supplier_category', 'rating']:
                self.fields[field].widget = forms.HiddenInput()

        elif partner_type == 'supplier':
            self.fields['supplier_account'].required = True
            # إخفاء حقول العملاء
            for field in ['customer_account', 'salesperson', 'discount_percentage', 'customer_category']:
                self.fields[field].widget = forms.HiddenInput()

        elif partner_type == 'both':
            self.fields['customer_account'].required = True
            self.fields['supplier_account'].required = True
            self.fields['salesperson'].required = True

    def _apply_permissions(self):
        """تطبيق الصلاحيات على الحقول"""
        if not self.user:
            return

        # تعطيل جميع الحقول لمن ليس لديه صلاحية التعديل
        if not self.user.has_perm('base_data.change_businesspartner'):
            for field in self.fields:
                self.fields[field].disabled = True

        # إخفاء الحقول المالية لغير المخولين
        if not self.user.has_perm('base_data.view_financial_info'):
            financial_fields = [
                'credit_limit', 'credit_period',
                'discount_percentage', 'payment_terms'
            ]
            for field in financial_fields:
                self.fields[field].widget = forms.HiddenInput()

        # إخفاء الحسابات المحاسبية لغير المحاسبين
        if not self.user.has_perm('accounting.view_account'):
            for field in ['customer_account', 'supplier_account']:
                self.fields[field].widget = forms.HiddenInput()

    def clean_code(self):
        """التحقق من عدم تكرار الرمز"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            qs = BusinessPartner.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الرمز مستخدم بالفعل'))
        return code

    def clean_tax_number(self):
        """التحقق من صحة الرقم الضريبي"""
        tax_number = self.cleaned_data.get('tax_number')
        if tax_number:
            tax_number = tax_number.strip()
            # التحقق من الصيغة (مثال: رقم ضريبي أردني)
            if len(tax_number) not in [9, 10, 15]:
                raise ValidationError(
                    _('الرقم الضريبي يجب أن يكون 9 أو 10 أو 15 رقم')
                )
        return tax_number

    def clean_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # التحقق من عدم التكرار
            qs = BusinessPartner.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                # تحذير فقط، ليس خطأ
                self.add_error('email',
                               _('تنبيه: هذا البريد الإلكتروني مستخدم لشريك آخر')
                               )
        return email

    def clean_mobile(self):
        """التحقق من صحة رقم الموبايل"""
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            # إزالة المسافات والشرطات
            mobile = mobile.replace(' ', '').replace('-', '')
            # التحقق من الصيغة الأردنية
            if not mobile.startswith(('079', '078', '077')):
                raise ValidationError(
                    _('رقم الموبايل يجب أن يبدأ بـ 077 أو 078 أو 079')
                )
            if len(mobile) != 10:
                raise ValidationError(
                    _('رقم الموبايل يجب أن يكون 10 أرقام')
                )
        return mobile

    def clean(self):
        """التحقق من منطقية البيانات"""
        cleaned_data = super().clean()
        partner_type = cleaned_data.get('partner_type')

        # التحقق من الحسابات المطلوبة
        if partner_type in ['customer', 'both']:
            if not cleaned_data.get('customer_account'):
                self.add_error('customer_account', _('حساب العميل مطلوب'))

        if partner_type in ['supplier', 'both']:
            if not cleaned_data.get('supplier_account'):
                self.add_error('supplier_account', _('حساب المورد مطلوب'))

        # التحقق من حد الائتمان
        account_type = cleaned_data.get('account_type')
        credit_limit = cleaned_data.get('credit_limit', 0)

        if account_type == 'cash' and credit_limit > 0:
            self.add_error('credit_limit',
                           _('لا يمكن وضع حد ائتمان للحسابات النقدية')
                           )

        return cleaned_data


class CustomerForm(BusinessPartnerForm):
    """نموذج العميل - مبني على نموذج الشريك التجاري"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين النوع كعميل
        self.fields['partner_type'].initial = 'customer'
        self.fields['partner_type'].widget = forms.HiddenInput()

        # إخفاء حقول الموردين
        supplier_fields = [
            'supplier_account', 'payment_terms',
            'supplier_category', 'rating'
        ]
        for field in supplier_fields:
            if field in self.fields:
                self.fields[field].widget = forms.HiddenInput()
                self.fields[field].required = False

        # جعل حقول العملاء مطلوبة
        self.fields['customer_account'].required = True
        self.fields['salesperson'].required = True

        # تخصيص التسميات
        self.fields['code'].label = _('رمز العميل')
        self.fields['name'].label = _('اسم العميل')
        self.fields['code'].widget.attrs['placeholder'] = _('رمز العميل')
        self.fields['name'].widget.attrs['placeholder'] = _('اسم العميل')


class SupplierForm(BusinessPartnerForm):
    """نموذج المورد - مبني على نموذج الشريك التجاري"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين النوع كمورد
        self.fields['partner_type'].initial = 'supplier'
        self.fields['partner_type'].widget = forms.HiddenInput()

        # إخفاء حقول العملاء
        customer_fields = [
            'customer_account', 'salesperson',
            'discount_percentage', 'customer_category'
        ]
        for field in customer_fields:
            if field in self.fields:
                self.fields[field].widget = forms.HiddenInput()
                self.fields[field].required = False

        # جعل حقول الموردين مطلوبة
        self.fields['supplier_account'].required = True

        # تخصيص التسميات
        self.fields['code'].label = _('رمز المورد')
        self.fields['name'].label = _('اسم المورد')
        self.fields['code'].widget.attrs['placeholder'] = _('رمز المورد')
        self.fields['name'].widget.attrs['placeholder'] = _('اسم المورد')


class PartnerQuickAddForm(forms.ModelForm):
    """نموذج إضافة سريعة للشركاء - للنوافذ المنبثقة"""

    class Meta:
        model = BusinessPartner
        fields = [
            'partner_type', 'code', 'name',
            'phone', 'mobile', 'account_type'
        ]
        widgets = {
            'partner_type': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'required': True,
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الرمز'),
                'required': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الاسم'),
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الهاتف'),
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الموبايل'),
                'required': True,
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        # نوع الشريك الافتراضي
        partner_type = kwargs.pop('partner_type', None)
        super().__init__(*args, **kwargs)

        if partner_type:
            self.fields['partner_type'].initial = partner_type
            self.fields['partner_type'].widget = forms.HiddenInput()

            # تخصيص التسميات حسب النوع
            if partner_type == 'customer':
                self.fields['code'].widget.attrs['placeholder'] = _('رمز العميل')
                self.fields['name'].widget.attrs['placeholder'] = _('اسم العميل')
            elif partner_type == 'supplier':
                self.fields['code'].widget.attrs['placeholder'] = _('رمز المورد')
                self.fields['name'].widget.attrs['placeholder'] = _('اسم المورد')
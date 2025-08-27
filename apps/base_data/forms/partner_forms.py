# apps/base_data/forms/partner_forms.py
"""
Forms الخاصة بالشركاء التجاريين - محدث 100%
يشمل: BusinessPartner، العملاء، الموردين، الفلاتر، الإضافة السريعة
Bootstrap 5 + RTL + جميع الحقول من models.py
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ..models import BusinessPartner
from core.models import User


class BusinessPartnerForm(forms.ModelForm):
    """نموذج الشريك التجاري الكامل - محدث 100%"""

    class Meta:
        model = BusinessPartner
        fields = [
            'partner_type', 'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email', 'website',
            'address', 'city', 'region', 'tax_number', 'tax_status',
            'commercial_register', 'credit_limit', 'credit_period',
            'customer_account', 'supplier_account',  # الحسابات المحاسبية المفقودة
            'salesperson', 'discount_percentage', 'customer_category',
            'payment_terms', 'supplier_category', 'rating', 'notes'
        ]
        widgets = {
            'partner_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'togglePartnerFields()',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود الشريك'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الشريك'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف'),
                'dir': 'ltr'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموبايل'),
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الفاكس'),
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'dir': 'ltr'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الإلكتروني'),
                'dir': 'ltr'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('العنوان الكامل')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة')
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي'),
                'dir': 'ltr'
            }),
            'tax_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري'),
                'dir': 'ltr'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'dir': 'ltr'
            }),
            # الحسابات المحاسبية
            'customer_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب العميل')
            }),
            'supplier_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب المورد')
            }),
            'salesperson': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر مندوب المبيعات')
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'dir': 'ltr'
            }),
            'customer_category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('شروط الدفع')
            }),
            'supplier_category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية')
            }),
        }
        labels = {
            'partner_type': _('نوع الشريك'),
            'code': _('كود الشريك'),
            'name': _('اسم الشريك'),
            'name_en': _('الاسم بالإنجليزية'),
            'account_type': _('نوع الحساب'),
            'contact_person': _('جهة الاتصال'),
            'phone': _('الهاتف'),
            'mobile': _('الموبايل'),
            'fax': _('الفاكس'),
            'email': _('البريد الإلكتروني'),
            'website': _('الموقع الإلكتروني'),
            'address': _('العنوان'),
            'city': _('المدينة'),
            'region': _('المنطقة'),
            'tax_number': _('الرقم الضريبي'),
            'tax_status': _('الحالة الضريبية'),
            'commercial_register': _('السجل التجاري'),
            'credit_limit': _('حد الائتمان'),
            'credit_period': _('فترة الائتمان (أيام)'),
            'customer_account': _('حساب العميل'),
            'supplier_account': _('حساب المورد'),
            'salesperson': _('مندوب المبيعات'),
            'discount_percentage': _('نسبة الخصم %'),
            'customer_category': _('تصنيف العميل'),
            'payment_terms': _('شروط الدفع'),
            'supplier_category': _('تصنيف المورد'),
            'rating': _('التقييم (1-5)'),
            'notes': _('ملاحظات'),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة مندوبي المبيعات حسب الشركة
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

            # فلترة الحسابات المحاسبية
            try:
                from accounting.models import Account
                accounts = Account.objects.filter(
                    company=company, is_active=True
                ).order_by('code')

                self.fields['customer_account'].queryset = accounts
                self.fields['supplier_account'].queryset = accounts
            except ImportError:
                # في حالة عدم وجود app المحاسبة
                pass

        # تحسين القوائم المنسدلة
        self.fields['partner_type'].empty_label = None
        self.fields['account_type'].empty_label = None
        self.fields['tax_status'].empty_label = None
        self.fields['customer_category'].empty_label = None
        self.fields['supplier_category'].empty_label = None

        # جعل الحقول الاختيارية
        optional_fields = [
            'code', 'name_en', 'contact_person', 'phone', 'mobile', 'fax',
            'email', 'website', 'address', 'city', 'region', 'tax_number',
            'commercial_register', 'customer_account', 'supplier_account',
            'salesperson', 'payment_terms', 'notes'
        ]
        for field in optional_fields:
            self.fields[field].required = False

    def clean_code(self):
        """التحقق من تفرد الكود"""
        code = self.cleaned_data.get('code')
        if code:
            queryset = BusinessPartner.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الكود مستخدم من قبل'))
        return code

    def clean_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(_('البريد الإلكتروني غير صحيح'))
        return email

    def clean_rating(self):
        """التحقق من التقييم"""
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError(_('التقييم يجب أن يكون بين 1 و 5'))
        return rating

    def clean_discount_percentage(self):
        """التحقق من نسبة الخصم"""
        discount = self.cleaned_data.get('discount_percentage')
        if discount and (discount < 0 or discount > 100):
            raise ValidationError(_('نسبة الخصم يجب أن تكون بين 0 و 100'))
        return discount

    def clean(self):
        """التحقق من صحة البيانات الإجمالية"""
        cleaned_data = super().clean()
        partner_type = cleaned_data.get('partner_type')

        # التحقق من حقول العميل
        if partner_type in ['customer', 'both']:
            discount = cleaned_data.get('discount_percentage', 0)
            if discount and discount > 50:
                # تحذير فقط للخصومات الكبيرة
                pass

        # التحقق من حقول المورد
        if partner_type in ['supplier', 'both']:
            rating = cleaned_data.get('rating')
            if rating and (rating < 1 or rating > 5):
                self.add_error('rating', _('التقييم يجب أن يكون بين 1 و 5'))

        return cleaned_data


class CustomerForm(forms.ModelForm):
    """نموذج العميل - محدث بجميع الحقول"""

    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'name_en', 'account_type', 'contact_person',
            'phone', 'mobile', 'fax', 'email', 'website', 'address',
            'city', 'region', 'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'customer_account',
            'salesperson', 'discount_percentage', 'customer_category', 'notes'
        ]
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'customer_category': forms.Select(attrs={'class': 'form-select'}),
            'customer_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب العميل')
            }),
            'salesperson': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر مندوب المبيعات')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود العميل'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العميل'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الهاتف'),
                'dir': 'ltr'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموبايل'),
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الفاكس'),
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'dir': 'ltr'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الإلكتروني'),
                'dir': 'ltr'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('العنوان')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة')
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي'),
                'dir': 'ltr'
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('السجل التجاري'),
                'dir': 'ltr'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'dir': 'ltr'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات')
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

            # الحسابات المحاسبية
            try:
                from accounting.models import Account
                self.fields['customer_account'].queryset = Account.objects.filter(
                    company=company, is_active=True
                ).order_by('code')
            except ImportError:
                pass

        # جعل الحقول اختيارية
        optional_fields = [
            'code', 'name_en', 'contact_person', 'phone', 'mobile', 'fax',
            'email', 'website', 'address', 'city', 'region', 'tax_number',
            'commercial_register', 'customer_account', 'salesperson', 'notes'
        ]
        for field in optional_fields:
            self.fields[field].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        # تعيين نوع الشريك كعميل
        if instance.partner_type == 'supplier':
            instance.partner_type = 'both'
        else:
            instance.partner_type = 'customer'

        if commit:
            instance.save()
        return instance


class SupplierForm(forms.ModelForm):
    """نموذج المورد - محدث بجميع الحقول"""

    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'name_en', 'account_type', 'contact_person',
            'phone', 'mobile', 'fax', 'email', 'website', 'address',
            'city', 'region', 'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'supplier_account',
            'payment_terms', 'supplier_category', 'rating', 'notes'
        ]
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'supplier_category': forms.Select(attrs={'class': 'form-select'}),
            'supplier_account': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر حساب المورد')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود المورد'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المورد'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الهاتف'),
                'dir': 'ltr'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموبايل'),
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الفاكس'),
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'dir': 'ltr'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الإلكتروني'),
                'dir': 'ltr'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('العنوان')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة')
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم الضريبي'),
                'dir': 'ltr'
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('السجل التجاري'),
                'dir': 'ltr'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'dir': 'ltr'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'dir': 'ltr'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('شروط الدفع')
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات')
            }),
        }
        labels = {
            'rating': _('التقييم (1-5)'),
            'payment_terms': _('شروط الدفع'),
            'supplier_category': _('تصنيف المورد'),
            'supplier_account': _('حساب المورد'),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # الحسابات المحاسبية
            try:
                from accounting.models import Account
                self.fields['supplier_account'].queryset = Account.objects.filter(
                    company=company, is_active=True
                ).order_by('code')
            except ImportError:
                pass

        # جعل الحقول اختيارية
        optional_fields = [
            'code', 'name_en', 'contact_person', 'phone', 'mobile', 'fax',
            'email', 'website', 'address', 'city', 'region', 'tax_number',
            'commercial_register', 'supplier_account', 'payment_terms', 'notes'
        ]
        for field in optional_fields:
            self.fields[field].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        # تعيين نوع الشريك كمورد
        if instance.partner_type == 'customer':
            instance.partner_type = 'both'
        else:
            instance.partner_type = 'supplier'

        if commit:
            instance.save()
        return instance

    def clean_rating(self):
        """التحقق من صحة التقييم"""
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError(_('التقييم يجب أن يكون بين 1 و 5'))
        return rating


class PartnerQuickAddForm(forms.ModelForm):
    """نموذج الإضافة السريعة للشريك"""

    class Meta:
        model = BusinessPartner
        fields = ['partner_type', 'code', 'name', 'name_en', 'phone', 'email']
        widgets = {
            'partner_type': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('كود الشريك'),
                'dir': 'ltr'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('اسم الشريك'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('الاسم بالإنجليزية'),
                'dir': 'ltr'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('رقم الهاتف'),
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('البريد الإلكتروني'),
                'dir': 'ltr'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['partner_type'].empty_label = None
        self.fields['code'].required = False
        self.fields['name_en'].required = False
        self.fields['phone'].required = False
        self.fields['email'].required = False


class ContactInfoForm(forms.ModelForm):
    """نموذج تحديث معلومات الاتصال فقط"""

    class Meta:
        model = BusinessPartner
        fields = [
            'contact_person', 'phone', 'mobile', 'fax', 'email',
            'website', 'address', 'city', 'region'
        ]
        widgets = {
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف'),
                'dir': 'ltr'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموبايل'),
                'dir': 'ltr'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الفاكس'),
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'dir': 'ltr'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الإلكتروني'),
                'dir': 'ltr'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('العنوان الكامل')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدينة')
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('المنطقة')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جميع الحقول اختيارية
        for field in self.fields.values():
            field.required = False


class PartnerImportForm(forms.Form):
    """نموذج استيراد الشركاء من Excel"""

    file = forms.FileField(
        label=_('ملف Excel'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        }),
        help_text=_('يجب أن يكون الملف بصيغة Excel (.xlsx أو .xls) أو CSV')
    )

    update_existing = forms.BooleanField(
        required=False,
        label=_('تحديث الموجود'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('في حالة وجود شريك بنفس الكود، سيتم تحديث بياناته')
    )

    import_type = forms.ChoiceField(
        label=_('نوع الاستيراد'),
        choices=[
            ('all', _('جميع الشركاء')),
            ('customers', _('العملاء فقط')),
            ('suppliers', _('الموردين فقط')),
        ],
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    validate_data = forms.BooleanField(
        required=False,
        label=_('التحقق من البيانات'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text=_('التحقق من صحة البيانات قبل الاستيراد')
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise ValidationError(_('الملف يجب أن يكون بصيغة Excel أو CSV'))

            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError(_('حجم الملف يجب أن يكون أقل من 10 ميجابايت'))

        return file


class PartnerExportForm(forms.Form):
    """نموذج تصدير الشركاء"""

    export_type = forms.ChoiceField(
        label=_('نوع التصدير'),
        choices=[
            ('all', _('جميع الشركاء')),
            ('customers', _('العملاء فقط')),
            ('suppliers', _('الموردين فقط')),
            ('active', _('النشطين فقط')),
            ('inactive', _('غير النشطين فقط')),
        ],
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    export_format = forms.ChoiceField(
        label=_('صيغة الملف'),
        choices=[
            ('xlsx', _('Excel (XLSX)')),
            ('csv', _('CSV')),
            ('pdf', _('PDF')),
        ],
        initial='xlsx',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    include_contact_info = forms.BooleanField(
        required=False,
        label=_('تضمين معلومات الاتصال'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    include_financial_info = forms.BooleanField(
        required=False,
        label=_('تضمين المعلومات المالية'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
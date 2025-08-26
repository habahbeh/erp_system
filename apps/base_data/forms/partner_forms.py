# apps/base_data/forms/partner_forms.py
"""
Forms الخاصة بالشركاء التجاريين
يشمل: BusinessPartner، العملاء، الموردين، الفلاتر، الإضافة السريعة
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import BusinessPartner


class BusinessPartnerForm(forms.ModelForm):
    """نموذج الشريك التجاري الكامل"""

    class Meta:
        model = BusinessPartner
        fields = [
            'partner_type', 'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email', 'website',
            'address', 'city', 'region', 'tax_number', 'tax_status',
            'commercial_register', 'credit_limit', 'credit_period',
            'salesperson', 'discount_percentage', 'customer_category',
            'payment_terms', 'supplier_category', 'rating', 'notes'
        ]
        widgets = {
            'partner_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'togglePartnerFields()'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'customer_category': forms.Select(attrs={'class': 'form-select'}),
            'supplier_category': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('كود الشريك')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الشريك'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم بالإنجليزية')
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم جهة الاتصال')
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
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('الموقع الإلكتروني')
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
                'placeholder': _('الرقم الضريبي')
            }),
            'commercial_register': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم السجل التجاري')
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'credit_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'salesperson': forms.Select(attrs={'class': 'form-select'}),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('شروط الدفع')
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
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
            'salesperson': _('مندوب المبيعات'),
            'discount_percentage': _('نسبة الخصم %'),
            'customer_category': _('تصنيف العميل'),
            'payment_terms': _('شروط الدفع'),
            'supplier_category': _('تصنيف المورد'),
            'rating': _('التقييم'),
            'notes': _('ملاحظات'),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة مندوبي المبيعات حسب الشركة
            from core.models import User
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company, is_active=True
            )
            self.fields['salesperson'].empty_label = _('اختر مندوب المبيعات')

        # تحسين القوائم المنسدلة
        self.fields['partner_type'].empty_label = None
        self.fields['account_type'].empty_label = None
        self.fields['tax_status'].empty_label = None

    def clean_code(self):
        """التحقق من تفرد الكود"""
        code = self.cleaned_data.get('code')
        if code:
            # التحقق من الكود المكرر في نفس الشركة
            queryset = BusinessPartner.objects.filter(
                company=self.instance.company if self.instance.pk else None,
                code=code
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(_('هذا الكود مستخدم من قبل'))

        return code

    def clean_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email

    def clean(self):
        """التحقق من صحة البيانات الإجمالية"""
        cleaned_data = super().clean()
        partner_type = cleaned_data.get('partner_type')

        # التحقق من حقول العميل
        if partner_type in ['customer', 'both']:
            if not cleaned_data.get('salesperson'):
                # يمكن ترك مندوب المبيعات فارغاً
                pass

        # التحقق من حقول المورد
        if partner_type in ['supplier', 'both']:
            rating = cleaned_data.get('rating')
            if rating and (rating < 1 or rating > 5):
                self.add_error('rating', _('التقييم يجب أن يكون بين 1 و 5'))

        return cleaned_data


class CustomerForm(forms.ModelForm):
    """نموذج العميل - يركز على حقول العملاء فقط"""

    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'name_en', 'account_type', 'contact_person',
            'phone', 'mobile', 'fax', 'email', 'website', 'address',
            'city', 'region', 'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'salesperson',
            'discount_percentage', 'customer_category', 'notes'
        ]
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'customer_category': forms.Select(attrs={'class': 'form-select'}),
            'salesperson': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('كود العميل')}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم العميل')}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم بالإنجليزية')}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('جهة الاتصال')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الهاتف')}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الموبايل')}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الفاكس')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('الموقع الإلكتروني')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('العنوان')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('المدينة')}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('المنطقة')}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الرقم الضريبي')}),
            'commercial_register': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('السجل التجاري')}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'credit_period': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'discount_percentage': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('ملاحظات')}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            from core.models import User
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company, is_active=True
            )
            self.fields['salesperson'].empty_label = _('اختر مندوب المبيعات')

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
    """نموذج المورد - يركز على حقول الموردين فقط"""

    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'name_en', 'account_type', 'contact_person',
            'phone', 'mobile', 'fax', 'email', 'website', 'address',
            'city', 'region', 'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'payment_terms',
            'supplier_category', 'rating', 'notes'
        ]
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_status': forms.Select(attrs={'class': 'form-select'}),
            'supplier_category': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('كود المورد')}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المورد')}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم بالإنجليزية')}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('جهة الاتصال')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الهاتف')}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الموبايل')}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الفاكس')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('الموقع الإلكتروني')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('العنوان')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('المدينة')}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('المنطقة')}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الرقم الضريبي')}),
            'commercial_register': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('السجل التجاري')}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'credit_period': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('شروط الدفع')}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('ملاحظات')}),
        }
        labels = {
            'rating': _('التقييم (1-5)'),
            'payment_terms': _('شروط الدفع'),
            'supplier_category': _('تصنيف المورد'),
        }

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
            raise forms.ValidationError(_('التقييم يجب أن يكون بين 1 و 5'))
        return rating


class PartnerQuickAddForm(forms.ModelForm):
    """نموذج الإضافة السريعة للشريك"""

    class Meta:
        model = BusinessPartner
        fields = ['partner_type', 'code', 'name', 'name_en', 'phone', 'email']
        widgets = {
            'partner_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('كود الشريك'), 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم الشريك'), 'required': True}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('الاسم بالإنجليزية')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('رقم الهاتف')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('البريد الإلكتروني')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['partner_type'].empty_label = None


class PartnerFilterForm(forms.Form):
    """نموذج فلترة الشركاء"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('البحث في الكود أو الاسم أو الهاتف...'),
            'class': 'form-control'
        }),
        label=_('البحث السريع')
    )

    partner_type = forms.ChoiceField(
        choices=[('', _('كل الأنواع'))] + BusinessPartner.PARTNER_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('نوع الشريك')
    )

    account_type = forms.ChoiceField(
        choices=[('', _('كل أنواع الحسابات'))] + BusinessPartner.ACCOUNT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('نوع الحساب')
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('المدينة...'),
            'class': 'form-control'
        }),
        label=_('المدينة')
    )

    is_active = forms.BooleanField(
        required=False,
        label=_("النشطة فقط"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة CSS classes للحقول
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({'class': 'form-control'})


class ContactInfoForm(forms.ModelForm):
    """نموذج تحديث معلومات الاتصال فقط"""

    class Meta:
        model = BusinessPartner
        fields = [
            'contact_person', 'phone', 'mobile', 'fax', 'email',
            'website', 'address', 'city', 'region'
        ]
        widgets = {
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PartnerImportForm(forms.Form):
    """نموذج استيراد الشركاء من Excel"""

    file = forms.FileField(
        label=_('ملف Excel'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        }),
        help_text=_('يجب أن يكون الملف بصيغة Excel (.xlsx أو .xls)')
    )

    update_existing = forms.BooleanField(
        required=False,
        label=_('تحديث الموجود'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('في حالة وجود شريك بنفس الكود، سيتم تحديث بياناته')
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(_('الملف يجب أن يكون بصيغة Excel'))

            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_('حجم الملف يجب أن يكون أقل من 5 ميجابايت'))

        return file
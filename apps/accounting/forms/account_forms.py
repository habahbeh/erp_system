# apps/accounting/forms/account_forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Account, AccountType
from apps.core.models import Currency


class AccountForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الحسابات"""

    class Meta:
        model = Account
        fields = [
            'code', 'name', 'name_en', 'account_type', 'parent',
            'currency', 'nature', 'notes', 'is_suspended',
            'is_cash_account', 'is_bank_account', 'accept_entries',
            'opening_balance', 'opening_balance_date'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # تخصيص الحقول الأساسية
        self.fields['code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('رمز الحساب (مثال: 1111)'),
            'maxlength': '20'
        })

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('اسم الحساب بالعربية')
        })

        self.fields['name_en'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('اسم الحساب بالإنجليزية (اختياري)')
        })

        # قوائم منسدلة
        self.fields['account_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent'].widget.attrs.update({'class': 'form-select'})
        self.fields['currency'].widget.attrs.update({'class': 'form-select'})
        self.fields['nature'].widget.attrs.update({'class': 'form-select'})

        # حقول نصية
        self.fields['notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': '3',
            'placeholder': _('ملاحظات إضافية (اختياري)')
        })

        # حقول رقمية
        self.fields['opening_balance'].widget.attrs.update({
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000'
        })

        self.fields['opening_balance_date'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })

        # checkboxes
        checkbox_fields = ['is_suspended', 'is_cash_account', 'is_bank_account', 'accept_entries']
        for field in checkbox_fields:
            self.fields[field].widget.attrs.update({'class': 'form-check-input'})

        # تحديد التسميات
        self.fields['code'].label = _('رمز الحساب')
        self.fields['name'].label = _('اسم الحساب')
        self.fields['name_en'].label = _('الاسم الإنجليزي')
        self.fields['account_type'].label = _('نوع الحساب')
        self.fields['parent'].label = _('الحساب الأب')
        self.fields['currency'].label = _('العملة الافتراضية')
        self.fields['nature'].label = _('طبيعة الحساب')
        self.fields['notes'].label = _('ملاحظات')
        self.fields['is_suspended'].label = _('موقوف')
        self.fields['is_cash_account'].label = _('حساب نقدي')
        self.fields['is_bank_account'].label = _('حساب بنكي')
        self.fields['accept_entries'].label = _('يقبل قيود مباشرة')
        self.fields['opening_balance'].label = _('الرصيد الافتتاحي')
        self.fields['opening_balance_date'].label = _('تاريخ الرصيد الافتتاحي')

        # فلترة الحسابات الأب (استثناء الحساب الحالي من قائمة الآباء)
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Account.objects.exclude(
                pk=self.instance.pk
            ).filter(
                company=self.request.current_company if self.request else None
            )
        else:
            if self.request and hasattr(self.request, 'current_company'):
                self.fields['parent'].queryset = Account.objects.filter(
                    company=self.request.current_company
                )

        # فلترة أنواع الحسابات والعملات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        company = None

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

        # التحقق من عدم تكرار الرمز في نفس الشركة
        existing = Account.objects.filter(code=code, company=company).exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError(_('رمز الحساب موجود مسبقاً في هذه الشركة'))

        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if len(name) < 3:
            raise ValidationError(_('يجب أن يكون اسم الحساب 3 أحرف على الأقل'))

        return name

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        accept_entries = cleaned_data.get('accept_entries')

        # منع تحديد حساب أب يقبل قيود مباشرة
        if parent and parent.accept_entries:
            raise ValidationError({
                'parent': _('لا يمكن اختيار حساب أب يقبل قيود مباشرة. يجب تعديل الحساب الأب أولاً.')
            })

        # التحقق من أن الحساب الحالي إذا كان له أطفال لا يمكنه قبول قيود
        if self.instance and self.instance.pk:
            if self.instance.children.exists() and accept_entries:
                raise ValidationError({
                    'accept_entries': _('الحسابات الأب لا يمكنها قبول قيود مباشرة. احذف الحسابات الفرعية أولاً.')
                })

        return cleaned_data


class AccountImportForm(forms.Form):
    """نموذج استيراد الحسابات من ملف Excel/CSV"""

    file = forms.FileField(
        label=_('ملف الاستيراد'),
        help_text=_('يدعم ملفات Excel (.xlsx, .xls) و CSV (.csv)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    update_existing = forms.BooleanField(
        label=_('تحديث الحسابات الموجودة'),
        help_text=_('في حالة وجود حساب بنفس الرمز، سيتم تحديث بياناته'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        file = self.cleaned_data['file']

        # التحقق من نوع الملف
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(_('نوع الملف غير مدعوم. يرجى رفع ملف Excel أو CSV'))

        # التحقق من حجم الملف (10MB max)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError(_('حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت'))

        return file


class AccountFilterForm(forms.Form):
    """نموذج فلترة الحسابات"""

    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        required=False,
        empty_label=_("جميع الأنواع"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_active = forms.ChoiceField(
        choices=[('', _('الكل')), ('1', _('نشط')), ('0', _('موقوف'))],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    has_children = forms.ChoiceField(
        choices=[('', _('الكل')), ('1', _('حسابات أب')), ('0', _('حسابات فرعية'))],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الرمز أو الاسم')
        })
    )
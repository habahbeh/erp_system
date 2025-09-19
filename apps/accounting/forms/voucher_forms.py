# apps/accounting/forms/voucher_forms.py
"""
نماذج السندات (القبض والصرف)
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import PaymentVoucher, ReceiptVoucher, Account
from apps.core.models import Currency


class PaymentVoucherForm(forms.ModelForm):
    """نموذج سند الصرف"""

    # حقول البحث للحسابات
    cash_account_search = forms.CharField(
        label=_('حساب الصندوق/البنك'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن حساب الصندوق أو البنك...',
            'data-target': 'cash_account'
        })
    )

    expense_account_search = forms.CharField(
        label=_('حساب المصروف'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن حساب المصروف (اختياري)...',
            'data-target': 'expense_account'
        })
    )

    class Meta:
        model = PaymentVoucher
        fields = [
            'date', 'amount', 'currency', 'beneficiary_name', 'beneficiary_type',
            'cash_account', 'expense_account', 'payment_method',
            'check_number', 'check_date', 'bank_name',
            'description', 'notes'
        ]

        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'beneficiary_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المستفيد...'
            }),
            'beneficiary_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cash_account': forms.HiddenInput(),
            'expense_account': forms.HiddenInput(),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'check_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الشيك...'
            }),
            'check_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم البنك...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف العملية...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية (اختياري)...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            # فلترة العملات والحسابات للشركة الحالية
            self.fields['currency'].queryset = Currency.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

            # إعداد العملة الافتراضية
            try:
                default_currency = Currency.objects.get(
                    company=self.request.current_company,
                    is_base=True
                )
                self.fields['currency'].initial = default_currency
            except Currency.DoesNotExist:
                pass

        # إذا كان النموذج يحتوي على بيانات موجودة
        if self.instance and self.instance.pk:
            if self.instance.cash_account:
                self.fields['cash_account_search'].initial = str(self.instance.cash_account)
            if self.instance.expense_account:
                self.fields['expense_account_search'].initial = str(self.instance.expense_account)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

        # التحقق من بيانات الشيك
        if payment_method == 'check':
            check_number = cleaned_data.get('check_number')
            check_date = cleaned_data.get('check_date')
            bank_name = cleaned_data.get('bank_name')

            if not check_number:
                raise ValidationError({'check_number': _('رقم الشيك مطلوب عند اختيار الدفع بالشيك')})
            if not check_date:
                raise ValidationError({'check_date': _('تاريخ الشيك مطلوب عند اختيار الدفع بالشيك')})
            if not bank_name:
                raise ValidationError({'bank_name': _('اسم البنك مطلوب عند اختيار الدفع بالشيك')})

        # التحقق من وجود حساب الصندوق
        cash_account = cleaned_data.get('cash_account')
        if not cash_account:
            raise ValidationError({'cash_account': _('حساب الصندوق/البنك مطلوب')})

        return cleaned_data


class ReceiptVoucherForm(forms.ModelForm):
    """نموذج سند القبض"""

    # حقول البحث للحسابات
    cash_account_search = forms.CharField(
        label=_('حساب الصندوق/البنك'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن حساب الصندوق أو البنك...',
            'data-target': 'cash_account'
        })
    )

    income_account_search = forms.CharField(
        label=_('حساب الإيراد'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن حساب الإيراد (اختياري)...',
            'data-target': 'income_account'
        })
    )

    class Meta:
        model = ReceiptVoucher
        fields = [
            'date', 'amount', 'currency', 'received_from', 'payer_type',
            'cash_account', 'income_account', 'receipt_method',
            'check_number', 'check_date', 'bank_name',
            'description', 'notes'
        ]

        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'received_from': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الدافع...'
            }),
            'payer_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cash_account': forms.HiddenInput(),
            'income_account': forms.HiddenInput(),
            'receipt_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'check_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الشيك...'
            }),
            'check_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم البنك...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف العملية...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية (اختياري)...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            # فلترة العملات للشركة الحالية
            self.fields['currency'].queryset = Currency.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

            # إعداد العملة الافتراضية
            try:
                default_currency = Currency.objects.get(
                    company=self.request.current_company,
                    is_base=True
                )
                self.fields['currency'].initial = default_currency
            except Currency.DoesNotExist:
                pass

        # إذا كان النموذج يحتوي على بيانات موجودة
        if self.instance and self.instance.pk:
            if self.instance.cash_account:
                self.fields['cash_account_search'].initial = str(self.instance.cash_account)
            if self.instance.income_account:
                self.fields['income_account_search'].initial = str(self.instance.income_account)

    def clean(self):
        cleaned_data = super().clean()
        receipt_method = cleaned_data.get('receipt_method')

        # التحقق من بيانات الشيك
        if receipt_method == 'check':
            check_number = cleaned_data.get('check_number')
            check_date = cleaned_data.get('check_date')
            bank_name = cleaned_data.get('bank_name')

            if not check_number:
                raise ValidationError({'check_number': _('رقم الشيك مطلوب عند اختيار القبض بالشيك')})
            if not check_date:
                raise ValidationError({'check_date': _('تاريخ الشيك مطلوب عند اختيار القبض بالشيك')})
            if not bank_name:
                raise ValidationError({'bank_name': _('اسم البنك مطلوب عند اختيار القبض بالشيك')})

        # التحقق من وجود حساب الصندوق
        cash_account = cleaned_data.get('cash_account')
        if not cash_account:
            raise ValidationError({'cash_account': _('حساب الصندوق/البنك مطلوب')})

        return cleaned_data
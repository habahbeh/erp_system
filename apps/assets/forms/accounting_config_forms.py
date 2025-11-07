# apps/assets/forms/accounting_config_forms.py
"""
نماذج إعدادات الحسابات المحاسبية للأصول
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from apps.assets.models import AssetAccountingConfiguration
from apps.accounting.models import Account


class AssetAccountingConfigurationForm(forms.ModelForm):
    """نموذج إعدادات الحسابات المحاسبية"""

    class Meta:
        model = AssetAccountingConfiguration
        fields = [
            # حسابات الصيانة
            'default_maintenance_expense_account',
            'capital_improvement_account',

            # حسابات الإيجار
            'operating_lease_expense_account',
            'finance_lease_liability_account',
            'finance_lease_interest_expense_account',

            # حسابات التأمين
            'insurance_expense_account',
            'insurance_deductible_expense_account',
            'insurance_claim_income_account',

            # حسابات عامة
            'default_cash_account',
            'default_bank_account',
            'default_supplier_account',
        ]

        widgets = {
            'default_maintenance_expense_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب مصروف الصيانة')
            }),
            'capital_improvement_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب التحسينات الرأسمالية')
            }),
            'operating_lease_expense_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب مصروف الإيجار التشغيلي')
            }),
            'finance_lease_liability_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب التزامات الإيجار التمويلي')
            }),
            'finance_lease_interest_expense_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب مصروف الفوائد')
            }),
            'insurance_expense_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب مصروف التأمين')
            }),
            'insurance_deductible_expense_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب مصروف التحمل')
            }),
            'insurance_claim_income_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب إيرادات التعويضات')
            }),
            'default_cash_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب النقدية الافتراضي')
            }),
            'default_bank_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب البنك الافتراضي')
            }),
            'default_supplier_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': _('اختر حساب الموردين الافتراضي')
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            # Filter accounts by company
            for field_name in self.fields:
                if isinstance(self.fields[field_name], forms.ModelChoiceField):
                    self.fields[field_name].queryset = Account.objects.filter(
                        company=company,
                        is_active=True
                    ).order_by('code')

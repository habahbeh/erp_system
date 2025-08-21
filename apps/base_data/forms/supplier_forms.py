# apps/base_data/forms/supplier_forms.py
"""
نماذج الموردين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import Supplier
from .customer_forms import CustomerForm


class SupplierForm(CustomerForm):
    """نموذج المورد - يرث من نموذج العميل"""

    class Meta(CustomerForm.Meta):
        model = Supplier
        fields = [
            'code', 'name', 'name_en', 'account_type',
            'contact_person', 'phone', 'mobile', 'fax', 'email', 'website',
            'address', 'city', 'region',
            'tax_number', 'tax_status', 'commercial_register',
            'credit_limit', 'credit_period', 'payment_terms',
            'notes', 'is_active'
        ]

    payment_terms = forms.CharField(
        label=_('شروط الدفع'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: الدفع خلال 30 يوم من تاريخ الفاتورة')
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إزالة حقل مندوب المبيعات
        if 'salesperson' in self.fields:
            del self.fields['salesperson']
        # إزالة حقل نسبة الخصم
        if 'discount_percentage' in self.fields:
            del self.fields['discount_percentage']
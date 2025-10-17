# apps/assets/forms/transaction_forms.py
"""
نماذج العمليات على الأصول
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import AssetTransaction, AssetTransfer, Asset
from apps.accounting.models import Account, CostCenter
from apps.core.models import Branch, User


class AssetTransactionForm(forms.ModelForm):
    """نموذج العمليات العامة على الأصول"""

    class Meta:
        model = AssetTransaction
        fields = [
            'transaction_date', 'transaction_type', 'asset',
            'amount', 'payment_method', 'business_partner',
            'reference_number', 'attachment', 'description', 'notes'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'business_partner': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاتورة أو المرجع'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['business_partner'].queryset = Account.objects.filter(
                company=self.company,
                is_active=True
            )


class AssetPurchaseForm(forms.ModelForm):
    """نموذج شراء أصل جديد"""

    class Meta:
        model = AssetTransaction
        fields = [
            'transaction_date', 'asset', 'amount',
            'payment_method', 'business_partner',
            'reference_number', 'attachment', 'description', 'notes'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'business_partner': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختر المورد'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاتورة'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'تفاصيل عملية الشراء'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تعيين نوع العملية
        self.instance.transaction_type = 'purchase'

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            )
            # فقط الموردين
            self.fields['business_partner'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='liabilities',
                is_active=True
            )
            self.fields['business_partner'].label = _('المورد')


class AssetSaleForm(forms.ModelForm):
    """نموذج بيع أصل"""

    class Meta:
        model = AssetTransaction
        fields = [
            'transaction_date', 'asset', 'sale_price',
            'payment_method', 'business_partner',
            'reference_number', 'attachment', 'description', 'notes'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'business_partner': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختر العميل'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم العقد أو الفاتورة'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'تفاصيل عملية البيع'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تعيين نوع العملية
        self.instance.transaction_type = 'sale'

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            )
            # فقط العملاء
            self.fields['business_partner'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='assets',
                is_active=True
            )
            self.fields['business_partner'].label = _('العميل')

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        sale_price = cleaned_data.get('sale_price')

        if asset and sale_price:
            # حساب القيمة الدفترية والربح/الخسارة
            cleaned_data['book_value_at_sale'] = asset.book_value
            cleaned_data['gain_loss'] = sale_price - asset.book_value
            cleaned_data['amount'] = sale_price

        return cleaned_data


class AssetDisposalForm(forms.ModelForm):
    """نموذج استبعاد/إتلاف أصل"""

    class Meta:
        model = AssetTransaction
        fields = [
            'transaction_date', 'asset',
            'description', 'attachment', 'notes'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'سبب الاستبعاد/الإتلاف وتفاصيله'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تعيين نوع العملية
        self.instance.transaction_type = 'disposal'
        self.instance.amount = Decimal('0.00')

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            )


class AssetTransferForm(forms.ModelForm):
    """نموذج تحويل أصل"""

    class Meta:
        model = AssetTransfer
        fields = [
            'transfer_date', 'asset',
            'from_branch', 'from_cost_center', 'from_employee',
            'to_branch', 'to_cost_center', 'to_employee',
            'reason', 'notes'
        ]
        widgets = {
            'transfer_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'from_branch': forms.Select(attrs={'class': 'form-select'}),
            'from_cost_center': forms.Select(attrs={'class': 'form-select'}),
            'from_employee': forms.Select(attrs={'class': 'form-select'}),
            'to_branch': forms.Select(attrs={'class': 'form-select'}),
            'to_cost_center': forms.Select(attrs={'class': 'form-select'}),
            'to_employee': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'سبب التحويل'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            )
            self.fields['from_branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['to_branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['from_cost_center'].queryset = CostCenter.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['to_cost_center'].queryset = CostCenter.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['from_employee'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['to_employee'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )

        # إذا كان هناك أصل محدد، ملء البيانات الحالية
        if self.instance.asset_id:
            asset = self.instance.asset
            if not self.instance.from_branch_id:
                self.initial['from_branch'] = asset.branch
            if not self.instance.from_cost_center_id:
                self.initial['from_cost_center'] = asset.cost_center
            if not self.instance.from_employee_id:
                self.initial['from_employee'] = asset.responsible_employee

    def clean(self):
        cleaned_data = super().clean()

        from_branch = cleaned_data.get('from_branch')
        to_branch = cleaned_data.get('to_branch')
        from_cost_center = cleaned_data.get('from_cost_center')
        to_cost_center = cleaned_data.get('to_cost_center')
        from_employee = cleaned_data.get('from_employee')
        to_employee = cleaned_data.get('to_employee')

        # التحقق من وجود تغيير
        if (from_branch == to_branch and
                from_cost_center == to_cost_center and
                from_employee == to_employee):
            raise ValidationError(
                _('يجب أن يكون هناك تغيير في الفرع أو مركز التكلفة أو الموظف المسؤول')
            )

        return cleaned_data
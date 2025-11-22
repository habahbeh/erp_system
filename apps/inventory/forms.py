# apps/inventory/forms.py
"""
نماذج المخازن
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from decimal import Decimal

from .models import (
    StockIn, StockOut, StockTransfer, StockCount, StockMovement,
    StockDocumentLine, StockTransferLine, StockCountLine,
    ItemStock, Batch
)
from apps.core.models import Item, ItemVariant, Warehouse, BusinessPartner


class StockInForm(forms.ModelForm):
    """نموذج سند الإدخال"""

    class Meta:
        model = StockIn
        fields = [
            'date', 'warehouse', 'source_type', 'supplier',
            'purchase_invoice', 'reference', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'purchase_invoice': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = getattr(self.request, 'current_company', None)

            if company:
                # تصفية المستودعات حسب الشركة
                self.fields['warehouse'].queryset = Warehouse.objects.filter(
                    company=company,
                    is_active=True
                ).order_by('name')

                # تصفية الموردين
                self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                    company=company,
                    partner_type__in=['supplier', 'both'],
                    is_active=True
                ).order_by('name')

                # جعل الحقول اختيارية
                self.fields['supplier'].required = False
                self.fields['purchase_invoice'].required = False


class StockDocumentLineForm(forms.ModelForm):
    """نموذج سطر سند إدخال/إخراج"""

    class Meta:
        model = StockDocumentLine
        fields = [
            'item', 'item_variant', 'quantity', 'unit_cost',
            'batch_number', 'expiry_date', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}),
            'item_variant': forms.Select(attrs={'class': 'form-select variant-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'step': '0.001',
                'min': '0.001'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control unit-cost-input',
                'step': '0.001',
                'min': '0'
            }),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Formsets
StockInLineFormSet = inlineformset_factory(
    StockIn,
    StockDocumentLine,
    form=StockDocumentLineForm,
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class StockOutForm(forms.ModelForm):
    """نموذج سند الإخراج"""

    class Meta:
        model = StockOut
        fields = [
            'date', 'warehouse', 'destination_type', 'customer',
            'sales_invoice', 'reference', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'destination_type': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'sales_invoice': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = getattr(self.request, 'current_company', None)

            if company:
                self.fields['warehouse'].queryset = Warehouse.objects.filter(
                    company=company,
                    is_active=True
                ).order_by('name')

                self.fields['customer'].queryset = BusinessPartner.objects.filter(
                    company=company,
                    partner_type__in=['customer', 'both'],
                    is_active=True
                ).order_by('name')

                self.fields['customer'].required = False
                self.fields['sales_invoice'].required = False


StockOutLineFormSet = inlineformset_factory(
    StockOut,
    StockDocumentLine,
    form=StockDocumentLineForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class StockTransferForm(forms.ModelForm):
    """نموذج التحويل بين المستودعات"""

    class Meta:
        model = StockTransfer
        fields = [
            'date', 'warehouse', 'destination_warehouse',
            'reference', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_source_warehouse'
            }),
            'destination_warehouse': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_dest_warehouse'
            }),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = getattr(self.request, 'current_company', None)

            if company:
                warehouses = Warehouse.objects.filter(
                    company=company,
                    is_active=True
                ).order_by('name')

                self.fields['warehouse'].queryset = warehouses
                self.fields['destination_warehouse'].queryset = warehouses

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('warehouse')
        destination = cleaned_data.get('destination_warehouse')

        if source and destination and source == destination:
            raise forms.ValidationError(
                _('لا يمكن التحويل من وإلى نفس المستودع')
            )

        return cleaned_data


class StockTransferLineForm(forms.ModelForm):
    """نموذج سطر التحويل"""

    class Meta:
        model = StockTransferLine
        fields = [
            'item', 'item_variant', 'quantity',
            'batch_number', 'expiry_date', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}),
            'item_variant': forms.Select(attrs={'class': 'form-select variant-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'step': '0.001',
                'min': '0.001'
            }),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


StockTransferLineFormSet = inlineformset_factory(
    StockTransfer,
    StockTransferLine,
    form=StockTransferLineForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class StockCountForm(forms.ModelForm):
    """نموذج الجرد"""

    class Meta:
        model = StockCount
        fields = [
            'date', 'count_type', 'warehouse', 'supervisor',
            'count_team', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'count_type': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'count_team': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Get company from request or passed parameter
        company = self.company
        if not company and self.request:
            company = getattr(self.request, 'current_company', None)

        if company:
            from apps.core.models import User

            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            # المستخدمون النشطون في الشركة
            users = User.objects.filter(
                company=company,
                is_active=True
            ).order_by('first_name', 'last_name')

            self.fields['supervisor'].queryset = users
            self.fields['count_team'].queryset = users


class StockCountLineForm(forms.ModelForm):
    """نموذج سطر الجرد"""

    class Meta:
        model = StockCountLine
        fields = [
            'item', 'system_quantity', 'counted_quantity',
            'unit_cost', 'notes', 'adjustment_reason'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'system_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'counted_quantity': forms.NumberInput(attrs={
                'class': 'form-control counted-qty-input',
                'step': '0.001'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
            'adjustment_reason': forms.TextInput(attrs={'class': 'form-control'}),
        }


StockCountLineFormSet = inlineformset_factory(
    StockCount,
    StockCountLine,
    form=StockCountLineForm,
    extra=0,  # لا نريد سطور فارغة في البداية
    can_delete=False
)


class ItemStockForm(forms.ModelForm):
    """نموذج تعديل رصيد مادة"""

    class Meta:
        model = ItemStock
        fields = [
            'min_level', 'max_level', 'reorder_point', 'storage_location'
        ]
        widgets = {
            'min_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'max_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BatchForm(forms.ModelForm):
    """نموذج إضافة/تعديل دفعة"""

    class Meta:
        model = Batch
        fields = [
            'item', 'item_variant', 'warehouse', 'batch_number',
            'manufacturing_date', 'expiry_date', 'quantity', 'unit_cost',
            'source_document', 'source_id', 'received_date'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'item_variant': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'source_document': forms.TextInput(attrs={'class': 'form-control'}),
            'source_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'received_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            company = getattr(self.request, 'current_company', None)

            if company:
                # تصفية المواد والمستودعات حسب الشركة
                self.fields['item'].queryset = Item.objects.filter(
                    company=company,
                    is_active=True
                ).order_by('name')

                self.fields['warehouse'].queryset = Warehouse.objects.filter(
                    company=company,
                    is_active=True
                ).order_by('name')

                # جعل بعض الحقول اختيارية
                self.fields['item_variant'].required = False
                self.fields['manufacturing_date'].required = False
                self.fields['expiry_date'].required = False

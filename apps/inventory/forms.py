# apps/inventory/forms.py
"""
نماذج المخازن
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date

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

    def clean_date(self):
        """التحقق من تاريخ الإدخال - لا يمكن أن يكون تاريخ مستقبلي"""
        stock_date = self.cleaned_data.get('date')

        if stock_date and stock_date > date.today():
            raise ValidationError(
                _('لا يمكن إدخال مخزون بتاريخ مستقبلي. يرجى اختيار تاريخ اليوم أو تاريخ سابق.')
            )

        return stock_date


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

    def clean_quantity(self):
        """التحقق من الكمية - يجب أن تكون أكبر من صفر"""
        quantity = self.cleaned_data.get('quantity')

        if quantity is not None and quantity <= 0:
            raise ValidationError(
                _('الكمية يجب أن تكون أكبر من صفر')
            )

        return quantity

    def clean_unit_cost(self):
        """التحقق من التكلفة - لا يمكن أن تكون سالبة"""
        unit_cost = self.cleaned_data.get('unit_cost')

        if unit_cost is not None and unit_cost < 0:
            raise ValidationError(
                _('تكلفة الوحدة لا يمكن أن تكون سالبة')
            )

        return unit_cost


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

    def clean_date(self):
        """التحقق من تاريخ الإخراج - لا يمكن أن يكون تاريخ مستقبلي"""
        stock_date = self.cleaned_data.get('date')

        if stock_date and stock_date > date.today():
            raise ValidationError(
                _('لا يمكن إخراج مخزون بتاريخ مستقبلي. يرجى اختيار تاريخ اليوم أو تاريخ سابق.')
            )

        return stock_date


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

    def clean_date(self):
        """التحقق من تاريخ التحويل - لا يمكن أن يكون تاريخ مستقبلي"""
        transfer_date = self.cleaned_data.get('date')

        if transfer_date and transfer_date > date.today():
            raise ValidationError(
                _('لا يمكن تحويل المخزون بتاريخ مستقبلي. يرجى اختيار تاريخ اليوم أو تاريخ سابق.')
            )

        return transfer_date

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

    def clean_quantity(self):
        """التحقق من الكمية - يجب أن تكون أكبر من صفر"""
        quantity = self.cleaned_data.get('quantity')

        if quantity is not None and quantity <= 0:
            raise ValidationError(
                _('الكمية يجب أن تكون أكبر من صفر')
            )

        return quantity


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

    def clean_date(self):
        """التحقق من تاريخ الجرد - لا يمكن أن يكون تاريخ مستقبلي"""
        count_date = self.cleaned_data.get('date')

        if count_date:
            if count_date > date.today():
                raise ValidationError(
                    _('لا يمكن جرد المخزون بتاريخ مستقبلي. يرجى اختيار تاريخ اليوم أو تاريخ سابق.')
                )

        return count_date

    def clean(self):
        """التحقق الشامل من البيانات"""
        cleaned_data = super().clean()
        warehouse = cleaned_data.get('warehouse')

        if not warehouse:
            raise ValidationError({
                'warehouse': _('يجب تحديد المستودع لإجراء الجرد')
            })

        return cleaned_data


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
                'step': '0.001',
                'min': '0'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
            'adjustment_reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_counted_quantity(self):
        """التحقق من الكمية المجروزة - لا يمكن أن تكون سالبة"""
        quantity = self.cleaned_data.get('counted_quantity')

        if quantity is not None and quantity < 0:
            raise ValidationError(
                _('الكمية المجروزة لا يمكن أن تكون سالبة. يرجى إدخال كمية صحيحة (0 أو أكبر).')
            )

        return quantity

    def clean(self):
        """التحقق الشامل من سطر الجرد"""
        cleaned_data = super().clean()
        system_qty = cleaned_data.get('system_quantity')
        counted_qty = cleaned_data.get('counted_quantity')

        # التحقق من وجود فرق كبير يحتاج سبب توضيحي
        if system_qty is not None and counted_qty is not None:
            difference = abs(system_qty - counted_qty)
            adjustment_reason = cleaned_data.get('adjustment_reason')

            # إذا كان الفرق أكبر من 10% من الكمية النظامية
            if system_qty > 0 and (difference / system_qty) > 0.1:
                if not adjustment_reason:
                    self.add_error('adjustment_reason', ValidationError(
                        _('يوجد فرق كبير بين الكمية النظامية والمجروزة (أكثر من 10%). يرجى إدخال سبب التسوية.')
                    ))

        return cleaned_data


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

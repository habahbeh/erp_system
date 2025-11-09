# apps/purchases/forms/order_forms.py
"""
نماذج أوامر الشراء
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import PurchaseOrder, PurchaseOrderItem
from apps.core.models import (
    BusinessPartner, Item, ItemVariant, Warehouse,
    UnitOfMeasure, Currency, User
)


class PurchaseOrderForm(forms.ModelForm):
    """نموذج أمر الشراء"""

    class Meta:
        model = PurchaseOrder
        fields = [
            'date', 'supplier', 'warehouse', 'currency',
            'requested_by', 'expected_delivery_date',
            'purchase_request', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المورد...',
                'required': 'required'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المستودع...',
                'required': 'required'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'requested_by': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الموظف...',
            }),
            'expected_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'purchase_request': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'طلب الشراء (اختياري)...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات إضافية...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.branch = kwargs.pop('branch', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الموردين
            self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            ).select_related('supplier_account')

            # تصفية المخازن
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company,
                is_active=True
            )
            # Note: Warehouse doesn't have direct branch field, but has default_for_branches ManyToMany

            # تصفية العملات
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            )

            # تصفية الموظفين
            self.fields['requested_by'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

            # تصفية طلبات الشراء
            from ..models import PurchaseRequest
            self.fields['purchase_request'].queryset = PurchaseRequest.objects.filter(
                company=self.company,
                status='approved'
            )

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            
            if self.user:
                self.fields['requested_by'].initial = self.user

            if self.company:
                # العملة الافتراضية
                default_currency = Currency.objects.filter(
                    code='KWD', is_active=True
                ).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

        # جعل بعض الحقول اختيارية
        self.fields['purchase_request'].required = False
        self.fields['expected_delivery_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        order_date = cleaned_data.get('date')
        expected_delivery = cleaned_data.get('expected_delivery_date')

        # التحقق من التواريخ
        if expected_delivery and order_date:
            if expected_delivery < order_date:
                raise ValidationError({
                    'expected_delivery_date': _('تاريخ التسليم المتوقع يجب أن يكون بعد تاريخ الأمر')
                })

        return cleaned_data


class PurchaseOrderItemForm(forms.ModelForm):
    """نموذج سطر أمر الشراء"""

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'item', 'description', 'quantity', 'unit_price'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm item-select',
                'data-placeholder': 'اختر المادة...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'البيان...',
                'rows': 2
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end quantity-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0.001'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end price-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية المواد
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'unit_of_measure')

        # جعل بعض الحقول اختيارية
        self.fields['description'].required = False


class BasePurchaseOrderItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور أمر الشراء"""

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        """تمرير company لكل form"""
        kwargs['company'] = self.company
        return super()._construct_form(i, **kwargs)

    def clean(self):
        """التحقق من وجود سطر واحد على الأقل"""
        if any(self.errors):
            return

        # التحقق من وجود سطر واحد على الأقل
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_forms += 1

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل لأمر الشراء'))


# إنشاء Inline Formset لسطور أمر الشراء
PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    formset=BasePurchaseOrderItemFormSet,
    extra=5,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=1,
    validate_min=True,
)

# apps/sales/forms/order_forms.py
"""
نماذج طلبات البيع
"""

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.sales.models import SalesOrder, SalesOrderItem
from apps.core.models import BusinessPartner, User, Warehouse, Item


class SalesOrderForm(forms.ModelForm):
    """نموذج طلب البيع"""

    class Meta:
        model = SalesOrder
        fields = [
            'date',
            'customer',
            'warehouse',
            'salesperson',
            'quotation',
            'delivery_date',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'customer': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'required': True,
                }
            ),
            'warehouse': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'required': True,
                }
            ),
            'salesperson': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'required': True,
                }
            ),
            'quotation': forms.Select(
                attrs={
                    'class': 'form-control select2',
                }
            ),
            'delivery_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تصفية الاختيارات حسب الشركة
        if self.company:
            self.fields['customer'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['customer', 'both'],
                is_active=True
            )

            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company,
                is_active=True
            )

            self.fields['salesperson'].queryset = User.objects.filter(
                is_active=True
            )

            # فقط عروض الأسعار المعتمدة وغير المحولة
            self.fields['quotation'].queryset = SalesOrder.objects.none()
            self.fields['quotation'].required = False

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            if self.user:
                self.fields['salesperson'].initial = self.user

            # المستودع الافتراضي
            if self.company:
                default_warehouse = Warehouse.objects.filter(
                    company=self.company,
                    is_active=True
                ).first()
                if default_warehouse:
                    self.fields['warehouse'].initial = default_warehouse

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        delivery_date = cleaned_data.get('delivery_date')

        # التحقق من تاريخ التسليم
        if delivery_date and date:
            if delivery_date < date:
                raise ValidationError({
                    'delivery_date': _('تاريخ التسليم يجب أن يكون بعد تاريخ الطلب أو مساوياً له')
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.company:
            instance.company = self.company

        if self.user:
            instance.created_by = self.user

        if commit:
            instance.save()

        return instance


class SalesOrderItemForm(forms.ModelForm):
    """نموذج سطر طلب البيع"""

    class Meta:
        model = SalesOrderItem
        fields = [
            'item',
            'quantity',
            'unit_price',
        ]
        widgets = {
            'item': forms.Select(
                attrs={
                    'class': 'form-control select2 item-select',
                    'required': True,
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control quantity-input',
                    'step': '0.001',
                    'min': '0.001',
                    'required': True,
                }
            ),
            'unit_price': forms.NumberInput(
                attrs={
                    'class': 'form-control unit-price-input',
                    'step': '0.001',
                    'min': '0',
                    'required': True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تصفية المواد حسب الشركة
        if self.company:
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('الكمية يجب أن تكون أكبر من صفر'))
        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price and unit_price < 0:
            raise ValidationError(_('السعر لا يمكن أن يكون سالباً'))
        return unit_price


# إنشاء SalesOrderItemFormSet
SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    form=SalesOrderItemForm,
    extra=5,  # عدد النماذج الإضافية الفارغة
    can_delete=True,
    min_num=1,  # الحد الأدنى من السطور
    validate_min=True,
)

# apps/sales/forms/invoice_forms.py
"""
نماذج فواتير المبيعات
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import SalesInvoice, InvoiceItem, DiscountCampaign
from apps.core.models import (
    BusinessPartner, Item, ItemVariant, Warehouse,
    UnitOfMeasure, Currency, User, PaymentMethod
)


class SalesInvoiceForm(forms.ModelForm):
    """نموذج فاتورة المبيعات"""

    class Meta:
        model = SalesInvoice
        fields = [
            # معلومات أساسية
            'date', 'customer', 'salesperson', 'warehouse',
            'currency', 'payment_method', 'invoice_type',

            # معلومات المستلم
            'recipient_name', 'recipient_phone', 'recipient_address',

            # معلومات الشحن
            'delivery_date', 'shipping_cost',

            # معلومات الدفع
            'payment_status', 'due_date',

            # معلومات العمولة
            'salesperson_commission_rate',

            # خصم الفاتورة
            'discount_campaign', 'discount_type', 'discount_value',

            # ملاحظات
            'notes'
        ]

        widgets = {
            # معلومات أساسية
            'date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'customer': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر العميل...',
                'required': 'required',
                'id': 'id_customer'
            }),
            'salesperson': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المندوب...',
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المستودع...',
                'required': 'required'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select',
            }),

            # معلومات المستلم
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المستلم...',
            }),
            'recipient_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05xxxxxxxx',
            }),
            'recipient_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'عنوان التسليم...',
            }),

            # معلومات الشحن
            'delivery_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0',
                'id': 'id_shipping_cost'
            }),

            # معلومات الدفع
            'payment_status': forms.Select(attrs={
                'class': 'form-select',
                'disabled': 'disabled'  # يتم تحديثها تلقائياً
            }),
            'due_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),

            # معلومات العمولة
            'salesperson_commission_rate': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0',
                'max': '100',
                'id': 'id_commission_rate'
            }),

            # خصم الفاتورة
            'discount_campaign': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر حملة خصم (اختياري)...',
                'id': 'id_discount_campaign'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_discount_type'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0',
                'id': 'id_discount_value'
            }),

            # ملاحظات
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
            # تصفية العملاء
            self.fields['customer'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['customer', 'both'],
                is_active=True
            ).select_related('customer_account', 'default_salesperson')

            # تصفية المخازن
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية العملات
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            )

            # تصفية طرق الدفع
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية المندوبين (Users فقط)
            self.fields['salesperson'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

            # تصفية حملات الخصم النشطة فقط
            from django.utils import timezone
            today = timezone.now().date()
            self.fields['discount_campaign'].queryset = DiscountCampaign.objects.filter(
                company=self.company,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            ).order_by('-priority', 'name')

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            self.fields['payment_status'].initial = 'unpaid'
            self.fields['invoice_type'].initial = 'cash_sale'
            self.fields['discount_type'].initial = 'percentage'
            self.fields['discount_value'].initial = 0

            if self.user:
                self.fields['salesperson'].initial = self.user

            if self.company:
                # العملة الافتراضية
                default_currency = Currency.objects.filter(
                    code='JOD', is_active=True
                ).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

                # طريقة الدفع الافتراضية
                default_payment = PaymentMethod.objects.filter(
                    company=self.company,
                    code='CASH',
                    is_active=True
                ).first()
                if default_payment:
                    self.fields['payment_method'].initial = default_payment

        # جعل بعض الحقول اختيارية
        self.fields['recipient_name'].required = False
        self.fields['recipient_phone'].required = False
        self.fields['recipient_address'].required = False
        self.fields['delivery_date'].required = False
        self.fields['shipping_cost'].required = False
        self.fields['due_date'].required = False
        self.fields['salesperson_commission_rate'].required = False
        self.fields['discount_campaign'].required = False
        self.fields['discount_value'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()

        invoice_date = cleaned_data.get('date')
        delivery_date = cleaned_data.get('delivery_date')
        due_date = cleaned_data.get('due_date')
        customer = cleaned_data.get('customer')
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')

        # التحقق من التواريخ
        if delivery_date and invoice_date:
            if delivery_date < invoice_date:
                raise ValidationError({
                    'delivery_date': _('تاريخ التسليم يجب أن يكون بعد تاريخ الفاتورة')
                })

        if due_date and invoice_date:
            if due_date < invoice_date:
                raise ValidationError({
                    'due_date': _('تاريخ الاستحقاق يجب أن يكون بعد تاريخ الفاتورة')
                })

        # التحقق من الخصم
        if discount_type == 'percentage' and discount_value:
            if discount_value < 0 or discount_value > 100:
                raise ValidationError({
                    'discount_value': _('نسبة الخصم يجب أن تكون بين 0 و 100')
                })

        # التحقق من حد الائتمان للعميل (إذا كان الدفع آجل)
        if customer and not self.instance.pk:  # فقط للفواتير الجديدة
            invoice_type = cleaned_data.get('invoice_type')
            if invoice_type in ['credit_sale', 'installment']:
                # سنتحقق من حد الائتمان بعد حساب الإجمالي في الـ view
                # لأننا نحتاج إلى السطور لحساب الإجمالي
                pass

        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    """نموذج سطر فاتورة المبيعات"""

    class Meta:
        model = InvoiceItem
        fields = [
            'item', 'description', 'quantity', 'unit_price',
            'discount_percentage', 'tax_rate', 'tax_included'
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
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end discount-input',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0',
                'max': '100'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end tax-rate-input',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0'
            }),
            'tax_included': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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
        self.fields['discount_percentage'].required = False
        self.fields['tax_rate'].required = False

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['discount_percentage'].initial = 0
            self.fields['tax_rate'].initial = 16  # ضريبة افتراضية 16%
            self.fields['tax_included'].initial = False

    def clean_discount_percentage(self):
        """التحقق من نسبة الخصم"""
        discount = self.cleaned_data.get('discount_percentage')
        if discount and (discount < 0 or discount > 100):
            raise ValidationError(_('نسبة الخصم يجب أن تكون بين 0 و 100'))
        return discount

    def clean_quantity(self):
        """التحقق من الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('الكمية يجب أن تكون أكبر من صفر'))
        return quantity

    def clean_unit_price(self):
        """التحقق من السعر"""
        price = self.cleaned_data.get('unit_price')
        if price and price < 0:
            raise ValidationError(_('السعر يجب أن يكون صفر أو أكبر'))
        return price


class BaseInvoiceItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور فاتورة المبيعات"""

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
        items_set = set()

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_forms += 1

                # التحقق من عدم تكرار المادة
                item = form.cleaned_data.get('item')
                if item:
                    if item.id in items_set:
                        raise ValidationError(_('لا يمكن إضافة نفس المادة أكثر من مرة'))
                    items_set.add(item.id)

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل للفاتورة'))


# إنشاء Inline Formset لسطور الفاتورة
InvoiceItemFormSet = inlineformset_factory(
    SalesInvoice,
    InvoiceItem,
    form=InvoiceItemForm,
    formset=BaseInvoiceItemFormSet,
    extra=5,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=1,
    validate_min=True,
)

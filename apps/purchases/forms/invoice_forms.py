# apps/purchases/forms/invoice_forms.py
"""
نماذج فواتير المشتريات
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import PurchaseInvoice, PurchaseInvoiceItem
from apps.core.models import (
    BusinessPartner, Item, ItemVariant, Warehouse,
    UnitOfMeasure, PaymentMethod, Currency
)
from apps.accounting.models import Account


class PurchaseInvoiceForm(forms.ModelForm):
    """نموذج فاتورة المشتريات"""

    class Meta:
        model = PurchaseInvoice
        fields = [
            'invoice_type', 'date', 'branch', 'supplier', 'warehouse',
            'payment_method', 'currency',
            'supplier_invoice_number', 'supplier_invoice_date',
            'discount_type', 'discount_value', 'discount_affects_cost',
            'discount_account', 'supplier_account', 'reference', 'notes'
        ]
        widgets = {
            'invoice_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الفرع...',
                'required': 'required'
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
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
            }),
            'currency': forms.HiddenInput(),
            'supplier_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم فاتورة المورد',
            }),
            'supplier_invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
                'value': '0.000'
            }),
            'discount_affects_cost': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'discount_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'حساب الخصم (اختياري)...',
            }),
            'supplier_account': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'حساب المورد (اختياري)...',
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم سند الإدخال (سيتم إنشاؤه تلقائياً)',
                'readonly': 'readonly'
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
        super().__init__(*args, **kwargs)

        # تخصيص رسائل الخطأ للحقول المطلوبة
        self.fields['invoice_type'].error_messages = {
            'required': 'يرجى اختيار نوع الفاتورة',
            'invalid': 'نوع الفاتورة غير صحيح'
        }
        self.fields['date'].error_messages = {
            'required': 'يرجى إدخال تاريخ الفاتورة',
            'invalid': 'تاريخ الفاتورة غير صحيح'
        }
        self.fields['branch'].error_messages = {
            'required': 'يرجى اختيار الفرع',
            'invalid': 'الفرع غير صحيح'
        }
        self.fields['supplier'].error_messages = {
            'required': 'يرجى اختيار المورد',
            'invalid': 'المورد غير صحيح'
        }
        self.fields['warehouse'].error_messages = {
            'required': 'يرجى اختيار المستودع',
            'invalid': 'المستودع غير صحيح'
        }
        self.fields['payment_method'].error_messages = {
            'required': 'يرجى اختيار طريقة الدفع',
            'invalid': 'طريقة الدفع غير صحيحة'
        }
        self.fields['currency'].error_messages = {
            'required': 'يرجى اختيار العملة',
            'invalid': 'العملة غير صحيحة'
        }
        self.fields['discount_type'].error_messages = {
            'required': 'يرجى اختيار نوع الخصم',
            'invalid': 'نوع الخصم غير صحيح'
        }
        self.fields['discount_value'].error_messages = {
            'required': 'يرجى إدخال قيمة الخصم',
            'invalid': 'قيمة الخصم غير صحيحة'
        }

        if self.company:
            # تصفية الفروع
            from apps.core.models import Branch
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )

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

            # تصفية طرق الدفع - فقط نقدي وآجل
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
                company=self.company,
                is_active=True,
                code__in=['CASH', 'CREDIT']
            )

            # تصفية العملات
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            )

            # تصفية الحسابات
            self.fields['discount_account'].queryset = Account.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('parent', 'account_type')

            # تصفية حسابات الموردين (الخصوم)
            # Note: AccountType has only 'name' field, not 'name_en'
            from apps.accounting.models import AccountType
            liability_types = AccountType.objects.filter(
                name__icontains='خصوم'
            )

            if liability_types.exists():
                self.fields['supplier_account'].queryset = Account.objects.filter(
                    company=self.company,
                    is_active=True,
                    account_type__in=liability_types
                ).select_related('parent', 'account_type')
            else:
                # Fallback: show all accounts if no liability types found
                self.fields['supplier_account'].queryset = Account.objects.filter(
                    company=self.company,
                    is_active=True
                ).select_related('parent', 'account_type')

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            self.fields['invoice_type'].initial = 'purchase'

            # تعيين الفرع الافتراضي
            if self.branch:
                self.fields['branch'].initial = self.branch

            if self.company:
                # العملة الافتراضية JOD
                default_currency = Currency.objects.filter(
                    code='JOD', is_active=True
                ).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

                # طريقة الدفع الافتراضية - نقدي
                default_payment = PaymentMethod.objects.filter(
                    company=self.company,
                    is_active=True,
                    code='CASH'
                ).first()
                if default_payment:
                    self.fields['payment_method'].initial = default_payment

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class PurchaseInvoiceItemForm(forms.ModelForm):
    """نموذج سطر فاتورة المشتريات - للاستخدام في Inline Formset"""

    class Meta:
        model = PurchaseInvoiceItem
        fields = [
            'item', 'item_variant', 'description', 'quantity', 'unit',
            'unit_price', 'discount_percentage', 'discount_amount',
            'tax_included', 'tax_rate', 'batch_number', 'expiry_date',
            'expense_account'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm item-select',
                'data-placeholder': 'اختر المادة...',
            }),
            'item_variant': forms.Select(attrs={
                'class': 'form-select form-select-sm variant-select',
                'data-placeholder': 'اختر المتغير...',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'البيان...',
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end quantity-input',
                'placeholder': '0.000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select form-select-sm',
            }),
            'unit_price': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end price-input',
                'placeholder': '0.000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'discount_percentage': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end discount-pct-input',
                'placeholder': '0.00',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'discount_amount': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end discount-amount-input',
                'placeholder': '0.000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'tax_included': forms.CheckboxInput(attrs={
                'class': 'form-check-input tax-included-check',
            }),
            'tax_rate': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end tax-rate-input',
                'placeholder': '16.00',
                'value': '16.00',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'رقم الدفعة',
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
            'expense_account': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'data-placeholder': 'حساب المشتريات...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Make fields optional (not required) to avoid RelatedObjectDoesNotExist error
        self.fields['item'].required = False
        self.fields['item_variant'].required = False
        self.fields['unit'].required = False
        self.fields['expense_account'].required = False

        # Set empty querysets by default to avoid errors
        self.fields['item'].queryset = Item.objects.none()
        self.fields['item_variant'].queryset = ItemVariant.objects.none()
        self.fields['unit'].queryset = UnitOfMeasure.objects.none()
        self.fields['expense_account'].queryset = Account.objects.none()

        if self.company:
            # تصفية المواد
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'base_uom')

            # تصفية المتغيرات
            self.fields['item_variant'].queryset = ItemVariant.objects.filter(
                item__company=self.company,
                is_active=True
            ).select_related('item')

            # تصفية الوحدات
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية حسابات المصروفات
            # Note: AccountType is a ForeignKey, need to filter by AccountType objects
            from apps.accounting.models import AccountType
            expense_types = AccountType.objects.filter(
                name__icontains='مصروف'
            ) | AccountType.objects.filter(
                name__icontains='تكلفة'
            ) | AccountType.objects.filter(
                name__icontains='مخزون'
            )

            if expense_types.exists():
                self.fields['expense_account'].queryset = Account.objects.filter(
                    company=self.company,
                    is_active=True,
                    account_type__in=expense_types
                ).select_related('parent', 'account_type')
            else:
                # Fallback: show all accounts if no expense types found
                self.fields['expense_account'].queryset = Account.objects.filter(
                    company=self.company,
                    is_active=True
                ).select_related('parent', 'account_type')

        # جعل بعض الحقول اختيارية
        self.fields['item_variant'].required = False
        self.fields['description'].required = False
        self.fields['batch_number'].required = False
        self.fields['expiry_date'].required = False
        self.fields['expense_account'].required = False

    def clean(self):
        """تنظيف البيانات قبل الحفظ"""
        cleaned_data = super().clean()

        # تنظيف item_variant - إذا كان فارغاً اجعله None
        item_variant = cleaned_data.get('item_variant')
        if item_variant == '' or item_variant is None:
            cleaned_data['item_variant'] = None

        # تنظيف expense_account - إذا كان فارغاً اجعله None
        expense_account = cleaned_data.get('expense_account')
        if expense_account == '' or expense_account is None:
            cleaned_data['expense_account'] = None

        return cleaned_data


class BasePurchaseInvoiceItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور الفاتورة مع تحقق إضافي"""

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
                # التحقق من أن السطر يحتوي على مادة
                if form.cleaned_data.get('item'):
                    valid_forms += 1

        if valid_forms < 1:
            raise ValidationError('⚠️ يرجى إضافة سطر واحد على الأقل للفاتورة. لا يمكن حفظ فاتورة فارغة.')


# إنشاء Inline Formset لسطور الفاتورة
PurchaseInvoiceItemFormSet = inlineformset_factory(
    PurchaseInvoice,
    PurchaseInvoiceItem,
    form=PurchaseInvoiceItemForm,
    formset=BasePurchaseInvoiceItemFormSet,
    extra=5,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=1,
    validate_min=True,
)

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
            'supplier_invoice_number',  # ✅ الملاحظة 3: نُقل للبداية
            'invoice_type', 'date', 'branch', 'supplier', 'warehouse',
            'payment_method', 'currency',
            'supplier_invoice_date',
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
                'required': 'required'  # ✅ الملاحظة 3: إجباري
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
            'invalid': 'نوع الفاتورة غير صحيح',
            'invalid_choice': 'الاختيار غير صحيح لنوع الفاتورة'
        }
        self.fields['date'].error_messages = {
            'required': 'يرجى إدخال تاريخ الفاتورة',
            'invalid': 'تاريخ الفاتورة غير صحيح'
        }
        self.fields['branch'].error_messages = {
            'required': 'يرجى اختيار الفرع',
            'invalid': 'الفرع غير صحيح',
            'invalid_choice': 'الاختيار غير صحيح للفرع'
        }
        self.fields['supplier'].error_messages = {
            'required': 'يرجى اختيار المورد',
            'invalid': 'المورد غير صحيح',
            'invalid_choice': 'الاختيار غير صحيح للمورد'
        }
        self.fields['warehouse'].error_messages = {
            'required': 'يرجى اختيار المستودع',
            'invalid': 'المستودع غير صحيح',
            'invalid_choice': 'الاختيار غير صحيح للمستودع'
        }
        self.fields['payment_method'].error_messages = {
            'required': 'يرجى اختيار طريقة الدفع',
            'invalid': 'طريقة الدفع غير صحيحة',
            'invalid_choice': 'الاختيار غير صحيح لطريقة الدفع'
        }
        self.fields['currency'].error_messages = {
            'required': 'يرجى اختيار العملة',
            'invalid': 'العملة غير صحيحة',
            'invalid_choice': 'الاختيار غير صحيح للعملة'
        }
        self.fields['discount_type'].error_messages = {
            'required': 'يرجى اختيار نوع الخصم',
            'invalid': 'نوع الخصم غير صحيح',
            'invalid_choice': 'الاختيار غير صحيح لنوع الخصم'
        }
        self.fields['discount_value'].error_messages = {
            'required': 'يرجى إدخال قيمة الخصم',
            'invalid': 'قيمة الخصم غير صحيحة'
        }

        # جعل بعض الحقول اختيارية مع قيم افتراضية
        self.fields['discount_type'].required = False
        self.fields['discount_value'].required = False
        self.fields['discount_account'].required = False
        self.fields['supplier_account'].required = False

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
            'unit_price', 'purchase_uom', 'purchase_quantity', 'purchase_unit_price',
            'conversion_rate', 'discount_percentage', 'discount_amount',
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
            'purchase_uom': forms.Select(attrs={
                'class': 'form-select form-select-sm purchase-uom-select',
                'data-placeholder': 'وحدة الشراء...',
            }),
            'purchase_quantity': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end purchase-qty-input',
                'placeholder': '0.000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'purchase_unit_price': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end purchase-price-input',
                'placeholder': '0.000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*'
            }),
            'conversion_rate': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-end conversion-rate-input',
                'placeholder': '1.000000',
                'inputmode': 'decimal',
                'pattern': '[0-9٠-٩.,]*',
                'readonly': 'readonly'
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
        self.fields['unit_price'].required = False
        self.fields['quantity'].required = False
        self.fields['expense_account'].required = False

        # ✅ PERFORMANCE FIX: Set empty querysets by default
        # Items and variants will be loaded via AJAX search
        # This prevents loading 5000+ variants on page load
        self.fields['item'].queryset = Item.objects.none()
        self.fields['item_variant'].queryset = ItemVariant.objects.none()
        self.fields['unit'].queryset = UnitOfMeasure.objects.none()
        self.fields['expense_account'].queryset = Account.objects.none()

        # ✅ For existing records (edit mode) OR POST data, include values in queryset
        # This ensures form validation works for selected items
        item_id = None
        variant_id = None

        # Check POST data first (for form submission)
        if self.data:
            # Get the field name prefix for this form in formset
            prefix = self.prefix
            if prefix:
                item_id = self.data.get(f'{prefix}-item')
                variant_id = self.data.get(f'{prefix}-item_variant')
            else:
                item_id = self.data.get('item')
                variant_id = self.data.get('item_variant')

        # Fallback to instance values (for edit mode)
        if not item_id and self.instance and self.instance.pk:
            item_id = self.instance.item_id
            variant_id = self.instance.item_variant_id

        # Update querysets to include the selected values
        if item_id:
            self.fields['item'].queryset = Item.objects.filter(pk=item_id)
        if variant_id:
            self.fields['item_variant'].queryset = ItemVariant.objects.filter(pk=variant_id)

        if self.company:
            # ✅ Items: Keep empty - loaded via AJAX search (item_search_ajax)
            # self.fields['item'].queryset = Item.objects.none()

            # ✅ Variants: Keep empty - loaded via AJAX when item is selected
            # self.fields['item_variant'].queryset = ItemVariant.objects.none()

            # تصفية الوحدات - هذه خفيفة (عادة < 50 وحدة)
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية حسابات المصروفات - خفيفة نسبياً
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

        item = cleaned_data.get('item')
        unit_price = cleaned_data.get('unit_price')
        quantity = cleaned_data.get('quantity')
        unit = cleaned_data.get('unit')

        # إذا تم اختيار مادة، تأكد من وجود السعر والكمية والوحدة
        if item:
            if not unit_price:
                raise ValidationError({'unit_price': 'السعر مطلوب عند اختيار المادة'})
            if not quantity:
                raise ValidationError({'quantity': 'الكمية مطلوبة عند اختيار المادة'})
            if not unit:
                raise ValidationError({'unit': 'الوحدة مطلوبة عند اختيار المادة'})

        # تنظيف item_variant - إذا كان فارغاً اجعله None
        item_variant = cleaned_data.get('item_variant')
        if item_variant == '' or item_variant is None:
            cleaned_data['item_variant'] = None

        # تنظيف expense_account - إذا كان فارغاً اجعله None
        expense_account = cleaned_data.get('expense_account')
        if expense_account == '' or expense_account is None:
            cleaned_data['expense_account'] = None

        return cleaned_data

    def save(self, commit=True):
        """حفظ البيانات - تخطي الحفظ إذا لم يتم اختيار مادة"""
        # إذا لم يتم اختيار مادة، لا تحفظ هذا السطر (سطر فارغ)
        if not self.cleaned_data.get('item') and not self.instance.pk:
            # هذا سطر جديد فارغ، لا نحفظه
            return None

        return super().save(commit=commit)


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

    def save(self, commit=True):
        """حفظ السطور - تخطي السطور الفارغة (بدون مادة)"""
        # إنشاء قائمة بالسطور الصحيحة فقط
        forms_to_save = []

        for form in self.forms:
            # تخطي إذا لم يكن هناك cleaned_data
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue

            # تخطي السطور المحذوفة
            if form.cleaned_data.get('DELETE', False):
                continue

            # تخطي السطور الفارغة (بدون مادة)
            if not form.cleaned_data.get('item'):
                continue

            forms_to_save.append(form)

        # استبدال قائمة النماذج بالنماذج الصحيحة فقط
        self.forms = forms_to_save

        # استدعاء save الأصلي
        return super().save(commit=commit)


# إنشاء Inline Formset لسطور الفاتورة
PurchaseInvoiceItemFormSet = inlineformset_factory(
    PurchaseInvoice,
    PurchaseInvoiceItem,
    form=PurchaseInvoiceItemForm,
    formset=BasePurchaseInvoiceItemFormSet,
    extra=5,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=0,  # لا نطلب حد أدنى هنا - سنتحقق في clean()
    validate_min=False,  # التحقق المخصص في BasePurchaseInvoiceItemFormSet.clean()
)

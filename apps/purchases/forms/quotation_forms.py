# apps/purchases/forms/quotation_forms.py
"""
نماذج عروض الأسعار
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from ..models import (
    PurchaseQuotationRequest, PurchaseQuotationRequestItem,
    PurchaseQuotation, PurchaseQuotationItem,
    PurchaseRequest
)
from apps.core.models import Item, BusinessPartner, Currency, User


class PurchaseQuotationRequestForm(forms.ModelForm):
    """نموذج طلب عرض أسعار"""

    # حقل لاختيار الموردين
    suppliers = forms.ModelMultipleChoiceField(
        queryset=BusinessPartner.objects.none(),
        required=True,
        label=_('الموردين'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'multiple': 'multiple',
            'data-placeholder': 'اختر الموردين...',
        }),
        help_text=_('اختر الموردين الذين سيتم إرسال طلب العرض لهم')
    )

    class Meta:
        model = PurchaseQuotationRequest
        fields = [
            'date', 'subject', 'description', 'purchase_request',
            'submission_deadline', 'required_delivery_date',
            'currency',
            'payment_terms', 'delivery_terms',
            'warranty_required', 'warranty_period_months',
            'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الموضوع...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف تفصيلي للأصناف المطلوبة...',
            }),
            'purchase_request': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختر طلب شراء معتمد (اختياري)...',
            }),
            'submission_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'required_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'مثال: دفعة مقدمة 30%، الباقي عند التسليم',
            }),
            'delivery_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'مثال: التسليم في المستودع الرئيسي',
            }),
            'warranty_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'warranty_period_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية طلبات الشراء المعتمدة مع عرض معلومات إضافية
            self.fields['purchase_request'].queryset = PurchaseRequest.objects.filter(
                company=self.company,
                status='approved'
            ).select_related('requested_by', 'department').order_by('-date')

            # تخصيص label_from_instance لعرض معلومات أكثر
            self.fields['purchase_request'].label_from_instance = lambda obj: (
                f"{obj.number} - {obj.date.strftime('%Y-%m-%d')} - "
                f"{obj.requested_by.get_full_name() if obj.requested_by else 'غير محدد'}"
            )

            # تصفية الموردين
            self.fields['suppliers'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            ).order_by('name')

            # تصفية العملات
            from apps.core.models import Currency
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            ).order_by('name')

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            self.fields['submission_deadline'].initial = date.today() + timedelta(days=7)
            self.fields['required_delivery_date'].initial = date.today() + timedelta(days=30)

            # تعيين العملة الافتراضية
            if self.company:
                from apps.core.models import Currency
                default_currency = Currency.objects.filter(
                    is_base=True,
                    is_active=True
                ).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

        # جعل الحقول اختيارية
        self.fields['description'].required = False
        self.fields['purchase_request'].required = False
        self.fields['required_delivery_date'].required = False
        # currency مطلوب في قاعدة البيانات
        self.fields['currency'].required = True
        self.fields['payment_terms'].required = False
        self.fields['delivery_terms'].required = False
        self.fields['warranty_period_months'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()

        request_date = cleaned_data.get('date')
        submission_deadline = cleaned_data.get('submission_deadline')
        required_delivery_date = cleaned_data.get('required_delivery_date')
        warranty_required = cleaned_data.get('warranty_required')
        warranty_period = cleaned_data.get('warranty_period_months')
        currency = cleaned_data.get('currency')

        # التحقق من العملة
        if not currency:
            # محاولة تعيين العملة الافتراضية
            if self.company:
                from apps.core.models import Currency
                default_currency = Currency.objects.filter(
                    is_base=True,
                    is_active=True
                ).first()
                if default_currency:
                    cleaned_data['currency'] = default_currency
                else:
                    raise ValidationError({
                        'currency': _('يجب تحديد العملة')
                    })
            else:
                raise ValidationError({
                    'currency': _('يجب تحديد العملة')
                })

        # التحقق من التواريخ
        if submission_deadline and request_date:
            if submission_deadline < request_date:
                raise ValidationError({
                    'submission_deadline': _('آخر موعد لتقديم العروض يجب أن يكون بعد تاريخ الطلب')
                })

        if required_delivery_date and submission_deadline:
            if required_delivery_date < submission_deadline:
                raise ValidationError({
                    'required_delivery_date': _('تاريخ التسليم المطلوب يجب أن يكون بعد آخر موعد لتقديم العروض')
                })

        # التحقق من الضمان
        if warranty_required and not warranty_period:
            raise ValidationError({
                'warranty_period_months': _('يجب تحديد مدة الضمان')
            })

        return cleaned_data


class PurchaseQuotationRequestItemForm(forms.ModelForm):
    """نموذج سطر طلب عرض الأسعار"""

    class Meta:
        model = PurchaseQuotationRequestItem
        fields = [
            'item', 'item_description', 'specifications',
            'quantity', 'unit', 'estimated_price', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm item-select',
                'data-placeholder': 'اختر المادة (اختياري)...',
            }),
            'item_description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'وصف المادة المطلوبة...',
                'rows': 2
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'المواصفات الفنية التفصيلية...',
                'rows': 2
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0.001'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'الوحدة...',
            }),
            'estimated_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 1,
                'placeholder': 'ملاحظات...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'unit_of_measure')

        # جعل الحقول اختيارية
        self.fields['item'].required = False
        self.fields['specifications'].required = False
        self.fields['unit'].required = False
        self.fields['estimated_price'].required = False
        self.fields['notes'].required = False

    def clean(self):
        """تعبئة الوحدة تلقائياً من المادة إذا كانت فارغة"""
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        unit = cleaned_data.get('unit')

        # إذا كانت المادة موجودة والوحدة فارغة، املأ الوحدة تلقائياً
        if item and not unit:
            if item.unit_of_measure:
                cleaned_data['unit'] = item.unit_of_measure.name

        return cleaned_data


class BasePurchaseQuotationRequestItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور طلب عرض الأسعار"""

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['company'] = self.company
        return super()._construct_form(i, **kwargs)

    def clean(self):
        if any(self.errors):
            return

        # التحقق من وجود سطر واحد على الأقل
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('item_description'):
                    valid_forms += 1

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة صنف واحد على الأقل'))


# إنشاء Inline Formset لسطور طلب عرض الأسعار
PurchaseQuotationRequestItemFormSet = inlineformset_factory(
    PurchaseQuotationRequest,
    PurchaseQuotationRequestItem,
    form=PurchaseQuotationRequestItemForm,
    formset=BasePurchaseQuotationRequestItemFormSet,
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class PurchaseQuotationForm(forms.ModelForm):
    """نموذج عرض السعر"""

    class Meta:
        model = PurchaseQuotation
        fields = [
            'quotation_request', 'supplier', 'date', 'valid_until',
            'supplier_quotation_number', 'currency',
            'payment_terms', 'delivery_terms',
            'delivery_period_days', 'warranty_period_months',
            'discount_amount', 'score',
            'evaluation_notes', 'notes', 'attachment'
        ]
        widgets = {
            'quotation_request': forms.Select(attrs={
                'class': 'form-select select2',
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-select select2',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'supplier_quotation_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم عرض المورد...',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'شروط الدفع...',
            }),
            'delivery_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'شروط التسليم...',
            }),
            'delivery_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'warranty_period_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'evaluation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات التقييم...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية...',
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية طلبات العروض
            self.fields['quotation_request'].queryset = PurchaseQuotationRequest.objects.filter(
                company=self.company
            ).order_by('-date')

            # تصفية الموردين
            self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            ).order_by('name')

            # تصفية العملات
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            )

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            self.fields['valid_until'].initial = date.today() + timedelta(days=30)

            if self.company:
                default_currency = Currency.objects.filter(is_base=True).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

        # جعل الحقول اختيارية
        self.fields['supplier_quotation_number'].required = False
        self.fields['payment_terms'].required = False
        self.fields['delivery_terms'].required = False
        self.fields['delivery_period_days'].required = False
        self.fields['warranty_period_months'].required = False
        self.fields['score'].required = False
        self.fields['evaluation_notes'].required = False
        self.fields['notes'].required = False
        self.fields['attachment'].required = False


class PurchaseQuotationItemForm(forms.ModelForm):
    """نموذج سطر عرض السعر"""

    class Meta:
        model = PurchaseQuotationItem
        fields = [
            'rfq_item', 'item', 'description', 'quantity', 'unit',
            'unit_price', 'discount_percentage', 'tax_rate',
            'brand', 'country_of_origin', 'notes'
        ]
        widgets = {
            'rfq_item': forms.HiddenInput(),
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm item-select',
                'data-placeholder': 'اختر المادة (اختياري)...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'الوصف...',
                'rows': 2
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end quantity-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0.001'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'الوحدة...',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end price-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end discount-pct-input',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0',
                'max': '100'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end tax-rate-input',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0',
                'max': '100'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'العلامة التجارية...',
            }),
            'country_of_origin': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'بلد المنشأ...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 1,
                'placeholder': 'ملاحظات...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'unit_of_measure')

        # جعل الحقول اختيارية
        self.fields['rfq_item'].required = False
        self.fields['item'].required = False
        self.fields['description'].required = False
        self.fields['unit'].required = False
        self.fields['brand'].required = False
        self.fields['country_of_origin'].required = False
        self.fields['notes'].required = False


class BasePurchaseQuotationItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور عرض السعر"""

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['company'] = self.company
        return super()._construct_form(i, **kwargs)

    def clean(self):
        if any(self.errors):
            return

        # التحقق من وجود سطر واحد على الأقل
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('quantity'):
                    valid_forms += 1

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل'))


# إنشاء Inline Formset لسطور عرض السعر
PurchaseQuotationItemFormSet = inlineformset_factory(
    PurchaseQuotation,
    PurchaseQuotationItem,
    form=PurchaseQuotationItemForm,
    formset=BasePurchaseQuotationItemFormSet,
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

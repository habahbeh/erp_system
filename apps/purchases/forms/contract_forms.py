# apps/purchases/forms/contract_forms.py
"""
نماذج عقود الشراء طويلة الأجل
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import PurchaseContract, PurchaseContractItem
from apps.core.models import (
    BusinessPartner, Item, ItemVariant, Warehouse,
    UnitOfMeasure, Currency, User
)


class PurchaseContractForm(forms.ModelForm):
    """نموذج عقد الشراء"""

    class Meta:
        model = PurchaseContract
        fields = [
            'supplier', 'contract_date', 'start_date', 'end_date',
            'currency', 'payment_terms', 'delivery_terms',
            'quality_standards', 'penalty_terms', 'termination_terms',
            'renewal_terms', 'attachment', 'notes'
        ]
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المورد...',
                'required': 'required'
            }),
            'contract_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'شروط الدفع (مثال: دفعة مقدمة 30%، الباقي عند التسليم)...',
            }),
            'delivery_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'شروط التسليم (مثال: التسليم في المستودع الرئيسي)...',
            }),
            'quality_standards': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'معايير الجودة والمواصفات المطلوبة...',
            }),
            'penalty_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'غرامات التأخير أو عدم الالتزام...',
            }),
            'termination_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'شروط وإجراءات إنهاء العقد...',
            }),
            'renewal_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'شروط التجديد (اختياري)...',
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
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

            # تصفية العملات
            self.fields['currency'].queryset = Currency.objects.filter(
                is_active=True
            )

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['contract_date'].initial = date.today()
            self.fields['start_date'].initial = date.today()

            if self.company:
                # العملة الافتراضية
                default_currency = Currency.objects.filter(
                    code='KWD', is_active=True
                ).first()
                if default_currency:
                    self.fields['currency'].initial = default_currency

        # جعل بعض الحقول اختيارية
        self.fields['payment_terms'].required = False
        self.fields['delivery_terms'].required = False
        self.fields['quality_standards'].required = False
        self.fields['penalty_terms'].required = False
        self.fields['termination_terms'].required = False
        self.fields['renewal_terms'].required = False
        self.fields['attachment'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()

        contract_date = cleaned_data.get('contract_date')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # التحقق من التواريخ
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': _('تاريخ الانتهاء يجب أن يكون بعد تاريخ البدء')
                })

        if contract_date and start_date:
            if start_date < contract_date:
                raise ValidationError({
                    'start_date': _('تاريخ البدء لا يمكن أن يكون قبل تاريخ العقد')
                })

        return cleaned_data


class PurchaseContractItemForm(forms.ModelForm):
    """نموذج سطر عقد الشراء - للاستخدام في Inline Formset"""

    class Meta:
        model = PurchaseContractItem
        fields = [
            'item', 'item_description', 'specifications', 'unit',
            'contracted_quantity', 'unit_price', 'discount_percentage',
            'min_order_quantity', 'max_order_quantity', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm item-select',
                'data-placeholder': 'اختر المادة (اختياري)...',
            }),
            'item_description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'وصف الصنف...',
                'required': 'required'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'المواصفات التفصيلية...',
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select form-select-sm',
            }),
            'contracted_quantity': forms.NumberInput(attrs={
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
            'min_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
            'max_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'ملاحظات...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Make fields optional (not required) to avoid RelatedObjectDoesNotExist error
        self.fields['item'].required = False
        self.fields['unit'].required = False
        self.fields['specifications'].required = False
        self.fields['min_order_quantity'].required = False
        self.fields['max_order_quantity'].required = False
        self.fields['notes'].required = False

        # Set empty querysets by default to avoid errors
        self.fields['item'].queryset = Item.objects.none()
        self.fields['unit'].queryset = UnitOfMeasure.objects.none()

        if self.company:
            # تصفية المواد
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'base_uom')

            # تصفية الوحدات
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True
            )

    def clean(self):
        """تنظيف البيانات قبل الحفظ"""
        cleaned_data = super().clean()

        contracted_quantity = cleaned_data.get('contracted_quantity')
        min_order = cleaned_data.get('min_order_quantity')
        max_order = cleaned_data.get('max_order_quantity')

        # التحقق من حدود الطلب
        if min_order and max_order:
            if min_order > max_order:
                raise ValidationError({
                    'min_order_quantity': _('الحد الأدنى لا يمكن أن يكون أكبر من الحد الأقصى')
                })

        if min_order and contracted_quantity:
            if min_order > contracted_quantity:
                raise ValidationError({
                    'min_order_quantity': _('الحد الأدنى لا يمكن أن يكون أكبر من الكمية المتعاقد عليها')
                })

        return cleaned_data


class BasePurchaseContractItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور العقد مع تحقق إضافي"""

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
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل للعقد'))


# إنشاء Inline Formset لسطور العقد
PurchaseContractItemFormSet = inlineformset_factory(
    PurchaseContract,
    PurchaseContractItem,
    form=PurchaseContractItemForm,
    formset=BasePurchaseContractItemFormSet,
    extra=3,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# نموذج الموافقة على العقد
class ContractApprovalForm(forms.Form):
    """نموذج الموافقة على العقد"""

    action = forms.ChoiceField(
        label=_('الإجراء'),
        choices=[
            ('approve', _('اعتماد العقد')),
            ('reject', _('رفض العقد')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات على الاعتماد أو سبب الرفض...'
        })
    )


# نموذج تغيير حالة العقد
class ContractStatusChangeForm(forms.Form):
    """نموذج تغيير حالة العقد"""

    STATUS_CHOICES = [
        ('activate', _('تفعيل العقد')),
        ('suspend', _('تعليق العقد')),
        ('terminate', _('إنهاء العقد')),
    ]

    action = forms.ChoiceField(
        label=_('الإجراء'),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    reason = forms.CharField(
        label=_('السبب'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'سبب التغيير...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        reason = cleaned_data.get('reason')

        # التعليق والإنهاء يتطلبان سبباً
        if action in ['suspend', 'terminate'] and not reason:
            raise ValidationError({
                'reason': _('يجب تحديد سبب التعليق أو الإنهاء')
            })

        return cleaned_data

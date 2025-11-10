# apps/purchases/forms/goods_receipt_forms.py
"""
نماذج استلام البضاعة (Goods Receipt)
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from datetime import date

from ..models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderItem
from apps.core.models import (
    BusinessPartner, Item, ItemVariant, Warehouse, User
)


class GoodsReceiptForm(forms.ModelForm):
    """نموذج محضر استلام البضاعة"""

    class Meta:
        model = GoodsReceipt
        fields = [
            'date', 'branch', 'purchase_order', 'supplier', 'warehouse',
            'delivery_note_number', 'delivery_date', 'received_by',
            'quality_check_status', 'quality_notes', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الفرع...',
                'required': 'required'
            }),
            'purchase_order': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر أمر الشراء...',
                'required': 'required',
                'id': 'id_purchase_order'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'المورد...',
                'required': 'required',
                'readonly': 'readonly'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر المستودع...',
                'required': 'required'
            }),
            'delivery_note_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم إيصال التسليم من المورد...',
            }),
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'received_by': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الموظف المستلم...',
                'required': 'required'
            }),
            'quality_check_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'quality_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات الفحص والجودة...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات عامة...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.branch = kwargs.pop('branch', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الفروع
            from apps.core.models import Branch
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية أوامر الشراء (المعتمدة أو المرسلة للمورد فقط)
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                company=self.company,
                status__in=['approved', 'sent_to_supplier', 'partially_received'],
                is_active=True
            ).select_related('supplier', 'warehouse')

            # تصفية الموردين
            self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            )

            # تصفية المخازن
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company,
                is_active=True
            )

            # تصفية الموظفين
            self.fields['received_by'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
            self.fields['delivery_date'].initial = date.today()

            # تعيين الفرع الافتراضي
            if self.branch:
                self.fields['branch'].initial = self.branch

            if self.user:
                self.fields['received_by'].initial = self.user

        # جعل بعض الحقول اختيارية
        self.fields['delivery_note_number'].required = False
        self.fields['delivery_date'].required = False
        self.fields['quality_notes'].required = False
        self.fields['notes'].required = False

        # إذا كان لدينا أمر شراء محدد، نملأ البيانات منه
        if self.instance.pk and self.instance.purchase_order:
            self.fields['supplier'].initial = self.instance.purchase_order.supplier
            self.fields['warehouse'].initial = self.instance.purchase_order.warehouse
            # جعل المورد والمستودع للقراءة فقط
            self.fields['supplier'].disabled = True
            self.fields['warehouse'].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        receipt_date = cleaned_data.get('date')
        delivery_date = cleaned_data.get('delivery_date')
        purchase_order = cleaned_data.get('purchase_order')

        # التحقق من التواريخ
        if delivery_date and receipt_date:
            if delivery_date > receipt_date:
                raise ValidationError({
                    'delivery_date': _('تاريخ التسليم لا يمكن أن يكون بعد تاريخ الاستلام')
                })

        # التحقق من أمر الشراء
        if purchase_order:
            if purchase_order.status not in ['approved', 'sent_to_supplier', 'partially_received']:
                raise ValidationError({
                    'purchase_order': _('أمر الشراء يجب أن يكون معتمداً أو مرسلاً للمورد')
                })

            # تعيين المورد والمستودع من أمر الشراء
            cleaned_data['supplier'] = purchase_order.supplier
            cleaned_data['warehouse'] = purchase_order.warehouse

        return cleaned_data


class GoodsReceiptLineForm(forms.ModelForm):
    """نموذج سطر محضر الاستلام"""

    class Meta:
        model = GoodsReceiptLine
        fields = [
            'purchase_order_line', 'item', 'received_quantity',
            'rejected_quantity', 'batch_number', 'expiry_date',
            'quality_status', 'quality_notes', 'notes'
        ]
        widgets = {
            'purchase_order_line': forms.HiddenInput(),
            'item': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'received_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end received-qty-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0.001'
            }),
            'rejected_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end rejected-qty-input',
                'step': '0.001',
                'placeholder': '0.000',
                'min': '0'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'رقم الدفعة...',
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
            'quality_status': forms.Select(attrs={
                'class': 'form-select form-select-sm',
            }),
            'quality_notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ملاحظات الجودة...',
                'rows': 2
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ملاحظات...',
                'rows': 2
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

            # تصفية سطور أمر الشراء
            self.fields['purchase_order_line'].queryset = PurchaseOrderItem.objects.filter(
                order__company=self.company
            )

        # جعل بعض الحقول اختيارية
        self.fields['rejected_quantity'].required = False
        self.fields['batch_number'].required = False
        self.fields['expiry_date'].required = False
        self.fields['quality_notes'].required = False
        self.fields['notes'].required = False

        # القيم الافتراضية
        if not self.instance.pk:
            self.fields['rejected_quantity'].initial = 0

    def clean(self):
        cleaned_data = super().clean()

        received_qty = cleaned_data.get('received_quantity', Decimal('0'))
        rejected_qty = cleaned_data.get('rejected_quantity', Decimal('0'))
        po_line = cleaned_data.get('purchase_order_line')

        # التحقق من الكميات
        if received_qty <= 0:
            raise ValidationError({
                'received_quantity': _('الكمية المستلمة يجب أن تكون أكبر من صفر')
            })

        if rejected_qty < 0:
            raise ValidationError({
                'rejected_quantity': _('الكمية المرفوضة لا يمكن أن تكون سالبة')
            })

        # التحقق من عدم تجاوز الكمية المطلوبة
        if po_line:
            # حساب إجمالي المستلم سابقاً
            total_received = GoodsReceiptLine.objects.filter(
                purchase_order_line=po_line,
                goods_receipt__status__in=['confirmed', 'invoiced']
            ).exclude(
                pk=self.instance.pk if self.instance.pk else None
            ).aggregate(
                total=models.Sum('received_quantity')
            )['total'] or Decimal('0')

            new_total = total_received + received_qty

            if new_total > po_line.quantity:
                raise ValidationError({
                    'received_quantity': _(
                        'الكمية المستلمة الإجمالية (%(total)s) تتجاوز الكمية المطلوبة (%(ordered)s)'
                    ) % {
                        'total': new_total,
                        'ordered': po_line.quantity
                    }
                })

        return cleaned_data


class BaseGoodsReceiptLineFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور محضر الاستلام"""

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        """تمرير company لكل form"""
        kwargs['company'] = self.company
        return super()._construct_form(i, **kwargs)

    def clean(self):
        """التحقق من وجود سطر واحد على الأقل"""
        super().clean()

        if any(self.errors):
            return

        # التحقق من عدد السطور
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_forms += 1

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل'))


# إنشاء Formset
GoodsReceiptLineFormSet = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptLine,
    form=GoodsReceiptLineForm,
    formset=BaseGoodsReceiptLineFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

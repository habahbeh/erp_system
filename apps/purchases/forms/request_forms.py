# apps/purchases/forms/request_forms.py
"""
نماذج طلبات الشراء
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import PurchaseRequest, PurchaseRequestItem
from apps.core.models import Item, User


class PurchaseRequestForm(forms.ModelForm):
    """نموذج طلب الشراء"""

    class Meta:
        model = PurchaseRequest
        fields = [
            'date', 'requested_by', 'department', 'purpose',
            'required_date', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'requested_by': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الموظف...',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم القسم...',
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'الغرض من الطلب...',
            }),
            'required_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية...',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية المستخدمين النشطين
            self.fields['requested_by'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['date'].initial = date.today()

            if self.user:
                self.fields['requested_by'].initial = self.user

        # جعل الحقول اختيارية (حسب المتطلبات)
        self.fields['department'].required = False
        self.fields['purpose'].required = False
        self.fields['required_date'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()

        request_date = cleaned_data.get('date')
        required_date = cleaned_data.get('required_date')

        # التحقق من التواريخ
        if required_date and request_date:
            if required_date < request_date:
                raise ValidationError({
                    'required_date': _('التاريخ المطلوب يجب أن يكون بعد تاريخ الطلب')
                })

        return cleaned_data


class PurchaseRequestItemForm(forms.ModelForm):
    """نموذج سطر طلب الشراء"""

    class Meta:
        model = PurchaseRequestItem
        fields = [
            'item', 'item_description', 'quantity', 'unit',
            'estimated_price', 'notes'
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
            # تصفية المواد
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category', 'unit_of_measure')

        # جعل الحقول اختيارية
        self.fields['item'].required = False
        self.fields['unit'].required = False
        self.fields['estimated_price'].required = False
        self.fields['notes'].required = False


class BasePurchaseRequestItemFormSet(BaseInlineFormSet):
    """Formset مخصص لسطور طلب الشراء"""

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
                # يجب أن يحتوي السطر على وصف على الأقل
                if form.cleaned_data.get('item_description'):
                    valid_forms += 1

        if valid_forms < 1:
            raise ValidationError(_('يجب إضافة سطر واحد على الأقل لطلب الشراء'))


# إنشاء Inline Formset لسطور طلب الشراء
PurchaseRequestItemFormSet = inlineformset_factory(
    PurchaseRequest,
    PurchaseRequestItem,
    form=PurchaseRequestItemForm,
    formset=BasePurchaseRequestItemFormSet,
    extra=5,  # عدد السطور الفارغة الافتراضية
    can_delete=True,
    min_num=1,
    validate_min=True,
)

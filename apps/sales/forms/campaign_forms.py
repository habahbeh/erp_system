# apps/sales/forms/campaign_forms.py
"""
نماذج حملات الخصومات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date

from apps.sales.models import DiscountCampaign
from apps.core.models import Item, ItemCategory, BusinessPartner


class DiscountCampaignForm(forms.ModelForm):
    """نموذج حملة الخصم"""

    class Meta:
        model = DiscountCampaign
        fields = [
            'name',
            'code',
            'campaign_type',
            'description',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'discount_percentage',
            'discount_amount',
            'max_discount_amount',
            'buy_quantity',
            'get_quantity',
            'min_purchase_amount',
            'max_purchase_amount',
            'max_uses',
            'max_uses_per_customer',
            'items',
            'categories',
            'customers',
            'is_active',
            'priority',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('مثال: عرض رمضان 2025'),
                    'required': True,
                }
            ),
            'code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('مثال: RAMADAN2025'),
                    'style': 'text-transform: uppercase;',
                    'required': True,
                }
            ),
            'campaign_type': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True,
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': _('وصف تفصيلي للحملة وشروطها'),
                }
            ),
            'start_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'start_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                }
            ),
            'end_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                }
            ),
            'discount_percentage': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                    'max': '100',
                    'placeholder': '0.00',
                }
            ),
            'discount_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': '0.000',
                }
            ),
            'max_discount_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': _('غير محدود'),
                }
            ),
            'buy_quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': '0',
                }
            ),
            'get_quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': '0',
                }
            ),
            'min_purchase_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': _('غير محدد'),
                }
            ),
            'max_purchase_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': _('غير محدد'),
                }
            ),
            'max_uses': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'placeholder': _('غير محدود'),
                }
            ),
            'max_uses_per_customer': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'placeholder': _('غير محدود'),
                }
            ),
            'items': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2',
                    'multiple': 'multiple',
                    'data-placeholder': _('جميع المواد'),
                }
            ),
            'categories': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2',
                    'multiple': 'multiple',
                    'data-placeholder': _('جميع الأصناف'),
                }
            ),
            'customers': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2',
                    'multiple': 'multiple',
                    'data-placeholder': _('جميع العملاء'),
                }
            ),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'priority': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': '0',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': _('ملاحظات إضافية'),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تصفية الحقول حسب الشركة
        if self.company:
            self.fields['items'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['categories'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['customers'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                is_customer=True,
                is_active=True
            )

        # تعيين القيم الافتراضية للحقول
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['priority'].initial = 0

    def clean_code(self):
        """التحقق من أن الكود فريد"""
        code = self.cleaned_data.get('code', '').upper()

        # التحقق من عدم وجود حملة أخرى بنفس الكود في نفس الشركة
        queryset = DiscountCampaign.objects.filter(
            company=self.company,
            code=code
        )

        # استثناء الحملة الحالية في حالة التعديل
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError(_('يوجد حملة أخرى بنفس الكود في هذه الشركة'))

        return code

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        campaign_type = cleaned_data.get('campaign_type')

        # التحقق من التواريخ
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        # التحقق من الأوقات
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError({
                    'end_time': _('وقت النهاية يجب أن يكون بعد وقت البداية')
                })

        # التحقق من حقول الخصم حسب نوع الحملة
        if campaign_type == 'percentage':
            discount_percentage = cleaned_data.get('discount_percentage', 0)
            if discount_percentage == 0:
                raise ValidationError({
                    'discount_percentage': _('يجب تحديد نسبة الخصم لحملات الخصم النسبي')
                })

        elif campaign_type == 'fixed':
            discount_amount = cleaned_data.get('discount_amount', 0)
            if discount_amount == 0:
                raise ValidationError({
                    'discount_amount': _('يجب تحديد مبلغ الخصم لحملات الخصم الثابت')
                })

        elif campaign_type == 'buy_x_get_y':
            buy_quantity = cleaned_data.get('buy_quantity', 0)
            get_quantity = cleaned_data.get('get_quantity', 0)
            if buy_quantity == 0 or get_quantity == 0:
                raise ValidationError({
                    'buy_quantity': _('يجب تحديد كمية الشراء والهدية لحملات اشتري X واحصل على Y')
                })

        # التحقق من حدود المشتريات
        min_amount = cleaned_data.get('min_purchase_amount')
        max_amount = cleaned_data.get('max_purchase_amount')

        if min_amount and max_amount:
            if min_amount > max_amount:
                raise ValidationError({
                    'max_purchase_amount': _('الحد الأقصى يجب أن يكون أكبر من الحد الأدنى')
                })

        return cleaned_data

    def save(self, commit=True):
        """حفظ الحملة"""
        instance = super().save(commit=False)

        # تعيين الشركة
        if self.company:
            instance.company = self.company

        # تحويل الكود للأحرف الكبيرة
        instance.code = instance.code.upper()

        if commit:
            instance.save()
            # حفظ العلاقات ManyToMany
            self.save_m2m()

        return instance

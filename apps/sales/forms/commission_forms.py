# apps/sales/forms/commission_forms.py
"""
نماذج عمولات المندوبين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from apps.sales.models import SalespersonCommission, SalesInvoice


class SalespersonCommissionForm(forms.ModelForm):
    """نموذج عمولة المندوب"""

    class Meta:
        model = SalespersonCommission
        fields = [
            'salesperson',
            'invoice',
            'commission_rate',
            'base_amount',
            'paid_amount',
            'payment_date',
            'notes',
        ]
        widgets = {
            'salesperson': forms.Select(
                attrs={
                    'class': 'form-select select2',
                    'data-placeholder': _('اختر المندوب'),
                    'required': True,
                }
            ),
            'invoice': forms.Select(
                attrs={
                    'class': 'form-select select2',
                    'data-placeholder': _('اختر الفاتورة'),
                    'required': True,
                }
            ),
            'commission_rate': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                    'max': '100',
                    'placeholder': '0.00',
                    'required': True,
                }
            ),
            'base_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': '0.000',
                    'required': True,
                }
            ),
            'paid_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': '0.000',
                }
            ),
            'payment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': _('ملاحظات إضافية'),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تصفية الحقول حسب الشركة
        if self.company:
            # تصفية المندوبين (الموظفين فقط)
            from apps.hr.models import Employee
            self.fields['salesperson'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('first_name', 'last_name')

            # تصفية الفواتير (فواتير مرحلة وليس لها عمولة)
            self.fields['invoice'].queryset = SalesInvoice.objects.filter(
                company=self.company,
                is_posted=True,
                commission__isnull=True  # فواتير بدون عمولة
            ).order_by('-date')

        # جعل بعض الحقول اختيارية
        self.fields['paid_amount'].required = False
        self.fields['payment_date'].required = False
        self.fields['notes'].required = False

        # إذا كان التعديل، جعل الفاتورة للقراءة فقط
        if self.instance.pk:
            self.fields['invoice'].disabled = True
            self.fields['salesperson'].disabled = True

        # تعيين قيم افتراضية
        if not self.instance.pk:
            self.fields['paid_amount'].initial = 0

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        commission_rate = cleaned_data.get('commission_rate', 0)
        base_amount = cleaned_data.get('base_amount', 0)
        paid_amount = cleaned_data.get('paid_amount', 0)
        payment_date = cleaned_data.get('payment_date')

        # حساب مبلغ العمولة
        if commission_rate and base_amount:
            commission_amount = base_amount * (commission_rate / 100)

            # التحقق من أن المبلغ المدفوع لا يتجاوز مبلغ العمولة
            if paid_amount > commission_amount:
                raise ValidationError({
                    'paid_amount': _('المبلغ المدفوع لا يمكن أن يتجاوز مبلغ العمولة ({})').format(
                        commission_amount
                    )
                })

        # التحقق من تاريخ الدفع
        if paid_amount > 0 and not payment_date:
            raise ValidationError({
                'payment_date': _('يجب تحديد تاريخ الدفع عند وجود مبلغ مدفوع')
            })

        # التحقق من تطابق المندوب مع مندوب الفاتورة
        invoice = cleaned_data.get('invoice')
        salesperson = cleaned_data.get('salesperson')

        if invoice and salesperson:
            # التأكد من أن الفاتورة مرحلة
            if not invoice.is_posted:
                raise ValidationError({
                    'invoice': _('يجب أن تكون الفاتورة مرحلة لحساب العمولة')
                })

            # يمكن إضافة تحقق من تطابق المندوب إذا لزم الأمر
            # if invoice.salesperson != salesperson.user:
            #     raise ValidationError({
            #         'salesperson': _('المندوب المختار لا يتطابق مع مندوب الفاتورة')
            #     })

        return cleaned_data

    def save(self, commit=True):
        """حفظ العمولة"""
        instance = super().save(commit=False)

        # تعيين الشركة
        if self.company:
            instance.company = self.company

        # تعيين الفرع من الفاتورة
        if instance.invoice:
            instance.branch = instance.invoice.branch

        if commit:
            instance.save()

        return instance


class RecordCommissionPaymentForm(forms.ModelForm):
    """نموذج تسجيل دفعة عمولة"""

    class Meta:
        model = SalespersonCommission
        fields = [
            'paid_amount',
            'payment_date',
            'notes',
        ]
        widgets = {
            'paid_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': '0.000',
                    'required': True,
                    'autofocus': True,
                }
            ),
            'payment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': _('ملاحظات الدفع'),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تعيين القيم الافتراضية
        if not self.instance.pk:
            self.fields['payment_date'].initial = date.today()

        # حساب المبلغ المتبقي لعرضه
        if self.instance.pk:
            self.remaining_amount = self.instance.remaining_amount
        else:
            self.remaining_amount = 0

        self.fields['notes'].required = False

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        paid_amount = cleaned_data.get('paid_amount', 0)
        payment_date = cleaned_data.get('payment_date')

        # التحقق من المبلغ المدفوع
        if paid_amount <= 0:
            raise ValidationError({
                'paid_amount': _('يجب أن يكون المبلغ المدفوع أكبر من صفر')
            })

        # التحقق من أن المبلغ لا يتجاوز المتبقي
        if self.instance.pk:
            new_total_paid = self.instance.paid_amount + paid_amount
            if new_total_paid > self.instance.commission_amount:
                raise ValidationError({
                    'paid_amount': _('المبلغ المدفوع يتجاوز المبلغ المتبقي ({})').format(
                        self.instance.remaining_amount
                    )
                })

        # التحقق من تاريخ الدفع
        if not payment_date:
            raise ValidationError({
                'payment_date': _('يجب تحديد تاريخ الدفع')
            })

        return cleaned_data

    def save(self, commit=True):
        """حفظ الدفعة"""
        instance = self.instance

        # إضافة المبلغ المدفوع للمبلغ الحالي
        paid_amount = self.cleaned_data.get('paid_amount', 0)
        instance.paid_amount += paid_amount

        # تحديث تاريخ الدفع
        instance.payment_date = self.cleaned_data.get('payment_date')

        # تحديث الملاحظات (دمج الملاحظات القديمة مع الجديدة)
        new_notes = self.cleaned_data.get('notes', '').strip()
        if new_notes:
            if instance.notes:
                instance.notes += f"\n\n[{date.today()}] {new_notes}"
            else:
                instance.notes = f"[{date.today()}] {new_notes}"

        if commit:
            instance.save()

        return instance

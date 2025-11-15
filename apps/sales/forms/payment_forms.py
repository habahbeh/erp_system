# apps/sales/forms/payment_forms.py
"""
نماذج أقساط الدفع
"""

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from datetime import date, timedelta

from apps.sales.models import PaymentInstallment, SalesInvoice


class PaymentInstallmentForm(forms.ModelForm):
    """نموذج قسط الدفع"""

    class Meta:
        model = PaymentInstallment
        fields = [
            'installment_number',
            'due_date',
            'amount',
            'notes',
        ]
        widgets = {
            'installment_number': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'required': True,
                }
            ),
            'due_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control amount-input',
                    'step': '0.001',
                    'min': '0.001',
                    'required': True,
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                }
            ),
        }

    def clean_installment_number(self):
        installment_number = self.cleaned_data.get('installment_number')
        if installment_number and installment_number < 1:
            raise ValidationError(_('رقم القسط يجب أن يكون 1 أو أكبر'))
        return installment_number

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError(_('المبلغ يجب أن يكون أكبر من صفر'))
        return amount

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            # التحقق من أن تاريخ الاستحقاق ليس في الماضي
            if due_date < date.today():
                raise ValidationError(_('تاريخ الاستحقاق لا يمكن أن يكون في الماضي'))
        return due_date


class RecordPaymentForm(forms.Form):
    """نموذج تسجيل دفعة على قسط"""

    payment_date = forms.DateField(
        label=_('تاريخ الدفع'),
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
        initial=date.today
    )

    paid_amount = forms.DecimalField(
        label=_('المبلغ المدفوع'),
        max_digits=15,
        decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001',
            }
        )
    )

    payment_method = forms.ModelChoiceField(
        label=_('طريقة الدفع'),
        queryset=None,
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2',
            }
        )
    )

    reference_number = forms.CharField(
        label=_('رقم المرجع'),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('رقم الشيك، رقم الحوالة، إلخ')
            }
        )
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.installment = kwargs.pop('installment', None)
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # تصفية طرق الدفع حسب الشركة
        if self.company:
            from apps.core.models import PaymentMethod
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
                company=self.company,
                is_active=True
            )

        # تعيين الحد الأقصى للمبلغ المدفوع
        if self.installment:
            remaining = self.installment.remaining_amount
            self.fields['paid_amount'].widget.attrs['max'] = str(remaining)
            self.fields['paid_amount'].help_text = _(
                'المبلغ المتبقي: {}'
            ).format(remaining)

    def clean_paid_amount(self):
        paid_amount = self.cleaned_data.get('paid_amount')

        if self.installment and paid_amount:
            remaining = self.installment.remaining_amount
            if paid_amount > remaining:
                raise ValidationError(
                    _('المبلغ المدفوع ({}) أكبر من المبلغ المتبقي ({})').format(
                        paid_amount, remaining
                    )
                )

        return paid_amount


class CreateInstallmentPlanForm(forms.Form):
    """نموذج إنشاء خطة أقساط تلقائية"""

    number_of_installments = forms.IntegerField(
        label=_('عدد الأقساط'),
        min_value=1,
        max_value=36,
        initial=3,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'min': '1',
                'max': '36',
            }
        ),
        help_text=_('عدد الأقساط المطلوبة (1-36)')
    )

    first_installment_date = forms.DateField(
        label=_('تاريخ أول قسط'),
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
        help_text=_('تاريخ استحقاق أول قسط')
    )

    interval_days = forms.IntegerField(
        label=_('الفترة بين الأقساط (بالأيام)'),
        min_value=1,
        initial=30,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'min': '1',
            }
        ),
        help_text=_('عدد الأيام بين كل قسط والآخر')
    )

    equal_amounts = forms.BooleanField(
        label=_('مبالغ متساوية'),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input',
            }
        ),
        help_text=_('توزيع المبلغ بالتساوي على جميع الأقساط')
    )

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)

        # تعيين تاريخ أول قسط الافتراضي (بعد شهر من تاريخ الفاتورة)
        if self.invoice and not self.is_bound:
            self.fields['first_installment_date'].initial = (
                self.invoice.date + timedelta(days=30)
            )

    def clean_first_installment_date(self):
        first_date = self.cleaned_data.get('first_installment_date')

        if first_date and self.invoice:
            # التحقق من أن تاريخ أول قسط بعد تاريخ الفاتورة
            if first_date < self.invoice.date:
                raise ValidationError(
                    _('تاريخ أول قسط يجب أن يكون بعد تاريخ الفاتورة ({})').format(
                        self.invoice.date
                    )
                )

        return first_date

    def generate_installments(self):
        """توليد قائمة الأقساط بناءً على المعطيات"""
        if not self.is_valid() or not self.invoice:
            return []

        number_of_installments = self.cleaned_data['number_of_installments']
        first_date = self.cleaned_data['first_installment_date']
        interval_days = self.cleaned_data['interval_days']
        equal_amounts = self.cleaned_data['equal_amounts']

        # حساب المبلغ المتبقي للتقسيط
        remaining_amount = self.invoice.total_with_tax - self.invoice.installments.aggregate(
            total=models.Sum('amount')
        ).get('total') or Decimal('0')

        installments = []

        if equal_amounts:
            # مبالغ متساوية
            amount_per_installment = remaining_amount / number_of_installments

            for i in range(number_of_installments):
                installment_date = first_date + timedelta(days=interval_days * i)

                # التأكد من أن آخر قسط يأخذ أي فرق بسبب التقريب
                if i == number_of_installments - 1:
                    amount = remaining_amount - (amount_per_installment * (number_of_installments - 1))
                else:
                    amount = amount_per_installment

                installments.append({
                    'installment_number': i + 1,
                    'due_date': installment_date,
                    'amount': amount,
                })
        else:
            # مبالغ مخصصة (سيتم إدخالها يدوياً)
            for i in range(number_of_installments):
                installment_date = first_date + timedelta(days=interval_days * i)

                installments.append({
                    'installment_number': i + 1,
                    'due_date': installment_date,
                    'amount': Decimal('0'),
                })

        return installments


# إنشاء InstallmentPlanFormSet
InstallmentPlanFormSet = inlineformset_factory(
    SalesInvoice,
    PaymentInstallment,
    form=PaymentInstallmentForm,
    extra=3,  # عدد النماذج الإضافية الفارغة
    can_delete=True,
    min_num=1,  # الحد الأدنى من الأقساط
    validate_min=True,
)

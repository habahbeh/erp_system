# apps/assets/forms/lease_forms.py
"""
نماذج الإيجار على الأصول
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

from ..models import AssetLease, LeasePayment, Asset, AssetTransaction
from apps.core.models import BusinessPartner


class AssetLeaseForm(forms.ModelForm):
    """نموذج عقد إيجار أصل"""

    class Meta:
        model = AssetLease
        fields = [
            'asset', 'lessor', 'lease_type',
            'start_date', 'end_date', 'payment_frequency',
            'monthly_payment', 'security_deposit',
            'interest_rate', 'residual_value', 'purchase_option_price',
            'status', 'contract_file', 'notes'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'lessor': forms.Select(attrs={'class': 'form-select'}),
            'lease_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_frequency': forms.Select(attrs={'class': 'form-select'}),
            'monthly_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'security_deposit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
                'value': '0.000'
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'للإيجار التمويلي فقط %'
            }),
            'residual_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'القيمة المتوقعة في نهاية العقد'
            }),
            'purchase_option_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'سعر خيار الشراء'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'contract_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            ).select_related('category')

            self.fields['lessor'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        monthly_payment = cleaned_data.get('monthly_payment')
        lease_type = cleaned_data.get('lease_type')
        interest_rate = cleaned_data.get('interest_rate')

        # التحقق من التواريخ
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        # التحقق من معدل الفائدة للإيجار التمويلي
        if lease_type == 'finance' and not interest_rate:
            raise ValidationError({
                'interest_rate': _('يجب تحديد معدل الفائدة للإيجار التمويلي')
            })

        return cleaned_data


class LeasePaymentForm(forms.ModelForm):
    """نموذج دفعة إيجار"""

    class Meta:
        model = LeasePayment
        fields = [
            'lease', 'payment_number', 'payment_date',
            'amount', 'principal_amount', 'interest_amount',
            'is_paid', 'paid_date',
            'notes'
        ]
        widgets = {
            'lease': forms.Select(attrs={'class': 'form-select'}),
            'payment_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم القسط'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'principal_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'للإيجار التمويلي فقط'
            }),
            'interest_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'للإيجار التمويلي فقط'
            }),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'paid_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # فقط العقود النشطة
            leases = AssetLease.objects.filter(
                company=self.company,
                status='active'
            ).select_related('asset', 'lessor')

            self.fields['lease'].queryset = leases

            # إضافة label مخصص للعقود
            self.fields['lease'].label_from_instance = lambda obj: f"{obj.lease_number} - {obj.asset.name} ({obj.get_lease_type_display()})"

            # إضافة رسالة توضيحية إذا لم توجد عقود
            if not leases.exists():
                self.fields['lease'].help_text = "لا توجد عقود نشطة. يرجى إنشاء عقد إيجار أولاً."

        # تحسين العلامات والنصوص
        self.fields['lease'].empty_label = "اختر عقد الإيجار"
        self.fields['payment_number'].help_text = "رقم القسط التسلسلي"
        self.fields['amount'].help_text = "مبلغ الدفعة"

        # إذا كان lease محدد، ملء البيانات الافتراضية
        if self.instance.lease_id:
            lease = self.instance.lease
            if not self.instance.amount:
                self.fields['amount'].initial = lease.monthly_payment

            # للإيجار التمويلي، حساب principal و interest
            if lease.lease_type == 'finance' and not self.instance.pk:
                # حساب بسيط - يمكن تحسينه لاحقاً
                if lease.interest_rate:
                    interest = (lease.monthly_payment * lease.interest_rate) / Decimal('100') / Decimal('12')
                    principal = lease.monthly_payment - interest
                    self.fields['principal_amount'].initial = principal
                    self.fields['interest_amount'].initial = interest

    def clean(self):
        cleaned_data = super().clean()

        payment_date = cleaned_data.get('payment_date')
        due_date = cleaned_data.get('due_date')
        payment_amount = cleaned_data.get('payment_amount')
        principal_amount = cleaned_data.get('principal_amount')
        interest_amount = cleaned_data.get('interest_amount')
        lease = cleaned_data.get('lease')

        # التحقق من التواريخ
        if payment_date and due_date:
            if payment_date < due_date:
                # تحذير فقط - الدفع المبكر مسموح
                pass

        # التحقق من المبالغ للإيجار التمويلي
        if lease and lease.lease_type == 'finance':
            if principal_amount and interest_amount:
                if abs((principal_amount + interest_amount) - payment_amount) > Decimal('0.01'):
                    raise ValidationError(
                        _('مجموع الأصل والفائدة يجب أن يساوي مبلغ الدفعة')
                    )
            elif not principal_amount or not interest_amount:
                raise ValidationError(
                    _('يجب تحديد مبلغ الأصل والفائدة للإيجار التمويلي')
                )

        return cleaned_data


class LeaseTerminationForm(forms.Form):
    """نموذج إنهاء عقد إيجار"""

    lease_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    termination_date = forms.DateField(
        label=_('تاريخ الإنهاء'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.date.today
    )

    termination_reason = forms.CharField(
        label=_('سبب الإنهاء'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'اذكر سبب إنهاء العقد بشكل مفصل'
        })
    )

    early_termination_fee = forms.DecimalField(
        label=_('غرامة الإنهاء المبكر'),
        max_digits=15,
        decimal_places=3,
        required=False,
        initial=Decimal('0.000'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000'
        })
    )

    def __init__(self, *args, **kwargs):
        self.lease = kwargs.pop('lease', None)
        super().__init__(*args, **kwargs)

        if self.lease:
            self.fields['lease_id'].initial = self.lease.id

    def clean(self):
        cleaned_data = super().clean()
        termination_date = cleaned_data.get('termination_date')
        termination_reason = cleaned_data.get('termination_reason')

        # التحقق من التاريخ
        if termination_date:
            if termination_date > datetime.date.today():
                raise ValidationError({
                    'termination_date': _('لا يمكن إنهاء العقد بتاريخ مستقبلي')
                })

            if self.lease and termination_date < self.lease.start_date:
                raise ValidationError({
                    'termination_date': _('تاريخ الإنهاء لا يمكن أن يكون قبل تاريخ بداية العقد')
                })

            # تحذير للإنهاء المبكر
            if self.lease and termination_date < self.lease.end_date:
                self.add_error(None, ValidationError(
                    _('تنبيه: إنهاء مبكر قبل تاريخ انتهاء العقد (%(end_date)s)') % {
                        'end_date': self.lease.end_date
                    },
                    code='warning'
                ))

        # التحقق من السبب
        if not termination_reason or len(termination_reason.strip()) < 20:
            raise ValidationError({
                'termination_reason': _('يجب إدخال سبب مفصل للإنهاء (20 حرف على الأقل)')
            })

        return cleaned_data


class LeaseRenewalForm(forms.Form):
    """نموذج تجديد عقد إيجار"""

    lease_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    new_start_date = forms.DateField(
        label=_('تاريخ بداية العقد الجديد'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    new_end_date = forms.DateField(
        label=_('تاريخ نهاية العقد الجديد'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    new_payment_amount = forms.DecimalField(
        label=_('مبلغ الدفعة الجديد'),
        max_digits=15,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000'
        })
    )

    same_terms = forms.BooleanField(
        required=False,
        initial=True,
        label=_('الاحتفاظ بنفس الشروط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('استخدام نفس شروط العقد السابق')
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )

    def __init__(self, *args, **kwargs):
        self.lease = kwargs.pop('lease', None)
        super().__init__(*args, **kwargs)

        if self.lease:
            self.fields['lease_id'].initial = self.lease.id
            # تعيين تاريخ البداية بعد نهاية العقد الحالي
            self.fields['new_start_date'].initial = self.lease.end_date + datetime.timedelta(days=1)
            # نفس مبلغ الدفعة
            self.fields['new_payment_amount'].initial = self.lease.monthly_payment

    def clean(self):
        cleaned_data = super().clean()
        new_start_date = cleaned_data.get('new_start_date')
        new_end_date = cleaned_data.get('new_end_date')

        # التحقق من التواريخ
        if new_start_date and new_end_date:
            if new_end_date <= new_start_date:
                raise ValidationError({
                    'new_end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        # التحقق من أن تاريخ البداية بعد نهاية العقد الحالي
        if self.lease and new_start_date:
            if new_start_date <= self.lease.end_date:
                raise ValidationError({
                    'new_start_date': _('تاريخ بداية العقد الجديد يجب أن يكون بعد نهاية العقد الحالي')
                })

        return cleaned_data


class PurchaseOptionForm(forms.Form):
    """نموذج تنفيذ خيار الشراء"""

    lease_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    exercise_date = forms.DateField(
        label=_('تاريخ التنفيذ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.date.today
    )

    purchase_price = forms.DecimalField(
        label=_('سعر الشراء'),
        max_digits=15,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000',
            'readonly': True
        }),
        help_text=_('من خيار الشراء في العقد')
    )

    payment_method = forms.ChoiceField(
        label=_('طريقة الدفع'),
        choices=AssetTransaction.PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    reference_number = forms.CharField(
        label=_('رقم المرجع'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الشيك أو رقم التحويل'
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )

    def __init__(self, *args, **kwargs):
        self.lease = kwargs.pop('lease', None)
        super().__init__(*args, **kwargs)

        if self.lease:
            self.fields['lease_id'].initial = self.lease.id
            if self.lease.purchase_option_price:
                self.fields['purchase_price'].initial = self.lease.purchase_option_price

    def clean(self):
        cleaned_data = super().clean()
        exercise_date = cleaned_data.get('exercise_date')

        # التحقق من وجود خيار الشراء
        if self.lease and not self.lease.purchase_option_price:
            raise ValidationError(_('هذا العقد لا يحتوي على خيار شراء'))

        # التحقق من التاريخ
        if exercise_date and self.lease:
            if exercise_date < self.lease.start_date:
                raise ValidationError({
                    'exercise_date': _('تاريخ التنفيذ لا يمكن أن يكون قبل بداية العقد')
                })

        return cleaned_data


class BulkPaymentProcessingForm(forms.Form):
    """نموذج معالجة دفعات جماعية"""

    payment_ids = forms.CharField(
        widget=forms.HiddenInput(),
        help_text=_('IDs للدفعات المحددة - JSON array')
    )

    processing_date = forms.DateField(
        label=_('تاريخ المعالجة'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.date.today
    )

    auto_post = forms.BooleanField(
        required=False,
        initial=True,
        label=_('ترحيل القيود تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean_processing_date(self):
        processing_date = self.cleaned_data.get('processing_date')

        if processing_date and processing_date > datetime.date.today():
            raise ValidationError(_('لا يمكن معالجة الدفعات بتاريخ مستقبلي'))

        return processing_date


class LeaseFilterForm(forms.Form):
    """نموذج فلترة عقود الإيجار"""

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label=_('جميع الأصول'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    lessor = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.none(),
        required=False,
        empty_label=_('جميع المؤجرين'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    lease_type = forms.ChoiceField(
        choices=[('', _('جميع الأنواع'))] + AssetLease.LEASE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('جميع الحالات'))] + AssetLease.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    expiring_soon = forms.BooleanField(
        required=False,
        label=_('قريبة من الانتهاء فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('خلال 30 يوم')
    )

    overdue_payments = forms.BooleanField(
        required=False,
        label=_('لديها دفعات متأخرة'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['lessor'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                is_active=True
            )


class PaymentFilterForm(forms.Form):
    """نموذج فلترة دفعات الإيجار"""

    lease = forms.ModelChoiceField(
        queryset=AssetLease.objects.none(),
        required=False,
        empty_label=_('جميع العقود'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_paid = forms.ChoiceField(
        choices=[
            ('', _('الكل')),
            ('yes', _('المدفوعة فقط')),
            ('no', _('غير المدفوعة فقط'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    overdue_only = forms.BooleanField(
        required=False,
        label=_('المتأخرة فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['lease'].queryset = AssetLease.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('asset', 'lessor')

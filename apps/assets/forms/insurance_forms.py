# apps/assets/forms/insurance_forms.py
"""
نماذج التأمين على الأصول
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

from ..models import InsuranceCompany, AssetInsurance, InsuranceClaim, Asset


class InsuranceCompanyForm(forms.ModelForm):
    """نموذج شركة تأمين"""

    class Meta:
        model = InsuranceCompany
        fields = [
            'code', 'name', 'name_en',
            'contact_person', 'phone', 'mobile', 'email', 'fax',
            'address', 'city', 'country',
            'website', 'license_number', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: INS001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم شركة التأمين'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Insurance Company Name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم جهة الاتصال'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+966-11-1234567'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+966-50-1234567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'info@insurance.com'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+966-11-1234568'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'العنوان الكامل'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الدولة'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.insurance.com'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الترخيص'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class AssetInsuranceForm(forms.ModelForm):
    """نموذج بوليصة تأمين أصل"""

    class Meta:
        model = AssetInsurance
        fields = [
            'insurance_company', 'asset',
            'coverage_type', 'coverage_description',
            'coverage_amount', 'premium_amount', 'deductible_amount',
            'payment_frequency', 'next_payment_date',
            'start_date', 'end_date', 'renewal_date',
            'policy_document', 'notes'
        ]
        widgets = {
            'insurance_company': forms.Select(attrs={'class': 'form-select'}),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'coverage_type': forms.Select(attrs={'class': 'form-select'}),
            'coverage_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'تفاصيل التغطية والاستثناءات'
            }),
            'coverage_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'premium_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'deductible_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
                'value': '0.000'
            }),
            'payment_frequency': forms.Select(attrs={'class': 'form-select'}),
            'next_payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'renewal_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'تاريخ التذكير بالتجديد'
            }),
            'policy_document': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['insurance_company'].queryset = InsuranceCompany.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            ).select_related('category')

        # إذا كان asset محدد، ملء coverage_amount من book_value
        if self.instance.asset_id:
            asset = self.instance.asset
            if not self.instance.coverage_amount:
                self.fields['coverage_amount'].initial = asset.book_value

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        renewal_date = cleaned_data.get('renewal_date')
        coverage_amount = cleaned_data.get('coverage_amount')
        asset = cleaned_data.get('asset')
        premium_amount = cleaned_data.get('premium_amount')

        # التحقق من التواريخ
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        if renewal_date and end_date:
            if renewal_date > end_date:
                raise ValidationError({
                    'renewal_date': _('تاريخ التجديد يجب أن يكون قبل أو يساوي تاريخ النهاية')
                })

        # تحذير إذا كان مبلغ التغطية أقل من القيمة الدفترية
        if coverage_amount and asset:
            if coverage_amount < asset.book_value:
                # تحذير فقط، لا نمنع
                self.add_error('coverage_amount', ValidationError(
                    _('تحذير: مبلغ التغطية (%(coverage)s) أقل من القيمة الدفترية للأصل (%(book_value)s)'),
                    code='warning',
                    params={
                        'coverage': coverage_amount,
                        'book_value': asset.book_value
                    }
                ))

        # التحقق من القسط
        if premium_amount and coverage_amount:
            if premium_amount >= coverage_amount:
                raise ValidationError({
                    'premium_amount': _('قسط التأمين يجب أن يكون أقل من مبلغ التغطية')
                })

        return cleaned_data


class InsuranceClaimForm(forms.ModelForm):
    """نموذج مطالبة تأمين"""

    class Meta:
        model = InsuranceClaim
        fields = [
            'insurance', 'claim_type',
            'incident_date', 'incident_time', 'incident_location',
            'incident_description',
            'estimated_damage', 'claim_amount',
            'police_report', 'damage_photos', 'repair_estimate',
            'other_documents', 'notes'
        ]
        widgets = {
            'insurance': forms.Select(attrs={'class': 'form-select'}),
            'claim_type': forms.Select(attrs={'class': 'form-select'}),
            'incident_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'incident_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'incident_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مكان وقوع الحادث'
            }),
            'incident_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'وصف مفصل للحادث'
            }),
            'estimated_damage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'claim_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'police_report': forms.FileInput(attrs={'class': 'form-control'}),
            'damage_photos': forms.FileInput(attrs={'class': 'form-control'}),
            'repair_estimate': forms.FileInput(attrs={'class': 'form-control'}),
            'other_documents': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # فقط البوليصات النشطة
            self.fields['insurance'].queryset = AssetInsurance.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            ).select_related('asset', 'insurance_company')

    def clean(self):
        cleaned_data = super().clean()

        insurance = cleaned_data.get('insurance')
        incident_date = cleaned_data.get('incident_date')
        claim_amount = cleaned_data.get('claim_amount')
        estimated_damage = cleaned_data.get('estimated_damage')

        # التحقق من أن تاريخ الحادث ضمن فترة البوليصة
        if insurance and incident_date:
            if incident_date < insurance.start_date or incident_date > insurance.end_date:
                raise ValidationError({
                    'incident_date': _('تاريخ الحادث يجب أن يكون ضمن فترة سريان البوليصة')
                })

        # التحقق من مبلغ المطالبة
        if insurance and claim_amount:
            if claim_amount > insurance.coverage_amount:
                raise ValidationError({
                    'claim_amount': _('مبلغ المطالبة (%(claim)s) يتجاوز حد التغطية (%(coverage)s)') % {
                        'claim': claim_amount,
                        'coverage': insurance.coverage_amount
                    }
                })

        # التحقق من مبلغ المطالبة vs الضرر المقدر
        if claim_amount and estimated_damage:
            if claim_amount > estimated_damage:
                raise ValidationError({
                    'claim_amount': _('مبلغ المطالبة لا يمكن أن يتجاوز الضرر المقدر')
                })

        return cleaned_data


class ClaimApprovalForm(forms.Form):
    """نموذج اعتماد مطالبة تأمين"""

    claim_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    approved_amount = forms.DecimalField(
        label=_('المبلغ المعتمد'),
        max_digits=15,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000'
        })
    )

    deductible_applied = forms.DecimalField(
        label=_('التحمل المطبق'),
        max_digits=15,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.000',
            'readonly': True
        }),
        help_text=_('يتم ملؤه تلقائياً من البوليصة')
    )

    approval_notes = forms.CharField(
        label=_('ملاحظات الاعتماد'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات إضافية'
        })
    )

    def __init__(self, *args, **kwargs):
        self.claim = kwargs.pop('claim', None)
        super().__init__(*args, **kwargs)

        if self.claim:
            self.fields['claim_id'].initial = self.claim.id
            # ملء المبلغ الافتراضي من مبلغ المطالبة
            self.fields['approved_amount'].initial = self.claim.claim_amount
            # ملء التحمل من البوليصة
            self.fields['deductible_applied'].initial = self.claim.insurance.deductible_amount

    def clean(self):
        cleaned_data = super().clean()
        approved_amount = cleaned_data.get('approved_amount')

        if self.claim:
            # التحقق من أن المبلغ المعتمد لا يتجاوز مبلغ المطالبة
            if approved_amount and approved_amount > self.claim.claim_amount:
                raise ValidationError({
                    'approved_amount': _('المبلغ المعتمد لا يمكن أن يتجاوز مبلغ المطالبة (%(claim_amount)s)') % {
                        'claim_amount': self.claim.claim_amount
                    }
                })

            # التحقق من أن المبلغ المعتمد لا يتجاوز حد التغطية
            if approved_amount and approved_amount > self.claim.insurance.coverage_amount:
                raise ValidationError({
                    'approved_amount': _('المبلغ المعتمد يتجاوز حد التغطية')
                })

        return cleaned_data


class ClaimRejectionForm(forms.Form):
    """نموذج رفض مطالبة تأمين"""

    claim_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    rejection_reason = forms.CharField(
        label=_('سبب الرفض'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'اذكر سبب رفض المطالبة بشكل مفصل'
        })
    )

    def __init__(self, *args, **kwargs):
        self.claim = kwargs.pop('claim', None)
        super().__init__(*args, **kwargs)

        if self.claim:
            self.fields['claim_id'].initial = self.claim.id

    def clean_rejection_reason(self):
        reason = self.cleaned_data.get('rejection_reason')
        if reason and len(reason.strip()) < 20:
            raise ValidationError(
                _('يجب إدخال سبب مفصل للرفض (20 حرف على الأقل)')
            )
        return reason


class ClaimPaymentForm(forms.Form):
    """نموذج معالجة دفع مطالبة تأمين"""

    claim_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    payment_date = forms.DateField(
        label=_('تاريخ الدفع'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.date.today
    )

    payment_notes = forms.CharField(
        label=_('ملاحظات الدفع'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'ملاحظات إضافية'
        })
    )

    auto_post = forms.BooleanField(
        required=False,
        initial=True,
        label=_('ترحيل القيد تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, **kwargs):
        self.claim = kwargs.pop('claim', None)
        super().__init__(*args, **kwargs)

        if self.claim:
            self.fields['claim_id'].initial = self.claim.id

    def clean_payment_date(self):
        payment_date = self.cleaned_data.get('payment_date')

        if payment_date and payment_date > datetime.date.today():
            raise ValidationError(_('لا يمكن معالجة دفع بتاريخ مستقبلي'))

        if self.claim and payment_date:
            if payment_date < self.claim.filed_date:
                raise ValidationError(_('تاريخ الدفع لا يمكن أن يكون قبل تاريخ تقديم المطالبة'))

        return payment_date


class InsuranceFilterForm(forms.Form):
    """نموذج فلترة بوليصات التأمين"""

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label=_('جميع الأصول'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    insurance_company = forms.ModelChoiceField(
        queryset=InsuranceCompany.objects.none(),
        required=False,
        empty_label=_('جميع الشركات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('جميع الحالات'))] + AssetInsurance.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    coverage_type = forms.ChoiceField(
        choices=[('', _('جميع أنواع التغطية'))] + AssetInsurance.COVERAGE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    expiring_soon = forms.BooleanField(
        required=False,
        label=_('قريبة من الانتهاء فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('خلال 30 يوم')
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
            self.fields['insurance_company'].queryset = InsuranceCompany.objects.filter(
                company=self.company,
                is_active=True
            )


class ClaimFilterForm(forms.Form):
    """نموذج فلترة مطالبات التأمين"""

    insurance = forms.ModelChoiceField(
        queryset=AssetInsurance.objects.none(),
        required=False,
        empty_label=_('جميع البوليصات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    claim_type = forms.ChoiceField(
        choices=[('', _('جميع الأنواع'))] + InsuranceClaim.CLAIM_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('جميع الحالات'))] + InsuranceClaim.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
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
            self.fields['insurance'].queryset = AssetInsurance.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('asset', 'insurance_company')

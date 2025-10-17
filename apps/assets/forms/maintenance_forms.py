# apps/assets/forms/maintenance_forms.py
"""
نماذج الصيانة
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import datetime

from ..models import MaintenanceType, MaintenanceSchedule, AssetMaintenance, Asset
from apps.accounting.models import Account
from apps.core.models import User


class MaintenanceTypeForm(forms.ModelForm):
    """نموذج نوع الصيانة"""

    class Meta:
        model = MaintenanceType
        fields = ['code', 'name', 'name_en', 'description']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: PREV, CORR, EMRG'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: صيانة وقائية، تصحيحية'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preventive, Corrective'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class MaintenanceScheduleForm(forms.ModelForm):
    """نموذج جدولة الصيانة"""

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'asset', 'maintenance_type', 'frequency', 'custom_days',
            'start_date', 'end_date', 'alert_before_days',
            'assigned_to', 'estimated_cost', 'description', 'notes'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'custom_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'عدد الأيام للتكرار المخصص'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'اتركه فارغاً للصيانة الدائمة'
            }),
            'alert_before_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '7'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
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
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                status='active',
                is_active=True
            )
            self.fields['assigned_to'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()

        frequency = cleaned_data.get('frequency')
        custom_days = cleaned_data.get('custom_days')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # التحقق من التكرار المخصص
        if frequency == 'custom' and not custom_days:
            raise ValidationError({
                'custom_days': _('يجب تحديد عدد الأيام للتكرار المخصص')
            })

        # التحقق من التواريخ
        if end_date and start_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        return cleaned_data


class AssetMaintenanceForm(forms.ModelForm):
    """نموذج صيانة الأصل"""

    class Meta:
        model = AssetMaintenance
        fields = [
            'asset', 'maintenance_type', 'maintenance_category',
            'maintenance_schedule', 'scheduled_date', 'start_date',
            'completion_date', 'status', 'performed_by',
            'external_vendor', 'vendor_invoice_number',
            'labor_cost', 'parts_cost', 'other_cost',
            'is_capital_improvement', 'parts_description',
            'description', 'issues_found', 'recommendations',
            'notes', 'attachment'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_category': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_schedule': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختياري - إذا كانت من جدول'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'performed_by': forms.Select(attrs={'class': 'form-select'}),
            'external_vendor': forms.Select(attrs={'class': 'form-select'}),
            'vendor_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم فاتورة المورد'
            }),
            'labor_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'parts_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'other_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'is_capital_improvement': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'parts_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'قطع الغيار المستخدمة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف الأعمال المنفذة'
            }),
            'issues_found': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'المشاكل المكتشفة'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'التوصيات'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['maintenance_schedule'].queryset = MaintenanceSchedule.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['performed_by'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['external_vendor'].queryset = Account.objects.filter(
                company=self.company,
                account_type__type_category='liabilities',
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        completion_date = cleaned_data.get('completion_date')
        status = cleaned_data.get('status')

        # التحقق من التواريخ
        if start_date and completion_date:
            if completion_date < start_date:
                raise ValidationError({
                    'completion_date': _('تاريخ الإنجاز يجب أن يكون بعد تاريخ البدء')
                })

        # التحقق من الحالة المكتملة
        if status == 'completed' and not completion_date:
            raise ValidationError({
                'completion_date': _('يجب تحديد تاريخ الإنجاز للصيانة المكتملة')
            })

        return cleaned_data


class MaintenanceFilterForm(forms.Form):
    """نموذج فلترة الصيانة"""

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label='جميع الأصول',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    maintenance_type = forms.ModelChoiceField(
        queryset=MaintenanceType.objects.none(),
        required=False,
        empty_label='جميع الأنواع',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'جميع الحالات')] + AssetMaintenance.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    maintenance_category = forms.ChoiceField(
        choices=[('', 'جميع التصنيفات')] + AssetMaintenance.MAINTENANCE_CATEGORY,
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
    overdue_only = forms.BooleanField(
        required=False,
        label=_('المتأخرة فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['asset'].queryset = Asset.objects.filter(
                company=company,
                is_active=True
            )
            self.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
                is_active=True
            )
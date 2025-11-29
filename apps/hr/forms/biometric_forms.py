# apps/hr/forms/biometric_forms.py
"""
نماذج أجهزة البصمة
Biometric Device Forms
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import (
    BiometricDevice,
    EmployeeBiometricMapping,
    Employee
)


class BiometricDeviceForm(forms.ModelForm):
    """نموذج إضافة/تعديل جهاز بصمة"""

    class Meta:
        model = BiometricDevice
        fields = [
            'name', 'device_type', 'serial_number',
            'connection_type', 'ip_address', 'port',
            'device_password', 'location', 'branch',
            'status', 'is_active', 'auto_sync', 'sync_interval',
            'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: جهاز البصمة - المدخل الرئيسي')
            }),
            'device_type': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الرقم التسلسلي للجهاز')
            }),
            'connection_type': forms.Select(attrs={'class': 'form-select'}),
            'ip_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '192.168.1.100'
            }),
            'port': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535
            }),
            'device_password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': _('كلمة مرور الجهاز (اختياري)')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: المدخل الرئيسي - الطابق الأرضي')
            }),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_sync': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 1440
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية')
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

        if company:
            # فلترة الفروع حسب الشركة
            from apps.core.models import Branch
            self.fields['branch'].queryset = Branch.objects.filter(
                company=company, is_active=True
            )

    def clean_ip_address(self):
        ip = self.cleaned_data.get('ip_address')
        connection_type = self.cleaned_data.get('connection_type')

        if connection_type == 'tcp' and not ip:
            raise forms.ValidationError(_('عنوان IP مطلوب للاتصال عبر TCP/IP'))

        return ip

    def clean(self):
        cleaned_data = super().clean()
        ip_address = cleaned_data.get('ip_address')
        port = cleaned_data.get('port')

        # التحقق من عدم تكرار نفس IP والمنفذ
        if self.company and ip_address and port:
            existing = BiometricDevice.objects.filter(
                company=self.company,
                ip_address=ip_address,
                port=port
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    _('يوجد جهاز آخر بنفس عنوان IP والمنفذ')
                )

        return cleaned_data


class EmployeeBiometricMappingForm(forms.ModelForm):
    """نموذج ربط موظف بجهاز بصمة"""

    class Meta:
        model = EmployeeBiometricMapping
        fields = [
            'employee', 'device', 'device_user_id',
            'is_enrolled', 'is_active', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select select2'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'device_user_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموظف في جهاز البصمة')
            }),
            'is_enrolled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات')
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

        if company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

            self.fields['device'].queryset = BiometricDevice.objects.filter(
                company=company, is_active=True
            )
            self.fields['device'].required = False

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        device = cleaned_data.get('device')
        device_user_id = cleaned_data.get('device_user_id')

        if self.company and employee and device_user_id:
            # التحقق من عدم تكرار الربط
            existing = EmployeeBiometricMapping.objects.filter(
                company=self.company,
                employee=employee,
                device=device
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    _('هذا الموظف مرتبط مسبقاً بهذا الجهاز')
                )

            # التحقق من عدم تكرار رقم المستخدم في نفس الجهاز
            if device:
                existing_id = EmployeeBiometricMapping.objects.filter(
                    device=device,
                    device_user_id=device_user_id
                )
                if self.instance.pk:
                    existing_id = existing_id.exclude(pk=self.instance.pk)

                if existing_id.exists():
                    raise forms.ValidationError(
                        _('رقم المستخدم %(id)s مستخدم مسبقاً في هذا الجهاز') % {'id': device_user_id}
                    )

        return cleaned_data


class BiometricMappingBulkForm(forms.Form):
    """نموذج ربط مجموعة موظفين"""

    device = forms.ModelChoiceField(
        queryset=BiometricDevice.objects.none(),
        label=_('الجهاز'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.none(),
        label=_('الموظفين'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select select2', 'size': 10})
    )

    start_id = forms.IntegerField(
        label=_('رقم البداية'),
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)

        if company:
            self.fields['device'].queryset = BiometricDevice.objects.filter(
                company=company, is_active=True
            )

            # الموظفين الذين ليس لديهم ربط بعد
            mapped_employees = EmployeeBiometricMapping.objects.filter(
                company=company
            ).values_list('employee_id', flat=True)

            self.fields['employees'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).exclude(id__in=mapped_employees).order_by('first_name', 'last_name')


class BiometricLogFilterForm(forms.Form):
    """نموذج فلترة سجلات البصمة"""

    device = forms.ModelChoiceField(
        queryset=BiometricDevice.objects.none(),
        label=_('الجهاز'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        label=_('الموظف'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    from_date = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    to_date = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    punch_type = forms.ChoiceField(
        choices=[('', _('الكل'))] + list(BiometricDevice.STATUS_CHOICES),
        label=_('نوع البصمة'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_processed = forms.ChoiceField(
        choices=[
            ('', _('الكل')),
            ('yes', _('معالجة')),
            ('no', _('غير معالجة'))
        ],
        label=_('حالة المعالجة'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)

        if company:
            self.fields['device'].queryset = BiometricDevice.objects.filter(
                company=company
            )
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            )

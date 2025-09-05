# apps/core/forms/numbering_forms.py
"""
نماذج تسلسل الترقيم
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import NumberingSequence


class NumberingSequenceForm(forms.ModelForm):
    """نموذج تعديل تسلسل الترقيم"""

    class Meta:
        model = NumberingSequence
        fields = [
            'document_type', 'prefix', 'suffix', 'next_number', 'padding',
            'yearly_reset', 'include_year', 'include_month', 'separator'
        ]
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: INV, PO, JV'),
                'maxlength': 20
            }),
            'suffix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اللاحقة (اختياري)'),
                'maxlength': 20
            }),
            'next_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'padding': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'value': 6
            }),
            'yearly_reset': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_year': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_month': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'separator': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 1,
                'value': '/'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.document_type = kwargs.pop('document_type', None)
        super().__init__(*args, **kwargs)

        # تخصيص التسميات
        self.fields['document_type'].label = _('نوع المستند')
        self.fields['prefix'].label = _('البادئة')
        self.fields['suffix'].label = _('اللاحقة')
        self.fields['next_number'].label = _('الرقم التالي')
        self.fields['padding'].label = _('عدد الأصفار')
        self.fields['yearly_reset'].label = _('إعادة ترقيم سنوياً')
        self.fields['include_year'].label = _('تضمين السنة')
        self.fields['include_month'].label = _('تضمين الشهر')
        self.fields['separator'].label = _('الفاصل')

        # إذا كان هناك نوع مستند محدد، اجعل الحقل للقراءة فقط
        if self.document_type:
            self.fields['document_type'].initial = self.document_type
            self.fields['document_type'].widget.attrs['readonly'] = True

        # help texts
        self.fields['prefix'].help_text = _('البادئة التي تظهر في بداية الرقم')
        self.fields['suffix'].help_text = _('اللاحقة التي تظهر في نهاية الرقم (اختياري)')
        self.fields['next_number'].help_text = _('الرقم التالي في التسلسل')
        self.fields['padding'].help_text = _('عدد الأصفار قبل الرقم (مثال: 6 = 000001)')
        self.fields['yearly_reset'].help_text = _('إعادة ترقيم من 1 كل سنة')
        self.fields['include_year'].help_text = _('إضافة السنة في الرقم')
        self.fields['include_month'].help_text = _('إضافة الشهر في الرقم')
        self.fields['separator'].help_text = _('الرمز الفاصل بين أجزاء الرقم')

    def clean_prefix(self):
        """التحقق من البادئة"""
        prefix = self.cleaned_data.get('prefix')
        if prefix:
            # إزالة المسافات والرموز الخاصة
            prefix = prefix.strip().upper()
            if not prefix.replace('_', '').replace('-', '').isalnum():
                raise ValidationError(_('البادئة يجب أن تحتوي على أحرف وأرقام فقط'))
        return prefix

    def clean_suffix(self):
        """التحقق من اللاحقة"""
        suffix = self.cleaned_data.get('suffix')
        if suffix:
            suffix = suffix.strip().upper()
            if not suffix.replace('_', '').replace('-', '').isalnum():
                raise ValidationError(_('اللاحقة يجب أن تحتوي على أحرف وأرقام فقط'))
        return suffix

    def clean_next_number(self):
        """التحقق من الرقم التالي"""
        next_number = self.cleaned_data.get('next_number')
        if next_number is not None and next_number < 1:
            raise ValidationError(_('الرقم التالي يجب أن يكون أكبر من 0'))
        return next_number

    def clean_padding(self):
        """التحقق من عدد الأصفار"""
        padding = self.cleaned_data.get('padding')
        if padding is not None and (padding < 1 or padding > 10):
            raise ValidationError(_('عدد الأصفار يجب أن يكون بين 1 و 10'))
        return padding

    def clean_separator(self):
        """التحقق من الفاصل"""
        separator = self.cleaned_data.get('separator')
        if separator and len(separator) > 1:
            raise ValidationError(_('الفاصل يجب أن يكون رمز واحد فقط'))
        return separator

    def clean(self):
        """التحقق العام من النموذج"""
        cleaned_data = super().clean()

        # إنشاء رقم تجريبي للمعاينة
        if not self.errors:
            try:
                # محاكاة إنشاء رقم
                import datetime
                parts = []

                prefix = cleaned_data.get('prefix', '')
                if prefix:
                    parts.append(prefix)

                if cleaned_data.get('include_year'):
                    parts.append(str(datetime.date.today().year))

                if cleaned_data.get('include_month'):
                    parts.append(f"{datetime.date.today().month:02d}")

                next_number = cleaned_data.get('next_number', 1)
                padding = cleaned_data.get('padding', 6)
                parts.append(str(next_number).zfill(padding))

                suffix = cleaned_data.get('suffix', '')
                if suffix:
                    parts.append(suffix)

                separator = cleaned_data.get('separator', '/')
                preview = separator.join(parts)

                # إضافة المعاينة للبيانات المنظفة
                cleaned_data['preview'] = preview

            except Exception:
                pass

        return cleaned_data

    def save(self, commit=True):
        """حفظ مع إضافة الشركة"""
        instance = super().save(commit=False)

        if self.request:
            if getattr(instance, 'company_id', None) is None:
                instance.company = self.request.current_company

        if commit:
            instance.save()
        return instance
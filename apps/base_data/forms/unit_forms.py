# apps/base_data/forms/unit_forms.py
"""
نماذج وحدات القياس
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import UnitOfMeasure


class UnitOfMeasureForm(forms.ModelForm):
    """نموذج وحدة القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: PCS'),
                'maxlength': '10',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: قطعة'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: Piece')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_code(self):
        """التحقق من عدم تكرار الرمز"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()  # تحويل للأحرف الكبيرة

            # التحقق من عدم التكرار
            qs = UnitOfMeasure.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(_('هذا الرمز مستخدم بالفعل'))

        return code
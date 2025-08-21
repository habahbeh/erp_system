# apps/base_data/forms/warehouse_forms.py
"""
نماذج المستودعات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from ..models import Warehouse

User = get_user_model()


class WarehouseForm(forms.ModelForm):
    """نموذج المستودع"""

    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'location', 'keeper', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('وصف موقع المستودع')
            }),
            'keeper': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة أمناء المخازن حسب الشركة
            self.fields['keeper'].queryset = User.objects.filter(
                company=company,
                is_active=True,
                groups__name__in=['أمناء المخازن', 'المدراء']
            ).distinct()

            # إضافة خيار فارغ
            self.fields['keeper'].empty_label = _('-- اختر أمين المستودع --')

    def clean_code(self):
        """التحقق من عدم تكرار الرمز في نفس الفرع"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()

            # التحقق من عدم التكرار في نفس الفرع
            if self.instance.branch:
                qs = Warehouse.objects.filter(
                    code=code,
                    branch=self.instance.branch
                )
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)

                if qs.exists():
                    raise forms.ValidationError(_('هذا الرمز مستخدم بالفعل في نفس الفرع'))

        return code
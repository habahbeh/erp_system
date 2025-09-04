# apps/core/forms/brand_forms.py
"""
نماذج العلامات التجارية
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import Brand


class BrandForm(forms.ModelForm):
    """نموذج إضافة/تعديل العلامة التجارية"""

    class Meta:
        model = Brand
        fields = [
            'name', 'name_en', 'description', 'logo',
            'website', 'country'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العلامة التجارية'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Brand Name')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف العلامة التجارية')
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('https://example.com')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('بلد المنشأ')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['name_en'].required = False
        self.fields['description'].required = False
        self.fields['logo'].required = False
        self.fields['website'].required = False
        self.fields['country'].required = False

    def clean_name(self):
        """التحقق من عدم تكرار اسم العلامة التجارية"""
        name = self.cleaned_data.get('name')
        if name and self.request:
            company = self.request.current_company
            queryset = Brand.objects.filter(company=company, name=name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الاسم مستخدم مسبقاً'))
        return name

    def clean_website(self):
        """التحقق من صحة رابط الموقع"""
        website = self.cleaned_data.get('website')
        if website:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
        return website

    def save(self, commit=True):
        """حفظ مع إضافة الشركة"""
        instance = super().save(commit=False)

        if self.request:
            if getattr(instance, 'company_id', None) is None:
                instance.company = self.request.current_company
            if getattr(instance, 'created_by_id', None) is None:
                instance.created_by = self.request.user

        if commit:
            instance.save()
        return instance
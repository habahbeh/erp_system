# apps/accounting/forms/account_type_forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import AccountType


class AccountTypeForm(forms.ModelForm):
    """نموذج إنشاء وتعديل أنواع الحسابات"""

    class Meta:
        model = AccountType
        fields = ['code', 'name', 'type_category', 'normal_balance']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # تخصيص الحقول
        self.fields['code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('أدخل رمز نوع الحساب (مثال: AST)'),
            'maxlength': '20'
        })

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('أدخل اسم نوع الحساب')
        })

        self.fields['type_category'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['normal_balance'].widget.attrs.update({
            'class': 'form-select'
        })

        # تحديد التسميات
        self.fields['code'].label = _('الرمز')
        self.fields['name'].label = _('الاسم')
        self.fields['type_category'].label = _('تصنيف الحساب')
        self.fields['normal_balance'].label = _('الرصيد الطبيعي')

    def clean_code(self):
        code = self.cleaned_data['code'].upper()

        # التحقق من عدم تكرار الرمز
        if AccountType.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('رمز نوع الحساب موجود مسبقاً'))

        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if len(name) < 3:
            raise ValidationError(_('يجب أن يكون اسم نوع الحساب 3 أحرف على الأقل'))

        return name


class AccountTypeImportForm(forms.Form):
    """نموذج استيراد أنواع الحسابات من ملف Excel/CSV"""

    file = forms.FileField(
        label=_('ملف الاستيراد'),
        help_text=_('يدعم ملفات Excel (.xlsx, .xls) و CSV (.csv)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    def clean_file(self):
        file = self.cleaned_data['file']

        # التحقق من نوع الملف
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(_('نوع الملف غير مدعوم. يرجى رفع ملف Excel أو CSV'))

        # التحقق من حجم الملف (5MB max)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError(_('حجم الملف كبير جداً. الحد الأقصى 5 ميجابايت'))

        return file
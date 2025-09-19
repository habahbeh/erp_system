# apps/accounting/forms/account_type_forms.py
"""
Account Type Forms - نماذج أنواع الحسابات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ..models import AccountType


class AccountTypeForm(forms.ModelForm):
    """نموذج نوع الحساب"""

    class Meta:
        model = AccountType
        fields = ['code', 'name', 'type_category', 'normal_balance']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز نوع الحساب (مثال: ASSET)',
                'maxlength': '20'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم نوع الحساب'
            }),
            'type_category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'normal_balance': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'code': 'الرمز',
            'name': 'الاسم',
            'type_category': 'التصنيف',
            'normal_balance': 'الرصيد الطبيعي'
        }
        help_texts = {
            'code': 'رمز فريد لنوع الحساب',
            'name': 'اسم وصفي لنوع الحساب',
            'type_category': 'تصنيف نوع الحساب في الميزانية',
            'normal_balance': 'الجانب الطبيعي للرصيد'
        }

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()

        # التحقق من طول الرمز
        if len(code) < 2:
            raise ValidationError('الرمز يجب أن يكون حرفين على الأقل')

        # التحقق من عدم تكرار الرمز
        if AccountType.objects.filter(code=code).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('هذا الرمز مستخدم من قبل')

        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        # التحقق من طول الاسم
        if len(name) < 3:
            raise ValidationError('الاسم يجب أن يكون 3 أحرف على الأقل')

        # التحقق من عدم تكرار الاسم
        if AccountType.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('هذا الاسم مستخدم من قبل')

        return name

    def clean(self):
        cleaned_data = super().clean()
        type_category = cleaned_data.get('type_category')
        normal_balance = cleaned_data.get('normal_balance')

        # التحقق من التطابق المنطقي
        if type_category and normal_balance:
            # الأصول والمصروفات يجب أن تكون مدينة عادة
            if type_category in ['assets', 'expenses'] and normal_balance != 'debit':
                self.add_error('normal_balance',
                               'الأصول والمصروفات عادة تكون مدينة الطبيعة')

            # الخصوم وحقوق الملكية والإيرادات يجب أن تكون دائنة عادة
            elif type_category in ['liabilities', 'equity', 'revenue'] and normal_balance != 'credit':
                self.add_error('normal_balance',
                               'الخصوم وحقوق الملكية والإيرادات عادة تكون دائنة الطبيعة')

        return cleaned_data


class AccountTypeImportForm(forms.Form):
    """نموذج استيراد أنواع الحسابات"""

    file = forms.FileField(
        label=_('ملف الاستيراد'),
        help_text=_('يدعم ملفات Excel (.xlsx, .xls) و CSV (.csv)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    update_existing = forms.BooleanField(
        label=_('تحديث الأنواع الموجودة'),
        help_text=_('في حالة وجود نوع بنفس الرمز، سيتم تحديث بياناته'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        file = self.cleaned_data['file']

        # التحقق من نوع الملف
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError('نوع الملف غير مدعوم. استخدم .xlsx, .xls, أو .csv')

        # التحقق من حجم الملف (5 ميجا كحد أقصى)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('حجم الملف كبير جداً. الحد الأقصى 5 ميجابايت')

        return file


class AccountTypeFilterForm(forms.Form):
    """نموذج فلترة أنواع الحسابات"""

    type_category = forms.ChoiceField(
        choices=[('', 'جميع التصنيفات')] + AccountType.ACCOUNT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    normal_balance = forms.ChoiceField(
        choices=[('', 'جميع الأرصدة'), ('debit', 'مدين'), ('credit', 'دائن')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في الرمز أو الاسم'
        })
    )
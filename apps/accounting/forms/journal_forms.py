# apps/accounting/forms/journal_forms.py
"""
نماذج القيود اليومية - محسنة لسهولة الاستخدام
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date
import json

from ..models import (JournalEntry, JournalEntryLine, JournalEntryTemplate, JournalEntryTemplateLine,
                      Account, AccountingPeriod, FiscalYear)
from ..models.account_models import CostCenter
from apps.core.forms import BaseForm


class JournalEntryForm(BaseForm):
    """نموذج القيد اليومي - محسن للاستخدام"""

    class Meta:
        model = JournalEntry
        fields = [
            'entry_date', 'entry_type', 'description', 'reference',
            'template', 'notes'
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'entry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'اكتب بيان القيد هنا...'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم المستند أو المرجع (اختياري)'
            }),
            'template': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_template'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية (اختياري)'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة القوالب حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['template'].queryset = JournalEntryTemplate.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).order_by('display_order', 'name')

        # إضافة خيار فارغ للقالب
        self.fields['template'].empty_label = "اختر قالب (اختياري)"

        # تحسين labels
        self.fields['entry_date'].label = "تاريخ القيد"
        self.fields['entry_type'].label = "نوع القيد"
        self.fields['description'].label = "بيان القيد"
        self.fields['reference'].label = "المرجع"
        self.fields['template'].label = "قالب القيد"
        self.fields['notes'].label = "ملاحظات"

    def clean(self):
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('entry_date')

        # التحقق من أن التاريخ ليس في المستقبل
        if entry_date and entry_date > date.today():
            raise ValidationError({
                'entry_date': _('لا يمكن أن يكون تاريخ القيد في المستقبل')
            })

        return cleaned_data


class JournalEntryLineForm(forms.ModelForm):
    """نموذج سطر القيد - محسن للإدخال السريع"""

    account_search = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن الحساب...',
            'autocomplete': 'off'
        }),
        label="الحساب",
        required=False
    )

    class Meta:
        model = JournalEntryLine
        fields = [
            'account', 'description', 'debit_amount', 'credit_amount',
            'reference', 'cost_center'
        ]
        widgets = {
            'account': forms.HiddenInput(),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'وصف العملية'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end amount-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end amount-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مرجع (اختياري)'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-select cost-center-select',
                'data-placeholder': 'اختر مركز التكلفة (اختياري)'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة مراكز التكلفة حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).order_by('code')

        # إضافة خيار فارغ لمركز التكلفة
        self.fields['cost_center'].empty_label = "-- اختر مركز التكلفة (اختياري) --"

        # إذا كان هناك instance، اعرض اسم الحساب
        if self.instance and self.instance.account_id:
            self.fields['account_search'].initial = f"{self.instance.account.code} - {self.instance.account.name}"

    def clean(self):
        cleaned_data = super().clean()
        debit_amount = cleaned_data.get('debit_amount', 0)
        credit_amount = cleaned_data.get('credit_amount', 0)

        # التحقق من المبالغ
        if debit_amount and credit_amount:
            raise ValidationError(_('لا يمكن إدخال مبلغ في المدين والدائن معاً'))

        if not debit_amount and not credit_amount:
            raise ValidationError(_('يجب إدخال مبلغ في المدين أو الدائن'))

        return cleaned_data


class JournalEntryTemplateForm(forms.ModelForm):
    """نموذج قالب القيد اليومي"""

    class Meta:
        model = JournalEntryTemplate
        fields = ['name', 'code', 'description', 'entry_type', 'default_description',
                  'default_reference', 'category', 'auto_balance', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم القالب (مثال: قيد مصروف إداري)'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز القالب (اختياري)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف القالب واستخداماته...'
            }),
            'entry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'البيان الافتراضي للقيود المنشأة من هذا القالب'
            }),
            'default_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المرجع الافتراضي (اختياري)'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'فئة القالب للتصنيف (اختياري)'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'auto_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # إعدادات افتراضية
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['display_order'].initial = 0

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()

        if code and self.request and hasattr(self.request, 'current_company'):
            # التحقق من عدم تكرار الرمز
            existing = JournalEntryTemplate.objects.filter(
                code=code,
                company=self.request.current_company
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('رمز القالب موجود مسبقاً')

        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if self.request and hasattr(self.request, 'current_company'):
            # التحقق من عدم تكرار الاسم
            existing = JournalEntryTemplate.objects.filter(
                name=name,
                company=self.request.current_company
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('اسم القالب موجود مسبقاً')

        return name


class JournalEntryTemplateLineForm(forms.ModelForm):
    """نموذج سطر قالب القيد"""

    class Meta:
        model = JournalEntryTemplateLine
        fields = ['account', 'description', 'debit_amount', 'credit_amount',
                  'reference', 'default_cost_center', 'is_required', 'amount_editable']
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select account-select',
                'data-placeholder': 'اختر الحساب'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'البيان (سيستخدم البيان الافتراضي إذا ترك فارغاً)'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المرجع (اختياري)'
            }),
            'default_cost_center': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختر مركز التكلفة (اختياري)'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'amount_editable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة الحسابات والمراكز للشركة الحالية
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['account'].queryset = Account.objects.filter(
                company=self.request.current_company,
                accept_entries=True,
                is_suspended=False
            ).order_by('code')

            self.fields['default_cost_center'].queryset = CostCenter.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).order_by('code')

        # إعدادات افتراضية
        self.fields['account'].empty_label = "-- اختر الحساب --"
        self.fields['default_cost_center'].empty_label = "-- اختر مركز التكلفة (اختياري) --"

        if not self.instance.pk:
            self.fields['is_required'].initial = True
            self.fields['amount_editable'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        debit_amount = cleaned_data.get('debit_amount', 0) or 0
        credit_amount = cleaned_data.get('credit_amount', 0) or 0

        # التحقق من عدم إدخال مبلغ في الجانبين
        if debit_amount > 0 and credit_amount > 0:
            raise ValidationError('لا يمكن إدخال مبلغ في المدين والدائن معاً')

        # يمكن ترك كلا المبلغين صفر للسطور المتغيرة
        return cleaned_data


class JournalEntryTemplateLineFormSet(forms.BaseInlineFormSet):
    """مجموعة نماذج سطور قالب القيد"""

    def clean(self):
        """التحقق من صحة القالب كاملاً"""
        if any(self.errors):
            return

        forms_data = []
        total_debit = 0
        total_credit = 0
        line_number = 1

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                form.cleaned_data['line_number'] = line_number
                forms_data.append(form.cleaned_data)

                total_debit += form.cleaned_data.get('debit_amount', 0) or 0
                total_credit += form.cleaned_data.get('credit_amount', 0) or 0
                line_number += 1

        # التحقق من وجود سطور
        if not forms_data:
            raise ValidationError('يجب إضافة سطر واحد على الأقل للقالب')

        # يمكن أن يكون القالب غير متوازن للسطور المتغيرة
        # لكن نحذر المستخدم
        if total_debit != total_credit and total_debit > 0 and total_credit > 0:
            # لا نرفع خطأ، فقط تحذير في الواجهة
            pass


class JournalEntryTemplateFilterForm(forms.Form):
    """نموذج فلترة قوالب القيود"""

    entry_type = forms.ChoiceField(
        choices=[('', 'جميع الأنواع')] + JournalEntryTemplate._meta.get_field('entry_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    category = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'فئة القالب'
        })
    )

    status = forms.ChoiceField(
        choices=[
            ('', 'جميع الحالات'),
            ('active', 'نشطة'),
            ('inactive', 'غير نشطة')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في اسم أو رمز القالب'
        })
    )


class UseTemplateForm(forms.Form):
    """نموذج استخدام قالب لإنشاء قيد"""

    template = forms.ModelChoiceField(
        queryset=JournalEntryTemplate.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'اختر القالب'
        }),
        label='القالب'
    )

    entry_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='تاريخ القيد'
    )

    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'سيستخدم البيان الافتراضي من القالب إذا ترك فارغاً'
        }),
        label='البيان'
    )

    reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'المرجع (اختياري)'
        }),
        label='المرجع'
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            self.fields['template'].queryset = JournalEntryTemplate.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).order_by('display_order', 'name')

        self.fields['template'].empty_label = "-- اختر القالب --"


# FormSet للسطور
JournalEntryLineFormSet = forms.modelformset_factory(
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,  # سطرين فارغين بشكل افتراضي
    can_delete=True,
    can_order=True
)


class QuickJournalEntryForm(forms.Form):
    """نموذج سريع للقيود البسيطة (سطرين فقط)"""

    entry_date = forms.DateField(
        label="التاريخ",
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_entry_date'
        })
    )

    description = forms.CharField(
        label="البيان",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'بيان القيد',
            'id': 'id_description'
        })
    )

    # السطر الأول (مدين)
    debit_account = forms.IntegerField(
        label="الحساب المدين",
        widget=forms.HiddenInput(attrs={'id': 'id_debit_account'})
    )

    # السطر الثاني (دائن)
    credit_account = forms.IntegerField(
        label="الحساب الدائن",
        widget=forms.HiddenInput(attrs={'id': 'id_credit_account'})
    )

    # المبلغ
    amount = forms.DecimalField(
        label="المبلغ",
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-end',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01',
            'id': 'id_amount'
        })
    )

    reference = forms.CharField(
        label="المرجع",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم المستند (اختياري)',
            'id': 'id_reference'
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        kwargs.pop('instance', None)  # إزالة instance إذا تم تمريره
        super().__init__(*args, **kwargs)

    def clean_debit_account(self):
        account_id = self.cleaned_data.get('debit_account')
        if not account_id:
            raise forms.ValidationError('يجب اختيار الحساب المدين')

        try:
            account = Account.objects.get(
                id=account_id,
                company=self.request.current_company,
                accept_entries=True,
                is_suspended=False
            )
            return account
        except Account.DoesNotExist:
            raise forms.ValidationError('الحساب المدين غير موجود أو غير صالح')

    def clean_credit_account(self):
        account_id = self.cleaned_data.get('credit_account')
        if not account_id:
            raise forms.ValidationError('يجب اختيار الحساب الدائن')

        try:
            account = Account.objects.get(
                id=account_id,
                company=self.request.current_company,
                accept_entries=True,
                is_suspended=False
            )
            return account
        except Account.DoesNotExist:
            raise forms.ValidationError('الحساب الدائن غير موجود أو غير صالح')

    def clean(self):
        cleaned_data = super().clean()
        debit_account = cleaned_data.get('debit_account')
        credit_account = cleaned_data.get('credit_account')

        if debit_account and credit_account and debit_account.id == credit_account.id:
            raise forms.ValidationError('لا يمكن أن يكون الحساب المدين والدائن نفس الحساب')

        return cleaned_data
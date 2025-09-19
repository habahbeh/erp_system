# apps/accounting/forms/journal_forms.py
"""
نماذج القيود اليومية - محسنة لسهولة الاستخدام
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date
import json

from ..models import JournalEntry, JournalEntryLine, JournalEntryTemplate, Account
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
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة مراكز التكلفة حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            from ..models import CostCenter
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

        # إضافة خيار فارغ لمركز التكلفة
        self.fields['cost_center'].empty_label = "بدون مركز تكلفة"

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


class JournalEntryTemplateForm(BaseForm):
    """نموذج قالب القيد"""

    class Meta:
        model = JournalEntryTemplate
        fields = ['name', 'description', 'entry_type', 'default_description', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم القالب'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'وصف القالب'
            }),
            'entry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'البيان الافتراضي للقيد'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }


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
            'class': 'form-control'
        })
    )

    description = forms.CharField(
        label="البيان",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'بيان القيد'
        })
    )

    # السطر الأول (مدين)
    debit_account_search = forms.CharField(
        label="الحساب المدين",
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن الحساب المدين...'
        })
    )
    debit_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.HiddenInput()
    )

    # السطر الثاني (دائن)
    credit_account_search = forms.CharField(
        label="الحساب الدائن",
        widget=forms.TextInput(attrs={
            'class': 'form-control account-autocomplete',
            'placeholder': 'ابحث عن الحساب الدائن...'
        })
    )
    credit_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.HiddenInput()
    )

    # المبلغ
    amount = forms.DecimalField(
        label="المبلغ",
        max_digits=15,
        decimal_places=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-end',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        })
    )

    reference = forms.CharField(
        label="المرجع",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم المستند (اختياري)'
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة الحسابات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            accounts = Account.objects.filter(
                company=self.request.current_company,
                accept_entries=True,
                is_suspended=False
            )
            self.fields['debit_account'].queryset = accounts
            self.fields['credit_account'].queryset = accounts

    def clean(self):
        cleaned_data = super().clean()
        debit_account = cleaned_data.get('debit_account')
        credit_account = cleaned_data.get('credit_account')

        if debit_account and credit_account and debit_account == credit_account:
            raise ValidationError('لا يمكن أن يكون الحساب المدين والدائن نفس الحساب')

        return cleaned_data

    def save(self, request):
        """حفظ القيد السريع"""
        from ..models import JournalEntry, JournalEntryLine

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=request.current_company,
            branch=request.current_branch,
            entry_date=self.cleaned_data['entry_date'],
            description=self.cleaned_data['description'],
            reference=self.cleaned_data.get('reference', ''),
            entry_type='manual',
            created_by=request.user
        )

        amount = self.cleaned_data['amount']

        # سطر المدين
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=self.cleaned_data['debit_account'],
            description=self.cleaned_data['description'],
            debit_amount=amount,
            credit_amount=0,
            currency=self.cleaned_data['debit_account'].currency,
            reference=self.cleaned_data.get('reference', '')
        )

        # سطر الدائن
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=self.cleaned_data['credit_account'],
            description=self.cleaned_data['description'],
            debit_amount=0,
            credit_amount=amount,
            currency=self.cleaned_data['credit_account'].currency,
            reference=self.cleaned_data.get('reference', '')
        )

        return journal_entry
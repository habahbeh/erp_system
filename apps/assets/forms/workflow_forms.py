# apps/assets/forms/workflow_forms.py
"""
نماذج سير العمل والموافقات
"""

from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
from ..models import (
    ApprovalWorkflow,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalHistory,
)

User = get_user_model()


class ApprovalWorkflowForm(forms.ModelForm):
    """
    نموذج إنشاء/تعديل سير عمل الموافقات
    """

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'name',
            'code',
            'document_type',
            'description',
            'is_active',
            'is_sequential',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم سير العمل',
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز فريد',
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف سير العمل...',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_sequential': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'اسم سير العمل',
            'code': 'الرمز',
            'document_type': 'نوع المستند',
            'description': 'الوصف',
            'is_active': 'نشط',
            'is_sequential': 'تسلسلي (يتطلب الموافقة بالترتيب)',
        }


class ApprovalLevelForm(forms.ModelForm):
    """
    نموذج إضافة/تعديل مستوى موافقة
    """

    class Meta:
        model = ApprovalLevel
        fields = [
            'workflow',
            'level_order',
            'name',
            'approver_role',
            'amount_from',
            'amount_to',
            'is_required',
            'expected_response_hours',
        ]
        widgets = {
            'workflow': forms.Select(attrs={
                'class': 'form-select',
            }),
            'level_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: مدير القسم',
            }),
            'approver_role': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'اختر الدور...',
            }),
            'amount_from': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
            }),
            'amount_to': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'expected_response_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '24',
            }),
        }
        labels = {
            'workflow': 'سير العمل',
            'level_order': 'رقم المستوى',
            'name': 'اسم المستوى',
            'approver_role': 'دور المعتمد',
            'amount_from': 'الحد الأدنى للمبلغ',
            'amount_to': 'الحد الأقصى للمبلغ',
            'is_required': 'مطلوب',
            'expected_response_hours': 'وقت الاستجابة المتوقع (ساعات)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تحسين عرض المستخدمين
        self.fields['approver'].queryset = User.objects.filter(is_active=True)
        self.fields['approver'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"

        self.fields['escalate_to'].queryset = User.objects.filter(is_active=True)
        self.fields['escalate_to'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        auto_escalate = cleaned_data.get('auto_escalate')
        escalate_to = cleaned_data.get('escalate_to')

        if min_amount and max_amount:
            if min_amount > max_amount:
                raise forms.ValidationError(
                    'الحد الأدنى يجب أن يكون أقل من الحد الأقصى'
                )

        if auto_escalate and not escalate_to:
            raise forms.ValidationError(
                'يجب تحديد المستخدم للتصعيد إليه عند تفعيل التصعيد التلقائي'
            )

        return cleaned_data


# Formset لإدارة مستويات الموافقة من داخل Workflow
ApprovalLevelFormSet = inlineformset_factory(
    ApprovalWorkflow,
    ApprovalLevel,
    form=ApprovalLevelForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class ApprovalRequestForm(forms.ModelForm):
    """
    نموذج إنشاء طلب موافقة
    """

    class Meta:
        model = ApprovalRequest
        fields = [
            'workflow',
            'document_type',
            'document_id',
            'amount',
            'description',
            'notes',
        ]
        widgets = {
            'workflow': forms.Select(attrs={
                'class': 'form-select',
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'document_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'معرف المستند',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'تفاصيل الطلب...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية...',
            }),
        }
        labels = {
            'workflow': 'سير العمل',
            'document_type': 'نوع المستند',
            'document_id': 'رقم المستند',
            'amount': 'المبلغ',
            'description': 'الوصف',
            'notes': 'ملاحظات',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة Workflows النشطة فقط
        self.fields['workflow'].queryset = ApprovalWorkflow.objects.filter(is_active=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.requester = self.user
        if commit:
            instance.save()
        return instance


class ApprovalActionForm(forms.Form):
    """
    نموذج الموافقة/الرفض على الطلب
    """
    ACTION_CHOICES = [
        ('approve', 'موافقة'),
        ('reject', 'رفض'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label='الإجراء'
    )

    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات إضافية (اختياري)...',
        }),
        label='الملاحظات'
    )

    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
        }),
        label='مرفق'
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comments = cleaned_data.get('comments')

        # يجب إضافة ملاحظات عند الرفض
        if action == 'reject' and not comments:
            raise forms.ValidationError(
                'يجب إضافة ملاحظات عند رفض الطلب'
            )

        return cleaned_data


class ApprovalRequestFilterForm(forms.Form):
    """
    نموذج فلترة طلبات الموافقة
    """
    STATUS_CHOICES = [
        ('', 'كل الحالات'),
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]

    PRIORITY_CHOICES = [
        ('', 'كل الأولويات'),
        ('low', 'منخفضة'),
        ('normal', 'عادية'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='الحالة'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='الأولوية'
    )

    workflow = forms.ModelChoiceField(
        queryset=ApprovalWorkflow.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='سير العمل',
        empty_label='كل سيرات العمل'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='من تاريخ'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='إلى تاريخ'
    )

    requester = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2',
        }),
        label='مقدم الطلب',
        empty_label='الكل'
    )


class QuickApprovalForm(forms.Form):
    """
    نموذج الموافقة السريعة (من Dashboard)
    """
    request_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    comments = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'ملاحظات (اختياري)...',
        })
    )


class BulkApprovalForm(forms.Form):
    """
    نموذج الموافقة على عدة طلبات دفعة واحدة
    """
    request_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

    action = forms.ChoiceField(
        choices=[
            ('approve', 'موافقة على الكل'),
            ('reject', 'رفض الكل'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='الإجراء'
    )

    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'ملاحظات للجميع...',
        }),
        label='الملاحظات'
    )

    def clean_request_ids(self):
        data = self.cleaned_data['request_ids']
        try:
            ids = [int(x) for x in data.split(',') if x.strip()]
            if not ids:
                raise forms.ValidationError('يجب تحديد طلب واحد على الأقل')
            return ids
        except ValueError:
            raise forms.ValidationError('معرفات الطلبات غير صحيحة')


class DelegateApprovalForm(forms.Form):
    """
    نموذج تفويض الموافقة لشخص آخر
    """
    delegate_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select select2',
        }),
        label='التفويض إلى',
        help_text='اختر المستخدم الذي سيتم تفويضه بالموافقة'
    )

    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'سبب التفويض...',
        }),
        label='السبب'
    )

    valid_until = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        }),
        label='صالح حتى',
        help_text='اترك فارغاً للتفويض الدائم'
    )

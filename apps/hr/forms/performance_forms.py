# apps/hr/forms/performance_forms.py
"""
نماذج التقييم والأداء
Performance Evaluation Forms
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.hr.models import (
    PerformancePeriod,
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationDetail,
    PerformanceGoal,
    PerformanceNote,
    Employee,
    Department,
)


class PerformancePeriodForm(forms.ModelForm):
    """نموذج فترة التقييم"""

    class Meta:
        model = PerformancePeriod
        fields = [
            'name', 'period_type', 'year', 'start_date', 'end_date',
            'evaluation_start', 'evaluation_end', 'status', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الفترة')
            }),
            'period_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2100
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'evaluation_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'evaluation_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        eval_start = cleaned_data.get('evaluation_start')
        eval_end = cleaned_data.get('evaluation_end')

        if start_date and end_date and start_date > end_date:
            raise ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ النهاية'))

        if eval_start and eval_end and eval_start > eval_end:
            raise ValidationError(_('تاريخ بداية التقييم يجب أن يكون قبل تاريخ نهاية التقييم'))

        return cleaned_data


class PerformanceCriteriaForm(forms.ModelForm):
    """نموذج معايير التقييم"""

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 5
        }),
        label=_('الأقسام المطبق عليها')
    )

    class Meta:
        model = PerformanceCriteria
        fields = [
            'name', 'name_en', 'description', 'criteria_type', 'weight',
            'max_score', 'is_required', 'applies_to_all', 'departments', 'display_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المعيار بالعربية')
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المعيار بالإنجليزية')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف المعيار')
            }),
            'criteria_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'applies_to_all': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['departments'].queryset = Department.objects.filter(
                company=company, is_active=True
            )


class PerformanceEvaluationForm(forms.ModelForm):
    """نموذج تقييم الأداء"""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('الموظف')
    )

    period = forms.ModelChoiceField(
        queryset=PerformancePeriod.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('فترة التقييم')
    )

    class Meta:
        model = PerformanceEvaluation
        fields = [
            'employee', 'period', 'manager_comments', 'strengths',
            'improvement_areas', 'goals_next_period'
        ]
        widgets = {
            'manager_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('تعليقات المدير')
            }),
            'strengths': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('نقاط القوة')
            }),
            'improvement_areas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('مجالات التحسين')
            }),
            'goals_next_period': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('أهداف الفترة القادمة')
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')
            self.fields['period'].queryset = PerformancePeriod.objects.filter(
                company=company, is_active=True
            ).exclude(status='closed')


class PerformanceEvaluationDetailForm(forms.ModelForm):
    """نموذج تفاصيل التقييم"""

    class Meta:
        model = PerformanceEvaluationDetail
        fields = ['self_score', 'manager_score', 'self_comments', 'manager_comments']
        widgets = {
            'self_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1
            }),
            'manager_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1
            }),
            'self_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات الموظف')
            }),
            'manager_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات المدير')
            }),
        }


class SelfEvaluationForm(forms.Form):
    """نموذج التقييم الذاتي"""

    def __init__(self, *args, criteria_list=None, **kwargs):
        super().__init__(*args, **kwargs)

        if criteria_list:
            for criteria in criteria_list:
                self.fields[f'score_{criteria.id}'] = forms.DecimalField(
                    label=criteria.name,
                    min_value=0,
                    max_value=criteria.max_score,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': 0,
                        'max': criteria.max_score,
                        'step': 0.1,
                        'data-criteria-id': criteria.id
                    }),
                    required=criteria.is_required,
                    help_text=f'{_("الحد الأقصى")}: {criteria.max_score} | {_("الوزن")}: {criteria.weight}%'
                )
                self.fields[f'comment_{criteria.id}'] = forms.CharField(
                    label=_('ملاحظات'),
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                        'placeholder': _('ملاحظاتك على هذا المعيار')
                    })
                )


class ManagerEvaluationForm(forms.Form):
    """نموذج تقييم المدير"""

    def __init__(self, *args, criteria_list=None, **kwargs):
        super().__init__(*args, **kwargs)

        if criteria_list:
            for criteria in criteria_list:
                self.fields[f'score_{criteria.id}'] = forms.DecimalField(
                    label=criteria.name,
                    min_value=0,
                    max_value=criteria.max_score,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': 0,
                        'max': criteria.max_score,
                        'step': 0.1,
                        'data-criteria-id': criteria.id
                    }),
                    required=criteria.is_required,
                    help_text=f'{_("الحد الأقصى")}: {criteria.max_score} | {_("الوزن")}: {criteria.weight}%'
                )
                self.fields[f'comment_{criteria.id}'] = forms.CharField(
                    label=_('ملاحظات المدير'),
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                        'placeholder': _('ملاحظاتك كمدير على هذا المعيار')
                    })
                )


class PerformanceGoalForm(forms.ModelForm):
    """نموذج أهداف الأداء"""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('الموظف')
    )

    period = forms.ModelChoiceField(
        queryset=PerformancePeriod.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('فترة التقييم')
    )

    class Meta:
        model = PerformanceGoal
        fields = [
            'employee', 'period', 'title', 'description', 'key_results',
            'priority', 'status', 'weight', 'target_value', 'achieved_value',
            'start_date', 'due_date', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان الهدف')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف الهدف')
            }),
            'key_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('النتائج الرئيسية المتوقعة (OKRs)')
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'target_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.01,
                'placeholder': _('القيمة المستهدفة')
            }),
            'achieved_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.01,
                'placeholder': _('القيمة المحققة')
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')
            self.fields['period'].queryset = PerformancePeriod.objects.filter(
                company=company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')

        if start_date and due_date and start_date > due_date:
            raise ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ الاستحقاق'))

        return cleaned_data


class PerformanceNoteForm(forms.ModelForm):
    """نموذج ملاحظات الأداء"""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('الموظف')
    )

    class Meta:
        model = PerformanceNote
        fields = [
            'employee', 'note_type', 'title', 'description', 'date',
            'is_visible_to_employee'
        ]
        widgets = {
            'note_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان الملاحظة')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('تفاصيل الملاحظة')
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_visible_to_employee': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')


class GoalProgressUpdateForm(forms.Form):
    """نموذج تحديث تقدم الهدف"""

    achieved_value = forms.DecimalField(
        label=_('القيمة المحققة'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01
        })
    )

    progress_note = forms.CharField(
        label=_('ملاحظة التقدم'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('أضف ملاحظة حول التقدم')
        })
    )

    status = forms.ChoiceField(
        label=_('الحالة'),
        choices=[
            ('in_progress', _('قيد التنفيذ')),
            ('completed', _('مكتمل')),
            ('cancelled', _('ملغي')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class EvaluationApprovalForm(forms.Form):
    """نموذج اعتماد التقييم"""

    action = forms.ChoiceField(
        label=_('الإجراء'),
        choices=[
            ('approve', _('اعتماد')),
            ('reject', _('رفض')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    comments = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('أضف ملاحظاتك')
        })
    )


class BulkEvaluationForm(forms.Form):
    """نموذج إنشاء تقييمات جماعية"""

    period = forms.ModelChoiceField(
        queryset=PerformancePeriod.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('فترة التقييم')
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('القسم')
    )

    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'multiple': 'multiple'
        }),
        label=_('الموظفين')
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['period'].queryset = PerformancePeriod.objects.filter(
                company=company, is_active=True, status='active'
            )
            self.fields['department'].queryset = Department.objects.filter(
                company=company, is_active=True
            )
            self.fields['employees'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')

# apps/hr/forms/training_forms.py
"""
نماذج التدريب والتطوير
Training & Development Forms
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.hr.models import (
    TrainingCategory,
    TrainingProvider,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRequest,
    TrainingPlan,
    TrainingPlanItem,
    TrainingFeedback,
    Employee,
    Department,
    JobTitle,
)


class TrainingCategoryForm(forms.ModelForm):
    """نموذج فئة التدريب"""

    parent = forms.ModelChoiceField(
        queryset=TrainingCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة الأم')
    )

    class Meta:
        model = TrainingCategory
        fields = ['name', 'name_en', 'description', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الفئة بالعربية')
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الفئة بالإنجليزية')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف الفئة')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['parent'].queryset = TrainingCategory.objects.filter(
                company=company, is_active=True
            )


class TrainingProviderForm(forms.ModelForm):
    """نموذج مزود التدريب"""

    class Meta:
        model = TrainingProvider
        fields = [
            'name', 'provider_type', 'contact_person', 'phone', 'email',
            'website', 'address', 'specializations', 'rating', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم مزود التدريب')
            }),
            'provider_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم جهة الاتصال')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('رابط الموقع الإلكتروني')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('العنوان')
            }),
            'specializations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('مجالات التدريب التي يقدمها')
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 5,
                'step': 0.1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TrainingCourseForm(forms.ModelForm):
    """نموذج الدورة التدريبية"""

    category = forms.ModelChoiceField(
        queryset=TrainingCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة')
    )

    provider = forms.ModelChoiceField(
        queryset=TrainingProvider.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('مزود التدريب')
    )

    trainer_employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('المدرب (موظف)')
    )

    target_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 5
        }),
        label=_('الأقسام المستهدفة')
    )

    target_job_titles = forms.ModelMultipleChoiceField(
        queryset=JobTitle.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 5
        }),
        label=_('المسميات الوظيفية المستهدفة')
    )

    class Meta:
        model = TrainingCourse
        fields = [
            'code', 'name', 'name_en', 'description', 'objectives',
            'category', 'provider', 'course_type', 'delivery_method', 'status',
            'start_date', 'end_date', 'duration_hours', 'duration_days',
            'location', 'max_participants', 'min_participants',
            'cost_per_participant', 'total_budget',
            'trainer_name', 'trainer_employee',
            'prerequisites', 'materials',
            'target_departments', 'target_job_titles',
            'certificate_issued', 'notes', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز الدورة')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الدورة بالعربية')
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الدورة بالإنجليزية')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف الدورة')
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ما سيتعلمه المتدربون')
            }),
            'course_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مكان الدورة')
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'min_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'cost_per_participant': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'total_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'trainer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المدرب')
            }),
            'prerequisites': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('المتطلبات السابقة')
            }),
            'materials': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('المواد التدريبية')
            }),
            'certificate_issued': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['category'].queryset = TrainingCategory.objects.filter(
                company=company, is_active=True
            )
            self.fields['provider'].queryset = TrainingProvider.objects.filter(
                company=company, is_active=True
            )
            self.fields['trainer_employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            )
            self.fields['target_departments'].queryset = Department.objects.filter(
                company=company, is_active=True
            )
            self.fields['target_job_titles'].queryset = JobTitle.objects.filter(
                company=company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ النهاية'))

        return cleaned_data


class TrainingEnrollmentForm(forms.ModelForm):
    """نموذج تسجيل التدريب"""

    course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الدورة')
    )

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('الموظف')
    )

    nominated_by = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('رشح بواسطة')
    )

    class Meta:
        model = TrainingEnrollment
        fields = [
            'course', 'employee', 'status', 'nominated_by',
            'enrollment_date', 'attendance_percentage', 'score', 'grade',
            'certificate_number', 'certificate_date', 'actual_cost', 'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'enrollment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'attendance_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('التقدير')
            }),
            'certificate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الشهادة')
            }),
            'certificate_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'actual_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['course'].queryset = TrainingCourse.objects.filter(
                company=company, is_active=True
            ).exclude(status='cancelled')
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')
            self.fields['nominated_by'].queryset = Employee.objects.filter(
                company=company, is_active=True
            )


class BulkEnrollmentForm(forms.Form):
    """نموذج تسجيل جماعي"""

    course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الدورة')
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
            self.fields['course'].queryset = TrainingCourse.objects.filter(
                company=company, is_active=True, status='open'
            )
            self.fields['department'].queryset = Department.objects.filter(
                company=company, is_active=True
            )
            self.fields['employees'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')


class TrainingRequestForm(forms.ModelForm):
    """نموذج طلب التدريب"""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2'
        }),
        label=_('الموظف')
    )

    course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الدورة المطلوبة')
    )

    training_category = forms.ModelChoiceField(
        queryset=TrainingCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('فئة التدريب')
    )

    class Meta:
        model = TrainingRequest
        fields = [
            'employee', 'request_type', 'course', 'custom_course_name',
            'training_category', 'justification', 'expected_benefits',
            'preferred_date_from', 'preferred_date_to', 'estimated_cost'
        ]
        widgets = {
            'request_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'custom_course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الدورة إذا لم تكن موجودة')
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('لماذا تحتاج هذا التدريب')
            }),
            'expected_benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ما الفوائد المتوقعة')
            }),
            'preferred_date_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'preferred_date_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company, is_active=True
            ).select_related('department')
            self.fields['course'].queryset = TrainingCourse.objects.filter(
                company=company, is_active=True
            )
            self.fields['training_category'].queryset = TrainingCategory.objects.filter(
                company=company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        custom_course_name = cleaned_data.get('custom_course_name')

        if not course and not custom_course_name:
            raise ValidationError(_('يجب تحديد دورة أو كتابة اسم الدورة المطلوبة'))

        return cleaned_data


class TrainingRequestApprovalForm(forms.Form):
    """نموذج موافقة طلب التدريب"""

    action = forms.ChoiceField(
        label=_('الإجراء'),
        choices=[
            ('approve', _('موافقة')),
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

    rejection_reason = forms.CharField(
        label=_('سبب الرفض'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('سبب الرفض (مطلوب عند الرفض)')
        })
    )


class TrainingPlanForm(forms.ModelForm):
    """نموذج خطة التدريب"""

    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('القسم')
    )

    class Meta:
        model = TrainingPlan
        fields = [
            'name', 'year', 'department', 'status',
            'total_budget', 'allocated_budget', 'objectives', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الخطة')
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2100
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'total_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'allocated_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('أهداف الخطة التدريبية')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['department'].queryset = Department.objects.filter(
                company=company, is_active=True
            )


class TrainingPlanItemForm(forms.ModelForm):
    """نموذج بند خطة التدريب"""

    course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الدورة')
    )

    category = forms.ModelChoiceField(
        queryset=TrainingCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة')
    )

    target_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 4
        }),
        label=_('الأقسام المستهدفة')
    )

    class Meta:
        model = TrainingPlanItem
        fields = [
            'course', 'custom_course_name', 'category',
            'target_employees_count', 'target_departments',
            'priority', 'planned_quarter', 'planned_budget', 'notes'
        ]
        widgets = {
            'custom_course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الدورة إذا غير موجودة')
            }),
            'target_employees_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'planned_quarter': forms.Select(attrs={
                'class': 'form-select'
            }),
            'planned_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['course'].queryset = TrainingCourse.objects.filter(
                company=company, is_active=True
            )
            self.fields['category'].queryset = TrainingCategory.objects.filter(
                company=company, is_active=True
            )
            self.fields['target_departments'].queryset = Department.objects.filter(
                company=company, is_active=True
            )


class TrainingFeedbackForm(forms.ModelForm):
    """نموذج تقييم التدريب"""

    class Meta:
        model = TrainingFeedback
        fields = [
            'content_rating', 'trainer_rating', 'materials_rating',
            'organization_rating', 'relevance_rating', 'overall_rating',
            'strengths', 'improvements', 'knowledge_gained',
            'application_plan', 'would_recommend', 'additional_comments'
        ]
        widgets = {
            'content_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'trainer_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'materials_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'organization_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'relevance_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'overall_rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'strengths': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ما أعجبك في الدورة')
            }),
            'improvements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('مقترحاتك للتحسين')
            }),
            'knowledge_gained': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ما المعرفة والمهارات التي اكتسبتها')
            }),
            'application_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('كيف ستطبق ما تعلمته في عملك')
            }),
            'would_recommend': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'additional_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class CourseFilterForm(forms.Form):
    """نموذج فلترة الدورات"""

    category = forms.ModelChoiceField(
        queryset=TrainingCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الفئة')
    )

    provider = forms.ModelChoiceField(
        queryset=TrainingProvider.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('المزود')
    )

    course_type = forms.ChoiceField(
        required=False,
        choices=[('', _('الكل'))] + list(TrainingCourse.COURSE_TYPE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('نوع الدورة')
    )

    status = forms.ChoiceField(
        required=False,
        choices=[('', _('الكل'))] + list(TrainingCourse.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('الحالة')
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['category'].queryset = TrainingCategory.objects.filter(
                company=company, is_active=True
            )
            self.fields['provider'].queryset = TrainingProvider.objects.filter(
                company=company, is_active=True
            )


class EnrollmentUpdateForm(forms.Form):
    """نموذج تحديث حالة التسجيل"""

    status = forms.ChoiceField(
        label=_('الحالة'),
        choices=TrainingEnrollment.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    attendance_percentage = forms.DecimalField(
        label=_('نسبة الحضور'),
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01
        })
    )

    score = forms.DecimalField(
        label=_('الدرجة'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )

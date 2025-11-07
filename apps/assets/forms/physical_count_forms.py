# apps/assets/forms/physical_count_forms.py
"""
نماذج الجرد الفعلي للأصول
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import datetime

from ..models import (
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine,
    PhysicalCountAdjustment, Asset, AssetCategory, AssetCondition
)
from apps.core.models import Branch, User


class PhysicalCountCycleForm(forms.ModelForm):
    """نموذج دورة الجرد"""

    class Meta:
        model = PhysicalCountCycle
        fields = [
            'name', 'cycle_type',
            'start_date', 'end_date', 'planned_completion_date',
            'branches', 'asset_categories',
            'team_leader', 'team_members',
            'description', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: جرد الربع الأول 2024'
            }),
            'cycle_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'planned_completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'branches': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'asset_categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5',
                'data-placeholder': 'اتركه فارغاً لجميع الفئات'
            }),
            'team_leader': forms.Select(attrs={'class': 'form-select'}),
            'team_members': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['branches'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['asset_categories'].queryset = AssetCategory.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['team_leader'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['team_members'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        planned_completion_date = cleaned_data.get('planned_completion_date')

        # التحقق من التواريخ
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

        if start_date and planned_completion_date:
            if planned_completion_date < start_date:
                raise ValidationError({
                    'planned_completion_date': _('تاريخ الإنجاز المخطط يجب أن يكون بعد تاريخ البداية')
                })

        return cleaned_data


class PhysicalCountForm(forms.ModelForm):
    """نموذج عملية جرد فعلية"""

    class Meta:
        model = PhysicalCount
        fields = [
            'cycle', 'count_date', 'branch', 'location',
            'responsible_team', 'supervisor', 'notes'
        ]
        widgets = {
            'cycle': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'اختياري - للجرد الطارئ'
            }),
            'count_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: المستودع الرئيسي - الطابق الثالث'
            }),
            'responsible_team': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # فقط الدورات الجارية أو في التخطيط
            self.fields['cycle'].queryset = PhysicalCountCycle.objects.filter(
                company=self.company,
                status__in=['planning', 'in_progress'],
                is_active=True
            )
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['responsible_team'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )
            self.fields['supervisor'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )


class PhysicalCountLineForm(forms.ModelForm):
    """نموذج سطر جرد"""

    class Meta:
        model = PhysicalCountLine
        fields = [
            'actual_location', 'actual_condition', 'actual_responsible',
            'notes'
        ]
        widgets = {
            'actual_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الموقع الفعلي للأصل'
            }),
            'actual_condition': forms.Select(attrs={'class': 'form-select'}),
            'actual_responsible': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات عن الأصل'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['actual_condition'].queryset = AssetCondition.objects.filter(
                is_active=True
            )
            self.fields['actual_responsible'].queryset = User.objects.filter(
                company=self.company,
                is_active=True
            )


class BarcodeCountForm(forms.Form):
    """نموذج الجرد بالباركود - للمسح السريع"""

    physical_count_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    barcode = forms.CharField(
        label=_('الباركود'),
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'امسح الباركود أو أدخله يدوياً',
            'autofocus': True,
            'autocomplete': 'off'
        })
    )

    location = forms.CharField(
        label=_('الموقع الفعلي'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الموقع (اختياري)'
        })
    )

    condition = forms.ModelChoiceField(
        queryset=AssetCondition.objects.filter(is_active=True),
        label=_('الحالة'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )

    def __init__(self, *args, **kwargs):
        self.physical_count = kwargs.pop('physical_count', None)
        super().__init__(*args, **kwargs)

        if self.physical_count:
            self.fields['physical_count_id'].initial = self.physical_count.id


class PhysicalCountAdjustmentForm(forms.ModelForm):
    """نموذج تسوية الجرد (للفقد والتلف)"""

    class Meta:
        model = PhysicalCountAdjustment
        fields = [
            'physical_count_line', 'adjustment_type',
            'adjustment_date', 'reason', 'notes'
        ]
        widgets = {
            'physical_count_line': forms.Select(attrs={
                'class': 'form-select'
            }),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'سبب التسوية (مطلوب - مفصل)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.physical_count = kwargs.pop('physical_count', None)
        super().__init__(*args, **kwargs)

        # فقط سطور الجرد التي تحتاج تسوية
        if self.physical_count:
            self.fields['physical_count_line'].queryset = self.physical_count.lines.filter(
                requires_adjustment=True
            )
        elif self.company:
            # جميع السطور التي تحتاج تسوية
            self.fields['physical_count_line'].queryset = PhysicalCountLine.objects.filter(
                physical_count__company=self.company,
                requires_adjustment=True,
                adjustments__isnull=True  # لم تُنشأ لها تسوية بعد
            ).select_related('physical_count', 'asset')

    def clean(self):
        cleaned_data = super().clean()

        adjustment_date = cleaned_data.get('adjustment_date')
        physical_count_line = cleaned_data.get('physical_count_line')
        reason = cleaned_data.get('reason')

        # التحقق من التاريخ
        if adjustment_date and adjustment_date > datetime.date.today():
            raise ValidationError({
                'adjustment_date': _('لا يمكن إنشاء تسوية بتاريخ مستقبلي')
            })

        # التحقق من أن تاريخ التسوية بعد تاريخ الجرد
        if physical_count_line and adjustment_date:
            if adjustment_date < physical_count_line.physical_count.count_date:
                raise ValidationError({
                    'adjustment_date': _('تاريخ التسوية يجب أن يكون بعد أو يساوي تاريخ الجرد')
                })

        # التحقق من السبب
        if not reason or len(reason.strip()) < 20:
            raise ValidationError({
                'reason': _('يجب إدخال سبب مفصل للتسوية (20 حرف على الأقل)')
            })

        return cleaned_data


class CountFilterForm(forms.Form):
    """نموذج فلترة عمليات الجرد"""

    cycle = forms.ModelChoiceField(
        queryset=PhysicalCountCycle.objects.none(),
        required=False,
        empty_label=_('جميع الدورات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        empty_label=_('جميع الفروع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('جميع الحالات'))] + PhysicalCount.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )

    has_variances = forms.BooleanField(
        required=False,
        label=_('التي بها فروقات فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['cycle'].queryset = PhysicalCountCycle.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('-start_date')

            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            )


class AdjustmentFilterForm(forms.Form):
    """نموذج فلترة تسويات الجرد"""

    physical_count = forms.ModelChoiceField(
        queryset=PhysicalCount.objects.none(),
        required=False,
        empty_label=_('جميع عمليات الجرد'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    adjustment_type = forms.ChoiceField(
        choices=[('', _('جميع الأنواع'))] + PhysicalCountAdjustment.ADJUSTMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('جميع الحالات'))] + PhysicalCountAdjustment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )

    posted_only = forms.BooleanField(
        required=False,
        label=_('المرحّلة فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['physical_count'].queryset = PhysicalCount.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('-count_date')


class BulkCountLineUpdateForm(forms.Form):
    """نموذج تحديث جماعي لسطور الجرد"""

    physical_count_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    line_ids = forms.CharField(
        widget=forms.HiddenInput(),
        help_text=_('IDs للسطور المحددة - JSON array')
    )

    action = forms.ChoiceField(
        label=_('الإجراء'),
        choices=[
            ('mark_found', _('وضع علامة موجود')),
            ('mark_not_found', _('وضع علامة مفقود')),
            ('mark_counted', _('وضع علامة مجرد')),
            ('update_location', _('تحديث الموقع')),
            ('update_condition', _('تحديث الحالة')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    new_location = forms.CharField(
        label=_('الموقع الجديد'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'يُستخدم عند اختيار "تحديث الموقع"'
        })
    )

    new_condition = forms.ModelChoiceField(
        queryset=AssetCondition.objects.filter(is_active=True),
        label=_('الحالة الجديدة'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.physical_count = kwargs.pop('physical_count', None)
        super().__init__(*args, **kwargs)

        if self.physical_count:
            self.fields['physical_count_id'].initial = self.physical_count.id

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_location = cleaned_data.get('new_location')
        new_condition = cleaned_data.get('new_condition')

        # التحقق من البيانات المطلوبة حسب الإجراء
        if action == 'update_location' and not new_location:
            raise ValidationError({
                'new_location': _('يجب تحديد الموقع الجديد')
            })

        if action == 'update_condition' and not new_condition:
            raise ValidationError({
                'new_condition': _('يجب تحديد الحالة الجديدة')
            })

        return cleaned_data

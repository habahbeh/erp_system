# apps/accounting/forms/fiscal_forms.py
"""
نماذج السنوات والفترات المالية
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from ..models import FiscalYear, AccountingPeriod


class FiscalYearForm(forms.ModelForm):
    """نموذج السنة المالية"""

    class Meta:
        model = FiscalYear
        fields = ['name', 'code', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم السنة المالية (مثال: السنة المالية 2024)'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رمز السنة (مثال: FY2024)'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # تعيين قيم افتراضية للسنة الجديدة
        if not self.instance.pk:
            current_year = date.today().year
            self.fields['start_date'].initial = date(current_year, 1, 1)
            self.fields['end_date'].initial = date(current_year, 12, 31)
            self.fields['name'].initial = f'السنة المالية {current_year}'
            self.fields['code'].initial = f'FY{current_year}'

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()

        if not self.request or not hasattr(self.request, 'current_company'):
            raise ValidationError('لا توجد شركة محددة')

        # التحقق من عدم تكرار الرمز
        existing = FiscalYear.objects.filter(
            code=code,
            company=self.request.current_company
        ).exclude(pk=self.instance.pk if self.instance else None)

        if existing.exists():
            raise ValidationError('رمز السنة المالية موجود مسبقاً')

        return code

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # التحقق من أن تاريخ النهاية بعد تاريخ البداية
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': 'تاريخ نهاية السنة يجب أن يكون بعد تاريخ البداية'
                })

            # التحقق من أن السنة لا تزيد عن 18 شهر
            if (end_date - start_date).days > 550:
                raise ValidationError('السنة المالية لا يمكن أن تزيد عن 18 شهراً')

            # التحقق من عدم تداخل السنوات المالية
            if self.request and hasattr(self.request, 'current_company'):
                overlapping = FiscalYear.objects.filter(
                    company=self.request.current_company
                ).exclude(pk=self.instance.pk if self.instance else None).filter(
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )

                if overlapping.exists():
                    raise ValidationError('توجد سنة مالية أخرى تتداخل مع هذه الفترة')

        return cleaned_data


class FiscalYearFilterForm(forms.Form):
    """نموذج فلترة السنوات المالية"""

    status = forms.ChoiceField(
        choices=[
            ('', 'جميع الحالات'),
            ('active', 'نشطة'),
            ('closed', 'مقفلة')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في الاسم أو الرمز'
        })
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # إعداد خيارات السنوات
        if request and hasattr(request, 'current_company'):
            years = FiscalYear.objects.filter(
                company=request.current_company
            ).dates('start_date', 'year', order='DESC')

            year_choices = [('', 'جميع السنوات')]
            for year_date in years:
                year_choices.append((year_date.year, str(year_date.year)))

            self.fields['year'].choices = year_choices


class CreatePeriodsForm(forms.Form):
    """نموذج إنشاء فترات محاسبية من السنة المالية"""

    period_type = forms.ChoiceField(
        label='نوع الفترات',
        choices=[
            ('monthly', 'شهرية (12 فترة)'),
            ('quarterly', 'ربع سنوية (4 فترات)'),
            ('semi_annual', 'نصف سنوية (فترتان)'),
            ('annual', 'سنوية (فترة واحدة)')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    create_adjustment_period = forms.BooleanField(
        label='إنشاء فترة تسويات',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_period_type(self):
        period_type = self.cleaned_data['period_type']
        valid_types = ['monthly', 'quarterly', 'semi_annual', 'annual']

        if period_type not in valid_types:
            raise ValidationError('نوع الفترة غير صحيح')

        return period_type


class AccountingPeriodForm(forms.ModelForm):
    """نموذج الفترة المحاسبية"""

    class Meta:
        model = AccountingPeriod
        fields = ['fiscal_year', 'name', 'start_date', 'end_date', 'is_adjustment']
        widgets = {
            'fiscal_year': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الفترة المحاسبية'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'is_adjustment': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة السنوات المالية للشركة الحالية
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(
                company=self.request.current_company,
                is_closed=False
            ).order_by('-start_date')

        # إذا كان هناك fiscal_year محدد مسبقاً
        fiscal_year_id = self.request.GET.get('fiscal_year') if self.request else None
        if fiscal_year_id and not self.instance.pk:
            try:
                fiscal_year = FiscalYear.objects.get(id=fiscal_year_id)
                self.fields['fiscal_year'].initial = fiscal_year

                # تعيين تواريخ افتراضية بناءً على آخر فترة
                last_period = AccountingPeriod.objects.filter(
                    fiscal_year=fiscal_year
                ).order_by('-end_date').first()

                if last_period:
                    self.fields['start_date'].initial = last_period.end_date + timedelta(days=1)
                else:
                    self.fields['start_date'].initial = fiscal_year.start_date

            except FiscalYear.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        fiscal_year = cleaned_data.get('fiscal_year')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # التحقق من أن تاريخ النهاية بعد البداية
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': 'تاريخ نهاية الفترة يجب أن يكون بعد تاريخ البداية'
                })

        if fiscal_year and start_date and end_date:
            # التحقق من أن الفترة داخل السنة المالية
            if start_date < fiscal_year.start_date:
                raise ValidationError({
                    'start_date': 'تاريخ بداية الفترة يجب أن يكون داخل السنة المالية'
                })

            if end_date > fiscal_year.end_date:
                raise ValidationError({
                    'end_date': 'تاريخ نهاية الفترة يجب أن يكون داخل السنة المالية'
                })

            # التحقق من عدم تداخل الفترات
            overlapping = AccountingPeriod.objects.filter(
                fiscal_year=fiscal_year
            ).exclude(pk=self.instance.pk if self.instance else None).filter(
                start_date__lte=end_date,
                end_date__gte=start_date
            )

            if overlapping.exists():
                raise ValidationError('توجد فترة محاسبية أخرى تتداخل مع هذه الفترة')

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        fiscal_year = self.cleaned_data.get('fiscal_year')

        if fiscal_year and name:
            # التحقق من عدم تكرار الاسم في نفس السنة المالية
            existing = AccountingPeriod.objects.filter(
                fiscal_year=fiscal_year,
                name=name
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('اسم الفترة موجود مسبقاً في هذه السنة المالية')

        return name


class AccountingPeriodFilterForm(forms.Form):
    """نموذج فلترة الفترات المحاسبية"""

    fiscal_year = forms.ModelChoiceField(
        queryset=FiscalYear.objects.none(),
        required=False,
        empty_label="جميع السنوات المالية",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[
            ('', 'جميع الحالات'),
            ('active', 'نشطة'),
            ('closed', 'مقفلة')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    period_type = forms.ChoiceField(
        choices=[
            ('', 'جميع الأنواع'),
            ('normal', 'عادية'),
            ('adjustment', 'تسويات')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في اسم الفترة'
        })
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if request and hasattr(request, 'current_company'):
            self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(
                company=request.current_company
            ).order_by('-start_date')


class PeriodClosingForm(forms.Form):
    """نموذج إقفال الفترة المحاسبية"""

    confirm_closing = forms.BooleanField(
        label='أؤكد إقفال هذه الفترة المحاسبية',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    closing_notes = forms.CharField(
        label='ملاحظات الإقفال',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات اختيارية حول إقفال الفترة...'
        })
    )

    def clean_confirm_closing(self):
        if not self.cleaned_data.get('confirm_closing'):
            raise ValidationError('يجب تأكيد إقفال الفترة')
        return self.cleaned_data['confirm_closing']
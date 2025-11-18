# apps/core/forms/pricing_forms.py
"""
Forms for Pricing Rules management
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import (
    PricingRule, PriceList, ItemCategory, Item
)
from decimal import Decimal
import json


class PricingRuleForm(forms.ModelForm):
    """
    Form for creating/editing pricing rules.
    Dynamic form that changes based on rule_type.
    """

    class Meta:
        model = PricingRule
        fields = [
            'name', 'code', 'description', 'rule_type', 'percentage_value',
            'formula', 'min_quantity', 'max_quantity',
            'start_date', 'end_date', 'apply_to_price_lists',
            'apply_to_categories', 'apply_to_items',
            'priority', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم القاعدة'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز القاعدة'),
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('وصف القاعدة')
            }),
            'rule_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_rule_type'
            }),
            'percentage_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '30.00',
                'id': 'id_percentage_value'
            }),
            'formula': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"base": "cost_price", "multiplier": 1.5}',
                'id': 'id_formula'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '100',
                'id': 'id_min_quantity'
            }),
            'max_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '1000',
                'id': 'id_max_quantity'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_start_date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_valid_to'
            }),
            'apply_to_price_lists': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'apply_to_categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'apply_to_items': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'value': '10'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Set querysets for company-specific data
        if self.company:
            self.fields['apply_to_price_lists'].queryset = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['apply_to_categories'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['apply_to_items'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category').order_by('name')

        # Set labels
        self.fields['name'].label = _('اسم القاعدة')
        self.fields['code'].label = _('رمز القاعدة')
        self.fields['description'].label = _('الوصف')
        self.fields['rule_type'].label = _('نوع القاعدة')
        self.fields['percentage_value'].label = _('القيمة بالنسبة المئوية')
        self.fields['formula'].label = _('صيغة التسعير (JSON)')
        self.fields['min_quantity'].label = _('الحد الأدنى للكمية')
        self.fields['max_quantity'].label = _('الحد الأقصى للكمية')
        self.fields['start_date'].label = _('تاريخ البداية')
        self.fields['end_date'].label = _('تاريخ النهاية')
        self.fields['apply_to_price_lists'].label = _('قوائم الأسعار المستهدفة')
        self.fields['apply_to_categories'].label = _('تطبيق على التصنيفات')
        self.fields['apply_to_items'].label = _('تطبيق على مواد محددة')
        self.fields['priority'].label = _('الأولوية')
        self.fields['is_active'].label = _('نشط')

        # Help texts
        self.fields['rule_type'].help_text = _('نوع القاعدة يحدد الحقول المطلوبة')
        self.fields['percentage_value'].help_text = _('للنسبة المئوية: 30 = 30%')
        self.fields['formula'].help_text = _('صيغة JSON للتسعير المعقد')
        self.fields['min_quantity'].help_text = _('للخصومات بناءً على الكمية')
        self.fields['apply_to_price_lists'].help_text = _('اتركه فارغاً للتطبيق على جميع قوائم الأسعار')
        self.fields['priority'].help_text = _('رقم أعلى = أولوية أعلى (1-100)')

        # Make certain fields optional
        self.fields['percentage_value'].required = False
        self.fields['formula'].required = False
        self.fields['min_quantity'].required = False
        self.fields['max_quantity'].required = False
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['apply_to_price_lists'].required = False
        self.fields['apply_to_categories'].required = False
        self.fields['apply_to_items'].required = False

    def clean_formula(self):
        """Validate JSON formula"""
        formula = self.cleaned_data.get('formula')
        if formula:
            try:
                # If it's a string, try to parse it
                if isinstance(formula, str):
                    formula = json.loads(formula)
                return formula
            except json.JSONDecodeError:
                raise ValidationError(_('صيغة JSON غير صالحة'))
        return {}

    def clean(self):
        cleaned_data = super().clean()
        rule_type = cleaned_data.get('rule_type')
        percentage_value = cleaned_data.get('percentage_value')
        formula = cleaned_data.get('formula')
        min_quantity = cleaned_data.get('min_quantity')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        max_quantity = cleaned_data.get('max_quantity')

        # Validation based on rule_type
        if rule_type in ['MARKUP_PERCENTAGE', 'DISCOUNT_PERCENTAGE']:
            if not percentage_value:
                raise ValidationError({
                    'percentage_value': _('القيمة المئوية مطلوبة لهذا النوع من القواعد')
                })

        elif rule_type == 'PRICE_FORMULA':
            if not formula:
                raise ValidationError({
                    'formula': _('الصيغة مطلوبة لهذا النوع من القواعد')
                })

        elif rule_type == 'BULK_DISCOUNT':
            if not min_quantity:
                raise ValidationError({
                    'min_quantity': _('الحد الأدنى للكمية مطلوب لخصم الكميات')
                })

        elif rule_type == 'SEASONAL_PRICING':
            if not start_date or not end_date:
                raise ValidationError({
                    'start_date': _('تواريخ الصلاحية مطلوبة للتسعير الموسمي'),
                    'end_date': _('تواريخ الصلاحية مطلوبة للتسعير الموسمي')
                })

        # Date validation
        if start_date and end_date and end_date < start_date:
            raise ValidationError({
                'end_date': _('تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية')
            })

        # Quantity validation
        if min_quantity and max_quantity and max_quantity < min_quantity:
            raise ValidationError({
                'max_quantity': _('الحد الأقصى يجب أن يكون أكبر من الحد الأدنى')
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set company if not set
        if not instance.company and self.company:
            instance.company = self.company

        # Ensure formula is dict
        if isinstance(instance.formula, str):
            try:
                instance.formula = json.loads(instance.formula)
            except:
                instance.formula = {}

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class PricingRuleTestForm(forms.Form):
    """
    Form for testing a pricing rule on a specific item/variant.
    """

    pricing_rule = forms.ModelChoiceField(
        queryset=PricingRule.objects.none(),
        required=True,
        label=_('قاعدة التسعير'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        required=True,
        label=_('المادة'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    quantity = forms.DecimalField(
        required=False,
        initial=Decimal('1'),
        label=_('الكمية'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'value': '1'
        })
    )

    cost_price = forms.DecimalField(
        required=False,
        label=_('سعر التكلفة'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '100.00'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['pricing_rule'].queryset = PricingRule.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('-priority', 'name')

            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')


class BulkPriceUpdateForm(forms.Form):
    """
    Form for bulk price updates across multiple items.
    """
    OPERATION_CHOICES = [
        ('PERCENTAGE_CHANGE', _('تغيير نسبة مئوية')),
        ('RECALCULATE', _('إعادة حساب الأسعار')),
    ]

    operation_type = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        required=True,
        label=_('نوع العملية'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    price_list = forms.ModelChoiceField(
        queryset=PriceList.objects.none(),
        required=False,
        label=_('قائمة الأسعار'),
        help_text=_('اتركه فارغاً للتطبيق على جميع قوائم الأسعار'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    categories = forms.ModelMultipleChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        label=_('التصنيفات'),
        help_text=_('اختر التصنيفات للتطبيق على المواد فيها'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.none(),
        required=False,
        label=_('مواد محددة'),
        help_text=_('اختر مواد محددة (أو اترك فارغاً للتطبيق على جميع المواد)'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    percentage_change = forms.DecimalField(
        required=False,
        label=_('نسبة التغيير %'),
        help_text=_('استخدم قيمة موجبة للزيادة أو سالبة للتخفيض (مثلاً: 10 = زيادة 10%, -5 = تخفيض 5%)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '10.00'
        })
    )

    apply_rules = forms.BooleanField(
        required=False,
        initial=False,
        label=_('تطبيق قواعد التسعير'),
        help_text=_('إذا كان محدداً، سيتم تطبيق قواعد التسعير عند إعادة الحساب'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    apply_changes = forms.BooleanField(
        required=False,
        initial=False,
        label=_('تطبيق التغييرات فوراً'),
        help_text=_('إذا لم يكن محدداً، سيتم عرض معاينة فقط'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['price_list'].queryset = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['categories'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['items'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        operation_type = cleaned_data.get('operation_type')
        percentage_change = cleaned_data.get('percentage_change')
        categories = cleaned_data.get('categories')
        items = cleaned_data.get('items')

        # Validate percentage_change for PERCENTAGE_CHANGE operation
        if operation_type == 'PERCENTAGE_CHANGE':
            if percentage_change is None:
                raise ValidationError({
                    'percentage_change': _('نسبة التغيير مطلوبة لهذا النوع من العمليات')
                })

            if percentage_change < -100:
                raise ValidationError({
                    'percentage_change': _('نسبة التغيير لا يمكن أن تكون أقل من -100%')
                })

        # Validate that at least categories or items are selected
        if not categories and not items:
            raise ValidationError(
                _('يجب اختيار تصنيفات أو مواد محددة على الأقل')
            )

        return cleaned_data


class PriceSimulationForm(forms.Form):
    """
    Form for simulating price changes before applying them.
    """

    pricing_rule = forms.ModelChoiceField(
        queryset=PricingRule.objects.none(),
        required=False,
        label=_('قاعدة التسعير'),
        help_text=_('اختر قاعدة للمحاكاة (أو اترك فارغاً لاستخدام نسبة مئوية)'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    percentage_change = forms.DecimalField(
        required=False,
        label=_('نسبة التغيير %'),
        help_text=_('نسبة التغيير لمحاكاة تأثيرها'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '10.00'
        })
    )

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.none(),
        required=False,
        label=_('مواد محددة'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    categories = forms.ModelMultipleChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        label=_('التصنيفات'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    price_list = forms.ModelChoiceField(
        queryset=PriceList.objects.none(),
        required=False,
        label=_('قائمة الأسعار'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    preview_count = forms.IntegerField(
        required=False,
        initial=50,
        min_value=1,
        max_value=1000,
        label=_('عدد المعاينة'),
        help_text=_('عدد المواد لمعاينتها'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': '50'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['pricing_rule'].queryset = PricingRule.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('-priority', 'name')

            self.fields['items'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['categories'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['price_list'].queryset = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        pricing_rule = cleaned_data.get('pricing_rule')
        percentage_change = cleaned_data.get('percentage_change')
        items = cleaned_data.get('items')
        categories = cleaned_data.get('categories')

        # Validate that either pricing_rule or percentage_change is provided
        if not pricing_rule and percentage_change is None:
            raise ValidationError(
                _('يجب اختيار قاعدة تسعير أو إدخال نسبة تغيير')
            )

        # Validate that at least items or categories are selected
        if not items and not categories:
            raise ValidationError(
                _('يجب اختيار مواد أو تصنيفات على الأقل')
            )

        return cleaned_data


class PriceComparisonForm(forms.Form):
    """
    Form for comparing prices across multiple price lists.
    """

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.none(),
        required=False,
        label=_('مواد محددة'),
        help_text=_('اختر مواد محددة للمقارنة'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    categories = forms.ModelMultipleChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        label=_('التصنيفات'),
        help_text=_('اختر تصنيفات للمقارنة جميع المواد فيها'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    price_lists = forms.ModelMultipleChoiceField(
        queryset=PriceList.objects.none(),
        required=False,
        label=_('قوائم الأسعار'),
        help_text=_('اختر قوائم أسعار محددة (أو اترك فارغاً لجميع القوائم)'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )

    include_all_lists = forms.BooleanField(
        required=False,
        initial=False,
        label=_('تضمين جميع قوائم الأسعار'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['items'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['categories'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['price_lists'].queryset = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        items = cleaned_data.get('items')
        categories = cleaned_data.get('categories')

        # Validate that at least items or categories are selected
        if not items and not categories:
            raise ValidationError(
                _('يجب اختيار مواد أو تصنيفات على الأقل')
            )

        return cleaned_data

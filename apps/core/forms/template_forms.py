# apps/core/forms/template_forms.py
"""
Forms for Item Template management
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import (
    ItemTemplate, ItemCategory, Brand, UnitOfMeasure,
    Currency, VariantAttribute
)
import json


class ItemTemplateForm(forms.ModelForm):
    """
    Form for creating/editing item templates.
    """

    class Meta:
        model = ItemTemplate
        fields = [
            'name', 'code', 'description', 'category', 'template_data',
            'auto_generate_codes', 'auto_create_prices',
            'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم القالب'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'TPL-001',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('وصف القالب')
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'template_data': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': '{}',
                'style': 'font-family: monospace;'
            }),
            'auto_generate_codes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'auto_create_prices': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
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
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

        # Set labels
        self.fields['name'].label = _('اسم القالب')
        self.fields['code'].label = _('كود القالب')
        self.fields['category'].label = _('التصنيف الافتراضي')
        self.fields['template_data'].label = _('بيانات القالب (JSON)')
        self.fields['auto_generate_codes'].label = _('توليد الأكواد تلقائياً')
        self.fields['code_prefix'].label = _('بادئة الكود')
        self.fields['code_pattern'].label = _('نمط الكود')
        self.fields['auto_create_variants'].label = _('إنشاء المتغيرات تلقائياً')
        self.fields['auto_create_prices'].label = _('إنشاء الأسعار تلقائياً')
        self.fields['notes'].label = _('ملاحظات')
        self.fields['is_active'].label = _('نشط')

        # Help texts
        self.fields['code'].help_text = _('كود فريد للقالب')
        self.fields['template_data'].help_text = _(
            'بيانات JSON تحدد بنية المادة الافتراضية'
        )
        self.fields['code_prefix'].help_text = _(
            'البادئة المستخدمة في توليد أكواد المواد'
        )
        self.fields['code_pattern'].help_text = _(
            'نمط توليد الكود. متغيرات: {prefix}, {counter}, {date}'
        )

        # Make certain fields optional
        self.fields['code_prefix'].required = False
        self.fields['notes'].required = False

    def clean_template_data(self):
        """Validate JSON template_data"""
        template_data = self.cleaned_data.get('template_data')
        if template_data:
            try:
                # If it's a string, try to parse it
                if isinstance(template_data, str):
                    template_data = json.loads(template_data)

                # Validate structure (basic validation)
                if not isinstance(template_data, dict):
                    raise ValidationError(_('بيانات القالب يجب أن تكون كائن JSON'))

                return template_data
            except json.JSONDecodeError as e:
                raise ValidationError(_('صيغة JSON غير صالحة: %(error)s') % {'error': str(e)})
        return {}

    def clean_code(self):
        """Validate unique code"""
        code = self.cleaned_data.get('code')
        if code:
            # Check for duplicate code
            existing = ItemTemplate.objects.filter(
                company=self.company,
                code=code
            )

            # Exclude current instance if editing
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(_('كود القالب موجود مسبقاً'))

        return code

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set company if not set
        if not instance.company and self.company:
            instance.company = self.company

        # Ensure template_data is dict
        if isinstance(instance.template_data, str):
            try:
                instance.template_data = json.loads(instance.template_data)
            except:
                instance.template_data = {}

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class ItemTemplateWizardForm(forms.Form):
    """
    Multi-step wizard form for creating item templates.
    This is a simplified interface compared to JSON editing.
    """

    # Step 1: Basic Info
    name = forms.CharField(
        max_length=100,
        required=True,
        label=_('اسم القالب'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('قالب مسامير')
        })
    )

    code = forms.CharField(
        max_length=50,
        required=True,
        label=_('كود القالب'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'TPL-NAILS'
        })
    )

    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        required=True,
        label=_('التصنيف'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Step 2: Item Defaults
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.none(),
        required=False,
        label=_('العلامة التجارية الافتراضية'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    base_uom = forms.ModelChoiceField(
        queryset=UnitOfMeasure.objects.none(),
        required=True,
        label=_('وحدة القياس الأساسية'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    currency = forms.ModelChoiceField(
        queryset=Currency.objects.none(),
        required=True,
        label=_('العملة'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    tax_rate = forms.DecimalField(
        required=True,
        initial=16,
        label=_('نسبة الضريبة %'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )

    has_variants = forms.BooleanField(
        required=False,
        initial=False,
        label=_('هل للمادة متغيرات؟'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Step 3: Variant Attributes (if has_variants = True)
    variant_attributes = forms.ModelMultipleChoiceField(
        queryset=VariantAttribute.objects.none(),
        required=False,
        label=_('خصائص المتغيرات'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5'
        }),
        help_text=_('اختر الخصائص التي ستستخدم لإنشاء المتغيرات')
    )

    # Step 4: Code Generation
    auto_generate_codes = forms.BooleanField(
        required=False,
        initial=True,
        label=_('توليد الأكواد تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    code_prefix = forms.CharField(
        max_length=10,
        required=False,
        label=_('بادئة الكود'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ITEM'
        })
    )

    # Step 5: Auto-creation Settings
    auto_create_variants = forms.BooleanField(
        required=False,
        initial=False,
        label=_('إنشاء المتغيرات تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    auto_create_prices = forms.BooleanField(
        required=False,
        initial=True,
        label=_('إنشاء الأسعار تلقائياً'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['brand'].queryset = Brand.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['base_uom'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['currency'].queryset = Currency.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['variant_attributes'].queryset = VariantAttribute.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

    def save(self, company):
        """
        Convert wizard form data to ItemTemplate.
        """
        # Build template_data from form fields
        template_data = {
            'base_item': {
                'category_id': self.cleaned_data['category'].id if self.cleaned_data.get('category') else None,
                'brand_id': self.cleaned_data['brand'].id if self.cleaned_data.get('brand') else None,
                'base_uom_id': self.cleaned_data['base_uom'].id if self.cleaned_data.get('base_uom') else None,
                'currency_id': self.cleaned_data['currency'].id if self.cleaned_data.get('currency') else None,
                'tax_rate': str(self.cleaned_data.get('tax_rate', '16.00')),
                'has_variants': self.cleaned_data.get('has_variants', False),
            }
        }

        # Add variant attributes if has_variants
        if self.cleaned_data.get('has_variants') and self.cleaned_data.get('variant_attributes'):
            template_data['variant_attributes'] = [
                {
                    'attribute_id': attr.id,
                    'attribute_name': attr.name
                }
                for attr in self.cleaned_data['variant_attributes']
            ]

        # Create ItemTemplate
        template = ItemTemplate.objects.create(
            company=company,
            name=self.cleaned_data['name'],
            code=self.cleaned_data['code'],
            category=self.cleaned_data['category'],
            template_data=template_data,
            auto_generate_codes=self.cleaned_data.get('auto_generate_codes', True),
            code_prefix=self.cleaned_data.get('code_prefix', ''),
            auto_create_variants=self.cleaned_data.get('auto_create_variants', False),
            auto_create_prices=self.cleaned_data.get('auto_create_prices', True)
        )

        return template


class UseTemplateForm(forms.Form):
    """
    Form for using a template to create a new item.
    Allows overriding template defaults.
    """

    template = forms.ModelChoiceField(
        queryset=ItemTemplate.objects.none(),
        required=True,
        label=_('القالب'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Override fields
    item_name = forms.CharField(
        max_length=200,
        required=True,
        label=_('اسم المادة'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('سيتم ملؤه من القالب')
        })
    )

    item_code = forms.CharField(
        max_length=50,
        required=False,
        label=_('كود المادة (اتركه فارغاً للتوليد التلقائي)'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('سيتم توليده تلقائياً')
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['template'].queryset = ItemTemplate.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

# apps/core/forms/uom_forms.py
"""
Forms for Unit of Measure (UoM) management - Updated Week 2
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import UoMGroup, UnitOfMeasure, UoMConversion, Item, ItemVariant
from decimal import Decimal


class UoMGroupForm(forms.ModelForm):
    """
    Form for creating/editing UoM Groups.

    ⭐ NEW Week 2

    UoM Groups organize units by type (Weight, Length, Volume, etc.)
    """

    class Meta:
        model = UoMGroup
        fields = [
            'name', 'code', 'description',
            'base_uom', 'allow_decimal',
            'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: الوزن، الطول، الحجم')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: WEIGHT, LENGTH, VOLUME'),
                'style': 'text-transform: uppercase;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف تفصيلي للمجموعة واستخداماتها')
            }),
            'base_uom': forms.Select(attrs={
                'class': 'form-select'
            }),
            'allow_decimal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': _('اسم المجموعة'),
            'code': _('رمز المجموعة'),
            'description': _('الوصف'),
            'base_uom': _('الوحدة الأساسية'),
            'allow_decimal': _('السماح بالأرقام العشرية'),
            'notes': _('ملاحظات'),
            'is_active': _('نشط')
        }
        help_texts = {
            'name': _('اسم المجموعة بالعربية'),
            'code': _('رمز فريد بالإنجليزية (حروف كبيرة)'),
            'base_uom': _('الوحدة الأساسية للمجموعة (يمكن تعيينها لاحقاً)'),
            'allow_decimal': _('هل يمكن استخدام كميات عشرية مع هذه المجموعة؟')
        }

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

        # Filter base_uom to show only units in this group (if editing)
        if self.instance.pk:
            self.fields['base_uom'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                uom_group=self.instance,
                is_active=True
            )
        else:
            # For new groups, show all units without a group
            self.fields['base_uom'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                uom_group__isnull=True,
                is_active=True
            )

        self.fields['base_uom'].required = False

    def clean_code(self):
        """Ensure code is uppercase and unique"""
        code = self.cleaned_data.get('code', '').upper().strip()

        if not code:
            raise ValidationError(_('رمز المجموعة مطلوب'))

        # Check uniqueness within company
        existing = UoMGroup.objects.filter(
            company=self.company,
            code=code
        ).exclude(pk=self.instance.pk if self.instance else None)

        if existing.exists():
            raise ValidationError(_('رمز المجموعة موجود مسبقاً'))

        return code

    def clean(self):
        cleaned_data = super().clean()
        base_uom = cleaned_data.get('base_uom')

        # If base_uom is set, ensure it belongs to this group
        if base_uom and self.instance.pk:
            if base_uom.uom_group and base_uom.uom_group != self.instance:
                raise ValidationError({
                    'base_uom': _('الوحدة الأساسية يجب أن تنتمي لهذه المجموعة')
                })

        return cleaned_data


class UoMConversionForm(forms.ModelForm):
    """
    Form for creating/editing UoM conversions.
    Handles conversion between different units of measure.
    """

    class Meta:
        model = UoMConversion
        fields = [
            'item', 'variant', 'from_uom',
            'conversion_factor', 'formula_expression',
            'notes', 'is_active'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_item'
            }),
            'variant': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_variant',
                'disabled': True  # Will be enabled by JS when item is selected
            }),
            'from_uom': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'conversion_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'min': '0.000001',
                'required': True,
                'placeholder': '12'
            }),
            'formula_expression': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اختياري: صيغة معقدة')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية')
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
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('category').order_by('name')

            self.fields['from_uom'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

        # Make item and variant optional
        self.fields['item'].required = False
        self.fields['variant'].required = False

        # Set labels
        self.fields['item'].label = _('المادة (اختياري - فارغ = تحويل عام)')
        self.fields['variant'].label = _('المتغير (اختياري)')
        self.fields['from_uom'].label = _('من الوحدة (تحويل إلى الوحدة الأساسية)')
        self.fields['conversion_factor'].label = _('معامل التحويل')
        self.fields['formula_expression'].label = _('صيغة التحويل (اختياري)')
        self.fields['notes'].label = _('ملاحظات')
        self.fields['is_active'].label = _('نشط')

        # Help texts
        self.fields['conversion_factor'].help_text = _(
            'مثال: 1 دزينة = 12 قطعة، أدخل 12'
        )
        self.fields['item'].help_text = _(
            'اتركه فارغاً لإنشاء تحويل عام ينطبق على جميع المواد'
        )

        # If editing, set variant queryset based on selected item
        if self.instance.pk and self.instance.item:
            self.fields['variant'].queryset = ItemVariant.objects.filter(
                item=self.instance.item,
                is_active=True
            ).order_by('code')
            self.fields['variant'].widget.attrs.pop('disabled', None)
        else:
            self.fields['variant'].queryset = ItemVariant.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        from_uom = cleaned_data.get('from_uom')
        conversion_factor = cleaned_data.get('conversion_factor')
        item = cleaned_data.get('item')
        variant = cleaned_data.get('variant')

        # Validation 1: conversion_factor must be positive
        if conversion_factor and conversion_factor <= 0:
            raise ValidationError({
                'conversion_factor': _('معامل التحويل يجب أن يكون أكبر من صفر')
            })

        # Validation 2: if variant is selected, item must be selected
        if variant and not item:
            raise ValidationError({
                'variant': _('يجب اختيار المادة أولاً قبل اختيار المتغير')
            })

        # Validation 3: check for duplicate conversion
        # Unique constraint is: item, variant, from_uom, company
        if self.company and from_uom:
            existing = UoMConversion.objects.filter(
                company=self.company,
                item=item,
                variant=variant,
                from_uom=from_uom
            )

            # Exclude current instance if editing
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                scope = _('عام')
                if variant:
                    scope = f'{item.name} - {variant.code}'
                elif item:
                    scope = item.name

                raise ValidationError(
                    _('يوجد تحويل مماثل بالفعل للنطاق: %(scope)s من %(uom)s') % {
                        'scope': scope,
                        'uom': from_uom.name
                    }
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set company if not set
        if not instance.company and self.company:
            instance.company = self.company

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class UoMConversionBulkForm(forms.Form):
    """
    Form for creating multiple UoM conversions at once.
    Useful for setting up standard conversions quickly.
    """

    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        required=False,
        label=_('المادة (اختياري)'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('اتركه فارغاً لإنشاء تحويلات عامة')
    )

    base_uom = forms.ModelChoiceField(
        queryset=UnitOfMeasure.objects.none(),
        required=True,
        label=_('الوحدة الأساسية'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('الوحدة التي سيتم التحويل إليها (مثل: قطعة)')
    )

    # Standard conversions (will be dynamically added)
    dozen_factor = forms.DecimalField(
        required=False,
        initial=Decimal('12'),
        label=_('معامل الدزينة'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '12'
        })
    )

    carton_factor = forms.DecimalField(
        required=False,
        label=_('معامل الكرتون'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '100'
        })
    )

    box_factor = forms.DecimalField(
        required=False,
        label=_('معامل الصندوق'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '50'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['item'].queryset = Item.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            self.fields['base_uom'].queryset = UnitOfMeasure.objects.filter(
                company=self.company,
                is_active=True,
                uom_type='UNIT'
            ).order_by('name')

    def save(self):
        """
        Create multiple UoMConversion objects.
        Returns list of created conversions.
        """
        if not self.company:
            return []

        item = self.cleaned_data.get('item')
        base_uom = self.cleaned_data.get('base_uom')
        conversions = []

        # Standard conversion mappings
        conversion_map = {
            'dozen_factor': 'DOZEN',
            'carton_factor': 'CARTON',
            'box_factor': 'BOX',
        }

        for field_name, uom_code in conversion_map.items():
            factor = self.cleaned_data.get(field_name)
            if factor and factor > 0:
                try:
                    from_uom = UnitOfMeasure.objects.get(
                        company=self.company,
                        code=uom_code,
                        is_active=True
                    )

                    # Check if conversion already exists
                    exists = UoMConversion.objects.filter(
                        company=self.company,
                        item=item,
                        from_uom=from_uom
                    ).exists()

                    if not exists:
                        conversion = UoMConversion.objects.create(
                            company=self.company,
                            item=item,
                            from_uom=from_uom,
                            conversion_factor=factor
                        )
                        conversions.append(conversion)
                except UnitOfMeasure.DoesNotExist:
                    pass  # UoM not found, skip

        return conversions

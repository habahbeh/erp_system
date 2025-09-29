# apps/core/forms/price_forms.py
"""
نماذج قوائم الأسعار
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from ..models import PriceList, PriceListItem, Item, ItemVariant


class PriceListForm(forms.ModelForm):
    """نموذج إنشاء/تعديل قائمة الأسعار"""

    class Meta:
        model = PriceList
        fields = ['name', 'code', 'description', 'currency', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم قائمة الأسعار'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز القائمة (مثل: WHOLESALE)'),
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف القائمة')
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة العملات النشطة
        from ..models import Currency
        self.fields['currency'].queryset = Currency.objects.filter(
            is_active=True
        ).order_by('name')

        # تخصيص التسميات
        self.fields['name'].label = _('اسم القائمة')
        self.fields['code'].label = _('رمز القائمة')
        self.fields['description'].label = _('الوصف')
        self.fields['currency'].label = _('العملة')
        self.fields['is_default'].label = _('قائمة افتراضية')

        # Help texts
        self.fields['code'].help_text = _('رمز فريد لقائمة الأسعار')
        self.fields['is_default'].help_text = _('القائمة الافتراضية المستخدمة عند عدم تحديد قائمة')

    def clean_code(self):
        """التحقق من تفرد الرمز"""
        code = self.cleaned_data.get('code')
        if code and self.request:
            company = self.request.current_company
            queryset = PriceList.objects.filter(company=company, code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الرمز مستخدم مسبقاً'))
        return code


class PriceListItemForm(forms.ModelForm):
    """نموذج إضافة سعر مادة في قائمة"""

    class Meta:
        model = PriceListItem
        fields = [
            'item', 'variant', 'price', 'min_quantity',
            'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'variant': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
                'required': True
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '1',
                'value': '1'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.price_list = kwargs.pop('price_list', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة الأمواد النشطة
            self.fields['item'].queryset = Item.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            # المتغيرات ستُحمل ديناميكياً عبر Ajax حسب المادة المختار
            self.fields['variant'].queryset = ItemVariant.objects.none()

        # تخصيص التسميات
        self.fields['variant'].label = _('المتغير (اختياري)')
        self.fields['variant'].help_text = _('فقط للأمواد التي لها متغيرات')
        self.fields['min_quantity'].label = _('الكمية الأدنى')
        self.fields['start_date'].label = _('تاريخ البداية')
        self.fields['end_date'].label = _('تاريخ النهاية')


class BulkPriceUpdateForm(forms.Form):
    """نموذج تحديث الأسعار بالجملة"""

    UPDATE_TYPES = [
        ('percentage', _('نسبة مئوية')),
        ('fixed', _('مبلغ ثابت')),
        ('set', _('تعيين سعر جديد')),
    ]

    update_type = forms.ChoiceField(
        label=_('نوع التحديث'),
        choices=UPDATE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    value = forms.DecimalField(
        label=_('القيمة'),
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': _('القيمة')
        })
    )

    operation = forms.ChoiceField(
        label=_('العملية'),
        choices=[
            ('add', _('إضافة')),
            ('subtract', _('طرح')),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    category = forms.ModelChoiceField(
        label=_('تصنيف محدد'),
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    brand = forms.ModelChoiceField(
        label=_('علامة تجارية محددة'),
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    round_to = forms.DecimalField(
        label=_('التقريب إلى'),
        max_digits=5,
        decimal_places=3,
        required=False,
        initial=Decimal('0.050'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': '0.050'
        }),
        help_text=_('مثال: 0.050 للتقريب إلى 0.05')
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            from ..models import ItemCategory, Brand

            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            self.fields['brand'].queryset = Brand.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

        # جعل العملية مطلوبة فقط لأنواع معينة
        self.fields['operation'].widget.attrs['data-depends-on'] = 'update_type'

    def clean(self):
        cleaned_data = super().clean()
        update_type = cleaned_data.get('update_type')
        operation = cleaned_data.get('operation')
        value = cleaned_data.get('value')

        # التحقق من صحة البيانات حسب نوع التحديث
        if update_type in ['percentage', 'fixed']:
            if not operation:
                raise ValidationError({
                    'operation': _('يجب تحديد العملية (إضافة أو طرح)')
                })

        if update_type == 'percentage':
            if value and (value < -100 or value > 1000):
                raise ValidationError({
                    'value': _('النسبة يجب أن تكون بين -100% و 1000%')
                })

        return cleaned_data
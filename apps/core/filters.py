# apps/core/filters.py
"""
Django Filters للبحث والتصفية
"""

import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Item, ItemCategory, Brand, UnitOfMeasure, Currency, Warehouse


class ItemFilter(django_filters.FilterSet):
    """فلتر الأصناف"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم، الكود، SKU، الباركود...'),
        })
    )

    category = django_filters.ModelChoiceFilter(
        queryset=ItemCategory.objects.none(),
        label=_('التصنيف'),
        empty_label=_('كل التصنيفات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    brand = django_filters.ModelChoiceFilter(
        queryset=Brand.objects.none(),
        label=_('العلامة التجارية'),
        empty_label=_('كل العلامات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    unit_of_measure = django_filters.ModelChoiceFilter(
        queryset=UnitOfMeasure.objects.none(),
        label=_('وحدة القياس'),
        empty_label=_('كل الوحدات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    currency = django_filters.ModelChoiceFilter(
        queryset=Currency.objects.none(),
        label=_('العملة'),
        empty_label=_('كل العملات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    default_warehouse = django_filters.ModelChoiceFilter(
        queryset=Warehouse.objects.none(),
        label=_('المستودع'),
        empty_label=_('كل المستودعات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    price_range = django_filters.RangeFilter(
        field_name='sale_price',
        label=_('نطاق السعر'),
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'placeholder': _('من - إلى')
        })
    )

    has_variants = django_filters.BooleanFilter(
        label=_('له متغيرات'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نعم')), (False, _('لا'))],
            attrs={'class': 'form-select'}
        )
    )

    is_active = django_filters.BooleanFilter(
        label=_('الحالة'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نشط')), (False, _('غير نشط'))],
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = Item
        fields = [
            'search', 'category', 'brand', 'unit_of_measure',
            'currency', 'default_warehouse', 'price_range',
            'has_variants', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة الخيارات حسب الشركة
            self.filters['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'name')

            self.filters['brand'].queryset = Brand.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.filters['unit_of_measure'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.filters['currency'].queryset = Currency.objects.filter(
                is_active=True
            ).order_by('name')

            self.filters['default_warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value) |
                Q(sku__icontains=value) |
                Q(barcode__icontains=value) |
                Q(short_description__icontains=value) |
                Q(manufacturer__icontains=value) |
                Q(model_number__icontains=value)
            ).distinct()
        return queryset


class ItemCategoryFilter(django_filters.FilterSet):
    """فلتر تصنيفات الأصناف"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم أو الكود...'),
        })
    )

    parent = django_filters.ModelChoiceFilter(
        queryset=ItemCategory.objects.none(),
        label=_('التصنيف الأب'),
        empty_label=_('كل التصنيفات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    level = django_filters.ChoiceFilter(
        label=_('المستوى'),
        choices=[(i, _('المستوى %(level)s') % {'level': i}) for i in range(1, 5)],
        empty_label=_('كل المستويات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_active = django_filters.BooleanFilter(
        label=_('الحالة'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نشط')), (False, _('غير نشط'))],
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = ItemCategory
        fields = ['search', 'parent', 'level', 'is_active']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة التصنيفات الأب حسب الشركة
            self.filters['parent'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('level', 'name')

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value) |
                Q(description__icontains=value)
            ).distinct()
        return queryset


class BrandFilter(django_filters.FilterSet):
    """فلتر العلامات التجارية"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في اسم العلامة...'),
        })
    )

    country = django_filters.CharFilter(
        field_name='country',
        lookup_expr='icontains',
        label=_('بلد المنشأ'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('بلد المنشأ')
        })
    )

    is_active = django_filters.BooleanFilter(
        label=_('الحالة'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نشط')), (False, _('غير نشط'))],
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = Brand
        fields = ['search', 'country', 'is_active']

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(description__icontains=value)
            ).distinct()
        return queryset


class UnitOfMeasureFilter(django_filters.FilterSet):
    """فلتر وحدات القياس"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم أو الرمز...'),
        })
    )

    is_active = django_filters.BooleanFilter(
        label=_('الحالة'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نشط')), (False, _('غير نشط'))],
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = UnitOfMeasure
        fields = ['search', 'is_active']

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value)
            ).distinct()
        return queryset
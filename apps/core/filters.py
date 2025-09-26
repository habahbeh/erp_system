# apps/core/filters.py
"""
Django Filters للبحث والتصفية
"""

import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Item, ItemCategory, Brand, UnitOfMeasure, Currency, Warehouse, BusinessPartner, User, UnitOfMeasure, Currency, Company, Branch
from .models import Warehouse


class ItemFilter(django_filters.FilterSet):
    """فلتر المواد"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم، الكود، رقم الكتالوج، الباركود...'),
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
            'currency', 'default_warehouse',
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
                Q(catalog_number__icontains=value) |
                Q(barcode__icontains=value) |
                Q(short_description__icontains=value) |
                Q(manufacturer__icontains=value) |
                Q(model_number__icontains=value)
            ).distinct()
        return queryset


class ItemCategoryFilter(django_filters.FilterSet):
    """فلتر تصنيفات المواد"""

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


class BusinessPartnerFilter(django_filters.FilterSet):
    """فلتر العملاء"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم، الكود، الهاتف، البريد...'),
        })
    )

    partner_type = django_filters.ChoiceFilter(
        choices=BusinessPartner.PARTNER_TYPES,
        label=_('نوع العميل'),
        empty_label=_('جميع الأنواع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    account_type = django_filters.ChoiceFilter(
        choices=BusinessPartner.ACCOUNT_TYPE_CHOICES,
        label=_('نوع الحساب'),
        empty_label=_('جميع الأنواع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sales_representative = django_filters.ModelChoiceFilter(
        queryset=User.objects.none(),
        label=_('المندوب'),
        empty_label=_('جميع المندوبين'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    tax_status = django_filters.ChoiceFilter(
        choices=BusinessPartner.TAX_STATUS_CHOICES,
        label=_('الحالة الضريبية'),
        empty_label=_('جميع الحالات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains',
        label=_('المدينة'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('المدينة')
        })
    )

    region = django_filters.CharFilter(
        field_name='region',
        lookup_expr='icontains',
        label=_('المنطقة'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('المنطقة')
        })
    )

    has_credit_limit = django_filters.BooleanFilter(
        method='filter_has_credit_limit',
        label=_('له حد ائتمان'),
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
        model = BusinessPartner
        fields = [
            'search', 'partner_type', 'account_type', 'sales_representative',
            'tax_status', 'city', 'region', 'has_credit_limit', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة المندوبين حسب الشركة
            self.filters['sales_representative'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value) |
                Q(contact_person__icontains=value) |
                Q(phone__icontains=value) |
                Q(mobile__icontains=value) |
                Q(email__icontains=value) |
                Q(tax_number__icontains=value) |
                Q(commercial_register__icontains=value) |
                Q(address__icontains=value) |
                Q(city__icontains=value) |
                Q(region__icontains=value)
            ).distinct()
        return queryset

    def filter_has_credit_limit(self, queryset, name, value):
        """فلترة حسب وجود حد ائتمان"""
        if value is True:
            return queryset.filter(credit_limit__gt=0)
        elif value is False:
            return queryset.filter(credit_limit=0)
        return queryset


class WarehouseFilter(django_filters.FilterSet):
    """فلتر المستودعات"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في اسم المستودع...'),
        })
    )

    manager = django_filters.ModelChoiceFilter(
        queryset=User.objects.none(),
        label=_('المدير'),
        empty_label=_('جميع المدراء'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_main = django_filters.BooleanFilter(
        label=_('مستودع رئيسي'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('رئيسي')), (False, _('فرعي'))],
            attrs={'class': 'form-select'}
        )
    )

    allow_negative_stock = django_filters.BooleanFilter(
        label=_('يسمح بالرصيد السالب'),
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
        model = Warehouse
        fields = ['search', 'manager', 'is_main', 'allow_negative_stock', 'is_active']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة المدراء حسب الشركة
            self.filters['manager'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name')

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value) |
                Q(address__icontains=value) |
                Q(phone__icontains=value)
            ).distinct()
        return queryset

# أضف هذا في نهاية ملف apps/core/filters.py

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

    has_logo = django_filters.BooleanFilter(
        method='filter_has_logo',
        label=_('له شعار'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نعم')), (False, _('لا'))],
            attrs={'class': 'form-select'}
        )
    )

    has_website = django_filters.BooleanFilter(
        method='filter_has_website',
        label=_('له موقع إلكتروني'),
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
        model = Brand
        fields = ['search', 'country', 'has_logo', 'has_website', 'is_active']

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(description__icontains=value) |
                Q(country__icontains=value) |
                Q(website__icontains=value)
            ).distinct()
        return queryset

    def filter_has_logo(self, queryset, name, value):
        """فلترة حسب وجود شعار"""
        if value is True:
            return queryset.exclude(logo__exact='')
        elif value is False:
            return queryset.filter(logo__exact='')
        return queryset

    def filter_has_website(self, queryset, name, value):
        """فلترة حسب وجود موقع إلكتروني"""
        if value is True:
            return queryset.exclude(website__exact='')
        elif value is False:
            return queryset.filter(website__exact='')
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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

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


class CurrencyFilter(django_filters.FilterSet):
    """فلتر العملات"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم أو الرمز...'),
        })
    )

    is_base = django_filters.BooleanFilter(
        label=_('العملة الأساسية'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('أساسية')), (False, _('عادية'))],
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
        model = Currency
        fields = ['search', 'is_base', 'is_active']

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(name__icontains=value) |
                Q(name_en__icontains=value) |
                Q(code__icontains=value) |
                Q(symbol__icontains=value)
            ).distinct()
        return queryset


class UserFilter(django_filters.FilterSet):
    """فلتر المستخدمين"""

    search = django_filters.CharFilter(
        method='filter_search',
        label=_('البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('البحث في الاسم، اسم المستخدم، البريد...'),
        })
    )

    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.none(),
        label=_('الشركة'),
        empty_label=_('كل الشركات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    branch = django_filters.ModelChoiceFilter(
        queryset=Branch.objects.none(),
        label=_('الفرع'),
        empty_label=_('كل الفروع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    role = django_filters.ChoiceFilter(
        choices=[
            ('superuser', _('مدير نظام')),
            ('staff', _('طاقم الإدارة')),
            ('user', _('مستخدم عادي')),
        ],
        label=_('الصلاحيات'),
        empty_label=_('كل الصلاحيات'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        method='filter_role'
    )

    is_active = django_filters.BooleanFilter(
        label=_('الحالة'),
        widget=forms.Select(
            choices=[(None, _('الكل')), (True, _('نشط')), (False, _('غير نشط'))],
            attrs={'class': 'form-select'}
        )
    )

    date_joined = django_filters.DateFromToRangeFilter(
        label=_('تاريخ الانضمام'),
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = User
        fields = ['search', 'company', 'branch', 'role', 'is_active', 'date_joined']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة الخيارات
        self.filters['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.filters['branch'].queryset = Branch.objects.filter(is_active=True).order_by('name')

    def filter_search(self, queryset, name, value):
        """البحث في عدة حقول"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(username__icontains=value) |
                Q(first_name__icontains=value) |
                Q(last_name__icontains=value) |
                Q(email__icontains=value) |
                Q(emp_number__icontains=value) |
                Q(phone__icontains=value)
            ).distinct()
        return queryset

    def filter_role(self, queryset, name, value):
        """فلترة حسب الدور"""
        if value == 'superuser':
            return queryset.filter(is_superuser=True)
        elif value == 'staff':
            return queryset.filter(is_staff=True, is_superuser=False)
        elif value == 'user':
            return queryset.filter(is_staff=False, is_superuser=False)
        return queryset

# تحديث __all__ في نهاية الملف
__all__ = [
    'ItemFilter',
    'ItemCategoryFilter',
    'BrandFilter',
    'UnitOfMeasureFilter',
    'BusinessPartnerFilter',
    'WarehouseFilter',
    'UserFilter',  # إضافة جديد
]


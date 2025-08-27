# apps/base_data/forms/filter_forms.py
"""
نماذج الفلترة والبحث - محدث 100% حسب models.py والمتطلبات
للاستخدام مع DataTables وواجهات البحث المتقدم
Bootstrap 5 + RTL + Server-side processing
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, timedelta

from ..models import Item, ItemCategory, BusinessPartner, Warehouse, UnitOfMeasure
from core.models import Branch, User


class BaseFilterForm(forms.Form):
    """نموذج أساسي للفلترة - يحتوي على حقول مشتركة"""

    search = forms.CharField(
        label=_('بحث'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('بحث...'),
            'data-kt-filter': 'search',
            'autocomplete': 'off'
        })
    )

    is_active = forms.ChoiceField(
        label=_('الحالة'),
        choices=[
            ('', _('الكل')),
            ('1', _('نشط فقط')),
            ('0', _('غير نشط فقط')),
        ],
        required=False,
        initial='1',
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'status',
        })
    )

    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
            'data-kt-filter': 'date_from',
        })
    )

    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
            'data-kt-filter': 'date_to',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))

        return cleaned_data


class ItemFilterForm(BaseFilterForm):
    """نموذج فلترة الأصناف - محدث 100%"""

    category = forms.ModelChoiceField(
        label=_('التصنيف'),
        queryset=ItemCategory.objects.none(),
        required=False,
        empty_label=_('جميع التصنيفات'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-control': 'select2',
            'data-placeholder': _('اختر التصنيف'),
            'data-kt-filter': 'category',
        })
    )

    unit = forms.ModelChoiceField(
        label=_('وحدة القياس'),
        queryset=UnitOfMeasure.objects.none(),
        required=False,
        empty_label=_('جميع الوحدات'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-control': 'select2',
            'data-kt-filter': 'unit',
        })
    )

    has_barcode = forms.ChoiceField(
        label=_('الباركود'),
        choices=[
            ('', _('الكل')),
            ('1', _('له باركود')),
            ('0', _('بدون باركود')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'has_barcode',
        })
    )

    price_range = forms.ChoiceField(
        label=_('نطاق السعر'),
        choices=[
            ('', _('الكل')),
            ('0-100', _('0 - 100')),
            ('100-500', _('100 - 500')),
            ('500-1000', _('500 - 1000')),
            ('1000+', _('أكثر من 1000')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'price_range',
        })
    )

    # حقول جديدة حسب models.py
    manufacturer = forms.CharField(
        label=_('الشركة المصنعة'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('الشركة المصنعة'),
            'data-kt-filter': 'manufacturer',
        })
    )

    stock_status = forms.ChoiceField(
        label=_('حالة المخزون'),
        choices=[
            ('', _('الكل')),
            ('in_stock', _('متوفر')),
            ('low_stock', _('منخفض')),
            ('out_of_stock', _('غير متوفر')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'stock_status',
        })
    )

    is_inactive = forms.ChoiceField(
        label=_('حالة النشاط'),
        choices=[
            ('', _('الكل')),
            ('0', _('فعال')),
            ('1', _('غير فعال')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'is_inactive',
        })
    )

    has_image = forms.ChoiceField(
        label=_('الصورة'),
        choices=[
            ('', _('الكل')),
            ('1', _('له صورة')),
            ('0', _('بدون صورة')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'has_image',
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company,
                is_active=True
            ).order_by('level', 'code')

            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

    def get_queryset(self, queryset):
        """تطبيق الفلاتر على queryset"""

        # البحث العام
        search = self.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(barcode__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(specifications__icontains=search)
            )

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # حالة النشاط (is_inactive)
        is_inactive = self.cleaned_data.get('is_inactive')
        if is_inactive == '1':
            queryset = queryset.filter(is_inactive=True)
        elif is_inactive == '0':
            queryset = queryset.filter(is_inactive=False)

        # التصنيف
        category = self.cleaned_data.get('category')
        if category:
            # البحث في التصنيف وتصنيفاته الفرعية
            categories = [category]
            children = ItemCategory.objects.filter(parent=category)
            if children.exists():
                categories.extend(children)
            queryset = queryset.filter(category__in=categories)

        # وحدة القياس
        unit = self.cleaned_data.get('unit')
        if unit:
            queryset = queryset.filter(unit=unit)

        # الباركود
        has_barcode = self.cleaned_data.get('has_barcode')
        if has_barcode == '1':
            queryset = queryset.exclude(Q(barcode='') | Q(barcode__isnull=True))
        elif has_barcode == '0':
            queryset = queryset.filter(Q(barcode='') | Q(barcode__isnull=True))

        # الصورة
        has_image = self.cleaned_data.get('has_image')
        if has_image == '1':
            queryset = queryset.exclude(Q(image='') | Q(image__isnull=True))
        elif has_image == '0':
            queryset = queryset.filter(Q(image='') | Q(image__isnull=True))

        # الشركة المصنعة
        manufacturer = self.cleaned_data.get('manufacturer')
        if manufacturer:
            queryset = queryset.filter(manufacturer__icontains=manufacturer)

        # نطاق السعر
        price_range = self.cleaned_data.get('price_range')
        if price_range:
            if price_range == '0-100':
                queryset = queryset.filter(sale_price__gte=0, sale_price__lte=100)
            elif price_range == '100-500':
                queryset = queryset.filter(sale_price__gt=100, sale_price__lte=500)
            elif price_range == '500-1000':
                queryset = queryset.filter(sale_price__gt=500, sale_price__lte=1000)
            elif price_range == '1000+':
                queryset = queryset.filter(sale_price__gt=1000)

        # حالة المخزون
        stock_status = self.cleaned_data.get('stock_status')
        if stock_status:
            if stock_status == 'in_stock':
                queryset = queryset.filter(
                    warehouse_items__quantity__gt=0
                ).distinct()
            elif stock_status == 'low_stock':
                queryset = queryset.filter(
                    warehouse_items__quantity__gt=0,
                    warehouse_items__quantity__lte=F('minimum_quantity')
                ).distinct()
            elif stock_status == 'out_of_stock':
                queryset = queryset.filter(
                    Q(warehouse_items__quantity__lte=0) |
                    Q(warehouse_items__isnull=True)
                ).distinct()

        # التاريخ
        date_from = self.cleaned_data.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.cleaned_data.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class BusinessPartnerFilterForm(BaseFilterForm):
    """نموذج فلترة الشركاء التجاريين - محدث 100%"""

    partner_type = forms.ChoiceField(
        label=_('نوع الشريك'),
        choices=[('', _('الكل'))] + BusinessPartner.PARTNER_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'partner_type',
        })
    )

    account_type = forms.ChoiceField(
        label=_('نوع الحساب'),
        choices=[('', _('الكل'))] + BusinessPartner.ACCOUNT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'account_type',
        })
    )

    tax_status = forms.ChoiceField(
        label=_('الحالة الضريبية'),
        choices=[
            ('', _('الكل')),
            ('taxable', _('خاضع للضريبة')),
            ('exempt', _('معفى من الضريبة')),
            ('export', _('تصدير')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'tax_status',
        })
    )

    city = forms.CharField(
        label=_('المدينة'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('المدينة'),
            'data-kt-filter': 'city',
        })
    )

    region = forms.CharField(
        label=_('المنطقة'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('المنطقة'),
            'data-kt-filter': 'region',
        })
    )

    has_tax_number = forms.ChoiceField(
        label=_('الرقم الضريبي'),
        choices=[
            ('', _('الكل')),
            ('1', _('له رقم ضريبي')),
            ('0', _('بدون رقم ضريبي')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'has_tax_number',
        })
    )

    credit_status = forms.ChoiceField(
        label=_('حالة الائتمان'),
        choices=[
            ('', _('الكل')),
            ('within_limit', _('ضمن الحد')),
            ('near_limit', _('قريب من الحد')),
            ('exceeded', _('تجاوز الحد')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'credit_status',
        })
    )

    salesperson = forms.ModelChoiceField(
        label=_('مندوب المبيعات'),
        queryset=User.objects.none(),
        required=False,
        empty_label=_('جميع المندوبين'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-control': 'select2',
            'data-kt-filter': 'salesperson',
        })
    )

    # حقول جديدة للعملاء
    customer_category = forms.ChoiceField(
        label=_('تصنيف العميل'),
        choices=[('', _('الكل'))] + [
            ('retail', _('تجزئة')),
            ('wholesale', _('جملة')),
            ('vip', _('VIP')),
            ('regular', _('عادي')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'customer_category',
        })
    )

    # حقول جديدة للموردين
    supplier_category = forms.ChoiceField(
        label=_('تصنيف المورد'),
        choices=[('', _('الكل'))] + [
            ('manufacturer', _('مصنع')),
            ('distributor', _('موزع')),
            ('importer', _('مستورد')),
            ('local', _('محلي')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'supplier_category',
        })
    )

    rating = forms.ChoiceField(
        label=_('التقييم'),
        choices=[
            ('', _('الكل')),
            ('5', _('5 نجوم')),
            ('4', _('4 نجوم فأكثر')),
            ('3', _('3 نجوم فأكثر')),
            ('2', _('2 نجوم فأكثر')),
            ('1', _('نجمة واحدة فأكثر')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'rating',
        })
    )

    has_email = forms.ChoiceField(
        label=_('البريد الإلكتروني'),
        choices=[
            ('', _('الكل')),
            ('1', _('له بريد إلكتروني')),
            ('0', _('بدون بريد إلكتروني')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'has_email',
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['salesperson'].queryset = User.objects.filter(
                company=company,
                is_active=True
            ).order_by('first_name', 'last_name')

    def get_queryset(self, queryset):
        """تطبيق الفلاتر على queryset"""

        # البحث العام
        search = self.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(phone__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search) |
                Q(tax_number__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(commercial_register__icontains=search)
            )

        # نوع الشريك
        partner_type = self.cleaned_data.get('partner_type')
        if partner_type:
            if partner_type == 'both':
                queryset = queryset.filter(partner_type='both')
            else:
                queryset = queryset.filter(
                    Q(partner_type=partner_type) | Q(partner_type='both')
                )

        # نوع الحساب
        account_type = self.cleaned_data.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)

        # الحالة الضريبية
        tax_status = self.cleaned_data.get('tax_status')
        if tax_status:
            queryset = queryset.filter(tax_status=tax_status)

        # المدينة
        city = self.cleaned_data.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        # المنطقة
        region = self.cleaned_data.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)

        # الرقم الضريبي
        has_tax_number = self.cleaned_data.get('has_tax_number')
        if has_tax_number == '1':
            queryset = queryset.exclude(Q(tax_number='') | Q(tax_number__isnull=True))
        elif has_tax_number == '0':
            queryset = queryset.filter(Q(tax_number='') | Q(tax_number__isnull=True))

        # البريد الإلكتروني
        has_email = self.cleaned_data.get('has_email')
        if has_email == '1':
            queryset = queryset.exclude(Q(email='') | Q(email__isnull=True))
        elif has_email == '0':
            queryset = queryset.filter(Q(email='') | Q(email__isnull=True))

        # مندوب المبيعات
        salesperson = self.cleaned_data.get('salesperson')
        if salesperson:
            queryset = queryset.filter(salesperson=salesperson)

        # تصنيف العميل
        customer_category = self.cleaned_data.get('customer_category')
        if customer_category:
            queryset = queryset.filter(
                customer_category=customer_category,
                partner_type__in=['customer', 'both']
            )

        # تصنيف المورد
        supplier_category = self.cleaned_data.get('supplier_category')
        if supplier_category:
            queryset = queryset.filter(
                supplier_category=supplier_category,
                partner_type__in=['supplier', 'both']
            )

        # التقييم
        rating = self.cleaned_data.get('rating')
        if rating:
            rating_value = int(rating)
            queryset = queryset.filter(
                rating__gte=rating_value,
                partner_type__in=['supplier', 'both']
            )

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # التاريخ
        date_from = self.cleaned_data.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.cleaned_data.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class WarehouseFilterForm(BaseFilterForm):
    """نموذج فلترة المستودعات - محدث 100%"""

    branch = forms.ModelChoiceField(
        label=_('الفرع'),
        queryset=Branch.objects.none(),
        required=False,
        empty_label=_('جميع الفروع'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-control': 'select2',
            'data-placeholder': _('اختر الفرع'),
            'data-kt-filter': 'branch',
        })
    )

    warehouse_type = forms.ChoiceField(
        label=_('نوع المستودع'),
        choices=[
            ('', _('جميع الأنواع')),
            ('main', _('رئيسي')),
            ('branch', _('فرعي')),
            ('transit', _('ترانزيت')),
            ('damaged', _('تالف')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'warehouse_type',
        })
    )

    keeper = forms.ModelChoiceField(
        label=_('أمين المستودع'),
        queryset=User.objects.none(),
        required=False,
        empty_label=_('جميع الأمناء'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-control': 'select2',
            'data-kt-filter': 'keeper',
        })
    )

    has_keeper = forms.ChoiceField(
        label=_('وجود أمين'),
        choices=[
            ('', _('الكل')),
            ('1', _('له أمين')),
            ('0', _('بدون أمين')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'has_keeper',
        })
    )

    location = forms.CharField(
        label=_('الموقع'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('الموقع'),
            'data-kt-filter': 'location',
        })
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if company:
            # فلترة الفروع
            branches = Branch.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            # فلترة حسب صلاحيات المستخدم
            if user and not user.is_superuser:
                if hasattr(user, 'profile') and hasattr(user.profile, 'allowed_branches'):
                    allowed_branches = user.profile.allowed_branches.all()
                    if allowed_branches.exists():
                        branches = branches.filter(
                            id__in=allowed_branches.values_list('id', flat=True)
                        )

            self.fields['branch'].queryset = branches

            # أمناء المستودعات
            self.fields['keeper'].queryset = User.objects.filter(
                company=company,
                is_active=True
            ).order_by('first_name', 'last_name')

    def get_queryset(self, queryset):
        """تطبيق الفلاتر على queryset"""

        # البحث العام
        search = self.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search)
            )

        # الفرع
        branch = self.cleaned_data.get('branch')
        if branch:
            queryset = queryset.filter(branch=branch)

        # نوع المستودع
        warehouse_type = self.cleaned_data.get('warehouse_type')
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)

        # الموقع
        location = self.cleaned_data.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        # أمين المستودع
        keeper = self.cleaned_data.get('keeper')
        if keeper:
            queryset = queryset.filter(keeper=keeper)

        # وجود أمين
        has_keeper = self.cleaned_data.get('has_keeper')
        if has_keeper == '1':
            queryset = queryset.exclude(keeper__isnull=True)
        elif has_keeper == '0':
            queryset = queryset.filter(keeper__isnull=True)

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # التاريخ
        date_from = self.cleaned_data.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.cleaned_data.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class GlobalSearchForm(forms.Form):
    """نموذج البحث الشامل في جميع البيانات الأساسية - محدث"""

    SEARCH_IN_CHOICES = [
        ('all', _('البحث في الكل')),
        ('items', _('الأصناف فقط')),
        ('partners', _('الشركاء التجاريين فقط')),
        ('warehouses', _('المستودعات فقط')),
        ('categories', _('التصنيفات فقط')),
        ('units', _('وحدات القياس فقط')),
    ]

    query = forms.CharField(
        label=_('كلمة البحث'),
        min_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': _('ابحث عن أي شيء...'),
            'autofocus': True,
            'data-kt-search-element': 'input',
            'autocomplete': 'off'
        })
    )

    search_in = forms.ChoiceField(
        label=_('البحث في'),
        choices=SEARCH_IN_CHOICES,
        initial='all',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'data-kt-search-element': 'filter',
        })
    )

    limit_results = forms.IntegerField(
        label=_('عدد النتائج'),
        initial=10,
        min_value=5,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'min': '5',
            'max': '50'
        })
    )

    def search(self, company, user=None):
        """تنفيذ البحث وإرجاع النتائج"""
        if not self.is_valid():
            return {}

        query = self.cleaned_data.get('query', '').strip()
        search_in = self.cleaned_data.get('search_in', 'all')
        limit = self.cleaned_data.get('limit_results', 10)

        if not query or len(query) < 2:
            return {}

        results = {}

        # البحث في الأصناف
        if search_in in ['all', 'items']:
            items = Item.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(name_en__icontains=query) |
                Q(barcode__icontains=query) |
                Q(manufacturer__icontains=query) |
                Q(specifications__icontains=query)
            ).select_related('category', 'unit')[:limit]

            if items:
                results['items'] = {
                    'title': _('الأصناف'),
                    'items': items,
                    'count': len(items),
                    'icon': 'fas fa-boxes',
                    'url_name': 'base_data:item_list',
                }

        # البحث في الشركاء
        if search_in in ['all', 'partners']:
            partners = BusinessPartner.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(name_en__icontains=query) |
                Q(phone__icontains=query) |
                Q(mobile__icontains=query) |
                Q(email__icontains=query) |
                Q(tax_number__icontains=query) |
                Q(contact_person__icontains=query)
            )[:limit]

            if partners:
                results['partners'] = {
                    'title': _('الشركاء التجاريون'),
                    'items': partners,
                    'count': len(partners),
                    'icon': 'fas fa-users',
                    'url_name': 'base_data:partner_list',
                }

        # البحث في المستودعات
        if search_in in ['all', 'warehouses']:
            warehouses = Warehouse.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(location__icontains=query)
            ).select_related('branch', 'keeper')[:limit]

            if warehouses:
                results['warehouses'] = {
                    'title': _('المستودعات'),
                    'items': warehouses,
                    'count': len(warehouses),
                    'icon': 'fas fa-warehouse',
                    'url_name': 'base_data:warehouse_list',
                }

        # البحث في التصنيفات
        if search_in in ['all', 'categories']:
            categories = ItemCategory.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(name_en__icontains=query)
            )[:limit]

            if categories:
                results['categories'] = {
                    'title': _('تصنيفات الأصناف'),
                    'items': categories,
                    'count': len(categories),
                    'icon': 'fas fa-sitemap',
                    'url_name': 'base_data:category_list',
                }

        # البحث في وحدات القياس
        if search_in in ['all', 'units']:
            units = UnitOfMeasure.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(name_en__icontains=query)
            )[:limit]

            if units:
                results['units'] = {
                    'title': _('وحدات القياس'),
                    'items': units,
                    'count': len(units),
                    'icon': 'fas fa-balance-scale',
                    'url_name': 'base_data:unit_list',
                }

        return results


class ExportForm(forms.Form):
    """نموذج تصدير البيانات - محدث"""

    FORMAT_CHOICES = [
        ('xlsx', _('Excel (XLSX)')),
        ('csv', _('CSV')),
        ('pdf', _('PDF')),
        ('json', _('JSON')),
    ]

    format = forms.ChoiceField(
        label=_('صيغة التصدير'),
        choices=FORMAT_CHOICES,
        initial='xlsx',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

    include_inactive = forms.BooleanField(
        label=_('تضمين البيانات غير النشطة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch',
        })
    )

    selected_fields = forms.MultipleChoiceField(
        label=_('الحقول المطلوبة'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        })
    )

    date_range = forms.ChoiceField(
        label=_('نطاق التاريخ'),
        choices=[
            ('all', _('جميع البيانات')),
            ('today', _('اليوم')),
            ('yesterday', _('أمس')),
            ('week', _('هذا الأسبوع')),
            ('month', _('هذا الشهر')),
            ('quarter', _('هذا الربع')),
            ('year', _('هذا العام')),
            ('custom', _('نطاق مخصص')),
        ],
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleCustomDateRange()'
        })
    )

    custom_date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    custom_date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    compress_file = forms.BooleanField(
        label=_('ضغط الملف'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch',
        }),
        help_text=_('إنشاء ملف مضغوط ZIP')
    )

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # بناء خيارات الحقول من النموذج
        field_choices = []
        for field in model_class._meta.fields:
            if field.name not in ['id', 'company', 'created_by', 'updated_by', 'password']:
                verbose_name = field.verbose_name or field.name
                field_choices.append((field.name, verbose_name))

        # إضافة الحقول المرتبطة المهمة
        for field in model_class._meta.fields:
            if hasattr(field, 'related_model') and field.related_model:
                if field.name in ['category', 'unit', 'branch', 'salesperson']:
                    verbose_name = f"{field.verbose_name} ({_('اسم')})"
                    field_choices.append(f'{field.name}__name', verbose_name)

        self.fields['selected_fields'].choices = field_choices
        # تحديد جميع الحقول الأساسية افتراضياً
        basic_fields = [choice[0] for choice in field_choices[:10]]  # أول 10 حقول
        self.fields['selected_fields'].initial = basic_fields

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')

        # التحقق من التواريخ المخصصة
        if date_range == 'custom':
            custom_date_from = cleaned_data.get('custom_date_from')
            custom_date_to = cleaned_data.get('custom_date_to')

            if not custom_date_from:
                self.add_error('custom_date_from', _('تاريخ البداية مطلوب للنطاق المخصص'))

            if not custom_date_to:
                self.add_error('custom_date_to', _('تاريخ النهاية مطلوب للنطاق المخصص'))

            if custom_date_from and custom_date_to and custom_date_from > custom_date_to:
                self.add_error('custom_date_to', _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))

        # التحقق من الحقول المحددة
        selected_fields = cleaned_data.get('selected_fields', [])
        if not selected_fields:
            self.add_error('selected_fields', _('يجب اختيار حقل واحد على الأقل'))

        return cleaned_data

    def get_date_filter(self):
        """الحصول على فلتر التاريخ"""
        date_range = self.cleaned_data.get('date_range')
        today = datetime.now().date()

        if date_range == 'today':
            return {'created_at__date': today}
        elif date_range == 'yesterday':
            yesterday = today - timedelta(days=1)
            return {'created_at__date': yesterday}
        elif date_range == 'week':
            week_start = today - timedelta(days=today.weekday())
            return {'created_at__date__gte': week_start}
        elif date_range == 'month':
            month_start = today.replace(day=1)
            return {'created_at__date__gte': month_start}
        elif date_range == 'quarter':
            quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
            return {'created_at__date__gte': quarter_start}
        elif date_range == 'year':
            year_start = today.replace(month=1, day=1)
            return {'created_at__date__gte': year_start}
        elif date_range == 'custom':
            date_from = self.cleaned_data.get('custom_date_from')
            date_to = self.cleaned_data.get('custom_date_to')
            filter_dict = {}
            if date_from:
                filter_dict['created_at__date__gte'] = date_from
            if date_to:
                filter_dict['created_at__date__lte'] = date_to
            return filter_dict

        return {}  # جميع البيانات


# نماذج خاصة بـ DataTables
class DataTablesFilterForm(forms.Form):
    """نموذج أساسي لفلاتر DataTables"""

    draw = forms.IntegerField(widget=forms.HiddenInput())
    start = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    length = forms.IntegerField(initial=25, widget=forms.HiddenInput())
    search_value = forms.CharField(required=False, widget=forms.HiddenInput())
    order_column = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    order_dir = forms.CharField(initial='asc', widget=forms.HiddenInput())


class QuickSearchForm(forms.Form):
    """نموذج البحث السريع في الهيدر"""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('بحث سريع...'),
            'data-kt-search-element': 'input',
            'autocomplete': 'off'
        })
    )

    def search_all(self, company, limit=5):
        """البحث السريع في جميع النماذج"""
        query = self.cleaned_data.get('q', '').strip()
        if not query or len(query) < 2:
            return []

        results = []

        # البحث في الأصناف
        items = Item.objects.filter(
            company=company,
            is_active=True
        ).filter(
            Q(code__icontains=query) | Q(name__icontains=query)
        )[:limit]

        for item in items:
            results.append({
                'type': 'item',
                'title': item.name,
                'subtitle': f'{item.code} - {item.category.name}',
                'url': f'/base-data/items/{item.pk}/',
                'icon': 'fas fa-box'
            })

        # البحث في الشركاء
        partners = BusinessPartner.objects.filter(
            company=company,
            is_active=True
        ).filter(
            Q(code__icontains=query) | Q(name__icontains=query)
        )[:limit]

        for partner in partners:
            results.append({
                'type': 'partner',
                'title': partner.name,
                'subtitle': f'{partner.code} - {partner.get_partner_type_display()}',
                'url': f'/base-data/partners/{partner.pk}/',
                'icon': 'fas fa-user-tie'
            })

        return results[:limit]
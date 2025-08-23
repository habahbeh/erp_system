# apps/base_data/forms/filter_forms.py
"""
نماذج الفلترة والبحث
للاستخدام مع DataTables وواجهات البحث المتقدم
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from ..models import Item, ItemCategory, BusinessPartner, Warehouse, UnitOfMeasure
from core.models import Branch


class BaseFilterForm(forms.Form):
    """نموذج أساسي للفلترة - يحتوي على حقول مشتركة"""

    search = forms.CharField(
        label=_('بحث'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('بحث...'),
            'data-kt-filter': 'search',
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
            'data-hide-search': 'true',
            'data-minimum-results-for-search': 'Infinity',
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


class ItemFilterForm(BaseFilterForm):
    """نموذج فلترة الأصناف - للاستخدام مع DataTables"""

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
            'data-hide-search': 'true',
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

    stock_status = forms.ChoiceField(
        label=_('حالة المخزون'),
        choices=[
            ('', _('الكل')),
            ('in_stock', _('متوفر')),
            ('low_stock', _('مخزون منخفض')),
            ('out_of_stock', _('نفذ المخزون')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'stock_status',
        })
    )

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

        # فلترة التصنيفات حسب الشركة
        self.fields['category'].queryset = ItemCategory.objects.filter(
            company=company,
            is_active=True
        ).order_by('level', 'name')

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
                Q(manufacturer__icontains=search)
            )

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        # التصنيف
        category = self.cleaned_data.get('category')
        if category:
            # البحث في التصنيف وتصنيفاته الفرعية
            categories = [category]
            categories.extend(category.get_descendants())
            queryset = queryset.filter(category__in=categories)

        # الباركود
        has_barcode = self.cleaned_data.get('has_barcode')
        if has_barcode == '1':
            queryset = queryset.exclude(barcode='')
        elif has_barcode == '0':
            queryset = queryset.filter(Q(barcode='') | Q(barcode__isnull=True))

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

        # التاريخ
        date_from = self.cleaned_data.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.cleaned_data.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class BusinessPartnerFilterForm(BaseFilterForm):
    """نموذج فلترة الشركاء التجاريين"""

    partner_type = forms.ChoiceField(
        label=_('النوع'),
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

    city = forms.CharField(
        label=_('المدينة'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('المدينة'),
            'data-kt-filter': 'city',
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
                Q(tax_number__icontains=search)
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

        # المدينة
        city = self.cleaned_data.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        # الرقم الضريبي
        has_tax_number = self.cleaned_data.get('has_tax_number')
        if has_tax_number == '1':
            queryset = queryset.exclude(tax_number='')
        elif has_tax_number == '0':
            queryset = queryset.filter(Q(tax_number='') | Q(tax_number__isnull=True))

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        return queryset


class WarehouseFilterForm(BaseFilterForm):
    """نموذج فلترة المستودعات"""

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
        label=_('النوع'),
        choices=[('', _('الكل'))] + Warehouse.warehouse_type.field.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select form-select-sm',
            'data-kt-filter': 'warehouse_type',
        })
    )

    has_keeper = forms.ChoiceField(
        label=_('أمين المستودع'),
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

    def __init__(self, company, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.user = user

        # فلترة الفروع
        branches = Branch.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        # فلترة حسب صلاحيات المستخدم
        if user and not user.is_superuser:
            if hasattr(user, 'profile'):
                allowed_branches = user.profile.allowed_branches.all()
                if allowed_branches.exists():
                    branches = branches.filter(
                        id__in=allowed_branches.values_list('id', flat=True)
                    )

        self.fields['branch'].queryset = branches

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

        # النوع
        warehouse_type = self.cleaned_data.get('warehouse_type')
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)

        # أمين المستودع
        has_keeper = self.cleaned_data.get('has_keeper')
        if has_keeper == '1':
            queryset = queryset.exclude(keeper__isnull=True)
        elif has_keeper == '0':
            queryset = queryset.filter(keeper__isnull=True)

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        return queryset


class GlobalSearchForm(forms.Form):
    """نموذج البحث الشامل في جميع البيانات الأساسية"""

    SEARCH_IN_CHOICES = [
        ('all', _('الكل')),
        ('items', _('الأصناف')),
        ('partners', _('الشركاء التجاريين')),
        ('warehouses', _('المستودعات')),
    ]

    query = forms.CharField(
        label=_('كلمة البحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': _('ابحث عن أي شيء...'),
            'autofocus': True,
            'data-kt-search-element': 'input',
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

    def search(self, company):
        """تنفيذ البحث وإرجاع النتائج"""
        if not self.is_valid():
            return {}

        query = self.cleaned_data.get('query', '').strip()
        search_in = self.cleaned_data.get('search_in', 'all')

        if not query:
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
                Q(barcode__icontains=query)
            )[:10]

            if items:
                results['items'] = {
                    'title': _('الأصناف'),
                    'items': items,
                    'count': items.count(),
                    'icon': 'fa-boxes',
                }

        # البحث في الشركاء
        if search_in in ['all', 'partners']:
            partners = BusinessPartner.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(phone__icontains=query) |
                Q(mobile__icontains=query)
            )[:10]

            if partners:
                results['partners'] = {
                    'title': _('الشركاء التجاريين'),
                    'items': partners,
                    'count': partners.count(),
                    'icon': 'fa-users',
                }

        # البحث في المستودعات
        if search_in in ['all', 'warehouses']:
            warehouses = Warehouse.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(code__icontains=query) |
                Q(name__icontains=query)
            )[:10]

            if warehouses:
                results['warehouses'] = {
                    'title': _('المستودعات'),
                    'items': warehouses,
                    'count': warehouses.count(),
                    'icon': 'fa-warehouse',
                }

        return results


# نماذج التصدير
class ExportForm(forms.Form):
    """نموذج تصدير البيانات"""

    FORMAT_CHOICES = [
        ('xlsx', _('Excel (XLSX)')),
        ('csv', _('CSV')),
        ('pdf', _('PDF')),
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
        label=_('تضمين غير النشط'),
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

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # بناء خيارات الحقول من النموذج
        field_choices = []
        for field in model_class._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                field_choices.append(
                    (field.name, field.verbose_name)
                )

        self.fields['selected_fields'].choices = field_choices
        # تحديد جميع الحقول افتراضياً
        self.fields['selected_fields'].initial = [c[0] for c in field_choices]
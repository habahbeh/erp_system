# apps/base_data/forms/filter_forms.py
"""
نماذج الفلترة والبحث - محدث حسب models.py والمتطلبات
للاستخدام مع DataTables وواجهات البحث المتقدم
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from decimal import Decimal

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


class ItemFilterForm(BaseFilterForm):
    """نموذج فلترة الأصناف"""

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
                Q(manufacturer__icontains=search)
            )

        # الحالة
        is_active = self.cleaned_data.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # التصنيف
        category = self.cleaned_data.get('category')
        if category:
            # البحث في التصنيف وتصنيفاته الفرعية
            categories = [category]
            children = ItemCategory.objects.filter(parent=category)
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

        # الحالة الضريبية
        tax_status = self.cleaned_data.get('tax_status')
        if tax_status:
            queryset = queryset.filter(tax_status=tax_status)

        # المدينة
        city = self.cleaned_data.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        # الرقم الضريبي
        has_tax_number = self.cleaned_data.get('has_tax_number')
        if has_tax_number == '1':
            queryset = queryset.exclude(Q(tax_number='') | Q(tax_number__isnull=True))
        elif has_tax_number == '0':
            queryset = queryset.filter(Q(tax_number='') | Q(tax_number__isnull=True))

        # مندوب المبيعات
        salesperson = self.cleaned_data.get('salesperson')
        if salesperson:
            queryset = queryset.filter(salesperson=salesperson)

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
    """نموذج البحث الشامل في جميع البيانات الأساسية"""

    SEARCH_IN_CHOICES = [
        ('all', _('البحث في الكل')),
        ('items', _('الأصناف فقط')),
        ('partners', _('الشركاء التجاريين فقط')),
        ('warehouses', _('المستودعات فقط')),
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
                Q(name_en__icontains=query) |
                Q(barcode__icontains=query)
            )[:10]

            if items:
                results['items'] = {
                    'title': _('الأصناف'),
                    'items': items,
                    'count': items.count(),
                    'icon': 'fas fa-boxes',
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
                Q(email__icontains=query)
            )[:10]

            if partners:
                results['partners'] = {
                    'title': _('الشركاء التجاريون'),
                    'items': partners,
                    'count': partners.count(),
                    'icon': 'fas fa-users',
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
            )[:10]

            if warehouses:
                results['warehouses'] = {
                    'title': _('المستودعات'),
                    'items': warehouses,
                    'count': warehouses.count(),
                    'icon': 'fas fa-warehouse',
                }

        return results


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
            ('week', _('هذا الأسبوع')),
            ('month', _('هذا الشهر')),
            ('year', _('هذا العام')),
            ('custom', _('نطاق مخصص')),
        ],
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
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

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # بناء خيارات الحقول من النموذج
        field_choices = []
        for field in model_class._meta.fields:
            if field.name not in ['id', 'company', 'created_by', 'updated_by']:
                field_choices.append(
                    (field.name, field.verbose_name or field.name)
                )

        self.fields['selected_fields'].choices = field_choices
        # تحديد جميع الحقول افتراضياً
        self.fields['selected_fields'].initial = [c[0] for c in field_choices]

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

        return cleaned_data
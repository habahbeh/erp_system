# apps/base_data/admin.py
"""
Admin interface للبيانات الأساسية
مع Bootstrap styling وإعدادات متقدمة
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, F
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UnitOfMeasure, ItemCategory, Item, ItemConversion, ItemComponent,
    Warehouse, BusinessPartner, Customer, Supplier, WarehouseItem
)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'name_en', 'items_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'company']
    search_fields = ['code', 'name', 'name_en']
    ordering = ['code']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ['code', 'name', 'name_en', 'company', 'branch', 'is_active']
        }),
        (_('تتبع العمليات'), {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    def items_count(self, obj):
        count = obj.item_set.count()
        return format_html('<span class="badge bg-primary">{}</span>', count)

    items_count.short_description = _('عدد الأصناف')

    actions = ['activate_units', 'deactivate_units']

    def activate_units(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, 'تم تفعيل {} وحدة قياس'.format(updated))

    activate_units.short_description = _('تفعيل الوحدات المحددة')

    def deactivate_units(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, 'تم إلغاء تفعيل {} وحدة قياس'.format(updated))

    deactivate_units.short_description = _('إلغاء تفعيل الوحدات المحددة')


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['indented_name', 'code', 'level', 'items_count', 'parent', 'is_active']
    list_filter = ['level', 'is_active', 'created_at', 'company']
    search_fields = ['code', 'name', 'name_en']
    ordering = ['level', 'name']
    readonly_fields = ['level', 'created_by', 'updated_by', 'created_at', 'updated_at']

    fieldsets = (
        (_('معلومات التصنيف'), {
            'fields': ['parent', 'code', 'name', 'name_en', 'level']
        }),
        (_('الشركة والفرع'), {
            'fields': ['company', 'branch', 'is_active']
        }),
        (_('تتبع العمليات'), {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    def indented_name(self, obj):
        indent = '--' * (obj.level - 1)
        return format_html('{} {}', indent, obj.name)

    indented_name.short_description = _('اسم التصنيف')

    def items_count(self, obj):
        count = obj.items.count()
        color = 'success' if count > 0 else 'secondary'
        return format_html('<span class="badge bg-{}">{}</span>', color, count)

    items_count.short_description = _('عدد الأصناف')


class ItemConversionInline(admin.TabularInline):
    model = ItemConversion
    extra = 1
    fields = ['from_unit', 'to_unit', 'factor']


class ItemComponentInline(admin.TabularInline):
    model = ItemComponent
    fk_name = 'parent_item'
    extra = 1
    fields = ['component_item', 'quantity', 'unit', 'waste_percentage', 'notes']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'category', 'unit', 'purchase_price',
        'sale_price', 'profit_margin', 'stock_status', 'is_active'
    ]
    list_filter = [
        'category', 'unit', 'manufacturer', 'is_active',
        'is_inactive', 'created_at', 'company'
    ]
    search_fields = ['code', 'name', 'name_en', 'barcode', 'manufacturer']
    ordering = ['code']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']
    inlines = [ItemConversionInline, ItemComponentInline]

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': [
                'code', 'name', 'name_en', 'barcode',
                'category', 'unit', 'manufacturer'
            ]
        }),
        (_('الأسعار والضرائب'), {
            'fields': ['purchase_price', 'sale_price', 'tax_rate']
        }),
        (_('الحسابات المحاسبية'), {
            'fields': [
                'sales_account', 'purchase_account',
                'inventory_account', 'cost_of_goods_account'
            ],
            'classes': ['collapse']
        }),
        (_('معلومات المخزون'), {
            'fields': ['minimum_quantity', 'maximum_quantity']
        }),
        (_('معلومات إضافية'), {
            'fields': ['specifications', 'weight', 'image', 'notes', 'substitute_items']
        }),
        (_('الحالة'), {
            'fields': ['company', 'branch', 'is_active', 'is_inactive']
        }),
        (_('تتبع العمليات'), {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    filter_horizontal = ['substitute_items']

    def profit_margin(self, obj):
        if obj.purchase_price and obj.sale_price:
            margin = obj.sale_price - obj.purchase_price
            percentage = (margin / obj.purchase_price) * 100 if obj.purchase_price > 0 else 0
            color = 'success' if percentage >= 20 else 'warning' if percentage >= 10 else 'danger'

            return format_html(
                '<span class="badge bg-{}">{}</span>',
                color, round(percentage, 1)
            ) + '%'
        return '-'

    profit_margin.short_description = _('هامش الربح')

    def stock_status(self, obj):
        # يحتاج إلى حساب من WarehouseItem
        total_stock = obj.warehouse_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        if total_stock <= 0:
            return format_html('<span class="badge bg-danger">نفد</span>')
        elif total_stock <= obj.minimum_quantity:
            return format_html('<span class="badge bg-warning">منخفض</span>')
        else:
            return format_html('<span class="badge bg-success">متوفر</span>')

    stock_status.short_description = _('حالة المخزون')

    actions = ['duplicate_items', 'update_tax_rate', 'mark_inactive']

    def duplicate_items(self, request, queryset):
        duplicated = 0
        for item in queryset:
            item.pk = None
            item.code = "{}_COPY".format(item.code)
            item.barcode = None
            item.save()
            duplicated += 1
        self.message_user(request, 'تم تكرار {} صنف'.format(duplicated))

    duplicate_items.short_description = _('تكرار الأصناف المحددة')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'branch', 'warehouse_type',
        'keeper', 'items_count', 'total_value', 'is_active'
    ]
    list_filter = ['warehouse_type', 'is_active', 'branch', 'company']
    search_fields = ['code', 'name', 'location']
    ordering = ['name']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    fieldsets = (
        (_('معلومات المستودع'), {
            'fields': ['code', 'name', 'location', 'warehouse_type', 'keeper']
        }),
        (_('الشركة والفرع'), {
            'fields': ['company', 'branch', 'is_active']
        }),
        (_('تتبع العمليات'), {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    def items_count(self, obj):
        count = obj.warehouse_items.filter(quantity__gt=0).count()
        return format_html('<span class="badge bg-info">{}</span>', count)

    items_count.short_description = _('عدد الأصناف')

    def total_value(self, obj):
        total = obj.warehouse_items.aggregate(
            total=Sum(F('quantity') * F('average_cost'))
        )['total'] or 0
        return '{:,.0f} د.أ'.format(total)

    total_value.short_description = _('إجمالي القيمة')


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'partner_type', 'city', 'contact_person',
        'credit_limit', 'credit_rating', 'is_active'
    ]
    list_filter = [
        'partner_type', 'account_type', 'customer_category',
        'supplier_category', 'tax_status', 'city', 'is_active', 'company'
    ]
    search_fields = [
        'code', 'name', 'name_en', 'contact_person',
        'email', 'phone', 'mobile', 'tax_number'
    ]
    ordering = ['name']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': [
                'code', 'name', 'name_en', 'partner_type', 'account_type'
            ]
        }),
        (_('معلومات الاتصال'), {
            'fields': [
                'contact_person', 'phone', 'mobile', 'fax',
                'email', 'website'
            ]
        }),
        (_('العنوان'), {
            'fields': ['address', 'city', 'region']
        }),
        (_('معلومات ضريبية'), {
            'fields': [
                'tax_number', 'tax_status', 'commercial_register'
            ],
            'classes': ['collapse']
        }),
        (_('معلومات الائتمان'), {
            'fields': ['credit_limit', 'credit_period']
        }),
        (_('حقول العملاء'), {
            'fields': [
                'salesperson', 'discount_percentage', 'customer_category'
            ],
            'classes': ['collapse']
        }),
        (_('حقول الموردين'), {
            'fields': [
                'payment_terms', 'supplier_category', 'rating'
            ],
            'classes': ['collapse']
        }),
        (_('الحسابات المحاسبية'), {
            'fields': ['customer_account', 'supplier_account'],
            'classes': ['collapse']
        }),
        (_('معلومات إضافية'), {
            'fields': ['notes']
        }),
        (_('الشركة والحالة'), {
            'fields': ['company', 'branch', 'is_active']
        }),
        (_('تتبع العمليات'), {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    def credit_rating(self, obj):
        if obj.partner_type in ['customer', 'both']:
            if obj.credit_limit >= 100000:
                return format_html('<span class="badge bg-success">ممتاز</span>')
            elif obj.credit_limit >= 50000:
                return format_html('<span class="badge bg-warning">جيد</span>')
            else:
                return format_html('<span class="badge bg-secondary">عادي</span>')
        elif obj.partner_type in ['supplier', 'both']:
            stars = '⭐' * obj.rating
            return format_html('<span title="{} من 5">{}</span>', obj.rating, stars)
        return '-'

    credit_rating.short_description = _('التصنيف')

    actions = ['convert_to_both', 'send_statements']

    def convert_to_both(self, request, queryset):
        updated = queryset.update(partner_type='both')
        self.message_user(request, 'تم تحويل {} شريك إلى عميل ومورد'.format(updated))

    convert_to_both.short_description = _('تحويل إلى عميل ومورد')


@admin.register(Customer)
class CustomerAdmin(BusinessPartnerAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(partner_type__in=['customer', 'both'])


@admin.register(Supplier)
class SupplierAdmin(BusinessPartnerAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(partner_type__in=['supplier', 'both'])


@admin.register(WarehouseItem)
class WarehouseItemAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'warehouse', 'quantity', 'average_cost',
        'total_value', 'stock_status'
    ]
    list_filter = ['warehouse', 'warehouse__company', 'item__category']
    search_fields = [
        'item__code', 'item__name', 'warehouse__name'
    ]
    ordering = ['-quantity']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    def total_value(self, obj):
        total = obj.quantity * obj.average_cost
        return '{:,.2f} د.أ'.format(total)

    total_value.short_description = _('إجمالي القيمة')

    def stock_status(self, obj):
        if obj.quantity <= 0:
            return format_html('<span class="badge bg-danger">نفد</span>')
        elif obj.quantity <= obj.item.minimum_quantity:
            return format_html('<span class="badge bg-warning">منخفض</span>')
        else:
            return format_html('<span class="badge bg-success">جيد</span>')

    stock_status.short_description = _('الحالة')

    actions = ['zero_stock', 'adjust_costs']

    def zero_stock(self, request, queryset):
        updated = queryset.update(quantity=0)
        self.message_user(request, 'تم تصفير {} رصيد'.format(updated))

    zero_stock.short_description = _('تصفير المخزون')


# تخصيص موقع الإدارة
admin.site.site_header = _('إدارة نظام ERP')
admin.site.site_title = _('نظام ERP')
admin.site.index_title = _('لوحة التحكم الرئيسية')
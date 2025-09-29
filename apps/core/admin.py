# apps/core/admin.py
"""
Django Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Currency, Company, Branch, User, UserProfile, Warehouse,
    BusinessPartner,PartnerRepresentative, Item, ItemCategory, Brand, UnitOfMeasure,
    VariantAttribute, VariantValue, ItemVariant, ItemVariantAttributeValue,
    NumberingSequence, CustomPermission, SystemSettings, AuditLog, PriceList, PriceListItem
)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_base', 'is_active']
    list_filter = ['is_base', 'is_active']
    search_fields = ['code', 'name', 'name_en']
    list_editable = ['exchange_rate', 'is_active']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tax_number', 'base_currency', 'is_active']
    list_filter = ['base_currency', 'is_active', 'country']
    search_fields = ['name', 'name_en', 'tax_number', 'commercial_register']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'code', 'is_main', 'is_active']
    list_filter = ['company', 'is_main', 'is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'ملف المستخدم'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'company', 'branch', 'is_staff', 'is_active']
    list_filter = ['company', 'branch', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('معلومات الشركة'), {
            'fields': ('company', 'branch', 'default_warehouse', 'phone', 'emp_number')
        }),
        (_('الصلاحيات الإضافية'), {
            'fields': ('max_discount_percentage', 'signature')
        }),
        (_('تفضيلات الواجهة'), {
            'fields': ('ui_language', 'theme')
        }),
    )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'code', 'is_main', 'allow_negative_stock', 'is_active']
    list_filter = ['company', 'is_main', 'allow_negative_stock', 'is_active']
    search_fields = ['name', 'name_en', 'code']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


class PartnerRepresentativeInline(admin.TabularInline):
    """إدراج المندوبين في صفحة العميل"""
    model = PartnerRepresentative
    extra = 1
    fields = ('representative_name', 'phone', 'is_primary', 'notes')


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    """إدارة العملاء في الـ Admin"""
    list_display = [
        'code', 'name', 'partner_type', 'account_type',
        'tax_status', 'get_representatives_count', 'is_active'
    ]
    list_filter = [
        'partner_type', 'account_type', 'tax_status',
        'is_active', 'created_at', 'company'
    ]
    search_fields = [
        'code', 'name', 'name_en', 'email', 'phone',
        'mobile', 'tax_number', 'commercial_register'
    ]
    autocomplete_fields = ['company', 'created_by']

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (
                'partner_type', 'code', 'name', 'name_en',
                'account_type', 'company'
            )
        }),
        ('معلومات الاتصال', {
            'fields': (
                'contact_person', 'phone', 'mobile', 'fax',
                'email', 'address', 'city', 'region'
            )
        }),
        ('المعلومات الضريبية', {
            'fields': (
                'tax_number', 'tax_status', 'commercial_register',
                'tax_exemption_start_date', 'tax_exemption_end_date',
                'tax_exemption_reason'
            )
        }),
        ('حدود الائتمان', {
            'fields': ('credit_limit', 'credit_period')
        }),
        ('المرفقات', {
            'fields': (
                'commercial_register_file', 'payment_letter_file',
                'tax_exemption_file', 'other_attachments'
            )
        }),
        ('أخرى', {
            'fields': ('notes', 'is_active', 'created_by')
        }),
    )

    inlines = [PartnerRepresentativeInline]

    def get_representatives_count(self, obj):
        """عدد المندوبين"""
        return obj.representatives.count()

    get_representatives_count.short_description = 'عدد المندوبين'

    def save_model(self, request, obj, form, change):
        """حفظ مع إضافة المستخدم الحالي"""
        if not change:  # إنشاء جديد
            obj.created_by = request.user
            if not obj.company:
                obj.company = request.user.company
        super().save_model(request, obj, form, change)


@admin.register(PartnerRepresentative)
class PartnerRepresentativeAdmin(admin.ModelAdmin):
    """إدارة مندوبي العملاء"""
    list_display = [
        'partner', 'representative_name', 'phone', 'is_primary', 'is_active'
    ]
    list_filter = ['is_primary', 'is_active', 'company']
    search_fields = [
        'partner__name', 'representative_name', 'phone', 'notes'
    ]
    autocomplete_fields = ['partner', 'company']

    fieldsets = (
        ('معلومات المندوب', {
            'fields': ('partner', 'representative_name', 'phone', 'is_primary')
        }),
        ('تفاصيل إضافية', {
            'fields': ('notes', 'company', 'is_active')
        }),
    )

    def save_model(self, request, obj, form, change):
        """حفظ مع إضافة المستخدم الحالي"""
        if not change:  # إنشاء جديد
            obj.created_by = request.user
            if not obj.company:
                obj.company = request.user.company
        super().save_model(request, obj, form, change)


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'level', 'company', 'is_active']
    list_filter = ['level', 'company', 'is_active']
    search_fields = ['name', 'name_en', 'code']
    readonly_fields = ['level', 'created_at', 'updated_at', 'created_by']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'company', 'is_active']
    list_filter = ['country', 'company', 'is_active']
    search_fields = ['name', 'name_en']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'name_en', 'code']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


class ItemVariantInline(admin.TabularInline):
    model = ItemVariant
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemVariantInline]
    list_display = ['name', 'code','item_code', 'category', 'brand', 'company', 'has_variants', 'is_active']
    list_filter = ['category', 'brand', 'unit_of_measure', 'currency', 'has_variants', 'company', 'is_active']
    search_fields = ['name', 'name_en', 'code', 'catalog_number', 'barcode']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = [
        (_('المعلومات الأساسية'), {
            'fields': ['code','item_code', 'name', 'name_en', 'catalog_number', 'barcode']
        }),
        (_('التصنيف والعلامة'), {
            'fields': ['category', 'brand']
        }),
        (_('وحدة القياس والعملة'), {
            'fields': ['unit_of_measure', 'currency']
        }),
        (_('الحسابات المحاسبية'), {
            'fields': ['sales_account', 'purchase_account', 'inventory_account', 'cost_of_goods_account']
        }),
        (_('الضرائب'), {
            'fields': ['tax_rate']
        }),
        (_('الوصف'), {
            'fields': ['short_description', 'description']
        }),
        (_('المتغيرات'), {
            'fields': ['has_variants']
        }),
        (_('الأبعاد الفيزيائية'), {
            'fields': ['weight', 'length', 'width', 'height']
        }),
        (_('معلومات التصنيع'), {
            'fields': ['manufacturer', 'model_number']
        }),
        (_('الملفات'), {
            'fields': ['image', 'attachment', 'attachment_name']
        }),
        (_('ملاحظات'), {
            'fields': ['notes', 'additional_notes']
        }),
        (_('الحالة'), {
            'fields': ['is_active']
        }),
    ]


@admin.register(VariantAttribute)
class VariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_required', 'sort_order', 'company', 'is_active']
    list_filter = ['is_required', 'company', 'is_active']
    search_fields = ['name', 'name_en', 'display_name']
    list_editable = ['sort_order', 'is_required']


class VariantValueInline(admin.TabularInline):
    model = VariantValue
    extra = 0


@admin.register(VariantValue)
class VariantValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'display_value', 'sort_order', 'company', 'is_active']
    list_filter = ['attribute', 'company', 'is_active']
    search_fields = ['value', 'value_en', 'display_value']
    list_editable = ['sort_order']


@admin.register(ItemVariant)
class ItemVariantAdmin(admin.ModelAdmin):
    list_display = ['item', 'code', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['item__name', 'code', 'catalog_number', 'barcode']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(NumberingSequence)
class NumberingSequenceAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'prefix', 'next_number', 'company', 'is_active']
    list_filter = ['document_type', 'yearly_reset', 'company', 'is_active']
    search_fields = ['document_type', 'prefix']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category']
    list_filter = ['category']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['users', 'groups']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['company', 'negative_stock_allowed', 'stock_valuation_method', 'customer_credit_check']
    list_filter = ['negative_stock_allowed', 'stock_valuation_method', 'customer_credit_check',
                   'auto_create_journal_entries']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_repr']
    list_filter = ['action', 'model_name', 'company', 'timestamp']
    search_fields = ['object_repr', 'user__username']
    readonly_fields = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr', 'old_values',
                       'new_values', 'ip_address']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'currency', 'is_default', 'is_active', 'company']
    list_filter = ['currency', 'is_default', 'is_active', 'company']
    search_fields = ['name', 'code']

@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    list_display = ['price_list', 'item', 'variant', 'price', 'is_active']
    list_filter = ['price_list', 'is_active']
    search_fields = ['item__name', 'variant__code']


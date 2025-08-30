# apps/core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Company, Currency, Warehouse, Branch, User, UserProfile,
    UnitOfMeasure, ItemCategory, Brand, BusinessPartner, Item,
    VariantAttribute, VariantValue, ItemVariant, ItemVariantAttributeValue,
    NumberingSequence, CustomPermission, SystemSettings, AuditLog
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tax_number', 'city', 'country', 'is_active']
    list_filter = ['is_active', 'country', 'city']
    search_fields = ['name', 'name_en', 'tax_number']
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'name_en', 'logo')
        }),
        (_('معلومات قانونية'), {
            'fields': ('tax_number', 'commercial_register', 'default_tax_rate')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('phone', 'email', 'address', 'city', 'country')
        }),
        (_('السنة المالية'), {
            'fields': ('fiscal_year_start_month', 'fiscal_year_start_day')
        }),
        (_('الحالة'), {
            'fields': ('is_active',)
        }),
    )


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'symbol', 'exchange_rate', 'is_base', 'is_active']
    list_filter = ['is_base', 'is_active']
    search_fields = ['name', 'code', 'symbol']
    list_editable = ['exchange_rate']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'branch', 'is_main', 'manager']
    list_filter = ['company', 'branch', 'is_main', 'is_active']
    search_fields = ['name', 'code']
    # raw_id_fields = ['manager']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'is_main', 'is_active']
    list_filter = ['company', 'is_main', 'is_active']
    search_fields = ['name', 'code']
    # raw_id_fields = ['default_warehouse']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('ملف المستخدم')
    filter_horizontal = ['allowed_branches', 'allowed_warehouses']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'company', 'branch', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'company', 'branch']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'emp_number']

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('معلومات الشركة'), {
            'fields': ('company', 'branch', 'emp_number', 'phone')
        }),
        (_('الإعدادات'), {
            'fields': ('default_warehouse', 'max_discount_percentage', 'signature')
        }),
        (_('واجهة المستخدم'), {
            'fields': ('ui_language', 'theme')
        }),
    )


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'code', 'name_en']


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'level', 'company']
    list_filter = ['company', 'level', 'is_active']
    search_fields = ['name', 'code', 'name_en']
    # raw_id_fields = ['parent']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'country', 'is_active']
    list_filter = ['company', 'country', 'is_active']
    search_fields = ['name', 'name_en', 'country']


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'partner_type', 'account_type', 'company', 'sales_representative']
    list_filter = ['company', 'partner_type', 'account_type', 'tax_status', 'is_active']
    search_fields = ['name', 'code', 'name_en', 'phone', 'email']
    # raw_id_fields = ['sales_representative']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('partner_type', 'code', 'name', 'name_en', 'account_type')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('contact_person', 'phone', 'mobile', 'fax', 'email')
        }),
        (_('العنوان'), {
            'fields': ('address', 'city', 'region')
        }),
        (_('معلومات ضريبية'), {
            'fields': ('tax_number', 'tax_status', 'commercial_register')
        }),
        (_('الائتمان'), {
            'fields': ('credit_limit', 'credit_period')
        }),
        (_('المندوب'), {
            'fields': ('sales_representative',)
        }),
        (_('إضافية'), {
            'fields': ('notes',)
        }),
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'unit_of_measure', 'company']
    list_filter = ['company', 'category', 'brand', 'currency', 'has_variants', 'is_active']
    search_fields = ['name', 'code', 'name_en', 'sku', 'barcode']
    # raw_id_fields = ['category', 'brand', 'unit_of_measure', 'currency', 'default_warehouse']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('code', 'name', 'name_en', 'sku', 'barcode')
        }),
        (_('التصنيف'), {
            'fields': ('category', 'brand', 'unit_of_measure', 'currency', 'default_warehouse')
        }),
        (_('الأسعار'), {
            'fields': ('tax_rate',)
        }),
        (_('الوصف'), {
            'fields': ('short_description', 'description', 'features')
        }),
        (_('الأبعاد'), {
            'fields': ('weight', 'length', 'width', 'height')
        }),
        (_('معلومات إضافية'), {
            'fields': ('manufacturer', 'model_number', 'has_variants')
        }),
        (_('الملفات'), {
            'fields': ('image', 'attachment', 'attachment_name')
        }),
        (_('ملاحظات'), {
            'fields': ('notes', 'additional_notes')
        }),
    )


@admin.register(VariantAttribute)
class VariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'company', 'is_required', 'sort_order']
    list_filter = ['company', 'is_required', 'is_active']
    search_fields = ['name', 'name_en', 'display_name']
    list_editable = ['sort_order']


@admin.register(VariantValue)
class VariantValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'display_value', 'sort_order']
    list_filter = ['attribute']
    search_fields = ['value', 'value_en', 'display_value']
    list_editable = ['sort_order']
    # raw_id_fields = ['attribute']


class ItemVariantAttributeValueInline(admin.TabularInline):
    model = ItemVariantAttributeValue
    extra = 0
    # raw_id_fields = ['attribute', 'value']


@admin.register(ItemVariant)
class ItemVariantAdmin(admin.ModelAdmin):
    list_display = ['item', 'code', 'sku', 'barcode', 'is_active']
    list_filter = ['item__company', 'is_active']
    search_fields = ['code', 'sku', 'barcode', 'item__name']
    # raw_id_fields = ['item']
    inlines = [ItemVariantAttributeValueInline]


@admin.register(NumberingSequence)
class NumberingSequenceAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'prefix', 'next_number', 'company', 'branch']
    list_filter = ['company', 'branch', 'document_type', 'yearly_reset']
    search_fields = ['prefix', 'suffix']


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category']
    list_filter = ['category']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['users', 'groups']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['company', 'stock_valuation_method', 'negative_stock_allowed']
    list_filter = ['stock_valuation_method', 'negative_stock_allowed', 'customer_credit_check']


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
# apps/base_data/admin.py
"""
إعدادات لوحة التحكم لوحدة البيانات الأساسية
تسجيل النماذج وتخصيص العرض
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    UnitOfMeasure, ItemCategory, Item,
    Warehouse, Customer, Supplier
)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    """إدارة وحدات القياس"""
    list_display = ['code', 'name', 'name_en', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['code', 'name', 'name_en']

    def save_model(self, request, obj, form, change):
        """إضافة المستخدم والشركة تلقائياً"""
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    """إدارة تصنيفات الأصناف"""
    list_display = ['code', 'name', 'parent', 'level', 'is_active']
    list_filter = ['level', 'is_active', 'company']
    search_fields = ['code', 'name', 'name_en']
    raw_id_fields = ['parent']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """إدارة الأصناف"""
    list_display = ['code', 'name', 'category', 'unit', 'sale_price', 'is_active']
    list_filter = ['category', 'unit', 'is_active', 'company']
    search_fields = ['code', 'name', 'barcode', 'name_en']
    raw_id_fields = ['category']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('code', 'name', 'name_en', 'barcode')
        }),
        (_('التصنيف والوحدة'), {
            'fields': ('category', 'unit', 'manufacturer')
        }),
        (_('الأسعار والضرائب'), {
            'fields': ('purchase_price', 'sale_price', 'tax_rate')
        }),
        (_('حدود المخزون'), {
            'fields': ('minimum_quantity', 'maximum_quantity')
        }),
        (_('معلومات إضافية'), {
            'fields': ('weight', 'image', 'notes', 'is_active')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """إدارة المستودعات"""
    list_display = ['code', 'name', 'branch', 'keeper', 'is_active']
    list_filter = ['branch', 'is_active', 'company']
    search_fields = ['code', 'name', 'location']
    raw_id_fields = ['keeper']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
            if not obj.branch:
                obj.branch = request.user.branch
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """إدارة العملاء"""
    list_display = ['code', 'name', 'account_type', 'phone', 'credit_limit', 'is_active']
    list_filter = ['account_type', 'tax_status', 'is_active', 'company']
    search_fields = ['code', 'name', 'phone', 'mobile', 'email']
    raw_id_fields = ['salesperson']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('code', 'name', 'name_en', 'account_type')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('contact_person', 'phone', 'mobile', 'fax', 'email', 'website')
        }),
        (_('العنوان'), {
            'fields': ('address', 'city', 'region')
        }),
        (_('معلومات ضريبية'), {
            'fields': ('tax_number', 'tax_status', 'commercial_register')
        }),
        (_('حدود الائتمان'), {
            'fields': ('credit_limit', 'credit_period', 'discount_percentage')
        }),
        (_('معلومات إضافية'), {
            'fields': ('salesperson', 'notes', 'is_active')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
            obj.branch = request.user.branch
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """إدارة الموردين"""
    list_display = ['code', 'name', 'account_type', 'phone', 'credit_limit', 'is_active']
    list_filter = ['account_type', 'tax_status', 'is_active', 'company']
    search_fields = ['code', 'name', 'phone', 'mobile', 'email']

    fieldsets = CustomerAdmin.fieldsets[:-1] + (
        (_('معلومات إضافية'), {
            'fields': ('payment_terms', 'notes', 'is_active')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.company = request.user.company
            obj.branch = request.user.branch
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
# apps/assets/admin.py
"""
تسجيل النماذج في لوحة الإدارة Django Admin
"""

from django.contrib import admin
from .models import (
    AssetCategory,
    DepreciationMethod,
    AssetCondition,
    Asset,
    AssetDepreciation,
    AssetAttachment,
    AssetValuation,
    AssetTransaction,
    AssetTransfer,
    MaintenanceType,
    MaintenanceSchedule,
    AssetMaintenance,
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'level', 'company', 'is_active']
    list_filter = ['is_active', 'level', 'company']
    search_fields = ['code', 'name', 'name_en']
    ordering = ['code']


@admin.register(DepreciationMethod)
class DepreciationMethodAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'method_type', 'is_active']
    list_filter = ['is_active', 'method_type']
    search_fields = ['code', 'name', 'name_en']


@admin.register(AssetCondition)
class AssetConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'color_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_en']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_number', 'name', 'category', 'status', 'purchase_date',
                    'original_cost', 'book_value', 'company', 'branch']
    list_filter = ['status', 'category', 'company', 'branch', 'purchase_date']
    search_fields = ['asset_number', 'name', 'serial_number', 'barcode']
    readonly_fields = ['asset_number', 'accumulated_depreciation', 'book_value', 'barcode']
    date_hierarchy = 'purchase_date'
    ordering = ['-purchase_date', '-asset_number']

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('asset_number', 'name', 'name_en', 'category', 'condition', 'status')
        }),
        ('معلومات الشراء', {
            'fields': ('purchase_date', 'purchase_invoice_number', 'supplier')
        }),
        ('المعلومات المالية', {
            'fields': ('original_cost', 'salvage_value', 'accumulated_depreciation', 'book_value')
        }),
        ('معلومات الإهلاك', {
            'fields': ('depreciation_method', 'useful_life_months', 'depreciation_start_date',
                       'total_expected_units', 'units_used', 'unit_name')
        }),
        ('الموقع والمسؤولية', {
            'fields': ('company', 'branch', 'cost_center', 'responsible_employee', 'physical_location')
        }),
        ('معلومات إضافية', {
            'fields': ('serial_number', 'model', 'manufacturer', 'barcode', 'description', 'notes')
        }),
        ('الضمان', {
            'fields': ('warranty_start_date', 'warranty_end_date', 'warranty_provider')
        }),
    )


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'depreciation_date', 'depreciation_amount',
                    'accumulated_depreciation_after', 'book_value_after']
    list_filter = ['depreciation_date', 'fiscal_year']
    search_fields = ['asset__asset_number', 'asset__name']
    date_hierarchy = 'depreciation_date'
    ordering = ['-depreciation_date']


@admin.register(AssetAttachment)
class AssetAttachmentAdmin(admin.ModelAdmin):
    list_display = ['asset', 'title', 'attachment_type', 'uploaded_at', 'expiry_date']
    list_filter = ['attachment_type', 'uploaded_at']
    search_fields = ['asset__asset_number', 'title']
    date_hierarchy = 'uploaded_at'


@admin.register(AssetValuation)
class AssetValuationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'valuation_date', 'old_value', 'new_value',
                    'difference', 'is_approved']
    list_filter = ['is_approved', 'valuation_date']
    search_fields = ['asset__asset_number', 'asset__name']
    date_hierarchy = 'valuation_date'
    readonly_fields = ['difference']


@admin.register(AssetTransaction)
class AssetTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'transaction_date', 'transaction_type',
                    'asset', 'amount', 'status', 'company']
    list_filter = ['transaction_type', 'status', 'transaction_date', 'company']
    search_fields = ['transaction_number', 'asset__asset_number', 'asset__name']
    readonly_fields = ['transaction_number', 'gain_loss']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date']


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number', 'transfer_date', 'asset', 'from_branch',
                    'to_branch', 'status', 'company']
    list_filter = ['status', 'transfer_date', 'from_branch', 'to_branch']
    search_fields = ['transfer_number', 'asset__asset_number', 'asset__name']
    readonly_fields = ['transfer_number']
    date_hierarchy = 'transfer_date'


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'name_en', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'name_en']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['schedule_number', 'asset', 'maintenance_type', 'frequency',
                    'next_maintenance_date', 'is_active']
    list_filter = ['frequency', 'is_active', 'next_maintenance_date']
    search_fields = ['schedule_number', 'asset__asset_number', 'asset__name']
    readonly_fields = ['schedule_number', 'next_maintenance_date']
    date_hierarchy = 'next_maintenance_date'


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['maintenance_number', 'asset', 'maintenance_type', 'scheduled_date',
                    'status', 'total_cost', 'company']
    list_filter = ['status', 'maintenance_category', 'scheduled_date', 'company']
    search_fields = ['maintenance_number', 'asset__asset_number', 'asset__name']
    readonly_fields = ['maintenance_number', 'total_cost']
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date']

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('maintenance_number', 'asset', 'maintenance_type',
                       'maintenance_category', 'maintenance_schedule')
        }),
        ('التواريخ والحالة', {
            'fields': ('scheduled_date', 'start_date', 'completion_date', 'status')
        }),
        ('المسؤولون', {
            'fields': ('performed_by', 'external_vendor', 'vendor_invoice_number')
        }),
        ('التكاليف', {
            'fields': ('labor_cost', 'parts_cost', 'other_cost', 'total_cost',
                       'is_capital_improvement')
        }),
        ('التفاصيل', {
            'fields': ('description', 'issues_found', 'recommendations',
                       'parts_description', 'notes', 'attachment')
        }),
        ('الشركة والفرع', {
            'fields': ('company', 'branch')
        }),
    )
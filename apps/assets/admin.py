from django.contrib import admin
from .models import (
    AssetCategory, DepreciationMethod, AssetCondition,
    Asset, AssetAttachment, AssetDepreciation, AssetValuation,
    AssetTransaction, AssetTransfer,
    MaintenanceType, MaintenanceSchedule, AssetMaintenance,
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine, PhysicalCountAdjustment,
    InsuranceCompany, AssetInsurance, InsuranceClaim,
    AssetLease, LeasePayment,
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest, ApprovalHistory
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['code', 'name']


@admin.register(DepreciationMethod)
class DepreciationMethodAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'method_type', 'rate_percentage', 'is_active']
    list_filter = ['method_type', 'is_active']


@admin.register(AssetCondition)
class AssetConditionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_number', 'name', 'category', 'status', 'book_value', 'branch']
    list_filter = ['status', 'category', 'branch']
    search_fields = ['asset_number', 'name', 'barcode', 'serial_number']
    readonly_fields = ['asset_number', 'book_value', 'accumulated_depreciation']


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'depreciation_date', 'depreciation_amount', 'is_posted']
    list_filter = ['is_posted', 'depreciation_date']
    search_fields = ['asset__asset_number', 'asset__name']


@admin.register(AssetTransaction)
class AssetTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'asset', 'transaction_type', 'transaction_date', 'amount', 'status']
    list_filter = ['transaction_type', 'status', 'transaction_date']
    search_fields = ['transaction_number', 'asset__asset_number']


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['schedule_number', 'asset', 'maintenance_type', 'frequency', 'next_maintenance_date', 'is_active']
    list_filter = ['is_active', 'frequency']
    search_fields = ['schedule_number', 'asset__asset_number']


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['maintenance_number', 'asset', 'maintenance_type', 'scheduled_date', 'status', 'total_cost']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['maintenance_number', 'asset__asset_number']


@admin.register(PhysicalCountCycle)
class PhysicalCountCycleAdmin(admin.ModelAdmin):
    list_display = ['cycle_number', 'name', 'cycle_type', 'start_date', 'status']
    list_filter = ['status', 'cycle_type']


@admin.register(PhysicalCount)
class PhysicalCountAdmin(admin.ModelAdmin):
    list_display = ['count_number', 'cycle', 'count_date', 'branch', 'status', 'total_assets', 'counted_assets']
    list_filter = ['status', 'branch']


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'phone', 'email']
    search_fields = ['code', 'name']


@admin.register(AssetInsurance)
class AssetInsuranceAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'asset', 'insurance_company', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['policy_number', 'asset__asset_number']


@admin.register(AssetLease)
class AssetLeaseAdmin(admin.ModelAdmin):
    list_display = ['lease_number', 'asset', 'lease_type', 'start_date', 'end_date', 'monthly_payment', 'status']
    list_filter = ['status', 'lease_type']
    search_fields = ['lease_number', 'asset__asset_number']


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'document_type', 'is_sequential', 'is_active']
    list_filter = ['is_active', 'document_type']
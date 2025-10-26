# apps/assets/admin.py
"""
Django Admin للأصول الثابتة
تم تفعيل جميع Models مع customization احترافي
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    AssetCategory, DepreciationMethod, AssetCondition,
    Asset, AssetAttachment, AssetDepreciation, AssetValuation,
    AssetTransaction, AssetTransfer,
    MaintenanceType, MaintenanceSchedule, AssetMaintenance,
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine, PhysicalCountAdjustment,
    InsuranceCompany, AssetInsurance, InsuranceClaim,
    AssetLease, LeasePayment,
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest, ApprovalHistory,
    NotificationTemplate, AssetNotification, NotificationSettings,
    AssetAccountingConfiguration,
)


# ==================== Asset Configuration ====================

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'default_depreciation_method', 'created_at']
    list_filter = ['default_depreciation_method', 'created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('code', 'name', 'name_en', 'parent', 'description')
        }),
        ('الإعدادات المحاسبية', {
            'fields': ('default_depreciation_method', 'default_useful_life_months', 'default_salvage_value_rate')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'default_depreciation_method')


@admin.register(DepreciationMethod)
class DepreciationMethodAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'method_type', 'rate_percentage', 'is_active']
    list_filter = ['method_type', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(AssetCondition)
class AssetConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_en']
    ordering = ['name']


# ==================== Assets ====================

class AssetAttachmentInline(admin.TabularInline):
    model = AssetAttachment
    extra = 0
    fields = ['file', 'description', 'uploaded_by', 'uploaded_at']
    readonly_fields = ['uploaded_by', 'uploaded_at']


class AssetDepreciationInline(admin.TabularInline):
    model = AssetDepreciation
    extra = 0
    fields = ['depreciation_date', 'depreciation_amount', 'book_value_after', 'is_posted']
    readonly_fields = ['book_value_after', 'is_posted']
    can_delete = False


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_number', 'name', 'category', 'status_badge',
        'original_cost', 'book_value', 'branch', 'purchase_date'
    ]
    list_filter = ['status', 'category', 'depreciation_status', 'purchase_date']
    search_fields = ['asset_number', 'name', 'barcode', 'serial_number', 'description']
    readonly_fields = [
        'asset_number', 'book_value', 'accumulated_depreciation'
    ]
    ordering = ['-purchase_date']
    list_per_page = 50
    date_hierarchy = 'purchase_date'

    inlines = [AssetAttachmentInline, AssetDepreciationInline]

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (
                'asset_number', 'name', 'name_en', 'category', 'description',
                'barcode', 'serial_number', 'manufacturer', 'model'
            )
        }),
        ('المعلومات المالية', {
            'fields': (
                'original_cost', 'salvage_value', 'book_value',
                'accumulated_depreciation', 'currency',
                'purchase_date', 'supplier', 'purchase_invoice_number'
            )
        }),
        ('الإهلاك', {
            'fields': (
                'depreciation_method', 'useful_life_months',
                'depreciation_status', 'depreciation_start_date'
            )
        }),
        ('الموقع والمسؤول', {
            'fields': (
                'physical_location', 'responsible_employee'
            )
        }),
        ('الحالة والضمان', {
            'fields': (
                'status', 'condition', 'warranty_start_date',
                'warranty_end_date', 'warranty_provider'
            )
        }),
    )

    def status_badge(self, obj):
        colors = {
            'active': 'success',
            'inactive': 'secondary',
            'disposed': 'danger',
            'sold': 'info',
            'under_maintenance': 'warning',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'category', 'depreciation_method', 'condition'
        )


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'depreciation_date', 'depreciation_amount',
        'book_value_after', 'is_posted', 'period'
    ]
    list_filter = ['is_posted', 'depreciation_date', 'fiscal_year']
    search_fields = ['asset__asset_number', 'asset__name']
    readonly_fields = ['book_value_after', 'accumulated_depreciation_after']
    date_hierarchy = 'depreciation_date'
    ordering = ['-depreciation_date']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('asset')


@admin.register(AssetValuation)
class AssetValuationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'valuation_date', 'old_value', 'new_value', 'difference', 'valuator_name']
    list_filter = ['valuation_date', 'is_approved']
    search_fields = ['asset__asset_number', 'asset__name', 'valuator_name']
    readonly_fields = ['difference', 'approved_at', 'created_at']
    date_hierarchy = 'valuation_date'


# ==================== Transactions ====================

@admin.register(AssetTransaction)
class AssetTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'asset', 'transaction_type',
        'transaction_date', 'amount', 'status_badge'
    ]
    list_filter = ['transaction_type', 'status', 'transaction_date']
    search_fields = ['transaction_number', 'asset__asset_number', 'description']
    readonly_fields = ['transaction_number', 'gain_loss', 'approved_at']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date']

    fieldsets = (
        ('معلومات العملية', {
            'fields': (
                'transaction_number', 'asset', 'transaction_type',
                'transaction_date', 'status'
            )
        }),
        ('التفاصيل المالية', {
            'fields': (
                'amount', 'sale_price', 'book_value_at_sale', 'gain_loss',
                'payment_method', 'reference_number'
            )
        }),
        ('الأطراف', {
            'fields': ('business_partner',)
        }),
        ('ملاحظات', {
            'fields': ('description', 'notes')
        }),
        ('الموافقة', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'pending': 'warning',
            'approved': 'success',
            'posted': 'info',
            'cancelled': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = [
        'transfer_number', 'asset', 'from_branch', 'to_branch',
        'transfer_date', 'status'
    ]
    list_filter = ['status', 'transfer_date', 'from_branch', 'to_branch']
    search_fields = ['transfer_number', 'asset__asset_number']
    readonly_fields = ['transfer_number', 'approved_at', 'approved_by']
    date_hierarchy = 'transfer_date'


# ==================== Maintenance ====================

@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'name_en']
    ordering = ['code']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'schedule_number', 'asset', 'maintenance_type',
        'frequency', 'next_maintenance_date', 'is_active'
    ]
    list_filter = ['is_active', 'frequency', 'maintenance_type']
    search_fields = ['schedule_number', 'asset__asset_number']
    readonly_fields = ['schedule_number', 'next_maintenance_date']
    date_hierarchy = 'start_date'


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = [
        'maintenance_number', 'asset', 'maintenance_type',
        'scheduled_date', 'status', 'total_cost'
    ]
    list_filter = ['status', 'maintenance_type', 'scheduled_date']
    search_fields = ['maintenance_number', 'asset__asset_number', 'performed_by']
    readonly_fields = ['maintenance_number', 'total_cost']
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('معلومات الصيانة', {
            'fields': (
                'maintenance_number', 'asset', 'maintenance_type',
                'schedule', 'priority'
            )
        }),
        ('التواريخ', {
            'fields': (
                'scheduled_date', 'actual_start_date', 'actual_end_date'
            )
        }),
        ('التفاصيل', {
            'fields': (
                'description', 'work_performed', 'parts_used',
                'performed_by', 'vendor'
            )
        }),
        ('التكلفة', {
            'fields': (
                'labor_cost', 'parts_cost', 'other_cost', 'total_cost'
            )
        }),
        ('الحالة', {
            'fields': ('status', 'completion_notes')
        }),
    )


# ==================== Physical Count ====================

@admin.register(PhysicalCountCycle)
class PhysicalCountCycleAdmin(admin.ModelAdmin):
    list_display = ['cycle_number', 'name', 'cycle_type', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'cycle_type', 'start_date']
    search_fields = ['cycle_number', 'name']
    readonly_fields = ['cycle_number']
    date_hierarchy = 'start_date'


class PhysicalCountLineInline(admin.TabularInline):
    model = PhysicalCountLine
    extra = 0
    fields = ['line_number', 'asset', 'is_found', 'is_counted', 'actual_location', 'notes']
    readonly_fields = ['line_number']


@admin.register(PhysicalCount)
class PhysicalCountAdmin(admin.ModelAdmin):
    list_display = [
        'count_number', 'cycle', 'count_date', 'branch',
        'total_assets', 'counted_assets', 'status'
    ]
    list_filter = ['status', 'branch', 'count_date']
    search_fields = ['count_number', 'cycle__cycle_number']
    readonly_fields = ['count_number', 'total_assets', 'counted_assets', 'approved_date']
    date_hierarchy = 'count_date'

    inlines = [PhysicalCountLineInline]


@admin.register(PhysicalCountAdjustment)
class PhysicalCountAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'adjustment_number', 'physical_count_line', 'adjustment_type',
        'adjustment_date', 'status'
    ]
    list_filter = ['status', 'adjustment_type', 'adjustment_date']
    search_fields = ['adjustment_number', 'physical_count_line__physical_count__count_number']
    readonly_fields = ['adjustment_number', 'loss_amount', 'approved_date']


# ==================== Insurance ====================

@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'phone', 'email']
    ordering = ['name']


@admin.register(AssetInsurance)
class AssetInsuranceAdmin(admin.ModelAdmin):
    list_display = [
        'policy_number', 'asset', 'insurance_company',
        'start_date', 'end_date', 'status'
    ]
    list_filter = ['status', 'insurance_company', 'start_date']
    search_fields = ['policy_number', 'asset__asset_number']
    readonly_fields = ['policy_number']
    date_hierarchy = 'start_date'

    fieldsets = (
        ('معلومات البوليصة', {
            'fields': ('policy_number', 'asset', 'insurance_company')
        }),
        ('التغطية', {
            'fields': (
                'coverage_type', 'coverage_amount', 'premium_amount',
                'deductible'
            )
        }),
        ('التواريخ', {
            'fields': ('start_date', 'end_date', 'payment_frequency')
        }),
        ('الحالة', {
            'fields': ('status', 'notes')
        }),
    )


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = [
        'claim_number', 'insurance', 'incident_date',
        'claim_amount', 'approved_amount', 'status'
    ]
    list_filter = ['status', 'incident_date', 'claim_type']
    search_fields = ['claim_number', 'insurance__policy_number']
    readonly_fields = ['claim_number', 'approval_date', 'payment_date', 'net_payment']
    date_hierarchy = 'incident_date'


# ==================== Lease ====================

@admin.register(AssetLease)
class AssetLeaseAdmin(admin.ModelAdmin):
    list_display = [
        'lease_number', 'asset', 'lease_type', 'lessor',
        'start_date', 'end_date', 'monthly_payment', 'status'
    ]
    list_filter = ['status', 'lease_type', 'start_date']
    search_fields = ['lease_number', 'asset__asset_number', 'lessor']
    readonly_fields = ['lease_number', 'contract_duration_months', 'total_payments']
    date_hierarchy = 'start_date'


@admin.register(LeasePayment)
class LeasePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'lease', 'payment_number', 'payment_date',
        'amount', 'is_paid', 'paid_date'
    ]
    list_filter = ['is_paid', 'payment_date']
    search_fields = ['lease__lease_number']
    readonly_fields = ['paid_date']
    date_hierarchy = 'payment_date'


# ==================== Workflow & Approvals ====================

class ApprovalLevelInline(admin.TabularInline):
    model = ApprovalLevel
    extra = 1
    fields = ['level', 'name', 'approver', 'is_required']


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'document_type', 'is_active']
    list_filter = ['is_active', 'document_type', 'is_sequential']
    search_fields = ['name', 'code', 'description']

    inlines = [ApprovalLevelInline]


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'workflow', 'requested_by', 'document_type',
        'amount', 'status', 'requested_date'
    ]
    list_filter = ['status', 'document_type', 'requested_date']
    search_fields = ['request_number', 'description', 'requested_by__username']
    readonly_fields = ['request_number', 'current_level', 'requested_date', 'completed_date']
    date_hierarchy = 'requested_date'


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'approval_request', 'level', 'approver', 'action',
        'action_date'
    ]
    list_filter = ['action', 'action_date']
    search_fields = ['approval_request__workflow__name', 'approver__username']
    readonly_fields = ['action_date']
    date_hierarchy = 'action_date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'approval_request', 'level', 'approver'
        )


# ==================== Notifications ====================

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'notification_type', 'notification_channel', 'is_active']
    list_filter = ['is_active', 'notification_type', 'notification_channel']
    search_fields = ['code', 'name', 'subject_template', 'body_template']


@admin.register(AssetNotification)
class AssetNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'notification_type', 'recipient', 'asset',
        'priority', 'is_sent', 'is_read', 'created_at'
    ]
    list_filter = ['is_read', 'is_sent', 'priority', 'notification_type', 'created_at']
    search_fields = ['recipient__username', 'asset__asset_number', 'subject']
    readonly_fields = ['created_at', 'sent_date', 'read_date']
    date_hierarchy = 'created_at'


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'maintenance_enabled', 'insurance_enabled',
        'warranty_enabled', 'lease_enabled'
    ]
    list_filter = [
        'maintenance_enabled', 'insurance_enabled',
        'warranty_enabled', 'lease_enabled'
    ]
    search_fields = ['user__username']


# ==================== Accounting Configuration ====================

@admin.register(AssetAccountingConfiguration)
class AssetAccountingConfigurationAdmin(admin.ModelAdmin):
    list_display = ['id', 'default_maintenance_expense_account', 'default_cash_account']

    fieldsets = (
        ('حسابات الصيانة', {
            'fields': (
                'default_maintenance_expense_account',
                'capital_improvement_account'
            )
        }),
        ('حسابات الإيجار', {
            'fields': (
                'operating_lease_expense_account',
                'finance_lease_liability_account',
                'finance_lease_interest_expense_account'
            )
        }),
        ('حسابات التأمين', {
            'fields': (
                'insurance_expense_account',
                'insurance_deductible_expense_account',
                'insurance_claim_income_account'
            )
        }),
        ('حسابات الدفع', {
            'fields': (
                'default_cash_account',
                'default_bank_account',
                'default_supplier_account'
            )
        }),
    )


# ==================== Admin Site Customization ====================

admin.site.site_header = "نظام إدارة الأصول الثابتة"
admin.site.site_title = "إدارة الأصول"
admin.site.index_title = "لوحة تحكم الأصول الثابتة"

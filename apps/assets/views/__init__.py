# apps/assets/views/__init__.py
"""
Assets Views Package
مركز تجميع جميع الـ Views لنظام الأصول الثابتة
"""

from .dashboard import *
from .asset_views import *
from .depreciation_views import *
from .transaction_views import *
from .maintenance_views import *
from .physical_count_views import *
from .insurance_views import *
from .lease_views import *
from .workflow_views import *
from .notification_views import *
from .report_views import *
from .api_views import *

__all__ = [
    # ==================== Dashboard ====================
    'AssetDashboardView',
    'dashboard_stats_ajax',
    'depreciation_chart_ajax',
    'maintenance_chart_ajax',
    'asset_status_chart_ajax',

    # ==================== Asset Base ====================
    # Asset Categories
    'AssetCategoryListView',
    'AssetCategoryCreateView',
    'AssetCategoryUpdateView',
    'AssetCategoryDeleteView',
    'AssetCategoryDetailView',
    'category_datatable_ajax',
    'category_tree_ajax',

    # Depreciation Methods
    'DepreciationMethodListView',
    'DepreciationMethodCreateView',
    'DepreciationMethodUpdateView',
    'DepreciationMethodDeleteView',

    # Asset Conditions
    'AssetConditionListView',
    'AssetConditionCreateView',
    'AssetConditionUpdateView',
    'AssetConditionDeleteView',

    # Assets
    'AssetListView',
    'AssetCreateView',
    'AssetDetailView',
    'AssetUpdateView',
    'AssetDeleteView',
    'asset_datatable_ajax',
    'asset_search_ajax',
    'generate_asset_number',
    'asset_barcode_pdf',
    'asset_qr_code',

    # Asset Attachments
    'upload_attachment',
    'delete_attachment',

    # Bulk Operations
    'bulk_import_assets',
    'download_import_template',
    'bulk_update_status',
    'bulk_update_location',

    # ==================== Depreciation ====================
    'AssetDepreciationListView',
    'AssetDepreciationDetailView',
    'CalculateDepreciationView',
    'BulkDepreciationCalculationView',
    'depreciation_datatable_ajax',
    'depreciation_schedule_ajax',
    'calculate_single_depreciation_ajax',

    # ==================== Transactions ====================
    # Asset Transactions
    'AssetTransactionListView',
    'AssetTransactionCreateView',
    'AssetTransactionDetailView',
    'AssetTransactionUpdateView',
    'AssetTransactionDeleteView',
    'transaction_datatable_ajax',
    'post_transaction',

    # Specific Transaction Types
    'SellAssetView',
    'DisposeAssetView',
    'RevalueAssetView',

    # Asset Transfers
    'AssetTransferListView',
    'AssetTransferCreateView',
    'AssetTransferDetailView',
    'AssetTransferUpdateView',
    'approve_transfer',
    'complete_transfer',
    'transfer_datatable_ajax',

    # ==================== Maintenance ====================
    # Maintenance Types
    'MaintenanceTypeListView',
    'MaintenanceTypeCreateView',
    'MaintenanceTypeUpdateView',
    'MaintenanceTypeDeleteView',

    # Maintenance Schedules
    'MaintenanceScheduleListView',
    'MaintenanceScheduleCreateView',
    'MaintenanceScheduleDetailView',
    'MaintenanceScheduleUpdateView',
    'MaintenanceScheduleDeleteView',
    'schedule_datatable_ajax',
    'generate_schedule_dates',

    # Asset Maintenance
    'AssetMaintenanceListView',
    'AssetMaintenanceCreateView',
    'AssetMaintenanceDetailView',
    'AssetMaintenanceUpdateView',
    'complete_maintenance',
    'maintenance_datatable_ajax',

    # ==================== Physical Count ====================
    # Physical Count Cycles
    'PhysicalCountCycleListView',
    'PhysicalCountCycleCreateView',
    'PhysicalCountCycleDetailView',
    'PhysicalCountCycleUpdateView',
    'cycle_datatable_ajax',

    # Physical Counts
    'PhysicalCountListView',
    'PhysicalCountCreateView',
    'PhysicalCountDetailView',
    'PhysicalCountUpdateView',
    'approve_physical_count',
    'count_datatable_ajax',

    # Physical Count Lines
    'PhysicalCountLineUpdateView',
    'count_line_ajax',
    'barcode_scan_ajax',
    'upload_count_photo',

    # Physical Count Adjustments
    'PhysicalCountAdjustmentListView',
    'PhysicalCountAdjustmentCreateView',
    'PhysicalCountAdjustmentDetailView',
    'post_adjustment',
    'adjustment_datatable_ajax',

    # ==================== Insurance ====================
    # Insurance Companies
    'InsuranceCompanyListView',
    'InsuranceCompanyCreateView',
    'InsuranceCompanyUpdateView',
    'InsuranceCompanyDeleteView',

    # Asset Insurance
    'AssetInsuranceListView',
    'AssetInsuranceCreateView',
    'AssetInsuranceDetailView',
    'AssetInsuranceUpdateView',
    'insurance_datatable_ajax',
    'insurance_expiring_ajax',

    # Insurance Claims
    'InsuranceClaimListView',
    'InsuranceClaimCreateView',
    'InsuranceClaimDetailView',
    'InsuranceClaimUpdateView',
    'approve_insurance_claim',
    'process_claim_payment',
    'claim_datatable_ajax',

    # ==================== Lease ====================
    'AssetLeaseListView',
    'AssetLeaseCreateView',
    'AssetLeaseDetailView',
    'AssetLeaseUpdateView',
    'lease_datatable_ajax',

    'LeasePaymentListView',
    'LeasePaymentCreateView',
    'process_lease_payment',
    'payment_datatable_ajax',

    # ==================== Workflow ====================
    'ApprovalWorkflowListView',
    'ApprovalWorkflowCreateView',
    'ApprovalWorkflowDetailView',
    'ApprovalWorkflowUpdateView',
    'ApprovalWorkflowDeleteView',

    'ApprovalLevelCreateView',
    'ApprovalLevelUpdateView',
    'ApprovalLevelDeleteView',

    'ApprovalRequestListView',
    'ApprovalRequestDetailView',
    'approve_request',
    'reject_request',
    'request_datatable_ajax',
    'my_pending_approvals_ajax',

    # ==================== Notifications ====================
    'notifications_dashboard',
    'overdue_maintenance_list',
    'upcoming_maintenance_list',
    'expiring_insurance_list',
    'overdue_lease_payments_list',
    'notification_count_ajax',
    'notification_details_ajax',

    # ==================== Reports ====================
    'reports_dashboard',
    'asset_register_report',
    'depreciation_report',
    'maintenance_report',
    'asset_movement_report',
    'valuation_report',
    'physical_count_report',

    # Export Functions
    'export_asset_register_excel',
    'export_depreciation_excel',

    # ==================== API Views ====================
    'asset_search_api',
    'asset_details_api',
    'category_assets_api',
    'asset_stats_api',
    'depreciation_schedule_api',
    'maintenance_alerts_api',
    'insurance_alerts_api',
    'barcode_scan_api',
    'asset_condition_list_api',
    'depreciation_method_list_api',
    'category_list_api',
    'validate_asset_number_api',
    'asset_qr_code_api',
]
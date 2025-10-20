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

__all__ = [
    # ==================== Dashboard ====================
    'AssetDashboardView',
    'dashboard_stats_api',
    'depreciation_alerts_api',
    'maintenance_alerts_api',

    # ==================== Asset Base ====================
    # Asset Categories
    'AssetCategoryListView',
    'AssetCategoryCreateView',
    'AssetCategoryUpdateView',
    'AssetCategoryDeleteView',
    'AssetCategoryDetailView',
    'asset_category_datatable_ajax',
    'asset_category_tree_ajax',

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
    'asset_autocomplete',
    'asset_search_ajax',
    'generate_asset_qr_code',
    'asset_timeline_ajax',

    # Asset Attachments
    'AssetAttachmentCreateView',
    'AssetAttachmentDeleteView',

    # Asset Valuations
    'AssetValuationListView',
    'AssetValuationCreateView',
    'AssetValuationDetailView',
    'AssetValuationApproveView',

    # Bulk Operations
    'asset_bulk_import',
    'asset_bulk_export',

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

    # Specific Transaction Types
    'SellAssetView',
    'DisposeAssetView',
    'RevalueAssetView',
    'post_transaction',

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

    'ApprovalRequestListView',
    'ApprovalRequestDetailView',
    'approve_request',
    'reject_request',
    'workflow_datatable_ajax',

    # ==================== Notifications ====================
    'NotificationTemplateListView',
    'NotificationTemplateCreateView',
    'NotificationTemplateUpdateView',
    'NotificationTemplateDeleteView',

    'AssetNotificationListView',
    'mark_notification_read',
    'mark_all_read',
    'notification_ajax',

    'NotificationSettingsView',
    'update_notification_settings',

    # ==================== Reports ====================
    # Asset Reports
    'AssetReportView',
    'AssetByCategoryReportView',
    'AssetByBranchReportView',
    'AssetByCostCenterReportView',
    'BookValueSummaryReportView',

    # Depreciation Reports
    'DepreciationReportView',
    'DepreciationScheduleReportView',
    'FullyDepreciatedAssetsReportView',

    # Maintenance Reports
    'MaintenanceDueReportView',
    'MaintenanceCostAnalysisReportView',

    # Physical Count Reports
    'PhysicalCountVarianceReportView',
    'MissingAssetsReportView',

    # Other Reports
    'WarrantyExpiryReportView',
    'InsuranceExpiryReportView',
    'DisposedAssetsReportView',
    'AssetMovementReportView',

    # Export Functions
    'export_assets',
    'export_asset_categories',
    'export_depreciation_schedule',
    'export_maintenance_analysis',
    'export_physical_count_variance',
    'export_insurance_report',
    'export_lease_schedule',
]
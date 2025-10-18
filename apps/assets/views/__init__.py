# apps/assets/views/__init__.py
"""
Assets Views Package
تصدير جميع views تطبيق إدارة الأصول
"""

# ==================== Dashboard ====================
from .dashboard_views import (
    AssetDashboardView,
    dashboard_stats_api,
    assets_by_category_chart_api,
    depreciation_trend_chart_api,
    maintenance_cost_chart_api,
    asset_age_distribution_api,
    alerts_summary_api,
    recent_activities_api,
    top_assets_by_value_api,
)

# ==================== Asset Views ====================
from .asset_views import (
    AssetListView,
    AssetCreateView,
    AssetUpdateView,
    AssetDetailView,
    AssetDeleteView,
    asset_datatable_ajax,
    asset_stats_ajax,
    asset_search_ajax,
    asset_quick_info_ajax,
)

# ==================== Transaction Views ====================
from .transaction_views import (
    AssetTransactionListView,
    AssetTransactionCreateView,
    AssetTransactionDetailView,
    AssetTransactionDeleteView,
    AssetTransferListView,
    AssetTransferCreateView,
    AssetTransferDetailView,
    AssetTransferDeleteView,
    transaction_datatable_ajax,
    transfer_datatable_ajax,
    approve_transfer_ajax,
    sell_asset_ajax,
    dispose_asset_ajax,
)

# ==================== Depreciation Views ====================
from .depreciation_views import (
    AssetDepreciationListView,
    AssetDepreciationDetailView,
    CalculateMonthlyDepreciationView,
    CalculateBatchDepreciationView,
    asset_depreciation_datatable_ajax,
    depreciation_stats_ajax,
    calculate_depreciation_ajax,
    calculate_batch_depreciation_ajax,
)

# ==================== Maintenance Views ====================
from .maintenance_views import (
    MaintenanceScheduleListView,
    MaintenanceScheduleCreateView,
    MaintenanceScheduleUpdateView,
    MaintenanceScheduleDetailView,
    MaintenanceScheduleDeleteView,
    AssetMaintenanceListView,
    AssetMaintenanceCreateView,
    AssetMaintenanceUpdateView,
    AssetMaintenanceDetailView,
    AssetMaintenanceDeleteView,
    maintenance_schedule_datatable_ajax,
    asset_maintenance_datatable_ajax,
    mark_maintenance_completed_ajax,
)

# ==================== Valuation Views ====================
from .valuation_views import (
    AssetValuationListView,
    AssetValuationCreateView,
    AssetValuationDetailView,
    AssetValuationDeleteView,
    asset_valuation_datatable_ajax,
    approve_valuation_ajax,
    valuation_stats_ajax,
    get_asset_current_value_ajax,
)

# ==================== Attachment Views ====================
from .attachment_views import (
    AssetAttachmentListView,
    AssetAttachmentCreateView,
    AssetAttachmentDetailView,
    AssetAttachmentDeleteView,
    download_attachment,
    view_attachment,
    asset_attachments_ajax,
    upload_attachment_ajax,
    delete_attachment_ajax,
    expired_attachments_ajax,
    expiring_soon_attachments_ajax,
)

# ==================== Settings Views ====================
from .settings_views import (
    # Asset Category
    AssetCategoryListView,
    AssetCategoryCreateView,
    AssetCategoryUpdateView,
    AssetCategoryDeleteView,
    asset_category_datatable_ajax,

    # Depreciation Method
    DepreciationMethodListView,
    DepreciationMethodCreateView,
    DepreciationMethodUpdateView,
    DepreciationMethodDeleteView,
    depreciation_method_datatable_ajax,

    # Asset Condition
    AssetConditionListView,
    AssetConditionCreateView,
    AssetConditionUpdateView,
    AssetConditionDeleteView,
    asset_condition_datatable_ajax,

    # Maintenance Type
    MaintenanceTypeListView,
    MaintenanceTypeCreateView,
    MaintenanceTypeUpdateView,
    MaintenanceTypeDeleteView,
    maintenance_type_datatable_ajax,
)

# ==================== Report Views ====================
from .report_views import (
    AssetRegisterReportView,
    export_asset_register,
    DepreciationReportView,
    export_depreciation_report,
    AssetMovementReportView,
    export_asset_movement_report,
    MaintenanceReportView,
    export_maintenance_report,
)

# ==================== Base Report Views ====================
from .base_report_views import (
    BaseAssetReportView,
    BaseAssetExportView,
    BaseAssetReportExportView,
)

# ==================== __all__ للتصدير ====================
__all__ = [
    # Dashboard
    'AssetDashboardView',
    'dashboard_stats_api',
    'assets_by_category_chart_api',
    'depreciation_trend_chart_api',
    'maintenance_cost_chart_api',
    'asset_age_distribution_api',
    'alerts_summary_api',
    'recent_activities_api',
    'top_assets_by_value_api',

    # Assets
    'AssetListView',
    'AssetCreateView',
    'AssetUpdateView',
    'AssetDetailView',
    'AssetDeleteView',
    'asset_datatable_ajax',
    'asset_stats_ajax',
    'asset_search_ajax',
    'asset_quick_info_ajax',

    # Transactions
    'AssetTransactionListView',
    'AssetTransactionCreateView',
    'AssetTransactionDetailView',
    'AssetTransactionDeleteView',
    'AssetTransferListView',
    'AssetTransferCreateView',
    'AssetTransferDetailView',
    'AssetTransferDeleteView',
    'transaction_datatable_ajax',
    'transfer_datatable_ajax',
    'approve_transfer_ajax',
    'sell_asset_ajax',
    'dispose_asset_ajax',

    # Depreciation
    'AssetDepreciationListView',
    'AssetDepreciationDetailView',
    'CalculateMonthlyDepreciationView',
    'CalculateBatchDepreciationView',
    'asset_depreciation_datatable_ajax',
    'depreciation_stats_ajax',
    'calculate_depreciation_ajax',
    'calculate_batch_depreciation_ajax',

    # Maintenance
    'MaintenanceScheduleListView',
    'MaintenanceScheduleCreateView',
    'MaintenanceScheduleUpdateView',
    'MaintenanceScheduleDetailView',
    'MaintenanceScheduleDeleteView',
    'AssetMaintenanceListView',
    'AssetMaintenanceCreateView',
    'AssetMaintenanceUpdateView',
    'AssetMaintenanceDetailView',
    'AssetMaintenanceDeleteView',
    'maintenance_schedule_datatable_ajax',
    'asset_maintenance_datatable_ajax',
    'mark_maintenance_completed_ajax',

    # Valuation
    'AssetValuationListView',
    'AssetValuationCreateView',
    'AssetValuationDetailView',
    'AssetValuationDeleteView',
    'asset_valuation_datatable_ajax',
    'approve_valuation_ajax',
    'valuation_stats_ajax',
    'get_asset_current_value_ajax',

    # Attachments
    'AssetAttachmentListView',
    'AssetAttachmentCreateView',
    'AssetAttachmentDetailView',
    'AssetAttachmentDeleteView',
    'download_attachment',
    'view_attachment',
    'asset_attachments_ajax',
    'upload_attachment_ajax',
    'delete_attachment_ajax',
    'expired_attachments_ajax',
    'expiring_soon_attachments_ajax',

    # Settings - Asset Category
    'AssetCategoryListView',
    'AssetCategoryCreateView',
    'AssetCategoryUpdateView',
    'AssetCategoryDeleteView',
    'asset_category_datatable_ajax',

    # Settings - Depreciation Method
    'DepreciationMethodListView',
    'DepreciationMethodCreateView',
    'DepreciationMethodUpdateView',
    'DepreciationMethodDeleteView',
    'depreciation_method_datatable_ajax',

    # Settings - Asset Condition
    'AssetConditionListView',
    'AssetConditionCreateView',
    'AssetConditionUpdateView',
    'AssetConditionDeleteView',
    'asset_condition_datatable_ajax',

    # Settings - Maintenance Type
    'MaintenanceTypeListView',
    'MaintenanceTypeCreateView',
    'MaintenanceTypeUpdateView',
    'MaintenanceTypeDeleteView',
    'maintenance_type_datatable_ajax',

    # Reports
    'AssetRegisterReportView',
    'export_asset_register',
    'DepreciationReportView',
    'export_depreciation_report',
    'AssetMovementReportView',
    'export_asset_movement_report',
    'MaintenanceReportView',
    'export_maintenance_report',

    # Base Report Classes
    'BaseAssetReportView',
    'BaseAssetExportView',
    'BaseAssetReportExportView',
]
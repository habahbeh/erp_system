# apps/assets/views/__init__.py
"""
Views تطبيق إدارة الأصول الثابتة
"""

from .dashboard_views import AssetsDashboardView
from .asset_views import (
    AssetListView,
    AssetCreateView,
    AssetUpdateView,
    AssetDetailView,
    AssetDeleteView,
    asset_datatable_ajax,
    AssetCategoryListView,
    AssetCategoryCreateView,
    AssetCategoryUpdateView,
    asset_category_datatable_ajax,
)
from .transaction_views import (
    AssetTransactionListView,
    AssetPurchaseView,
    AssetSaleView,
    AssetDisposalView,
    AssetTransferListView,
    AssetTransferCreateView,
    asset_transaction_datatable_ajax,
)
from .maintenance_views import (
    MaintenanceScheduleListView,
    MaintenanceScheduleCreateView,
    MaintenanceScheduleUpdateView,
    AssetMaintenanceListView,
    AssetMaintenanceCreateView,
    AssetMaintenanceUpdateView,
    AssetMaintenanceDetailView,
    maintenance_datatable_ajax,
)
from .depreciation_views import (
    DepreciationCalculationView,
    DepreciationHistoryView,
    depreciation_history_ajax,
)
from .report_views import (
    AssetRegisterReportView,
    DepreciationReportView,
    MaintenanceReportView,
    AssetMovementReportView,
)

__all__ = [
    # Dashboard
    'AssetsDashboardView',

    # Assets
    'AssetListView',
    'AssetCreateView',
    'AssetUpdateView',
    'AssetDetailView',
    'AssetDeleteView',
    'asset_datatable_ajax',
    'AssetCategoryListView',
    'AssetCategoryCreateView',
    'AssetCategoryUpdateView',
    'asset_category_datatable_ajax',

    # Transactions
    'AssetTransactionListView',
    'AssetPurchaseView',
    'AssetSaleView',
    'AssetDisposalView',
    'AssetTransferListView',
    'AssetTransferCreateView',
    'asset_transaction_datatable_ajax',

    # Maintenance
    'MaintenanceScheduleListView',
    'MaintenanceScheduleCreateView',
    'MaintenanceScheduleUpdateView',
    'AssetMaintenanceListView',
    'AssetMaintenanceCreateView',
    'AssetMaintenanceUpdateView',
    'AssetMaintenanceDetailView',
    'maintenance_datatable_ajax',

    # Depreciation
    'DepreciationCalculationView',
    'DepreciationHistoryView',
    'depreciation_history_ajax',

    # Reports
    'AssetRegisterReportView',
    'DepreciationReportView',
    'MaintenanceReportView',
    'AssetMovementReportView',
]
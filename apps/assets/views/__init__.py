# apps/assets/views/__init__.py
"""
Views تطبيق إدارة الأصول الثابتة
"""

# Base Report Views
from .base_report_views import BaseReportView, ExportMixin

# Dashboard
from .dashboard_views import AssetsDashboardView

# Assets
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

# Transactions
from .transaction_views import (
    AssetTransactionListView,
    AssetPurchaseView,
    AssetSaleView,
    AssetDisposalView,
    AssetTransferListView,
    AssetTransferCreateView,
    asset_transaction_datatable_ajax,
)

# Maintenance
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

# Depreciation
from .depreciation_views import (
    DepreciationCalculationView,
    DepreciationHistoryView,
    depreciation_history_ajax,
)

# Reports
from .report_views import (
    ReportsListView,
    AssetRegisterReportView,
    DepreciationReportView,
    MaintenanceReportView,
    AssetMovementReportView,
    AssetByCostCenterReportView,
    AssetNearEndOfLifeReportView,
    FairValueReportView,
)

__all__ = [
    # Base Classes
    'BaseReportView',
    'ExportMixin',

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
    'ReportsListView',
    'AssetRegisterReportView',
    'DepreciationReportView',
    'MaintenanceReportView',
    'AssetMovementReportView',
    'AssetByCostCenterReportView',
    'AssetNearEndOfLifeReportView',
    'FairValueReportView',
]
# apps/base_data/views/__init__.py
"""
استيراد جميع Views لسهولة الوصول - محدث 100%
جميع Views محدثة حسب models.py + Bootstrap 5 + RTL
"""

# Items Views
from .item_views import (
    ItemListView,
    ItemCreateView,
    ItemUpdateView,
    ItemDetailView,
    ItemDeleteView,
    ItemQuickAddView,
    ItemDuplicateView,
    ItemToggleActiveView,
    ItemDataTableView,
    ItemSelectView,
    ItemStockView,
)

# Partners Views
from .partner_views import (
    BusinessPartnerListView,
    CustomerListView,
    SupplierListView,
    BusinessPartnerCreateView,
    CustomerCreateView,
    SupplierCreateView,
    BusinessPartnerUpdateView,
    BusinessPartnerDetailView,
    BusinessPartnerDeleteView,
    PartnerQuickAddView,
    ContactInfoUpdateView,
    PartnerToggleActiveView,
    PartnerDataTableView,
    PartnerSelectView,
    CustomerSelectView,
    SupplierSelectView,
    PartnerStatementView,
    PartnerConvertTypeView,
)

# Warehouse Views
from .warehouse_views import (
    WarehouseListView,
    WarehouseCreateView,
    WarehouseUpdateView,
    WarehouseDetailView,
    WarehouseInventoryView,
    WarehouseTransferView,
    UnitOfMeasureListView,
    UnitOfMeasureCreateView,
    UnitOfMeasureUpdateView,
    WarehouseSelectView,
    UnitSelectView,
)

# Category Views
from .category_views import (
    ItemCategoryListView,
    ItemCategoryCreateView,
    ItemCategoryUpdateView,
    ItemCategoryDetailView,
    ItemCategoryDeleteView,
    CategoryQuickAddView,
    CategorySelectView,
    CategoryMoveView,
)

# AJAX Views
from .ajax_views import (
    BaseDataTableView,
    DashboardStatsView,
    QuickSearchView,
    BulkActionView,
    ItemBulkActionView,
    PartnerBulkActionView,
    WarehouseBulkActionView,
    ValidationView,
    ItemStockCheckView,
    PartnerBalanceView,
    NotificationsView,
)

# Export Views
from .export_views import (
    BaseExportView,
    ItemExportView,
    PartnerExportView,
    WarehouseExportView,
    StockReportExportView,
    CustomExportView,
)

# Import Views
from .import_views import (
    BaseImportView,
    ItemImportView,
    PartnerImportView,
    ImportErrorsView,
    DownloadSampleView,
)

# Report Views
from .report_views import (
    ReportsIndexView,
    ItemsReportView,
    StockReportView,
    PartnersReportView,
    CategoriesReportView,
    LowStockReportView,
    ReportChartsView,
)

__all__ = [
    # Items
    'ItemListView',
    'ItemCreateView',
    'ItemUpdateView',
    'ItemDetailView',
    'ItemDeleteView',
    'ItemQuickAddView',
    'ItemDuplicateView',
    'ItemToggleActiveView',
    'ItemDataTableView',
    'ItemSelectView',
    'ItemStockView',

    # Partners
    'BusinessPartnerListView',
    'CustomerListView',
    'SupplierListView',
    'BusinessPartnerCreateView',
    'CustomerCreateView',
    'SupplierCreateView',
    'BusinessPartnerUpdateView',
    'BusinessPartnerDetailView',
    'BusinessPartnerDeleteView',
    'PartnerQuickAddView',
    'ContactInfoUpdateView',
    'PartnerToggleActiveView',
    'PartnerDataTableView',
    'PartnerSelectView',
    'CustomerSelectView',
    'SupplierSelectView',
    'PartnerStatementView',
    'PartnerConvertTypeView',

    # Warehouses
    'WarehouseListView',
    'WarehouseCreateView',
    'WarehouseUpdateView',
    'WarehouseDetailView',
    'WarehouseInventoryView',
    'WarehouseTransferView',
    'UnitOfMeasureListView',
    'UnitOfMeasureCreateView',
    'UnitOfMeasureUpdateView',
    'WarehouseSelectView',
    'UnitSelectView',

    # Categories
    'ItemCategoryListView',
    'ItemCategoryCreateView',
    'ItemCategoryUpdateView',
    'ItemCategoryDetailView',
    'ItemCategoryDeleteView',
    'CategoryQuickAddView',
    'CategorySelectView',
    'CategoryMoveView',

    # AJAX
    'BaseDataTableView',
    'DashboardStatsView',
    'QuickSearchView',
    'BulkActionView',
    'ItemBulkActionView',
    'PartnerBulkActionView',
    'WarehouseBulkActionView',
    'ValidationView',
    'ItemStockCheckView',
    'PartnerBalanceView',
    'NotificationsView',

    # Export
    'BaseExportView',
    'ItemExportView',
    'PartnerExportView',
    'WarehouseExportView',
    'StockReportExportView',
    'CustomExportView',

    # Import
    'BaseImportView',
    'ItemImportView',
    'PartnerImportView',
    'ImportErrorsView',
    'DownloadSampleView',

    # Reports
    'ReportsIndexView',
    'ItemsReportView',
    'StockReportView',
    'PartnersReportView',
    'CategoriesReportView',
    'LowStockReportView',
    'ReportChartsView',
]
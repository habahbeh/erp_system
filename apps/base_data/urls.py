# apps/base_data/urls.py
"""
URLs البيانات الأساسية - محدث 100%
متطابق مع جميع Views + Bootstrap 5 + RTL + DataTables
"""

from django.urls import path, include
from . import views

app_name = 'base_data'

urlpatterns = [
    # === ITEMS URLs === #
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('items/<int:pk>/duplicate/', views.ItemDuplicateView.as_view(), name='item_duplicate'),
    path('items/<int:pk>/stock/', views.ItemStockView.as_view(), name='item_stock'),
    path('items/quick-add/', views.ItemQuickAddView.as_view(), name='item_quick_add'),

    # Items AJAX URLs
    path('ajax/items/datatable/', views.ItemDataTableView.as_view(), name='item_datatable'),
    path('ajax/items/select/', views.ItemSelectView.as_view(), name='item_select'),
    path('ajax/items/<int:pk>/toggle-active/', views.ItemToggleActiveView.as_view(), name='item_toggle_active'),
    path('ajax/items/<int:item_id>/stock-check/', views.ItemStockCheckView.as_view(), name='item_stock_check'),
    path('ajax/items/bulk-action/', views.ItemBulkActionView.as_view(), name='item_bulk_action'),

    # === PARTNERS URLs === #
    # General Partners
    path('partners/', views.BusinessPartnerListView.as_view(), name='partner_list'),
    path('partners/create/', views.BusinessPartnerCreateView.as_view(), name='partner_create'),
    path('partners/<int:pk>/', views.BusinessPartnerDetailView.as_view(), name='partner_detail'),
    path('partners/<int:pk>/edit/', views.BusinessPartnerUpdateView.as_view(), name='partner_update'),
    path('partners/<int:pk>/delete/', views.BusinessPartnerDeleteView.as_view(), name='partner_delete'),
    path('partners/<int:pk>/contact/', views.ContactInfoUpdateView.as_view(), name='partner_contact_update'),
    path('partners/<int:pk>/statement/', views.PartnerStatementView.as_view(), name='partner_statement'),
    path('partners/quick-add/', views.PartnerQuickAddView.as_view(), name='partner_quick_add'),

    # Customers
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),

    # Partners AJAX URLs
    path('ajax/partners/datatable/', views.PartnerDataTableView.as_view(), name='partner_datatable'),
    path('ajax/partners/select/', views.PartnerSelectView.as_view(), name='partner_select'),
    path('ajax/customers/select/', views.CustomerSelectView.as_view(), name='customer_select'),
    path('ajax/suppliers/select/', views.SupplierSelectView.as_view(), name='supplier_select'),
    path('ajax/partners/<int:pk>/toggle-active/', views.PartnerToggleActiveView.as_view(),
         name='partner_toggle_active'),
    path('ajax/partners/<int:pk>/convert-type/', views.PartnerConvertTypeView.as_view(), name='partner_convert_type'),
    path('ajax/partners/<int:partner_id>/balance/', views.PartnerBalanceView.as_view(), name='partner_balance'),
    path('ajax/partners/bulk-action/', views.PartnerBulkActionView.as_view(), name='partner_bulk_action'),

    # === WAREHOUSES URLs === #
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/inventory/', views.WarehouseInventoryView.as_view(), name='warehouse_inventory'),
    path('warehouses/transfer/', views.WarehouseTransferView.as_view(), name='warehouse_transfer'),

    # Warehouses AJAX URLs
    path('ajax/warehouses/select/', views.WarehouseSelectView.as_view(), name='warehouse_select'),
    path('ajax/warehouses/bulk-action/', views.WarehouseBulkActionView.as_view(), name='warehouse_bulk_action'),

    # === UNITS URLs === #
    path('units/', views.UnitOfMeasureListView.as_view(), name='unit_list'),
    path('units/create/', views.UnitOfMeasureCreateView.as_view(), name='unit_create'),
    path('units/<int:pk>/edit/', views.UnitOfMeasureUpdateView.as_view(), name='unit_update'),

    # Units AJAX URLs
    path('ajax/units/select/', views.UnitSelectView.as_view(), name='unit_select'),

    # === CATEGORIES URLs === #
    path('categories/', views.ItemCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ItemCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.ItemCategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/edit/', views.ItemCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ItemCategoryDeleteView.as_view(), name='category_delete'),
    path('categories/quick-add/', views.CategoryQuickAddView.as_view(), name='category_quick_add'),

    # Categories AJAX URLs
    path('ajax/categories/select/', views.CategorySelectView.as_view(), name='category_select'),
    path('ajax/categories/<int:pk>/move/', views.CategoryMoveView.as_view(), name='category_move'),

    # === EXPORT URLs === #
    path('export/items/', views.ItemExportView.as_view(), name='item_export'),
    path('export/partners/', views.PartnerExportView.as_view(), name='partner_export'),
    path('export/warehouses/', views.WarehouseExportView.as_view(), name='warehouse_export'),
    path('export/stock-report/', views.StockReportExportView.as_view(), name='stock_report_export'),
    path('export/custom/', views.CustomExportView.as_view(), name='custom_export'),

    # === IMPORT URLs === #
    path('import/items/', views.ItemImportView.as_view(), name='item_import'),
    path('import/partners/', views.PartnerImportView.as_view(), name='partner_import'),
    path('import/errors/', views.ImportErrorsView.as_view(), name='import_errors'),
    path('import/sample/<str:model_type>/', views.DownloadSampleView.as_view(), name='download_sample'),

    # === REPORTS URLs === #
    path('reports/', views.ReportsIndexView.as_view(), name='reports_index'),
    path('reports/items/', views.ItemsReportView.as_view(), name='items_report'),
    path('reports/stock/', views.StockReportView.as_view(), name='stock_report'),
    path('reports/partners/', views.PartnersReportView.as_view(), name='partners_report'),
    path('reports/categories/', views.CategoriesReportView.as_view(), name='categories_report'),
    path('reports/low-stock/', views.LowStockReportView.as_view(), name='low_stock_report'),

    # Reports Charts AJAX
    path('ajax/reports/charts/<str:chart_type>/', views.ReportChartsView.as_view(), name='report_charts'),

    # === GENERAL AJAX URLs === #
    path('ajax/dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('ajax/quick-search/', views.QuickSearchView.as_view(), name='quick_search'),
    path('ajax/validation/', views.ValidationView.as_view(), name='validation'),
    path('ajax/notifications/', views.NotificationsView.as_view(), name='notifications'),
]

# === API-style URLs (اختيارية للمستقبل) === #
api_patterns = [
    # RESTful API endpoints (للاستخدام مع JavaScript frameworks)
    path('api/items/', views.ItemDataTableView.as_view(), name='api_items'),
    path('api/partners/', views.PartnerDataTableView.as_view(), name='api_partners'),
    path('api/warehouses/', views.WarehouseSelectView.as_view(), name='api_warehouses'),
    path('api/categories/', views.CategorySelectView.as_view(), name='api_categories'),
    path('api/units/', views.UnitSelectView.as_view(), name='api_units'),
]

# إضافة API patterns إلى URL الرئيسية (اختياري)
# urlpatterns += api_patterns
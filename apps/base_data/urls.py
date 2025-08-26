# apps/base_data/urls.py
"""
URL patterns لتطبيق البيانات الأساسية - كامل ومتكامل
يشمل: الأصناف، الشركاء التجاريين، المستودعات، وحدات القياس، API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # ============== من item_views.py ==============
    # الأصناف
    ItemListView, ItemDetailView, ItemCreateView, ItemUpdateView, ItemDeleteView,
    ItemDataTableView, ItemQuickAddView, ItemSearchAjaxView, ItemInfoAjaxView,
    ItemReportView, ItemExportView,

    # التصنيفات
    CategoryListView, CategoryCreateView, CategoryUpdateView,

    # إدارة البيانات المرتبطة
    ItemComponentsManageView, ItemConversionsManageView, ItemSubstitutesManageView,

    # ============== من partner_views.py ==============
    # الشركاء التجاريين
    BusinessPartnerListView, BusinessPartnerDetailView, BusinessPartnerCreateView,
    BusinessPartnerUpdateView, BusinessPartnerDeleteView, BusinessPartnerDataTableView,
    PartnerQuickAddView, PartnerSearchAjaxView, PartnerInfoAjaxView,
    PartnerReportView, PartnerExportView,

    # العملاء
    CustomerListView, CustomerDetailView, CustomerCreateView, CustomerUpdateView,
    CustomerDataTableView,

    # الموردين
    SupplierListView, SupplierDetailView, SupplierCreateView, SupplierUpdateView,
    SupplierDataTableView,

    # معلومات الاتصال
    ContactInfoManageView,

    # ============== من warehouse_views.py ==============
    # المستودعات
    WarehouseListView, WarehouseDetailView, WarehouseCreateView,
    WarehouseUpdateView, WarehouseDeleteView, WarehouseDataTableView,
    WarehouseSearchAjaxView, WarehouseInfoAjaxView,

    # أرصدة المستودعات
    WarehouseInventoryView, WarehouseItemUpdateView,

    # التحويلات بين المستودعات
    WarehouseTransferListView, WarehouseTransferCreateView,

    # وحدات القياس
    UnitOfMeasureListView, UnitOfMeasureCreateView, UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView, UnitDataTableView, UnitSearchAjaxView,

    # التقارير والتصدير
    WarehouseReportView, InventoryReportView, WarehouseExportView,

    # Views مساعدة
    get_warehouses_by_branch_ajax, get_warehouse_items_ajax,

    # ============== من api_views.py ==============
    # ViewSets
    ItemCategoryViewSet, ItemViewSet, BusinessPartnerViewSet,
    CustomerViewSet, SupplierViewSet, WarehouseViewSet, UnitOfMeasureViewSet,

    # API Views البحث
    ItemSearchAPIView, PartnerSearchAPIView, WarehouseSearchAPIView,

    # API Views التحقق
    CheckBarcodeAPIView, CheckCodeAPIView,

    # API Views الإحصائيات
    StatsAPIView,

    # Function-based API Views
    get_item_by_barcode, get_warehouses_by_branch, get_item_stock_by_warehouse,
)

app_name = 'base_data'

# ============== إعداد REST API Router ==============
router = DefaultRouter()
router.register(r'categories', ItemCategoryViewSet, basename='api-category')
router.register(r'items', ItemViewSet, basename='api-item')
router.register(r'partners', BusinessPartnerViewSet, basename='api-partner')
router.register(r'customers', CustomerViewSet, basename='api-customer')
router.register(r'suppliers', SupplierViewSet, basename='api-supplier')
router.register(r'warehouses', WarehouseViewSet, basename='api-warehouse')
router.register(r'units', UnitOfMeasureViewSet, basename='api-unit')

urlpatterns = [
    # ============== الأصناف ==============
    path('items/', ItemListView.as_view(), name='item_list'),
    path('items/add/', ItemCreateView.as_view(), name='item_add'),
    path('items/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', ItemUpdateView.as_view(), name='item_edit'),
    path('items/<int:pk>/delete/', ItemDeleteView.as_view(), name='item_delete'),

    # إدارة البيانات المرتبطة بالأصناف
    path('items/<int:pk>/components/', ItemComponentsManageView.as_view(), name='item_components'),
    path('items/<int:pk>/conversions/', ItemConversionsManageView.as_view(), name='item_conversions'),
    path('items/<int:pk>/substitutes/', ItemSubstitutesManageView.as_view(), name='item_substitutes'),

    # تقارير وتصدير الأصناف
    path('items/report/', ItemReportView.as_view(), name='item_report'),
    path('items/export/', ItemExportView.as_view(), name='item_export'),

    # DataTables و AJAX للأصناف
    path('items/datatable/', ItemDataTableView.as_view(), name='item_datatable'),
    path('items/quick-add/', ItemQuickAddView.as_view(), name='item_quick_add'),
    path('items/ajax/search/', ItemSearchAjaxView.as_view(), name='item_search_ajax'),
    path('items/ajax/<int:pk>/info/', ItemInfoAjaxView.as_view(), name='item_info_ajax'),

    # ============== التصنيفات (4 مستويات) ==============
    # path('categories/', views.CategoryListView.as_view(), name='category_list'),
    # path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    # path('categories/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_detail'),
    # path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    # path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # التصنيفات - شجرة التصنيفات
    # path('categories/tree/', views.CategoryTreeView.as_view(), name='category_tree'),

    # التصنيفات - AJAX Views
    # path('categories/datatable/', views.CategoryDataTableView.as_view(), name='category_datatable'),
    # path('categories/quick-add/', views.CategoryQuickAddView.as_view(), name='category_quick_add'),
    # path('categories/check-code/', views.CategoryCheckCodeView.as_view(), name='category_check_code'),
    # path('categories/search/', views.CategorySearchAjaxView.as_view(), name='category_search_ajax'),
    # path('categories/<int:pk>/info/', views.CategoryInfoAjaxView.as_view(), name='category_info_ajax'),
    # path('categories/tree-ajax/', views.CategoryTreeAjaxView.as_view(), name='category_tree_ajax'),

    # التصنيفات - التصدير
    # path('categories/export/', views.CategoryExportView.as_view(), name='category_export'),

    # ============== الشركاء التجاريين ==============
    path('partners/', BusinessPartnerListView.as_view(), name='partner_list'),
    path('partners/add/', BusinessPartnerCreateView.as_view(), name='partner_add'),
    path('partners/<int:pk>/', BusinessPartnerDetailView.as_view(), name='partner_detail'),
    path('partners/<int:pk>/edit/', BusinessPartnerUpdateView.as_view(), name='partner_edit'),
    path('partners/<int:pk>/delete/', BusinessPartnerDeleteView.as_view(), name='partner_delete'),

    # معلومات الاتصال
    path('partners/<int:pk>/contacts/', ContactInfoManageView.as_view(), name='partner_contact_info'),

    # تقارير وتصدير الشركاء
    path('partners/report/', PartnerReportView.as_view(), name='partner_report'),
    path('partners/export/', PartnerExportView.as_view(), name='partner_export'),

    # DataTables و AJAX للشركاء
    path('partners/datatable/', BusinessPartnerDataTableView.as_view(), name='partner_datatable'),
    path('partners/quick-add/', PartnerQuickAddView.as_view(), name='partner_quick_add'),
    path('partners/ajax/search/', PartnerSearchAjaxView.as_view(), name='partner_search_ajax'),
    path('partners/ajax/<int:pk>/info/', PartnerInfoAjaxView.as_view(), name='partner_info_ajax'),

    # ============== العملاء ==============
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/datatable/', CustomerDataTableView.as_view(), name='customer_datatable'),

    # ============== الموردين ==============
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/add/', SupplierCreateView.as_view(), name='supplier_add'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/datatable/', SupplierDataTableView.as_view(), name='supplier_datatable'),

    # ============== المستودعات ==============
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/add/', WarehouseCreateView.as_view(), name='warehouse_add'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # أرصدة المستودعات
    path('warehouses/<int:pk>/inventory/', WarehouseInventoryView.as_view(), name='warehouse_inventory'),
    path('warehouse-items/<int:pk>/edit/', WarehouseItemUpdateView.as_view(), name='warehouse_item_edit'),

    # التحويلات بين المستودعات
    path('warehouse-transfers/', WarehouseTransferListView.as_view(), name='warehouse_transfer_list'),
    path('warehouse-transfers/add/', WarehouseTransferCreateView.as_view(), name='warehouse_transfer_add'),

    # تقارير وتصدير المستودعات
    path('warehouses/report/', WarehouseReportView.as_view(), name='warehouse_report'),
    path('inventory/report/', InventoryReportView.as_view(), name='inventory_report'),
    path('warehouses/export/', WarehouseExportView.as_view(), name='warehouse_export'),

    # DataTables و AJAX للمستودعات
    path('warehouses/datatable/', WarehouseDataTableView.as_view(), name='warehouse_datatable'),
    path('warehouses/ajax/search/', WarehouseSearchAjaxView.as_view(), name='warehouse_search_ajax'),
    path('warehouses/ajax/<int:pk>/info/', WarehouseInfoAjaxView.as_view(), name='warehouse_info_ajax'),
    path('warehouses/ajax/by-branch/', get_warehouses_by_branch_ajax, name='warehouses_by_branch_ajax'),
    path('warehouses/ajax/items/', get_warehouse_items_ajax, name='warehouse_items_ajax'),

    # ============== وحدات القياس ==============
    path('units/', UnitOfMeasureListView.as_view(), name='unit_list'),
    path('units/add/', UnitOfMeasureCreateView.as_view(), name='unit_add'),
    path('units/<int:pk>/edit/', UnitOfMeasureUpdateView.as_view(), name='unit_edit'),
    path('units/<int:pk>/delete/', UnitOfMeasureDeleteView.as_view(), name='unit_delete'),
    path('units/datatable/', UnitDataTableView.as_view(), name='unit_datatable'),
    path('units/ajax/search/', UnitSearchAjaxView.as_view(), name='unit_search_ajax'),

    # ============== API Endpoints للبحث السريع ==============
    path('ajax/items/search/', ItemSearchAPIView.as_view(), name='ajax_item_search'),
    path('ajax/partners/search/', PartnerSearchAPIView.as_view(), name='ajax_partner_search'),
    path('ajax/warehouses/search/', WarehouseSearchAPIView.as_view(), name='ajax_warehouse_search'),

    # ============== API Endpoints للتحقق من البيانات ==============
    path('ajax/check-barcode/', CheckBarcodeAPIView.as_view(), name='ajax_check_barcode'),
    path('ajax/check-code/', CheckCodeAPIView.as_view(), name='ajax_check_code'),

    # ============== API Endpoints للإحصائيات ==============
    path('ajax/stats/', StatsAPIView.as_view(), name='ajax_stats'),

    # ============== Function-based API Endpoints ==============
    path('ajax/item/by-barcode/', get_item_by_barcode, name='ajax_item_by_barcode'),
    path('ajax/warehouses/by-branch/', get_warehouses_by_branch, name='ajax_warehouses_by_branch'),
    path('ajax/item-stock/', get_item_stock_by_warehouse, name='ajax_item_stock'),

    # ============== REST API ==============
    path('api/v1/', include(router.urls)),

    # REST API إضافية
    path('api/v1/search/items/', ItemSearchAPIView.as_view(), name='api_search_items'),
    path('api/v1/search/partners/', PartnerSearchAPIView.as_view(), name='api_search_partners'),
    path('api/v1/search/warehouses/', WarehouseSearchAPIView.as_view(), name='api_search_warehouses'),
    path('api/v1/validation/barcode/', CheckBarcodeAPIView.as_view(), name='api_validate_barcode'),
    path('api/v1/validation/code/', CheckCodeAPIView.as_view(), name='api_validate_code'),
    path('api/v1/stats/', StatsAPIView.as_view(), name='api_stats'),
    path('api/v1/item/barcode/', get_item_by_barcode, name='api_item_barcode'),
    path('api/v1/warehouses/branch/', get_warehouses_by_branch, name='api_warehouses_branch'),
    path('api/v1/stock/item-warehouse/', get_item_stock_by_warehouse, name='api_stock_item_warehouse'),
]

# ============== معلومات إضافية للمطورين ==============
"""
تنظيم URLs:

1. الأصناف (/items/):
   - CRUD كامل مع التفاصيل
   - إدارة المكونات والمعدلات والبدائل
   - تقارير وتصدير
   - DataTables و AJAX

2. التصنيفات (/categories/):
   - دعم 4 مستويات
   - إدارة الشجرة الهرمية

3. الشركاء (/partners/):
   - CRUD شامل
   - إدارة معلومات الاتصال
   - تخصص للعملاء والموردين

4. المستودعات (/warehouses/):
   - إدارة شاملة للمستودعات
   - أرصدة وتحويلات
   - تقارير المخزون

5. وحدات القياس (/units/):
   - إدارة بسيطة وفعالة

6. AJAX Endpoints (/ajax/):
   - بحث سريع
   - تحقق من البيانات
   - إحصائيات

7. REST API (/api/v1/):
   - ViewSets كاملة
   - endpoints متخصصة
   - function-based APIs

المميزات:
- URLs منطقية ومنظمة
- REST API منفصل ومنظم  
- AJAX endpoints سهلة الاستخدام
- تدعم جميع العمليات المطلوبة
- متوافقة مع جميع الـ Views
- سهولة الصيانة والتطوير
"""
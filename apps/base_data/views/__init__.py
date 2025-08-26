# apps/base_data/views/__init__.py
"""
Views لتطبيق البيانات الأساسية - كامل ومطابق للمتطلبات
منظمة في ملفات منفصلة لسهولة الصيانة والتطوير
يشمل: الأصناف، الشركاء التجاريين، المستودعات، وحدات القياس، API
"""

# ============== Item Views ==============
from .item_views import (
    # Mixins والكلاسات الأساسية
    BaseItemMixin,

    # الأصناف
    ItemListView,
    ItemDetailView,
    ItemCreateView,
    ItemUpdateView,
    ItemDeleteView,

    # التصنيفات (4 مستويات)
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,

    # إدارة البيانات المرتبطة
    ItemComponentsManageView,
    ItemConversionsManageView,
    ItemSubstitutesManageView,

    # التقارير والتصدير
    ItemReportView,
    ItemExportView,

    # DataTables AJAX
    ItemDataTableView,

    # AJAX للنماذج
    ItemQuickAddView,
    ItemSearchAjaxView,
    ItemInfoAjaxView,
)

# ============== Partner Views ==============
from .partner_views import (
    # Mixins والكلاسات الأساسية
    BasePartnerMixin,

    # الشركاء التجاريين
    BusinessPartnerListView,
    BusinessPartnerDetailView,
    BusinessPartnerCreateView,
    BusinessPartnerUpdateView,
    BusinessPartnerDeleteView,

    # العملاء
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDetailView,

    # الموردين
    SupplierListView,
    SupplierCreateView,
    SupplierUpdateView,
    SupplierDetailView,

    # معلومات الاتصال
    ContactInfoManageView,

    # التقارير والتصدير
    PartnerReportView,
    PartnerExportView,

    # DataTables AJAX
    BusinessPartnerDataTableView,
    CustomerDataTableView,
    SupplierDataTableView,

    # AJAX للنماذج
    PartnerQuickAddView,
    PartnerSearchAjaxView,
    PartnerInfoAjaxView,
)

# ============== Warehouse Views ==============
from .warehouse_views import (
    # Mixins والكلاسات الأساسية
    BaseWarehouseMixin,

    # المستودعات
    WarehouseListView,
    WarehouseDetailView,
    WarehouseCreateView,
    WarehouseUpdateView,
    WarehouseDeleteView,

    # أرصدة المستودعات
    WarehouseInventoryView,
    WarehouseItemUpdateView,

    # التحويلات بين المستودعات
    WarehouseTransferListView,
    WarehouseTransferCreateView,

    # وحدات القياس
    UnitOfMeasureListView,
    UnitOfMeasureCreateView,
    UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView,

    # التقارير والتصدير
    WarehouseReportView,
    InventoryReportView,
    WarehouseExportView,

    # DataTables AJAX
    WarehouseDataTableView,
    UnitDataTableView,

    # AJAX للنماذج
    WarehouseSearchAjaxView,
    WarehouseInfoAjaxView,
    UnitSearchAjaxView,

    # Views مساعدة
    get_warehouses_by_branch_ajax,
    get_warehouse_items_ajax,
)

# ============== API Views ==============
from .api_views import (
    # Permissions والكلاسات الأساسية
    BaseDataPermission,
    BaseDataViewSetMixin,

    # ViewSets للتصنيفات
    ItemCategoryViewSet,

    # ViewSets للأصناف
    ItemViewSet,

    # ViewSets للشركاء التجاريين
    BusinessPartnerViewSet,
    CustomerViewSet,
    SupplierViewSet,

    # ViewSets للمستودعات
    WarehouseViewSet,

    # ViewSets لوحدات القياس
    UnitOfMeasureViewSet,

    # API Views البحث السريع
    ItemSearchAPIView,
    PartnerSearchAPIView,
    WarehouseSearchAPIView,

    # API Views التحقق من البيانات
    CheckBarcodeAPIView,
    CheckCodeAPIView,

    # API Views الإحصائيات
    StatsAPIView,

    # Function-based API Views
    get_item_by_barcode,
    get_warehouses_by_branch,
    get_item_stock_by_warehouse,
)

# ============== __all__ للتنظيم والاستيراد ==============
__all__ = [
    # ========== Base Classes ==========
    'BaseItemMixin',
    'BasePartnerMixin',
    'BaseWarehouseMixin',
    'BaseDataPermission',
    'BaseDataViewSetMixin',

    # ========== الأصناف ==========
    'ItemListView',
    'ItemDetailView',
    'ItemCreateView',
    'ItemUpdateView',
    'ItemDeleteView',
    'ItemDataTableView',
    'ItemQuickAddView',
    'ItemSearchAjaxView',
    'ItemInfoAjaxView',
    'ItemReportView',
    'ItemExportView',

    # ========== التصنيفات ==========
    'CategoryListView',
    'CategoryCreateView',
    'CategoryUpdateView',

    # ========== إدارة البيانات المرتبطة ==========
    'ItemComponentsManageView',
    'ItemConversionsManageView',
    'ItemSubstitutesManageView',

    # ========== الشركاء التجاريين ==========
    'BusinessPartnerListView',
    'BusinessPartnerDetailView',
    'BusinessPartnerCreateView',
    'BusinessPartnerUpdateView',
    'BusinessPartnerDeleteView',
    'BusinessPartnerDataTableView',
    'PartnerQuickAddView',
    'PartnerSearchAjaxView',
    'PartnerInfoAjaxView',
    'PartnerReportView',
    'PartnerExportView',

    # ========== العملاء ==========
    'CustomerListView',
    'CustomerDetailView',
    'CustomerCreateView',
    'CustomerUpdateView',
    'CustomerDataTableView',

    # ========== الموردين ==========
    'SupplierListView',
    'SupplierDetailView',
    'SupplierCreateView',
    'SupplierUpdateView',
    'SupplierDataTableView',

    # ========== معلومات الاتصال ==========
    'ContactInfoManageView',

    # ========== المستودعات ==========
    'WarehouseListView',
    'WarehouseDetailView',
    'WarehouseCreateView',
    'WarehouseUpdateView',
    'WarehouseDeleteView',
    'WarehouseDataTableView',
    'WarehouseSearchAjaxView',
    'WarehouseInfoAjaxView',
    'WarehouseReportView',
    'WarehouseExportView',

    # ========== أرصدة المستودعات ==========
    'WarehouseInventoryView',
    'WarehouseItemUpdateView',
    'InventoryReportView',

    # ========== التحويلات بين المستودعات ==========
    'WarehouseTransferListView',
    'WarehouseTransferCreateView',

    # ========== وحدات القياس ==========
    'UnitOfMeasureListView',
    'UnitOfMeasureCreateView',
    'UnitOfMeasureUpdateView',
    'UnitOfMeasureDeleteView',
    'UnitDataTableView',
    'UnitSearchAjaxView',

    # ========== API ViewSets ==========
    'ItemCategoryViewSet',
    'ItemViewSet',
    'BusinessPartnerViewSet',
    'CustomerViewSet',
    'SupplierViewSet',
    'WarehouseViewSet',
    'UnitOfMeasureViewSet',

    # ========== API Views البحث ==========
    'ItemSearchAPIView',
    'PartnerSearchAPIView',
    'WarehouseSearchAPIView',

    # ========== API Views التحقق ==========
    'CheckBarcodeAPIView',
    'CheckCodeAPIView',

    # ========== API Views الإحصائيات ==========
    'StatsAPIView',

    # ========== Function-based Views ==========
    'get_item_by_barcode',
    'get_warehouses_by_branch',
    'get_warehouses_by_branch_ajax',
    'get_warehouse_items_ajax',
    'get_item_stock_by_warehouse',
]

# ============== معلومات إضافية للمطورين ==============
"""
تنظيم Views التطبيق:

1. item_views.py:
   - الأصناف والتصنيفات (4 مستويات)
   - معدلات التحويل والمكونات والمواد البديلة
   - التقارير والتصدير والـ DataTables
   - AJAX Views للبحث والمعلومات السريعة

2. partner_views.py:
   - الشركاء التجاريين (عملاء، موردين، كلاهما)
   - معلومات الاتصال والحسابات
   - التقارير والتصدير المتخصصة
   - AJAX Views للبحث والتحقق

3. warehouse_views.py:
   - المستودعات وأنواعها (رئيسي، فرعي، عبور، تالف)
   - أرصدة المستودعات وإدارة المخزون
   - التحويلات بين المستودعات
   - وحدات القياس والتحويلات
   - تقارير الأرصدة والمخزون

4. api_views.py:
   - REST API ViewSets كاملة
   - API للبحث والتحقق من البيانات
   - إحصائيات ومعلومات النظام
   - Function-based APIs للوظائف السريعة

المميزات الرئيسية:
- صلاحيات مفصلة لكل عملية
- فلترة تلقائية حسب الشركة والفرع  
- Breadcrumbs للتنقل
- DataTables مع Server-side processing
- AJAX للعمليات السريعة
- تقارير وتصدير Excel/CSV
- REST API شامل
- إدارة الأخطاء والرسائل
- دعم اللغة العربية والإنجليزية
"""
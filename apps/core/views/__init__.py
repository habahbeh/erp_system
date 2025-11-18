# apps/core/views/__init__.py - التحديث النهائي مع Price Views
"""
استيراد جميع الـ Views
"""

from .base_views import dashboard, dashboard_ajax, switch_company, get_company_branches
from .item_views import (
    ItemListView, ItemCreateView, ItemUpdateView, ItemDeleteView, ItemDetailView,
    ItemCategoryListView, ItemCategoryCreateView, ItemCategoryUpdateView, ItemCategoryDeleteView
)
from .partner_views import (
    BusinessPartnerListView, BusinessPartnerCreateView, BusinessPartnerUpdateView,
    BusinessPartnerDeleteView, BusinessPartnerDetailView, partner_create_ajax, item_search_ajax
)
from .warehouse_views import (
    WarehouseListView, WarehouseCreateView, WarehouseUpdateView,
    WarehouseDeleteView, WarehouseDetailView
)
from .brand_views import (
    BrandListView, BrandCreateView, BrandUpdateView,
    BrandDeleteView, BrandDetailView
)
from .unit_views import (
    UnitOfMeasureListView, UnitOfMeasureCreateView, UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView, UnitOfMeasureDetailView
)
from .currency_views import (
    CurrencyListView, CurrencyCreateView, CurrencyUpdateView,
    CurrencyDeleteView, CurrencyDetailView
)
from .company_views import (
    CompanyDetailView, CompanyUpdateView
)
from .branch_views import (
    BranchListView, BranchCreateView, BranchUpdateView,
    BranchDeleteView, BranchDetailView
)
from .numbering_views import (
    NumberingSequenceListView, NumberingSequenceUpdateView
)
from .user_views import (
    UserListView, UserCreateView, UserUpdateView,
    UserDeleteView, UserDetailView, change_password_view
)
from .user_profile_views import (
    UserProfileListView, UserProfileDetailView, UserProfileUpdateView,
    BulkUserProfileUpdateView, user_permissions_view, create_missing_profiles, UserProfileDeleteView
)
from .variant_views import (
    VariantAttributeListView, VariantAttributeCreateView, VariantAttributeUpdateView,
    VariantAttributeDeleteView, VariantAttributeDetailView
)
from .permission_views import (
    CustomPermissionListView, CustomPermissionCreateView, CustomPermissionUpdateView,
    CustomPermissionDeleteView, CustomPermissionDetailView,
    PermissionGroupListView, PermissionGroupCreateView, PermissionGroupUpdateView,
    PermissionGroupDeleteView, PermissionGroupDetailView,
    BulkPermissionAssignView, CopyUserPermissionsView, create_default_permission_groups
)

# ✅ إضافة Price Views الجديدة
from .price_views import (
    PriceListListView, PriceListCreateView, PriceListUpdateView,
    PriceListDeleteView, PriceListDetailView, PriceListItemsView,
    ItemPricesView, update_item_prices, bulk_update_prices, update_price_list_items
)

# ✅ Week 1 Day 4: إضافة Views الجديدة للنماذج الثلاثة
from .uom_views import (
    UoMConversionListView, UoMConversionDetailView, UoMConversionCreateView,
    UoMConversionUpdateView, UoMConversionDeleteView, UoMConversionBulkCreateView
)

# ⭐ Week 2 Day 2: UoM Group Views
from .uom_group_views import (
    UoMGroupListView, UoMGroupDetailView, UoMGroupCreateView,
    UoMGroupUpdateView, UoMGroupDeleteView
)

# ⭐ Week 2 Day 4: UoM Import/Export Views
from .uom_import_export_views import (
    ExportConversionsView, ImportConversionsView,
    DownloadTemplateView, ImportResultsView
)

from .pricing_views import (
    PricingRuleListView, PricingRuleDetailView, PricingRuleCreateView,
    PricingRuleUpdateView, PricingRuleDeleteView, PricingRuleTestView, PricingRuleCloneView
)
from .price_calculator_views import (
    BulkPriceUpdateView, PriceSimulatorView, PriceComparisonView,
    PriceReportView, ItemPriceCalculatorView
)
from .template_views import (
    ItemTemplateListView, ItemTemplateDetailView, ItemTemplateCreateView,
    ItemTemplateWizardCreateView, ItemTemplateUpdateView, ItemTemplateDeleteView,
    ItemTemplateCloneView, ItemTemplateUseView
)

# ⭐ Week 4 Day 1: Chart Views for Price Visualizations
from .chart_views import (
    PriceTrendChartView, PriceDistributionChartView, CategoryPriceComparisonChartView,
    PriceListComparisonChartView, PricingRulesImpactChartView,
    PriceStatisticsSummaryView, MonthlyPriceChangesChartView
)

# ⭐ Week 4 Day 1: Pricing Dashboard
from .pricing_dashboard_view import PricingDashboardView

# ⭐ Week 4 Day 2: DataTables Views
from .datatables_views import (
    PricingRuleDatatableView, PriceListItemDatatableView, ItemPricesDatatableView,
    ExportPricingRulesView, ExportPriceListItemsView
)

# ⭐ Week 4 Day 2: Enhanced List Views with DataTables
from .pricing_list_views import (
    PricingRuleListDTView, PriceListItemsDTView
)

# ⭐ Week 4 Day 3: AJAX Price Operations
from .ajax_price_views import (
    UpdatePriceAjaxView, BulkUpdatePricesAjaxView, CalculatePriceAjaxView,
    ValidatePriceRuleAjaxView, TogglePriceRuleAjaxView, GetItemPricesAjaxView
)

# ⭐ Week 4 Day 3: Inline Price Editor
from .inline_price_editor_view import InlinePriceEditorView

# ⭐ Week 4 Day 4: Dashboard Widgets & Enhanced Dashboards
from .dashboard_views import (
    EnhancedPricingDashboardView, MainDashboardView
)

# ⭐ Week 5: Import/Export System
from .price_import_export_views import (
    PriceListExportView, PriceListImportView, PriceListImportResultsView,
    PricingRuleExportView, PriceListTemplateDownloadView,
    BulkPriceExportView, ItemsExportView
)

from .ajax_views import (
    item_datatable_ajax, partner_datatable_ajax, warehouse_datatable_ajax,
    brand_datatable_ajax, unit_datatable_ajax, currency_datatable_ajax,
    branch_datatable_ajax, variant_attribute_datatable_ajax, user_datatable_ajax,
    profile_datatable_ajax, permission_datatable_ajax, group_datatable_ajax,
    price_list_datatable_ajax  , price_list_items_ajax
)


__all__ = [
    # Base Views
    'dashboard',
    'dashboard_ajax',
    'switch_company',
    'get_company_branches',

    # Item Views
    'ItemListView',
    'ItemCreateView',
    'ItemUpdateView',
    'ItemDeleteView',
    'ItemDetailView',

    # Category Views
    'ItemCategoryListView',
    'ItemCategoryCreateView',
    'ItemCategoryUpdateView',
    'ItemCategoryDeleteView',

    # Partner Views
    'BusinessPartnerListView',
    'BusinessPartnerCreateView',
    'BusinessPartnerUpdateView',
    'BusinessPartnerDeleteView',
    'BusinessPartnerDetailView',

    # Warehouse Views
    'WarehouseListView',
    'WarehouseCreateView',
    'WarehouseUpdateView',
    'WarehouseDeleteView',
    'WarehouseDetailView',

    # Brand Views
    'BrandListView',
    'BrandCreateView',
    'BrandUpdateView',
    'BrandDeleteView',
    'BrandDetailView',

    # Unit Views
    'UnitOfMeasureListView',
    'UnitOfMeasureCreateView',
    'UnitOfMeasureUpdateView',
    'UnitOfMeasureDeleteView',
    'UnitOfMeasureDetailView',

    # Currency Views
    'CurrencyListView',
    'CurrencyCreateView',
    'CurrencyUpdateView',
    'CurrencyDeleteView',
    'CurrencyDetailView',

    # Company Views
    'CompanyDetailView',
    'CompanyUpdateView',

    # Branch Views
    'BranchListView',
    'BranchCreateView',
    'BranchUpdateView',
    'BranchDeleteView',
    'BranchDetailView',

    # Numbering Views
    'NumberingSequenceListView',
    'NumberingSequenceUpdateView',

    # User Views
    'UserListView',
    'UserCreateView',
    'UserUpdateView',
    'UserDeleteView',
    'UserDetailView',
    'change_password_view',

    # User Profile Views
    'UserProfileListView',
    'UserProfileDetailView',
    'UserProfileUpdateView',
    'UserProfileDeleteView',
    'BulkUserProfileUpdateView',
    'user_permissions_view',
    'create_missing_profiles',

    # Variant Views
    'VariantAttributeListView',
    'VariantAttributeCreateView',
    'VariantAttributeUpdateView',
    'VariantAttributeDeleteView',
    'VariantAttributeDetailView',

    # Permission Views
    'CustomPermissionListView',
    'CustomPermissionCreateView',
    'CustomPermissionUpdateView',
    'CustomPermissionDeleteView',
    'CustomPermissionDetailView',
    'PermissionGroupListView',
    'PermissionGroupCreateView',
    'PermissionGroupUpdateView',
    'PermissionGroupDeleteView',
    'PermissionGroupDetailView',
    'BulkPermissionAssignView',
    'CopyUserPermissionsView',
    'create_default_permission_groups',

    # ✅ Price Views الجديدة
    'PriceListListView',
    'PriceListCreateView',
    'PriceListUpdateView',
    'PriceListDeleteView',
    'PriceListDetailView',
    'PriceListItemsView',
    'ItemPricesView',
    'update_item_prices',
    'bulk_update_prices',
    'update_price_list_items',

    # Ajax Views
    'item_datatable_ajax',
    'partner_datatable_ajax',
    'warehouse_datatable_ajax',
    'brand_datatable_ajax',
    'unit_datatable_ajax',
    'currency_datatable_ajax',
    'branch_datatable_ajax',
    'variant_attribute_datatable_ajax',
    'user_datatable_ajax',
    'profile_datatable_ajax',
    'permission_datatable_ajax',
    'group_datatable_ajax',
    'price_list_datatable_ajax',
    'price_list_items_ajax',

    # ✅ Week 1 Day 4: UoM Conversion Views (6)
    'UoMConversionListView',
    'UoMConversionDetailView',
    'UoMConversionCreateView',
    'UoMConversionUpdateView',
    'UoMConversionDeleteView',
    'UoMConversionBulkCreateView',

    # ⭐ Week 2 Day 2: UoM Group Views (5)
    'UoMGroupListView',
    'UoMGroupDetailView',
    'UoMGroupCreateView',
    'UoMGroupUpdateView',
    'UoMGroupDeleteView',

    # ⭐ Week 2 Day 4: UoM Import/Export Views (4)
    'ExportConversionsView',
    'ImportConversionsView',
    'DownloadTemplateView',
    'ImportResultsView',

    # ✅ Week 1 Day 4: Pricing Rule Views (7)
    'PricingRuleListView',
    'PricingRuleDetailView',
    'PricingRuleCreateView',
    'PricingRuleUpdateView',
    'PricingRuleDeleteView',
    'PricingRuleTestView',
    'PricingRuleCloneView',

    # ✅ Week 3 Day 3: Price Calculator Views (5)
    'BulkPriceUpdateView',
    'PriceSimulatorView',
    'PriceComparisonView',
    'PriceReportView',
    'ItemPriceCalculatorView',

    # ✅ Week 1 Day 4: Item Template Views (8)
    'ItemTemplateListView',
    'ItemTemplateDetailView',
    'ItemTemplateCreateView',
    'ItemTemplateWizardCreateView',
    'ItemTemplateUpdateView',
    'ItemTemplateDeleteView',
    'ItemTemplateCloneView',
    'ItemTemplateUseView',

    # ⭐ Week 4 Day 1: Chart Views for Price Visualizations (7)
    'PriceTrendChartView',
    'PriceDistributionChartView',
    'CategoryPriceComparisonChartView',
    'PriceListComparisonChartView',
    'PricingRulesImpactChartView',
    'PriceStatisticsSummaryView',
    'MonthlyPriceChangesChartView',

    # ⭐ Week 4 Day 1: Pricing Dashboard (1)
    'PricingDashboardView',

    # ⭐ Week 4 Day 2: DataTables Views (5)
    'PricingRuleDatatableView',
    'PriceListItemDatatableView',
    'ItemPricesDatatableView',
    'ExportPricingRulesView',
    'ExportPriceListItemsView',

    # ⭐ Week 4 Day 2: Enhanced List Views (2)
    'PricingRuleListDTView',
    'PriceListItemsDTView',

    # ⭐ Week 4 Day 3: AJAX Price Operations (6)
    'UpdatePriceAjaxView',
    'BulkUpdatePricesAjaxView',
    'CalculatePriceAjaxView',
    'ValidatePriceRuleAjaxView',
    'TogglePriceRuleAjaxView',
    'GetItemPricesAjaxView',

    # ⭐ Week 4 Day 3: Inline Price Editor (1)
    'InlinePriceEditorView',

    # ⭐ Week 4 Day 4: Dashboard Widgets & Enhanced Dashboards (2)
    'EnhancedPricingDashboardView',
    'MainDashboardView',

    # ⭐ Week 5: Import/Export System (7)
    'PriceListExportView',
    'PriceListImportView',
    'PriceListImportResultsView',
    'PricingRuleExportView',
    'PriceListTemplateDownloadView',
    'BulkPriceExportView',
    'ItemsExportView',
]
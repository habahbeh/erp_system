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
    BusinessPartnerDeleteView, BusinessPartnerDetailView
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
    ItemPricesView, update_item_prices, bulk_update_prices
)

from .ajax_views import (
    item_datatable_ajax, partner_datatable_ajax, warehouse_datatable_ajax,
    brand_datatable_ajax, unit_datatable_ajax, currency_datatable_ajax,
    branch_datatable_ajax, variant_attribute_datatable_ajax, user_datatable_ajax,
    profile_datatable_ajax, permission_datatable_ajax, group_datatable_ajax,
    price_list_datatable_ajax  # ✅ إضافة Ajax view للأسعار
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
    'price_list_datatable_ajax',  # ✅ Ajax للأسعار
]
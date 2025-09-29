# apps/core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # الرئيسية
    path('', views.dashboard, name='dashboard'),
    path('ajax/dashboard/', views.dashboard_ajax, name='dashboard_ajax'),
    # path('switch-branch/<int:branch_id>/', views.switch_branch, name='switch_branch'),
    path('switch-company/<int:company_id>/', views.switch_company, name='switch_company'),
    path('ajax/company/<int:company_id>/branches/', views.get_company_branches, name='company_branches'),

    # المواد
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/update/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),


    # تصنيفات المواد
    path('categories/', views.ItemCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ItemCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.ItemCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ItemCategoryDeleteView.as_view(), name='category_delete'),

    # العملاء
    path('partners/', views.BusinessPartnerListView.as_view(), name='partner_list'),
    path('partners/<int:pk>/', views.BusinessPartnerDetailView.as_view(), name='partner_detail'),
    path('partners/create/', views.BusinessPartnerCreateView.as_view(), name='partner_create'),
    path('partners/<int:pk>/update/', views.BusinessPartnerUpdateView.as_view(), name='partner_update'),
    path('partners/<int:pk>/delete/', views.BusinessPartnerDeleteView.as_view(), name='partner_delete'),

    # المستودعات
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/update/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # العلامات التجارية
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<int:pk>/update/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),

    # وحدات القياس
    path('units/', views.UnitOfMeasureListView.as_view(), name='unit_list'),
    path('units/<int:pk>/', views.UnitOfMeasureDetailView.as_view(), name='unit_detail'),
    path('units/create/', views.UnitOfMeasureCreateView.as_view(), name='unit_create'),
    path('units/<int:pk>/update/', views.UnitOfMeasureUpdateView.as_view(), name='unit_update'),
    path('units/<int:pk>/delete/', views.UnitOfMeasureDeleteView.as_view(), name='unit_delete'),

    # العملات
    path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currencies/<int:pk>/', views.CurrencyDetailView.as_view(), name='currency_detail'),
    path('currencies/create/', views.CurrencyCreateView.as_view(), name='currency_create'),
    path('currencies/<int:pk>/update/', views.CurrencyUpdateView.as_view(), name='currency_update'),
    path('currencies/<int:pk>/delete/', views.CurrencyDeleteView.as_view(), name='currency_delete'),

    # الشركة
    path('company/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('company/update/', views.CompanyUpdateView.as_view(), name='company_update'),

    # الفروع - إضافة جديد
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
    path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/update/', views.BranchUpdateView.as_view(), name='branch_update'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),

    # تسلسل الترقيم - إضافة جديد
    path('numbering/', views.NumberingSequenceListView.as_view(), name='numbering_list'),
    path('numbering/<str:document_type>/', views.NumberingSequenceUpdateView.as_view(), name='numbering_update'),

    # خصائص المتغيرات - إضافة جديد
    path('variant-attributes/', views.VariantAttributeListView.as_view(), name='variant_attribute_list'),
    path('variant-attributes/<int:pk>/', views.VariantAttributeDetailView.as_view(), name='variant_attribute_detail'),
    path('variant-attributes/create/', views.VariantAttributeCreateView.as_view(), name='variant_attribute_create'),
    path('variant-attributes/<int:pk>/update/', views.VariantAttributeUpdateView.as_view(),
         name='variant_attribute_update'),
    path('variant-attributes/<int:pk>/delete/', views.VariantAttributeDeleteView.as_view(),
         name='variant_attribute_delete'),


    # المستخدمين - إضافة جديد
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/change-password/', views.change_password_view, name='user_change_password'),


    # ملفات المستخدمين
    path('profiles/', views.UserProfileListView.as_view(), name='profile_list'),
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='profile_detail'),
    path('profiles/<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile_update'),
    path('profiles/<int:pk>/delete/', views.UserProfileDeleteView.as_view(), name='profile_delete'),  # إضافة جديد
    path('profiles/bulk-update/', views.BulkUserProfileUpdateView.as_view(), name='bulk_profile_update'),
    path('profiles/create-missing/', views.create_missing_profiles, name='create_missing_profiles'),
    path('users/<int:user_id>/permissions/', views.user_permissions_view, name='user_permissions'),

    # الصلاحيات المخصصة - إضافة جديد
    path('permissions/', views.CustomPermissionListView.as_view(), name='permission_list'),
    path('permissions/<int:pk>/', views.CustomPermissionDetailView.as_view(), name='permission_detail'),
    path('permissions/create/', views.CustomPermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<int:pk>/update/', views.CustomPermissionUpdateView.as_view(), name='permission_update'),
    path('permissions/<int:pk>/delete/', views.CustomPermissionDeleteView.as_view(), name='permission_delete'),

    # مجموعات الصلاحيات - إضافة جديد
    path('permission-groups/', views.PermissionGroupListView.as_view(), name='group_list'),
    path('permission-groups/<int:pk>/', views.PermissionGroupDetailView.as_view(), name='group_detail'),
    path('permission-groups/create/', views.PermissionGroupCreateView.as_view(), name='group_create'),
    path('permission-groups/<int:pk>/update/', views.PermissionGroupUpdateView.as_view(), name='group_update'),
    path('permission-groups/<int:pk>/delete/', views.PermissionGroupDeleteView.as_view(), name='group_delete'),
    path('permissions/create-default-groups/', views.create_default_permission_groups, name='create_default_groups'),


    # العمليات المتقدمة - إضافة جديد
    path('permissions/bulk-assign/', views.BulkPermissionAssignView.as_view(), name='bulk_permission_assign'),
    path('permissions/copy-user-permissions/', views.CopyUserPermissionsView.as_view(), name='copy_user_permissions'),



    # Ajax endpoints
    path('ajax/items/datatable/', views.item_datatable_ajax, name='item_datatable_ajax'),
    path('ajax/partners/datatable/', views.partner_datatable_ajax, name='partner_datatable_ajax'),
    path('ajax/warehouses/datatable/', views.warehouse_datatable_ajax, name='warehouse_datatable_ajax'),
    path('ajax/brands/datatable/', views.brand_datatable_ajax, name='brand_datatable_ajax'),
    path('ajax/units/datatable/', views.unit_datatable_ajax, name='unit_datatable_ajax'),
    path('ajax/currencies/datatable/', views.currency_datatable_ajax, name='currency_datatable_ajax'),
    path('ajax/branches/datatable/', views.branch_datatable_ajax, name='branch_datatable_ajax'),  # إضافة جديد
    path('ajax/variant-attributes/datatable/', views.variant_attribute_datatable_ajax, name='variant_attribute_datatable_ajax'),
    path('ajax/users/datatable/', views.user_datatable_ajax, name='user_datatable_ajax'),  # إضافة جديد
    path('ajax/profiles/datatable/', views.profile_datatable_ajax, name='profile_datatable_ajax'),  # إضافة جديد
    path('ajax/permissions/datatable/', views.permission_datatable_ajax, name='permission_datatable_ajax'),  # إضافة جديد
    path('ajax/groups/datatable/', views.group_datatable_ajax, name='group_datatable_ajax'),  # إضافة جديد


    # قوائم الأسعار
    path('price-lists/', views.PriceListListView.as_view(), name='price_list_list'),
    path('price-lists/create/', views.PriceListCreateView.as_view(), name='price_list_create'),
    path('price-lists/<int:pk>/', views.PriceListDetailView.as_view(), name='price_list_detail'),
    path('price-lists/<int:pk>/update/', views.PriceListUpdateView.as_view(), name='price_list_update'),
    path('price-lists/<int:pk>/delete/', views.PriceListDeleteView.as_view(), name='price_list_delete'),
    path('price-lists/<int:pk>/items/', views.PriceListItemsView.as_view(), name='price_list_items'),

    # إدارة أسعار الأمواد
    path('items/<int:item_id>/prices/', views.ItemPricesView.as_view(), name='item_prices'),
    path('items/<int:item_id>/prices/update/', views.update_item_prices, name='update_item_prices'),

    # التحديث الجماعي
    path('price-lists/<int:price_list_id>/bulk-update/', views.bulk_update_prices, name='bulk_update_prices'),

    # Ajax
    path('ajax/price-lists/datatable/', views.price_list_datatable_ajax, name='price_list_datatable_ajax'),


]





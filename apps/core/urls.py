# apps/core/urls.py
"""
URLs الأساسية لتطبيق النواة
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # الرئيسية
    path('', views.dashboard, name='dashboard'),
    path('switch-branch/<int:branch_id>/', views.switch_branch, name='switch_branch'),

    # الأصناف
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/update/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),

    # تصنيفات الأصناف
    path('categories/', views.ItemCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ItemCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.ItemCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ItemCategoryDeleteView.as_view(), name='category_delete'),

    # الشركاء التجاريون
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

    # Ajax endpoints
    path('ajax/items/datatable/', views.item_datatable_ajax, name='item_datatable_ajax'),
    path('ajax/partners/datatable/', views.partner_datatable_ajax, name='partner_datatable_ajax'),
    path('ajax/warehouses/datatable/', views.warehouse_datatable_ajax, name='warehouse_datatable_ajax'),
    path('ajax/brands/datatable/', views.brand_datatable_ajax, name='brand_datatable_ajax'),
    path('ajax/units/datatable/', views.unit_datatable_ajax, name='unit_datatable_ajax'),
    path('ajax/currencies/datatable/', views.currency_datatable_ajax, name='currency_datatable_ajax'),

]






# # apps/core/urls.py
# """
# URLs الأساسية لتطبيق النواة
# """
#
# from django.urls import path
# from . import views
#
# app_name = 'core'
#
# urlpatterns = [
#     # الرئيسية
#     path('', views.dashboard, name='dashboard'),
#     path('switch-branch/<int:branch_id>/', views.switch_branch, name='switch_branch'),
#
#     # الشركات
#     # path('companies/', views.CompanyListView.as_view(), name='company_list'),
#     # path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
#     # path('companies/<int:pk>/update/', views.CompanyUpdateView.as_view(), name='company_update'),
#     # path('companies/<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
#     #
#     # # الفروع
#     # path('branches/', views.BranchListView.as_view(), name='branch_list'),
#     # path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
#     # path('branches/<int:pk>/update/', views.BranchUpdateView.as_view(), name='branch_update'),
#     # path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
#     #
#     # # المستودعات
#     # path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
#     # path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
#     # path('warehouses/<int:pk>/update/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
#     # path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouse_delete'),
#     #
#     # # الشركاء التجاريين
#     # path('partners/', views.BusinessPartnerListView.as_view(), name='partner_list'),
#     # path('partners/create/', views.BusinessPartnerCreateView.as_view(), name='partner_create'),
#     # path('partners/<int:pk>/update/', views.BusinessPartnerUpdateView.as_view(), name='partner_update'),
#     # path('partners/<int:pk>/delete/', views.BusinessPartnerDeleteView.as_view(), name='partner_delete'),
#     #
#     # # الأصناف
#     path('items/', views.ItemListView.as_view(), name='item_list'),
#     path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
#     path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
#     path('items/<int:pk>/update/', views.ItemUpdateView.as_view(), name='item_update'),
#     path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
#
#     #
#     # # تصنيفات الأصناف
#     path('categories/', views.ItemCategoryListView.as_view(), name='category_list'),
#     path('categories/create/', views.ItemCategoryCreateView.as_view(), name='category_create'),
#     path('categories/<int:pk>/update/', views.ItemCategoryUpdateView.as_view(), name='category_update'),
#     path('categories/<int:pk>/delete/', views.ItemCategoryDeleteView.as_view(), name='category_delete'),
#     #
#     # # العلامات التجارية
#     # path('brands/', views.BrandListView.as_view(), name='brand_list'),
#     # path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
#     # path('brands/<int:pk>/update/', views.BrandUpdateView.as_view(), name='brand_update'),
#     # path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
#     #
#     # # وحدات القياس
#     # path('units/', views.UnitOfMeasureListView.as_view(), name='unit_list'),
#     # path('units/create/', views.UnitOfMeasureCreateView.as_view(), name='unit_create'),
#     # path('units/<int:pk>/update/', views.UnitOfMeasureUpdateView.as_view(), name='unit_update'),
#     # path('units/<int:pk>/delete/', views.UnitOfMeasureDeleteView.as_view(), name='unit_delete'),
#     #
#     # # العملات
#     # path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
#     # path('currencies/create/', views.CurrencyCreateView.as_view(), name='currency_create'),
#     # path('currencies/<int:pk>/update/', views.CurrencyUpdateView.as_view(), name='currency_update'),
#     # path('currencies/<int:pk>/delete/', views.CurrencyDeleteView.as_view(), name='currency_delete'),
#     #
#     # # المستخدمين
#     # path('users/', views.UserListView.as_view(), name='user_list'),
#     # path('users/create/', views.UserCreateView.as_view(), name='user_create'),
#     # path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
#     # path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
#     #
#     # # ملفات المستخدمين
#     # path('profiles/', views.UserProfileListView.as_view(), name='profile_list'),
#     # path('profiles/create/', views.UserProfileCreateView.as_view(), name='profile_create'),
#     # path('profiles/<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile_update'),
#     # path('profiles/<int:pk>/delete/', views.UserProfileDeleteView.as_view(), name='profile_delete'),
#     #
#     # # تسلسل الترقيم
#     # path('numbering/', views.NumberingSequenceListView.as_view(), name='numbering_list'),
#     # path('numbering/create/', views.NumberingSequenceCreateView.as_view(), name='numbering_create'),
#     # path('numbering/<int:pk>/update/', views.NumberingSequenceUpdateView.as_view(), name='numbering_update'),
#     # path('numbering/<int:pk>/delete/', views.NumberingSequenceDeleteView.as_view(), name='numbering_delete'),
#     #
#     # # الصلاحيات المخصصة
#     # path('permissions/', views.CustomPermissionListView.as_view(), name='permission_list'),
#     # path('permissions/create/', views.CustomPermissionCreateView.as_view(), name='permission_create'),
#     # path('permissions/<int:pk>/update/', views.CustomPermissionUpdateView.as_view(), name='permission_update'),
#     # path('permissions/<int:pk>/delete/', views.CustomPermissionDeleteView.as_view(), name='permission_delete'),
#     #
#     # # خصائص المتغيرات
#     # path('variant-attributes/', views.VariantAttributeListView.as_view(), name='variant_attribute_list'),
#     # path('variant-attributes/create/', views.VariantAttributeCreateView.as_view(), name='variant_attribute_create'),
#     # path('variant-attributes/<int:pk>/update/', views.VariantAttributeUpdateView.as_view(), name='variant_attribute_update'),
#     # path('variant-attributes/<int:pk>/delete/', views.VariantAttributeDeleteView.as_view(), name='variant_attribute_delete'),
#     #
#     # # قيم المتغيرات
#     # path('variant-values/', views.VariantValueListView.as_view(), name='variant_value_list'),
#     # path('variant-values/create/', views.VariantValueCreateView.as_view(), name='variant_value_create'),
#     # path('variant-values/<int:pk>/update/', views.VariantValueUpdateView.as_view(), name='variant_value_update'),
#     # path('variant-values/<int:pk>/delete/', views.VariantValueDeleteView.as_view(), name='variant_value_delete'),
#     #
#     # # متغيرات الأصناف
#     # path('item-variants/', views.ItemVariantListView.as_view(), name='item_variant_list'),
#     # path('item-variants/create/', views.ItemVariantCreateView.as_view(), name='item_variant_create'),
#     # path('item-variants/<int:pk>/update/', views.ItemVariantUpdateView.as_view(), name='item_variant_update'),
#     # path('item-variants/<int:pk>/delete/', views.ItemVariantDeleteView.as_view(), name='item_variant_delete'),
#     #
#     # # إعدادات النظام
#     # path('settings/', views.SystemSettingsListView.as_view(), name='settings_list'),
#     # path('settings/create/', views.SystemSettingsCreateView.as_view(), name='settings_create'),
#     # path('settings/<int:pk>/update/', views.SystemSettingsUpdateView.as_view(), name='settings_update'),
#     # path('settings/<int:pk>/delete/', views.SystemSettingsDeleteView.as_view(), name='settings_delete'),
#     #
#     # # سجل العمليات
#     # path('audit-log/', views.AuditLogListView.as_view(), name='audit_list'),
#     # path('audit-log/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit_detail'),
#     #
#     # Ajax endpoints
#     path('ajax/items/datatable/', views.item_datatable_ajax, name='item_datatable_ajax'),
#     # path('ajax/partners/autocomplete/', views.partner_autocomplete, name='partner_autocomplete'),
#     # path('ajax/items/autocomplete/', views.item_autocomplete, name='item_autocomplete'),
#     # path('ajax/items/<int:item_id>/details/', views.get_item_details, name='item_details'),
#     # path('ajax/check-barcode/', views.check_barcode, name='check_barcode'),
# ]
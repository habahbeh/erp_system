# apps/base_data/urls.py
"""
URLs لوحدة البيانات الأساسية
"""

from django.urls import path
from . import views

app_name = 'base_data'

urlpatterns = [
    # العملاء
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # الموردين
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/add/', views.SupplierCreateView.as_view(), name='supplier_add'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # الأصناف
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/add/', views.ItemCreateView.as_view(), name='item_add'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_edit'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),

    # تصنيفات الأصناف
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # المستودعات
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/add/', views.WarehouseCreateView.as_view(), name='warehouse_add'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # وحدات القياس
    path('units/', views.UnitListView.as_view(), name='unit_list'),
    path('units/add/', views.UnitCreateView.as_view(), name='unit_add'),
    path('units/<int:pk>/edit/', views.UnitUpdateView.as_view(), name='unit_edit'),
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='unit_delete'),
]
# apps/inventory/urls.py
"""
URLs للمخازن
"""

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),

    # Stock In (سندات الإدخال)
    path('stock-in/', views.StockInListView.as_view(), name='stock_in_list'),
    path('stock-in/create/', views.StockInCreateView.as_view(), name='stock_in_create'),
    path('stock-in/<int:pk>/', views.StockInDetailView.as_view(), name='stock_in_detail'),
    path('stock-in/<int:pk>/update/', views.StockInUpdateView.as_view(), name='stock_in_update'),
    path('stock-in/<int:pk>/post/', views.StockInPostView.as_view(), name='stock_in_post'),
    path('stock-in/<int:pk>/unpost/', views.StockInUnpostView.as_view(), name='stock_in_unpost'),

    # Stock Out (سندات الإخراج)
    path('stock-out/', views.StockOutListView.as_view(), name='stock_out_list'),
    path('stock-out/create/', views.StockOutCreateView.as_view(), name='stock_out_create'),
    path('stock-out/<int:pk>/', views.StockOutDetailView.as_view(), name='stock_out_detail'),
    path('stock-out/<int:pk>/update/', views.StockOutUpdateView.as_view(), name='stock_out_update'),
    path('stock-out/<int:pk>/post/', views.StockOutPostView.as_view(), name='stock_out_post'),
    path('stock-out/<int:pk>/unpost/', views.StockOutUnpostView.as_view(), name='stock_out_unpost'),

    # Stock Transfers (التحويلات)
    path('transfers/', views.StockTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.StockTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.StockTransferDetailView.as_view(), name='transfer_detail'),

    # Reports (التقارير)
    path('reports/stock/', views.StockReportView.as_view(), name='stock_report'),
    path('reports/movements/', views.StockMovementReportView.as_view(), name='movement_report'),

    # Stock Count (الجرد)
    path('stock-count/', views.StockCountListView.as_view(), name='count_list'),
    path('stock-count/create/', views.StockCountCreateView.as_view(), name='count_create'),
    path('stock-count/<int:pk>/', views.StockCountDetailView.as_view(), name='count_detail'),
    path('stock-count/<int:pk>/update/', views.StockCountUpdateView.as_view(), name='count_update'),
    path('stock-count/<int:pk>/process/', views.StockCountProcessView.as_view(), name='count_process'),

    # Batches (الدفعات)
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/update/', views.BatchUpdateView.as_view(), name='batch_update'),
    path('reports/batches/expired/', views.BatchExpiredReportView.as_view(), name='batch_expired_report'),
]

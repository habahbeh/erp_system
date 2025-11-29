# apps/inventory/urls.py
"""
URLs للمخازن
"""

from django.urls import path
from . import views
from . import report_views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),

    # Stock In (سندات الإدخال)
    path('stock-in/', views.StockInListView.as_view(), name='stock_in_list'),
    path('stock-in/create/', views.StockInCreateView.as_view(), name='stock_in_create'),
    path('stock-in/<int:pk>/', views.StockInDetailView.as_view(), name='stock_in_detail'),
    path('stock-in/<int:pk>/update/', views.StockInUpdateView.as_view(), name='stock_in_update'),
    path('stock-in/<int:pk>/delete/', views.StockInDeleteView.as_view(), name='stock_in_delete'),
    path('stock-in/<int:pk>/post/', views.StockInPostView.as_view(), name='stock_in_post'),
    path('stock-in/<int:pk>/unpost/', views.StockInUnpostView.as_view(), name='stock_in_unpost'),

    # Stock Out (سندات الإخراج)
    path('stock-out/', views.StockOutListView.as_view(), name='stock_out_list'),
    path('stock-out/create/', views.StockOutCreateView.as_view(), name='stock_out_create'),
    path('stock-out/<int:pk>/', views.StockOutDetailView.as_view(), name='stock_out_detail'),
    path('stock-out/<int:pk>/update/', views.StockOutUpdateView.as_view(), name='stock_out_update'),
    path('stock-out/<int:pk>/delete/', views.StockOutDeleteView.as_view(), name='stock_out_delete'),
    path('stock-out/<int:pk>/post/', views.StockOutPostView.as_view(), name='stock_out_post'),
    path('stock-out/<int:pk>/unpost/', views.StockOutUnpostView.as_view(), name='stock_out_unpost'),

    # Stock Transfers (التحويلات)
    path('transfers/', views.StockTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.StockTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.StockTransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/update/', views.StockTransferUpdateView.as_view(), name='transfer_update'),
    path('transfers/<int:pk>/delete/', views.StockTransferDeleteView.as_view(), name='transfer_delete'),
    path('transfers/<int:pk>/approve/', views.StockTransferApproveView.as_view(), name='transfer_approve'),

    # Reports (التقارير)
    path('reports/stock/', views.StockReportView.as_view(), name='stock_report'),
    path('reports/movements/', views.StockMovementReportView.as_view(), name='movement_report'),

    # Stock Count (الجرد)
    path('stock-count/', views.StockCountListView.as_view(), name='count_list'),
    path('stock-count/create/', views.StockCountCreateView.as_view(), name='count_create'),
    path('stock-count/<int:pk>/', views.StockCountDetailView.as_view(), name='count_detail'),
    path('stock-count/<int:pk>/update/', views.StockCountUpdateView.as_view(), name='count_update'),
    path('stock-count/<int:pk>/delete/', views.StockCountDeleteView.as_view(), name='count_delete'),
    path('stock-count/<int:pk>/start/', views.StockCountStartView.as_view(), name='count_start'),
    path('stock-count/<int:pk>/complete/', views.StockCountCompleteView.as_view(), name='count_complete'),
    path('stock-count/<int:pk>/approve/', views.StockCountApproveView.as_view(), name='count_approve'),
    path('stock-count/<int:pk>/cancel/', views.StockCountCancelView.as_view(), name='count_cancel'),
    path('stock-count/<int:pk>/process/', views.StockCountProcessView.as_view(), name='count_process'),

    # Batches (الدفعات)
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/update/', views.BatchUpdateView.as_view(), name='batch_update'),
    path('batches/<int:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),
    path('reports/batches/expired/', views.BatchExpiredReportView.as_view(), name='batch_expired_report'),

    # Alerts (التنبيهات)
    path('alerts/', views.InventoryAlertsView.as_view(), name='alerts_list'),
    path('api/alerts/', views.InventoryAlertsAPIView.as_view(), name='alerts_api'),

    # Reservations (الحجوزات)
    path('reservations/', views.StockReservationListView.as_view(), name='reservation_list'),
    path('reservations/<int:pk>/release/', views.release_reservation_view, name='reservation_release'),

    # AJAX Endpoints
    path('ajax/get-item-stock/', views.ajax_get_item_stock, name='ajax_get_item_stock'),
    path('ajax/get-batches/', views.ajax_get_batches, name='ajax_get_batches'),
    path('ajax/check-availability/', views.ajax_check_availability, name='ajax_check_availability'),
    path('ajax/item-search/', views.ajax_item_search, name='ajax_item_search'),

    # ==================== التقارير الشاملة ====================
    path('reports/', report_views.reports_list, name='reports_list'),
    path('reports/stock-status/', report_views.stock_status_report, name='report_stock_status'),
    path('reports/stock-movement/', report_views.stock_movement_report, name='report_stock_movement'),
    path('reports/stock-valuation/', report_views.stock_valuation_report, name='report_stock_valuation'),
    path('reports/low-stock/', report_views.low_stock_report, name='report_low_stock'),
    path('reports/batch-expiry/', report_views.batch_expiry_report, name='report_batch_expiry'),
]

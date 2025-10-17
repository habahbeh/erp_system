# apps/assets/urls.py
"""
URLs تطبيق الأصول الثابتة
"""

from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════
    # لوحة التحكم
    # ═══════════════════════════════════════════════════════════
    path('', views.AssetsDashboardView.as_view(), name='dashboard'),

    # ═══════════════════════════════════════════════════════════
    # الأصول الثابتة
    # ═══════════════════════════════════════════════════════════
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/update/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('assets/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),

    # Ajax
    path('assets/datatable-ajax/', views.asset_datatable_ajax, name='asset_datatable_ajax'),

    # ═══════════════════════════════════════════════════════════
    # فئات الأصول
    # ═══════════════════════════════════════════════════════════
    path('categories/', views.AssetCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.AssetCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.AssetCategoryUpdateView.as_view(), name='category_update'),

    # Ajax
    path('categories/datatable-ajax/', views.asset_category_datatable_ajax, name='category_datatable_ajax'),

    # ═══════════════════════════════════════════════════════════
    # العمليات على الأصول
    # ═══════════════════════════════════════════════════════════
    path('transactions/', views.AssetTransactionListView.as_view(), name='transaction_list'),
    path('transactions/purchase/', views.AssetPurchaseView.as_view(), name='asset_purchase'),
    path('transactions/sale/', views.AssetSaleView.as_view(), name='asset_sale'),
    path('transactions/disposal/', views.AssetDisposalView.as_view(), name='asset_disposal'),

    # Ajax
    path('transactions/datatable-ajax/', views.asset_transaction_datatable_ajax, name='transaction_datatable_ajax'),

    # ═══════════════════════════════════════════════════════════
    # التحويلات
    # ═══════════════════════════════════════════════════════════
    path('transfers/', views.AssetTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.AssetTransferCreateView.as_view(), name='transfer_create'),

    # ═══════════════════════════════════════════════════════════
    # الصيانة
    # ═══════════════════════════════════════════════════════════
    # جدولة الصيانة
    path('maintenance/schedules/', views.MaintenanceScheduleListView.as_view(), name='maintenance_schedule_list'),
    path('maintenance/schedules/create/', views.MaintenanceScheduleCreateView.as_view(),
         name='maintenance_schedule_create'),
    path('maintenance/schedules/<int:pk>/update/', views.MaintenanceScheduleUpdateView.as_view(),
         name='maintenance_schedule_update'),

    # سجل الصيانة
    path('maintenance/', views.AssetMaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', views.AssetMaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/', views.AssetMaintenanceDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/<int:pk>/update/', views.AssetMaintenanceUpdateView.as_view(), name='maintenance_update'),

    # Ajax
    path('maintenance/datatable-ajax/', views.maintenance_datatable_ajax, name='maintenance_datatable_ajax'),

    # ═══════════════════════════════════════════════════════════
    # الإهلاك
    # ═══════════════════════════════════════════════════════════
    path('depreciation/calculate/', views.DepreciationCalculationView.as_view(), name='depreciation_calculate'),
    path('depreciation/history/', views.DepreciationHistoryView.as_view(), name='depreciation_history'),

    # Ajax
    path('depreciation/history-ajax/', views.depreciation_history_ajax, name='depreciation_history_ajax'),

    # ═══════════════════════════════════════════════════════════
    # التقارير
    # ═══════════════════════════════════════════════════════════

    # صفحة قائمة التقارير الرئيسية
    path('reports/', views.ReportsListView.as_view(), name='reports_list'),

    # تقرير سجل الأصول
    path('reports/asset-register/', views.AssetRegisterReportView.as_view(), name='report_asset_register'),

    # تقرير الإهلاك
    path('reports/depreciation/', views.DepreciationReportView.as_view(), name='report_depreciation'),

    # تقرير الصيانة
    path('reports/maintenance/', views.MaintenanceReportView.as_view(), name='report_maintenance'),

    # تقرير حركة الأصول
    path('reports/movement/', views.AssetMovementReportView.as_view(), name='report_movement'),

    # تقرير الأصول حسب مركز التكلفة
    path('reports/by-cost-center/', views.AssetByCostCenterReportView.as_view(), name='report_by_cost_center'),

    # تقرير الأصول القريبة من نهاية العمر
    path('reports/near-end-of-life/', views.AssetNearEndOfLifeReportView.as_view(), name='report_near_end_of_life'),

    # تقرير القيمة العادلة
    path('reports/fair-value/', views.FairValueReportView.as_view(), name='report_fair_value'),
]
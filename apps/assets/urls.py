from django.urls import path
from .views import *

app_name = 'assets'

urlpatterns = [
    # ==================== Dashboard ====================
    path('', AssetDashboardView.as_view(), name='dashboard'),
    path('ajax/dashboard-stats/', dashboard_stats_ajax, name='dashboard_stats_ajax'),
    path('ajax/depreciation-chart/', depreciation_chart_ajax, name='depreciation_chart_ajax'),
    path('ajax/maintenance-chart/', maintenance_chart_ajax, name='maintenance_chart_ajax'),
    path('ajax/asset-status-chart/', asset_status_chart_ajax, name='asset_status_chart_ajax'),

    # ==================== Categories ====================
    path('categories/', AssetCategoryListView.as_view(), name='category_list'),
    path('categories/create/', AssetCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', AssetCategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/update/', AssetCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', AssetCategoryDeleteView.as_view(), name='category_delete'),
    path('ajax/categories/datatable/', asset_category_datatable_ajax, name='category_datatable_ajax'),
    path('ajax/categories/tree/', category_tree_ajax, name='category_tree_ajax'),


    path('depreciation-methods/', DepreciationMethodListView.as_view(), name='depreciation_method_list'),
    path('depreciation-methods/create/', DepreciationMethodCreateView.as_view(), name='depreciation_method_create'),
    path('depreciation-methods/<int:pk>/update/', DepreciationMethodUpdateView.as_view(), name='depreciation_method_update'),
    path('depreciation-methods/<int:pk>/delete/', DepreciationMethodDeleteView.as_view(), name='depreciation_method_delete'),

    path('conditions/', AssetConditionListView.as_view(), name='condition_list'),
    path('conditions/create/', AssetConditionCreateView.as_view(), name='condition_create'),
    path('conditions/<int:pk>/update/', AssetConditionUpdateView.as_view(), name='condition_update'),
    path('conditions/<int:pk>/delete/', AssetConditionDeleteView.as_view(), name='condition_delete'),

    # ==================== Assets ====================
    path('assets/', AssetListView.as_view(), name='asset_list'),
    path('assets/create/', AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/update/', AssetUpdateView.as_view(), name='asset_update'),
    path('assets/<int:pk>/delete/', AssetDeleteView.as_view(), name='asset_delete'),
    path('ajax/assets/datatable/', asset_datatable_ajax, name='asset_datatable_ajax'),
    path('ajax/assets/autocomplete/', asset_autocomplete, name='asset_autocomplete'),
    path('ajax/assets/generate-number/', generate_asset_number, name='generate_asset_number'),
    path('assets/<int:pk>/barcode-pdf/', asset_barcode_pdf, name='asset_barcode_pdf'),
    path('assets/<int:pk>/qr-code/', asset_qr_code, name='asset_qr_code'),

    # Attachments
    path('assets/<int:pk>/upload-attachment/', upload_attachment, name='upload_attachment'),
    path('attachments/<int:pk>/delete/', delete_attachment, name='delete_attachment'),

    # Bulk Operations
    path('assets/bulk-import/', bulk_import_assets, name='bulk_import_assets'),
    path('assets/download-template/', download_import_template, name='download_import_template'),
    path('assets/bulk-update-status/', bulk_update_status, name='bulk_update_status'),
    path('assets/bulk-update-location/', bulk_update_location, name='bulk_update_location'),

    # ==================== Depreciation ====================
    path('depreciation/', AssetDepreciationListView.as_view(), name='depreciation_list'),
    path('depreciation/<int:pk>/', AssetDepreciationDetailView.as_view(), name='depreciation_detail'),
    path('depreciation/calculate/', CalculateDepreciationView.as_view(), name='calculate_depreciation'),
    path('depreciation/bulk-calculate/', BulkDepreciationCalculationView.as_view(), name='bulk_calculate_depreciation'),
    path('ajax/depreciation/datatable/', depreciation_datatable_ajax, name='depreciation_datatable_ajax'),
    path('ajax/depreciation/schedule/', depreciation_schedule_ajax, name='depreciation_schedule_ajax'),
    path('ajax/depreciation/<int:pk>/calculate/', calculate_single_depreciation_ajax,
         name='calculate_single_depreciation_ajax'),

    # ==================== Transactions ====================
    path('transactions/', AssetTransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', AssetTransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', AssetTransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/update/', AssetTransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', AssetTransactionDeleteView.as_view(), name='transaction_delete'),
    path('ajax/transactions/datatable/', transaction_datatable_ajax, name='transaction_datatable_ajax'),
    path('transactions/<int:pk>/post/', PostTransactionView.as_view(), name='post_transaction'),

    # Specific Transactions
    path('transactions/sell/', SellAssetView.as_view(), name='sell_asset'),
    path('transactions/dispose/', DisposeAssetView.as_view(), name='dispose_asset'),
    path('transactions/revalue/', RevalueAssetView.as_view(), name='revalue_asset'),

    # ==================== Transfers ====================
    path('transfers/', AssetTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', AssetTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', AssetTransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/update/', AssetTransferUpdateView.as_view(), name='transfer_update'),
    path('ajax/transfers/datatable/', transfer_datatable_ajax, name='transfer_datatable_ajax'),
    path('ajax/transfers/<int:pk>/approve/', approve_transfer, name='approve_transfer'),
    path('ajax/transfers/<int:pk>/reject/', reject_transfer, name='reject_transfer'),
    path('ajax/transfers/<int:pk>/complete/', complete_transfer, name='complete_transfer'),

    # ==================== Maintenance ====================
    path('maintenance/types/', MaintenanceTypeListView.as_view(), name='maintenance_type_list'),
    path('maintenance/types/create/', MaintenanceTypeCreateView.as_view(), name='maintenance_type_create'),
    path('maintenance/types/<int:pk>/update/', MaintenanceTypeUpdateView.as_view(), name='maintenance_type_update'),
    path('maintenance/types/<int:pk>/delete/', MaintenanceTypeDeleteView.as_view(), name='maintenance_type_delete'),

    path('maintenance/schedules/', MaintenanceScheduleListView.as_view(), name='schedule_list'),
    path('maintenance/schedules/create/', MaintenanceScheduleCreateView.as_view(), name='schedule_create'),
    path('maintenance/schedules/<int:pk>/', MaintenanceScheduleDetailView.as_view(), name='schedule_detail'),
    path('maintenance/schedules/<int:pk>/update/', MaintenanceScheduleUpdateView.as_view(), name='schedule_update'),
    path('maintenance/schedules/<int:pk>/delete/', MaintenanceScheduleDeleteView.as_view(), name='schedule_delete'),
    path('ajax/schedules/datatable/', schedule_datatable_ajax, name='schedule_datatable_ajax'),
    path('ajax/schedules/generate-dates/', generate_schedule_dates, name='generate_schedule_dates'),

    path('maintenance/', AssetMaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', AssetMaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/', AssetMaintenanceDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/<int:pk>/update/', AssetMaintenanceUpdateView.as_view(), name='maintenance_update'),
    path('ajax/maintenance/datatable/', maintenance_datatable_ajax, name='maintenance_datatable_ajax'),
    path('ajax/maintenance/<int:pk>/complete/', complete_maintenance, name='complete_maintenance'),

    # ==================== Physical Count ====================
    path('physical-count/cycles/', PhysicalCountCycleListView.as_view(), name='cycle_list'),
    path('physical-count/cycles/create/', PhysicalCountCycleCreateView.as_view(), name='cycle_create'),
    path('physical-count/cycles/<int:pk>/', PhysicalCountCycleDetailView.as_view(), name='cycle_detail'),
    path('physical-count/cycles/<int:pk>/update/', PhysicalCountCycleUpdateView.as_view(), name='cycle_update'),
    path('ajax/cycles/datatable/', cycle_datatable_ajax, name='cycle_datatable_ajax'),
    path('ajax/cycles/<int:pk>/start/', StartCycleView.as_view(), name='start_cycle'),
    path('ajax/cycles/<int:pk>/complete/', CompleteCycleView.as_view(), name='complete_cycle'),

    path('physical-count/', PhysicalCountListView.as_view(), name='count_list'),
    path('physical-count/create/', PhysicalCountCreateView.as_view(), name='count_create'),
    path('physical-count/<int:pk>/', PhysicalCountDetailView.as_view(), name='count_detail'),
    path('physical-count/<int:pk>/update/', PhysicalCountUpdateView.as_view(), name='count_update'),
    path('ajax/counts/datatable/', count_datatable_ajax, name='count_datatable_ajax'),
    path('ajax/counts/<int:pk>/approve/', approve_physical_count, name='approve_physical_count'),

    path('ajax/count-lines/<int:pk>/', count_line_ajax, name='count_line_ajax'),
    path('ajax/barcode-scan/', barcode_scan_ajax, name='barcode_scan_ajax'),
    path('ajax/upload-count-photo/', upload_count_photo, name='upload_count_photo'),

    path('physical-count/adjustments/', PhysicalCountAdjustmentListView.as_view(), name='adjustment_list'),
    path('physical-count/adjustments/create/', PhysicalCountAdjustmentCreateView.as_view(), name='adjustment_create'),
    path('physical-count/adjustments/<int:pk>/', PhysicalCountAdjustmentDetailView.as_view(), name='adjustment_detail'),
    path('ajax/adjustments/datatable/', adjustment_datatable_ajax, name='adjustment_datatable_ajax'),
    path('ajax/adjustments/<int:pk>/post/', post_adjustment, name='post_adjustment'),

    # ==================== Insurance ====================
    path('insurance/companies/', InsuranceCompanyListView.as_view(), name='insurance_company_list'),
    path('insurance/companies/create/', InsuranceCompanyCreateView.as_view(), name='insurance_company_create'),
    path('insurance/companies/<int:pk>/update/', InsuranceCompanyUpdateView.as_view(), name='insurance_company_update'),
    path('insurance/companies/<int:pk>/delete/', InsuranceCompanyDeleteView.as_view(), name='insurance_company_delete'),

    path('insurance/', AssetInsuranceListView.as_view(), name='insurance_list'),
    path('insurance/create/', AssetInsuranceCreateView.as_view(), name='insurance_create'),
    path('insurance/<int:pk>/', AssetInsuranceDetailView.as_view(), name='insurance_detail'),
    path('insurance/<int:pk>/update/', AssetInsuranceUpdateView.as_view(), name='insurance_update'),
    path('ajax/insurance/datatable/', insurance_datatable_ajax, name='insurance_datatable_ajax'),
    path('ajax/insurance/expiring/', insurance_expiring_ajax, name='insurance_expiring_ajax'),

    path('insurance/claims/', InsuranceClaimListView.as_view(), name='claim_list'),
    path('insurance/claims/create/', InsuranceClaimCreateView.as_view(), name='claim_create'),
    path('insurance/claims/<int:pk>/', InsuranceClaimDetailView.as_view(), name='claim_detail'),
    path('insurance/claims/<int:pk>/update/', InsuranceClaimUpdateView.as_view(), name='claim_update'),
    path('ajax/claims/datatable/', claim_datatable_ajax, name='claim_datatable_ajax'),
    path('ajax/claims/<int:pk>/approve/', approve_insurance_claim, name='approve_insurance_claim'),
    path('ajax/claims/<int:pk>/pay/', process_claim_payment, name='process_claim_payment'),

    # ==================== Lease ====================
    path('leases/', AssetLeaseListView.as_view(), name='lease_list'),
    path('leases/create/', AssetLeaseCreateView.as_view(), name='lease_create'),
    path('leases/<int:pk>/', AssetLeaseDetailView.as_view(), name='lease_detail'),
    path('leases/<int:pk>/update/', AssetLeaseUpdateView.as_view(), name='lease_update'),
    path('leases/<int:pk>/terminate/', TerminateLeaseView.as_view(), name='terminate_lease'),
    path('leases/<int:pk>/renew/', RenewLeaseView.as_view(), name='renew_lease'),
    path('leases/<int:pk>/exercise-purchase/', ExercisePurchaseOptionView.as_view(), name='exercise_purchase'),
    path('ajax/leases/datatable/', lease_datatable_ajax, name='lease_datatable_ajax'),

    path('lease-payments/', LeasePaymentListView.as_view(), name='payment_list'),
    path('lease-payments/create/', LeasePaymentCreateView.as_view(), name='payment_create'),
    path('ajax/payments/datatable/', payment_datatable_ajax, name='payment_datatable_ajax'),
    path('ajax/payments/<int:pk>/process/', process_lease_payment, name='process_lease_payment'),

    # ==================== Workflow ====================
    path('workflows/', ApprovalWorkflowListView.as_view(), name='workflow_list'),
    path('workflows/create/', ApprovalWorkflowCreateView.as_view(), name='workflow_create'),
    path('workflows/<int:pk>/', ApprovalWorkflowDetailView.as_view(), name='workflow_detail'),
    path('workflows/<int:pk>/update/', ApprovalWorkflowUpdateView.as_view(), name='workflow_update'),
    path('workflows/<int:pk>/delete/', ApprovalWorkflowDeleteView.as_view(), name='workflow_delete'),

    path('workflows/levels/create/', ApprovalLevelCreateView.as_view(), name='level_create'),
    path('workflows/levels/<int:pk>/update/', ApprovalLevelUpdateView.as_view(), name='level_update'),
    path('workflows/levels/<int:pk>/delete/', ApprovalLevelDeleteView.as_view(), name='level_delete'),

    path('approval-requests/', ApprovalRequestListView.as_view(), name='request_list'),
    path('approval-requests/<int:pk>/', ApprovalRequestDetailView.as_view(), name='request_detail'),
    path('ajax/requests/datatable/', request_datatable_ajax, name='request_datatable_ajax'),
    path('ajax/requests/<int:pk>/approve/', approve_request, name='approve_request'),
    path('ajax/requests/<int:pk>/reject/', reject_request, name='reject_request'),
    path('ajax/requests/my-pending/', my_pending_approvals_ajax, name='my_pending_approvals_ajax'),

    # ==================== Notifications ====================
    path('notifications/', notifications_dashboard, name='notifications_dashboard'),
    path('notifications/maintenance/overdue/', overdue_maintenance_list, name='overdue_maintenance_list'),
    path('notifications/maintenance/upcoming/', upcoming_maintenance_list, name='upcoming_maintenance_list'),
    path('notifications/insurance/expiring/', expiring_insurance_list, name='expiring_insurance_list'),
    path('notifications/lease/overdue/', overdue_lease_payments_list, name='overdue_lease_payments_list'),
    path('ajax/notifications/count/', notification_count_ajax, name='notification_count_ajax'),
    path('ajax/notifications/details/', notification_details_ajax, name='notification_details_ajax'),

    # ==================== Reports ====================
    path('reports/', reports_dashboard, name='reports'),
    path('reports/asset-register/', asset_register_report, name='asset_register_report'),
    path('reports/depreciation/', depreciation_report, name='depreciation_report'),
    path('reports/maintenance/', maintenance_report, name='maintenance_report'),
    path('reports/movement/', asset_movement_report, name='asset_movement_report'),
    path('reports/valuation/', valuation_report, name='valuation_report'),
    path('reports/physical-count/', physical_count_report, name='physical_count_report'),
    path('reports/export/asset-register/', export_asset_register_excel, name='export_asset_register_excel'),
    path('reports/export/depreciation/', export_depreciation_excel, name='export_depreciation_excel'),

    # ==================== API ====================
    path('api/assets/search/', asset_search_api, name='asset_search_api'),
    path('api/assets/<int:pk>/', asset_details_api, name='asset_details_api'),
    path('api/categories/<int:pk>/assets/', category_assets_api, name='category_assets_api'),
    path('api/stats/', asset_stats_api, name='asset_stats_api'),
    path('api/depreciation/<int:pk>/schedule/', depreciation_schedule_api, name='depreciation_schedule_api'),
    path('api/maintenance/alerts/', maintenance_alerts_api, name='maintenance_alerts_api'),
    path('api/insurance/alerts/', insurance_alerts_api, name='insurance_alerts_api'),
    path('api/barcode-scan/', barcode_scan_api, name='barcode_scan_api'),
    path('api/conditions/', asset_condition_list_api, name='asset_condition_list_api'),
    path('api/depreciation-methods/', depreciation_method_list_api, name='depreciation_method_list_api'),
    path('api/categories/', category_list_api, name='category_list_api'),
    path('api/validate-asset-number/', validate_asset_number_api, name='validate_asset_number_api'),
    path('api/assets/<int:pk>/qr-code/', asset_qr_code_api, name='asset_qr_code_api'),



]
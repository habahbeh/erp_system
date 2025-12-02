# apps/purchases/urls.py
"""
URL Configuration for Purchases App
"""

from django.urls import path
from .views import *
from .views.dashboard import PurchaseDashboardView, dashboard_stats_api, monthly_chart_api, top_suppliers_api
from .views.quotation_views import (
    get_purchase_request_items_ajax,
    rfq_get_item_stock_multi_branch_ajax,
    rfq_get_item_stock_current_branch_ajax,
    rfq_item_search_ajax,
    quotation_get_item_stock_multi_branch_ajax,
    quotation_get_item_stock_current_branch_ajax,
    quotation_item_search_ajax,
    create_rfq_from_purchase_request
)
from .views.invoice_views import (
    get_supplier_item_price_ajax as invoice_get_supplier_price,
    get_item_stock_multi_branch_ajax as invoice_get_stock_multi_branch,
    get_item_stock_current_branch_ajax as invoice_get_stock_current,
    item_search_ajax as invoice_item_search,
    save_invoice_draft_ajax,
    get_item_uom_conversions_ajax,
    get_item_all_prices_ajax,
    copy_invoice_as_draft
)
from .views.ajax_views import ajax_get_item_price_by_uom
from .views.order_views import (
    get_supplier_item_price_ajax as order_get_supplier_price,
    get_item_stock_multi_branch_ajax as order_get_stock_multi_branch,
    get_item_stock_current_branch_ajax as order_get_stock_current,
    item_search_ajax as order_item_search,
    save_order_draft_ajax
)
from .views.goods_receipt_views import (
    get_purchase_order_item_price_ajax as receipt_get_order_price,
    get_item_stock_multi_branch_ajax as receipt_get_stock_multi_branch,
    get_item_stock_current_branch_ajax as receipt_get_stock_current,
    item_search_ajax as receipt_item_search,
    save_receipt_draft_ajax,
    get_purchase_order_lines_ajax as receipt_get_order_lines
)
from .views.request_views import (
    get_item_stock_multi_branch_ajax as request_get_stock_multi_branch,
    get_item_stock_current_branch_ajax as request_get_stock_current,
    item_search_ajax as request_item_search,
    save_request_draft_ajax,
    get_employee_department_ajax
)
from .views.contract_views import (
    contract_get_item_stock_multi_branch_ajax,
    contract_get_item_stock_current_branch_ajax,
    contract_item_search_ajax,
    contract_add_supplier_ajax
)
from .views.report_views import (
    reports_list, purchases_summary_report, supplier_performance_report,
    purchase_orders_report, items_purchases_report, contracts_report,
    export_purchases_summary_excel, export_purchases_summary_pdf,
    export_supplier_performance_excel, export_supplier_performance_pdf,
    export_purchase_orders_excel, export_purchase_orders_pdf,
    export_items_purchases_excel, export_items_purchases_pdf,
    export_contracts_excel, export_contracts_pdf
)

app_name = 'purchases'

urlpatterns = [
    # ==================== Dashboard ====================
    path('dashboard/', PurchaseDashboardView.as_view(), name='dashboard'),
    path('api/dashboard/stats/', dashboard_stats_api, name='dashboard_stats_api'),
    path('api/dashboard/monthly-chart/', monthly_chart_api, name='monthly_chart_api'),
    path('api/dashboard/top-suppliers/', top_suppliers_api, name='top_suppliers_api'),


    # ==================== Purchase Invoices ====================
    path('invoices/', PurchaseInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', PurchaseInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', PurchaseInvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', PurchaseInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', PurchaseInvoiceDeleteView.as_view(), name='invoice_delete'),

    # Invoice Actions
    path('invoices/<int:pk>/post/', post_invoice, name='post_invoice'),
    path('invoices/<int:pk>/unpost/', unpost_invoice, name='unpost_invoice'),
    path('invoices/<int:pk>/copy-as-draft/', copy_invoice_as_draft, name='copy_invoice_as_draft'),

    # Invoice AJAX & Export
    path('ajax/invoices/datatable/', invoice_datatable_ajax, name='invoice_datatable_ajax'),
    path('ajax/invoices/get-supplier-price/', invoice_get_supplier_price, name='get_supplier_item_price_ajax'),
    path('ajax/invoices/get-stock-multi-branch/', invoice_get_stock_multi_branch, name='get_item_stock_multi_branch_ajax'),
    path('ajax/invoices/get-stock-current/', invoice_get_stock_current, name='get_item_stock_current_branch_ajax'),
    path('ajax/invoices/item-search/', invoice_item_search, name='item_search_ajax'),
    path('ajax/invoices/get-price-by-uom/', ajax_get_item_price_by_uom, name='ajax_get_item_price_by_uom'),
    path('ajax/invoices/save-draft/', save_invoice_draft_ajax, name='save_invoice_draft_ajax'),
    path('ajax/invoices/uom-conversions/', get_item_uom_conversions_ajax, name='get_item_uom_conversions_ajax'),
    path('ajax/invoices/item-all-prices/', get_item_all_prices_ajax, name='get_item_all_prices_ajax'),
    path('invoices/export/', export_invoices_excel, name='export_invoices_excel'),

    # ==================== Purchase Orders ====================
    path('orders/', PurchaseOrderListView.as_view(), name='order_list'),
    path('orders/create/', PurchaseOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update/', PurchaseOrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='order_delete'),

    # Order Workflow Actions
    path('orders/<int:pk>/submit/', submit_for_approval, name='submit_for_approval'),
    path('orders/<int:pk>/approve/', approve_order, name='approve_order'),
    path('orders/<int:pk>/reject/', reject_order, name='reject_order'),
    path('orders/<int:pk>/send/', send_to_supplier, name='send_to_supplier'),
    path('orders/<int:pk>/cancel/', cancel_order, name='cancel_order'),
    path('orders/<int:pk>/convert-to-invoice/', convert_to_invoice, name='convert_to_invoice'),

    # Order AJAX & Export
    path('ajax/orders/datatable/', order_datatable_ajax, name='order_datatable_ajax'),
    path('ajax/orders/get-supplier-price/', order_get_supplier_price, name='order_get_supplier_item_price_ajax'),
    path('ajax/orders/get-stock-multi-branch/', order_get_stock_multi_branch, name='order_get_item_stock_multi_branch_ajax'),
    path('ajax/orders/get-stock-current/', order_get_stock_current, name='order_get_item_stock_current_branch_ajax'),
    path('ajax/orders/item-search/', order_item_search, name='order_item_search_ajax'),
    path('ajax/orders/save-draft/', save_order_draft_ajax, name='save_order_draft_ajax'),
    path('orders/export/', export_orders_excel, name='export_orders_excel'),

    # ==================== Goods Receipts ====================
    path('goods-receipts/', GoodsReceiptListView.as_view(), name='goods_receipt_list'),
    path('goods-receipts/create/', GoodsReceiptCreateView.as_view(), name='goods_receipt_create'),
    path('goods-receipts/<int:pk>/', GoodsReceiptDetailView.as_view(), name='goods_receipt_detail'),
    path('goods-receipts/<int:pk>/update/', GoodsReceiptUpdateView.as_view(), name='goods_receipt_update'),
    path('goods-receipts/<int:pk>/delete/', GoodsReceiptDeleteView.as_view(), name='goods_receipt_delete'),

    # Goods Receipt Actions
    path('goods-receipts/<int:pk>/confirm/', confirm_goods_receipt, name='confirm_goods_receipt'),
    path('goods-receipts/<int:pk>/post/', post_goods_receipt, name='post_goods_receipt'),
    path('goods-receipts/<int:pk>/unpost/', unpost_goods_receipt, name='unpost_goods_receipt'),

    # Goods Receipt AJAX & Export
    path('ajax/goods-receipts/datatable/', goods_receipt_datatable_ajax, name='goods_receipt_datatable_ajax'),
    path('ajax/goods-receipts/get-order-price/', receipt_get_order_price, name='receipt_get_purchase_order_item_price_ajax'),
    path('ajax/goods-receipts/get-order-lines/', receipt_get_order_lines, name='receipt_get_purchase_order_lines_ajax'),
    path('ajax/goods-receipts/get-stock-multi-branch/', receipt_get_stock_multi_branch, name='receipt_get_item_stock_multi_branch_ajax'),
    path('ajax/goods-receipts/get-stock-current/', receipt_get_stock_current, name='receipt_get_item_stock_current_branch_ajax'),
    path('ajax/goods-receipts/item-search/', receipt_item_search, name='receipt_item_search_ajax'),
    path('ajax/goods-receipts/save-draft/', save_receipt_draft_ajax, name='save_receipt_draft_ajax'),
    path('goods-receipts/export/', export_goods_receipts_excel, name='export_goods_receipts_excel'),

    # ==================== Purchase Requests ====================
    path('requests/', PurchaseRequestListView.as_view(), name='request_list'),
    path('requests/create/', PurchaseRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', PurchaseRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/update/', PurchaseRequestUpdateView.as_view(), name='request_update'),
    path('requests/<int:pk>/delete/', PurchaseRequestDeleteView.as_view(), name='request_delete'),

    # Request Workflow Actions
    path('requests/<int:pk>/submit/', submit_request, name='submit_request'),
    path('requests/<int:pk>/approve/', approve_request, name='approve_request'),
    path('requests/<int:pk>/reject/', reject_request, name='reject_request'),
    path('requests/<int:pk>/create-order/', create_order_from_request, name='create_order_from_request'),

    # Request AJAX & Export
    path('ajax/requests/datatable/', request_datatable_ajax, name='request_datatable_ajax'),
    path('ajax/requests/get-stock-multi-branch/', request_get_stock_multi_branch, name='request_get_item_stock_multi_branch_ajax'),
    path('ajax/requests/get-stock-current/', request_get_stock_current, name='request_get_item_stock_current_branch_ajax'),
    path('ajax/requests/item-search/', request_item_search, name='request_item_search_ajax'),
    path('ajax/requests/save-draft/', save_request_draft_ajax, name='save_request_draft_ajax'),
    path('ajax/requests/get-employee-department/', get_employee_department_ajax, name='get_employee_department_ajax'),
    path('requests/export/', export_requests_excel, name='export_requests_excel'),

    # ==================== Quotation Requests (RFQ) ====================
    path('rfqs/', PurchaseQuotationRequestListView.as_view(), name='rfq_list'),
    path('rfqs/create/', PurchaseQuotationRequestCreateView.as_view(), name='rfq_create'),
    path('rfqs/create-from-request/<int:request_id>/', create_rfq_from_purchase_request, name='create_rfq_from_request'),
    path('rfqs/<int:pk>/', PurchaseQuotationRequestDetailView.as_view(), name='rfq_detail'),
    path('rfqs/<int:pk>/update/', PurchaseQuotationRequestUpdateView.as_view(), name='rfq_update'),
    path('rfqs/<int:pk>/delete/', PurchaseQuotationRequestDeleteView.as_view(), name='rfq_delete'),

    # RFQ Actions
    path('rfqs/<int:pk>/send/', send_rfq_to_suppliers, name='send_rfq_to_suppliers'),
    path('rfqs/<int:pk>/cancel/', cancel_rfq, name='cancel_rfq'),
    path('rfqs/<int:pk>/evaluate/', mark_rfq_as_evaluating, name='mark_rfq_as_evaluating'),

    # RFQ AJAX & Export
    path('ajax/rfqs/datatable/', rfq_datatable_ajax, name='rfq_datatable_ajax'),
    path('ajax/rfqs/get-purchase-request-items/<int:request_id>/', get_purchase_request_items_ajax, name='get_purchase_request_items_ajax'),
    path('ajax/rfqs/get-stock-multi-branch/', rfq_get_item_stock_multi_branch_ajax, name='rfq_get_item_stock_multi_branch_ajax'),
    path('ajax/rfqs/get-stock-current/', rfq_get_item_stock_current_branch_ajax, name='rfq_get_item_stock_current_branch_ajax'),
    path('ajax/rfqs/item-search/', rfq_item_search_ajax, name='rfq_item_search_ajax'),
    path('rfqs/export/', export_rfqs_excel, name='export_rfqs_excel'),

    # ==================== Quotations ====================
    path('quotations/', PurchaseQuotationListView.as_view(), name='quotation_list'),
    path('quotations/create/', PurchaseQuotationCreateView.as_view(), name='quotation_create'),
    path('quotations/<int:pk>/', PurchaseQuotationDetailView.as_view(), name='quotation_detail'),
    path('quotations/<int:pk>/update/', PurchaseQuotationUpdateView.as_view(), name='quotation_update'),
    path('quotations/<int:pk>/delete/', PurchaseQuotationDeleteView.as_view(), name='quotation_delete'),

    # Quotation Actions
    path('quotations/<int:pk>/evaluate/', evaluate_quotation, name='evaluate_quotation'),
    path('quotations/<int:pk>/award/', award_quotation, name='award_quotation'),
    path('quotations/<int:pk>/reject/', reject_quotation, name='reject_quotation'),
    path('quotations/<int:pk>/convert-to-order/', convert_quotation_to_order, name='convert_quotation_to_order'),

    # Quotation AJAX & Export
    path('ajax/quotations/datatable/', quotation_datatable_ajax, name='quotation_datatable_ajax'),
    path('ajax/quotations/get-stock-multi-branch/', quotation_get_item_stock_multi_branch_ajax, name='quotation_get_item_stock_multi_branch_ajax'),
    path('ajax/quotations/get-stock-current/', quotation_get_item_stock_current_branch_ajax, name='quotation_get_item_stock_current_branch_ajax'),
    path('ajax/quotations/item-search/', quotation_item_search_ajax, name='quotation_item_search_ajax'),
    path('quotations/export/', export_quotations_excel, name='export_quotations_excel'),

    # ==================== Purchase Contracts ====================
    path('contracts/', PurchaseContractListView.as_view(), name='contract_list'),
    path('contracts/create/', PurchaseContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/', PurchaseContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/update/', PurchaseContractUpdateView.as_view(), name='contract_update'),
    path('contracts/<int:pk>/delete/', PurchaseContractDeleteView.as_view(), name='contract_delete'),

    # Contract Workflow Actions
    path('contracts/<int:pk>/approve/', contract_approve, name='contract_approve'),
    path('contracts/<int:pk>/change-status/', contract_change_status, name='contract_change_status'),
    path('contracts/check-expiry/', contract_check_expiry, name='contract_check_expiry'),
    path('contracts/<int:pk>/copy/', contract_copy_or_renew, name='contract_copy_or_renew'),

    # Contract AJAX
    path('ajax/contracts/get-stock-multi-branch/', contract_get_item_stock_multi_branch_ajax, name='contract_get_item_stock_multi_branch_ajax'),
    path('ajax/contracts/get-stock-current/', contract_get_item_stock_current_branch_ajax, name='contract_get_item_stock_current_branch_ajax'),
    path('ajax/contracts/item-search/', contract_item_search_ajax, name='contract_item_search_ajax'),
    path('ajax/contracts/add-supplier/', contract_add_supplier_ajax, name='contract_add_supplier_ajax'),

    # ==================== Reports ====================
    path('reports/', reports_list, name='reports_list'),
    path('reports/purchases-summary/', purchases_summary_report, name='purchases_summary_report'),
    path('reports/supplier-performance/', supplier_performance_report, name='supplier_performance_report'),
    path('reports/purchase-orders/', purchase_orders_report, name='purchase_orders_report'),
    path('reports/items-purchases/', items_purchases_report, name='items_purchases_report'),
    path('reports/contracts/', contracts_report, name='contracts_report'),

    # Report Exports
    path('reports/purchases-summary/export/excel/', export_purchases_summary_excel, name='export_purchases_summary_excel'),
    path('reports/purchases-summary/export/pdf/', export_purchases_summary_pdf, name='export_purchases_summary_pdf'),
    path('reports/supplier-performance/export/excel/', export_supplier_performance_excel, name='export_supplier_performance_excel'),
    path('reports/supplier-performance/export/pdf/', export_supplier_performance_pdf, name='export_supplier_performance_pdf'),
    path('reports/purchase-orders/export/excel/', export_purchase_orders_excel, name='export_purchase_orders_excel'),
    path('reports/purchase-orders/export/pdf/', export_purchase_orders_pdf, name='export_purchase_orders_pdf'),
    path('reports/items-purchases/export/excel/', export_items_purchases_excel, name='export_items_purchases_excel'),
    path('reports/items-purchases/export/pdf/', export_items_purchases_pdf, name='export_items_purchases_pdf'),
    path('reports/contracts/export/excel/', export_contracts_excel, name='export_contracts_excel'),
    path('reports/contracts/export/pdf/', export_contracts_pdf, name='export_contracts_pdf'),
]

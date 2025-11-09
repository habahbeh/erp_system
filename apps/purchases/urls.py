# apps/purchases/urls.py
"""
URL Configuration for Purchases App
"""

from django.urls import path
from .views import *

app_name = 'purchases'

urlpatterns = [
    # ==================== Purchase Invoices ====================
    path('invoices/', PurchaseInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', PurchaseInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', PurchaseInvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', PurchaseInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', PurchaseInvoiceDeleteView.as_view(), name='invoice_delete'),

    # Invoice Actions
    path('invoices/<int:pk>/post/', post_invoice, name='post_invoice'),
    path('invoices/<int:pk>/unpost/', unpost_invoice, name='unpost_invoice'),

    # Invoice AJAX & Export
    path('ajax/invoices/datatable/', invoice_datatable_ajax, name='invoice_datatable_ajax'),
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
    path('requests/export/', export_requests_excel, name='export_requests_excel'),

    # ==================== Quotation Requests (RFQ) ====================
    path('rfqs/', PurchaseQuotationRequestListView.as_view(), name='rfq_list'),
    path('rfqs/create/', PurchaseQuotationRequestCreateView.as_view(), name='rfq_create'),
    path('rfqs/<int:pk>/', PurchaseQuotationRequestDetailView.as_view(), name='rfq_detail'),
    path('rfqs/<int:pk>/update/', PurchaseQuotationRequestUpdateView.as_view(), name='rfq_update'),
    path('rfqs/<int:pk>/delete/', PurchaseQuotationRequestDeleteView.as_view(), name='rfq_delete'),

    # RFQ Actions
    path('rfqs/<int:pk>/send/', send_rfq_to_suppliers, name='send_rfq_to_suppliers'),
    path('rfqs/<int:pk>/cancel/', cancel_rfq, name='cancel_rfq'),
    path('rfqs/<int:pk>/evaluate/', mark_rfq_as_evaluating, name='mark_rfq_as_evaluating'),

    # RFQ AJAX & Export
    path('ajax/rfqs/datatable/', rfq_datatable_ajax, name='rfq_datatable_ajax'),
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
]

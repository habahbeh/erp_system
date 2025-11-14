# apps/purchases/views/__init__.py
"""
Views for Purchases app
"""

# Dashboard Views
from .dashboard import (
    PurchaseDashboardView,
    dashboard_stats_api,
    monthly_chart_api,
    top_suppliers_api,
)

# Invoice Views
from .invoice_views import (
    PurchaseInvoiceListView,
    PurchaseInvoiceDetailView,
    PurchaseInvoiceCreateView,
    PurchaseInvoiceUpdateView,
    PurchaseInvoiceDeleteView,
    post_invoice,
    unpost_invoice,
    invoice_datatable_ajax,
    export_invoices_excel,
)

# Order Views
from .order_views import (
    PurchaseOrderListView,
    PurchaseOrderDetailView,
    PurchaseOrderCreateView,
    PurchaseOrderUpdateView,
    PurchaseOrderDeleteView,
    submit_for_approval,
    approve_order,
    reject_order,
    send_to_supplier,
    cancel_order,
    convert_to_invoice,
    order_datatable_ajax,
    export_orders_excel,
)

# Request Views
from .request_views import (
    PurchaseRequestListView,
    PurchaseRequestDetailView,
    PurchaseRequestCreateView,
    PurchaseRequestUpdateView,
    PurchaseRequestDeleteView,
    submit_request,
    approve_request,
    reject_request,
    create_order_from_request,
    request_datatable_ajax,
    export_requests_excel,
)

# Quotation Views
from .quotation_views import (
    PurchaseQuotationRequestListView,
    PurchaseQuotationRequestDetailView,
    PurchaseQuotationRequestCreateView,
    PurchaseQuotationRequestUpdateView,
    PurchaseQuotationRequestDeleteView,
    send_rfq_to_suppliers,
    cancel_rfq,
    mark_rfq_as_evaluating,
    PurchaseQuotationListView,
    PurchaseQuotationDetailView,
    PurchaseQuotationCreateView,
    PurchaseQuotationUpdateView,
    PurchaseQuotationDeleteView,
    evaluate_quotation,
    award_quotation,
    reject_quotation,
    convert_quotation_to_order,
    rfq_datatable_ajax,
    quotation_datatable_ajax,
    export_rfqs_excel,
    export_quotations_excel,
)

# Contract Views
from .contract_views import (
    PurchaseContractListView,
    PurchaseContractDetailView,
    PurchaseContractCreateView,
    PurchaseContractUpdateView,
    PurchaseContractDeleteView,
    contract_approve,
    contract_change_status,
    contract_check_expiry,
    contract_copy_or_renew,
)

# Goods Receipt Views
from .goods_receipt_views import (
    GoodsReceiptListView,
    GoodsReceiptDetailView,
    GoodsReceiptCreateView,
    GoodsReceiptUpdateView,
    GoodsReceiptDeleteView,
    confirm_goods_receipt,
    post_goods_receipt,
    unpost_goods_receipt,
    goods_receipt_datatable_ajax,
    export_goods_receipts_excel,
)

# AJAX Views
from .ajax_views import (
    ajax_items_search,
    ajax_request_credit_approval,
    ajax_price_history,
    ajax_supplier_info,
)

# Report Views
from .report_views import (
    reports_list,
    purchases_summary_report,
    supplier_performance_report,
    purchase_orders_report,
    items_purchases_report,
    contracts_report,
    export_purchases_summary_excel,
    export_purchases_summary_pdf,
    export_supplier_performance_excel,
    export_supplier_performance_pdf,
    export_purchase_orders_excel,
    export_purchase_orders_pdf,
    export_items_purchases_excel,
    export_items_purchases_pdf,
)

__all__ = [
    # Dashboard Views
    "PurchaseDashboardView",
    "dashboard_stats_api",
    "monthly_chart_api",
    "top_suppliers_api",

    # Invoice Views
    "PurchaseInvoiceListView",
    "PurchaseInvoiceDetailView",
    "PurchaseInvoiceCreateView",
    "PurchaseInvoiceUpdateView",
    "PurchaseInvoiceDeleteView",
    "post_invoice",
    "unpost_invoice",
    "invoice_datatable_ajax",
    "export_invoices_excel",

    # Order Views
    "PurchaseOrderListView",
    "PurchaseOrderDetailView",
    "PurchaseOrderCreateView",
    "PurchaseOrderUpdateView",
    "PurchaseOrderDeleteView",
    "submit_for_approval",
    "approve_order",
    "reject_order",
    "send_to_supplier",
    "cancel_order",
    "convert_to_invoice",
    "order_datatable_ajax",
    "export_orders_excel",

    # Request Views
    "PurchaseRequestListView",
    "PurchaseRequestDetailView",
    "PurchaseRequestCreateView",
    "PurchaseRequestUpdateView",
    "PurchaseRequestDeleteView",
    "submit_request",
    "approve_request",
    "reject_request",
    "create_order_from_request",
    "request_datatable_ajax",
    "export_requests_excel",

    # Quotation Request Views
    "PurchaseQuotationRequestListView",
    "PurchaseQuotationRequestDetailView",
    "PurchaseQuotationRequestCreateView",
    "PurchaseQuotationRequestUpdateView",
    "PurchaseQuotationRequestDeleteView",
    "send_rfq_to_suppliers",
    "cancel_rfq",
    "mark_rfq_as_evaluating",

    # Quotation Views
    "PurchaseQuotationListView",
    "PurchaseQuotationDetailView",
    "PurchaseQuotationCreateView",
    "PurchaseQuotationUpdateView",
    "PurchaseQuotationDeleteView",
    "evaluate_quotation",
    "award_quotation",
    "reject_quotation",
    "convert_quotation_to_order",
    "rfq_datatable_ajax",
    "quotation_datatable_ajax",
    "export_rfqs_excel",
    "export_quotations_excel",

    # Contract Views
    "PurchaseContractListView",
    "PurchaseContractDetailView",
    "PurchaseContractCreateView",
    "PurchaseContractUpdateView",
    "PurchaseContractDeleteView",
    "contract_approve",
    "contract_change_status",
    "contract_check_expiry",
    "contract_copy_or_renew",

    # Goods Receipt Views
    "GoodsReceiptListView",
    "GoodsReceiptDetailView",
    "GoodsReceiptCreateView",
    "GoodsReceiptUpdateView",
    "GoodsReceiptDeleteView",
    "confirm_goods_receipt",
    "post_goods_receipt",
    "unpost_goods_receipt",
    "goods_receipt_datatable_ajax",
    "export_goods_receipts_excel",

    # AJAX Views
    "ajax_items_search",
    "ajax_request_credit_approval",
    "ajax_price_history",
    "ajax_supplier_info",

    # Report Views
    "reports_list",
    "purchases_summary_report",
    "supplier_performance_report",
    "purchase_orders_report",
    "items_purchases_report",
    "contracts_report",
    "export_purchases_summary_excel",
    "export_purchases_summary_pdf",
    "export_supplier_performance_excel",
    "export_supplier_performance_pdf",
    "export_purchase_orders_excel",
    "export_purchase_orders_pdf",
    "export_items_purchases_excel",
    "export_items_purchases_pdf",
]

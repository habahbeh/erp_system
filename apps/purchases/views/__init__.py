# apps/purchases/views/__init__.py
"""
Views for Purchases app
"""

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

__all__ = [
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
]

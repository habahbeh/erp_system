# apps/sales/views/__init__.py
"""
Views لنظام المبيعات
"""

from .dashboard_views import sales_dashboard

from .invoice_views import (
    SalesInvoiceListView,
    SalesInvoiceCreateView,
    SalesInvoiceUpdateView,
    SalesInvoiceDetailView,
    SalesInvoiceDeleteView,
    SalesInvoicePostView,
    SalesInvoiceUnpostView,
    invoice_datatable_ajax,
    export_invoices_excel,
)

from .quotation_views import (
    QuotationListView,
    QuotationCreateView,
    QuotationUpdateView,
    QuotationDetailView,
    QuotationDeleteView,
    ConvertToOrderView,
    ApproveQuotationView,
)

from .order_views import (
    SalesOrderListView,
    SalesOrderCreateView,
    SalesOrderUpdateView,
    SalesOrderDetailView,
    SalesOrderDeleteView,
    ApproveSalesOrderView,
    ConvertToInvoiceView,
)

from .payment_views import (
    InstallmentListView,
    CreateInstallmentPlanView,
    InstallmentDetailView,
    RecordPaymentView,
    CancelInstallmentView,
    UpdateInstallmentStatusView,
)

from .commission_views import (
    CommissionListView,
    CommissionCreateView,
    CommissionUpdateView,
    CommissionDetailView,
    CommissionDeleteView,
    RecordCommissionPaymentView,
    CommissionReportView,
)

__all__ = [
    # Dashboard
    'sales_dashboard',
    # Invoice Views
    'SalesInvoiceListView',
    'SalesInvoiceCreateView',
    'SalesInvoiceUpdateView',
    'SalesInvoiceDetailView',
    'SalesInvoiceDeleteView',
    'SalesInvoicePostView',
    'SalesInvoiceUnpostView',
    'invoice_datatable_ajax',
    'export_invoices_excel',
    # Quotation Views
    'QuotationListView',
    'QuotationCreateView',
    'QuotationUpdateView',
    'QuotationDetailView',
    'QuotationDeleteView',
    'ConvertToOrderView',
    'ApproveQuotationView',
    # Order Views
    'SalesOrderListView',
    'SalesOrderCreateView',
    'SalesOrderUpdateView',
    'SalesOrderDetailView',
    'SalesOrderDeleteView',
    'ApproveSalesOrderView',
    'ConvertToInvoiceView',
    # Payment/Installment Views
    'InstallmentListView',
    'CreateInstallmentPlanView',
    'InstallmentDetailView',
    'RecordPaymentView',
    'CancelInstallmentView',
    'UpdateInstallmentStatusView',
    # Commission Views
    'CommissionListView',
    'CommissionCreateView',
    'CommissionUpdateView',
    'CommissionDetailView',
    'CommissionDeleteView',
    'RecordCommissionPaymentView',
    'CommissionReportView',
]

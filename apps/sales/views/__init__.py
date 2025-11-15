# apps/sales/views/__init__.py
"""
Views لنظام المبيعات
"""

from .invoice_views import (
    SalesInvoiceListView,
    SalesInvoiceCreateView,
    SalesInvoiceUpdateView,
    SalesInvoiceDetailView,
    SalesInvoiceDeleteView,
    SalesInvoicePostView,
    SalesInvoiceUnpostView,
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

from .campaign_views import (
    CampaignListView,
    CampaignCreateView,
    CampaignUpdateView,
    CampaignDetailView,
    CampaignDeleteView,
    ToggleCampaignStatusView,
    GetActiveCampaignsAjax,
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

from .pos_views import (
    POSSessionListView,
    POSSessionCreateView,
    POSSessionDetailView,
    POSSessionCloseView,
    POSInterfaceView,
    POSSearchItemView,
    POSCreateInvoiceView,
    POSSessionReopenView,
    POSSessionPrintReportView,
)

__all__ = [
    # Invoice Views
    'SalesInvoiceListView',
    'SalesInvoiceCreateView',
    'SalesInvoiceUpdateView',
    'SalesInvoiceDetailView',
    'SalesInvoiceDeleteView',
    'SalesInvoicePostView',
    'SalesInvoiceUnpostView',
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
    # Campaign Views
    'CampaignListView',
    'CampaignCreateView',
    'CampaignUpdateView',
    'CampaignDetailView',
    'CampaignDeleteView',
    'ToggleCampaignStatusView',
    'GetActiveCampaignsAjax',
    # Commission Views
    'CommissionListView',
    'CommissionCreateView',
    'CommissionUpdateView',
    'CommissionDetailView',
    'CommissionDeleteView',
    'RecordCommissionPaymentView',
    'CommissionReportView',
    # POS Views
    'POSSessionListView',
    'POSSessionCreateView',
    'POSSessionDetailView',
    'POSSessionCloseView',
    'POSInterfaceView',
    'POSSearchItemView',
    'POSCreateInvoiceView',
    'POSSessionReopenView',
    'POSSessionPrintReportView',
]

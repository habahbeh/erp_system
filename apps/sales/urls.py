# apps/sales/urls.py
"""
URL Configuration for Sales App
"""

from django.urls import path
from .views.report_views import (
    customer_statement_report,
    sales_detailed_report,
    profit_loss_report,
    tax_report,
    invoice_search_report,
    quotation_comparison_report,
    commission_report,
    campaign_report,
)
from .views import (
    # Invoice Views
    SalesInvoiceListView,
    SalesInvoiceCreateView,
    SalesInvoiceUpdateView,
    SalesInvoiceDetailView,
    SalesInvoiceDeleteView,
    SalesInvoicePostView,
    SalesInvoiceUnpostView,
    # Quotation Views
    QuotationListView,
    QuotationCreateView,
    QuotationUpdateView,
    QuotationDetailView,
    QuotationDeleteView,
    ConvertToOrderView,
    ApproveQuotationView,
    # Order Views
    SalesOrderListView,
    SalesOrderCreateView,
    SalesOrderUpdateView,
    SalesOrderDetailView,
    SalesOrderDeleteView,
    ApproveSalesOrderView,
    ConvertToInvoiceView,
    # Installment Views
    InstallmentListView,
    CreateInstallmentPlanView,
    InstallmentDetailView,
    RecordPaymentView,
    CancelInstallmentView,
    UpdateInstallmentStatusView,
    # Campaign Views
    CampaignListView,
    CampaignCreateView,
    CampaignUpdateView,
    CampaignDetailView,
    CampaignDeleteView,
    ToggleCampaignStatusView,
    GetActiveCampaignsAjax,
    # Commission Views
    CommissionListView,
    CommissionCreateView,
    CommissionUpdateView,
    CommissionDetailView,
    CommissionDeleteView,
    RecordCommissionPaymentView,
    CommissionReportView,
    # POS Views
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

app_name = 'sales'

urlpatterns = [
    # ==================== Sales Invoices ====================
    path('invoices/', SalesInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', SalesInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', SalesInvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', SalesInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', SalesInvoiceDeleteView.as_view(), name='invoice_delete'),

    # Invoice Actions
    path('invoices/<int:pk>/post/', SalesInvoicePostView.as_view(), name='invoice_post'),
    path('invoices/<int:pk>/unpost/', SalesInvoiceUnpostView.as_view(), name='invoice_unpost'),

    # ==================== Quotations ====================
    path('quotations/', QuotationListView.as_view(), name='quotation_list'),
    path('quotations/create/', QuotationCreateView.as_view(), name='quotation_create'),
    path('quotations/<int:pk>/', QuotationDetailView.as_view(), name='quotation_detail'),
    path('quotations/<int:pk>/update/', QuotationUpdateView.as_view(), name='quotation_update'),
    path('quotations/<int:pk>/delete/', QuotationDeleteView.as_view(), name='quotation_delete'),

    # Quotation Actions
    path('quotations/<int:pk>/approve/', ApproveQuotationView.as_view(), name='quotation_approve'),
    path('quotations/<int:pk>/convert-to-order/', ConvertToOrderView.as_view(), name='quotation_convert_to_order'),

    # ==================== Sales Orders ====================
    path('orders/', SalesOrderListView.as_view(), name='order_list'),
    path('orders/create/', SalesOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', SalesOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update/', SalesOrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', SalesOrderDeleteView.as_view(), name='order_delete'),

    # Order Actions
    path('orders/<int:pk>/approve/', ApproveSalesOrderView.as_view(), name='order_approve'),
    path('orders/<int:pk>/convert-to-invoice/', ConvertToInvoiceView.as_view(), name='order_convert_to_invoice'),

    # ==================== Payment Installments ====================
    path('installments/', InstallmentListView.as_view(), name='installment_list'),
    path('installments/<int:pk>/', InstallmentDetailView.as_view(), name='installment_detail'),
    path('installments/<int:pk>/record-payment/', RecordPaymentView.as_view(), name='record_payment'),
    path('installments/<int:pk>/cancel/', CancelInstallmentView.as_view(), name='cancel_installment'),
    path('installments/update-status/', UpdateInstallmentStatusView.as_view(), name='update_installment_status'),

    # Installment Plan
    path('invoices/<int:invoice_pk>/create-installment-plan/', CreateInstallmentPlanView.as_view(), name='create_installment_plan'),

    # ==================== Discount Campaigns ====================
    path('campaigns/', CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', CampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<int:pk>/', CampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<int:pk>/update/', CampaignUpdateView.as_view(), name='campaign_update'),
    path('campaigns/<int:pk>/delete/', CampaignDeleteView.as_view(), name='campaign_delete'),

    # Campaign Actions
    path('campaigns/<int:pk>/toggle-status/', ToggleCampaignStatusView.as_view(), name='toggle_campaign_status'),
    path('campaigns/get-active-campaigns/', GetActiveCampaignsAjax.as_view(), name='get_active_campaigns'),

    # ==================== Salesperson Commissions ====================
    path('commissions/', CommissionListView.as_view(), name='commission_list'),
    path('commissions/create/', CommissionCreateView.as_view(), name='commission_create'),
    path('commissions/<int:pk>/', CommissionDetailView.as_view(), name='commission_detail'),
    path('commissions/<int:pk>/update/', CommissionUpdateView.as_view(), name='commission_update'),
    path('commissions/<int:pk>/delete/', CommissionDeleteView.as_view(), name='commission_delete'),

    # Commission Actions
    path('commissions/<int:pk>/record-payment/', RecordCommissionPaymentView.as_view(), name='record_commission_payment'),
    path('commissions/report/', CommissionReportView.as_view(), name='commission_report'),

    # ==================== POS Sessions ====================
    path('pos/sessions/', POSSessionListView.as_view(), name='pos_session_list'),
    path('pos/sessions/create/', POSSessionCreateView.as_view(), name='pos_session_create'),
    path('pos/sessions/<int:pk>/', POSSessionDetailView.as_view(), name='pos_session_detail'),
    path('pos/sessions/<int:pk>/close/', POSSessionCloseView.as_view(), name='pos_session_close'),
    path('pos/sessions/<int:pk>/reopen/', POSSessionReopenView.as_view(), name='pos_session_reopen'),
    path('pos/sessions/<int:pk>/print/', POSSessionPrintReportView.as_view(), name='pos_session_print'),

    # POS Selling Interface
    path('pos/<int:pk>/interface/', POSInterfaceView.as_view(), name='pos_interface'),
    path('pos/search-item/', POSSearchItemView.as_view(), name='pos_search_item'),
    path('pos/<int:session_id>/create-invoice/', POSCreateInvoiceView.as_view(), name='pos_create_invoice'),

    # ==================== Reports ====================
    path('reports/customer-statement/', customer_statement_report, name='report_customer_statement'),
    path('reports/sales-detailed/', sales_detailed_report, name='report_sales_detailed'),
    path('reports/profit-loss/', profit_loss_report, name='report_profit_loss'),
    path('reports/tax/', tax_report, name='report_tax'),
    path('reports/invoice-search/', invoice_search_report, name='report_invoice_search'),
    path('reports/quotation-comparison/', quotation_comparison_report, name='report_quotation_comparison'),
    path('reports/commission/', commission_report, name='report_commission'),
    path('reports/campaign/', campaign_report, name='report_campaign'),
]

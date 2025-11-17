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
)
from .views import (
    # Dashboard
    sales_dashboard,
    # Invoice Views
    SalesInvoiceListView,
    SalesInvoiceCreateView,
    SalesInvoiceUpdateView,
    SalesInvoiceDetailView,
    SalesInvoiceDeleteView,
    SalesInvoicePostView,
    SalesInvoiceUnpostView,
    invoice_datatable_ajax,
    export_invoices_excel,
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
    # Commission Views
    CommissionListView,
    CommissionCreateView,
    CommissionUpdateView,
    CommissionDetailView,
    CommissionDeleteView,
    RecordCommissionPaymentView,
    CommissionReportView,
)

app_name = 'sales'

urlpatterns = [
    # ==================== Dashboard ====================
    path('', sales_dashboard, name='dashboard'),

    # ==================== Sales Invoices ====================
    path('invoices/', SalesInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', SalesInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', SalesInvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', SalesInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', SalesInvoiceDeleteView.as_view(), name='invoice_delete'),

    # Invoice Actions
    path('invoices/<int:pk>/post/', SalesInvoicePostView.as_view(), name='invoice_post'),
    path('invoices/<int:pk>/unpost/', SalesInvoiceUnpostView.as_view(), name='invoice_unpost'),

    # Invoice AJAX & Export
    path('ajax/invoices/datatable/', invoice_datatable_ajax, name='invoice_datatable_ajax'),
    path('invoices/export/', export_invoices_excel, name='export_invoices_excel'),

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

    # ==================== Salesperson Commissions ====================
    path('commissions/', CommissionListView.as_view(), name='commission_list'),
    path('commissions/create/', CommissionCreateView.as_view(), name='commission_create'),
    path('commissions/<int:pk>/', CommissionDetailView.as_view(), name='commission_detail'),
    path('commissions/<int:pk>/update/', CommissionUpdateView.as_view(), name='commission_update'),
    path('commissions/<int:pk>/delete/', CommissionDeleteView.as_view(), name='commission_delete'),

    # Commission Actions
    path('commissions/<int:pk>/record-payment/', RecordCommissionPaymentView.as_view(), name='record_commission_payment'),
    path('commissions/report/', CommissionReportView.as_view(), name='commission_report'),

    # ==================== Reports ====================
    path('reports/customer-statement/', customer_statement_report, name='report_customer_statement'),
    path('reports/sales-detailed/', sales_detailed_report, name='report_sales_detailed'),
    path('reports/profit-loss/', profit_loss_report, name='report_profit_loss'),
    path('reports/tax/', tax_report, name='report_tax'),
    path('reports/invoice-search/', invoice_search_report, name='report_invoice_search'),
    path('reports/quotation-comparison/', quotation_comparison_report, name='report_quotation_comparison'),
    path('reports/commission/', commission_report, name='report_commission'),
]

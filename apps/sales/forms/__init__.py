# apps/sales/forms/__init__.py
"""
نماذج نظام المبيعات
"""

from .invoice_forms import (
    SalesInvoiceForm,
    InvoiceItemForm,
    InvoiceItemFormSet,
)

from .quotation_forms import (
    QuotationForm,
    QuotationItemForm,
    QuotationItemFormSet,
)

from .order_forms import (
    SalesOrderForm,
    SalesOrderItemForm,
    SalesOrderItemFormSet,
)

from .payment_forms import (
    PaymentInstallmentForm,
    RecordPaymentForm,
    CreateInstallmentPlanForm,
    InstallmentPlanFormSet,
)

from .campaign_forms import (
    DiscountCampaignForm,
)

from .commission_forms import (
    SalespersonCommissionForm,
    RecordCommissionPaymentForm,
)

__all__ = [
    'SalesInvoiceForm',
    'InvoiceItemForm',
    'InvoiceItemFormSet',
    'QuotationForm',
    'QuotationItemForm',
    'QuotationItemFormSet',
    'SalesOrderForm',
    'SalesOrderItemForm',
    'SalesOrderItemFormSet',
    'PaymentInstallmentForm',
    'RecordPaymentForm',
    'CreateInstallmentPlanForm',
    'InstallmentPlanFormSet',
    'DiscountCampaignForm',
    'SalespersonCommissionForm',
    'RecordCommissionPaymentForm',
]

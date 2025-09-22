# apps/accounting/views/__init__.py
from . import dashboard
from .account_type_views import *
from .account_views import *
from .journal_views import *
from .voucher_views import *
from .report_views import *
from . import fiscal_views

__all__ = [
    # Dashboard
    'dashboard',

    # Account Type views
    'AccountTypeListView', 'AccountTypeCreateView', 'AccountTypeUpdateView', 'AccountTypeDeleteView',
    'account_type_datatable_ajax', 'account_type_stats_ajax',

    # Account views
    'AccountListView', 'AccountCreateView', 'AccountUpdateView', 'AccountDeleteView', 'AccountDetailView',
    'account_datatable_ajax', 'account_hierarchy_ajax', 'account_search_ajax', 'account_stats_ajax',

    # Journal views
    'JournalEntryListView', 'JournalEntryCreateView', 'JournalEntryUpdateView',
    'JournalEntryDetailView', 'JournalEntryDeleteView', 'QuickJournalEntryView',
    'journal_entry_datatable_ajax', 'account_autocomplete', 'post_journal_entry',
    'unpost_journal_entry', 'get_template_lines',

    # Voucher views
    'PaymentVoucherListView', 'PaymentVoucherCreateView', 'PaymentVoucherUpdateView',
    'PaymentVoucherDetailView', 'PaymentVoucherDeleteView',
    'ReceiptVoucherListView', 'ReceiptVoucherCreateView', 'ReceiptVoucherUpdateView',
    'ReceiptVoucherDetailView', 'ReceiptVoucherDeleteView',
    'post_payment_voucher', 'unpost_payment_voucher', 'post_receipt_voucher', 'unpost_receipt_voucher',

    # Fiscal views
    'FiscalYearListView', 'FiscalYearCreateView', 'FiscalYearUpdateView',
    'FiscalYearDetailView', 'FiscalYearDeleteView', 'fiscal_year_datatable_ajax', 'create_periods_ajax',
    'AccountingPeriodListView', 'AccountingPeriodCreateView', 'AccountingPeriodUpdateView',
    'AccountingPeriodDetailView', 'AccountingPeriodDeleteView', 'close_period_ajax', 'reopen_period_ajax',

    # Cost Center views
    'CostCenterListView', 'CostCenterCreateView', 'CostCenterUpdateView',
    'CostCenterDetailView', 'CostCenterDeleteView', 'cost_center_search_ajax',

    # Report views
    'export_account_types', 'import_account_types', 'export_accounts', 'import_accounts',

    # Report views
    'GeneralLedgerView', 'TrialBalanceView', 'AccountStatementView',
    'IncomeStatementView', 'BalanceSheetView', 'AccountComparisonView',
    'export_general_ledger', 'export_trial_balance', 'export_account_statement',
    'export_income_statement', 'export_balance_sheet', 'export_cost_centers',
    'account_search_for_reports',
]
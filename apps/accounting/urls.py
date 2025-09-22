# apps/accounting/urls.py
from django.urls import path
from .views import (
    dashboard,
    # Account Type Views
    account_type_views,
    # Account Views
    account_views,
    # Journal Views
    journal_views,
    # Template Views
    template_views,
    # Voucher Views
    voucher_views,
    # Report Views
    report_views,
    # Fiscal Views
    fiscal_views
)

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', dashboard.AccountingDashboardView.as_view(), name='dashboard'),

    # Account Types URLs
    path('account-types/', account_type_views.AccountTypeListView.as_view(), name='account_type_list'),
    path('account-types/create/', account_type_views.AccountTypeCreateView.as_view(), name='account_type_create'),
    path('account-types/<int:pk>/update/', account_type_views.AccountTypeUpdateView.as_view(),
         name='account_type_update'),
    path('account-types/<int:pk>/delete/', account_type_views.AccountTypeDeleteView.as_view(),
         name='account_type_delete'),

    # Accounts URLs
    path('accounts/', account_views.AccountListView.as_view(), name='account_list'),
    path('accounts/create/', account_views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/', account_views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/update/', account_views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', account_views.AccountDeleteView.as_view(), name='account_delete'),

    # Journal Entry URLs
    path('journal-entries/', journal_views.JournalEntryListView.as_view(), name='journal_entry_list'),
    path('journal-entries/create/', journal_views.JournalEntryCreateView.as_view(), name='journal_entry_create'),
    path('journal-entries/<int:pk>/', journal_views.JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('journal-entries/<int:pk>/update/', journal_views.JournalEntryUpdateView.as_view(),
         name='journal_entry_update'),
    path('journal-entries/<int:pk>/delete/', journal_views.JournalEntryDeleteView.as_view(),
         name='journal_entry_delete'),
    path('journal-entries/quick/', journal_views.QuickJournalEntryView.as_view(), name='quick_journal_entry'),

    # Payment Voucher URLs
    path('payment-vouchers/', voucher_views.PaymentVoucherListView.as_view(), name='payment_voucher_list'),
    path('payment-vouchers/create/', voucher_views.PaymentVoucherCreateView.as_view(), name='payment_voucher_create'),
    path('payment-vouchers/<int:pk>/', voucher_views.PaymentVoucherDetailView.as_view(), name='payment_voucher_detail'),
    path('payment-vouchers/<int:pk>/update/', voucher_views.PaymentVoucherUpdateView.as_view(),
         name='payment_voucher_update'),
    path('payment-vouchers/<int:pk>/delete/', voucher_views.PaymentVoucherDeleteView.as_view(),
         name='payment_voucher_delete'),

    # Receipt Voucher URLs
    path('receipt-vouchers/', voucher_views.ReceiptVoucherListView.as_view(), name='receipt_voucher_list'),
    path('receipt-vouchers/create/', voucher_views.ReceiptVoucherCreateView.as_view(), name='receipt_voucher_create'),
    path('receipt-vouchers/<int:pk>/', voucher_views.ReceiptVoucherDetailView.as_view(), name='receipt_voucher_detail'),
    path('receipt-vouchers/<int:pk>/update/', voucher_views.ReceiptVoucherUpdateView.as_view(),
         name='receipt_voucher_update'),
    path('receipt-vouchers/<int:pk>/delete/', voucher_views.ReceiptVoucherDeleteView.as_view(),
         name='receipt_voucher_delete'),

    # ========== تقارير محاسبية جديدة ==========
    # General Ledger - دفتر الأستاذ
    path('reports/general-ledger/', report_views.GeneralLedgerView.as_view(), name='general_ledger'),

    # Trial Balance - ميزان المراجعة
    path('reports/trial-balance/', report_views.TrialBalanceView.as_view(), name='trial_balance'),

    # Ajax endpoints - DataTables
    path('ajax/account-types/', account_type_views.account_type_datatable_ajax, name='account_type_datatable_ajax'),
    path('ajax/accounts/', account_views.account_datatable_ajax, name='account_datatable_ajax'),
    path('ajax/journal-entries/', journal_views.journal_entry_datatable_ajax, name='journal_entry_datatable_ajax'),
    path('ajax/payment-vouchers/', voucher_views.payment_voucher_datatable_ajax, name='payment_voucher_datatable_ajax'),
    path('ajax/receipt-vouchers/', voucher_views.receipt_voucher_datatable_ajax, name='receipt_voucher_datatable_ajax'),

    # Ajax endpoints - Account related
    path('ajax/accounts/search/', account_views.account_search_ajax, name='account_search_ajax'),
    path('ajax/accounts/autocomplete/', journal_views.account_autocomplete, name='account_autocomplete'),
    path('ajax/accounts/hierarchy/', account_views.account_hierarchy_ajax, name='account_hierarchy_ajax'),
    path('ajax/accounts/stats/', account_views.account_stats_ajax, name='account_stats_ajax'),

    # Ajax endpoints - Reports
    path('ajax/accounts/search-for-reports/', report_views.account_search_for_reports,
         name='account_search_for_reports'),

    # Ajax endpoints - Account Type related
    path('ajax/account-types/stats/', account_type_views.account_type_stats_ajax, name='account_type_stats_ajax'),

    # Ajax endpoints - Journal Entry related
    path('ajax/templates/<int:template_id>/lines/', journal_views.get_template_lines, name='get_template_lines'),

    # Journal Entry Actions
    path('ajax/journal-entries/<int:pk>/post/', journal_views.post_journal_entry, name='post_journal_entry'),
    path('ajax/journal-entries/<int:pk>/unpost/', journal_views.unpost_journal_entry, name='unpost_journal_entry'),

    # Voucher Actions - Payment Vouchers
    path('ajax/payment-vouchers/<int:pk>/post/', voucher_views.post_payment_voucher, name='post_payment_voucher'),
    path('ajax/payment-vouchers/<int:pk>/unpost/', voucher_views.unpost_payment_voucher, name='unpost_payment_voucher'),

    # Voucher Actions - Receipt Vouchers
    path('ajax/receipt-vouchers/<int:pk>/post/', voucher_views.post_receipt_voucher, name='post_receipt_voucher'),
    path('ajax/receipt-vouchers/<int:pk>/unpost/', voucher_views.unpost_receipt_voucher, name='unpost_receipt_voucher'),

    # Export/Import URLs
    path('account-types/export/', report_views.export_account_types, name='export_account_types'),
    path('account-types/import/', report_views.import_account_types, name='import_account_types'),
    path('accounts/export/', report_views.export_accounts, name='export_accounts'),
    path('accounts/import/', report_views.import_accounts, name='import_accounts'),

    # Voucher Export URLs
    path('payment-vouchers/export/', voucher_views.export_payment_vouchers, name='export_payment_vouchers'),
    path('receipt-vouchers/export/', voucher_views.export_receipt_vouchers, name='export_receipt_vouchers'),

    # ========== تقارير محاسبية كاملة ==========
    # General Ledger - دفتر الأستاذ
    path('reports/general-ledger/', report_views.GeneralLedgerView.as_view(), name='general_ledger'),

    # Trial Balance - ميزان المراجعة
    path('reports/trial-balance/', report_views.TrialBalanceView.as_view(), name='trial_balance'),

    # Account Statement - كشف الحساب
    path('reports/account-statement/', report_views.AccountStatementView.as_view(), name='account_statement'),

    # Income Statement - قائمة الدخل
    path('reports/income-statement/', report_views.IncomeStatementView.as_view(), name='income_statement'),

    # Balance Sheet - الميزانية العمومية
    path('reports/balance-sheet/', report_views.BalanceSheetView.as_view(), name='balance_sheet'),

    # Account Comparison - مقارنة الحسابات
    path('reports/account-comparison/', report_views.AccountComparisonView.as_view(), name='account_comparison'),

    # ========== تصدير جميع التقارير ==========
    path('reports/general-ledger/export/', report_views.export_general_ledger, name='export_general_ledger'),
    path('reports/trial-balance/export/', report_views.export_trial_balance, name='export_trial_balance'),
    path('reports/account-statement/export/', report_views.export_account_statement, name='export_account_statement'),
    path('reports/income-statement/export/', report_views.export_income_statement, name='export_income_statement'),
    path('reports/balance-sheet/export/', report_views.export_balance_sheet, name='export_balance_sheet'),

    # ========== السنوات المالية ==========
    path('fiscal-years/', fiscal_views.FiscalYearListView.as_view(), name='fiscal_year_list'),
    path('fiscal-years/create/', fiscal_views.FiscalYearCreateView.as_view(), name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/', fiscal_views.FiscalYearDetailView.as_view(), name='fiscal_year_detail'),
    path('fiscal-years/<int:pk>/update/', fiscal_views.FiscalYearUpdateView.as_view(), name='fiscal_year_update'),
    path('fiscal-years/<int:pk>/delete/', fiscal_views.FiscalYearDeleteView.as_view(), name='fiscal_year_delete'),

    # Ajax - السنوات المالية
    path('ajax/fiscal-years/', fiscal_views.fiscal_year_datatable_ajax, name='fiscal_year_datatable_ajax'),
    path('ajax/fiscal-years/<int:fiscal_year_id>/create-periods/', fiscal_views.create_periods_ajax,
         name='create_periods_ajax'),

    # ========== الفترات المحاسبية ==========
    path('periods/', fiscal_views.AccountingPeriodListView.as_view(), name='period_list'),
    path('periods/create/', fiscal_views.AccountingPeriodCreateView.as_view(), name='period_create'),
    path('periods/<int:pk>/', fiscal_views.AccountingPeriodDetailView.as_view(), name='period_detail'),
    path('periods/<int:pk>/update/', fiscal_views.AccountingPeriodUpdateView.as_view(), name='period_update'),
    path('periods/<int:pk>/delete/', fiscal_views.AccountingPeriodDeleteView.as_view(), name='period_delete'),

    # Ajax - الفترات المحاسبية
    path('ajax/periods/', fiscal_views.period_datatable_ajax, name='period_datatable_ajax'),
    path('ajax/periods/<int:period_id>/close/', fiscal_views.close_period_ajax, name='close_period_ajax'),
    path('ajax/periods/<int:period_id>/reopen/', fiscal_views.reopen_period_ajax, name='reopen_period_ajax'),

    # ========== مراكز التكلفة ==========
    path('cost-centers/', fiscal_views.CostCenterListView.as_view(), name='cost_center_list'),
    path('cost-centers/create/', fiscal_views.CostCenterCreateView.as_view(), name='cost_center_create'),
    path('cost-centers/<int:pk>/', fiscal_views.CostCenterDetailView.as_view(), name='cost_center_detail'),
    path('cost-centers/<int:pk>/update/', fiscal_views.CostCenterUpdateView.as_view(), name='cost_center_update'),
    path('cost-centers/<int:pk>/delete/', fiscal_views.CostCenterDeleteView.as_view(), name='cost_center_delete'),
    path('cost-centers/export/', report_views.export_cost_centers, name='export_cost_centers'),

    # Ajax - مراكز التكلفة
    path('ajax/cost-centers/', fiscal_views.cost_center_datatable_ajax, name='cost_center_datatable_ajax'),
    path('ajax/cost-centers/search/', fiscal_views.cost_center_search_ajax, name='cost_center_search_ajax'),

    # Ajax endpoints للفترات المحاسبية
    # path('ajax/periods/datatable/', period_datatable_ajax, name='period_datatable_ajax'),

    # Ajax endpoints لمراكز التكلفة
    # path('ajax/cost-centers/datatable/', cost_center_datatable_ajax, name='cost_center_datatable_ajax'),
    # path('ajax/cost-centers/<int:pk>/toggle-status/', toggle_cost_center_status, name='toggle_cost_center_status'),

    path('ajax/periods/datatable/', fiscal_views.period_datatable_ajax, name='period_datatable_ajax'),
    path('ajax/cost-centers/datatable/', fiscal_views.cost_center_datatable_ajax, name='cost_center_datatable_ajax'),
    path('ajax/cost-centers/<int:pk>/toggle-status/', fiscal_views.toggle_cost_center_status, name='toggle_cost_center_status'),

    # # هذه URLs غير موجودة في ملف urls.py
    # path('templates/', TemplateListView.as_view(), name='template_list'),
    # path('templates/create/', TemplateCreateView.as_view(), name='template_create'),
    # path('templates/<int:pk>/', TemplateDetailView.as_view(), name='template_detail'),
    # path('templates/<int:pk>/update/', TemplateUpdateView.as_view(), name='template_update'),
    # path('templates/<int:pk>/delete/', TemplateDeleteView.as_view(), name='template_delete'),
    # path('templates/<int:pk>/use/', UseTemplateView.as_view(), name='use_template'),
    # path('templates/<int:pk>/lines/', TemplateLineManageView.as_view(), name='template_lines'),


    #  Journal Entry Templates URLs - إضافة جديدة
    path('templates/', template_views.JournalEntryTemplateListView.as_view(), name='template_list'),
    path('templates/create/', template_views.JournalEntryTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', template_views.JournalEntryTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/update/', template_views.JournalEntryTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', template_views.JournalEntryTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/use/', template_views.UseTemplateView.as_view(), name='use_template'),

    # ========== تصدير السنوات المالية والفترات المحاسبية ==========
    path('fiscal-years/export/', report_views.export_fiscal_years, name='export_fiscal_years'),
    path('periods/export/', report_views.export_periods, name='export_periods'),
]
# apps/reports/urls.py
"""
URLs للتقارير
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.reports_dashboard, name='dashboard'),

    # تقارير Core Module
    path('core/items/', views.items_report, name='items_report'),
    path('core/items/excel/', views.export_items_excel, name='export_items_excel'),
    path('core/items/pdf/', views.export_items_pdf, name='export_items_pdf'),

    path('core/partners/', views.partners_report, name='partners_report'),
    path('core/partners/excel/', views.export_partners_excel, name='export_partners_excel'),
    path('core/partners/pdf/', views.export_partners_pdf, name='export_partners_pdf'),

    path('core/warehouses/', views.warehouses_report, name='warehouses_report'),
    path('core/warehouses/excel/', views.export_warehouses_excel, name='export_warehouses_excel'),
    path('core/warehouses/pdf/', views.export_warehouses_pdf, name='export_warehouses_pdf'),

    path('core/pricelists/', views.pricelists_report, name='pricelists_report'),
    path('core/pricelists/excel/', views.export_pricelists_excel, name='export_pricelists_excel'),
    path('core/pricelists/pdf/', views.export_pricelists_pdf, name='export_pricelists_pdf'),

    # تقارير Accounting Module
    path('accounting/chart-of-accounts/', views.chart_of_accounts_report, name='chart_of_accounts_report'),
    path('accounting/chart-of-accounts/excel/', views.export_coa_excel, name='export_coa_excel'),
    path('accounting/chart-of-accounts/pdf/', views.export_coa_pdf, name='export_coa_pdf'),

    path('accounting/trial-balance/', views.trial_balance_report, name='trial_balance_report'),
    path('accounting/trial-balance/excel/', views.export_trial_balance_excel, name='export_trial_balance_excel'),
    path('accounting/trial-balance/pdf/', views.export_trial_balance_pdf, name='export_trial_balance_pdf'),

    path('accounting/general-ledger/', views.general_ledger_report, name='general_ledger_report'),
    path('accounting/general-ledger/excel/', views.export_general_ledger_excel, name='export_general_ledger_excel'),
    path('accounting/general-ledger/pdf/', views.export_general_ledger_pdf, name='export_general_ledger_pdf'),

    path('accounting/journal-entries/', views.journal_entries_report, name='journal_entries_report'),
    path('accounting/journal-entries/excel/', views.export_journal_entries_excel, name='export_journal_entries_excel'),
    path('accounting/journal-entries/pdf/', views.export_journal_entries_pdf, name='export_journal_entries_pdf'),

    path('accounting/receipts-payments/', views.receipts_payments_report, name='receipts_payments_report'),
    path('accounting/receipts-payments/excel/', views.export_receipts_payments_excel, name='export_receipts_payments_excel'),
    path('accounting/receipts-payments/pdf/', views.export_receipts_payments_pdf, name='export_receipts_payments_pdf'),

    path('accounting/income-statement/', views.income_statement_report, name='income_statement_report'),
    path('accounting/income-statement/excel/', views.export_income_statement_excel, name='export_income_statement_excel'),
    path('accounting/income-statement/pdf/', views.export_income_statement_pdf, name='export_income_statement_pdf'),

    path('accounting/balance-sheet/', views.balance_sheet_report, name='balance_sheet_report'),
    path('accounting/balance-sheet/excel/', views.export_balance_sheet_excel, name='export_balance_sheet_excel'),
    path('accounting/balance-sheet/pdf/', views.export_balance_sheet_pdf, name='export_balance_sheet_pdf'),

    # تقارير Inventory Module
    path('inventory/stock/', views.stock_report, name='stock_report'),
    path('inventory/stock/excel/', views.export_stock_excel, name='export_stock_excel'),
    path('inventory/stock/pdf/', views.export_stock_pdf, name='export_stock_pdf'),

    path('inventory/movement/', views.stock_movement_report, name='stock_movement_report'),
    path('inventory/movement/excel/', views.export_stock_movement_excel, name='export_stock_movement_excel'),
    path('inventory/movement/pdf/', views.export_stock_movement_pdf, name='export_stock_movement_pdf'),

    path('inventory/in-out/', views.stock_in_out_report, name='stock_in_out_report'),
    path('inventory/in-out/excel/', views.export_stock_in_out_excel, name='export_stock_in_out_excel'),
    path('inventory/in-out/pdf/', views.export_stock_in_out_pdf, name='export_stock_in_out_pdf'),
]

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
    # Report Views
    report_views
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

    # Ajax endpoints - DataTables
    path('ajax/account-types/', account_type_views.account_type_datatable_ajax, name='account_type_datatable_ajax'),
    path('ajax/accounts/', account_views.account_datatable_ajax, name='account_datatable_ajax'),
    path('ajax/journal-entries/', journal_views.journal_entry_datatable_ajax, name='journal_entry_datatable_ajax'),

    # Ajax endpoints - Account related
    path('ajax/accounts/search/', account_views.account_search_ajax, name='account_search_ajax'),
    path('ajax/accounts/autocomplete/', journal_views.account_autocomplete, name='account_autocomplete'),
    path('ajax/accounts/hierarchy/', account_views.account_hierarchy_ajax, name='account_hierarchy_ajax'),
    path('ajax/accounts/stats/', account_views.account_stats_ajax, name='account_stats_ajax'),

    # Ajax endpoints - Account Type related
    path('ajax/account-types/stats/', account_type_views.account_type_stats_ajax, name='account_type_stats_ajax'),

    # Ajax endpoints - Journal Entry related
    path('ajax/templates/<int:template_id>/lines/', journal_views.get_template_lines, name='get_template_lines'),

    # Journal Entry Actions
    path('ajax/journal-entries/<int:pk>/post/', journal_views.post_journal_entry, name='post_journal_entry'),
    path('ajax/journal-entries/<int:pk>/unpost/', journal_views.unpost_journal_entry, name='unpost_journal_entry'),

    # Export/Import URLs
    path('account-types/export/', report_views.export_account_types, name='export_account_types'),
    path('account-types/import/', report_views.import_account_types, name='import_account_types'),
    path('accounts/export/', report_views.export_accounts, name='export_accounts'),
    path('accounts/import/', report_views.import_accounts, name='import_accounts'),
]
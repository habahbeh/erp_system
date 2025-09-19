# تحديث apps/accounting/urls.py
from django.urls import path
from .views import account_type_views, account_views

app_name = 'accounting'

urlpatterns = [
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
    path('accounts/<int:pk>/update/', account_views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', account_views.AccountDeleteView.as_view(), name='account_delete'),

    # Ajax endpoints
    path('ajax/account-types/', account_type_views.account_type_datatable_ajax, name='account_type_datatable_ajax'),
    path('ajax/accounts/', account_views.account_datatable_ajax, name='account_datatable_ajax'),

    # Export/Import
    path('account-types/export/', account_type_views.export_account_types, name='export_account_types'),
    path('account-types/import/', account_type_views.import_account_types, name='import_account_types'),
    path('accounts/export/', account_views.export_accounts, name='export_accounts'),
    path('accounts/import/', account_views.import_accounts, name='import_accounts'),
]
# apps/accounting/admin.py
from django.contrib import admin
#
# from django.contrib import admin
# from django.utils.translation import gettext_lazy as _
# from .models import (
#     AccountType, Account, FiscalYear, AccountingPeriod,
#     JournalEntry, JournalEntryLine, PaymentVoucher, ReceiptVoucher, CostCenter
# )
#
#
# @admin.register(AccountType)
# class AccountTypeAdmin(admin.ModelAdmin):
#     list_display = ['name', 'code', 'type_category', 'normal_balance']
#     list_filter = ['type_category', 'normal_balance']
#     search_fields = ['name', 'code']
#
#
# @admin.register(Account)
# class AccountAdmin(admin.ModelAdmin):
#     list_display = ['code', 'name', 'account_type', 'parent', 'level', 'company']
#     list_filter = ['company', 'account_type', 'level', 'is_suspended', 'is_cash_account']
#     search_fields = ['code', 'name', 'name_en']
#     # raw_id_fields = ['parent', 'currency']
#
#     fieldsets = (
#         (_('معلومات أساسية'), {
#             'fields': ('code', 'name', 'name_en', 'account_type', 'parent')
#         }),
#         (_('الإعدادات'), {
#             'fields': ('currency', 'nature', 'is_cash_account', 'is_bank_account', 'accept_entries')
#         }),
#         (_('الرصيد الافتتاحي'), {
#             'fields': ('opening_balance', 'opening_balance_date')
#         }),
#         (_('الحالة'), {
#             'fields': ('is_suspended', 'notes')
#         }),
#     )
#
#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # تعديل
#             return ['level']
#         return []
#
#
# @admin.register(FiscalYear)
# class FiscalYearAdmin(admin.ModelAdmin):
#     list_display = ['name', 'code', 'start_date', 'end_date', 'company', 'is_closed']
#     list_filter = ['company', 'is_closed', 'start_date']
#     search_fields = ['name', 'code']
#     date_hierarchy = 'start_date'
#
#
# @admin.register(AccountingPeriod)
# class AccountingPeriodAdmin(admin.ModelAdmin):
#     list_display = ['name', 'fiscal_year', 'start_date', 'end_date', 'is_closed']
#     list_filter = ['fiscal_year', 'is_closed', 'is_adjustment']
#     search_fields = ['name']
#     # raw_id_fields = ['fiscal_year']
#     date_hierarchy = 'start_date'
#
#
# class JournalEntryLineInline(admin.TabularInline):
#     model = JournalEntryLine
#     extra = 2
#     # raw_id_fields = ['account', 'currency', 'cost_center']
#     fields = ['account', 'description', 'debit_amount', 'credit_amount', 'currency', 'cost_center']
#
#
# @admin.register(JournalEntry)
# class JournalEntryAdmin(admin.ModelAdmin):
#     list_display = ['number', 'date', 'description', 'company', 'is_posted', 'created_by']
#     list_filter = ['company', 'entry_type', 'is_posted', 'is_reversed', 'date']
#     search_fields = ['number', 'description', 'reference']
#     # raw_id_fields = ['fiscal_year', 'period', 'posted_by', 'reversed_entry']
#     date_hierarchy = 'date'
#     inlines = [JournalEntryLineInline]
#
#     fieldsets = (
#         (_('معلومات أساسية'), {
#             'fields': ('number', 'date', 'entry_type', 'fiscal_year', 'period')
#         }),
#         (_('التفاصيل'), {
#             'fields': ('description', 'reference')
#         }),
#         (_('الحالة'), {
#             'fields': ('is_posted', 'posted_date', 'posted_by', 'is_reversed', 'reversed_entry')
#         }),
#         (_('ملاحظات'), {
#             'fields': ('notes',)
#         }),
#     )
#
#     def get_readonly_fields(self, request, obj=None):
#         readonly_fields = ['number']
#         if obj and obj.is_posted:
#             readonly_fields.extend(['date', 'entry_type', 'fiscal_year', 'period', 'description', 'reference'])
#         return readonly_fields
#
#     def has_delete_permission(self, request, obj=None):
#         if obj and obj.is_posted:
#             return False
#         return super().has_delete_permission(request, obj)
#
#
# @admin.register(PaymentVoucher)
# class PaymentVoucherAdmin(admin.ModelAdmin):
#     list_display = ['number', 'date', 'beneficiary_name', 'amount', 'payment_method', 'company', 'is_posted']
#     list_filter = ['company', 'payment_method', 'beneficiary_type', 'is_posted', 'date']
#     search_fields = ['number', 'beneficiary_name', 'description', 'check_number']
#     # raw_id_fields = ['currency', 'cash_account', 'expense_account', 'journal_entry']
#     date_hierarchy = 'date'
#
#     fieldsets = (
#         (_('معلومات أساسية'), {
#             'fields': ('number', 'date', 'beneficiary_name', 'beneficiary_type', 'beneficiary_id')
#         }),
#         (_('التفاصيل المالية'), {
#             'fields': ('amount', 'currency', 'exchange_rate', 'payment_method')
#         }),
#         (_('الحسابات'), {
#             'fields': ('cash_account', 'expense_account')
#         }),
#         (_('البيان'), {
#             'fields': ('description',)
#         }),
#         (_('معلومات الشيك'), {
#             'fields': ('check_number', 'check_date', 'bank_name'),
#             'classes': ['collapse']
#         }),
#         (_('المحاسبة'), {
#             'fields': ('journal_entry', 'is_posted')
#         }),
#         (_('ملاحظات'), {
#             'fields': ('notes',)
#         }),
#     )
#
#     def get_readonly_fields(self, request, obj=None):
#         readonly_fields = ['number']
#         if obj and obj.is_posted:
#             readonly_fields.extend(['date', 'amount', 'currency', 'cash_account', 'expense_account'])
#         return readonly_fields
#
#
# @admin.register(ReceiptVoucher)
# class ReceiptVoucherAdmin(admin.ModelAdmin):
#     list_display = ['number', 'date', 'received_from', 'amount', 'receipt_method', 'company', 'is_posted']
#     list_filter = ['company', 'receipt_method', 'payer_type', 'is_posted', 'date']
#     search_fields = ['number', 'received_from', 'description', 'check_number']
#     # raw_id_fields = ['currency', 'cash_account', 'income_account', 'journal_entry']
#     date_hierarchy = 'date'
#
#     fieldsets = (
#         (_('معلومات أساسية'), {
#             'fields': ('number', 'date', 'received_from', 'payer_type', 'payer_id')
#         }),
#         (_('التفاصيل المالية'), {
#             'fields': ('amount', 'currency', 'exchange_rate', 'receipt_method')
#         }),
#         (_('الحسابات'), {
#             'fields': ('cash_account', 'income_account')
#         }),
#         (_('البيان'), {
#             'fields': ('description',)
#         }),
#         (_('معلومات الشيك'), {
#             'fields': ('check_number', 'check_date', 'bank_name'),
#             'classes': ['collapse']
#         }),
#         (_('المحاسبة'), {
#             'fields': ('journal_entry', 'is_posted')
#         }),
#         (_('ملاحظات'), {
#             'fields': ('notes',)
#         }),
#     )
#
#     def get_readonly_fields(self, request, obj=None):
#         readonly_fields = ['number']
#         if obj and obj.is_posted:
#             readonly_fields.extend(['date', 'amount', 'currency', 'cash_account', 'income_account'])
#         return readonly_fields
#
#
# @admin.register(CostCenter)
# class CostCenterAdmin(admin.ModelAdmin):
#     list_display = ['code', 'name', 'parent', 'manager', 'company']
#     list_filter = ['company', 'is_active']
#     search_fields = ['code', 'name']
#     # raw_id_fields = ['parent', 'manager']
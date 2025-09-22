# apps/accounting/admin.py
"""
Django Admin Configuration للنظام المحاسبي
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils.translation import gettext_lazy as _

from .models import (
    AccountType, Account, CostCenter, FiscalYear, AccountingPeriod,
    JournalEntry, JournalEntryLine, JournalEntryTemplate, JournalEntryTemplateLine,
    PaymentVoucher, ReceiptVoucher, AccountBalance, AccountBalanceHistory
)


# ========== Account Type Admin ==========

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type_category', 'normal_balance', 'accounts_count']
    list_filter = ['type_category', 'normal_balance']
    search_fields = ['code', 'name']
    ordering = ['code']

    def accounts_count(self, obj):
        count = obj.accounts.count()
        if count > 0:
            url = reverse('admin:accounting_account_changelist') + f'?account_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} حساب</a>', url, count)
        return '0 حساب'

    accounts_count.short_description = 'عدد الحسابات'


# ========== Account Admin ==========

class AccountInline(admin.TabularInline):
    model = Account
    extra = 0
    fields = ['code', 'name', 'accept_entries', 'is_suspended']
    readonly_fields = ['level']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'account_type', 'parent', 'level',
        'opening_balance', 'current_balance', 'status_badge', 'entry_lines_count'
    ]
    list_filter = [
        'account_type', 'level', 'is_suspended', 'accept_entries',
        'is_cash_account', 'is_bank_account', 'company'
    ]
    search_fields = ['code', 'name', 'name_en']
    ordering = ['code']
    readonly_fields = ['level', 'created_at', 'updated_at', 'created_by']
    raw_id_fields = ['parent']
    inlines = [AccountInline]

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('code', 'name', 'name_en', 'account_type', 'parent')
        }),
        ('الإعدادات المالية', {
            'fields': ('currency', 'nature', 'opening_balance', 'opening_balance_date')
        }),
        ('خصائص الحساب', {
            'fields': ('is_cash_account', 'is_bank_account', 'accept_entries', 'is_suspended')
        }),
        ('معلومات إضافية', {
            'fields': ('notes', 'level'),
            'classes': ('collapse',)
        }),
        ('تواريخ النظام', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        if obj.is_suspended:
            return format_html('<span style="color: red;">●</span> موقوف')
        elif not obj.accept_entries:
            return format_html('<span style="color: orange;">●</span> حساب أب')
        else:
            return format_html('<span style="color: green;">●</span> نشط')

    status_badge.short_description = 'الحالة'

    def current_balance(self, obj):
        balance = obj.get_balance()
        if balance > 0:
            return format_html('<span style="color: blue;">{:,.2f} مدين</span>', balance)
        elif balance < 0:
            return format_html('<span style="color: red;">{:,.2f} دائن</span>', abs(balance))
        else:
            return '0.00'

    current_balance.short_description = 'الرصيد الحالي'

    def entry_lines_count(self, obj):
        try:
            count = obj.journal_entry_lines.count()
            if count > 0:
                return format_html('<a href="/admin/accounting/journalentryline/?account__id__exact={}">{} قيد</a>',
                                   obj.id, count)
            return '0 قيد'
        except:
            return '0 قيد'

    entry_lines_count.short_description = 'عدد القيود'

    actions = ['suspend_accounts', 'activate_accounts']

    def suspend_accounts(self, request, queryset):
        updated = queryset.update(is_suspended=True)
        self.message_user(request, f'تم إيقاف {updated} حساب')

    suspend_accounts.short_description = 'إيقاف الحسابات المختارة'

    def activate_accounts(self, request, queryset):
        updated = queryset.update(is_suspended=False)
        self.message_user(request, f'تم تنشيط {updated} حساب')

    activate_accounts.short_description = 'تنشيط الحسابات المختارة'


# ========== Cost Center Admin ==========

class CostCenterInline(admin.TabularInline):
    model = CostCenter
    extra = 0
    fields = ['code', 'name', 'cost_center_type', 'is_active']


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'cost_center_type', 'parent', 'level', 'manager', 'is_active', 'usage_count']
    list_filter = ['cost_center_type', 'level', 'is_active', 'company']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    raw_id_fields = ['parent', 'manager']
    inlines = [CostCenterInline]

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('code', 'name', 'parent', 'cost_center_type')
        }),
        ('الإدارة', {
            'fields': ('manager', 'description')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        })
    )

    def usage_count(self, obj):
        try:
            count = obj.journal_lines.count()
            return f'{count} استخدام'
        except:
            return '0 استخدام'

    usage_count.short_description = 'الاستخدام'


# ========== Fiscal Year Admin ==========

class AccountingPeriodInline(admin.TabularInline):
    model = AccountingPeriod
    extra = 0
    fields = ['name', 'start_date', 'end_date', 'is_closed', 'is_adjustment']
    readonly_fields = []


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'start_date', 'end_date', 'is_closed', 'periods_count', 'duration_days']
    list_filter = ['is_closed', 'company', 'start_date__year']
    search_fields = ['code', 'name']
    ordering = ['-start_date']
    inlines = [AccountingPeriodInline]

    def periods_count(self, obj):
        count = obj.periods.count()
        return f'{count} فترة'

    periods_count.short_description = 'عدد الفترات'

    def duration_days(self, obj):
        duration = (obj.end_date - obj.start_date).days + 1
        return f'{duration} يوم'

    duration_days.short_description = 'المدة'


# ========== Accounting Period Admin ==========

@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'fiscal_year', 'start_date', 'end_date', 'is_closed', 'is_adjustment', 'entries_count']
    list_filter = ['is_closed', 'is_adjustment', 'fiscal_year', 'company']
    search_fields = ['name', 'fiscal_year__name']
    ordering = ['-fiscal_year__start_date', 'start_date']

    def entries_count(self, obj):
        try:
            count = obj.journal_entries.count()
            return f'{count} قيد'
        except:
            return '0 قيد'

    entries_count.short_description = 'عدد القيود'


# ========== Journal Entry Template Admin ==========

class JournalEntryTemplateLineInline(admin.TabularInline):
    model = JournalEntryTemplateLine
    extra = 1
    fields = ['line_number', 'account', 'description', 'debit_amount', 'credit_amount', 'is_required']
    raw_id_fields = ['account']


@admin.register(JournalEntryTemplate)
class JournalEntryTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'entry_type', 'is_active', 'lines_count', 'total_debit', 'total_credit',
                    'is_balanced']
    list_filter = ['entry_type', 'is_active', 'company']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']
    inlines = [JournalEntryTemplateLineInline]

    fieldsets = (
        ('معلومات القالب', {
            'fields': ('name', 'code', 'description', 'entry_type')
        }),
        ('الإعدادات الافتراضية', {
            'fields': ('default_description', 'default_reference', 'category')
        }),
        ('خيارات العرض', {
            'fields': ('display_order', 'auto_balance', 'is_active')
        })
    )

    def lines_count(self, obj):
        return obj.template_lines.count()

    lines_count.short_description = 'عدد السطور'

    def total_debit(self, obj):
        return f'{obj.get_total_debit():,.2f}'

    total_debit.short_description = 'إجمالي المدين'

    def total_credit(self, obj):
        return f'{obj.get_total_credit():,.2f}'

    total_credit.short_description = 'إجمالي الدائن'

    def is_balanced(self, obj):
        balanced = obj.is_balanced()
        if balanced:
            return format_html('<span style="color: green;">✓ متوازن</span>')
        else:
            return format_html('<span style="color: red;">✗ غير متوازن</span>')

    is_balanced.short_description = 'التوازن'


# ========== Journal Entry Admin ==========

class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 0
    fields = ['line_number', 'account', 'description', 'debit_amount', 'credit_amount', 'cost_center']
    raw_id_fields = ['account', 'cost_center']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'entry_date', 'entry_type', 'description_short',
        'total_debit', 'total_credit', 'status_badge', 'lines_count'
    ]
    list_filter = ['status', 'entry_type', 'fiscal_year', 'company', 'entry_date']
    search_fields = ['number', 'description', 'reference']
    ordering = ['-entry_date', '-number']
    readonly_fields = ['number', 'total_debit', 'total_credit', 'is_balanced', 'posted_date', 'posted_by']
    raw_id_fields = ['fiscal_year', 'period', 'template', 'created_by']
    inlines = [JournalEntryLineInline]
    date_hierarchy = 'entry_date'

    fieldsets = (
        ('معلومات القيد', {
            'fields': ('number', 'entry_date', 'entry_type', 'status')
        }),
        ('التفاصيل', {
            'fields': ('description', 'reference', 'template')
        }),
        ('الفترة المالية', {
            'fields': ('fiscal_year', 'period')
        }),
        ('الإجماليات', {
            'fields': ('total_debit', 'total_credit', 'is_balanced'),
            'classes': ('collapse',)
        }),
        ('معلومات الترحيل', {
            'fields': ('posted_by', 'posted_date'),
            'classes': ('collapse',)
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    description_short.short_description = 'البيان'

    def status_badge(self, obj):
        colors = {
            'draft': 'orange',
            'posted': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'الحالة'

    def lines_count(self, obj):
        return obj.lines.count()

    lines_count.short_description = 'عدد السطور'

    actions = ['post_entries', 'unpost_entries']

    def post_entries(self, request, queryset):
        posted_count = 0
        for entry in queryset:
            if entry.can_post():
                try:
                    entry.post(user=request.user)
                    posted_count += 1
                except Exception as e:
                    self.message_user(request, f'خطأ في ترحيل القيد {entry.number}: {str(e)}', level='ERROR')

        if posted_count > 0:
            self.message_user(request, f'تم ترحيل {posted_count} قيد')

    post_entries.short_description = 'ترحيل القيود المختارة'

    def unpost_entries(self, request, queryset):
        unposted_count = 0
        for entry in queryset:
            if entry.can_unpost():
                try:
                    entry.unpost()
                    unposted_count += 1
                except Exception as e:
                    self.message_user(request, f'خطأ في إلغاء ترحيل القيد {entry.number}: {str(e)}', level='ERROR')

        if unposted_count > 0:
            self.message_user(request, f'تم إلغاء ترحيل {unposted_count} قيد')

    unpost_entries.short_description = 'إلغاء ترحيل القيود المختارة'


# ========== Journal Entry Line Admin ==========

@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = [
        'journal_entry', 'line_number', 'account', 'description_short',
        'debit_amount', 'credit_amount', 'cost_center'
    ]
    list_filter = ['journal_entry__status', 'journal_entry__entry_date', 'account__account_type', 'cost_center']
    search_fields = ['journal_entry__number', 'account__name', 'account__code', 'description']
    ordering = ['journal_entry__entry_date', 'journal_entry__number', 'line_number']
    raw_id_fields = ['journal_entry', 'account', 'cost_center']

    def description_short(self, obj):
        return obj.description[:30] + '...' if len(obj.description) > 30 else obj.description

    description_short.short_description = 'البيان'


# ========== Payment Voucher Admin ==========

@admin.register(PaymentVoucher)
class PaymentVoucherAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'date', 'beneficiary_name', 'amount', 'payment_method',
        'status_badge', 'cash_account', 'posted_status'
    ]
    list_filter = ['status', 'payment_method', 'date', 'company']
    search_fields = ['number', 'beneficiary_name', 'description']
    ordering = ['-date', '-number']
    readonly_fields = ['number', 'posted_date', 'posted_by']
    raw_id_fields = ['cash_account', 'expense_account', 'currency', 'journal_entry']
    date_hierarchy = 'date'

    fieldsets = (
        ('معلومات السند', {
            'fields': ('number', 'date', 'status')
        }),
        ('المستفيد', {
            'fields': ('beneficiary_name', 'beneficiary_type')
        }),
        ('التفاصيل المالية', {
            'fields': ('amount', 'currency', 'exchange_rate')
        }),
        ('الحسابات', {
            'fields': ('cash_account', 'expense_account')
        }),
        ('طريقة الدفع', {
            'fields': ('payment_method', 'check_number', 'check_date', 'bank_name')
        }),
        ('البيان والملاحظات', {
            'fields': ('description', 'notes')
        }),
        ('معلومات الترحيل', {
            'fields': ('journal_entry', 'posted_by', 'posted_date'),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        colors = {
            'draft': 'orange',
            'confirmed': 'blue',
            'posted': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'الحالة'

    def posted_status(self, obj):
        if obj.journal_entry:
            url = reverse('admin:accounting_journalentry_change', args=[obj.journal_entry.id])
            return format_html('<a href="{}">قيد رقم {}</a>', url, obj.journal_entry.number)
        return 'غير مرحل'

    posted_status.short_description = 'القيد المحاسبي'


# ========== Receipt Voucher Admin ==========

@admin.register(ReceiptVoucher)
class ReceiptVoucherAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'date', 'received_from', 'amount', 'receipt_method',
        'status_badge', 'cash_account', 'posted_status'
    ]
    list_filter = ['status', 'receipt_method', 'date', 'company']
    search_fields = ['number', 'received_from', 'description']
    ordering = ['-date', '-number']
    readonly_fields = ['number', 'posted_date', 'posted_by']
    raw_id_fields = ['cash_account', 'income_account', 'currency', 'journal_entry']
    date_hierarchy = 'date'

    fieldsets = (
        ('معلومات السند', {
            'fields': ('number', 'date', 'status')
        }),
        ('الدافع', {
            'fields': ('received_from', 'payer_type')
        }),
        ('التفاصيل المالية', {
            'fields': ('amount', 'currency', 'exchange_rate')
        }),
        ('الحسابات', {
            'fields': ('cash_account', 'income_account')
        }),
        ('طريقة القبض', {
            'fields': ('receipt_method', 'check_number', 'check_date', 'bank_name')
        }),
        ('البيان والملاحظات', {
            'fields': ('description', 'notes')
        }),
        ('معلومات الترحيل', {
            'fields': ('journal_entry', 'posted_by', 'posted_date'),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        colors = {
            'draft': 'orange',
            'confirmed': 'blue',
            'posted': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'الحالة'

    def posted_status(self, obj):
        if obj.journal_entry:
            url = reverse('admin:accounting_journalentry_change', args=[obj.journal_entry.id])
            return format_html('<a href="{}">قيد رقم {}</a>', url, obj.journal_entry.number)
        return 'غير مرحل'

    posted_status.short_description = 'القيد المحاسبي'


# ========== Account Balance Admin ==========

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'fiscal_year', 'period', 'opening_balance_display',
        'period_movement', 'closing_balance_display', 'last_updated'
    ]
    list_filter = ['fiscal_year', 'period', 'company', 'is_balanced']
    search_fields = ['account__name', 'account__code']
    ordering = ['account__code', 'fiscal_year', 'period']
    readonly_fields = [
        'closing_balance_debit', 'closing_balance_credit', 'last_updated', 'is_balanced'
    ]
    raw_id_fields = ['account', 'fiscal_year', 'period']

    def opening_balance_display(self, obj):
        if obj.opening_balance_debit > 0:
            return format_html('<span style="color: blue;">{:,.2f} مدين</span>', obj.opening_balance_debit)
        elif obj.opening_balance_credit > 0:
            return format_html('<span style="color: red;">{:,.2f} دائن</span>', obj.opening_balance_credit)
        else:
            return '0.00'

    opening_balance_display.short_description = 'الرصيد الافتتاحي'

    def period_movement(self, obj):
        return f'مدين: {obj.period_debit:,.2f} | دائن: {obj.period_credit:,.2f}'

    period_movement.short_description = 'حركة الفترة'

    def closing_balance_display(self, obj):
        if obj.closing_balance_debit > 0:
            return format_html('<span style="color: blue;">{:,.2f} مدين</span>', obj.closing_balance_debit)
        elif obj.closing_balance_credit > 0:
            return format_html('<span style="color: red;">{:,.2f} دائن</span>', obj.closing_balance_credit)
        else:
            return '0.00'

    closing_balance_display.short_description = 'الرصيد الختامي'

    actions = ['refresh_balances']

    def refresh_balances(self, request, queryset):
        updated_count = 0
        for balance in queryset:
            balance.refresh_balance()
            updated_count += 1
        self.message_user(request, f'تم تحديث {updated_count} رصيد')

    refresh_balances.short_description = 'تحديث الأرصدة المختارة'


# ========== Account Balance History Admin ==========

@admin.register(AccountBalanceHistory)
class AccountBalanceHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'change_date', 'change_reason', 'old_balance_display',
        'new_balance_display', 'net_change_display', 'changed_by'
    ]
    list_filter = ['change_date', 'change_reason', 'reference_type', 'company']
    search_fields = ['account__name', 'account__code', 'change_reason']
    ordering = ['-change_date']
    readonly_fields = ['change_date', 'net_change']
    raw_id_fields = ['account', 'changed_by']
    date_hierarchy = 'change_date'

    def old_balance_display(self, obj):
        if obj.old_debit_balance > 0:
            return format_html('<span style="color: blue;">{:,.2f} مدين</span>', obj.old_debit_balance)
        elif obj.old_credit_balance > 0:
            return format_html('<span style="color: red;">{:,.2f} دائن</span>', obj.old_credit_balance)
        else:
            return '0.00'

    old_balance_display.short_description = 'الرصيد السابق'

    def new_balance_display(self, obj):
        if obj.new_debit_balance > 0:
            return format_html('<span style="color: blue;">{:,.2f} مدين</span>', obj.new_debit_balance)
        elif obj.new_credit_balance > 0:
            return format_html('<span style="color: red;">{:,.2f} دائن</span>', obj.new_credit_balance)
        else:
            return '0.00'

    new_balance_display.short_description = 'الرصيد الجديد'

    def net_change_display(self, obj):
        net_change = obj.net_change
        if net_change > 0:
            return format_html('<span style="color: green;">+{:,.2f}</span>', net_change)
        elif net_change < 0:
            return format_html('<span style="color: red;">{:,.2f}</span>', net_change)
        else:
            return '0.00'

    net_change_display.short_description = 'صافي التغيير'


# ========== Admin Site Customization ==========

admin.site.site_header = "نظام إدارة الحسابات"
admin.site.site_title = "النظام المحاسبي"
admin.site.index_title = "لوحة تحكم النظام المحاسبي"
# apps/accounting/templatetags/accounting_tags.py
"""
Template Tags للمحاسبة - للاستخدام في القوالب
"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def currency_format(amount):
    """
    تنسيق المبالغ المالية
    Usage: {{ amount|currency_format }}
    """
    if amount is None:
        return "0.00"

    try:
        amount = Decimal(str(amount))
        return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return "0.00"


@register.filter
def accounting_balance_display(amount, account_type='debit'):
    """
    عرض الرصيد المحاسبي مع تحديد نوعه
    Usage: {{ balance|accounting_balance_display:account.account_type.normal_balance }}
    """
    if amount is None or amount == 0:
        return mark_safe('<span class="text-muted">0.00</span>')

    try:
        amount = Decimal(str(amount))
        formatted_amount = f"{abs(amount):,.2f}"

        if amount > 0:
            if account_type == 'debit':
                return mark_safe(f'<span class="text-success">{formatted_amount} مدين</span>')
            else:
                return mark_safe(f'<span class="text-primary">{formatted_amount} دائن</span>')
        else:
            if account_type == 'debit':
                return mark_safe(f'<span class="text-danger">{formatted_amount} دائن</span>')
            else:
                return mark_safe(f'<span class="text-warning">{formatted_amount} مدين</span>')
    except (ValueError, TypeError):
        return mark_safe('<span class="text-muted">0.00</span>')


@register.filter
def journal_entry_status_badge(status):
    """
    عرض حالة القيد اليومي مع badge ملون
    Usage: {{ entry.status|journal_entry_status_badge }}
    """
    badges = {
        'draft': '<span class="badge bg-secondary">مسودة</span>',
        'posted': '<span class="badge bg-success">مرحل</span>',
        'cancelled': '<span class="badge bg-danger">ملغي</span>',
    }
    return mark_safe(badges.get(status, f'<span class="badge bg-light text-dark">{status}</span>'))


@register.filter
def voucher_status_badge(status):
    """
    عرض حالة السند مع badge ملون
    Usage: {{ voucher.status|voucher_status_badge }}
    """
    badges = {
        'draft': '<span class="badge bg-secondary">مسودة</span>',
        'confirmed': '<span class="badge bg-warning">مؤكد</span>',
        'posted': '<span class="badge bg-success">مرحل</span>',
        'cancelled': '<span class="badge bg-danger">ملغي</span>',
    }
    return mark_safe(badges.get(status, f'<span class="badge bg-light text-dark">{status}</span>'))


@register.filter
def account_type_badge(account_type):
    """
    عرض نوع الحساب مع badge ملون
    Usage: {{ account.account_type.type_category|account_type_badge }}
    """
    badges = {
        'assets': '<span class="badge bg-success">أصول</span>',
        'liabilities': '<span class="badge bg-warning">خصوم</span>',
        'equity': '<span class="badge bg-info">حقوق ملكية</span>',
        'revenue': '<span class="badge bg-primary">إيرادات</span>',
        'expenses': '<span class="badge bg-danger">مصروفات</span>',
    }
    return mark_safe(badges.get(account_type, f'<span class="badge bg-light text-dark">{account_type}</span>'))


@register.filter
def fiscal_period_status(period):
    """
    عرض حالة الفترة المالية
    Usage: {{ period|fiscal_period_status }}
    """
    if period.is_closed:
        return mark_safe('<span class="badge bg-secondary">مقفلة</span>')

    # التحقق من أن الفترة في المدى الزمني الحالي
    today = date.today()
    if period.start_date <= today <= period.end_date:
        return mark_safe('<span class="badge bg-success">نشطة</span>')
    elif today < period.start_date:
        return mark_safe('<span class="badge bg-info">مستقبلية</span>')
    else:
        return mark_safe('<span class="badge bg-warning">منتهية</span>')


@register.filter
def days_ago(date_value):
    """
    حساب عدد الأيام منذ تاريخ معين
    Usage: {{ entry.created_at|days_ago }}
    """
    if not date_value:
        return ""

    try:
        if hasattr(date_value, 'date'):
            date_value = date_value.date()

        today = date.today()
        delta = today - date_value

        if delta.days == 0:
            return "اليوم"
        elif delta.days == 1:
            return "أمس"
        elif delta.days < 7:
            return f"منذ {delta.days} أيام"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"منذ {weeks} أسبوع" if weeks == 1 else f"منذ {weeks} أسابيع"
        elif delta.days < 365:
            months = delta.days // 30
            return f"منذ {months} شهر" if months == 1 else f"منذ {months} أشهر"
        else:
            years = delta.days // 365
            return f"منذ {years} سنة" if years == 1 else f"منذ {years} سنوات"
    except (AttributeError, TypeError):
        return ""


@register.inclusion_tag('accounting/tags/balance_summary.html')
def balance_summary(account, as_of_date=None):
    """
    عرض ملخص رصيد الحساب
    Usage: {% balance_summary account %}
    """
    if not as_of_date:
        as_of_date = date.today()

    # هنا يمكن إضافة منطق حساب الرصيد
    balance = account.get_balance(as_of_date) if hasattr(account, 'get_balance') else account.opening_balance

    return {
        'account': account,
        'balance': balance,
        'as_of_date': as_of_date,
    }


@register.inclusion_tag('accounting/tags/quick_stats.html')
def accounting_quick_stats(company):
    """
    عرض إحصائيات سريعة للمحاسبة
    Usage: {% accounting_quick_stats request.current_company %}
    """
    from ..models import Account, JournalEntry, PaymentVoucher, ReceiptVoucher

    try:
        stats = {
            'accounts_count': Account.objects.filter(company=company).count(),
            'journal_entries_count': JournalEntry.objects.filter(company=company).count(),
            'payment_vouchers_count': PaymentVoucher.objects.filter(company=company).count(),
            'receipt_vouchers_count': ReceiptVoucher.objects.filter(company=company).count(),
        }
    except Exception:
        stats = {
            'accounts_count': 0,
            'journal_entries_count': 0,
            'payment_vouchers_count': 0,
            'receipt_vouchers_count': 0,
        }

    return {'stats': stats, 'company': company}


@register.simple_tag
def get_account_balance(account, as_of_date=None):
    """
    الحصول على رصيد الحساب
    Usage: {% get_account_balance account %}
    """
    if not as_of_date:
        as_of_date = date.today()

    # منطق حساب الرصيد - يمكن تطويره أكثر
    if hasattr(account, 'get_balance'):
        return account.get_balance(as_of_date)
    else:
        return account.opening_balance or 0


@register.simple_tag
def percentage_change(old_value, new_value):
    """
    حساب نسبة التغيير بين قيمتين
    Usage: {% percentage_change old_revenue new_revenue %}
    """
    try:
        old_value = Decimal(str(old_value or 0))
        new_value = Decimal(str(new_value or 0))

        if old_value == 0:
            return "∞%" if new_value != 0 else "0%"

        change = ((new_value - old_value) / old_value) * 100
        return f"{change:+.1f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "0%"


@register.simple_tag
def account_hierarchy_display(account, level=0):
    """
    عرض التسلسل الهرمي للحساب
    Usage: {% account_hierarchy_display account %}
    """
    indent = "━━ " * level
    return format_html("{}{}", indent, account.name)


@register.filter
def can_edit_journal_entry(journal_entry, user):
    """
    التحقق من إمكانية تعديل القيد
    Usage: {{ entry|can_edit_journal_entry:request.user }}
    """
    if not hasattr(journal_entry, 'can_edit'):
        return False

    return (journal_entry.can_edit() and
            user.has_perm('accounting.change_journalentry'))


@register.filter
def can_post_journal_entry(journal_entry, user):
    """
    التحقق من إمكانية ترحيل القيد
    Usage: {{ entry|can_post_journal_entry:request.user }}
    """
    if not hasattr(journal_entry, 'can_post'):
        return False

    return (journal_entry.can_post() and
            user.has_perm('accounting.change_journalentry'))


@register.filter
def account_code_display(account):
    """
    عرض رمز واسم الحساب معاً
    Usage: {{ account|account_code_display }}
    """
    return f"{account.code} - {account.name}"


@register.filter
def trim_description(description, max_length=50):
    """
    اقتطاع الوصف إلى طول محدد
    Usage: {{ description|trim_description:30 }}
    """
    if not description:
        return ""

    if len(description) <= max_length:
        return description

    return description[:max_length] + "..."


@register.simple_tag
def aging_analysis_badge(days):
    """
    عرض badge لتحليل الأعمار
    Usage: {% aging_analysis_badge entry.days_since %}
    """
    if days <= 30:
        return mark_safe('<span class="badge bg-success">حالي</span>')
    elif days <= 60:
        return mark_safe('<span class="badge bg-warning">31-60</span>')
    elif days <= 90:
        return mark_safe('<span class="badge bg-orange">61-90</span>')
    elif days <= 120:
        return mark_safe('<span class="badge bg-danger">91-120</span>')
    else:
        return mark_safe('<span class="badge bg-dark">+120</span>')


@register.filter
def multiply(value, arg):
    """
    ضرب قيمتين
    Usage: {{ amount|multiply:exchange_rate }}
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """
    طرح قيمتين
    Usage: {{ total_debit|subtract:total_credit }}
    """
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return 0


@register.simple_tag(takes_context=True)
def active_nav_class(context, url_name, exact=False):
    """
    إضافة class نشط للتنقل
    Usage: {% active_nav_class 'accounting:dashboard' %}
    """
    request = context.get('request')
    if not request:
        return ""

    try:
        current_url = request.resolver_match.url_name

        if exact:
            return "active" if current_url == url_name else ""
        else:
            return "active" if url_name in current_url else ""
    except AttributeError:
        return ""


@register.inclusion_tag('accounting/tags/permissions_check.html', takes_context=True)
def check_accounting_permissions(context, object_type):
    """
    فحص صلاحيات المستخدم للمحاسبة
    Usage: {% check_accounting_permissions 'account' %}
    """
    user = context.get('request', {}).get('user')

    if not user:
        return {'can_view': False, 'can_add': False, 'can_edit': False, 'can_delete': False}

    permissions = {
        'can_view': user.has_perm(f'accounting.view_{object_type}'),
        'can_add': user.has_perm(f'accounting.add_{object_type}'),
        'can_edit': user.has_perm(f'accounting.change_{object_type}'),
        'can_delete': user.has_perm(f'accounting.delete_{object_type}'),
    }

    return permissions
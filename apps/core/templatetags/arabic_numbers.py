# apps/core/templatetags/arabic_numbers.py
"""
Template tags لتحويل الأرقام إلى العربية الهندية
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='arabic_numbers')
def arabic_numbers(value):
    """
    تحويل الأرقام الإنجليزية إلى عربية هندية

    Usage:
        {{ value|arabic_numbers }}
        {{ 12345|arabic_numbers }}  -> ١٢٣٤٥
    """
    if value is None:
        return value

    # Arabic-Indic digits
    arabic_digits = {
        '0': '٠',
        '1': '١',
        '2': '٢',
        '3': '٣',
        '4': '٤',
        '5': '٥',
        '6': '٦',
        '7': '٧',
        '8': '٨',
        '9': '٩',
    }

    # Convert to string
    str_value = str(value)

    # Replace each digit
    for eng, ar in arabic_digits.items():
        str_value = str_value.replace(eng, ar)

    return mark_safe(str_value)


@register.filter(name='format_number_ar')
def format_number_ar(value, decimals=0):
    """
    تنسيق الرقم مع فواصل وتحويله للعربية

    Usage:
        {{ 1234567.89|format_number_ar:2 }}  -> ١،٢٣٤،٥٦٧٫٨٩
    """
    if value is None:
        return value

    try:
        # Convert to float
        num = float(value)

        # Format with commas and decimals
        if decimals == 0:
            formatted = f"{num:,.0f}"
        else:
            formatted = f"{num:,.{decimals}f}"

        # Convert to Arabic numbers
        return arabic_numbers(formatted)
    except (ValueError, TypeError):
        return value


@register.filter(name='currency_ar')
def currency_ar(value, currency_code='JOD'):
    """
    تنسيق المبلغ كعملة مع أرقام عربية

    Usage:
        {{ 1234.5|currency_ar }}  -> ١،٢٣٤٫٥٠٠ دينار
        {{ 1234.5|currency_ar:'USD' }}  -> ١،٢٣٤٫٥٠ دولار
    """
    if value is None:
        return value

    try:
        num = float(value)

        # Format based on currency
        if currency_code == 'JOD':
            formatted = f"{num:,.3f}"
            suffix = " دينار"
        elif currency_code == 'USD':
            formatted = f"{num:,.2f}"
            suffix = " دولار"
        elif currency_code == 'EUR':
            formatted = f"{num:,.2f}"
            suffix = " يورو"
        else:
            formatted = f"{num:,.2f}"
            suffix = f" {currency_code}"

        return arabic_numbers(formatted) + suffix
    except (ValueError, TypeError):
        return value

# apps/core/templatetags/price_filters.py
from django import template
from decimal import Decimal

register = template.Library()



@register.filter(name='get_value')
def get_value(dictionary, key):
    """
    Custom filter to get value from dictionary
    Usage: {{ mydict|get_value:key }}
    """
    if dictionary is None:
        return ''

    # تحويل المفتاح إلى int إذا كان number
    try:
        key = int(key)
    except (ValueError, TypeError):
        key = str(key)

    # محاولة الوصول للقيمة
    value = dictionary.get(key, '')

    # إرجاع القيمة أو فارغ
    return value if value else ''


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Alias for get_value
    """
    return get_value(dictionary, key)




@register.filter(name='dict_value')
def dict_value(dictionary, key):
    """Get value from dictionary - supports int/str keys"""
    if not dictionary:
        return ''

    try:
        # ✅ محاولة الوصول بالمفتاح كما هو أولاً
        if key in dictionary:
            return dictionary[key]

        # ✅ محاولة تحويله لـ int
        int_key = int(key)
        if int_key in dictionary:
            return dictionary[int_key]

        return ''
    except (ValueError, TypeError, KeyError):
        return ''
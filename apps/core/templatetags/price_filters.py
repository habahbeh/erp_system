# apps/core/templatetags/price_filters.py
from django import template

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
    """Get value from dictionary"""
    if not dictionary:
        return ''
    try:
        return dictionary.get(int(key), '')
    except:
        return ''
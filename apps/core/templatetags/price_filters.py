# apps/core/templatetags/price_filters.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None

    if isinstance(dictionary, dict):
        return dictionary.get(key)

    return None
# apps/base_data/templatetags/base_data_tags.py
from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """البحث في القاموس بمفتاح"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None
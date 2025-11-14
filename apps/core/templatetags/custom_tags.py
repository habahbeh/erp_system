# apps/core/templatetags/custom_tags.py
import os
from django import template
from django.apps import apps

register = template.Library()

@register.simple_tag
def custom_permissions_available():
    """التحقق من وجود نموذج CustomPermission"""
    try:
        apps.get_model('core', 'CustomPermission')
        return True
    except LookupError:
        return False


@register.filter(name='basename')
def basename(value):
    """
    Extract the filename from a path
    Usage: {{ file.name|basename }}
    """
    if not value:
        return ''
    return os.path.basename(str(value))
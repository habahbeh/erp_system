# apps/core/templatetags/custom_tags.py
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
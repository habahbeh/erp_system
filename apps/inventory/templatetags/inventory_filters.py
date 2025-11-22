# apps/inventory/templatetags/inventory_filters.py
from django import template

register = template.Library()


@register.filter(name='sum_attr')
def sum_attr(queryset, attribute_name):
    """
    Sum a specific attribute across all objects in a queryset or list.

    Usage: {{ stock_in.lines.all|sum_attr:"total_cost" }}

    Args:
        queryset: A queryset or list of objects
        attribute_name: The name of the attribute to sum

    Returns:
        The sum of all values, or 0 if the queryset is empty
    """
    if not queryset:
        return 0

    try:
        total = sum(getattr(obj, attribute_name, 0) or 0 for obj in queryset)
        return total
    except (TypeError, AttributeError):
        return 0


@register.filter(name='abs')
def absolute_value(value):
    """
    Return the absolute value of a number.

    Usage: {{ batch.days_to_expiry|abs }}

    Args:
        value: A numeric value

    Returns:
        The absolute value of the number
    """
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value

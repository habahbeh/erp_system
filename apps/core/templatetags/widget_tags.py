# apps/core/templatetags/widget_tags.py
"""
Custom Template Tags for Dashboard Widgets
Provides reusable widget components
"""

from django import template
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

register = template.Library()


@register.inclusion_tag('widgets/stat_card.html')
def stat_card(title, value, icon, color='primary', subtitle='', trend=None, url='#'):
    """
    Render a statistics card widget

    Args:
        title: Card title
        value: Main value to display
        icon: Font Awesome icon class
        color: Bootstrap color (primary, success, info, warning, danger)
        subtitle: Optional subtitle text
        trend: Optional trend data {'value': 5, 'direction': 'up'}
        url: Optional link URL
    """
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'subtitle': subtitle,
        'trend': trend,
        'url': url
    }


@register.inclusion_tag('widgets/mini_chart_card.html')
def mini_chart_card(title, chart_id, chart_type='line', data=None, color='primary', height=150):
    """
    Render a mini chart card widget

    Args:
        title: Card title
        chart_id: Unique ID for the chart canvas
        chart_type: Chart type (line, bar, doughnut)
        data: Chart data object
        color: Chart color
        height: Chart height in pixels
    """
    return {
        'title': title,
        'chart_id': chart_id,
        'chart_type': chart_type,
        'data': data,
        'color': color,
        'height': height
    }


@register.inclusion_tag('widgets/activity_feed.html')
def activity_feed(activities, title='آخر النشاطات', max_items=5):
    """
    Render an activity feed widget

    Args:
        activities: List of activity items
        title: Widget title
        max_items: Maximum number of items to display
    """
    return {
        'activities': activities[:max_items],
        'title': title,
        'has_more': len(activities) > max_items
    }


@register.inclusion_tag('widgets/quick_actions.html')
def quick_actions(actions, title='إجراءات سريعة'):
    """
    Render a quick actions widget

    Args:
        actions: List of action items with 'label', 'icon', 'url', 'color'
        title: Widget title
    """
    return {
        'actions': actions,
        'title': title
    }


@register.inclusion_tag('widgets/progress_card.html')
def progress_card(title, current, total, color='success', show_percentage=True):
    """
    Render a progress card widget

    Args:
        title: Card title
        current: Current value
        total: Total value
        color: Progress bar color
        show_percentage: Show percentage label
    """
    percentage = int((current / total * 100)) if total > 0 else 0

    return {
        'title': title,
        'current': current,
        'total': total,
        'percentage': percentage,
        'color': color,
        'show_percentage': show_percentage
    }


@register.inclusion_tag('widgets/list_widget.html')
def list_widget(title, items, icon='fa-list', color='primary', show_more_url='#'):
    """
    Render a list widget

    Args:
        title: Widget title
        items: List of items to display
        icon: Title icon
        color: Widget color
        show_more_url: URL for "show more" link
    """
    return {
        'title': title,
        'items': items,
        'icon': icon,
        'color': color,
        'show_more_url': show_more_url
    }


@register.inclusion_tag('widgets/alert_widget.html')
def alert_widget(title, message, alert_type='info', dismissible=True):
    """
    Render an alert widget

    Args:
        title: Alert title
        message: Alert message
        alert_type: Alert type (success, info, warning, danger)
        dismissible: Allow dismissing the alert
    """
    return {
        'title': title,
        'message': message,
        'alert_type': alert_type,
        'dismissible': dismissible
    }


@register.simple_tag
def widget_container(size='col-md-6', extra_class=''):
    """
    Generate widget container div opening tag

    Args:
        size: Bootstrap column size
        extra_class: Additional CSS classes
    """
    return mark_safe(f'<div class="{size} {extra_class} mb-4">')


@register.simple_tag
def widget_container_end():
    """
    Generate widget container div closing tag
    """
    return mark_safe('</div>')


@register.filter
def format_trend(value):
    """
    Format trend value with + or - sign

    Args:
        value: Numeric value
    """
    if value > 0:
        return f'+{value}'
    return str(value)


@register.filter
def trend_color(value):
    """
    Get color class based on trend direction

    Args:
        value: Numeric value
    """
    if value > 0:
        return 'text-success'
    elif value < 0:
        return 'text-danger'
    return 'text-muted'


@register.filter
def trend_icon(value):
    """
    Get icon class based on trend direction

    Args:
        value: Numeric value
    """
    if value > 0:
        return 'fa-arrow-up'
    elif value < 0:
        return 'fa-arrow-down'
    return 'fa-minus'


@register.filter
def short_number(value):
    """
    Format large numbers with K, M suffixes

    Args:
        value: Numeric value
    """
    try:
        num = float(value)
        if num >= 1000000:
            return f'{num/1000000:.1f}M'
        elif num >= 1000:
            return f'{num/1000:.1f}K'
        return str(int(num))
    except (ValueError, TypeError):
        return value


@register.filter
def time_ago(value):
    """
    Convert datetime to "time ago" format

    Args:
        value: Datetime object
    """
    if not value:
        return ''

    now = datetime.now()
    if value.tzinfo:
        from django.utils import timezone
        now = timezone.now()

    diff = now - value

    if diff.days > 365:
        return f'منذ {diff.days // 365} سنة'
    elif diff.days > 30:
        return f'منذ {diff.days // 30} شهر'
    elif diff.days > 0:
        return f'منذ {diff.days} يوم'
    elif diff.seconds > 3600:
        return f'منذ {diff.seconds // 3600} ساعة'
    elif diff.seconds > 60:
        return f'منذ {diff.seconds // 60} دقيقة'
    else:
        return 'الآن'

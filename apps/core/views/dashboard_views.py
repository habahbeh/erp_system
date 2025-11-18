# apps/core/views/dashboard_views.py
"""
Enhanced Dashboard Views with Widgets
Uses custom widget template tags for reusable components
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.core.models import (
    Item, PriceList, PriceListItem, PricingRule,
    BusinessPartner, ItemCategory, AuditLog
)


class EnhancedPricingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Enhanced pricing dashboard using widget system

    Features:
    - Statistics cards with trends
    - Quick action buttons
    - Mini charts for key metrics
    - Recent activity feed
    - Progress indicators
    - Alert notifications
    """
    template_name = 'core/pricing/enhanced_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # Statistics Cards
        context['stat_cards'] = self._get_stat_cards(company)

        # Quick Actions
        context['quick_actions'] = self._get_quick_actions()

        # Recent Activities
        context['recent_activities'] = self._get_recent_activities(company)

        # Progress Indicators
        context['progress_cards'] = self._get_progress_cards(company)

        # List Widgets
        context['top_items'] = self._get_top_items(company)
        context['recent_price_changes'] = self._get_recent_price_changes(company)

        # Alert Widgets
        context['alerts'] = self._get_alerts(company)

        # Mini Chart Data
        context['chart_data'] = self._get_chart_data(company)

        return context

    def _get_stat_cards(self, company):
        """Get statistics cards data"""
        # Total Items
        total_items = Item.objects.filter(company=company, is_active=True).count()

        # Total Price Lists
        total_pricelists = PriceList.objects.filter(company=company, is_active=True).count()

        # Total Pricing Rules
        total_rules = PricingRule.objects.filter(company=company, is_active=True).count()
        active_rules = PricingRule.objects.filter(
            company=company,
            is_active=True,
            valid_from__lte=timezone.now().date(),
            valid_to__gte=timezone.now().date()
        ).count()

        # Total Price Items
        total_price_items = PriceListItem.objects.filter(
            price_list__company=company,
            is_active=True
        ).count()

        # Average Price
        avg_price = PriceListItem.objects.filter(
            price_list__company=company,
            is_active=True
        ).aggregate(Avg('price'))['price__avg'] or Decimal('0')

        return [
            {
                'title': 'إجمالي الأصناف',
                'value': total_items,
                'icon': 'fa-box',
                'color': 'primary',
                'subtitle': 'صنف نشط',
                'trend': {'value': 5, 'direction': 'up'},
                'url': '#'
            },
            {
                'title': 'قوائم الأسعار',
                'value': total_pricelists,
                'icon': 'fa-list-alt',
                'color': 'success',
                'subtitle': 'قائمة نشطة',
                'url': '#'
            },
            {
                'title': 'قواعد التسعير',
                'value': f'{active_rules}/{total_rules}',
                'icon': 'fa-sliders-h',
                'color': 'info',
                'subtitle': 'قاعدة نشطة',
                'url': '#'
            },
            {
                'title': 'متوسط السعر',
                'value': f'{avg_price:,.2f}',
                'icon': 'fa-dollar-sign',
                'color': 'warning',
                'subtitle': f'من {total_price_items} سعر',
                'trend': {'value': 3, 'direction': 'up'},
                'url': '#'
            }
        ]

    def _get_quick_actions(self):
        """Get quick actions data"""
        from django.urls import reverse

        return [
            {
                'label': 'سعر جديد',
                'icon': 'fa-plus',
                'url': reverse('core:pricelist_item_create'),
                'color': 'primary'
            },
            {
                'label': 'قاعدة تسعير',
                'icon': 'fa-sliders-h',
                'url': reverse('core:pricing_rule_create'),
                'color': 'success'
            },
            {
                'label': 'قائمة أسعار',
                'icon': 'fa-list-alt',
                'url': reverse('core:pricelist_create'),
                'color': 'info'
            },
            {
                'label': 'محرر الأسعار',
                'icon': 'fa-pen',
                'url': reverse('core:inline_price_editor'),
                'color': 'warning'
            },
            {
                'label': 'تقرير الأسعار',
                'icon': 'fa-chart-line',
                'url': reverse('core:pricing_dashboard'),
                'color': 'danger'
            },
            {
                'label': 'تصدير Excel',
                'icon': 'fa-file-excel',
                'url': '#',
                'color': 'secondary'
            }
        ]

    def _get_recent_activities(self, company):
        """Get recent activities from audit log"""
        activities = []

        # Get recent audit logs
        recent_logs = AuditLog.objects.filter(
            company=company,
            model_name__in=['PriceListItem', 'PricingRule', 'PriceList']
        ).order_by('-created_at')[:10]

        for log in recent_logs:
            icon = 'fa-plus' if log.action == 'CREATE' else 'fa-edit' if log.action == 'UPDATE' else 'fa-trash'
            color = 'success' if log.action == 'CREATE' else 'info' if log.action == 'UPDATE' else 'danger'

            activities.append({
                'title': f'{log.get_action_display()} - {log.model_name}',
                'description': f'بواسطة {log.user.get_full_name() or log.user.username}',
                'time': log.created_at,
                'icon': icon,
                'color': color
            })

        return activities

    def _get_progress_cards(self, company):
        """Get progress indicators"""
        # Items with prices
        total_items = Item.objects.filter(company=company, is_active=True).count()
        items_with_prices = Item.objects.filter(
            company=company,
            is_active=True,
            price_list_items__isnull=False
        ).distinct().count()

        # Active rules vs total rules
        total_rules = PricingRule.objects.filter(company=company, is_active=True).count()
        active_rules = PricingRule.objects.filter(
            company=company,
            is_active=True,
            valid_from__lte=timezone.now().date(),
            valid_to__gte=timezone.now().date()
        ).count()

        return [
            {
                'title': 'الأصناف المسعرة',
                'current': items_with_prices,
                'total': total_items,
                'color': 'success',
                'show_percentage': True
            },
            {
                'title': 'قواعد التسعير النشطة',
                'current': active_rules,
                'total': total_rules,
                'color': 'info',
                'show_percentage': True
            }
        ]

    def _get_top_items(self, company):
        """Get top items by price"""
        top_items = PriceListItem.objects.filter(
            price_list__company=company,
            is_active=True
        ).select_related('item', 'price_list').order_by('-price')[:5]

        items = []
        for price_item in top_items:
            items.append({
                'title': price_item.item.name,
                'subtitle': price_item.price_list.name,
                'value': f'{price_item.price:,.2f}',
                'icon': 'fa-box',
                'color': 'primary',
                'badge_color': 'success',
                'url': '#'
            })

        return items

    def _get_recent_price_changes(self, company):
        """Get recent price changes from audit log"""
        changes = AuditLog.objects.filter(
            company=company,
            model_name='PriceListItem',
            action='UPDATE'
        ).order_by('-created_at')[:5]

        items = []
        for change in changes:
            items.append({
                'title': f'تغيير سعر',
                'subtitle': f'{change.user.get_full_name() or change.user.username}',
                'value': change.created_at.strftime('%Y-%m-%d'),
                'icon': 'fa-edit',
                'color': 'info',
                'badge_color': 'warning'
            })

        return items

    def _get_alerts(self, company):
        """Get system alerts"""
        alerts = []

        # Check for items without prices
        items_without_prices = Item.objects.filter(
            company=company,
            is_active=True,
            price_list_items__isnull=True
        ).count()

        if items_without_prices > 0:
            alerts.append({
                'title': 'تنبيه',
                'message': f'يوجد {items_without_prices} صنف بدون أسعار. يرجى إضافة الأسعار.',
                'alert_type': 'warning',
                'dismissible': True
            })

        # Check for expired pricing rules
        expired_rules = PricingRule.objects.filter(
            company=company,
            is_active=True,
            valid_to__lt=timezone.now().date()
        ).count()

        if expired_rules > 0:
            alerts.append({
                'title': 'قواعد تسعير منتهية',
                'message': f'يوجد {expired_rules} قاعدة تسعير منتهية الصلاحية. يرجى المراجعة.',
                'alert_type': 'info',
                'dismissible': True
            })

        return alerts

    def _get_chart_data(self, company):
        """Get chart data for mini charts"""
        import json

        # Price distribution by category
        categories = ItemCategory.objects.filter(
            company=company,
            level=1,
            is_active=True
        )[:5]

        category_labels = [cat.name for cat in categories]
        category_counts = [
            PriceListItem.objects.filter(
                item__category=cat,
                is_active=True
            ).count()
            for cat in categories
        ]

        price_distribution_data = {
            'labels': category_labels,
            'datasets': [{
                'label': 'عدد الأسعار',
                'data': category_counts,
                'backgroundColor': [
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                'borderColor': [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                'borderWidth': 1
            }]
        }

        return {
            'price_distribution': json.dumps(price_distribution_data)
        }


class MainDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main system dashboard with overview widgets
    """
    template_name = 'core/dashboard/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company
        branch = self.request.current_branch

        # Statistics
        context['stat_cards'] = [
            {
                'title': 'إجمالي الأصناف',
                'value': Item.objects.filter(company=company, is_active=True).count(),
                'icon': 'fa-box',
                'color': 'primary',
                'url': '#'
            },
            {
                'title': 'الشركاء',
                'value': BusinessPartner.objects.filter(company=company, is_active=True).count(),
                'icon': 'fa-handshake',
                'color': 'success',
                'url': '#'
            },
            {
                'title': 'قوائم الأسعار',
                'value': PriceList.objects.filter(company=company, is_active=True).count(),
                'icon': 'fa-list-alt',
                'color': 'info',
                'url': '#'
            },
            {
                'title': 'الفرع الحالي',
                'value': branch.name if branch else 'غير محدد',
                'icon': 'fa-building',
                'color': 'warning',
                'url': '#'
            }
        ]

        # Quick actions
        context['quick_actions'] = [
            {
                'label': 'صنف جديد',
                'icon': 'fa-plus',
                'url': '#',
                'color': 'primary'
            },
            {
                'label': 'شريك جديد',
                'icon': 'fa-user-plus',
                'url': '#',
                'color': 'success'
            },
            {
                'label': 'قائمة أسعار',
                'icon': 'fa-list-alt',
                'url': '#',
                'color': 'info'
            },
            {
                'label': 'التقارير',
                'icon': 'fa-chart-bar',
                'url': '#',
                'color': 'danger'
            }
        ]

        # Recent activities
        context['recent_activities'] = []
        recent_logs = AuditLog.objects.filter(
            company=company
        ).order_by('-created_at')[:10]

        for log in recent_logs:
            icon = 'fa-plus' if log.action == 'CREATE' else 'fa-edit' if log.action == 'UPDATE' else 'fa-trash'
            color = 'success' if log.action == 'CREATE' else 'info' if log.action == 'UPDATE' else 'danger'

            context['recent_activities'].append({
                'title': f'{log.get_action_display()} - {log.model_name}',
                'description': f'بواسطة {log.user.get_full_name() or log.user.username}',
                'time': log.created_at,
                'icon': icon,
                'color': color
            })

        return context

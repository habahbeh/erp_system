# apps/assets/views/dashboard_views.py
"""
لوحة التحكم الرئيسية للأصول
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.urls import reverse
from decimal import Decimal
import datetime

from ..models import (
    Asset, AssetTransaction, AssetMaintenance,
    MaintenanceSchedule, AssetDepreciation
)
from apps.core.mixins import CompanyMixin


class AssetsDashboardView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم الأصول الثابتة"""

    template_name = 'assets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        today = datetime.date.today()

        # إحصائيات الأصول
        assets_stats = self._get_assets_statistics(company)

        # إحصائيات الصيانة
        maintenance_stats = self._get_maintenance_statistics(company, today)

        # الأصول حسب الفئة
        assets_by_category = self._get_assets_by_category(company)

        # الأصول حسب الحالة
        assets_by_status = self._get_assets_by_status(company)

        # الصيانة القريبة (خلال 30 يوم)
        upcoming_maintenance = self._get_upcoming_maintenance(company, today)

        # الصيانة المتأخرة
        overdue_maintenance = self._get_overdue_maintenance(company, today)

        # الأصول القريبة من نهاية العمر (أقل من 6 أشهر)
        near_end_life_assets = self._get_near_end_life_assets(company)

        # الضمانات المنتهية قريباً (خلال 30 يوم)
        expiring_warranties = self._get_expiring_warranties(company, today)

        # آخر العمليات
        recent_transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related('asset', 'branch').order_by('-transaction_date')[:5]

        context.update({
            'title': 'لوحة تحكم الأصول الثابتة',
            'assets_stats': assets_stats,
            'maintenance_stats': maintenance_stats,
            'assets_by_category': assets_by_category,
            'assets_by_status': assets_by_status,
            'upcoming_maintenance': upcoming_maintenance,
            'overdue_maintenance': overdue_maintenance,
            'near_end_life_assets': near_end_life_assets,
            'expiring_warranties': expiring_warranties,
            'recent_transactions': recent_transactions,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': ''}
            ],
        })

        return context

    def _get_assets_statistics(self, company):
        """إحصائيات الأصول"""
        assets = Asset.objects.filter(company=company)

        total_assets = assets.count()
        active_assets = assets.filter(status='active').count()

        # القيم المالية
        totals = assets.aggregate(
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        )

        return {
            'total_count': total_assets,
            'active_count': active_assets,
            'inactive_count': assets.filter(status='inactive').count(),
            'under_maintenance_count': assets.filter(status='under_maintenance').count(),
            'disposed_count': assets.filter(status='disposed').count(),
            'sold_count': assets.filter(status='sold').count(),
            'total_cost': totals['total_cost'] or Decimal('0'),
            'total_depreciation': totals['total_depreciation'] or Decimal('0'),
            'total_book_value': totals['total_book_value'] or Decimal('0'),
        }

    def _get_maintenance_statistics(self, company, today):
        """إحصائيات الصيانة"""
        maintenances = AssetMaintenance.objects.filter(company=company)

        # صيانة هذا الشهر
        this_month = maintenances.filter(
            scheduled_date__year=today.year,
            scheduled_date__month=today.month
        )

        # التكاليف
        this_month_cost = this_month.aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')

        return {
            'total_count': maintenances.count(),
            'scheduled_count': maintenances.filter(status='scheduled').count(),
            'in_progress_count': maintenances.filter(status='in_progress').count(),
            'completed_count': maintenances.filter(status='completed').count(),
            'this_month_count': this_month.count(),
            'this_month_cost': this_month_cost,
        }

    def _get_assets_by_category(self, company):
        """الأصول حسب الفئة"""
        categories = Asset.objects.filter(
            company=company,
            is_active=True
        ).values(
            'category__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('original_cost'),
            total_book_value=Sum('book_value')
        ).order_by('-total_book_value')[:10]

        return list(categories)

    def _get_assets_by_status(self, company):
        """الأصول حسب الحالة"""
        statuses = Asset.objects.filter(
            company=company
        ).values('status').annotate(
            count=Count('id')
        )

        return list(statuses)

    def _get_upcoming_maintenance(self, company, today):
        """الصيانة القريبة"""
        next_30_days = today + datetime.timedelta(days=30)

        return AssetMaintenance.objects.filter(
            company=company,
            status='scheduled',
            scheduled_date__gte=today,
            scheduled_date__lte=next_30_days
        ).select_related('asset', 'maintenance_type').order_by('scheduled_date')[:10]

    def _get_overdue_maintenance(self, company, today):
        """الصيانة المتأخرة"""
        return AssetMaintenance.objects.filter(
            company=company,
            status='scheduled',
            scheduled_date__lt=today
        ).select_related('asset', 'maintenance_type').order_by('scheduled_date')[:10]

    def _get_near_end_life_assets(self, company):
        """الأصول القريبة من نهاية العمر"""
        today = datetime.date.today()
        six_months_later = today + datetime.timedelta(days=180)

        assets = []
        for asset in Asset.objects.filter(company=company, status='active'):
            end_date = asset.depreciation_start_date + datetime.timedelta(
                days=asset.useful_life_months * 30
            )
            if today <= end_date <= six_months_later:
                assets.append({
                    'asset': asset,
                    'end_date': end_date,
                    'days_remaining': (end_date - today).days
                })

        return sorted(assets, key=lambda x: x['days_remaining'])[:10]

    def _get_expiring_warranties(self, company, today):
        """الضمانات المنتهية قريباً"""
        next_30_days = today + datetime.timedelta(days=30)

        return Asset.objects.filter(
            company=company,
            status='active',
            warranty_end_date__gte=today,
            warranty_end_date__lte=next_30_days
        ).order_by('warranty_end_date')[:10]
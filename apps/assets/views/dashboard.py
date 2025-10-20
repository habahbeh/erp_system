# apps/assets/views/dashboard.py
"""
لوحة تحكم نظام الأصول الثابتة
- إحصائيات عامة
- تنبيهات الصيانة
- تنبيهات الإهلاك
- تنبيهات الضمان والتأمين
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import datetime

from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message

from ..models import (
    Asset, AssetCategory, AssetDepreciation,
    AssetMaintenance, MaintenanceSchedule,
    AssetInsurance, InsuranceClaim,
    PhysicalCount, AssetTransaction
)


class AssetDashboardView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم الأصول الثابتة"""

    template_name = 'assets/dashboard.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الإحصائيات الأساسية
        stats = self.get_basic_stats()

        # الإحصائيات المالية
        financial_stats = self.get_financial_stats()

        # تنبيهات الصيانة القادمة
        maintenance_alerts = self.get_maintenance_alerts()

        # تنبيهات الإهلاك
        depreciation_alerts = self.get_depreciation_alerts()

        # تنبيهات الضمان والتأمين
        expiry_alerts = self.get_expiry_alerts()

        # الأصول المضافة حديثاً
        recent_assets = self.get_recent_assets()

        # إحصائيات حسب الفئة
        category_stats = self.get_category_stats()

        context.update({
            'title': _('لوحة تحكم الأصول الثابتة'),
            'stats': stats,
            'financial_stats': financial_stats,
            'maintenance_alerts': maintenance_alerts,
            'depreciation_alerts': depreciation_alerts,
            'expiry_alerts': expiry_alerts,
            'recent_assets': recent_assets,
            'category_stats': category_stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': ''},
            ]
        })

        return context

    def get_basic_stats(self):
        """الإحصائيات الأساسية"""
        total_assets = Asset.objects.filter(
            company=self.request.current_company
        ).count()

        active_assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).count()

        under_maintenance = Asset.objects.filter(
            company=self.request.current_company,
            status='under_maintenance'
        ).count()

        disposed = Asset.objects.filter(
            company=self.request.current_company,
            status__in=['disposed', 'sold']
        ).count()

        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'under_maintenance': under_maintenance,
            'disposed': disposed,
            'active_percentage': (active_assets / total_assets * 100) if total_assets > 0 else 0
        }

    def get_financial_stats(self):
        """الإحصائيات المالية"""
        financial = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).aggregate(
            total_cost=Coalesce(Sum('original_cost'), Decimal('0')),
            total_depreciation=Coalesce(Sum('accumulated_depreciation'), Decimal('0')),
            total_book_value=Coalesce(Sum('book_value'), Decimal('0'))
        )

        return {
            'total_cost': financial['total_cost'],
            'total_depreciation': financial['total_depreciation'],
            'total_book_value': financial['total_book_value'],
            'depreciation_percentage': (
                    financial['total_depreciation'] / financial['total_cost'] * 100
            ) if financial['total_cost'] > 0 else 0
        }

    def get_maintenance_alerts(self):
        """تنبيهات الصيانة المستحقة خلال 30 يوم"""
        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=30)

        schedules = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True,
            next_maintenance_date__lte=due_date,
            next_maintenance_date__gte=today
        ).select_related('asset', 'maintenance_type').order_by('next_maintenance_date')[:5]

        return schedules

    def get_depreciation_alerts(self):
        """الأصول القريبة من الإهلاك الكامل (>90%)"""
        assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).annotate(
            depreciation_percentage=Case(
                When(original_cost=0, then=0),
                default=(F('accumulated_depreciation') * 100.0) / F('original_cost'),
                output_field=DecimalField()
            )
        ).filter(
            depreciation_percentage__gte=90,
            depreciation_percentage__lt=100
        ).order_by('-depreciation_percentage')[:5]

        return assets

    def get_expiry_alerts(self):
        """تنبيهات انتهاء الضمان والتأمين"""
        today = datetime.date.today()
        expiry_date = today + datetime.timedelta(days=30)

        # الضمانات المنتهية
        warranty_expiring = Asset.objects.filter(
            company=self.request.current_company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__lte=expiry_date,
            warranty_end_date__gte=today
        ).count()

        # التأمينات المنتهية
        insurance_expiring = AssetInsurance.objects.filter(
            company=self.request.current_company,
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).count()

        return {
            'warranty_expiring': warranty_expiring,
            'insurance_expiring': insurance_expiring
        }

    def get_recent_assets(self):
        """الأصول المضافة خلال آخر 30 يوم"""
        thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)

        return Asset.objects.filter(
            company=self.request.current_company,
            created_at__gte=thirty_days_ago
        ).select_related('category').order_by('-created_at')[:5]

    def get_category_stats(self):
        """إحصائيات حسب الفئة"""
        return AssetCategory.objects.filter(
            company=self.request.current_company
        ).annotate(
            asset_count=Count('assets', filter=Q(assets__status='active')),
            total_value=Coalesce(Sum('assets__book_value', filter=Q(assets__status='active')), Decimal('0'))
        ).filter(asset_count__gt=0).order_by('-total_value')[:10]


# ==================== Ajax Endpoints ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API للحصول على إحصائيات Dashboard محدثة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    # إحصائيات أساسية
    stats = {
        'total_assets': Asset.objects.filter(company=request.current_company).count(),
        'active_assets': Asset.objects.filter(company=request.current_company, status='active').count(),
        'total_book_value': float(
            Asset.objects.filter(
                company=request.current_company,
                status='active'
            ).aggregate(total=Coalesce(Sum('book_value'), 0))['total']
        ),
        'maintenance_due': MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lte=datetime.date.today() + datetime.timedelta(days=7)
        ).count()
    }

    return JsonResponse(stats)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_alerts_api(request):
    """API لتنبيهات الإهلاك"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    # الأصول القريبة من الإهلاك الكامل
    alerts = Asset.objects.filter(
        company=request.current_company,
        status='active'
    ).annotate(
        depreciation_percentage=(F('accumulated_depreciation') * 100.0) / F('original_cost')
    ).filter(
        depreciation_percentage__gte=90
    ).values(
        'id', 'asset_number', 'name', 'depreciation_percentage'
    )[:10]

    return JsonResponse({'alerts': list(alerts)})


@login_required
@permission_required_with_message('assets.view_assetmaintenance')
@require_http_methods(["GET"])
def maintenance_alerts_api(request):
    """API لتنبيهات الصيانة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=int(request.GET.get('days', 30)))

    schedules = MaintenanceSchedule.objects.filter(
        company=request.current_company,
        is_active=True,
        next_maintenance_date__lte=due_date,
        next_maintenance_date__gte=today
    ).select_related('asset', 'maintenance_type').values(
        'id',
        'asset__asset_number',
        'asset__name',
        'maintenance_type__name',
        'next_maintenance_date',
        'estimated_cost'
    ).order_by('next_maintenance_date')

    return JsonResponse({'maintenance_alerts': list(schedules)})
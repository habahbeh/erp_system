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
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, timedelta

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

        # المعاملات الأخيرة
        recent_transactions = self.get_recent_transactions()

        context.update({
            'title': _('لوحة تحكم الأصول الثابتة'),
            'stats': stats,
            'financial_stats': financial_stats,
            'maintenance_alerts': maintenance_alerts,
            'depreciation_alerts': depreciation_alerts,
            'expiry_alerts': expiry_alerts,
            'recent_assets': recent_assets,
            'category_stats': category_stats,
            'recent_transactions': recent_transactions,
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

        inactive = Asset.objects.filter(
            company=self.request.current_company,
            status='inactive'
        ).count()

        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'under_maintenance': under_maintenance,
            'disposed': disposed,
            'inactive': inactive,
            'active_percentage': round((active_assets / total_assets * 100), 2) if total_assets > 0 else 0
        }

    def get_financial_stats(self):
        """الإحصائيات المالية"""
        financial = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).aggregate(
            total_cost=Coalesce(Sum('acquisition_cost'), Decimal('0')),
            total_depreciation=Coalesce(Sum('accumulated_depreciation'), Decimal('0')),
            total_book_value=Coalesce(Sum('book_value'), Decimal('0'))
        )

        depreciation_percentage = 0
        if financial['total_cost'] > 0:
            depreciation_percentage = round(
                float(financial['total_depreciation'] / financial['total_cost'] * 100),
                2
            )

        return {
            'total_cost': financial['total_cost'],
            'total_depreciation': financial['total_depreciation'],
            'total_book_value': financial['total_book_value'],
            'depreciation_percentage': depreciation_percentage
        }

    def get_maintenance_alerts(self):
        """تنبيهات الصيانة المستحقة خلال 30 يوم"""
        today = date.today()
        due_date = today + timedelta(days=30)

        # الصيانة المتأخرة
        overdue = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True,
            next_maintenance_date__lt=today
        ).count()

        # الصيانة القادمة
        upcoming = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True,
            next_maintenance_date__gte=today,
            next_maintenance_date__lte=due_date
        ).select_related('asset', 'maintenance_type').order_by('next_maintenance_date')[:5]

        return {
            'overdue_count': overdue,
            'upcoming_schedules': upcoming
        }

    def get_depreciation_alerts(self):
        """الأصول القريبة من الإهلاك الكامل (>90%)"""
        assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active',
            acquisition_cost__gt=0
        ).annotate(
            depreciation_percentage=Case(
                When(acquisition_cost=0, then=Value(0)),
                default=(F('accumulated_depreciation') * 100.0) / F('acquisition_cost'),
                output_field=DecimalField(max_digits=5, decimal_places=2)
            )
        ).filter(
            depreciation_percentage__gte=90,
            depreciation_percentage__lt=100
        ).select_related('category').order_by('-depreciation_percentage')[:5]

        return assets

    def get_expiry_alerts(self):
        """تنبيهات انتهاء الضمان والتأمين"""
        today = date.today()
        expiry_date = today + timedelta(days=60)

        # الضمانات المنتهية
        warranty_expiring = Asset.objects.filter(
            company=self.request.current_company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__gte=today,
            warranty_end_date__lte=expiry_date
        ).select_related('category').order_by('warranty_end_date')[:5]

        # التأمينات المنتهية
        insurance_expiring = AssetInsurance.objects.filter(
            company=self.request.current_company,
            status='active',
            end_date__gte=today,
            end_date__lte=expiry_date
        ).select_related('asset', 'insurance_company').order_by('end_date')[:5]

        return {
            'warranty_expiring': warranty_expiring,
            'insurance_expiring': insurance_expiring,
            'warranty_count': warranty_expiring.count(),
            'insurance_count': insurance_expiring.count()
        }

    def get_recent_assets(self):
        """الأصول المضافة خلال آخر 30 يوم"""
        thirty_days_ago = date.today() - timedelta(days=30)

        return Asset.objects.filter(
            company=self.request.current_company,
            created_at__gte=thirty_days_ago
        ).select_related('category', 'branch').order_by('-created_at')[:5]

    def get_category_stats(self):
        """إحصائيات حسب الفئة"""
        return AssetCategory.objects.filter(
            is_active=True
        ).annotate(
            asset_count=Count(
                'assets',
                filter=Q(assets__company=self.request.current_company, assets__status='active')
            ),
            total_value=Coalesce(
                Sum(
                    'assets__book_value',
                    filter=Q(assets__company=self.request.current_company, assets__status='active')
                ),
                Decimal('0')
            )
        ).filter(asset_count__gt=0).order_by('-total_value')[:10]

    def get_recent_transactions(self):
        """المعاملات الأخيرة"""
        return AssetTransaction.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'business_partner').order_by('-transaction_date')[:5]


# ==================== Ajax Endpoints ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def dashboard_stats_ajax(request):
    """API للحصول على إحصائيات Dashboard محدثة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        # إحصائيات أساسية
        total_assets = Asset.objects.filter(company=request.current_company).count()
        active_assets = Asset.objects.filter(company=request.current_company, status='active').count()

        # القيمة الدفترية الإجمالية
        book_value_data = Asset.objects.filter(
            company=request.current_company,
            status='active'
        ).aggregate(
            total=Coalesce(Sum('book_value'), Decimal('0'))
        )

        # الصيانة المستحقة
        today = date.today()
        maintenance_due = MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lte=today + timedelta(days=7)
        ).count()

        stats = {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'total_book_value': float(book_value_data['total']),
            'maintenance_due': maintenance_due
        }

        return JsonResponse({'success': True, 'stats': stats})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_chart_ajax(request):
    """بيانات رسم الإهلاك الشهري"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        from django.db.models.functions import TruncMonth

        year = int(request.GET.get('year', date.today().year))

        # الإهلاك الشهري
        monthly_depreciation = AssetDepreciation.objects.filter(
            company=request.current_company,
            depreciation_date__year=year
        ).annotate(
            month=TruncMonth('depreciation_date')
        ).values('month').annotate(
            total=Sum('depreciation_amount')
        ).order_by('month')

        labels = []
        data = []

        for item in monthly_depreciation:
            labels.append(item['month'].strftime('%B'))
            data.append(float(item['total']))

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def maintenance_chart_ajax(request):
    """بيانات رسم تكلفة الصيانة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        from django.db.models.functions import TruncMonth

        year = int(request.GET.get('year', date.today().year))

        # تكلفة الصيانة الشهرية
        monthly_maintenance = AssetMaintenance.objects.filter(
            company=request.current_company,
            scheduled_date__year=year,
            status='completed'
        ).annotate(
            month=TruncMonth('scheduled_date')
        ).values('month').annotate(
            total=Sum(F('labor_cost') + F('parts_cost') + F('other_cost'))
        ).order_by('month')

        labels = []
        data = []

        for item in monthly_maintenance:
            labels.append(item['month'].strftime('%B'))
            data.append(float(item['total']))

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_status_chart_ajax(request):
    """بيانات رسم توزيع الأصول حسب الحالة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        # توزيع الأصول حسب الحالة
        status_distribution = Asset.objects.filter(
            company=request.current_company
        ).values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        labels = []
        data = []
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'under_maintenance': '#ffc107',
            'disposed': '#dc3545',
            'sold': '#17a2b8',
            'lost': '#e83e8c'
        }
        background_colors = []

        for item in status_distribution:
            status_display = dict(Asset.STATUS_CHOICES).get(item['status'], item['status'])
            labels.append(status_display)
            data.append(item['count'])
            background_colors.append(colors.get(item['status'], '#6c757d'))

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'backgroundColor': background_colors
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
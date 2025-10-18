# apps/assets/views/dashboard_views.py
"""
Dashboard Views - لوحة تحكم إدارة الأصول
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.db.models import Q, Sum, Count, Avg, F
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, datetime, timedelta
import json

from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, AssetTransaction, AssetDepreciation,
    AssetMaintenance, MaintenanceSchedule, AssetValuation, AssetAttachment
)


class AssetDashboardView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم إدارة الأصول"""

    template_name = 'assets/dashboard/dashboard.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company = self.request.current_company
        today = date.today()
        current_year = today.year
        current_month = today.month

        # ========== الإحصائيات الرئيسية ==========

        # إجمالي الأصول
        total_assets = Asset.objects.filter(company=company).count()

        # الأصول النشطة
        active_assets = Asset.objects.filter(company=company, status='active').count()

        # إجمالي القيمة الدفترية
        total_book_value = Asset.objects.filter(
            company=company,
            status='active'
        ).aggregate(total=Sum('book_value'))['total'] or Decimal('0.00')

        # إجمالي التكلفة الأصلية
        total_original_cost = Asset.objects.filter(
            company=company,
            status='active'
        ).aggregate(total=Sum('original_cost'))['total'] or Decimal('0.00')

        # إجمالي الإهلاك المتراكم
        total_accumulated_depreciation = Asset.objects.filter(
            company=company,
            status='active'
        ).aggregate(total=Sum('accumulated_depreciation'))['total'] or Decimal('0.00')

        # نسبة الإهلاك
        if total_original_cost > 0:
            depreciation_percentage = (total_accumulated_depreciation / total_original_cost) * 100
        else:
            depreciation_percentage = 0

        # ========== إحصائيات الفترة الحالية ==========

        # الأصول المضافة هذا الشهر
        assets_added_this_month = Asset.objects.filter(
            company=company,
            purchase_date__year=current_year,
            purchase_date__month=current_month
        ).count()

        # إهلاك هذا الشهر
        depreciation_this_month = AssetDepreciation.objects.filter(
            company=company,
            depreciation_date__year=current_year,
            depreciation_date__month=current_month
        ).aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')

        # تكلفة الصيانة هذا الشهر
        maintenance_cost_this_month = AssetMaintenance.objects.filter(
            company=company,
            scheduled_date__year=current_year,
            scheduled_date__month=current_month
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

        # ========== حسب الفئات ==========

        assets_by_category = Asset.objects.filter(
            company=company,
            status='active'
        ).values(
            'category__name'
        ).annotate(
            count=Count('id'),
            total_value=Sum('book_value')
        ).order_by('-total_value')[:5]

        # ========== حسب الحالة ==========

        assets_by_status = Asset.objects.filter(
            company=company
        ).values('status').annotate(
            count=Count('id')
        )

        status_dict = {item['status']: item['count'] for item in assets_by_status}

        # ========== التنبيهات ==========

        # الأصول تحت الصيانة
        assets_under_maintenance = Asset.objects.filter(
            company=company,
            status='under_maintenance'
        ).count()

        # الصيانات المتأخرة
        overdue_maintenances = AssetMaintenance.objects.filter(
            company=company,
            status='scheduled',
            scheduled_date__lt=today
        ).count()

        # الصيانات القادمة (خلال 7 أيام)
        upcoming_maintenances = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__lte=today + timedelta(days=7),
            next_maintenance_date__gte=today
        ).count()

        # المرفقات منتهية الصلاحية
        expired_attachments = AssetAttachment.objects.filter(
            asset__company=company,
            expiry_date__lt=today
        ).count()

        # التقييمات المعلقة
        pending_valuations = AssetValuation.objects.filter(
            asset__company=company,
            is_approved=False
        ).count()

        # الضمانات منتهية
        expired_warranties = Asset.objects.filter(
            company=company,
            status='active',
            warranty_end_date__lt=today
        ).count()

        # ========== آخر العمليات ==========

        # آخر الأصول المضافة
        recent_assets = Asset.objects.filter(
            company=company
        ).select_related('category', 'condition').order_by('-created_at')[:5]

        # آخر المعاملات
        recent_transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related('asset', 'business_partner').order_by('-transaction_date')[:5]

        # آخر الصيانات
        recent_maintenances = AssetMaintenance.objects.filter(
            company=company
        ).select_related('asset', 'maintenance_type').order_by('-scheduled_date')[:5]

        # ========== الأصول القابلة للإهلاك ==========

        depreciable_assets_count = Asset.objects.filter(
            company=company,
            status='active'
        ).exclude(
            accumulated_depreciation__gte=F('original_cost') - F('salvage_value')
        ).count()

        # ========== الصلاحيات ==========

        user = self.request.user
        permissions = {
            'can_add_asset': user.has_perm('assets.add_asset'),
            'can_purchase_asset': user.has_perm('assets.can_purchase_asset'),
            'can_sell_asset': user.has_perm('assets.can_sell_asset'),
            'can_transfer_asset': user.has_perm('assets.can_transfer_asset'),
            'can_revalue_asset': user.has_perm('assets.can_revalue_asset'),
            'can_dispose_asset': user.has_perm('assets.can_dispose_asset'),
            'can_calculate_depreciation': user.has_perm('assets.can_calculate_depreciation'),
            'can_add_maintenance': user.has_perm('assets.add_assetmaintenance'),
        }

        # ========== تجميع البيانات ==========

        context.update({
            'title': _('لوحة تحكم إدارة الأصول'),

            # الإحصائيات الرئيسية
            'total_assets': total_assets,
            'active_assets': active_assets,
            'total_book_value': total_book_value,
            'total_original_cost': total_original_cost,
            'total_accumulated_depreciation': total_accumulated_depreciation,
            'depreciation_percentage': depreciation_percentage,

            # الفترة الحالية
            'assets_added_this_month': assets_added_this_month,
            'depreciation_this_month': depreciation_this_month,
            'maintenance_cost_this_month': maintenance_cost_this_month,

            # التصنيفات
            'assets_by_category': assets_by_category,
            'assets_by_status': status_dict,

            # التنبيهات
            'assets_under_maintenance': assets_under_maintenance,
            'overdue_maintenances': overdue_maintenances,
            'upcoming_maintenances': upcoming_maintenances,
            'expired_attachments': expired_attachments,
            'pending_valuations': pending_valuations,
            'expired_warranties': expired_warranties,
            'depreciable_assets_count': depreciable_assets_count,

            # آخر العمليات
            'recent_assets': recent_assets,
            'recent_transactions': recent_transactions,
            'recent_maintenances': recent_maintenances,

            # الصلاحيات
            'permissions': permissions,

            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('لوحة تحكم الأصول'), 'url': ''}
            ],
        })

        return context


# ========== Ajax Endpoints ==========

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """إحصائيات Dashboard - API"""

    try:
        company = request.current_company

        stats = {
            'total_assets': Asset.objects.filter(company=company).count(),
            'active_assets': Asset.objects.filter(company=company, status='active').count(),
            'total_book_value': float(
                Asset.objects.filter(company=company, status='active').aggregate(
                    total=Sum('book_value')
                )['total'] or 0
            ),
            'assets_by_status': {}
        }

        # حسب الحالة
        for status_choice in Asset.STATUS_CHOICES:
            status_code = status_choice[0]
            count = Asset.objects.filter(company=company, status=status_code).count()
            stats['assets_by_status'][status_code] = count

        return JsonResponse({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def assets_by_category_chart_api(request):
    """رسم بياني للأصول حسب الفئة"""

    try:
        company = request.current_company

        assets_by_category = Asset.objects.filter(
            company=company,
            status='active'
        ).values(
            'category__name'
        ).annotate(
            count=Count('id'),
            total_value=Sum('book_value')
        ).order_by('-total_value')[:10]

        labels = [item['category__name'] for item in assets_by_category]
        counts = [item['count'] for item in assets_by_category]
        values = [float(item['total_value'] or 0) for item in assets_by_category]

        return JsonResponse({
            'success': True,
            'data': {
                'labels': labels,
                'counts': counts,
                'values': values
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_trend_chart_api(request):
    """رسم بياني لاتجاه الإهلاك"""

    try:
        company = request.current_company
        current_year = date.today().year

        # البيانات الشهرية للسنة الحالية
        monthly_data = []
        for month in range(1, 13):
            month_total = AssetDepreciation.objects.filter(
                company=company,
                depreciation_date__year=current_year,
                depreciation_date__month=month
            ).aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')

            monthly_data.append(float(month_total))

        return JsonResponse({
            'success': True,
            'data': {
                'labels': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                           'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
                'values': monthly_data
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def maintenance_cost_chart_api(request):
    """رسم بياني لتكاليف الصيانة"""

    try:
        company = request.current_company
        current_year = date.today().year

        # البيانات الشهرية
        monthly_data = []
        for month in range(1, 13):
            month_total = AssetMaintenance.objects.filter(
                company=company,
                scheduled_date__year=current_year,
                scheduled_date__month=month
            ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

            monthly_data.append(float(month_total))

        return JsonResponse({
            'success': True,
            'data': {
                'labels': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                           'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
                'values': monthly_data
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_age_distribution_api(request):
    """توزيع أعمار الأصول"""

    try:
        company = request.current_company
        today = date.today()

        # تصنيف الأصول حسب العمر
        age_ranges = {
            'أقل من سنة': 0,
            '1-3 سنوات': 0,
            '3-5 سنوات': 0,
            '5-10 سنوات': 0,
            'أكثر من 10 سنوات': 0
        }

        assets = Asset.objects.filter(company=company, status='active')

        for asset in assets:
            age_days = (today - asset.purchase_date).days
            age_years = age_days / 365.25

            if age_years < 1:
                age_ranges['أقل من سنة'] += 1
            elif age_years < 3:
                age_ranges['1-3 سنوات'] += 1
            elif age_years < 5:
                age_ranges['3-5 سنوات'] += 1
            elif age_years < 10:
                age_ranges['5-10 سنوات'] += 1
            else:
                age_ranges['أكثر من 10 سنوات'] += 1

        return JsonResponse({
            'success': True,
            'data': {
                'labels': list(age_ranges.keys()),
                'values': list(age_ranges.values())
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def alerts_summary_api(request):
    """ملخص التنبيهات"""

    try:
        company = request.current_company
        today = date.today()

        alerts = {
            'overdue_maintenances': {
                'count': AssetMaintenance.objects.filter(
                    company=company,
                    status='scheduled',
                    scheduled_date__lt=today
                ).count(),
                'severity': 'danger',
                'url': reverse('assets:maintenance_list') + '?status=scheduled'
            },
            'upcoming_maintenances': {
                'count': MaintenanceSchedule.objects.filter(
                    company=company,
                    is_active=True,
                    next_maintenance_date__lte=today + timedelta(days=7),
                    next_maintenance_date__gte=today
                ).count(),
                'severity': 'warning',
                'url': reverse('assets:maintenance_schedule_list')
            },
            'expired_warranties': {
                'count': Asset.objects.filter(
                    company=company,
                    status='active',
                    warranty_end_date__lt=today
                ).count(),
                'severity': 'info',
                'url': reverse('assets:asset_list') + '?warranty_expired=1'
            },
            'expired_attachments': {
                'count': AssetAttachment.objects.filter(
                    asset__company=company,
                    expiry_date__lt=today
                ).count(),
                'severity': 'warning',
                'url': '#'
            },
            'pending_valuations': {
                'count': AssetValuation.objects.filter(
                    asset__company=company,
                    is_approved=False
                ).count(),
                'severity': 'info',
                'url': reverse('assets:valuation_list') + '?approval_status=pending'
            }
        }

        return JsonResponse({
            'success': True,
            'alerts': alerts
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def recent_activities_api(request):
    """آخر الأنشطة"""

    try:
        company = request.current_company
        limit = int(request.GET.get('limit', 10))

        activities = []

        # آخر الأصول المضافة
        recent_assets = Asset.objects.filter(
            company=company
        ).select_related('category').order_by('-created_at')[:limit]

        for asset in recent_assets:
            activities.append({
                'type': 'asset_added',
                'icon': 'fas fa-plus-circle',
                'color': 'success',
                'title': f'إضافة أصل جديد',
                'description': f'{asset.asset_number} - {asset.name}',
                'date': asset.created_at.strftime('%Y-%m-%d %H:%M'),
                'url': reverse('assets:asset_detail', args=[asset.pk])
            })

        # آخر المعاملات
        recent_transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related('asset').order_by('-transaction_date')[:limit]

        for trans in recent_transactions:
            activities.append({
                'type': 'transaction',
                'icon': 'fas fa-exchange-alt',
                'color': 'primary',
                'title': f'{trans.get_transaction_type_display()}',
                'description': f'{trans.asset.name} - {trans.amount:,.2f}',
                'date': trans.transaction_date.strftime('%Y-%m-%d'),
                'url': reverse('assets:transaction_detail', args=[trans.pk])
            })

        # ترتيب حسب التاريخ
        activities.sort(key=lambda x: x['date'], reverse=True)

        return JsonResponse({
            'success': True,
            'activities': activities[:limit]
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def top_assets_by_value_api(request):
    """أعلى الأصول قيمة"""

    try:
        company = request.current_company
        limit = int(request.GET.get('limit', 10))

        top_assets = Asset.objects.filter(
            company=company,
            status='active'
        ).select_related('category').order_by('-book_value')[:limit]

        data = []
        for asset in top_assets:
            data.append({
                'asset_number': asset.asset_number,
                'name': asset.name,
                'category': asset.category.name,
                'book_value': float(asset.book_value),
                'original_cost': float(asset.original_cost),
                'url': reverse('assets:asset_detail', args=[asset.pk])
            })

        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
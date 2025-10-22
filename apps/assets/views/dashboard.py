# apps/assets/views/dashboard.py
"""
لوحة تحكم نظام الأصول الثابتة - محسّنة
- إحصائيات شاملة ومفصّلة
- رسوم بيانية تفاعلية
- تنبيهات ذكية
- إحصائيات الجرد والإيجارات
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.db.models import (
    Sum, Count, Q, F, DecimalField, Case, When, Value, Avg,
    Max, Min, FloatField
)
from django.db.models.functions import Coalesce, TruncMonth, TruncDate
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta, datetime
import json

from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message

from ..models import (
    Asset, AssetCategory, AssetDepreciation,
    AssetMaintenance, MaintenanceSchedule,
    AssetInsurance, InsuranceClaim,
    PhysicalCount, PhysicalCountCycle,
    AssetTransaction, AssetTransfer,
    AssetLease, LeasePayment
)


class AssetDashboardView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم الأصول الثابتة - محسّنة"""

    template_name = 'assets/dashboard.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # الإحصائيات الأساسية
            stats = self.get_basic_stats()

            # الإحصائيات المالية المفصّلة
            financial_stats = self.get_financial_stats()

            # تنبيهات الصيانة
            maintenance_alerts = self.get_maintenance_alerts()

            # تنبيهات الإهلاك
            depreciation_alerts = self.get_depreciation_alerts()

            # تنبيهات الضمان والتأمين
            expiry_alerts = self.get_expiry_alerts()

            # الأصول المضافة حديثاً
            recent_assets = self.get_recent_assets()

            # إحصائيات حسب الفئة (أفضل 10)
            category_stats = self.get_category_stats()

            # إحصائيات حسب الفروع
            branch_stats = self.get_branch_stats()

            # المعاملات الأخيرة
            recent_transactions = self.get_recent_transactions()

            # إحصائيات الجرد الفعلي
            physical_count_stats = self.get_physical_count_stats()

            # إحصائيات الإيجارات
            lease_stats = self.get_lease_stats()

            # إحصائيات الصيانة
            maintenance_stats = self.get_maintenance_stats()

            # إحصائيات التأمين
            insurance_stats = self.get_insurance_stats()

            # Quick Actions
            quick_actions = self.get_quick_actions()

            context.update({
                'title': _('لوحة تحكم الأصول الثابتة'),
                'stats': stats,
                'financial_stats': financial_stats,
                'maintenance_alerts': maintenance_alerts,
                'depreciation_alerts': depreciation_alerts,
                'expiry_alerts': expiry_alerts,
                'recent_assets': recent_assets,
                'category_stats': category_stats,
                'branch_stats': branch_stats,
                'recent_transactions': recent_transactions,
                'physical_count_stats': physical_count_stats,
                'lease_stats': lease_stats,
                'maintenance_stats': maintenance_stats,
                'insurance_stats': insurance_stats,
                'quick_actions': quick_actions,
                'breadcrumbs': [
                    {'title': _('لوحة التحكم'), 'url': ''},
                ]
            })

        except Exception as e:
            import traceback
            print(f"Error in dashboard: {traceback.format_exc()}")
            context['error'] = str(e)

        return context

    def get_basic_stats(self):
        """الإحصائيات الأساسية - محسّنة"""
        company = self.request.current_company

        # الأصول حسب الحالة
        assets_by_status = Asset.objects.filter(
            company=company
        ).values('status').annotate(
            count=Count('id')
        )

        status_dict = {item['status']: item['count'] for item in assets_by_status}

        total_assets = sum(status_dict.values())
        active_assets = status_dict.get('active', 0)
        under_maintenance = status_dict.get('under_maintenance', 0)
        disposed = status_dict.get('disposed', 0) + status_dict.get('sold', 0)
        inactive = status_dict.get('inactive', 0)
        lost = status_dict.get('lost', 0)
        damaged = status_dict.get('damaged', 0)

        # نسب مئوية
        active_percentage = round((active_assets / total_assets * 100), 2) if total_assets > 0 else 0
        maintenance_percentage = round((under_maintenance / total_assets * 100), 2) if total_assets > 0 else 0

        # مقارنة مع الشهر الماضي
        last_month = timezone.now() - timedelta(days=30)
        new_assets_last_month = Asset.objects.filter(
            company=company,
            created_at__gte=last_month
        ).count()

        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'under_maintenance': under_maintenance,
            'disposed': disposed,
            'inactive': inactive,
            'lost': lost,
            'damaged': damaged,
            'active_percentage': active_percentage,
            'maintenance_percentage': maintenance_percentage,
            'new_assets_last_month': new_assets_last_month,
            'status_distribution': status_dict,
        }

    def get_financial_stats(self):
        """الإحصائيات المالية المفصّلة"""
        company = self.request.current_company

        # الأصول النشطة فقط
        active_assets = Asset.objects.filter(
            company=company,
            status='active'
        )

        financial = active_assets.aggregate(
            total_original_cost=Coalesce(Sum('original_cost'), Decimal('0')),
            total_depreciation=Coalesce(Sum('accumulated_depreciation'), Decimal('0')),
            total_book_value=Coalesce(Sum('book_value'), Decimal('0')),
            total_salvage_value=Coalesce(Sum('salvage_value'), Decimal('0')),
            avg_book_value=Coalesce(Avg('book_value'), Decimal('0')),
            max_book_value=Coalesce(Max('book_value'), Decimal('0')),
            min_book_value=Coalesce(Min('book_value'), Decimal('0')),
        )

        # نسبة الإهلاك الإجمالية
        depreciation_percentage = 0
        if financial['total_original_cost'] > 0:
            depreciation_percentage = round(
                float(financial['total_depreciation'] / financial['total_original_cost'] * 100),
                2
            )

        # القيمة المتوقعة المتبقية
        expected_remaining_value = financial['total_book_value'] - financial['total_salvage_value']

        # معدل الإهلاك الشهري المتوقع
        current_year = timezone.now().year
        current_year_depreciation = AssetDepreciation.objects.filter(
            company=company,
            depreciation_date__year=current_year
        ).aggregate(
            total=Coalesce(Sum('depreciation_amount'), Decimal('0'))
        )['total']

        months_passed = timezone.now().month
        avg_monthly_depreciation = (
            current_year_depreciation / months_passed
        ) if months_passed > 0 else Decimal('0')

        # الأصول الأعلى قيمة (Top 5)
        top_assets = active_assets.order_by('-book_value')[:5].values(
            'asset_number', 'name', 'book_value'
        )

        return {
            'total_original_cost': financial['total_original_cost'],
            'total_depreciation': financial['total_depreciation'],
            'total_book_value': financial['total_book_value'],
            'total_salvage_value': financial['total_salvage_value'],
            'depreciation_percentage': depreciation_percentage,
            'expected_remaining_value': max(expected_remaining_value, Decimal('0')),
            'avg_book_value': financial['avg_book_value'],
            'max_book_value': financial['max_book_value'],
            'min_book_value': financial['min_book_value'],
            'avg_monthly_depreciation': avg_monthly_depreciation,
            'current_year_depreciation': current_year_depreciation,
            'top_assets': list(top_assets),
        }

    def get_maintenance_alerts(self):
        """تنبيهات الصيانة المستحقة - محسّنة"""
        company = self.request.current_company
        today = date.today()
        due_date = today + timedelta(days=30)

        # الصيانة المتأخرة (Overdue)
        overdue = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__lt=today
        ).select_related('asset', 'maintenance_type')

        overdue_count = overdue.count()
        overdue_list = overdue.order_by('next_maintenance_date')[:5]

        # الصيانة المستحقة خلال 7 أيام (Critical)
        critical_date = today + timedelta(days=7)
        critical = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__gte=today,
            next_maintenance_date__lte=critical_date
        ).select_related('asset', 'maintenance_type')

        critical_count = critical.count()
        critical_list = critical.order_by('next_maintenance_date')[:5]

        # الصيانة القادمة (8-30 يوم)
        upcoming = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__gt=critical_date,
            next_maintenance_date__lte=due_date
        ).select_related('asset', 'maintenance_type')

        upcoming_count = upcoming.count()
        upcoming_list = upcoming.order_by('next_maintenance_date')[:5]

        # الصيانات الجارية
        in_progress = AssetMaintenance.objects.filter(
            company=company,
            status='in_progress'
        ).select_related('asset', 'maintenance_type').count()

        return {
            'overdue_count': overdue_count,
            'overdue_list': overdue_list,
            'critical_count': critical_count,
            'critical_list': critical_list,
            'upcoming_count': upcoming_count,
            'upcoming_list': upcoming_list,
            'in_progress_count': in_progress,
            'total_alerts': overdue_count + critical_count,
        }

    def get_depreciation_alerts(self):
        """الأصول القريبة من الإهلاك الكامل - محسّنة"""
        company = self.request.current_company

        # الأصول المهلكة بالكامل (100%)
        fully_depreciated = Asset.objects.filter(
            company=company,
            status='active',
            original_cost__gt=0
        ).annotate(
            depreciation_percentage=Case(
                When(original_cost=0, then=Value(0)),
                default=(F('accumulated_depreciation') * 100.0) / F('original_cost'),
                output_field=FloatField()
            )
        ).filter(
            depreciation_percentage__gte=99.9
        ).select_related('category')

        # الأصول القريبة من الإهلاك الكامل (90-99%)
        nearly_depreciated = Asset.objects.filter(
            company=company,
            status='active',
            original_cost__gt=0
        ).annotate(
            depreciation_percentage=Case(
                When(original_cost=0, then=Value(0)),
                default=(F('accumulated_depreciation') * 100.0) / F('original_cost'),
                output_field=FloatField()
            )
        ).filter(
            depreciation_percentage__gte=90,
            depreciation_percentage__lt=99.9
        ).select_related('category')

        # الأصول المتوقفة عن الإهلاك
        paused_depreciation = Asset.objects.filter(
            company=company,
            status='active',
            depreciation_status='paused'
        ).count()

        return {
            'fully_depreciated': fully_depreciated[:5],
            'fully_depreciated_count': fully_depreciated.count(),
            'nearly_depreciated': nearly_depreciated.order_by('-depreciation_percentage')[:5],
            'nearly_depreciated_count': nearly_depreciated.count(),
            'paused_count': paused_depreciation,
            'total_alerts': fully_depreciated.count() + nearly_depreciated.count(),
        }

    def get_expiry_alerts(self):
        """تنبيهات انتهاء الضمان والتأمين - محسّنة"""
        company = self.request.current_company
        today = date.today()
        expiry_date_30 = today + timedelta(days=30)
        expiry_date_60 = today + timedelta(days=60)

        # الضمانات المنتهية
        warranty_expired = Asset.objects.filter(
            company=company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__lt=today
        ).count()

        # الضمانات المنتهية قريباً (خلال 30 يوم)
        warranty_expiring_soon = Asset.objects.filter(
            company=company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__gte=today,
            warranty_end_date__lte=expiry_date_30
        ).select_related('category', 'supplier')

        # الضمانات المنتهية خلال 60 يوم
        warranty_expiring = Asset.objects.filter(
            company=company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__gt=expiry_date_30,
            warranty_end_date__lte=expiry_date_60
        ).select_related('category', 'supplier')

        # التأمينات المنتهية قريباً (خلال 30 يوم)
        insurance_expiring_soon = AssetInsurance.objects.filter(
            company=company,
            status='active',
            end_date__gte=today,
            end_date__lte=expiry_date_30
        ).select_related('asset', 'insurance_company')

        # التأمينات المنتهية خلال 60 يوم
        insurance_expiring = AssetInsurance.objects.filter(
            company=company,
            status='active',
            end_date__gt=expiry_date_30,
            end_date__lte=expiry_date_60
        ).select_related('asset', 'insurance_company')

        # الأصول غير المؤمّنة
        uninsured_assets = Asset.objects.filter(
            company=company,
            status='active',
            insurance_status__in=['not_insured', 'expired']
        ).count()

        return {
            'warranty_expired': warranty_expired,
            'warranty_expiring_soon': warranty_expiring_soon.order_by('warranty_end_date')[:5],
            'warranty_expiring_soon_count': warranty_expiring_soon.count(),
            'warranty_expiring': warranty_expiring.order_by('warranty_end_date')[:5],
            'warranty_expiring_count': warranty_expiring.count(),
            'insurance_expiring_soon': insurance_expiring_soon.order_by('end_date')[:5],
            'insurance_expiring_soon_count': insurance_expiring_soon.count(),
            'insurance_expiring': insurance_expiring.order_by('end_date')[:5],
            'insurance_expiring_count': insurance_expiring.count(),
            'uninsured_assets': uninsured_assets,
            'total_warranty_alerts': warranty_expired + warranty_expiring_soon.count(),
            'total_insurance_alerts': insurance_expiring_soon.count() + insurance_expiring.count(),
        }

    def get_recent_assets(self):
        """الأصول المضافة حديثاً - محسّنة"""
        company = self.request.current_company
        thirty_days_ago = timezone.now() - timedelta(days=30)

        assets = Asset.objects.filter(
            company=company,
            created_at__gte=thirty_days_ago
        ).select_related(
            'category', 'branch', 'condition', 'created_by'
        ).order_by('-created_at')[:10]

        return assets

    def get_category_stats(self):
        """إحصائيات حسب الفئة - محسّنة"""
        company = self.request.current_company

        categories = AssetCategory.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            asset_count=Count(
                'assets',
                filter=Q(assets__status='active')
            ),
            total_original_cost=Coalesce(
                Sum(
                    'assets__original_cost',
                    filter=Q(assets__status='active')
                ),
                Decimal('0')
            ),
            total_book_value=Coalesce(
                Sum(
                    'assets__book_value',
                    filter=Q(assets__status='active')
                ),
                Decimal('0')
            ),
            total_depreciation=Coalesce(
                Sum(
                    'assets__accumulated_depreciation',
                    filter=Q(assets__status='active')
                ),
                Decimal('0')
            ),
            avg_depreciation_pct=Case(
                When(total_original_cost=0, then=Value(0)),
                default=(F('total_depreciation') * 100.0) / F('total_original_cost'),
                output_field=FloatField()
            )
        ).filter(
            asset_count__gt=0
        ).order_by('-total_book_value')[:10]

        return categories

    def get_branch_stats(self):
        """إحصائيات حسب الفروع"""
        company = self.request.current_company

        from apps.core.models import Branch

        branches = Branch.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            asset_count=Count(
                'assets',
                filter=Q(assets__status='active')
            ),
            total_value=Coalesce(
                Sum(
                    'assets__book_value',
                    filter=Q(assets__status='active')
                ),
                Decimal('0')
            )
        ).filter(
            asset_count__gt=0
        ).order_by('-total_value')[:10]

        return branches

    def get_recent_transactions(self):
        """المعاملات الأخيرة - محسّنة"""
        company = self.request.current_company

        transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related(
            'asset', 'business_partner', 'created_by'
        ).order_by('-transaction_date')[:10]

        return transactions

    def get_physical_count_stats(self):
        """إحصائيات الجرد الفعلي"""
        company = self.request.current_company
        today = date.today()

        # دورة الجرد النشطة
        active_cycle = PhysicalCountCycle.objects.filter(
            company=company,
            status='in_progress'
        ).first()

        # عمليات الجرد المعلقة
        pending_counts = PhysicalCount.objects.filter(
            company=company,
            status__in=['draft', 'in_progress']
        ).count()

        # الأصول التي تحتاج جرد
        assets_needing_count = Asset.objects.filter(
            company=company,
            status='active'
        ).annotate(
            days_since_count=Case(
                When(
                    last_physical_count_date__isnull=False,
                    then=Value((today - F('last_physical_count_date')).days)
                ),
                default=Value(999),
                output_field=FloatField()
            )
        ).filter(
            Q(last_physical_count_date__isnull=True) |
            Q(days_since_count__gte=365)
        ).count()

        # آخر جرد
        last_count = PhysicalCount.objects.filter(
            company=company,
            status='completed'
        ).order_by('-count_date').first()

        return {
            'active_cycle': active_cycle,
            'pending_counts': pending_counts,
            'assets_needing_count': assets_needing_count,
            'last_count': last_count,
            'has_alerts': assets_needing_count > 0 or pending_counts > 0,
        }

    def get_lease_stats(self):
        """إحصائيات الإيجارات"""
        company = self.request.current_company
        today = date.today()

        # عقود الإيجار النشطة
        active_leases = AssetLease.objects.filter(
            company=company,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).count()

        # إجمالي الأقساط الشهرية
        total_monthly_payments = AssetLease.objects.filter(
            company=company,
            status='active'
        ).aggregate(
            total=Coalesce(Sum('monthly_payment'), Decimal('0'))
        )['total']

        # أقساط متأخرة
        overdue_payments = LeasePayment.objects.filter(
            lease__company=company,
            is_paid=False,
            payment_date__lt=today
        ).count()

        # أقساط مستحقة خلال 7 أيام
        due_soon = LeasePayment.objects.filter(
            lease__company=company,
            is_paid=False,
            payment_date__gte=today,
            payment_date__lte=today + timedelta(days=7)
        ).count()

        # عقود منتهية قريباً (خلال 60 يوم)
        expiring_soon = AssetLease.objects.filter(
            company=company,
            status='active',
            end_date__gte=today,
            end_date__lte=today + timedelta(days=60)
        ).count()

        return {
            'active_leases': active_leases,
            'total_monthly_payments': total_monthly_payments,
            'overdue_payments': overdue_payments,
            'due_soon': due_soon,
            'expiring_soon': expiring_soon,
            'has_alerts': overdue_payments > 0 or due_soon > 0,
        }

    def get_maintenance_stats(self):
        """إحصائيات الصيانة الشاملة"""
        company = self.request.current_company
        current_year = timezone.now().year

        # تكلفة الصيانة السنوية
        yearly_cost = AssetMaintenance.objects.filter(
            company=company,
            status='completed',
            completion_date__year=current_year
        ).aggregate(
            total=Coalesce(
                Sum(F('labor_cost') + F('parts_cost') + F('other_cost')),
                Decimal('0')
            )
        )['total']

        # عدد الصيانات المكتملة
        completed_count = AssetMaintenance.objects.filter(
            company=company,
            status='completed',
            completion_date__year=current_year
        ).count()

        # متوسط تكلفة الصيانة
        avg_cost = yearly_cost / completed_count if completed_count > 0 else Decimal('0')

        # الأصول الأكثر صيانة
        top_maintained = Asset.objects.filter(
            company=company,
            status='active'
        ).annotate(
            maintenance_count=Count(
                'maintenances',
                filter=Q(
                    maintenances__status='completed',
                    maintenances__completion_date__year=current_year
                )
            ),
            total_maintenance_cost=Coalesce(
                Sum(
                    F('maintenances__labor_cost') +
                    F('maintenances__parts_cost') +
                    F('maintenances__other_cost'),
                    filter=Q(
                        maintenances__status='completed',
                        maintenances__completion_date__year=current_year
                    )
                ),
                Decimal('0')
            )
        ).filter(
            maintenance_count__gt=0
        ).order_by('-total_maintenance_cost')[:5]

        return {
            'yearly_cost': yearly_cost,
            'completed_count': completed_count,
            'avg_cost': avg_cost,
            'top_maintained': top_maintained,
        }

    def get_insurance_stats(self):
        """إحصائيات التأمين"""
        company = self.request.current_company
        current_year = timezone.now().year

        # بوليصات التأمين النشطة
        active_policies = AssetInsurance.objects.filter(
            company=company,
            status='active'
        ).count()

        # إجمالي الأقساط السنوية
        total_premiums = AssetInsurance.objects.filter(
            company=company,
            status='active'
        ).aggregate(
            total=Coalesce(Sum('premium_amount'), Decimal('0'))
        )['total']

        # إجمالي التغطية
        total_coverage = AssetInsurance.objects.filter(
            company=company,
            status='active'
        ).aggregate(
            total=Coalesce(Sum('coverage_amount'), Decimal('0'))
        )['total']

        # المطالبات هذا العام
        claims_count = InsuranceClaim.objects.filter(
            insurance__company=company,
            filed_date__year=current_year
        ).count()

        # المطالبات المدفوعة
        paid_claims = InsuranceClaim.objects.filter(
            insurance__company=company,
            status='paid',
            filed_date__year=current_year
        ).aggregate(
            total=Coalesce(Sum('approved_amount'), Decimal('0'))
        )['total']

        return {
            'active_policies': active_policies,
            'total_premiums': total_premiums,
            'total_coverage': total_coverage,
            'claims_count': claims_count,
            'paid_claims': paid_claims,
        }

    def get_quick_actions(self):
        """الإجراءات السريعة بناءً على الصلاحيات"""
        user = self.request.user
        actions = []

        if user.has_perm('assets.add_asset'):
            actions.append({
                'title': 'إضافة أصل جديد',
                'icon': 'fas fa-plus-circle',
                'url': reverse('assets:asset_create'),
                'color': 'primary'
            })

        if user.has_perm('assets.can_calculate_depreciation'):
            actions.append({
                'title': 'احتساب الإهلاك',
                'icon': 'fas fa-calculator',
                'url': reverse('assets:bulk_calculate_depreciation'),
                'color': 'success'
            })

        if user.has_perm('assets.add_assetmaintenance'):
            actions.append({
                'title': 'جدولة صيانة',
                'icon': 'fas fa-tools',
                'url': reverse('assets:schedule_create'),
                'color': 'warning'
            })

        if user.has_perm('assets.can_conduct_physical_count'):
            actions.append({
                'title': 'بدء جرد',
                'icon': 'fas fa-clipboard-check',
                'url': reverse('assets:count_create'),
                'color': 'info'
            })

        if user.has_perm('assets.view_asset'):
            actions.append({
                'title': 'التقارير',
                'icon': 'fas fa-chart-bar',
                'url': reverse('assets:reports'),
                'color': 'secondary'
            })

        return actions


# ==================== Ajax Endpoints - محسّنة ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def dashboard_stats_ajax(request):
    """API للحصول على إحصائيات Dashboard محدثة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company

        # إحصائيات أساسية
        total_assets = Asset.objects.filter(company=company).count()
        active_assets = Asset.objects.filter(company=company, status='active').count()

        # القيمة الدفترية الإجمالية
        book_value_data = Asset.objects.filter(
            company=company,
            status='active'
        ).aggregate(
            total=Coalesce(Sum('book_value'), Decimal('0'))
        )

        # الصيانة المستحقة
        today = date.today()
        maintenance_due = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__lte=today + timedelta(days=7)
        ).count()

        # الإهلاك هذا الشهر
        current_month_start = date(today.year, today.month, 1)
        monthly_depreciation = AssetDepreciation.objects.filter(
            company=company,
            depreciation_date__gte=current_month_start
        ).aggregate(
            total=Coalesce(Sum('depreciation_amount'), Decimal('0'))
        )['total']

        # الأصول الجديدة هذا الشهر
        new_assets_this_month = Asset.objects.filter(
            company=company,
            created_at__gte=current_month_start
        ).count()

        stats = {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'total_book_value': float(book_value_data['total']),
            'maintenance_due': maintenance_due,
            'monthly_depreciation': float(monthly_depreciation),
            'new_assets_this_month': new_assets_this_month,
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
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
    """بيانات رسم الإهلاك الشهري - محسّنة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company
        year = int(request.GET.get('year', date.today().year))
        category_id = request.GET.get('category_id')

        # Query الإهلاك الشهري
        depreciation_query = AssetDepreciation.objects.filter(
            company=company,
            depreciation_date__year=year,
            is_posted=True
        )

        # فلترة حسب الفئة إن وجدت
        if category_id:
            depreciation_query = depreciation_query.filter(
                asset__category_id=category_id
            )

        # تجميع البيانات
        monthly_depreciation = depreciation_query.annotate(
            month=TruncMonth('depreciation_date')
        ).values('month').annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('month')

        # إعداد البيانات للرسم
        labels = []
        data = []
        counts = []

        for item in monthly_depreciation:
            labels.append(item['month'].strftime('%B %Y'))
            data.append(float(item['total']))
            counts.append(item['count'])

        # حساب الإجمالي والمتوسط
        total = sum(data)
        average = total / len(data) if data else 0

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'counts': counts,
            'total': total,
            'average': round(average, 2),
            'year': year
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def maintenance_chart_ajax(request):
    """بيانات رسم تكلفة الصيانة - محسّنة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company
        year = int(request.GET.get('year', date.today().year))
        category_id = request.GET.get('category_id')
        maintenance_category = request.GET.get('maintenance_category')

        # Query الصيانة
        maintenance_query = AssetMaintenance.objects.filter(
            company=company,
            completion_date__year=year,
            status='completed'
        )

        # فلترة حسب الفئة
        if category_id:
            maintenance_query = maintenance_query.filter(
                asset__category_id=category_id
            )

        # فلترة حسب نوع الصيانة
        if maintenance_category:
            maintenance_query = maintenance_query.filter(
                maintenance_category=maintenance_category
            )

        # تجميع البيانات
        monthly_maintenance = maintenance_query.annotate(
            month=TruncMonth('completion_date')
        ).values('month').annotate(
            total_cost=Sum(
                F('labor_cost') + F('parts_cost') + F('other_cost')
            ),
            count=Count('id'),
            avg_cost=Avg(
                F('labor_cost') + F('parts_cost') + F('other_cost')
            )
        ).order_by('month')

        # إعداد البيانات
        labels = []
        data = []
        counts = []
        averages = []

        for item in monthly_maintenance:
            labels.append(item['month'].strftime('%B %Y'))
            data.append(float(item['total_cost']))
            counts.append(item['count'])
            averages.append(float(item['avg_cost']) if item['avg_cost'] else 0)

        # حساب الإجماليات
        total_cost = sum(data)
        total_count = sum(counts)
        overall_average = total_cost / total_count if total_count > 0 else 0

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'counts': counts,
            'averages': averages,
            'total_cost': round(total_cost, 2),
            'total_count': total_count,
            'overall_average': round(overall_average, 2),
            'year': year
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_status_chart_ajax(request):
    """بيانات رسم توزيع الأصول حسب الحالة - محسّنة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company
        category_id = request.GET.get('category_id')
        branch_id = request.GET.get('branch_id')

        # Query الأصول
        assets_query = Asset.objects.filter(company=company)

        # فلترة
        if category_id:
            assets_query = assets_query.filter(category_id=category_id)

        if branch_id:
            assets_query = assets_query.filter(branch_id=branch_id)

        # توزيع الأصول حسب الحالة
        status_distribution = assets_query.values('status').annotate(
            count=Count('id'),
            total_value=Coalesce(Sum('book_value'), Decimal('0'))
        ).order_by('-count')

        # إعداد البيانات
        labels = []
        data = []
        values = []
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'under_maintenance': '#ffc107',
            'disposed': '#dc3545',
            'sold': '#17a2b8',
            'lost': '#e83e8c',
            'damaged': '#fd7e14'
        }
        background_colors = []

        status_labels = dict(Asset.STATUS_CHOICES)

        for item in status_distribution:
            status = item['status']
            labels.append(status_labels.get(status, status))
            data.append(item['count'])
            values.append(float(item['total_value']))
            background_colors.append(colors.get(status, '#6c757d'))

        # حساب الإجماليات
        total_count = sum(data)
        total_value = sum(values)

        # النسب المئوية
        percentages = [
            round((count / total_count * 100), 2) if total_count > 0 else 0
            for count in data
        ]

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'values': values,
            'percentages': percentages,
            'backgroundColor': background_colors,
            'total_count': total_count,
            'total_value': round(total_value, 2)
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def category_chart_ajax(request):
    """بيانات رسم توزيع الأصول حسب الفئة - جديد"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company
        limit = int(request.GET.get('limit', 10))

        # إحصائيات الفئات
        categories = AssetCategory.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            asset_count=Count(
                'assets',
                filter=Q(assets__status='active')
            ),
            total_value=Coalesce(
                Sum(
                    'assets__book_value',
                    filter=Q(assets__status='active')
                ),
                Decimal('0')
            )
        ).filter(
            asset_count__gt=0
        ).order_by('-total_value')[:limit]

        # إعداد البيانات
        labels = []
        counts = []
        values = []

        for category in categories:
            labels.append(category.name)
            counts.append(category.asset_count)
            values.append(float(category.total_value))

        return JsonResponse({
            'success': True,
            'labels': labels,
            'counts': counts,
            'values': values,
            'total_categories': len(labels)
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_age_chart_ajax(request):
    """بيانات رسم توزيع أعمار الأصول - جديد"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'success': False, 'error': 'لا توجد شركة محددة'}, status=400)

    try:
        company = request.current_company
        today = date.today()

        # الأصول النشطة
        assets = Asset.objects.filter(
            company=company,
            status='active'
        ).annotate(
            age_days=(
                (today.year - F('purchase_date__year')) * 365 +
                (today.month - F('purchase_date__month')) * 30 +
                (today.day - F('purchase_date__day'))
            )
        )

        # تصنيف الأعمار
        age_ranges = [
            ('أقل من سنة', 0, 365),
            ('1-2 سنة', 365, 730),
            ('2-3 سنوات', 730, 1095),
            ('3-5 سنوات', 1095, 1825),
            ('أكثر من 5 سنوات', 1825, 99999),
        ]

        labels = []
        data = []

        for label, min_days, max_days in age_ranges:
            count = assets.filter(
                age_days__gte=min_days,
                age_days__lt=max_days
            ).count()
            labels.append(label)
            data.append(count)

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
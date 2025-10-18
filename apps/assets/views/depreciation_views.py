# apps/assets/views/depreciation_views.py
"""
Depreciation Views - إدارة الإهلاك
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from datetime import date, datetime
import json

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message, company_required
from ..models import Asset, AssetDepreciation, AssetCategory
from django.utils import timezone


class AssetDepreciationListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة سجلات الإهلاك"""

    template_name = 'assets/depreciation/depreciation_list.html'
    permission_required = 'assets.view_assetdepreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        current_year = date.today().year
        total_depreciation = AssetDepreciation.objects.filter(
            company=self.request.current_company,
            depreciation_date__year=current_year
        ).aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')

        total_records = AssetDepreciation.objects.filter(
            company=self.request.current_company
        ).count()

        this_month_count = AssetDepreciation.objects.filter(
            company=self.request.current_company,
            depreciation_date__year=date.today().year,
            depreciation_date__month=date.today().month
        ).count()

        context.update({
            'title': _('سجلات الإهلاك'),
            'can_calculate': self.request.user.has_perm('assets.can_calculate_depreciation'),
            'total_depreciation': total_depreciation,
            'total_records': total_records,
            'this_month_count': this_month_count,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الإهلاك'), 'url': ''}
            ],
        })
        return context


class AssetDepreciationDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل سجل إهلاك"""

    model = AssetDepreciation
    template_name = 'assets/depreciation/depreciation_detail.html'
    context_object_name = 'depreciation'
    permission_required = 'assets.view_assetdepreciation'

    def get_queryset(self):
        return AssetDepreciation.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'fiscal_year', 'period', 'journal_entry', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تفاصيل إهلاك {self.object.asset.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الإهلاك'), 'url': reverse('assets:depreciation_list')},
                {'title': f'تفاصيل', 'url': ''}
            ],
        })
        return context


class CalculateMonthlyDepreciationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """احتساب الإهلاك الشهري لأصل واحد"""

    template_name = 'assets/depreciation/calculate_monthly.html'
    permission_required = 'assets.can_calculate_depreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # قائمة الأصول النشطة القابلة للإهلاك
        active_assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).select_related('category', 'depreciation_method')

        context.update({
            'title': _('احتساب الإهلاك الشهري'),
            'active_assets': active_assets,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('احتساب الإهلاك'), 'url': ''}
            ],
        })
        return context


class CalculateBatchDepreciationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """احتساب الإهلاك الدفعي لجميع الأصول"""

    template_name = 'assets/depreciation/calculate_batch.html'
    permission_required = 'assets.can_calculate_depreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الأصول القابلة للإهلاك
        depreciable_assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        ).exclude(
            accumulated_depreciation__gte=models.F('original_cost') - models.F('salvage_value')
        ).select_related('category', 'depreciation_method')

        total_count = depreciable_assets.count()
        total_book_value = depreciable_assets.aggregate(
            total=Sum('book_value')
        )['total'] or Decimal('0.00')

        context.update({
            'title': _('احتساب الإهلاك الدفعي'),
            'depreciable_assets': depreciable_assets,
            'total_count': total_count,
            'total_book_value': total_book_value,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('احتساب دفعي'), 'url': ''}
            ],
        })
        return context


# Ajax Views

@login_required
@permission_required_with_message('assets.view_assetdepreciation')
@require_http_methods(["GET"])
def asset_depreciation_datatable_ajax(request):
    """Ajax endpoint لجدول سجلات الإهلاك"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    asset_id = request.GET.get('asset_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        queryset = AssetDepreciation.objects.filter(
            company=request.current_company
        ).select_related('asset', 'fiscal_year', 'period', 'created_by')

        # تطبيق الفلاتر
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)

        if date_from:
            queryset = queryset.filter(depreciation_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(depreciation_date__lte=date_to)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        # الترتيب
        queryset = queryset.order_by('-depreciation_date')

        # العد الإجمالي
        total_records = AssetDepreciation.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []

        for record in queryset:
            data.append([
                record.depreciation_date.strftime('%Y-%m-%d'),
                f"{record.asset.asset_number} - {record.asset.name}",
                record.fiscal_year.name if record.fiscal_year else '--',
                record.period.name if record.period else '--',
                f"{record.depreciation_amount:,.3f}",
                f"{record.accumulated_depreciation_after:,.3f}",
                f"{record.book_value_after:,.3f}",
                f'''
                    <a href="{reverse('assets:depreciation_detail', args=[record.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                '''
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_assetdepreciation')
@require_http_methods(["GET"])
def depreciation_stats_ajax(request):
    """Ajax endpoint لإحصائيات الإهلاك"""

    try:
        current_year = date.today().year

        # إحصائيات السنة الحالية
        year_stats = AssetDepreciation.objects.filter(
            company=request.current_company,
            depreciation_date__year=current_year
        ).aggregate(
            total_amount=Sum('depreciation_amount'),
            count=Count('id'),
            avg_amount=Avg('depreciation_amount')
        )

        # إحصائيات شهرية للسنة الحالية
        monthly_stats = []
        for month in range(1, 13):
            month_data = AssetDepreciation.objects.filter(
                company=request.current_company,
                depreciation_date__year=current_year,
                depreciation_date__month=month
            ).aggregate(
                total=Sum('depreciation_amount'),
                count=Count('id')
            )
            monthly_stats.append({
                'month': month,
                'total': float(month_data['total'] or 0),
                'count': month_data['count']
            })

        # إحصائيات حسب الفئة
        category_stats = AssetDepreciation.objects.filter(
            company=request.current_company,
            depreciation_date__year=current_year
        ).values(
            'asset__category__name'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('-total')

        return JsonResponse({
            'success': True,
            'year_stats': {
                'total_amount': float(year_stats['total_amount'] or 0),
                'count': year_stats['count'],
                'avg_amount': float(year_stats['avg_amount'] or 0)
            },
            'monthly_stats': monthly_stats,
            'category_stats': list(category_stats)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.can_calculate_depreciation')
@require_http_methods(["POST"])
def calculate_depreciation_ajax(request):
    """حساب الإهلاك لأصل واحد - Ajax"""

    try:
        asset_id = request.POST.get('asset_id')

        if not asset_id:
            return JsonResponse({
                'success': False,
                'message': 'يجب تحديد الأصل'
            })

        asset = get_object_or_404(
            Asset,
            pk=asset_id,
            company=request.current_company
        )

        # استدعاء دالة حساب الإهلاك من النموذج
        depreciation_record = asset.calculate_monthly_depreciation(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم احتساب إهلاك {asset.name} بنجاح',
            'data': {
                'depreciation_amount': float(depreciation_record.depreciation_amount),
                'accumulated_depreciation': float(depreciation_record.accumulated_depreciation_after),
                'book_value': float(depreciation_record.book_value_after)
            }
        })

    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في احتساب الإهلاك: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.can_calculate_depreciation')
@require_http_methods(["POST"])
def calculate_batch_depreciation_ajax(request):
    """حساب الإهلاك الدفعي لجميع الأصول - Ajax"""

    try:
        # الأصول القابلة للإهلاك
        from django.db.models import F

        depreciable_assets = Asset.objects.filter(
            company=request.current_company,
            status='active'
        ).exclude(
            accumulated_depreciation__gte=F('original_cost') - F('salvage_value')
        )

        success_count = 0
        failed_count = 0
        errors = []

        with transaction.atomic():
            for asset in depreciable_assets:
                try:
                    asset.calculate_monthly_depreciation(user=request.user)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{asset.name}: {str(e)}")

        return JsonResponse({
            'success': True,
            'message': f'تم احتساب إهلاك {success_count} أصل بنجاح',
            'data': {
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': errors
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في الاحتساب الدفعي: {str(e)}'
        })
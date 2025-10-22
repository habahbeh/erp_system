# apps/assets/views/depreciation_views.py
"""
Views إدارة الإهلاك
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
import json
from datetime import date, timedelta
from decimal import Decimal

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import Asset, AssetDepreciation
from apps.accounting.models import FiscalYear, AccountingPeriod


class AssetDepreciationListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سجلات الإهلاك"""

    model = AssetDepreciation
    template_name = 'assets/depreciation/depreciation_list.html'
    context_object_name = 'depreciation_records'
    permission_required = 'assets.view_asset'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetDepreciation.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'fiscal_year',
            'period', 'created_by', 'journal_entry'
        )

        # الفلترة
        asset = self.request.GET.get('asset')
        fiscal_year = self.request.GET.get('fiscal_year')
        period = self.request.GET.get('period')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        is_posted = self.request.GET.get('is_posted')

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if fiscal_year:
            queryset = queryset.filter(fiscal_year_id=fiscal_year)

        if period:
            queryset = queryset.filter(period_id=period)

        if date_from:
            queryset = queryset.filter(depreciation_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(depreciation_date__lte=date_to)

        if is_posted:
            queryset = queryset.filter(is_posted=(is_posted == '1'))

        return queryset.order_by('-depreciation_date', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # السنوات المالية
        fiscal_years = FiscalYear.objects.filter(
            company=self.request.current_company
        ).order_by('-start_date')

        # إحصائيات
        stats = self.get_queryset().aggregate(
            total_depreciation=Sum('depreciation_amount'),
            count=Count('id')
        )

        context.update({
            'title': _('سجلات الإهلاك'),
            'can_calculate': self.request.user.has_perm('assets.can_calculate_depreciation'),
            'fiscal_years': fiscal_years,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الإهلاك'), 'url': ''},
            ]
        })
        return context


class AssetDepreciationDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل سجل الإهلاك"""

    model = AssetDepreciation
    template_name = 'assets/depreciation/depreciation_detail.html'
    context_object_name = 'depreciation'
    permission_required = 'assets.view_asset'

    def get_queryset(self):
        return AssetDepreciation.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'fiscal_year',
            'period', 'created_by', 'journal_entry'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'سجل إهلاك - {self.object.asset.asset_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الإهلاك'), 'url': reverse('assets:depreciation_list')},
                {'title': f'{self.object.asset.asset_number}', 'url': ''},
            ]
        })
        return context


class CalculateDepreciationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """احتساب إهلاك أصل واحد"""

    template_name = 'assets/depreciation/calculate_depreciation.html'
    permission_required = 'assets.can_calculate_depreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asset_id = self.request.GET.get('asset_id') or self.kwargs.get('asset_id')
        asset = None

        if asset_id:
            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=self.request.current_company
            )

        context.update({
            'title': _('احتساب الإهلاك'),
            'asset': asset,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('احتساب الإهلاك'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            asset_id = request.POST.get('asset_id')

            if not asset_id:
                messages.error(request, 'يجب تحديد الأصل')
                return redirect('assets:calculate_depreciation')

            asset = get_object_or_404(
                Asset,
                pk=asset_id,
                company=request.current_company
            )

            # احتساب الإهلاك
            depreciation_record = asset.calculate_monthly_depreciation(user=request.user)

            messages.success(
                request,
                f'تم احتساب إهلاك الأصل {asset.asset_number} بمبلغ {depreciation_record.depreciation_amount:,.2f} بنجاح'
            )

            return redirect('assets:depreciation_detail', pk=depreciation_record.pk)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('assets:calculate_depreciation')

        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('assets:asset_list')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'خطأ في احتساب الإهلاك: {str(e)}')
            return redirect('assets:calculate_depreciation')


class BulkDepreciationCalculationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """احتساب الإهلاك الجماعي"""

    template_name = 'assets/depreciation/bulk_calculate.html'
    permission_required = 'assets.can_calculate_depreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الأصول المؤهلة للإهلاك
        eligible_assets = Asset.objects.filter(
            company=self.request.current_company,
            status='active',
            depreciation_status='active'
        ).exclude(
            depreciation_method__method_type='units_of_production'
        ).count()

        context.update({
            'title': _('احتساب الإهلاك الجماعي'),
            'eligible_assets': eligible_assets,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('احتساب الإهلاك الجماعي'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            category_id = request.POST.get('category_id')
            branch_id = request.POST.get('branch_id')

            # الأصول المؤهلة
            assets = Asset.objects.filter(
                company=request.current_company,
                status='active',
                depreciation_status='active'
            ).exclude(
                depreciation_method__method_type='units_of_production'
            )

            if category_id:
                assets = assets.filter(category_id=category_id)

            if branch_id:
                assets = assets.filter(branch_id=branch_id)

            # احتساب الإهلاك لكل أصل
            success_count = 0
            error_count = 0
            errors = []

            for asset in assets:
                try:
                    asset.calculate_monthly_depreciation(user=request.user)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"{asset.asset_number}: {str(e)}")

            # الرسائل
            if success_count > 0:
                messages.success(
                    request,
                    f'تم احتساب الإهلاك لـ {success_count} أصل بنجاح'
                )

            if error_count > 0:
                messages.warning(
                    request,
                    f'فشل احتساب {error_count} أصل. الأخطاء: {", ".join(errors[:5])}'
                )

            return redirect('assets:depreciation_list')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'خطأ في الاحتساب الجماعي: {str(e)}')
            return redirect('assets:bulk_calculate_depreciation')


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_datatable_ajax(request):
    """Ajax endpoint لجدول سجلات الإهلاك"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    is_posted = request.GET.get('is_posted', '')
    fiscal_year = request.GET.get('fiscal_year', '')

    try:
        queryset = AssetDepreciation.objects.filter(
            company=request.current_company
        ).select_related('asset', 'fiscal_year', 'period', 'journal_entry')

        # تطبيق الفلاتر
        if is_posted:
            queryset = queryset.filter(is_posted=(is_posted == '1'))

        if fiscal_year:
            queryset = queryset.filter(fiscal_year_id=fiscal_year)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-depreciation_date', '-id')

        total_records = AssetDepreciation.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_view = request.user.has_perm('assets.view_asset')

        for dep in queryset:
            # الحالة
            if dep.is_posted:
                status_badge = '<span class="badge bg-success">مرحّل</span>'
            else:
                status_badge = '<span class="badge bg-warning">غير مرحّل</span>'

            # أزرار الإجراءات
            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('assets:depreciation_detail', args=[dep.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            if dep.journal_entry:
                actions.append(f'''
                    <a href="{reverse('accounting:journal_entry_detail', args=[dep.journal_entry.pk])}" 
                       class="btn btn-outline-secondary btn-sm" title="القيد" data-bs-toggle="tooltip">
                        <i class="fas fa-file-invoice"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                dep.depreciation_date.strftime('%Y-%m-%d'),
                dep.asset.asset_number,
                dep.asset.name,
                f"{dep.depreciation_amount:,.2f}",
                f"{dep.accumulated_depreciation_after:,.2f}",
                f"{dep.book_value_after:,.2f}",
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_schedule_ajax(request):
    """جدول الإهلاك المستقبلي لأصل معين"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    asset_id = request.GET.get('asset_id')

    if not asset_id:
        return JsonResponse({'error': 'يجب تحديد الأصل'}, status=400)

    try:
        asset = get_object_or_404(
            Asset,
            pk=asset_id,
            company=request.current_company
        )

        # حساب جدول الإهلاك المستقبلي
        schedule = []
        remaining_months = asset.get_remaining_months()

        if asset.depreciation_method.method_type == 'straight_line':
            depreciable_amount = asset.get_depreciable_amount()
            monthly_depreciation = depreciable_amount / asset.useful_life_months

            current_accumulated = asset.accumulated_depreciation
            current_book_value = asset.book_value

            from dateutil.relativedelta import relativedelta
            current_date = date.today()

            for i in range(min(remaining_months, 24)):  # أول 24 شهر
                month_date = current_date + relativedelta(months=i)

                # التأكد من عدم تجاوز المبلغ القابل للإهلاك
                remaining = depreciable_amount - current_accumulated
                if monthly_depreciation > remaining:
                    monthly_depreciation = remaining

                if monthly_depreciation <= 0:
                    break

                current_accumulated += monthly_depreciation
                current_book_value -= monthly_depreciation

                schedule.append({
                    'month': month_date.strftime('%Y-%m'),
                    'depreciation_amount': float(monthly_depreciation),
                    'accumulated_depreciation': float(current_accumulated),
                    'book_value': float(current_book_value)
                })

        elif asset.depreciation_method.method_type == 'declining_balance':
            rate = asset.depreciation_method.rate_percentage / 100

            current_accumulated = asset.accumulated_depreciation
            current_book_value = asset.book_value

            from dateutil.relativedelta import relativedelta
            current_date = date.today()

            for i in range(min(remaining_months, 24)):
                month_date = current_date + relativedelta(months=i)

                monthly_depreciation = current_book_value * (rate / 12)

                # التأكد من عدم تجاوز المبلغ القابل للإهلاك
                depreciable_amount = asset.get_depreciable_amount()
                remaining = depreciable_amount - current_accumulated

                if monthly_depreciation > remaining:
                    monthly_depreciation = remaining

                if monthly_depreciation <= 0:
                    break

                current_accumulated += monthly_depreciation
                current_book_value -= monthly_depreciation

                schedule.append({
                    'month': month_date.strftime('%Y-%m'),
                    'depreciation_amount': float(monthly_depreciation),
                    'accumulated_depreciation': float(current_accumulated),
                    'book_value': float(current_book_value)
                })

        return JsonResponse({
            'success': True,
            'schedule': schedule,
            'asset': {
                'asset_number': asset.asset_number,
                'name': asset.name,
                'current_book_value': float(asset.book_value),
                'remaining_months': remaining_months
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'خطأ في حساب جدول الإهلاك: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_calculate_depreciation')
@require_http_methods(["POST"])
def calculate_single_depreciation_ajax(request, pk):
    """احتساب إهلاك أصل واحد عبر Ajax"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=pk,
            company=request.current_company
        )

        # احتساب الإهلاك
        depreciation_record = asset.calculate_monthly_depreciation(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم احتساب الإهلاك بنجاح',
            'depreciation_amount': float(depreciation_record.depreciation_amount),
            'book_value': float(depreciation_record.book_value_after),
            'journal_entry_number': depreciation_record.journal_entry.number if depreciation_record.journal_entry else None,
            'depreciation_id': depreciation_record.pk
        })

    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=403)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في احتساب الإهلاك: {str(e)}'
        }, status=500)
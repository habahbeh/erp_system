# apps/assets/views/depreciation_views.py
"""
Views الإهلاك
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import FormView, TemplateView
from django.db.models import Q, Sum
from django.db import transaction as db_transaction
from decimal import Decimal
import datetime

from ..models import Asset, AssetDepreciation
from ..forms import AssetDepreciationCalculationForm
from ..utils import DepreciationCalculator, generate_depreciation_journal_entry
from apps.core.mixins import CompanyMixin


class DepreciationCalculationView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """احتساب الإهلاك"""

    template_name = 'assets/depreciation/calculation_form.html'
    form_class = AssetDepreciationCalculationForm
    permission_required = 'assets.can_calculate_depreciation'
    success_url = reverse_lazy('assets:depreciation_history')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    @db_transaction.atomic
    def form_valid(self, form):
        calculation_date = form.cleaned_data['calculation_date']
        selected_assets = form.cleaned_data.get('assets')
        units_used = form.cleaned_data.get('units_used')

        company = self.request.user.company
        branch = self.request.user.branch

        # إذا لم يتم تحديد أصول، احتسب للجميع
        if not selected_assets:
            assets = Asset.objects.filter(
                company=company,
                status='active',
                is_active=True
            )
        else:
            assets = selected_assets

        depreciation_records = []
        total_depreciation = Decimal('0.00')
        errors = []

        for asset in assets:
            try:
                # التحقق من عدم وجود إهلاك لنفس التاريخ
                existing = AssetDepreciation.objects.filter(
                    asset=asset,
                    depreciation_date=calculation_date
                ).exists()

                if existing:
                    errors.append(f'{asset.asset_number}: يوجد إهلاك مسجل لهذا التاريخ')
                    continue

                # احتساب الإهلاك
                calculator = DepreciationCalculator(asset)

                # لوحدات الإنتاج
                if asset.depreciation_method.method_type == 'units_of_production':
                    if units_used:
                        depreciation_amount = calculator._units_of_production_method(units_used)
                    else:
                        errors.append(f'{asset.asset_number}: يجب تحديد الوحدات المستخدمة')
                        continue
                else:
                    depreciation_amount = calculator.calculate_monthly_depreciation(calculation_date)

                # إذا كان الإهلاك صفر (أصل مهلك بالكامل)
                if depreciation_amount == Decimal('0.00'):
                    errors.append(f'{asset.asset_number}: الأصل مهلك بالكامل')
                    continue

                # إنشاء سجل الإهلاك
                accumulated_before = asset.accumulated_depreciation
                accumulated_after = accumulated_before + depreciation_amount
                book_value_after = asset.original_cost - accumulated_after

                depreciation_record = AssetDepreciation.objects.create(
                    asset=asset,
                    depreciation_date=calculation_date,
                    depreciation_amount=depreciation_amount,
                    accumulated_depreciation_before=accumulated_before,
                    accumulated_depreciation_after=accumulated_after,
                    book_value_after=book_value_after,
                    units_used_in_period=units_used if asset.depreciation_method.method_type == 'units_of_production' else None,
                    calculated_by=self.request.user
                )

                # تحديث الأصل
                asset.accumulated_depreciation = accumulated_after
                asset.book_value = book_value_after
                if units_used and asset.depreciation_method.method_type == 'units_of_production':
                    asset.units_used += units_used
                asset.save()

                depreciation_records.append(depreciation_record)
                total_depreciation += depreciation_amount

            except Exception as e:
                errors.append(f'{asset.asset_number}: {str(e)}')

        # توليد القيد المحاسبي الموحد
        if depreciation_records:
            try:
                journal_entry = generate_depreciation_journal_entry(
                    company,
                    branch,
                    calculation_date,
                    depreciation_records
                )

                # ربط القيد بسجلات الإهلاك
                for record in depreciation_records:
                    record.journal_entry = journal_entry
                    record.save()

                messages.success(
                    self.request,
                    f'تم احتساب الإهلاك بنجاح لـ {len(depreciation_records)} أصل - '
                    f'إجمالي الإهلاك: {total_depreciation:,.3f} - '
                    f'القيد رقم: {journal_entry.number}'
                )
            except Exception as e:
                messages.warning(
                    self.request,
                    f'تم احتساب الإهلاك ولكن فشل توليد القيد المحاسبي: {str(e)}'
                )
        else:
            messages.warning(
                self.request,
                'لم يتم احتساب إهلاك لأي أصل'
            )

        # عرض الأخطاء
        if errors:
            for error in errors:
                messages.warning(self.request, error)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'احتساب الإهلاك',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'احتساب الإهلاك', 'url': ''}
            ],
        })
        return context


class DepreciationHistoryView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """سجل الإهلاك"""

    template_name = 'assets/depreciation/history_list.html'
    permission_required = 'assets.view_assetdepreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        company = self.request.user.company

        total_stats = AssetDepreciation.objects.filter(
            asset__company=company
        ).aggregate(
            total_depreciation=Sum('depreciation_amount'),
            count=Sum('id')
        )

        # هذا الشهر
        today = datetime.date.today()
        this_month_stats = AssetDepreciation.objects.filter(
            asset__company=company,
            depreciation_date__year=today.year,
            depreciation_date__month=today.month
        ).aggregate(
            total=Sum('depreciation_amount'),
            count=Sum('id')
        )

        context.update({
            'title': 'سجل الإهلاك',
            'total_depreciation': total_stats['total_depreciation'] or Decimal('0'),
            'total_count': total_stats['count'] or 0,
            'this_month_depreciation': this_month_stats['total'] or Decimal('0'),
            'this_month_count': this_month_stats['count'] or 0,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الإهلاك', 'url': ''}
            ],
        })

        return context


@login_required
@permission_required('assets.view_assetdepreciation', raise_exception=True)
def depreciation_history_ajax(request):
    """Ajax endpoint لسجل الإهلاك"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    asset_id = request.GET.get('asset', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    queryset = AssetDepreciation.objects.filter(
        asset__company=request.user.company
    ).select_related('asset', 'calculated_by', 'journal_entry')

    # البحث
    if search_value:
        queryset = queryset.filter(
            Q(asset__asset_number__icontains=search_value) |
            Q(asset__name__icontains=search_value)
        )

    # الفلاتر
    if asset_id:
        queryset = queryset.filter(asset_id=asset_id)

    if date_from:
        queryset = queryset.filter(depreciation_date__gte=date_from)

    if date_to:
        queryset = queryset.filter(depreciation_date__lte=date_to)

    total_records = AssetDepreciation.objects.filter(asset__company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('-depreciation_date')[start:start + length]

    data = []
    for record in queryset:
        # القيد المحاسبي
        journal_link = ''
        if record.journal_entry:
            journal_link = f'<a href="#" class="badge bg-success">{record.journal_entry.number}</a>'
        else:
            journal_link = '<span class="badge bg-secondary">-</span>'

        data.append([
            record.depreciation_date.strftime('%Y-%m-%d'),
            f'<strong>{record.asset.asset_number}</strong><br><small>{record.asset.name}</small>',
            record.asset.category.name if record.asset.category else '-',
            f'{record.depreciation_amount:,.3f}',
            f'{record.accumulated_depreciation_after:,.3f}',
            f'{record.book_value_after:,.3f}',
            journal_link,
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })
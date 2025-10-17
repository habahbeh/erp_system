# apps/assets/views/report_views.py
"""
Views التقارير
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from decimal import Decimal
import datetime

from ..models import Asset, AssetDepreciation, AssetMaintenance, AssetTransaction
from apps.core.mixins import CompanyMixin


class AssetRegisterReportView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """تقرير سجل الأصول الثابتة"""

    template_name = 'assets/reports/asset_register.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        # الفلاتر من GET
        category_id = self.request.GET.get('category', '')
        status = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        # الاستعلام الأساسي
        assets = Asset.objects.filter(
            company=company
        ).select_related(
            'category', 'condition', 'depreciation_method',
            'branch', 'cost_center'
        )

        # تطبيق الفلاتر
        if category_id:
            assets = assets.filter(category_id=category_id)

        if status:
            assets = assets.filter(status=status)

        if date_from:
            assets = assets.filter(purchase_date__gte=date_from)

        if date_to:
            assets = assets.filter(purchase_date__lte=date_to)

        # الإحصائيات
        totals = assets.aggregate(
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        )

        # حسب الفئة
        by_category = assets.values(
            'category__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        ).order_by('category__name')

        context.update({
            'title': 'تقرير سجل الأصول الثابتة',
            'assets': assets,
            'totals': totals,
            'by_category': by_category,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التقارير', 'url': ''},
                {'title': 'سجل الأصول', 'url': ''}
            ],
        })

        return context


class DepreciationReportView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الإهلاك"""

    template_name = 'assets/reports/depreciation_report.html'
    permission_required = 'assets.view_assetdepreciation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        # الفلاتر
        year = self.request.GET.get('year', datetime.date.today().year)
        month = self.request.GET.get('month', '')
        category_id = self.request.GET.get('category', '')

        # الاستعلام
        depreciations = AssetDepreciation.objects.filter(
            asset__company=company,
            depreciation_date__year=year
        ).select_related('asset', 'asset__category')

        if month:
            depreciations = depreciations.filter(depreciation_date__month=month)

        if category_id:
            depreciations = depreciations.filter(asset__category_id=category_id)

        # الإحصائيات
        total_depreciation = depreciations.aggregate(
            total=Sum('depreciation_amount')
        )['total'] or Decimal('0')

        # حسب الشهر
        by_month = depreciations.values(
            'depreciation_date__month'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('depreciation_date__month')

        # حسب الفئة
        by_category = depreciations.values(
            'asset__category__name'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('asset__category__name')

        context.update({
            'title': f'تقرير الإهلاك - {year}',
            'depreciations': depreciations,
            'total_depreciation': total_depreciation,
            'by_month': by_month,
            'by_category': by_category,
            'year': year,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التقارير', 'url': ''},
                {'title': 'تقرير الإهلاك', 'url': ''}
            ],
        })

        return context


class MaintenanceReportView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الصيانة"""

    template_name = 'assets/reports/maintenance_report.html'
    permission_required = 'assets.view_assetmaintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        # الفلاتر
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        asset_id = self.request.GET.get('asset', '')
        status = self.request.GET.get('status', '')

        # الاستعلام
        maintenances = AssetMaintenance.objects.filter(
            company=company
        ).select_related('asset', 'maintenance_type')

        if date_from:
            maintenances = maintenances.filter(scheduled_date__gte=date_from)

        if date_to:
            maintenances = maintenances.filter(scheduled_date__lte=date_to)

        if asset_id:
            maintenances = maintenances.filter(asset_id=asset_id)

        if status:
            maintenances = maintenances.filter(status=status)

        # الإحصائيات
        total_cost = maintenances.filter(status='completed').aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')

        total_count = maintenances.count()
        completed_count = maintenances.filter(status='completed').count()

        # حسب الأصل
        by_asset = maintenances.values(
            'asset__asset_number',
            'asset__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-total_cost')[:10]

        # حسب النوع
        by_type = maintenances.values(
            'maintenance_type__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-count')

        context.update({
            'title': 'تقرير الصيانة',
            'maintenances': maintenances,
            'total_cost': total_cost,
            'total_count': total_count,
            'completed_count': completed_count,
            'by_asset': by_asset,
            'by_type': by_type,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التقارير', 'url': ''},
                {'title': 'تقرير الصيانة', 'url': ''}
            ],
        })

        return context


class AssetMovementReportView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """تقرير حركة الأصول"""

    template_name = 'assets/reports/movement_report.html'
    permission_required = 'assets.view_assettransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        # الفلاتر
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        transaction_type = self.request.GET.get('transaction_type', '')

        # الاستعلام
        transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related('asset', 'branch')

        if date_from:
            transactions = transactions.filter(transaction_date__gte=date_from)

        if date_to:
            transactions = transactions.filter(transaction_date__lte=date_to)

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        # الإحصائيات
        total_amount = transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # حسب النوع
        by_type = transactions.values(
            'transaction_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # عمليات الشراء
        purchases = transactions.filter(transaction_type='purchase')
        purchase_total = purchases.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # عمليات البيع
        sales = transactions.filter(transaction_type='sale')
        sale_total = sales.aggregate(total=Sum('sale_price'))['total'] or Decimal('0')
        total_gain_loss = sales.aggregate(total=Sum('gain_loss'))['total'] or Decimal('0')

        context.update({
            'title': 'تقرير حركة الأصول',
            'transactions': transactions,
            'total_amount': total_amount,
            'by_type': by_type,
            'purchase_count': purchases.count(),
            'purchase_total': purchase_total,
            'sale_count': sales.count(),
            'sale_total': sale_total,
            'total_gain_loss': total_gain_loss,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التقارير', 'url': ''},
                {'title': 'تقرير الحركة', 'url': ''}
            ],
        })

        return context
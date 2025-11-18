# apps/core/views/chart_views.py
"""
Chart Views for Pricing Visualizations
Provides JSON data endpoints for Chart.js charts
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from apps.core.models import (
    PricingRule, PriceList, Item, ItemCategory
)
from apps.core.utils.chart_data_builder import ChartDataBuilder


class PriceTrendChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for price trend chart data
    """

    def get(self, request, *args, **kwargs):
        """
        Get price trend data for an item

        Query params:
            - item_id: Item ID (required)
            - price_list_id: Price list ID (optional)
            - days: Number of days (default 30)
        """
        item_id = request.GET.get('item_id')
        price_list_id = request.GET.get('price_list_id')
        days = int(request.GET.get('days', 30))

        if not item_id:
            return JsonResponse({
                'success': False,
                'error': _('معرف الصنف مطلوب')
            }, status=400)

        try:
            item = get_object_or_404(Item, id=item_id, company=request.current_company)
            price_list = None

            if price_list_id:
                price_list = get_object_or_404(
                    PriceList,
                    id=price_list_id,
                    company=request.current_company
                )

            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_price_trend_data(
                item=item,
                price_list=price_list,
                days=days
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PriceDistributionChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for price distribution histogram
    """

    def get(self, request, *args, **kwargs):
        """
        Get price distribution data

        Query params:
            - price_list_id: Price list ID (required)
            - category_id: Category ID (optional)
        """
        price_list_id = request.GET.get('price_list_id')
        category_id = request.GET.get('category_id')

        if not price_list_id:
            return JsonResponse({
                'success': False,
                'error': _('معرف قائمة الأسعار مطلوب')
            }, status=400)

        try:
            price_list = get_object_or_404(
                PriceList,
                id=price_list_id,
                company=request.current_company
            )

            category = None
            if category_id:
                category = get_object_or_404(
                    ItemCategory,
                    id=category_id,
                    company=request.current_company
                )

            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_price_distribution_data(
                price_list=price_list,
                category=category
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CategoryPriceComparisonChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for category price comparison chart
    """

    def get(self, request, *args, **kwargs):
        """
        Get category price comparison data

        Query params:
            - price_list_id: Price list ID (required)
            - category_ids: Comma-separated category IDs (optional)
        """
        price_list_id = request.GET.get('price_list_id')
        category_ids = request.GET.get('category_ids', '')

        if not price_list_id:
            return JsonResponse({
                'success': False,
                'error': _('معرف قائمة الأسعار مطلوب')
            }, status=400)

        try:
            price_list = get_object_or_404(
                PriceList,
                id=price_list_id,
                company=request.current_company
            )

            categories = None
            if category_ids:
                category_id_list = [int(cid) for cid in category_ids.split(',')]
                categories = ItemCategory.objects.filter(
                    id__in=category_id_list,
                    company=request.current_company
                )

            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_category_price_comparison(
                price_list=price_list,
                categories=categories
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PriceListComparisonChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for price list comparison chart
    """

    def get(self, request, *args, **kwargs):
        """
        Get price list comparison data for an item

        Query params:
            - item_id: Item ID (required)
            - price_list_ids: Comma-separated price list IDs (optional)
        """
        item_id = request.GET.get('item_id')
        price_list_ids = request.GET.get('price_list_ids', '')

        if not item_id:
            return JsonResponse({
                'success': False,
                'error': _('معرف الصنف مطلوب')
            }, status=400)

        try:
            item = get_object_or_404(Item, id=item_id, company=request.current_company)

            price_lists = None
            if price_list_ids:
                price_list_id_list = [int(plid) for plid in price_list_ids.split(',')]
                price_lists = PriceList.objects.filter(
                    id__in=price_list_id_list,
                    company=request.current_company
                )

            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_price_list_comparison_data(
                item=item,
                price_lists=price_lists
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PricingRulesImpactChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for pricing rules impact chart
    """

    def get(self, request, *args, **kwargs):
        """
        Get pricing rules impact data

        Query params:
            - active_only: Boolean (default true)
        """
        active_only = request.GET.get('active_only', 'true').lower() == 'true'

        try:
            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_pricing_rules_impact_data(
                active_only=active_only
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PriceStatisticsSummaryView(LoginRequiredMixin, View):
    """
    AJAX endpoint for price statistics summary
    """

    def get(self, request, *args, **kwargs):
        """
        Get price statistics summary

        Query params:
            - price_list_id: Price list ID (optional)
            - category_id: Category ID (optional)
        """
        price_list_id = request.GET.get('price_list_id')
        category_id = request.GET.get('category_id')

        try:
            price_list = None
            if price_list_id:
                price_list = get_object_or_404(
                    PriceList,
                    id=price_list_id,
                    company=request.current_company
                )

            category = None
            if category_id:
                category = get_object_or_404(
                    ItemCategory,
                    id=category_id,
                    company=request.current_company
                )

            builder = ChartDataBuilder(request.current_company)
            stats = builder.get_price_statistics_summary(
                price_list=price_list,
                category=category
            )

            return JsonResponse({
                'success': True,
                'data': stats
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class MonthlyPriceChangesChartView(LoginRequiredMixin, View):
    """
    AJAX endpoint for monthly price changes chart
    """

    def get(self, request, *args, **kwargs):
        """
        Get monthly price changes data

        Query params:
            - months: Number of months (default 12)
        """
        months = int(request.GET.get('months', 12))

        try:
            builder = ChartDataBuilder(request.current_company)
            chart_data = builder.get_monthly_price_changes_data(
                months=months
            )

            return JsonResponse({
                'success': True,
                'data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

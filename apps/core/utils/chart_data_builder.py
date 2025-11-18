# apps/core/utils/chart_data_builder.py
"""
Chart Data Builder Utility
Prepares data for Chart.js visualizations in the pricing system
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.db.models import Count, Avg, Min, Max, Sum, Q
from django.utils.translation import gettext as _

from apps.core.models import (
    PricingRule, PriceList, PriceListItem, Item,
    ItemCategory, Company
)


class ChartDataBuilder:
    """
    Builds chart data for various pricing visualizations
    """

    def __init__(self, company: Company):
        """
        Initialize chart data builder

        Args:
            company: Company instance for data filtering
        """
        self.company = company

    def get_price_trend_data(
        self,
        item: Item,
        price_list: Optional[PriceList] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get price trend data for an item over time

        Args:
            item: Item to analyze
            price_list: Specific price list (None for all lists)
            days: Number of days to look back

        Returns:
            Dict with labels, datasets for Chart.js line chart
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get price history (we'll simulate this as we don't have audit trail yet)
        prices_query = PriceListItem.objects.filter(
            item=item,
            item__company=self.company
        )

        if price_list:
            prices_query = prices_query.filter(price_list=price_list)

        prices = prices_query.select_related('price_list', 'uom')

        # Build datasets by price list
        datasets = []
        colors = [
            'rgb(75, 192, 192)',   # Teal
            'rgb(255, 99, 132)',   # Red
            'rgb(54, 162, 235)',   # Blue
            'rgb(255, 206, 86)',   # Yellow
            'rgb(153, 102, 255)',  # Purple
        ]

        price_lists = {}
        for price_item in prices:
            pl_id = price_item.price_list.id
            if pl_id not in price_lists:
                price_lists[pl_id] = {
                    'name': price_item.price_list.name,
                    'prices': []
                }
            price_lists[pl_id]['prices'].append({
                'date': price_item.updated_at.date() if hasattr(price_item, 'updated_at') else end_date,
                'price': float(price_item.price)
            })

        # Generate labels (dates)
        labels = []
        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        # Build datasets
        for idx, (pl_id, pl_data) in enumerate(price_lists.items()):
            color = colors[idx % len(colors)]

            # For now, use current price across all dates
            # In production, this would use actual price history
            current_price = pl_data['prices'][0]['price'] if pl_data['prices'] else 0

            datasets.append({
                'label': pl_data['name'],
                'data': [current_price] * len(labels),  # Simplified for now
                'borderColor': color,
                'backgroundColor': color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
                'tension': 0.4,
                'fill': True
            })

        return {
            'labels': labels,
            'datasets': datasets
        }

    def get_price_distribution_data(
        self,
        price_list: PriceList,
        category: Optional[ItemCategory] = None
    ) -> Dict[str, Any]:
        """
        Get price distribution data for histogram/bar chart

        Args:
            price_list: Price list to analyze
            category: Optional category filter

        Returns:
            Dict with price range distribution data
        """
        prices_query = PriceListItem.objects.filter(
            price_list=price_list,
            item__company=self.company
        )

        if category:
            prices_query = prices_query.filter(item__category=category)

        prices = prices_query.values_list('price', flat=True)

        if not prices:
            return {
                'labels': [],
                'datasets': []
            }

        # Calculate price ranges
        min_price = float(min(prices))
        max_price = float(max(prices))

        # Create 10 equal ranges
        range_size = (max_price - min_price) / 10
        ranges = []
        range_labels = []

        for i in range(10):
            range_start = min_price + (i * range_size)
            range_end = range_start + range_size

            count = sum(1 for p in prices if range_start <= float(p) < range_end)
            ranges.append(count)
            range_labels.append(f'{range_start:.0f}-{range_end:.0f}')

        return {
            'labels': range_labels,
            'datasets': [{
                'label': _('عدد الأصناف'),
                'data': ranges,
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgb(54, 162, 235)',
                'borderWidth': 1
            }]
        }

    def get_category_price_comparison(
        self,
        price_list: PriceList,
        categories: Optional[List[ItemCategory]] = None
    ) -> Dict[str, Any]:
        """
        Compare average prices across categories

        Args:
            price_list: Price list to analyze
            categories: List of categories (None for all)

        Returns:
            Dict with category comparison data for bar chart
        """
        if categories is None:
            categories = ItemCategory.objects.filter(
                company=self.company,
                is_active=True
            )[:10]  # Limit to 10 categories

        labels = []
        avg_prices = []
        item_counts = []

        for category in categories:
            prices = PriceListItem.objects.filter(
                price_list=price_list,
                item__category=category,
                item__company=self.company
            ).values_list('price', flat=True)

            if prices:
                labels.append(category.name)
                avg_prices.append(float(sum(prices) / len(prices)))
                item_counts.append(len(prices))

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': _('متوسط السعر'),
                    'data': avg_prices,
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgb(75, 192, 192)',
                    'borderWidth': 1,
                    'yAxisID': 'y'
                },
                {
                    'label': _('عدد الأصناف'),
                    'data': item_counts,
                    'backgroundColor': 'rgba(255, 206, 86, 0.6)',
                    'borderColor': 'rgb(255, 206, 86)',
                    'borderWidth': 1,
                    'yAxisID': 'y1'
                }
            ]
        }

    def get_price_list_comparison_data(
        self,
        item: Item,
        price_lists: Optional[List[PriceList]] = None
    ) -> Dict[str, Any]:
        """
        Compare item prices across different price lists

        Args:
            item: Item to compare
            price_lists: List of price lists (None for all)

        Returns:
            Dict with comparison data for radar/bar chart
        """
        if price_lists is None:
            price_lists = PriceList.objects.filter(
                company=self.company,
                is_active=True
            )[:6]  # Limit to 6 price lists

        labels = []
        prices = []
        colors = []

        color_palette = [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)',
        ]

        for idx, price_list in enumerate(price_lists):
            try:
                price_item = PriceListItem.objects.get(
                    item=item,
                    price_list=price_list
                )
                labels.append(price_list.name)
                prices.append(float(price_item.price))
                colors.append(color_palette[idx % len(color_palette)])
            except PriceListItem.DoesNotExist:
                continue

        return {
            'labels': labels,
            'datasets': [{
                'label': _('السعر'),
                'data': prices,
                'backgroundColor': colors,
                'borderColor': [c.replace('0.6', '1') for c in colors],
                'borderWidth': 2
            }]
        }

    def get_pricing_rules_impact_data(
        self,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze impact of pricing rules by type

        Args:
            active_only: Only include active rules

        Returns:
            Dict with rule type distribution for pie chart
        """
        rules_query = PricingRule.objects.filter(company=self.company)

        if active_only:
            rules_query = rules_query.filter(is_active=True)

        rule_types = rules_query.values('rule_type').annotate(
            count=Count('id')
        ).order_by('-count')

        type_labels = {
            'DISCOUNT_PERCENTAGE': _('خصم نسبة مئوية'),
            'DISCOUNT_AMOUNT': _('خصم مبلغ ثابت'),
            'MARKUP_PERCENTAGE': _('هامش ربح نسبي'),
            'MARKUP_AMOUNT': _('هامش ربح ثابت'),
            'BULK_DISCOUNT': _('خصم الكميات'),
            'CUSTOM_FORMULA': _('معادلة مخصصة'),
        }

        labels = []
        data = []
        background_colors = [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)',
        ]

        for idx, rule_type_data in enumerate(rule_types):
            rule_type = rule_type_data['rule_type']
            labels.append(type_labels.get(rule_type, rule_type))
            data.append(rule_type_data['count'])

        return {
            'labels': labels,
            'datasets': [{
                'label': _('عدد القواعد'),
                'data': data,
                'backgroundColor': background_colors[:len(labels)],
                'borderColor': [c.replace('0.6', '1') for c in background_colors[:len(labels)]],
                'borderWidth': 2
            }]
        }

    def get_price_statistics_summary(
        self,
        price_list: Optional[PriceList] = None,
        category: Optional[ItemCategory] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for pricing dashboard

        Args:
            price_list: Optional price list filter
            category: Optional category filter

        Returns:
            Dict with statistical summary data
        """
        prices_query = PriceListItem.objects.filter(
            item__company=self.company
        )

        if price_list:
            prices_query = prices_query.filter(price_list=price_list)

        if category:
            prices_query = prices_query.filter(item__category=category)

        prices = prices_query.values_list('price', flat=True)

        if not prices:
            return {
                'total_items': 0,
                'avg_price': 0,
                'min_price': 0,
                'max_price': 0,
                'total_value': 0,
                'price_lists_count': 0
            }

        return {
            'total_items': len(prices),
            'avg_price': float(sum(prices) / len(prices)),
            'min_price': float(min(prices)),
            'max_price': float(max(prices)),
            'total_value': float(sum(prices)),
            'price_lists_count': PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).count()
        }

    def get_monthly_price_changes_data(
        self,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Get monthly price change statistics

        Args:
            months: Number of months to analyze

        Returns:
            Dict with monthly change data for line chart
        """
        # Generate month labels
        labels = []
        end_date = datetime.now().date()

        for i in range(months):
            month_date = end_date - timedelta(days=30 * i)
            labels.insert(0, month_date.strftime('%Y-%m'))

        # For now, return placeholder data
        # In production, this would track actual price changes
        return {
            'labels': labels,
            'datasets': [{
                'label': _('عدد التعديلات'),
                'data': [0] * months,  # Placeholder
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        }

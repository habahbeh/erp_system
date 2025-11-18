# apps/core/utils/price_calculator.py
"""
⭐ Week 3 Day 3: Price Calculator & Bulk Operations

أدوات متقدمة لحساب وإدارة الأسعار بالجملة - Advanced Price Calculation Tools

Features:
- Bulk price calculation
- Price simulation before applying
- Price comparison across lists
- What-if analysis
- Mass price updates
- Price report generation

Author: Claude Code
Created: Week 3 Day 3
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from datetime import date
from django.db.models import Q, Count, Avg, Min, Max
from django.utils import timezone
from django.db import transaction

from apps.core.models import (
    Item,
    ItemVariant,
    PriceList,
    PriceListItem,
    PricingRule,
    UnitOfMeasure,
    ItemCategory
)
from apps.core.utils.pricing_engine import PricingEngine


class PriceCalculator:
    """
    ⭐ حاسبة الأسعار المتقدمة - Advanced Price Calculator

    Responsibilities:
    1. Bulk price calculations
    2. Price simulations
    3. Price comparisons
    4. Mass updates
    5. What-if analysis
    6. Price reports

    Usage:
        calculator = PriceCalculator(company)

        # Calculate all prices for an item
        prices = calculator.calculate_all_prices(item, variant)

        # Simulate price changes
        simulation = calculator.simulate_price_change(rule, items)

        # Compare prices across lists
        comparison = calculator.compare_price_lists(items)
    """

    def __init__(self, company):
        """
        Initialize price calculator

        Args:
            company: الشركة
        """
        self.company = company
        self.engine = PricingEngine(company)
        self._cache = {}

    def calculate_all_prices(
        self,
        item,
        variant=None,
        include_uoms=True
    ) -> Dict:
        """
        ⭐ حساب جميع الأسعار لمادة معينة

        يحسب الأسعار عبر:
        - جميع قوائم الأسعار
        - جميع وحدات القياس (إذا طلب)
        - تطبيق جميع قواعد التسعير

        Args:
            item: المادة
            variant: المتغير (اختياري)
            include_uoms: هل نحسب لجميع وحدات القياس؟

        Returns:
            Dict: {
                'item': {...},
                'variant': {...},
                'price_lists': [
                    {
                        'price_list': {...},
                        'uoms': [
                            {
                                'uom': {...},
                                'prices': {
                                    'base': Decimal,
                                    'final': Decimal,
                                    'discount': Decimal,
                                    'rules_applied': int
                                }
                            }
                        ]
                    }
                ]
            }
        """
        result = {
            'item': {
                'code': item.code,
                'name': item.name,
            },
            'variant': None,
            'price_lists': []
        }

        if variant:
            result['variant'] = {
                'code': variant.code,
                'name': variant.name if hasattr(variant, 'name') else variant.code
            }

        # الحصول على جميع قوائم الأسعار
        price_lists = PriceList.objects.filter(
            company=self.company,
            is_active=True
        ).order_by('name')

        # الحصول على وحدات القياس
        uoms = []
        if include_uoms and item.base_uom:
            # الوحدة الأساسية
            uoms.append(item.base_uom)

            # جميع الوحدات في نفس المجموعة
            if hasattr(item.base_uom, 'uom_group') and item.base_uom.uom_group:
                additional_uoms = UnitOfMeasure.objects.filter(
                    company=self.company,
                    uom_group=item.base_uom.uom_group,
                    is_active=True
                ).exclude(pk=item.base_uom.pk)
                uoms.extend(list(additional_uoms))
        else:
            uoms = [None]  # سنحسب فقط للوحدة الأساسية

        # حساب الأسعار لكل قائمة
        for price_list in price_lists:
            pl_data = {
                'price_list': {
                    'code': price_list.code,
                    'name': price_list.name,
                    'currency': price_list.currency.code
                },
                'uoms': []
            }

            for uom in uoms:
                # حساب السعر
                price_result = self.engine.calculate_price(
                    item=item,
                    variant=variant,
                    uom=uom,
                    quantity=1,
                    price_list=price_list
                )

                uom_data = {
                    'uom': {
                        'code': uom.code if uom else item.base_uom.code,
                        'name': uom.name if uom else item.base_uom.name
                    } if (uom or item.base_uom) else None,
                    'prices': {
                        'base': float(price_result.base_price),
                        'final': float(price_result.final_price),
                        'discount': float(price_result.total_discount),
                        'discount_percentage': float(price_result.total_discount_percentage),
                        'rules_applied': len(price_result.applied_rules)
                    }
                }

                pl_data['uoms'].append(uom_data)

            result['price_lists'].append(pl_data)

        return result

    def simulate_price_change(
        self,
        rule=None,
        percentage_change=None,
        items=None,
        categories=None,
        price_list=None,
        preview_count=20
    ) -> Dict:
        """
        ⭐ محاكاة تغيير الأسعار قبل التطبيق

        يتيح رؤية تأثير:
        - تطبيق قاعدة تسعير جديدة
        - تغيير نسبة مئوية
        - قبل تنفيذ التغيير فعلياً

        Args:
            rule: قاعدة تسعير للمحاكاة
            percentage_change: تغيير نسبة مئوية (مثل: 10 = زيادة 10%)
            items: مواد محددة للمحاكاة
            categories: تصنيفات للمحاكاة
            price_list: قائمة أسعار محددة (افتراضياً: الافتراضية)
            preview_count: عدد المواد للمعاينة

        Returns:
            Dict: {
                'summary': {...},
                'preview': [...],
                'affected_items': int,
                'average_change': Decimal
            }
        """
        # الحصول على المواد
        if not items:
            query = Item.objects.filter(company=self.company, is_active=True)

            if categories:
                query = query.filter(category__in=categories)

            items = list(query[:preview_count])

        # الحصول على قائمة الأسعار
        if not price_list:
            price_list = PriceList.objects.filter(
                company=self.company,
                is_default=True
            ).first()

        if not price_list:
            price_list = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).first()

        simulation_results = {
            'rule': {
                'name': rule.name if rule else 'تغيير نسبة مئوية',
                'type': rule.rule_type if rule else 'PERCENTAGE_CHANGE',
                'value': float(rule.percentage_value) if rule else percentage_change
            },
            'price_list': {
                'code': price_list.code,
                'name': price_list.name
            } if price_list else None,
            'preview': [],
            'statistics': {
                'items_count': len(items),
                'average_old_price': Decimal('0.00'),
                'average_new_price': Decimal('0.00'),
                'average_change': Decimal('0.00'),
                'average_change_percentage': Decimal('0.00'),
                'total_increase': 0,
                'total_decrease': 0,
                'total_no_change': 0
            }
        }

        total_old_price = Decimal('0.00')
        total_new_price = Decimal('0.00')

        for item in items:
            # حساب السعر الحالي (بدون قاعدة جديدة)
            current_result = self.engine.calculate_price(
                item=item,
                price_list=price_list,
                apply_rules=False  # بدون قواعد للحصول على السعر الأساسي
            )

            old_price = current_result.final_price

            # حساب السعر الجديد
            if rule:
                # استخدام القاعدة
                cost_price = item.cost_price if hasattr(item, 'cost_price') else None
                new_price = rule.calculate_price(
                    base_price=old_price,
                    quantity=1,
                    cost_price=cost_price
                )
            elif percentage_change:
                # تطبيق تغيير نسبة مئوية
                if percentage_change > 0:
                    # زيادة
                    new_price = old_price * (Decimal('1') + (Decimal(str(percentage_change)) / Decimal('100')))
                else:
                    # نقصان
                    new_price = old_price * (Decimal('1') + (Decimal(str(percentage_change)) / Decimal('100')))
            else:
                new_price = old_price

            # حساب التغيير
            change = new_price - old_price
            change_pct = Decimal('0.00')
            if old_price > 0:
                change_pct = (change / old_price) * Decimal('100')

            # تحديد نوع التغيير
            if change > 0:
                simulation_results['statistics']['total_increase'] += 1
            elif change < 0:
                simulation_results['statistics']['total_decrease'] += 1
            else:
                simulation_results['statistics']['total_no_change'] += 1

            simulation_results['preview'].append({
                'code': item.code,
                'name': item.name,
                'category': item.category.name if item.category else None,
                'old_price': float(old_price),
                'new_price': float(new_price),
                'change': float(change),
                'change_percentage': float(change_pct)
            })

            total_old_price += old_price
            total_new_price += new_price

        # حساب المتوسطات
        items_count = len(items)
        if items_count > 0:
            avg_old = total_old_price / items_count
            avg_new = total_new_price / items_count
            avg_change = avg_new - avg_old
            avg_change_pct = Decimal('0.00')
            if avg_old > 0:
                avg_change_pct = (avg_change / avg_old) * Decimal('100')

            simulation_results['statistics']['average_old_price'] = float(avg_old)
            simulation_results['statistics']['average_new_price'] = float(avg_new)
            simulation_results['statistics']['average_change'] = float(avg_change)
            simulation_results['statistics']['average_change_percentage'] = float(avg_change_pct)

        return simulation_results

    def bulk_update_prices(
        self,
        rule=None,
        percentage_change=None,
        items=None,
        categories=None,
        price_list=None,
        apply=False
    ) -> Dict:
        """
        ⭐ تحديث أسعار متعددة دفعة واحدة

        Args:
            rule: قاعدة تسعير للتطبيق
            percentage_change: تغيير نسبة مئوية
            items: مواد محددة
            categories: تصنيفات محددة
            price_list: قائمة أسعار محددة
            apply: هل نطبق التغييرات فعلياً؟ (افتراضياً: لا)

        Returns:
            Dict: {
                'success': bool,
                'updated': int,
                'errors': [],
                'preview': [...]
            }
        """
        # أولاً: محاكاة التغييرات
        simulation = self.simulate_price_change(
            rule=rule,
            percentage_change=percentage_change,
            items=items,
            categories=categories,
            price_list=price_list,
            preview_count=1000  # محاكاة حتى 1000 مادة
        )

        result = {
            'success': False,
            'updated': 0,
            'errors': [],
            'simulation': simulation
        }

        if not apply:
            # معاينة فقط، لا تطبيق
            result['message'] = 'محاكاة فقط - لم يتم تطبيق التغييرات'
            return result

        # تطبيق التغييرات فعلياً
        try:
            with transaction.atomic():
                updated_count = 0

                for preview_item in simulation['preview']:
                    item = Item.objects.get(
                        company=self.company,
                        code=preview_item['code']
                    )

                    # تحديث أو إنشاء سعر جديد
                    price_list_obj = price_list if price_list else PriceList.objects.filter(
                        company=self.company,
                        is_default=True
                    ).first()

                    if not price_list_obj:
                        continue

                    # البحث عن سعر موجود أو إنشاء جديد
                    price_item, created = PriceListItem.objects.update_or_create(
                        price_list=price_list_obj,
                        item=item,
                        variant=None,
                        uom=None,
                        min_quantity=1,
                        defaults={
                            'price': Decimal(str(preview_item['new_price'])),
                            'is_active': True
                        }
                    )

                    updated_count += 1

                result['success'] = True
                result['updated'] = updated_count
                result['message'] = f'تم تحديث {updated_count} سعر بنجاح'

        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            result['message'] = f'فشل التحديث: {str(e)}'

        return result

    def compare_price_lists(
        self,
        items=None,
        categories=None,
        include_all_lists=True
    ) -> Dict:
        """
        ⭐ مقارنة الأسعار عبر قوائم أسعار متعددة

        Args:
            items: مواد محددة للمقارنة
            categories: تصنيفات محددة
            include_all_lists: هل نشمل جميع قوائم الأسعار؟

        Returns:
            Dict: {
                'price_lists': [...],
                'items': [
                    {
                        'item': {...},
                        'prices': {
                            'RETAIL': Decimal,
                            'WHOLESALE': Decimal,
                            ...
                        },
                        'lowest': Decimal,
                        'highest': Decimal,
                        'difference': Decimal
                    }
                ]
            }
        """
        # الحصول على المواد
        if not items:
            query = Item.objects.filter(company=self.company, is_active=True)

            if categories:
                query = query.filter(category__in=categories)

            items = list(query[:50])  # حد أقصى 50 مادة للمقارنة

        # الحصول على قوائم الأسعار
        if include_all_lists:
            price_lists = PriceList.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')
        else:
            price_lists = PriceList.objects.filter(
                company=self.company,
                is_active=True,
                is_default=True
            )

        result = {
            'price_lists': [
                {
                    'code': pl.code,
                    'name': pl.name,
                    'currency': pl.currency.code
                }
                for pl in price_lists
            ],
            'items': []
        }

        for item in items:
            item_comparison = {
                'item': {
                    'code': item.code,
                    'name': item.name,
                    'category': item.category.name if item.category else None
                },
                'prices': {},
                'lowest': None,
                'highest': None,
                'difference': None
            }

            prices_list = []

            for price_list in price_lists:
                price_result = self.engine.calculate_price(
                    item=item,
                    quantity=1,
                    price_list=price_list
                )

                item_comparison['prices'][price_list.code] = float(price_result.final_price)
                prices_list.append(price_result.final_price)

            if prices_list:
                item_comparison['lowest'] = float(min(prices_list))
                item_comparison['highest'] = float(max(prices_list))
                item_comparison['difference'] = item_comparison['highest'] - item_comparison['lowest']

            result['items'].append(item_comparison)

        return result

    def generate_price_report(
        self,
        price_list=None,
        categories=None,
        include_variants=False
    ) -> Dict:
        """
        ⭐ إنشاء تقرير شامل للأسعار

        Args:
            price_list: قائمة أسعار محددة
            categories: تصنيفات محددة
            include_variants: هل نشمل المتغيرات؟

        Returns:
            Dict: تقرير شامل بالأسعار
        """
        if not price_list:
            price_list = PriceList.objects.filter(
                company=self.company,
                is_default=True
            ).first()

        # الحصول على المواد
        items_query = Item.objects.filter(
            company=self.company,
            is_active=True
        )

        if categories:
            items_query = items_query.filter(category__in=categories)

        # إحصائيات
        statistics = {
            'total_items': items_query.count(),
            'items_with_price': 0,
            'items_without_price': 0,
            'average_price': Decimal('0.00'),
            'min_price': None,
            'max_price': None
        }

        items_data = []
        total_price = Decimal('0.00')
        price_count = 0

        for item in items_query:
            price_result = self.engine.calculate_price(
                item=item,
                quantity=1,
                price_list=price_list
            )

            item_data = {
                'code': item.code,
                'name': item.name,
                'category': item.category.name if item.category else None,
                'base_price': float(price_result.base_price),
                'final_price': float(price_result.final_price),
                'discount': float(price_result.total_discount),
                'rules_applied': len(price_result.applied_rules)
            }

            if price_result.final_price > 0:
                statistics['items_with_price'] += 1
                total_price += price_result.final_price
                price_count += 1

                if statistics['min_price'] is None or price_result.final_price < statistics['min_price']:
                    statistics['min_price'] = float(price_result.final_price)

                if statistics['max_price'] is None or price_result.final_price > statistics['max_price']:
                    statistics['max_price'] = float(price_result.final_price)
            else:
                statistics['items_without_price'] += 1

            items_data.append(item_data)

        if price_count > 0:
            statistics['average_price'] = float(total_price / price_count)

        return {
            'price_list': {
                'code': price_list.code,
                'name': price_list.name,
                'currency': price_list.currency.code
            } if price_list else None,
            'generated_at': timezone.now().isoformat(),
            'statistics': statistics,
            'items': items_data
        }


# دوال مساعدة - Helper Functions

def calculate_all_item_prices(item, variant=None, company=None) -> Dict:
    """
    دالة مساعدة سريعة لحساب جميع الأسعار

    Usage:
        from apps.core.utils.price_calculator import calculate_all_item_prices

        prices = calculate_all_item_prices(item=my_item)
        print(prices)
    """
    if not company:
        company = item.company

    calculator = PriceCalculator(company)
    return calculator.calculate_all_prices(item, variant)


def simulate_price_changes(rule, items=None, company=None) -> Dict:
    """
    دالة مساعدة سريعة لمحاكاة تغييرات الأسعار

    Usage:
        from apps.core.utils.price_calculator import simulate_price_changes

        simulation = simulate_price_changes(
            rule=my_rule,
            items=[item1, item2, item3]
        )
        print(f"Average change: {simulation['statistics']['average_change']}")
    """
    if not company:
        if rule:
            company = rule.company
        elif items:
            company = items[0].company

    calculator = PriceCalculator(company)
    return calculator.simulate_price_change(rule=rule, items=items)


def compare_prices_across_lists(items, company) -> Dict:
    """
    دالة مساعدة سريعة لمقارنة الأسعار

    Usage:
        from apps.core.utils.price_calculator import compare_prices_across_lists

        comparison = compare_prices_across_lists(
            items=[item1, item2],
            company=my_company
        )
        for item_data in comparison['items']:
            print(f"{item_data['item']['name']}: {item_data['prices']}")
    """
    calculator = PriceCalculator(company)
    return calculator.compare_price_lists(items=items)

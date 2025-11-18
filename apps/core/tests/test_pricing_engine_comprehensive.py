"""
Comprehensive Unit Tests for Pricing Engine
============================================

Tests all aspects of the pricing engine including:
- Core price calculations
- All pricing rule types
- Edge cases
- Error handling
- Performance benchmarks

Author: Mohammad + Claude
Date: 2025-11-19
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.models import (
    Company, Item, ItemVariant, UnitOfMeasure, PriceList,
    PriceListItem, PricingRule, ItemCategory
)
from apps.core.utils.pricing_engine import PricingEngine

User = get_user_model()


class PricingEngineTestCase(TestCase):
    """Base test case with common setup"""

    def setUp(self):
        """Create test data"""
        # Create company
        self.company = Company.objects.create(
            name_ar='شركة الاختبار',
            name_en='Test Company',
            code='TEST'
        )

        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create category
        self.category = ItemCategory.objects.create(
            company=self.company,
            name_ar='إلكترونيات',
            name_en='Electronics',
            code='ELEC',
            created_by=self.user
        )

        # Create UOM
        self.uom_piece = UnitOfMeasure.objects.create(
            company=self.company,
            name_ar='قطعة',
            name_en='Piece',
            code='PC',
            created_by=self.user
        )

        # Create item
        self.item = Item.objects.create(
            company=self.company,
            item_code='LAPTOP001',
            name_ar='لابتوب',
            name_en='Laptop',
            category=self.category,
            base_uom=self.uom_piece,
            has_variants=True,
            created_by=self.user
        )

        # Create variant
        self.variant = ItemVariant.objects.create(
            item=self.item,
            sku='LAPTOP001-V1',
            name_ar='لابتوب أسود',
            name_en='Black Laptop',
            cost=Decimal('800.00'),
            base_price=Decimal('1000.00'),
            created_by=self.user
        )

        # Create price list
        self.price_list = PriceList.objects.create(
            company=self.company,
            name_ar='قائمة التجزئة',
            name_en='Retail Price List',
            code='RETAIL',
            is_default=True,
            created_by=self.user
        )

        # Create price list item
        self.price_item = PriceListItem.objects.create(
            price_list=self.price_list,
            item_variant=self.variant,
            uom=self.uom_piece,
            price=Decimal('1200.00'),
            created_by=self.user
        )


class TestBasicPricing(PricingEngineTestCase):
    """Test basic pricing calculations without rules"""

    def test_get_base_price(self):
        """Test getting base price from price list"""
        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=False
        )

        self.assertEqual(result['base_price'], Decimal('1200.00'))
        self.assertEqual(result['final_price'], Decimal('1200.00'))
        self.assertEqual(len(result['applied_rules']), 0)

    def test_quantity_calculation(self):
        """Test price calculation with different quantities"""
        engine = PricingEngine()

        # Quantity = 5
        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('5'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=False
        )

        # Base calculation: 1200 * 5 = 6000
        self.assertEqual(result['total_amount'], Decimal('6000.00'))

    def test_missing_price(self):
        """Test behavior when price is not found"""
        # Create new variant without price
        new_variant = ItemVariant.objects.create(
            item=self.item,
            sku='LAPTOP002',
            name_ar='لابتوب أبيض',
            name_en='White Laptop',
            cost=Decimal('800.00'),
            base_price=Decimal('1000.00'),
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=new_variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece
        )

        # Should fallback to variant's base_price
        self.assertEqual(result['base_price'], Decimal('1000.00'))
        self.assertIn('Fallback to base price', result['calculation_log'])


class TestPercentageDiscountRule(PricingEngineTestCase):
    """Test percentage discount pricing rules"""

    def test_simple_percentage_discount(self):
        """Test basic percentage discount"""
        # Create rule: 10% discount
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم 10%',
            name_en='10% Discount',
            code='DISC10',
            rule_type='percentage_discount',
            value=Decimal('10.00'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Expected: 1200 - (1200 * 0.10) = 1080
        self.assertEqual(result['base_price'], Decimal('1200.00'))
        self.assertEqual(result['final_price'], Decimal('1080.00'))
        self.assertEqual(len(result['applied_rules']), 1)
        self.assertEqual(result['applied_rules'][0]['rule_code'], 'DISC10')

    def test_multiple_percentage_discounts(self):
        """Test stacking multiple percentage discounts"""
        # Rule 1: 10% discount
        rule1 = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم 10%',
            name_en='10% Discount',
            code='DISC10',
            rule_type='percentage_discount',
            value=Decimal('10.00'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        # Rule 2: 5% discount (higher priority)
        rule2 = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم 5%',
            name_en='5% Discount',
            code='DISC5',
            rule_type='percentage_discount',
            value=Decimal('5.00'),
            priority=20,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Expected: 1200 - (1200 * 0.05) = 1140 (first)
        #          1140 - (1140 * 0.10) = 1026 (second)
        self.assertEqual(result['final_price'], Decimal('1026.00'))
        self.assertEqual(len(result['applied_rules']), 2)


class TestFixedDiscountRule(PricingEngineTestCase):
    """Test fixed amount discount rules"""

    def test_fixed_discount(self):
        """Test fixed amount discount"""
        # Create rule: 100 fixed discount
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم 100',
            name_en='100 Discount',
            code='FIXED100',
            rule_type='fixed_discount',
            value=Decimal('100.00'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Expected: 1200 - 100 = 1100
        self.assertEqual(result['final_price'], Decimal('1100.00'))

    def test_fixed_discount_not_below_zero(self):
        """Test that fixed discount doesn't result in negative price"""
        # Create rule: 2000 fixed discount (more than price)
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم 2000',
            name_en='2000 Discount',
            code='FIXED2000',
            rule_type='fixed_discount',
            value=Decimal('2000.00'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Price should not go below zero
        self.assertGreaterEqual(result['final_price'], Decimal('0'))


class TestQuantityBasedPricing(PricingEngineTestCase):
    """Test quantity-based pricing rules"""

    def test_quantity_tier_rule(self):
        """Test quantity-based tier pricing"""
        # Create rule: 15% discount for quantity >= 10
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم الكمية',
            name_en='Quantity Discount',
            code='QTY10',
            rule_type='quantity_tier',
            value=Decimal('15.00'),  # 15% discount
            min_quantity=Decimal('10'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        # Test with quantity < 10 (rule should NOT apply)
        result1 = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('5'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        self.assertEqual(result1['final_price'], Decimal('1200.00'))
        self.assertEqual(len(result1['applied_rules']), 0)

        # Test with quantity >= 10 (rule SHOULD apply)
        result2 = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('10'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Expected: 1200 - (1200 * 0.15) = 1020
        self.assertEqual(result2['final_price'], Decimal('1020.00'))
        self.assertEqual(len(result2['applied_rules']), 1)


class TestCategoryBasedPricing(PricingEngineTestCase):
    """Test category-based pricing rules"""

    def test_category_rule(self):
        """Test category-specific pricing"""
        # Create rule for Electronics category: 20% discount
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم الإلكترونيات',
            name_en='Electronics Discount',
            code='ELEC20',
            rule_type='category_markup',
            value=Decimal('-20.00'),  # Negative = discount
            category=self.category,
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Expected: 1200 - (1200 * 0.20) = 960
        self.assertEqual(result['final_price'], Decimal('960.00'))

    def test_category_rule_not_applied_to_other_categories(self):
        """Test that category rule is not applied to items in other categories"""
        # Create different category
        other_category = ItemCategory.objects.create(
            company=self.company,
            name_ar='ملابس',
            name_en='Clothing',
            code='CLOTH',
            created_by=self.user
        )

        # Create item in different category
        other_item = Item.objects.create(
            company=self.company,
            item_code='SHIRT001',
            name_ar='قميص',
            name_en='Shirt',
            category=other_category,
            base_uom=self.uom_piece,
            has_variants=False,
            created_by=self.user
        )

        other_variant = ItemVariant.objects.create(
            item=other_item,
            sku='SHIRT001-V1',
            name_ar='قميص أزرق',
            name_en='Blue Shirt',
            cost=Decimal('50.00'),
            base_price=Decimal('100.00'),
            created_by=self.user
        )

        PriceListItem.objects.create(
            price_list=self.price_list,
            item_variant=other_variant,
            uom=self.uom_piece,
            price=Decimal('120.00'),
            created_by=self.user
        )

        # Create rule for Electronics only
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='خصم الإلكترونيات',
            name_en='Electronics Discount',
            code='ELEC20',
            rule_type='category_markup',
            value=Decimal('-20.00'),
            category=self.category,
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        # Calculate for clothing item
        result = engine.calculate_price(
            item=other_item,
            variant=other_variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Rule should NOT apply
        self.assertEqual(result['final_price'], Decimal('120.00'))
        self.assertEqual(len(result['applied_rules']), 0)


class TestDateBasedPricing(PricingEngineTestCase):
    """Test date-based pricing rules"""

    def test_active_date_range_rule(self):
        """Test rule that is active within date range"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Create rule active today
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='عرض محدود',
            name_en='Limited Offer',
            code='LIMITED',
            rule_type='percentage_discount',
            value=Decimal('25.00'),
            start_date=yesterday,
            end_date=tomorrow,
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True,
            check_date=today
        )

        # Rule should apply
        # Expected: 1200 - (1200 * 0.25) = 900
        self.assertEqual(result['final_price'], Decimal('900.00'))
        self.assertEqual(len(result['applied_rules']), 1)

    def test_expired_rule_not_applied(self):
        """Test that expired rule is not applied"""
        today = date.today()
        two_weeks_ago = today - timedelta(days=14)
        one_week_ago = today - timedelta(days=7)

        # Create expired rule
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='عرض منتهي',
            name_en='Expired Offer',
            code='EXPIRED',
            rule_type='percentage_discount',
            value=Decimal('30.00'),
            start_date=two_weeks_ago,
            end_date=one_week_ago,
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True,
            check_date=today
        )

        # Rule should NOT apply
        self.assertEqual(result['final_price'], Decimal('1200.00'))
        self.assertEqual(len(result['applied_rules']), 0)


class TestRulePriority(PricingEngineTestCase):
    """Test pricing rule priority ordering"""

    def test_rules_applied_in_priority_order(self):
        """Test that rules are applied in correct priority order"""
        # Rule with priority 30 (applied first)
        rule1 = PricingRule.objects.create(
            company=self.company,
            name_ar='قاعدة 1',
            name_en='Rule 1',
            code='RULE1',
            rule_type='percentage_discount',
            value=Decimal('10.00'),
            priority=30,
            is_active=True,
            created_by=self.user
        )

        # Rule with priority 20 (applied second)
        rule2 = PricingRule.objects.create(
            company=self.company,
            name_ar='قاعدة 2',
            name_en='Rule 2',
            code='RULE2',
            rule_type='percentage_discount',
            value=Decimal('5.00'),
            priority=20,
            is_active=True,
            created_by=self.user
        )

        # Rule with priority 10 (applied third)
        rule3 = PricingRule.objects.create(
            company=self.company,
            name_ar='قاعدة 3',
            name_en='Rule 3',
            code='RULE3',
            rule_type='fixed_discount',
            value=Decimal('50.00'),
            priority=10,
            is_active=True,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Check that rules were applied in correct order
        self.assertEqual(len(result['applied_rules']), 3)
        self.assertEqual(result['applied_rules'][0]['rule_code'], 'RULE1')
        self.assertEqual(result['applied_rules'][1]['rule_code'], 'RULE2')
        self.assertEqual(result['applied_rules'][2]['rule_code'], 'RULE3')

        # Calculate expected price:
        # 1200 - (1200 * 0.10) = 1080 (after rule1)
        # 1080 - (1080 * 0.05) = 1026 (after rule2)
        # 1026 - 50 = 976 (after rule3)
        self.assertEqual(result['final_price'], Decimal('976.00'))


class TestEdgeCases(PricingEngineTestCase):
    """Test edge cases and error handling"""

    def test_zero_quantity(self):
        """Test behavior with zero quantity"""
        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('0'),
            price_list=self.price_list,
            uom=self.uom_piece
        )

        self.assertEqual(result['total_amount'], Decimal('0'))

    def test_negative_quantity(self):
        """Test that negative quantity raises error"""
        engine = PricingEngine()

        with self.assertRaises(ValueError):
            result = engine.calculate_price(
                item=self.item,
                variant=self.variant,
                quantity=Decimal('-5'),
                price_list=self.price_list,
                uom=self.uom_piece
            )

    def test_very_large_quantity(self):
        """Test calculation with very large quantity"""
        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('999999'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=False
        )

        # Should not raise error
        expected = Decimal('1200.00') * Decimal('999999')
        self.assertEqual(result['total_amount'], expected)

    def test_inactive_rule_not_applied(self):
        """Test that inactive rules are not applied"""
        # Create inactive rule
        rule = PricingRule.objects.create(
            company=self.company,
            name_ar='قاعدة معطلة',
            name_en='Inactive Rule',
            code='INACTIVE',
            rule_type='percentage_discount',
            value=Decimal('50.00'),
            priority=10,
            is_active=False,
            created_by=self.user
        )

        engine = PricingEngine()

        result = engine.calculate_price(
            item=self.item,
            variant=self.variant,
            quantity=Decimal('1'),
            price_list=self.price_list,
            uom=self.uom_piece,
            apply_rules=True
        )

        # Inactive rule should NOT apply
        self.assertEqual(result['final_price'], Decimal('1200.00'))
        self.assertEqual(len(result['applied_rules']), 0)


class TestPerformance(PricingEngineTestCase):
    """Test performance benchmarks"""

    def test_calculate_1000_prices_performance(self):
        """Test that calculating 1000 prices is fast enough"""
        import time

        engine = PricingEngine()

        start_time = time.time()

        # Calculate 1000 prices
        for i in range(1000):
            result = engine.calculate_price(
                item=self.item,
                variant=self.variant,
                quantity=Decimal('1'),
                price_list=self.price_list,
                uom=self.uom_piece,
                apply_rules=False
            )

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 1 second
        self.assertLess(duration, 1.0,
                       f"Calculating 1000 prices took {duration:.2f}s (target: < 1.0s)")


# Run tests with: python manage.py test apps.core.tests.test_pricing_engine_comprehensive

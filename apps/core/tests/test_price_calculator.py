# apps/core/tests/test_price_calculator.py
"""
Tests for Price Calculator utilities
"""

from django.test import TestCase
from decimal import Decimal

from apps.core.models import (
    Company, Currency, PricingRule, PriceList,
    Item, ItemCategory, UnitOfMeasure, PriceListItem
)
from apps.core.utils.price_calculator import PriceCalculator
from apps.core.utils.pricing_engine import PricingEngine


class PriceCalculatorTestCase(TestCase):
    """Test cases for PriceCalculator class"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create currency
        cls.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_active=True
        )

        # Create company
        cls.company = Company.objects.create(
            name='Test Company',
            name_en='Test Company',
            currency=cls.currency
        )

        # Create UoM
        cls.uom = UnitOfMeasure.objects.create(
            name='Piece',
            code='PCS',
            company=cls.company
        )

        # Create category
        cls.category = ItemCategory.objects.create(
            name='Test Category',
            code='CAT01',
            company=cls.company
        )

        # Create items
        cls.items = []
        for i in range(10):
            item = Item.objects.create(
                name=f'Test Item {i}',
                code=f'ITEM{i:02d}',
                company=cls.company,
                category=cls.category,
                base_uom=cls.uom,
                currency=cls.currency
            )
            cls.items.append(item)

        # Create price lists
        cls.price_list_1 = PriceList.objects.create(
            name='Retail',
            code='RET',
            company=cls.company,
            currency=cls.currency
        )

        cls.price_list_2 = PriceList.objects.create(
            name='Wholesale',
            code='WHO',
            company=cls.company,
            currency=cls.currency
        )

        # Create prices
        for item in cls.items[:5]:
            PriceListItem.objects.create(
                item=item,
                price_list=cls.price_list_1,
                uom=cls.uom,
                price=Decimal('100.00')
            )
            PriceListItem.objects.create(
                item=item,
                price_list=cls.price_list_2,
                uom=cls.uom,
                price=Decimal('80.00')
            )

        # Create pricing rule
        cls.pricing_rule = PricingRule.objects.create(
            name='10% Discount',
            code='DISC10',
            company=cls.company,
            rule_type='DISCOUNT_PERCENTAGE',
            percentage_value=Decimal('10.00'),
            priority=10,
            is_active=True
        )
        cls.pricing_rule.apply_to_categories.add(cls.category)

    def test_calculator_initialization(self):
        """Test PriceCalculator initialization"""
        calculator = PriceCalculator(self.company)
        self.assertIsNotNone(calculator)
        self.assertEqual(calculator.company, self.company)
        self.assertIsInstance(calculator.engine, PricingEngine)

    def test_calculate_all_prices(self):
        """Test calculate_all_prices method"""
        calculator = PriceCalculator(self.company)
        result = calculator.calculate_all_prices(
            item=self.items[0],
            variant=None,
            include_uoms=True
        )

        self.assertIsNotNone(result)
        self.assertIn('total_price_lists', result)
        self.assertIn('prices_by_list', result)
        self.assertGreater(result['total_price_lists'], 0)

    def test_simulate_price_change_with_percentage(self):
        """Test simulate_price_change with percentage"""
        calculator = PriceCalculator(self.company)
        result = calculator.simulate_price_change(
            rule=None,
            percentage_change=Decimal('10.00'),
            items=self.items[:3],
            categories=None,
            price_list=self.price_list_1,
            preview_count=10
        )

        self.assertIsNotNone(result)
        self.assertIn('total_affected', result)
        self.assertIn('statistics', result)
        self.assertIn('preview', result)
        self.assertGreater(result['total_affected'], 0)

    def test_simulate_price_change_with_rule(self):
        """Test simulate_price_change with pricing rule"""
        calculator = PriceCalculator(self.company)
        result = calculator.simulate_price_change(
            rule=self.pricing_rule,
            percentage_change=None,
            items=None,
            categories=[self.category],
            price_list=self.price_list_1,
            preview_count=10
        )

        self.assertIsNotNone(result)
        self.assertGreater(result['total_affected'], 0)

    def test_bulk_update_prices_preview(self):
        """Test bulk_update_prices in preview mode"""
        calculator = PriceCalculator(self.company)
        result = calculator.bulk_update_prices(
            rule=None,
            percentage_change=Decimal('5.00'),
            items=self.items[:3],
            categories=None,
            price_list=self.price_list_1,
            apply=False  # Preview mode
        )

        self.assertIsNotNone(result)
        self.assertIn('preview', result)
        self.assertGreater(len(result['preview']), 0)

        # Verify no actual changes were made
        original_price = PriceListItem.objects.get(
            item=self.items[0],
            price_list=self.price_list_1
        ).price
        self.assertEqual(original_price, Decimal('100.00'))

    def test_bulk_update_prices_apply(self):
        """Test bulk_update_prices with apply=True"""
        calculator = PriceCalculator(self.company)

        # Get original price
        price_item = PriceListItem.objects.get(
            item=self.items[0],
            price_list=self.price_list_1
        )
        original_price = price_item.price

        result = calculator.bulk_update_prices(
            rule=None,
            percentage_change=Decimal('10.00'),
            items=[self.items[0]],
            categories=None,
            price_list=self.price_list_1,
            apply=True  # Apply changes
        )

        self.assertIsNotNone(result)
        self.assertIn('updated_count', result)

        # Verify price was updated
        price_item.refresh_from_db()
        expected_price = original_price * Decimal('1.10')
        self.assertEqual(price_item.price, expected_price)

    def test_compare_price_lists(self):
        """Test compare_price_lists method"""
        calculator = PriceCalculator(self.company)
        result = calculator.compare_price_lists(
            items=self.items[:3],
            categories=None,
            price_lists=[self.price_list_1, self.price_list_2],
            include_all_lists=False
        )

        self.assertIsNotNone(result)
        self.assertIn('total_items', result)
        self.assertIn('total_price_lists', result)
        self.assertIn('comparison_data', result)
        self.assertEqual(result['total_price_lists'], 2)

    def test_compare_price_lists_all_lists(self):
        """Test compare_price_lists with all lists"""
        calculator = PriceCalculator(self.company)
        result = calculator.compare_price_lists(
            items=self.items[:2],
            categories=None,
            price_lists=None,
            include_all_lists=True
        )

        self.assertIsNotNone(result)
        self.assertGreaterEqual(result['total_price_lists'], 2)

    def test_generate_price_report(self):
        """Test generate_price_report method"""
        calculator = PriceCalculator(self.company)
        result = calculator.generate_price_report(
            price_list=self.price_list_1,
            categories=[self.category],
            include_variants=True,
            include_inactive=False
        )

        self.assertIsNotNone(result)
        self.assertIn('total_items', result)
        self.assertIn('items_by_category', result)
        self.assertGreater(result['total_items'], 0)


class PricingEngineIntegrationTestCase(TestCase):
    """Integration tests for PricingEngine"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create currency
        cls.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_active=True
        )

        # Create company
        cls.company = Company.objects.create(
            name='Test Company',
            name_en='Test Company',
            currency=cls.currency
        )

        # Create UoM
        cls.uom = UnitOfMeasure.objects.create(
            name='Piece',
            code='PCS',
            company=cls.company
        )

        # Create category
        cls.category = ItemCategory.objects.create(
            name='Electronics',
            code='ELEC',
            company=cls.company
        )

        # Create item
        cls.item = Item.objects.create(
            name='Laptop',
            code='LAP01',
            company=cls.company,
            category=cls.category,
            base_uom=cls.uom,
            currency=cls.currency
        )

        # Create price list
        cls.price_list = PriceList.objects.create(
            name='Standard',
            code='STD',
            company=cls.company,
            currency=cls.currency
        )

        # Create base price
        cls.base_price_item = PriceListItem.objects.create(
            item=cls.item,
            price_list=cls.price_list,
            uom=cls.uom,
            price=Decimal('1000.00')
        )

        # Create multiple rules with different priorities
        cls.rule_1 = PricingRule.objects.create(
            name='10% Markup',
            code='MKP10',
            company=cls.company,
            rule_type='MARKUP_PERCENTAGE',
            percentage_value=Decimal('10.00'),
            priority=10,
            is_active=True
        )
        cls.rule_1.apply_to_items.add(cls.item)

        cls.rule_2 = PricingRule.objects.create(
            name='5% Discount',
            code='DSC05',
            company=cls.company,
            rule_type='DISCOUNT_PERCENTAGE',
            percentage_value=Decimal('5.00'),
            priority=5,
            is_active=True
        )
        cls.rule_2.apply_to_items.add(cls.item)

    def test_cascading_rules(self):
        """Test that multiple rules apply in cascade"""
        engine = PricingEngine(self.company)

        result = engine.calculate_price(
            item=self.item,
            variant=None,
            uom=self.uom,
            quantity=Decimal('1'),
            price_list=self.price_list,
            customer=None,
            check_date=None,
            apply_rules=True
        )

        self.assertIsNotNone(result)
        # Should have 2 rules applied
        self.assertEqual(len(result.applied_rules), 2)

        # Calculate expected price: 1000 * 1.10 * 0.95 = 1045
        expected_price = Decimal('1000.00') * Decimal('1.10') * Decimal('0.95')
        self.assertEqual(result.final_price, expected_price)

    def test_rule_priority_order(self):
        """Test that rules apply in correct priority order"""
        engine = PricingEngine(self.company)

        result = engine.calculate_price(
            item=self.item,
            variant=None,
            uom=self.uom,
            quantity=Decimal('1'),
            price_list=self.price_list,
            customer=None,
            check_date=None,
            apply_rules=True
        )

        # Higher priority rule (10) should apply first
        self.assertEqual(result.applied_rules[0]['code'], 'MKP10')
        self.assertEqual(result.applied_rules[1]['code'], 'DSC05')

    def test_calculation_log(self):
        """Test calculation log generation"""
        engine = PricingEngine(self.company)

        result = engine.calculate_price(
            item=self.item,
            variant=None,
            uom=self.uom,
            quantity=Decimal('1'),
            price_list=self.price_list,
            customer=None,
            check_date=None,
            apply_rules=True
        )

        log = result.get_calculation_log()
        self.assertIsInstance(log, list)
        self.assertGreater(len(log), 0)

    def test_price_without_rules(self):
        """Test price calculation without applying rules"""
        engine = PricingEngine(self.company)

        result = engine.calculate_price(
            item=self.item,
            variant=None,
            uom=self.uom,
            quantity=Decimal('1'),
            price_list=self.price_list,
            customer=None,
            check_date=None,
            apply_rules=False  # Don't apply rules
        )

        # Should return base price
        self.assertEqual(result.final_price, Decimal('1000.00'))
        self.assertEqual(len(result.applied_rules), 0)

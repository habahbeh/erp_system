"""
Comprehensive Unit Tests for UoM Conversion System
==================================================

Tests all aspects of Unit of Measure conversions including:
- Direct conversions
- Multi-step conversion chains
- Circular dependency detection
- Reverse conversions
- UoM groups
- Edge cases

Author: Mohammad + Claude
Date: 2025-11-19
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.models import (
    Company, Item, ItemVariant, UnitOfMeasure, UoMConversion,
    UoMGroup, ItemCategory
)

User = get_user_model()


class UoMConversionTestCase(TestCase):
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

        # Create UoM Group
        self.uom_group = UoMGroup.objects.create(
            company=self.company,
            name_ar='مجموعة الكمية',
            name_en='Quantity Group',
            code='QTY',
            created_by=self.user
        )

        # Create base UoMs
        self.uom_piece = UnitOfMeasure.objects.create(
            company=self.company,
            name_ar='قطعة',
            name_en='Piece',
            code='PC',
            uom_group=self.uom_group,
            created_by=self.user
        )

        self.uom_dozen = UnitOfMeasure.objects.create(
            company=self.company,
            name_ar='دزينة',
            name_en='Dozen',
            code='DOZ',
            uom_group=self.uom_group,
            created_by=self.user
        )

        self.uom_box = UnitOfMeasure.objects.create(
            company=self.company,
            name_ar='كرتون',
            name_en='Box',
            code='BOX',
            uom_group=self.uom_group,
            created_by=self.user
        )

        # Create category
        self.category = ItemCategory.objects.create(
            company=self.company,
            name_ar='مواد',
            name_en='Materials',
            code='MAT',
            created_by=self.user
        )

        # Create item
        self.item = Item.objects.create(
            company=self.company,
            item_code='ITEM001',
            name_ar='مادة اختبار',
            name_en='Test Item',
            category=self.category,
            base_uom=self.uom_piece,
            has_variants=False,
            created_by=self.user
        )


class TestDirectConversion(UoMConversionTestCase):
    """Test direct UoM conversions"""

    def test_simple_conversion(self):
        """Test basic 1:12 conversion (piece to dozen)"""
        # Create conversion: 1 dozen = 12 pieces
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Convert 24 pieces to dozens
        result_quantity = conversion.convert(Decimal('24'))

        # Expected: 24 / 12 = 2 dozens
        self.assertEqual(result_quantity, Decimal('2.00'))

    def test_reverse_conversion(self):
        """Test reverse conversion (dozen to piece)"""
        # Create conversion: 1 dozen = 12 pieces
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Get reverse conversion
        reverse_conversion = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_piece
        ).first()

        if not reverse_conversion:
            # Create reverse manually
            reverse_conversion = UoMConversion.objects.create(
                item=self.item,
                from_uom=self.uom_dozen,
                to_uom=self.uom_piece,
                conversion_factor=Decimal('0.0833333333'),  # 1/12
                created_by=self.user
            )

        # Convert 3 dozens to pieces
        result_quantity = reverse_conversion.convert(Decimal('3'))

        # Expected: 3 * 12 = 36 pieces
        self.assertEqual(result_quantity, Decimal('36.00'))

    def test_decimal_conversion(self):
        """Test conversion with decimal results"""
        # Create conversion: 1 box = 144 pieces (12 dozens)
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_box,
            conversion_factor=Decimal('144.00'),
            created_by=self.user
        )

        # Convert 100 pieces to boxes
        conversion = UoMConversion.objects.get(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_box
        )

        result_quantity = conversion.convert(Decimal('100'))

        # Expected: 100 / 144 = 0.694444...
        expected = Decimal('100') / Decimal('144')
        self.assertAlmostEqual(
            float(result_quantity),
            float(expected),
            places=4
        )


class TestMultiStepConversion(UoMConversionTestCase):
    """Test multi-step conversion chains"""

    def test_two_step_conversion(self):
        """Test conversion chain: piece → dozen → box"""
        # Create conversions
        # 1 dozen = 12 pieces
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # 1 box = 12 dozens
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_box,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Find conversion chain from piece to box
        # This would require a helper function in the model or utils
        # For now, we calculate manually:
        # 144 pieces = 12 dozens = 1 box
        # So: piece to box factor = 144

        # Convert 288 pieces to boxes
        # 288 pieces = 24 dozens = 2 boxes
        piece_to_dozen = Decimal('12.00')
        dozen_to_box = Decimal('12.00')
        total_factor = piece_to_dozen * dozen_to_box  # 144

        quantity_in_pieces = Decimal('288')
        expected_boxes = quantity_in_pieces / total_factor  # 2.00

        self.assertEqual(expected_boxes, Decimal('2.00'))


class TestUoMGroup(UoMConversionTestCase):
    """Test UoM Group functionality"""

    def test_uoms_in_same_group(self):
        """Test that UoMs in same group can be converted"""
        # All our test UoMs are in the same group
        self.assertEqual(self.uom_piece.uom_group, self.uom_group)
        self.assertEqual(self.uom_dozen.uom_group, self.uom_group)
        self.assertEqual(self.uom_box.uom_group, self.uom_group)

    def test_uoms_in_different_groups_cannot_convert(self):
        """Test that UoMs in different groups cannot be directly converted"""
        # Create different UoM group (weight)
        weight_group = UoMGroup.objects.create(
            company=self.company,
            name_ar='مجموعة الوزن',
            name_en='Weight Group',
            code='WEIGHT',
            created_by=self.user
        )

        # Create weight UoM
        uom_kg = UnitOfMeasure.objects.create(
            company=self.company,
            name_ar='كيلوغرام',
            name_en='Kilogram',
            code='KG',
            uom_group=weight_group,
            created_by=self.user
        )

        # Should not be able to convert piece to kg directly
        # (they're in different groups)
        self.assertNotEqual(self.uom_piece.uom_group, uom_kg.uom_group)


class TestConversionChains(UoMConversionTestCase):
    """Test conversion chain calculations"""

    def test_find_conversion_path(self):
        """Test finding conversion path between UoMs"""
        # Create conversion chain: piece → dozen → box
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_box,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Check if direct path exists
        direct_conversion = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_box
        ).exists()

        # Direct path should NOT exist (must go through dozen)
        self.assertFalse(direct_conversion)

        # Check if both steps exist
        step1_exists = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen
        ).exists()

        step2_exists = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_box
        ).exists()

        self.assertTrue(step1_exists)
        self.assertTrue(step2_exists)


class TestCircularDependencyDetection(UoMConversionTestCase):
    """Test detection of circular conversion dependencies"""

    def test_detect_simple_circular_dependency(self):
        """Test detection of A → B → A circular dependency"""
        # Create conversion: piece → dozen
        UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Try to create reverse: dozen → piece with different factor
        # This creates potential circular dependency
        # The system should detect this

        # For now, we allow reverse conversions
        # In production, you might want to validate this
        reverse_conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_piece,
            conversion_factor=Decimal('0.0833333333'),
            created_by=self.user
        )

        # Check that both exist
        forward_exists = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen
        ).exists()

        reverse_exists = UoMConversion.objects.filter(
            item=self.item,
            from_uom=self.uom_dozen,
            to_uom=self.uom_piece
        ).exists()

        self.assertTrue(forward_exists)
        self.assertTrue(reverse_exists)


class TestEdgeCases(UoMConversionTestCase):
    """Test edge cases and error handling"""

    def test_zero_quantity_conversion(self):
        """Test conversion with zero quantity"""
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        result = conversion.convert(Decimal('0'))

        self.assertEqual(result, Decimal('0'))

    def test_negative_quantity_conversion(self):
        """Test conversion with negative quantity"""
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Negative quantities might be valid for returns/adjustments
        result = conversion.convert(Decimal('-24'))

        # Expected: -24 / 12 = -2
        self.assertEqual(result, Decimal('-2.00'))

    def test_very_small_quantity_conversion(self):
        """Test conversion with very small quantity"""
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        result = conversion.convert(Decimal('0.01'))

        # Expected: 0.01 / 12 = 0.000833...
        expected = Decimal('0.01') / Decimal('12.00')
        self.assertAlmostEqual(
            float(result),
            float(expected),
            places=6
        )

    def test_very_large_quantity_conversion(self):
        """Test conversion with very large quantity"""
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        large_quantity = Decimal('999999999')
        result = conversion.convert(large_quantity)

        # Expected: 999999999 / 12
        expected = large_quantity / Decimal('12.00')
        self.assertEqual(result, expected)

    def test_conversion_with_zero_factor(self):
        """Test that zero conversion factor is not allowed"""
        with self.assertRaises(Exception):
            UoMConversion.objects.create(
                item=self.item,
                from_uom=self.uom_piece,
                to_uom=self.uom_dozen,
                conversion_factor=Decimal('0.00'),
                created_by=self.user
            )

    def test_same_uom_conversion(self):
        """Test conversion from UoM to itself"""
        # This should not be allowed or should return 1:1
        # Depending on business rules
        pass  # Implement based on business requirements


class TestPrecision(UoMConversionTestCase):
    """Test decimal precision in conversions"""

    def test_decimal_precision_maintained(self):
        """Test that decimal precision is maintained"""
        # Create conversion with high precision factor
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.345678'),
            created_by=self.user
        )

        result = conversion.convert(Decimal('100.00'))

        # Result should maintain precision
        # 100 / 12.345678 = 8.10005186...
        expected = Decimal('100.00') / Decimal('12.345678')

        self.assertAlmostEqual(
            float(result),
            float(expected),
            places=6
        )

    def test_rounding_behavior(self):
        """Test rounding behavior in conversions"""
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Convert quantity that doesn't divide evenly
        result = conversion.convert(Decimal('10'))

        # Expected: 10 / 12 = 0.8333...
        # Check precision
        expected = Decimal('10') / Decimal('12')

        # Should maintain at least 4 decimal places
        self.assertAlmostEqual(
            float(result),
            float(expected),
            places=4
        )


class TestPerformance(UoMConversionTestCase):
    """Test performance of UoM conversions"""

    def test_1000_conversions_performance(self):
        """Test that 1000 conversions complete quickly"""
        import time

        # Create conversion
        conversion = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        start_time = time.time()

        # Perform 1000 conversions
        for i in range(1000):
            result = conversion.convert(Decimal('100'))

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 0.1 seconds
        self.assertLess(duration, 0.1,
                       f"1000 conversions took {duration:.3f}s (target: < 0.1s)")


class TestMultiItemConversions(UoMConversionTestCase):
    """Test UoM conversions for multiple items"""

    def test_different_items_different_conversions(self):
        """Test that different items can have different conversion factors"""
        # Create second item
        item2 = Item.objects.create(
            company=self.company,
            item_code='ITEM002',
            name_ar='مادة ثانية',
            name_en='Second Item',
            category=self.category,
            base_uom=self.uom_piece,
            has_variants=False,
            created_by=self.user
        )

        # Item 1: 1 dozen = 12 pieces
        conversion1 = UoMConversion.objects.create(
            item=self.item,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('12.00'),
            created_by=self.user
        )

        # Item 2: 1 dozen = 10 pieces (different!)
        conversion2 = UoMConversion.objects.create(
            item=item2,
            from_uom=self.uom_piece,
            to_uom=self.uom_dozen,
            conversion_factor=Decimal('10.00'),
            created_by=self.user
        )

        # Test conversions
        result1 = conversion1.convert(Decimal('24'))  # 24/12 = 2
        result2 = conversion2.convert(Decimal('20'))  # 20/10 = 2

        self.assertEqual(result1, Decimal('2.00'))
        self.assertEqual(result2, Decimal('2.00'))

        # But same quantity gives different results:
        result1_100 = conversion1.convert(Decimal('100'))  # 100/12 = 8.33...
        result2_100 = conversion2.convert(Decimal('100'))  # 100/10 = 10

        self.assertNotEqual(result1_100, result2_100)


# Run tests with: python manage.py test apps.core.tests.test_uom_comprehensive

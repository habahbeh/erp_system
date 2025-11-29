# tests/inventory/test_edge_cases.py
"""
اختبارات الحالات الحدية والخاصة
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError


@pytest.mark.django_db
class TestNegativeStockHandling:
    """اختبارات التعامل مع المخزون السالب"""

    def test_negative_stock_prevented_by_default(self, company, branch, warehouse, item, customer, user, fiscal_year, accounts):
        """اختبار منع المخزون السالب افتراضياً"""
        from apps.inventory.models import StockOut, StockDocumentLine

        # لا يوجد مخزون
        stock_out = StockOut.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            destination_type='sales',
            customer=customer,
            created_by=user
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=item,
            quantity=Decimal('100'),
            unit_cost=Decimal('0')
        )

        with pytest.raises(ValidationError):
            stock_out.post(user=user)

    def test_negative_stock_allowed_when_enabled(self, company, branch, warehouse, item, customer, user, fiscal_year, accounts):
        """اختبار السماح بالمخزون السالب عند التفعيل"""
        from apps.inventory.models import StockOut, StockDocumentLine, ItemStock

        # تعيين الحسابات للمادة
        item.inventory_account = accounts['inventory']
        item.cost_of_goods_account = accounts['cogs']
        item.save()

        # تفعيل المخزون السالب
        warehouse.allow_negative_stock = True
        warehouse.save()

        stock_out = StockOut.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            destination_type='sales',
            customer=customer,
            created_by=user
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=item,
            quantity=Decimal('50'),
            unit_cost=Decimal('10')
        )

        # يجب أن يعمل
        stock_out.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        assert item_stock.quantity == Decimal('-50')


@pytest.mark.django_db
class TestZeroQuantityHandling:
    """اختبارات التعامل مع الكمية صفر"""

    def test_zero_quantity_line_rejected(self, company, branch, warehouse, item, supplier, user):
        """اختبار رفض سطور بكمية صفر"""
        from apps.inventory.models import StockIn, StockDocumentLine

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        with pytest.raises(ValidationError):
            line = StockDocumentLine(
                stock_in=stock_in,
                item=item,
                quantity=Decimal('0'),
                unit_cost=Decimal('10')
            )
            line.full_clean()

    def test_negative_quantity_rejected(self, company, branch, warehouse, item, supplier, user):
        """اختبار رفض الكميات السالبة"""
        from apps.inventory.models import StockIn, StockDocumentLine

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        with pytest.raises(ValidationError):
            line = StockDocumentLine(
                stock_in=stock_in,
                item=item,
                quantity=Decimal('-10'),
                unit_cost=Decimal('10')
            )
            line.full_clean()


@pytest.mark.django_db
class TestDecimalPrecision:
    """اختبارات دقة الأرقام العشرية"""

    def test_quantity_decimal_precision(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار دقة الكميات العشرية"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=item,
            quantity=Decimal('100.123'),
            unit_cost=Decimal('10.555')
        )

        stock_in.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        assert item_stock.quantity == Decimal('100.123')
        assert item_stock.average_cost == Decimal('10.555')

    def test_cost_rounding(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار تقريب التكاليف"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock

        # 100 × 10 = 1000
        stock_in1 = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )
        StockDocumentLine.objects.create(
            stock_in=stock_in1,
            item=item,
            quantity=Decimal('100'),
            unit_cost=Decimal('10')
        )
        stock_in1.post(user=user)

        # 7 × 13 = 91
        stock_in2 = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )
        StockDocumentLine.objects.create(
            stock_in=stock_in2,
            item=item,
            quantity=Decimal('7'),
            unit_cost=Decimal('13')
        )
        stock_in2.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        # المتوسط = 1091 / 107 = 10.196...
        # التحقق من الدقة
        expected = Decimal('1091') / Decimal('107')
        assert abs(item_stock.average_cost - expected) < Decimal('0.001')


@pytest.mark.django_db
class TestConcurrentOperations:
    """اختبارات العمليات المتزامنة"""

    def test_concurrent_stock_updates(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار تحديثات متزامنة للمخزون"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock
        from django.db import transaction

        # إنشاء سندين للترحيل المتزامن
        stock_in1 = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )
        StockDocumentLine.objects.create(
            stock_in=stock_in1,
            item=item,
            quantity=Decimal('50'),
            unit_cost=Decimal('10')
        )

        stock_in2 = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )
        StockDocumentLine.objects.create(
            stock_in=stock_in2,
            item=item,
            quantity=Decimal('30'),
            unit_cost=Decimal('12')
        )

        # ترحيل متسلسل (محاكاة التزامن)
        stock_in1.post(user=user)
        stock_in2.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        # 50 + 30 = 80
        # (500 + 360) / 80 = 10.75
        assert item_stock.quantity == Decimal('80')
        assert abs(item_stock.average_cost - Decimal('10.75')) < Decimal('0.01')


@pytest.mark.django_db
class TestVariantEdgeCases:
    """اختبارات حالات خاصة للمتغيرات"""

    def test_variant_required_for_variant_item(self, company, branch, warehouse, item_with_variants, supplier, user):
        """اختبار إلزامية المتغير للمواد ذات المتغيرات"""
        from apps.inventory.models import StockIn, StockDocumentLine

        item, variant1, variant2 = item_with_variants

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        with pytest.raises(ValidationError):
            line = StockDocumentLine(
                stock_in=stock_in,
                item=item,
                item_variant=None,  # بدون متغير
                quantity=Decimal('100'),
                unit_cost=Decimal('10')
            )
            line.full_clean()

    def test_variant_must_belong_to_item(self, company, branch, warehouse, item_with_variants, item, supplier, user):
        """اختبار أن المتغير يجب أن يتبع المادة"""
        from apps.inventory.models import StockIn, StockDocumentLine

        variant_item, variant1, variant2 = item_with_variants

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        with pytest.raises(ValidationError):
            line = StockDocumentLine(
                stock_in=stock_in,
                item=item,  # مادة مختلفة
                item_variant=variant1,  # متغير من مادة أخرى
                quantity=Decimal('100'),
                unit_cost=Decimal('10')
            )
            line.full_clean()


@pytest.mark.django_db
class TestDateEdgeCases:
    """اختبارات حالات خاصة للتواريخ"""

    def test_future_date_allowed(self, company, branch, warehouse, item, supplier, user):
        """اختبار السماح بتاريخ مستقبلي"""
        from apps.inventory.models import StockIn

        future_date = date.today() + timedelta(days=30)

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=future_date,
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        assert stock_in.date == future_date

    def test_very_old_date(self, company, branch, warehouse, item, supplier, user):
        """اختبار تاريخ قديم جداً"""
        from apps.inventory.models import StockIn

        old_date = date(2020, 1, 1)

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=old_date,
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        assert stock_in.date == old_date


@pytest.mark.django_db
class TestLargeQuantities:
    """اختبارات الكميات الكبيرة"""

    def test_large_quantity(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار كميات كبيرة"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=item,
            quantity=Decimal('999999.999'),
            unit_cost=Decimal('0.001')
        )

        stock_in.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        assert item_stock.quantity == Decimal('999999.999')

    def test_large_cost(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار تكاليف كبيرة"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock

        stock_in = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=item,
            quantity=Decimal('10'),
            unit_cost=Decimal('999999.999')
        )

        stock_in.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        assert item_stock.average_cost == Decimal('999999.999')
        assert item_stock.total_value == Decimal('9999999.990')

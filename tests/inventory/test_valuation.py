# tests/inventory/test_valuation.py
"""
اختبارات تقييم المخزون
"""

import pytest
from decimal import Decimal
from datetime import date
from django.db import models


@pytest.mark.django_db
class TestWeightedAverageValuation:
    """اختبارات تقييم المتوسط المرجح"""

    def test_weighted_average_single_purchase(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار المتوسط المرجح لعملية شراء واحدة"""
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
            quantity=Decimal('100'),
            unit_cost=Decimal('10.000')
        )

        stock_in.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        # متوسط التكلفة = 10
        assert item_stock.average_cost == Decimal('10.000')
        assert item_stock.total_value == Decimal('1000.000')

    def test_weighted_average_multiple_purchases(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار المتوسط المرجح لعمليات شراء متعددة"""
        from apps.inventory.models import StockIn, StockDocumentLine, ItemStock

        # الشراء الأول: 100 × 10 = 1000
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
            unit_cost=Decimal('10.000')
        )
        stock_in1.post(user=user)

        # الشراء الثاني: 50 × 12 = 600
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
            quantity=Decimal('50'),
            unit_cost=Decimal('12.000')
        )
        stock_in2.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        # المتوسط المرجح = (1000 + 600) / (100 + 50) = 1600 / 150 = 10.667
        expected_avg = (Decimal('1000') + Decimal('600')) / Decimal('150')
        assert item_stock.quantity == Decimal('150')
        assert abs(item_stock.average_cost - expected_avg) < Decimal('0.001')
        assert item_stock.total_value == Decimal('1600.000')

    def test_cost_after_stock_out(self, company, branch, warehouse, item, supplier, customer, user, fiscal_year, accounts):
        """اختبار التكلفة بعد الإخراج"""
        from apps.inventory.models import StockIn, StockOut, StockDocumentLine, ItemStock

        # تعيين الحسابات للمادة
        item.inventory_account = accounts['inventory']
        item.cost_of_goods_account = accounts['cogs']
        item.save()

        # إدخال: 100 × 10 = 1000
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
            quantity=Decimal('100'),
            unit_cost=Decimal('10.000')
        )
        stock_in.post(user=user)

        # إخراج: 40
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
            quantity=Decimal('40'),
            unit_cost=Decimal('0')  # سيتم استخدام متوسط التكلفة
        )
        stock_out.post(user=user)

        item_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse,
            company=company
        )

        # الرصيد: 100 - 40 = 60
        # القيمة: 1000 - (40 × 10) = 600
        # المتوسط يبقى: 10
        assert item_stock.quantity == Decimal('60')
        assert item_stock.average_cost == Decimal('10.000')
        assert item_stock.total_value == Decimal('600.000')

    def test_average_cost_preserved_after_out(self, company, branch, warehouse, item, supplier, customer, user, fiscal_year, accounts):
        """اختبار الحفاظ على متوسط التكلفة بعد الإخراج"""
        from apps.inventory.models import StockIn, StockOut, StockDocumentLine, ItemStock

        # تعيين الحسابات للمادة
        item.inventory_account = accounts['inventory']
        item.cost_of_goods_account = accounts['cogs']
        item.save()

        # إدخال بأسعار مختلفة
        # 50 × 10 = 500
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
            unit_cost=Decimal('10.000')
        )
        stock_in1.post(user=user)

        # 50 × 14 = 700
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
            quantity=Decimal('50'),
            unit_cost=Decimal('14.000')
        )
        stock_in2.post(user=user)

        item_stock = ItemStock.objects.get(item=item, warehouse=warehouse, company=company)
        avg_before = item_stock.average_cost  # 12.00

        # إخراج
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
            quantity=Decimal('30'),
            unit_cost=Decimal('0')
        )
        stock_out.post(user=user)

        item_stock.refresh_from_db()
        # المتوسط يجب أن يبقى كما هو
        assert item_stock.average_cost == avg_before


@pytest.mark.django_db
class TestStockValuationReport:
    """اختبارات تقرير قيمة المخزون"""

    def test_total_inventory_value(self, company, warehouse, warehouse2, item, user):
        """اختبار إجمالي قيمة المخزون"""
        from apps.inventory.models import ItemStock

        # رصيد في المستودع الأول
        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            quantity=Decimal('100'),
            average_cost=Decimal('10'),
            total_value=Decimal('1000'),
            created_by=user
        )

        # رصيد في المستودع الثاني
        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse2,
            quantity=Decimal('50'),
            average_cost=Decimal('12'),
            total_value=Decimal('600'),
            created_by=user
        )

        total_value = ItemStock.objects.filter(company=company).aggregate(
            total=models.Sum('total_value')
        )['total']

        assert total_value == Decimal('1600')

    def test_inventory_value_by_warehouse(self, company, warehouse, warehouse2, item, user):
        """اختبار قيمة المخزون حسب المستودع"""
        from apps.inventory.models import ItemStock
        from django.db import models

        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            quantity=Decimal('100'),
            average_cost=Decimal('10'),
            total_value=Decimal('1000'),
            created_by=user
        )

        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse2,
            quantity=Decimal('50'),
            average_cost=Decimal('12'),
            total_value=Decimal('600'),
            created_by=user
        )

        wh1_value = ItemStock.objects.filter(
            company=company,
            warehouse=warehouse
        ).aggregate(total=models.Sum('total_value'))['total']

        wh2_value = ItemStock.objects.filter(
            company=company,
            warehouse=warehouse2
        ).aggregate(total=models.Sum('total_value'))['total']

        assert wh1_value == Decimal('1000')
        assert wh2_value == Decimal('600')


@pytest.mark.django_db
class TestCostCalculation:
    """اختبارات حساب التكلفة"""

    def test_stock_out_uses_average_cost(self, company, branch, warehouse, item, customer, user, item_stock, fiscal_year, accounts):
        """اختبار أن الإخراج يستخدم متوسط التكلفة"""
        from apps.inventory.models import StockOut, StockDocumentLine, StockMovement

        # تعيين الحسابات للمادة
        item.inventory_account = accounts['inventory']
        item.cost_of_goods_account = accounts['cogs']
        item.save()

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
            quantity=Decimal('20'),
            unit_cost=Decimal('0')  # لم نحدد التكلفة
        )

        stock_out.post(user=user)

        # التحقق من استخدام متوسط التكلفة
        movement = StockMovement.objects.filter(
            reference_type='stock_out',
            reference_id=stock_out.pk
        ).first()

        assert movement.unit_cost == Decimal('10.000')  # من item_stock
        assert abs(movement.total_cost) == Decimal('200.000')  # 20 × 10 (سالب للإخراج)

    def test_transfer_preserves_cost(self, company, branch, warehouse, warehouse2, item, user, item_stock, fiscal_year, accounts):
        """اختبار أن التحويل يحافظ على التكلفة"""
        from apps.inventory.models import StockTransfer, StockTransferLine, ItemStock

        transfer = StockTransfer.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            destination_warehouse=warehouse2,
            status='draft',
            created_by=user
        )

        StockTransferLine.objects.create(
            transfer=transfer,
            item=item,
            quantity=Decimal('30'),
            unit_cost=item_stock.average_cost
        )

        transfer.approve(user)
        transfer.send(user)
        transfer.receive(user)

        dest_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse2,
            company=company
        )

        # التحقق من أن التكلفة انتقلت
        assert dest_stock.average_cost == item_stock.average_cost

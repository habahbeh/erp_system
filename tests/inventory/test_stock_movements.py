# tests/inventory/test_stock_movements.py
"""
اختبارات حركات المخزون
"""

import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestStockIn:
    """اختبارات سندات الإدخال"""

    def test_create_stock_in(self, company, branch, warehouse, item, supplier, user):
        """اختبار إنشاء سند إدخال"""
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

        assert stock_in.pk is not None
        assert stock_in.number.startswith('SI/')
        assert stock_in.is_posted is False

    def test_stock_in_auto_number(self, company, branch, warehouse, item, supplier, user):
        """اختبار توليد رقم السند تلقائياً"""
        from apps.inventory.models import StockIn

        stock_in1 = StockIn.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            source_type='purchase',
            supplier=supplier,
            created_by=user
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

        # التحقق من تسلسل الأرقام
        num1 = int(stock_in1.number.split('/')[-1])
        num2 = int(stock_in2.number.split('/')[-1])
        assert num2 == num1 + 1

    def test_stock_in_post(self, stock_in, fiscal_year, accounts, user):
        """اختبار ترحيل سند إدخال"""
        from apps.inventory.models import ItemStock, StockMovement

        # ترحيل السند
        stock_in.post(user=user)

        assert stock_in.is_posted is True
        assert stock_in.posted_by == user
        assert stock_in.posted_date is not None

        # التحقق من تحديث المخزون
        line = stock_in.lines.first()
        item_stock = ItemStock.objects.get(
            item=line.item,
            warehouse=stock_in.warehouse,
            company=stock_in.company
        )

        assert item_stock.quantity == Decimal('100')
        assert item_stock.average_cost == Decimal('10.000')

        # التحقق من حركة المخزون
        movement = StockMovement.objects.filter(
            reference_type='stock_in',
            reference_id=stock_in.pk
        ).first()

        assert movement is not None
        assert movement.movement_type == 'in'
        assert movement.quantity == Decimal('100')

    def test_stock_in_cannot_post_twice(self, stock_in, fiscal_year, accounts, user):
        """اختبار منع الترحيل المزدوج"""
        stock_in.post(user=user)

        with pytest.raises(ValidationError):
            stock_in.post(user=user)

    def test_stock_in_unpost(self, stock_in, fiscal_year, accounts, user):
        """اختبار إلغاء ترحيل سند إدخال"""
        from apps.inventory.models import ItemStock, StockMovement

        stock_in.post(user=user)
        stock_in.unpost()

        assert stock_in.is_posted is False
        assert stock_in.posted_by is None

        # التحقق من تصفير المخزون
        item_stock = ItemStock.objects.get(
            item=stock_in.lines.first().item,
            warehouse=stock_in.warehouse
        )
        assert item_stock.quantity == Decimal('0')

        # التحقق من حذف الحركة
        movements = StockMovement.objects.filter(
            reference_type='stock_in',
            reference_id=stock_in.pk
        )
        assert movements.count() == 0


@pytest.mark.django_db
class TestStockOut:
    """اختبارات سندات الإخراج"""

    def test_create_stock_out(self, company, branch, warehouse, item, customer, user):
        """اختبار إنشاء سند إخراج"""
        from apps.inventory.models import StockOut, StockDocumentLine

        stock_out = StockOut.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            destination_type='sales',
            customer=customer,
            created_by=user
        )

        assert stock_out.pk is not None
        assert stock_out.number.startswith('SO/')
        assert stock_out.is_posted is False

    def test_stock_out_post(self, company, branch, warehouse, item, customer, user, item_stock, fiscal_year, accounts):
        """اختبار ترحيل سند إخراج"""
        from apps.inventory.models import StockOut, StockDocumentLine, ItemStock, StockMovement

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
            quantity=Decimal('30'),
            unit_cost=Decimal('0')  # سيتم حسابها من متوسط التكلفة
        )

        initial_qty = item_stock.quantity

        stock_out.post(user=user)

        assert stock_out.is_posted is True

        # التحقق من خصم المخزون
        item_stock.refresh_from_db()
        assert item_stock.quantity == initial_qty - Decimal('30')

        # التحقق من حركة المخزون
        movement = StockMovement.objects.filter(
            reference_type='stock_out',
            reference_id=stock_out.pk
        ).first()

        assert movement is not None
        assert movement.movement_type == 'out'
        assert movement.quantity == Decimal('-30')  # سالب للإخراج

    def test_stock_out_insufficient_quantity(self, company, branch, warehouse, item, customer, user, item_stock, fiscal_year):
        """اختبار منع الإخراج بكمية أكبر من المتاح"""
        from apps.inventory.models import StockOut, StockDocumentLine

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
            quantity=Decimal('200'),  # أكثر من المتاح (100)
            unit_cost=Decimal('0')
        )

        with pytest.raises(ValidationError):
            stock_out.post(user=user)


@pytest.mark.django_db
class TestStockTransfer:
    """اختبارات التحويلات"""

    def test_create_transfer(self, company, branch, warehouse, warehouse2, item, user):
        """اختبار إنشاء تحويل"""
        from apps.inventory.models import StockTransfer, StockTransferLine

        transfer = StockTransfer.objects.create(
            company=company,
            branch=branch,
            date=date.today(),
            warehouse=warehouse,
            destination_warehouse=warehouse2,
            status='draft',
            created_by=user
        )

        assert transfer.pk is not None
        assert transfer.number.startswith('ST/')
        assert transfer.status == 'draft'

    def test_transfer_same_warehouse_validation(self, company, branch, warehouse, user):
        """اختبار منع التحويل لنفس المستودع"""
        from apps.inventory.forms import StockTransferForm

        form = StockTransferForm(data={
            'date': date.today(),
            'warehouse': warehouse.pk,
            'destination_warehouse': warehouse.pk,  # نفس المستودع
        })
        form.request = type('obj', (object,), {'current_company': company})()

        assert form.is_valid() is False
        assert '__all__' in form.errors

    def test_transfer_workflow(self, company, branch, warehouse, warehouse2, item, user, item_stock):
        """اختبار دورة التحويل الكاملة"""
        from apps.inventory.models import StockTransfer, StockTransferLine, ItemStock

        # إنشاء التحويل
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
            unit_cost=Decimal('10')
        )

        # اعتماد التحويل
        transfer.approve(user)
        assert transfer.status == 'approved'

        # إرسال التحويل
        transfer.send(user)
        assert transfer.status == 'in_transit'

        # التحقق من خصم المستودع المصدر
        item_stock.refresh_from_db()
        assert item_stock.quantity == Decimal('70')  # 100 - 30

        # استلام التحويل
        transfer.receive(user)
        assert transfer.status == 'received'

        # التحقق من إضافة المستودع الهدف
        dest_stock = ItemStock.objects.get(
            item=item,
            warehouse=warehouse2,
            company=company
        )
        assert dest_stock.quantity == Decimal('30')

    def test_transfer_cancel(self, company, branch, warehouse, warehouse2, item, user, item_stock):
        """اختبار إلغاء تحويل"""
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
            quantity=Decimal('20'),
            unit_cost=Decimal('10')
        )

        transfer.approve(user)
        transfer.send(user)

        initial_qty = item_stock.quantity - Decimal('20')  # بعد الإرسال
        item_stock.refresh_from_db()

        # إلغاء التحويل
        transfer.cancel(user)
        assert transfer.status == 'cancelled'

        # التحقق من إعادة الكمية
        item_stock.refresh_from_db()
        assert item_stock.quantity == Decimal('100')  # الأصلي


@pytest.mark.django_db
class TestStockMovementHistory:
    """اختبارات سجل الحركات"""

    def test_movement_history(self, stock_in, fiscal_year, accounts, user):
        """اختبار سجل الحركات"""
        from apps.inventory.models import StockMovement

        stock_in.post(user=user)

        movements = StockMovement.objects.filter(
            item=stock_in.lines.first().item,
            warehouse=stock_in.warehouse
        ).order_by('-date')

        assert movements.count() >= 1

        movement = movements.first()
        assert movement.reference_type == 'stock_in'
        assert movement.reference_number == stock_in.number
        assert movement.balance_quantity == Decimal('100')

    def test_movement_balance_tracking(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار تتبع الرصيد في الحركات"""
        from apps.inventory.models import StockIn, StockDocumentLine, StockMovement

        # الحركة الأولى
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
        stock_in1.post(user=user)

        # الحركة الثانية
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
        stock_in2.post(user=user)

        # التحقق من الأرصدة
        movements = StockMovement.objects.filter(
            item=item,
            warehouse=warehouse
        ).order_by('date')

        assert movements.count() == 2

        # الحركة الأولى
        m1 = movements.first()
        assert m1.balance_before == Decimal('0')
        assert m1.balance_quantity == Decimal('50')

        # الحركة الثانية
        m2 = movements.last()
        assert m2.balance_before == Decimal('50')
        assert m2.balance_quantity == Decimal('80')

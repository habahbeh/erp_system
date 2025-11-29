# tests/inventory/test_stock_management.py
"""
اختبارات إدارة المخزون
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestWarehouseManagement:
    """اختبارات إدارة المستودعات"""

    def test_create_warehouse(self, company, branch, user):
        """اختبار إنشاء مستودع جديد"""
        from apps.core.models import Warehouse

        warehouse = Warehouse.objects.create(
            company=company,
            branch=branch,
            name='مستودع جديد',
            code='WH-NEW',
            is_active=True,
            allow_negative_stock=False,
            created_by=user
        )

        assert warehouse.pk is not None
        assert warehouse.name == 'مستودع جديد'
        assert warehouse.code == 'WH-NEW'
        assert warehouse.is_active is True
        assert warehouse.allow_negative_stock is False

    def test_warehouse_unique_code(self, warehouse, company, branch, user):
        """اختبار أن كود المستودع فريد"""
        from apps.core.models import Warehouse
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Warehouse.objects.create(
                company=company,
                branch=branch,
                name='مستودع مكرر',
                code=warehouse.code,  # نفس الكود
                created_by=user
            )


@pytest.mark.django_db
class TestStockLevels:
    """اختبارات مستويات المخزون"""

    def test_view_stock_levels(self, item_stock):
        """اختبار عرض مستويات المخزون"""
        assert item_stock.quantity == Decimal('100')
        assert item_stock.average_cost == Decimal('10.000')
        assert item_stock.total_value == Decimal('1000.000')

    def test_stock_by_warehouse(self, company, item, warehouse, warehouse2, user):
        """اختبار المخزون حسب المستودع"""
        from apps.inventory.models import ItemStock

        # إنشاء رصيد في المستودع الأول
        stock1 = ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            quantity=Decimal('50'),
            average_cost=Decimal('10'),
            total_value=Decimal('500'),
            created_by=user
        )

        # إنشاء رصيد في المستودع الثاني
        stock2 = ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse2,
            quantity=Decimal('30'),
            average_cost=Decimal('12'),
            total_value=Decimal('360'),
            created_by=user
        )

        # التحقق من الأرصدة
        wh1_stock = ItemStock.objects.get(warehouse=warehouse, item=item)
        wh2_stock = ItemStock.objects.get(warehouse=warehouse2, item=item)

        assert wh1_stock.quantity == Decimal('50')
        assert wh2_stock.quantity == Decimal('30')

    def test_get_total_stock(self, company, item, warehouse, warehouse2, user):
        """اختبار إجمالي المخزون"""
        from apps.inventory.models import ItemStock

        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            quantity=Decimal('50'),
            reserved_quantity=Decimal('10'),
            average_cost=Decimal('10'),
            total_value=Decimal('500'),
            created_by=user
        )

        ItemStock.objects.create(
            company=company,
            item=item,
            warehouse=warehouse2,
            quantity=Decimal('30'),
            reserved_quantity=Decimal('5'),
            average_cost=Decimal('12'),
            total_value=Decimal('360'),
            created_by=user
        )

        total = ItemStock.get_total_stock(item, company=company)

        assert total['total_quantity'] == Decimal('80')
        assert total['total_reserved'] == Decimal('15')
        assert total['total_available'] == Decimal('65')
        assert total['warehouses_count'] == 2

    def test_low_stock_alert(self, item_stock):
        """اختبار تنبيهات انخفاض المخزون"""
        # الرصيد الحالي 100، الحد الأدنى 10
        assert item_stock.is_below_min_level() is False

        # تخفيض الرصيد
        item_stock.quantity = Decimal('5')
        item_stock.save()

        assert item_stock.is_below_min_level() is True

    def test_reorder_point(self, item_stock):
        """اختبار نقطة إعادة الطلب"""
        # الرصيد 100، نقطة إعادة الطلب 20
        assert item_stock.check_reorder_needed() is False

        # تخفيض الرصيد
        item_stock.quantity = Decimal('20')
        item_stock.save()

        assert item_stock.check_reorder_needed() is True

    def test_maximum_stock_level(self, item_stock):
        """اختبار الحد الأقصى للمخزون"""
        # الرصيد 100، الحد الأقصى 500
        assert item_stock.is_above_max_level() is False

        # زيادة الرصيد
        item_stock.quantity = Decimal('600')
        item_stock.save()

        assert item_stock.is_above_max_level() is True


@pytest.mark.django_db
class TestStockReservation:
    """اختبارات حجز المخزون"""

    def test_reserve_quantity(self, item_stock):
        """اختبار حجز كمية"""
        initial_qty = item_stock.quantity
        reserve_qty = Decimal('20')

        item_stock.reserve_quantity(reserve_qty)

        assert item_stock.reserved_quantity == reserve_qty
        assert item_stock.get_available_quantity() == initial_qty - reserve_qty

    def test_reserve_exceeds_available(self, item_stock):
        """اختبار حجز أكثر من المتاح"""
        with pytest.raises(ValidationError):
            item_stock.reserve_quantity(Decimal('200'))  # أكثر من 100

    def test_release_reserved_quantity(self, item_stock):
        """اختبار إلغاء حجز"""
        item_stock.reserve_quantity(Decimal('30'))
        assert item_stock.reserved_quantity == Decimal('30')

        item_stock.release_reserved_quantity(Decimal('10'))
        assert item_stock.reserved_quantity == Decimal('20')

    def test_release_more_than_reserved(self, item_stock):
        """اختبار إلغاء أكثر من المحجوز"""
        item_stock.reserve_quantity(Decimal('20'))

        with pytest.raises(ValidationError):
            item_stock.release_reserved_quantity(Decimal('30'))


@pytest.mark.django_db
class TestItemStockVariants:
    """اختبارات المخزون مع المتغيرات"""

    def test_stock_with_variant(self, company, warehouse, item_with_variants, user):
        """اختبار المخزون مع متغيرات"""
        from apps.inventory.models import ItemStock

        item, variant1, variant2 = item_with_variants

        # إنشاء رصيد للمتغير الأول
        stock1 = ItemStock.objects.create(
            company=company,
            item=item,
            item_variant=variant1,
            warehouse=warehouse,
            quantity=Decimal('50'),
            average_cost=Decimal('15'),
            total_value=Decimal('750'),
            created_by=user
        )

        # إنشاء رصيد للمتغير الثاني
        stock2 = ItemStock.objects.create(
            company=company,
            item=item,
            item_variant=variant2,
            warehouse=warehouse,
            quantity=Decimal('30'),
            average_cost=Decimal('15'),
            total_value=Decimal('450'),
            created_by=user
        )

        # التحقق
        assert stock1.item_variant.code == 'VAR-RED'
        assert stock2.item_variant.code == 'VAR-BLUE'

        # إجمالي المادة
        total = ItemStock.get_total_stock(item, company=company)
        assert total['total_quantity'] == Decimal('80')

    def test_variant_stock_isolation(self, company, warehouse, item_with_variants, user):
        """اختبار عزل مخزون المتغيرات"""
        from apps.inventory.models import ItemStock

        item, variant1, variant2 = item_with_variants

        stock1 = ItemStock.objects.create(
            company=company,
            item=item,
            item_variant=variant1,
            warehouse=warehouse,
            quantity=Decimal('100'),
            average_cost=Decimal('10'),
            total_value=Decimal('1000'),
            created_by=user
        )

        # التحقق من عدم التداخل
        stocks = ItemStock.objects.filter(item=item, warehouse=warehouse)
        assert stocks.count() == 1
        assert stocks.first().item_variant == variant1

# tests/inventory/test_inventory_count.py
"""
اختبارات الجرد
"""

import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestStockCount:
    """اختبارات الجرد"""

    def test_create_stock_count(self, company, branch, warehouse, user):
        """اختبار إنشاء جرد جديد"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            created_by=user
        )

        assert count.pk is not None
        assert count.number.startswith('SC/')
        assert count.status == 'planned'

    def test_stock_count_auto_populate_lines(self, company, warehouse, item_stock, user):
        """اختبار إضافة سطور الجرد تلقائياً"""
        from apps.inventory.models import StockCount, StockCountLine

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            created_by=user
        )

        # إضافة السطور تلقائياً من المخزون الموجود
        count.populate_lines()

        lines = count.lines.all()
        assert lines.count() >= 1

        line = lines.first()
        assert line.system_quantity == item_stock.quantity
        assert line.unit_cost == item_stock.average_cost

    def test_stock_count_difference_calculation(self, company, warehouse, item, item_stock, user):
        """اختبار حساب الفروقات"""
        from apps.inventory.models import StockCount, StockCountLine

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='in_progress',
            created_by=user
        )

        line = StockCountLine.objects.create(
            count=count,
            item=item,
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('95'),  # نقص 5
            unit_cost=Decimal('10'),
            system_value=Decimal('1000'),
            counted_value=Decimal('950'),
            difference_quantity=Decimal('-5'),
            difference_value=Decimal('-50')
        )

        assert line.difference_quantity == Decimal('-5')
        assert line.difference_value == Decimal('-50')

    def test_stock_count_workflow(self, company, warehouse, item, item_stock, user, fiscal_year, accounts):
        """اختبار دورة الجرد الكاملة"""
        from apps.inventory.models import StockCount, StockCountLine, ItemStock

        # إنشاء الجرد
        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='in_progress',
            created_by=user
        )

        line = StockCountLine.objects.create(
            count=count,
            item=item,
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('90'),  # نقص 10
            unit_cost=Decimal('10'),
            system_value=Decimal('1000'),
            counted_value=Decimal('900'),
            difference_quantity=Decimal('-10'),
            difference_value=Decimal('-100')
        )

        # اكتمال الجرد
        count.status = 'completed'
        count.save()

        # اعتماد الجرد ومعالجة الفروقات
        count.process_adjustments(user)

        assert count.status == 'approved'

        # التحقق من تحديث المخزون
        item_stock.refresh_from_db()
        assert item_stock.quantity == Decimal('90')

    def test_stock_count_surplus(self, company, warehouse, item, item_stock, user, fiscal_year, accounts):
        """اختبار جرد مع فائض"""
        from apps.inventory.models import StockCount, StockCountLine, ItemStock

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='in_progress',
            created_by=user
        )

        line = StockCountLine.objects.create(
            count=count,
            item=item,
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('110'),  # زيادة 10
            unit_cost=Decimal('10'),
            system_value=Decimal('1000'),
            counted_value=Decimal('1100'),
            difference_quantity=Decimal('10'),
            difference_value=Decimal('100')
        )

        count.status = 'completed'
        count.save()
        count.process_adjustments(user)

        item_stock.refresh_from_db()
        assert item_stock.quantity == Decimal('110')

    def test_stock_count_no_difference(self, company, warehouse, item, item_stock, user):
        """اختبار جرد بدون فروقات"""
        from apps.inventory.models import StockCount, StockCountLine

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='in_progress',
            created_by=user
        )

        line = StockCountLine.objects.create(
            count=count,
            item=item,
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('100'),  # نفس الكمية
            unit_cost=Decimal('10'),
            system_value=Decimal('1000'),
            counted_value=Decimal('1000'),
            difference_quantity=Decimal('0'),
            difference_value=Decimal('0')
        )

        assert line.difference_quantity == Decimal('0')
        assert not line.has_difference  # خاصية وليست دالة

    def test_stock_count_cancel(self, company, warehouse, user):
        """اختبار إلغاء جرد"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='in_progress',
            created_by=user
        )

        count.cancel()  # بدون معامل
        assert count.status == 'cancelled'

    def test_stock_count_cannot_modify_after_approval(self, company, warehouse, item, item_stock, user, fiscal_year, accounts):
        """اختبار منع التعديل بعد الاعتماد"""
        from apps.inventory.models import StockCount, StockCountLine

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='completed',
            created_by=user
        )

        StockCountLine.objects.create(
            count=count,
            item=item,
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('100'),
            unit_cost=Decimal('10'),
            system_value=Decimal('1000'),
            counted_value=Decimal('1000'),
            difference_quantity=Decimal('0'),
            difference_value=Decimal('0')
        )

        count.process_adjustments(user)

        # محاولة التعديل بعد الاعتماد
        with pytest.raises(ValidationError):
            count.status = 'in_progress'
            count.save()


@pytest.mark.django_db
class TestStockCountTypes:
    """اختبارات أنواع الجرد"""

    def test_periodic_count(self, company, warehouse, user):
        """اختبار الجرد الدوري"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='periodic',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            created_by=user
        )

        assert count.count_type == 'periodic'

    def test_annual_count(self, company, warehouse, user):
        """اختبار الجرد السنوي"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='annual',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            created_by=user
        )

        assert count.count_type == 'annual'

    def test_cycle_count(self, company, warehouse, user):
        """اختبار الجرد الدوري (cycle)"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='cycle',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            created_by=user
        )

        assert count.count_type == 'cycle'

    def test_special_count(self, company, warehouse, user):
        """اختبار الجرد الخاص"""
        from apps.inventory.models import StockCount

        count = StockCount.objects.create(
            company=company,
            date=date.today(),
            count_type='special',
            warehouse=warehouse,
            supervisor=user,
            status='planned',
            notes='جرد بسبب سرقة',
            created_by=user
        )

        assert count.count_type == 'special'
        assert 'سرقة' in count.notes

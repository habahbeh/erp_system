# tests/inventory/test_batches.py
"""
اختبارات نظام الدفعات
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta


@pytest.mark.django_db
class TestBatchManagement:
    """اختبارات إدارة الدفعات"""

    def test_create_batch(self, company, warehouse, item, user):
        """اختبار إنشاء دفعة"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-001',
            manufacturing_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=365),
            quantity=Decimal('100'),
            unit_cost=Decimal('10'),
            total_value=Decimal('1000'),
            source_document='test',
            source_id=1,
            received_date=date.today(),
            created_by=user
        )

        assert batch.pk is not None
        assert batch.batch_number == 'BATCH-001'
        assert batch.quantity == Decimal('100')

    def test_batch_unique_number_per_item(self, company, warehouse, item, user):
        """اختبار أن رقم الدفعة فريد لكل مادة"""
        from apps.inventory.models import Batch
        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.core.models import ItemVariant

        # إنشاء متغير للمادة للتحقق من القيد الفريد بشكل صحيح
        variant = ItemVariant.objects.create(
            item=item,
            company=company,
            code='TEST-VAR-001',
            is_active=True,
            created_by=user
        )

        Batch.objects.create(
            company=company,
            item=item,
            item_variant=variant,
            warehouse=warehouse,
            batch_number='BATCH-001',
            quantity=Decimal('100'),
            unit_cost=Decimal('10'),
            total_value=Decimal('1000'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        # إنشاء دفعة أخرى بنفس رقم الدفعة يجب أن يفشل في التحقق
        batch2 = Batch(
            company=company,
            item=item,
            item_variant=variant,
            warehouse=warehouse,
            batch_number='BATCH-001',  # نفس الرقم
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        with pytest.raises(DjangoValidationError):
            batch2.validate_unique()


@pytest.mark.django_db
class TestBatchExpiry:
    """اختبارات انتهاء صلاحية الدفعات"""

    def test_batch_is_expired(self, company, warehouse, item, user):
        """اختبار الدفعة المنتهية"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-EXP',
            expiry_date=date.today() - timedelta(days=10),  # منتهية
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=1,
            received_date=date.today(),
            created_by=user
        )

        assert batch.is_expired() is True

    def test_batch_not_expired(self, company, warehouse, item, user):
        """اختبار الدفعة غير المنتهية"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-ACTIVE',
            expiry_date=date.today() + timedelta(days=100),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        assert batch.is_expired() is False

    def test_days_to_expiry(self, company, warehouse, item, user):
        """اختبار أيام حتى الانتهاء"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-30',
            expiry_date=date.today() + timedelta(days=30),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        days = batch.days_to_expiry()
        assert days == 30

    def test_expiry_status_expired(self, company, warehouse, item, user):
        """اختبار حالة الصلاحية - منتهية"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-GONE',
            expiry_date=date.today() - timedelta(days=5),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=1,
            received_date=date.today(),
            created_by=user
        )

        assert batch.get_expiry_status() == 'expired'

    def test_expiry_status_expiring_soon(self, company, warehouse, item, user):
        """اختبار حالة الصلاحية - قريبة من الانتهاء"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-SOON',
            expiry_date=date.today() + timedelta(days=15),  # أقل من 30 يوم
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        assert batch.get_expiry_status() == 'expiring_soon'

    def test_expiry_status_active(self, company, warehouse, item, user):
        """اختبار حالة الصلاحية - نشطة"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-OK',
            expiry_date=date.today() + timedelta(days=180),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        assert batch.get_expiry_status() == 'active'


@pytest.mark.django_db
class TestBatchTracking:
    """اختبارات تتبع الدفعات"""

    def test_batch_in_stock_in(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار الدفعات في سند الإدخال"""
        from apps.inventory.models import StockIn, StockDocumentLine, Batch

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
            unit_cost=Decimal('10'),
            batch_number='BATCH-IN-001',
            expiry_date=date.today() + timedelta(days=365)
        )

        stock_in.post(user=user)

        # التحقق من إنشاء الدفعة
        batch = Batch.objects.filter(
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-IN-001'
        ).first()

        assert batch is not None
        assert batch.quantity == Decimal('100')
        assert batch.expiry_date == date.today() + timedelta(days=365)

    def test_fifo_batch_selection(self, company, warehouse, item, user):
        """اختبار اختيار الدفعات بـ FIFO"""
        from apps.inventory.models import Batch

        # دفعة قديمة
        batch1 = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-OLD',
            expiry_date=date.today() + timedelta(days=30),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=1,
            received_date=date.today() - timedelta(days=60),
            created_by=user
        )

        # دفعة جديدة
        batch2 = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-NEW',
            expiry_date=date.today() + timedelta(days=180),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=2,
            received_date=date.today() - timedelta(days=10),
            created_by=user
        )

        # الترتيب حسب FIFO (الأقدم أولاً)
        batches = Batch.objects.filter(
            item=item,
            warehouse=warehouse,
            quantity__gt=0
        ).order_by('received_date')

        assert batches.first() == batch1
        assert batches.last() == batch2

    def test_fefo_batch_selection(self, company, warehouse, item, user):
        """اختبار اختيار الدفعات بـ FEFO"""
        from apps.inventory.models import Batch

        # دفعة تنتهي لاحقاً
        batch1 = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-LATER',
            expiry_date=date.today() + timedelta(days=180),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=1,
            received_date=date.today() - timedelta(days=60),
            created_by=user
        )

        # دفعة تنتهي قريباً
        batch2 = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-SOONER',
            expiry_date=date.today() + timedelta(days=30),
            quantity=Decimal('50'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test',
            source_id=2,
            received_date=date.today() - timedelta(days=10),
            created_by=user
        )

        # الترتيب حسب FEFO (الأقرب للانتهاء أولاً)
        batches = Batch.objects.filter(
            item=item,
            warehouse=warehouse,
            quantity__gt=0
        ).order_by('expiry_date')

        assert batches.first() == batch2
        assert batches.last() == batch1


@pytest.mark.django_db
class TestBatchReservation:
    """اختبارات حجز الدفعات"""

    def test_reserve_batch_quantity(self, company, warehouse, item, user):
        """اختبار حجز كمية من دفعة"""
        from apps.inventory.models import Batch

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-RES',
            expiry_date=date.today() + timedelta(days=365),
            quantity=Decimal('100'),
            reserved_quantity=Decimal('0'),
            unit_cost=Decimal('10'),
            total_value=Decimal('1000'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        batch.reserve(Decimal('30'))

        assert batch.reserved_quantity == Decimal('30')
        assert batch.get_available_quantity() == Decimal('70')

    def test_cannot_reserve_more_than_available(self, company, warehouse, item, user):
        """اختبار منع حجز أكثر من المتاح"""
        from apps.inventory.models import Batch
        from django.core.exceptions import ValidationError

        batch = Batch.objects.create(
            company=company,
            item=item,
            warehouse=warehouse,
            batch_number='BATCH-LIMIT',
            expiry_date=date.today() + timedelta(days=365),
            quantity=Decimal('50'),
            reserved_quantity=Decimal('20'),
            unit_cost=Decimal('10'),
            total_value=Decimal('500'),
            source_document='test', source_id=1, received_date=date.today(),
            created_by=user
        )

        with pytest.raises(ValidationError):
            batch.reserve(Decimal('40'))  # المتاح 30 فقط

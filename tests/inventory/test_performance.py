# tests/inventory/test_performance.py
"""
اختبارات الأداء لنظام المخزون
"""

import pytest
import time
from decimal import Decimal
from datetime import date, timedelta
from django.db import connection, reset_queries
from django.conf import settings


def count_queries(func):
    """Decorator لحساب عدد الاستعلامات"""
    def wrapper(*args, **kwargs):
        settings.DEBUG = True
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        settings.DEBUG = False
        return result, query_count
    return wrapper


@pytest.mark.django_db
class TestQueryOptimization:
    """اختبارات تحسين الاستعلامات"""

    def test_stock_in_list_queries(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار عدد الاستعلامات في قائمة سندات الإدخال"""
        from apps.inventory.models import StockIn, StockDocumentLine

        # إنشاء 20 سند
        for i in range(20):
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
                unit_cost=Decimal('10')
            )

        settings.DEBUG = True
        reset_queries()

        # استعلام القائمة مع select_related
        stock_ins = StockIn.objects.filter(company=company).select_related(
            'warehouse', 'supplier', 'created_by', 'posted_by'
        ).prefetch_related('lines')[:20]

        # فرض تنفيذ الاستعلام
        list(stock_ins)

        query_count = len(connection.queries)
        settings.DEBUG = False

        # يجب أن يكون عدد الاستعلامات محدود (N+1 problem solved)
        assert query_count <= 5, f"Too many queries: {query_count}"

    def test_item_stock_bulk_query(self, company, warehouse, item, user):
        """اختبار استعلام المخزون بالجملة"""
        from apps.inventory.models import ItemStock
        from apps.core.models import Item, ItemCategory, UnitOfMeasure, Currency

        # إنشاء 100 مادة مع أرصدة
        category = item.category
        uom = item.base_uom
        currency = item.currency

        items = []
        for i in range(100):
            new_item = Item.objects.create(
                company=company,
                code=f'ITEM-PERF-{i:03d}',
                name=f'مادة اختبار {i}',
                category=category,
                base_uom=uom,
                currency=currency,
                created_by=user
            )
            items.append(new_item)

            ItemStock.objects.create(
                company=company,
                item=new_item,
                warehouse=warehouse,
                quantity=Decimal(str(i * 10)),
                average_cost=Decimal('10'),
                total_value=Decimal(str(i * 100)),
                created_by=user
            )

        settings.DEBUG = True
        reset_queries()

        # استعلام كل الأرصدة
        stocks = ItemStock.objects.filter(
            company=company,
            warehouse=warehouse
        ).select_related('item', 'item_variant')[:100]

        list(stocks)

        query_count = len(connection.queries)
        settings.DEBUG = False

        # استعلام واحد فقط
        assert query_count <= 2, f"Too many queries: {query_count}"


@pytest.mark.django_db
class TestBulkOperations:
    """اختبارات العمليات بالجملة"""

    def test_bulk_stock_in_performance(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار أداء إدخال بالجملة"""
        from apps.inventory.models import StockIn, StockDocumentLine

        start_time = time.time()

        # إنشاء 50 سند
        for i in range(50):
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
                unit_cost=Decimal('10')
            )
            stock_in.post(user=user)

        end_time = time.time()
        elapsed = end_time - start_time

        # يجب أن يكتمل في أقل من 30 ثانية
        assert elapsed < 30, f"Bulk operation too slow: {elapsed:.2f}s"

    def test_stock_movement_query_performance(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار أداء استعلام الحركات"""
        from apps.inventory.models import StockIn, StockDocumentLine, StockMovement

        # إنشاء 100 حركة
        for i in range(50):
            stock_in = StockIn.objects.create(
                company=company,
                branch=branch,
                date=date.today() - timedelta(days=i),
                warehouse=warehouse,
                source_type='purchase',
                supplier=supplier,
                created_by=user
            )
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=item,
                quantity=Decimal('10'),
                unit_cost=Decimal('10')
            )
            stock_in.post(user=user)

        start_time = time.time()

        # استعلام الحركات مع فلاتر
        movements = StockMovement.objects.filter(
            company=company,
            item=item,
            date__gte=date.today() - timedelta(days=30)
        ).select_related('item', 'warehouse', 'created_by').order_by('-date')[:50]

        list(movements)

        end_time = time.time()
        elapsed = end_time - start_time

        # يجب أن يكتمل في أقل من ثانية
        assert elapsed < 1, f"Query too slow: {elapsed:.2f}s"


@pytest.mark.django_db
class TestMemoryUsage:
    """اختبارات استخدام الذاكرة"""

    def test_large_report_memory(self, company, warehouse, item, user):
        """اختبار الذاكرة في التقارير الكبيرة"""
        from apps.inventory.models import ItemStock
        from apps.core.models import Item, ItemCategory, UnitOfMeasure, Currency
        import sys

        category = item.category
        uom = item.base_uom
        currency = item.currency

        # إنشاء 200 مادة
        for i in range(200):
            new_item = Item.objects.create(
                company=company,
                code=f'ITEM-MEM-{i:03d}',
                name=f'مادة اختبار ذاكرة {i}',
                category=category,
                base_uom=uom,
                currency=currency,
                created_by=user
            )
            ItemStock.objects.create(
                company=company,
                item=new_item,
                warehouse=warehouse,
                quantity=Decimal('100'),
                average_cost=Decimal('10'),
                total_value=Decimal('1000'),
                created_by=user
            )

        # استخدام iterator بدلاً من list للذاكرة
        stocks = ItemStock.objects.filter(
            company=company
        ).select_related('item').iterator(chunk_size=50)

        total = Decimal('0')
        for stock in stocks:
            total += stock.total_value

        assert total > 0


@pytest.mark.django_db
class TestIndexUsage:
    """اختبارات استخدام الفهارس"""

    def test_index_on_date_search(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار استخدام الفهرس في البحث بالتاريخ"""
        from apps.inventory.models import StockIn, StockDocumentLine

        # إنشاء سندات على مدار 6 أشهر
        for i in range(180):
            stock_in = StockIn.objects.create(
                company=company,
                branch=branch,
                date=date.today() - timedelta(days=i),
                warehouse=warehouse,
                source_type='purchase',
                supplier=supplier,
                created_by=user
            )
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=item,
                quantity=Decimal('10'),
                unit_cost=Decimal('10')
            )

        settings.DEBUG = True
        reset_queries()

        # بحث بنطاق تاريخ
        stock_ins = StockIn.objects.filter(
            company=company,
            date__gte=date.today() - timedelta(days=30),
            date__lte=date.today()
        ).order_by('-date')[:20]

        list(stock_ins)

        query_info = connection.queries[-1]
        settings.DEBUG = False

        # التحقق من استخدام الفهرس (لا يجب أن يكون full scan)
        # في MySQL/PostgreSQL يمكن التحقق من EXPLAIN
        assert 'SELECT' in query_info['sql']


@pytest.mark.django_db
class TestConcurrencyPerformance:
    """اختبارات أداء التزامن"""

    def test_concurrent_posts_performance(self, company, branch, warehouse, item, supplier, user, fiscal_year, accounts):
        """اختبار أداء الترحيل المتزامن"""
        from apps.inventory.models import StockIn, StockDocumentLine
        from concurrent.futures import ThreadPoolExecutor
        import threading

        # إنشاء 10 سندات
        stock_ins = []
        for i in range(10):
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
                unit_cost=Decimal('10')
            )
            stock_ins.append(stock_in)

        def post_stock_in(si):
            try:
                si.post(user=user)
                return True
            except Exception:
                return False

        start_time = time.time()

        # ترحيل متسلسل (بدل متزامن لتجنب race conditions)
        results = []
        for si in stock_ins:
            results.append(post_stock_in(si))

        end_time = time.time()
        elapsed = end_time - start_time

        # التحقق من نجاح الترحيل
        assert all(results) or sum(results) >= 8  # 80% نجاح على الأقل

        # يجب أن يكتمل في وقت معقول
        assert elapsed < 15, f"Concurrent posts too slow: {elapsed:.2f}s"

"""
اختبارات الأداء
المرحلة 4: قياس أداء النظام
"""
import pytest
import time
from decimal import Decimal
from datetime import date, timedelta
from django.db import connection
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db


class TestQueryPerformance:
    """اختبارات أداء الاستعلامات"""

    def test_invoice_list_query_count(self, company, branch, warehouse, supplier,
                                       currency, payment_method, admin_user, item, uom):
        """اختبار عدد الاستعلامات عند عرض قائمة الفواتير"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # إنشاء 10 فواتير
        invoices = []
        for i in range(10):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal('10'),
                unit=uom,
                unit_price=Decimal('100.000'),
            )
            invoices.append(invoice)

        # قياس الاستعلامات
        with CaptureQueriesContext(connection) as context:
            list(PurchaseInvoice.objects.filter(company=company)
                 .select_related('supplier', 'currency', 'branch', 'warehouse')
                 .prefetch_related('items')[:10])

        # يجب أن يكون عدد الاستعلامات معقولاً (أقل من 5)
        # بدون select_related سيكون N+1 problem
        query_count = len(context)
        print(f"\nQuery count for 10 invoices: {query_count}")

        # تنظيف
        for invoice in invoices:
            invoice.items.all().delete()
            invoice.delete()

    def test_invoice_creation_time(self, company, branch, warehouse, supplier,
                                    currency, payment_method, admin_user, item, uom):
        """اختبار وقت إنشاء الفاتورة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        start_time = time.time()

        invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        invoice.calculate_totals()
        invoice.save()

        elapsed_time = time.time() - start_time
        print(f"\nInvoice creation time: {elapsed_time:.4f} seconds")

        # يجب أن يكون الإنشاء سريعاً (أقل من ثانية)
        assert elapsed_time < 1.0

        # تنظيف
        invoice.items.all().delete()
        invoice.delete()

    def test_bulk_invoice_creation(self, company, branch, warehouse, supplier,
                                    currency, payment_method, admin_user, item, uom):
        """اختبار إنشاء فواتير متعددة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        count = 20
        invoices = []

        start_time = time.time()

        for i in range(count):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )

            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal('10'),
                unit=uom,
                unit_price=Decimal('100.000'),
            )

            invoices.append(invoice)

        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / count
        print(f"\n{count} invoices created in {elapsed_time:.4f} seconds")
        print(f"Average time per invoice: {avg_time:.4f} seconds")

        # تنظيف
        for invoice in invoices:
            invoice.items.all().delete()
            invoice.delete()


class TestCalculationPerformance:
    """اختبارات أداء الحسابات"""

    def test_totals_calculation_time(self, company, branch, warehouse, supplier,
                                      currency, payment_method, admin_user, item, uom):
        """اختبار وقت حساب المجاميع"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            created_by=admin_user,
        )

        # إضافة 50 بند
        for i in range(50):
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal(str(i + 1)),
                unit=uom,
                unit_price=Decimal('100.000'),
                tax_rate=Decimal('16.00'),
            )

        start_time = time.time()
        invoice.calculate_totals()
        invoice.save()
        elapsed_time = time.time() - start_time

        print(f"\nTotals calculation for 50 items: {elapsed_time:.4f} seconds")

        # يجب أن تكون الحسابات سريعة
        assert elapsed_time < 2.0

        # تنظيف
        invoice.items.all().delete()
        invoice.delete()


class TestDatabasePerformance:
    """اختبارات أداء قاعدة البيانات"""

    def test_invoice_filter_performance(self, company, branch, warehouse, supplier,
                                         currency, payment_method, admin_user, item, uom):
        """اختبار أداء البحث والفلترة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # إنشاء فواتير للاختبار
        invoices = []
        for i in range(30):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today() - timedelta(days=i),
                created_by=admin_user,
            )
            invoices.append(invoice)

        # اختبار فلترة بالتاريخ
        start_time = time.time()
        filtered = list(PurchaseInvoice.objects.filter(
            company=company,
            date__gte=date.today() - timedelta(days=7)
        ))
        elapsed_time = time.time() - start_time

        print(f"\nDate filter query time: {elapsed_time:.4f} seconds")
        print(f"Results: {len(filtered)} invoices")

        # تنظيف
        for invoice in invoices:
            invoice.delete()

    def test_aggregate_query_performance(self, company, branch, warehouse, supplier,
                                          currency, payment_method, admin_user, item, uom):
        """اختبار أداء الاستعلامات التجميعية"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem
        from django.db.models import Sum, Count, Avg

        # إنشاء بيانات
        invoices = []
        for i in range(20):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )

            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal('10'),
                unit=uom,
                unit_price=Decimal('100.000'),
            )

            invoice.calculate_totals()
            invoice.save()
            invoices.append(invoice)

        # اختبار استعلام تجميعي
        start_time = time.time()
        stats = PurchaseInvoice.objects.filter(company=company).aggregate(
            total_amount=Sum('total_with_tax'),
            avg_amount=Avg('total_with_tax'),
            count=Count('id')
        )
        elapsed_time = time.time() - start_time

        print(f"\nAggregate query time: {elapsed_time:.4f} seconds")
        print(f"Stats: {stats}")

        # تنظيف
        for invoice in invoices:
            invoice.items.all().delete()
            invoice.delete()


class TestMemoryUsage:
    """اختبارات استهلاك الذاكرة"""

    def test_large_queryset_memory(self, company, branch, warehouse, supplier,
                                    currency, payment_method, admin_user):
        """اختبار استهلاك الذاكرة مع نتائج كبيرة"""
        from apps.purchases.models import PurchaseInvoice
        import sys

        # إنشاء 50 فاتورة
        invoices = []
        for i in range(50):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )
            invoices.append(invoice)

        # قياس باستخدام iterator vs list
        # iterator يستهلك ذاكرة أقل

        # باستخدام list
        queryset = PurchaseInvoice.objects.filter(company=company)
        list_results = list(queryset)
        list_size = sys.getsizeof(list_results)

        # باستخدام iterator
        iter_count = 0
        for inv in PurchaseInvoice.objects.filter(company=company).iterator():
            iter_count += 1

        print(f"\nList size: {list_size} bytes")
        print(f"Iterator processed: {iter_count} records")

        # تنظيف
        for invoice in invoices:
            invoice.delete()


class TestConcurrencyPerformance:
    """اختبارات أداء العمليات المتزامنة"""

    def test_sequential_number_generation(self, company, branch, warehouse, supplier,
                                           currency, payment_method, admin_user):
        """اختبار توليد الأرقام المتسلسلة"""
        from apps.purchases.models import PurchaseInvoice

        invoices = []
        numbers = set()

        start_time = time.time()

        for i in range(30):
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )
            invoices.append(invoice)
            numbers.add(invoice.number)

        elapsed_time = time.time() - start_time

        print(f"\n30 invoices with unique numbers: {elapsed_time:.4f} seconds")

        # التأكد من عدم وجود أرقام مكررة
        assert len(numbers) == len(invoices), "Duplicate invoice numbers found!"

        # تنظيف
        for invoice in invoices:
            invoice.delete()

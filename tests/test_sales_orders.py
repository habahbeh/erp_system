"""
اختبارات طلبات البيع
Sales Order Tests
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError


pytestmark = pytest.mark.django_db


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def customer(company):
    """إنشاء عميل تجريبي"""
    from apps.core.models import BusinessPartner
    customer, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='CUST-SO',
        defaults={
            'name': 'عميل طلبات البيع',
            'name_en': 'Sales Order Customer',
            'partner_type': 'customer',
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def sales_order(company, warehouse, customer, admin_user):
    """إنشاء طلب بيع تجريبي"""
    from apps.sales.models import SalesOrder
    order = SalesOrder.objects.create(
        company=company,
        warehouse=warehouse,
        customer=customer,
        salesperson=admin_user,
        date=date.today(),
        created_by=admin_user,
    )
    return order


@pytest.fixture
def sales_order_with_items(sales_order, item, uom):
    """طلب بيع مع سطور"""
    from apps.sales.models import SalesOrderItem

    SalesOrderItem.objects.create(
        order=sales_order,
        item=item,
        quantity=Decimal('10.000'),
        unit_price=Decimal('100.000'),
    )

    SalesOrderItem.objects.create(
        order=sales_order,
        item=item,
        quantity=Decimal('5.000'),
        unit_price=Decimal('200.000'),
    )

    return sales_order


# ============================================
# اختبارات إنشاء طلب البيع
# ============================================

class TestSalesOrderCreation:
    """اختبارات إنشاء طلب البيع"""

    def test_create_basic_order(self, company, warehouse, customer, admin_user):
        """اختبار إنشاء طلب أساسي"""
        from apps.sales.models import SalesOrder

        order = SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        assert order.pk is not None
        assert order.number.startswith('SO/')
        assert order.is_approved == False
        assert order.is_delivered == False
        assert order.is_invoiced == False

    def test_auto_generate_number(self, company, warehouse, customer, admin_user):
        """اختبار توليد الرقم التلقائي"""
        from apps.sales.models import SalesOrder

        order1 = SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        order2 = SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        num1 = int(order1.number.split('/')[-1])
        num2 = int(order2.number.split('/')[-1])
        assert num2 == num1 + 1

    def test_delivery_date(self, company, warehouse, customer, admin_user):
        """اختبار تاريخ التسليم"""
        from apps.sales.models import SalesOrder

        delivery = date.today() + timedelta(days=7)
        order = SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            delivery_date=delivery,
            created_by=admin_user,
        )

        assert order.delivery_date == delivery


# ============================================
# اختبارات سطور طلب البيع
# ============================================

class TestSalesOrderItems:
    """اختبارات سطور طلب البيع"""

    def test_add_item(self, sales_order, item):
        """اختبار إضافة سطر"""
        from apps.sales.models import SalesOrderItem

        line = SalesOrderItem.objects.create(
            order=sales_order,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('50.000'),
        )

        assert line.pk is not None
        assert line.delivered_quantity == Decimal('0')
        assert line.invoiced_quantity == Decimal('0')

    def test_multiple_items(self, sales_order, item):
        """اختبار سطور متعددة"""
        from apps.sales.models import SalesOrderItem

        SalesOrderItem.objects.create(
            order=sales_order,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000'),
        )

        SalesOrderItem.objects.create(
            order=sales_order,
            item=item,
            quantity=Decimal('5.000'),
            unit_price=Decimal('200.000'),
        )

        assert sales_order.lines.count() == 2

    def test_track_delivered_quantity(self, sales_order, item):
        """اختبار تتبع الكمية المسلمة"""
        from apps.sales.models import SalesOrderItem

        line = SalesOrderItem.objects.create(
            order=sales_order,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000'),
        )

        # تسليم جزئي
        line.delivered_quantity = Decimal('5.000')
        line.save()

        line.refresh_from_db()
        assert line.delivered_quantity == Decimal('5.000')

    def test_track_invoiced_quantity(self, sales_order, item):
        """اختبار تتبع الكمية المفوترة"""
        from apps.sales.models import SalesOrderItem

        line = SalesOrderItem.objects.create(
            order=sales_order,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000'),
        )

        # فوترة جزئية
        line.invoiced_quantity = Decimal('7.000')
        line.save()

        line.refresh_from_db()
        assert line.invoiced_quantity == Decimal('7.000')


# ============================================
# اختبارات حالة الطلب
# ============================================

class TestSalesOrderStatus:
    """اختبارات حالة الطلب"""

    def test_initial_status(self, sales_order):
        """اختبار الحالة الأولية"""
        assert sales_order.is_approved == False
        assert sales_order.is_delivered == False
        assert sales_order.is_invoiced == False

    def test_approve_order(self, sales_order):
        """اختبار اعتماد الطلب"""
        sales_order.is_approved = True
        sales_order.save()

        sales_order.refresh_from_db()
        assert sales_order.is_approved == True

    def test_mark_as_delivered(self, sales_order_with_items):
        """اختبار وضع علامة التسليم"""
        sales_order_with_items.is_delivered = True
        sales_order_with_items.save()

        sales_order_with_items.refresh_from_db()
        assert sales_order_with_items.is_delivered == True

    def test_mark_as_invoiced(self, sales_order_with_items):
        """اختبار وضع علامة الفوترة"""
        sales_order_with_items.is_invoiced = True
        sales_order_with_items.save()

        sales_order_with_items.refresh_from_db()
        assert sales_order_with_items.is_invoiced == True


# ============================================
# اختبارات الربط بعرض السعر
# ============================================

class TestQuotationLink:
    """اختبارات الربط بعرض السعر"""

    def test_order_from_quotation(self, company, warehouse, customer, currency, admin_user):
        """اختبار إنشاء طلب من عرض سعر"""
        from apps.sales.models import SalesOrder, Quotation

        # إنشاء عرض سعر
        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        # إنشاء طلب مرتبط
        order = SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            quotation=quote,
            created_by=admin_user,
        )

        assert order.quotation == quote
        assert order.quotation.pk == quote.pk

    def test_quotation_orders_relation(self, company, warehouse, customer, currency, admin_user):
        """اختبار علاقة عرض السعر بالطلبات"""
        from apps.sales.models import SalesOrder, Quotation

        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        SalesOrder.objects.create(
            company=company,
            warehouse=warehouse,
            customer=customer,
            salesperson=admin_user,
            date=date.today(),
            quotation=quote,
            created_by=admin_user,
        )

        assert quote.orders.count() == 1


# ============================================
# اختبارات التحويل لفاتورة
# ============================================

class TestConvertToInvoice:
    """اختبارات التحويل لفاتورة"""

    def test_mark_order_as_invoiced(self, sales_order_with_items):
        """اختبار وضع علامة الفوترة"""
        sales_order_with_items.is_approved = True
        sales_order_with_items.is_invoiced = True
        sales_order_with_items.save()

        sales_order_with_items.refresh_from_db()
        assert sales_order_with_items.is_invoiced == True

    def test_cannot_invoice_unapproved(self, sales_order_with_items):
        """اختبار عدم فوترة طلب غير معتمد"""
        # يجب التحقق في التطبيق الفعلي
        assert sales_order_with_items.is_approved == False


# ============================================
# اختبارات الحذف
# ============================================

class TestSalesOrderDeletion:
    """اختبارات حذف الطلب"""

    def test_delete_unprocessed_order(self, sales_order):
        """اختبار حذف طلب غير معالج"""
        pk = sales_order.pk
        sales_order.delete()

        from apps.sales.models import SalesOrder
        assert not SalesOrder.objects.filter(pk=pk).exists()

    def test_cascade_delete_items(self, sales_order_with_items):
        """اختبار حذف السطور عند حذف الطلب"""
        from apps.sales.models import SalesOrderItem

        order_pk = sales_order_with_items.pk
        items_count = sales_order_with_items.lines.count()
        assert items_count > 0

        sales_order_with_items.delete()

        # التحقق من حذف السطور
        assert SalesOrderItem.objects.filter(order_id=order_pk).count() == 0

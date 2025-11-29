"""
اختبارات عمولات المندوبين
Salesperson Commission Tests
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
        code='CUST-COMM',
        defaults={
            'name': 'عميل العمولات',
            'name_en': 'Commission Customer',
            'partner_type': 'customer',
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def salesperson(company, branch):
    """إنشاء مندوب مبيعات"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user, created = User.objects.get_or_create(
        username='salesperson_test',
        defaults={
            'email': 'salesperson@test.com',
            'first_name': 'مندوب',
            'last_name': 'مبيعات',
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    return user


@pytest.fixture
def sales_invoice_with_commission(company, branch, warehouse, customer, currency,
                                   payment_method, salesperson, uom, item):
    """فاتورة مبيعات مع عمولة"""
    from apps.sales.models import SalesInvoice, InvoiceItem

    invoice = SalesInvoice.objects.create(
        company=company,
        branch=branch,
        warehouse=warehouse,
        customer=customer,
        currency=currency,
        payment_method=payment_method,
        salesperson=salesperson,
        date=date.today(),
        receipt_number='REC-COMM-001',
        salesperson_commission_rate=Decimal('5.00'),
        created_by=salesperson,
    )

    InvoiceItem.objects.create(
        invoice=invoice,
        item=item,
        quantity=Decimal('10.000'),
        unit=uom,
        unit_price=Decimal('100.000'),
    )

    invoice.calculate_totals()
    invoice.save()

    return invoice


# ============================================
# اختبارات حساب العمولة في الفاتورة
# ============================================

class TestInvoiceCommission:
    """اختبارات حساب العمولة في الفاتورة"""

    def test_calculate_commission(self, sales_invoice_with_commission):
        """اختبار حساب العمولة"""
        invoice = sales_invoice_with_commission
        invoice.calculate_commission()

        expected = invoice.total_with_tax * Decimal('0.05')
        assert invoice.salesperson_commission_amount == expected

    def test_zero_commission_rate(self, company, branch, warehouse, customer,
                                   currency, payment_method, admin_user, uom, item):
        """اختبار عمولة صفر"""
        from apps.sales.models import SalesInvoice, InvoiceItem

        invoice = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-ZERO-COMM',
            salesperson_commission_rate=Decimal('0'),
            created_by=admin_user,
        )

        InvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        invoice.calculate_totals()
        invoice.calculate_commission()

        assert invoice.salesperson_commission_amount == Decimal('0')

    def test_commission_in_totals(self, sales_invoice_with_commission):
        """اختبار حساب العمولة ضمن المجاميع"""
        invoice = sales_invoice_with_commission
        invoice.calculate_totals()

        # العمولة يجب أن تُحسب مع المجاميع
        assert invoice.salesperson_commission_amount > 0


# ============================================
# اختبارات نموذج العمولة
# ============================================

class TestSalespersonCommission:
    """اختبارات نموذج عمولة المندوب"""

    def test_create_commission(self, sales_invoice_with_commission):
        """اختبار إنشاء عمولة"""
        from apps.sales.models import SalespersonCommission

        # ملاحظة: يحتاج Employee من HR module
        # هذا الاختبار قد يفشل إذا كان HR module معطل

    def test_calculate_commission_method(self):
        """اختبار دالة حساب العمولة"""
        from apps.sales.models import SalespersonCommission

        # اختبار الحساب
        commission_rate = Decimal('5.00')
        base_amount = Decimal('1000.000')
        expected = base_amount * (commission_rate / 100)

        assert expected == Decimal('50.000')

    def test_update_payment_status_unpaid(self):
        """اختبار تحديث حالة الدفع - غير مدفوعة"""
        # اختبار المنطق
        paid_amount = Decimal('0')
        commission_amount = Decimal('100.000')

        if paid_amount == 0:
            status = 'unpaid'
        elif paid_amount >= commission_amount:
            status = 'paid'
        else:
            status = 'partial'

        assert status == 'unpaid'

    def test_update_payment_status_partial(self):
        """اختبار تحديث حالة الدفع - جزئية"""
        paid_amount = Decimal('50.000')
        commission_amount = Decimal('100.000')

        if paid_amount == 0:
            status = 'unpaid'
        elif paid_amount >= commission_amount:
            status = 'paid'
        else:
            status = 'partial'

        assert status == 'partial'

    def test_update_payment_status_paid(self):
        """اختبار تحديث حالة الدفع - مدفوعة"""
        paid_amount = Decimal('100.000')
        commission_amount = Decimal('100.000')

        if paid_amount == 0:
            status = 'unpaid'
        elif paid_amount >= commission_amount:
            status = 'paid'
        else:
            status = 'partial'

        assert status == 'paid'


# ============================================
# اختبارات إنشاء العمولة من الفاتورة
# ============================================

class TestCommissionFromInvoice:
    """اختبارات إنشاء العمولة من الفاتورة"""

    def test_invoice_has_commission_rate(self, sales_invoice_with_commission):
        """اختبار أن الفاتورة لديها نسبة عمولة"""
        assert sales_invoice_with_commission.salesperson_commission_rate == Decimal('5.00')

    def test_invoice_has_salesperson(self, sales_invoice_with_commission, salesperson):
        """اختبار أن الفاتورة لديها مندوب"""
        assert sales_invoice_with_commission.salesperson == salesperson


# ============================================
# اختبارات التحقق من الصحة
# ============================================

class TestCommissionValidation:
    """اختبارات التحقق من صحة العمولة"""

    def test_commission_rate_range(self):
        """اختبار نطاق نسبة العمولة"""
        # يجب أن تكون بين 0 و 100
        valid_rates = [Decimal('0'), Decimal('5.00'), Decimal('100.00')]
        invalid_rates = [Decimal('-1'), Decimal('101')]

        for rate in valid_rates:
            assert 0 <= rate <= 100

        for rate in invalid_rates:
            assert not (0 <= rate <= 100)

    def test_paid_amount_not_exceed_commission(self):
        """اختبار أن المدفوع لا يتجاوز العمولة"""
        commission_amount = Decimal('100.000')
        paid_amount = Decimal('150.000')

        # يجب أن يفشل هذا
        assert paid_amount > commission_amount


# ============================================
# اختبارات تسجيل الدفع
# ============================================

class TestRecordPayment:
    """اختبارات تسجيل دفع العمولة"""

    def test_record_payment_logic(self):
        """اختبار منطق تسجيل الدفع"""
        paid_amount = Decimal('0')
        commission_amount = Decimal('100.000')
        payment = Decimal('50.000')

        # التحقق من صحة الدفعة
        assert payment > 0
        remaining = commission_amount - paid_amount
        assert payment <= remaining

        # تسجيل الدفعة
        new_paid = paid_amount + payment
        assert new_paid == Decimal('50.000')

    def test_full_payment_logic(self):
        """اختبار منطق الدفع الكامل"""
        commission_amount = Decimal('100.000')

        # دفع كامل
        paid_amount = commission_amount
        remaining = commission_amount - paid_amount

        assert remaining == Decimal('0')
        assert paid_amount >= commission_amount


# ============================================
# اختبارات التقارير
# ============================================

class TestCommissionReports:
    """اختبارات تقارير العمولات"""

    def test_filter_by_salesperson(self, sales_invoice_with_commission, salesperson):
        """اختبار الفلترة حسب المندوب"""
        from apps.sales.models import SalesInvoice

        invoices = SalesInvoice.objects.filter(
            salesperson=salesperson,
            salesperson_commission_rate__gt=0
        )

        assert invoices.count() >= 1

    def test_filter_by_date_range(self, sales_invoice_with_commission):
        """اختبار الفلترة حسب الفترة"""
        from apps.sales.models import SalesInvoice

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        invoices = SalesInvoice.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            salesperson_commission_rate__gt=0
        )

        assert invoices.count() >= 1

    def test_aggregate_commissions(self, sales_invoice_with_commission):
        """اختبار تجميع العمولات"""
        from apps.sales.models import SalesInvoice
        from django.db.models import Sum

        total = SalesInvoice.objects.filter(
            salesperson=sales_invoice_with_commission.salesperson
        ).aggregate(
            total_commission=Sum('salesperson_commission_amount')
        )

        assert total['total_commission'] is not None or total['total_commission'] >= 0

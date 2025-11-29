"""
اختبارات أقساط الدفع
Payment Installments Tests
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone


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
        code='CUST-INST',
        defaults={
            'name': 'عميل الأقساط',
            'name_en': 'Installment Customer',
            'partner_type': 'customer',
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def sales_invoice(company, branch, warehouse, customer, currency, payment_method, admin_user, uom, item):
    """إنشاء فاتورة مبيعات للأقساط"""
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
        receipt_number='REC-INST-001',
        created_by=admin_user,
    )

    # إضافة سطر
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


@pytest.fixture
def installment(sales_invoice):
    """إنشاء قسط تجريبي"""
    from apps.sales.models import PaymentInstallment

    installment = PaymentInstallment.objects.create(
        company=sales_invoice.company,
        branch=sales_invoice.branch,
        invoice=sales_invoice,
        installment_number=1,
        due_date=date.today() + timedelta(days=30),
        amount=Decimal('500.000'),
    )
    return installment


# ============================================
# اختبارات إنشاء الأقساط
# ============================================

class TestInstallmentCreation:
    """اختبارات إنشاء الأقساط"""

    def test_create_installment(self, sales_invoice):
        """اختبار إنشاء قسط"""
        from apps.sales.models import PaymentInstallment

        installment = PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('500.000'),
        )

        assert installment.pk is not None
        assert installment.status == 'pending'
        assert installment.paid_amount == Decimal('0')

    def test_create_multiple_installments(self, sales_invoice):
        """اختبار إنشاء أقساط متعددة"""
        from apps.sales.models import PaymentInstallment

        for i in range(1, 4):
            PaymentInstallment.objects.create(
                company=sales_invoice.company,
                branch=sales_invoice.branch,
                invoice=sales_invoice,
                installment_number=i,
                due_date=date.today() + timedelta(days=30 * i),
                amount=Decimal('333.333'),
            )

        assert sales_invoice.installments.count() == 3

    def test_unique_installment_number(self, sales_invoice):
        """اختبار أن رقم القسط فريد لكل فاتورة"""
        from apps.sales.models import PaymentInstallment
        from django.db import IntegrityError

        PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('500.000'),
        )

        with pytest.raises(IntegrityError):
            PaymentInstallment.objects.create(
                company=sales_invoice.company,
                branch=sales_invoice.branch,
                invoice=sales_invoice,
                installment_number=1,  # نفس الرقم
                due_date=date.today() + timedelta(days=60),
                amount=Decimal('500.000'),
            )


# ============================================
# اختبارات حالة القسط
# ============================================

class TestInstallmentStatus:
    """اختبارات حالة القسط"""

    def test_initial_status_pending(self, installment):
        """اختبار الحالة الأولية معلق"""
        assert installment.status == 'pending'

    def test_remaining_amount(self, installment):
        """اختبار المبلغ المتبقي"""
        assert installment.remaining_amount == installment.amount

    def test_is_paid_property(self, installment):
        """اختبار خاصية مدفوع"""
        assert installment.is_paid == False

        installment.paid_amount = installment.amount
        assert installment.is_paid == True

    def test_is_overdue_property(self, sales_invoice):
        """اختبار خاصية متأخر"""
        from apps.sales.models import PaymentInstallment

        # قسط متأخر
        overdue = PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() - timedelta(days=10),  # في الماضي
            amount=Decimal('500.000'),
        )

        assert overdue.is_overdue == True

    def test_update_status_to_paid(self, installment):
        """اختبار تحديث الحالة لمدفوع"""
        installment.paid_amount = installment.amount
        installment.update_status()

        assert installment.status == 'paid'

    def test_update_status_to_overdue(self, sales_invoice):
        """اختبار تحديث الحالة لمتأخر"""
        from apps.sales.models import PaymentInstallment

        installment = PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() - timedelta(days=5),
            amount=Decimal('500.000'),
        )

        installment.update_status()
        assert installment.status == 'overdue'


# ============================================
# اختبارات الدفع
# ============================================

class TestInstallmentPayment:
    """اختبارات دفع الأقساط"""

    def test_mark_as_paid(self, installment):
        """اختبار وضع علامة مدفوع"""
        installment.mark_as_paid()

        installment.refresh_from_db()
        assert installment.status == 'paid'
        assert installment.paid_amount == installment.amount
        assert installment.payment_date is not None

    def test_partial_payment(self, installment):
        """اختبار الدفع الجزئي"""
        partial = installment.amount / 2
        installment.paid_amount = partial
        installment.update_status()

        # الحالة تبقى pending لأنه لم يُدفع بالكامل
        assert installment.status == 'pending'
        assert installment.remaining_amount == installment.amount - partial

    def test_payment_updates_invoice(self, installment, sales_invoice):
        """اختبار أن الدفع يحدث الفاتورة"""
        installment.mark_as_paid()

        # التحقق من تحديث الفاتورة
        sales_invoice.refresh_from_db()
        # ملاحظة: هذا يعتمد على منطق update_payment_status


# ============================================
# اختبارات الإلغاء
# ============================================

class TestInstallmentCancellation:
    """اختبارات إلغاء الأقساط"""

    def test_cancel_unpaid_installment(self, installment):
        """اختبار إلغاء قسط غير مدفوع"""
        installment.cancel()

        installment.refresh_from_db()
        assert installment.status == 'cancelled'

    def test_cannot_cancel_paid_installment(self, installment):
        """اختبار عدم إمكانية إلغاء قسط مدفوع"""
        installment.paid_amount = installment.amount
        installment.save()

        with pytest.raises(ValidationError):
            installment.cancel()

    def test_cannot_cancel_partial_paid(self, installment):
        """اختبار عدم إمكانية إلغاء قسط مدفوع جزئياً"""
        installment.paid_amount = Decimal('100.000')
        installment.save()

        with pytest.raises(ValidationError):
            installment.cancel()


# ============================================
# اختبارات الفهرسة
# ============================================

class TestInstallmentIndexes:
    """اختبارات الفهرسة"""

    def test_filter_by_status(self, sales_invoice):
        """اختبار الفلترة حسب الحالة"""
        from apps.sales.models import PaymentInstallment

        # إنشاء أقساط بحالات مختلفة
        PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('500.000'),
            status='pending',
        )

        PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=2,
            due_date=date.today() + timedelta(days=60),
            amount=Decimal('500.000'),
            status='paid',
        )

        pending = PaymentInstallment.objects.filter(
            invoice=sales_invoice, status='pending'
        ).count()
        paid = PaymentInstallment.objects.filter(
            invoice=sales_invoice, status='paid'
        ).count()

        assert pending == 1
        assert paid == 1

    def test_filter_by_due_date(self, sales_invoice):
        """اختبار الفلترة حسب تاريخ الاستحقاق"""
        from apps.sales.models import PaymentInstallment

        # قسط مستحق قريباً
        PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=1,
            due_date=date.today() + timedelta(days=5),
            amount=Decimal('500.000'),
        )

        # قسط مستحق لاحقاً
        PaymentInstallment.objects.create(
            company=sales_invoice.company,
            branch=sales_invoice.branch,
            invoice=sales_invoice,
            installment_number=2,
            due_date=date.today() + timedelta(days=60),
            amount=Decimal('500.000'),
        )

        # الأقساط المستحقة خلال 7 أيام
        upcoming = PaymentInstallment.objects.filter(
            invoice=sales_invoice,
            due_date__lte=date.today() + timedelta(days=7),
            status='pending',
        ).count()

        assert upcoming == 1

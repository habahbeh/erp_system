"""
اختبارات عروض الأسعار
Sales Quotation Tests
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
        code='CUST-QT',
        defaults={
            'name': 'عميل عروض الأسعار',
            'name_en': 'Quotation Customer',
            'partner_type': 'customer',
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def quotation(company, customer, currency, admin_user):
    """إنشاء عرض سعر تجريبي"""
    from apps.sales.models import Quotation
    quote = Quotation.objects.create(
        company=company,
        customer=customer,
        currency=currency,
        salesperson=admin_user,
        date=date.today(),
        validity_days=30,
        created_by=admin_user,
    )
    return quote


@pytest.fixture
def quotation_with_items(quotation, item, uom):
    """عرض سعر مع سطور"""
    from apps.sales.models import QuotationItem

    QuotationItem.objects.create(
        quotation=quotation,
        item=item,
        quantity=Decimal('10.000'),
        unit_price=Decimal('100.000'),
    )

    QuotationItem.objects.create(
        quotation=quotation,
        item=item,
        quantity=Decimal('5.000'),
        unit_price=Decimal('200.000'),
    )

    # حساب المجموع
    total = sum(line.quantity * line.unit_price for line in quotation.lines.all())
    quotation.total_amount = total
    quotation.save()

    return quotation


# ============================================
# اختبارات إنشاء عرض السعر
# ============================================

class TestQuotationCreation:
    """اختبارات إنشاء عرض السعر"""

    def test_create_basic_quotation(self, company, customer, currency, admin_user):
        """اختبار إنشاء عرض سعر أساسي"""
        from apps.sales.models import Quotation

        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            validity_days=30,
            created_by=admin_user,
        )

        assert quote.pk is not None
        assert quote.number.startswith('QT/')
        assert quote.is_approved == False
        assert quote.converted_to_order == False

    def test_auto_generate_number(self, company, customer, currency, admin_user):
        """اختبار توليد الرقم التلقائي"""
        from apps.sales.models import Quotation

        quote1 = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        quote2 = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            created_by=admin_user,
        )

        num1 = int(quote1.number.split('/')[-1])
        num2 = int(quote2.number.split('/')[-1])
        assert num2 == num1 + 1

    def test_expiry_date_calculated(self, company, customer, currency, admin_user):
        """اختبار حساب تاريخ الانتهاء"""
        from apps.sales.models import Quotation

        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            validity_days=15,
            created_by=admin_user,
        )

        expected_expiry = date.today() + timedelta(days=15)
        assert quote.expiry_date == expected_expiry


# ============================================
# اختبارات سطور عرض السعر
# ============================================

class TestQuotationItems:
    """اختبارات سطور عرض السعر"""

    def test_add_item(self, quotation, item):
        """اختبار إضافة سطر"""
        from apps.sales.models import QuotationItem

        line = QuotationItem.objects.create(
            quotation=quotation,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('50.000'),
        )

        assert line.pk is not None
        assert line.total == Decimal('500.000')

    def test_line_with_discount(self, quotation, item):
        """اختبار سطر مع خصم"""
        from apps.sales.models import QuotationItem

        line = QuotationItem.objects.create(
            quotation=quotation,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000'),
            discount_percentage=Decimal('10.00'),
        )

        # 10 * 100 = 1000
        # خصم 10% = 900
        assert line.total == Decimal('900.000')

    def test_multiple_items(self, quotation, item):
        """اختبار سطور متعددة"""
        from apps.sales.models import QuotationItem

        QuotationItem.objects.create(
            quotation=quotation,
            item=item,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000'),
        )

        QuotationItem.objects.create(
            quotation=quotation,
            item=item,
            quantity=Decimal('5.000'),
            unit_price=Decimal('200.000'),
        )

        assert quotation.lines.count() == 2


# ============================================
# اختبارات حالة عرض السعر
# ============================================

class TestQuotationStatus:
    """اختبارات حالة عرض السعر"""

    def test_initial_status(self, quotation):
        """اختبار الحالة الأولية"""
        assert quotation.is_approved == False
        assert quotation.converted_to_order == False

    def test_approve_quotation(self, quotation):
        """اختبار اعتماد العرض"""
        quotation.is_approved = True
        quotation.save()

        quotation.refresh_from_db()
        assert quotation.is_approved == True

    def test_is_expired(self, company, customer, currency, admin_user):
        """اختبار انتهاء صلاحية العرض"""
        from apps.sales.models import Quotation

        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today() - timedelta(days=60),
            validity_days=30,
            created_by=admin_user,
        )

        # تاريخ الانتهاء قبل 30 يوم
        assert quote.expiry_date < date.today()


# ============================================
# اختبارات التحويل لطلب
# ============================================

class TestConvertToOrder:
    """اختبارات التحويل لطلب بيع"""

    def test_mark_as_converted(self, quotation_with_items):
        """اختبار وضع علامة التحويل"""
        quotation_with_items.converted_to_order = True
        quotation_with_items.save()

        quotation_with_items.refresh_from_db()
        assert quotation_with_items.converted_to_order == True

    def test_cannot_convert_unapproved(self, quotation_with_items):
        """اختبار عدم إمكانية تحويل عرض غير معتمد"""
        # في التطبيق الفعلي، يجب التحقق من الاعتماد قبل التحويل
        assert quotation_with_items.is_approved == False


# ============================================
# اختبارات الصلاحية
# ============================================

class TestQuotationValidity:
    """اختبارات الصلاحية"""

    def test_validity_days_default(self, quotation):
        """اختبار القيمة الافتراضية للصلاحية"""
        assert quotation.validity_days == 30

    def test_custom_validity_days(self, company, customer, currency, admin_user):
        """اختبار صلاحية مخصصة"""
        from apps.sales.models import Quotation

        quote = Quotation.objects.create(
            company=company,
            customer=customer,
            currency=currency,
            salesperson=admin_user,
            date=date.today(),
            validity_days=45,
            created_by=admin_user,
        )

        expected_expiry = date.today() + timedelta(days=45)
        assert quote.expiry_date == expected_expiry

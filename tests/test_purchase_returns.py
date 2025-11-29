"""
اختبارات مرتجعات المشتريات
المرحلة 2: الاختبارات الوظيفية
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


class TestPurchaseReturnCreation:
    """اختبارات إنشاء مرتجعات المشتريات"""

    def test_create_return(self, company, branch, warehouse, supplier,
                           currency, payment_method, admin_user, item, uom):
        """اختبار إنشاء مرتجع"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        line = PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item,
            quantity=Decimal('5'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        assert return_invoice.invoice_type == 'return'
        assert return_invoice.number.startswith('PR/')
        assert line.subtotal == Decimal('500.000')

    def test_link_return_to_invoice(self, company, branch, warehouse, supplier,
                                     currency, payment_method, admin_user, item, uom):
        """اختبار ربط مرتجع بفاتورة أصلية"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # إنشاء الفاتورة الأصلية
        original = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='purchase',
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=original,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # إنشاء المرتجع مع الربط
        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            original_invoice=original,
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item,
            quantity=Decimal('2'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        assert return_invoice.original_invoice == original
        assert original.returns.count() == 1
        assert original.returns.first() == return_invoice

    def test_return_with_same_supplier(self, company, branch, warehouse, supplier,
                                        currency, payment_method, admin_user, item, uom):
        """اختبار أن المرتجع يحتفظ بنفس المورد"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        original = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='purchase',
            created_by=admin_user,
        )

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            original_invoice=original,
            created_by=admin_user,
        )

        assert return_invoice.supplier == original.supplier

    def test_return_partial_quantity(self, company, branch, warehouse, supplier,
                                      currency, payment_method, admin_user, item, uom):
        """اختبار إرجاع كمية جزئية"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # فاتورة أصلية بـ 10 قطع
        original = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='purchase',
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=original,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # إرجاع 3 قطع فقط
        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            original_invoice=original,
            created_by=admin_user,
        )

        return_line = PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item,
            quantity=Decimal('3'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # الفاتورة الأصلية = 1000
        # المرتجع = 300
        original.calculate_totals()
        return_invoice.calculate_totals()

        assert original.subtotal_before_discount == Decimal('1000.000')
        assert return_invoice.subtotal_before_discount == Decimal('300.000')


class TestReturnNumbering:
    """اختبارات ترقيم المرتجعات"""

    def test_return_number_prefix(self, company, branch, warehouse, supplier,
                                   currency, payment_method, admin_user):
        """اختبار بادئة رقم المرتجع"""
        from apps.purchases.models import PurchaseInvoice

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        year = date.today().strftime('%Y')
        assert return_invoice.number.startswith(f'PR/{year}/')

    def test_return_sequential_numbers(self, company, branch, warehouse, supplier,
                                        currency, payment_method, admin_user):
        """اختبار الترقيم المتسلسل للمرتجعات"""
        from apps.purchases.models import PurchaseInvoice

        return1 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        return2 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        num1 = int(return1.number.split('/')[-1])
        num2 = int(return2.number.split('/')[-1])

        assert num2 == num1 + 1

    def test_separate_numbering_for_invoices_and_returns(self, company, branch,
                                                          warehouse, supplier,
                                                          currency, payment_method,
                                                          admin_user):
        """اختبار أن الفواتير والمرتجعات لها ترقيم منفصل"""
        from apps.purchases.models import PurchaseInvoice

        # فاتورة
        invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='purchase',
            created_by=admin_user,
        )

        # مرتجع
        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        assert invoice.number.startswith('PI/')
        assert return_invoice.number.startswith('PR/')


class TestReturnCalculations:
    """اختبارات حسابات المرتجعات"""

    def test_return_with_discount(self, company, branch, warehouse, supplier,
                                   currency, payment_method, admin_user, item, uom):
        """اختبار مرتجع مع خصم"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item,
            quantity=Decimal('5'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        return_invoice.calculate_totals()
        return_invoice.save()

        # 5 * 100 = 500
        # خصم 10% = 50
        # بعد الخصم = 450

        assert return_invoice.subtotal_before_discount == Decimal('500.000')
        assert return_invoice.discount_amount == Decimal('50.000')
        assert return_invoice.subtotal_after_discount == Decimal('450.000')

    def test_return_with_tax(self, company, branch, warehouse, supplier,
                             currency, payment_method, admin_user, item, uom):
        """اختبار مرتجع مع ضريبة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        line = PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item,
            quantity=Decimal('5'),
            unit=uom,
            unit_price=Decimal('100.000'),
            tax_rate=Decimal('16.00'),
            tax_included=False,
        )

        return_invoice.calculate_totals()
        return_invoice.save()

        # 5 * 100 = 500
        # ضريبة = 80
        assert line.tax_amount == Decimal('80.000')
        assert return_invoice.tax_amount == Decimal('80.000')


class TestMultipleReturns:
    """اختبارات المرتجعات المتعددة"""

    def test_multiple_returns_for_one_invoice(self, company, branch, warehouse,
                                               supplier, currency, payment_method,
                                               admin_user, item, uom):
        """اختبار عدة مرتجعات لفاتورة واحدة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # الفاتورة الأصلية بـ 10 قطع
        original = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='purchase',
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=original,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # مرتجع 1: 2 قطع
        return1 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            original_invoice=original,
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=return1,
            item=item,
            quantity=Decimal('2'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # مرتجع 2: 3 قطع
        return2 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            original_invoice=original,
            created_by=admin_user,
        )

        PurchaseInvoiceItem.objects.create(
            invoice=return2,
            item=item,
            quantity=Decimal('3'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # التحقق
        assert original.returns.count() == 2

        # حساب إجمالي المرتجعات
        total_returned = sum(
            r.subtotal_before_discount
            for r in original.returns.all()
        )

        return1.calculate_totals()
        return2.calculate_totals()

        # 200 + 300 = 500
        assert return1.subtotal_before_discount + return2.subtotal_before_discount == Decimal('500.000')


class TestReturnWithVariants:
    """اختبارات مرتجعات المواد ذات المتغيرات"""

    def test_return_item_with_variant(self, company, branch, warehouse, supplier,
                                       currency, payment_method, admin_user,
                                       item_with_variants, uom):
        """اختبار إرجاع مادة مع متغير"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem
        from apps.core.models import ItemVariant

        variant = item_with_variants.variants.first()

        return_invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            invoice_type='return',
            created_by=admin_user,
        )

        line = PurchaseInvoiceItem.objects.create(
            invoice=return_invoice,
            item=item_with_variants,
            item_variant=variant,
            quantity=Decimal('2'),
            unit=uom,
            unit_price=Decimal('150.000'),
        )

        assert line.item_variant == variant
        assert line.subtotal == Decimal('300.000')

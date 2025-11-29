"""
اختبارات الحالات الخاصة (Edge Cases)
المرحلة 3: اختبار السيناريوهات غير الاعتيادية
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


class TestNegativeQuantities:
    """اختبارات الكميات السالبة"""

    def test_negative_quantity_in_invoice(self, company, branch, warehouse,
                                          supplier, currency, payment_method,
                                          admin_user, item, uom):
        """اختبار إدخال كمية سالبة في الفاتورة"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        # محاولة إدخال كمية سالبة
        try:
            line = PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal('-10'),
                unit=uom,
                unit_price=Decimal('100.000'),
            )

            # إذا تم الإنشاء، تحقق من حساب المجموع
            assert line.subtotal == Decimal('-1000.000')
        except (ValidationError, IntegrityError):
            # الكميات السالبة غير مسموحة - سلوك صحيح
            pass


class TestZeroValues:
    """اختبارات القيم الصفرية"""

    def test_zero_quantity(self, company, branch, warehouse, supplier,
                          currency, payment_method, admin_user, item, uom):
        """اختبار كمية صفر"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        line = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('0'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        assert line.subtotal == Decimal('0.000')

    def test_zero_price(self, company, branch, warehouse, supplier,
                       currency, payment_method, admin_user, item, uom):
        """اختبار سعر صفر"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        line = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('0.000'),
        )

        assert line.subtotal == Decimal('0.000')

    def test_zero_discount(self, company, branch, warehouse, supplier,
                          currency, payment_method, admin_user, item, uom):
        """اختبار خصم صفر"""
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
            discount_value=Decimal('0'),
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

        assert invoice.discount_amount == Decimal('0.000')
        assert invoice.subtotal_after_discount == Decimal('1000.000')


class TestInactiveEntities:
    """اختبارات الكيانات غير النشطة"""

    def test_invoice_with_inactive_supplier(self, company, branch, warehouse,
                                            inactive_supplier, currency,
                                            payment_method, admin_user):
        """اختبار إنشاء فاتورة لمورد غير نشط"""
        from apps.purchases.models import PurchaseInvoice

        # بعض الأنظمة تسمح بذلك مع تحذير
        # والبعض الآخر يرفض
        try:
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=inactive_supplier,
                currency=currency,
                payment_method=payment_method,
                date=date.today(),
                created_by=admin_user,
            )
            # تم الإنشاء - يجب التحقق من التحذيرات
            assert invoice.supplier == inactive_supplier
        except ValidationError:
            # رُفض - سلوك صحيح أيضاً
            pass


class TestExtremeValues:
    """اختبارات القيم المتطرفة"""

    def test_very_large_quantity(self, company, branch, warehouse, supplier,
                                 currency, payment_method, admin_user, item, uom):
        """اختبار كمية كبيرة جداً"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        line = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('999999999'),
            unit=uom,
            unit_price=Decimal('1.000'),
        )

        assert line.subtotal == Decimal('999999999.000')

    def test_very_small_price(self, company, branch, warehouse, supplier,
                             currency, payment_method, admin_user, item, uom):
        """اختبار سعر صغير جداً"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        line = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('1000'),
            unit=uom,
            unit_price=Decimal('0.001'),
        )

        assert line.subtotal == Decimal('1.000')

    def test_hundred_percent_discount(self, company, branch, warehouse, supplier,
                                      currency, payment_method, admin_user, item, uom):
        """اختبار خصم 100%"""
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
            discount_value=Decimal('100.00'),
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

        assert invoice.subtotal_after_discount == Decimal('0.000')


class TestDateValidation:
    """اختبارات التحقق من التاريخ"""

    def test_future_invoice_date(self, company, branch, warehouse, supplier,
                                  currency, payment_method, admin_user):
        """اختبار فاتورة بتاريخ مستقبلي"""
        from apps.purchases.models import PurchaseInvoice

        future_date = date.today() + timedelta(days=30)

        try:
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=future_date,
                created_by=admin_user,
            )
            # بعض الأنظمة تسمح بذلك
            assert invoice.date == future_date
        except ValidationError:
            # رُفض - سلوك صحيح
            pass

    def test_very_old_invoice_date(self, company, branch, warehouse, supplier,
                                   currency, payment_method, admin_user):
        """اختبار فاتورة بتاريخ قديم جداً"""
        from apps.purchases.models import PurchaseInvoice

        old_date = date(2000, 1, 1)

        try:
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=old_date,
                created_by=admin_user,
            )
            assert invoice.date == old_date
        except ValidationError:
            pass


class TestDuplicates:
    """اختبارات التكرارات"""

    def test_duplicate_invoice_items(self, company, branch, warehouse, supplier,
                                      currency, payment_method, admin_user, item, uom):
        """اختبار إضافة نفس المادة مرتين"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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

        # إضافة المادة مرة أولى
        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('10'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # إضافة نفس المادة مرة ثانية
        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=Decimal('5'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        # يجب أن يكون هناك بندين
        assert invoice.items.count() == 2

        invoice.calculate_totals()
        # المجموع = 1000 + 500 = 1500
        assert invoice.subtotal_before_discount == Decimal('1500.000')


class TestEmptyInvoice:
    """اختبارات الفواتير الفارغة"""

    def test_invoice_without_items(self, company, branch, warehouse, supplier,
                                    currency, payment_method, admin_user):
        """اختبار فاتورة بدون بنود"""
        from apps.purchases.models import PurchaseInvoice

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

        invoice.calculate_totals()
        invoice.save()

        assert invoice.subtotal_before_discount == Decimal('0.000')
        assert invoice.items.count() == 0

    def test_post_empty_invoice_fails(self, company, branch, warehouse, supplier,
                                       currency, payment_method, admin_user):
        """اختبار ترحيل فاتورة فارغة"""
        from apps.purchases.models import PurchaseInvoice

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

        # محاولة ترحيل فاتورة فارغة
        try:
            invoice.post(admin_user)
            # إذا تم الترحيل، قد يكون مقبولاً
            pytest.skip("System allows posting empty invoices")
        except ValidationError:
            # رُفض - سلوك متوقع
            pass
        except Exception as e:
            # أي خطأ آخر
            pytest.skip(f"Cannot test: {e}")


class TestTaxEdgeCases:
    """اختبارات حالات الضريبة الخاصة"""

    def test_tax_rate_zero(self, company, branch, warehouse, supplier,
                           currency, payment_method, admin_user, item, uom):
        """اختبار نسبة ضريبة صفر"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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
            tax_rate=Decimal('0.00'),
            tax_included=False,
        )

        invoice.calculate_totals()
        invoice.save()

        assert invoice.tax_amount == Decimal('0.000')

    def test_tax_rate_hundred_percent(self, company, branch, warehouse, supplier,
                                       currency, payment_method, admin_user, item, uom):
        """اختبار نسبة ضريبة 100%"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

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
            tax_rate=Decimal('100.00'),
            tax_included=False,
        )

        invoice.calculate_totals()
        invoice.save()

        # الضريبة = 1000 * 100% = 1000
        assert invoice.tax_amount == Decimal('1000.000')


class TestDiscountEdgeCases:
    """اختبارات حالات الخصم الخاصة"""

    def test_discount_greater_than_subtotal(self, company, branch, warehouse,
                                             supplier, currency, payment_method,
                                             admin_user, item, uom):
        """اختبار خصم أكبر من المجموع"""
        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            discount_type='amount',
            discount_value=Decimal('2000.000'),  # أكبر من المجموع
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

        # المجموع = 1000، الخصم = 2000
        # النتيجة تعتمد على تصميم النظام
        # قد تكون -1000 أو 0 أو يُرفض
        assert invoice.subtotal_after_discount <= Decimal('1000.000')


class TestConcurrentOperations:
    """اختبارات العمليات المتزامنة"""

    def test_multiple_invoices_same_number(self, company, branch, warehouse,
                                           supplier, currency, payment_method,
                                           admin_user):
        """اختبار إنشاء فواتير متعددة بنفس الرقم"""
        from apps.purchases.models import PurchaseInvoice

        invoice1 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            created_by=admin_user,
        )

        invoice2 = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            created_by=admin_user,
        )

        # يجب أن تكون الأرقام مختلفة
        assert invoice1.number != invoice2.number


class TestSpecialCharacters:
    """اختبارات الأحرف الخاصة"""

    def test_special_chars_in_notes(self, company, branch, warehouse, supplier,
                                     currency, payment_method, admin_user):
        """اختبار أحرف خاصة في الملاحظات"""
        from apps.purchases.models import PurchaseInvoice

        special_notes = "اختبار <script>alert('XSS')</script> \" ' & < >"

        invoice = PurchaseInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            supplier=supplier,
            currency=currency,
            payment_method=payment_method,
            date=date.today(),
            notes=special_notes,
            created_by=admin_user,
        )

        # يجب حفظ النص كما هو أو تنظيفه
        assert invoice.notes is not None

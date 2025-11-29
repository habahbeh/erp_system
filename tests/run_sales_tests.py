#!/usr/bin/env python
"""
سكربت فحص نظام المبيعات يدوياً
يعمل مع قاعدة البيانات الفعلية
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class SalesTestRunner:
    """منفذ اختبارات المبيعات"""

    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': [],
        }
        self.company = None
        self.branch = None
        self.warehouse = None
        self.customer = None
        self.item = None
        self.currency = None
        self.payment_method = None
        self.user = None
        self.uom = None

    def setup(self):
        """إعداد البيانات التجريبية"""
        from apps.core.models import (
            Company, Branch, Warehouse, BusinessPartner,
            Item, ItemCategory, Currency, PaymentMethod, UnitOfMeasure
        )

        print("\n📦 إعداد البيانات التجريبية...")

        # الشركة
        self.company = Company.objects.first()
        if not self.company:
            print("❌ لا توجد شركة في النظام!")
            return False

        # الفرع
        self.branch = Branch.objects.filter(company=self.company).first()
        if not self.branch:
            print("❌ لا يوجد فرع في النظام!")
            return False

        # المستودع
        self.warehouse = Warehouse.objects.filter(company=self.company).first()
        if not self.warehouse:
            print("❌ لا يوجد مستودع في النظام!")
            return False

        # العميل
        self.customer = BusinessPartner.objects.filter(
            company=self.company,
            partner_type__in=['customer', 'both']
        ).first()
        if not self.customer:
            self.customer = BusinessPartner.objects.create(
                company=self.company,
                code='TEST-CUST',
                name='عميل اختباري',
                partner_type='customer',
                is_active=True,
            )
            print("✅ تم إنشاء عميل اختباري")

        # المادة
        self.item = Item.objects.filter(company=self.company, is_active=True).first()
        if not self.item:
            category = ItemCategory.objects.filter(company=self.company).first()
            uom = UnitOfMeasure.objects.filter(company=self.company).first()
            if category and uom:
                self.item = Item.objects.create(
                    company=self.company,
                    code='TEST-ITEM',
                    name='مادة اختبارية',
                    category=category,
                    base_uom=uom,
                    item_type='stock',
                    is_active=True,
                )
                print("✅ تم إنشاء مادة اختبارية")

        # العملة
        self.currency = Currency.objects.first()

        # طريقة الدفع
        self.payment_method = PaymentMethod.objects.filter(company=self.company).first()
        if not self.payment_method:
            self.payment_method = PaymentMethod.objects.create(
                company=self.company,
                code='CASH',
                name='نقدي',
                is_active=True,
            )

        # وحدة القياس
        self.uom = UnitOfMeasure.objects.filter(company=self.company).first()

        # المستخدم
        self.user = User.objects.filter(is_superuser=True).first()
        if not self.user:
            self.user = User.objects.first()

        print(f"✅ الشركة: {self.company.name}")
        print(f"✅ الفرع: {self.branch.name}")
        print(f"✅ المستودع: {self.warehouse.name}")
        print(f"✅ العميل: {self.customer.name}")
        print(f"✅ المادة: {self.item.name if self.item else 'غير متوفر'}")
        print(f"✅ العملة: {self.currency.name if self.currency else 'غير متوفر'}")

        return True

    def run_test(self, name, func):
        """تشغيل اختبار واحد"""
        try:
            func()
            self.results['passed'].append(name)
            print(f"  ✅ {name}")
        except AssertionError as e:
            self.results['failed'].append((name, str(e)))
            print(f"  ❌ {name}: {e}")
        except Exception as e:
            self.results['failed'].append((name, str(e)))
            print(f"  ❌ {name}: {type(e).__name__}: {e}")

    def skip_test(self, name, reason):
        """تخطي اختبار"""
        self.results['skipped'].append((name, reason))
        print(f"  ⏭️ {name}: {reason}")

    # ============================================
    # اختبارات فواتير المبيعات
    # ============================================

    def test_sales_invoices(self):
        """اختبارات فواتير المبيعات"""
        from apps.sales.models import SalesInvoice, InvoiceItem

        print("\n📄 اختبارات فواتير المبيعات:")

        # 1. إنشاء فاتورة
        def test_create_invoice():
            invoice = SalesInvoice(
                company=self.company,
                branch=self.branch,
                warehouse=self.warehouse,
                customer=self.customer,
                currency=self.currency,
                payment_method=self.payment_method,
                salesperson=self.user,
                date=date.today(),
                receipt_number='TEST-REC-001',
                created_by=self.user,
            )
            invoice.save()
            assert invoice.pk is not None, "فشل إنشاء الفاتورة"
            assert invoice.number.startswith('SI/'), f"رقم الفاتورة غير صحيح: {invoice.number}"
            invoice.delete()

        self.run_test("إنشاء فاتورة مبيعات", test_create_invoice)

        # 2. توليد الرقم التلقائي
        def test_auto_number():
            inv1 = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='AUTO-1', created_by=self.user,
            )
            inv2 = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='AUTO-2', created_by=self.user,
            )
            num1 = int(inv1.number.split('/')[-1])
            num2 = int(inv2.number.split('/')[-1])
            assert num2 == num1 + 1, f"الترقيم غير تسلسلي: {num1}, {num2}"
            inv1.delete()
            inv2.delete()

        self.run_test("توليد الرقم التلقائي", test_auto_number)

        # 3. حساب المجاميع
        def test_calculate_totals():
            if not self.item or not self.uom:
                raise Exception("لا توجد مادة أو وحدة قياس")

            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='CALC-001', created_by=self.user,
            )

            InvoiceItem.objects.create(
                invoice=invoice, item=self.item,
                quantity=Decimal('10'), unit=self.uom,
                unit_price=Decimal('100'), tax_rate=Decimal('16'),
            )

            invoice.calculate_totals()
            assert invoice.subtotal_before_discount == Decimal('1000'), \
                f"المجموع خطأ: {invoice.subtotal_before_discount}"
            assert invoice.tax_amount == Decimal('160'), \
                f"الضريبة خطأ: {invoice.tax_amount}"

            invoice.delete()

        if self.item and self.uom:
            self.run_test("حساب مجاميع الفاتورة", test_calculate_totals)
        else:
            self.skip_test("حساب مجاميع الفاتورة", "لا توجد مادة")

        # 4. حالة الدفع
        def test_payment_status():
            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='PAY-001', created_by=self.user,
            )

            if self.item and self.uom:
                InvoiceItem.objects.create(
                    invoice=invoice, item=self.item,
                    quantity=Decimal('10'), unit=self.uom,
                    unit_price=Decimal('100'),
                )
                invoice.calculate_totals()

            assert invoice.payment_status == 'unpaid', "الحالة الأولية خطأ"

            invoice.paid_amount = invoice.total_with_tax / 2
            invoice.update_payment_status()
            assert invoice.payment_status == 'partial', "حالة الدفع الجزئي خطأ"

            invoice.paid_amount = invoice.total_with_tax
            invoice.update_payment_status()
            assert invoice.payment_status == 'paid', "حالة الدفع الكامل خطأ"

            invoice.delete()

        self.run_test("حالة الدفع", test_payment_status)

        # 5. الصلاحيات
        def test_permissions():
            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='PERM-001', created_by=self.user,
            )

            # المسؤول يمكنه التعديل
            assert invoice.can_user_edit(self.user), "المسؤول لا يمكنه التعديل"

            # بعد الترحيل لا يمكن التعديل
            invoice.is_posted = True
            assert not invoice.can_user_edit(self.user), "يمكن التعديل بعد الترحيل!"

            invoice.delete()

        self.run_test("صلاحيات الفاتورة", test_permissions)

    # ============================================
    # اختبارات عروض الأسعار
    # ============================================

    def test_quotations(self):
        """اختبارات عروض الأسعار"""
        from apps.sales.models import Quotation, QuotationItem

        print("\n📋 اختبارات عروض الأسعار:")

        # 1. إنشاء عرض سعر
        def test_create_quotation():
            quote = Quotation.objects.create(
                company=self.company,
                customer=self.customer,
                currency=self.currency,
                salesperson=self.user,
                date=date.today(),
                validity_days=30,
                created_by=self.user,
            )
            assert quote.pk is not None, "فشل إنشاء العرض"
            assert quote.number.startswith('QT/'), f"رقم العرض غير صحيح: {quote.number}"
            quote.delete()

        self.run_test("إنشاء عرض سعر", test_create_quotation)

        # 2. تاريخ الانتهاء
        def test_expiry_date():
            quote = Quotation.objects.create(
                company=self.company,
                customer=self.customer,
                currency=self.currency,
                salesperson=self.user,
                date=date.today(),
                validity_days=15,
                created_by=self.user,
            )
            expected = date.today() + timedelta(days=15)
            assert quote.expiry_date == expected, \
                f"تاريخ الانتهاء خطأ: {quote.expiry_date} != {expected}"
            quote.delete()

        self.run_test("حساب تاريخ الانتهاء", test_expiry_date)

        # 3. إضافة سطور
        def test_add_items():
            if not self.item:
                raise Exception("لا توجد مادة")

            quote = Quotation.objects.create(
                company=self.company,
                customer=self.customer,
                currency=self.currency,
                salesperson=self.user,
                date=date.today(),
                created_by=self.user,
            )

            QuotationItem.objects.create(
                quotation=quote,
                item=self.item,
                quantity=Decimal('10'),
                unit_price=Decimal('100'),
            )

            assert quote.lines.count() == 1, "عدد السطور خطأ"
            quote.delete()

        if self.item:
            self.run_test("إضافة سطور للعرض", test_add_items)
        else:
            self.skip_test("إضافة سطور للعرض", "لا توجد مادة")

    # ============================================
    # اختبارات طلبات البيع
    # ============================================

    def test_sales_orders(self):
        """اختبارات طلبات البيع"""
        from apps.sales.models import SalesOrder, SalesOrderItem

        print("\n📦 اختبارات طلبات البيع:")

        # 1. إنشاء طلب
        def test_create_order():
            order = SalesOrder.objects.create(
                company=self.company,
                warehouse=self.warehouse,
                customer=self.customer,
                salesperson=self.user,
                date=date.today(),
                created_by=self.user,
            )
            assert order.pk is not None, "فشل إنشاء الطلب"
            assert order.number.startswith('SO/'), f"رقم الطلب غير صحيح: {order.number}"
            order.delete()

        self.run_test("إنشاء طلب بيع", test_create_order)

        # 2. حالة الطلب
        def test_order_status():
            order = SalesOrder.objects.create(
                company=self.company,
                warehouse=self.warehouse,
                customer=self.customer,
                salesperson=self.user,
                date=date.today(),
                created_by=self.user,
            )

            assert not order.is_approved, "حالة الاعتماد الأولية خطأ"
            assert not order.is_delivered, "حالة التسليم الأولية خطأ"
            assert not order.is_invoiced, "حالة الفوترة الأولية خطأ"

            order.is_approved = True
            order.save()
            order.refresh_from_db()
            assert order.is_approved, "فشل تحديث حالة الاعتماد"

            order.delete()

        self.run_test("حالة طلب البيع", test_order_status)

    # ============================================
    # اختبارات الأقساط
    # ============================================

    def test_installments(self):
        """اختبارات الأقساط"""
        from apps.sales.models import SalesInvoice, PaymentInstallment

        print("\n💰 اختبارات الأقساط:")

        # 1. إنشاء قسط
        def test_create_installment():
            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='INST-001', created_by=self.user,
            )

            installment = PaymentInstallment.objects.create(
                company=self.company,
                branch=self.branch,
                invoice=invoice,
                installment_number=1,
                due_date=date.today() + timedelta(days=30),
                amount=Decimal('500'),
            )

            assert installment.pk is not None, "فشل إنشاء القسط"
            assert installment.status == 'pending', "حالة القسط الأولية خطأ"

            installment.delete()
            invoice.delete()

        self.run_test("إنشاء قسط", test_create_installment)

        # 2. خصائص القسط
        def test_installment_properties():
            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='INST-002', created_by=self.user,
            )

            installment = PaymentInstallment.objects.create(
                company=self.company, branch=self.branch,
                invoice=invoice, installment_number=1,
                due_date=date.today() + timedelta(days=30),
                amount=Decimal('500'),
            )

            assert installment.remaining_amount == Decimal('500'), "المبلغ المتبقي خطأ"
            assert not installment.is_paid, "خاصية is_paid خطأ"

            installment.delete()
            invoice.delete()

        self.run_test("خصائص القسط", test_installment_properties)

    # ============================================
    # اختبارات العمولات
    # ============================================

    def test_commissions(self):
        """اختبارات العمولات"""
        from apps.sales.models import SalesInvoice, InvoiceItem

        print("\n💵 اختبارات العمولات:")

        # 1. حساب العمولة
        def test_calculate_commission():
            invoice = SalesInvoice.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                customer=self.customer, currency=self.currency,
                payment_method=self.payment_method, salesperson=self.user,
                date=date.today(), receipt_number='COMM-001',
                salesperson_commission_rate=Decimal('5'),
                created_by=self.user,
            )

            if self.item and self.uom:
                InvoiceItem.objects.create(
                    invoice=invoice, item=self.item,
                    quantity=Decimal('10'), unit=self.uom,
                    unit_price=Decimal('100'),
                )
                invoice.calculate_totals()

            invoice.calculate_commission()
            expected = invoice.total_with_tax * Decimal('0.05')

            assert invoice.salesperson_commission_amount == expected, \
                f"العمولة خطأ: {invoice.salesperson_commission_amount} != {expected}"

            invoice.delete()

        self.run_test("حساب العمولة", test_calculate_commission)

    # ============================================
    # التنفيذ
    # ============================================

    def run_all(self):
        """تشغيل جميع الاختبارات"""
        print("=" * 60)
        print("🧪 فحص نظام المبيعات الشامل")
        print("=" * 60)

        if not self.setup():
            print("\n❌ فشل الإعداد - لا يمكن المتابعة")
            return

        with transaction.atomic():
            # إنشاء savepoint للتراجع
            sid = transaction.savepoint()

            try:
                self.test_sales_invoices()
                self.test_quotations()
                self.test_sales_orders()
                self.test_installments()
                self.test_commissions()
            finally:
                # التراجع عن جميع التغييرات
                transaction.savepoint_rollback(sid)

        # طباعة النتائج
        print("\n" + "=" * 60)
        print("📊 ملخص النتائج")
        print("=" * 60)

        print(f"\n✅ نجح: {len(self.results['passed'])}")
        for name in self.results['passed']:
            print(f"   - {name}")

        if self.results['failed']:
            print(f"\n❌ فشل: {len(self.results['failed'])}")
            for name, error in self.results['failed']:
                print(f"   - {name}: {error}")

        if self.results['skipped']:
            print(f"\n⏭️ تخطي: {len(self.results['skipped'])}")
            for name, reason in self.results['skipped']:
                print(f"   - {name}: {reason}")

        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])
        success_rate = len(self.results['passed']) / total * 100 if total > 0 else 0

        print(f"\n📈 نسبة النجاح: {success_rate:.1f}%")
        print("=" * 60)

        return self.results


if __name__ == '__main__':
    runner = SalesTestRunner()
    runner.run_all()

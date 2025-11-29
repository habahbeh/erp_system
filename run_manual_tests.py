#!/usr/bin/env python
"""
اختبار يدوي لنظام المشتريات
يُشغل مباشرة على قاعدة البيانات الحالية
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
import traceback

User = get_user_model()

# ألوان للطباعة
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, error=None):
    """طباعة نتيجة الاختبار"""
    if passed:
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        print(f"  {RED}✗{RESET} {name}")
        if error:
            print(f"    {RED}Error: {error}{RESET}")

class TestResults:
    """تتبع نتائج الاختبارات"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, name, passed, error=None):
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append((name, error))
        print_test(name, passed, error)

results = TestResults()

def get_or_create_test_data():
    """إنشاء بيانات الاختبار"""
    from apps.core.models import (
        Company, Branch, Warehouse, Currency,
        PaymentMethod, UnitOfMeasure, ItemCategory,
        Item, BusinessPartner
    )

    # استخدام الشركة الموجودة
    company = Company.objects.first()
    if not company:
        raise Exception("لا توجد شركة في النظام")

    # استخدام الفرع الموجود أو إنشاء جديد
    branch = Branch.objects.filter(company=company).first()
    if not branch:
        branch = Branch.objects.create(
            company=company,
            code='TEST_BRANCH',
            name='فرع الاختبار',
            is_active=True,
        )

    # استخدام المستودع الموجود أو إنشاء جديد
    warehouse = Warehouse.objects.filter(company=company).first()
    if not warehouse:
        warehouse = Warehouse.objects.create(
            company=company,
            code='TEST_WH',
            name='مستودع الاختبار',
            is_active=True,
        )

    # العملة
    currency = Currency.objects.filter(code='JOD').first()
    if not currency:
        currency, _ = Currency.objects.get_or_create(
            code='JOD',
            defaults={
                'name': 'دينار أردني',
                'name_en': 'Jordanian Dinar',
                'symbol': 'د.أ',
                'exchange_rate': Decimal('1.000000'),
                'is_active': True,
            }
        )

    # طريقة الدفع
    payment_method = PaymentMethod.objects.filter(company=company).first()
    if not payment_method:
        payment_method = PaymentMethod.objects.create(
            company=company,
            code='CASH_TEST',
            name='نقدي اختبار',
            is_active=True,
        )

    # وحدة القياس
    uom = UnitOfMeasure.objects.filter(company=company).first()
    if not uom:
        uom = UnitOfMeasure.objects.create(
            company=company,
            code='PC_TEST',
            name='قطعة اختبار',
            is_active=True,
        )

    # الفئة
    category = ItemCategory.objects.filter(company=company).first()
    if not category:
        category = ItemCategory.objects.create(
            company=company,
            code='CAT_TEST',
            name='فئة الاختبار',
            level=1,
        )

    # المادة
    item = Item.objects.filter(company=company, is_active=True).first()
    if not item:
        item = Item.objects.create(
            company=company,
            code='ITEM_TEST',
            name='مادة اختبار',
            category=category,
            base_uom=uom,
            item_type='stock',
            is_active=True,
        )

    # المورد
    supplier = BusinessPartner.objects.filter(
        company=company,
        partner_type='supplier',
        is_active=True
    ).first()
    if not supplier:
        supplier = BusinessPartner.objects.create(
            company=company,
            code='SUP_TEST',
            name='مورد الاختبار',
            partner_type='supplier',
            is_active=True,
        )

    # المستخدم
    user = User.objects.filter(is_active=True).first()
    if not user:
        user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='testpass123',
            is_staff=True,
        )

    return {
        'company': company,
        'branch': branch,
        'warehouse': warehouse,
        'currency': currency,
        'payment_method': payment_method,
        'uom': uom,
        'category': category,
        'item': item,
        'supplier': supplier,
        'user': user,
    }

def test_purchase_invoice_creation(data):
    """اختبار إنشاء فاتورة مشتريات"""
    print(f"\n{BLUE}═══ اختبار فاتورة المشتريات ═══{RESET}")

    from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

    # 1. إنشاء فاتورة بسيطة
    invoice = None
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        passed = invoice.id is not None and invoice.number is not None
        results.record("إنشاء فاتورة مشتريات بسيطة", passed)
        data['invoice'] = invoice
    except Exception as e:
        results.record("إنشاء فاتورة مشتريات بسيطة", False, str(e))
        return

    # 2. إضافة بنود للفاتورة
    try:
        item = PurchaseInvoiceItem.objects.create(
            invoice=data['invoice'],
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        passed = item.id is not None and item.subtotal == Decimal('1000.000')
        results.record("إضافة بند للفاتورة", passed)
    except Exception as e:
        results.record("إضافة بند للفاتورة", False, str(e))

    # 3. حساب المجاميع
    try:
        data['invoice'].calculate_totals()
        data['invoice'].save()

        passed = data['invoice'].subtotal_before_discount == Decimal('1000.000')
        results.record("حساب المجاميع", passed)
    except Exception as e:
        results.record("حساب المجاميع", False, str(e))

    # 4. رقم الفاتورة يبدأ بـ PI/
    try:
        passed = data['invoice'].number.startswith('PI/')
        results.record("رقم الفاتورة يبدأ بـ PI/", passed,
                      f"الرقم: {data['invoice'].number}" if not passed else None)
    except Exception as e:
        results.record("رقم الفاتورة يبدأ بـ PI/", False, str(e))

def test_purchase_invoice_with_discount(data):
    """اختبار فاتورة مع خصم"""
    print(f"\n{BLUE}═══ اختبار الخصم ═══{RESET}")

    from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

    # 1. خصم نسبة مئوية
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            created_by=data['user'],
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        invoice.calculate_totals()
        invoice.save()

        # 1000 - 10% = 900
        passed = invoice.discount_amount == Decimal('100.000')
        results.record("خصم نسبة مئوية 10%", passed,
                      f"الخصم: {invoice.discount_amount}" if not passed else None)

        # حفظ للتنظيف
        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("خصم نسبة مئوية 10%", False, str(e))

    # 2. خصم مبلغ ثابت
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            discount_type='amount',
            discount_value=Decimal('50.000'),
            created_by=data['user'],
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('5'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        invoice.calculate_totals()
        invoice.save()

        # 500 - 50 = 450
        passed = invoice.subtotal_after_discount == Decimal('450.000')
        results.record("خصم مبلغ ثابت 50", passed,
                      f"المجموع بعد الخصم: {invoice.subtotal_after_discount}" if not passed else None)

        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("خصم مبلغ ثابت 50", False, str(e))

def test_purchase_invoice_with_tax(data):
    """اختبار فاتورة مع ضريبة"""
    print(f"\n{BLUE}═══ اختبار الضريبة ═══{RESET}")

    from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

    # 1. ضريبة غير شاملة
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
            tax_rate=Decimal('16.00'),
            tax_included=False,
        )

        invoice.calculate_totals()
        invoice.save()

        # الضريبة = 1000 * 16% = 160
        passed = invoice.tax_amount == Decimal('160.000')
        results.record("ضريبة 16% غير شاملة", passed,
                      f"الضريبة: {invoice.tax_amount}" if not passed else None)

        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("ضريبة 16% غير شاملة", False, str(e))

    # 2. ضريبة شاملة
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('1'),
            unit=data['uom'],
            unit_price=Decimal('116.000'),  # شامل الضريبة
            tax_rate=Decimal('16.00'),
            tax_included=True,
        )

        invoice.calculate_totals()
        invoice.save()

        # السعر الأساسي = 116 / 1.16 = 100
        # الضريبة = 16
        passed = abs(invoice.tax_amount - Decimal('16.000')) < Decimal('0.01')
        results.record("ضريبة 16% شاملة", passed,
                      f"الضريبة: {invoice.tax_amount}" if not passed else None)

        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("ضريبة 16% شاملة", False, str(e))

def test_purchase_return(data):
    """اختبار مرتجعات المشتريات"""
    print(f"\n{BLUE}═══ اختبار المرتجعات ═══{RESET}")

    from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

    # 1. إنشاء مرتجع
    try:
        return_invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='return',
            created_by=data['user'],
        )

        passed = return_invoice.invoice_type == 'return'
        results.record("إنشاء مرتجع مشتريات", passed)
        data['return_invoice'] = return_invoice
        data.setdefault('test_invoices', []).append(return_invoice)
    except Exception as e:
        results.record("إنشاء مرتجع مشتريات", False, str(e))
        return

    # 2. رقم المرتجع يبدأ بـ PR/
    try:
        passed = data['return_invoice'].number.startswith('PR/')
        results.record("رقم المرتجع يبدأ بـ PR/", passed,
                      f"الرقم: {data['return_invoice'].number}" if not passed else None)
    except Exception as e:
        results.record("رقم المرتجع يبدأ بـ PR/", False, str(e))

def test_purchase_order_creation(data):
    """اختبار أوامر الشراء"""
    print(f"\n{BLUE}═══ اختبار أوامر الشراء ═══{RESET}")

    from apps.purchases.models import PurchaseOrder, PurchaseOrderItem

    # 1. إنشاء أمر شراء
    try:
        order = PurchaseOrder.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            date=date.today(),
            status='draft',
            created_by=data['user'],
        )

        passed = order.id is not None and order.status == 'draft'
        results.record("إنشاء أمر شراء", passed)
        data['order'] = order
        data.setdefault('test_orders', []).append(order)
    except Exception as e:
        results.record("إنشاء أمر شراء", False, str(e))
        return

    # 2. رقم أمر الشراء يبدأ بـ PO/
    try:
        passed = data['order'].number.startswith('PO/')
        results.record("رقم أمر الشراء يبدأ بـ PO/", passed,
                      f"الرقم: {data['order'].number}" if not passed else None)
    except Exception as e:
        results.record("رقم أمر الشراء يبدأ بـ PO/", False, str(e))

    # 3. إضافة بنود
    try:
        item = PurchaseOrderItem.objects.create(
            order=data['order'],
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        passed = item.subtotal == Decimal('1000.000')
        results.record("إضافة بند لأمر الشراء", passed)
    except Exception as e:
        results.record("إضافة بند لأمر الشراء", False, str(e))

def test_purchase_order_workflow(data):
    """اختبار سير عمل أوامر الشراء"""
    print(f"\n{BLUE}═══ اختبار سير العمل ═══{RESET}")

    from apps.purchases.models import PurchaseOrder, PurchaseOrderItem

    # إنشاء أمر جديد للاختبار
    try:
        order = PurchaseOrder.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            date=date.today(),
            status='draft',
            created_by=data['user'],
        )

        PurchaseOrderItem.objects.create(
            order=order,
            item=data['item'],
            quantity=Decimal('5'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        data.setdefault('test_orders', []).append(order)

        # 1. تقديم للموافقة
        if hasattr(order, 'submit_for_approval'):
            try:
                order.submit_for_approval(data['user'])
                passed = order.status == 'pending_approval'
                results.record("تقديم للموافقة", passed,
                              f"الحالة: {order.status}" if not passed else None)
            except Exception as e:
                results.record("تقديم للموافقة", False, str(e))
        else:
            results.record("تقديم للموافقة", False, "الدالة غير موجودة")

        # 2. الموافقة
        if hasattr(order, 'approve'):
            try:
                order.approve(data['user'])
                passed = order.status == 'approved'
                results.record("الموافقة على الأمر", passed,
                              f"الحالة: {order.status}" if not passed else None)
            except Exception as e:
                results.record("الموافقة على الأمر", False, str(e))
        else:
            results.record("الموافقة على الأمر", False, "الدالة غير موجودة")

    except Exception as e:
        results.record("إنشاء أمر للاختبار", False, str(e))

def test_purchase_request(data):
    """اختبار طلبات الشراء"""
    print(f"\n{BLUE}═══ اختبار طلبات الشراء ═══{RESET}")

    from apps.purchases.models import PurchaseRequest, PurchaseRequestItem

    # 1. إنشاء طلب شراء
    try:
        request = PurchaseRequest.objects.create(
            company=data['company'],
            branch=data['branch'],
            date=date.today(),
            status='draft',
            requested_by=data['user'],
            created_by=data['user'],
        )

        passed = request.id is not None and request.status == 'draft'
        results.record("إنشاء طلب شراء", passed)
        data.setdefault('test_requests', []).append(request)

    except Exception as e:
        results.record("إنشاء طلب شراء", False, str(e))

def test_edge_cases(data):
    """اختبار الحالات الخاصة"""
    print(f"\n{BLUE}═══ اختبار الحالات الخاصة ═══{RESET}")

    from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem
    from django.core.exceptions import ValidationError

    # 1. فاتورة بدون بنود
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        invoice.calculate_totals()
        passed = invoice.subtotal_before_discount == Decimal('0.000')
        results.record("فاتورة بدون بنود = 0", passed)
        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("فاتورة بدون بنود = 0", False, str(e))

    # 2. كمية صفر
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('0'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        passed = item.subtotal == Decimal('0.000')
        results.record("كمية صفر = مجموع صفر", passed)
        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("كمية صفر = مجموع صفر", False, str(e))

    # 3. سعر صفر
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('0.000'),
        )

        passed = item.subtotal == Decimal('0.000')
        results.record("سعر صفر = مجموع صفر", passed)
        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("سعر صفر = مجموع صفر", False, str(e))

    # 4. عدة بنود لنفس الفاتورة
    try:
        invoice = PurchaseInvoice.objects.create(
            company=data['company'],
            branch=data['branch'],
            warehouse=data['warehouse'],
            supplier=data['supplier'],
            currency=data['currency'],
            payment_method=data['payment_method'],
            date=date.today(),
            invoice_type='purchase',
            created_by=data['user'],
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('10'),
            unit=data['uom'],
            unit_price=Decimal('100.000'),
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=data['item'],
            quantity=Decimal('5'),
            unit=data['uom'],
            unit_price=Decimal('200.000'),
        )

        invoice.calculate_totals()
        invoice.save()

        # 1000 + 1000 = 2000
        passed = invoice.subtotal_before_discount == Decimal('2000.000')
        results.record("عدة بنود لنفس الفاتورة", passed,
                      f"المجموع: {invoice.subtotal_before_discount}" if not passed else None)
        data.setdefault('test_invoices', []).append(invoice)
    except Exception as e:
        results.record("عدة بنود لنفس الفاتورة", False, str(e))

def cleanup_test_data(data):
    """تنظيف بيانات الاختبار"""
    print(f"\n{YELLOW}جاري تنظيف بيانات الاختبار...{RESET}")

    try:
        # حذف الفواتير المنشأة أثناء الاختبار
        for invoice in data.get('test_invoices', []):
            try:
                invoice.items.all().delete()
                invoice.delete()
            except:
                pass

        # حذف أوامر الشراء
        for order in data.get('test_orders', []):
            try:
                order.items.all().delete()
                order.delete()
            except:
                pass

        # حذف طلبات الشراء
        for request in data.get('test_requests', []):
            try:
                request.items.all().delete()
                request.delete()
            except:
                pass

        # حذف الفاتورة الرئيسية
        if 'invoice' in data:
            try:
                data['invoice'].items.all().delete()
                data['invoice'].delete()
            except:
                pass

        print(f"  {GREEN}✓{RESET} تم تنظيف البيانات بنجاح")
    except Exception as e:
        print(f"  {RED}✗{RESET} خطأ في التنظيف: {e}")

def main():
    """تشغيل جميع الاختبارات"""
    print(f"\n{BLUE}{'═' * 50}{RESET}")
    print(f"{BLUE}   اختبار نظام المشتريات الشامل   {RESET}")
    print(f"{BLUE}{'═' * 50}{RESET}")

    data = {}
    try:
        # إنشاء بيانات الاختبار
        print(f"\n{YELLOW}جاري إنشاء بيانات الاختبار...{RESET}")
        data = get_or_create_test_data()
        print(f"  {GREEN}✓{RESET} تم إنشاء بيانات الاختبار")
        print(f"    الشركة: {data['company'].name}")
        print(f"    الفرع: {data['branch'].name}")
        print(f"    المورد: {data['supplier'].name}")

        # تشغيل الاختبارات
        test_purchase_invoice_creation(data)
        test_purchase_invoice_with_discount(data)
        test_purchase_invoice_with_tax(data)
        test_purchase_return(data)
        test_purchase_order_creation(data)
        test_purchase_order_workflow(data)
        test_purchase_request(data)
        test_edge_cases(data)

    except Exception as e:
        print(f"\n{RED}خطأ عام: {e}{RESET}")
        traceback.print_exc()

    finally:
        # تنظيف البيانات
        cleanup_test_data(data)

    # طباعة النتائج النهائية
    print(f"\n{BLUE}{'═' * 50}{RESET}")
    print(f"{BLUE}   نتائج الاختبارات   {RESET}")
    print(f"{BLUE}{'═' * 50}{RESET}")
    print(f"\n  {GREEN}نجح: {results.passed}{RESET}")
    print(f"  {RED}فشل: {results.failed}{RESET}")
    print(f"  المجموع: {results.passed + results.failed}")

    if results.errors:
        print(f"\n{RED}الأخطاء:{RESET}")
        for name, error in results.errors:
            print(f"  - {name}: {error}")

    return results.failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

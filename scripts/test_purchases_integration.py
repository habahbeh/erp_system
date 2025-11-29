#!/usr/bin/env python
"""
اختبار التكامل مع نظام المشتريات
Test Purchases Integration - Auto-create StockIn from PurchaseInvoice
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem
from apps.inventory.models import StockIn, Warehouse
from apps.core.models import Company, User, Item, BusinessPartner, PaymentMethod, Currency
from apps.accounting.models import JournalEntry
from django.db import transaction
from datetime import date
from decimal import Decimal


def test_purchases_integration():
    """اختبار التكامل التلقائي بين المشتريات والمخزون"""

    print("=" * 80)
    print("اختبار التكامل مع نظام المشتريات")
    print("=" * 80)
    print()

    # 1. الحصول على البيانات الأساسية
    try:
        company = Company.objects.first()
        user = User.objects.filter(is_superuser=True).first()
        warehouse = Warehouse.objects.filter(company=company).first()
        supplier = BusinessPartner.objects.filter(
            company=company,
            partner_type__in=['supplier', 'both']
        ).first()
        payment_method = PaymentMethod.objects.first()
        currency = Currency.objects.first()

        if not all([company, user, warehouse, supplier, payment_method, currency]):
            print("❌ البيانات الأساسية غير مكتملة!")
            return

        print(f"✅ الشركة: {company.name}")
        print(f"✅ المستودع: {warehouse.name}")
        print(f"✅ المورد: {supplier.name}")
        print(f"✅ طريقة الدفع: {payment_method.name}")
        print(f"✅ العملة: {currency.name}")
        print(f"✅ المستخدم: {user.username}")
        print()

    except Exception as e:
        print(f"❌ خطأ في جلب البيانات: {e}")
        return

    # 2. الحصول على مواد للاختبار (بدون متغيرات لتبسيط الاختبار)
    items = Item.objects.filter(
        company=company,
        inventory_account__isnull=False,
        has_variants=False  # فقط المواد التي ليس لها متغيرات
    )[:3]

    if items.count() < 2:
        print("❌ لا توجد مواد كافية مربوطة بحسابات!")
        return

    print(f"📦 عدد المواد المستخدمة: {items.count()}")
    print()

    # 3. إنشاء فاتورة شراء اختبارية
    print("📝 إنشاء فاتورة شراء اختبارية...")

    try:
        with transaction.atomic():
            # إنشاء الفاتورة (غير مرحلة)
            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=warehouse.branch,
                warehouse=warehouse,
                supplier=supplier,
                payment_method=payment_method,
                currency=currency,
                date=date.today(),
                reference='TEST-AUTO-STOCKIN',
                notes='اختبار التكامل التلقائي',
                is_posted=False,  # مهم: غير مرحلة في البداية
                created_by=user
            )

            print(f"✅ تم إنشاء الفاتورة: {invoice.number}")

            # إضافة سطور الفاتورة
            total = Decimal('0')
            for i, item in enumerate(items, 1):
                quantity = Decimal('10')
                unit_price = Decimal('50.00')

                line = PurchaseInvoiceItem.objects.create(
                    invoice=invoice,
                    item=item,
                    quantity=quantity,
                    unit_price=unit_price
                )

                total += quantity * unit_price
                print(f"   • {item.name}: {quantity} × {unit_price} = {quantity * unit_price}")

            invoice.total_amount = total
            invoice.save()

            print(f"✅ تم إضافة {items.count()} سطور")
            print(f"💰 الإجمالي: {total}")
            print()

    except Exception as e:
        print(f"❌ خطأ في إنشاء الفاتورة: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. التحقق من عدم وجود StockIn قبل الترحيل
    print("🔍 التحقق من عدم وجود StockIn قبل الترحيل...")
    stock_in_before = StockIn.objects.filter(
        company=company,
        purchase_invoice=invoice
    ).first()

    if stock_in_before:
        print(f"⚠️  يوجد StockIn قبل الترحيل! {stock_in_before.number}")
    else:
        print("✅ لا يوجد StockIn قبل الترحيل (صحيح)")
    print()

    # 5. ترحيل الفاتورة (هنا يجب أن تعمل الإشارة)
    print("📤 ترحيل الفاتورة...")
    print("   (هنا يجب أن تعمل الإشارة وتنشئ StockIn تلقائياً)")
    print()

    try:
        invoice.is_posted = True
        invoice.posted_by = user
        invoice.posted_date = date.today()
        invoice.save()

        print(f"✅ تم ترحيل الفاتورة بنجاح")
        print()

    except Exception as e:
        print(f"❌ خطأ في ترحيل الفاتورة: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. التحقق من إنشاء StockIn تلقائياً
    print("🔍 التحقق من إنشاء StockIn تلقائياً...")

    stock_in = StockIn.objects.filter(
        company=company,
        purchase_invoice=invoice
    ).first()

    if not stock_in:
        print("❌ فشل! لم يتم إنشاء StockIn تلقائياً")
        print()
        print("🔧 الأسباب المحتملة:")
        print("   1. الإشارة غير مسجلة في apps/purchases/apps.py")
        print("   2. خطأ في كود الإشارة")
        print("   3. الفاتورة لا تحتوي على مواد")
        print()
        return

    print(f"✅✅✅ ممتاز! تم إنشاء StockIn تلقائياً: {stock_in.number}")
    print()

    # 7. التحقق من تفاصيل StockIn
    print("📋 تفاصيل StockIn المُنشأ:")
    print(f"   • رقم السند: {stock_in.number}")
    print(f"   • التاريخ: {stock_in.date}")
    print(f"   • المستودع: {stock_in.warehouse.name}")
    print(f"   • المورد: {stock_in.supplier.name if stock_in.supplier else 'غير محدد'}")
    print(f"   • نوع المصدر: {stock_in.source_type}")
    print(f"   • الفاتورة المرتبطة: {stock_in.purchase_invoice.number}")
    print(f"   • مرحل؟: {'نعم' if stock_in.is_posted else 'لا'}")
    print()

    # 8. التحقق من سطور StockIn
    print("📦 سطور StockIn:")
    lines_count = stock_in.lines.count()

    if lines_count == 0:
        print("❌ لا توجد سطور في StockIn!")
    else:
        print(f"✅ عدد السطور: {lines_count}")

        for line in stock_in.lines.all():
            print(f"   • {line.item.name}: {line.quantity} وحدة × {line.unit_cost} = {line.total_cost}")

    print()

    # 9. التحقق من الترحيل التلقائي
    if stock_in.is_posted:
        print(f"✅ تم ترحيل StockIn تلقائياً")
        print(f"   • تاريخ الترحيل: {stock_in.posted_date}")
        print(f"   • مرحل بواسطة: {stock_in.posted_by.username if stock_in.posted_by else 'غير محدد'}")
    else:
        print("⚠️  StockIn غير مرحل (يجب أن يكون مرحل تلقائياً)")

    print()

    # 10. التحقق من القيود المحاسبية
    print("💰 التحقق من القيود المحاسبية:")

    if stock_in.journal_entry:
        je = stock_in.journal_entry
        print(f"✅ تم إنشاء قيد محاسبي: {je.number}")

        debits = sum(line.debit_amount for line in je.lines.all())
        credits = sum(line.credit_amount for line in je.lines.all())
        balanced = debits == credits

        print(f"   • مدين: {debits:.2f}")
        print(f"   • دائن: {credits:.2f}")
        print(f"   • {'✅ متوازن' if balanced else '❌ غير متوازن'}")
    else:
        print("⚠️  لا يوجد قيد محاسبي (قد يكون معطل في الإعدادات)")

    print()

    # النتيجة النهائية
    print("=" * 80)
    print("النتيجة النهائية")
    print("=" * 80)

    all_checks = [
        stock_in is not None,
        lines_count == items.count(),
        stock_in.is_posted,
    ]

    if all(all_checks):
        print("✅✅✅ ممتاز! التكامل يعمل بشكل كامل!")
        print()
        print("📝 ما تم اختباره:")
        print("   ✅ إنشاء StockIn تلقائياً عند ترحيل فاتورة الشراء")
        print("   ✅ نسخ جميع السطور من الفاتورة إلى StockIn")
        print("   ✅ ترحيل StockIn تلقائياً")
        print("   ✅ إنشاء القيود المحاسبية (إن كان مفعل)")
        print()
        print("🎯 الأولوية: 🔴🔴🔴 Very High - تم الحل!")
    else:
        print("⚠️  بعض الفحوصات فشلت:")
        if not stock_in:
            print("   ❌ لم يتم إنشاء StockIn")
        if lines_count != items.count():
            print(f"   ❌ عدد السطور غير صحيح ({lines_count} بدلاً من {items.count()})")
        if not stock_in.is_posted:
            print("   ❌ StockIn غير مرحل")

    print()


if __name__ == '__main__':
    test_purchases_integration()

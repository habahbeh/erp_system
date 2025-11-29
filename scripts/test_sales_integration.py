#!/usr/bin/env python
"""
اختبار التكامل مع نظام المبيعات
Test Sales Integration - Auto-reserve stock from SalesOrder
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sales.models import SalesOrder, SalesOrderItem
from apps.inventory.models import StockReservation, ItemStock, Warehouse
from apps.core.models import Company, User, Item, BusinessPartner
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal


def test_sales_integration():
    """اختبار التكامل التلقائي بين المبيعات ونظام حجز المخزون"""

    print("=" * 80)
    print("اختبار التكامل مع نظام المبيعات - حجز المخزون")
    print("=" * 80)
    print()

    # 1. الحصول على البيانات الأساسية
    try:
        company = Company.objects.first()
        user = User.objects.filter(is_superuser=True).first()
        warehouse = Warehouse.objects.filter(company=company).first()
        customer = BusinessPartner.objects.filter(
            company=company,
            partner_type__in=['customer', 'both']
        ).first()

        if not all([company, user, warehouse, customer]):
            print("❌ البيانات الأساسية غير مكتملة!")
            print(f"   company: {company}")
            print(f"   user: {user}")
            print(f"   warehouse: {warehouse}")
            print(f"   customer: {customer}")
            return

        print(f"✅ الشركة: {company.name}")
        print(f"✅ المستودع: {warehouse.name}")
        print(f"✅ العميل: {customer.name}")
        print(f"✅ المستخدم: {user.username}")
        print()

    except Exception as e:
        print(f"❌ خطأ في جلب البيانات: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. الحصول على مواد لديها رصيد في المخزون
    items_with_stock = ItemStock.objects.filter(
        company=company,
        warehouse=warehouse,
        quantity__gt=10,
        item__has_variants=False  # فقط المواد بدون متغيرات لتبسيط الاختبار
    ).select_related('item')[:3]

    if not items_with_stock.exists():
        print("❌ لا توجد مواد لديها رصيد كافٍ في المخزون!")
        return

    print(f"📦 عدد المواد المستخدمة: {items_with_stock.count()}")
    for item_stock in items_with_stock:
        print(f"   • {item_stock.item.name}: الرصيد الحالي = {item_stock.quantity}")
    print()

    # 3. إنشاء أمر بيع اختباري (غير موافق عليه)
    print("📝 إنشاء أمر بيع اختباري...")

    try:
        with transaction.atomic():
            # إنشاء الأمر (غير موافق عليه)
            order = SalesOrder.objects.create(
                company=company,
                date=date.today(),
                customer=customer,
                warehouse=warehouse,
                salesperson=user,  # مطلوب
                delivery_date=date.today() + timedelta(days=7),
                is_approved=False,  # مهم: غير موافق عليه في البداية
                created_by=user,
                notes='اختبار التكامل التلقائي'
            )

            print(f"✅ تم إنشاء الأمر: {order.number}")

            # إضافة سطور الأمر
            for i, item_stock in enumerate(items_with_stock, 1):
                quantity = Decimal('5')  # نحجز 5 وحدات من كل صنف
                unit_price = Decimal('100.00')

                line = SalesOrderItem.objects.create(
                    order=order,
                    item=item_stock.item,
                    quantity=quantity,
                    unit_price=unit_price
                )

                print(f"   • {item_stock.item.name}: {quantity} وحدة × {unit_price} = {quantity * unit_price}")

            print(f"✅ تم إضافة {items_with_stock.count()} سطور")
            print()

    except Exception as e:
        print(f"❌ خطأ في إنشاء الأمر: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. التحقق من عدم وجود حجوزات قبل الموافقة
    print("🔍 التحقق من عدم وجود حجوزات قبل الموافقة...")

    content_type = ContentType.objects.get_for_model(SalesOrder)
    reservations_before = StockReservation.objects.filter(
        company=company,
        reference_type=content_type,
        reference_id=order.id
    )

    if reservations_before.exists():
        print(f"⚠️  يوجد {reservations_before.count()} حجوزات قبل الموافقة!")
    else:
        print("✅ لا توجد حجوزات قبل الموافقة (صحيح)")
    print()

    # 5. الموافقة على الأمر (هنا يجب أن تعمل الإشارة)
    print("✅ الموافقة على الأمر...")
    print("   (هنا يجب أن تعمل الإشارة وتنشئ حجوزات تلقائياً)")
    print()

    try:
        order.is_approved = True
        order.save()

        print(f"✅ تم الموافقة على الأمر بنجاح")
        print()

    except Exception as e:
        print(f"❌ خطأ في الموافقة على الأمر: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. التحقق من إنشاء الحجوزات تلقائياً
    print("🔍 التحقق من إنشاء الحجوزات تلقائياً...")

    reservations = StockReservation.objects.filter(
        company=company,
        reference_type=content_type,
        reference_id=order.id
    )

    if not reservations.exists():
        print("❌ فشل! لم يتم إنشاء حجوزات تلقائياً")
        print()
        print("🔧 الأسباب المحتملة:")
        print("   1. الإشارة غير مسجلة في apps/sales/apps.py")
        print("   2. خطأ في كود الإشارة")
        print("   3. الأمر لا يحتوي على مواد")
        print()
        return

    print(f"✅✅✅ ممتاز! تم إنشاء {reservations.count()} حجوزات تلقائياً")
    print()

    # 7. التحقق من تفاصيل الحجوزات
    print("📋 تفاصيل الحجوزات:")
    for res in reservations:
        print(f"   • المادة: {res.item.name}")
        print(f"     - الكمية المحجوزة: {res.quantity}")
        print(f"     - المستودع: {res.warehouse.name}")
        print(f"     - الحالة: {res.get_status_display()}")
        print(f"     - محجوز بواسطة: {res.reserved_by.username if res.reserved_by else 'غير محدد'}")
        if res.expires_at:
            print(f"     - ينتهي في: {res.expires_at}")
        print()

    # 8. التحقق من تأثير الحجز على الرصيد المتاح
    print("📊 تأثير الحجوزات على الرصيد المتاح:")
    for res in reservations:
        item_stock = ItemStock.objects.get(
            company=company,
            warehouse=warehouse,
            item=res.item
        )

        total_reserved = StockReservation.objects.filter(
            company=company,
            item=res.item,
            warehouse=warehouse,
            status__in=['active', 'confirmed']
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

        available = item_stock.quantity - total_reserved

        print(f"   • {res.item.name}:")
        print(f"     - الرصيد الكلي: {item_stock.quantity}")
        print(f"     - المحجوز: {total_reserved}")
        print(f"     - المتاح: {available}")
        print()

    # 9. اختبار تحرير الحجوزات عند اكتمال الأمر
    print("🔄 اختبار تحرير الحجوزات عند اكتمال الأمر...")

    try:
        # محاكاة اكتمال الأمر (تم التسليم)
        order.is_delivered = True
        order.save()

        print(f"✅ تم تحديث الأمر كـ 'مُسلّم'")

        # التحقق من تحرير الحجوزات
        active_reservations = StockReservation.objects.filter(
            company=company,
            reference_type=content_type,
            reference_id=order.id,
            status__in=['active', 'confirmed']
        )

        if active_reservations.exists():
            print(f"⚠️  مازال هناك {active_reservations.count()} حجوزات نشطة (يجب أن تُحرر)")
        else:
            print(f"✅ تم تحرير جميع الحجوزات بنجاح")

        # عرض حالات الحجوزات
        all_reservations = StockReservation.objects.filter(
            company=company,
            reference_type=content_type,
            reference_id=order.id
        )

        print(f"\n📋 حالات الحجوزات بعد الاكتمال:")
        for res in all_reservations:
            print(f"   • {res.item.name}: {res.get_status_display()}")

        print()

    except Exception as e:
        print(f"❌ خطأ في تحرير الحجوزات: {e}")
        import traceback
        traceback.print_exc()

    # النتيجة النهائية
    print("=" * 80)
    print("النتيجة النهائية")
    print("=" * 80)

    all_checks = [
        reservations.count() == items_with_stock.count(),
        all(r.status in ['released'] for r in all_reservations),
    ]

    if all(all_checks):
        print("✅✅✅ ممتاز! التكامل يعمل بشكل كامل!")
        print()
        print("📝 ما تم اختباره:")
        print("   ✅ إنشاء حجوزات تلقائياً عند الموافقة على أمر البيع")
        print("   ✅ حجز الكميات الصحيحة لكل صنف")
        print("   ✅ تحرير الحجوزات تلقائياً عند اكتمال الأمر")
        print()
        print("🎯 الأولوية: 🔴🔴 High - تم الحل!")
    else:
        print("⚠️  بعض الفحوصات فشلت:")
        if reservations.count() != items_with_stock.count():
            print(f"   ❌ عدد الحجوزات غير صحيح ({reservations.count()} بدلاً من {items_with_stock.count()})")
        if not all(r.status in ['released'] for r in all_reservations):
            print(f"   ❌ بعض الحجوزات لم تُحرر")

    print()


# Import Sum for aggregation
from django.db.models import Sum


if __name__ == '__main__':
    test_sales_integration()

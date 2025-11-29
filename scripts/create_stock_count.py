#!/usr/bin/env python
"""
إنشاء جرد شامل للمخزون
Create comprehensive stock count
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.models import StockCount, StockCountLine, ItemStock, Warehouse
from apps.core.models import Company, User
from django.db import transaction
from datetime import date
from decimal import Decimal
import random


def create_stock_count():
    """إنشاء جرد شامل للمخزون"""

    print("=" * 80)
    print("إنشاء جرد شامل للمخزون")
    print("=" * 80)
    print()

    # الحصول على البيانات الأساسية
    try:
        company = Company.objects.first()
        user = User.objects.filter(is_superuser=True).first()
        warehouse = Warehouse.objects.filter(company=company).first()

        if not all([company, user, warehouse]):
            print("❌ البيانات الأساسية غير مكتملة!")
            return

        print(f"✅ الشركة: {company.name}")
        print(f"✅ المستودع: {warehouse.name}")
        print(f"✅ المستخدم: {user.username}")
        print()

    except Exception as e:
        print(f"❌ خطأ في جلب البيانات الأساسية: {e}")
        return

    # الحصول على جميع المواد التي لديها رصيد في المستودع
    # استخدام distinct على item لتفادي التكرار
    items_with_stock = ItemStock.objects.filter(
        company=company,
        warehouse=warehouse,
        quantity__gt=0
    ).select_related('item').order_by('item', '-quantity')

    # الحصول على قائمة المواد الفريدة
    seen_items = set()
    unique_items_with_stock = []
    for item_stock in items_with_stock:
        if item_stock.item.id not in seen_items:
            seen_items.add(item_stock.item.id)
            unique_items_with_stock.append(item_stock)

    total_items = len(unique_items_with_stock)

    if total_items == 0:
        print("⚠️  لا توجد مواد في المخزون!")
        return

    print(f"📦 عدد المواد في المخزون: {total_items}")
    print()

    try:
        with transaction.atomic():
            # إنشاء سند الجرد
            stock_count = StockCount.objects.create(
                company=company,
                warehouse=warehouse,
                date=date.today(),
                count_type='full',  # جرد كامل
                supervisor=user,
                notes='جرد شامل للمخزون',
                created_by=user
            )

            print(f"✅ تم إنشاء سند الجرد: {stock_count.number}")
            print()

            # إنشاء خطوط الجرد لجميع المواد
            print("إضافة المواد إلى سند الجرد...")
            print()

            created_lines = 0
            for i, item_stock in enumerate(unique_items_with_stock, 1):
                # الكمية الدفترية (من النظام)
                book_quantity = item_stock.quantity

                # الكمية الفعلية (نحاكي الجرد الفعلي)
                # في الحقيقة: 80% مطابقة تماماً، 15% فيها فروقات صغيرة، 5% فروقات كبيرة
                rand = random.random()
                if rand < 0.80:
                    # مطابقة تماماً
                    actual_quantity = book_quantity
                elif rand < 0.95:
                    # فرق صغير (±1-2 وحدات)
                    diff = Decimal(random.choice([-2, -1, 1, 2]))
                    actual_quantity = max(Decimal('0'), book_quantity + diff)
                else:
                    # فرق كبير (±5-10%)
                    diff_percent = Decimal(random.choice([-0.1, -0.05, 0.05, 0.1]))
                    actual_quantity = max(Decimal('0'), book_quantity * (Decimal('1') + diff_percent))

                line = StockCountLine.objects.create(
                    count=stock_count,
                    item=item_stock.item,
                    system_quantity=book_quantity,
                    counted_quantity=actual_quantity,
                    unit_cost=item_stock.average_cost,
                    notes='جرد فعلي'
                )

                created_lines += 1

                if i % 10 == 0 or i == total_items:
                    print(f"  [{i}/{total_items}] تمت إضافة {i} مادة...")

            print()
            print(f"✅ تمت إضافة {created_lines} سطر جرد")
            print()

            # اعتماد سند الجرد
            print("اعتماد سند الجرد...")
            stock_count.status = 'approved'
            stock_count.approved_by = user
            stock_count.approval_date = date.today()
            stock_count.save()
            print(f"✅ تم اعتماد سند الجرد بنجاح")
            print()

            # حساب الإحصائيات
            lines = stock_count.lines.all()
            total_lines = lines.count()
            matched_lines = lines.filter(difference_quantity=0).count()
            positive_variance = lines.filter(difference_quantity__gt=0).count()
            negative_variance = lines.filter(difference_quantity__lt=0).count()

            total_variance_value = sum(
                line.difference_value
                for line in lines
            )

            print("=" * 80)
            print("إحصائيات الجرد")
            print("=" * 80)
            print(f"📦 إجمالي الأصناف: {total_lines}")
            print(f"✅ مطابقة: {matched_lines} ({matched_lines*100/total_lines:.1f}%)")
            print(f"📈 زيادة: {positive_variance} ({positive_variance*100/total_lines:.1f}%)")
            print(f"📉 نقص: {negative_variance} ({negative_variance*100/total_lines:.1f}%)")
            print(f"💰 قيمة الفروقات: {total_variance_value:.2f} دينار")
            print()

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return

    # التحقق النهائي
    print("=" * 80)
    print("التحقق النهائي")
    print("=" * 80)

    total_counts = StockCount.objects.filter(company=company).count()
    approved_counts = StockCount.objects.filter(company=company, status='approved').count()

    print(f"📦 إجمالي سندات الجرد: {total_counts}")
    print(f"✅ المعتمدة: {approved_counts}")
    print()


if __name__ == '__main__':
    create_stock_count()

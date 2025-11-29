#!/usr/bin/env python
"""
إنشاء سندات تحويل تجريبية
Create test stock transfer documents
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.models import StockTransfer, StockTransferLine, ItemStock, Warehouse
from apps.core.models import Item, Branch, Company, User
from django.db import transaction
from datetime import date
from decimal import Decimal


def create_test_stock_transfer():
    """إنشاء سندات تحويل تجريبية"""

    print("=" * 80)
    print("إنشاء سندات تحويل تجريبية")
    print("=" * 80)
    print()

    # الحصول على البيانات الأساسية
    try:
        company = Company.objects.first()
        user = User.objects.filter(is_superuser=True).first()

        if not all([company, user]):
            print("❌ البيانات الأساسية غير مكتملة!")
            return

        print(f"✅ الشركة: {company.name}")
        print(f"✅ المستخدم: {user.username}")
        print()

    except Exception as e:
        print(f"❌ خطأ في جلب البيانات الأساسية: {e}")
        return

    # الحصول على مستودعين مختلفين
    warehouses = Warehouse.objects.filter(
        company=company
    ).select_related('branch')[:5]

    if warehouses.count() < 2:
        print("⚠️  يجب أن يكون هناك مستودعين على الأقل!")
        return

    from_warehouse = warehouses[0]
    to_warehouse = warehouses[1]

    print(f"📦 المستودع المصدر: {from_warehouse.name}")
    print(f"📦 المستودع الوجهة: {to_warehouse.name}")
    print()

    # الحصول على المواد التي لديها رصيد في المستودع المصدر
    items_with_stock = ItemStock.objects.filter(
        company=company,
        warehouse=from_warehouse,
        quantity__gt=10
    ).select_related('item')[:3]

    if not items_with_stock.exists():
        print("⚠️  لا توجد مواد لديها رصيد كافٍ في المستودع المصدر!")
        return

    print(f"📦 عدد المواد المتاحة: {items_with_stock.count()}")
    print()

    # إنشاء سندات التحويل
    success_count = 0
    errors = []

    for i, item_stock in enumerate(items_with_stock, 1):
        print(f"[{i}/{items_with_stock.count()}] إنشاء سند تحويل لـ {item_stock.item.name}...")
        print(f"   الرصيد الحالي في المصدر: {item_stock.quantity}")

        try:
            with transaction.atomic():
                # إنشاء سند التحويل
                transfer = StockTransfer.objects.create(
                    company=company,
                    branch=from_warehouse.branch,
                    warehouse=from_warehouse,
                    destination_warehouse=to_warehouse,
                    date=date.today(),
                    reference=f'TEST-TRANS-{i}',
                    notes=f'سند تحويل تجريبي {i}',
                    created_by=user
                )

                # إنشاء سطر التحويل
                quantity_to_transfer = min(Decimal('3'), item_stock.quantity * Decimal('0.1'))

                line = StockTransferLine.objects.create(
                    transfer=transfer,
                    item=item_stock.item,
                    quantity=quantity_to_transfer,
                    unit_cost=item_stock.average_cost,
                    notes=f'تحويل تجريبي'
                )

                print(f"   ✅ تم إنشاء السند: {transfer.number}")
                print(f"   📝 الكمية المحولة: {quantity_to_transfer}")

                # الموافقة على السند
                transfer.approve(user=user)
                print(f"   ✅ تم الموافقة على السند")

                # إرسال السند
                transfer.send(user=user)
                print(f"   📤 تم إرسال السند")

                # استلام السند
                transfer.receive(user=user)
                print(f"   📥 تم استلام السند بنجاح")

                success_count += 1
                print()

        except Exception as e:
            error_msg = f"{item_stock.item.name}: {str(e)}"
            errors.append(error_msg)
            print(f"   ❌ خطأ: {e}")
            print()

    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    print(f"✅ نجح: {success_count}")
    print(f"❌ فشل: {len(errors)}")
    print()

    if errors:
        print("=" * 80)
        print("الأخطاء")
        print("=" * 80)
        for error in errors:
            print(f"  • {error}")
        print()

    # التحقق النهائي
    print("=" * 80)
    print("التحقق النهائي")
    print("=" * 80)

    total_transfers = StockTransfer.objects.filter(company=company).count()
    posted_transfers = StockTransfer.objects.filter(company=company, is_posted=True).count()

    print(f"📦 إجمالي سندات التحويل: {total_transfers}")
    print(f"✅ المرحلة: {posted_transfers}")
    print()


if __name__ == '__main__':
    create_test_stock_transfer()

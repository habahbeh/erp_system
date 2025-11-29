#!/usr/bin/env python
"""
إنشاء سندات إخراج تجريبية
Create test stock out documents
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.models import StockOut, StockDocumentLine, ItemStock, Warehouse
from apps.core.models import Item, Branch, Company, User
from django.db import transaction
from datetime import date
from decimal import Decimal


def create_test_stock_out():
    """إنشاء سندات إخراج تجريبية"""

    print("=" * 80)
    print("إنشاء سندات إخراج تجريبية")
    print("=" * 80)
    print()

    # الحصول على البيانات الأساسية
    try:
        company = Company.objects.first()
        branch = Branch.objects.filter(company=company).first()
        warehouse = Warehouse.objects.filter(company=company, branch=branch).first()
        user = User.objects.filter(is_superuser=True).first()

        if not all([company, branch, warehouse, user]):
            print("❌ البيانات الأساسية غير مكتملة!")
            print(f"   Company: {company}")
            print(f"   Branch: {branch}")
            print(f"   Warehouse: {warehouse}")
            print(f"   User: {user}")
            return

        print(f"✅ الشركة: {company.name}")
        print(f"✅ الفرع: {branch.name}")
        print(f"✅ المستودع: {warehouse.name}")
        print(f"✅ المستخدم: {user.username}")
        print()

    except Exception as e:
        print(f"❌ خطأ في جلب البيانات الأساسية: {e}")
        return

    # الحصول على المواد التي لديها رصيد متاح
    items_with_stock = ItemStock.objects.filter(
        company=company,
        warehouse=warehouse,
        quantity__gt=10  # كمية أكبر من 10 لنضمن إمكانية الإخراج
    ).select_related('item')[:5]

    if not items_with_stock.exists():
        print("⚠️  لا توجد مواد لديها رصيد كافٍ!")
        print("   يجب أن يكون هناك مواد برصيد أكبر من 10")
        return

    print(f"📦 عدد المواد المتاحة: {items_with_stock.count()}")
    print()

    # إنشاء سندات إخراج
    success_count = 0
    errors = []

    for i, item_stock in enumerate(items_with_stock, 1):
        print(f"[{i}/{items_with_stock.count()}] إنشاء سند إخراج لـ {item_stock.item.name}...")
        print(f"   الرصيد الحالي: {item_stock.quantity}")

        try:
            with transaction.atomic():
                # إنشاء سند الإخراج
                stock_out = StockOut.objects.create(
                    company=company,
                    branch=branch,
                    warehouse=warehouse,
                    date=date.today(),
                    destination_type='sales',  # نوع الوجهة: مبيعات
                    reference=f'TEST-OUT-{i}',
                    notes=f'سند إخراج تجريبي {i}',
                    created_by=user
                )

                # إنشاء سطر الإخراج
                # نخرج 5 وحدات أو 25% من الرصيد (أيهما أقل)
                quantity_to_issue = min(Decimal('5'), item_stock.quantity * Decimal('0.25'))

                line = StockDocumentLine.objects.create(
                    stock_out=stock_out,
                    item=item_stock.item,
                    quantity=quantity_to_issue,
                    unit_cost=item_stock.average_cost,
                    notes=f'إخراج تجريبي'
                )

                print(f"   ✅ تم إنشاء السند: {stock_out.number}")
                print(f"   📝 الكمية المخرجة: {quantity_to_issue}")

                # ترحيل السند
                stock_out.post(user=user)

                print(f"   ✅ تم ترحيل السند بنجاح")

                # التحقق من إنشاء القيد المحاسبي
                if stock_out.journal_entry:
                    print(f"   💰 تم إنشاء القيد المحاسبي: {stock_out.journal_entry.number}")
                else:
                    print(f"   ⚠️  لم يتم إنشاء قيد محاسبي")

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

    total_stock_outs = StockOut.objects.filter(company=company).count()
    posted_stock_outs = StockOut.objects.filter(company=company, is_posted=True).count()
    with_journal = StockOut.objects.filter(
        company=company,
        is_posted=True,
        journal_entry__isnull=False
    ).count()

    print(f"📦 إجمالي سندات الإخراج: {total_stock_outs}")
    print(f"✅ المرحلة: {posted_stock_outs}")
    print(f"💰 لديها قيود محاسبية: {with_journal}")
    print()


if __name__ == '__main__':
    create_test_stock_out()

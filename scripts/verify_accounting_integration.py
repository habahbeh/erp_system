#!/usr/bin/env python
"""
التحقق النهائي من التكامل المحاسبي
Final verification of accounting integration
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.models import StockIn, StockOut, StockTransfer
from apps.accounting.models import JournalEntry
from apps.core.models import Item, Company
from decimal import Decimal


def verify_accounting_integration():
    """التحقق النهائي من التكامل المحاسبي"""

    print("=" * 80)
    print("التحقق النهائي من التكامل المحاسبي")
    print("=" * 80)
    print()

    company = Company.objects.first()

    # 1. التحقق من ربط المواد بالحسابات
    print("1️⃣  التحقق من ربط المواد بالحسابات المحاسبية")
    print("-" * 80)

    total_items = Item.objects.filter(company=company).count()
    items_with_inventory_account = Item.objects.filter(
        company=company,
        inventory_account__isnull=False
    ).count()
    items_with_cogs_account = Item.objects.filter(
        company=company,
        cost_of_goods_account__isnull=False
    ).count()

    print(f"إجمالي المواد: {total_items}")
    print(f"✅ مربوطة بحساب المخزون: {items_with_inventory_account}/{total_items} ({items_with_inventory_account*100/total_items:.1f}%)")
    print(f"✅ مربوطة بحساب التكلفة: {items_with_cogs_account}/{total_items} ({items_with_cogs_account*100/total_items:.1f}%)")
    print()

    # 2. التحقق من سندات الإدخال
    print("2️⃣  التحقق من سندات الإدخال")
    print("-" * 80)

    total_stock_in = StockIn.objects.filter(company=company).count()
    posted_stock_in = StockIn.objects.filter(company=company, is_posted=True).count()
    with_journal_stock_in = StockIn.objects.filter(
        company=company,
        is_posted=True,
        journal_entry__isnull=False
    ).count()

    print(f"إجمالي السندات: {total_stock_in}")
    print(f"✅ المرحلة: {posted_stock_in}/{total_stock_in} ({posted_stock_in*100/total_stock_in if total_stock_in > 0 else 0:.1f}%)")
    print(f"💰 لديها قيود محاسبية: {with_journal_stock_in}/{posted_stock_in} ({with_journal_stock_in*100/posted_stock_in if posted_stock_in > 0 else 0:.1f}%)")
    print()

    # 3. التحقق من سندات الإخراج
    print("3️⃣  التحقق من سندات الإخراج")
    print("-" * 80)

    total_stock_out = StockOut.objects.filter(company=company).count()
    posted_stock_out = StockOut.objects.filter(company=company, is_posted=True).count()
    with_journal_stock_out = StockOut.objects.filter(
        company=company,
        is_posted=True,
        journal_entry__isnull=False
    ).count()

    print(f"إجمالي السندات: {total_stock_out}")
    print(f"✅ المرحلة: {posted_stock_out}/{total_stock_out} ({posted_stock_out*100/total_stock_out if total_stock_out > 0 else 0:.1f}%)")
    print(f"💰 لديها قيود محاسبية: {with_journal_stock_out}/{posted_stock_out} ({with_journal_stock_out*100/posted_stock_out if posted_stock_out > 0 else 0:.1f}%)")
    print()

    # 4. التحقق من سندات التحويل
    print("4️⃣  التحقق من سندات التحويل")
    print("-" * 80)

    total_transfers = StockTransfer.objects.filter(company=company).count()
    completed_transfers = StockTransfer.objects.filter(company=company, status='completed').count()

    print(f"إجمالي السندات: {total_transfers}")
    print(f"✅ المكتملة: {completed_transfers}/{total_transfers} ({completed_transfers*100/total_transfers if total_transfers > 0 else 0:.1f}%)")
    print()

    # 5. فحص عينة من القيود المحاسبية
    print("5️⃣  فحص عينة من القيود المحاسبية")
    print("-" * 80)

    # فحص آخر 5 قيود من سندات الإدخال
    recent_stock_ins = StockIn.objects.filter(
        company=company,
        is_posted=True,
        journal_entry__isnull=False
    ).order_by('-posted_date')[:5]

    print(f"آخر {recent_stock_ins.count()} قيود من سندات الإدخال:")
    for si in recent_stock_ins:
        je = si.journal_entry
        debits = sum(line.debit_amount for line in je.lines.all())
        credits = sum(line.credit_amount for line in je.lines.all())
        balanced = debits == credits

        status = "✅ متوازن" if balanced else "❌ غير متوازن"
        print(f"  {si.number} → {je.number}: مدين={debits:.2f}, دائن={credits:.2f} {status}")

    print()

    # فحص آخر 5 قيود من سندات الإخراج
    recent_stock_outs = StockOut.objects.filter(
        company=company,
        is_posted=True,
        journal_entry__isnull=False
    ).order_by('-posted_date')[:5]

    print(f"آخر {recent_stock_outs.count()} قيود من سندات الإخراج:")
    for so in recent_stock_outs:
        je = so.journal_entry
        debits = sum(line.debit_amount for line in je.lines.all())
        credits = sum(line.credit_amount for line in je.lines.all())
        balanced = debits == credits

        status = "✅ متوازن" if balanced else "❌ غير متوازن"
        print(f"  {so.number} → {je.number}: مدين={debits:.2f}, دائن={credits:.2f} {status}")

    print()

    # 6. النتيجة النهائية
    print("=" * 80)
    print("النتيجة النهائية")
    print("=" * 80)

    all_checks_passed = (
        items_with_inventory_account == total_items and
        items_with_cogs_account == total_items and
        with_journal_stock_in == posted_stock_in and
        with_journal_stock_out == posted_stock_out
    )

    if all_checks_passed:
        print("✅✅✅ ممتاز! جميع الفحوصات نجحت!")
        print("   التكامل المحاسبي يعمل بشكل كامل وصحيح.")
    else:
        print("⚠️  بعض الفحوصات بحاجة إلى مراجعة:")
        if items_with_inventory_account < total_items:
            print(f"   • بعض المواد غير مربوطة بحساب المخزون")
        if items_with_cogs_account < total_items:
            print(f"   • بعض المواد غير مربوطة بحساب التكلفة")
        if with_journal_stock_in < posted_stock_in:
            print(f"   • بعض سندات الإدخال المرحلة بدون قيود محاسبية")
        if with_journal_stock_out < posted_stock_out:
            print(f"   • بعض سندات الإخراج المرحلة بدون قيود محاسبية")

    print()


if __name__ == '__main__':
    verify_accounting_integration()

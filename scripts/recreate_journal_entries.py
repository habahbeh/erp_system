#!/usr/bin/env python
"""
إعادة إنشاء القيود المحاسبية لسندات الإدخال
Recreate journal entries for existing stock in documents
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.models import StockIn
from apps.accounting.models import FiscalYear, AccountingPeriod
from django.db import transaction
from datetime import date


def recreate_journal_entries():
    """إعادة إنشاء القيود المحاسبية لسندات الإدخال المرحلة"""

    print("=" * 80)
    print("إعادة إنشاء القيود المحاسبية لسندات الإدخال")
    print("=" * 80)
    print()

    # الحصول على جميع السندات المرحلة بدون قيود محاسبية
    stock_ins = StockIn.objects.filter(
        is_posted=True,
        journal_entry__isnull=True
    ).select_related('company', 'branch', 'warehouse', 'posted_by')

    total = stock_ins.count()
    print(f"📦 إجمالي السندات المرحلة بدون قيود: {total}")
    print()

    if total == 0:
        print("✅ جميع السندات لديها قيود محاسبية!")
        return

    # إحصائيات
    success_count = 0
    failed_count = 0
    errors = []

    # معالجة كل سند
    for i, stock_in in enumerate(stock_ins, 1):
        print(f"[{i}/{total}] معالجة {stock_in.number}...")

        # البحث عن السنة المالية المناسبة لتاريخ السند
        fiscal_year = FiscalYear.objects.filter(
            start_date__lte=stock_in.date,
            end_date__gte=stock_in.date,
            is_closed=False
        ).first()

        if not fiscal_year:
            print(f"  ⚠️  لا توجد سنة مالية مفتوحة للتاريخ {stock_in.date}")
            failed_count += 1
            errors.append(f"{stock_in.number}: لا توجد سنة مالية مفتوحة")
            continue

        # التحقق من الفترة المحاسبية
        period = AccountingPeriod.objects.filter(
            fiscal_year=fiscal_year,
            start_date__lte=stock_in.date,
            end_date__gte=stock_in.date,
            is_closed=False
        ).first()

        if not period:
            print(f"  ⚠️  لا توجد فترة محاسبية مفتوحة للتاريخ {stock_in.date}")
            failed_count += 1
            errors.append(f"{stock_in.number}: لا توجد فترة محاسبية مفتوحة")
            continue

        try:
            with transaction.atomic():
                # إنشاء القيد المحاسبي
                stock_in.create_journal_entry(user=stock_in.posted_by)
                success_count += 1
                print(f"  ✅ تم إنشاء القيد المحاسبي")

        except Exception as e:
            failed_count += 1
            error_msg = f"{stock_in.number}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ خطأ: {e}")

    print()
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    print(f"✅ نجح: {success_count}")
    print(f"❌ فشل: {failed_count}")
    print(f"📦 الإجمالي: {total}")
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

    remaining = StockIn.objects.filter(
        is_posted=True,
        journal_entry__isnull=True
    ).count()

    if remaining == 0:
        print("✅ جميع السندات المرحلة لديها قيود محاسبية الآن!")
    else:
        print(f"⚠️  لا يزال هناك {remaining} سند بدون قيود محاسبية")

    print()


if __name__ == '__main__':
    recreate_journal_entries()

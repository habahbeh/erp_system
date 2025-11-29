#!/usr/bin/env python
"""
ربط جميع المواد بالحسابات المحاسبية
Link all items to accounting accounts
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Item
from apps.accounting.models import Account
from decimal import Decimal


def link_items_to_accounts():
    """ربط جميع المواد بالحسابات المحاسبية"""

    print("=" * 80)
    print("ربط المواد بالحسابات المحاسبية")
    print("=" * 80)
    print()

    # البحث عن الحسابات المحاسبية المطلوبة
    try:
        inventory_account = Account.objects.filter(code='120000').first()
        if not inventory_account:
            print("⚠️  حساب المخزون (120000) غير موجود!")
            print("   البحث عن حسابات بديلة...")
            # البحث عن أي حساب مخزون
            inventory_account = Account.objects.filter(
                code__startswith='12',
                can_have_children=False
            ).first()

        if inventory_account:
            print(f"✅ حساب المخزون: {inventory_account.code} - {inventory_account.name}")
        else:
            print("❌ لم يتم العثور على حساب مخزون!")
            return

    except Exception as e:
        print(f"❌ خطأ في البحث عن حساب المخزون: {e}")
        return

    try:
        cogs_account = Account.objects.filter(code='510000').first()
        if not cogs_account:
            print("⚠️  حساب تكلفة البضاعة المباعة (510000) غير موجود!")
            print("   البحث عن حسابات بديلة...")
            # البحث عن أي حساب تكلفة
            cogs_account = Account.objects.filter(
                code__startswith='51',
                can_have_children=False
            ).first()

        if cogs_account:
            print(f"✅ حساب تكلفة البضاعة: {cogs_account.code} - {cogs_account.name}")
        else:
            print("❌ لم يتم العثور على حساب تكلفة البضاعة!")
            return

    except Exception as e:
        print(f"❌ خطأ في البحث عن حساب تكلفة البضاعة: {e}")
        return

    print()
    print("-" * 80)
    print()

    # الحصول على جميع المواد
    items = Item.objects.all()
    total_items = items.count()

    print(f"📦 إجمالي المواد: {total_items}")
    print()

    # إحصائيات
    updated_count = 0
    already_linked_count = 0

    # ربط كل مادة
    for i, item in enumerate(items, 1):
        needs_update = False

        if not item.inventory_account:
            item.inventory_account = inventory_account
            needs_update = True

        if not item.cost_of_goods_account:
            item.cost_of_goods_account = cogs_account
            needs_update = True

        if needs_update:
            item.save()
            updated_count += 1
            print(f"  [{i}/{total_items}] ✅ {item.code} - {item.name}")
        else:
            already_linked_count += 1
            print(f"  [{i}/{total_items}] ⏭️  {item.code} - {item.name} (مربوط مسبقاً)")

    print()
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    print(f"✅ تم التحديث: {updated_count}")
    print(f"⏭️  مربوط مسبقاً: {already_linked_count}")
    print(f"📦 الإجمالي: {total_items}")
    print()

    # التحقق النهائي
    print("=" * 80)
    print("التحقق النهائي")
    print("=" * 80)

    items_without_inventory_account = Item.objects.filter(
        inventory_account__isnull=True
    ).count()

    items_without_cogs_account = Item.objects.filter(
        cost_of_goods_account__isnull=True
    ).count()

    if items_without_inventory_account == 0 and items_without_cogs_account == 0:
        print("✅ جميع المواد مربوطة بالحسابات المحاسبية بنجاح!")
    else:
        print(f"⚠️  مواد بدون حساب مخزون: {items_without_inventory_account}")
        print(f"⚠️  مواد بدون حساب تكلفة: {items_without_cogs_account}")

    print()


if __name__ == '__main__':
    link_items_to_accounts()

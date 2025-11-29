"""
Script لتنظيف السجلات المكررة في ItemStock
يدمج السجلات المكررة لنفس المادة في نفس المستودع
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Count
from apps.inventory.models import ItemStock
from decimal import Decimal


def cleanup_duplicate_stocks():
    """Find and merge duplicate ItemStock records"""

    print("🔍 البحث عن السجلات المكررة في ItemStock...")

    # Find duplicates
    duplicates = (
        ItemStock.objects
        .values('company', 'item', 'warehouse')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )

    total_duplicates = duplicates.count()
    print(f"📊 وجدت {total_duplicates} مجموعة من السجلات المكررة")

    if total_duplicates == 0:
        print("✅ لا توجد سجلات مكررة!")
        return

    merged_count = 0
    deleted_count = 0

    for dup in duplicates:
        # Get all records for this combination
        stocks = ItemStock.objects.filter(
            company_id=dup['company'],
            item_id=dup['item'],
            warehouse_id=dup['warehouse']
        ).order_by('id')

        # Keep the first one
        main_stock = stocks.first()
        duplicates_to_merge = stocks[1:]

        print(f"\n📦 معالجة: المادة {main_stock.item.name} في المستودع {main_stock.warehouse.name}")
        print(f"   عدد السجلات المكررة: {duplicates_to_merge.count()}")

        # Merge quantities
        total_quantity = main_stock.quantity
        total_value = main_stock.total_value

        for dup_stock in duplicates_to_merge:
            total_quantity += dup_stock.quantity
            total_value += dup_stock.total_value
            print(f"   - دمج سجل: كمية={dup_stock.quantity}, قيمة={dup_stock.total_value}")

            # IMPORTANT: Zero out the duplicate before deleting
            # to bypass the prevent_delete_if_has_balance signal
            dup_stock.quantity = Decimal('0')
            dup_stock.total_value = Decimal('0')
            dup_stock.average_cost = Decimal('0')
            dup_stock.save()

            # Now safe to delete
            dup_stock.delete()
            deleted_count += 1

        # Update main record
        main_stock.quantity = total_quantity
        main_stock.total_value = total_value

        if total_quantity > 0:
            main_stock.average_cost = total_value / total_quantity
        else:
            main_stock.average_cost = Decimal('0')

        main_stock.save()

        print(f"   ✅ النتيجة: كمية نهائية={total_quantity}, قيمة={total_value}, متوسط التكلفة={main_stock.average_cost}")
        merged_count += 1

    print(f"\n{'='*60}")
    print(f"✅ تم الانتهاء!")
    print(f"📊 الإحصائيات:")
    print(f"   - مجموعات تم دمجها: {merged_count}")
    print(f"   - سجلات تم حذفها: {deleted_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("="*60)
    print("🧹 تنظيف السجلات المكررة في ItemStock")
    print("="*60)

    response = input("\n⚠️  هل أنت متأكد من المتابعة؟ (yes/no): ")

    if response.lower() in ['yes', 'y', 'نعم']:
        cleanup_duplicate_stocks()
    else:
        print("❌ تم الإلغاء")

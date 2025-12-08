"""
سكريبت لتحديث partner_id في سطور القيود اليومية من الفواتير
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.accounting.models import JournalEntryLine, JournalEntry

def update_partner_ids():
    """تحديث partner_id من المراجع"""

    updated_count = 0

    # الحصول على جميع السطور التي ليس لها partner_id
    lines_without_partner = JournalEntryLine.objects.filter(
        partner_id__isnull=True
    ).select_related('journal_entry')

    print(f"عدد السطور بدون partner_id: {lines_without_partner.count()}")

    with transaction.atomic():
        for line in lines_without_partner:
            entry = line.journal_entry
            reference = entry.reference or ''

            # البحث عن partner_id في سطور القيد الأخرى
            other_line = entry.lines.filter(
                partner_id__isnull=False
            ).first()

            if other_line:
                line.partner_id = other_line.partner_id
                line.partner_type = other_line.partner_type
                line.save(update_fields=['partner_id', 'partner_type'])
                updated_count += 1

                if updated_count % 100 == 0:
                    print(f"تم تحديث {updated_count} سطر...")

    print(f"\n✅ تم التحديث بنجاح!")
    print(f"إجمالي السطور المحدثة: {updated_count}")

if __name__ == '__main__':
    print("بدء تحديث partner_id في سطور القيود...")
    update_partner_ids()

# apps/purchases/management/commands/fix_rfq_units.py
"""
أمر لتعبئة الوحدات الفارغة في عناصر طلبات عروض الأسعار
"""

from django.core.management.base import BaseCommand
from apps.purchases.models import PurchaseQuotationRequestItem


class Command(BaseCommand):
    help = 'تعبئة الوحدات الفارغة في عناصر طلبات عروض الأسعار من المواد المرتبطة'

    def handle(self, *args, **options):
        # جلب جميع العناصر التي لديها مادة
        items = PurchaseQuotationRequestItem.objects.filter(
            item__isnull=False
        ).select_related('item__unit_of_measure')

        updated_count = 0
        for item in items:
            # التحقق من أن الوحدة فارغة أو تحتوي على whitespace فقط
            unit_is_empty = not item.unit or not item.unit.strip()

            if unit_is_empty and item.item and item.item.unit_of_measure:
                item.unit = item.item.unit_of_measure.name
                item.save(update_fields=['unit'])
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'تحديث: {item.quotation_request.number} - {item.item.name} → {item.unit}'
                    )
                )

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ تم تحديث {updated_count} عنصر بنجاح'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ جميع العناصر لديها وحدات صحيحة'
                )
            )

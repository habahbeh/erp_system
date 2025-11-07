"""
أمر Django لحذف سجلات الإهلاك لتاريخ محدد
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.assets.models import AssetDepreciation
from datetime import datetime


class Command(BaseCommand):
    help = 'حذف سجلات الإهلاك لتاريخ محدد'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='التاريخ بصيغة YYYY-MM-DD (مثال: 2025-10-31)',
            required=True
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='تأكيد الحذف'
        )

    def handle(self, *args, **options):
        date_str = options['date']
        confirm = options['confirm']

        try:
            # تحويل التاريخ
            depreciation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(self.style.ERROR(
                f'❌ صيغة التاريخ خاطئة. استخدم: YYYY-MM-DD'
            ))
            return

        # البحث عن السجلات
        records = AssetDepreciation.objects.filter(
            depreciation_date=depreciation_date
        ).select_related('asset', 'journal_entry')

        count = records.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(
                f'⚠️ لا توجد سجلات إهلاك لتاريخ {depreciation_date}'
            ))
            return

        # عرض السجلات
        self.stdout.write(self.style.WARNING(
            f'\n📋 تم العثور على {count} سجل إهلاك لتاريخ {depreciation_date}:\n'
        ))

        total_amount = 0
        for record in records[:10]:  # عرض أول 10 فقط
            self.stdout.write(
                f'  - {record.asset.asset_number}: {record.depreciation_amount} '
                f'(القيد: {record.journal_entry.number if record.journal_entry else "بدون"})'
            )
            total_amount += record.depreciation_amount

        if count > 10:
            self.stdout.write(f'  ... و {count - 10} سجل آخر')

        self.stdout.write(
            f'\n💰 المبلغ الإجمالي: {total_amount}\n'
        )

        # طلب التأكيد
        if not confirm:
            self.stdout.write(self.style.WARNING(
                '⚠️ لم يتم الحذف. استخدم --confirm للتأكيد\n'
                'مثال: python manage.py delete_depreciation_by_date --date=2025-10-31 --confirm'
            ))
            return

        # الحذف
        self.stdout.write(self.style.WARNING(
            '⏳ جاري الحذف...'
        ))

        with transaction.atomic():
            # حذف القيود المحاسبية المرتبطة
            journal_entries = []
            for record in records:
                if record.journal_entry:
                    journal_entries.append(record.journal_entry)

                # تحديث الأصل - إرجاع الإهلاك المتراكم
                asset = record.asset
                asset.accumulated_depreciation -= record.depreciation_amount
                asset.book_value += record.depreciation_amount

                # إذا كان الإهلاك مكتمل، إرجاعه لنشط
                if asset.depreciation_status == 'completed':
                    asset.depreciation_status = 'active'

                asset.save()

            # حذف السجلات
            deleted_count, _ = records.delete()

            # حذف القيود المحاسبية
            for entry in journal_entries:
                if entry:
                    try:
                        # إلغاء الترحيل أولاً
                        if entry.status == 'posted':
                            entry.unpost()
                        entry.delete()
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️ تعذر حذف القيد {entry.number}: {e}'
                        ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ تم حذف {deleted_count} سجل إهلاك بنجاح!\n'
            f'✅ تم تحديث الأصول وإرجاع الأرصدة\n'
        ))

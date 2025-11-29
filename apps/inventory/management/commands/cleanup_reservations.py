# apps/inventory/management/commands/cleanup_reservations.py
"""
أمر Django لتنظيف الحجوزات المنتهية
يمكن تشغيله دورياً عبر cron job

الاستخدام:
    python manage.py cleanup_reservations
    python manage.py cleanup_reservations --company=1
"""

from django.core.management.base import BaseCommand
from apps.inventory.services import ReservationService
from apps.core.models import Company


class Command(BaseCommand):
    help = 'تنظيف حجوزات المخزون المنتهية'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=int,
            help='رقم الشركة (اختياري - إذا لم يحدد ينظف للكل)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض ما سيتم تنظيفه بدون تنفيذ',
        )

    def handle(self, *args, **options):
        company_id = options.get('company')
        dry_run = options.get('dry_run', False)

        company = None
        if company_id:
            try:
                company = Company.objects.get(pk=company_id)
                self.stdout.write(f'تنظيف حجوزات الشركة: {company.name}')
            except Company.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'الشركة رقم {company_id} غير موجودة')
                )
                return

        if dry_run:
            from apps.inventory.models import StockReservation
            from django.utils import timezone

            filters = {
                'status': 'active',
                'expires_at__lt': timezone.now()
            }
            if company:
                filters['company'] = company

            expired_count = StockReservation.objects.filter(**filters).count()
            self.stdout.write(
                self.style.WARNING(
                    f'سيتم تنظيف {expired_count} حجز منتهي (dry-run)'
                )
            )
        else:
            count = ReservationService.cleanup_expired_reservations(company)
            self.stdout.write(
                self.style.SUCCESS(f'تم تنظيف {count} حجز منتهي')
            )

# Path: apps/assets/management/commands/generate_maintenance_tasks.py
"""
Management Command لتوليد مهام الصيانة الدورية التلقائية
يمكن جدولته في Cron للتنفيذ اليومي
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import datetime

from apps.assets.models import MaintenanceSchedule, AssetMaintenance
from apps.core.models import Company


class Command(BaseCommand):
    help = 'توليد مهام الصيانة الدورية وإرسال التنبيهات'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=30,
            help='عدد الأيام المستقبلية للبحث عن صيانة مستحقة (افتراضي: 30)'
        )
        parser.add_argument(
            '--company',
            type=int,
            help='معرف الشركة - اتركه فارغاً لجميع الشركات'
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='إرسال تنبيهات بالبريد الإلكتروني'
        )

    def handle(self, *args, **options):
        today = datetime.date.today()
        days_ahead = options['days_ahead']
        future_date = today + datetime.timedelta(days=days_ahead)

        self.stdout.write(
            self.style.WARNING(
                f'📅 البحث عن صيانة من {today} إلى {future_date}'
            )
        )

        # تحديد الشركات
        if options['company']:
            companies = Company.objects.filter(id=options['company'], is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)

        total_generated = 0
        total_alerts = 0

        for company in companies:
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(
                self.style.HTTP_INFO(f'🏢 الشركة: {company.name}')
            )
            self.stdout.write(f'{"=" * 60}')

            # الجداول النشطة
            schedules = MaintenanceSchedule.objects.filter(
                company=company,
                is_active=True,
                next_maintenance_date__lte=future_date
            ).select_related('asset', 'maintenance_type', 'assigned_to')

            self.stdout.write(f'📋 جداول الصيانة النشطة: {schedules.count()}')

            for schedule in schedules:
                try:
                    # التحقق من عدم وجود صيانة مجدولة لنفس التاريخ
                    existing = AssetMaintenance.objects.filter(
                        asset=schedule.asset,
                        maintenance_schedule=schedule,
                        scheduled_date=schedule.next_maintenance_date,
                        status__in=['scheduled', 'in_progress']
                    ).exists()

                    if existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⏭️  {schedule.asset.asset_number}: صيانة موجودة مسبقاً'
                            )
                        )
                        continue

                    # إنشاء مهمة الصيانة
                    with transaction.atomic():
                        maintenance = AssetMaintenance.objects.create(
                            company=company,
                            branch=schedule.asset.branch,
                            asset=schedule.asset,
                            maintenance_type=schedule.maintenance_type,
                            maintenance_category='preventive',
                            maintenance_schedule=schedule,
                            scheduled_date=schedule.next_maintenance_date,
                            status='scheduled',
                            labor_cost=schedule.estimated_cost,
                            description=f'صيانة دورية - {schedule.maintenance_type.name}',
                            created_by=None  # System
                        )

                        # تحديث تاريخ الصيانة القادمة في الجدول
                        schedule.update_next_maintenance_date()

                        total_generated += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ {schedule.asset.asset_number}: '
                                f'{maintenance.maintenance_number} - '
                                f'{maintenance.scheduled_date}'
                            )
                        )

                        # إرسال تنبيه إذا كانت الصيانة قريبة
                        if schedule.is_due_soon() and options['send_alerts']:
                            alert_sent = self._send_alert(maintenance, schedule)
                            if alert_sent:
                                total_alerts += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ {schedule.asset.asset_number}: {str(e)}'
                        )
                    )

            # التحقق من الصيانة المتأخرة
            overdue = AssetMaintenance.objects.filter(
                company=company,
                status='scheduled',
                scheduled_date__lt=today
            ).count()

            if overdue > 0:
                self.stdout.write(
                    self.style.ERROR(f'\n⚠️  صيانة متأخرة: {overdue}')
                )

        # النتيجة النهائية
        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.SUCCESS('✅ اكتمل التوليد'))
        self.stdout.write(f'{"=" * 60}')
        self.stdout.write(f'📊 مهام تم توليدها: {total_generated}')
        if options['send_alerts']:
            self.stdout.write(f'📧 تنبيهات تم إرسالها: {total_alerts}')

    def _send_alert(self, maintenance, schedule):
        """إرسال تنبيه بالبريد الإلكتروني"""

        if not schedule.assigned_to or not schedule.assigned_to.email:
            return False

        try:
            subject = f'تنبيه صيانة: {maintenance.asset.name}'

            message = f"""
مرحباً {schedule.assigned_to.get_full_name()},

تذكير بصيانة قادمة:

الأصل: {maintenance.asset.name} ({maintenance.asset.asset_number})
نوع الصيانة: {maintenance.maintenance_type.name}
التاريخ المجدول: {maintenance.scheduled_date}
التكلفة المتوقعة: {schedule.estimated_cost} د.أ

الرجاء التنسيق لتنفيذ الصيانة في الوقت المحدد.

تحياتنا،
نظام إدارة الأصول
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[schedule.assigned_to.email],
                fail_silently=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'    📧 تنبيه تم إرساله إلى: {schedule.assigned_to.email}'
                )
            )
            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'    ❌ فشل إرسال التنبيه: {str(e)}')
            )
            return False
# apps/inventory/management/commands/check_inventory_alerts.py
"""
أمر Django لفحص تنبيهات المخزون
يمكن تشغيله دورياً عبر cron job

الاستخدام:
    python manage.py check_inventory_alerts
    python manage.py check_inventory_alerts --company=1
    python manage.py check_inventory_alerts --email
"""

from django.core.management.base import BaseCommand
from apps.inventory.services import InventoryAlertService
from apps.core.models import Company


class Command(BaseCommand):
    help = 'فحص تنبيهات المخزون وعرضها أو إرسالها بالبريد'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=int,
            help='رقم الشركة (اختياري - إذا لم يحدد يفحص كل الشركات)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='عدد الأيام للتحذير من انتهاء الصلاحية (افتراضي 30)',
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='إرسال التنبيهات بالبريد الإلكتروني',
        )
        parser.add_argument(
            '--critical-only',
            action='store_true',
            help='عرض التنبيهات الحرجة فقط',
        )

    def handle(self, *args, **options):
        company_id = options.get('company')
        days = options.get('days', 30)
        send_email = options.get('email', False)
        critical_only = options.get('critical_only', False)

        companies = []
        if company_id:
            try:
                companies = [Company.objects.get(pk=company_id)]
            except Company.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'الشركة رقم {company_id} غير موجودة')
                )
                return
        else:
            companies = Company.objects.filter(is_active=True)

        total_alerts = 0

        for company in companies:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.HTTP_INFO(f'الشركة: {company.name}'))
            self.stdout.write('='*60)

            alerts = InventoryAlertService.get_all_alerts(
                company, days_threshold=days
            )

            if critical_only:
                alerts_to_show = alerts['critical']
            else:
                alerts_to_show = (
                    alerts['critical'] +
                    alerts['high'] +
                    alerts['medium'] +
                    alerts['low']
                )

            if not alerts_to_show:
                self.stdout.write(self.style.SUCCESS('لا توجد تنبيهات'))
                continue

            # عرض التنبيهات
            for severity in ['critical', 'high', 'medium', 'low']:
                if critical_only and severity != 'critical':
                    continue

                severity_alerts = alerts[severity]
                if not severity_alerts:
                    continue

                if severity == 'critical':
                    style = self.style.ERROR
                elif severity == 'high':
                    style = self.style.WARNING
                elif severity == 'medium':
                    style = self.style.NOTICE
                else:
                    style = self.style.HTTP_INFO

                self.stdout.write(style(f'\n{severity.upper()} ({len(severity_alerts)}):'))

                for alert in severity_alerts:
                    self.stdout.write(f"  - {alert['message']}")

            total_alerts += len(alerts_to_show)

            # إرسال البريد الإلكتروني
            if send_email and alerts_to_show:
                self._send_alert_email(company, alerts)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(
            self.style.SUCCESS(f'إجمالي التنبيهات: {total_alerts}')
        )

    def _send_alert_email(self, company, alerts):
        """إرسال التنبيهات بالبريد الإلكتروني"""
        from django.core.mail import send_mail
        from django.conf import settings

        subject = f'تنبيهات المخزون - {company.name}'

        message_lines = [f'تنبيهات المخزون للشركة: {company.name}\n']

        for severity in ['critical', 'high', 'medium', 'low']:
            severity_alerts = alerts[severity]
            if not severity_alerts:
                continue

            message_lines.append(f'\n{severity.upper()}:')
            for alert in severity_alerts:
                message_lines.append(f"  - {alert['message']}")

        message = '\n'.join(message_lines)

        try:
            # إرسال لمسؤولي المخزون
            # يمكن تخصيص قائمة المستلمين حسب الحاجة
            recipients = getattr(settings, 'INVENTORY_ALERT_EMAILS', [])

            if recipients:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'تم إرسال التنبيهات بالبريد')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'لم يتم تحديد INVENTORY_ALERT_EMAILS في settings'
                    )
                )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'فشل إرسال البريد: {e}')
            )

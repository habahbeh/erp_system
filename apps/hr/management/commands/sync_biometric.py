"""
أمر Django لمزامنة بيانات البصمة من أجهزة ZKTeco
يمكن تشغيله يدوياً أو عبر cron job للمزامنة التلقائية

الاستخدام:
    python manage.py sync_biometric                    # مزامنة جميع الأجهزة
    python manage.py sync_biometric --device-id 1     # مزامنة جهاز محدد
    python manage.py sync_biometric --company-id 1    # مزامنة أجهزة شركة محددة
    python manage.py sync_biometric --auto-only       # الأجهزة مع auto_sync=True فقط
    python manage.py sync_biometric --due-only        # الأجهزة المستحقة للمزامنة فقط
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'مزامنة بيانات البصمة من أجهزة ZKTeco'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='معرف جهاز محدد للمزامنة',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف الشركة للمزامنة',
        )
        parser.add_argument(
            '--auto-only',
            action='store_true',
            help='مزامنة الأجهزة مع auto_sync=True فقط',
        )
        parser.add_argument(
            '--due-only',
            action='store_true',
            help='مزامنة الأجهزة المستحقة للمزامنة فقط (حسب sync_interval)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='فرض المزامنة حتى لو لم يحن موعدها',
        )
        parser.add_argument(
            '--process-logs',
            action='store_true',
            help='معالجة السجلات غير المعالجة بعد المزامنة',
        )

    def handle(self, *args, **options):
        from apps.hr.models import BiometricDevice, BiometricLog, BiometricSyncLog
        from apps.hr.services.biometric_service import ZKTecoService

        verbosity = options.get('verbosity', 1)

        # بناء استعلام الأجهزة
        devices = BiometricDevice.objects.filter(
            is_active=True,
            status__in=['active', 'offline']  # include offline to retry
        )

        if options['device_id']:
            devices = devices.filter(pk=options['device_id'])
            if not devices.exists():
                raise CommandError(f'الجهاز برقم {options["device_id"]} غير موجود أو غير نشط')

        if options['company_id']:
            devices = devices.filter(company_id=options['company_id'])

        if options['auto_only']:
            devices = devices.filter(auto_sync=True)

        if options['due_only'] and not options['force']:
            # فقط الأجهزة التي حان موعد مزامنتها
            now = timezone.now()
            due_devices = []
            for device in devices:
                if device.last_sync is None:
                    due_devices.append(device.pk)
                else:
                    next_sync = device.last_sync + timedelta(minutes=device.sync_interval)
                    if now >= next_sync:
                        due_devices.append(device.pk)
            devices = devices.filter(pk__in=due_devices)

        device_count = devices.count()

        if device_count == 0:
            if verbosity > 0:
                self.stdout.write(self.style.WARNING('لا توجد أجهزة للمزامنة'))
            return

        if verbosity > 0:
            self.stdout.write(f'بدء مزامنة {device_count} جهاز(ة)...')

        total_records = 0
        successful = 0
        failed = 0

        for device in devices:
            try:
                if verbosity > 1:
                    self.stdout.write(f'  جاري مزامنة: {device.name} ({device.ip_address}:{device.port})')

                # إنشاء سجل المزامنة
                sync_log = BiometricSyncLog.objects.create(
                    device=device,
                    company=device.company,
                    sync_type='auto',
                    status='running',
                    started_at=timezone.now()
                )

                service = ZKTecoService(device)

                # الاتصال بالجهاز
                if not service.connect():
                    sync_log.status = 'failed'
                    sync_log.error_message = 'فشل الاتصال بالجهاز'
                    sync_log.completed_at = timezone.now()
                    sync_log.save()

                    device.status = 'offline'
                    device.save(update_fields=['status'])

                    failed += 1
                    if verbosity > 0:
                        self.stdout.write(self.style.ERROR(f'    ✗ فشل الاتصال بـ {device.name}'))
                    continue

                # تحديث حالة الجهاز
                device.status = 'active'
                device.last_connection = timezone.now()
                device.save(update_fields=['status', 'last_connection'])

                # جلب سجلات الحضور
                attendance_logs = service.get_attendance()
                sync_log.records_fetched = len(attendance_logs)

                if verbosity > 2:
                    self.stdout.write(f'    تم جلب {len(attendance_logs)} سجل')

                # معالجة وحفظ السجلات
                new_records = 0
                processed = 0
                failed_records = 0

                for log in attendance_logs:
                    try:
                        # تحقق من وجود السجل مسبقاً
                        exists = BiometricLog.objects.filter(
                            device=device,
                            device_user_id=str(log.get('user_id', '')),
                            punch_time=log.get('timestamp')
                        ).exists()

                        if not exists:
                            # تحديد نوع البصمة
                            punch_type = 'in'  # افتراضي
                            status = log.get('status', 0)
                            if status == 1:
                                punch_type = 'out'
                            elif status == 2:
                                punch_type = 'break_out'
                            elif status == 3:
                                punch_type = 'break_in'
                            elif status == 4:
                                punch_type = 'overtime_in'
                            elif status == 5:
                                punch_type = 'overtime_out'

                            # تحديد نوع التحقق
                            verify_map = {
                                0: 'password',
                                1: 'fingerprint',
                                2: 'card',
                                15: 'face'
                            }
                            verification_type = verify_map.get(log.get('punch', 0), 'fingerprint')

                            # البحث عن الموظف المرتبط
                            from apps.hr.models import EmployeeBiometricMapping
                            employee = None
                            mapping = EmployeeBiometricMapping.objects.filter(
                                device_user_id=str(log.get('user_id', '')),
                                is_active=True,
                                company=device.company
                            ).filter(
                                models.Q(device=device) | models.Q(device__isnull=True)
                            ).first()

                            if mapping:
                                employee = mapping.employee

                            BiometricLog.objects.create(
                                device=device,
                                company=device.company,
                                device_user_id=str(log.get('user_id', '')),
                                punch_time=log.get('timestamp'),
                                punch_type=punch_type,
                                verification_type=verification_type,
                                employee=employee,
                                raw_data=log
                            )
                            new_records += 1

                        processed += 1
                    except Exception as e:
                        failed_records += 1
                        logger.error(f'خطأ في معالجة سجل: {e}')

                # تحديث سجل المزامنة
                sync_log.records_processed = processed
                sync_log.records_failed = failed_records
                sync_log.new_attendance_records = new_records
                sync_log.status = 'completed' if failed_records == 0 else 'partial'
                sync_log.completed_at = timezone.now()
                sync_log.save()

                # تحديث آخر مزامنة للجهاز
                device.last_sync = timezone.now()
                device.save(update_fields=['last_sync'])

                # قطع الاتصال
                service.disconnect()

                total_records += new_records
                successful += 1

                if verbosity > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✓ {device.name}: {new_records} سجل جديد من أصل {len(attendance_logs)}'
                    ))

            except Exception as e:
                failed += 1
                logger.error(f'خطأ في مزامنة {device.name}: {e}')
                if verbosity > 0:
                    self.stdout.write(self.style.ERROR(f'    ✗ {device.name}: {str(e)}'))

                # تحديث سجل المزامنة في حالة الخطأ
                try:
                    sync_log.status = 'failed'
                    sync_log.error_message = str(e)
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                except:
                    pass

        # معالجة السجلات غير المعالجة
        if options['process_logs']:
            if verbosity > 0:
                self.stdout.write('\nجاري معالجة السجلات...')

            processed_count = self._process_unprocessed_logs(verbosity)

            if verbosity > 0:
                self.stdout.write(self.style.SUCCESS(f'تم معالجة {processed_count} سجل'))

        # ملخص
        if verbosity > 0:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'الملخص:')
            self.stdout.write(f'  - الأجهزة الناجحة: {successful}')
            self.stdout.write(f'  - الأجهزة الفاشلة: {failed}')
            self.stdout.write(f'  - إجمالي السجلات الجديدة: {total_records}')
            self.stdout.write('='*50)

    def _process_unprocessed_logs(self, verbosity=1):
        """معالجة سجلات البصمة غير المعالجة وتحويلها لسجلات حضور"""
        from apps.hr.models import BiometricLog, Attendance
        from django.db import models

        unprocessed = BiometricLog.objects.filter(
            is_processed=False,
            employee__isnull=False
        ).select_related('employee', 'company').order_by('punch_time')

        processed_count = 0

        for log in unprocessed:
            try:
                date = log.punch_time.date()
                employee = log.employee

                # البحث عن سجل حضور لنفس اليوم
                attendance, created = Attendance.objects.get_or_create(
                    employee=employee,
                    company=log.company,
                    date=date,
                    defaults={
                        'status': 'present'
                    }
                )

                # تحديث الحضور أو الانصراف
                if log.punch_type == 'in':
                    if attendance.check_in is None or log.punch_time.time() < attendance.check_in:
                        attendance.check_in = log.punch_time.time()
                elif log.punch_type == 'out':
                    if attendance.check_out is None or log.punch_time.time() > attendance.check_out:
                        attendance.check_out = log.punch_time.time()

                attendance.source = 'biometric'
                attendance.save()

                # تحديث سجل البصمة
                log.is_processed = True
                log.processed_at = timezone.now()
                log.attendance = attendance
                log.save()

                processed_count += 1

            except Exception as e:
                logger.error(f'خطأ في معالجة سجل {log.pk}: {e}')

        return processed_count

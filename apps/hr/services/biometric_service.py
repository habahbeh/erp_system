# apps/hr/services/biometric_service.py
"""
خدمة التكامل مع أجهزة البصمة
Biometric Device Integration Service

يدعم أجهزة ZKTeco وغيرها من الأجهزة المتوافقة
"""

import socket
import struct
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

logger = logging.getLogger(__name__)


class ZKTecoDevice:
    """
    فئة للتواصل مع أجهزة ZKTeco
    ZKTeco Device Communication Class

    تدعم بروتوكول UDP المستخدم في معظم أجهزة ZKTeco
    """

    # أوامر ZKTeco
    CMD_CONNECT = 1000
    CMD_EXIT = 1001
    CMD_ENABLE_DEVICE = 1002
    CMD_DISABLE_DEVICE = 1003
    CMD_GET_ATTENDANCE = 1007
    CMD_GET_USERS = 9
    CMD_GET_TIME = 201
    CMD_SET_TIME = 202
    CMD_CLEAR_ATTENDANCE = 1008
    CMD_GET_DEVICE_INFO = 11

    def __init__(self, ip: str, port: int = 4370, password: str = ''):
        """
        تهيئة الاتصال بالجهاز

        Args:
            ip: عنوان IP للجهاز
            port: رقم المنفذ (الافتراضي 4370)
            password: كلمة مرور الجهاز (اختياري)
        """
        self.ip = ip
        self.port = port
        self.password = password
        self.socket = None
        self.session_id = 0
        self.reply_id = 0
        self.connected = False

    def _create_header(self, command: int, data: bytes = b'') -> bytes:
        """إنشاء header للرسالة"""
        checksum = 0
        session_id = self.session_id
        reply_id = self.reply_id

        buf = struct.pack('<HHHH', command, checksum, session_id, reply_id)
        buf += data

        # حساب checksum
        checksum = sum(buf) & 0xFFFF
        buf = struct.pack('<HHHH', command, checksum, session_id, reply_id)
        buf += data

        return buf

    def connect(self) -> bool:
        """
        الاتصال بالجهاز

        Returns:
            True إذا نجح الاتصال، False خلاف ذلك
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5)

            # إرسال أمر الاتصال
            cmd_data = self._create_header(self.CMD_CONNECT)
            self.socket.sendto(cmd_data, (self.ip, self.port))

            # استقبال الرد
            data, addr = self.socket.recvfrom(1024)

            if len(data) >= 8:
                # تحليل الرد
                reply = struct.unpack('<HHHH', data[:8])
                if reply[0] == 2000:  # CMD_ACK_OK
                    self.session_id = reply[2]
                    self.reply_id = reply[3]
                    self.connected = True
                    logger.info(f"Connected to ZKTeco device at {self.ip}:{self.port}")
                    return True

            logger.warning(f"Failed to connect to ZKTeco device at {self.ip}:{self.port}")
            return False

        except socket.timeout:
            logger.error(f"Connection timeout to {self.ip}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"Connection error to {self.ip}:{self.port}: {str(e)}")
            return False

    def disconnect(self):
        """قطع الاتصال بالجهاز"""
        if self.socket and self.connected:
            try:
                cmd_data = self._create_header(self.CMD_EXIT)
                self.socket.sendto(cmd_data, (self.ip, self.port))
            except:
                pass
            finally:
                self.socket.close()
                self.socket = None
                self.connected = False
                logger.info(f"Disconnected from ZKTeco device at {self.ip}:{self.port}")

    def get_attendance_logs(self, start_date: datetime = None) -> List[Dict]:
        """
        جلب سجلات الحضور من الجهاز

        Args:
            start_date: تاريخ البداية لجلب السجلات (اختياري)

        Returns:
            قائمة بسجلات الحضور
        """
        if not self.connected:
            logger.warning("Not connected to device")
            return []

        logs = []
        try:
            # إرسال أمر جلب الحضور
            cmd_data = self._create_header(self.CMD_GET_ATTENDANCE)
            self.socket.sendto(cmd_data, (self.ip, self.port))

            # استقبال البيانات
            all_data = b''
            while True:
                try:
                    data, addr = self.socket.recvfrom(65535)
                    if len(data) <= 8:
                        break
                    all_data += data[8:]  # تخطي header
                except socket.timeout:
                    break

            # تحليل البيانات
            if len(all_data) > 0:
                record_size = 40  # حجم سجل الحضور في ZKTeco
                num_records = len(all_data) // record_size

                for i in range(num_records):
                    record_data = all_data[i * record_size:(i + 1) * record_size]
                    if len(record_data) >= record_size:
                        log = self._parse_attendance_record(record_data)
                        if log and (not start_date or log['punch_time'] >= start_date):
                            logs.append(log)

            logger.info(f"Fetched {len(logs)} attendance logs from {self.ip}")

        except Exception as e:
            logger.error(f"Error fetching attendance logs: {str(e)}")

        return logs

    def _parse_attendance_record(self, data: bytes) -> Optional[Dict]:
        """تحليل سجل حضور واحد"""
        try:
            # تنسيق ZKTeco للحضور
            user_id = struct.unpack('<H', data[0:2])[0]

            # استخراج الوقت (timestamp)
            timestamp = struct.unpack('<I', data[4:8])[0]

            # تحويل timestamp إلى datetime
            # ZKTeco يستخدم timestamp خاص يبدأ من 2000-01-01
            base_date = datetime(2000, 1, 1)
            punch_time = base_date + timedelta(seconds=timestamp)

            # نوع البصمة (0=حضور، 1=انصراف، الخ)
            punch_type = data[8] if len(data) > 8 else 0

            # نوع التحقق (0=بصمة، 1=كلمة مرور، 2=بطاقة)
            verify_type = data[9] if len(data) > 9 else 0

            return {
                'user_id': str(user_id),
                'punch_time': timezone.make_aware(punch_time) if timezone.is_naive(punch_time) else punch_time,
                'punch_type': self._get_punch_type(punch_type),
                'verify_type': self._get_verify_type(verify_type),
            }
        except Exception as e:
            logger.error(f"Error parsing attendance record: {str(e)}")
            return None

    def _get_punch_type(self, code: int) -> str:
        """تحويل كود نوع البصمة إلى نص"""
        types = {
            0: 'in',
            1: 'out',
            2: 'break_out',
            3: 'break_in',
            4: 'overtime_in',
            5: 'overtime_out',
        }
        return types.get(code, 'in')

    def _get_verify_type(self, code: int) -> str:
        """تحويل كود نوع التحقق إلى نص"""
        types = {
            0: 'fingerprint',
            1: 'password',
            2: 'card',
            3: 'face',
        }
        return types.get(code, 'fingerprint')

    def get_users(self) -> List[Dict]:
        """جلب قائمة المستخدمين من الجهاز"""
        if not self.connected:
            return []

        users = []
        try:
            cmd_data = self._create_header(self.CMD_GET_USERS)
            self.socket.sendto(cmd_data, (self.ip, self.port))

            data, addr = self.socket.recvfrom(65535)
            # تحليل بيانات المستخدمين...

        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")

        return users

    def get_device_info(self) -> Dict:
        """جلب معلومات الجهاز"""
        if not self.connected:
            return {}

        try:
            cmd_data = self._create_header(self.CMD_GET_DEVICE_INFO)
            self.socket.sendto(cmd_data, (self.ip, self.port))

            data, addr = self.socket.recvfrom(1024)
            # تحليل معلومات الجهاز...

            return {
                'ip': self.ip,
                'port': self.port,
                'connected': self.connected,
            }
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return {}

    def test_connection(self) -> Tuple[bool, str]:
        """
        اختبار الاتصال بالجهاز

        Returns:
            (نجاح/فشل, رسالة)
        """
        try:
            if self.connect():
                info = self.get_device_info()
                self.disconnect()
                return True, "تم الاتصال بالجهاز بنجاح"
            else:
                return False, "فشل الاتصال بالجهاز"
        except socket.timeout:
            return False, "انتهت مهلة الاتصال"
        except ConnectionRefusedError:
            return False, "تم رفض الاتصال"
        except Exception as e:
            return False, f"خطأ: {str(e)}"


class BiometricService:
    """
    خدمة إدارة أجهزة البصمة ومعالجة البيانات
    Biometric Device Management and Data Processing Service
    """

    @staticmethod
    def test_device_connection(device) -> Tuple[bool, str]:
        """
        اختبار الاتصال بجهاز البصمة

        Args:
            device: كائن BiometricDevice

        Returns:
            (نجاح/فشل, رسالة)
        """
        if device.device_type == 'zkteco':
            zk = ZKTecoDevice(
                ip=device.ip_address,
                port=device.port,
                password=device.device_password
            )
            return zk.test_connection()
        else:
            return False, "نوع الجهاز غير مدعوم حالياً"

    @staticmethod
    @transaction.atomic
    def sync_device_attendance(device, user=None) -> Dict:
        """
        مزامنة سجلات الحضور من جهاز البصمة

        Args:
            device: كائن BiometricDevice
            user: المستخدم الذي قام بالمزامنة (اختياري)

        Returns:
            نتائج المزامنة
        """
        from ..models import BiometricLog, BiometricSyncLog, EmployeeBiometricMapping, Attendance

        result = {
            'success': False,
            'records_fetched': 0,
            'records_processed': 0,
            'records_failed': 0,
            'new_attendance': 0,
            'message': '',
        }

        # إنشاء سجل مزامنة
        sync_log = BiometricSyncLog.objects.create(
            company=device.company,
            device=device,
            sync_type='manual' if user else 'auto',
            status='running',
            started_at=timezone.now(),
            created_by=user,
        )

        try:
            # الاتصال بالجهاز
            if device.device_type == 'zkteco':
                zk = ZKTecoDevice(
                    ip=device.ip_address,
                    port=device.port,
                    password=device.device_password
                )

                if not zk.connect():
                    raise Exception("فشل الاتصال بالجهاز")

                try:
                    # جلب آخر وقت مزامنة
                    last_sync = device.last_sync

                    # جلب سجلات الحضور
                    logs = zk.get_attendance_logs(start_date=last_sync)
                    result['records_fetched'] = len(logs)

                    # معالجة السجلات
                    for log_data in logs:
                        try:
                            # البحث عن الموظف
                            mapping = EmployeeBiometricMapping.objects.filter(
                                company=device.company,
                                device_user_id=log_data['user_id'],
                                is_active=True
                            ).first()

                            # إنشاء سجل البصمة
                            biometric_log, created = BiometricLog.objects.get_or_create(
                                device=device,
                                device_user_id=log_data['user_id'],
                                punch_time=log_data['punch_time'],
                                defaults={
                                    'company': device.company,
                                    'employee': mapping.employee if mapping else None,
                                    'punch_type': log_data['punch_type'],
                                    'verification_type': log_data['verify_type'],
                                }
                            )

                            if created:
                                result['records_processed'] += 1

                                # إنشاء أو تحديث سجل الحضور
                                if mapping and mapping.employee:
                                    attendance_created = BiometricService._process_attendance_log(
                                        biometric_log, mapping.employee
                                    )
                                    if attendance_created:
                                        result['new_attendance'] += 1

                        except Exception as e:
                            result['records_failed'] += 1
                            logger.error(f"Error processing log: {str(e)}")

                finally:
                    zk.disconnect()

            else:
                raise Exception("نوع الجهاز غير مدعوم")

            # تحديث وقت المزامنة
            device.last_sync = timezone.now()
            device.last_connection = timezone.now()
            device.status = 'active'
            device.save()

            # تحديث سجل المزامنة
            sync_log.status = 'completed'
            sync_log.completed_at = timezone.now()
            sync_log.records_fetched = result['records_fetched']
            sync_log.records_processed = result['records_processed']
            sync_log.records_failed = result['records_failed']
            sync_log.new_attendance_records = result['new_attendance']
            sync_log.save()

            result['success'] = True
            result['message'] = f"تمت المزامنة بنجاح: {result['records_processed']} سجل"

        except Exception as e:
            sync_log.status = 'failed'
            sync_log.completed_at = timezone.now()
            sync_log.error_message = str(e)
            sync_log.save()

            device.status = 'offline'
            device.save()

            result['message'] = f"فشلت المزامنة: {str(e)}"
            logger.error(f"Sync failed for device {device}: {str(e)}")

        return result

    @staticmethod
    def _process_attendance_log(biometric_log, employee) -> bool:
        """
        معالجة سجل البصمة وإنشاء/تحديث سجل الحضور

        Args:
            biometric_log: سجل البصمة
            employee: الموظف

        Returns:
            True إذا تم إنشاء سجل جديد
        """
        from ..models import Attendance

        punch_date = biometric_log.punch_time.date()
        punch_time = biometric_log.punch_time.time()

        # البحث عن سجل حضور موجود
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=punch_date,
            defaults={
                'company': employee.company,
                'branch': employee.branch,
                'status': 'present',
            }
        )

        # تحديث أوقات الحضور/الانصراف
        if biometric_log.punch_type == 'in':
            if not attendance.check_in or punch_time < attendance.check_in:
                attendance.check_in = punch_time
        elif biometric_log.punch_type == 'out':
            if not attendance.check_out or punch_time > attendance.check_out:
                attendance.check_out = punch_time

        # حساب ساعات العمل
        if attendance.check_in and attendance.check_out:
            attendance.working_hours = attendance.calculate_working_hours()

        attendance.save()

        # ربط سجل البصمة بالحضور
        biometric_log.attendance = attendance
        biometric_log.is_processed = True
        biometric_log.processed_at = timezone.now()
        biometric_log.save()

        return created

    @staticmethod
    def sync_all_devices(company) -> Dict:
        """
        مزامنة جميع أجهزة البصمة النشطة للشركة

        Args:
            company: الشركة

        Returns:
            ملخص نتائج المزامنة
        """
        from ..models import BiometricDevice

        devices = BiometricDevice.objects.filter(
            company=company,
            is_active=True,
            auto_sync=True
        )

        summary = {
            'total_devices': devices.count(),
            'successful': 0,
            'failed': 0,
            'total_records': 0,
            'devices': [],
        }

        for device in devices:
            result = BiometricService.sync_device_attendance(device)
            summary['devices'].append({
                'device': device.name,
                'success': result['success'],
                'records': result['records_processed'],
                'message': result['message'],
            })

            if result['success']:
                summary['successful'] += 1
                summary['total_records'] += result['records_processed']
            else:
                summary['failed'] += 1

        return summary

    @staticmethod
    def get_unprocessed_logs(company, device=None) -> List:
        """جلب سجلات البصمة غير المعالجة"""
        from ..models import BiometricLog

        qs = BiometricLog.objects.filter(
            company=company,
            is_processed=False
        )

        if device:
            qs = qs.filter(device=device)

        return qs.select_related('employee', 'device').order_by('punch_time')

    @staticmethod
    def reprocess_unmatched_logs(company) -> int:
        """
        إعادة معالجة سجلات البصمة غير المربوطة بموظفين
        (بعد إضافة ربط جديد)

        Returns:
            عدد السجلات المعالجة
        """
        from ..models import BiometricLog, EmployeeBiometricMapping

        processed = 0

        # جلب السجلات غير المربوطة بموظف
        unmatched_logs = BiometricLog.objects.filter(
            company=company,
            employee__isnull=True,
            is_processed=False
        )

        for log in unmatched_logs:
            # البحث عن ربط الموظف
            mapping = EmployeeBiometricMapping.objects.filter(
                company=company,
                device_user_id=log.device_user_id,
                is_active=True
            ).first()

            if mapping and mapping.employee:
                log.employee = mapping.employee
                log.save()

                # معالجة الحضور
                BiometricService._process_attendance_log(log, mapping.employee)
                processed += 1

        return processed

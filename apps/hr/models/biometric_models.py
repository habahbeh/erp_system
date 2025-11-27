# apps/hr/models/biometric_models.py
"""
نماذج أجهزة البصمة والحضور البيومتري
Biometric Devices and Attendance Models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class BiometricDevice(models.Model):
    """
    جهاز البصمة
    Biometric/Fingerprint Device
    """

    DEVICE_TYPE_CHOICES = [
        ('zkteco', 'ZKTeco'),
        ('hikvision', 'Hikvision'),
        ('suprema', 'Suprema'),
        ('anviz', 'Anviz'),
        ('other', _('أخرى')),
    ]

    CONNECTION_TYPE_CHOICES = [
        ('tcp', 'TCP/IP'),
        ('usb', 'USB'),
        ('serial', 'Serial'),
    ]

    STATUS_CHOICES = [
        ('active', _('نشط')),
        ('inactive', _('غير نشط')),
        ('maintenance', _('صيانة')),
        ('offline', _('غير متصل')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='biometric_devices',
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.CASCADE,
        related_name='biometric_devices',
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    name = models.CharField(
        _('اسم الجهاز'),
        max_length=100
    )

    device_type = models.CharField(
        _('نوع الجهاز'),
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='zkteco'
    )

    serial_number = models.CharField(
        _('الرقم التسلسلي'),
        max_length=100,
        blank=True
    )

    # إعدادات الاتصال
    connection_type = models.CharField(
        _('نوع الاتصال'),
        max_length=20,
        choices=CONNECTION_TYPE_CHOICES,
        default='tcp'
    )

    ip_address = models.GenericIPAddressField(
        _('عنوان IP'),
        null=True,
        blank=True
    )

    port = models.PositiveIntegerField(
        _('المنفذ'),
        default=4370,
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )

    # بيانات المصادقة
    device_password = models.CharField(
        _('كلمة مرور الجهاز'),
        max_length=50,
        blank=True,
        help_text=_('كلمة مرور الاتصال بالجهاز إن وجدت')
    )

    # الموقع
    location = models.CharField(
        _('الموقع'),
        max_length=200,
        blank=True,
        help_text=_('موقع الجهاز الفعلي')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    # آخر اتصال
    last_sync = models.DateTimeField(
        _('آخر مزامنة'),
        null=True,
        blank=True
    )

    last_connection = models.DateTimeField(
        _('آخر اتصال'),
        null=True,
        blank=True
    )

    # إعدادات المزامنة
    auto_sync = models.BooleanField(
        _('مزامنة تلقائية'),
        default=True
    )

    sync_interval = models.PositiveIntegerField(
        _('فترة المزامنة (دقائق)'),
        default=15,
        help_text=_('الفترة بين كل مزامنة تلقائية')
    )

    # ملاحظات
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_biometric_devices',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('جهاز بصمة')
        verbose_name_plural = _('أجهزة البصمة')
        ordering = ['name']
        unique_together = [['company', 'ip_address', 'port']]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class BiometricLog(models.Model):
    """
    سجل البصمات الخام من الجهاز
    Raw Biometric Logs from Device
    """

    PUNCH_TYPE_CHOICES = [
        ('in', _('حضور')),
        ('out', _('انصراف')),
        ('break_out', _('خروج استراحة')),
        ('break_in', _('عودة استراحة')),
        ('overtime_in', _('بداية إضافي')),
        ('overtime_out', _('نهاية إضافي')),
    ]

    VERIFICATION_TYPE_CHOICES = [
        ('fingerprint', _('بصمة')),
        ('face', _('وجه')),
        ('card', _('بطاقة')),
        ('password', _('كلمة مرور')),
        ('manual', _('يدوي')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='biometric_logs',
        verbose_name=_('الشركة')
    )

    device = models.ForeignKey(
        BiometricDevice,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('الجهاز')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='biometric_logs',
        verbose_name=_('الموظف'),
        null=True,
        blank=True
    )

    # رقم البصمة في الجهاز
    device_user_id = models.CharField(
        _('رقم المستخدم في الجهاز'),
        max_length=50
    )

    # وقت البصمة
    punch_time = models.DateTimeField(
        _('وقت البصمة')
    )

    punch_type = models.CharField(
        _('نوع البصمة'),
        max_length=20,
        choices=PUNCH_TYPE_CHOICES,
        default='in'
    )

    verification_type = models.CharField(
        _('نوع التحقق'),
        max_length=20,
        choices=VERIFICATION_TYPE_CHOICES,
        default='fingerprint'
    )

    # هل تم معالجة هذا السجل
    is_processed = models.BooleanField(
        _('تم المعالجة'),
        default=False
    )

    processed_at = models.DateTimeField(
        _('وقت المعالجة'),
        null=True,
        blank=True
    )

    # السجل المرتبط في الحضور
    attendance = models.ForeignKey(
        'hr.Attendance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='biometric_logs',
        verbose_name=_('سجل الحضور')
    )

    # بيانات إضافية من الجهاز
    raw_data = models.JSONField(
        _('البيانات الخام'),
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('سجل بصمة')
        verbose_name_plural = _('سجلات البصمة')
        ordering = ['-punch_time']
        # منع تكرار نفس البصمة
        unique_together = [['device', 'device_user_id', 'punch_time']]

    def __str__(self):
        return f"{self.device_user_id} - {self.punch_time}"


class EmployeeBiometricMapping(models.Model):
    """
    ربط الموظف برقمه في أجهزة البصمة
    Employee to Biometric Device Mapping
    """

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='employee_biometric_mappings',
        verbose_name=_('الشركة')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='biometric_mappings',
        verbose_name=_('الموظف')
    )

    device = models.ForeignKey(
        BiometricDevice,
        on_delete=models.CASCADE,
        related_name='employee_mappings',
        verbose_name=_('الجهاز'),
        null=True,
        blank=True,
        help_text=_('اتركه فارغاً للتطبيق على جميع الأجهزة')
    )

    device_user_id = models.CharField(
        _('رقم المستخدم في الجهاز'),
        max_length=50
    )

    # هل البصمة مسجلة في الجهاز
    is_enrolled = models.BooleanField(
        _('مسجل في الجهاز'),
        default=False
    )

    enrolled_at = models.DateTimeField(
        _('تاريخ التسجيل'),
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ربط بصمة موظف')
        verbose_name_plural = _('ربط بصمات الموظفين')
        unique_together = [['employee', 'device'], ['device', 'device_user_id']]

    def __str__(self):
        return f"{self.employee} - {self.device_user_id}"


class BiometricSyncLog(models.Model):
    """
    سجل عمليات المزامنة
    Sync Operations Log
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('running', _('جاري التنفيذ')),
        ('completed', _('مكتمل')),
        ('failed', _('فشل')),
        ('partial', _('مكتمل جزئياً')),
    ]

    SYNC_TYPE_CHOICES = [
        ('manual', _('يدوي')),
        ('auto', _('تلقائي')),
        ('scheduled', _('مجدول')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='biometric_sync_logs',
        verbose_name=_('الشركة')
    )

    device = models.ForeignKey(
        BiometricDevice,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name=_('الجهاز')
    )

    sync_type = models.CharField(
        _('نوع المزامنة'),
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        default='manual'
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    started_at = models.DateTimeField(
        _('وقت البدء'),
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        _('وقت الانتهاء'),
        null=True,
        blank=True
    )

    # إحصائيات
    records_fetched = models.PositiveIntegerField(
        _('السجلات المجلوبة'),
        default=0
    )

    records_processed = models.PositiveIntegerField(
        _('السجلات المعالجة'),
        default=0
    )

    records_failed = models.PositiveIntegerField(
        _('السجلات الفاشلة'),
        default=0
    )

    new_attendance_records = models.PositiveIntegerField(
        _('سجلات حضور جديدة'),
        default=0
    )

    # رسائل الخطأ
    error_message = models.TextField(
        _('رسالة الخطأ'),
        blank=True
    )

    # تفاصيل إضافية
    details = models.JSONField(
        _('التفاصيل'),
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='biometric_sync_logs',
        verbose_name=_('بواسطة')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('سجل مزامنة')
        verbose_name_plural = _('سجلات المزامنة')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device} - {self.created_at}"

    @property
    def duration(self):
        """مدة المزامنة"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

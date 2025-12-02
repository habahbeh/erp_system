# apps/hr/models/notification_models.py
"""
نماذج الإشعارات للموارد البشرية
HR Notification Models
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class HRNotification(BaseModel):
    """نموذج إشعارات الموارد البشرية"""

    NOTIFICATION_TYPES = [
        ('contract_expiry', 'انتهاء العقد'),
        ('leave_balance_low', 'رصيد إجازات منخفض'),
        ('leave_request', 'طلب إجازة'),
        ('advance_due', 'قسط سلفة مستحق'),
        ('attendance_absent', 'غياب موظف'),
        ('attendance_late', 'تأخر موظف'),
        ('document_expiry', 'انتهاء وثيقة'),
        ('probation_end', 'انتهاء فترة التجربة'),
        ('increment_due', 'استحقاق علاوة'),
        ('payroll_ready', 'كشف راتب جاهز'),
        ('general', 'إشعار عام'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    ]

    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='general'
    )
    title = models.CharField(_('العنوان'), max_length=255)
    message = models.TextField(_('الرسالة'))
    priority = models.CharField(
        _('الأولوية'),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # المستلم
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hr_notifications',
        verbose_name=_('المستلم'),
        null=True,
        blank=True,
        help_text=_('اتركه فارغاً للإشعارات العامة')
    )

    # الموظف المعني (إن وجد)
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('الموظف'),
        null=True,
        blank=True
    )

    # الربط بالكائن المرتبط
    related_object_type = models.CharField(
        _('نوع الكائن المرتبط'),
        max_length=100,
        blank=True,
        null=True
    )
    related_object_id = models.PositiveIntegerField(
        _('معرف الكائن المرتبط'),
        blank=True,
        null=True
    )

    # الحالة
    is_read = models.BooleanField(_('مقروءة'), default=False)
    read_at = models.DateTimeField(_('تاريخ القراءة'), null=True, blank=True)

    # تاريخ انتهاء الصلاحية (للإشعارات المؤقتة)
    expires_at = models.DateTimeField(_('تاريخ انتهاء الصلاحية'), null=True, blank=True)

    # رابط الإجراء
    action_url = models.CharField(
        _('رابط الإجراء'),
        max_length=500,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'hr_notification'
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['company', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_notification_type_display()}"

    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @classmethod
    def get_unread_count(cls, user, company):
        """الحصول على عدد الإشعارات غير المقروءة"""
        return cls.objects.filter(
            company=company,
            recipient=user,
            is_read=False,
            is_active=True
        ).count()

    @classmethod
    def get_unread_notifications(cls, user, company, limit=10):
        """الحصول على الإشعارات غير المقروءة"""
        return cls.objects.filter(
            company=company,
            recipient=user,
            is_read=False,
            is_active=True
        ).select_related('employee')[:limit]


class NotificationSetting(BaseModel):
    """إعدادات الإشعارات"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hr_notification_settings',
        verbose_name=_('المستخدم')
    )

    # إعدادات أنواع الإشعارات
    notify_contract_expiry = models.BooleanField(
        _('إشعار انتهاء العقود'),
        default=True
    )
    contract_expiry_days = models.PositiveIntegerField(
        _('أيام التنبيه قبل انتهاء العقد'),
        default=30
    )

    notify_leave_balance = models.BooleanField(
        _('إشعار رصيد الإجازات'),
        default=True
    )
    leave_balance_threshold = models.PositiveIntegerField(
        _('حد رصيد الإجازات المنخفض'),
        default=5
    )

    notify_leave_requests = models.BooleanField(
        _('إشعار طلبات الإجازات'),
        default=True
    )

    notify_advance_dues = models.BooleanField(
        _('إشعار أقساط السلف'),
        default=True
    )

    notify_attendance = models.BooleanField(
        _('إشعارات الحضور'),
        default=True
    )

    notify_documents = models.BooleanField(
        _('إشعار انتهاء الوثائق'),
        default=True
    )
    document_expiry_days = models.PositiveIntegerField(
        _('أيام التنبيه قبل انتهاء الوثيقة'),
        default=30
    )

    # إعدادات البريد الإلكتروني
    email_notifications = models.BooleanField(
        _('إرسال بريد إلكتروني'),
        default=False
    )

    class Meta:
        db_table = 'hr_notification_setting'
        verbose_name = _('إعدادات الإشعارات')
        verbose_name_plural = _('إعدادات الإشعارات')

    def __str__(self):
        return f"إعدادات إشعارات {self.user}"

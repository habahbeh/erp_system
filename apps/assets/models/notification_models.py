# apps/assets/models/notification_models.py
"""
نماذج الإشعارات للأصول الثابتة
- قوالب الإشعارات
- الإشعارات المرسلة
- إعدادات الإشعارات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
import datetime


class NotificationTemplate(BaseModel):
    """قوالب الإشعارات"""

    NOTIFICATION_TYPES = [
        ('maintenance_due', _('صيانة مستحقة')),
        ('warranty_expiry', _('انتهاء ضمان')),
        ('insurance_expiry', _('انتهاء تأمين')),
        ('depreciation_complete', _('إهلاك كامل')),
        ('approval_pending', _('موافقة معلقة')),
        ('asset_inactive', _('أصل معطل')),
        ('physical_count_due', _('جرد متأخر')),
        ('lease_payment_due', _('قسط إيجار مستحق')),
    ]

    CHANNEL_TYPES = [
        ('email', _('بريد إلكتروني')),
        ('sms', _('رسالة نصية')),
        ('system', _('إشعار نظام')),
        ('all', _('جميع القنوات')),
    ]

    code = models.CharField(_('رمز القالب'), max_length=50, unique=True)
    name = models.CharField(_('اسم القالب'), max_length=200)
    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    # القنوات
    notification_channel = models.CharField(
        _('قناة الإرسال'),
        max_length=20,
        choices=CHANNEL_TYPES,
        default='system'
    )

    # محتوى القالب
    subject_template = models.CharField(
        _('قالب العنوان'),
        max_length=200,
        help_text=_('يمكن استخدام متغيرات مثل: {asset_name}, {date}')
    )
    body_template = models.TextField(
        _('قالب المحتوى'),
        help_text=_('يمكن استخدام متغيرات مثل: {asset_name}, {asset_number}, {date}, {location}')
    )

    # إعدادات الإرسال
    send_to_responsible = models.BooleanField(
        _('إرسال للمسؤول عن الأصل'),
        default=True
    )
    send_to_supervisor = models.BooleanField(
        _('إرسال للمشرف'),
        default=False
    )
    additional_recipients = models.ManyToManyField(
        'core.User',
        verbose_name=_('مستلمون إضافيون'),
        related_name='notification_templates',
        blank=True
    )

    is_active = models.BooleanField(_('نشط'), default=True)

    class Meta:
        verbose_name = _('قالب إشعار')
        verbose_name_plural = _('قوالب الإشعارات')
        ordering = ['notification_type', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def render_subject(self, context):
        """إنشاء العنوان من القالب"""
        return self.subject_template.format(**context)

    def render_body(self, context):
        """إنشاء المحتوى من القالب"""
        return self.body_template.format(**context)


class AssetNotification(models.Model):
    """الإشعارات المرسلة"""

    NOTIFICATION_TYPES = [
        ('maintenance_due', _('صيانة مستحقة')),
        ('warranty_expiry', _('انتهاء ضمان')),
        ('insurance_expiry', _('انتهاء تأمين')),
        ('depreciation_complete', _('إهلاك كامل')),
        ('approval_pending', _('موافقة معلقة')),
        ('asset_inactive', _('أصل معطل')),
        ('physical_count_due', _('جرد متأخر')),
        ('lease_payment_due', _('قسط إيجار مستحق')),
    ]

    PRIORITY_LEVELS = [
        ('low', _('منخفض')),
        ('medium', _('متوسط')),
        ('high', _('عالي')),
        ('urgent', _('عاجل')),
    ]

    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('الأصل'),
        null=True,
        blank=True
    )

    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name=_('القالب')
    )

    # المستلم
    recipient = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='asset_notifications',
        verbose_name=_('المستلم')
    )

    # المحتوى
    subject = models.CharField(_('العنوان'), max_length=200)
    body = models.TextField(_('المحتوى'))
    priority = models.CharField(
        _('الأولوية'),
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium'
    )

    # التوقيت
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    sent_date = models.DateTimeField(_('تاريخ الإرسال'), null=True, blank=True)
    is_sent = models.BooleanField(_('تم الإرسال'), default=False)

    # القراءة
    is_read = models.BooleanField(_('مقروء'), default=False)
    read_date = models.DateTimeField(_('تاريخ القراءة'), null=True, blank=True)

    # الربط بالكائن المرتبط
    related_object_type = models.CharField(
        _('نوع الكائن المرتبط'),
        max_length=50,
        blank=True,
        help_text=_('مثل: maintenance, insurance, physical_count')
    )
    related_object_id = models.PositiveIntegerField(
        _('معرف الكائن المرتبط'),
        null=True,
        blank=True
    )

    # رابط الإجراء
    action_url = models.CharField(_('رابط الإجراء'), max_length=500, blank=True)

    class Meta:
        verbose_name = _('إشعار أصل')
        verbose_name_plural = _('إشعارات الأصول')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"

    def mark_as_read(self):
        """وضع علامة مقروء"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_date = timezone.now()
            self.save(update_fields=['is_read', 'read_date'])

    def mark_as_sent(self):
        """وضع علامة مرسل"""
        from django.utils import timezone
        if not self.is_sent:
            self.is_sent = True
            self.sent_date = timezone.now()
            self.save(update_fields=['is_sent', 'sent_date'])

    @classmethod
    def create_notification(cls, notification_type, asset, recipient, template=None, context=None):
        """إنشاء إشعار جديد"""
        if not template:
            # البحث عن القالب المناسب
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()

        if not template:
            return None

        # السياق الافتراضي
        if context is None:
            context = {}

        # إضافة معلومات الأصل للسياق
        if asset:
            context.update({
                'asset_name': asset.name,
                'asset_number': asset.asset_number,
                'location': asset.physical_location or '',
                'responsible': asset.responsible_employee.get_full_name() if asset.responsible_employee else '',
            })

        # إنشاء الإشعار
        notification = cls.objects.create(
            notification_type=notification_type,
            asset=asset,
            template=template,
            recipient=recipient,
            subject=template.render_subject(context),
            body=template.render_body(context),
        )

        return notification


class NotificationSettings(BaseModel):
    """إعدادات الإشعارات لكل مستخدم"""

    user = models.OneToOneField(
        'core.User',
        on_delete=models.CASCADE,
        related_name='asset_notification_settings',
        verbose_name=_('المستخدم')
    )

    # تفعيل/تعطيل أنواع الإشعارات
    maintenance_enabled = models.BooleanField(_('إشعارات الصيانة'), default=True)
    warranty_enabled = models.BooleanField(_('إشعارات الضمان'), default=True)
    insurance_enabled = models.BooleanField(_('إشعارات التأمين'), default=True)
    depreciation_enabled = models.BooleanField(_('إشعارات الإهلاك'), default=True)
    approval_enabled = models.BooleanField(_('إشعارات الموافقات'), default=True)
    physical_count_enabled = models.BooleanField(_('إشعارات الجرد'), default=True)
    lease_enabled = models.BooleanField(_('إشعارات الإيجار'), default=True)

    # التوقيت - كم يوم قبل الحدث
    maintenance_days_before = models.IntegerField(
        _('التنبيه قبل الصيانة (أيام)'),
        default=7
    )
    warranty_days_before = models.IntegerField(
        _('التنبيه قبل انتهاء الضمان (أيام)'),
        default=30
    )
    insurance_days_before = models.IntegerField(
        _('التنبيه قبل انتهاء التأمين (أيام)'),
        default=30
    )
    lease_days_before = models.IntegerField(
        _('التنبيه قبل قسط الإيجار (أيام)'),
        default=7
    )

    # قنوات الإرسال
    email_enabled = models.BooleanField(_('البريد الإلكتروني'), default=True)
    sms_enabled = models.BooleanField(_('الرسائل النصية'), default=False)
    system_enabled = models.BooleanField(_('إشعارات النظام'), default=True)

    # البريد الإلكتروني البديل
    alternative_email = models.EmailField(_('بريد إلكتروني بديل'), blank=True)
    alternative_phone = models.CharField(_('هاتف بديل'), max_length=20, blank=True)

    # أوقات الإرسال المفضلة
    send_summary_daily = models.BooleanField(_('ملخص يومي'), default=False)
    send_summary_weekly = models.BooleanField(_('ملخص أسبوعي'), default=True)
    preferred_time = models.TimeField(
        _('الوقت المفضل'),
        default=datetime.time(9, 0),
        help_text=_('وقت إرسال الملخصات')
    )

    class Meta:
        verbose_name = _('إعدادات إشعارات')
        verbose_name_plural = _('إعدادات الإشعارات')

    def __str__(self):
        return f"إعدادات إشعارات {self.user.username}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """الحصول على الإعدادات أو إنشاؤها"""
        settings, created = cls.objects.get_or_create(
            user=user,
            defaults={'company': user.company}
        )
        return settings
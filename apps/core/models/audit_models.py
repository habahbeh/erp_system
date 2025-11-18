# apps/core/models/audit_models.py
"""
نماذج التدقيق والسجلات - Audit Models
- AuditLog: سجل جميع العمليات في النظام
- VariantLifecycleEvent: سجل دورة حياة المتغيرات (NEW)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """سجل العمليات - لتتبع جميع التغييرات في النظام"""

    ACTION_CHOICES = [
        ('CREATE', _('إنشاء')),
        ('UPDATE', _('تعديل')),
        ('DELETE', _('حذف')),
        ('VIEW', _('عرض')),
        ('LOGIN', _('دخول')),
        ('LOGOUT', _('خروج'))
    ]

    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, verbose_name=_('المستخدم'))
    action = models.CharField(_('العملية'), max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(_('النموذج'), max_length=100)
    object_id = models.PositiveIntegerField(_('معرف السجل'), null=True, blank=True)
    object_repr = models.CharField(_('وصف السجل'), max_length=200)
    old_values = models.JSONField(_('القيم القديمة'), blank=True, null=True)
    new_values = models.JSONField(_('القيم الجديدة'), blank=True, null=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, verbose_name=_('الشركة'))
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, verbose_name=_('الفرع'))
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)
    timestamp = models.DateTimeField(_('التوقيت'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل عملية')
        verbose_name_plural = _('سجل العمليات')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr}"


class VariantLifecycleEvent(models.Model):
    """
    سجل دورة حياة المتغيرات - NEW

    يتتبع جميع الأحداث المهمة في حياة المتغير:
    - الإنشاء
    - التعديل
    - إيقاف الإنتاج (discontinued)
    - إعادة التفعيل
    - تغيير السعر
    - تغيير الباركود
    - إلخ
    """

    EVENT_TYPE_CHOICES = [
        ('CREATED', _('إنشاء')),
        ('UPDATED', _('تحديث')),
        ('DISCONTINUED', _('إيقاف الإنتاج')),
        ('REACTIVATED', _('إعادة تفعيل')),
        ('PRICE_CHANGED', _('تغيير سعر')),
        ('COST_CHANGED', _('تغيير تكلفة')),
        ('BARCODE_CHANGED', _('تغيير باركود')),
        ('UOM_ADDED', _('إضافة وحدة قياس')),
        ('UOM_REMOVED', _('حذف وحدة قياس')),
        ('ATTRIBUTE_CHANGED', _('تغيير خاصية')),
        ('IMAGE_UPDATED', _('تحديث صورة')),
        ('STOCK_ADJUSTED', _('تعديل مخزون')),
    ]

    # المتغير المرتبط
    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        related_name='lifecycle_events',
        verbose_name=_('المتغير')
    )

    # نوع الحدث
    event_type = models.CharField(
        _('نوع الحدث'),
        max_length=30,
        choices=EVENT_TYPE_CHOICES
    )

    # تفاصيل الحدث
    event_description = models.TextField(
        _('وصف الحدث'),
        help_text=_('وصف تفصيلي للحدث')
    )

    # القيم القديمة والجديدة (JSON)
    old_values = models.JSONField(
        _('القيم القديمة'),
        default=dict,
        blank=True,
        help_text=_('القيم قبل التغيير')
    )

    new_values = models.JSONField(
        _('القيم الجديدة'),
        default=dict,
        blank=True,
        help_text=_('القيم بعد التغيير')
    )

    # من قام بالتغيير
    changed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('تم بواسطة')
    )

    # التوقيت
    timestamp = models.DateTimeField(
        _('التوقيت'),
        auto_now_add=True
    )

    # السبب (اختياري)
    reason = models.CharField(
        _('السبب'),
        max_length=200,
        blank=True,
        help_text=_('سبب التغيير')
    )

    # ملاحظات إضافية
    notes = models.TextField(_('ملاحظات'), blank=True)

    # معلومات النظام
    ip_address = models.GenericIPAddressField(
        _('عنوان IP'),
        blank=True,
        null=True
    )

    user_agent = models.CharField(
        _('معلومات المتصفح'),
        max_length=300,
        blank=True
    )

    class Meta:
        verbose_name = _('حدث دورة حياة متغير')
        verbose_name_plural = _('أحداث دورة حياة المتغيرات')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['variant', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.variant} - {self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @staticmethod
    def log_event(variant, event_type, description, old_values=None, new_values=None,
                  changed_by=None, reason='', notes='', ip_address=None):
        """
        دالة مساعدة لتسجيل حدث جديد

        Args:
            variant: المتغير
            event_type: نوع الحدث
            description: وصف الحدث
            old_values: القيم القديمة (dict)
            new_values: القيم الجديدة (dict)
            changed_by: المستخدم الذي قام بالتغيير
            reason: سبب التغيير
            notes: ملاحظات
            ip_address: عنوان IP

        Returns:
            VariantLifecycleEvent: الحدث المسجل
        """
        event = VariantLifecycleEvent.objects.create(
            variant=variant,
            event_type=event_type,
            event_description=description,
            old_values=old_values or {},
            new_values=new_values or {},
            changed_by=changed_by,
            reason=reason,
            notes=notes,
            ip_address=ip_address
        )
        return event

    def get_changes_summary(self):
        """
        الحصول على ملخص التغييرات

        Returns:
            list: قائمة بالتغييرات في صيغة قابلة للقراءة
        """
        changes = []

        for key in self.new_values.keys():
            old_val = self.old_values.get(key)
            new_val = self.new_values.get(key)

            if old_val != new_val:
                changes.append({
                    'field': key,
                    'old_value': old_val,
                    'new_value': new_val
                })

        return changes

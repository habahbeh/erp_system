# Path: apps/assets/signals.py
"""
Signals للأحداث التلقائية في نظام الأصول
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import datetime

from .models import (
    Asset, AssetMaintenance, MaintenanceSchedule,
    AssetTransaction, AssetAttachment
)


@receiver(post_save, sender=Asset)
def asset_created_handler(sender, instance, created, **kwargs):
    """
    عند إنشاء أصل جديد:
    1. إنشاء جدول صيانة افتراضي إذا كانت الفئة تحتوي على إعدادات افتراضية
    2. إرسال إشعار للمسؤول
    """
    if created:
        # إنشاء جدول صيانة وقائية افتراضي (سنوي)
        if instance.category:
            try:
                # البحث عن نوع صيانة وقائية
                from .models import MaintenanceType
                preventive_type = MaintenanceType.objects.filter(
                    code='PREV',
                    is_active=True
                ).first()

                if preventive_type:
                    # إنشاء جدولة سنوية
                    MaintenanceSchedule.objects.create(
                        company=instance.company,
                        branch=instance.branch,
                        asset=instance,
                        maintenance_type=preventive_type,
                        frequency='annual',
                        start_date=instance.purchase_date,
                        next_maintenance_date=instance.purchase_date + datetime.timedelta(days=365),
                        alert_before_days=30,
                        description=f'صيانة وقائية سنوية - {instance.name}',
                        created_by=instance.created_by
                    )
            except Exception as e:
                pass  # فشل صامت


@receiver(post_save, sender=AssetMaintenance)
def maintenance_status_changed(sender, instance, created, **kwargs):
    """
    عند تغيير حالة الصيانة:
    1. تحديث حالة الأصل
    2. إرسال إشعار
    """
    if not created:
        # تحديث حالة الأصل
        if instance.status == 'in_progress':
            if instance.asset.status != 'under_maintenance':
                instance.asset.status = 'under_maintenance'
                instance.asset.save()

        elif instance.status == 'completed':
            if instance.asset.status == 'under_maintenance':
                # التحقق من عدم وجود صيانة أخرى جارية
                other_maintenance = AssetMaintenance.objects.filter(
                    asset=instance.asset,
                    status='in_progress'
                ).exclude(pk=instance.pk).exists()

                if not other_maintenance:
                    instance.asset.status = 'active'
                    instance.asset.save()


@receiver(pre_save, sender=AssetMaintenance)
def check_overdue_maintenance(sender, instance, **kwargs):
    """
    التحقق من الصيانة المتأخرة قبل الحفظ
    """
    if instance.status == 'scheduled':
        if instance.scheduled_date < datetime.date.today():
            # يمكن إضافة منطق للتنبيه
            pass


@receiver(post_save, sender=AssetAttachment)
def attachment_expiry_check(sender, instance, created, **kwargs):
    """
    التحقق من انتهاء صلاحية المرفقات (مثل الضمانات)
    """
    if instance.expiry_date:
        days_until_expiry = (instance.expiry_date - datetime.date.today()).days

        # إشعار قبل 30 يوم من الانتهاء
        if 0 < days_until_expiry <= 30:
            try:
                # إرسال إشعار للمسؤول
                if instance.asset.responsible_employee and instance.asset.responsible_employee.email:
                    subject = f'تنبيه: انتهاء صلاحية {instance.get_attachment_type_display()}'
                    message = f"""
تنبيه: سينتهي {instance.get_attachment_type_display()} للأصل {instance.asset.name} في {instance.expiry_date}

عدد الأيام المتبقية: {days_until_expiry} يوم

الرجاء اتخاذ الإجراء اللازم.
                    """

                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[instance.asset.responsible_employee.email],
                        fail_silently=True
                    )
            except Exception:
                pass


@receiver(post_save, sender=AssetTransaction)
def transaction_completed_handler(sender, instance, created, **kwargs):
    """
    عند اكتمال عملية على الأصل:
    1. تحديث حالة الأصل
    2. تسجيل في سجل التدقيق
    """
    if instance.status == 'completed':
        # تحديث حالة الأصل حسب نوع العملية
        if instance.transaction_type == 'sale':
            instance.asset.status = 'sold'
            instance.asset.save()

        elif instance.transaction_type == 'disposal':
            instance.asset.status = 'disposed'
            instance.asset.save()


# تسجيل الـ Signals
def register_signals():
    """تسجيل جميع الـ Signals"""
    pass  # يتم التسجيل تلقائياً عبر decorators
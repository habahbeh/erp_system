# apps/assets/signals.py
"""
إشارات Django للأصول الثابتة
- إشعارات تلقائية
- تحديثات تلقائية
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import datetime

from .models import (
    Asset,
    AssetMaintenance,
    MaintenanceSchedule,
    AssetInsurance,
    PhysicalCount,
    AssetLease,
    LeasePayment,
)


# ============ إشعارات الصيانة ============

@receiver(post_save, sender=MaintenanceSchedule)
def check_maintenance_due(sender, instance, created, **kwargs):
    """إرسال إشعار عند قرب موعد الصيانة"""
    from .models import AssetNotification, NotificationSettings

    if not instance.is_active:
        return

    if instance.is_due_soon():
        # الحصول على المسؤول
        responsible = instance.assigned_to or instance.asset.responsible_employee

        if not responsible:
            return

        # الحصول على إعدادات الإشعارات
        settings = NotificationSettings.objects.filter(
            user=responsible,
            maintenance_enabled=True
        ).first()

        if not settings:
            return

        # التحقق من عدم وجود إشعار سابق في آخر 24 ساعة
        yesterday = timezone.now() - datetime.timedelta(days=1)
        existing = AssetNotification.objects.filter(
            notification_type='maintenance_due',
            asset=instance.asset,
            recipient=responsible,
            created_at__gte=yesterday
        ).exists()

        if existing:
            return

        # إنشاء الإشعار
        context = {
            'asset_name': instance.asset.name,
            'asset_number': instance.asset.asset_number,
            'date': instance.next_maintenance_date.strftime('%Y-%m-%d'),
            'location': instance.asset.physical_location or '',
            'maintenance_type': instance.maintenance_type.name,
        }

        AssetNotification.create_notification(
            notification_type='maintenance_due',
            asset=instance.asset,
            recipient=responsible,
            context=context
        )


# ============ إشعارات الضمان ============

@receiver(post_save, sender=Asset)
def check_warranty_expiry(sender, instance, created, **kwargs):
    """إرسال إشعار عند قرب انتهاء الضمان"""
    from .models import AssetNotification, NotificationSettings

    if not instance.warranty_end_date:
        return

    responsible = instance.responsible_employee
    if not responsible:
        return

    settings = NotificationSettings.objects.filter(
        user=responsible,
        warranty_enabled=True
    ).first()

    if not settings:
        return

    # التحقق من قرب انتهاء الضمان
    today = datetime.date.today()
    days_until_expiry = (instance.warranty_end_date - today).days

    if 0 <= days_until_expiry <= settings.warranty_days_before:
        # التحقق من عدم وجود إشعار سابق
        yesterday = timezone.now() - datetime.timedelta(days=1)
        existing = AssetNotification.objects.filter(
            notification_type='warranty_expiry',
            asset=instance,
            recipient=responsible,
            created_at__gte=yesterday
        ).exists()

        if not existing:
            context = {
                'asset_name': instance.name,
                'asset_number': instance.asset_number,
                'date': instance.warranty_end_date.strftime('%Y-%m-%d'),
                'days': days_until_expiry,
            }

            AssetNotification.create_notification(
                notification_type='warranty_expiry',
                asset=instance,
                recipient=responsible,
                context=context
            )


# ============ إشعارات التأمين ============

@receiver(post_save, sender=AssetInsurance)
def check_insurance_expiry(sender, instance, created, **kwargs):
    """إرسال إشعار عند قرب انتهاء التأمين"""
    from .models import AssetNotification, NotificationSettings

    if instance.status != 'active':
        return

    responsible = instance.asset.responsible_employee
    if not responsible:
        return

    settings = NotificationSettings.objects.filter(
        user=responsible,
        insurance_enabled=True
    ).first()

    if not settings:
        return

    # التحقق من قرب انتهاء التأمين
    today = datetime.date.today()
    days_until_expiry = (instance.end_date - today).days

    if 0 <= days_until_expiry <= settings.insurance_days_before:
        yesterday = timezone.now() - datetime.timedelta(days=1)
        existing = AssetNotification.objects.filter(
            notification_type='insurance_expiry',
            asset=instance.asset,
            recipient=responsible,
            created_at__gte=yesterday
        ).exists()

        if not existing:
            context = {
                'asset_name': instance.asset.name,
                'asset_number': instance.asset.asset_number,
                'date': instance.end_date.strftime('%Y-%m-%d'),
                'days': days_until_expiry,
                'insurance_company': instance.insurance_company.name,
            }

            AssetNotification.create_notification(
                notification_type='insurance_expiry',
                asset=instance.asset,
                recipient=responsible,
                context=context
            )


# ============ إشعارات الإهلاك الكامل ============

@receiver(post_save, sender=Asset)
def check_depreciation_complete(sender, instance, created, **kwargs):
    """إرسال إشعار عند إهلاك الأصل بالكامل"""
    from .models import AssetNotification

    if instance.is_fully_depreciated() and instance.depreciation_status == 'active':
        responsible = instance.responsible_employee
        if not responsible:
            return

        # التحقق من عدم وجود إشعار سابق
        existing = AssetNotification.objects.filter(
            notification_type='depreciation_complete',
            asset=instance,
            recipient=responsible
        ).exists()

        if not existing:
            context = {
                'asset_name': instance.name,
                'asset_number': instance.asset_number,
            }

            AssetNotification.create_notification(
                notification_type='depreciation_complete',
                asset=instance,
                recipient=responsible,
                context=context
            )


# ============ تحديث حالة الأصل ============

@receiver(post_save, sender=AssetMaintenance)
def update_asset_status_on_maintenance(sender, instance, created, **kwargs):
    """تحديث حالة الأصل عند بدء/انتهاء الصيانة"""
    if instance.status == 'in_progress':
        instance.asset.status = 'under_maintenance'
        instance.asset.save(update_fields=['status'])
    elif instance.status == 'completed':
        if instance.asset.status == 'under_maintenance':
            instance.asset.status = 'active'
            instance.asset.save(update_fields=['status'])


# ============ تحديث حالة التأمين ============

@receiver(post_save, sender=AssetInsurance)
def update_insurance_status(sender, instance, created, **kwargs):
    """تحديث حالة التأمين للأصل"""
    if instance.is_active():
        instance.asset.insurance_status = 'insured'
    elif instance.status == 'expired':
        instance.asset.insurance_status = 'expired'
    else:
        instance.asset.insurance_status = 'not_insured'

    instance.asset.save(update_fields=['insurance_status'])


# ============ إشعارات الإيجار ============

@receiver(post_save, sender=LeasePayment)
def check_lease_payment_due(sender, instance, created, **kwargs):
    """إرسال إشعار عند قرب موعد قسط الإيجار"""
    from .models import AssetNotification, NotificationSettings

    if instance.is_paid:
        return

    responsible = instance.lease.asset.responsible_employee
    if not responsible:
        return

    settings = NotificationSettings.objects.filter(
        user=responsible,
        lease_enabled=True
    ).first()

    if not settings:
        return

    today = datetime.date.today()
    days_until_payment = (instance.payment_date - today).days

    if 0 <= days_until_payment <= settings.lease_days_before:
        yesterday = timezone.now() - datetime.timedelta(days=1)
        existing = AssetNotification.objects.filter(
            notification_type='lease_payment_due',
            asset=instance.lease.asset,
            recipient=responsible,
            created_at__gte=yesterday
        ).exists()

        if not existing:
            context = {
                'asset_name': instance.lease.asset.name,
                'asset_number': instance.lease.asset.asset_number,
                'date': instance.payment_date.strftime('%Y-%m-%d'),
                'amount': str(instance.amount),
                'payment_number': instance.payment_number,
            }

            AssetNotification.create_notification(
                notification_type='lease_payment_due',
                asset=instance.lease.asset,
                recipient=responsible,
                context=context
            )
"""
الإشارات التلقائية
لإنشاء ملف المستخدم وتسجيل العمليات
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, AuditLog

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف المستخدم تلقائياً"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف المستخدم"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
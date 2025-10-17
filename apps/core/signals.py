"""
الإشارات التلقائية
لإنشاء ملف المستخدم وتسجيل العمليات
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, AuditLog, Company

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


# ✅ **إضافة Signal جديد للشركة:**
@receiver(post_save, sender=Company)
def create_company_defaults(sender, instance, created, **kwargs):
    """إنشاء البيانات الافتراضية للشركة الجديدة"""
    if created:
        # إنشاء تسلسلات الترقيم
        sequences_count = instance.create_default_sequences()

        # إنشاء دليل الحسابات الافتراضي
        accounts_count = instance.create_default_accounts()

        print(f"✅ تم إنشاء {sequences_count} تسلسل ترقيم للشركة {instance.name}")
        print(f"✅ تم إنشاء {accounts_count} حساب افتراضي للشركة {instance.name}")
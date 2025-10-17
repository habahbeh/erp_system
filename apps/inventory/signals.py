# في apps/inventory/signals.py (ملف جديد)
"""
إشارات المخزون
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import ItemStock


@receiver(post_save, sender=ItemStock)
def delete_empty_stock(sender, instance, **kwargs):
    """حذف رصيد المادة إذا أصبح صفر"""
    # لا نحذف تلقائياً، فقط نعطي تحذير
    # يمكن تفعيل الحذف التلقائي حسب الحاجة

    if instance.quantity == 0 and instance.reserved_quantity == 0:
        # يمكن حذفه أو تركه للسجل التاريخي
        # instance.delete()
        pass
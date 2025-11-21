# apps/inventory/signals.py
"""
إشارات المخزون
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import ItemStock
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ItemStock)
def check_low_stock_alert(sender, instance, created, **kwargs):
    """
    التحقق من انخفاض المخزون وإرسال تنبيه
    """
    # التحقق من الحد الأدنى
    if instance.is_below_min_level():
        logger.warning(
            f"Low stock alert: {instance.item.name} "
            f"(Variant: {instance.item_variant.code if instance.item_variant else 'N/A'}) "
            f"in warehouse {instance.warehouse.name}. "
            f"Current: {instance.quantity}, Min: {instance.min_level}"
        )
        # يمكن إضافة إرسال إشعار للمستخدمين هنا
        # من خلال notification system أو email

    # التحقق من نقطة إعادة الطلب
    if instance.check_reorder_needed():
        logger.info(
            f"Reorder point reached: {instance.item.name} "
            f"(Variant: {instance.item_variant.code if instance.item_variant else 'N/A'}) "
            f"in warehouse {instance.warehouse.name}. "
            f"Current: {instance.quantity}, Reorder Point: {instance.reorder_point}"
        )
        # يمكن إضافة إنشاء طلب شراء تلقائي هنا


@receiver(post_save, sender=ItemStock)
def delete_empty_stock(sender, instance, **kwargs):
    """
    حذف رصيد المادة إذا أصبح صفر (اختياري)

    ملاحظة: معطل حالياً للحفاظ على السجل التاريخي
    يمكن تفعيله حسب الحاجة
    """
    # if instance.quantity == 0 and instance.reserved_quantity == 0:
    #     instance.delete()
    #     logger.info(f"Deleted empty stock for {instance.item.name} in {instance.warehouse.name}")
    pass


@receiver(pre_delete, sender=ItemStock)
def prevent_delete_if_has_balance(sender, instance, **kwargs):
    """
    منع حذف رصيد المادة إذا كان له رصيد
    """
    if instance.quantity != 0:
        raise ValidationError(
            f'لا يمكن حذف رصيد المادة {instance.item.name} '
            f'في المستودع {instance.warehouse.name} لأن الرصيد = {instance.quantity}'
        )
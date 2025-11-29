# apps/purchases/signals.py
"""
إشارات المشتريات
تربط فواتير المشتريات بنظام المخزون تلقائياً
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import PurchaseInvoice
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseInvoice)
def create_stock_in_on_purchase_post(sender, instance, created, **kwargs):
    """
    إنشاء سند إدخال تلقائياً عند اعتماد فاتورة شراء

    يتم التشغيل عند:
    - اعتماد الفاتورة (is_posted = True)
    - إذا لم يكن لها سند إدخال مسبقاً
    """
    # تحقق من أن الفاتورة معتمدة ولم يتم إنشاء سند إدخال لها
    if not instance.is_posted:
        return

    # تحقق من وجود سند إدخال مرتبط
    from apps.inventory.models import StockIn

    existing_stock_in = StockIn.objects.filter(
        purchase_invoice=instance,
        company=instance.company
    ).first()

    if existing_stock_in:
        logger.info(f"StockIn already exists for PurchaseInvoice {instance.number}")
        return

    # إنشاء سند إدخال جديد
    try:
        with transaction.atomic():
            stock_in = StockIn.objects.create(
                company=instance.company,
                branch=getattr(instance, 'branch', None),
                date=instance.date,
                warehouse=instance.warehouse,
                source_type='purchase',
                supplier=instance.supplier,
                purchase_invoice=instance,
                reference=instance.number,
                notes=f'سند إدخال تلقائي لفاتورة شراء {instance.number}',
                created_by=instance.created_by
            )

            # إنشاء سطور السند من سطور الفاتورة
            from apps.inventory.models import StockDocumentLine

            for line in instance.lines.all():
                # تأكد من أن الصنف له مخزون (يمكن تخطي الخدمات)
                if not line.item:
                    continue

                StockDocumentLine.objects.create(
                    stock_in=stock_in,
                    item=line.item,
                    item_variant=line.item_variant if hasattr(line, 'item_variant') else None,
                    quantity=line.quantity,
                    unit_cost=line.unit_price,
                    notes=getattr(line, 'notes', '') or ''
                )

            # ترحيل السند تلقائياً
            stock_in.post(user=instance.created_by)

            logger.info(f"StockIn {stock_in.number} created and posted for PurchaseInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error creating StockIn for PurchaseInvoice {instance.number}: {str(e)}")
        # لا نرفع exception لعدم منع حفظ الفاتورة


@receiver(post_delete, sender=PurchaseInvoice)
def delete_stock_in_on_purchase_delete(sender, instance, **kwargs):
    """
    حذف سند الإدخال عند حذف فاتورة الشراء
    """
    from apps.inventory.models import StockIn

    try:
        stock_ins = StockIn.objects.filter(
            purchase_invoice=instance,
            company=instance.company
        )

        for stock_in in stock_ins:
            # إلغاء الترحيل أولاً
            if stock_in.is_posted:
                stock_in.unpost()

            # ثم الحذف
            stock_in.delete()
            logger.info(f"StockIn {stock_in.number} deleted with PurchaseInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error deleting StockIn for PurchaseInvoice {instance.number}: {str(e)}")

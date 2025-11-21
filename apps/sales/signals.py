# apps/sales/signals.py
"""
إشارات المبيعات
تربط فواتير المبيعات بنظام المخزون تلقائياً
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import SalesInvoice
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SalesInvoice)
def create_stock_out_on_sales_post(sender, instance, created, **kwargs):
    """
    إنشاء سند إخراج تلقائياً عند اعتماد فاتورة بيع

    يتم التشغيل عند:
    - اعتماد الفاتورة (is_posted = True)
    - إذا لم يكن لها سند إخراج مسبقاً
    """
    # تحقق من أن الفاتورة معتمدة
    if not instance.is_posted:
        return

    # تحقق من وجود سند إخراج مرتبط
    from apps.inventory.models import StockOut

    existing_stock_out = StockOut.objects.filter(
        sales_invoice=instance,
        company=instance.company
    ).first()

    if existing_stock_out:
        logger.info(f"StockOut already exists for SalesInvoice {instance.number}")
        return

    # إنشاء سند إخراج جديد
    try:
        with transaction.atomic():
            stock_out = StockOut.objects.create(
                company=instance.company,
                branch=getattr(instance, 'branch', None),
                date=instance.date,
                warehouse=instance.warehouse,
                destination_type='sales',
                customer=instance.customer,
                sales_invoice=instance,
                reference=instance.number,
                notes=f'سند إخراج تلقائي لفاتورة بيع {instance.number}',
                created_by=instance.created_by
            )

            # إنشاء سطور السند من سطور الفاتورة
            from apps.inventory.models import StockDocumentLine

            for line in instance.items.all():  # items هو related_name للـ lines
                # تأكد من أن الصنف له مخزون (يمكن تخطي الخدمات)
                if not line.item:
                    continue

                StockDocumentLine.objects.create(
                    stock_out=stock_out,
                    item=line.item,
                    item_variant=line.item_variant if hasattr(line, 'item_variant') else None,
                    quantity=line.quantity,
                    unit_cost=0,  # سيتم تحديثه تلقائياً من متوسط التكلفة عند الترحيل
                    notes=line.notes or ''
                )

            # ترحيل السند تلقائياً
            # هنا سيتم التحقق من توفر الكمية ورفع exception إذا لم تكن متوفرة
            stock_out.post(user=instance.created_by)

            logger.info(f"StockOut {stock_out.number} created and posted for SalesInvoice {instance.number}")

    except ValidationError as ve:
        # خطأ في التحقق من الكمية - يجب إبلاغ المستخدم
        logger.error(f"Validation error creating StockOut for SalesInvoice {instance.number}: {str(ve)}")
        # يمكن إضافة رسالة للمستخدم هنا
        raise  # إعادة رفع الخطأ لإيقاف العملية

    except Exception as e:
        logger.error(f"Error creating StockOut for SalesInvoice {instance.number}: {str(e)}")
        # لا نرفع exception لعدم منع حفظ الفاتورة في حالات أخرى


@receiver(post_delete, sender=SalesInvoice)
def delete_stock_out_on_sales_delete(sender, instance, **kwargs):
    """
    حذف سند الإخراج عند حذف فاتورة البيع
    """
    from apps.inventory.models import StockOut

    try:
        stock_outs = StockOut.objects.filter(
            sales_invoice=instance,
            company=instance.company
        )

        for stock_out in stock_outs:
            # إلغاء الترحيل أولاً
            if stock_out.is_posted:
                stock_out.unpost()

            # ثم الحذف
            stock_out.delete()
            logger.info(f"StockOut {stock_out.number} deleted with SalesInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error deleting StockOut for SalesInvoice {instance.number}: {str(e)}")

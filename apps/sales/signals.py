# apps/sales/signals.py
"""
إشارات المبيعات
تربط فواتير المبيعات وأوامر البيع بنظام المخزون تلقائياً
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import SalesInvoice, SalesOrder
from datetime import datetime, timedelta
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


# ============================================================================
# SalesOrder Signals - Stock Reservation
# ============================================================================

@receiver(post_save, sender=SalesOrder)
def create_stock_reservation_on_order_approval(sender, instance, created, **kwargs):
    """
    حجز المخزون تلقائياً عند الموافقة على أمر البيع

    يتم التشغيل عند:
    - الموافقة على الأمر (is_approved = True)
    - إذا لم يكن محجوز مسبقاً
    """
    # تحقق من أن الأمر موافق عليه
    if not instance.is_approved:
        return

    # تخطي إذا كان الأمر مكتمل (تم تسليمه أو فوترته بالكامل)
    if instance.is_delivered or instance.is_invoiced:
        return

    # تحقق من وجود حجوزات مرتبطة
    from apps.inventory.models import StockReservation

    content_type = ContentType.objects.get_for_model(SalesOrder)

    existing_reservations = StockReservation.objects.filter(
        reference_type=content_type,
        reference_id=instance.id,
        company=instance.company,
        status__in=['active', 'confirmed']
    ).exists()

    if existing_reservations:
        logger.info(f"Stock reservations already exist for SalesOrder {instance.number}")
        return

    # إنشاء حجوزات للمواد
    try:
        with transaction.atomic():
            created_count = 0

            for line in instance.lines.all():
                # تخطي إذا لم يكن هناك صنف
                if not line.item:
                    continue

                # تخطي إذا كانت الكمية صفر أو أقل
                if line.quantity <= 0:
                    continue

                # حساب الكمية المتبقية للحجز
                # (الكمية الكلية - المسلم - المفوتر)
                remaining_quantity = line.quantity - line.delivered_quantity - line.invoiced_quantity

                if remaining_quantity <= 0:
                    continue

                # الحصول على ItemStock للصنف في المستودع
                from apps.inventory.models import ItemStock

                item_stock = ItemStock.objects.filter(
                    company=instance.company,
                    warehouse=instance.warehouse,
                    item=line.item,
                    item_variant=getattr(line, 'item_variant', None) if hasattr(line, 'item_variant') else None
                ).first()

                if not item_stock:
                    logger.warning(f"No ItemStock found for {line.item.name} in {instance.warehouse.name}")
                    continue

                # إنشاء الحجز
                # تاريخ انتهاء الصلاحية: تاريخ التسليم المتوقع + 7 أيام
                expires_at = None
                if instance.delivery_date:
                    # Convert date to timezone-aware datetime
                    naive_dt = datetime.combine(instance.delivery_date, datetime.min.time())
                    expires_at = timezone.make_aware(naive_dt) + timedelta(days=7)

                reservation = StockReservation.objects.create(
                    company=instance.company,
                    item=line.item,
                    item_variant=getattr(line, 'item_variant', None) if hasattr(line, 'item_variant') else None,
                    warehouse=instance.warehouse,
                    item_stock=item_stock,
                    quantity=remaining_quantity,
                    reference_type=content_type,
                    reference_id=instance.id,
                    status='active',
                    reserved_by=instance.created_by,
                    expires_at=expires_at,
                    confirmed_at=timezone.now(),
                    notes=f'حجز تلقائي لأمر بيع {instance.number}',
                    created_by=instance.created_by
                )

                created_count += 1
                logger.info(f"Created reservation for {line.item.name}: {remaining_quantity} units")

            if created_count > 0:
                logger.info(f"Created {created_count} stock reservations for SalesOrder {instance.number}")

    except Exception as e:
        logger.error(f"Error creating stock reservations for SalesOrder {instance.number}: {str(e)}")
        # لا نرفع exception لعدم منع حفظ الأمر


@receiver(post_save, sender=SalesOrder)
def release_stock_reservation_on_order_completion(sender, instance, created, **kwargs):
    """
    تحرير المخزون المحجوز عند اكتمال أمر البيع

    يتم التشغيل عند:
    - تسليم الأمر بالكامل (is_delivered = True)
    - أو فوترة الأمر بالكامل (is_invoiced = True)
    """
    # تحرير الحجز فقط إذا اكتمل الأمر
    if not (instance.is_delivered or instance.is_invoiced):
        return

    # تحرير جميع الحجوزات النشطة المرتبطة بهذا الأمر
    from apps.inventory.models import StockReservation

    content_type = ContentType.objects.get_for_model(SalesOrder)

    try:
        reservations = StockReservation.objects.filter(
            reference_type=content_type,
            reference_id=instance.id,
            company=instance.company,
            status__in=['active', 'confirmed']
        )

        released_count = 0
        for reservation in reservations:
            reservation.status = 'released'
            reservation.released_at = timezone.now()
            reservation.save()
            released_count += 1

        if released_count > 0:
            logger.info(f"Released {released_count} stock reservations for SalesOrder {instance.number}")

    except Exception as e:
        logger.error(f"Error releasing stock reservations for SalesOrder {instance.number}: {str(e)}")


@receiver(post_delete, sender=SalesOrder)
def release_stock_reservation_on_order_deletion(sender, instance, **kwargs):
    """
    تحرير المخزون المحجوز عند حذف أمر البيع
    """
    from apps.inventory.models import StockReservation

    content_type = ContentType.objects.get_for_model(SalesOrder)

    try:
        reservations = StockReservation.objects.filter(
            reference_type=content_type,
            reference_id=instance.id,
            company=instance.company,
            status__in=['active', 'confirmed']
        )

        # حذف الحجوزات مباشرة
        deleted_count = reservations.count()
        reservations.delete()

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} stock reservations for deleted SalesOrder {instance.number}")

    except Exception as e:
        logger.error(f"Error deleting stock reservations for SalesOrder {instance.number}: {str(e)}")

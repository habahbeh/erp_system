# apps/inventory/services.py
"""
خدمات نظام المخزون
- نظام التنبيهات الآلي
- إدارة الحجز مع timeout
- التحقق من الدفعات المنتهية
"""

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# ==========================================
# نظام التنبيهات الآلي
# ==========================================

class InventoryAlertService:
    """خدمة تنبيهات المخزون"""

    # أنواع التنبيهات
    ALERT_TYPES = {
        'low_stock': _('انخفاض المخزون'),
        'reorder_point': _('نقطة إعادة الطلب'),
        'max_stock': _('تجاوز الحد الأقصى'),
        'expiring_soon': _('قرب انتهاء الصلاحية'),
        'expired': _('منتهي الصلاحية'),
        'negative_stock': _('مخزون سالب'),
    }

    @classmethod
    def check_stock_levels(cls, company, warehouse=None):
        """
        فحص مستويات المخزون وإنشاء التنبيهات

        Args:
            company: الشركة
            warehouse: المستودع (اختياري - إذا None يفحص كل المستودعات)

        Returns:
            list: قائمة التنبيهات
        """
        from .models import ItemStock

        alerts = []

        filters = {'company': company}
        if warehouse:
            filters['warehouse'] = warehouse

        stocks = ItemStock.objects.filter(**filters).select_related(
            'item', 'warehouse'
        )

        for stock in stocks:
            # فحص انخفاض المخزون
            if stock.is_below_min_level():
                alerts.append({
                    'type': 'low_stock',
                    'severity': 'high',
                    'item': stock.item,
                    'warehouse': stock.warehouse,
                    'current_qty': stock.quantity,
                    'min_level': stock.min_level,
                    'message': f'المادة {stock.item.name} أقل من الحد الأدنى ({stock.min_level}) في {stock.warehouse.name}'
                })

            # فحص نقطة إعادة الطلب
            elif stock.check_reorder_needed():
                alerts.append({
                    'type': 'reorder_point',
                    'severity': 'medium',
                    'item': stock.item,
                    'warehouse': stock.warehouse,
                    'current_qty': stock.quantity,
                    'reorder_point': stock.reorder_point,
                    'message': f'المادة {stock.item.name} وصلت لنقطة إعادة الطلب ({stock.reorder_point}) في {stock.warehouse.name}'
                })

            # فحص تجاوز الحد الأقصى
            if stock.is_above_max_level():
                alerts.append({
                    'type': 'max_stock',
                    'severity': 'low',
                    'item': stock.item,
                    'warehouse': stock.warehouse,
                    'current_qty': stock.quantity,
                    'max_level': stock.max_level,
                    'message': f'المادة {stock.item.name} تجاوزت الحد الأقصى ({stock.max_level}) في {stock.warehouse.name}'
                })

            # فحص المخزون السالب
            if stock.quantity < 0:
                alerts.append({
                    'type': 'negative_stock',
                    'severity': 'critical',
                    'item': stock.item,
                    'warehouse': stock.warehouse,
                    'current_qty': stock.quantity,
                    'message': f'المادة {stock.item.name} لها رصيد سالب ({stock.quantity}) في {stock.warehouse.name}'
                })

        return alerts

    @classmethod
    def check_batch_expiry(cls, company, days_threshold=30, warehouse=None):
        """
        فحص الدفعات القريبة من الانتهاء أو المنتهية

        Args:
            company: الشركة
            days_threshold: عدد الأيام للتحذير (افتراضي 30 يوم)
            warehouse: المستودع (اختياري)

        Returns:
            list: قائمة التنبيهات
        """
        from .models import Batch

        alerts = []
        today = timezone.now().date()
        warning_date = today + timedelta(days=days_threshold)

        filters = {
            'company': company,
            'quantity__gt': 0,
            'expiry_date__isnull': False
        }
        if warehouse:
            filters['warehouse'] = warehouse

        batches = Batch.objects.filter(**filters).select_related(
            'item', 'warehouse'
        )

        for batch in batches:
            if batch.is_expired():
                alerts.append({
                    'type': 'expired',
                    'severity': 'critical',
                    'item': batch.item,
                    'warehouse': batch.warehouse,
                    'batch_number': batch.batch_number,
                    'expiry_date': batch.expiry_date,
                    'quantity': batch.quantity,
                    'message': f'الدفعة {batch.batch_number} للمادة {batch.item.name} منتهية الصلاحية منذ {-batch.days_to_expiry()} يوم'
                })
            elif batch.expiry_date <= warning_date:
                days_left = batch.days_to_expiry()
                alerts.append({
                    'type': 'expiring_soon',
                    'severity': 'high' if days_left <= 7 else 'medium',
                    'item': batch.item,
                    'warehouse': batch.warehouse,
                    'batch_number': batch.batch_number,
                    'expiry_date': batch.expiry_date,
                    'days_left': days_left,
                    'quantity': batch.quantity,
                    'message': f'الدفعة {batch.batch_number} للمادة {batch.item.name} ستنتهي صلاحيتها خلال {days_left} يوم'
                })

        return alerts

    @classmethod
    def get_all_alerts(cls, company, warehouse=None, days_threshold=30):
        """
        الحصول على جميع التنبيهات

        Args:
            company: الشركة
            warehouse: المستودع (اختياري)
            days_threshold: عدد الأيام للتحذير من انتهاء الصلاحية

        Returns:
            dict: التنبيهات مصنفة حسب الخطورة
        """
        stock_alerts = cls.check_stock_levels(company, warehouse)
        expiry_alerts = cls.check_batch_expiry(company, days_threshold, warehouse)

        all_alerts = stock_alerts + expiry_alerts

        # تصنيف حسب الخطورة
        result = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'total_count': len(all_alerts)
        }

        for alert in all_alerts:
            severity = alert.get('severity', 'medium')
            result[severity].append(alert)

        return result

    @classmethod
    def get_alerts_summary(cls, company):
        """
        ملخص سريع للتنبيهات (للعرض في Dashboard)

        Returns:
            dict: ملخص التنبيهات
        """
        alerts = cls.get_all_alerts(company)

        return {
            'critical_count': len(alerts['critical']),
            'high_count': len(alerts['high']),
            'medium_count': len(alerts['medium']),
            'low_count': len(alerts['low']),
            'total_count': alerts['total_count'],
            'has_critical': len(alerts['critical']) > 0,
        }


# ==========================================
# نظام إدارة الحجز مع Timeout
# ==========================================

class ReservationService:
    """خدمة إدارة حجز المخزون مع timeout"""

    # مدة الحجز الافتراضية (بالدقائق)
    DEFAULT_TIMEOUT_MINUTES = 30

    @classmethod
    def reserve_stock(cls, item_stock, quantity, reference_type, reference_id,
                      timeout_minutes=None, user=None):
        """
        حجز كمية من المخزون مع timeout

        Args:
            item_stock: سجل رصيد المادة
            quantity: الكمية المراد حجزها
            reference_type: نوع المرجع (sales_order, etc.)
            reference_id: رقم المرجع
            timeout_minutes: مدة الحجز بالدقائق (اختياري)
            user: المستخدم

        Returns:
            StockReservation: سجل الحجز
        """
        from .models import StockReservation

        if timeout_minutes is None:
            timeout_minutes = cls.DEFAULT_TIMEOUT_MINUTES

        # التحقق من الكمية المتاحة
        available = item_stock.get_available_quantity()
        if available < quantity:
            raise ValidationError(
                f'الكمية المتاحة ({available}) أقل من المطلوب حجزها ({quantity})'
            )

        # حساب وقت انتهاء الحجز
        expires_at = timezone.now() + timedelta(minutes=timeout_minutes)

        with transaction.atomic():
            # إنشاء سجل الحجز
            reservation = StockReservation.objects.create(
                company=item_stock.company,
                item_stock=item_stock,
                item=item_stock.item,
                item_variant=item_stock.item_variant,
                warehouse=item_stock.warehouse,
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                reserved_by=user,
                expires_at=expires_at,
                status='active'
            )

            # تحديث الكمية المحجوزة
            item_stock.reserved_quantity += quantity
            item_stock.save(update_fields=['reserved_quantity'])

            logger.info(
                f'Reserved {quantity} of {item_stock.item.name} '
                f'for {reference_type}#{reference_id}, expires at {expires_at}'
            )

            return reservation

    @classmethod
    def release_reservation(cls, reservation, partial_quantity=None):
        """
        إلغاء حجز (كلي أو جزئي)

        Args:
            reservation: سجل الحجز
            partial_quantity: الكمية المراد إلغاؤها (اختياري - إذا None يلغي كل الحجز)
        """
        if reservation.status != 'active':
            raise ValidationError('الحجز غير نشط')

        quantity_to_release = partial_quantity or reservation.quantity

        if quantity_to_release > reservation.quantity:
            raise ValidationError('الكمية المراد إلغاؤها أكبر من المحجوز')

        with transaction.atomic():
            # تحديث الكمية المحجوزة
            item_stock = reservation.item_stock
            item_stock.reserved_quantity -= quantity_to_release
            item_stock.save(update_fields=['reserved_quantity'])

            if partial_quantity and partial_quantity < reservation.quantity:
                # إلغاء جزئي
                reservation.quantity -= quantity_to_release
                reservation.save(update_fields=['quantity'])
            else:
                # إلغاء كامل
                reservation.status = 'released'
                reservation.released_at = timezone.now()
                reservation.save(update_fields=['status', 'released_at'])

            logger.info(
                f'Released {quantity_to_release} from reservation #{reservation.pk}'
            )

    @classmethod
    def confirm_reservation(cls, reservation):
        """
        تأكيد الحجز (تحويله لإخراج فعلي)

        Args:
            reservation: سجل الحجز
        """
        if reservation.status != 'active':
            raise ValidationError('الحجز غير نشط')

        with transaction.atomic():
            reservation.status = 'confirmed'
            reservation.confirmed_at = timezone.now()
            reservation.save(update_fields=['status', 'confirmed_at'])

            # لا نلغي الحجز من reserved_quantity هنا
            # سيتم ذلك عند ترحيل سند الإخراج

            logger.info(f'Confirmed reservation #{reservation.pk}')

    @classmethod
    def cleanup_expired_reservations(cls, company=None):
        """
        تنظيف الحجوزات المنتهية

        Args:
            company: الشركة (اختياري - إذا None ينظف للكل)

        Returns:
            int: عدد الحجوزات التي تم إلغاؤها
        """
        from .models import StockReservation

        filters = {
            'status': 'active',
            'expires_at__lt': timezone.now()
        }
        if company:
            filters['company'] = company

        expired_reservations = StockReservation.objects.filter(**filters)
        count = 0

        for reservation in expired_reservations:
            try:
                cls.release_reservation(reservation)
                reservation.status = 'expired'
                reservation.save(update_fields=['status'])
                count += 1
                logger.info(
                    f'Auto-released expired reservation #{reservation.pk}'
                )
            except Exception as e:
                logger.error(
                    f'Failed to release expired reservation #{reservation.pk}: {e}'
                )

        return count

    @classmethod
    def extend_reservation(cls, reservation, additional_minutes=30):
        """
        تمديد فترة الحجز

        Args:
            reservation: سجل الحجز
            additional_minutes: دقائق إضافية

        Returns:
            datetime: وقت الانتهاء الجديد
        """
        if reservation.status != 'active':
            raise ValidationError('الحجز غير نشط')

        reservation.expires_at = timezone.now() + timedelta(minutes=additional_minutes)
        reservation.save(update_fields=['expires_at'])

        logger.info(
            f'Extended reservation #{reservation.pk} to {reservation.expires_at}'
        )

        return reservation.expires_at


# ==========================================
# خدمة التحقق من الدفعات
# ==========================================

class BatchValidationService:
    """خدمة التحقق من صلاحية الدفعات"""

    @classmethod
    def validate_batch_for_use(cls, batch, raise_on_expired=False, warn_days=30):
        """
        التحقق من صلاحية الدفعة للاستخدام

        Args:
            batch: الدفعة
            raise_on_expired: رفع خطأ إذا كانت منتهية (افتراضي False = تحذير فقط)
            warn_days: عدد أيام التحذير المسبق

        Returns:
            dict: نتيجة التحقق
        """
        result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }

        if not batch.expiry_date:
            return result

        status = batch.get_expiry_status()
        days_left = batch.days_to_expiry()

        if status == 'expired':
            message = f'الدفعة {batch.batch_number} منتهية الصلاحية منذ {-days_left} يوم'
            if raise_on_expired:
                result['valid'] = False
                result['errors'].append(message)
            else:
                result['warnings'].append(message)

        elif status == 'expiring_soon':
            result['warnings'].append(
                f'الدفعة {batch.batch_number} ستنتهي صلاحيتها خلال {days_left} يوم'
            )

        elif status == 'warning' and days_left <= warn_days:
            result['warnings'].append(
                f'الدفعة {batch.batch_number} ستنتهي صلاحيتها خلال {days_left} يوم'
            )

        return result

    @classmethod
    def get_valid_batches_fifo(cls, item, warehouse, company, quantity,
                                exclude_expired=True):
        """
        الحصول على الدفعات الصالحة بترتيب FIFO

        Args:
            item: المادة
            warehouse: المستودع
            company: الشركة
            quantity: الكمية المطلوبة
            exclude_expired: استبعاد الدفعات المنتهية

        Returns:
            list: قائمة الدفعات مع الكميات
        """
        from .models import Batch

        filters = {
            'item': item,
            'warehouse': warehouse,
            'company': company,
            'quantity__gt': 0
        }

        batches = Batch.objects.filter(**filters).order_by('received_date')

        if exclude_expired:
            today = timezone.now().date()
            batches = batches.exclude(expiry_date__lt=today)

        result = []
        remaining = quantity

        for batch in batches:
            if remaining <= 0:
                break

            available = batch.get_available_quantity()
            if available <= 0:
                continue

            take_qty = min(available, remaining)
            result.append({
                'batch': batch,
                'quantity': take_qty,
                'expiry_date': batch.expiry_date,
                'days_to_expiry': batch.days_to_expiry()
            })
            remaining -= take_qty

        return result, remaining

    @classmethod
    def get_valid_batches_fefo(cls, item, warehouse, company, quantity,
                                exclude_expired=True):
        """
        الحصول على الدفعات الصالحة بترتيب FEFO (First Expired First Out)

        Args:
            item: المادة
            warehouse: المستودع
            company: الشركة
            quantity: الكمية المطلوبة
            exclude_expired: استبعاد الدفعات المنتهية

        Returns:
            list: قائمة الدفعات مع الكميات
        """
        from .models import Batch
        from django.db.models import F
        from django.db.models.functions import Coalesce

        filters = {
            'item': item,
            'warehouse': warehouse,
            'company': company,
            'quantity__gt': 0
        }

        # ترتيب بتاريخ الانتهاء (الأقرب أولاً)، الدفعات بدون تاريخ انتهاء في النهاية
        batches = Batch.objects.filter(**filters).order_by(
            F('expiry_date').asc(nulls_last=True),
            'received_date'
        )

        if exclude_expired:
            today = timezone.now().date()
            batches = batches.exclude(expiry_date__lt=today)

        result = []
        remaining = quantity

        for batch in batches:
            if remaining <= 0:
                break

            available = batch.get_available_quantity()
            if available <= 0:
                continue

            take_qty = min(available, remaining)
            result.append({
                'batch': batch,
                'quantity': take_qty,
                'expiry_date': batch.expiry_date,
                'days_to_expiry': batch.days_to_expiry()
            })
            remaining -= take_qty

        return result, remaining

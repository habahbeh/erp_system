# apps/inventory/cache.py
"""
نظام التخزين المؤقت (Caching) لتحسين أداء نظام المخزون
"""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
import hashlib


# ==========================================
# Cache Keys
# ==========================================

def _get_stock_cache_key(company_id, item_id, warehouse_id=None, variant_id=None):
    """توليد مفتاح cache لرصيد المادة"""
    parts = [f'stock_{company_id}_{item_id}']
    if warehouse_id:
        parts.append(str(warehouse_id))
    if variant_id:
        parts.append(str(variant_id))
    return '_'.join(parts)


def _get_total_stock_cache_key(company_id, item_id, variant_id=None):
    """توليد مفتاح cache لإجمالي رصيد المادة"""
    key = f'total_stock_{company_id}_{item_id}'
    if variant_id:
        key += f'_{variant_id}'
    return key


def _get_alerts_cache_key(company_id, warehouse_id=None):
    """توليد مفتاح cache للتنبيهات"""
    key = f'inv_alerts_{company_id}'
    if warehouse_id:
        key += f'_{warehouse_id}'
    return key


# ==========================================
# Cache Service
# ==========================================

class InventoryCacheService:
    """خدمة التخزين المؤقت للمخزون"""

    # مدة الـ cache بالثواني
    STOCK_CACHE_TTL = 300  # 5 دقائق
    ALERTS_CACHE_TTL = 600  # 10 دقائق
    REPORT_CACHE_TTL = 1800  # 30 دقيقة

    @classmethod
    def get_item_stock(cls, company_id, item_id, warehouse_id, variant_id=None):
        """
        الحصول على رصيد المادة مع caching

        Args:
            company_id: رقم الشركة
            item_id: رقم المادة
            warehouse_id: رقم المستودع
            variant_id: رقم المتغير (اختياري)

        Returns:
            dict: بيانات الرصيد أو None
        """
        cache_key = _get_stock_cache_key(company_id, item_id, warehouse_id, variant_id)

        # محاولة الحصول من cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # الحصول من قاعدة البيانات
        from .models import ItemStock

        filters = {
            'company_id': company_id,
            'item_id': item_id,
            'warehouse_id': warehouse_id,
        }
        if variant_id:
            filters['item_variant_id'] = variant_id
        else:
            filters['item_variant__isnull'] = True

        try:
            stock = ItemStock.objects.get(**filters)
            data = {
                'id': stock.id,
                'quantity': float(stock.quantity),
                'reserved_quantity': float(stock.reserved_quantity),
                'available_quantity': float(stock.get_available_quantity()),
                'average_cost': float(stock.average_cost),
                'total_value': float(stock.total_value),
                'min_level': float(stock.min_level) if stock.min_level else None,
                'max_level': float(stock.max_level) if stock.max_level else None,
                'reorder_point': float(stock.reorder_point) if stock.reorder_point else None,
                'is_below_min': stock.is_below_min_level(),
                'needs_reorder': stock.check_reorder_needed(),
                'is_above_max': stock.is_above_max_level(),
            }
        except ItemStock.DoesNotExist:
            data = None

        # حفظ في cache
        cache.set(cache_key, data, cls.STOCK_CACHE_TTL)

        return data

    @classmethod
    def get_total_stock(cls, company_id, item_id, variant_id=None):
        """
        الحصول على إجمالي رصيد المادة في كل المستودعات مع caching

        Args:
            company_id: رقم الشركة
            item_id: رقم المادة
            variant_id: رقم المتغير (اختياري)

        Returns:
            dict: إجمالي الرصيد
        """
        cache_key = _get_total_stock_cache_key(company_id, item_id, variant_id)

        # محاولة الحصول من cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # الحصول من قاعدة البيانات
        from .models import ItemStock
        from apps.core.models import Item

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return None

        data = ItemStock.get_total_stock(
            item=item,
            item_variant_id=variant_id,
            company_id=company_id
        )

        # تحويل Decimal لـ float للـ cache
        data = {k: float(v) if isinstance(v, Decimal) else v for k, v in data.items()}

        # حفظ في cache
        cache.set(cache_key, data, cls.STOCK_CACHE_TTL)

        return data

    @classmethod
    def get_alerts_summary(cls, company_id, warehouse_id=None):
        """
        الحصول على ملخص التنبيهات مع caching

        Args:
            company_id: رقم الشركة
            warehouse_id: رقم المستودع (اختياري)

        Returns:
            dict: ملخص التنبيهات
        """
        cache_key = _get_alerts_cache_key(company_id, warehouse_id)

        # محاولة الحصول من cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # الحصول من الخدمة
        from .services import InventoryAlertService
        from apps.core.models import Company, Warehouse

        company = Company.objects.get(pk=company_id)
        warehouse = Warehouse.objects.get(pk=warehouse_id) if warehouse_id else None

        data = InventoryAlertService.get_alerts_summary(company)

        # حفظ في cache
        cache.set(cache_key, data, cls.ALERTS_CACHE_TTL)

        return data

    @classmethod
    def invalidate_stock_cache(cls, company_id, item_id, warehouse_id=None, variant_id=None):
        """
        إبطال cache الرصيد عند التغيير

        Args:
            company_id: رقم الشركة
            item_id: رقم المادة
            warehouse_id: رقم المستودع (اختياري)
            variant_id: رقم المتغير (اختياري)
        """
        # إبطال cache الرصيد المحدد
        if warehouse_id:
            cache_key = _get_stock_cache_key(company_id, item_id, warehouse_id, variant_id)
            cache.delete(cache_key)

        # إبطال cache الإجمالي
        total_key = _get_total_stock_cache_key(company_id, item_id, variant_id)
        cache.delete(total_key)

        # إبطال cache التنبيهات
        alerts_key = _get_alerts_cache_key(company_id, warehouse_id)
        cache.delete(alerts_key)
        # إبطال cache التنبيهات العامة للشركة
        cache.delete(_get_alerts_cache_key(company_id))

    @classmethod
    def invalidate_all_stock_cache(cls, company_id=None):
        """
        إبطال كل cache المخزون

        Args:
            company_id: رقم الشركة (اختياري - إذا None يبطل للكل)
        """
        # استخدام pattern matching إذا كان cache backend يدعمه
        # أو مسح كل الـ cache
        try:
            if hasattr(cache, 'delete_pattern'):
                if company_id:
                    cache.delete_pattern(f'stock_{company_id}_*')
                    cache.delete_pattern(f'total_stock_{company_id}_*')
                    cache.delete_pattern(f'inv_alerts_{company_id}*')
                else:
                    cache.delete_pattern('stock_*')
                    cache.delete_pattern('total_stock_*')
                    cache.delete_pattern('inv_alerts_*')
        except AttributeError:
            # cache backend لا يدعم pattern matching
            # في هذه الحالة نعتمد على TTL
            pass


# ==========================================
# Cache Signals
# ==========================================

@receiver(post_save, sender='inventory.ItemStock')
def invalidate_item_stock_cache_on_save(sender, instance, **kwargs):
    """إبطال cache عند حفظ ItemStock"""
    InventoryCacheService.invalidate_stock_cache(
        company_id=instance.company_id,
        item_id=instance.item_id,
        warehouse_id=instance.warehouse_id,
        variant_id=instance.item_variant_id
    )


@receiver(post_delete, sender='inventory.ItemStock')
def invalidate_item_stock_cache_on_delete(sender, instance, **kwargs):
    """إبطال cache عند حذف ItemStock"""
    InventoryCacheService.invalidate_stock_cache(
        company_id=instance.company_id,
        item_id=instance.item_id,
        warehouse_id=instance.warehouse_id,
        variant_id=instance.item_variant_id
    )


@receiver(post_save, sender='inventory.StockMovement')
def invalidate_cache_on_movement(sender, instance, **kwargs):
    """إبطال cache عند إنشاء حركة مخزون"""
    InventoryCacheService.invalidate_stock_cache(
        company_id=instance.company_id,
        item_id=instance.item_id,
        warehouse_id=instance.warehouse_id,
        variant_id=instance.item_variant_id if hasattr(instance, 'item_variant_id') else None
    )


# ==========================================
# Query Optimization Helpers
# ==========================================

def get_optimized_stock_queryset(company, warehouse=None, with_item=True, with_warehouse=True):
    """
    الحصول على queryset محسن للأرصدة

    Args:
        company: الشركة
        warehouse: المستودع (اختياري)
        with_item: تضمين المادة (select_related)
        with_warehouse: تضمين المستودع (select_related)

    Returns:
        QuerySet: queryset محسن
    """
    from .models import ItemStock

    queryset = ItemStock.objects.filter(company=company)

    if warehouse:
        queryset = queryset.filter(warehouse=warehouse)

    select_related_fields = []
    if with_item:
        select_related_fields.extend(['item', 'item__category'])
    if with_warehouse:
        select_related_fields.append('warehouse')

    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)

    return queryset


def get_optimized_movements_queryset(company, item=None, warehouse=None,
                                      date_from=None, date_to=None):
    """
    الحصول على queryset محسن للحركات

    Args:
        company: الشركة
        item: المادة (اختياري)
        warehouse: المستودع (اختياري)
        date_from: من تاريخ (اختياري)
        date_to: إلى تاريخ (اختياري)

    Returns:
        QuerySet: queryset محسن
    """
    from .models import StockMovement

    queryset = StockMovement.objects.filter(company=company)

    if item:
        queryset = queryset.filter(item=item)
    if warehouse:
        queryset = queryset.filter(warehouse=warehouse)
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)

    queryset = queryset.select_related(
        'item', 'warehouse', 'created_by'
    ).order_by('-date')

    return queryset

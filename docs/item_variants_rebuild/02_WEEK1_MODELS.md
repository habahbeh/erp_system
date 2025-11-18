# 🏗️ Week 1 - Django Models

## 🎯 الهدف
بناء Django Models للنظام الجديد مع Managers و QuerySets محسّنة

---

## 📁 هيكلة الملفات

```
apps/core/models/
├── __init__.py (updated)
├── base_models.py (موجود)
├── company_models.py (موجود)
├── item_models.py (موجود - سنعدله)
├── uom_models.py (✨ جديد)
├── pricing_models.py (✨ جديد)
├── template_models.py (✨ جديد)
└── audit_models.py (✨ جديد)
```

---

## 📄 ملف: `uom_models.py`

```python
"""
وحدات القياس ونظام التحويلات
Unit of Measure System
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .base_models import BaseModel


class UnitOfMeasure(BaseModel):
    """وحدات القياس"""

    UOM_TYPE_CHOICES = [
        ('UNIT', _('وحدة')),
        ('WEIGHT', _('وزن')),
        ('LENGTH', _('طول')),
        ('VOLUME', _('حجم')),
        ('AREA', _('مساحة')),
        ('TIME', _('وقت')),
    ]

    # معلومات أساسية
    name = models.CharField(_('الاسم'), max_length=50)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=50, blank=True)
    code = models.CharField(_('الرمز'), max_length=20, unique=True)
    symbol = models.CharField(_('الرمز المختصر'), max_length=10, blank=True)

    # التصنيف
    uom_type = models.CharField(
        _('نوع الوحدة'),
        max_length=10,
        choices=UOM_TYPE_CHOICES,
        default='UNIT'
    )
    category = models.CharField(_('الفئة'), max_length=50, blank=True)

    # الدقة
    rounding_precision = models.DecimalField(
        _('دقة التقريب'),
        max_digits=10,
        decimal_places=6,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.000001'))]
    )

    class Meta:
        verbose_name = _('وحدة قياس')
        verbose_name_plural = _('وحدات القياس')
        ordering = ['uom_type', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['uom_type']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol or self.code})"

    def round_quantity(self, quantity):
        """تقريب الكمية حسب دقة الوحدة"""
        if self.rounding_precision:
            return (Decimal(str(quantity)) / self.rounding_precision).quantize(
                Decimal('1')
            ) * self.rounding_precision
        return Decimal(str(quantity))


class UoMConversion(BaseModel):
    """تحويلات وحدات القياس"""

    # ربط بالمادة أو المتغير
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='uom_conversions',
        verbose_name=_('المادة'),
        null=True,
        blank=True
    )
    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        related_name='uom_conversions',
        verbose_name=_('المتغير'),
        null=True,
        blank=True
    )

    # التحويل
    from_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='conversions_from',
        verbose_name=_('من الوحدة')
    )
    to_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='conversions_to',
        verbose_name=_('إلى الوحدة')
    )
    conversion_factor = models.DecimalField(
        _('معامل التحويل'),
        max_digits=20,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text=_('عدد وحدات to_uom في from_uom واحدة')
    )

    # الاستخدام
    is_default_purchase_uom = models.BooleanField(
        _('وحدة الشراء الافتراضية'),
        default=False
    )
    is_default_sale_uom = models.BooleanField(
        _('وحدة البيع الافتراضية'),
        default=False
    )

    class Meta:
        verbose_name = _('تحويل وحدة قياس')
        verbose_name_plural = _('تحويلات وحدات القياس')
        unique_together = [['item', 'variant', 'from_uom', 'to_uom']]
        indexes = [
            models.Index(fields=['item', 'from_uom']),
            models.Index(fields=['variant', 'from_uom']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(item__isnull=False) |
                    models.Q(variant__isnull=False)
                ),
                name='uom_conversion_requires_item_or_variant'
            ),
        ]

    def __str__(self):
        target = self.variant or self.item
        return f"{target}: 1 {self.from_uom.name} = {self.conversion_factor} {self.to_uom.name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        # التحقق من وجود item أو variant
        if not self.item and not self.variant:
            raise ValidationError(_('يجب تحديد المادة أو المتغير'))

        # التحقق من عدم التحويل إلى نفس الوحدة
        if self.from_uom == self.to_uom:
            raise ValidationError(_('لا يمكن التحويل إلى نفس الوحدة'))

    def convert(self, quantity):
        """تحويل كمية من from_uom إلى to_uom"""
        return Decimal(str(quantity)) * self.conversion_factor

    def reverse_convert(self, quantity):
        """تحويل كمية من to_uom إلى from_uom"""
        return Decimal(str(quantity)) / self.conversion_factor
```

---

## 📄 ملف: `pricing_models.py`

```python
"""
نظام التسعير المتقدم
Advanced Pricing System
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import json

from .base_models import BaseModel


class PricingRule(BaseModel):
    """قواعد التسعير الديناميكية"""

    RULE_TYPE_CHOICES = [
        ('DISCOUNT_PERCENTAGE', _('خصم بالنسبة المئوية')),
        ('DISCOUNT_FIXED', _('خصم ثابت')),
        ('PRICE_FORMULA', _('صيغة تسعير')),
        ('BULK_DISCOUNT', _('خصم الكميات')),
    ]

    APPLIES_TO_CHOICES = [
        ('ALL', _('الكل')),
        ('CATEGORY', _('تصنيف')),
        ('ITEM', _('مادة')),
        ('VARIANT', _('متغير')),
    ]

    # معلومات أساسية
    name = models.CharField(_('الاسم'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)

    # نوع القاعدة
    rule_type = models.CharField(
        _('نوع القاعدة'),
        max_length=20,
        choices=RULE_TYPE_CHOICES
    )

    # التطبيق على
    applies_to = models.CharField(
        _('يطبق على'),
        max_length=10,
        choices=APPLIES_TO_CHOICES
    )
    category = models.ForeignKey(
        'ItemCategory',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('التصنيف')
    )
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('المادة')
    )
    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('المتغير')
    )

    # قائمة الأسعار
    price_list = models.ForeignKey(
        'PriceList',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('قائمة الأسعار')
    )

    # شروط الكمية
    min_quantity = models.DecimalField(
        _('الحد الأدنى للكمية'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )
    max_quantity = models.DecimalField(
        _('الحد الأقصى للكمية'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    # الخصم
    discount_percentage = models.DecimalField(
        _('نسبة الخصم %'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fixed_discount_amount = models.DecimalField(
        _('مبلغ الخصم الثابت'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    # الصيغة (JSON)
    formula = models.JSONField(
        _('صيغة التسعير'),
        null=True,
        blank=True,
        help_text=_('مثال: {"base": "cost", "multiplier": 1.5, "min_profit": 0.2}')
    )

    # الأولوية
    priority = models.IntegerField(
        _('الأولوية'),
        default=0,
        help_text=_('الأعلى يطبق أولاً')
    )

    # الصلاحية
    valid_from = models.DateField(_('صالح من'), null=True, blank=True)
    valid_to = models.DateField(_('صالح حتى'), null=True, blank=True)

    class Meta:
        verbose_name = _('قاعدة تسعير')
        verbose_name_plural = _('قواعد التسعير')
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active', 'priority']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['rule_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"

    def applies_to_variant(self, variant):
        """هل تنطبق القاعدة على هذا المتغير؟"""
        if self.applies_to == 'ALL':
            return True
        elif self.applies_to == 'VARIANT':
            return self.variant == variant
        elif self.applies_to == 'ITEM':
            return self.item == variant.item
        elif self.applies_to == 'CATEGORY':
            return self.category == variant.item.category
        return False

    def calculate_price(self, base_price, quantity=1, cost_price=None):
        """حساب السعر بناءً على القاعدة"""
        price = Decimal(str(base_price))

        # التحقق من شرط الكمية
        if self.min_quantity and Decimal(str(quantity)) < self.min_quantity:
            return price
        if self.max_quantity and Decimal(str(quantity)) > self.max_quantity:
            return price

        if self.rule_type == 'DISCOUNT_PERCENTAGE':
            price *= (1 - self.discount_percentage / 100)

        elif self.rule_type == 'DISCOUNT_FIXED':
            price -= self.fixed_discount_amount

        elif self.rule_type == 'PRICE_FORMULA' and self.formula:
            price = self._apply_formula(cost_price or price)

        return max(price, Decimal('0'))

    def _apply_formula(self, cost_price):
        """تطبيق صيغة التسعير"""
        if not self.formula:
            return cost_price

        cost = Decimal(str(cost_price))
        multiplier = Decimal(str(self.formula.get('multiplier', 1)))
        min_profit = Decimal(str(self.formula.get('min_profit', 0)))

        calculated_price = cost * multiplier

        # التأكد من الحد الأدنى للربح
        if min_profit:
            min_price = cost * (1 + min_profit)
            calculated_price = max(calculated_price, min_price)

        return calculated_price


class PriceHistory(models.Model):
    """تاريخ تغيرات الأسعار"""

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )
    price_list_item = models.ForeignKey(
        'PriceListItem',
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('السعر')
    )

    # التغيير
    old_price = models.DecimalField(
        _('السعر القديم'),
        max_digits=20,
        decimal_places=3,
        null=True
    )
    new_price = models.DecimalField(
        _('السعر الجديد'),
        max_digits=20,
        decimal_places=3
    )
    change_percentage = models.DecimalField(
        _('نسبة التغيير %'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # السبب
    reason = models.CharField(_('السبب'), max_length=255, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    # من قام بالتعديل
    changed_by = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        verbose_name=_('عُدل بواسطة')
    )
    changed_at = models.DateTimeField(_('تاريخ التعديل'), auto_now_add=True)

    # معلومات إضافية
    old_data = models.JSONField(_('البيانات القديمة'), null=True, blank=True)
    new_data = models.JSONField(_('البيانات الجديدة'), null=True, blank=True)

    class Meta:
        verbose_name = _('سجل تغيير السعر')
        verbose_name_plural = _('سجل تغييرات الأسعار')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['price_list_item', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
        ]

    def __str__(self):
        return f"{self.price_list_item}: {self.old_price} → {self.new_price}"

    def save(self, *args, **kwargs):
        # حساب نسبة التغيير
        if self.old_price and self.new_price and self.old_price > 0:
            self.change_percentage = (
                (self.new_price - self.old_price) / self.old_price * 100
            )
        super().save(*args, **kwargs)


class VariantLifecycleEvent(models.Model):
    """سجل أحداث المتغيرات"""

    EVENT_TYPE_CHOICES = [
        ('CREATED', _('تم الإنشاء')),
        ('ACTIVATED', _('تم التفعيل')),
        ('DEACTIVATED', _('تم التعطيل')),
        ('DISCONTINUED', _('تم الإيقاف')),
        ('PRICE_CHANGED', _('تغيير السعر')),
        ('STOCK_ADJUSTED', _('تعديل المخزون')),
        ('ATTRIBUTE_CHANGED', _('تغيير الخصائص')),
    ]

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )
    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        related_name='lifecycle_events',
        verbose_name=_('المتغير')
    )

    # نوع الحدث
    event_type = models.CharField(
        _('نوع الحدث'),
        max_length=20,
        choices=EVENT_TYPE_CHOICES
    )

    # التفاصيل
    old_value = models.JSONField(_('القيمة القديمة'), null=True, blank=True)
    new_value = models.JSONField(_('القيمة الجديدة'), null=True, blank=True)
    change_summary = models.TextField(_('ملخص التغيير'), blank=True)

    # من قام بالحدث
    user = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المستخدم')
    )
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)

    # التوقيت
    created_at = models.DateTimeField(_('التاريخ'), auto_now_add=True)

    class Meta:
        verbose_name = _('حدث متغير')
        verbose_name_plural = _('أحداث المتغيرات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['variant', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.variant}: {self.get_event_type_display()}"
```

---

## 📄 ملف: `template_models.py`

```python
"""
قوالب المواد ونظام الاستيراد الجماعي
Templates & Bulk Import System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .base_models import BaseModel


class ItemTemplate(BaseModel):
    """قوالب المواد"""

    # معلومات القالب
    name = models.CharField(_('الاسم'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    category = models.ForeignKey(
        'ItemCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('التصنيف')
    )

    # البيانات
    template_data = models.JSONField(
        _('بيانات القالب'),
        help_text=_('البنية الكاملة للمادة والمتغيرات والأسعار')
    )

    # الاستخدام
    usage_count = models.IntegerField(_('عدد مرات الاستخدام'), default=0)
    last_used_at = models.DateTimeField(_('آخر استخدام'), null=True, blank=True)

    # الحالة
    is_public = models.BooleanField(
        _('عام'),
        default=False,
        help_text=_('متاح لجميع المستخدمين')
    )

    class Meta:
        verbose_name = _('قالب مادة')
        verbose_name_plural = _('قوالب المواد')
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.name

    def use(self):
        """تسجيل استخدام القالب"""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])

    def get_structure(self):
        """الحصول على البنية بشكل مقروء"""
        data = self.template_data
        return {
            'item': data.get('item', {}),
            'variants_count': len(data.get('variants', [])),
            'has_uom': len(data.get('uom_conversions', [])) > 0,
            'has_prices': len(data.get('prices', [])) > 0,
        }


class BulkImportJob(models.Model):
    """سجل عمليات الاستيراد الجماعي"""

    IMPORT_TYPE_CHOICES = [
        ('SIMPLE_ITEMS', _('مواد بسيطة')),
        ('ITEMS_WITH_VARIANTS', _('مواد بمتغيرات')),
        ('VARIANTS_ONLY', _('متغيرات فقط')),
        ('PRICES_ONLY', _('أسعار فقط')),
        ('UOM_CONVERSIONS', _('تحويلات وحدات')),
    ]

    STATUS_CHOICES = [
        ('PENDING', _('قيد الانتظار')),
        ('PROCESSING', _('قيد المعالجة')),
        ('COMPLETED', _('مكتمل')),
        ('FAILED', _('فشل')),
        ('PARTIALLY_COMPLETED', _('مكتمل جزئياً')),
    ]

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    # معلومات الملف
    filename = models.CharField(_('اسم الملف'), max_length=255)
    file_path = models.CharField(_('مسار الملف'), max_length=500, blank=True)
    file_size_kb = models.IntegerField(_('حجم الملف (كيلوبايت)'), null=True, blank=True)

    # نوع الاستيراد
    import_type = models.CharField(
        _('نوع الاستيراد'),
        max_length=25,
        choices=IMPORT_TYPE_CHOICES
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # الإحصائيات
    total_rows = models.IntegerField(_('إجمالي الصفوف'), default=0)
    processed_rows = models.IntegerField(_('الصفوف المعالجة'), default=0)
    success_count = models.IntegerField(_('عدد النجاحات'), default=0)
    error_count = models.IntegerField(_('عدد الأخطاء'), default=0)
    warning_count = models.IntegerField(_('عدد التحذيرات'), default=0)

    # السجلات
    error_log = models.JSONField(_('سجل الأخطاء'), null=True, blank=True)
    warning_log = models.JSONField(_('سجل التحذيرات'), null=True, blank=True)
    processing_log = models.JSONField(_('سجل المعالجة'), null=True, blank=True)

    # التوقيت
    started_at = models.DateTimeField(_('بدء المعالجة'), null=True, blank=True)
    completed_at = models.DateTimeField(_('انتهاء المعالجة'), null=True, blank=True)
    processing_time_seconds = models.IntegerField(_('وقت المعالجة (ثانية)'), null=True, blank=True)

    # من قام بالاستيراد
    created_by = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        verbose_name=_('أنشئ بواسطة')
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('عملية استيراد جماعي')
        verbose_name_plural = _('عمليات الاستيراد الجماعي')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]

    def __str__(self):
        return f"{self.filename} ({self.get_status_display()})"

    def start_processing(self):
        """بدء المعالجة"""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def complete(self):
        """إكمال المعالجة"""
        self.completed_at = timezone.now()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.processing_time_seconds = int(delta.total_seconds())

        if self.error_count == 0:
            self.status = 'COMPLETED'
        elif self.success_count > 0:
            self.status = 'PARTIALLY_COMPLETED'
        else:
            self.status = 'FAILED'

        self.save(update_fields=['completed_at', 'processing_time_seconds', 'status'])

    def get_success_rate(self):
        """نسبة النجاح"""
        if self.processed_rows == 0:
            return 0
        return (self.success_count / self.processed_rows) * 100
```

---

## 📄 تعديلات على `item_models.py`

```python
# إضافة حقول جديدة إلى Item

class Item(BaseModel):
    # ... الحقول الموجودة ...

    # ⭐ إضافة وحدة القياس الأساسية
    base_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='items_using_as_base',
        verbose_name=_('الوحدة الأساسية'),
        null=True,  # للتوافق مع البيانات الموجودة
        blank=True
    )

    # ⭐ خصائص إضافية
    is_stockable = models.BooleanField(_('قابل للتخزين'), default=True)
    track_serial_numbers = models.BooleanField(_('تتبع الأرقام التسلسلية'), default=False)
    track_batches = models.BooleanField(_('تتبع الدفعات'), default=False)

    # ⭐ التسعير
    default_purchase_price = models.DecimalField(
        _('سعر الشراء الافتراضي'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )
    last_purchase_price = models.DecimalField(
        _('آخر سعر شراء'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    # ⭐ الحالة المحسنة
    is_discontinued = models.BooleanField(_('متوقف'), default=False)
    discontinued_date = models.DateField(_('تاريخ الإيقاف'), null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=['is_stockable', 'is_active']),
            models.Index(fields=['is_discontinued']),
        ]


# تعديلات على ItemVariant

class ItemVariant(BaseModel):
    # ... الحقول الموجودة ...

    # ⭐ معلومات مالية محسّنة
    cost_price = models.DecimalField(
        _('سعر التكلفة'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('تكلفة الإنتاج/الشراء')
    )
    default_sale_price = models.DecimalField(
        _('السعر الأساسي'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )
    last_purchase_price = models.DecimalField(
        _('آخر سعر شراء'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )
    average_cost = models.DecimalField(
        _('متوسط التكلفة'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    # ⭐ الأبعاد المحسنة
    volume = models.DecimalField(
        _('الحجم'),
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True
    )
    volume_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='variants_volume',
        verbose_name=_('وحدة الحجم'),
        null=True,
        blank=True
    )

    # ⭐ الحالة المحسنة
    is_discontinued = models.BooleanField(_('متوقف'), default=False)
    discontinued_date = models.DateField(_('تاريخ الإيقاف'), null=True, blank=True)
    replacement_variant = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaced_by',
        verbose_name=_('البديل')
    )

    # ⭐ صورة مخصصة
    image_url = models.URLField(_('رابط الصورة'), max_length=500, blank=True)

    class Meta(BaseModel.Meta):
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=['is_active', 'is_discontinued']),
            models.Index(fields=['code']),  # SKU
        ]

    def discontinue(self, replacement=None, reason=''):
        """إيقاف المتغير"""
        from django.utils import timezone

        self.is_discontinued = True
        self.discontinued_date = timezone.now().date()
        self.replacement_variant = replacement
        self.save()

        # تسجيل الحدث
        VariantLifecycleEvent.objects.create(
            company=self.company,
            variant=self,
            event_type='DISCONTINUED',
            new_value={
                'discontinued_date': str(self.discontinued_date),
                'replacement': replacement.code if replacement else None,
                'reason': reason
            }
        )

    def get_price_for_list(self, price_list, uom=None, quantity=1):
        """الحصول على السعر لقائمة معينة"""
        # سيتم تنفيذه في Pricing Engine
        pass
```

---

## 📄 تعديلات على `price_list_items` (في PriceList models)

```python
class PriceListItem(BaseModel):
    # ... الحقول الموجودة ...

    # ⭐ إضافة وحدة القياس
    uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='price_list_items',
        verbose_name=_('وحدة القياس'),
        null=True,  # للتوافق
        blank=True
    )

    # ⭐ شروط الكمية
    min_quantity = models.DecimalField(
        _('الحد الأدنى للكمية'),
        max_digits=20,
        decimal_places=3,
        default=Decimal('1')
    )
    max_quantity = models.DecimalField(
        _('الحد الأقصى للكمية'),
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    # ⭐ الصلاحية
    valid_from = models.DateField(_('صالح من'), null=True, blank=True)
    valid_to = models.DateField(_('صالح حتى'), null=True, blank=True)

    class Meta:
        unique_together = [['price_list', 'item', 'variant', 'uom', 'min_quantity']]
        indexes = [
            models.Index(fields=['uom', 'price_list']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def save(self, *args, **kwargs):
        # تسجيل في التاريخ عند التعديل
        if self.pk:
            old_instance = PriceListItem.objects.get(pk=self.pk)
            if old_instance.price != self.price:
                PriceHistory.objects.create(
                    company=self.company,
                    price_list_item=self,
                    old_price=old_instance.price,
                    new_price=self.price,
                    changed_by=self.updated_by or self.created_by
                )

        super().save(*args, **kwargs)
```

---

## ✅ Checklist

- [ ] إنشاء `uom_models.py`
- [ ] إنشاء `pricing_models.py`
- [ ] إنشاء `template_models.py`
- [ ] تعديل `item_models.py`
- [ ] تحديث `__init__.py`
- [ ] كتابة Managers مخصصة
- [ ] كتابة QuerySets محسنة
- [ ] Testing للـ Models

---

**التالي:** تطبيق الكود الفعلي + Migration files

**الحالة:** 📝 Documentation جاهز
**آخر تحديث:** 2025-01-18

# apps/core/models/pricing_models.py
"""
نماذج التسعير - Pricing System
- PriceList: قوائم الأسعار
- PriceListItem: الأسعار (variant × uom × price_list) - محدّث
- PricingRule: قواعد التسعير الديناميكية (NEW)
- PriceHistory: تاريخ تغييرات الأسعار (NEW)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from .base_models import BaseModel


class PriceList(BaseModel):
    """قوائم الأسعار - مثل: جملة، تجزئة، VIP"""

    name = models.CharField(_('اسم القائمة'), max_length=100)
    code = models.CharField(_('رمز القائمة'), max_length=20)
    description = models.TextField(_('الوصف'), blank=True)
    is_default = models.BooleanField(_('قائمة افتراضية'), default=False)
    currency = models.ForeignKey(
        'Currency',
        on_delete=models.PROTECT,
        verbose_name=_('العملة'),
        related_name='price_lists'
    )

    class Meta:
        verbose_name = _('قائمة أسعار')
        verbose_name_plural = _('قوائم الأسعار')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def save(self, *args, **kwargs):
        """تأكد من وجود قائمة افتراضية واحدة فقط"""
        if self.is_default:
            PriceList.objects.filter(
                company=self.company,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class PriceListItem(models.Model):
    """
    أسعار المواد في كل قائمة

    ⭐ KEY CHANGE: الآن يتضمن UoM
    التسعير = variant × uom × price_list
    """

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('قائمة الأسعار')
    )
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='price_list_items',
        verbose_name=_('المادة')
    )
    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='price_list_items',
        verbose_name=_('المتغير')
    )

    # ⭐ NEW: UoM في التسعير
    uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='price_list_items',
        verbose_name=_('وحدة القياس'),
        help_text=_('السعر لهذه الوحدة. فارغ = الوحدة الأساسية')
    )

    price = models.DecimalField(
        _('السعر'),
        max_digits=15,
        decimal_places=3
    )
    min_quantity = models.DecimalField(
        _('الكمية الأدنى'),
        max_digits=10,
        decimal_places=3,
        default=1,
        help_text=_('السعر يطبق من هذه الكمية فما فوق')
    )
    start_date = models.DateField(
        _('تاريخ البداية'),
        null=True,
        blank=True
    )
    end_date = models.DateField(
        _('تاريخ النهاية'),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('سعر مادة')
        verbose_name_plural = _('أسعار المواد')
        # ⭐ KEY CHANGE: unique constraint الآن يشمل UoM
        unique_together = [['price_list', 'item', 'variant', 'uom', 'min_quantity']]
        ordering = ['item__name', 'variant__code', 'uom__name']
        indexes = [
            models.Index(fields=['price_list', 'item']),
            models.Index(fields=['is_active', 'start_date', 'end_date']),
            models.Index(fields=['item', 'variant', 'uom']),
        ]

    def clean(self):
        """التحقق من صحة البيانات"""
        from django.core.exceptions import ValidationError

        # إذا كان المادة له متغيرات، يجب تحديد متغير
        if self.item.has_variants and not self.variant:
            raise ValidationError(
                _('يجب تحديد متغير للمادة التي لها متغيرات')
            )

        # إذا كان المادة بدون متغيرات، لا يجب تحديد متغير
        if not self.item.has_variants and self.variant:
            raise ValidationError(
                _('لا يمكن تحديد متغير لمادة بدون متغيرات')
            )

        # التحقق من تواريخ الصلاحية
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                )

    def is_valid_date(self, check_date=None):
        """التحقق من صلاحية السعر في تاريخ معين"""
        from django.utils import timezone

        if not check_date:
            check_date = timezone.now().date()

        if not self.is_active:
            return False

        if self.start_date and check_date < self.start_date:
            return False

        if self.end_date and check_date > self.end_date:
            return False

        return True

    def __str__(self):
        variant_str = f" - {self.variant.code}" if self.variant else ""
        uom_str = f" ({self.uom.code})" if self.uom else ""
        return f"{self.price_list.name}: {self.item.name}{variant_str}{uom_str} - {self.price}"


class PricingRule(BaseModel):
    """
    قواعد التسعير الديناميكية - NEW

    تسمح بإنشاء أسعار تلقائية بناءً على قواعد
    مثل: السعر = التكلفة × 1.5
         أو: خصم 10% للكميات الكبيرة
    """

    RULE_TYPE_CHOICES = [
        ('MARKUP_PERCENTAGE', _('نسبة الربح')),        # سعر = تكلفة + نسبة%
        ('DISCOUNT_PERCENTAGE', _('خصم بالنسبة المئوية')),
        ('PRICE_FORMULA', _('صيغة تسعير')),            # صيغة مخصصة
        ('BULK_DISCOUNT', _('خصم الكميات')),          # خصم حسب الكمية
        ('SEASONAL_PRICING', _('تسعير موسمي')),       # أسعار خاصة بفترة
    ]

    name = models.CharField(_('اسم القاعدة'), max_length=100)
    code = models.CharField(_('رمز القاعدة'), max_length=20)
    description = models.TextField(_('الوصف'), blank=True)

    rule_type = models.CharField(
        _('نوع القاعدة'),
        max_length=30,
        choices=RULE_TYPE_CHOICES,
        default='MARKUP_PERCENTAGE'
    )

    # قيمة النسبة (للخصم أو الزيادة)
    percentage_value = models.DecimalField(
        _('قيمة النسبة %'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('مثال: 15.00 تعني 15%')
    )

    # صيغة التسعير (JSON)
    formula = models.JSONField(
        _('الصيغة'),
        default=dict,
        blank=True,
        help_text=_('صيغة التسعير بصيغة JSON، مثل: {"base": "cost", "multiplier": 1.5, "add": 10}')
    )

    # شروط التطبيق
    min_quantity = models.DecimalField(
        _('الكمية الأدنى'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('القاعدة تطبق من هذه الكمية فما فوق')
    )

    max_quantity = models.DecimalField(
        _('الكمية الأقصى'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    # نطاق التطبيق
    apply_to_all_items = models.BooleanField(
        _('تطبيق على جميع المواد'),
        default=False
    )

    apply_to_categories = models.ManyToManyField(
        'ItemCategory',
        blank=True,
        related_name='pricing_rules',
        verbose_name=_('التصنيفات المشمولة')
    )

    apply_to_items = models.ManyToManyField(
        'Item',
        blank=True,
        related_name='pricing_rules',
        verbose_name=_('المواد المشمولة')
    )

    apply_to_price_lists = models.ManyToManyField(
        PriceList,
        blank=True,
        related_name='pricing_rules',
        verbose_name=_('قوائم الأسعار المشمولة')
    )

    # الأولوية
    priority = models.IntegerField(
        _('الأولوية'),
        default=10,
        help_text=_('القواعد ذات الأولوية الأعلى تطبق أولاً')
    )

    # التواريخ
    start_date = models.DateField(_('تاريخ البداية'), null=True, blank=True)
    end_date = models.DateField(_('تاريخ النهاية'), null=True, blank=True)

    class Meta:
        verbose_name = _('قاعدة تسعير')
        verbose_name_plural = _('قواعد التسعير')
        unique_together = [['company', 'code']]
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"

    def calculate_price(self, base_price, quantity=1, cost_price=None):
        """
        حساب السعر بناءً على القاعدة

        Args:
            base_price: السعر الأساسي
            quantity: الكمية
            cost_price: سعر التكلفة (للقواعد التي تعتمد على التكلفة)

        Returns:
            Decimal: السعر المحسوب
        """
        from decimal import Decimal

        base_price = Decimal(str(base_price))
        quantity = Decimal(str(quantity))

        # التحقق من الكمية
        if self.min_quantity and quantity < self.min_quantity:
            return base_price

        if self.max_quantity and quantity > self.max_quantity:
            return base_price

        # تطبيق القاعدة حسب النوع
        if self.rule_type == 'MARKUP_PERCENTAGE':
            if cost_price:
                cost_price = Decimal(str(cost_price))
                markup = cost_price * (self.percentage_value / Decimal('100'))
                return cost_price + markup
            return base_price

        elif self.rule_type == 'DISCOUNT_PERCENTAGE':
            discount = base_price * (self.percentage_value / Decimal('100'))
            return base_price - discount

        elif self.rule_type == 'PRICE_FORMULA':
            # تطبيق صيغة مخصصة
            if self.formula:
                try:
                    multiplier = Decimal(str(self.formula.get('multiplier', 1)))
                    add_amount = Decimal(str(self.formula.get('add', 0)))

                    if self.formula.get('base') == 'cost' and cost_price:
                        return (Decimal(str(cost_price)) * multiplier) + add_amount
                    else:
                        return (base_price * multiplier) + add_amount
                except:
                    return base_price

        elif self.rule_type == 'BULK_DISCOUNT':
            # خصم متدرج حسب الكمية
            if self.percentage_value:
                discount = base_price * (self.percentage_value / Decimal('100'))
                return base_price - discount

        return base_price

    def is_valid_date(self, check_date=None):
        """التحقق من صلاحية القاعدة في تاريخ معين"""
        from django.utils import timezone

        if not check_date:
            check_date = timezone.now().date()

        if not self.is_active:
            return False

        if self.start_date and check_date < self.start_date:
            return False

        if self.end_date and check_date > self.end_date:
            return False

        return True


class PriceHistory(models.Model):
    """
    تاريخ تغييرات الأسعار - NEW
    Audit trail لتتبع جميع تغييرات الأسعار
    """

    price_list_item = models.ForeignKey(
        PriceListItem,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('سعر المادة')
    )

    old_price = models.DecimalField(
        _('السعر القديم'),
        max_digits=15,
        decimal_places=3
    )

    new_price = models.DecimalField(
        _('السعر الجديد'),
        max_digits=15,
        decimal_places=3
    )

    change_percentage = models.DecimalField(
        _('نسبة التغيير %'),
        max_digits=10,
        decimal_places=2,
        help_text=_('نسبة الزيادة أو النقص في السعر')
    )

    change_reason = models.CharField(
        _('سبب التغيير'),
        max_length=200,
        blank=True,
        help_text=_('سبب تغيير السعر')
    )

    changed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('تم التغيير بواسطة')
    )

    changed_at = models.DateTimeField(
        _('تاريخ التغيير'),
        auto_now_add=True
    )

    # معلومات إضافية
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سجل سعر')
        verbose_name_plural = _('سجل الأسعار')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['price_list_item', '-changed_at']),
            models.Index(fields=['-changed_at']),
        ]

    def __str__(self):
        return f"{self.price_list_item}: {self.old_price} → {self.new_price}"

    def save(self, *args, **kwargs):
        """حساب نسبة التغيير تلقائياً"""
        if self.old_price and self.new_price:
            if self.old_price > 0:
                change = ((self.new_price - self.old_price) / self.old_price) * Decimal('100')
                self.change_percentage = change
        super().save(*args, **kwargs)


# دالة مساعدة محدّثة للحصول على سعر مادة
def get_item_price(item, variant=None, uom=None, price_list=None, quantity=1, check_date=None):
    """
    ⭐ محدّث: الحصول على سعر مادة أو متغير من قائمة أسعار معينة
    الآن يدعم UoM

    Args:
        item: المادة
        variant: المتغير (اختياري)
        uom: وحدة القياس (اختياري - الافتراضي: الوحدة الأساسية)
        price_list: قائمة الأسعار (إذا لم تحدد، ستستخدم القائمة الافتراضية)
        quantity: الكمية (للتحقق من الكمية الأدنى)
        check_date: تاريخ التحقق (افتراضياً اليوم)

    Returns:
        Decimal: السعر أو 0 إذا لم يوجد
    """
    from decimal import Decimal
    from django.utils import timezone

    if not check_date:
        check_date = timezone.now().date()

    # إذا لم تحدد قائمة أسعار، استخدم الافتراضية
    if not price_list:
        try:
            price_list = PriceList.objects.filter(
                company=item.company,
                is_default=True,
                is_active=True
            ).first()

            if not price_list:
                price_list = PriceList.objects.filter(
                    company=item.company,
                    is_active=True
                ).first()

            if not price_list:
                return Decimal('0.000')
        except:
            return Decimal('0.000')

    try:
        # البحث عن السعر
        query = PriceListItem.objects.filter(
            price_list=price_list,
            item=item,
            is_active=True
        )

        # إضافة شرط المتغير
        if variant:
            query = query.filter(variant=variant)
        else:
            query = query.filter(variant__isnull=True)

        # ⭐ NEW: إضافة شرط UoM
        if uom:
            query = query.filter(uom=uom)
        else:
            query = query.filter(uom__isnull=True)

        # البحث عن سعر صالح في التاريخ المحدد مع الكمية المناسبة
        prices = query.filter(
            min_quantity__lte=quantity
        ).order_by('-min_quantity')

        for price_item in prices:
            if price_item.is_valid_date(check_date):
                return price_item.price

        # إذا لم يوجد سعر صالح، أرجع 0
        return Decimal('0.000')

    except PriceListItem.DoesNotExist:
        return Decimal('0.000')

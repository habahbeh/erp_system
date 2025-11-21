# apps/core/models/item_models.py
"""
نماذج المواد والمتغيرات - Item Models
- ItemCategory: تصنيفات المواد (4 مستويات)
- Brand: العلامات التجارية
- Item: المواد - محدّث مع base_uom
- VariantAttribute: خصائص المتغيرات
- VariantValue: قيم الخصائص
- ItemVariant: متغيرات المواد - محدّث
- ItemVariantAttributeValue: ربط المتغير بالخصائص
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base_models import BaseModel


class ItemCategory(BaseModel):
    """تصنيفات المواد - 4 مستويات"""

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                               verbose_name=_('التصنيف الأب'))
    code = models.CharField(_('رمز التصنيف'), max_length=20)
    name = models.CharField(_('اسم التصنيف'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    level = models.PositiveIntegerField(_('المستوى'), default=1, editable=False)
    description = models.TextField(_('الوصف'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    class Meta:
        verbose_name = _('تصنيف المواد')
        verbose_name_plural = _('تصنيفات المواد')
        unique_together = [['company', 'code']]
        ordering = ['level', 'name']

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
            if self.level > 4:
                raise ValueError(_('لا يمكن تجاوز 4 مستويات'))
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        indent = "  " * (self.level - 1)
        return f"{indent}{self.name}"


class Brand(BaseModel):
    """العلامات التجارية"""

    name = models.CharField(_('اسم العلامة التجارية'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    description = models.TextField(_('الوصف'), blank=True)
    logo = models.ImageField(_('الشعار'), upload_to='brands/logos/', blank=True, null=True)
    website = models.URLField(_('الموقع الإلكتروني'), blank=True)
    country = models.CharField(_('بلد المنشأ'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('علامة تجارية')
        verbose_name_plural = _('العلامات التجارية')
        unique_together = [['name', 'company']]
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(BaseModel):
    """
    المواد - محدّث

    ⭐ KEY CHANGES:
    - base_uom: الوحدة الأساسية للمادة
    - is_discontinued: soft delete بدلاً من hard delete
    """

    code = models.CharField(_('رمز المادة'), max_length=50)
    item_code = models.CharField(_('رمز الكود'), max_length=100, blank=True, null=True)
    name = models.CharField(_('اسم المادة'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)
    catalog_number = models.CharField(_('رقم الكتالوج'), max_length=100, blank=True, null=True)
    barcode = models.CharField(_('الباركود'), max_length=100, blank=True, null=True)

    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT, related_name='items',
                                 verbose_name=_('التصنيف'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='items',
                              verbose_name=_('العلامة التجارية'))

    # ⭐ RENAMED: unit_of_measure → base_uom (الوحدة الأساسية)
    base_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name=_('الوحدة الأساسية'),
        help_text=_('الوحدة الأساسية للمادة (مثل: قطعة)'),
        null=True,  # Temporary for migration
        blank=True
    )

    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, verbose_name=_('العملة'), related_name='items')

    tax_rate = models.DecimalField(_('نسبة الضريبة %'), max_digits=5, decimal_places=2, default=16.0)

    # الوصف والمواصفات
    short_description = models.TextField(_('وصف مختصر'), max_length=300, blank=True)
    description = models.TextField(_('الوصف التفصيلي'), blank=True)
    specifications = models.JSONField(_('المواصفات الفنية'), default=dict, blank=True)
    features = models.TextField(_('المميزات'), blank=True)

    # المتغيرات
    has_variants = models.BooleanField(_('له متغيرات'), default=False)

    # ⭐ NEW: Soft delete
    is_discontinued = models.BooleanField(
        _('متوقف الإنتاج'),
        default=False,
        help_text=_('المادة متوقفة عن الإنتاج لكن يمكن الرجوع إليها')
    )

    discontinued_date = models.DateField(
        _('تاريخ التوقف'),
        null=True,
        blank=True
    )

    discontinued_reason = models.CharField(
        _('سبب التوقف'),
        max_length=200,
        blank=True
    )

    # الأبعاد الفيزيائية
    weight = models.DecimalField(_('الوزن (كغ)'), max_digits=10, decimal_places=3, null=True, blank=True)
    length = models.DecimalField(_('الطول (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(_('العرض (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(_('الارتفاع (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)

    # معلومات إضافية
    manufacturer = models.CharField(_('الشركة المصنعة'), max_length=200, blank=True)
    model_number = models.CharField(_('رقم الموديل'), max_length=100, blank=True)

    # الملفات والصور
    image = models.ImageField(_('صورة المادة'), upload_to='items/images/', blank=True, null=True)
    attachment = models.FileField(_('ملف مرفق'), upload_to='items/attachments/', blank=True, null=True)
    attachment_name = models.CharField(_('اسم المرفق'), max_length=100, blank=True)

    # الملاحظات
    notes = models.TextField(_('ملاحظات'), blank=True)
    additional_notes = models.TextField(_('ملاحظات إضافية'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    # الحسابات المحاسبية
    sales_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_items',
        verbose_name=_('حساب المبيعات')
    )
    purchase_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_items',
        verbose_name=_('حساب المشتريات')
    )
    inventory_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('حساب المخزون')
    )
    cost_of_goods_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cogs_items',
        verbose_name=_('حساب تكلفة البضاعة المباعة')
    )

    class Meta:
        verbose_name = _('مادة')
        verbose_name_plural = _('المواد')
        ordering = ['name']
        unique_together = [['code', 'company'], ['barcode', 'company']]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', 'code']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        """عرض اسم المادة"""
        if self.code:
            return f"{self.code} - {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        prefix = 'ITM'
        last_item = Item.objects.filter(company=self.company, code__startswith=prefix).order_by('-id').first()

        if last_item:
            try:
                last_number = int(last_item.code[3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:06d}"

    def discontinue(self, reason='', user=None):
        """
        إيقاف المادة عن الإنتاج - Soft delete

        Args:
            reason: سبب الإيقاف
            user: المستخدم الذي قام بالإيقاف
        """
        from django.utils import timezone
        from .audit_models import VariantLifecycleEvent

        self.is_discontinued = True
        self.discontinued_date = timezone.now().date()
        self.discontinued_reason = reason
        self.is_active = False
        self.save()

        # تسجيل الحدث لكل متغير
        for variant in self.variants.all():
            variant.is_discontinued = True
            variant.is_active = False
            variant.save()

            VariantLifecycleEvent.log_event(
                variant=variant,
                event_type='DISCONTINUED',
                description=f'تم إيقاف المتغير: {reason}',
                changed_by=user,
                reason=reason
            )

    def reactivate(self, user=None):
        """إعادة تفعيل المادة"""
        from .audit_models import VariantLifecycleEvent

        self.is_discontinued = False
        self.discontinued_date = None
        self.discontinued_reason = ''
        self.is_active = True
        self.save()

        # إعادة تفعيل المتغيرات
        for variant in self.variants.all():
            variant.is_discontinued = False
            variant.is_active = True
            variant.save()

            VariantLifecycleEvent.log_event(
                variant=variant,
                event_type='REACTIVATED',
                description='تم إعادة تفعيل المتغير',
                changed_by=user
            )

    def delete(self, *args, **kwargs):
        """منع الحذف إذا كان للمادة رصيد في المخزون"""
        from apps.inventory.models import ItemStock
        from django.core.exceptions import ValidationError

        # التحقق من وجود رصيد
        stock_exists = ItemStock.objects.filter(
            item=self,
            quantity__gt=0
        ).exists()

        if stock_exists:
            raise ValidationError(
                f'لا يمكن حذف المادة "{self.name}" لأن لها رصيد في المخزون. '
                'يرجى إفراغ المخزون أولاً أو استخدام "إيقاف الإنتاج".'
            )

        super().delete(*args, **kwargs)


class VariantAttribute(BaseModel):
    """خصائص المتغيرات - مثل: الحجم، اللون، المادة"""

    name = models.CharField(_('اسم الخاصية'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    display_name = models.CharField(_('اسم العرض'), max_length=100, blank=True)
    is_required = models.BooleanField(_('إجباري'), default=True)
    sort_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    class Meta:
        verbose_name = _('خاصية المتغير')
        verbose_name_plural = _('خصائص المتغيرات')
        ordering = ['sort_order', 'name']
        unique_together = [['name', 'company']]

    def __str__(self):
        return self.display_name or self.name


class VariantValue(BaseModel):
    """قيم الخصائص - مثل: 5 سم، 10 سم، أحمر، أزرق"""

    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, related_name='values',
                                  verbose_name=_('الخاصية'))
    value = models.CharField(_('القيمة'), max_length=100)
    value_en = models.CharField(_('القيمة الإنجليزية'), max_length=100, blank=True)
    display_value = models.CharField(_('قيمة العرض'), max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    class Meta:
        verbose_name = _('قيمة المتغير')
        verbose_name_plural = _('قيم المتغيرات')
        ordering = ['attribute', 'sort_order', 'value']
        unique_together = [['attribute', 'value']]

    def __str__(self):
        return f"{self.attribute.name}: {self.display_value or self.value}"


class ItemVariant(BaseModel):
    """
    متغيرات المواد - محدّث

    ⭐ KEY CHANGES:
    - is_discontinued: soft delete
    - cost_price: سعر التكلفة (لحساب الأسعار)
    - base_price: السعر الأساسي
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='variants', verbose_name=_('المادة'))
    code = models.CharField(_('كود المتغير'), max_length=50)
    catalog_number = models.CharField(_('رقم الكتالوج'), max_length=100, blank=True, null=True)
    barcode = models.CharField(_('باركود المتغير'), max_length=100, blank=True)

    # ⭐ NEW: التسعير
    cost_price = models.DecimalField(
        _('سعر التكلفة'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('سعر التكلفة - يستخدم في حساب الأسعار')
    )

    base_price = models.DecimalField(
        _('السعر الأساسي'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('السعر الأساسي قبل تطبيق قوائم الأسعار')
    )

    # الأبعاد الفيزيائية الخاصة بالمتغير
    # ✅ إذا لم تُحدد، يستخدم أبعاد Item الأساسية
    weight = models.DecimalField(
        _('الوزن الخاص'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('إذا لم يُحدد، يُستخدم وزن المادة الأساسية')
    )
    length = models.DecimalField(
        _('الطول الخاص (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('إذا لم يُحدد، يُستخدم طول المادة الأساسية')
    )
    width = models.DecimalField(
        _('العرض الخاص (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('إذا لم يُحدد، يُستخدم عرض المادة الأساسية')
    )
    height = models.DecimalField(
        _('الارتفاع الخاص (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('إذا لم يُحدد، يُستخدم ارتفاع المادة الأساسية')
    )

    # الملفات
    image = models.ImageField(_('صورة المتغير'), upload_to='items/variants/', blank=True, null=True)

    # ⭐ NEW: Soft delete
    is_discontinued = models.BooleanField(
        _('متوقف الإنتاج'),
        default=False
    )

    discontinued_date = models.DateField(
        _('تاريخ التوقف'),
        null=True,
        blank=True
    )

    # ملاحظات
    notes = models.TextField(_('ملاحظات المتغير'), blank=True)

    class Meta:
        verbose_name = _('متغير المادة')
        verbose_name_plural = _('متغيرات المواد')
        ordering = ['item', 'code']
        unique_together = [['item', 'code']]
        indexes = [
            models.Index(fields=['item', 'is_active']),
            models.Index(fields=['item', 'code']),
            models.Index(fields=['code']),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        base_code = self.item.code
        variant_count = self.item.variants.count() + 1
        return f"{base_code}-V{variant_count:03d}"

    def __str__(self):
        # عرض الخصائص في الاسم
        attributes = self.variant_attribute_values.select_related('attribute', 'value')
        attr_str = ", ".join([f"{av.attribute.name}: {av.value.value}" for av in attributes])
        return f"{self.item.name} ({attr_str})" if attr_str else f"{self.item.name} - {self.code}"

    def get_full_name(self):
        """الحصول على الاسم الكامل مع الخصائص"""
        attributes = self.variant_attribute_values.select_related('attribute', 'value')
        attr_parts = [av.value.value for av in attributes]
        if attr_parts:
            return f"{self.item.name} - {' - '.join(attr_parts)}"
        return f"{self.item.name} - {self.code}"

    def get_attribute_values_dict(self):
        """
        الحصول على خصائص المتغير كـ dictionary

        Returns:
            dict: {attribute_name: value}
        """
        attributes = self.variant_attribute_values.select_related('attribute', 'value')
        return {
            av.attribute.name: av.value.value
            for av in attributes
        }

    def get_stock_across_warehouses(self, company=None):
        """
        الحصول على الرصيد في كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            QuerySet: أرصدة المادة في كل المستودعات
        """
        from apps.inventory.models import ItemStock

        filters = {
            'item': self.item,
            'item_variant': self
        }

        if company:
            filters['company'] = company
        elif self.company:
            filters['company'] = self.company

        return ItemStock.objects.filter(**filters).select_related('warehouse')

    def get_total_stock(self, company=None):
        """
        إجمالي الرصيد عبر كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            dict: {
                'total_quantity': Decimal,
                'total_reserved': Decimal,
                'total_available': Decimal,
                'total_value': Decimal,
                'warehouses_count': int
            }
        """
        from apps.inventory.models import ItemStock

        return ItemStock.get_total_stock(
            item=self.item,
            item_variant=self,
            company=company or self.company
        )

    def get_average_cost(self, company=None):
        """
        متوسط التكلفة عبر كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            Decimal: متوسط التكلفة الموزون
        """
        from decimal import Decimal

        stocks = self.get_stock_across_warehouses(company)

        total_value = sum(s.total_value for s in stocks)
        total_quantity = sum(s.quantity for s in stocks)

        if total_quantity > 0:
            return total_value / total_quantity

        # إذا لم يوجد رصيد، أرجع cost_price إذا كان موجوداً
        return self.cost_price or Decimal('0')

    def get_total_available(self, company=None):
        """
        إجمالي الكمية المتاحة (غير المحجوزة)

        Args:
            company: الشركة (اختياري)

        Returns:
            Decimal: الكمية المتاحة
        """
        stocks = self.get_stock_across_warehouses(company)
        return sum(s.get_available_quantity() for s in stocks)

    def check_stock_availability(self, quantity, warehouse=None, company=None):
        """
        التحقق من توفر كمية معينة

        Args:
            quantity: الكمية المطلوبة
            warehouse: المستودع (اختياري - إذا لم يحدد، يتحقق من كل المستودعات)
            company: الشركة (اختياري)

        Returns:
            dict: {
                'available': bool,
                'quantity_available': Decimal,
                'shortage': Decimal
            }
        """
        from apps.inventory.models import ItemStock
        from decimal import Decimal

        if warehouse:
            # التحقق من مستودع محدد
            try:
                stock = ItemStock.objects.get(
                    item=self.item,
                    item_variant=self,
                    warehouse=warehouse,
                    company=company or self.company
                )
                available = stock.get_available_quantity()
            except ItemStock.DoesNotExist:
                available = Decimal('0')
        else:
            # التحقق من كل المستودعات
            available = self.get_total_available(company)

        return {
            'available': available >= quantity,
            'quantity_available': available,
            'shortage': max(quantity - available, Decimal('0'))
        }

    def get_dimensions(self):
        """
        الحصول على الأبعاد الفيزيائية للمتغير

        إذا لم تُحدد أبعاد خاصة بالمتغير، يُستخدم أبعاد المادة الأساسية

        Returns:
            dict: {
                'weight': Decimal,
                'length': Decimal,
                'width': Decimal,
                'height': Decimal,
                'volume': Decimal  # (length * width * height) / 1,000,000 = m³
            }
        """
        from decimal import Decimal

        # استخدم أبعاد المتغير أو أبعاد Item كـ fallback
        weight = self.weight if self.weight is not None else self.item.weight
        length = self.length if self.length is not None else self.item.length
        width = self.width if self.width is not None else self.item.width
        height = self.height if self.height is not None else self.item.height

        # حساب الحجم (m³) = (length × width × height) / 1,000,000
        volume = None
        if length and width and height:
            volume = (length * width * height) / Decimal('1000000')

        return {
            'weight': weight,
            'length': length,
            'width': width,
            'height': height,
            'volume': volume
        }

    def calculate_shipping_weight(self):
        """
        حساب الوزن القابل للشحن (Dimensional Weight)

        يُستخدم في الشحن - يأخذ الأكبر بين:
        - الوزن الفعلي
        - الوزن الحجمي = (Length × Width × Height) / 5000

        Returns:
            Decimal: الوزن القابل للشحن بالكيلو
        """
        from decimal import Decimal

        dimensions = self.get_dimensions()
        actual_weight = dimensions['weight'] or Decimal('0')

        # حساب الوزن الحجمي (معامل 5000 هو المعيار في الشحن)
        volumetric_weight = Decimal('0')
        if dimensions['length'] and dimensions['width'] and dimensions['height']:
            volumetric_weight = (
                dimensions['length'] *
                dimensions['width'] *
                dimensions['height']
            ) / Decimal('5000')

        # أرجع الأكبر
        return max(actual_weight, volumetric_weight)


class ItemVariantAttributeValue(BaseModel):
    """ربط متغير المادة بقيم الخصائص"""

    variant = models.ForeignKey(ItemVariant, on_delete=models.CASCADE, related_name='variant_attribute_values',
                                verbose_name=_('المتغير'))
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, verbose_name=_('الخاصية'))
    value = models.ForeignKey(VariantValue, on_delete=models.CASCADE, verbose_name=_('القيمة'))

    class Meta:
        verbose_name = _('قيمة خاصية المتغير')
        verbose_name_plural = _('قيم خصائص المتغيرات')
        unique_together = [['variant', 'attribute']]

    def __str__(self):
        return f"{self.variant.code} - {self.attribute.name}: {self.value.value}"

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

    # الأبعاد الفيزيائية الخاصة
    weight = models.DecimalField(_('الوزن الخاص'), max_digits=10, decimal_places=3, null=True, blank=True)

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

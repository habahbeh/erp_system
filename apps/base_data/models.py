# apps/base_data/models.py
"""
نماذج البيانات الأساسية
يحتوي على: الشركاء التجاريين (العملاء/الموردين)، الأصناف، وحدات القياس، المستودعات
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import Company, Branch, User
from django.utils import timezone


class BaseModel(models.Model):
    """نموذج أساسي يحتوي على حقول مشتركة"""

    # الشركة والفرع
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    # التتبع
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        verbose_name=_('أنشأ بواسطة')
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated',
        verbose_name=_('عدّل بواسطة')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التعديل')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    class Meta:
        abstract = True


class UnitOfMeasure(BaseModel):
    """وحدات القياس"""

    code = models.CharField(
        _('الرمز'),
        max_length=10,
        unique=True
    )

    name = models.CharField(
        _('الاسم'),
        max_length=50
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=50,
        blank=True
    )

    class Meta:
        verbose_name = _('وحدة قياس')
        verbose_name_plural = _('وحدات القياس')

    def __str__(self):
        return f"{self.name} ({self.code})"


class ItemCategory(BaseModel):
    """تصنيفات الأصناف - 4 مستويات"""

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('التصنيف الأب')
    )

    code = models.CharField(
        _('رمز التصنيف'),
        max_length=20
    )

    name = models.CharField(
        _('اسم التصنيف'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
    )

    level = models.IntegerField(
        _('المستوى'),
        default=1,
        editable=False
    )

    cost_of_goods_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='category_cogs',
        verbose_name=_('حساب تكلفة البضاعة المباعة')
    )

    class Meta:
        verbose_name = _('تصنيف الأصناف')
        verbose_name_plural = _('تصنيفات الأصناف')
        unique_together = [['company', 'code']]

    def save(self, *args, **kwargs):
        """حساب المستوى تلقائياً"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{'--' * (self.level - 1)} {self.name}"


class Item(BaseModel):
    """الأصناف/المواد"""

    # معلومات أساسية
    code = models.CharField(
        _('رمز الصنف'),
        max_length=50
    )

    name = models.CharField(
        _('اسم الصنف'),
        max_length=200
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=200,
        blank=True
    )

    barcode = models.CharField(
        _('الباركود'),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )

    # التصنيف والوحدة
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        verbose_name=_('التصنيف')
    )

    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name=_('وحدة القياس')
    )

    # الأسعار والضرائب
    purchase_price = models.DecimalField(
        _('سعر الشراء'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    sale_price = models.DecimalField(
        _('سعر البيع'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    tax_rate = models.DecimalField(
        _('نسبة الضريبة %'),
        max_digits=5,
        decimal_places=2,
        default=16.0
    )

    # حسابات المواد
    sales_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_sales',
        verbose_name=_('حساب المبيعات')
    )

    purchase_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_purchases',
        verbose_name=_('حساب المشتريات')
    )

    inventory_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_inventory',
        verbose_name=_('حساب المخزون')
    )

    cost_of_goods_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cogs_items',
        verbose_name=_('حساب تكلفة البضاعة')
    )

    # المواد البديلة
    substitute_items = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        verbose_name=_('المواد البديلة')
    )

    # معلومات إضافية
    manufacturer = models.CharField(
        _('الشركة المصنعة'),
        max_length=100,
        blank=True
    )

    specifications = models.TextField(
        _('المواصفات'),
        blank=True
    )

    weight = models.DecimalField(
        _('الوزن'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    image = models.ImageField(
        _('صورة الصنف'),
        upload_to='item/',
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # حدود المخزون
    minimum_quantity = models.DecimalField(
        _('الحد الأدنى'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    maximum_quantity = models.DecimalField(
        _('الحد الأعلى'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # حالة المادة
    is_inactive = models.BooleanField(
        _('غير فعالة'),
        default=False
    )

    class Meta:
        verbose_name = _('صنف')
        verbose_name_plural = _('الأصناف')
        unique_together = [['company', 'code']]

    def __str__(self):
        return "{} - {}".format(self.code, self.name)


class ItemConversion(BaseModel):
    """معدلات المادة - تحويل الوحدات"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='conversions',
        verbose_name=_('المادة')
    )

    from_unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='from_conversions',
        verbose_name=_('من وحدة')
    )

    to_unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='to_conversions',
        verbose_name=_('إلى وحدة')
    )

    factor = models.DecimalField(
        _('معامل التحويل'),
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text=_('عدد وحدات "إلى" في وحدة واحدة من "من"')
    )

    class Meta:
        verbose_name = _('معدل المادة')
        verbose_name_plural = _('معدلات المواد')
        unique_together = [['item', 'from_unit', 'to_unit']]

    def __str__(self):
        return f"{self.item.name}: 1 {self.from_unit.name} = {self.factor} {self.to_unit.name}"


class ItemComponent(BaseModel):
    """مستهلكات المادة - مكونات المنتج"""

    parent_item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name=_('المادة الأساسية')
    )

    component_item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='used_in',
        verbose_name=_('المادة المكونة')
    )

    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name=_('الوحدة')
    )

    waste_percentage = models.DecimalField(
        _('نسبة الهدر %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('مستهلك المادة')
        verbose_name_plural = _('مستهلكات المواد')
        unique_together = [['parent_item', 'component_item']]

    def get_total_quantity(self):
        """الكمية الإجمالية مع الهدر"""
        return self.quantity * (1 + self.waste_percentage / 100)

    def __str__(self):
        return f"{self.parent_item.name} <- {self.component_item.name} ({self.quantity})"


class Warehouse(BaseModel):
    """المستودعات"""

    code = models.CharField(
        _('رمز المستودع'),
        max_length=20
    )

    name = models.CharField(
        _('اسم المستودع'),
        max_length=100
    )

    location = models.CharField(
        _('الموقع'),
        max_length=200,
        blank=True
    )

    keeper = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name=_('أمين المستودع')
    )

    warehouse_type = models.CharField(
        _('نوع المستودع'),
        max_length=20,
        choices=[
            ('main', _('رئيسي')),
            ('branch', _('فرعي')),
            ('transit', _('ترانزيت')),
            ('damaged', _('تالف')),
        ],
        default='branch'
    )

    class Meta:
        verbose_name = _('مستودع')
        verbose_name_plural = _('المستودعات')
        unique_together = [['company', 'branch', 'code']]

    def __str__(self):
        return f"{self.name} ({self.branch.name if self.branch else 'الشركة'})"


# 🆕 جدول واحد للعملاء والموردين
class BusinessPartner(BaseModel):
    """الشركاء التجاريين (العملاء والموردين)"""

    PARTNER_TYPES = [
        ('customer', _('عميل')),
        ('supplier', _('مورد')),
        ('both', _('عميل ومورد')),
    ]

    ACCOUNT_TYPE_CHOICES = [
        ('cash', _('نقدي')),
        ('credit', _('ذمم')),
    ]

    # نوع الشريك
    partner_type = models.CharField(
        _('نوع الشريك'),
        max_length=10,
        choices=PARTNER_TYPES,
        default='customer'
    )

    # معلومات أساسية
    code = models.CharField(
        _('الرمز'),
        max_length=50
    )

    name = models.CharField(
        _('الاسم'),
        max_length=200
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=200,
        blank=True
    )

    account_type = models.CharField(
        _('نوع الحساب'),
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default='credit'
    )

    # معلومات الاتصال
    contact_person = models.CharField(
        _('اسم جهة الاتصال'),
        max_length=100,
        blank=True
    )

    phone = models.CharField(
        _('الهاتف'),
        max_length=20,
        blank=True
    )

    mobile = models.CharField(
        _('الموبايل'),
        max_length=20,
        blank=True
    )

    fax = models.CharField(
        _('الفاكس'),
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        _('البريد الإلكتروني'),
        blank=True
    )

    website = models.URLField(
        _('الموقع الإلكتروني'),
        blank=True
    )

    # العنوان
    address = models.TextField(
        _('العنوان'),
        blank=True
    )

    city = models.CharField(
        _('المدينة'),
        max_length=50,
        blank=True
    )

    region = models.CharField(
        _('المنطقة'),
        max_length=50,
        blank=True
    )

    # معلومات ضريبية
    tax_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=50,
        blank=True
    )

    tax_status = models.CharField(
        _('الحالة الضريبية'),
        max_length=20,
        choices=[
            ('taxable', _('خاضع')),
            ('exempt', _('معفى')),
            ('export', _('تصدير')),
        ],
        default='taxable'
    )

    commercial_register = models.CharField(
        _('السجل التجاري'),
        max_length=50,
        blank=True
    )

    # حدود الائتمان
    credit_limit = models.DecimalField(
        _('حد الائتمان'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    credit_period = models.IntegerField(
        _('فترة الائتمان (أيام)'),
        default=30
    )

    # الحسابات المحاسبية
    customer_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_partners',
        verbose_name=_('حساب العميل')
    )

    supplier_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_partners',
        verbose_name=_('حساب المورد')
    )

    # حقول خاصة بالعملاء
    salesperson = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_partners',
        verbose_name=_('مندوب المبيعات')
    )

    discount_percentage = models.DecimalField(
        _('نسبة الخصم %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('للعملاء فقط')
    )

    customer_category = models.CharField(
        _('تصنيف العميل'),
        max_length=20,
        choices=[
            ('retail', _('تجزئة')),
            ('wholesale', _('جملة')),
            ('vip', _('VIP')),
            ('regular', _('عادي')),
        ],
        default='regular',
        blank=True
    )

    # حقول خاصة بالموردين
    payment_terms = models.CharField(
        _('شروط الدفع'),
        max_length=100,
        blank=True,
        help_text=_('للموردين')
    )

    supplier_category = models.CharField(
        _('تصنيف المورد'),
        max_length=20,
        choices=[
            ('manufacturer', _('مصنع')),
            ('distributor', _('موزع')),
            ('importer', _('مستورد')),
            ('local', _('محلي')),
        ],
        default='local',
        blank=True
    )

    rating = models.IntegerField(
        _('التقييم'),
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('من 1 إلى 5 - للموردين')
    )

    # معلومات إضافية
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('شريك تجاري')
        verbose_name_plural = _('الشركاء التجاريون')
        unique_together = [['company', 'code']]

    def __str__(self):
        type_label = dict(self.PARTNER_TYPES)[self.partner_type]
        return f"{self.code} - {self.name} ({type_label})"

    def is_customer(self):
        """هل هو عميل؟"""
        return self.partner_type in ['customer', 'both']

    def is_supplier(self):
        """هل هو مورد؟"""
        return self.partner_type in ['supplier', 'both']


# للتوافق مع الكود الموجود - يمكن حذفها لاحقاً
class Customer(BusinessPartner):
    """العملاء - للتوافق مع الكود الموجود"""

    class Meta:
        proxy = True
        verbose_name = _('عميل')
        verbose_name_plural = _('العملاء')

    def save(self, *args, **kwargs):
        if not self.partner_type:
            self.partner_type = 'customer'
        super().save(*args, **kwargs)

    objects = models.Manager()  # المدير الافتراضي

    class CustomerManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(
                partner_type__in=['customer', 'both']
            )

    customers = CustomerManager()


class Supplier(BusinessPartner):
    """الموردين - للتوافق مع الكود الموجود"""

    class Meta:
        proxy = True
        verbose_name = _('مورد')
        verbose_name_plural = _('الموردين')

    def save(self, *args, **kwargs):
        if not self.partner_type:
            self.partner_type = 'supplier'
        super().save(*args, **kwargs)

    objects = models.Manager()  # المدير الافتراضي

    class SupplierManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(
                partner_type__in=['supplier', 'both']
            )

    suppliers = SupplierManager()


class WarehouseItem(BaseModel):
    """أرصدة المستودعات"""

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='warehouse_items',
        verbose_name=_('المستودع')
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='warehouse_items',
        verbose_name=_('المادة')
    )

    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    average_cost = models.DecimalField(
        _('متوسط التكلفة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    class Meta:
        unique_together = [['warehouse', 'item']]
        verbose_name = _('رصيد مستودع')
        verbose_name_plural = _('أرصدة المستودعات')

    def __str__(self):
        return f"{self.item.name} @ {self.warehouse.name}: {self.quantity}"
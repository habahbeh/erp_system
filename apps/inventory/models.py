# apps/inventory/models.py
"""
نماذج المخازن
يحتوي على: سندات الإدخال/الإخراج، التحويلات بين المخازن، الجرد، حركة المواد
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, Item, Warehouse, Customer, Supplier
from apps.accounting.models import Account, JournalEntry
from apps.core.models import User


class StockDocument(BaseModel):
    """نموذج أساسي للمستندات المخزنية"""

    DOCUMENT_TYPES = [
        ('in', _('سند إدخال')),
        ('out', _('سند إخراج')),
        ('transfer', _('سند تحويل')),
    ]

    document_type = models.CharField(
        _('نوع السند'),
        max_length=10,
        choices=DOCUMENT_TYPES
    )

    number = models.CharField(
        _('رقم السند'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    # المستودع
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع'),
        related_name='%(class)s_documents'
    )

    # المرجع
    reference = models.CharField(
        _('المرجع'),
        max_length=100,
        blank=True,
        help_text=_('رقم الفاتورة أو المستند المرتبط')
    )

    # الحالة
    is_posted = models.BooleanField(
        _('مرحل'),
        default=False
    )

    posted_date = models.DateTimeField(
        _('تاريخ الترحيل'),
        null=True,
        blank=True
    )

    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_posted',
        verbose_name=_('رحل بواسطة')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        abstract = True


class StockIn(StockDocument):
    """سند إدخال"""

    SOURCE_TYPES = [
        ('purchase', _('مشتريات')),
        ('return', _('مرتجع مبيعات')),
        ('production', _('إنتاج')),
        ('opening', _('رصيد افتتاحي')),
        ('adjustment', _('تسوية')),
        ('other', _('أخرى')),
    ]

    source_type = models.CharField(
        _('مصدر الإدخال'),
        max_length=20,
        choices=SOURCE_TYPES
    )

    # المورد (اختياري)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المورد')
    )

    # فاتورة المشتريات المرتبطة
    purchase_invoice = models.ForeignKey(
        'purchases.PurchaseInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('فاتورة المشتريات'),
        related_name='stock_ins'
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    class Meta:
        verbose_name = _('سند إدخال')
        verbose_name_plural = _('سندات الإدخال')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد رقم السند"""
        self.document_type = 'in'

        if not self.number:
            year = self.date.strftime('%Y')
            last_doc = StockIn.objects.filter(
                company=self.company,
                number__startswith=f"SI/{year}/"
            ).order_by('-number').first()

            if last_doc:
                last_number = int(last_doc.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"SI/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.get_source_type_display()}"


class StockOut(StockDocument):
    """سند إخراج"""

    DESTINATION_TYPES = [
        ('sales', _('مبيعات')),
        ('return', _('مرتجع مشتريات')),
        ('consumption', _('استهلاك')),
        ('damage', _('تالف')),
        ('adjustment', _('تسوية')),
        ('other', _('أخرى')),
    ]

    destination_type = models.CharField(
        _('جهة الإخراج'),
        max_length=20,
        choices=DESTINATION_TYPES
    )

    # العميل (اختياري)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('العميل')
    )

    # فاتورة المبيعات المرتبطة
    sales_invoice = models.ForeignKey(
        'sales.SalesInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('فاتورة المبيعات'),
        related_name='stock_outs'
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    class Meta:
        verbose_name = _('سند إخراج')
        verbose_name_plural = _('سندات الإخراج')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد رقم السند"""
        self.document_type = 'out'

        if not self.number:
            year = self.date.strftime('%Y')
            last_doc = StockOut.objects.filter(
                company=self.company,
                number__startswith=f"SO/{year}/"
            ).order_by('-number').first()

            if last_doc:
                last_number = int(last_doc.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"SO/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.get_destination_type_display()}"


class StockDocumentLine(models.Model):
    """سطور سندات الإدخال/الإخراج"""

    # العلاقة مع السند (إدخال أو إخراج)
    stock_in = models.ForeignKey(
        StockIn,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lines',
        verbose_name=_('سند الإدخال')
    )

    stock_out = models.ForeignKey(
        StockOut,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lines',
        verbose_name=_('سند الإخراج')
    )

    # المادة
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
    )

    # الكمية والتكلفة
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    unit_cost = models.DecimalField(
        _('تكلفة الوحدة'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    total_cost = models.DecimalField(
        _('التكلفة الإجمالية'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # معلومات إضافية
    batch_number = models.CharField(
        _('رقم الدفعة'),
        max_length=50,
        blank=True
    )

    expiry_date = models.DateField(
        _('تاريخ الانتهاء'),
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سطر سند مخزني')
        verbose_name_plural = _('سطور السندات المخزنية')

    def save(self, *args, **kwargs):
        """حساب التكلفة الإجمالية"""
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class StockTransfer(StockDocument):
    """التحويلات بين المخازن"""

    # المستودع المصدر (موروث من StockDocument)
    # warehouse = المستودع المصدر

    # المستودع الهدف
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع الهدف'),
        related_name='incoming_transfers'
    )

    # الموافقات
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='approved_transfers'
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # الاستلام
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('استلم بواسطة'),
        related_name='received_transfers'
    )

    received_date = models.DateTimeField(
        _('تاريخ الاستلام'),
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('pending', _('معلق')),
            ('approved', _('معتمد')),
            ('in_transit', _('في الطريق')),
            ('received', _('مستلم')),
            ('cancelled', _('ملغي')),
        ],
        default='draft'
    )

    class Meta:
        verbose_name = _('تحويل مخزني')
        verbose_name_plural = _('التحويلات المخزنية')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد رقم السند"""
        self.document_type = 'transfer'

        if not self.number:
            year = self.date.strftime('%Y')
            last_transfer = StockTransfer.objects.filter(
                company=self.company,
                number__startswith=f"ST/{year}/"
            ).order_by('-number').first()

            if last_transfer:
                last_number = int(last_transfer.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"ST/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.warehouse.name} إلى {self.destination_warehouse.name}"


class StockTransferLine(models.Model):
    """سطور التحويل المخزني"""

    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('التحويل')
    )

    # المادة
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
    )

    barcode = models.CharField(
        _('باركود'),
        max_length=50,
        blank=True
    )

    # الكميات
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    received_quantity = models.DecimalField(
        _('الكمية المستلمة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    # التكلفة
    unit_cost = models.DecimalField(
        _('الإفرادي'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    total_cost = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سطر تحويل')
        verbose_name_plural = _('سطور التحويلات')

    def save(self, *args, **kwargs):
        """حساب الإجمالي والباركود"""
        if self.item and not self.barcode:
            self.barcode = self.item.barcode or ''

        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class StockMovement(models.Model):
    """حركة المواد"""

    MOVEMENT_TYPES = [
        ('in', _('إدخال')),
        ('out', _('إخراج')),
        ('transfer_out', _('تحويل صادر')),
        ('transfer_in', _('تحويل وارد')),
    ]

    # المعلومات الأساسية
    date = models.DateTimeField(
        _('التاريخ والوقت'),
        auto_now_add=True
    )

    movement_type = models.CharField(
        _('نوع الحركة'),
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    # المادة والمستودع
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    # الكميات والتكلفة
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3
    )

    unit_cost = models.DecimalField(
        _('تكلفة الوحدة'),
        max_digits=12,
        decimal_places=3
    )

    total_cost = models.DecimalField(
        _('التكلفة الإجمالية'),
        max_digits=15,
        decimal_places=3
    )

    # الرصيد بعد الحركة
    balance_quantity = models.DecimalField(
        _('رصيد الكمية'),
        max_digits=12,
        decimal_places=3
    )

    balance_value = models.DecimalField(
        _('رصيد القيمة'),
        max_digits=15,
        decimal_places=3
    )

    # المرجع
    reference_type = models.CharField(
        _('نوع المرجع'),
        max_length=50,
        blank=True
    )

    reference_id = models.IntegerField(
        _('رقم المرجع'),
        null=True,
        blank=True
    )

    reference_number = models.CharField(
        _('رقم المستند'),
        max_length=50,
        blank=True
    )

    # الشركة والفرع
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('أنشأ بواسطة')
    )

    class Meta:
        verbose_name = _('حركة مادة')
        verbose_name_plural = _('حركة المواد')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['item', 'warehouse', '-date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.get_movement_type_display()} - {self.quantity}"


class StockCount(BaseModel):
    """الجرد"""

    COUNT_TYPES = [
        ('periodic', _('جرد دوري')),
        ('annual', _('جرد سنوي')),
        ('cycle', _('جرد دائري')),
        ('special', _('جرد خاص')),
    ]

    # معلومات أساسية
    number = models.CharField(
        _('رقم الجرد'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('تاريخ الجرد')
    )

    count_type = models.CharField(
        _('نوع الجرد'),
        max_length=20,
        choices=COUNT_TYPES,
        default='periodic'
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    # الفريق
    count_team = models.ManyToManyField(
        User,
        verbose_name=_('فريق الجرد'),
        related_name='stock_counts'
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('المشرف'),
        related_name='supervised_counts'
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('planned', _('مخطط')),
            ('in_progress', _('جاري')),
            ('completed', _('مكتمل')),
            ('approved', _('معتمد')),
            ('cancelled', _('ملغي')),
        ],
        default='planned'
    )

    # الموافقة
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='approved_counts'
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # القيد المحاسبي للتسويات
    adjustment_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('قيد التسوية')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('جرد')
        verbose_name_plural = _('الجرد')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد رقم الجرد"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_count = StockCount.objects.filter(
                company=self.company,
                number__startswith=f"SC/{year}/"
            ).order_by('-number').first()

            if last_count:
                last_number = int(last_count.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"SC/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.warehouse.name}"


class StockCountLine(models.Model):
    """سطور الجرد"""

    count = models.ForeignKey(
        StockCount,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الجرد')
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
    )

    # الكميات
    system_quantity = models.DecimalField(
        _('الكمية بالنظام'),
        max_digits=12,
        decimal_places=3,
        help_text=_('الكمية المسجلة في النظام')
    )

    counted_quantity = models.DecimalField(
        _('الكمية الفعلية'),
        max_digits=12,
        decimal_places=3,
        help_text=_('الكمية المحسوبة فعلياً')
    )

    difference_quantity = models.DecimalField(
        _('الفرق'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False
    )

    # القيم
    unit_cost = models.DecimalField(
        _('تكلفة الوحدة'),
        max_digits=12,
        decimal_places=3
    )

    system_value = models.DecimalField(
        _('القيمة بالنظام'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )

    counted_value = models.DecimalField(
        _('القيمة الفعلية'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )

    difference_value = models.DecimalField(
        _('فرق القيمة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الملاحظات
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    adjustment_reason = models.CharField(
        _('سبب الفرق'),
        max_length=200,
        blank=True
    )

    class Meta:
        verbose_name = _('سطر جرد')
        verbose_name_plural = _('سطور الجرد')
        unique_together = [['count', 'item']]

    def save(self, *args, **kwargs):
        """حساب الفروقات"""
        # حساب الفرق في الكمية
        self.difference_quantity = self.counted_quantity - self.system_quantity

        # حساب القيم
        self.system_value = self.system_quantity * self.unit_cost
        self.counted_value = self.counted_quantity * self.unit_cost
        self.difference_value = self.counted_value - self.system_value

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - فرق: {self.difference_quantity}"


class ItemStock(models.Model):
    """رصيد المواد في المستودعات"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name=_('المادة')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name=_('المستودع')
    )

    # الكميات
    quantity = models.DecimalField(
        _('الكمية المتاحة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    reserved_quantity = models.DecimalField(
        _('الكمية المحجوزة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    # التكلفة
    average_cost = models.DecimalField(
        _('متوسط التكلفة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    total_value = models.DecimalField(
        _('القيمة الإجمالية'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    # آخر حركة
    last_movement_date = models.DateTimeField(
        _('تاريخ آخر حركة'),
        null=True,
        blank=True
    )

    # الشركة
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    class Meta:
        verbose_name = _('رصيد مادة')
        verbose_name_plural = _('أرصدة المواد')
        unique_together = [['item', 'warehouse']]

    def get_available_quantity(self):
        """الكمية المتاحة للبيع"""
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.item.name} @ {self.warehouse.name}: {self.quantity}"
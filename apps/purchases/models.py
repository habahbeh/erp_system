# apps/purchases/models.py
"""
نماذج المشتريات
يحتوي على: فواتير المشتريات، مرتجع المشتريات، أوامر الشراء، طلبات الشراء
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, Supplier, Item, Warehouse
from apps.accounting.models import Account, Currency, JournalEntry
from apps.sales.models import PaymentMethod
from apps.core.models import User, Branch


class PurchaseInvoice(BaseModel):
    """فواتير المشتريات"""

    INVOICE_TYPES = [
        ('purchase', _('فاتورة مشتريات')),
        ('return', _('مرتجع مشتريات')),
    ]

    # نوع الفاتورة
    invoice_type = models.CharField(
        _('نوع الفاتورة'),
        max_length=10,
        choices=INVOICE_TYPES,
        default='purchase'
    )

    # معلومات أساسية
    number = models.CharField(
        _('رقم الفاتورة'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('تاريخ الفاتورة')
    )

    # طريقة الدفع
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        verbose_name=_('طريقة الدفع')
    )

    # العملة
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    # التواريخ والمراجع
    receipt_date = models.DateField(
        _('تاريخ الإيصال'),
        null=True,
        blank=True
    )

    receipt_number = models.CharField(
        _('رقم الإيصال'),
        max_length=50
    )

    reference = models.CharField(
        _('المرجع'),
        max_length=100,
        blank=True,
        help_text=_('رقم سند إدخال')
    )

    # البيانات الإجبارية
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name=_('اسم المورد')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    # رقم فاتورة المورد
    supplier_invoice_number = models.CharField(
        _('رقم فاتورة المورد'),
        max_length=50,
        blank=True
    )

    supplier_invoice_date = models.DateField(
        _('تاريخ فاتورة المورد'),
        null=True,
        blank=True
    )

    # الخصم على مستوى الفاتورة
    discount_type = models.CharField(
        _('نوع الخصم'),
        max_length=10,
        choices=[
            ('percentage', _('نسبة مئوية')),
            ('amount', _('مبلغ')),
        ],
        default='percentage'
    )

    discount_value = models.DecimalField(
        _('قيمة الخصم'),
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    discount_affects_cost = models.BooleanField(
        _('يؤثر على التكلفة'),
        default=True,
        help_text=_('خصم المشتريات عادة يؤثر على التكلفة')
    )

    discount_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('حساب الخصم'),
        related_name='purchase_discount_invoices'
    )

    # المبالغ الإجمالية
    subtotal_before_discount = models.DecimalField(
        _('المجموع قبل الخصم'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    discount_amount = models.DecimalField(
        _('مبلغ الخصم'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    subtotal_after_discount = models.DecimalField(
        _('المجموع بعد الخصم'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    tax_amount = models.DecimalField(
        _('قيمة الضريبة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    total_amount = models.DecimalField(
        _('الإجمالي قبل الضريبة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    total_with_tax = models.DecimalField(
        _('الإجمالي بعد الضريبة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الحسابات
    supplier_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('حساب المورد'),
        related_name='supplier_invoices',
        null=True,
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    # الحالة
    is_posted = models.BooleanField(
        _('مرحل'),
        default=False
    )

    # للمرتجعات
    original_invoice = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name=_('الفاتورة الأصلية')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('فاتورة مشتريات')
        verbose_name_plural = _('فواتير المشتريات')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد رقم الفاتورة وحساب المجاميع"""
        if not self.number:
            prefix = 'PI' if self.invoice_type == 'purchase' else 'PR'
            year = self.date.strftime('%Y')

            last_invoice = PurchaseInvoice.objects.filter(
                company=self.company,
                invoice_type=self.invoice_type,
                number__startswith=f"{prefix}/{year}/"
            ).order_by('-number').first()

            if last_invoice:
                last_number = int(last_invoice.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"{prefix}/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """حساب مجاميع الفاتورة"""
        # مجموع السطور قبل خصم الفاتورة
        lines_total = sum(line.subtotal for line in self.lines.all())
        self.subtotal_before_discount = lines_total

        # حساب خصم الفاتورة
        if self.discount_type == 'percentage':
            self.discount_amount = lines_total * (self.discount_value / 100)
        else:
            self.discount_amount = self.discount_value

        self.subtotal_after_discount = lines_total - self.discount_amount

        # مجموع الضرائب
        self.tax_amount = sum(line.tax_amount for line in self.lines.all())

        # الإجماليات
        self.total_amount = self.subtotal_after_discount
        self.total_with_tax = self.total_amount + self.tax_amount

    def __str__(self):
        return f"{self.number} - {self.supplier.name}"


class PurchaseInvoiceItem(models.Model):
    """سطور فاتورة المشتريات"""

    invoice = models.ForeignKey(
        PurchaseInvoice,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الفاتورة')
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

    name_latin = models.CharField(
        _('الاسم اللاتيني'),
        max_length=200,
        blank=True
    )

    # البيان
    description = models.TextField(
        _('البيان'),
        blank=True
    )

    # الكمية والسعر
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    unit = models.ForeignKey(
        'base_data.UnitOfMeasure',
        on_delete=models.PROTECT,
        verbose_name=_('الوحدة')
    )

    unit_price = models.DecimalField(
        _('الإفرادي'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    subtotal = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الخصم على السطر
    discount_percentage = models.DecimalField(
        _('خصم %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    discount_amount = models.DecimalField(
        _('خصم (قيمة)'),
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # الضريبة
    tax_included = models.BooleanField(
        _('ضريبة مضافة شامل الضريبة'),
        default=False
    )

    tax_type = models.CharField(
        _('نوع الضريبة'),
        max_length=50,
        blank=True
    )

    tax_rate = models.DecimalField(
        _('نسبة الضريبة %'),
        max_digits=5,
        decimal_places=2,
        default=16
    )

    tax_amount = models.DecimalField(
        _('قيمة الضريبة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الحسابات
    expense_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('حساب المشتريات'),
        related_name='purchase_lines',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('سطر فاتورة مشتريات')
        verbose_name_plural = _('سطور فواتير المشتريات')

    def save(self, *args, **kwargs):
        """حساب المبالغ"""
        # البيانات من المادة
        if self.item and not self.barcode:
            self.barcode = self.item.barcode or ''
        if self.item and not self.name_latin:
            self.name_latin = self.item.name_en or ''
        if self.item and not self.unit_id:
            self.unit = self.item.unit

        # الإجمالي قبل الخصم
        gross_total = self.quantity * self.unit_price

        # تطبيق الخصم (النسبة لها الأولوية)
        if self.discount_percentage > 0:
            self.discount_amount = gross_total * (self.discount_percentage / 100)

        # الإجمالي بعد الخصم
        self.subtotal = gross_total - self.discount_amount

        # حساب الضريبة
        if self.tax_included:
            # السعر شامل الضريبة
            self.tax_amount = self.subtotal - (self.subtotal / (1 + self.tax_rate / 100))
        else:
            # السعر غير شامل
            self.tax_amount = self.subtotal * (self.tax_rate / 100)

        super().save(*args, **kwargs)

        # تحديث مجاميع الفاتورة
        if self.invoice:
            self.invoice.calculate_totals()
            self.invoice.save()

        # تحديث تكلفة المادة إذا كان الخصم يؤثر على التكلفة
        if self.invoice and self.invoice.discount_affects_cost:
            # سيتم تطويرها مع نظام المخزون
            pass

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class PurchaseOrder(BaseModel):
    """أوامر الشراء - بموافقة مدير المشتريات"""

    number = models.CharField(
        _('رقم الأمر'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name=_('المورد')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    # الموظف الطالب
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('طلب بواسطة'),
        related_name='purchase_orders_requested'
    )

    # موافقة المدير
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='purchase_orders_approved'
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # التواريخ
    expected_delivery_date = models.DateField(
        _('تاريخ التسليم المتوقع'),
        null=True,
        blank=True
    )

    # من طلب الشراء
    purchase_request = models.ForeignKey(
        'PurchaseRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('طلب الشراء'),
        related_name='orders'
    )

    # المجاميع
    total_amount = models.DecimalField(
        _('المبلغ الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('pending_approval', _('بانتظار الموافقة')),
            ('approved', _('معتمد')),
            ('rejected', _('مرفوض')),
            ('sent', _('مرسل للمورد')),
            ('partial', _('استلام جزئي')),
            ('completed', _('مكتمل')),
            ('cancelled', _('ملغي')),
        ],
        default='draft'
    )

    # التحويل لفاتورة
    is_invoiced = models.BooleanField(
        _('تم إصدار فاتورة'),
        default=False
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    rejection_reason = models.TextField(
        _('سبب الرفض'),
        blank=True
    )

    class Meta:
        verbose_name = _('أمر شراء')
        verbose_name_plural = _('أوامر الشراء')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']
        permissions = [
            ('approve_purchase_order', _('يمكنه اعتماد أوامر الشراء')),
        ]

    def save(self, *args, **kwargs):
        """توليد الرقم"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_order = PurchaseOrder.objects.filter(
                company=self.company,
                number__startswith=f"PO/{year}/"
            ).order_by('-number').first()

            if last_order:
                last_number = int(last_order.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"PO/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def can_approve(self, user):
        """هل يمكن للمستخدم اعتماد الأمر"""
        return user.has_perm('purchases.approve_purchase_order')

    def __str__(self):
        return f"{self.number} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    """سطور أمر الشراء"""

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الأمر')
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
    )

    description = models.TextField(
        _('البيان'),
        blank=True
    )

    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3
    )

    unit_price = models.DecimalField(
        _('السعر'),
        max_digits=12,
        decimal_places=3
    )

    received_quantity = models.DecimalField(
        _('الكمية المستلمة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    invoiced_quantity = models.DecimalField(
        _('الكمية المفوترة'),
        max_digits=12,
        decimal_places=3,
        default=0
    )

    total = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    class Meta:
        verbose_name = _('سطر أمر شراء')
        verbose_name_plural = _('سطور أوامر الشراء')

    def save(self, *args, **kwargs):
        """حساب الإجمالي"""
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # تحديث إجمالي الأمر
        if self.order:
            self.order.total_amount = sum(
                line.total for line in self.order.lines.all()
            )
            self.order.save()


class PurchaseRequest(BaseModel):
    """طلبات الشراء - بدون حقول إجبارية"""

    number = models.CharField(
        _('رقم الطلب'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    # الموظف الطالب
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('طلب بواسطة'),
        related_name='purchase_requests'
    )

    department = models.CharField(
        _('القسم'),
        max_length=100,
        blank=True
    )

    # الغرض
    purpose = models.TextField(
        _('الغرض من الطلب'),
        blank=True
    )

    required_date = models.DateField(
        _('التاريخ المطلوب'),
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('submitted', _('مقدم')),
            ('approved', _('معتمد')),
            ('rejected', _('مرفوض')),
            ('ordered', _('تم الطلب')),
        ],
        default='draft'
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('طلب شراء')
        verbose_name_plural = _('طلبات الشراء')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد الرقم"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_request = PurchaseRequest.objects.filter(
                company=self.company,
                number__startswith=f"PR/{year}/"
            ).order_by('-number').first()

            if last_request:
                last_number = int(last_request.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"PR/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.requested_by.get_full_name()}"


class PurchaseRequestItem(models.Model):
    """سطور طلب الشراء"""

    request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الطلب')
    )

    # يمكن أن تكون مادة موجودة أو وصف لمادة جديدة
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة'),
        null=True,
        blank=True
    )

    item_description = models.TextField(
        _('وصف المادة'),
        help_text=_('للمواد غير الموجودة في النظام')
    )

    quantity = models.DecimalField(
        _('الكمية المطلوبة'),
        max_digits=12,
        decimal_places=3
    )

    unit = models.CharField(
        _('الوحدة'),
        max_length=50,
        blank=True
    )

    estimated_price = models.DecimalField(
        _('السعر التقديري'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سطر طلب شراء')
        verbose_name_plural = _('سطور طلبات الشراء')
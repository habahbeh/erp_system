# apps/purchases/models.py
"""
نماذج المشتريات
يحتوي على: فواتير المشتريات، مرتجع المشتريات، أوامر الشراء، طلبات الشراء
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, BusinessPartner, Item, Warehouse, UnitOfMeasure, User, Branch, PaymentMethod
from apps.accounting.models import Account, Currency, JournalEntry

class PurchaseInvoice(DocumentBaseModel):
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
        verbose_name=_('طريقة الدفع'),
        related_name='purchase_invoices'
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
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        verbose_name=_('اسم المورد'),
        related_name='purchase_invoices'
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

    @transaction.atomic
    def post(self, user=None):
        """ترحيل الفاتورة وإنشاء سند إدخال وقيد محاسبي"""
        from django.utils import timezone
        from apps.inventory.models import StockIn, StockDocumentLine
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod

        if self.is_posted:
            raise ValidationError(_('الفاتورة مرحلة مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في الفاتورة'))

        # 1. إنشاء سند الإدخال
        stock_in = StockIn.objects.create(
            company=self.company,
            branch=self.branch,
            date=self.date,
            warehouse=self.warehouse,
            source_type='purchase',
            supplier=self.supplier,
            purchase_invoice=self,
            reference=self.number,
            notes=f"إدخال لفاتورة مشتريات {self.number}",
            created_by=user or self.created_by
        )

        # 2. نسخ سطور الفاتورة لسند الإدخال
        for invoice_line in self.lines.all():
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=invoice_line.item,
                item_variant=invoice_line.item_variant,
                quantity=invoice_line.quantity,
                unit_cost=invoice_line.unit_price,
                batch_number=invoice_line.batch_number,
                expiry_date=invoice_line.expiry_date
            )

        # 3. ترحيل سند الإدخال (يحدث المخزون تلقائياً)
        stock_in.post(user=user)

        # 4. إنشاء القيد المحاسبي
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"فاتورة مشتريات {self.number} - {self.supplier.name}",
            reference=self.number,
            source_document='purchase_invoice',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # سطور المخزون (مدين)
        from collections import defaultdict
        inventory_accounts = defaultdict(lambda: {'debit': 0, 'items': []})

        for line in self.lines.all():
            inventory_account = line.item.inventory_account or Account.objects.get(
                company=self.company, code='120000'
            )
            inventory_accounts[inventory_account]['debit'] += line.subtotal
            inventory_accounts[inventory_account]['items'].append(line.item.name)

        for account, data in inventory_accounts.items():
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=account,
                description=f"مشتريات - {', '.join(data['items'][:3])}",
                debit_amount=data['debit'],
                credit_amount=0,
                currency=self.currency,
                reference=self.number
            )
            line_number += 1

        # سطر الضريبة (مدين - قابلة للخصم)
        if self.tax_amount > 0:
            try:
                tax_account = Account.objects.get(
                    company=self.company, code='120400'  # حساب الضريبة القابلة للخصم
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=tax_account,
                    description=f"ضريبة المشتريات",
                    debit_amount=self.tax_amount,
                    credit_amount=0,
                    currency=self.currency,
                    reference=self.number
                )
                line_number += 1
            except Account.DoesNotExist:
                pass

        # سطر خصم المشتريات (دائن - إذا وجد)
        if self.discount_amount > 0 and not self.discount_affects_cost:
            discount_account = self.discount_account or Account.objects.get(
                company=self.company, code='530000'
            )
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=discount_account,
                description=f"خصم مشتريات",
                debit_amount=0,
                credit_amount=self.discount_amount,
                currency=self.currency,
                reference=self.number
            )
            line_number += 1

        # سطر المورد (دائن)
        supplier_account = self.supplier_account or self.supplier.get_account()

        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=supplier_account,
            description=f"فاتورة مشتريات - {self.supplier.name}",
            debit_amount=0,
            credit_amount=self.total_with_tax,
            currency=self.currency,
            reference=self.number,
            partner_type='supplier',
            partner_id=self.supplier.pk
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث الفاتورة
        self.journal_entry = journal_entry
        self.is_posted = True
        self.save()

        return stock_in, journal_entry

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل الفاتورة"""
        if not self.is_posted:
            raise ValidationError(_('الفاتورة غير مرحلة'))

        # إلغاء سند الإدخال
        from apps.inventory.models import StockIn
        stock_in = StockIn.objects.filter(
            purchase_invoice=self,
            company=self.company
        ).first()

        if stock_in:
            stock_in.unpost()
            stock_in.delete()

        # إلغاء القيد المحاسبي
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()
            self.journal_entry = None

        self.is_posted = False
        self.save()

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

    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='purchase_invoice_lines',
        help_text=_('للمواد ذات المتغيرات (مثل: قميص أحمر L)')
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
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name=_('الوحدة'),
        related_name='purchase_invoice_items'
    )

    unit_price = models.DecimalField(
        _('الإفرادي'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    # ✅ **إضافة معلومات الدفعة:**
    batch_number = models.CharField(
        _('رقم الدفعة'),
        max_length=50,
        blank=True,
        help_text=_('رقم دفعة الإنتاج')
    )

    expiry_date = models.DateField(
        _('تاريخ الانتهاء'),
        null=True,
        blank=True,
        help_text=_('للمواد القابلة للتلف')
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

    # ✅ **إضافة دالة clean للتحقق:**
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()

        # إذا كان المادة له متغيرات، يجب تحديد متغير
        if self.item and self.item.has_variants and not self.item_variant:
            raise ValidationError({
                'item_variant': _('يجب تحديد متغير للمادة الذي له متغيرات')
            })

        # إذا كان المادة بدون متغيرات، لا يجب تحديد متغير
        if self.item and not self.item.has_variants and self.item_variant:
            raise ValidationError({
                'item_variant': _('لا يمكن تحديد متغير لمادة بدون متغيرات')
            })

        # التحقق من أن المتغير يتبع المادة
        if self.item_variant and self.item_variant.item != self.item:
            raise ValidationError({
                'item_variant': _('المتغير المحدد لا يتبع المادة')
            })

    def save(self, *args, **kwargs):
        """حساب المبالغ"""
        # البيانات من المادة
        if self.item and not self.barcode:
            # استخدم باركود المتغير إذا وجد، وإلا باركود المادة
            if self.item_variant and self.item_variant.barcode:
                self.barcode = self.item_variant.barcode
            else:
                self.barcode = self.item.barcode or ''

        if self.item and not self.name_latin:
            self.name_latin = self.item.name_en or ''

        if self.item and not self.unit_id:
            self.unit = self.item.unit_of_measure

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
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        verbose_name=_('المورد'),
        related_name='purchase_orders'
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

    @transaction.atomic
    def submit_for_approval(self, user=None):
        """تقديم للموافقة"""
        if self.status != 'draft':
            raise ValidationError(_('يمكن تقديم المسودات فقط للموافقة'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في الأمر'))

        # حساب الإجمالي
        self.calculate_total()

        self.status = 'pending_approval'
        self.save()

    def calculate_total(self):
        """حساب إجمالي الأمر"""
        total = sum(line.total for line in self.lines.all())
        self.total_amount = total
        self.save()

    @transaction.atomic
    def approve(self, user):
        """اعتماد أمر الشراء"""
        from django.utils import timezone

        # التحقق من الحالة
        if self.status != 'pending_approval':
            raise ValidationError(_('الأمر ليس بانتظار الموافقة'))

        # التحقق من الصلاحية
        if not self.can_approve(user):
            raise PermissionDenied(_('ليس لديك صلاحية اعتماد أوامر الشراء'))

        # الاعتماد
        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    @transaction.atomic
    def reject(self, user, reason):
        """رفض أمر الشراء"""
        from django.utils import timezone

        if self.status != 'pending_approval':
            raise ValidationError(_('الأمر ليس بانتظار الموافقة'))

        if not self.can_approve(user):
            raise PermissionDenied(_('ليس لديك صلاحية رفض أوامر الشراء'))

        if not reason:
            raise ValidationError(_('يجب تحديد سبب الرفض'))

        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()

    @transaction.atomic
    def send_to_supplier(self, user=None):
        """إرسال للمورد"""
        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد الأمر قبل الإرسال'))

        self.status = 'sent'
        self.save()

        # يمكن إضافة إرسال بريد إلكتروني للمورد هنا

    @transaction.atomic
    def mark_as_received(self, received_quantity_dict=None):
        """تسجيل استلام جزئي أو كامل"""
        if self.status not in ['sent', 'partial']:
            raise ValidationError(_('الأمر ليس في حالة تسمح بالاستلام'))

        # تحديث الكميات المستلمة
        if received_quantity_dict:
            for line_id, quantity in received_quantity_dict.items():
                try:
                    line = self.lines.get(id=line_id)
                    line.received_quantity += quantity
                    line.save()
                except PurchaseOrderItem.DoesNotExist:
                    continue

        # التحقق من الاستلام الكامل
        all_received = all(
            line.received_quantity >= line.quantity
            for line in self.lines.all()
        )

        if all_received:
            self.status = 'completed'
        else:
            self.status = 'partial'

        self.save()

    @transaction.atomic
    def convert_to_invoice(self, user=None):
        """تحويل لفاتورة مشتريات"""
        if self.status not in ['approved', 'sent', 'partial', 'completed']:
            raise ValidationError(_('حالة الأمر لا تسمح بالتحويل لفاتورة'))

        if self.is_invoiced:
            raise ValidationError(_('تم إصدار فاتورة لهذا الأمر مسبقاً'))

        from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem

        # إنشاء الفاتورة
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            date=timezone.now().date(),
            supplier=self.supplier,
            warehouse=self.warehouse,
            currency=self.currency,
            payment_method=PaymentMethod.objects.filter(
                company=self.company,
                is_active=True
            ).first(),
            receipt_number=f"PO-{self.number}",
            reference=self.number,
            description=f"تحويل من أمر شراء {self.number}",
            created_by=user or self.created_by
        )

        # نسخ السطور
        for line in self.lines.all():
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=line.item,
                description=line.description,
                quantity=line.quantity,
                unit=line.item.unit_of_measure,
                unit_price=line.unit_price
            )

        # تحديث الأمر
        self.is_invoiced = True
        self.save()

        return invoice

    @transaction.atomic
    def cancel(self, user=None, reason=None):
        """إلغاء أمر الشراء"""
        if self.status in ['completed', 'cancelled']:
            raise ValidationError(_('لا يمكن إلغاء أمر مكتمل أو ملغي مسبقاً'))

        if self.is_invoiced:
            raise ValidationError(_('لا يمكن إلغاء أمر تم إصدار فاتورة له'))

        self.status = 'cancelled'
        if reason:
            self.rejection_reason = reason
        self.save()

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
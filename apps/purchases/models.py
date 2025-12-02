# apps/purchases/models.py
"""
نماذج المشتريات
يحتوي على: فواتير المشتريات، مرتجع المشتريات، أوامر الشراء، طلبات الشراء
"""

from django.db import models, transaction
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError, PermissionDenied
from decimal import Decimal
from apps.core.models import BaseModel, DocumentBaseModel, BusinessPartner, Item, Warehouse, UnitOfMeasure, User, Branch, PaymentMethod, Currency, ItemVariant
from apps.accounting.models import Account, JournalEntry
from apps.hr.models import Department, Employee

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
        max_length=50,
        blank=True,
        null=True
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
        blank=False  # ✅ الملاحظة 3: أصبح إجباري
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

    # ربط بمحضر الاستلام (3-way matching)
    goods_receipt = models.ForeignKey(
        'GoodsReceipt',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('محضر الاستلام'),
        related_name='invoices',
        help_text=_('مطابقة ثلاثية: أمر الشراء ← محضر الاستلام ← الفاتورة')
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
        indexes = [
            models.Index(fields=['company', '-date'], name='pi_company_date_idx'),
            models.Index(fields=['is_posted', '-date'], name='pi_posted_date_idx'),
            models.Index(fields=['supplier', '-date'], name='pi_supplier_date_idx'),
            models.Index(fields=['warehouse', '-date'], name='pi_warehouse_date_idx'),
            models.Index(fields=['invoice_type', '-date'], name='pi_type_date_idx'),
        ]

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()

        # التحقق من أن الخصم لا يتجاوز المجموع
        if self.discount_type == 'percentage':
            if self.discount_value > Decimal('100'):
                raise ValidationError({
                    'discount_value': _('نسبة الخصم لا يمكن أن تتجاوز 100%')
                })
        elif self.discount_type == 'amount':
            if self.subtotal_before_discount and self.discount_value > self.subtotal_before_discount:
                raise ValidationError({
                    'discount_value': _('مبلغ الخصم لا يمكن أن يتجاوز إجمالي الفاتورة')
                })

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
            self.discount_amount = lines_total * (self.discount_value / Decimal('100'))
        else:
            self.discount_amount = self.discount_value

        self.subtotal_after_discount = lines_total - self.discount_amount

        # مجموع الضرائب (للعرض فقط)
        self.tax_amount = sum(line.tax_amount for line in self.lines.all())

        # مجموع الضرائب المضافة فقط (غير الشاملة)
        added_tax = sum(
            line.tax_amount for line in self.lines.all()
            if not line.tax_included
        )

        # الإجمالي النهائي = المجموع بعد الخصم + الضرائب المضافة فقط
        # (الضرائب الشاملة موجودة في subtotal بالفعل)
        self.total_amount = self.subtotal_after_discount
        self.total_with_tax = self.total_amount + added_tax

    @transaction.atomic
    def post(self, user=None):
        """ترحيل الفاتورة وإنشاء قيد محاسبي (مع المطابقة الثلاثية)"""
        from django.utils import timezone
        from apps.inventory.models import StockIn, StockDocumentLine
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod

        if self.is_posted:
            raise ValidationError(_('الفاتورة مرحلة مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في الفاتورة'))

        # ==================== المطابقة الثلاثية (3-Way Matching) ====================
        # إذا كان هناك محضر استلام، نستخدم سند الإدخال الموجود
        # إذا لم يكن هناك محضر استلام، نُنشئ سند إدخال جديد (للتوافق مع العمليات القديمة)

        if self.goods_receipt:
            # التحقق من أن محضر الاستلام مؤكد ومرحل
            if not self.goods_receipt.is_posted:
                raise ValidationError(_('يجب ترحيل محضر الاستلام قبل ترحيل الفاتورة'))

            # التحقق من المطابقة بين كميات الفاتورة ومحضر الاستلام
            for invoice_line in self.lines.all():
                # البحث عن السطر المطابق مع التعامل مع item_variant الاختياري
                gr_filter = {'item': invoice_line.item}
                if invoice_line.item_variant:
                    gr_filter['item_variant'] = invoice_line.item_variant

                gr_line = self.goods_receipt.lines.filter(**gr_filter).first()

                if not gr_line:
                    raise ValidationError(
                        _('المادة %(item)s غير موجودة في محضر الاستلام') % {'item': invoice_line.item.name}
                    )

                if invoice_line.quantity > gr_line.received_quantity:
                    raise ValidationError(
                        _('كمية الفاتورة (%(invoice_qty)s) للمادة %(item)s تتجاوز الكمية المستلمة (%(received_qty)s)') % {
                            'invoice_qty': invoice_line.quantity,
                            'item': invoice_line.item.name,
                            'received_qty': gr_line.received_quantity
                        }
                    )

            # استخدام سند الإدخال من محضر الاستلام
            stock_in = self.goods_receipt.stock_in

            # تحديث حالة محضر الاستلام
            self.goods_receipt.status = 'invoiced'
            self.goods_receipt.invoice = self
            self.goods_receipt.save()

        else:
            # الطريقة القديمة: إنشاء سند إدخال جديد
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
                # بناء بيانات السطر مع التعامل مع item_variant الاختياري
                line_data = {
                    'stock_in': stock_in,
                    'item': invoice_line.item,
                    'quantity': invoice_line.quantity,
                    'unit_cost': invoice_line.unit_price,
                }

                # إضافة الحقول الاختيارية فقط إذا كانت موجودة
                if invoice_line.item_variant:
                    line_data['item_variant'] = invoice_line.item_variant
                if invoice_line.batch_number:
                    line_data['batch_number'] = invoice_line.batch_number
                if invoice_line.expiry_date:
                    line_data['expiry_date'] = invoice_line.expiry_date

                StockDocumentLine.objects.create(**line_data)

            # 3. ترحيل سند الإدخال بدون إنشاء قيد محاسبي
            # القيد المحاسبي سيتم إنشاؤه من الفاتورة فقط
            stock_in.post(user=user, create_journal_entry=False)

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
            # Get inventory account from item or use default
            if hasattr(line.item, 'inventory_account') and line.item.inventory_account:
                inventory_account = line.item.inventory_account
            else:
                # Use expense_account from line if exists, otherwise default
                if line.expense_account:
                    inventory_account = line.expense_account
                else:
                    inventory_account = get_default_account(
                        self.company, '120000', 'المخزون', fallback_required=True
                    )
            # subtotal يشمل الضريبة إذا كانت شاملة، فلا نضيفها مرة أخرى
            inventory_accounts[inventory_account]['debit'] += line.subtotal
            inventory_accounts[inventory_account]['items'].append(line.item.name)

        # إذا كان الخصم يؤثر على التكلفة، نوزعه على حسابات المخزون
        if self.discount_affects_cost and self.discount_amount > 0:
            total_before_discount = sum(data['debit'] for data in inventory_accounts.values())
            if total_before_discount > 0:
                for account in inventory_accounts:
                    ratio = inventory_accounts[account]['debit'] / total_before_discount
                    inventory_accounts[account]['debit'] -= self.discount_amount * ratio

        # تقريب المبالغ لتجنب فروق التقريب
        for account in inventory_accounts:
            inventory_accounts[account]['debit'] = inventory_accounts[account]['debit'].quantize(Decimal('0.001'))

        # حساب الضريبة المضافة مسبقاً لاستخدامها في التوازن
        added_tax_amount = sum(
            line.tax_amount for line in self.lines.all()
            if not line.tax_included
        )

        # ضبط فروق التقريب على آخر حساب (لضمان توازن القيد)
        total_inventory_debit = sum(data['debit'] for data in inventory_accounts.values())
        expected_inventory = self.total_with_tax - added_tax_amount
        rounding_diff = expected_inventory - total_inventory_debit
        if rounding_diff != 0 and inventory_accounts:
            # إضافة فرق التقريب لآخر حساب
            last_account = list(inventory_accounts.keys())[-1]
            inventory_accounts[last_account]['debit'] += rounding_diff

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
        # فقط الضرائب المضافة (غير الشاملة) - الضرائب الشاملة موجودة في تكلفة المخزون
        # استخدام added_tax_amount المحسوبة مسبقاً

        if added_tax_amount > 0:
            tax_account = get_default_account(
                self.company, '120400', 'ضريبة المشتريات القابلة للخصم', fallback_required=False
            )
            if tax_account:
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=tax_account,
                    description=f"ضريبة المشتريات (المضافة)",
                    debit_amount=added_tax_amount,
                    credit_amount=0,
                    currency=self.currency,
                    reference=self.number
                )
                line_number += 1

        # سطر خصم المشتريات (دائن - إذا وجد)
        if self.discount_amount > 0 and not self.discount_affects_cost:
            if self.discount_account:
                discount_account = self.discount_account
            else:
                discount_account = get_default_account(
                    self.company, '530000', 'خصم مشتريات', fallback_required=False
                )

            if discount_account:
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
        if self.supplier_account:
            supplier_account = self.supplier_account
        elif hasattr(self.supplier, 'supplier_account') and self.supplier.supplier_account:
            supplier_account = self.supplier.supplier_account
        else:
            # Fallback to a default suppliers account
            supplier_account = get_default_account(
                self.company, '210000', 'الموردون', fallback_required=True
            )

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

        # إذا كانت الفاتورة مرتبطة بمحضر استلام، لا نحذف سند الإدخال
        # لأنه تابع لمحضر الاستلام وليس للفاتورة
        if self.goods_receipt:
            # إعادة حالة محضر الاستلام إلى "مؤكد"
            self.goods_receipt.status = 'confirmed'
            self.goods_receipt.invoice = None
            self.goods_receipt.save()
        else:
            # إلغاء سند الإدخال (الطريقة القديمة)
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
        verbose_name=_('المادة'),
        null=True,
        blank=True
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

    # ✅ **UoM Conversion Fields - تحويل الوحدات:**
    purchase_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('وحدة الشراء'),
        related_name='purchase_invoice_items_purchase_uom',
        help_text=_('الوحدة التي يتم الشراء بها (مثل: كرتونة، صندوق)')
    )

    purchase_quantity = models.DecimalField(
        _('كمية الشراء'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text=_('الكمية بوحدة الشراء')
    )

    purchase_unit_price = models.DecimalField(
        _('سعر وحدة الشراء'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('السعر بوحدة الشراء (مثل: 100$ للكرتونة)')
    )

    conversion_rate = models.DecimalField(
        _('معامل التحويل'),
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text=_('كم وحدة أساسية في وحدة الشراء (مثل: 1 كرتونة = 100 قطعة)')
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
        default=16,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
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

        # تنظيف item_variant - إذا كان فارغاً اجعله None
        if self.item_variant_id == '' or self.item_variant_id is None:
            self.item_variant = None

        # تخطي التحقق إذا لم يتم تحديد مادة
        if not self.item:
            return

        # إذا كان المادة له متغيرات، يجب تحديد متغير
        if self.item.has_variants and not self.item_variant:
            raise ValidationError({
                'item_variant': _('يجب تحديد متغير للمادة الذي له متغيرات')
            })

        # إذا كان المادة بدون متغيرات، لا يجب تحديد متغير
        if not self.item.has_variants and self.item_variant:
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
            self.unit = self.item.base_uom

        # الإجمالي قبل الخصم
        gross_total = self.quantity * self.unit_price

        # تطبيق الخصم (النسبة لها الأولوية)
        if self.discount_percentage > 0:
            self.discount_amount = gross_total * (self.discount_percentage / Decimal('100'))

        # الإجمالي بعد الخصم
        self.subtotal = gross_total - self.discount_amount

        # حساب الضريبة
        if self.tax_included:
            # السعر شامل الضريبة
            self.tax_amount = self.subtotal - (self.subtotal / (Decimal('1') + self.tax_rate / Decimal('100')))
        else:
            # السعر غير شامل
            self.tax_amount = self.subtotal * (self.tax_rate / Decimal('100'))

        super().save(*args, **kwargs)

        # تحديث مجاميع الفاتورة
        if self.invoice:
            self.invoice.calculate_totals()
            self.invoice.save()

        # تحديث تكلفة المادة إذا كان الخصم يؤثر على التكلفة
        if self.invoice and self.invoice.discount_affects_cost:
            # سيتم تطويرها مع نظام المخزون
            pass

    @property
    def total(self):
        """حساب الإجمالي النهائي للسطر (شامل الضريبة المضافة)"""
        if self.tax_included:
            # الضريبة مشمولة في السعر، الإجمالي = الإجمالي بعد الخصم
            return self.subtotal
        else:
            # الضريبة غير مشمولة، يجب إضافتها
            return self.subtotal + self.tax_amount

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class PurchaseOrder(DocumentBaseModel):
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
        Employee,
        on_delete=models.PROTECT,
        verbose_name=_('طلب بواسطة'),
        related_name='purchase_orders_requested',
        null=True,
        blank=True
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
        indexes = [
            models.Index(fields=['company', '-date'], name='po_company_date_idx'),
            models.Index(fields=['status', '-date'], name='po_status_date_idx'),
            models.Index(fields=['supplier', '-date'], name='po_supplier_date_idx'),
            models.Index(fields=['is_invoiced', '-date'], name='po_invoiced_date_idx'),
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

    def calculate_totals(self):
        """حساب مجاميع أمر الشراء"""
        self.total_amount = sum(line.total for line in self.lines.all())
        self.save()

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
        from django.utils import timezone
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
            reference=self.number,
            notes=f"تحويل من أمر شراء {self.number}",
            created_by=user or self.created_by
        )

        # نسخ السطور
        for line in self.lines.all():
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=line.item,
                description=line.description,
                quantity=line.quantity,
                unit=line.item.base_uom,
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

    unit = models.ForeignKey(
        'core.UnitOfMeasure',
        on_delete=models.PROTECT,
        verbose_name=_('الوحدة'),
        null=True,
        blank=True,
        help_text=_('وحدة القياس للمادة')
    )

    description = models.TextField(
        _('البيان'),
        blank=True
    )

    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    unit_price = models.DecimalField(
        _('السعر'),
        max_digits=12,
        decimal_places=3
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

    subtotal = models.DecimalField(
        _('المجموع'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('المجموع بعد الخصم قبل الضريبة')
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
        default=16,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    tax_amount = models.DecimalField(
        _('قيمة الضريبة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False
    )

    total = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('المجموع الكلي بعد الضريبة')
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

    class Meta:
        verbose_name = _('سطر أمر شراء')
        verbose_name_plural = _('سطور أوامر الشراء')

    def save(self, *args, **kwargs):
        """حساب المبالغ مع الخصم والضريبة"""
        from decimal import Decimal

        # الإجمالي قبل الخصم
        gross_total = self.quantity * self.unit_price

        # تطبيق الخصم (النسبة لها الأولوية)
        if self.discount_percentage > 0:
            self.discount_amount = gross_total * (self.discount_percentage / Decimal('100'))

        # الإجمالي بعد الخصم (subtotal)
        self.subtotal = gross_total - self.discount_amount

        # حساب الضريبة
        if self.tax_included:
            # السعر شامل الضريبة
            self.tax_amount = self.subtotal - (self.subtotal / (Decimal('1') + self.tax_rate / Decimal('100')))
        else:
            # السعر غير شامل
            self.tax_amount = self.subtotal * (self.tax_rate / Decimal('100'))

        # الإجمالي النهائي
        if self.tax_included:
            # الضريبة مشمولة في السعر
            self.total = self.subtotal
        else:
            # الضريبة غير مشمولة، يجب إضافتها
            self.total = self.subtotal + self.tax_amount

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

    # المستخدم الطالب (يمكن أن يكون User مباشرة أو من خلال Employee)
    requested_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        verbose_name=_('طلب بواسطة'),
        related_name='purchase_requests',
        null=True,
        blank=True
    )

    # الموظف الطالب (اختياري - للربط مع نظام HR)
    requested_by_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        verbose_name=_('الموظف الطالب'),
        related_name='employee_purchase_requests',
        null=True,
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        verbose_name=_('القسم'),
        null=True,
        blank=True,
        related_name='purchase_requests'
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

    # الأولوية
    PRIORITY_CHOICES = [
        ('low', _('منخفضة')),
        ('normal', _('عادية')),
        ('high', _('عالية')),
        ('urgent', _('عاجلة')),
    ]
    priority = models.CharField(
        _('الأولوية'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
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

    # معلومات الاعتماد
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        verbose_name=_('معتمد من قبل'),
        related_name='approved_purchase_requests',
        null=True,
        blank=True
    )
    approved_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )
    rejection_reason = models.TextField(
        _('سبب الرفض'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # المرفقات
    attachment = models.FileField(
        _('مرفق'),
        upload_to='purchase_requests/%Y/%m/',
        null=True,
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
        requested_by_name = self.requested_by.get_full_name() if self.requested_by else _('غير محدد')
        return f"{self.number} - {requested_by_name}"

    def submit(self):
        """تقديم طلب الشراء للموافقة"""
        if self.status != 'draft':
            raise ValueError(_('يمكن تقديم الطلب في حالة مسودة فقط'))
        self.status = 'submitted'
        self.save()

    def approve(self, user=None):
        """اعتماد طلب الشراء"""
        from django.utils import timezone
        if self.status != 'submitted':
            raise ValueError(_('يمكن اعتماد الطلب في حالة مقدم فقط'))
        self.status = 'approved'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.save()

    def reject(self, user=None, reason=''):
        """رفض طلب الشراء"""
        if self.status != 'submitted':
            raise ValueError(_('يمكن رفض الطلب في حالة مقدم فقط'))
        self.status = 'rejected'
        self.approved_by = user  # نسجل من رفض أيضاً
        self.rejection_reason = reason
        self.save()


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
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
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


class PurchaseQuotationRequest(BaseModel):
    """طلب عروض أسعار - Request for Quotation (RFQ)"""

    number = models.CharField(
        _('رقم طلب العرض'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    # الموضوع والوصف
    subject = models.CharField(
        _('الموضوع'),
        max_length=200
    )

    description = models.TextField(
        _('الوصف'),
        blank=True,
        help_text=_('وصف تفصيلي للأصناف المطلوبة')
    )

    # ربط بطلب الشراء (اختياري)
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('طلب الشراء'),
        related_name='quotation_requests'
    )

    # التواريخ المهمة
    submission_deadline = models.DateField(
        _('آخر موعد لتقديم العروض'),
        help_text=_('آخر موعد لاستلام عروض الأسعار من الموردين')
    )

    required_delivery_date = models.DateField(
        _('تاريخ التسليم المطلوب'),
        null=True,
        blank=True
    )

    # العملة
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة'),
        null=True,
        blank=True
    )

    # شروط العرض
    payment_terms = models.TextField(
        _('شروط الدفع'),
        blank=True,
        help_text=_('مثال: دفعة مقدمة 30%، الباقي عند التسليم')
    )

    delivery_terms = models.TextField(
        _('شروط التسليم'),
        blank=True,
        help_text=_('مثال: التسليم في المستودع الرئيسي')
    )

    warranty_required = models.BooleanField(
        _('ضمان مطلوب'),
        default=False
    )

    warranty_period_months = models.IntegerField(
        _('مدة الضمان (بالأشهر)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('sent', _('مرسل للموردين')),
            ('receiving', _('استقبال العروض')),
            ('evaluating', _('تقييم العروض')),
            ('awarded', _('تم الترسية')),
            ('cancelled', _('ملغي')),
        ],
        default='draft'
    )

    # العرض الفائز
    awarded_quotation = models.ForeignKey(
        'PurchaseQuotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('العرض الفائز'),
        related_name='won_requests'
    )

    award_date = models.DateField(
        _('تاريخ الترسية'),
        null=True,
        blank=True
    )

    award_reason = models.TextField(
        _('سبب الترسية'),
        blank=True,
        help_text=_('لماذا تم اختيار هذا العرض')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    @property
    def total_estimated(self):
        """حساب التكلفة التقديرية الإجمالية"""
        total = Decimal('0')
        for item in self.items.all():
            if item.estimated_price and item.quantity:
                total += item.estimated_price * item.quantity
        return total

    @property
    def is_awarded(self):
        """هل تم ترسية العرض"""
        return self.status == 'awarded' and self.awarded_quotation is not None

    class Meta:
        verbose_name = _('طلب عرض أسعار')
        verbose_name_plural = _('طلبات عروض الأسعار')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد الرقم"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_rfq = PurchaseQuotationRequest.objects.filter(
                company=self.company,
                number__startswith=f"RFQ/{year}/"
            ).order_by('-number').first()

            if last_rfq:
                last_number = int(last_rfq.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"RFQ/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    @transaction.atomic
    def send_to_suppliers(self, supplier_ids, user=None):
        """إرسال طلب العرض للموردين المحددين"""
        if self.status != 'draft':
            raise ValidationError(_('يمكن إرسال طلبات العروض في حالة مسودة فقط'))

        if not supplier_ids:
            raise ValidationError(_('يجب تحديد مورد واحد على الأقل'))

        # إنشاء عروض أسعار للموردين مع نسخ الأصناف
        for supplier_id in supplier_ids:
            supplier = BusinessPartner.objects.get(id=supplier_id)
            quotation = PurchaseQuotation.objects.create(
                company=self.company,
                quotation_request=self,
                supplier=supplier,
                date=self.date,
                valid_until=self.submission_deadline,
                currency=self.currency,
                status='sent',
                created_by=user or self.created_by
            )

            # نسخ الأصناف من طلب العرض إلى عرض السعر
            for rfq_item in self.items.all():
                PurchaseQuotationItem.objects.create(
                    quotation=quotation,
                    rfq_item=rfq_item,
                    item=rfq_item.item,
                    description=rfq_item.item_description,
                    quantity=rfq_item.quantity,
                    unit_price=0,  # سيقوم المورد بتعبئة السعر
                    discount_percentage=0,
                    tax_percentage=0
                )

        self.status = 'sent'
        self.save()

    def __str__(self):
        return f"{self.number} - {self.subject}"


class PurchaseQuotationRequestItem(models.Model):
    """أصناف طلب عرض الأسعار"""

    quotation_request = models.ForeignKey(
        PurchaseQuotationRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('طلب العرض')
    )

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

    specifications = models.TextField(
        _('المواصفات المطلوبة'),
        blank=True,
        help_text=_('المواصفات الفنية التفصيلية')
    )

    quantity = models.DecimalField(
        _('الكمية المطلوبة'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
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
        blank=True,
        help_text=_('للمرجعية فقط')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    @property
    def line_total(self):
        """حساب الإجمالي التقديري للسطر"""
        if self.estimated_price and self.quantity:
            return self.estimated_price * self.quantity
        return Decimal('0')

    class Meta:
        verbose_name = _('صنف طلب عرض أسعار')
        verbose_name_plural = _('أصناف طلبات عروض الأسعار')


class PurchaseQuotation(BaseModel):
    """عرض سعر من مورد - Quotation"""

    number = models.CharField(
        _('رقم العرض'),
        max_length=50,
        editable=False
    )

    # ربط بطلب العرض
    quotation_request = models.ForeignKey(
        PurchaseQuotationRequest,
        on_delete=models.PROTECT,
        verbose_name=_('طلب العرض'),
        related_name='quotations'
    )

    # المورد
    supplier = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        verbose_name=_('المورد'),
        related_name='quotations'
    )

    # التواريخ
    date = models.DateField(
        _('تاريخ العرض')
    )

    valid_until = models.DateField(
        _('صالح حتى'),
        help_text=_('آخر موعد لصلاحية هذا العرض')
    )

    # رقم عرض المورد
    supplier_quotation_number = models.CharField(
        _('رقم عرض المورد'),
        max_length=50,
        blank=True
    )

    # العملة
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    # شروط العرض
    payment_terms = models.TextField(
        _('شروط الدفع'),
        blank=True
    )

    delivery_terms = models.TextField(
        _('شروط التسليم'),
        blank=True
    )

    delivery_period_days = models.IntegerField(
        _('مدة التسليم (بالأيام)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    warranty_period_months = models.IntegerField(
        _('مدة الضمان (بالأشهر)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    # المبالغ
    subtotal = models.DecimalField(
        _('المجموع الفرعي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    discount_amount = models.DecimalField(
        _('الخصم'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    tax_amount = models.DecimalField(
        _('الضريبة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    total_amount = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # التقييم
    score = models.DecimalField(
        _('التقييم'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('التقييم من 100')
    )

    evaluation_notes = models.TextField(
        _('ملاحظات التقييم'),
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('sent', _('مرسل')),
            ('received', _('مستلم')),
            ('under_evaluation', _('تحت التقييم')),
            ('accepted', _('مقبول')),
            ('rejected', _('مرفوض')),
            ('awarded', _('فائز')),
        ],
        default='draft'
    )

    is_awarded = models.BooleanField(
        _('فائز'),
        default=False
    )

    rejection_reason = models.TextField(
        _('سبب الرفض'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # المرفقات
    attachment = models.FileField(
        _('المرفقات'),
        upload_to='quotations/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('ملف PDF لعرض السعر من المورد')
    )

    class Meta:
        verbose_name = _('عرض سعر')
        verbose_name_plural = _('عروض الأسعار')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد الرقم وحساب المجاميع"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_quote = PurchaseQuotation.objects.filter(
                company=self.company,
                number__startswith=f"QT/{year}/"
            ).order_by('-number').first()

            if last_quote:
                last_number = int(last_quote.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"QT/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """حساب المجاميع"""
        self.subtotal = sum(line.total for line in self.lines.all())
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.save()

    @transaction.atomic
    def mark_as_awarded(self, user=None):
        """تحديد هذا العرض كفائز"""
        from django.utils import timezone

        if self.status not in ['received', 'under_evaluation']:
            raise ValidationError(_('لا يمكن ترسية إلا العروض المستلمة أو تحت التقييم'))

        # إلغاء أي عرض فائز سابق لنفس الطلب
        PurchaseQuotation.objects.filter(
            quotation_request=self.quotation_request,
            is_awarded=True
        ).update(is_awarded=False, status='rejected')

        # تحديد هذا العرض كفائز
        self.is_awarded = True
        self.status = 'awarded'
        self.save()

        # تحديث طلب العرض
        self.quotation_request.awarded_quotation = self
        self.quotation_request.award_date = timezone.now().date()
        self.quotation_request.status = 'awarded'
        self.quotation_request.save()

    @transaction.atomic
    def convert_to_purchase_order(self, user=None):
        """تحويل لأمر شراء"""
        from django.utils import timezone
        from datetime import timedelta

        if not self.is_awarded:
            raise ValidationError(_('يمكن تحويل العروض الفائزة فقط'))

        # التحقق من وجود مستودع
        warehouse = Warehouse.objects.filter(
            company=self.company,
            is_active=True
        ).first()

        if not warehouse:
            raise ValidationError(_('لا يوجد مستودع نشط للشركة'))

        # الحصول على الموظف من المستخدم
        employee = None
        if user and hasattr(user, 'employee'):
            employee = user.employee
        elif self.created_by and hasattr(self.created_by, 'employee'):
            employee = self.created_by.employee

        # حساب تاريخ التسليم المتوقع
        expected_delivery = None
        if self.delivery_period_days:
            expected_delivery = timezone.now().date() + timedelta(days=self.delivery_period_days)

        # الحصول على branch من quotation_request أو من warehouse
        branch = None
        if self.quotation_request and hasattr(self.quotation_request, 'branch'):
            branch = self.quotation_request.branch
        if not branch:
            branch = warehouse.branch

        # إنشاء أمر الشراء
        order = PurchaseOrder.objects.create(
            company=self.company,
            branch=branch,
            date=timezone.now().date(),
            supplier=self.supplier,
            warehouse=warehouse,
            currency=self.currency,
            requested_by=employee,
            expected_delivery_date=expected_delivery,
            status='draft',
            notes=f"تحويل من عرض سعر {self.number}\n\n"
                  f"شروط الدفع: {self.payment_terms or '-'}\n"
                  f"شروط التسليم: {self.delivery_terms or '-'}\n"
                  f"مدة الضمان: {self.warranty_period_months or 0} شهر",
            created_by=user or self.created_by
        )

        # نسخ السطور مع جميع التفاصيل
        for line in self.lines.all():
            if line.item:
                PurchaseOrderItem.objects.create(
                    order=order,
                    item=line.item,
                    description=line.description or '',
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount_percentage=line.discount_percentage,
                    tax_rate=line.tax_rate
                )

        order.calculate_total()
        return order

    def __str__(self):
        return f"{self.number} - {self.supplier.name}"


class PurchaseQuotationItem(models.Model):
    """سطور عرض السعر"""

    quotation = models.ForeignKey(
        PurchaseQuotation,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('عرض السعر')
    )

    # ربط بصنف طلب العرض
    rfq_item = models.ForeignKey(
        PurchaseQuotationRequestItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('صنف طلب العرض'),
        related_name='quotation_lines'
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة'),
        null=True,
        blank=True
    )

    description = models.TextField(
        _('الوصف'),
        blank=True
    )

    # الكمية والسعر
    quantity = models.DecimalField(
        _('الكمية'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    unit = models.CharField(
        _('الوحدة'),
        max_length=50,
        blank=True
    )

    unit_price = models.DecimalField(
        _('سعر الوحدة'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    discount_percentage = models.DecimalField(
        _('خصم %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    tax_rate = models.DecimalField(
        _('نسبة الضريبة %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    total = models.DecimalField(
        _('الإجمالي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # معلومات إضافية
    brand = models.CharField(
        _('العلامة التجارية'),
        max_length=100,
        blank=True
    )

    country_of_origin = models.CharField(
        _('بلد المنشأ'),
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سطر عرض سعر')
        verbose_name_plural = _('سطور عروض الأسعار')

    def save(self, *args, **kwargs):
        """حساب الإجمالي"""
        gross = self.quantity * self.unit_price
        discount = gross * (self.discount_percentage / Decimal('100'))
        self.total = gross - discount
        super().save(*args, **kwargs)

        # تحديث إجمالي عرض السعر
        if self.quotation:
            self.quotation.calculate_totals()


# ================== Purchase Contracts (العقود طويلة الأجل) ==================

class PurchaseContract(BaseModel):
    """عقد شراء طويل الأجل - Long-term Purchase Contract"""

    number = models.CharField(
        _('رقم العقد'),
        max_length=50,
        editable=False
    )

    supplier = models.ForeignKey(
        'core.BusinessPartner',
        on_delete=models.PROTECT,
        verbose_name=_('المورد'),
        related_name='purchase_contracts',
        limit_choices_to={'partner_type__in': ['supplier', 'both']}
    )

    contract_date = models.DateField(
        _('تاريخ العقد'),
        default=timezone.now
    )

    start_date = models.DateField(
        _('تاريخ البدء')
    )

    end_date = models.DateField(
        _('تاريخ الانتهاء')
    )

    contract_value = models.DecimalField(
        _('قيمة العقد'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('إجمالي قيمة العقد المتوقعة')
    )

    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    # شروط العقد
    payment_terms = models.TextField(
        _('شروط الدفع'),
        blank=True
    )

    delivery_terms = models.TextField(
        _('شروط التسليم'),
        blank=True
    )

    quality_standards = models.TextField(
        _('معايير الجودة'),
        blank=True,
        help_text=_('المواصفات والمعايير المطلوبة')
    )

    penalty_terms = models.TextField(
        _('شروط الغرامات'),
        blank=True,
        help_text=_('غرامات التأخير أو عدم الالتزام')
    )

    termination_terms = models.TextField(
        _('شروط الإنهاء'),
        blank=True,
        help_text=_('شروط وإجراءات إنهاء العقد')
    )

    renewal_terms = models.TextField(
        _('شروط التجديد'),
        blank=True
    )

    # الحالة
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('active', _('نشط')),
        ('suspended', _('معلق')),
        ('completed', _('مكتمل')),
        ('terminated', _('منهي')),
        ('expired', _('منتهي الصلاحية')),
    ]

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # الموافقات
    approved = models.BooleanField(
        _('معتمد'),
        default=False
    )

    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('معتمد من'),
        related_name='approved_contracts'
    )

    approved_at = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # معلومات تنفيذ العقد
    total_ordered = models.DecimalField(
        _('إجمالي المطلوب'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('إجمالي قيمة أوامر الشراء المرتبطة')
    )

    total_received = models.DecimalField(
        _('إجمالي المستلم'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('إجمالي قيمة المواد المستلمة')
    )

    total_invoiced = models.DecimalField(
        _('إجمالي المفوتر'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('إجمالي قيمة الفواتير المرتبطة')
    )

    # المرفقات
    attachment = models.FileField(
        _('المرفقات'),
        upload_to='contracts/',
        blank=True,
        null=True,
        help_text=_('نسخة ممسوحة من العقد الموقع')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('عقد شراء')
        verbose_name_plural = _('عقود الشراء')
        ordering = ['-contract_date', '-created_at']
        permissions = [
            ('approve_purchasecontract', _('يمكنه اعتماد عقود الشراء')),
        ]

    def __str__(self):
        return f"{self.number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        """Generate contract number if new"""
        if not self.number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='purchase_contract'
                )
                self.number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                # Create default sequence if it doesn't exist
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='purchase_contract',
                    prefix='PC',
                    next_number=1,
                    padding=5,
                    include_year=True,
                    yearly_reset=True
                )
                self.number = sequence.get_next_number()
        super().save(*args, **kwargs)

    def activate(self, user=None):
        """تفعيل العقد"""
        if self.status != 'draft':
            raise ValueError(_('يمكن تفعيل العقود في حالة المسودة فقط'))

        if not self.approved:
            raise ValueError(_('يجب اعتماد العقد قبل التفعيل'))

        self.status = 'active'
        self.save()

        # تسجيل في السجل
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            company=self.company,
            action='UPDATE',
            model_name='PurchaseContract',
            object_id=self.id,
            object_repr=f'تفعيل العقد {self.number}'
        )

    def suspend(self, reason='', user=None):
        """تعليق العقد"""
        if self.status not in ['active']:
            raise ValueError(_('يمكن تعليق العقود النشطة فقط'))

        self.status = 'suspended'
        if reason:
            self.notes = f"{self.notes}\n\nسبب التعليق: {reason}"
        self.save()

        # تسجيل في السجل
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            company=self.company,
            action='UPDATE',
            model_name='PurchaseContract',
            object_id=self.id,
            object_repr=f'تعليق العقد {self.number}: {reason}'
        )

    def terminate(self, reason='', user=None):
        """إنهاء العقد"""
        if self.status not in ['active', 'suspended']:
            raise ValueError(_('يمكن إنهاء العقود النشطة أو المعلقة فقط'))

        self.status = 'terminated'
        if reason:
            self.notes = f"{self.notes}\n\nسبب الإنهاء: {reason}"
        self.save()

        # تسجيل في السجل
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            company=self.company,
            action='UPDATE',
            model_name='PurchaseContract',
            object_id=self.id,
            object_repr=f'إنهاء العقد {self.number}: {reason}'
        )

    def check_expiry(self):
        """فحص انتهاء صلاحية العقد"""
        from datetime import date
        if self.status in ['active', 'suspended'] and self.end_date and self.end_date < date.today():
            self.status = 'expired'
            self.save()
            return True
        return False

    def get_utilization_percentage(self):
        """حساب نسبة استخدام العقد"""
        if self.contract_value > 0:
            return (self.total_ordered / self.contract_value) * 100
        return 0

    def get_remaining_value(self):
        """حساب القيمة المتبقية"""
        return self.contract_value - self.total_ordered

    def update_totals(self):
        """تحديث الإجماليات من أوامر الشراء والفواتير"""
        # حساب من أوامر الشراء المرتبطة
        orders = self.purchase_orders.filter(status__in=['approved', 'sent', 'partial', 'completed'])
        self.total_ordered = sum(order.total_amount for order in orders)

        # حساب من الفواتير المرتبطة
        invoices = self.purchase_invoices.filter(is_posted=True)
        self.total_invoiced = sum(invoice.grand_total for invoice in invoices)

        self.save()


class PurchaseContractItem(models.Model):
    """سطور العقد - Contract Line Items"""

    contract = models.ForeignKey(
        PurchaseContract,
        on_delete=models.CASCADE,
        verbose_name=_('العقد'),
        related_name='items'
    )

    item = models.ForeignKey(
        'core.Item',
        on_delete=models.PROTECT,
        verbose_name=_('الصنف'),
        null=True,
        blank=True
    )

    item_description = models.CharField(
        _('وصف الصنف'),
        max_length=500
    )

    specifications = models.TextField(
        _('المواصفات'),
        blank=True
    )

    unit = models.ForeignKey(
        'core.UnitOfMeasure',
        on_delete=models.PROTECT,
        verbose_name=_('الوحدة')
    )

    # الكمية والسعر
    contracted_quantity = models.DecimalField(
        _('الكمية المتعاقد عليها'),
        max_digits=15,
        decimal_places=3,
        help_text=_('إجمالي الكمية خلال فترة العقد')
    )

    unit_price = models.DecimalField(
        _('سعر الوحدة'),
        max_digits=15,
        decimal_places=3
    )

    # حدود الطلب
    min_order_quantity = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('أقل كمية يمكن طلبها في المرة الواحدة')
    )

    max_order_quantity = models.DecimalField(
        _('الحد الأقصى للطلب'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('أقصى كمية يمكن طلبها في المرة الواحدة')
    )

    # معلومات التنفيذ
    ordered_quantity = models.DecimalField(
        _('الكمية المطلوبة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    received_quantity = models.DecimalField(
        _('الكمية المستلمة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # الخصم
    discount_percentage = models.DecimalField(
        _('نسبة الخصم'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
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
        verbose_name = _('سطر عقد')
        verbose_name_plural = _('سطور العقود')

    def __str__(self):
        return f"{self.contract.number} - {self.item_description}"

    def save(self, *args, **kwargs):
        """حساب الإجمالي"""
        gross = self.contracted_quantity * self.unit_price
        discount = gross * (self.discount_percentage / Decimal('100'))
        self.total = gross - discount
        super().save(*args, **kwargs)

        # تحديث قيمة العقد
        if self.contract:
            contract_value = sum(item.total for item in self.contract.items.all())
            self.contract.contract_value = contract_value
            self.contract.save()

    def get_remaining_quantity(self):
        """حساب الكمية المتبقية"""
        return self.contracted_quantity - self.ordered_quantity

    def get_utilization_percentage(self):
        """حساب نسبة الاستخدام"""
        if self.contracted_quantity > 0:
            return (self.ordered_quantity / self.contracted_quantity) * 100
        return 0


# ================== Goods Receipt (استلام البضاعة) ==================

class GoodsReceipt(DocumentBaseModel):
    """استلام البضاعة - Goods Receipt Note (GRN)

    يُنشأ عند استلام البضاعة من المورد، قبل فاتورة المورد.
    يُستخدم لتحديث المخزون ومطابقته مع أمر الشراء والفاتورة لاحقاً.
    """

    number = models.CharField(
        _('رقم محضر الاستلام'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('تاريخ الاستلام')
    )

    # ربط بأمر الشراء
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        verbose_name=_('أمر الشراء'),
        related_name='goods_receipts'
    )

    supplier = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        verbose_name=_('المورد'),
        related_name='goods_receipts'
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع المستلم')
    )

    # معلومات التسليم
    delivery_note_number = models.CharField(
        _('رقم إيصال التسليم من المورد'),
        max_length=50,
        blank=True,
        help_text=_('رقم مستند التسليم الذي أرسله المورد')
    )

    delivery_date = models.DateField(
        _('تاريخ التسليم الفعلي'),
        null=True,
        blank=True
    )

    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('استلمها'),
        related_name='goods_receipts_received',
        help_text=_('موظف المستودع الذي استلم البضاعة')
    )

    # جودة الاستلام
    quality_check_status = models.CharField(
        _('حالة الفحص'),
        max_length=20,
        choices=[
            ('pending', _('بانتظار الفحص')),
            ('passed', _('مطابق')),
            ('partial', _('مطابق جزئياً')),
            ('failed', _('مرفوض')),
        ],
        default='pending'
    )

    quality_notes = models.TextField(
        _('ملاحظات الفحص'),
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('confirmed', _('مؤكد')),
            ('invoiced', _('تم إصدار فاتورة')),
            ('cancelled', _('ملغي')),
        ],
        default='draft'
    )

    # ربط بالفاتورة (يُملأ لاحقاً)
    invoice = models.ForeignKey(
        'PurchaseInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الفاتورة المرتبطة'),
        related_name='goods_receipts'
    )

    # تم الترحيل إلى المخزون
    is_posted = models.BooleanField(
        _('مرحل للمخزون'),
        default=False
    )

    # سند الإدخال
    stock_in = models.ForeignKey(
        'inventory.StockIn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('سند الإدخال'),
        related_name='goods_receipts'
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('محضر استلام بضاعة')
        verbose_name_plural = _('محاضر استلام البضائع')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']
        permissions = [
            ('confirm_goods_receipt', _('يمكنه تأكيد استلام البضاعة')),
        ]
        indexes = [
            models.Index(fields=['company', '-date'], name='gr_company_date_idx'),
            models.Index(fields=['status', '-date'], name='gr_status_date_idx'),
            models.Index(fields=['supplier', '-date'], name='gr_supplier_date_idx'),
            models.Index(fields=['is_posted', '-date'], name='gr_posted_date_idx'),
        ]

    def __str__(self):
        return f"{self.number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        """توليد الرقم"""
        if not self.number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='goods_receipt'
                )
                self.number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                # Create default sequence if it doesn't exist
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='goods_receipt',
                    prefix='GR',
                    next_number=1,
                    padding=5,
                    include_year=True,
                    yearly_reset=True
                )
                self.number = sequence.get_next_number()
        super().save(*args, **kwargs)

    @transaction.atomic
    def post(self, user=None):
        """ترحيل الاستلام للمخزون"""
        from apps.inventory.models import StockIn, StockDocumentLine

        if self.is_posted:
            raise ValidationError(_('محضر الاستلام مرحل مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في محضر الاستلام'))

        if self.status != 'confirmed':
            raise ValidationError(_('يجب تأكيد محضر الاستلام قبل الترحيل'))

        # إنشاء سند الإدخال
        stock_in = StockIn.objects.create(
            company=self.company,
            branch=self.branch,
            date=self.date,
            warehouse=self.warehouse,
            source_type='purchase',
            supplier=self.supplier,
            reference=self.number,
            notes=f"استلام من أمر شراء {self.purchase_order.number}",
            created_by=user or self.created_by
        )

        # نسخ سطور الاستلام لسند الإدخال
        for gr_line in self.lines.all():
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=gr_line.item,
                item_variant=gr_line.item_variant,
                quantity=gr_line.received_quantity,
                unit_cost=gr_line.unit_price,
                batch_number=gr_line.batch_number,
                expiry_date=gr_line.expiry_date
            )

        # ترحيل سند الإدخال (يحدث المخزون)
        stock_in.post(user=user)

        # تحديث محضر الاستلام
        self.stock_in = stock_in
        self.is_posted = True
        self.save()

        # تحديث أمر الشراء
        self.purchase_order.mark_as_received()

        return stock_in

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل الاستلام"""
        if not self.is_posted:
            raise ValidationError(_('محضر الاستلام غير مرحل'))

        if self.invoice:
            raise ValidationError(_('لا يمكن إلغاء ترحيل محضر استلام مرتبط بفاتورة'))

        # إلغاء سند الإدخال
        if self.stock_in:
            self.stock_in.unpost()
            self.stock_in.delete()
            self.stock_in = None

        self.is_posted = False
        self.save()

    @transaction.atomic
    def confirm(self, user=None):
        """تأكيد محضر الاستلام"""
        if self.status != 'draft':
            raise ValidationError(_('يمكن تأكيد المحاضر في حالة المسودة فقط'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في محضر الاستلام'))

        self.status = 'confirmed'
        self.save()

        # التسجيل في السجل
        from apps.core.models import AuditLog
        AuditLog.log_action(
            user=user,
            company=self.company,
            action='UPDATE',
            model_name='GoodsReceipt',
            object_id=self.id,
            description=f'تأكيد محضر استلام {self.number}'
        )


class GoodsReceiptLine(models.Model):
    """سطور محضر استلام البضاعة"""

    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('محضر الاستلام')
    )

    # ربط بسطر أمر الشراء
    purchase_order_line = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        verbose_name=_('سطر أمر الشراء'),
        related_name='goods_receipt_lines'
    )

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
        related_name='goods_receipt_lines'
    )

    # الكميات
    ordered_quantity = models.DecimalField(
        _('الكمية المطلوبة'),
        max_digits=12,
        decimal_places=3,
        editable=False,
        help_text=_('من أمر الشراء')
    )

    received_quantity = models.DecimalField(
        _('الكمية المستلمة'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    rejected_quantity = models.DecimalField(
        _('الكمية المرفوضة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    unit_price = models.DecimalField(
        _('السعر'),
        max_digits=12,
        decimal_places=3,
        editable=False,
        help_text=_('من أمر الشراء')
    )

    # معلومات الدفعة
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

    # الجودة
    quality_status = models.CharField(
        _('حالة الجودة'),
        max_length=20,
        choices=[
            ('accepted', _('مقبول')),
            ('rejected', _('مرفوض')),
            ('partial', _('مقبول جزئياً')),
        ],
        default='accepted'
    )

    quality_notes = models.TextField(
        _('ملاحظات الجودة'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سطر محضر استلام')
        verbose_name_plural = _('سطور محاضر الاستلام')

    def __str__(self):
        return f"{self.goods_receipt.number} - {self.item.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()

        # التحقق من الكمية
        if hasattr(self, 'purchase_order_line'):
            # لا يمكن استلام أكثر من المطلوب
            total_received = self.purchase_order_line.goods_receipt_lines.exclude(
                pk=self.pk
            ).aggregate(
                total=Sum('received_quantity')
            )['total'] or Decimal('0')

            new_total = total_received + self.received_quantity

            if new_total > self.purchase_order_line.quantity:
                raise ValidationError({
                    'received_quantity': _(
                        'الكمية المستلمة الإجمالية (%(total)s) تتجاوز الكمية المطلوبة (%(ordered)s)'
                    ) % {
                        'total': new_total,
                        'ordered': self.purchase_order_line.quantity
                    }
                })

    def save(self, *args, **kwargs):
        """نسخ البيانات من أمر الشراء"""
        if self.purchase_order_line:
            self.item = self.purchase_order_line.item
            self.ordered_quantity = self.purchase_order_line.quantity
            self.unit_price = self.purchase_order_line.unit_price

        super().save(*args, **kwargs)


# Helper Functions for Account Management
def get_default_account(company, code, account_name, fallback_required=True):
    """
    Helper function to get account by code with proper error handling.

    Args:
        company: Company instance
        code: Account code
        account_name: Account name (for error messages)
        fallback_required: If True, raises error if account not found

    Returns:
        Account instance or None
    """
    try:
        return Account.objects.get(company=company, code=code)
    except Account.DoesNotExist:
        if fallback_required:
            raise ValidationError(
                _('الحساب المطلوب غير موجود: %(code)s - %(name)s. يرجى إنشاء الحساب أولاً.') % {
                    'code': code,
                    'name': account_name
                }
            )
        return None
    except Account.MultipleObjectsReturned:
        # Return first one if multiple exist
        return Account.objects.filter(company=company, code=code).first()
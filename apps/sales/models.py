# apps/sales/models.py
"""
نماذج المبيعات
يحتوي على: فواتير المبيعات، مرتجع المبيعات، عروض الأسعار، طلبات البيع
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.core.models import BaseModel, DocumentBaseModel, BusinessPartner, Item, Warehouse, UnitOfMeasure, User, Branch, PaymentMethod, Currency
from apps.accounting.models import Account, JournalEntry



class SalesInvoice(DocumentBaseModel):
    """فواتير المبيعات"""

    INVOICE_TYPES = [
        ('sales', _('فاتورة مبيعات')),
        ('return', _('مرتجع مبيعات')),
    ]

    # نوع الفاتورة
    invoice_type = models.CharField(
        _('نوع الفاتورة'),
        max_length=10,
        choices=INVOICE_TYPES,
        default='sales'
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
    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['customer', 'both']},
        verbose_name=_('اسم الزبون'),
        related_name='sales_invoices'
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    salesperson = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('المندوب'),
        related_name='sales_invoices'
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
        default=False
    )

    discount_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('حساب الخصم'),
        related_name='discount_invoices'
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
    customer_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('حساب العميل'),
        related_name='customer_invoices',
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

    # ========== معلومات المستلم ==========
    recipient_name = models.CharField(
        _('اسم المستلم'),
        max_length=200,
        blank=True,
        help_text=_('اسم الشخص المستلم - قد يختلف عن اسم العميل')
    )

    recipient_phone = models.CharField(
        _('هاتف المستلم'),
        max_length=20,
        blank=True
    )

    recipient_address = models.TextField(
        _('عنوان التسليم'),
        blank=True
    )

    # ========== معلومات الشحن والتسليم ==========
    delivery_date = models.DateField(
        _('تاريخ التسليم المتوقع'),
        null=True,
        blank=True
    )

    actual_delivery_date = models.DateField(
        _('تاريخ التسليم الفعلي'),
        null=True,
        blank=True
    )

    shipping_cost = models.DecimalField(
        _('تكلفة الشحن'),
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # ========== معلومات الدفع ==========
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', _('غير مدفوع')),
        ('partial', _('مدفوع جزئياً')),
        ('paid', _('مدفوع بالكامل')),
    ]

    payment_status = models.CharField(
        _('حالة الدفع'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )

    paid_amount = models.DecimalField(
        _('المبلغ المدفوع'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    remaining_amount = models.DecimalField(
        _('المبلغ المتبقي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    due_date = models.DateField(
        _('تاريخ الاستحقاق'),
        null=True,
        blank=True,
        help_text=_('تاريخ استحقاق الدفع للفواتير الآجلة')
    )

    # ========== معلومات العمولة ==========
    salesperson_commission_rate = models.DecimalField(
        _('نسبة عمولة المندوب %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    salesperson_commission_amount = models.DecimalField(
        _('قيمة عمولة المندوب'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False
    )

    # ========== معلومات الفوترة الإلكترونية الحكومية ==========
    GOVERNMENT_STATUS_CHOICES = [
        ('not_submitted', _('لم يتم الإرسال')),
        ('submitted', _('تم الإرسال')),
        ('accepted', _('تم القبول')),
        ('rejected', _('تم الرفض')),
    ]

    government_invoice_uuid = models.CharField(
        _('UUID الفاتورة الحكومية'),
        max_length=100,
        blank=True,
        help_text=_('معرف الفاتورة في النظام الحكومي')
    )

    government_submission_date = models.DateTimeField(
        _('تاريخ الإرسال للنظام الحكومي'),
        null=True,
        blank=True
    )

    government_status = models.CharField(
        _('حالة الفاتورة الحكومية'),
        max_length=20,
        choices=GOVERNMENT_STATUS_CHOICES,
        default='not_submitted'
    )

    class Meta:
        verbose_name = _('فاتورة مبيعات')
        verbose_name_plural = _('فواتير المبيعات')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']
        permissions = [
            ('post_salesinvoice', _('يمكنه ترحيل فواتير المبيعات')),
            ('unpost_salesinvoice', _('يمكنه إلغاء ترحيل فواتير المبيعات')),
        ]

    def save(self, *args, **kwargs):
        """توليد رقم الفاتورة وحساب المجاميع"""
        if not self.number:
            prefix = 'SI' if self.invoice_type == 'sales' else 'SR'
            year = self.date.strftime('%Y')

            last_invoice = SalesInvoice.objects.filter(
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

        # مجموع الضرائب
        self.tax_amount = sum(line.tax_amount for line in self.lines.all())

        # الإجماليات
        self.total_amount = self.subtotal_after_discount
        self.total_with_tax = self.total_amount + self.tax_amount + self.shipping_cost

        # حساب المبلغ المتبقي
        self.remaining_amount = self.total_with_tax - self.paid_amount

        # حساب عمولة المندوب
        if self.salesperson_commission_rate > 0:
            self.salesperson_commission_amount = self.total_with_tax * (self.salesperson_commission_rate / Decimal('100'))

    def calculate_commission(self):
        """حساب عمولة المندوب"""
        if self.salesperson_commission_rate > 0:
            self.salesperson_commission_amount = self.total_with_tax * (self.salesperson_commission_rate / Decimal('100'))
        else:
            self.salesperson_commission_amount = 0
        return self.salesperson_commission_amount

    def update_payment_status(self):
        """تحديث حالة الدفع بناءً على المبلغ المدفوع"""
        if self.paid_amount == 0:
            self.payment_status = 'unpaid'
        elif self.paid_amount >= self.total_with_tax:
            self.payment_status = 'paid'
            self.paid_amount = self.total_with_tax  # تصحيح المبلغ المدفوع
        else:
            self.payment_status = 'partial'

        # تحديث المبلغ المتبقي
        self.remaining_amount = self.total_with_tax - self.paid_amount

    @transaction.atomic
    def post(self, user=None):
        """ترحيل الفاتورة وإنشاء سند إخراج وقيد محاسبي"""
        from django.utils import timezone
        from apps.inventory.models import StockOut, StockDocumentLine, ItemStock
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod

        if self.is_posted:
            raise ValidationError(_('الفاتورة مرحلة مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في الفاتورة'))

        # 1. إنشاء سند الإخراج
        stock_out = StockOut.objects.create(
            company=self.company,
            branch=self.branch,
            date=self.date,
            warehouse=self.warehouse,
            destination_type='sales',
            customer=self.customer,
            sales_invoice=self,
            reference=self.number,
            notes=f"إخراج لفاتورة مبيعات {self.number}",
            created_by=user or self.created_by
        )

        # 2. نسخ سطور الفاتورة لسند الإخراج
        for invoice_line in self.lines.all():
            # الحصول على رصيد المادة
            try:
                stock = ItemStock.objects.get(
                    item=invoice_line.item,
                    item_variant=invoice_line.item_variant,
                    warehouse=self.warehouse,
                    company=self.company
                )
                unit_cost = stock.average_cost
            except ItemStock.DoesNotExist:
                raise ValidationError(
                    f'لا يوجد رصيد للمادة {invoice_line.item.name} في المستودع {self.warehouse.name}'
                )

            # التحقق من الكمية المتاحة
            available = stock.quantity - stock.reserved_quantity
            if available < invoice_line.quantity:
                raise ValidationError(
                    f'الكمية المتاحة من {invoice_line.item.name} ({available}) '
                    f'أقل من المطلوب ({invoice_line.quantity})'
                )

            # إنشاء سطر سند الإخراج
            StockDocumentLine.objects.create(
                stock_out=stock_out,
                item=invoice_line.item,
                item_variant=invoice_line.item_variant,
                quantity=invoice_line.quantity,
                unit_cost=unit_cost,
                batch_number=invoice_line.batch_number,
                expiry_date=invoice_line.expiry_date
            )

        # 3. ترحيل سند الإخراج (يحدث المخزون تلقائياً)
        stock_out.post(user=user)

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
            description=f"فاتورة مبيعات {self.number} - {self.customer.name}",
            reference=self.number,
            source_document='sales_invoice',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # سطر العميل (مدين)
        customer_account = self.customer_account or self.customer.get_account()

        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=customer_account,
            description=f"فاتورة مبيعات - {self.customer.name}",
            debit_amount=self.total_with_tax,
            credit_amount=0,
            currency=self.currency,
            reference=self.number,
            partner_type='customer',
            partner_id=self.customer.pk
        )
        line_number += 1

        # سطر الإيرادات (دائن)
        from collections import defaultdict
        revenue_accounts = defaultdict(lambda: {'credit': 0, 'items': []})

        for line in self.lines.all():
            revenue_account = line.revenue_account or line.item.sales_account or Account.objects.get(
                company=self.company, code='410000'
            )
            revenue_accounts[revenue_account]['credit'] += line.subtotal
            revenue_accounts[revenue_account]['items'].append(line.item.name)

        # إذا كان الخصم يؤثر على التكلفة، نطرحه من الإيرادات
        total_revenue = sum(data['credit'] for data in revenue_accounts.values())
        if self.discount_amount > 0 and self.discount_affects_cost:
            # توزيع الخصم على حسابات الإيرادات بنسبة كل حساب
            for account, data in revenue_accounts.items():
                proportion = data['credit'] / total_revenue if total_revenue > 0 else 0
                discount_portion = self.discount_amount * proportion
                data['credit'] -= discount_portion

        for account, data in revenue_accounts.items():
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=account,
                description=f"إيرادات - {', '.join(data['items'][:3])}",
                debit_amount=0,
                credit_amount=data['credit'],
                currency=self.currency,
                reference=self.number
            )
            line_number += 1

        # سطر الضريبة (دائن)
        if self.tax_amount > 0:
            try:
                tax_account = Account.objects.get(
                    company=self.company, code='210200'  # حساب الضريبة المستحقة
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=tax_account,
                    description=f"ضريبة المبيعات",
                    debit_amount=0,
                    credit_amount=self.tax_amount,
                    currency=self.currency,
                    reference=self.number
                )
                line_number += 1
            except Account.DoesNotExist:
                pass

        # سطر الشحن (دائن - إذا وجد)
        if self.shipping_cost > 0:
            try:
                shipping_account = Account.objects.get(
                    company=self.company, code='411000'  # حساب إيرادات الشحن
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=shipping_account,
                    description=f"إيرادات شحن",
                    debit_amount=0,
                    credit_amount=self.shipping_cost,
                    currency=self.currency,
                    reference=self.number
                )
                line_number += 1
            except Account.DoesNotExist:
                # إذا لم يوجد حساب شحن، أضفه لحساب الإيرادات الرئيسي
                revenue_account = Account.objects.get(
                    company=self.company, code='410000'
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=revenue_account,
                    description=f"إيرادات شحن",
                    debit_amount=0,
                    credit_amount=self.shipping_cost,
                    currency=self.currency,
                    reference=self.number
                )
                line_number += 1

        # سطر خصم المبيعات (مدين - إذا وجد)
        if self.discount_amount > 0 and not self.discount_affects_cost:
            discount_account = self.discount_account or Account.objects.get(
                company=self.company, code='420000'
            )
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=discount_account,
                description=f"خصم مبيعات",
                debit_amount=self.discount_amount,
                credit_amount=0,
                currency=self.currency,
                reference=self.number
            )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث الفاتورة
        self.journal_entry = journal_entry
        self.is_posted = True
        self.save()

        return stock_out, journal_entry

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل الفاتورة"""
        if not self.is_posted:
            raise ValidationError(_('الفاتورة غير مرحلة'))

        # إلغاء سند الإخراج
        from apps.inventory.models import StockOut
        stock_out = StockOut.objects.filter(
            sales_invoice=self,
            company=self.company
        ).first()

        if stock_out:
            stock_out.unpost()
            stock_out.delete()

        # إلغاء القيد المحاسبي
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()
            self.journal_entry = None

        self.is_posted = False
        self.save()

    def can_user_create(self, user):
        """هل يمكن للمستخدم إنشاء فواتير مبيعات"""
        if user.is_superuser:
            return True
        if user.has_perm('sales.add_salesinvoice'):
            return True
        if hasattr(user, 'profile'):
            return user.profile.has_custom_permission('create_sales_invoice')
        return False

    def can_user_edit(self, user):
        """هل يمكن للمستخدم تعديل الفاتورة"""
        if self.is_posted:
            return False
        if user.is_superuser:
            return True
        if user.has_perm('sales.change_salesinvoice'):
            return True
        if hasattr(user, 'profile'):
            return user.profile.has_custom_permission('edit_sales_invoice')
        return False

    def can_user_delete(self, user):
        """هل يمكن للمستخدم حذف الفاتورة"""
        if self.is_posted:
            return False
        if user.is_superuser:
            return True
        if user.has_perm('sales.delete_salesinvoice'):
            return True
        if hasattr(user, 'profile'):
            return user.profile.has_custom_permission('delete_sales_invoice')
        return False

    def can_user_post(self, user):
        """هل يمكن للمستخدم ترحيل الفاتورة"""
        if user.is_superuser:
            return True
        if user.has_perm('sales.post_salesinvoice'):
            return True
        if hasattr(user, 'profile'):
            # التحقق مع حد المبلغ
            return user.profile.has_custom_permission_with_limit(
                'post_sales_invoice',
                self.total_with_tax
            )
        return False

    def can_user_apply_discount(self, user, discount_amount):
        """هل يمكن للمستخدم تطبيق خصم"""
        if user.is_superuser:
            return True

        # التحقق من حد الخصم المسموح
        if hasattr(user, 'profile'):
            max_discount = user.profile.max_discount_percentage
            discount_percentage = (discount_amount / self.subtotal_before_discount) * 100
            return discount_percentage <= max_discount

        return False

    def __str__(self):
        return f"{self.number} - {self.customer.name}"


class InvoiceItem(models.Model):
    """سطور الفاتورة"""

    invoice = models.ForeignKey(
        SalesInvoice,
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

    # ✅ **إضافة المتغير:**
    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='sales_invoice_lines',
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
        related_name='sales_invoice_items'
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
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('حساب البضاعة'),
        related_name='revenue_lines',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('سطر فاتورة')
        verbose_name_plural = _('سطور الفواتير')

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()

        # التحقق فقط إذا كانت المادة موجودة (استخدام item_id لتجنب RelatedObjectDoesNotExist)
        if not self.item_id:
            return

        # إذا كان المادة له متغيرات، يجب تحديد متغير
        if hasattr(self.item, 'has_variants') and self.item.has_variants and not self.item_variant_id:
            raise ValidationError({
                'item_variant': _('يجب تحديد متغير للمادة الذي له متغيرات')
            })

        # إذا كان المادة بدون متغيرات، لا يجب تحديد متغير
        if hasattr(self.item, 'has_variants') and not self.item.has_variants and self.item_variant_id:
            raise ValidationError({
                'item_variant': _('لا يمكن تحديد متغير لمادة بدون متغيرات')
            })

        # التحقق من أن المتغير يتبع المادة
        if self.item_variant_id and self.item_variant.item_id != self.item_id:
            raise ValidationError({
                'item_variant': _('المتغير المحدد لا يتبع المادة')
            })

    def save(self, *args, **kwargs):
        """حساب المبالغ"""
        # التحقق من وجود المادة قبل المتابعة (استخدام item_id لتجنب RelatedObjectDoesNotExist)
        if not self.item_id:
            # حفظ السطر بدون حسابات إذا لم تكن المادة محددة
            super().save(*args, **kwargs)
            return

        # 🆕 إضافة: الحصول على السعر من قائمة الأسعار
        if not self.unit_price:
            from apps.core.models import get_item_price, PriceList

            # الحصول على قائمة أسعار العميل (إذا وجدت)
            price_list = None
            if hasattr(self.invoice.customer, 'default_price_list'):
                price_list = self.invoice.customer.default_price_list

            # إذا لم توجد، استخدم القائمة الافتراضية
            if not price_list:
                price_list = PriceList.objects.filter(
                    company=self.invoice.company,
                    is_default=True,
                    is_active=True
                ).first()

            # الحصول على السعر
            if price_list:
                self.unit_price = get_item_price(
                    item=self.item,
                    variant=self.item_variant,
                    price_list=price_list,
                    quantity=self.quantity,
                    check_date=self.invoice.date
                )

            # إذا لم يوجد سعر، استخدم آخر سعر بيع
            if not self.unit_price or self.unit_price == 0:
                # يمكن إضافة last_sale_price في Item
                self.unit_price = 0  # أو رفع خطأ

        # البيانات من المادة
        if not self.barcode:
            # استخدم باركود المتغير إذا وجد، وإلا باركود المادة
            if self.item_variant and self.item_variant.barcode:
                self.barcode = self.item_variant.barcode
            else:
                self.barcode = self.item.barcode or ''

        if not self.name_latin:
            self.name_latin = self.item.name_en or ''

        if not self.unit_id:
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

    def __str__(self):
        if self.item_id:
            return f"{self.item.name} - {self.quantity}"
        return f"سطر فاتورة #{self.pk}" if self.pk else "سطر فاتورة جديد"


class Quotation(BaseModel):
    """عروض الأسعار"""

    number = models.CharField(
        _('رقم العرض'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['customer', 'both']},
        verbose_name=_('العميل'),
        related_name='sales_quotations'
    )

    salesperson = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('المندوب'),
        related_name='sales_quotations'
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    validity_days = models.IntegerField(
        _('صلاحية العرض (أيام)'),
        default=30
    )

    expiry_date = models.DateField(
        _('تاريخ انتهاء العرض'),
        null=True,
        blank=True
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
    is_approved = models.BooleanField(
        _('معتمد'),
        default=False
    )

    converted_to_order = models.BooleanField(
        _('محول لطلب'),
        default=False
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('عرض سعر')
        verbose_name_plural = _('عروض الأسعار')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد الرقم وحساب تاريخ الانتهاء"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_quote = Quotation.objects.filter(
                company=self.company,
                number__startswith=f"QT/{year}/"
            ).order_by('-number').first()

            if last_quote:
                last_number = int(last_quote.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"QT/{year}/{new_number:06d}"

        # حساب تاريخ الانتهاء
        if self.validity_days and not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = self.date + timedelta(days=self.validity_days)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.customer.name}"


class QuotationItem(models.Model):
    """سطور عرض السعر"""

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('عرض السعر')
    )

    # نسخ من InvoiceItem مع تبسيط
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

    discount_percentage = models.DecimalField(
        _('خصم %'),
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

    class Meta:
        verbose_name = _('سطر عرض سعر')
        verbose_name_plural = _('سطور عروض الأسعار')


class SalesOrder(BaseModel):
    """طلبات البيع"""

    number = models.CharField(
        _('رقم الطلب'),
        max_length=50,
        editable=False
    )

    date = models.DateField(
        _('التاريخ')
    )

    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['customer', 'both']},
        verbose_name=_('العميل'),
        related_name='sales_orders'
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    salesperson = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('المندوب'),
        related_name='sales_orders'
    )

    # من عرض السعر
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('عرض السعر'),
        related_name='orders'
    )

    # التواريخ
    delivery_date = models.DateField(
        _('تاريخ التسليم المتوقع'),
        null=True,
        blank=True
    )

    # الحالة
    is_approved = models.BooleanField(
        _('معتمد'),
        default=False
    )

    is_delivered = models.BooleanField(
        _('تم التسليم'),
        default=False
    )

    is_invoiced = models.BooleanField(
        _('تم إصدار فاتورة'),
        default=False
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('طلب بيع')
        verbose_name_plural = _('طلبات البيع')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        """توليد الرقم"""
        if not self.number:
            year = self.date.strftime('%Y')
            last_order = SalesOrder.objects.filter(
                company=self.company,
                number__startswith=f"SO/{year}/"
            ).order_by('-number').first()

            if last_order:
                last_number = int(last_order.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"SO/{year}/{new_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.customer.name}"


class SalesOrderItem(models.Model):
    """سطور طلب البيع"""

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الطلب')
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('المادة')
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

    delivered_quantity = models.DecimalField(
        _('الكمية المسلمة'),
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
        verbose_name = _('سطر طلب بيع')
        verbose_name_plural = _('سطور طلبات البيع')


# ========================================
# نموذج أقساط الدفع
# ========================================

class PaymentInstallment(DocumentBaseModel):
    """
    نموذج أقساط الدفع
    يدير الأقساط والدفعات المستحقة على فواتير المبيعات
    """

    # الحالات المتاحة للقسط
    STATUS_CHOICES = [
        ('pending', _('معلق')),
        ('paid', _('مدفوع')),
        ('overdue', _('متأخر')),
        ('cancelled', _('ملغي')),
    ]

    # ========== العلاقات ==========
    invoice = models.ForeignKey(
        SalesInvoice,
        on_delete=models.PROTECT,
        related_name='installments',
        verbose_name=_('الفاتورة'),
        help_text=_('فاتورة المبيعات المرتبطة بهذا القسط')
    )

    receipt_voucher = models.ForeignKey(
        'accounting.ReceiptVoucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installments',
        verbose_name=_('سند القبض'),
        help_text=_('سند القبض المرتبط بدفع هذا القسط')
    )

    # ========== بيانات القسط ==========
    installment_number = models.PositiveIntegerField(
        _('رقم القسط'),
        help_text=_('رقم تسلسلي للقسط (1، 2، 3...)')
    )

    due_date = models.DateField(
        _('تاريخ الاستحقاق'),
        help_text=_('التاريخ المحدد لدفع هذا القسط')
    )

    amount = models.DecimalField(
        _('المبلغ المستحق'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ المطلوب دفعه في هذا القسط')
    )

    paid_amount = models.DecimalField(
        _('المبلغ المدفوع'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ الذي تم دفعه فعلياً')
    )

    payment_date = models.DateField(
        _('تاريخ الدفع'),
        null=True,
        blank=True,
        help_text=_('التاريخ الفعلي لدفع القسط')
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_('حالة القسط (معلق، مدفوع، متأخر، ملغي)')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية على القسط أو الدفع')
    )

    class Meta:
        verbose_name = _('قسط دفع')
        verbose_name_plural = _('أقساط الدفع')
        ordering = ['invoice', 'installment_number']
        unique_together = [['invoice', 'installment_number']]
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.invoice.number} - قسط {self.installment_number} - {self.amount}"

    @property
    def remaining_amount(self):
        """المبلغ المتبقي للدفع"""
        return self.amount - self.paid_amount

    @property
    def is_paid(self):
        """هل تم دفع القسط بالكامل؟"""
        return self.paid_amount >= self.amount

    @property
    def is_overdue(self):
        """هل القسط متأخر؟"""
        from django.utils import timezone
        if self.status == 'paid':
            return False
        return timezone.now().date() > self.due_date

    def update_status(self):
        """تحديث حالة القسط بناءً على المبلغ المدفوع والتاريخ"""
        from django.utils import timezone

        if self.status == 'cancelled':
            return

        if self.is_paid:
            self.status = 'paid'
        elif timezone.now().date() > self.due_date:
            self.status = 'overdue'
        else:
            self.status = 'pending'

    def mark_as_paid(self, payment_date=None, receipt_voucher=None):
        """تعليم القسط كمدفوع"""
        from django.utils import timezone

        self.paid_amount = self.amount
        self.payment_date = payment_date or timezone.now().date()
        self.status = 'paid'

        if receipt_voucher:
            self.receipt_voucher = receipt_voucher

        self.save()

        # تحديث حالة الدفع في الفاتورة
        self.invoice.update_payment_status()
        self.invoice.save()

    def cancel(self):
        """إلغاء القسط"""
        if self.paid_amount > 0:
            raise ValidationError(_('لا يمكن إلغاء قسط تم دفعه كلياً أو جزئياً'))

        self.status = 'cancelled'
        self.save()


# ========================================
# نموذج عمولات المندوبين
# ========================================

class SalespersonCommission(DocumentBaseModel):
    """
    نموذج عمولات مندوبي المبيعات
    يدير حساب ودفع العمولات للمندوبين بناءً على المبيعات
    """

    # حالات الدفع
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', _('غير مدفوعة')),
        ('partial', _('مدفوعة جزئياً')),
        ('paid', _('مدفوعة بالكامل')),
    ]

    # ========== العلاقات ==========
    salesperson = models.ForeignKey(
        'hr.Employee',
        on_delete=models.PROTECT,
        related_name='sales_commissions',
        verbose_name=_('المندوب'),
        help_text=_('مندوب المبيعات المستحق للعمولة')
    )

    invoice = models.OneToOneField(
        SalesInvoice,
        on_delete=models.CASCADE,
        related_name='commission',
        verbose_name=_('الفاتورة'),
        help_text=_('فاتورة المبيعات المرتبطة بهذه العمولة')
    )

    payment_voucher = models.ForeignKey(
        'accounting.PaymentVoucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='salesperson_commissions',
        verbose_name=_('سند الصرف'),
        help_text=_('سند الصرف المرتبط بدفع هذه العمولة')
    )

    # ========== بيانات العمولة ==========
    commission_rate = models.DecimalField(
        _('نسبة العمولة %'),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('نسبة العمولة المئوية من قيمة الفاتورة')
    )

    base_amount = models.DecimalField(
        _('المبلغ الأساسي'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('المبلغ الأساسي المحتسب عليه العمولة (إجمالي الفاتورة)')
    )

    commission_amount = models.DecimalField(
        _('مبلغ العمولة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('المبلغ المحتسب للعمولة')
    )

    # ========== بيانات الدفع ==========
    paid_amount = models.DecimalField(
        _('المبلغ المدفوع'),
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ الذي تم دفعه من العمولة')
    )

    remaining_amount = models.DecimalField(
        _('المبلغ المتبقي'),
        max_digits=12,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('المبلغ المتبقي من العمولة')
    )

    payment_status = models.CharField(
        _('حالة الدفع'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        help_text=_('حالة دفع العمولة')
    )

    payment_date = models.DateField(
        _('تاريخ الدفع'),
        null=True,
        blank=True,
        help_text=_('تاريخ دفع العمولة')
    )

    # ========== معلومات إضافية ==========
    calculation_date = models.DateField(
        _('تاريخ الحساب'),
        auto_now_add=True,
        help_text=_('تاريخ حساب العمولة')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات على العمولة أو الدفع')
    )

    class Meta:
        verbose_name = _('عمولة مندوب')
        verbose_name_plural = _('عمولات المندوبين')
        ordering = ['-calculation_date', '-invoice__date']
        indexes = [
            models.Index(fields=['salesperson', 'payment_status']),
            models.Index(fields=['invoice']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['-calculation_date']),
        ]

    def __str__(self):
        return f"عمولة {self.salesperson} - {self.invoice.number} - {self.commission_amount}"

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()

        # التحقق من أن المبلغ المدفوع لا يتجاوز مبلغ العمولة
        if self.paid_amount > self.commission_amount:
            raise ValidationError(_('المبلغ المدفوع لا يمكن أن يتجاوز مبلغ العمولة'))

    def save(self, *args, **kwargs):
        """حفظ العمولة مع حساب المبالغ"""
        # حساب العمولة عند الإنشاء أو إذا تغيرت النسبة أو المبلغ الأساسي
        if not self.pk or 'commission_rate' in kwargs.get('update_fields', []) or 'base_amount' in kwargs.get('update_fields', []):
            self.calculate_commission()

        # حساب المبلغ المتبقي
        self.remaining_amount = self.commission_amount - self.paid_amount

        # تحديث حالة الدفع
        self.update_payment_status()

        super().save(*args, **kwargs)

    def calculate_commission(self):
        """حساب مبلغ العمولة بناءً على النسبة والمبلغ الأساسي"""
        if self.commission_rate > 0 and self.base_amount > 0:
            self.commission_amount = self.base_amount * (self.commission_rate / 100)
        else:
            self.commission_amount = Decimal('0')

        return self.commission_amount

    def update_payment_status(self):
        """تحديث حالة الدفع بناءً على المبلغ المدفوع"""
        if self.paid_amount == 0:
            self.payment_status = 'unpaid'
        elif self.paid_amount >= self.commission_amount:
            self.payment_status = 'paid'
            self.paid_amount = self.commission_amount  # تصحيح المبلغ المدفوع
        else:
            self.payment_status = 'partial'

        # تحديث المبلغ المتبقي
        self.remaining_amount = self.commission_amount - self.paid_amount

    def mark_as_paid(self, payment_date=None, payment_voucher=None):
        """
        تعليم العمولة كمدفوعة

        Args:
            payment_date: تاريخ الدفع (افتراضياً اليوم)
            payment_voucher: سند الصرف المرتبط (اختياري)
        """
        from django.utils import timezone

        self.paid_amount = self.commission_amount
        self.payment_date = payment_date or timezone.now().date()
        self.payment_status = 'paid'
        self.remaining_amount = Decimal('0')

        if payment_voucher:
            self.payment_voucher = payment_voucher

        self.save()

    def record_payment(self, amount, payment_date=None, payment_voucher=None):
        """
        تسجيل دفعة من العمولة

        Args:
            amount: مبلغ الدفعة
            payment_date: تاريخ الدفع (افتراضياً اليوم)
            payment_voucher: سند الصرف المرتبط (اختياري)
        """
        from django.utils import timezone

        # التحقق من أن المبلغ صحيح
        if amount <= 0:
            raise ValidationError(_('مبلغ الدفعة يجب أن يكون أكبر من صفر'))

        if amount > self.remaining_amount:
            raise ValidationError(_('مبلغ الدفعة لا يمكن أن يتجاوز المبلغ المتبقي'))

        # تسجيل الدفعة
        self.paid_amount += amount
        self.payment_date = payment_date or timezone.now().date()

        if payment_voucher:
            self.payment_voucher = payment_voucher

        self.save()

    @staticmethod
    def create_from_invoice(invoice):
        """
        إنشاء عمولة تلقائياً من فاتورة مبيعات

        Args:
            invoice: فاتورة المبيعات

        Returns:
            SalespersonCommission: العمولة المنشأة أو None
        """
        # التحقق من وجود مندوب ونسبة عمولة
        if not invoice.salesperson or invoice.salesperson_commission_rate == 0:
            return None

        # التحقق من عدم وجود عمولة مسبقاً
        if hasattr(invoice, 'commission'):
            return invoice.commission

        # إنشاء العمولة
        commission = SalespersonCommission.objects.create(
            company=invoice.company,
            branch=invoice.branch,
            salesperson=invoice.salesperson,
            invoice=invoice,
            commission_rate=invoice.salesperson_commission_rate,
            base_amount=invoice.total_with_tax,
            created_by=invoice.created_by
        )

        return commission


# ========================================

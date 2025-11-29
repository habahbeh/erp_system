# apps/inventory/models.py
"""
نماذج المخازن
يحتوي على: سندات الإدخال/الإخراج، التحويلات بين المخازن، الجرد، حركة المواد
"""

import logging
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.core.models import BaseModel, DocumentBaseModel, Item, Warehouse, BusinessPartner, User
from apps.accounting.models import Account, JournalEntry

logger = logging.getLogger(__name__)


class StockDocument(DocumentBaseModel):
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
        BusinessPartner,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        verbose_name=_('المورد'),
        related_name='stock_ins'
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
        permissions = [
            ('can_post_stock_document', _('يمكنه ترحيل سندات المخزون')),
        ]

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

    # ✅ **إضافة دالة الترحيل:**
    @transaction.atomic
    def post(self, user=None, create_journal_entry=True):
        """ترحيل السند وتحديث المخزون

        Args:
            user: المستخدم الذي يقوم بالترحيل
            create_journal_entry: إنشاء قيد محاسبي (افتراضي True)
                                  استخدم False عند الترحيل من فاتورة مشتريات
        """
        from django.utils import timezone

        if self.is_posted:
            raise ValidationError(_('السند مرحل مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في السند'))

        # تحديث رصيد كل مادة
        for line in self.lines.all():
            # التحقق من صحة البيانات
            line.full_clean()

            # الحصول على أو إنشاء رصيد المادة
            stock, created = ItemStock.objects.get_or_create(
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                company=self.company,
                defaults={
                    'quantity': 0,
                    'reserved_quantity': 0,
                    'average_cost': line.unit_cost,
                    'total_value': 0,
                    'created_by': user or self.created_by
                }
            )

            # حساب متوسط التكلفة الجديد (Weighted Average)
            old_quantity = stock.quantity
            old_value = stock.total_value
            new_quantity = old_quantity + line.quantity
            new_value = old_value + line.total_cost

            if new_quantity > 0:
                stock.average_cost = new_value / new_quantity

            # تحديث الكمية والقيمة
            stock.quantity = new_quantity
            stock.total_value = new_value
            stock.last_movement_date = timezone.now()
            stock.save()

            # تحديث معلومات آخر شراء
            stock.update_last_purchase(
                price=line.unit_cost,
                total=line.total_cost,
                date=self.date,
                supplier=self.supplier if hasattr(self, 'supplier') else None
            )

            # تحديث آخر سعر شراء للمورد
            if self.supplier:
                from apps.core.models import PartnerItemPrice
                partner_price, created = PartnerItemPrice.objects.get_or_create(
                    company=self.company,
                    partner=self.supplier,
                    item=line.item,
                    item_variant=line.item_variant,
                    defaults={
                        'created_by': user or self.created_by
                    }
                )
                partner_price.update_purchase_price(
                    price=line.unit_cost,
                    quantity=line.quantity,
                    date=self.date
                )

            # إنشاء حركة المادة
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='in',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
                total_cost=line.total_cost,
                balance_before=old_quantity,
                balance_quantity=stock.quantity,
                balance_value=stock.total_value,
                reference_type='stock_in',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )

            # إنشاء دفعة إذا تم تحديد رقم الدفعة
            if hasattr(line, 'batch_number') and line.batch_number:
                Batch.objects.create(
                    company=self.company,
                    item=line.item,
                    item_variant=line.item_variant,
                    warehouse=self.warehouse,
                    batch_number=line.batch_number,
                    manufacturing_date=getattr(line, 'manufacturing_date', None),
                    expiry_date=getattr(line, 'expiry_date', None),
                    quantity=line.quantity,
                    reserved_quantity=Decimal('0'),
                    unit_cost=line.unit_cost,
                    total_value=line.total_cost,
                    source_document='stock_in',
                    source_id=self.pk,
                    received_date=self.date,
                    created_by=user or self.created_by
                )

        # إنشاء القيد المحاسبي (إذا كان مطلوباً)
        if create_journal_entry and not self.journal_entry:
            self.create_journal_entry(user)

        # تحديث حالة السند
        self.is_posted = True
        self.posted_date = timezone.now()
        self.posted_by = user
        self.save()

    # ✅ **دالة إنشاء القيد المحاسبي:**
    def create_journal_entry(self, user=None):
        """إنشاء القيد المحاسبي للسند"""
        from apps.accounting.models import JournalEntry, JournalEntryLine
        from apps.accounting.models import FiscalYear, AccountingPeriod

        # الحصول على السنة والفترة المالية
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            # السند بدون قيد محاسبي
            return None

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=getattr(self, 'branch', None),
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"سند إدخال رقم {self.number} - {self.get_source_type_display()}",
            reference=self.number,
            source_document='stock_in',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # تجميع السطور حسب حساب المخزون
        from collections import defaultdict
        inventory_accounts = defaultdict(lambda: {'debit': 0, 'items': []})

        for line in self.lines.all():
            # Skip lines without items
            if not line.item:
                continue

            # حساب المخزون من المادة
            inventory_account = line.item.inventory_account if hasattr(line.item, 'inventory_account') else None

            # إذا لم يكن للمادة حساب مخزون، استخدم الحساب الافتراضي
            if not inventory_account:
                from apps.accounting.models import Account
                try:
                    inventory_account = Account.objects.get(company=self.company, code='120000')
                except Account.DoesNotExist:
                    continue

            if inventory_account:
                inventory_accounts[inventory_account]['debit'] += line.total_cost
                inventory_accounts[inventory_account]['items'].append(line.item.name)

        # إنشاء سطر لكل حساب مخزون (مدين)
        for account, data in inventory_accounts.items():
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=account,
                description=f"إدخال مخزون - {', '.join(data['items'][:3])}",
                debit_amount=data['debit'],
                credit_amount=0,
                currency=self.company.base_currency,
                reference=self.number
            )
            line_number += 1

        # الطرف الدائن (حسب المصدر)
        from apps.accounting.models import Account

        credit_account = None
        credit_description = ""
        partner_type = None
        partner_id = None
        total_amount = sum(data['debit'] for data in inventory_accounts.values())

        if self.source_type == 'purchase':
            # حساب المورد (دائن)
            if self.supplier:
                # محاولة الحصول على حساب المورد
                if hasattr(self.supplier, 'supplier_account') and self.supplier.supplier_account:
                    credit_account = self.supplier.supplier_account
                else:
                    # استخدام حساب الموردين الافتراضي
                    try:
                        credit_account = Account.objects.get(company=self.company, code='210000')
                    except Account.DoesNotExist:
                        pass

                if credit_account:
                    credit_description = f"شراء من {self.supplier.name}"
                    partner_type = 'supplier'
                    partner_id = self.supplier.pk

        elif self.source_type == 'opening':
            # حساب الأرباح المحتجزة (رصيد افتتاحي)
            try:
                credit_account = Account.objects.get(company=self.company, code='320101')
                credit_description = "رصيد افتتاحي للمخزون"
            except Account.DoesNotExist:
                # استخدام حساب حقوق الملكية العام
                try:
                    credit_account = Account.objects.get(company=self.company, code='3')
                    credit_description = "رصيد افتتاحي للمخزون"
                except Account.DoesNotExist:
                    pass

        elif self.source_type == 'return':
            # حساب العملاء (مرتجع مبيعات)
            try:
                credit_account = Account.objects.get(company=self.company, code='1102')
                credit_description = "مرتجع مبيعات"
            except Account.DoesNotExist:
                pass

        elif self.source_type == 'production':
            # حساب تكلفة الإنتاج
            try:
                credit_account = Account.objects.get(company=self.company, code='5')
                credit_description = "إنتاج"
            except Account.DoesNotExist:
                pass

        elif self.source_type == 'adjustment':
            # حساب فروقات جرد (تسوية)
            try:
                credit_account = Account.objects.get(company=self.company, code='5')
                credit_description = "تسوية مخزون"
            except Account.DoesNotExist:
                pass

        else:  # other
            # حساب افتراضي
            try:
                credit_account = Account.objects.get(company=self.company, code='3')
                credit_description = "إدخال مخزون - أخرى"
            except Account.DoesNotExist:
                pass

        # إنشاء سطر القيد الدائن
        if credit_account:
            line_data = {
                'journal_entry': journal_entry,
                'line_number': line_number,
                'account': credit_account,
                'description': credit_description,
                'debit_amount': 0,
                'credit_amount': total_amount,
                'currency': self.company.base_currency,
                'reference': self.number,
            }

            # إضافة معلومات الشريك إذا كانت موجودة
            if partner_type:
                line_data['partner_type'] = partner_type
            if partner_id:
                line_data['partner_id'] = partner_id

            JournalEntryLine.objects.create(**line_data)

        # ترحيل القيد
        journal_entry.post(user=user)

        # ربط القيد بالسند
        self.journal_entry = journal_entry
        self.save()

        return journal_entry

    # ✅ **دالة إلغاء الترحيل:**
    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل السند"""
        if not self.is_posted:
            raise ValidationError(_('السند غير مرحل'))

        # عكس الحركات المخزنية
        for line in self.lines.all():
            # الحصول على رصيد المادة
            try:
                stock = ItemStock.objects.get(
                    item=line.item,
                    item_variant=line.item_variant,
                    warehouse=self.warehouse,
                    company=self.company
                )

                # التحقق من إمكانية الإلغاء
                if stock.quantity < line.quantity:
                    raise ValidationError(
                        f'لا يمكن إلغاء السند: الكمية المتاحة من {line.item.name} أقل من المطلوب'
                    )

                # حساب القيمة الجديدة
                old_quantity = stock.quantity
                old_value = stock.total_value
                new_quantity = old_quantity - line.quantity
                new_value = old_value - line.total_cost

                # حساب متوسط التكلفة الجديد
                if new_quantity > 0:
                    stock.average_cost = new_value / new_quantity
                else:
                    stock.average_cost = 0

                # تحديث الرصيد
                stock.quantity = new_quantity
                stock.total_value = new_value
                stock.save()

                # حذف حركة المادة
                StockMovement.objects.filter(
                    reference_type='stock_in',
                    reference_id=self.pk,
                    item=line.item,
                    item_variant=line.item_variant
                ).delete()

            except ItemStock.DoesNotExist:
                raise ValidationError(f'رصيد المادة {line.item.name} غير موجود')

        # إلغاء القيد المحاسبي
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()
            self.journal_entry = None

        # تحديث حالة السند
        self.is_posted = False
        self.posted_date = None
        self.posted_by = None
        self.save()

    # ✅ **دوال التحقق من الصلاحيات:**
    def can_edit(self):
        """هل يمكن تعديل السند"""
        return not self.is_posted

    def can_post(self):
        """هل يمكن ترحيل السند"""
        if self.is_posted:
            return False
        if not self.lines.exists():
            return False
        return True

    def can_delete(self):
        """هل يمكن حذف السند"""
        return not self.is_posted

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
        BusinessPartner,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'partner_type__in': ['customer', 'both']},
        verbose_name=_('العميل'),
        related_name='stock_outs'
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

    # ✅ **إضافة دالة الترحيل:**
    @transaction.atomic
    def post(self, user=None):
        """ترحيل السند وتحديث المخزون"""
        from django.utils import timezone

        if self.is_posted:
            raise ValidationError(_('السند مرحل مسبقاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في السند'))

        # تحديث رصيد كل مادة
        for line in self.lines.all():
            # التحقق من صحة البيانات
            line.full_clean()

            # الحصول على رصيد المادة أو إنشاؤه إذا كان المخزون السالب مسموحاً
            try:
                stock = ItemStock.objects.get(
                    item=line.item,
                    item_variant=line.item_variant,
                    warehouse=self.warehouse,
                    company=self.company
                )
            except ItemStock.DoesNotExist:
                if self.warehouse.allow_negative_stock:
                    # إنشاء سجل مخزون جديد بكمية صفر إذا كان المخزون السالب مسموحاً
                    stock = ItemStock.objects.create(
                        item=line.item,
                        item_variant=line.item_variant,
                        warehouse=self.warehouse,
                        company=self.company,
                        quantity=Decimal('0'),
                        reserved_quantity=Decimal('0'),
                        average_cost=line.unit_cost or Decimal('0'),
                        total_value=Decimal('0'),
                        created_by=user or self.created_by
                    )
                else:
                    raise ValidationError(
                        f'لا يوجد رصيد للمادة {line.item.name} في المستودع {self.warehouse.name}'
                    )

            # التحقق من الكمية المتاحة
            available_quantity = stock.quantity - stock.reserved_quantity

            # التحقق من السماح بالرصيد السالب
            if not self.warehouse.allow_negative_stock:
                if available_quantity < line.quantity:
                    raise ValidationError(
                        f'الكمية المتاحة من {line.item.name} ({available_quantity}) '
                        f'أقل من المطلوب ({line.quantity}). '
                        f'المستودع "{self.warehouse.name}" لا يسمح بالرصيد السالب.'
                    )
            else:
                # تحذير فقط
                if available_quantity < line.quantity:
                    logger.warning(
                        f'Negative stock will occur for {line.item.name} '
                        f'in warehouse {self.warehouse.name}. '
                        f'Available: {available_quantity}, Required: {line.quantity}'
                    )

            # حساب القيمة (بمتوسط التكلفة)
            line.unit_cost = stock.average_cost
            line.total_cost = line.quantity * stock.average_cost
            line.save()

            # تحديث الكمية والقيمة
            old_quantity = stock.quantity
            old_value = stock.total_value
            new_quantity = old_quantity - line.quantity
            new_value = old_value - line.total_cost

            stock.quantity = new_quantity
            stock.total_value = new_value
            stock.last_movement_date = timezone.now()
            stock.save()

            # إنشاء حركة المادة
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='out',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                quantity=-line.quantity,  # سالب للإخراج
                unit_cost=line.unit_cost,
                total_cost=-line.total_cost,
                balance_before=old_quantity,
                balance_quantity=stock.quantity,
                balance_value=stock.total_value,
                reference_type='stock_out',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )

            # تحديث آخر سعر بيع للعميل
            if self.customer:
                from apps.core.models import PartnerItemPrice
                # استخدام السعر من قائمة الأسعار إذا كان موجوداً
                sale_price = line.unit_cost  # Default to cost price
                if self.customer.default_price_list:
                    from apps.core.models import get_item_price
                    price_info = get_item_price(
                        item=line.item,
                        variant=line.item_variant,
                        price_list=self.customer.default_price_list,
                        quantity=line.quantity,
                        check_date=self.date
                    )
                    if price_info:
                        sale_price = price_info['price']

                partner_price, created = PartnerItemPrice.objects.get_or_create(
                    company=self.company,
                    partner=self.customer,
                    item=line.item,
                    item_variant=line.item_variant,
                    defaults={
                        'created_by': user or self.created_by
                    }
                )
                partner_price.update_sale_price(
                    price=sale_price,
                    quantity=line.quantity,
                    date=self.date
                )

        # إنشاء القيد المحاسبي (إذا كان مطلوباً)
        if not self.journal_entry:
            self.create_journal_entry(user)

        # تحديث حالة السند
        self.is_posted = True
        self.posted_date = timezone.now()
        self.posted_by = user
        self.save()

    # ✅ **دالة إنشاء القيد المحاسبي:**
    def create_journal_entry(self, user=None):
        """إنشاء القيد المحاسبي للسند"""
        from apps.accounting.models import JournalEntry, JournalEntryLine
        from apps.accounting.models import FiscalYear, AccountingPeriod

        # الحصول على السنة والفترة المالية
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            return None

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=getattr(self, 'branch', None),
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"سند إخراج رقم {self.number} - {self.get_destination_type_display()}",
            reference=self.number,
            source_document='stock_out',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # تجميع السطور حسب الحسابات
        from collections import defaultdict
        cost_accounts = defaultdict(lambda: {'debit': 0, 'items': []})
        inventory_accounts = defaultdict(lambda: {'credit': 0})

        for line in self.lines.all():
            # Skip lines without items
            if not line.item:
                continue

            # حساب تكلفة البضاعة المباعة أو المصروف
            if self.destination_type == 'sales':
                cost_account = line.item.cost_of_goods_account if hasattr(line.item, 'cost_of_goods_account') else None
            else:
                cost_account = line.item.inventory_account if hasattr(line.item, 'inventory_account') else None

            if cost_account:
                cost_accounts[cost_account]['debit'] += line.total_cost
                cost_accounts[cost_account]['items'].append(line.item.name)

            # حساب المخزون (دائن)
            inventory_account = line.item.inventory_account if hasattr(line.item, 'inventory_account') else None
            if inventory_account:
                inventory_accounts[inventory_account]['credit'] += line.total_cost

        # سطور تكلفة البضاعة/المصروف (مدين)
        for account, data in cost_accounts.items():
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=account,
                description=f"تكلفة - {', '.join(data['items'][:3])}",
                debit_amount=data['debit'],
                credit_amount=0,
                currency=self.company.base_currency,
                reference=self.number
            )
            line_number += 1

        # سطور المخزون (دائن)
        for account, data in inventory_accounts.items():
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=account,
                description=f"إخراج مخزون",
                debit_amount=0,
                credit_amount=data['credit'],
                currency=self.company.base_currency,
                reference=self.number
            )
            line_number += 1

        # ترحيل القيد
        journal_entry.post(user=user)

        # ربط القيد بالسند
        self.journal_entry = journal_entry
        self.save()

        return journal_entry

    # ✅ **دالة إلغاء الترحيل:**
    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل السند"""
        if not self.is_posted:
            raise ValidationError(_('السند غير مرحل'))

        # عكس الحركات المخزنية
        for line in self.lines.all():
            # الحصول على رصيد المادة
            try:
                stock = ItemStock.objects.get(
                    item=line.item,
                    item_variant=line.item_variant,
                    warehouse=self.warehouse,
                    company=self.company
                )

                # إعادة الكمية والقيمة
                old_quantity = stock.quantity
                old_value = stock.total_value
                new_quantity = old_quantity + line.quantity
                new_value = old_value + line.total_cost

                # حساب متوسط التكلفة
                if new_quantity > 0:
                    stock.average_cost = new_value / new_quantity

                stock.quantity = new_quantity
                stock.total_value = new_value
                stock.save()

                # حذف حركة المادة
                StockMovement.objects.filter(
                    reference_type='stock_out',
                    reference_id=self.pk,
                    item=line.item,
                    item_variant=line.item_variant
                ).delete()

            except ItemStock.DoesNotExist:
                raise ValidationError(f'رصيد المادة {line.item.name} غير موجود')

        # إلغاء القيد المحاسبي
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()
            self.journal_entry = None

        # تحديث حالة السند
        self.is_posted = False
        self.posted_date = None
        self.posted_by = None
        self.save()

    # ✅ **دوال التحقق من الصلاحيات:**
    def can_edit(self):
        """هل يمكن تعديل السند"""
        return not self.is_posted

    def can_post(self):
        """هل يمكن ترحيل السند"""
        if self.is_posted:
            return False
        if not self.lines.exists():
            return False
        return True

    def can_delete(self):
        """هل يمكن حذف السند"""
        return not self.is_posted

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

    # ✅ **إضافة المتغير:**
    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='stock_document_lines',
        help_text=_('للمواد ذات المتغيرات')
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
        permissions = [
            ('can_approve_transfer', _('يمكنه اعتماد التحويلات')),
        ]

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

    # ✅ **دالة الاعتماد:**
    def approve(self, user):
        """اعتماد التحويل"""
        from django.utils import timezone

        if self.status != 'draft':
            raise ValidationError(_('يمكن اعتماد المسودات فقط'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في التحويل'))

        # التحقق من الصلاحية
        if not user.has_perm('inventory.can_approve_transfer'):
            raise ValidationError(_('ليس لديك صلاحية اعتماد التحويلات'))

        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    # ✅ **دالة الإرسال (الإخراج من المستودع المصدر):**
    @transaction.atomic
    def send(self, user=None):
        """إرسال التحويل (إخراج من المستودع المصدر)"""
        from django.utils import timezone

        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد التحويل أولاً'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في التحويل'))

        # التحقق والإخراج من المستودع المصدر
        for line in self.lines.all():
            line.full_clean()

            # الحصول على رصيد المادة في المستودع المصدر
            try:
                source_stock = ItemStock.objects.get(
                    item=line.item,
                    item_variant=line.item_variant,
                    warehouse=self.warehouse,  # المستودع المصدر
                    company=self.company
                )
            except ItemStock.DoesNotExist:
                raise ValidationError(
                    f'لا يوجد رصيد للمادة {line.item.name} في المستودع {self.warehouse.name}'
                )

            # التحقق من الكمية المتاحة
            available_quantity = source_stock.quantity - source_stock.reserved_quantity
            if available_quantity < line.quantity:
                raise ValidationError(
                    f'الكمية المتاحة من {line.item.name} ({available_quantity}) '
                    f'أقل من المطلوب ({line.quantity})'
                )

            # حساب القيمة (بمتوسط التكلفة)
            line.unit_cost = source_stock.average_cost
            line.total_cost = line.quantity * source_stock.average_cost
            line.save()

            # إخراج من المستودع المصدر
            old_quantity = source_stock.quantity
            old_value = source_stock.total_value
            new_quantity = old_quantity - line.quantity
            new_value = old_value - line.total_cost

            source_stock.quantity = new_quantity
            source_stock.total_value = new_value
            source_stock.last_movement_date = timezone.now()
            source_stock.save()

            # إنشاء حركة الإخراج
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='transfer_out',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                quantity=-line.quantity,  # سالب للإخراج
                unit_cost=line.unit_cost,
                total_cost=-line.total_cost,
                balance_before=old_quantity,
                balance_quantity=source_stock.quantity,
                balance_value=source_stock.total_value,
                reference_type='stock_transfer',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )

        # تحديث حالة التحويل
        self.status = 'in_transit'
        self.is_posted = True
        self.posted_date = timezone.now()
        self.posted_by = user
        self.save()

    # ✅ **دالة الاستلام (الإدخال للمستودع الهدف):**
    @transaction.atomic
    def receive(self, user=None):
        """استلام التحويل (إدخال للمستودع الهدف)"""
        from django.utils import timezone

        if self.status != 'in_transit':
            raise ValidationError(_('التحويل ليس في الطريق'))

        # الإدخال للمستودع الهدف
        for line in self.lines.all():
            # الحصول على أو إنشاء رصيد المادة في المستودع الهدف
            dest_stock, created = ItemStock.objects.get_or_create(
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.destination_warehouse,
                company=self.company,
                defaults={
                    'quantity': 0,
                    'reserved_quantity': 0,
                    'average_cost': line.unit_cost,
                    'total_value': 0,
                    'created_by': user or self.created_by
                }
            )

            # حساب الكمية المستلمة (قد تكون أقل من المرسلة)
            received_qty = line.received_quantity or line.quantity
            received_cost = received_qty * line.unit_cost

            # حساب متوسط التكلفة الجديد (Weighted Average)
            old_quantity = dest_stock.quantity
            old_value = dest_stock.total_value
            new_quantity = old_quantity + received_qty
            new_value = old_value + received_cost

            if new_quantity > 0:
                dest_stock.average_cost = new_value / new_quantity

            # تحديث الكمية والقيمة
            dest_stock.quantity = new_quantity
            dest_stock.total_value = new_value
            dest_stock.last_movement_date = timezone.now()
            dest_stock.save()

            # تحديث الكمية المستلمة في السطر
            line.received_quantity = received_qty
            line.save()

            # إنشاء حركة الإدخال
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='transfer_in',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.destination_warehouse,
                quantity=received_qty,
                unit_cost=line.unit_cost,
                total_cost=received_cost,
                balance_before=old_quantity,
                balance_quantity=dest_stock.quantity,
                balance_value=dest_stock.total_value,
                reference_type='stock_transfer',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )

        # تحديث حالة التحويل
        self.status = 'received'
        self.received_by = user
        self.received_date = timezone.now()
        self.save()

    # ✅ **دالة الإلغاء:**
    @transaction.atomic
    def cancel(self, user=None):
        """إلغاء التحويل"""
        if self.status == 'received':
            raise ValidationError(_('لا يمكن إلغاء تحويل مستلم'))

        if self.status == 'in_transit':
            # إعادة الكميات للمستودع المصدر
            for line in self.lines.all():
                try:
                    source_stock = ItemStock.objects.get(
                        item=line.item,
                        item_variant=line.item_variant,
                        warehouse=self.warehouse,
                        company=self.company
                    )

                    # إعادة الكمية والقيمة
                    old_quantity = source_stock.quantity
                    old_value = source_stock.total_value
                    new_quantity = old_quantity + line.quantity
                    new_value = old_value + line.total_cost

                    if new_quantity > 0:
                        source_stock.average_cost = new_value / new_quantity

                    source_stock.quantity = new_quantity
                    source_stock.total_value = new_value
                    source_stock.save()

                    # حذف حركات التحويل
                    StockMovement.objects.filter(
                        reference_type='stock_transfer',
                        reference_id=self.pk,
                        item=line.item,
                        item_variant=line.item_variant
                    ).delete()

                except ItemStock.DoesNotExist:
                    pass

        # تحديث الحالة
        self.status = 'cancelled'
        self.save()

    # ✅ **دوال التحقق من الصلاحيات:**
    def can_edit(self):
        """هل يمكن تعديل التحويل"""
        return self.status in ['draft', 'pending']

    def can_post(self):
        """هل يمكن إرسال التحويل"""
        if self.status != 'approved':
            return False
        if not self.lines.exists():
            return False
        return True

    def can_delete(self):
        """هل يمكن حذف التحويل"""
        return self.status == 'draft'

    def can_approve(self):
        """هل يمكن اعتماد التحويل"""
        if self.status != 'draft':
            return False
        if not self.lines.exists():
            return False
        return True

    def can_cancel(self):
        """هل يمكن إلغاء التحويل"""
        return self.status != 'received'

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

    # ✅ **إضافة المتغير:**
    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='stock_transfer_lines',
        help_text=_('للمواد ذات المتغيرات')
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

    # ✅ **إضافة معلومات الدفعة:**
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
        verbose_name = _('سطر تحويل')
        verbose_name_plural = _('سطور التحويلات')

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
        """حساب الإجمالي والباركود"""
        if self.item and not self.barcode:
            # استخدم باركود المتغير إذا وجد، وإلا باركود المادة
            if self.item_variant and self.item_variant.barcode:
                self.barcode = self.item_variant.barcode
            else:
                self.barcode = self.item.barcode or ''

        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class StockMovement(BaseModel):
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

    # ✅ **إضافة المتغير:**
    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='stock_movements'
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

    # الرصيد قبل وبعد الحركة
    balance_before = models.DecimalField(
        _('رصيد الكمية قبل الحركة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text=_('الرصيد قبل تطبيق هذه الحركة')
    )

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


    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )



    class Meta:
        verbose_name = _('حركة مادة')
        verbose_name_plural = _('حركة المواد')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['item', 'warehouse', '-date']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['movement_type', '-date']),
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
        related_name='inventory_supervised_counts'
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
            ('processed', _('معالج')),
            ('cancelled', _('ملغي')),
        ],
        default='planned'
    )

    # تواريخ سير العمل
    started_at = models.DateTimeField(
        _('تاريخ البدء'),
        null=True,
        blank=True,
        help_text=_('تاريخ بدء عملية الجرد')
    )

    completed_at = models.DateTimeField(
        _('تاريخ الإتمام'),
        null=True,
        blank=True,
        help_text=_('تاريخ إتمام عملية الجرد')
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

    # المعالجة (تحديث المخزون)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('عولج بواسطة'),
        related_name='processed_counts'
    )

    processed_at = models.DateTimeField(
        _('تاريخ المعالجة'),
        null=True,
        blank=True,
        help_text=_('تاريخ معالجة الجرد وتحديث المخزون')
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
        """توليد رقم الجرد مع التحقق من منع التعديل بعد الاعتماد"""
        # منع تغيير الحالة بعد الاعتماد (إلا للمعالجة)
        if self.pk:
            old_instance = StockCount.objects.filter(pk=self.pk).first()
            if old_instance:
                # منع تعديل جرد معتمد (إلا التغيير إلى processed)
                if old_instance.status == 'approved':
                    update_fields = kwargs.get('update_fields', None)
                    if update_fields is None or 'status' in update_fields:
                        # السماح بالتغيير من approved إلى processed فقط
                        if self.status != 'approved' and self.status != 'processed':
                            from django.core.exceptions import ValidationError
                            raise ValidationError(_('لا يمكن تعديل جرد معتمد'))

                # منع تعديل جرد معالج نهائياً
                if old_instance.status == 'processed':
                    update_fields = kwargs.get('update_fields', None)
                    if update_fields is None or 'status' in update_fields:
                        if self.status != 'processed':
                            from django.core.exceptions import ValidationError
                            raise ValidationError(_('لا يمكن تعديل جرد معالج'))

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

    def populate_lines(self):
        """ملء سطور الجرد من أرصدة المستودع"""
        if self.status not in ['planned', 'in_progress']:
            raise ValueError(_('لا يمكن ملء السطور إلا للجرد المخطط أو الجاري'))

        # حذف السطور الحالية
        self.lines.all().delete()

        # جلب أرصدة المواد في المستودع
        stocks = ItemStock.objects.filter(
            company=self.company,
            warehouse=self.warehouse,
            quantity__gt=0
        ).select_related('item')

        lines_created = []
        for stock in stocks:
            line = StockCountLine.objects.create(
                count=self,
                item=stock.item,
                system_quantity=stock.quantity,
                counted_quantity=stock.quantity,  # افتراضياً نفس الكمية
                unit_cost=stock.average_cost or Decimal('0')
            )
            lines_created.append(line)

        return lines_created

    def cancel(self):
        """إلغاء الجرد"""
        if self.status in ['approved']:
            raise ValueError(_('لا يمكن إلغاء جرد معتمد'))

        self.status = 'cancelled'
        self.save(update_fields=['status'])

    @transaction.atomic
    def process_adjustments(self, user=None):
        """معالجة تسويات الجرد وإنشاء قيد التسوية"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine
        from apps.accounting.models import FiscalYear, AccountingPeriod, Account

        if self.status not in ['completed']:
            raise ValueError(_('يجب أن يكون الجرد مكتمل لمعالجة التسويات'))

        # الحصول على السنة والفترة المالية
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValueError(_('لا توجد سنة مالية مفتوحة للتاريخ المحدد'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        # حساب إجمالي التسويات
        total_adjustment = sum(
            line.difference_value for line in self.lines.all()
        )

        if total_adjustment == Decimal('0'):
            self.status = 'approved'
            self.approval_date = timezone.now()
            self.approved_by = user
            self.save()
            return None

        # الحصول على الفرع (من المستودع أو الفرع الرئيسي)
        from apps.core.models import Branch
        branch = getattr(self.warehouse, 'branch', None)
        if not branch:
            branch = Branch.objects.filter(company=self.company, is_main=True).first()
        if not branch:
            branch = Branch.objects.filter(company=self.company).first()

        # إنشاء قيد التسوية
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"تسوية جرد رقم {self.number}",
            reference=self.number,
            source_document='stock_count',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1
        abs_total = abs(total_adjustment)

        # حساب المخزون
        inventory_account = Account.objects.filter(
            company=self.company,
            code='120000'
        ).first()

        # حساب فروقات الجرد
        adjustment_account = Account.objects.filter(
            company=self.company,
            code__in=['560000', '510000']  # حساب فروقات الجرد أو تكلفة البضاعة
        ).first()

        if not adjustment_account:
            adjustment_account = inventory_account

        if total_adjustment < 0:  # نقص
            # مدين: فروقات الجرد (مصروف)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=adjustment_account,
                description='نقص في الجرد',
                debit_amount=abs_total,
                credit_amount=Decimal('0'),
                currency=self.company.base_currency
            )
            line_number += 1

            # دائن: المخزون
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=inventory_account,
                description='تسوية نقص المخزون',
                debit_amount=Decimal('0'),
                credit_amount=abs_total,
                currency=self.company.base_currency
            )
        else:  # زيادة
            # مدين: المخزون
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=inventory_account,
                description='تسوية زيادة المخزون',
                debit_amount=abs_total,
                credit_amount=Decimal('0'),
                currency=self.company.base_currency
            )
            line_number += 1

            # دائن: فروقات الجرد (إيراد)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=adjustment_account,
                description='زيادة في الجرد',
                debit_amount=Decimal('0'),
                credit_amount=abs_total,
                currency=self.company.base_currency
            )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث حالة الجرد
        self.status = 'approved'
        self.approval_date = timezone.now()
        self.approved_by = user
        self.adjustment_entry = journal_entry
        self.save()

        # تحديث أرصدة المخزون
        for line in self.lines.all():
            if line.difference_quantity != Decimal('0'):
                try:
                    stock = ItemStock.objects.get(
                        company=self.company,
                        item=line.item,
                        warehouse=self.warehouse
                    )
                    stock.quantity = line.counted_quantity
                    stock.total_value = line.counted_value
                    if stock.quantity > 0:
                        stock.average_cost = stock.total_value / stock.quantity
                    stock.save()
                except ItemStock.DoesNotExist:
                    pass

        return journal_entry

    # ✅ **دوال التحقق من الصلاحيات:**
    def can_edit(self):
        """هل يمكن تعديل الجرد"""
        return self.status in ['planned', 'in_progress']

    def can_delete(self):
        """هل يمكن حذف الجرد"""
        return self.status == 'planned'

    def can_process(self):
        """هل يمكن معالجة الجرد"""
        if self.status != 'completed':
            return False
        if not self.lines.exists():
            return False
        return True

    def can_cancel(self):
        """هل يمكن إلغاء الجرد"""
        return self.status not in ['approved']


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

    @property
    def has_difference(self):
        """هل يوجد فرق بين الكمية الفعلية والنظام؟"""
        return self.difference_quantity != Decimal('0')


class ItemStock(BaseModel):
    """رصيد المواد في المستودعات"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name=_('المادة')
    )

    # ✅ **إضافة المتغير:**
    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('المتغير'),
        related_name='stock_records'
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

    # الرصيد الافتتاحي
    opening_balance = models.DecimalField(
        _('الرصيد الافتتاحي'),
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text=_('الرصيد عند بداية الفترة المالية')
    )

    opening_value = models.DecimalField(
        _('قيمة الرصيد الافتتاحي'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    # معلومات آخر عملية شراء
    last_purchase_price = models.DecimalField(
        _('آخر سعر شراء للوحدة'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('سعر الوحدة في آخر عملية شراء')
    )

    last_purchase_total = models.DecimalField(
        _('آخر سعر شراء إجمالي'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('إجمالي تكلفة آخر عملية شراء')
    )

    last_purchase_date = models.DateField(
        _('تاريخ آخر شراء'),
        null=True,
        blank=True
    )

    last_supplier = models.ForeignKey(
        'core.BusinessPartner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('آخر مورد'),
        related_name='last_supplied_stocks',
        limit_choices_to={'partner_type__in': ['supplier', 'both']}
    )

    # حدود المخزون
    min_level = models.DecimalField(
        _('الحد الأدنى للمخزون'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('عند الوصول لهذا الحد يتم التنبيه')
    )

    max_level = models.DecimalField(
        _('الحد الأقصى للمخزون'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('الحد الأقصى المسموح للتخزين')
    )

    reorder_point = models.DecimalField(
        _('نقطة إعادة الطلب'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('عند الوصول لهذه النقطة يتم طلب المزيد')
    )

    # موقع التخزين
    storage_location = models.CharField(
        _('موقع التخزين'),
        max_length=100,
        blank=True,
        help_text=_('الرف أو المنطقة في المستودع')
    )

    # Optimistic Locking - حماية من Race Conditions
    version = models.IntegerField(
        _('رقم الإصدار'),
        default=0,
        help_text=_('يستخدم لمنع التحديثات المتزامنة (Optimistic Locking)')
    )

    class Meta:
        verbose_name = _('رصيد مادة')
        verbose_name_plural = _('أرصدة المواد')
        unique_together = [['item', 'item_variant', 'warehouse', 'company']]
        indexes = [
            models.Index(fields=['item', 'warehouse']),
            models.Index(fields=['item', 'item_variant', 'warehouse']),
        ]

    def save(self, *args, **kwargs):
        """
        حفظ مع Optimistic Locking لمنع Race Conditions

        يتحقق من رقم الإصدار قبل التحديث، وإذا تغير (تحديث متزامن)
        يرفع ConcurrencyError
        """
        from django.db.models import F

        if self.pk:  # تحديث سجل موجود
            # الحصول على رقم الإصدار الحالي
            current_version = self.version

            # تحديث باستخدام F() expression للتحقق من الإصدار
            updated = ItemStock.objects.filter(
                pk=self.pk,
                version=current_version
            ).update(
                quantity=self.quantity,
                reserved_quantity=self.reserved_quantity,
                average_cost=self.average_cost,
                total_value=self.total_value,
                last_movement_date=self.last_movement_date,
                opening_balance=self.opening_balance,
                opening_value=self.opening_value,
                last_purchase_price=self.last_purchase_price,
                last_purchase_total=self.last_purchase_total,
                last_purchase_date=self.last_purchase_date,
                last_supplier=self.last_supplier,
                min_level=self.min_level,
                max_level=self.max_level,
                reorder_point=self.reorder_point,
                storage_location=self.storage_location,
                version=F('version') + 1  # زيادة رقم الإصدار تلقائياً
            )

            if updated == 0:
                # لم يتم التحديث = تغير رقم الإصدار = تحديث متزامن
                raise ValidationError(
                    _('حدث تضارب في التحديث. '
                      'تم تعديل هذا السجل من قبل مستخدم آخر. '
                      'يرجى إعادة المحاولة.')
                )

            # تحديث رقم الإصدار في الكائن الحالي
            self.version = current_version + 1

            # إعادة تحميل الكائن من قاعدة البيانات للحصول على القيم المحدثة
            self.refresh_from_db()

        else:  # إنشاء سجل جديد
            super().save(*args, **kwargs)

    def get_available_quantity(self):
        """الكمية المتاحة للبيع/التحويل"""
        return self.quantity - self.reserved_quantity

    def reserve_quantity(self, quantity):
        """حجز كمية (لطلبات البيع مثلاً)"""
        if self.get_available_quantity() < quantity:
            raise ValidationError(
                f'الكمية المتاحة ({self.get_available_quantity()}) '
                f'أقل من المطلوب ({quantity})'
            )

        self.reserved_quantity += quantity
        self.save()

    def release_reserved_quantity(self, quantity):
        """إلغاء حجز كمية"""
        if self.reserved_quantity < quantity:
            raise ValidationError('الكمية المحجوزة أقل من المطلوب إلغاؤه')

        self.reserved_quantity -= quantity
        self.save()

    def is_below_reorder_level(self, reorder_level=None):
        """هل الكمية أقل من حد إعادة الطلب"""
        if reorder_level is None:
            # استخدام reorder_point من الحقل الجديد
            reorder_level = self.reorder_point
        if reorder_level is None:
            return False
        return self.quantity <= reorder_level

    def update_last_purchase(self, price, total, date, supplier=None):
        """
        تحديث معلومات آخر عملية شراء

        Args:
            price: سعر الوحدة
            total: الإجمالي
            date: تاريخ الشراء
            supplier: المورد (اختياري)
        """
        self.last_purchase_price = price
        self.last_purchase_total = total
        self.last_purchase_date = date
        if supplier:
            self.last_supplier = supplier
        self.save(update_fields=[
            'last_purchase_price',
            'last_purchase_total',
            'last_purchase_date',
            'last_supplier'
        ])

    def check_reorder_needed(self):
        """
        التحقق من الحاجة لإعادة الطلب

        Returns:
            bool: True إذا كانت الكمية أقل من نقطة إعادة الطلب
        """
        if self.reorder_point:
            return self.quantity <= self.reorder_point
        return False

    def is_below_min_level(self):
        """
        التحقق من أن الرصيد أقل من الحد الأدنى

        Returns:
            bool: True إذا كانت الكمية أقل من الحد الأدنى
        """
        if self.min_level:
            return self.quantity < self.min_level
        return False

    def is_above_max_level(self):
        """
        التحقق من أن الرصيد أعلى من الحد الأقصى

        Returns:
            bool: True إذا كانت الكمية أعلى من الحد الأقصى
        """
        if self.max_level:
            return self.quantity > self.max_level
        return False

    @classmethod
    def get_total_stock(cls, item, item_variant=None, company=None):
        """الحصول على إجمالي رصيد المادة في كل المستودعات"""
        filters = {'item': item}

        if item_variant:
            filters['item_variant'] = item_variant

        if company:
            filters['company'] = company

        stocks = cls.objects.filter(**filters)

        return {
            'total_quantity': sum(s.quantity for s in stocks),
            'total_reserved': sum(s.reserved_quantity for s in stocks),
            'total_available': sum(s.get_available_quantity() for s in stocks),
            'total_value': sum(s.total_value for s in stocks),
            'warehouses_count': stocks.count()
        }

    @classmethod
    def transfer_between_warehouses(cls, item, item_variant, from_warehouse,
                                    to_warehouse, quantity, company, user=None):
        """تحويل سريع بين مستودعين (بدون إنشاء StockTransfer)"""
        from django.utils import timezone

        # الحصول على الرصيد المصدر
        try:
            source_stock = cls.objects.get(
                item=item,
                item_variant=item_variant,
                warehouse=from_warehouse,
                company=company
            )
        except cls.DoesNotExist:
            raise ValidationError('الرصيد المصدر غير موجود')

        # التحقق من الكمية
        if source_stock.get_available_quantity() < quantity:
            raise ValidationError('الكمية المتاحة غير كافية')

        # الإخراج من المصدر
        unit_cost = source_stock.average_cost
        total_cost = quantity * unit_cost

        source_stock.quantity -= quantity
        source_stock.total_value -= total_cost
        source_stock.last_movement_date = timezone.now()
        source_stock.save()

        # الإدخال للهدف
        dest_stock, created = cls.objects.get_or_create(
            item=item,
            item_variant=item_variant,
            warehouse=to_warehouse,
            company=company,
            defaults={
                'quantity': 0,
                'reserved_quantity': 0,
                'average_cost': unit_cost,
                'total_value': 0,
                'created_by': user
            }
        )

        # حساب متوسط التكلفة
        old_quantity = dest_stock.quantity
        old_value = dest_stock.total_value
        new_quantity = old_quantity + quantity
        new_value = old_value + total_cost

        if new_quantity > 0:
            dest_stock.average_cost = new_value / new_quantity

        dest_stock.quantity = new_quantity
        dest_stock.total_value = new_value
        dest_stock.last_movement_date = timezone.now()
        dest_stock.save()

        return source_stock, dest_stock

    def __str__(self):
        variant_str = f" - {self.item_variant.code}" if self.item_variant else ""
        return f"{self.item.name}{variant_str} @ {self.warehouse.name}: {self.quantity}"


class Batch(BaseModel):
    """دفعات المواد - لتتبع FIFO/LIFO"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('المادة')
    )

    item_variant = models.ForeignKey(
        'core.ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='batches',
        verbose_name=_('المتغير')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('المستودع')
    )

    batch_number = models.CharField(
        _('رقم الدفعة'),
        max_length=50
    )

    manufacturing_date = models.DateField(
        _('تاريخ الإنتاج'),
        null=True,
        blank=True
    )

    expiry_date = models.DateField(
        _('تاريخ الانتهاء'),
        null=True,
        blank=True
    )

    # الكميات
    quantity = models.DecimalField(
        _('الكمية'),
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
    unit_cost = models.DecimalField(
        _('تكلفة الوحدة'),
        max_digits=12,
        decimal_places=3
    )

    total_value = models.DecimalField(
        _('القيمة الإجمالية'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    # المصدر
    source_document = models.CharField(
        _('المستند المصدر'),
        max_length=50
    )

    source_id = models.IntegerField(
        _('رقم المصدر')
    )

    received_date = models.DateField(
        _('تاريخ الاستلام')
    )

    class Meta:
        verbose_name = _('دفعة')
        verbose_name_plural = _('الدفعات')
        unique_together = [['item', 'item_variant', 'warehouse', 'batch_number', 'company']]
        ordering = ['received_date']  # FIFO
        indexes = [
            models.Index(fields=['item', 'warehouse', 'received_date']),
            models.Index(fields=['expiry_date']),
        ]

    def is_expired(self):
        """هل الدفعة منتهية الصلاحية"""
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date

    def days_to_expiry(self):
        """عدد الأيام حتى انتهاء الصلاحية"""
        if not self.expiry_date:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.expiry_date - today
        return delta.days

    def get_expiry_status(self):
        """حالة الدفعة حسب تاريخ الانتهاء"""
        if not self.expiry_date:
            return 'no_expiry'

        days = self.days_to_expiry()

        if days < 0:
            return 'expired'
        elif days <= 30:
            return 'expiring_soon'
        elif days <= 90:
            return 'warning'
        else:
            return 'active'

    def get_available_quantity(self):
        """الكمية المتاحة"""
        return self.quantity - self.reserved_quantity

    def reserve(self, quantity):
        """حجز كمية من الدفعة"""
        available = self.get_available_quantity()
        if quantity > available:
            raise ValidationError(
                _('الكمية المطلوبة ({}) أكبر من المتاح ({})').format(quantity, available)
            )
        self.reserved_quantity += quantity
        self.save(update_fields=['reserved_quantity'])

    def release_reserved(self, quantity):
        """تحرير كمية محجوزة"""
        if quantity > self.reserved_quantity:
            raise ValidationError(
                _('الكمية المطلوب تحريرها ({}) أكبر من المحجوز ({})').format(
                    quantity, self.reserved_quantity
                )
            )
        self.reserved_quantity -= quantity
        self.save(update_fields=['reserved_quantity'])

    def clean(self):
        """التحقق من صحة البيانات مع تحذير الدفعات المنتهية"""
        super().clean()

        # تحذير إذا كانت الدفعة منتهية الصلاحية
        if self.expiry_date and self.is_expired():
            from django.contrib import messages
            import warnings
            warnings.warn(
                f'تحذير: الدفعة {self.batch_number} منتهية الصلاحية!',
                UserWarning
            )

    # ✅ **دوال التحقق من الصلاحيات:**
    def can_delete(self):
        """هل يمكن حذف الدفعة"""
        # لا يمكن حذف دفعة فيها كمية
        return self.quantity == 0 and self.reserved_quantity == 0

    def __str__(self):
        return f"{self.item.name} - {self.batch_number}"


class StockReservation(BaseModel):
    """
    حجز المخزون مع timeout
    يستخدم لحجز كميات مؤقتة (مثل عند إنشاء طلب بيع)
    """

    RESERVATION_STATUS = [
        ('active', _('نشط')),
        ('confirmed', _('مؤكد')),
        ('released', _('محرر')),
        ('expired', _('منتهي')),
    ]

    # العلاقة مع رصيد المادة
    item_stock = models.ForeignKey(
        ItemStock,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('رصيد المادة')
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
        verbose_name=_('المتغير')
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name=_('المستودع')
    )

    # الكمية المحجوزة
    quantity = models.DecimalField(
        _('الكمية المحجوزة'),
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    # المرجع (طلب البيع، عرض السعر، إلخ)
    reference_type = models.CharField(
        _('نوع المرجع'),
        max_length=50,
        help_text=_('مثل: sales_order, quotation')
    )

    reference_id = models.IntegerField(
        _('رقم المرجع')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=RESERVATION_STATUS,
        default='active'
    )

    # التوقيت
    reserved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_reservations',
        verbose_name=_('حجز بواسطة')
    )

    expires_at = models.DateTimeField(
        _('ينتهي في'),
        help_text=_('وقت انتهاء صلاحية الحجز')
    )

    confirmed_at = models.DateTimeField(
        _('تاريخ التأكيد'),
        null=True,
        blank=True
    )

    released_at = models.DateTimeField(
        _('تاريخ التحرير'),
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('حجز مخزون')
        verbose_name_plural = _('حجوزات المخزون')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['item', 'warehouse']),
        ]

    def is_expired(self):
        """هل الحجز منتهي الصلاحية"""
        return self.status == 'active' and timezone.now() > self.expires_at

    def time_remaining(self):
        """الوقت المتبقي للحجز"""
        if self.status != 'active':
            return None
        remaining = self.expires_at - timezone.now()
        if remaining.total_seconds() < 0:
            return None
        return remaining

    def __str__(self):
        return f"حجز {self.quantity} من {self.item.name} - {self.get_status_display()}"

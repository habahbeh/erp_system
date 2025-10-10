# apps/accounting/models/voucher_models.py
"""
نماذج السندات (القبض والصرف) - مع الربط التلقائي للقيود
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import DocumentBaseModel
from .account_models import Account
from .journal_models import JournalEntry, JournalEntryLine


class PaymentVoucher(DocumentBaseModel):
    """سند الصرف"""

    PAYMENT_METHODS = [
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('transfer', _('حوالة')),
        ('credit_card', _('بطاقة ائتمان'))
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('confirmed', _('مؤكد')),
        ('posted', _('مرحل')),
        ('cancelled', _('ملغي')),
    ]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')

    # المستفيد
    beneficiary_name = models.CharField(_('اسم المستفيد'), max_length=200)
    beneficiary_type = models.CharField(_('نوع المستفيد'), max_length=20,
                                       choices=[('supplier', _('مورد')), ('employee', _('موظف')), ('other', _('أخرى'))])
    beneficiary_id = models.IntegerField(_('معرف المستفيد'), null=True, blank=True)

    # التفاصيل المالية
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=3, validators=[MinValueValidator(0)])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # طريقة الدفع
    payment_method = models.CharField(_('طريقة الدفع'), max_length=20, choices=PAYMENT_METHODS, default='cash')

    # الحسابات
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='payment_vouchers',
                                    verbose_name=_('حساب الصندوق/البنك'))
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='expense_vouchers',
                                       verbose_name=_('حساب المصروف'), null=True, blank=True)

    # البيان
    description = models.TextField(_('البيان'))

    # معلومات الشيك
    check_number = models.CharField(_('رقم الشيك'), max_length=50, blank=True)
    check_date = models.DateField(_('تاريخ الشيك'), null=True, blank=True)
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)

    # القيد المحاسبي
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name=_('القيد المحاسبي'))

    # معلومات الترحيل
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='posted_payment_vouchers', verbose_name=_('رحل بواسطة'))
    posted_date = models.DateTimeField(_('تاريخ الترحيل'), null=True, blank=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سند صرف')
        verbose_name_plural = _('سندات الصرف')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)

    def generate_number(self):
        """توليد رقم السند"""
        year_month = self.date.strftime('%Y%m')
        last_voucher = PaymentVoucher.objects.filter(
            company=self.company,
            number__startswith=f"PV{year_month}"
        ).order_by('-number').first()

        if last_voucher:
            last_number = int(last_voucher.number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"PV{year_month}{new_number:04d}"

    def can_post(self):
        """هل يمكن ترحيل السند"""
        return self.status == 'confirmed' and not self.journal_entry

    def can_unpost(self):
        """هل يمكن إلغاء ترحيل السند"""
        return self.status == 'posted' and self.journal_entry

    def can_edit(self):
        """هل يمكن تعديل السند"""
        return self.status in ['draft', 'confirmed']

    def can_delete(self):
        """هل يمكن حذف السند"""
        return self.status == 'draft' and not self.journal_entry

    @transaction.atomic
    def post(self, user=None):
        """ترحيل السند وإنشاء القيد المحاسبي"""
        if not self.can_post():
            raise ValidationError(_('لا يمكن ترحيل هذا السند'))

        # التحقق من صحة البيانات
        if not self.cash_account:
            raise ValidationError(_('يجب تحديد حساب الصندوق/البنك'))

        # الحصول على السنة المالية والفترة النشطة
        from .fiscal_models import FiscalYear, AccountingPeriod

        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة تشمل تاريخ السند'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            raise ValidationError(_('لا توجد فترة محاسبية نشطة تشمل تاريخ السند'))

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"سند صرف رقم {self.number} - {self.description}",
            reference=self.number,
            source_document='payment_voucher',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        # إنشاء سطور القيد
        line_number = 1

        # حساب المصروف (إذا لم يحدد نستخدم حساب افتراضي أو نتخطاه)
        expense_account = self.expense_account or self.cash_account

        # سطر المصروف (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=expense_account,
            description=f"{self.description} - {self.beneficiary_name}",
            debit_amount=self.amount,
            credit_amount=0,
            currency=self.currency,
            exchange_rate=self.exchange_rate,
            reference=self.number
        )
        line_number += 1

        # سطر الصندوق/البنك (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=self.cash_account,
            description=f"سند صرف - {self.beneficiary_name}",
            debit_amount=0,
            credit_amount=self.amount,
            currency=self.currency,
            exchange_rate=self.exchange_rate,
            reference=self.number
        )

        # ترحيل القيد تلقائياً
        journal_entry.post(user=user)

        # تحديث السند
        self.journal_entry = journal_entry
        self.status = 'posted'
        self.posted_by = user
        from django.utils import timezone
        self.posted_date = timezone.now()
        self.save()

        return journal_entry

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل السند"""
        if not self.can_unpost():
            raise ValidationError(_('لا يمكن إلغاء ترحيل هذا السند'))

        # إلغاء ترحيل القيد
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()

        # تحديث السند
        self.journal_entry = None
        self.status = 'confirmed'
        self.posted_by = None
        self.posted_date = None
        self.save()

    def __str__(self):
        return f"{self.number} - {self.beneficiary_name}"


class ReceiptVoucher(DocumentBaseModel):
    """سند القبض"""

    RECEIPT_METHODS = [
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('transfer', _('حوالة')),
        ('credit_card', _('بطاقة ائتمان'))
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('confirmed', _('مؤكد')),
        ('posted', _('مرحل')),
        ('cancelled', _('ملغي')),
    ]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')

    # المستلم من
    received_from = models.CharField(_('مستلم من'), max_length=200)
    payer_type = models.CharField(_('نوع الدافع'), max_length=20,
                                 choices=[('customer', _('عميل')), ('other', _('أخرى'))])
    payer_id = models.IntegerField(_('معرف الدافع'), null=True, blank=True)

    # التفاصيل المالية
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=3, validators=[MinValueValidator(0)])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # طريقة القبض
    receipt_method = models.CharField(_('طريقة القبض'), max_length=20, choices=RECEIPT_METHODS, default='cash')

    # الحسابات
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='receipt_vouchers',
                                    verbose_name=_('حساب الصندوق/البنك'))
    income_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='income_vouchers',
                                      verbose_name=_('حساب الإيراد'), null=True, blank=True)

    # البيان
    description = models.TextField(_('البيان'))

    # معلومات الشيك
    check_number = models.CharField(_('رقم الشيك'), max_length=50, blank=True)
    check_date = models.DateField(_('تاريخ الشيك'), null=True, blank=True)
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)

    # القيد المحاسبي
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name=_('القيد المحاسبي'))

    # معلومات الترحيل
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='posted_receipt_vouchers', verbose_name=_('رحل بواسطة'))
    posted_date = models.DateTimeField(_('تاريخ الترحيل'), null=True, blank=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سند قبض')
        verbose_name_plural = _('سندات القبض')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)

    def generate_number(self):
        """توليد رقم السند"""
        year_month = self.date.strftime('%Y%m')
        last_voucher = ReceiptVoucher.objects.filter(
            company=self.company,
            number__startswith=f"RV{year_month}"
        ).order_by('-number').first()

        if last_voucher:
            last_number = int(last_voucher.number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"RV{year_month}{new_number:04d}"

    def can_post(self):
        """هل يمكن ترحيل السند"""
        return self.status == 'confirmed' and not self.journal_entry

    def can_unpost(self):
        """هل يمكن إلغاء ترحيل السند"""
        return self.status == 'posted' and self.journal_entry

    def can_edit(self):
        """هل يمكن تعديل السند"""
        return self.status in ['draft', 'confirmed']

    def can_delete(self):
        """هل يمكن حذف السند"""
        return self.status == 'draft' and not self.journal_entry

    @transaction.atomic
    def post(self, user=None):
        """ترحيل السند وإنشاء القيد المحاسبي"""
        if not self.can_post():
            raise ValidationError(_('لا يمكن ترحيل هذا السند'))

        # التحقق من صحة البيانات
        if not self.cash_account:
            raise ValidationError(_('يجب تحديد حساب الصندوق/البنك'))

        # الحصول على السنة المالية والفترة النشطة
        from .fiscal_models import FiscalYear, AccountingPeriod

        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة تشمل تاريخ السند'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            raise ValidationError(_('لا توجد فترة محاسبية نشطة تشمل تاريخ السند'))

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"سند قبض رقم {self.number} - {self.description}",
            reference=self.number,
            source_document='receipt_voucher',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        # إنشاء سطور القيد
        line_number = 1

        # سطر الصندوق/البنك (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=self.cash_account,
            description=f"سند قبض - {self.received_from}",
            debit_amount=self.amount,
            credit_amount=0,
            currency=self.currency,
            exchange_rate=self.exchange_rate,
            reference=self.number
        )
        line_number += 1

        # حساب الإيراد (إذا لم يحدد نستخدم حساب افتراضي أو نتخطاه)
        income_account = self.income_account or self.cash_account

        # سطر الإيراد (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=income_account,
            description=f"{self.description} - {self.received_from}",
            debit_amount=0,
            credit_amount=self.amount,
            currency=self.currency,
            exchange_rate=self.exchange_rate,
            reference=self.number
        )

        # ترحيل القيد تلقائياً
        journal_entry.post(user=user)

        # تحديث السند
        self.journal_entry = journal_entry
        self.status = 'posted'
        self.posted_by = user
        from django.utils import timezone
        self.posted_date = timezone.now()
        self.save()

        return journal_entry

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل السند"""
        if not self.can_unpost():
            raise ValidationError(_('لا يمكن إلغاء ترحيل هذا السند'))

        # إلغاء ترحيل القيد
        if self.journal_entry:
            self.journal_entry.unpost()
            self.journal_entry.delete()

        # تحديث السند
        self.journal_entry = None
        self.status = 'confirmed'
        self.posted_by = None
        self.posted_date = None
        self.save()

    def __str__(self):
        return f"{self.number} - {self.received_from}"
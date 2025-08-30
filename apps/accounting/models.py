# apps/accounting/models.py
"""
نماذج المحاسبة - الإصدار المُصحح
يحتوي على: دليل الحسابات، القيود، السندات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel


class AccountType(models.Model):
    """أنواع الحسابات الرئيسية"""

    ACCOUNT_TYPES = [
        ('assets', _('الأصول')),
        ('liabilities', _('الخصوم')),
        ('equity', _('حقوق الملكية')),
        ('revenue', _('الإيرادات')),
        ('expenses', _('المصروفات')),
    ]

    code = models.CharField(_('الرمز'), max_length=20, unique=True)
    name = models.CharField(_('الاسم'), max_length=50)
    type_category = models.CharField(_('التصنيف'), max_length=20, choices=ACCOUNT_TYPES)
    normal_balance = models.CharField(
        _('الرصيد الطبيعي'),
        max_length=10,
        choices=[('debit', _('مدين')), ('credit', _('دائن'))]
    )

    class Meta:
        verbose_name = _('نوع حساب')
        verbose_name_plural = _('أنواع الحسابات')

    def __str__(self):
        return self.name


class Account(BaseModel):
    """دليل الحسابات"""

    ACCOUNT_NATURE = [
        ('debit', _('مدين')),
        ('credit', _('دائن')),
        ('both', _('كلاهما')),
    ]

    # معلومات أساسية
    code = models.CharField(_('رمز الحساب'), max_length=20)
    name = models.CharField(_('اسم الحساب'), max_length=200)
    name_en = models.CharField(_('الاسم اللاتيني'), max_length=200, blank=True)

    # التصنيف والتسلسل
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, verbose_name=_('نوع الحساب'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_('الحساب الأب'))

    # الإعدادات
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة الافتراضية'))
    nature = models.CharField(_('جهة الحساب'), max_length=10, choices=ACCOUNT_NATURE, default='both')

    # معلومات إضافية
    notes = models.TextField(_('ملاحظات'), blank=True)

    # الحالة
    is_suspended = models.BooleanField(_('موقوف'), default=False)

    # خصائص الحساب
    is_cash_account = models.BooleanField(_('حساب نقدي'), default=False)
    is_bank_account = models.BooleanField(_('حساب بنكي'), default=False)
    accept_entries = models.BooleanField(_('يقبل القيود'), default=True)

    # المستوى (محسوب تلقائياً)
    level = models.IntegerField(_('المستوى'), default=1, editable=False)

    # الرصيد الافتتاحي
    opening_balance = models.DecimalField(_('الرصيد الافتتاحي'), max_digits=15, decimal_places=3, default=0)
    opening_balance_date = models.DateField(_('تاريخ الرصيد الافتتاحي'), null=True, blank=True)

    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('دليل الحسابات')
        unique_together = [['company', 'code']]
        ordering = ['code']

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
            if not self.account_type_id:
                self.account_type = self.parent.account_type
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def get_full_name(self):
        if self.parent:
            return f"{self.parent.get_full_name()} / {self.name}"
        return self.name

    def get_balance(self, date=None):
        return self.opening_balance

    def __str__(self):
        return f"{self.code} - {self.name}"


class FiscalYear(BaseModel):
    """السنة المالية"""

    name = models.CharField(_('اسم السنة المالية'), max_length=100)
    code = models.CharField(_('الرمز'), max_length=20)
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    is_closed = models.BooleanField(_('مقفلة'), default=False)

    class Meta:
        verbose_name = _('سنة مالية')
        verbose_name_plural = _('السنوات المالية')
        unique_together = [['company', 'code']]
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class AccountingPeriod(BaseModel):
    """الفترة المحاسبية"""

    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods', verbose_name=_('السنة المالية'))
    name = models.CharField(_('اسم الفترة'), max_length=50)
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    is_closed = models.BooleanField(_('مقفلة'), default=False)
    is_adjustment = models.BooleanField(_('فترة تسويات'), default=False)

    class Meta:
        verbose_name = _('فترة محاسبية')
        verbose_name_plural = _('الفترات المحاسبية')
        ordering = ['start_date']

    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"


class JournalEntry(BaseModel):
    """القيود اليومية"""

    ENTRY_TYPES = [
        ('normal', _('قيد عادي')),
        ('opening', _('قيد افتتاحي')),
        ('closing', _('قيد إقفال')),
        ('adjustment', _('قيد تسوية')),
    ]

    # معلومات أساسية
    number = models.CharField(_('رقم القيد'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, verbose_name=_('السنة المالية'))
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT, verbose_name=_('الفترة المحاسبية'))
    entry_type = models.CharField(_('نوع القيد'), max_length=20, choices=ENTRY_TYPES, default='normal')

    # البيان والوصف
    description = models.TextField(_('البيان'))
    reference = models.CharField(_('المرجع'), max_length=100, blank=True)

    # الحالة
    is_posted = models.BooleanField(_('مرحل'), default=False)
    posted_date = models.DateTimeField(_('تاريخ الترحيل'), null=True, blank=True)
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_entries', verbose_name=_('رحل بواسطة'))

    # الإلغاء
    is_reversed = models.BooleanField(_('ملغي'), default=False)
    reversed_entry = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversing_entries', verbose_name=_('القيد العكسي'))

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('قيد يومية')
        verbose_name_plural = _('القيود اليومية')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        if not self.number:
            year_month = self.date.strftime('%Y%m')
            last_entry = JournalEntry.objects.filter(
                company=self.company,
                number__startswith=f"JE{year_month}"
            ).order_by('-number').first()

            if last_entry:
                last_number = int(last_entry.number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"JE{year_month}{new_number:04d}"

        if not self.period_id:
            self.period = AccountingPeriod.objects.get(
                fiscal_year=self.fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date
            )

        super().save(*args, **kwargs)

    def get_total_debit(self):
        return self.lines.aggregate(total=models.Sum('debit_amount'))['total'] or 0

    def get_total_credit(self):
        return self.lines.aggregate(total=models.Sum('credit_amount'))['total'] or 0

    def is_balanced(self):
        return self.get_total_debit() == self.get_total_credit()

    def __str__(self):
        return f"{self.number} - {self.date}"


class JournalEntryLine(models.Model):
    """سطور القيد"""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines', verbose_name=_('القيد'))
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name=_('الحساب'))
    description = models.CharField(_('البيان'), max_length=500, blank=True)

    # المبالغ
    debit_amount = models.DecimalField(_('مدين'), max_digits=15, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    credit_amount = models.DecimalField(_('دائن'), max_digits=15, decimal_places=3, default=0, validators=[MinValueValidator(0)])

    # العملة
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # مراكز التكلفة (اختياري)
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('مركز التكلفة'))

    # المعلومات الإضافية
    partner_type = models.CharField(
        _('نوع الشريك'),
        max_length=20,
        choices=[('customer', _('عميل')), ('supplier', _('مورد')), ('employee', _('موظف')), ('other', _('أخرى'))],
        blank=True
    )
    partner_id = models.IntegerField(_('معرف الشريك'), null=True, blank=True)

    class Meta:
        verbose_name = _('سطر قيد')
        verbose_name_plural = _('سطور القيود')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError(_('لا يمكن أن يكون المبلغ مدين ودائن في نفس الوقت'))
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError(_('يجب إدخال مبلغ مدين أو دائن'))

    def __str__(self):
        return f"{self.account.name} - {self.debit_amount or self.credit_amount}"


class PaymentVoucher(BaseModel):
    """سند الصرف"""

    PAYMENT_METHODS = [('cash', _('نقدي')), ('check', _('شيك')), ('transfer', _('حوالة')), ('credit_card', _('بطاقة ائتمان'))]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))

    # المستفيد
    beneficiary_name = models.CharField(_('اسم المستفيد'), max_length=200)
    beneficiary_type = models.CharField(_('نوع المستفيد'), max_length=20, choices=[('supplier', _('مورد')), ('employee', _('موظف')), ('other', _('أخرى'))])
    beneficiary_id = models.IntegerField(_('معرف المستفيد'), null=True, blank=True)

    # التفاصيل المالية
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=3, validators=[MinValueValidator(0)])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # طريقة الدفع
    payment_method = models.CharField(_('طريقة الدفع'), max_length=20, choices=PAYMENT_METHODS, default='cash')

    # الحسابات
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='payment_vouchers', verbose_name=_('حساب الصندوق/البنك'))
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='expense_vouchers', verbose_name=_('حساب المصروف'), null=True, blank=True)

    # البيان
    description = models.TextField(_('البيان'))

    # معلومات الشيك
    check_number = models.CharField(_('رقم الشيك'), max_length=50, blank=True)
    check_date = models.DateField(_('تاريخ الشيك'), null=True, blank=True)
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)

    # القيد المحاسبي
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('القيد المحاسبي'))

    # الحالة
    is_posted = models.BooleanField(_('مرحل'), default=False)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سند صرف')
        verbose_name_plural = _('سندات الصرف')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        if not self.number:
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

            self.number = f"PV{year_month}{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.beneficiary_name}"


class ReceiptVoucher(BaseModel):
    """سند القبض"""

    RECEIPT_METHODS = [('cash', _('نقدي')), ('check', _('شيك')), ('transfer', _('حوالة')), ('credit_card', _('بطاقة ائتمان'))]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))

    # المستلم من
    received_from = models.CharField(_('مستلم من'), max_length=200)
    payer_type = models.CharField(_('نوع الدافع'), max_length=20, choices=[('customer', _('عميل')), ('other', _('أخرى'))])
    payer_id = models.IntegerField(_('معرف الدافع'), null=True, blank=True)

    # التفاصيل المالية
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=3, validators=[MinValueValidator(0)])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # طريقة القبض
    receipt_method = models.CharField(_('طريقة القبض'), max_length=20, choices=RECEIPT_METHODS, default='cash')

    # الحسابات
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='receipt_vouchers', verbose_name=_('حساب الصندوق/البنك'))
    income_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='income_vouchers', verbose_name=_('حساب الإيراد'), null=True, blank=True)

    # البيان
    description = models.TextField(_('البيان'))

    # معلومات الشيك
    check_number = models.CharField(_('رقم الشيك'), max_length=50, blank=True)
    check_date = models.DateField(_('تاريخ الشيك'), null=True, blank=True)
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)

    # القيد المحاسبي
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('القيد المحاسبي'))

    # الحالة
    is_posted = models.BooleanField(_('مرحل'), default=False)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سند قبض')
        verbose_name_plural = _('سندات القبض')
        unique_together = [['company', 'number']]
        ordering = ['-date', '-number']

    def save(self, *args, **kwargs):
        if not self.number:
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

            self.number = f"RV{year_month}{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.received_from}"


class CostCenter(BaseModel):
    """مراكز التكلفة"""

    code = models.CharField(_('الرمز'), max_length=20)
    name = models.CharField(_('الاسم'), max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_('المركز الأب'))
    manager = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('المسؤول'))

    class Meta:
        verbose_name = _('مركز تكلفة')
        verbose_name_plural = _('مراكز التكلفة')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"
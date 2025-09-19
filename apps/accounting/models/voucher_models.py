# apps/accounting/models/voucher_models.py
"""
نماذج السندات (القبض والصرف)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import DocumentBaseModel
from .account_models import Account
from .journal_models import JournalEntry


class PaymentVoucher(DocumentBaseModel):
    """سند الصرف"""

    PAYMENT_METHODS = [
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('transfer', _('حوالة')),
        ('credit_card', _('بطاقة ائتمان'))
    ]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))

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


class ReceiptVoucher(DocumentBaseModel):
    """سند القبض"""

    RECEIPT_METHODS = [
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('transfer', _('حوالة')),
        ('credit_card', _('بطاقة ائتمان'))
    ]

    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))

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
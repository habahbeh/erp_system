# apps/accounting/models/balance_models.py
"""
نماذج الأرصدة المحاسبية - لتتبع أرصدة الحسابات بكفاءة
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

from apps.core.models import BaseModel
from .account_models import Account
from .fiscal_models import FiscalYear, AccountingPeriod


class AccountBalance(BaseModel):
    """أرصدة الحسابات - لتحسين أداء حساب الأرصدة"""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name=_('الحساب')
    )

    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        verbose_name=_('السنة المالية')
    )

    period = models.ForeignKey(
        AccountingPeriod,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('الفترة المحاسبية')
    )

    # الرصيد الافتتاحي
    opening_balance_debit = models.DecimalField(
        _('رصيد افتتاحي مدين'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    opening_balance_credit = models.DecimalField(
        _('رصيد افتتاحي دائن'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # الحركة خلال الفترة
    period_debit = models.DecimalField(
        _('إجمالي المدين للفترة'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    period_credit = models.DecimalField(
        _('إجمالي الدائن للفترة'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # الرصيد الختامي (محسوب)
    closing_balance_debit = models.DecimalField(
        _('رصيد ختامي مدين'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    closing_balance_credit = models.DecimalField(
        _('رصيد ختامي دائن'),
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # معلومات إضافية
    last_updated = models.DateTimeField(_('آخر تحديث'), auto_now=True)
    is_balanced = models.BooleanField(_('متوازن'), default=True)

    class Meta:
        verbose_name = _('رصيد حساب')
        verbose_name_plural = _('أرصدة الحسابات')
        unique_together = [
            ['account', 'fiscal_year', 'period', 'company'],
            ['account', 'fiscal_year', 'company']  # للرصيد السنوي
        ]
        indexes = [
            models.Index(fields=['account', 'fiscal_year']),
            models.Index(fields=['fiscal_year', 'period']),
            models.Index(fields=['company', 'fiscal_year']),
        ]
        ordering = ['account__code', 'fiscal_year', 'period']

    def __str__(self):
        if self.period:
            return f"{self.account.name} - {self.fiscal_year.name} - {self.period.name}"
        return f"{self.account.name} - {self.fiscal_year.name}"

    def calculate_closing_balance(self):
        """حساب الرصيد الختامي"""

        # الرصيد الافتتاحي الصافي
        opening_net = self.opening_balance_debit - self.opening_balance_credit

        # حركة الفترة الصافية
        period_net = self.period_debit - self.period_credit

        # الرصيد الختامي الصافي
        closing_net = opening_net + period_net

        # تحديد الجانب حسب طبيعة الحساب
        if self.account.account_type.normal_balance == 'debit':
            # حسابات طبيعتها مدينة
            if closing_net >= 0:
                self.closing_balance_debit = abs(closing_net)
                self.closing_balance_credit = Decimal('0.0000')
            else:
                self.closing_balance_debit = Decimal('0.0000')
                self.closing_balance_credit = abs(closing_net)
        else:
            # حسابات طبيعتها دائنة
            if closing_net <= 0:
                self.closing_balance_credit = abs(closing_net)
                self.closing_balance_debit = Decimal('0.0000')
            else:
                self.closing_balance_credit = Decimal('0.0000')
                self.closing_balance_debit = abs(closing_net)

        return closing_net

    def update_period_movements(self):
        """تحديث حركة الفترة من القيود المحاسبية"""
        from .journal_models import JournalEntryLine

        # فلترة خطوط القيود المرحلة للحساب والفترة
        filter_kwargs = {
            'account': self.account,
            'journal_entry__company': self.company,
            'journal_entry__status': 'posted',
            'journal_entry__fiscal_year': self.fiscal_year
        }

        if self.period:
            filter_kwargs['journal_entry__period'] = self.period

        lines = JournalEntryLine.objects.filter(**filter_kwargs)

        # حساب الإجماليات
        totals = lines.aggregate(
            total_debit=models.Sum('debit_amount'),
            total_credit=models.Sum('credit_amount')
        )

        self.period_debit = totals['total_debit'] or Decimal('0.0000')
        self.period_credit = totals['total_credit'] or Decimal('0.0000')

        return self.period_debit, self.period_credit

    def refresh_balance(self):
        """إعادة حساب الرصيد كاملاً"""
        # تحديث حركة الفترة
        self.update_period_movements()

        # حساب الرصيد الختامي
        closing_net = self.calculate_closing_balance()

        # التحقق من التوازن
        self.is_balanced = (self.closing_balance_debit == 0 and self.closing_balance_credit == 0) or \
                           (self.closing_balance_debit > 0) != (self.closing_balance_credit > 0)

        self.save()
        return closing_net

    @property
    def net_balance(self):
        """الرصيد الصافي (موجب للمدين، سالب للدائن)"""
        return self.closing_balance_debit - self.closing_balance_credit

    @property
    def balance_display(self):
        """عرض الرصيد للمستخدم"""
        if self.closing_balance_debit > 0:
            return f"{self.closing_balance_debit:,.2f} مدين"
        elif self.closing_balance_credit > 0:
            return f"{self.closing_balance_credit:,.2f} دائن"
        else:
            return "0.00 متوازن"

    @classmethod
    def get_or_create_balance(cls, account, fiscal_year, period=None, company=None):
        """الحصول على رصيد أو إنشاؤه إذا لم يكن موجوداً"""
        if not company:
            company = account.company

        balance, created = cls.objects.get_or_create(
            account=account,
            fiscal_year=fiscal_year,
            period=period,
            company=company,
            defaults={
                'opening_balance_debit': account.opening_balance if account.opening_balance > 0 else Decimal('0.0000'),
                'opening_balance_credit': abs(account.opening_balance) if account.opening_balance < 0 else Decimal(
                    '0.0000'),
            }
        )

        if created or not balance.last_updated:
            balance.refresh_balance()

        return balance

    @classmethod
    def update_balances_for_entry(cls, journal_entry):
        """تحديث أرصدة جميع الحسابات المتأثرة بقيد معين"""
        updated_accounts = []

        for line in journal_entry.lines.all():
            balance = cls.get_or_create_balance(
                account=line.account,
                fiscal_year=journal_entry.fiscal_year,
                period=journal_entry.period,
                company=journal_entry.company
            )
            balance.refresh_balance()
            updated_accounts.append(balance)

        return updated_accounts


class AccountBalanceHistory(BaseModel):
    """تاريخ تغييرات أرصدة الحسابات - للتتبع والمراجعة"""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='balance_history',
        verbose_name=_('الحساب')
    )

    change_date = models.DateTimeField(_('تاريخ التغيير'), auto_now_add=True)
    change_reason = models.CharField(_('سبب التغيير'), max_length=100)

    # الرصيد قبل التغيير
    old_debit_balance = models.DecimalField(_('الرصيد المدين السابق'), max_digits=15, decimal_places=4, default=0)
    old_credit_balance = models.DecimalField(_('الرصيد الدائن السابق'), max_digits=15, decimal_places=4, default=0)

    # الرصيد بعد التغيير
    new_debit_balance = models.DecimalField(_('الرصيد المدين الجديد'), max_digits=15, decimal_places=4, default=0)
    new_credit_balance = models.DecimalField(_('الرصيد الدائن الجديد'), max_digits=15, decimal_places=4, default=0)

    # المبلغ المتأثر
    affected_amount = models.DecimalField(_('المبلغ المتأثر'), max_digits=15, decimal_places=4, default=0)

    # مرجع العملية
    reference_type = models.CharField(_('نوع المرجع'), max_length=50)  # journal_entry, payment_voucher, etc.
    reference_id = models.PositiveIntegerField(_('معرف المرجع'))

    changed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('تم التغيير بواسطة')
    )

    class Meta:
        verbose_name = _('تاريخ رصيد حساب')
        verbose_name_plural = _('تاريخ أرصدة الحسابات')
        ordering = ['-change_date']
        indexes = [
            models.Index(fields=['account', '-change_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.account.name} - {self.change_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def net_change(self):
        """صافي التغيير في الرصيد"""
        old_net = self.old_debit_balance - self.old_credit_balance
        new_net = self.new_debit_balance - self.new_credit_balance
        return new_net - old_net
# apps/assets/models/transaction_models.py
"""
نماذج العمليات على الأصول - محسّنة
- العمليات العامة (شراء، بيع، استبعاد، إلخ)
- التحويلات بين الفروع والأقسام
- الاستئجار (جديد)
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import DocumentBaseModel, BusinessPartner
from decimal import Decimal


class AssetTransaction(DocumentBaseModel):
    """العمليات على الأصول - سجل شامل"""

    TRANSACTION_TYPES = [
        ('purchase', _('شراء')),
        ('sale', _('بيع')),
        ('disposal', _('استبعاد/إتلاف')),
        ('revaluation', _('إعادة تقييم')),
        ('capital_improvement', _('تحسينات رأسمالية')),
        ('donation_in', _('هبة مستلمة')),
        ('donation_out', _('هبة معطاة')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('approved', _('معتمد')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغي')),
    ]

    PAYMENT_METHODS = [
        ('cash', _('نقدي')),
        ('bank', _('بنك')),
        ('credit', _('آجل')),
        ('other', _('أخرى')),
    ]

    # المعلومات الأساسية
    transaction_number = models.CharField(
        _('رقم العملية'),
        max_length=50,
        editable=False,
        unique=True
    )
    transaction_date = models.DateField(_('تاريخ العملية'))
    transaction_type = models.CharField(
        _('نوع العملية'),
        max_length=30,
        choices=TRANSACTION_TYPES
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # الأصل
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('الأصل')
    )

    # المبالغ المالية
    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ الإجمالي للعملية')
    )

    # للبيع فقط
    sale_price = models.DecimalField(
        _('سعر البيع'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    book_value_at_sale = models.DecimalField(
        _('القيمة الدفترية عند البيع'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True
    )
    gain_loss = models.DecimalField(
        _('الربح/الخسارة'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('سعر البيع - القيمة الدفترية')
    )

    # طريقة الدفع/التحصيل
    payment_method = models.CharField(
        _('طريقة الدفع/التحصيل'),
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash'
    )

    # الطرف الآخر (مورد/عميل)
    business_partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transactions',
        verbose_name=_('الطرف الآخر (مورد/عميل)')
    )

    # المستندات
    reference_number = models.CharField(
        _('رقم المرجع'),
        max_length=100,
        blank=True,
        help_text=_('رقم الفاتورة أو العقد')
    )
    attachment = models.FileField(
        _('المرفق'),
        upload_to='assets/transactions/%Y/%m/',
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transactions',
        verbose_name=_('القيد المحاسبي')
    )

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_asset_transactions',
        verbose_name=_('وافق عليه')
    )
    approved_at = models.DateTimeField(_('تاريخ الموافقة'), null=True, blank=True)

    description = models.TextField(_('الوصف'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عملية على أصل')
        verbose_name_plural = _('العمليات على الأصول')
        ordering = ['-transaction_date', '-transaction_number']

    def save(self, *args, **kwargs):
        # توليد رقم العملية تلقائياً
        if not self.transaction_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_transaction'
                )
                self.transaction_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_transaction',
                    prefix='AT',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.transaction_number = sequence.get_next_number()

        # حساب الربح/الخسارة للبيع
        if self.transaction_type == 'sale' and self.sale_price and self.book_value_at_sale:
            self.gain_loss = self.sale_price - self.book_value_at_sale

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - {self.asset.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.transaction_type == 'sale':
            if not self.sale_price:
                raise ValidationError({
                    'sale_price': _('يجب تحديد سعر البيع')
                })
            if not self.business_partner:
                raise ValidationError({
                    'business_partner': _('يجب تحديد العميل')
                })

        if self.transaction_type == 'purchase':
            if not self.business_partner:
                raise ValidationError({
                    'business_partner': _('يجب تحديد المورد')
                })


class AssetTransfer(DocumentBaseModel):
    """تحويل الأصول بين الفروع/الأقسام/الموظفين"""

    STATUS_CHOICES = [
        ('pending', _('معلق')),
        ('approved', _('معتمد')),
        ('completed', _('مكتمل')),
        ('rejected', _('مرفوض')),
        ('cancelled', _('ملغي')),
    ]

    # المعلومات الأساسية
    transfer_number = models.CharField(
        _('رقم التحويل'),
        max_length=50,
        editable=False,
        unique=True
    )
    transfer_date = models.DateField(_('تاريخ التحويل'))
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # الأصل
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='transfers',
        verbose_name=_('الأصل')
    )

    # من
    from_branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        related_name='asset_transfers_from',
        verbose_name=_('من الفرع')
    )
    from_cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.PROTECT,
        related_name='asset_transfers_from',
        verbose_name=_('من مركز التكلفة'),
        null=True,
        blank=True
    )
    from_employee = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_from',
        verbose_name=_('من الموظف')
    )

    # إلى
    to_branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        related_name='asset_transfers_to',
        verbose_name=_('إلى الفرع')
    )
    to_cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.PROTECT,
        related_name='asset_transfers_to',
        verbose_name=_('إلى مركز التكلفة'),
        null=True,
        blank=True
    )
    to_employee = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_to',
        verbose_name=_('إلى الموظف')
    )

    # السبب
    reason = models.TextField(_('سبب التحويل'))

    # الموافقات
    requested_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_asset_transfers',
        verbose_name=_('طلب بواسطة')
    )
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_asset_transfers',
        verbose_name=_('وافق عليه')
    )
    approved_at = models.DateTimeField(_('تاريخ الموافقة'), null=True, blank=True)

    # التسليم والاستلام
    delivered_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_asset_transfers',
        verbose_name=_('سلم بواسطة')
    )
    delivered_at = models.DateTimeField(_('تاريخ التسليم'), null=True, blank=True)

    received_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_asset_transfers',
        verbose_name=_('استلم بواسطة')
    )
    received_at = models.DateTimeField(_('تاريخ الاستلام'), null=True, blank=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('تحويل أصل')
        verbose_name_plural = _('تحويلات الأصول')
        ordering = ['-transfer_date', '-transfer_number']

    def save(self, *args, **kwargs):
        # توليد رقم التحويل تلقائياً
        if not self.transfer_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_transaction'
                )
                self.transfer_number = f"TRF{sequence.get_next_number()}"
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_transaction',
                    prefix='TRF',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.transfer_number = sequence.get_next_number()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transfer_number} - {self.asset.name} - {self.from_branch.name} → {self.to_branch.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.from_branch == self.to_branch and self.from_cost_center == self.to_cost_center and self.from_employee == self.to_employee:
            raise ValidationError(_('يجب أن يكون هناك تغيير في الموقع أو المسؤولية'))


# ✅ جديد: نظام الاستئجار
class AssetLease(DocumentBaseModel):
    """عقود استئجار الأصول"""

    LEASE_TYPES = [
        ('operating', _('إيجار تشغيلي')),
        ('finance', _('إيجار تمويلي')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('active', _('نشط')),
        ('completed', _('مكتمل')),
        ('terminated', _('منهي')),
        ('cancelled', _('ملغي')),
    ]

    # المعلومات الأساسية
    lease_number = models.CharField(
        _('رقم العقد'),
        max_length=50,
        editable=False,
        unique=True
    )

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='leases',
        verbose_name=_('الأصل')
    )

    lease_type = models.CharField(
        _('نوع الإيجار'),
        max_length=20,
        choices=LEASE_TYPES,
        help_text=_('تشغيلي: مصروف، تمويلي: يُضاف للأصول')
    )

    lessor = models.ForeignKey(
        BusinessPartner,
        on_delete=models.PROTECT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        related_name='leased_assets',
        verbose_name=_('المؤجر')
    )

    # التواريخ
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    contract_duration_months = models.IntegerField(
        _('مدة العقد (شهور)'),
        editable=False
    )

    # المبالغ
    monthly_payment = models.DecimalField(
        _('القسط الشهري'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    total_payments = models.DecimalField(
        _('إجمالي الأقساط'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )

    security_deposit = models.DecimalField(
        _('التأمين'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # للإيجار التمويلي فقط
    interest_rate = models.DecimalField(
        _('معدل الفائدة %'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MinValueValidator(100)]
    )

    residual_value = models.DecimalField(
        _('القيمة المتبقية'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('القيمة المتوقعة في نهاية العقد')
    )

    purchase_option_price = models.DecimalField(
        _('سعر خيار الشراء'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('السعر لشراء الأصل في نهاية العقد')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # المستندات
    contract_file = models.FileField(
        _('ملف العقد'),
        upload_to='assets/leases/%Y/%m/',
        blank=True
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عقد استئجار أصل')
        verbose_name_plural = _('عقود استئجار الأصول')
        ordering = ['-start_date', '-lease_number']

    def save(self, *args, **kwargs):
        # توليد رقم العقد
        if not self.lease_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_lease'
                )
                self.lease_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_lease',
                    prefix='LS',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.lease_number = sequence.get_next_number()

        # حساب مدة العقد
        if self.start_date and self.end_date:
            months = (self.end_date.year - self.start_date.year) * 12
            months += self.end_date.month - self.start_date.month
            self.contract_duration_months = months

            # حساب إجمالي الأقساط
            self.total_payments = self.monthly_payment * months

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lease_number} - {self.asset.name} - {self.get_lease_type_display()}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            })

        if self.lease_type == 'finance':
            if not self.interest_rate:
                raise ValidationError({
                    'interest_rate': _('يجب تحديد معدل الفائدة للإيجار التمويلي')
                })

    def get_remaining_months(self):
        """الأشهر المتبقية من العقد"""
        import datetime
        today = datetime.date.today()

        if today > self.end_date:
            return 0

        months = (self.end_date.year - today.year) * 12
        months += self.end_date.month - today.month
        return max(0, months)

    def get_paid_amount(self):
        """المبلغ المدفوع حتى الآن"""
        paid = self.payments.filter(
            is_paid=True
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        return paid

    def get_remaining_amount(self):
        """المبلغ المتبقي"""
        return self.total_payments - self.get_paid_amount()


class LeasePayment(models.Model):
    """دفعات الإيجار"""

    lease = models.ForeignKey(
        AssetLease,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('العقد')
    )

    payment_number = models.IntegerField(_('رقم القسط'))
    payment_date = models.DateField(_('تاريخ الاستحقاق'))

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    # للإيجار التمويلي
    principal_amount = models.DecimalField(
        _('أصل المبلغ'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('الجزء من الأصل')
    )
    interest_amount = models.DecimalField(
        _('الفائدة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('الجزء من الفائدة')
    )

    # الدفع
    is_paid = models.BooleanField(_('مدفوع'), default=False)
    paid_date = models.DateField(_('تاريخ الدفع الفعلي'), null=True, blank=True)

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lease_payments',
        verbose_name=_('القيد المحاسبي')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('دفعة إيجار')
        verbose_name_plural = _('دفعات الإيجار')
        ordering = ['lease', 'payment_number']
        unique_together = [['lease', 'payment_number']]

    def __str__(self):
        return f"{self.lease.lease_number} - قسط {self.payment_number} - {self.amount}"

    @transaction.atomic
    def process_payment(self, user=None):
        """معالجة دفعة الإيجار مع القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod
        from ..accounting_config import AssetAccountingConfiguration

        if self.is_paid:
            raise ValidationError(_('الدفعة مدفوعة مسبقاً'))

        # ✅ الحصول على الإعدادات
        config = AssetAccountingConfiguration.get_or_create_for_company(self.lease.company)

        # تحديد تاريخ الدفع
        payment_date = self.paid_date or timezone.now().date()

        # الحصول على السنة والفترة المالية
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.lease.company,
                start_date__lte=payment_date,
                end_date__gte=payment_date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة'))

        period = AccountingPeriod.objects.filter(
            fiscal_year=fiscal_year,
            start_date__lte=payment_date,
            end_date__gte=payment_date,
            is_closed=False
        ).first()

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.lease.company,
            branch=self.lease.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=payment_date,
            entry_type='auto',
            description=f"دفع إيجار {self.lease.lease_number} - قسط {self.payment_number}",
            reference=self.lease.lease_number,
            source_document='lease_payment',
            source_id=self.pk,
            created_by=user or self.lease.created_by
        )

        line_number = 1

        if self.lease.lease_type == 'operating':
            # ✅ إيجار تشغيلي - مصروف - ديناميكي
            rent_expense_account = config.get_operating_lease_expense_account()
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=rent_expense_account,
                description=f"إيجار {self.lease.asset.name}",
                debit_amount=self.amount,
                credit_amount=0,
                currency=self.lease.company.base_currency,
                cost_center=self.lease.asset.cost_center
            )
            line_number += 1

        else:
            # ✅ إيجار تمويلي - ديناميكي
            lease_accounts = config.get_finance_lease_accounts()

            # من: حساب الالتزام - أصل المبلغ (مدين)
            if self.principal_amount > 0:
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=lease_accounts['liability'],
                    description=f"سداد أصل إيجار تمويلي",
                    debit_amount=self.principal_amount,
                    credit_amount=0,
                    currency=self.lease.company.base_currency
                )
                line_number += 1

            # من: مصروف الفائدة (مدين)
            if self.interest_amount > 0:
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=lease_accounts['interest'],
                    description=f"فائدة إيجار تمويلي",
                    debit_amount=self.interest_amount,
                    credit_amount=0,
                    currency=self.lease.company.base_currency
                )
                line_number += 1

        # ✅ إلى: البنك/الصندوق (دائن) - ديناميكي
        cash_account = config.get_bank_account()
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=cash_account,
            description=f"دفع قسط إيجار",
            debit_amount=0,
            credit_amount=self.amount,
            currency=self.lease.company.base_currency
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث الدفعة
        self.journal_entry = journal_entry
        self.is_paid = True
        self.paid_date = payment_date
        self.save()

        return journal_entry
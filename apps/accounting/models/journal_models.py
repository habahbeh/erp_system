# apps/accounting/models/journal_models.py
"""
نماذج القيود اليومية - محسنة لسهولة الاستخدام
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import date
from django.utils import timezone

from apps.core.models import BaseModel, DocumentBaseModel
from .account_models import Account, CostCenter
from .fiscal_models import FiscalYear, AccountingPeriod


class JournalEntryTemplate(BaseModel):
    """قوالب القيود - لسهولة الإدخال المتكرر"""

    name = models.CharField(_('اسم القالب'), max_length=100)
    description = models.TextField(_('الوصف'), blank=True)
    entry_type = models.CharField(_('نوع القيد'), max_length=20, default='manual')
    default_description = models.TextField(_('البيان الافتراضي'))
    display_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    class Meta:
        verbose_name = _('قالب قيد')
        verbose_name_plural = _('قوالب القيود')
        unique_together = [['company', 'name']]
        ordering = ['display_order', 'name']

    def create_journal_entry(self, **kwargs):
        """إنشاء قيد من القالب"""
        entry = JournalEntry.objects.create(
            company=self.company,
            entry_type=self.entry_type,
            description=self.default_description,
            template=self,
            **kwargs
        )

        # نسخ سطور القالب
        for template_line in self.template_lines.all():
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=template_line.account,
                description=template_line.description,
                debit_amount=template_line.debit_amount,
                credit_amount=template_line.credit_amount,
                reference=template_line.reference
            )

        return entry

    def __str__(self):
        return self.name


class JournalEntry(DocumentBaseModel):
    """القيود اليومية - محسن لسهولة الاستخدام"""

    ENTRY_TYPES = [
        ('manual', _('قيد يدوي')),
        ('auto', _('قيد تلقائي')),
        ('opening', _('قيد افتتاحي')),
        ('closing', _('قيد إقفال')),
        ('adjustment', _('قيد تسوية')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('posted', _('مرحل')),
        ('cancelled', _('ملغي')),
    ]

    # الحقول الأساسية
    number = models.CharField(_('رقم القيد'), max_length=50, editable=False)
    entry_date = models.DateField(_('تاريخ القيد'), default=date.today)
    entry_type = models.CharField(_('نوع القيد'), max_length=20, choices=ENTRY_TYPES, default='manual')
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')

    # السنة والفترة (تحديد تلقائي)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, verbose_name=_('السنة المالية'),
                                    null=True, blank=True)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT, verbose_name=_('الفترة المحاسبية'),
                               null=True, blank=True)

    # التفاصيل
    description = models.TextField(_('البيان'), help_text=_('وصف مختصر للقيد'))
    reference = models.CharField(_('المرجع'), max_length=100, blank=True,
                                 help_text=_('رقم المستند أو المرجع'))

    # المبالغ المحسوبة تلقائياً
    total_debit = models.DecimalField(_('إجمالي المدين'), max_digits=15, decimal_places=4,
                                      default=0, editable=False)
    total_credit = models.DecimalField(_('إجمالي الدائن'), max_digits=15, decimal_places=4,
                                       default=0, editable=False)

    # الحالة والترحيل
    is_balanced = models.BooleanField(_('متوازن'), default=False, editable=False)
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='posted_journal_entries', verbose_name=_('رحل بواسطة'))
    posted_date = models.DateTimeField(_('تاريخ الترحيل'), null=True, blank=True)

    # الإلغاء والعكس
    is_reversed = models.BooleanField(_('معكوس'), default=False)
    reversed_entry = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='reversing_entries', verbose_name=_('القيد العكسي'))

    # ربط بالمصادر الأخرى
    source_document = models.CharField(_('المستند المصدر'), max_length=100, blank=True)
    source_id = models.PositiveIntegerField(_('معرف المصدر'), null=True, blank=True)

    # قالب (إذا تم إنشاؤه من قالب)
    template = models.ForeignKey(JournalEntryTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name=_('القالب'))

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('قيد يومية')
        verbose_name_plural = _('القيود اليومية')
        unique_together = [['company', 'number']]
        ordering = ['-entry_date', '-number']
        indexes = [
            models.Index(fields=['entry_date', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['number']),
        ]

    def save(self, *args, **kwargs):
        # توليد رقم القيد تلقائياً
        if not self.number:
            self.number = self.generate_number()

        # تحديد السنة والفترة تلقائياً
        if not self.fiscal_year_id:
            self.auto_set_fiscal_period()

        super().save(*args, **kwargs)

        # حساب الإجماليات
        self.calculate_totals()

    def generate_number(self):
        """توليد رقم القيد بناءً على التسلسل"""
        from apps.core.models import NumberingSequence

        try:
            sequence = NumberingSequence.objects.get(
                company=self.company,
                document_type='journal_entry'
            )
            return sequence.get_next_number()
        except NumberingSequence.DoesNotExist:
            # إنشاء تسلسل افتراضي
            sequence = NumberingSequence.objects.create(
                company=self.company,
                document_type='journal_entry',
                prefix='JV',
                next_number=1,
                padding=6
            )
            return sequence.get_next_number()

    def auto_set_fiscal_period(self):
        """تحديد السنة والفترة المالية تلقائياً"""
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.entry_date,
                end_date__gte=self.entry_date,
                is_closed=False
            )
            self.fiscal_year = fiscal_year

            # البحث عن الفترة
            period = AccountingPeriod.objects.filter(
                fiscal_year=fiscal_year,
                start_date__lte=self.entry_date,
                end_date__gte=self.entry_date,
                is_closed=False
            ).first()

            if period:
                self.period = period

        except FiscalYear.DoesNotExist:
            pass

    def calculate_totals(self):
        """حساب إجمالي المدين والدائن"""
        lines = self.lines.all()
        self.total_debit = sum(line.debit_amount for line in lines)
        self.total_credit = sum(line.credit_amount for line in lines)
        self.is_balanced = self.total_debit == self.total_credit

        # حفظ بدون إعادة حساب
        JournalEntry.objects.filter(pk=self.pk).update(
            total_debit=self.total_debit,
            total_credit=self.total_credit,
            is_balanced=self.is_balanced
        )

    def clean(self):
        """التحقق من صحة القيد"""
        if self.status == 'posted':
            if not self.is_balanced:
                raise ValidationError(_('لا يمكن ترحيل قيد غير متوازن'))

            if not self.lines.exists():
                raise ValidationError(_('لا يمكن ترحيل قيد بدون سطور'))

    def post(self, user=None):
        """ترحيل القيد"""
        if self.status == 'posted':
            raise ValidationError(_('القيد مرحل مسبقاً'))

        self.calculate_totals()

        if not self.is_balanced:
            raise ValidationError(_('القيد غير متوازن'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في القيد'))

        self.status = 'posted'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()

    def unpost(self):
        """إلغاء ترحيل القيد"""
        if self.status != 'posted':
            raise ValidationError(_('القيد غير مرحل'))

        self.status = 'draft'
        self.posted_by = None
        self.posted_date = None
        self.save()

    def can_edit(self):
        """هل يمكن تعديل القيد"""
        return self.status == 'draft'

    def can_post(self):
        """هل يمكن ترحيل القيد"""
        return self.status == 'draft' and self.is_balanced and self.lines.exists()

    def can_unpost(self):
        """هل يمكن إلغاء ترحيل القيد"""
        return self.status == 'posted'

    def get_absolute_url(self):
        return reverse('accounting:journal_entry_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.number} - {self.description[:50]}"


class JournalEntryLine(models.Model):
    """سطر القيد اليومي - محسن للإدخال السريع"""

    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE,
                                      related_name='lines', verbose_name=_('القيد'))

    line_number = models.PositiveIntegerField(_('رقم السطر'), default=1)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name=_('الحساب'))

    description = models.CharField(_('البيان'), max_length=255,
                                   help_text=_('وصف العملية لهذا السطر'))

    # المبالغ
    debit_amount = models.DecimalField(_('مدين'), max_digits=15, decimal_places=4, default=0,
                                       validators=[MinValueValidator(0)])
    credit_amount = models.DecimalField(_('دائن'), max_digits=15, decimal_places=4, default=0,
                                        validators=[MinValueValidator(0)])

    # العملة وسعر الصرف
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة'))
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=12, decimal_places=6, default=1)

    # معلومات إضافية
    reference = models.CharField(_('المرجع'), max_length=100, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name=_('مركز التكلفة'))

    # للربط مع الشركاء
    partner_type = models.CharField(
        _('نوع الشريك'),
        max_length=20,
        choices=[('customer', _('عميل')), ('supplier', _('مورد')), ('employee', _('موظف')), ('other', _('أخرى'))],
        blank=True
    )
    partner_id = models.IntegerField(_('معرف الشريك'), null=True, blank=True)

    class Meta:
        verbose_name = _('سطر قيد يومية')
        verbose_name_plural = _('سطور قيود اليومية')
        ordering = ['line_number']
        unique_together = [['journal_entry', 'line_number']]

    def clean(self):
        """التحقق من صحة السطر"""
        # التأكد من أن أحد المبلغين فقط موجود
        if self.debit_amount and self.credit_amount:
            raise ValidationError(_('لا يمكن إدخال مبلغ في المدين والدائن معاً'))

        if not self.debit_amount and not self.credit_amount:
            raise ValidationError(_('يجب إدخال مبلغ في المدين أو الدائن'))

        # التأكد من أن المبالغ موجبة
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValidationError(_('المبالغ يجب أن تكون موجبة'))

        # التحقق من أن الحساب يقبل قيود
        if not self.account.accept_entries:
            raise ValidationError(f'الحساب {self.account.name} لا يقبل قيود مباشرة')

    def save(self, *args, **kwargs):
        # تعيين رقم السطر تلقائياً
        if not self.line_number:
            max_line = self.journal_entry.lines.aggregate(
                max_line=models.Max('line_number')
            )['max_line']
            self.line_number = (max_line or 0) + 1

        # تعيين العملة الافتراضية
        if not self.currency_id:
            self.currency = self.account.currency

        super().save(*args, **kwargs)

        # إعادة حساب إجماليات القيد
        self.journal_entry.calculate_totals()

    @property
    def amount(self):
        """المبلغ (مدين أو دائن)"""
        return self.debit_amount or self.credit_amount

    @property
    def is_debit(self):
        """هل السطر مدين"""
        return self.debit_amount > 0

    @property
    def is_credit(self):
        """هل السطر دائن"""
        return self.credit_amount > 0

    def __str__(self):
        amount = self.debit_amount or self.credit_amount
        side = 'مدين' if self.debit_amount else 'دائن'
        return f"{self.account.name} - {amount} {side}"


class JournalEntryTemplateLine(models.Model):
    """سطور قالب القيد"""

    template = models.ForeignKey(JournalEntryTemplate, on_delete=models.CASCADE,
                                 related_name='template_lines', verbose_name=_('القالب'))

    line_number = models.PositiveIntegerField(_('رقم السطر'))
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name=_('الحساب'))
    description = models.CharField(_('البيان'), max_length=255)

    # يمكن ترك المبالغ فارغة ليملأها المستخدم
    debit_amount = models.DecimalField(_('مدين'), max_digits=15, decimal_places=4, default=0)
    credit_amount = models.DecimalField(_('دائن'), max_digits=15, decimal_places=4, default=0)
    reference = models.CharField(_('المرجع'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('سطر قالب قيد')
        verbose_name_plural = _('سطور قوالب القيود')
        ordering = ['line_number']
        unique_together = [['template', 'line_number']]

    def __str__(self):
        return f"{self.template.name} - {self.line_number}"
# apps/accounting/models/journal_models.py
"""
نماذج القيود اليومية - محسنة لسهولة الاستخدام
"""

from django.db import models, transaction
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
    code = models.CharField(_('رمز القالب'), max_length=20, blank=True)
    description = models.TextField(_('الوصف'), blank=True)

    entry_type = models.CharField(_('نوع القيد'), max_length=20,
                                  choices=[
                                      ('manual', _('قيد يدوي')),
                                      ('auto', _('قيد تلقائي')),
                                      ('opening', _('قيد افتتاحي')),
                                      ('closing', _('قيد إقفال')),
                                      ('adjustment', _('قيد تسوية')),
                                  ], default='manual')

    default_description = models.TextField(_('البيان الافتراضي'))
    default_reference = models.CharField(_('المرجع الافتراضي'), max_length=100, blank=True)

    display_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)
    is_active = models.BooleanField(_('نشط'), default=True)

    # إعدادات القالب
    auto_balance = models.BooleanField(_('توازن تلقائي'), default=False,
                                       help_text=_('هل يحسب المبلغ الأخير تلقائياً للتوازن'))

    category = models.CharField(_('فئة القالب'), max_length=50, blank=True,
                                help_text=_('لتصنيف القوالب'))

    class Meta:
        verbose_name = _('قالب قيد')
        verbose_name_plural = _('قوالب القيود')
        unique_together = [['company', 'name'], ['company', 'code']]
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        # توليد رمز تلقائي إذا لم يوجد
        if not self.code:
            self.code = self.name[:10].upper().replace(' ', '')
        super().save(*args, **kwargs)

    def create_journal_entry(self, **kwargs):
        """إنشاء قيد من القالب"""
        # استخراج القيم وحذفها من kwargs لتجنب التكرار
        description = kwargs.pop('description', self.default_description)
        reference = kwargs.pop('reference', self.default_reference)

        entry = JournalEntry.objects.create(
            company=self.company,
            entry_type=self.entry_type,
            description=description,
            reference=reference,
            template=self,
            **kwargs
        )

        # نسخ سطور القالب
        for template_line in self.template_lines.all().order_by('line_number'):
            JournalEntryLine.objects.create(
                journal_entry=entry,
                line_number=template_line.line_number,
                account=template_line.account,
                description=template_line.description or entry.description,
                debit_amount=template_line.debit_amount,
                credit_amount=template_line.credit_amount,
                reference=template_line.reference or entry.reference,
                cost_center=template_line.default_cost_center
            )

        return entry

    def get_total_debit(self):
        """إجمالي المدين في القالب"""
        return sum(line.debit_amount for line in self.template_lines.all())

    def get_total_credit(self):
        """إجمالي الدائن في القالب"""
        return sum(line.credit_amount for line in self.template_lines.all())

    def is_balanced(self):
        """هل القالب متوازن"""
        return self.get_total_debit() == self.get_total_credit()

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
        from django.db import transaction as db_transaction

        self.full_clean()

        is_new = self.pk is None

        # ✅ توليد رقم القيد قبل الحفظ للمرة الأولى
        if is_new and not self.number:
            # Generate number outside of any transaction to avoid issues
            self.number = self.generate_number()
            # تحديد السنة والفترة
            if not self.fiscal_year_id:
                self.auto_set_fiscal_period()

        # الآن احفظ
        super().save(*args, **kwargs)

        # حساب الإجماليات
        if self.pk:
            self.calculate_totals()

    def generate_number(self):
        """توليد رقم القيد بناءً على التسلسل - مع قفل لمنع التكرار"""
        from apps.core.models import NumberingSequence
        from django.db import transaction, connection
        from django.db.models import F
        import datetime
        import time

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # استخدام transaction مستقل تماماً مع عزلية عالية
                with transaction.atomic(using='default'):
                    # استخدام FOR UPDATE مع SKIP LOCKED للتعامل مع التنافس
                    try:
                        sequence = NumberingSequence.objects.select_for_update(nowait=False, skip_locked=False).get(
                            company=self.company,
                            document_type='journal_entry'
                        )
                    except NumberingSequence.DoesNotExist:
                        # إنشاء تسلسل افتراضي
                        sequence, created = NumberingSequence.objects.get_or_create(
                            company=self.company,
                            document_type='journal_entry',
                            defaults={
                                'prefix': 'JV',
                                'next_number': 1,
                                'padding': 6,
                                'include_year': True,
                                'yearly_reset': True,
                                'separator': '/'
                            }
                        )
                        if not created:
                            # إعادة القراءة مع القفل
                            sequence = NumberingSequence.objects.select_for_update(nowait=False).get(pk=sequence.pk)

                    # بناء الرقم مباشرة هنا
                    current_year = datetime.date.today().year
                    current_month = datetime.date.today().month

                    # التحقق من إعادة الترقيم السنوي
                    if sequence.yearly_reset and sequence.include_year:
                        if sequence.last_reset_year != current_year:
                            sequence.next_number = 1
                            sequence.last_reset_year = current_year

                    # احفظ الرقم الحالي قبل الزيادة
                    current_number = sequence.next_number

                    # بناء الرقم
                    parts = []
                    if sequence.prefix:
                        parts.append(sequence.prefix)
                    if sequence.include_year:
                        parts.append(str(current_year))
                    if sequence.include_month:
                        parts.append(f"{current_month:02d}")
                    parts.append(str(current_number).zfill(sequence.padding))
                    if sequence.suffix:
                        parts.append(sequence.suffix)

                    number = sequence.separator.join(parts)

                    # زيادة العداد باستخدام F expression (atomic على مستوى قاعدة البيانات)
                    updated_rows = NumberingSequence.objects.filter(
                        pk=sequence.pk,
                        next_number=current_number  # تأكد أن القيمة لم تتغير
                    ).update(
                        next_number=F('next_number') + 1,
                        last_reset_year=current_year
                    )

                    # إذا لم يتم التحديث (لأن رقم آخر قام بالتغيير)، حاول مرة أخرى
                    if updated_rows == 0:
                        raise Exception("تم تعديل التسلسل من قبل عملية أخرى")

                # إذا نجحت العملية، اخرج من الحلقة
                print(f"✅ Generated number: {number} (attempt {attempt + 1})")
                return number

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Attempt {attempt + 1} failed: {error_msg}")
                # في حالة وجود أي خطأ، انتظر قليلاً وحاول مرة أخرى
                if attempt < max_attempts - 1:
                    wait_time = 0.05 * (2 ** attempt)  # Exponential backoff: 50ms, 100ms, 200ms, 400ms...
                    time.sleep(wait_time)
                    continue
                else:
                    # فشلت جميع المحاولات
                    raise ValidationError(f'فشل في توليد رقم القيد بعد {max_attempts} محاولات: {error_msg}')

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

        # التحقق الإضافي من الفترة المالية
        if self.entry_date and self.period:
            if not (self.period.start_date <= self.entry_date <= self.period.end_date):
                raise ValidationError(_('تاريخ القيد خارج نطاق الفترة المحاسبية'))

        # التحقق من السنة المالية
        if self.entry_date and self.fiscal_year:
            if not (self.fiscal_year.start_date <= self.entry_date <= self.fiscal_year.end_date):
                raise ValidationError(_('تاريخ القيد خارج نطاق السنة المالية'))

        # التحقق من إقفال الفترة
        if self.period and self.period.is_closed and self.status != 'posted':
            raise ValidationError(_('لا يمكن إنشاء قيود في فترة مقفلة'))

    @transaction.atomic
    def post(self, user=None):
        """ترحيل القيد وتحديث الأرصدة"""
        if self.status == 'posted':
            raise ValidationError(_('القيد مرحل مسبقاً'))

        self.calculate_totals()

        if not self.is_balanced:
            raise ValidationError(_('القيد غير متوازن'))

        if not self.lines.exists():
            raise ValidationError(_('لا توجد سطور في القيد'))

        # ترحيل القيد
        self.status = 'posted'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()

        # تحديث أرصدة الحسابات
        self.update_account_balances()

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل القيد وتحديث الأرصدة"""
        if self.status != 'posted':
            raise ValidationError(_('القيد غير مرحل'))

        # إلغاء الترحيل
        self.status = 'draft'
        self.posted_by = None
        self.posted_date = None
        self.save()

        # تحديث أرصدة الحسابات
        self.update_account_balances()

    def update_account_balances(self):
        """تحديث أرصدة جميع الحسابات المتأثرة"""
        from .balance_models import AccountBalance

        # الحصول على جميع الحسابات المتأثرة
        affected_accounts = set()
        for line in self.lines.all():
            affected_accounts.add(line.account)

        # تحديث رصيد كل حساب
        for account in affected_accounts:
            balance = AccountBalance.get_or_create_balance(
                account=account,
                fiscal_year=self.fiscal_year,
                period=self.period,
                company=self.company
            )
            balance.refresh_balance()

            # تسجيل التاريخ
            self.log_balance_change(account, balance)

    def log_balance_change(self, account, balance):
        """تسجيل تغيير الرصيد في التاريخ"""
        from .balance_models import AccountBalanceHistory

        # البحث عن آخر رصيد مسجل
        last_history = AccountBalanceHistory.objects.filter(
            account=account,
            company=self.company
        ).order_by('-change_date').first()

        old_debit = last_history.new_debit_balance if last_history else 0
        old_credit = last_history.new_credit_balance if last_history else 0

        # تسجيل التغيير
        AccountBalanceHistory.objects.create(
            account=account,
            company=self.company,
            change_reason=f"ترحيل قيد {self.number}",
            old_debit_balance=old_debit,
            old_credit_balance=old_credit,
            new_debit_balance=balance.closing_balance_debit,
            new_credit_balance=balance.closing_balance_credit,
            affected_amount=sum(
                [line.debit_amount + line.credit_amount for line in self.lines.filter(account=account)]),
            reference_type='journal_entry',
            reference_id=self.pk,
            changed_by=self.posted_by or self.created_by
        )

    def can_edit(self):
        """هل يمكن تعديل القيد"""
        return self.status == 'draft'

    def can_post(self):
        """هل يمكن ترحيل القيد"""
        return self.status == 'draft' and self.is_balanced and self.lines.exists()

    def can_unpost(self):
        """هل يمكن إلغاء ترحيل القيد"""
        return self.status == 'posted'

    def can_delete(self):
        """هل يمكن حذف القيد"""
        return self.status == 'draft'

    def get_absolute_url(self):
        return reverse('accounting:journal_entry_detail', kwargs={'pk': self.pk})

    def reverse_entry(self, user=None, reversal_date=None, reason=None):
        """
        عكس القيد المحاسبي (إنشاء قيد معكوس)

        Args:
            user: المستخدم الذي يقوم بالعكس
            reversal_date: تاريخ القيد العكسي (افتراضي: اليوم)
            reason: سبب العكس

        Returns:
            القيد العكسي الجديد
        """
        if self.status != 'posted':
            raise ValidationError(_('لا يمكن عكس قيد غير مرحّل'))

        if not reversal_date:
            reversal_date = date.today()

        # إنشاء القيد العكسي
        reversal_entry = JournalEntry(
            company=self.company,
            branch=self.branch,
            fiscal_year=self.fiscal_year,
            period=self.period,
            entry_date=reversal_date,
            entry_type='adjustment',
            description=f"عكس قيد: {self.number} - {reason or self.description}",
            reference=f"REV-{self.number}",
            source_document=self.source_document,
            source_id=self.source_id,
            created_by=user
        )

        # توليد رقم القيد العكسي
        reversal_entry.number = reversal_entry.generate_number()

        # حفظ القيد في transaction
        with transaction.atomic():
            reversal_entry.save()

            # نسخ السطور بشكل معكوس (المدين يصبح دائن والعكس)
            for line in self.lines.all():
                JournalEntryLine.objects.create(
                    journal_entry=reversal_entry,
                    line_number=line.line_number,
                    account=line.account,
                    description=f"عكس: {line.description}",
                    debit_amount=line.credit_amount,  # عكس
                    credit_amount=line.debit_amount,  # عكس
                    currency=line.currency,
                    exchange_rate=line.exchange_rate,
                    cost_center=line.cost_center
                )

            # ترحيل القيد العكسي تلقائياً
            reversal_entry.post(user=user)

        return reversal_entry

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
                                    related_name='journal_lines',
                                    verbose_name=_('مركز التكلفة'))

    # للربط مع الشركاء
    partner_type = models.CharField(
        _('نوع العميل'),
        max_length=20,
        choices=[('customer', _('عميل')), ('supplier', _('مورد')), ('employee', _('موظف')), ('other', _('أخرى'))],
        blank=True
    )
    partner_id = models.IntegerField(_('معرف العميل'), null=True, blank=True)

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
    description = models.CharField(_('البيان'), max_length=255, blank=True)

    # المبالغ - يمكن ترك أحدهما فارغ
    debit_amount = models.DecimalField(_('مدين'), max_digits=15, decimal_places=4, default=0)
    credit_amount = models.DecimalField(_('دائن'), max_digits=15, decimal_places=4, default=0)

    reference = models.CharField(_('المرجع'), max_length=100, blank=True)

    # مركز التكلفة الافتراضي
    default_cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL,
                                            null=True, blank=True,
                                            verbose_name=_('مركز التكلفة الافتراضي'))

    # هل هذا السطر مطلوب
    is_required = models.BooleanField(_('إجباري'), default=True)

    # هل يمكن تعديل المبلغ عند استخدام القالب
    amount_editable = models.BooleanField(_('المبلغ قابل للتعديل'), default=True)

    class Meta:
        verbose_name = _('سطر قالب قيد')
        verbose_name_plural = _('سطور قوالب القيود')
        ordering = ['line_number']
        unique_together = [['template', 'line_number']]

    def clean(self):
        """التحقق من صحة السطر"""
        # التأكد من أن أحد المبلغين فقط موجود (أو كلاهما صفر للمتغير)
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError(_('لا يمكن إدخال مبلغ في المدين والدائن معاً'))

        # التحقق من أن الحساب يقبل قيود
        if not self.account.accept_entries:
            raise ValidationError(f'الحساب {self.account.name} لا يقبل قيود مباشرة')

    def save(self, *args, **kwargs):
        # تعيين رقم السطر تلقائياً
        if not self.line_number:
            max_line = self.template.template_lines.aggregate(
                max_line=models.Max('line_number')
            )['max_line']
            self.line_number = (max_line or 0) + 1

        super().save(*args, **kwargs)

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
        return f"{self.template.name} - {self.line_number}: {self.account.name} ({amount} {side})"
# apps/assets/models/insurance_models.py
"""
نماذج التأمين على الأصول الثابتة
- شركات التأمين
- بوليصات التأمين
- مطالبات التأمين
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel, DocumentBaseModel
from decimal import Decimal
import datetime


class InsuranceCompany(BaseModel):
    """شركات التأمين"""

    code = models.CharField(_('رمز الشركة'), max_length=20)
    name = models.CharField(_('اسم شركة التأمين'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)

    # معلومات الاتصال
    contact_person = models.CharField(_('جهة الاتصال'), max_length=100, blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    mobile = models.CharField(_('الموبايل'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    fax = models.CharField(_('الفاكس'), max_length=20, blank=True)

    # العنوان
    address = models.TextField(_('العنوان'), blank=True)
    city = models.CharField(_('المدينة'), max_length=50, blank=True)
    country = models.CharField(_('الدولة'), max_length=50, blank=True)

    # معلومات إضافية
    website = models.URLField(_('الموقع الإلكتروني'), blank=True)
    license_number = models.CharField(_('رقم الترخيص'), max_length=50, blank=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('شركة تأمين')
        verbose_name_plural = _('شركات التأمين')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_active_policies_count(self):
        """عدد البوليصات النشطة"""
        return self.insurance_policies.filter(status='active').count()

    def get_total_coverage_amount(self):
        """إجمالي مبلغ التغطية للبوليصات النشطة"""
        total = self.insurance_policies.filter(
            status='active'
        ).aggregate(
            total=models.Sum('coverage_amount')
        )['total']
        return total or Decimal('0')


class AssetInsurance(DocumentBaseModel):
    """بوليصة تأمين الأصول"""

    COVERAGE_TYPES = [
        ('comprehensive', _('شامل')),
        ('fire', _('حريق')),
        ('theft', _('سرقة')),
        ('damage', _('أضرار')),
        ('liability', _('مسؤولية')),
        ('custom', _('مخصص')),
    ]

    PAYMENT_FREQUENCIES = [
        ('annual', _('سنوي')),
        ('semi_annual', _('نصف سنوي')),
        ('quarterly', _('ربع سنوي')),
        ('monthly', _('شهري')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('active', _('نشط')),
        ('expired', _('منتهي')),
        ('cancelled', _('ملغي')),
    ]

    # المعلومات الأساسية
    policy_number = models.CharField(
        _('رقم البوليصة'),
        max_length=50,
        editable=False,
        unique=True
    )

    insurance_company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.PROTECT,
        related_name='insurance_policies',
        verbose_name=_('شركة التأمين')
    )

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='insurances',
        verbose_name=_('الأصل')
    )

    # نوع التغطية
    coverage_type = models.CharField(
        _('نوع التغطية'),
        max_length=20,
        choices=COVERAGE_TYPES
    )
    coverage_description = models.TextField(
        _('وصف التغطية'),
        blank=True,
        help_text=_('تفاصيل التغطية والاستثناءات')
    )

    # المبالغ
    coverage_amount = models.DecimalField(
        _('مبلغ التغطية'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text=_('الحد الأقصى للتغطية')
    )
    premium_amount = models.DecimalField(
        _('قسط التأمين'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    deductible_amount = models.DecimalField(
        _('مبلغ التحمل'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ الذي تتحمله الشركة قبل التأمين')
    )

    # الدفع
    payment_frequency = models.CharField(
        _('دورية الدفع'),
        max_length=20,
        choices=PAYMENT_FREQUENCIES,
        default='annual'
    )
    next_payment_date = models.DateField(_('تاريخ الدفعة القادمة'), null=True, blank=True)

    # التواريخ
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    renewal_date = models.DateField(
        _('تاريخ التجديد'),
        null=True,
        blank=True,
        help_text=_('تاريخ التذكير بالتجديد')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # المرفقات
    policy_document = models.FileField(
        _('مستند البوليصة'),
        upload_to='assets/insurance/policies/%Y/%m/',
        blank=True
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('بوليصة تأمين أصل')
        verbose_name_plural = _('بوليصات تأمين الأصول')
        ordering = ['-start_date', '-policy_number']

    def save(self, *args, **kwargs):
        # توليد رقم البوليصة
        if not self.policy_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_insurance'
                )
                self.policy_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_insurance',
                    prefix='INS',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.policy_number = sequence.get_next_number()

        # تحديث حالة التأمين
        if self.status == 'active':
            self.asset.insurance_status = 'insured'
            self.asset.save(update_fields=['insurance_status'])

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.policy_number} - {self.asset.name} - {self.insurance_company.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            })

        if self.coverage_amount < self.asset.book_value:
            # تحذير فقط
            pass

    def is_active(self):
        """هل البوليصة نشطة"""
        today = datetime.date.today()
        return (
            self.status == 'active' and
            self.start_date <= today <= self.end_date
        )

    def is_expiring_soon(self, days=30):
        """هل البوليصة قريبة من الانتهاء"""
        today = datetime.date.today()
        expiry_threshold = self.end_date - datetime.timedelta(days=days)
        return today >= expiry_threshold and self.status == 'active'

    def get_remaining_days(self):
        """الأيام المتبقية"""
        today = datetime.date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    def get_total_paid_premium(self):
        """إجمالي الأقساط المدفوعة"""
        # يمكن ربطه بنظام المدفوعات لاحقاً
        return self.premium_amount

    def calculate_next_payment_date(self):
        """حساب تاريخ الدفعة القادمة"""
        from dateutil.relativedelta import relativedelta

        if not self.next_payment_date:
            self.next_payment_date = self.start_date
            return self.next_payment_date

        if self.payment_frequency == 'monthly':
            next_date = self.next_payment_date + relativedelta(months=1)
        elif self.payment_frequency == 'quarterly':
            next_date = self.next_payment_date + relativedelta(months=3)
        elif self.payment_frequency == 'semi_annual':
            next_date = self.next_payment_date + relativedelta(months=6)
        else:  # annual
            next_date = self.next_payment_date + relativedelta(years=1)

        if next_date <= self.end_date:
            self.next_payment_date = next_date
            self.save(update_fields=['next_payment_date'])
            return next_date

        return None


class InsuranceClaim(DocumentBaseModel):
    """مطالبات التأمين"""

    CLAIM_TYPES = [
        ('damage', _('ضرر')),
        ('theft', _('سرقة')),
        ('fire', _('حريق')),
        ('accident', _('حادث')),
        ('natural_disaster', _('كارثة طبيعية')),
        ('other', _('أخرى')),
    ]

    STATUS_CHOICES = [
        ('filed', _('مقدم')),
        ('under_review', _('قيد المراجعة')),
        ('approved', _('معتمد')),
        ('rejected', _('مرفوض')),
        ('paid', _('مدفوع')),
        ('cancelled', _('ملغي')),
    ]

    # المعلومات الأساسية
    claim_number = models.CharField(
        _('رقم المطالبة'),
        max_length=50,
        editable=False,
        unique=True
    )

    insurance = models.ForeignKey(
        AssetInsurance,
        on_delete=models.PROTECT,
        related_name='claims',
        verbose_name=_('بوليصة التأمين')
    )

    claim_type = models.CharField(
        _('نوع المطالبة'),
        max_length=20,
        choices=CLAIM_TYPES
    )

    # تفاصيل الحادث
    incident_date = models.DateField(_('تاريخ الحادث'))
    incident_time = models.TimeField(_('وقت الحادث'), null=True, blank=True)
    incident_location = models.CharField(_('مكان الحادث'), max_length=200, blank=True)
    incident_description = models.TextField(_('وصف الحادث'))

    # المبالغ
    estimated_damage = models.DecimalField(
        _('الضرر المقدر'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    claim_amount = models.DecimalField(
        _('مبلغ المطالبة'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    approved_amount = models.DecimalField(
        _('المبلغ المعتمد'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    deductible_applied = models.DecimalField(
        _('التحمل المطبق'),
        max_digits=15,
        decimal_places=3,
        default=0
    )
    net_payment = models.DecimalField(
        _('صافي الدفع'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('المبلغ المعتمد - التحمل')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='filed'
    )

    # التواريخ
    filed_date = models.DateField(_('تاريخ التقديم'), auto_now_add=True)
    review_date = models.DateField(_('تاريخ المراجعة'), null=True, blank=True)
    approval_date = models.DateField(_('تاريخ الاعتماد'), null=True, blank=True)
    payment_date = models.DateField(_('تاريخ الدفع'), null=True, blank=True)

    # المسؤولون
    filed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='filed_insurance_claims',
        verbose_name=_('قدم بواسطة')
    )
    reviewed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_insurance_claims',
        verbose_name=_('راجع بواسطة')
    )

    # المرفقات
    police_report = models.FileField(
        _('تقرير الشرطة'),
        upload_to='assets/insurance/claims/%Y/%m/police/',
        blank=True,
        help_text=_('إن وجد')
    )
    damage_photos = models.FileField(
        _('صور الضرر'),
        upload_to='assets/insurance/claims/%Y/%m/photos/',
        blank=True
    )
    repair_estimate = models.FileField(
        _('تقدير الإصلاح'),
        upload_to='assets/insurance/claims/%Y/%m/estimates/',
        blank=True
    )
    other_documents = models.FileField(
        _('مستندات أخرى'),
        upload_to='assets/insurance/claims/%Y/%m/other/',
        blank=True
    )

    # القيد المحاسبي (عند الدفع)
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_claims',
        verbose_name=_('القيد المحاسبي')
    )

    rejection_reason = models.TextField(_('سبب الرفض'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('مطالبة تأمين')
        verbose_name_plural = _('مطالبات التأمين')
        ordering = ['-filed_date', '-claim_number']

    def save(self, *args, **kwargs):
        # توليد رقم المطالبة
        if not self.claim_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='insurance_claim'
                )
                self.claim_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='insurance_claim',
                    prefix='CLM',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.claim_number = sequence.get_next_number()

        # حساب صافي الدفع
        self.net_payment = self.approved_amount - self.deductible_applied

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.claim_number} - {self.insurance.asset.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.claim_amount > self.insurance.coverage_amount:
            raise ValidationError({
                'claim_amount': _('مبلغ المطالبة يتجاوز حد التغطية')
            })

        if self.approved_amount > self.claim_amount:
            raise ValidationError({
                'approved_amount': _('المبلغ المعتمد لا يمكن أن يتجاوز مبلغ المطالبة')
            })

    @transaction.atomic
    def approve(self, approved_amount, user=None):
        """اعتماد المطالبة"""
        from django.utils import timezone

        if self.status not in ['filed', 'under_review']:
            raise ValidationError(_('لا يمكن اعتماد المطالبة في هذه الحالة'))

        self.approved_amount = approved_amount
        self.deductible_applied = self.insurance.deductible_amount
        self.status = 'approved'
        self.approval_date = timezone.now().date()
        self.reviewed_by = user
        self.save()

    @transaction.atomic
    def process_payment(self, user=None):
        """معالجة دفع المطالبة مع القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod
        from ..accounting_config import AssetAccountingConfiguration

        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد المطالبة قبل الدفع'))

        # ✅ الحصول على الإعدادات
        config = AssetAccountingConfiguration.get_or_create_for_company(self.company)
        insurance_accounts = config.get_insurance_accounts()

        payment_date = timezone.now().date()

        # الحصول على السنة والفترة
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
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

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=payment_date,
            entry_type='auto',
            description=f"تعويض تأمين {self.claim_number} - {self.insurance.asset.name}",
            reference=self.claim_number,
            source_document='insurance_claim',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # ✅ من: البنك (مدين) - المبلغ المستلم - ديناميكي
        cash_account = config.get_bank_account()
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=cash_account,
            description=f"تعويض تأمين - {self.insurance.asset.name}",
            debit_amount=self.net_payment,
            credit_amount=0,
            currency=self.company.base_currency
        )
        line_number += 1

        # ✅ من: مصروف التحمل (مدين) - إذا وجد - ديناميكي
        if self.deductible_applied > 0:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=insurance_accounts['deductible'],
                description=f"تحمل تأمين",
                debit_amount=self.deductible_applied,
                credit_amount=0,
                currency=self.company.base_currency
            )
            line_number += 1

        # ✅ إلى: إيراد تعويض تأمين (دائن) - ديناميكي
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=insurance_accounts['income'],
            description=f"تعويض ضرر على {self.insurance.asset.name}",
            debit_amount=0,
            credit_amount=self.approved_amount,
            currency=self.company.base_currency
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث المطالبة
        self.journal_entry = journal_entry
        self.status = 'paid'
        self.payment_date = payment_date
        self.save()

        return journal_entry

    def reject(self, reason, user=None):
        """رفض المطالبة"""
        if self.status not in ['filed', 'under_review']:
            raise ValidationError(_('لا يمكن رفض المطالبة في هذه الحالة'))

        self.status = 'rejected'
        self.rejection_reason = reason
        self.reviewed_by = user
        self.save()
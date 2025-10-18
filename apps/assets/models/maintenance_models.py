# apps/assets/models/maintenance_models.py
"""
نماذج الصيانة - محسّنة
- أنواع الصيانة
- جدولة الصيانة الدورية
- سجل الصيانة الفعلية
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import DocumentBaseModel, BusinessPartner
import datetime
from dateutil.relativedelta import relativedelta


class MaintenanceType(models.Model):
    """أنواع الصيانة"""

    name = models.CharField(_('نوع الصيانة'), max_length=100, unique=True)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100)
    code = models.CharField(_('الرمز'), max_length=20, unique=True)
    description = models.TextField(_('الوصف'), blank=True)
    is_active = models.BooleanField(_('نشط'), default=True)

    class Meta:
        verbose_name = _('نوع صيانة')
        verbose_name_plural = _('أنواع الصيانة')
        ordering = ['name']

    def __str__(self):
        return self.name


class MaintenanceSchedule(DocumentBaseModel):
    """جدولة الصيانة الدورية التلقائية"""

    FREQUENCY_CHOICES = [
        ('daily', _('يومي')),
        ('weekly', _('أسبوعي')),
        ('monthly', _('شهري')),
        ('quarterly', _('ربع سنوي')),
        ('semi_annual', _('نصف سنوي')),
        ('annual', _('سنوي')),
        ('custom', _('مخصص')),
    ]

    # المعلومات الأساسية
    schedule_number = models.CharField(
        _('رقم الجدولة'),
        max_length=50,
        editable=False,
        unique=True
    )

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.CASCADE,
        related_name='maintenance_schedules',
        verbose_name=_('الأصل')
    )

    maintenance_type = models.ForeignKey(
        MaintenanceType,
        on_delete=models.PROTECT,
        related_name='schedules',
        verbose_name=_('نوع الصيانة')
    )

    # التكرار
    frequency = models.CharField(
        _('التكرار'),
        max_length=20,
        choices=FREQUENCY_CHOICES
    )
    custom_days = models.IntegerField(
        _('عدد الأيام (للتكرار المخصص)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )

    # التواريخ
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(
        _('تاريخ النهاية'),
        null=True,
        blank=True,
        help_text=_('اتركه فارغاً للصيانة الدائمة')
    )
    next_maintenance_date = models.DateField(
        _('تاريخ الصيانة القادمة'),
        editable=False
    )

    # التنبيهات
    alert_before_days = models.IntegerField(
        _('التنبيه قبل (أيام)'),
        default=7,
        validators=[MinValueValidator(0)]
    )

    # المسؤولون
    assigned_to = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_schedules',
        verbose_name=_('مسند إلى')
    )

    # التكلفة المتوقعة
    estimated_cost = models.DecimalField(
        _('التكلفة المتوقعة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # الحالة
    is_active = models.BooleanField(_('نشط'), default=True)

    description = models.TextField(_('الوصف'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('جدولة صيانة')
        verbose_name_plural = _('جدولة الصيانة')
        ordering = ['next_maintenance_date']

    def save(self, *args, **kwargs):
        # توليد رقم الجدولة
        if not self.schedule_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_maintenance'
                )
                self.schedule_number = f"SCH{sequence.get_next_number()}"
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_maintenance',
                    prefix='SCH',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.schedule_number = sequence.get_next_number()

        # حساب تاريخ الصيانة القادمة إذا لم يكن محدداً
        if not self.next_maintenance_date:
            self.next_maintenance_date = self.start_date

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.schedule_number} - {self.asset.name} - {self.get_frequency_display()}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            })

        if self.frequency == 'custom' and not self.custom_days:
            raise ValidationError({
                'custom_days': _('يجب تحديد عدد الأيام للتكرار المخصص')
            })

    def calculate_next_maintenance_date(self):
        """حساب تاريخ الصيانة القادمة بناءً على التكرار"""
        current_date = self.next_maintenance_date

        if self.frequency == 'daily':
            next_date = current_date + datetime.timedelta(days=1)
        elif self.frequency == 'weekly':
            next_date = current_date + datetime.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            next_date = current_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            next_date = current_date + relativedelta(months=3)
        elif self.frequency == 'semi_annual':
            next_date = current_date + relativedelta(months=6)
        elif self.frequency == 'annual':
            next_date = current_date + relativedelta(years=1)
        elif self.frequency == 'custom' and self.custom_days:
            next_date = current_date + datetime.timedelta(days=self.custom_days)
        else:
            return None

        # التحقق من تاريخ النهاية
        if self.end_date and next_date > self.end_date:
            return None

        return next_date

    def update_next_maintenance_date(self):
        """تحديث تاريخ الصيانة القادمة"""
        next_date = self.calculate_next_maintenance_date()
        if next_date:
            self.next_maintenance_date = next_date
            self.save()
            return True
        else:
            self.is_active = False
            self.save()
            return False

    def is_due_soon(self):
        """هل الصيانة قريبة (خلال فترة التنبيه)"""
        today = datetime.date.today()
        alert_date = self.next_maintenance_date - datetime.timedelta(days=self.alert_before_days)
        return today >= alert_date

    def is_overdue(self):
        """هل الصيانة متأخرة"""
        return datetime.date.today() > self.next_maintenance_date


class AssetMaintenance(DocumentBaseModel):
    """سجل الصيانة الفعلية المنفذة"""

    STATUS_CHOICES = [
        ('scheduled', _('مجدولة')),
        ('in_progress', _('جارية')),
        ('completed', _('مكتملة')),
        ('cancelled', _('ملغاة')),
    ]

    MAINTENANCE_CATEGORY = [
        ('preventive', _('وقائية')),
        ('corrective', _('تصحيحية')),
        ('emergency', _('طارئة')),
        ('improvement', _('تحسين')),
    ]

    # المعلومات الأساسية
    maintenance_number = models.CharField(
        _('رقم الصيانة'),
        max_length=50,
        editable=False,
        unique=True
    )

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='maintenances',
        verbose_name=_('الأصل')
    )

    maintenance_type = models.ForeignKey(
        MaintenanceType,
        on_delete=models.PROTECT,
        related_name='maintenances',
        verbose_name=_('نوع الصيانة')
    )

    maintenance_category = models.CharField(
        _('تصنيف الصيانة'),
        max_length=20,
        choices=MAINTENANCE_CATEGORY,
        default='preventive'
    )

    # الربط بالجدولة
    maintenance_schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances',
        verbose_name=_('الجدولة'),
        help_text=_('إذا كانت الصيانة من جدول دوري')
    )

    # التواريخ
    scheduled_date = models.DateField(_('التاريخ المجدول'))
    start_date = models.DateField(_('تاريخ البدء'), null=True, blank=True)
    completion_date = models.DateField(_('تاريخ الإنجاز'), null=True, blank=True)

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    # المسؤولون
    performed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_maintenances',
        verbose_name=_('نفذ بواسطة')
    )

    # المورد (إذا كانت صيانة خارجية)
    external_vendor = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        related_name='asset_maintenances',
        verbose_name=_('المورد الخارجي')
    )
    vendor_invoice_number = models.CharField(
        _('رقم فاتورة المورد'),
        max_length=50,
        blank=True
    )

    # التكاليف
    labor_cost = models.DecimalField(
        _('تكلفة العمالة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    parts_cost = models.DecimalField(
        _('تكلفة قطع الغيار'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    other_cost = models.DecimalField(
        _('تكاليف أخرى'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_cost = models.DecimalField(
        _('إجمالي التكلفة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )

    # هل هي تحسين رأسمالي؟
    is_capital_improvement = models.BooleanField(
        _('تحسين رأسمالي'),
        default=False,
        help_text=_('إذا كانت نعم، ستضاف التكلفة لقيمة الأصل')
    )

    # قطع الغيار المستخدمة
    parts_description = models.TextField(_('وصف قطع الغيار'), blank=True)

    # الوصف والملاحظات
    description = models.TextField(_('وصف الأعمال المنفذة'))
    issues_found = models.TextField(_('المشاكل المكتشفة'), blank=True)
    recommendations = models.TextField(_('التوصيات'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    # المرفقات
    attachment = models.FileField(
        _('مرفق'),
        upload_to='assets/maintenance/%Y/%m/',
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_maintenances',
        verbose_name=_('القيد المحاسبي')
    )

    class Meta:
        verbose_name = _('صيانة أصل')
        verbose_name_plural = _('صيانة الأصول')
        ordering = ['-scheduled_date', '-maintenance_number']

    def save(self, *args, **kwargs):
        # توليد رقم الصيانة
        if not self.maintenance_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset_maintenance'
                )
                self.maintenance_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset_maintenance',
                    prefix='MAINT',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.maintenance_number = sequence.get_next_number()

        # حساب إجمالي التكلفة
        self.total_cost = self.labor_cost + self.parts_cost + self.other_cost

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.maintenance_number} - {self.asset.name} - {self.scheduled_date}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.completion_date and self.start_date:
            if self.completion_date < self.start_date:
                raise ValidationError({
                    'completion_date': _('تاريخ الإنجاز يجب أن يكون بعد تاريخ البدء')
                })

        if self.status == 'completed' and not self.completion_date:
            raise ValidationError({
                'completion_date': _('يجب تحديد تاريخ الإنجاز للصيانة المكتملة')
            })

    @transaction.atomic
    def mark_as_completed(self, completion_date=None, user=None):
        """وضع علامة مكتمل على الصيانة مع القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod
        from ..accounting_config import AssetAccountingConfiguration

        self.status = 'completed'
        self.completion_date = completion_date or datetime.date.today()

        # ✅ الحصول على الإعدادات
        config = AssetAccountingConfiguration.get_or_create_for_company(self.company)

        # إنشاء القيد المحاسبي للصيانة
        if self.total_cost > 0:
            try:
                fiscal_year = FiscalYear.objects.get(
                    company=self.company,
                    start_date__lte=self.completion_date,
                    end_date__gte=self.completion_date,
                    is_closed=False
                )
            except FiscalYear.DoesNotExist:
                raise ValidationError(_('لا توجد سنة مالية نشطة'))

            period = AccountingPeriod.objects.filter(
                fiscal_year=fiscal_year,
                start_date__lte=self.completion_date,
                end_date__gte=self.completion_date,
                is_closed=False
            ).first()

            # ✅ التحقق: هل تحسين رأسمالي؟
            if self.is_capital_improvement:
                # إضافة التكلفة للأصل
                self.asset.original_cost += self.total_cost
                self.asset.book_value += self.total_cost
                self.asset.save()

                # قيد تحسين رأسمالي
                journal_entry = JournalEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    fiscal_year=fiscal_year,
                    period=period,
                    entry_date=self.completion_date,
                    entry_type='auto',
                    description=f"تحسين رأسمالي - صيانة {self.maintenance_number} - {self.asset.name}",
                    reference=self.maintenance_number,
                    source_document='asset_maintenance',
                    source_id=self.pk,
                    created_by=user or self.created_by
                )

                # من: حساب الأصل (مدين)
                if not self.asset.category.asset_account:
                    raise ValidationError(
                        _('لم يتم تحديد حساب الأصول في فئة الأصل')
                    )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=1,
                    account=self.asset.category.asset_account,
                    description=f"تحسين رأسمالي على {self.asset.name}",
                    debit_amount=self.total_cost,
                    credit_amount=0,
                    currency=self.company.base_currency
                )

                # إلى: البنك/الصندوق أو المورد (دائن)
                if self.external_vendor:
                    # دفع للمورد
                    payable_account = config.get_supplier_account(self.external_vendor)
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=2,
                        account=payable_account,
                        description=f"مستحق للمورد - {self.external_vendor.name}",
                        debit_amount=0,
                        credit_amount=self.total_cost,
                        currency=self.company.base_currency,
                        partner_type='supplier',
                        partner_id=self.external_vendor.pk
                    )
                else:
                    # دفع نقدي
                    cash_account = config.get_cash_account()
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=2,
                        account=cash_account,
                        description=f"دفع تحسين رأسمالي",
                        debit_amount=0,
                        credit_amount=self.total_cost,
                        currency=self.company.base_currency
                    )

            else:
                # صيانة عادية - قيد مصروف
                journal_entry = JournalEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    fiscal_year=fiscal_year,
                    period=period,
                    entry_date=self.completion_date,
                    entry_type='auto',
                    description=f"مصروف صيانة {self.maintenance_number} - {self.asset.name}",
                    reference=self.maintenance_number,
                    source_document='asset_maintenance',
                    source_id=self.pk,
                    created_by=user or self.created_by
                )

                # ✅ من: مصروف الصيانة (مدين) - ديناميكي
                maintenance_expense_account = config.get_maintenance_expense_account(
                    category=self.asset.category
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=1,
                    account=maintenance_expense_account,
                    description=f"صيانة {self.asset.name}",
                    debit_amount=self.total_cost,
                    credit_amount=0,
                    currency=self.company.base_currency,
                    cost_center=self.asset.cost_center
                )

                # إلى: البنك/الصندوق أو المورد (دائن)
                if self.external_vendor:
                    # دفع للمورد
                    payable_account = config.get_supplier_account(self.external_vendor)
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=2,
                        account=payable_account,
                        description=f"مستحق للمورد - {self.external_vendor.name}",
                        debit_amount=0,
                        credit_amount=self.total_cost,
                        currency=self.company.base_currency,
                        partner_type='supplier',
                        partner_id=self.external_vendor.pk
                    )
                else:
                    # دفع نقدي
                    cash_account = config.get_cash_account()
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=2,
                        account=cash_account,
                        description=f"دفع نقدي لصيانة",
                        debit_amount=0,
                        credit_amount=self.total_cost,
                        currency=self.company.base_currency
                    )

            # ترحيل القيد
            journal_entry.post(user=user)

            # ربط القيد بالصيانة
            self.journal_entry = journal_entry

        self.save()

        # تحديث تاريخ الجدولة القادم إذا كانت مرتبطة بجدول
        if self.maintenance_schedule:
            self.maintenance_schedule.update_next_maintenance_date()

    def get_duration_days(self):
        """حساب مدة الصيانة بالأيام"""
        if self.start_date and self.completion_date:
            return (self.completion_date - self.start_date).days
        return None

    def is_overdue(self):
        """هل الصيانة متأخرة"""
        if self.status in ['completed', 'cancelled']:
            return False
        return datetime.date.today() > self.scheduled_date
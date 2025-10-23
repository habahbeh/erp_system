# apps/assets/models/physical_count_models.py
"""
نماذج الجرد الفعلي للأصول الثابتة
- دورات الجرد
- عمليات الجرد
- سطور الجرد
- قيود التسوية
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel, DocumentBaseModel
from decimal import Decimal
import datetime


class PhysicalCountCycle(BaseModel):
    """دورة الجرد - سنوية/نصف سنوية/ربع سنوية"""

    CYCLE_TYPES = [
        ('monthly', _('شهري')),
        ('quarterly', _('ربع سنوي')),
        ('semi_annual', _('نصف سنوي')),
        ('annual', _('سنوي')),
    ]

    STATUS_CHOICES = [
        ('planning', _('في التخطيط')),
        ('in_progress', _('جارية')),
        ('completed', _('مكتملة')),
        ('cancelled', _('ملغاة')),
    ]

    cycle_number = models.CharField(
        _('رقم الدورة'),
        max_length=50,
        editable=False,
        unique=True
    )

    name = models.CharField(_('اسم الدورة'), max_length=200)
    cycle_type = models.CharField(_('نوع الدورة'), max_length=20, choices=CYCLE_TYPES)

    # التواريخ
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    planned_completion_date = models.DateField(_('تاريخ الإنجاز المخطط'))

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )

    # الفروع المشمولة
    branches = models.ManyToManyField(
        'core.Branch',
        verbose_name=_('الفروع المشمولة'),
        related_name='physical_count_cycles'
    )

    # فئات الأصول المشمولة
    asset_categories = models.ManyToManyField(
        'AssetCategory',
        verbose_name=_('فئات الأصول المشمولة'),
        related_name='physical_count_cycles',
        blank=True,
        help_text=_('اتركها فارغة لتشمل جميع الفئات')
    )

    # الفريق المسؤول
    team_leader = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='led_count_cycles',
        verbose_name=_('قائد الفريق')
    )

    team_members = models.ManyToManyField(
        'core.User',
        verbose_name=_('أعضاء الفريق'),
        related_name='count_cycles',
        blank=True
    )

    # الإحصائيات
    total_assets = models.IntegerField(_('إجمالي الأصول'), default=0, editable=False)
    counted_assets = models.IntegerField(_('الأصول المجردة'), default=0, editable=False)
    variance_count = models.IntegerField(_('عدد الفروقات'), default=0, editable=False)

    description = models.TextField(_('الوصف'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('دورة جرد')
        verbose_name_plural = _('دورات الجرد')
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        # توليد رقم الدورة
        if not self.cycle_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='physical_count_cycle'
                )
                self.cycle_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='physical_count_cycle',
                    prefix='CYC',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.cycle_number = sequence.get_next_number()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cycle_number} - {self.name}"

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            })

        if self.planned_completion_date < self.start_date:
            raise ValidationError({
                'planned_completion_date': _('تاريخ الإنجاز المخطط يجب أن يكون بعد تاريخ البداية')
            })

    def update_statistics(self):
        """تحديث الإحصائيات"""
        counts = self.physical_counts.all()

        self.total_assets = sum(c.total_assets for c in counts)
        self.counted_assets = sum(c.counted_assets for c in counts)
        self.variance_count = sum(c.variance_count for c in counts)

        self.save(update_fields=['total_assets', 'counted_assets', 'variance_count'])

    def get_completion_percentage(self):
        """نسبة الإنجاز"""
        if self.total_assets == 0:
            return 0
        return (self.counted_assets / self.total_assets) * 100

    # ═══════════════════════════════════════════════════════════════
    # 🔒 Validation Methods - التحقق من الصلاحيات
    # ═══════════════════════════════════════════════════════════════

    def can_edit(self):
        """هل يمكن تعديل دورة الجرد؟"""
        # لا يمكن تعديل دورة مكتملة أو ملغاة
        if self.status in ['completed', 'cancelled']:
            return False

        # لا يمكن تعديل إذا كانت جارية ولديها جرد معتمد
        if self.status == 'in_progress':
            has_approved_counts = self.physical_counts.filter(
                status='approved'
            ).exists()
            if has_approved_counts:
                return False

        return True

    def can_delete(self):
        """هل يمكن حذف دورة الجرد؟"""
        # لا يمكن حذف دورة جارية أو مكتملة
        if self.status in ['in_progress', 'completed']:
            return False

        # لا يمكن حذف إذا كان لديها عمليات جرد
        if self.physical_counts.exists():
            return False

        return True

    def can_start(self):
        """هل يمكن بدء دورة الجرد؟"""
        # يمكن البدء فقط من حالة التخطيط
        if self.status != 'planning':
            return False

        # يجب أن يكون هناك فروع مشمولة
        if not self.branches.exists():
            return False

        # يجب تحديد قائد الفريق
        if not self.team_leader:
            return False

        return True

    def can_complete(self):
        """هل يمكن إكمال دورة الجرد؟"""
        # يمكن الإكمال فقط من حالة جارية
        if self.status != 'in_progress':
            return False

        # يجب أن تكون جميع عمليات الجرد مكتملة أو معتمدة
        pending_counts = self.physical_counts.filter(
            status__in=['draft', 'in_progress']
        ).exists()

        if pending_counts:
            return False

        return True

    # ═══════════════════════════════════════════════════════════════
    # 💼 Business Methods - طرق العمليات
    # ═══════════════════════════════════════════════════════════════

    @transaction.atomic
    def start_cycle(self, user=None):
        """بدء دورة الجرد"""
        if not self.can_start():
            raise ValidationError('لا يمكن بدء هذه الدورة. تحقق من الحالة والبيانات المطلوبة')

        self.status = 'in_progress'
        self.save(update_fields=['status', 'updated_at'])

        return self

    @transaction.atomic
    def complete_cycle(self, user=None):
        """إكمال دورة الجرد"""
        if not self.can_complete():
            raise ValidationError('لا يمكن إكمال هذه الدورة. تحقق من حالة عمليات الجرد')

        # تحديث الإحصائيات النهائية
        self.update_statistics()

        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])

        return self


class PhysicalCount(DocumentBaseModel):
    """عملية جرد فعلية واحدة"""

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('in_progress', _('جاري')),
        ('completed', _('مكتمل')),
        ('approved', _('معتمد')),
        ('cancelled', _('ملغي')),
    ]

    count_number = models.CharField(
        _('رقم الجرد'),
        max_length=50,
        editable=False,
        unique=True
    )

    # الربط بالدورة
    cycle = models.ForeignKey(
        PhysicalCountCycle,
        on_delete=models.PROTECT,
        related_name='physical_counts',
        verbose_name=_('دورة الجرد'),
        null=True,
        blank=True,
        help_text=_('اتركها فارغة للجرد الطارئ')
    )

    count_date = models.DateField(_('تاريخ الجرد'))

    # الموقع
    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        verbose_name=_('الفرع')
    )

    location = models.CharField(
        _('الموقع المحدد'),
        max_length=200,
        blank=True,
        help_text=_('مثل: المستودع الرئيسي، الطابق الثالث')
    )

    # الفريق
    responsible_team = models.ManyToManyField(
        'core.User',
        verbose_name=_('الفريق المسؤول'),
        related_name='physical_counts'
    )

    supervisor = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_counts',
        verbose_name=_('المشرف')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # الإحصائيات
    total_assets = models.IntegerField(_('إجمالي الأصول'), default=0, editable=False)
    counted_assets = models.IntegerField(_('الأصول المجردة'), default=0, editable=False)
    found_assets = models.IntegerField(_('الأصول الموجودة'), default=0, editable=False)
    missing_assets = models.IntegerField(_('الأصول المفقودة'), default=0, editable=False)
    variance_count = models.IntegerField(_('عدد الفروقات'), default=0, editable=False)

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_physical_counts',
        verbose_name=_('اعتمد بواسطة')
    )
    approved_date = models.DateTimeField(_('تاريخ الاعتماد'), null=True, blank=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('جرد فعلي')
        verbose_name_plural = _('الجرد الفعلي')
        ordering = ['-count_date', '-count_number']

    def save(self, *args, **kwargs):
        # توليد رقم الجرد
        if not self.count_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='physical_count'
                )
                self.count_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='physical_count',
                    prefix='CNT',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.count_number = sequence.get_next_number()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.count_number} - {self.branch.name} - {self.count_date}"

    def update_statistics(self):
        """تحديث الإحصائيات"""
        lines = self.lines.all()

        self.total_assets = lines.count()
        self.counted_assets = lines.filter(is_counted=True).count()
        self.found_assets = lines.filter(is_found=True).count()
        self.missing_assets = lines.filter(is_found=False).count()
        self.variance_count = lines.filter(
            models.Q(has_location_variance=True) |
            models.Q(has_condition_variance=True) |
            models.Q(has_responsible_variance=True) |
            models.Q(is_found=False)
        ).count()

        self.save(update_fields=[
            'total_assets', 'counted_assets', 'found_assets',
            'missing_assets', 'variance_count'
        ])

        # تحديث إحصائيات الدورة
        if self.cycle:
            self.cycle.update_statistics()

    # ═══════════════════════════════════════════════════════════════
    # 🔒 Validation Methods - التحقق من الصلاحيات
    # ═══════════════════════════════════════════════════════════════

    def can_edit(self):
        """هل يمكن تعديل الجرد؟"""
        # لا يمكن تعديل جرد معتمد أو ملغي
        if self.status in ['approved', 'cancelled']:
            return False

        # لا يمكن تعديل إذا كانت الدورة مكتملة
        if self.cycle and self.cycle.status == 'completed':
            return False

        return True

    def can_delete(self):
        """هل يمكن حذف الجرد؟"""
        # لا يمكن حذف جرد معتمد
        if self.status == 'approved':
            return False

        # لا يمكن حذف إذا كان له سطور جرد
        if self.lines.exists():
            return False

        return True

    def can_approve(self):
        """هل يمكن اعتماد الجرد؟"""
        # يمكن الاعتماد فقط من حالة مكتمل
        if self.status != 'completed':
            return False

        # يجب أن تكون جميع الأصول مجردة
        if self.counted_assets < self.total_assets:
            return False

        # يجب أن يكون هناك أصول للجرد
        if self.total_assets == 0:
            return False

        return True

    def can_start(self):
        """هل يمكن بدء الجرد؟"""
        # يمكن البدء فقط من حالة مسودة
        if self.status != 'draft':
            return False

        # يجب أن يكون هناك فريق مسؤول
        if not self.responsible_team.exists():
            return False

        return True

    def can_complete(self):
        """هل يمكن إكمال الجرد؟"""
        # يمكن الإكمال من حالة جاري فقط
        if self.status != 'in_progress':
            return False

        # يجب جرد جميع الأصول
        if self.counted_assets < self.total_assets:
            return False

        return True

    # ═══════════════════════════════════════════════════════════════
    # 💼 Business Methods - طرق العمليات
    # ═══════════════════════════════════════════════════════════════

    @transaction.atomic
    def approve(self, user):
        """اعتماد الجرد"""
        from django.utils import timezone

        # ✅ استخدام validation method
        if not self.can_approve():
            raise ValidationError(_('لا يمكن اعتماد هذا الجرد. تحقق من حالته والأصول المجردة'))

        self.status = 'approved'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.save()

        # تحديث تواريخ آخر جرد للأصول
        for line in self.lines.all():
            line.asset.last_physical_count_date = self.count_date
            if line.actual_location:
                line.asset.actual_location = line.actual_location
                line.asset.location_verified_date = self.count_date
            line.asset.save(update_fields=['last_physical_count_date', 'actual_location', 'location_verified_date'])


class PhysicalCountLine(models.Model):
    """سطر الجرد - لكل أصل"""

    physical_count = models.ForeignKey(
        PhysicalCount,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('الجرد')
    )

    line_number = models.IntegerField(_('رقم السطر'))

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='physical_count_lines',
        verbose_name=_('الأصل')
    )

    # الحالة المتوقعة (من السجلات)
    expected_location = models.CharField(_('الموقع المتوقع'), max_length=200)
    expected_condition = models.ForeignKey(
        'AssetCondition',
        on_delete=models.PROTECT,
        related_name='expected_in_counts',
        verbose_name=_('الحالة المتوقعة'),
        null=True,
        blank=True
    )
    expected_responsible = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expected_responsible_for',
        verbose_name=_('المسؤول المتوقع')
    )

    # الحالة الفعلية (من الجرد)
    is_found = models.BooleanField(_('موجود'), default=False)
    is_counted = models.BooleanField(_('تم الجرد'), default=False)

    actual_location = models.CharField(_('الموقع الفعلي'), max_length=200, blank=True)
    actual_condition = models.ForeignKey(
        'AssetCondition',
        on_delete=models.PROTECT,
        related_name='actual_in_counts',
        verbose_name=_('الحالة الفعلية'),
        null=True,
        blank=True
    )
    actual_responsible = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actual_responsible_for',
        verbose_name=_('المسؤول الفعلي')
    )

    # الفروقات
    has_location_variance = models.BooleanField(_('فرق في الموقع'), default=False, editable=False)
    has_condition_variance = models.BooleanField(_('فرق في الحالة'), default=False, editable=False)
    has_responsible_variance = models.BooleanField(_('فرق في المسؤول'), default=False, editable=False)

    # تاريخ ووقت الجرد
    counted_date = models.DateTimeField(_('تاريخ ووقت الجرد'), null=True, blank=True)
    counted_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counted_assets',
        verbose_name=_('جرد بواسطة')
    )

    # ملاحظات وصور
    notes = models.TextField(_('ملاحظات'), blank=True)
    photos = models.JSONField(
        _('صور الأصل'),
        default=list,
        blank=True,
        help_text=_('قائمة بروابط الصور الملتقطة أثناء الجرد')
    )

    # الإجراء المطلوب
    requires_adjustment = models.BooleanField(
        _('يحتاج تسوية'),
        default=False,
        help_text=_('فقد أو تلف يحتاج قيد محاسبي')
    )

    class Meta:
        verbose_name = _('سطر جرد')
        verbose_name_plural = _('سطور الجرد')
        ordering = ['physical_count', 'line_number']
        unique_together = [['physical_count', 'line_number']]

    def save(self, *args, **kwargs):
        # تعيين رقم السطر تلقائياً
        if not self.line_number:
            max_line = self.physical_count.lines.aggregate(
                max_line=models.Max('line_number')
            )['max_line']
            self.line_number = (max_line or 0) + 1

        # تحديد الفروقات
        if self.is_counted and self.is_found:
            self.has_location_variance = (
                self.expected_location.strip().lower() != self.actual_location.strip().lower()
            )
            self.has_condition_variance = (
                self.expected_condition != self.actual_condition
            )
            self.has_responsible_variance = (
                self.expected_responsible != self.actual_responsible
            )

            # إذا كانت الحالة سيئة أو مفقود، يحتاج تسوية
            if not self.is_found or (
                self.actual_condition and
                self.actual_condition.name.lower() in ['تالف', 'معطل', 'damaged', 'broken']
            ):
                self.requires_adjustment = True

        super().save(*args, **kwargs)

        # تحديث إحصائيات الجرد
        self.physical_count.update_statistics()

    def __str__(self):
        return f"{self.physical_count.count_number} - {self.line_number}: {self.asset.name}"

    def has_any_variance(self):
        """هل يوجد أي فرق"""
        return (
            not self.is_found or
            self.has_location_variance or
            self.has_condition_variance or
            self.has_responsible_variance
        )


class PhysicalCountAdjustment(DocumentBaseModel):
    """قيود تسوية الجرد للفقد والتلف"""

    ADJUSTMENT_TYPES = [
        ('loss', _('فقد')),
        ('damage', _('تلف')),
        ('write_off', _('إعدام')),
        ('correction', _('تصحيح')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('approved', _('معتمد')),
        ('posted', _('مرحّل')),
        ('cancelled', _('ملغي')),
    ]

    adjustment_number = models.CharField(
        _('رقم التسوية'),
        max_length=50,
        editable=False,
        unique=True
    )

    physical_count_line = models.ForeignKey(
        PhysicalCountLine,
        on_delete=models.PROTECT,
        related_name='adjustments',
        verbose_name=_('سطر الجرد')
    )

    adjustment_type = models.CharField(
        _('نوع التسوية'),
        max_length=20,
        choices=ADJUSTMENT_TYPES
    )

    adjustment_date = models.DateField(_('تاريخ التسوية'))

    # المبالغ
    asset_original_cost = models.DecimalField(
        _('التكلفة الأصلية'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )
    accumulated_depreciation = models.DecimalField(
        _('الإهلاك المتراكم'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )
    book_value = models.DecimalField(
        _('القيمة الدفترية'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )
    loss_amount = models.DecimalField(
        _('مبلغ الخسارة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('القيمة الدفترية = الخسارة')
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='physical_count_adjustments',
        verbose_name=_('القيد المحاسبي')
    )

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_count_adjustments',
        verbose_name=_('اعتمد بواسطة')
    )
    approved_date = models.DateTimeField(_('تاريخ الاعتماد'), null=True, blank=True)

    reason = models.TextField(_('السبب'))
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('تسوية جرد')
        verbose_name_plural = _('تسويات الجرد')
        ordering = ['-adjustment_date', '-adjustment_number']

    def save(self, *args, **kwargs):
        # توليد رقم التسوية
        if not self.adjustment_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='count_adjustment'
                )
                self.adjustment_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='count_adjustment',
                    prefix='CADJ',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.adjustment_number = sequence.get_next_number()

        # حفظ المبالغ من الأصل
        asset = self.physical_count_line.asset
        self.asset_original_cost = asset.original_cost
        self.accumulated_depreciation = asset.accumulated_depreciation
        self.book_value = asset.book_value
        self.loss_amount = self.book_value

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adjustment_number} - {self.physical_count_line.asset.name}"

    @transaction.atomic
    def post(self, user=None):
        """ترحيل قيد التسوية"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, Account, FiscalYear, AccountingPeriod

        if self.status == 'posted':
            raise ValidationError(_('التسوية مرحلة مسبقاً'))

        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد التسوية قبل الترحيل'))

        # الحصول على السنة والفترة
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.adjustment_date,
                end_date__gte=self.adjustment_date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة'))

        period = AccountingPeriod.objects.filter(
            fiscal_year=fiscal_year,
            start_date__lte=self.adjustment_date,
            end_date__gte=self.adjustment_date,
            is_closed=False
        ).first()

        asset = self.physical_count_line.asset

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.adjustment_date,
            entry_type='auto',
            description=f"تسوية جرد - {self.get_adjustment_type_display()} - {asset.name}",
            reference=self.adjustment_number,
            source_document='physical_count_adjustment',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # 1. مجمع الإهلاك (مدين)
        if self.accumulated_depreciation > 0:
            acc_depreciation_account = asset.category.accumulated_depreciation_account
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=acc_depreciation_account,
                description=f"إقفال مجمع إهلاك أصل {self.get_adjustment_type_display().lower()}",
                debit_amount=self.accumulated_depreciation,
                credit_amount=0,
                currency=self.company.base_currency
            )
            line_number += 1

        # 2. خسارة الفقد/التلف (مدين)
        if self.loss_amount > 0:
            loss_account = asset.category.loss_on_disposal_account
            if not loss_account:
                loss_account = asset.category.loss_on_disposal_account

            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=loss_account,
                description=f"خسارة {self.get_adjustment_type_display().lower()} من الجرد - {asset.name}",
                debit_amount=self.loss_amount,
                credit_amount=0,
                currency=self.company.base_currency,
                cost_center=asset.cost_center
            )
            line_number += 1

        # 3. حساب الأصل (دائن)
        asset_account = asset.category.asset_account
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=asset_account,
            description=f"إقفال أصل {self.get_adjustment_type_display().lower()} - {asset.name}",
            debit_amount=0,
            credit_amount=self.asset_original_cost,
            currency=self.company.base_currency
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث التسوية
        self.journal_entry = journal_entry
        self.status = 'posted'
        self.save()

        # تحديث حالة الأصل
        if self.adjustment_type == 'loss':
            asset.status = 'lost'
        elif self.adjustment_type == 'damage':
            asset.status = 'damaged'
        elif self.adjustment_type == 'write_off':
            asset.status = 'disposed'

        asset.save()

        return journal_entry
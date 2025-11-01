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

    # ============================================================
    # Validation Methods - متى يمكن التعديل/الحذف/الإتمام
    # ============================================================

    def can_edit(self):
        """
        هل يمكن تعديل العملية؟

        Returns:
            bool: True إذا كان يمكن التعديل
        """
        # لا يمكن تعديل العملية المكتملة أو الملغاة
        if self.status in ['completed', 'cancelled']:
            return False

        # إذا كان لها قيد محاسبي مرحّل
        if self.journal_entry and self.journal_entry.status == 'posted':
            return False

        return True

    def can_delete(self):
        """
        هل يمكن حذف العملية؟

        Returns:
            bool: True إذا كان يمكن الحذف
        """
        # لا يمكن حذف العملية المكتملة
        if self.status == 'completed':
            return False

        # إذا كان لها قيد محاسبي
        if self.journal_entry:
            return False

        return True

    def can_post(self):
        """
        هل يمكن ترحيل العملية (إنشاء القيد)؟

        Returns:
            bool: True إذا كان يمكن الترحيل
        """
        # يجب أن تكون معتمدة
        if self.status != 'approved':
            return False

        # لا يجب أن يكون لها قيد مسبقاً
        if self.journal_entry:
            return False

        return True

    # ============================================================
    # Accounting Methods - إنشاء القيود المحاسبية
    # ============================================================

    @transaction.atomic
    def create_journal_entry(self, user=None):
        """
        إنشاء قيد محاسبي حسب نوع العملية

        Args:
            user: المستخدم الذي ينشئ القيد

        Returns:
            JournalEntry: القيد المحاسبي المنشأ
        """
        if self.transaction_type == 'purchase':
            return self.asset.create_purchase_journal_entry(user=user)
        elif self.transaction_type == 'sale':
            return self.asset.sell(
                sale_price=self.sale_price,
                buyer=self.business_partner,
                user=user
            )
        elif self.transaction_type == 'disposal':
            return self.asset.dispose(
                reason=self.description,
                user=user
            )
        else:
            raise ValidationError(
                f'نوع العملية {self.get_transaction_type_display()} لا يدعم إنشاء قيد تلقائياً'
            )

    def post(self, user=None):
        """
        ترحيل العملية (إنشاء القيد وتحديث الحالة)

        Args:
            user: المستخدم الذي يرحّل
        """
        if not self.can_post():
            raise ValidationError('لا يمكن ترحيل هذه العملية')

        # إنشاء القيد
        journal_entry = self.create_journal_entry(user=user)

        # تحديث الحالة
        self.status = 'completed'
        self.journal_entry = journal_entry
        self.save()

        return journal_entry


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
        if self.transfer_number and hasattr(self, 'asset') and self.asset:
            parts = [self.transfer_number, self.asset.name]

            if hasattr(self, 'from_branch') and self.from_branch and hasattr(self, 'to_branch') and self.to_branch:
                parts.append(f"{self.from_branch.name} → {self.to_branch.name}")

            return " - ".join(parts)
        return str(_('تحويل جديد'))

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.from_branch == self.to_branch and self.from_cost_center == self.to_cost_center and self.from_employee == self.to_employee:
            raise ValidationError(_('يجب أن يكون هناك تغيير في الموقع أو المسؤولية'))

    # ============================================================
    # Validation Methods - متى يمكن التعديل/الحذف/الإتمام
    # ============================================================

    def can_edit(self):
        """
        هل يمكن تعديل التحويل؟

        Returns:
            bool: True إذا كان يمكن التعديل
        """
        # يمكن التعديل فقط إذا كان معلق أو مرفوض
        if self.status not in ['pending', 'rejected']:
            return False

        # إذا تم التسليم أو الاستلام، لا يمكن التعديل
        if self.delivered_at or self.received_at:
            return False

        return True

    def can_delete(self):
        """
        هل يمكن حذف التحويل؟

        Returns:
            bool: True إذا كان يمكن الحذف
        """
        # يمكن الحذف فقط إذا كان معلق
        if self.status != 'pending':
            return False

        # إذا تم التسليم أو الاستلام، لا يمكن الحذف
        if self.delivered_at or self.received_at:
            return False

        return True

    def can_approve(self):
        """
        هل يمكن الموافقة على التحويل؟

        Returns:
            bool: True إذا كان يمكن الموافقة
        """
        # يمكن الموافقة فقط إذا كان معلق
        if self.status != 'pending':
            return False

        return True

    def can_reject(self):
        """
        هل يمكن رفض التحويل؟

        Returns:
            bool: True إذا كان يمكن الرفض
        """
        # يمكن الرفض فقط إذا كان معلق
        if self.status != 'pending':
            return False

        return True

    def can_complete(self):
        """
        هل يمكن إكمال التحويل؟

        Returns:
            bool: True إذا كان يمكن الإكمال
        """
        # يجب أن يكون معتمد
        if self.status != 'approved':
            return False

        # يجب أن يكون تم التسليم والاستلام
        if not self.delivered_at or not self.received_at:
            return False

        return True

    # ============================================================
    # Business Methods - العمليات التجارية
    # ============================================================

    @transaction.atomic
    def approve(self, user=None):
        """
        الموافقة على التحويل

        Args:
            user: المستخدم الموافق

        Returns:
            self: التحويل بعد الموافقة
        """
        from django.utils import timezone

        # ✅ استخدام validation method
        if not self.can_approve():
            raise ValidationError(_('لا يمكن الموافقة على هذا التحويل. تحقق من حالته'))

        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

        return self

    @transaction.atomic
    def reject(self, reason='', user=None):
        """
        رفض التحويل

        Args:
            reason: سبب الرفض
            user: المستخدم الرافض

        Returns:
            self: التحويل بعد الرفض
        """
        # ✅ استخدام validation method
        if not self.can_reject():
            raise ValidationError(_('لا يمكن رفض هذا التحويل. تحقق من حالته'))

        self.status = 'rejected'
        if reason:
            self.notes = f"{self.notes}\n\nسبب الرفض: {reason}" if self.notes else f"سبب الرفض: {reason}"
        self.save(update_fields=['status', 'notes', 'updated_at'])

        return self

    @transaction.atomic
    def complete(self, user=None):
        """
        إكمال التحويل وتحديث بيانات الأصل

        Args:
            user: المستخدم المكمل

        Returns:
            self: التحويل بعد الإكمال
        """
        # ✅ استخدام validation method
        if not self.can_complete():
            raise ValidationError(_('لا يمكن إكمال هذا التحويل. تحقق من حالته والتسليم والاستلام'))

        # تحديث بيانات الأصل
        asset = self.asset
        asset.branch = self.to_branch

        if self.to_cost_center:
            asset.cost_center = self.to_cost_center

        if self.to_employee:
            asset.responsible_employee = self.to_employee

        asset.save(update_fields=['branch', 'cost_center', 'responsible_employee', 'updated_at'])

        # تحديث حالة التحويل
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])

        return self


# ✅ جديد: نظام الاستئجار
class AssetLease(DocumentBaseModel):
    """عقود استئجار الأصول"""

    LEASE_TYPES = [
        ('operating', _('إيجار تشغيلي')),
        ('finance', _('إيجار تمويلي')),
    ]

    PAYMENT_FREQUENCY_CHOICES = [
        ('monthly', _('شهري')),
        ('quarterly', _('ربع سنوي')),
        ('semi_annual', _('نصف سنوي')),
        ('annual', _('سنوي')),
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

    # دورية الدفع
    payment_frequency = models.CharField(
        _('دورية الدفع'),
        max_length=20,
        choices=PAYMENT_FREQUENCY_CHOICES,
        default='monthly',
        help_text=_('تكرار دفع الأقساط')
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

    # ═══════════════════════════════════════════════════════════════
    # 🔒 Validation Methods - التحقق من الصلاحيات
    # ═══════════════════════════════════════════════════════════════

    def can_edit(self):
        """هل يمكن تعديل عقد الإيجار؟"""
        # لا يمكن تعديل عقد مكتمل أو منهي
        if self.status in ['completed', 'terminated']:
            return False

        # لا يمكن تعديل إذا كانت هناك دفعات مدفوعة
        if self.payments.filter(is_paid=True).exists():
            return False

        return True

    def can_delete(self):
        """هل يمكن حذف عقد الإيجار؟"""
        # لا يمكن حذف عقد نشط أو مكتمل
        if self.status in ['active', 'completed']:
            return False

        # لا يمكن حذف إذا كانت هناك دفعات
        if self.payments.exists():
            return False

        return True

    def can_activate(self):
        """هل يمكن تفعيل عقد الإيجار؟"""
        # يمكن التفعيل فقط من حالة مسودة
        if self.status != 'draft':
            return False

        # يجب أن يكون هناك مبلغ شهري
        if self.monthly_payment <= 0:
            return False

        return True

    def can_terminate(self):
        """هل يمكن إنهاء عقد الإيجار؟"""
        # يمكن الإنهاء من حالة نشط فقط
        if self.status != 'active':
            return False

        return True

    # ═══════════════════════════════════════════════════════════════
    # 💰 Accounting Methods - الطرق المحاسبية
    # ═══════════════════════════════════════════════════════════════

    @transaction.atomic
    def create_journal_entry(self, payment_date=None, payment_amount=None, user=None):
        """إنشاء قيد محاسبي لدفعة الإيجار"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod, Account

        if not payment_date:
            payment_date = timezone.now().date()

        if not payment_amount:
            payment_amount = self.monthly_payment

        # الحصول على السنة المالية والفترة
        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=payment_date,
                end_date__gte=payment_date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError('لا توجد سنة مالية نشطة لتاريخ الدفع')

        period = AccountingPeriod.objects.filter(
            fiscal_year=fiscal_year,
            start_date__lte=payment_date,
            end_date__gte=payment_date,
            is_closed=False
        ).first()

        if not period:
            raise ValidationError('لا توجد فترة محاسبية نشطة لتاريخ الدفع')

        # الحصول على الحسابات المحاسبية
        # للإيجار التشغيلي: مصروف
        # للإيجار التمويلي: التزام طويل الأجل + فائدة
        if self.lease_type == 'operating':
            # مصروف إيجار تشغيلي
            try:
                expense_account = Account.objects.get(
                    company=self.company,
                    code='520100',  # مصاريف إيجار
                    is_active=True
                )
            except Account.DoesNotExist:
                raise ValidationError('لم يتم العثور على حساب مصاريف الإيجار (520100)')
        else:
            # إيجار تمويلي - التزام
            try:
                liability_account = Account.objects.get(
                    company=self.company,
                    code='220100',  # التزامات إيجار تمويلي
                    is_active=True
                )
            except Account.DoesNotExist:
                raise ValidationError('لم يتم العثور على حساب التزامات الإيجار التمويلي (220100)')

            expense_account = liability_account

        # حساب الدفع (نقدية أو موردين)
        try:
            payment_account = Account.objects.get(
                company=self.company,
                code='110100',  # النقدية
                is_active=True
            )
        except Account.DoesNotExist:
            raise ValidationError('لم يتم العثور على حساب النقدية (110100)')

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=payment_date,
            entry_type='lease_payment',
            description=f'دفع إيجار {self.get_lease_type_display()} - {self.asset.name}',
            reference=self.lease_number,
            source_model='asset_lease',
            source_id=self.id,
            status='draft',
            created_by=user
        )

        # السطر 1: مدين - مصروف/التزام
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=expense_account,
            description=f'إيجار {self.asset.name} - {payment_date}',
            debit_amount=payment_amount,
            credit_amount=0,
            currency=self.company.base_currency,
            cost_center=self.asset.cost_center if self.asset.cost_center else None
        )

        # السطر 2: دائن - النقدية
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=payment_account,
            description=f'دفع إيجار - {self.lessor.name}',
            debit_amount=0,
            credit_amount=payment_amount,
            currency=self.company.base_currency
        )

        # حساب الإجماليات
        journal_entry.calculate_totals()

        return journal_entry

    # ═══════════════════════════════════════════════════════════════
    # 💼 Business Methods - طرق العمليات
    # ═══════════════════════════════════════════════════════════════

    @transaction.atomic
    def terminate(self, termination_date=None, reason='', user=None):
        """إنهاء عقد الإيجار"""
        import datetime

        if not self.can_terminate():
            raise ValidationError('لا يمكن إنهاء هذا العقد. يجب أن يكون نشطاً')

        if not termination_date:
            termination_date = datetime.date.today()

        self.status = 'terminated'
        self.notes = f"{self.notes}\n\nتم الإنهاء بتاريخ {termination_date}. السبب: {reason}" if self.notes else f"تم الإنهاء بتاريخ {termination_date}. السبب: {reason}"
        self.save()

        # تحديث حالة الأصل
        if self.asset.status == 'leased':
            self.asset.status = 'active'
            self.asset.save(update_fields=['status'])

        return self


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

    # ═══════════════════════════════════════════════════════════════
    # 🔒 Validation Methods - التحقق من الصلاحيات
    # ═══════════════════════════════════════════════════════════════

    def can_edit(self):
        """هل يمكن تعديل الدفعة؟"""
        # لا يمكن تعديل دفعة مدفوعة
        if self.is_paid:
            return False

        # لا يمكن تعديل إذا كان لها قيد محاسبي
        if self.journal_entry:
            return False

        # لا يمكن تعديل إذا كان العقد منهي أو مكتمل
        if self.lease.status in ['terminated', 'completed']:
            return False

        return True

    def can_delete(self):
        """هل يمكن حذف الدفعة؟"""
        # لا يمكن حذف دفعة مدفوعة
        if self.is_paid:
            return False

        # لا يمكن حذف إذا كان لها قيد محاسبي
        if self.journal_entry:
            return False

        return True

    def can_pay(self):
        """هل يمكن دفع الدفعة؟"""
        # لا يمكن الدفع إذا كانت مدفوعة مسبقاً
        if self.is_paid:
            return False

        # لا يمكن الدفع إذا كان العقد غير نشط
        if self.lease.status != 'active':
            return False

        # يجب أن يكون المبلغ أكبر من صفر
        if self.amount <= 0:
            return False

        return True

    # ═══════════════════════════════════════════════════════════════
    # 💰 Accounting Methods - الطرق المحاسبية
    # ═══════════════════════════════════════════════════════════════

    @transaction.atomic
    def process_payment(self, user=None):
        """معالجة دفعة الإيجار مع القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod
        from ..accounting_config import AssetAccountingConfiguration

        # ✅ استخدام validation method
        if not self.can_pay():
            raise ValidationError(_('لا يمكن دفع هذه الدفعة. تحقق من حالتها وحالة العقد'))

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
# apps/assets/models/transaction_models.py
"""
نماذج العمليات على الأصول
- العمليات العامة (شراء، بيع، استبعاد، إلخ)
- التحويلات بين الفروع والأقسام
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import DocumentBaseModel, BusinessPartner


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
            if not self.counterpart_account:
                raise ValidationError({
                    'counterpart_account': _('يجب تحديد العميل')
                })

        if self.transaction_type == 'purchase':
            if not self.counterpart_account:
                raise ValidationError({
                    'counterpart_account': _('يجب تحديد المورد')
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
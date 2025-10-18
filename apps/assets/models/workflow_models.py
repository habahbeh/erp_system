# apps/assets/models/workflow_models.py
"""
نماذج سير العمل والموافقات
- تعريف سير العمل
- مستويات الموافقة
- طلبات الموافقة
- سجل الموافقات
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel, DocumentBaseModel
from decimal import Decimal


class ApprovalWorkflow(BaseModel):
    """تعريف سير عمل الموافقات"""

    DOCUMENT_TYPES = [
        ('asset_transaction', _('عملية أصل')),
        ('asset_maintenance', _('صيانة')),
        ('asset_transfer', _('تحويل')),
        ('physical_count_adjustment', _('تسوية جرد')),
        ('insurance_claim', _('مطالبة تأمين')),
        ('asset_lease', _('عقد إيجار')),
    ]

    name = models.CharField(_('اسم سير العمل'), max_length=200)
    code = models.CharField(_('الرمز'), max_length=50)
    document_type = models.CharField(
        _('نوع المستند'),
        max_length=50,
        choices=DOCUMENT_TYPES
    )

    description = models.TextField(_('الوصف'), blank=True)
    is_active = models.BooleanField(_('نشط'), default=True)

    # هل يُطلب تسلسلياً أم متوازياً
    is_sequential = models.BooleanField(
        _('تسلسلي'),
        default=True,
        help_text=_('إذا كان نعم: موافقة تلو الأخرى، لا: كل المستويات معاً')
    )

    class Meta:
        verbose_name = _('سير عمل موافقات')
        verbose_name_plural = _('سير عمل الموافقات')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ApprovalLevel(models.Model):
    """مستوى الموافقة"""

    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='levels',
        verbose_name=_('سير العمل')
    )

    level_order = models.IntegerField(
        _('ترتيب المستوى'),
        validators=[MinValueValidator(1)],
        help_text=_('1 = المستوى الأول، 2 = الثاني، إلخ')
    )

    name = models.CharField(_('اسم المستوى'), max_length=100)

    # المعتمد
    approver_role = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        related_name='approval_levels',
        verbose_name=_('دور المعتمد'),
        help_text=_('المجموعة التي يمكنها الاعتماد')
    )

    # شروط المبلغ
    amount_from = models.DecimalField(
        _('المبلغ من'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('اتركه فارغاً لعدم التقييد')
    )
    amount_to = models.DecimalField(
        _('المبلغ إلى'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('اتركه فارغاً لعدم التقييد')
    )

    # هل إجباري
    is_required = models.BooleanField(_('إجباري'), default=True)

    # وقت الاستجابة المتوقع (ساعات)
    expected_response_hours = models.IntegerField(
        _('وقت الاستجابة المتوقع (ساعات)'),
        default=24,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = _('مستوى موافقة')
        verbose_name_plural = _('مستويات الموافقات')
        ordering = ['workflow', 'level_order']
        unique_together = [['workflow', 'level_order']]

    def __str__(self):
        return f"{self.workflow.name} - المستوى {self.level_order}: {self.name}"

    def can_approve_amount(self, amount):
        """هل يمكن اعتماد هذا المبلغ في هذا المستوى"""
        if self.amount_from is None and self.amount_to is None:
            return True

        if self.amount_from and amount < self.amount_from:
            return False

        if self.amount_to and amount > self.amount_to:
            return False

        return True


class ApprovalRequest(DocumentBaseModel):
    """طلب موافقة"""

    STATUS_CHOICES = [
        ('pending', _('معلق')),
        ('in_progress', _('قيد المراجعة')),
        ('approved', _('معتمد')),
        ('rejected', _('مرفوض')),
        ('cancelled', _('ملغي')),
    ]

    request_number = models.CharField(
        _('رقم الطلب'),
        max_length=50,
        editable=False,
        unique=True
    )

    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.PROTECT,
        related_name='approval_requests',
        verbose_name=_('سير العمل')
    )

    # الكائن المرتبط
    document_type = models.CharField(_('نوع المستند'), max_length=50)
    document_id = models.PositiveIntegerField(_('معرف المستند'))

    # المبلغ (إن وجد)
    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    current_level = models.ForeignKey(
        ApprovalLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_requests',
        verbose_name=_('المستوى الحالي')
    )

    # الطالب
    requested_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_requests',
        verbose_name=_('طلب بواسطة')
    )
    requested_date = models.DateTimeField(_('تاريخ الطلب'), auto_now_add=True)

    # الإكمال
    completed_date = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)

    description = models.TextField(_('الوصف'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('طلب موافقة')
        verbose_name_plural = _('طلبات الموافقات')
        ordering = ['-requested_date']

    def save(self, *args, **kwargs):
        # توليد رقم الطلب
        if not self.request_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='approval_request'
                )
                self.request_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='approval_request',
                    prefix='APR',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.request_number = sequence.get_next_number()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_number} - {self.workflow.name}"

    @transaction.atomic
    def start_approval_process(self):
        """بدء عملية الموافقة"""
        if self.status != 'pending':
            raise ValidationError(_('الطلب ليس في حالة معلق'))

        # الحصول على المستوى الأول
        first_level = self.workflow.levels.filter(
            is_required=True
        ).order_by('level_order').first()

        if not first_level:
            # لا توجد مستويات - اعتماد مباشر
            self.status = 'approved'
            self.completed_date = models.timezone.now()
            self.save()
            return True

        # التحقق من المبلغ
        if self.amount and not first_level.can_approve_amount(self.amount):
            # البحث عن مستوى مناسب
            first_level = self.workflow.levels.filter(
                is_required=True,
                amount_from__lte=self.amount
            ).order_by('level_order').first()

        if not first_level:
            raise ValidationError(_('لا يوجد مستوى موافقة مناسب لهذا المبلغ'))

        self.current_level = first_level
        self.status = 'in_progress'
        self.save()

        # إنشاء سجل الموافقة
        ApprovalHistory.objects.create(
            approval_request=self,
            level=first_level,
            action='created',
            notes='بدء عملية الموافقة'
        )

        return True

    @transaction.atomic
    def approve_current_level(self, user, comments=''):
        """اعتماد المستوى الحالي"""
        from django.utils import timezone

        if self.status not in ['pending', 'in_progress']:
            raise ValidationError(_('الطلب ليس في حالة تسمح بالاعتماد'))

        if not self.current_level:
            raise ValidationError(_('لا يوجد مستوى حالي'))

        # التحقق من صلاحية المستخدم
        if not user.groups.filter(id=self.current_level.approver_role.id).exists():
            raise ValidationError(_('ليس لديك صلاحية الاعتماد في هذا المستوى'))

        # تسجيل الموافقة
        ApprovalHistory.objects.create(
            approval_request=self,
            level=self.current_level,
            approver=user,
            action='approved',
            action_date=timezone.now(),
            comments=comments
        )

        # الانتقال للمستوى التالي
        next_level = self.workflow.levels.filter(
            level_order__gt=self.current_level.level_order,
            is_required=True
        ).order_by('level_order').first()

        if next_level:
            # التحقق من المبلغ
            if self.amount and not next_level.can_approve_amount(self.amount):
                next_level = self.workflow.levels.filter(
                    level_order__gt=self.current_level.level_order,
                    is_required=True,
                    amount_from__lte=self.amount
                ).order_by('level_order').first()

        if next_level:
            # يوجد مستوى تالي
            self.current_level = next_level
            self.save()
        else:
            # لا يوجد مستوى تالي - اعتماد نهائي
            self.status = 'approved'
            self.current_level = None
            self.completed_date = timezone.now()
            self.save()

    @transaction.atomic
    def reject(self, user, reason):
        """رفض الطلب"""
        from django.utils import timezone

        if self.status not in ['pending', 'in_progress']:
            raise ValidationError(_('الطلب ليس في حالة تسمح بالرفض'))

        # تسجيل الرفض
        ApprovalHistory.objects.create(
            approval_request=self,
            level=self.current_level,
            approver=user,
            action='rejected',
            action_date=timezone.now(),
            comments=reason
        )

        self.status = 'rejected'
        self.completed_date = timezone.now()
        self.save()


class ApprovalHistory(models.Model):
    """سجل الموافقات"""

    ACTION_CHOICES = [
        ('created', _('تم الإنشاء')),
        ('approved', _('معتمد')),
        ('rejected', _('مرفوض')),
        ('cancelled', _('ملغي')),
    ]

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('طلب الموافقة')
    )

    level = models.ForeignKey(
        ApprovalLevel,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('المستوى')
    )

    approver = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_actions',
        verbose_name=_('المعتمد')
    )

    action = models.CharField(_('الإجراء'), max_length=20, choices=ACTION_CHOICES)
    action_date = models.DateTimeField(_('تاريخ الإجراء'), auto_now_add=True)

    comments = models.TextField(_('التعليقات'), blank=True)

    class Meta:
        verbose_name = _('سجل موافقة')
        verbose_name_plural = _('سجل الموافقات')
        ordering = ['-action_date']

    def __str__(self):
        return f"{self.approval_request.request_number} - {self.get_action_display()}"
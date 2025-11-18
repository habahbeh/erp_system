# apps/core/models/template_models.py
"""
نماذج القوالب والاستيراد الجماعي - NEW
- ItemTemplate: قوالب المواد للاستخدام المتكرر
- BulkImportJob: سجل عمليات الاستيراد الجماعي
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base_models import BaseModel


class ItemTemplate(BaseModel):
    """
    قوالب المواد - NEW

    تسمح بحفظ تكوين مادة كاملة (مع متغيرات + UoM + أسعار)
    لإعادة استخدامها في إنشاء مواد مشابهة بسرعة

    مثال: قالب "مسامير" يحتوي على:
    - المتغيرات: أحجام مختلفة
    - وحدات القياس: قطعة، دزينة، كرتون
    - قوائم أسعار: جملة، تجزئة، VIP
    """

    name = models.CharField(
        _('اسم القالب'),
        max_length=200,
        help_text=_('اسم وصفي للقالب، مثل "قالب مسامير"')
    )

    code = models.CharField(
        _('رمز القالب'),
        max_length=50
    )

    description = models.TextField(
        _('الوصف'),
        blank=True,
        help_text=_('وصف تفصيلي للقالب واستخداماته')
    )

    # التصنيف الذي ينطبق عليه القالب
    category = models.ForeignKey(
        'ItemCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates',
        verbose_name=_('التصنيف')
    )

    # بيانات القالب (JSON)
    template_data = models.JSONField(
        _('بيانات القالب'),
        default=dict,
        help_text=_('البنية الكاملة للمادة بصيغة JSON')
    )

    # البنية:
    # {
    #     "base_item": {
    #         "unit_of_measure_code": "PCS",
    #         "currency_code": "JOD",
    #         "tax_rate": 16.0
    #     },
    #     "variant_attributes": [
    #         {
    #             "name": "الحجم",
    #             "values": ["5 سم", "10 سم", "15 سم"]
    #         }
    #     ],
    #     "uom_conversions": [
    #         {"from_uom": "DOZEN", "factor": 12},
    #         {"from_uom": "CARTON", "factor": 100}
    #     ],
    #     "price_structure": {
    #         "wholesale": {"multiplier": 1.3},
    #         "retail": {"multiplier": 1.5},
    #         "vip": {"multiplier": 1.2}
    #     }
    # }

    # إعدادات إضافية
    auto_generate_codes = models.BooleanField(
        _('توليد الرموز تلقائياً'),
        default=True,
        help_text=_('توليد رموز المواد والمتغيرات تلقائياً')
    )

    auto_create_prices = models.BooleanField(
        _('إنشاء الأسعار تلقائياً'),
        default=True,
        help_text=_('إنشاء أسعار حسب قواعد التسعير المحددة')
    )

    # إحصائيات الاستخدام
    usage_count = models.IntegerField(
        _('عدد مرات الاستخدام'),
        default=0,
        help_text=_('عدد المواد التي تم إنشاؤها من هذا القالب')
    )

    last_used_at = models.DateTimeField(
        _('آخر استخدام'),
        null=True,
        blank=True
    )

    # ملاحظات
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('قالب مادة')
        verbose_name_plural = _('قوالب المواد')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def increment_usage(self):
        """زيادة عداد الاستخدام"""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])

    def create_item_from_template(self, item_data):
        """
        إنشاء مادة جديدة من القالب

        Args:
            item_data: بيانات إضافية خاصة بالمادة (الاسم، الكود، إلخ)

        Returns:
            Item: المادة المنشأة
        """
        # سيتم تنفيذ هذه الدالة في Week 4 (User Interface)
        pass


class BulkImportJob(BaseModel):
    """
    سجل عمليات الاستيراد الجماعي - NEW

    يتتبع جميع عمليات استيراد المواد من Excel
    مع تفاصيل النجاح/الفشل والأخطاء
    """

    JOB_STATUS_CHOICES = [
        ('PENDING', _('قيد الانتظار')),
        ('PROCESSING', _('جاري المعالجة')),
        ('COMPLETED', _('مكتمل')),
        ('COMPLETED_WITH_ERRORS', _('مكتمل مع أخطاء')),
        ('FAILED', _('فشل')),
        ('CANCELLED', _('ملغي')),
    ]

    job_id = models.CharField(
        _('معرف العملية'),
        max_length=50,
        unique=True,
        editable=False,
        help_text=_('معرف فريد للعملية')
    )

    file_name = models.CharField(
        _('اسم الملف'),
        max_length=255
    )

    file_path = models.FileField(
        _('ملف الاستيراد'),
        upload_to='imports/%Y/%m/',
        help_text=_('ملف Excel المستورد')
    )

    status = models.CharField(
        _('الحالة'),
        max_length=30,
        choices=JOB_STATUS_CHOICES,
        default='PENDING'
    )

    # الإحصائيات
    total_rows = models.IntegerField(
        _('إجمالي السطور'),
        default=0
    )

    processed_rows = models.IntegerField(
        _('السطور المعالجة'),
        default=0
    )

    successful_rows = models.IntegerField(
        _('السطور الناجحة'),
        default=0
    )

    failed_rows = models.IntegerField(
        _('السطور الفاشلة'),
        default=0
    )

    # الأخطاء والتحذيرات
    errors = models.JSONField(
        _('الأخطاء'),
        default=list,
        blank=True,
        help_text=_('قائمة بجميع الأخطاء حسب رقم السطر')
    )
    # البنية:
    # [
    #     {"row": 5, "error": "رمز المادة مكرر", "field": "code"},
    #     {"row": 12, "error": "سعر غير صحيح", "field": "price"}
    # ]

    warnings = models.JSONField(
        _('التحذيرات'),
        default=list,
        blank=True
    )

    # معلومات الإنشاء
    import_type = models.CharField(
        _('نوع الاستيراد'),
        max_length=50,
        choices=[
            ('NEW_ITEMS', _('مواد جديدة')),
            ('UPDATE_PRICES', _('تحديث أسعار')),
            ('UPDATE_STOCK', _('تحديث مخزون')),
            ('FULL_UPDATE', _('تحديث كامل')),
        ],
        default='NEW_ITEMS'
    )

    # التوقيت
    started_at = models.DateTimeField(
        _('بدأ في'),
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        _('انتهى في'),
        null=True,
        blank=True
    )

    duration_seconds = models.IntegerField(
        _('المدة (ثوان)'),
        null=True,
        blank=True
    )

    # ملاحظات
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عملية استيراد جماعي')
        verbose_name_plural = _('عمليات الاستيراد الجماعي')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['company', '-created_at']),
        ]

    def __str__(self):
        return f"{self.job_id} - {self.file_name}"

    def save(self, *args, **kwargs):
        """توليد job_id تلقائياً"""
        if not self.job_id:
            import uuid
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            self.job_id = f"IMP-{timestamp}-{unique_id}"

        super().save(*args, **kwargs)

    def mark_as_processing(self):
        """تعيين الحالة كـ "جاري المعالجة" """
        from django.utils import timezone
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_as_completed(self):
        """تعيين الحالة كـ "مكتمل" """
        from django.utils import timezone
        self.completed_at = timezone.now()

        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())

        if self.failed_rows > 0:
            self.status = 'COMPLETED_WITH_ERRORS'
        else:
            self.status = 'COMPLETED'

        self.save(update_fields=['status', 'completed_at', 'duration_seconds'])

    def mark_as_failed(self, error_message):
        """تعيين الحالة كـ "فشل" """
        from django.utils import timezone
        self.status = 'FAILED'
        self.completed_at = timezone.now()

        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())

        # إضافة رسالة الخطأ الرئيسية
        self.errors.append({
            "row": 0,
            "error": error_message,
            "field": "general"
        })

        self.save()

    def add_error(self, row_number, error_message, field_name=None):
        """إضافة خطأ لسطر معين"""
        error_entry = {
            "row": row_number,
            "error": error_message
        }
        if field_name:
            error_entry["field"] = field_name

        if not isinstance(self.errors, list):
            self.errors = []

        self.errors.append(error_entry)
        self.failed_rows += 1
        self.save(update_fields=['errors', 'failed_rows'])

    def add_warning(self, row_number, warning_message):
        """إضافة تحذير لسطر معين"""
        warning_entry = {
            "row": row_number,
            "warning": warning_message
        }

        if not isinstance(self.warnings, list):
            self.warnings = []

        self.warnings.append(warning_entry)
        self.save(update_fields=['warnings'])

    def get_success_rate(self):
        """حساب نسبة النجاح"""
        if self.total_rows == 0:
            return 0
        return (self.successful_rows / self.total_rows) * 100

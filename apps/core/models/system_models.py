# apps/core/models/system_models.py
"""
نماذج النظام - System Models
- NumberingSequence: تسلسلات الترقيم التلقائي
- SystemSettings: إعدادات النظام
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base_models import BaseModel


class NumberingSequence(BaseModel):
    """تسلسل الترقيم التلقائي للمستندات"""

    DOCUMENT_TYPES = [
        # المبيعات
        ('sales_invoice', _('فاتورة مبيعات')),
        ('sales_return', _('مرتجع مبيعات')),
        ('sales_quotation', _('عرض سعر')),
        ('sales_order', _('أمر بيع')),
        # المشتريات
        ('purchase_invoice', _('فاتورة مشتريات')),
        ('purchase_return', _('مرتجع مشتريات')),
        ('purchase_order', _('أمر شراء')),
        ('purchase_request', _('طلب شراء')),
        # المخازن
        ('stock_in', _('سند إدخال')),
        ('stock_out', _('سند إخراج')),
        ('stock_transfer', _('سند تحويل')),
        ('stock_count', _('جرد')),
        # المحاسبة
        ('journal_entry', _('قيد يومية')),
        ('payment_voucher', _('سند صرف')),
        ('receipt_voucher', _('سند قبض')),
        # الأصول
        ('asset', _('أصل ثابت')),
        ('asset_transaction', _('عملية على أصل')),
        ('asset_maintenance', _('صيانة أصل')),
    ]

    document_type = models.CharField(_('نوع المستند'), max_length=50, choices=DOCUMENT_TYPES)
    prefix = models.CharField(_('البادئة'), max_length=20, help_text=_('مثال: INV, PO, JV'))
    suffix = models.CharField(_('اللاحقة'), max_length=20, blank=True)
    next_number = models.IntegerField(_('الرقم التالي'), default=1)
    padding = models.IntegerField(_('عدد الأصفار'), default=6, help_text=_('مثال: 6 = 000001'))
    yearly_reset = models.BooleanField(_('إعادة ترقيم سنوياً'), default=True)
    include_year = models.BooleanField(_('تضمين السنة'), default=True)
    include_month = models.BooleanField(_('تضمين الشهر'), default=False)
    separator = models.CharField(_('الفاصل'), max_length=1, default='/', help_text=_('مثال: / أو -'))

    last_reset_year = models.IntegerField(
        _('آخر سنة إعادة ترقيم'),
        null=True,
        blank=True,
        help_text=_('لتتبع السنة الأخيرة التي تم فيها إعادة الترقيم')
    )

    class Meta:
        verbose_name = _('تسلسل ترقيم')
        verbose_name_plural = _('تسلسلات الترقيم')
        unique_together = [['company', 'document_type']]

    def get_next_number(self):
        """الحصول على الرقم التالي مع دعم الترقيم السنوي - مع قفل للمنع من التكرار"""
        import datetime
        from django.db import transaction

        current_year = datetime.date.today().year
        current_month = datetime.date.today().month

        # استخدام select_for_update لمنع التداخل في الأرقام
        with transaction.atomic():
            # إعادة قراءة السجل مع قفل
            sequence = NumberingSequence.objects.select_for_update().get(pk=self.pk)

            # التحقق من إعادة الترقيم السنوي
            if sequence.yearly_reset and sequence.include_year:
                # إذا تغيرت السنة، أعد الترقيم
                if sequence.last_reset_year != current_year:
                    sequence.next_number = 1
                    sequence.last_reset_year = current_year

            # بناء الرقم
            parts = []

            if sequence.prefix:
                parts.append(sequence.prefix)

            if sequence.include_year:
                parts.append(str(current_year))

            if sequence.include_month:
                parts.append(f"{current_month:02d}")

            parts.append(str(sequence.next_number).zfill(sequence.padding))

            if sequence.suffix:
                parts.append(sequence.suffix)

            number = sequence.separator.join(parts)

            # زيادة العداد
            sequence.next_number += 1
            sequence.save()

        return number

    def get_preview_number(self):
        """الحصول على معاينة للرقم التالي بدون تغيير العداد"""
        import datetime

        current_year = datetime.date.today().year
        current_month = datetime.date.today().month

        parts = []

        if self.prefix:
            parts.append(self.prefix)

        if self.include_year:
            parts.append(str(current_year))

        if self.include_month:
            parts.append(f"{current_month:02d}")

        # استخدم next_number المتوقع
        expected_number = self.next_number

        # إذا كان سيتم إعادة الترقيم، استخدم 1
        if self.yearly_reset and self.include_year:
            if self.last_reset_year != current_year:
                expected_number = 1

        parts.append(str(expected_number).zfill(self.padding))

        if self.suffix:
            parts.append(self.suffix)

        return self.separator.join(parts)

    def reset_sequence(self, start_number=1):
        """إعادة ترقيم التسلسل يدوياً"""
        import datetime
        self.next_number = start_number
        self.last_reset_year = datetime.date.today().year
        self.save()

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.prefix}"


class SystemSettings(models.Model):
    """إعدادات النظام"""

    company = models.OneToOneField('Company', on_delete=models.CASCADE, verbose_name=_('الشركة'), related_name='settings')
    negative_stock_allowed = models.BooleanField(_('السماح بالرصيد السالب'), default=False)
    stock_valuation_method = models.CharField(_('طريقة تقييم المخزون'), max_length=20,
                                              choices=[('fifo', _('الوارد أولاً صادر أولاً')),
                                                       ('lifo', _('الوارد أخيراً صادر أولاً')),
                                                       ('average', _('متوسط التكلفة'))], default='average')
    customer_credit_check = models.BooleanField(_('فحص حد ائتمان العملاء'), default=True)
    credit_restore_on_check_date = models.BooleanField(
        _('استرجاع الائتمان عند تاريخ صرف الشيك'),
        default=False,
        help_text=_('إذا كان نعم، يتم استرجاع ائتمان العميل عند تاريخ صرف الشيك وليس عند إدخال سند القبض')
    )
    auto_create_journal_entries = models.BooleanField(_('إنشاء قيود تلقائياً'), default=True)
    session_timeout = models.IntegerField(_('مهلة انتهاء الجلسة (دقائق)'), default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('إعدادات النظام')
        verbose_name_plural = _('إعدادات النظام')

    def __str__(self):
        return f"إعدادات {self.company.name}"

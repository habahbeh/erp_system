# apps/accounting/models/fiscal_models.py
"""
نماذج السنوات والفترات المالية
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class FiscalYear(BaseModel):
    """السنة المالية"""

    name = models.CharField(_('اسم السنة المالية'), max_length=100)
    code = models.CharField(_('الرمز'), max_length=20)
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    is_closed = models.BooleanField(_('مقفلة'), default=False)

    class Meta:
        verbose_name = _('سنة مالية')
        verbose_name_plural = _('السنوات المالية')
        unique_together = [['company', 'code']]
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class AccountingPeriod(BaseModel):
    """الفترة المحاسبية"""

    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE,
                                   related_name='periods', verbose_name=_('السنة المالية'))
    name = models.CharField(_('اسم الفترة'), max_length=50)
    start_date = models.DateField(_('تاريخ البداية'))
    end_date = models.DateField(_('تاريخ النهاية'))
    is_closed = models.BooleanField(_('مقفلة'), default=False)
    is_adjustment = models.BooleanField(_('فترة تسويات'), default=False)

    class Meta:
        verbose_name = _('فترة محاسبية')
        verbose_name_plural = _('الفترات المحاسبية')
        ordering = ['start_date']

    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"

# apps/core/models/base_models.py
"""
النماذج الأساسية - Base Models
- BaseModel: النموذج الأساسي لجميع الكيانات
- DocumentBaseModel: النموذج الأساسي للمستندات
- Currency: العملات
- PaymentMethod: طرق الدفع
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class BaseModel(models.Model):
    """النموذج الأساسي الموحد - للبيانات الأساسية"""

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, verbose_name=_('الشركة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التعديل'))
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created',
                                   verbose_name=_('أنشأ بواسطة'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))

    class Meta:
        abstract = True


class DocumentBaseModel(BaseModel):
    """النموذج الأساسي للمستندات والفواتير - يحتاج فرع"""

    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, verbose_name=_('الفرع'))

    class Meta:
        abstract = True


class Currency(models.Model):
    """العملات - نموذج مستقل"""

    code = models.CharField(_('رمز العملة'), max_length=3, unique=True)
    name = models.CharField(_('اسم العملة'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100)
    symbol = models.CharField(_('رمز العملة'), max_length=10)
    exchange_rate = models.DecimalField(_('سعر الصرف'), max_digits=10, decimal_places=4, default=1.0000)
    is_base = models.BooleanField(_('العملة الأساسية'), default=False)
    is_active = models.BooleanField(_('نشطة'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('عملة')
        verbose_name_plural = _('العملات')

    def save(self, *args, **kwargs):
        if self.is_base:
            Currency.objects.filter(is_base=True).exclude(pk=self.pk).update(is_base=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class PaymentMethod(BaseModel):
    """طرق الدفع"""

    code = models.CharField(_('الرمز'), max_length=20)
    name = models.CharField(_('الاسم'), max_length=50)
    is_cash = models.BooleanField(_('نقدي'), default=True)

    class Meta:
        verbose_name = _('طريقة دفع')
        verbose_name_plural = _('طرق الدفع')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name

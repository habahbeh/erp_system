# apps/accounting/models/account_models.py
"""
نماذج الحسابات ودليل الحسابات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


class AccountType(models.Model):
    """أنواع الحسابات الرئيسية"""

    ACCOUNT_TYPES = [
        ('assets', _('الأصول')),
        ('liabilities', _('الخصوم')),
        ('equity', _('حقوق الملكية')),
        ('revenue', _('الإيرادات')),
        ('expenses', _('المصروفات')),
    ]

    code = models.CharField(_('الرمز'), max_length=20, unique=True)
    name = models.CharField(_('الاسم'), max_length=50)
    type_category = models.CharField(_('التصنيف'), max_length=20, choices=ACCOUNT_TYPES)
    normal_balance = models.CharField(
        _('الرصيد الطبيعي'),
        max_length=10,
        choices=[('debit', _('مدين')), ('credit', _('دائن'))]
    )

    class Meta:
        verbose_name = _('نوع حساب')
        verbose_name_plural = _('أنواع الحسابات')

    def __str__(self):
        return self.name


class Account(BaseModel):
    """دليل الحسابات"""

    ACCOUNT_NATURE = [
        ('debit', _('مدين')),
        ('credit', _('دائن')),
        ('both', _('كلاهما')),
    ]

    # معلومات أساسية
    code = models.CharField(_('رمز الحساب'), max_length=20)
    name = models.CharField(_('اسم الحساب'), max_length=200)
    name_en = models.CharField(_('الاسم اللاتيني'), max_length=200, blank=True)

    # التصنيف والتسلسل
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, verbose_name=_('نوع الحساب'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children', verbose_name=_('الحساب الأب'))

    # الإعدادات
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, verbose_name=_('العملة الافتراضية'))
    nature = models.CharField(_('جهة الحساب'), max_length=10, choices=ACCOUNT_NATURE, default='both')

    # معلومات إضافية
    notes = models.TextField(_('ملاحظات'), blank=True)

    # الحالة
    is_suspended = models.BooleanField(_('موقوف'), default=False)

    # خصائص الحساب
    is_cash_account = models.BooleanField(_('حساب نقدي'), default=False)
    is_bank_account = models.BooleanField(_('حساب بنكي'), default=False)
    accept_entries = models.BooleanField(_('يقبل القيود'), default=True)

    # المستوى (محسوب تلقائياً)
    level = models.IntegerField(_('المستوى'), default=1, editable=False)

    # الرصيد الافتتاحي
    opening_balance = models.DecimalField(_('الرصيد الافتتاحي'), max_digits=15, decimal_places=3, default=0)
    opening_balance_date = models.DateField(_('تاريخ الرصيد الافتتاحي'), null=True, blank=True)

    # إضافات
    can_have_children = models.BooleanField(_('يمكن أن يحتوي على حسابات فرعية'), default=True)
    is_system_account = models.BooleanField(_('حساب نظام'), default=False)

    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('دليل الحسابات')
        unique_together = [['company', 'code']]
        ordering = ['code']

    def get_full_name(self):
        if self.parent:
            return f"{self.parent.get_full_name()} / {self.name}"
        return self.name

    def get_balance(self, date=None):
        return self.opening_balance

    def clean(self):
        # التحقق من عمق الهيكل الهرمي فقط
        if self.parent:
            level = 1
            current_parent = self.parent
            while current_parent:
                level += 1
                if level > 4:
                    raise ValidationError(_('لا يمكن تجاوز 4 مستويات في الهيكل الهرمي'))
                current_parent = current_parent.parent

        return super().clean()

    def save(self, *args, **kwargs):
        # حساب المستوى
        if self.parent:
            self.level = self.parent.level + 1
            if not self.account_type_id:
                self.account_type = self.parent.account_type
        else:
            self.level = 1

        super().save(*args, **kwargs)

        # بعد الحفظ، تحقق من أن الأطفال لا يملكون آباء يقبلون قيود
        if self.children.exists() and self.accept_entries:
            self.accept_entries = False
            super().save(update_fields=['accept_entries'])

    def can_accept_entries(self):
        """تحقق مما إذا كان الحساب يمكنه قبول قيود"""
        return not self.children.exists()

    def get_children_count(self):
        """عدد الحسابات الفرعية"""
        if not self.pk:
            return 0
        return self.children.count()

    def __str__(self):
        return f"{self.code} - {self.name}"


class CostCenter(BaseModel):
    """مراكز التكلفة"""

    code = models.CharField(_('الرمز'), max_length=20)
    name = models.CharField(_('الاسم'), max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children', verbose_name=_('المركز الأب'))
    manager = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name=_('المسؤول'))

    class Meta:
        verbose_name = _('مركز تكلفة')
        verbose_name_plural = _('مراكز التكلفة')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"
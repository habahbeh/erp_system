"""
نماذج تطبيق النواة
يحتوي على المستخدمين والصلاحيات وسجل العمليات
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """نموذج المستخدم المخصص"""

    # معلومات إضافية
    phone = models.CharField(
        _('رقم الهاتف'),
        max_length=20,
        blank=True
    )

    employee_id = models.CharField(
        _('رقم الموظف'),
        max_length=20,
        blank=True,
        unique=True,
        null=True
    )

    # الشركة والفرع
    company = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        verbose_name=_('الشركة'),
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        'Branch',
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    # حدود الصلاحيات
    max_discount_percentage = models.DecimalField(
        _('نسبة الخصم المسموحة'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_approve_discount(self, discount_percentage):
        """هل يستطيع الموافقة على هذا الخصم؟"""
        if self.is_superuser:
            return True
        if hasattr(self, 'profile'):
            return discount_percentage <= self.profile.max_discount_percentage
        return discount_percentage <= 15.0

    def can_access_branch(self, branch):
        """هل يستطيع الوصول لهذا الفرع؟"""
        if self.is_superuser:
            return True
        if hasattr(self, 'profile'):
            allowed = self.profile.allowed_branches.all()
            if not allowed.exists():  # فارغ = كل الفروع
                return True
            return branch in allowed
        return branch == self.branch

    def get_allowed_branches(self):
        """الحصول على الفروع المسموحة"""
        if self.is_superuser:
            return Branch.objects.all()
        if hasattr(self, 'profile'):
            allowed = self.profile.allowed_branches.all()
            if allowed.exists():
                return allowed
        # فقط فرع المستخدم
        if self.branch:
            return Branch.objects.filter(id=self.branch.id)
        return Branch.objects.none()

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.get_full_name() or self.username


class Company(models.Model):
    """نموذج الشركة"""

    name = models.CharField(_('اسم الشركة'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200)

    # معلومات قانونية
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, unique=True)
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)

    # معلومات الاتصال
    phone = models.CharField(_('الهاتف'), max_length=20)
    email = models.EmailField(_('البريد الإلكتروني'))
    address = models.TextField(_('العنوان'))

    # الشعار
    logo = models.ImageField(_('الشعار'), upload_to='company_logos/', blank=True)

    is_active = models.BooleanField(_('نشطة'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('شركة')
        verbose_name_plural = _('الشركات')

    def __str__(self):
        return self.name


class Branch(models.Model):
    """نموذج الفرع"""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_('الشركة')
    )

    code = models.CharField(_('رمز الفرع'), max_length=10, unique=True)
    name = models.CharField(_('اسم الفرع'), max_length=100)

    # معلومات الاتصال
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    address = models.TextField(_('العنوان'), blank=True)

    is_main = models.BooleanField(_('الفرع الرئيسي'), default=False)
    is_active = models.BooleanField(_('نشط'), default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('فرع')
        verbose_name_plural = _('الفروع')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class AuditLog(models.Model):
    """سجل العمليات"""

    ACTION_CHOICES = [
        ('CREATE', 'إنشاء'),
        ('UPDATE', 'تعديل'),
        ('DELETE', 'حذف'),
        ('VIEW', 'عرض'),
    ]

    # معلومات المستخدم
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('المستخدم')
    )

    # معلومات العملية
    action = models.CharField(
        _('العملية'),
        max_length=10,
        choices=ACTION_CHOICES
    )

    model_name = models.CharField(_('النموذج'), max_length=100)
    object_id = models.PositiveIntegerField(_('معرف السجل'))
    object_repr = models.CharField(_('وصف السجل'), max_length=200)

    # البيانات
    old_values = models.JSONField(_('القيم القديمة'), blank=True, null=True)
    new_values = models.JSONField(_('القيم الجديدة'), blank=True, null=True)

    # معلومات إضافية
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)
    user_agent = models.TextField(_('المتصفح'), blank=True)

    timestamp = models.DateTimeField(_('التوقيت'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل عملية')
        verbose_name_plural = _('سجل العمليات')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr}"


# بعد class AuditLog أضف:

class UserProfile(models.Model):
    """إعدادات إضافية للمستخدم"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # حدود الصلاحيات
    max_discount_percentage = models.DecimalField(
        _('نسبة الخصم المسموحة'),
        max_digits=5,
        decimal_places=2,
        default=15.0
    )

    max_credit_limit = models.DecimalField(
        _('حد الائتمان المسموح'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # قيود الفروع
    allowed_branches = models.ManyToManyField(
        'Branch',
        verbose_name=_('الفروع المسموحة'),
        blank=True,
        help_text=_('فارغ = كل الفروع')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ملف المستخدم')
        verbose_name_plural = _('ملفات المستخدمين')

    def __str__(self):
        return f"ملف {self.user.username}"
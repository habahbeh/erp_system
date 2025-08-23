# apps/core/models.py
"""
نماذج تطبيق النواة
يحتوي على: الشركات، الفروع، المستخدمين، الصلاحيات، الإعدادات، سجل العمليات
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Company(models.Model):
    """نموذج الشركة"""

    # معلومات أساسية
    name = models.CharField(
        _('اسم الشركة'),
        max_length=200
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=200
    )

    # معلومات قانونية
    tax_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=50,
        unique=True
    )

    commercial_register = models.CharField(
        _('السجل التجاري'),
        max_length=50,
        blank=True
    )

    # معلومات الاتصال
    phone = models.CharField(
        _('الهاتف'),
        max_length=20
    )

    fax = models.CharField(
        _('الفاكس'),
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        _('البريد الإلكتروني')
    )

    website = models.URLField(
        _('الموقع الإلكتروني'),
        blank=True
    )

    address = models.TextField(
        _('العنوان')
    )

    city = models.CharField(
        _('المدينة'),
        max_length=50
    )

    country = models.CharField(
        _('الدولة'),
        max_length=50,
        default='الأردن'
    )

    # الشعار
    logo = models.ImageField(
        _('الشعار'),
        upload_to='company_logos/',
        blank=True
    )

    # 🆕 السنة المالية
    fiscal_year_start_month = models.IntegerField(
        _('شهر بداية السنة المالية'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    fiscal_year_start_day = models.IntegerField(
        _('يوم بداية السنة المالية'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )

    # 🆕 العملة الأساسية
    base_currency = models.ForeignKey(
        'accounting.Currency',
        on_delete=models.PROTECT,
        verbose_name=_('العملة الأساسية'),
        null=True,
        blank=True,
        related_name='companies'
    )

    # 🆕 إعدادات الضرائب
    default_tax_rate = models.DecimalField(
        _('نسبة الضريبة الافتراضية %'),
        max_digits=5,
        decimal_places=2,
        default=16.0
    )

    tax_registration_number = models.CharField(
        _('رقم التسجيل الضريبي'),
        max_length=50,
        blank=True
    )

    is_active = models.BooleanField(
        _('نشطة'),
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

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

    code = models.CharField(
        _('رمز الفرع'),
        max_length=10
    )

    name = models.CharField(
        _('اسم الفرع'),
        max_length=100
    )

    # معلومات الاتصال
    phone = models.CharField(
        _('الهاتف'),
        max_length=20,
        blank=True
    )

    fax = models.CharField(
        _('الفاكس'),
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        _('البريد الإلكتروني'),
        blank=True
    )

    address = models.TextField(
        _('العنوان'),
        blank=True
    )

    # 🆕 الإعدادات الافتراضية
    default_warehouse = models.ForeignKey(
        'base_data.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('المستودع الافتراضي'),
        related_name='default_for_branches'
    )

    default_cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('مركز التكلفة الافتراضي'),
        related_name='default_for_branches'
    )

    is_main = models.BooleanField(
        _('الفرع الرئيسي'),
        default=False
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _('فرع')
        verbose_name_plural = _('الفروع')
        unique_together = [['company', 'code']]

    def save(self, *args, **kwargs):
        """التأكد من وجود فرع رئيسي واحد فقط لكل شركة"""
        if self.is_main:
            Branch.objects.filter(
                company=self.company,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class User(AbstractUser):
    """نموذج المستخدم المخصص"""

    # معلومات إضافية
    phone = models.CharField(
        _('رقم الهاتف'),
        max_length=20,
        blank=True
    )

    emp_number = models.CharField(
        _('رقم الموظف'),
        max_length=20,
        blank=True,
        unique=True,
        null=True
    )

    # الشركة والفرع
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name=_('الشركة'),
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    # 🆕 ربط مع الموظف
    employee = models.OneToOneField(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الموظف'),
        related_name='user_account'
    )

    # 🆕 المستودع الافتراضي
    default_warehouse = models.ForeignKey(
        'base_data.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('المستودع الافتراضي'),
        related_name='default_users'
    )

    # حدود الصلاحيات
    max_discount_percentage = models.DecimalField(
        _('نسبة الخصم المسموحة'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # 🆕 التوقيع
    signature = models.ImageField(
        _('التوقيع'),
        upload_to='signatures/',
        blank=True
    )

    # 🆕 إعدادات الواجهة
    ui_language = models.CharField(
        _('لغة الواجهة'),
        max_length=5,
        choices=[
            ('ar', _('العربية')),
            ('en', _('English')),
        ],
        default='ar'
    )

    theme = models.CharField(
        _('المظهر'),
        max_length=20,
        choices=[
            ('light', _('فاتح')),
            ('dark', _('داكن')),
            ('auto', _('تلقائي')),
        ],
        default='light'
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def can_approve_discount(self, discount_percentage):
        """هل يستطيع الموافقة على هذا الخصم؟"""
        if self.is_superuser:
            return True
        if hasattr(self, 'profile'):
            return discount_percentage <= self.profile.max_discount_percentage
        return discount_percentage <= self.max_discount_percentage

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
        Branch,
        verbose_name=_('الفروع المسموحة'),
        blank=True,
        help_text=_('فارغ = كل الفروع')
    )

    # 🆕 قيود المستودعات
    allowed_warehouses = models.ManyToManyField(
        'base_data.Warehouse',
        verbose_name=_('المستودعات المسموحة'),
        blank=True,
        help_text=_('فارغ = كل المستودعات')
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _('ملف المستخدم')
        verbose_name_plural = _('ملفات المستخدمين')

    def __str__(self):
        return f"ملف {self.user.username}"


# 🆕 تسلسل الترقيم التلقائي
class NumberingSequence(models.Model):
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
        # الموارد البشرية
        ('payroll', _('كشف رواتب')),
        ('loan', _('سلفة/قرض')),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('الفرع'),
        help_text=_('فارغ = على مستوى الشركة')
    )

    document_type = models.CharField(
        _('نوع المستند'),
        max_length=50,
        choices=DOCUMENT_TYPES
    )

    prefix = models.CharField(
        _('البادئة'),
        max_length=20,
        help_text=_('مثال: INV, PO, JV')
    )

    suffix = models.CharField(
        _('اللاحقة'),
        max_length=20,
        blank=True
    )

    next_number = models.IntegerField(
        _('الرقم التالي'),
        default=1
    )

    padding = models.IntegerField(
        _('عدد الأصفار'),
        default=6,
        help_text=_('مثال: 6 = 000001')
    )

    yearly_reset = models.BooleanField(
        _('إعادة ترقيم سنوياً'),
        default=True
    )

    include_year = models.BooleanField(
        _('تضمين السنة'),
        default=True
    )

    include_month = models.BooleanField(
        _('تضمين الشهر'),
        default=False
    )

    separator = models.CharField(
        _('الفاصل'),
        max_length=1,
        default='/',
        help_text=_('مثال: / أو -')
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    class Meta:
        verbose_name = _('تسلسل ترقيم')
        verbose_name_plural = _('تسلسلات الترقيم')
        unique_together = [
            ['company', 'branch', 'document_type']
        ]

    def get_next_number(self):
        """الحصول على الرقم التالي"""
        import datetime

        parts = [self.prefix]

        if self.include_year:
            parts.append(str(datetime.date.today().year))

        if self.include_month:
            parts.append(f"{datetime.date.today().month:02d}")

        parts.append(str(self.next_number).zfill(self.padding))

        if self.suffix:
            parts.append(self.suffix)

        number = self.separator.join(parts)

        # زيادة العداد
        self.next_number += 1
        self.save()

        return number

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.prefix}"


# 🆕 الصلاحيات المخصصة
class CustomPermission(models.Model):
    """صلاحيات مخصصة إضافية"""

    name = models.CharField(
        _('اسم الصلاحية'),
        max_length=100
    )

    code = models.CharField(
        _('رمز الصلاحية'),
        max_length=100,
        unique=True
    )

    description = models.TextField(
        _('الوصف'),
        blank=True
    )

    category = models.CharField(
        _('التصنيف'),
        max_length=50,
        choices=[
            ('sales', _('المبيعات')),
            ('purchases', _('المشتريات')),
            ('inventory', _('المخازن')),
            ('accounting', _('المحاسبة')),
            ('hr', _('الموارد البشرية')),
            ('reports', _('التقارير')),
            ('system', _('النظام')),
        ]
    )

    users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_('المستخدمون'),
        related_name='custom_permissions'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        verbose_name=_('المجموعات')
    )

    class Meta:
        verbose_name = _('صلاحية مخصصة')
        verbose_name_plural = _('الصلاحيات المخصصة')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# 🆕 إعدادات النظام
class SystemSettings(models.Model):
    """إعدادات النظام العامة"""

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('الشركة'),
        related_name='settings'
    )

    # إعدادات المخزون
    negative_stock_allowed = models.BooleanField(
        _('السماح بالرصيد السالب'),
        default=False
    )

    auto_create_batches = models.BooleanField(
        _('إنشاء دفعات تلقائياً'),
        default=False
    )

    stock_valuation_method = models.CharField(
        _('طريقة تقييم المخزون'),
        max_length=20,
        choices=[
            ('fifo', _('الوارد أولاً صادر أولاً')),
            ('lifo', _('الوارد أخيراً صادر أولاً')),
            ('average', _('متوسط التكلفة')),
        ],
        default='average'
    )

    # إعدادات المبيعات
    customer_credit_check = models.BooleanField(
        _('فحص حد ائتمان العملاء'),
        default=True
    )

    auto_reserve_stock = models.BooleanField(
        _('حجز المخزون تلقائياً'),
        default=True
    )

    sales_return_period = models.IntegerField(
        _('فترة السماح بالمرتجعات (أيام)'),
        default=7
    )

    # إعدادات المحاسبة
    auto_create_journal_entries = models.BooleanField(
        _('إنشاء قيود تلقائياً'),
        default=True
    )

    require_approval_journal_entries = models.BooleanField(
        _('تتطلب موافقة على القيود'),
        default=True
    )

    # إعدادات الموارد البشرية
    overtime_rate = models.DecimalField(
        _('معدل أجر الوقت الإضافي'),
        max_digits=5,
        decimal_places=2,
        default=1.5,
        help_text=_('1.5 = مرة ونصف الأجر العادي')
    )

    annual_leave_days = models.IntegerField(
        _('أيام الإجازة السنوية'),
        default=21
    )

    # إعدادات عامة
    session_timeout = models.IntegerField(
        _('مهلة انتهاء الجلسة (دقائق)'),
        default=30
    )

    password_expiry_days = models.IntegerField(
        _('مدة صلاحية كلمة المرور (أيام)'),
        default=90,
        help_text=_('0 = لا تنتهي')
    )

    force_two_factor = models.BooleanField(
        _('إجبار المصادقة الثنائية'),
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _('إعدادات النظام')
        verbose_name_plural = _('إعدادات النظام')

    def __str__(self):
        return f"إعدادات {self.company.name}"


class AuditLog(models.Model):
    """سجل العمليات"""

    ACTION_CHOICES = [
        ('CREATE', _('إنشاء')),
        ('UPDATE', _('تعديل')),
        ('DELETE', _('حذف')),
        ('VIEW', _('عرض')),
        ('PRINT', _('طباعة')),
        ('EXPORT', _('تصدير')),
        ('LOGIN', _('دخول')),
        ('LOGOUT', _('خروج')),
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

    model_name = models.CharField(
        _('النموذج'),
        max_length=100
    )

    object_id = models.PositiveIntegerField(
        _('معرف السجل'),
        null=True,
        blank=True
    )

    object_repr = models.CharField(
        _('وصف السجل'),
        max_length=200
    )

    # البيانات
    old_values = models.JSONField(
        _('القيم القديمة'),
        blank=True,
        null=True
    )

    new_values = models.JSONField(
        _('القيم الجديدة'),
        blank=True,
        null=True
    )

    # 🆕 معلومات إضافية
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('الفرع')
    )

    # معلومات تقنية
    ip_address = models.GenericIPAddressField(
        _('عنوان IP'),
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        _('المتصفح'),
        blank=True
    )

    timestamp = models.DateTimeField(
        _('التوقيت'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('سجل عملية')
        verbose_name_plural = _('سجل العمليات')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr}"
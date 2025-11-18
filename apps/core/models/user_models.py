# apps/core/models/user_models.py
"""
نماذج المستخدمين والصلاحيات - User Models
- User: المستخدم (يمتد من AbstractUser)
- UserProfile: ملف المستخدم الإضافي
- CustomPermission: الصلاحيات المخصصة
- PermissionGroup: مجموعات الصلاحيات
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class User(AbstractUser):
    """المستخدم"""

    phone = models.CharField(_('رقم الهاتف'), max_length=20, blank=True)
    emp_number = models.CharField(_('رقم الموظف'), max_length=20, blank=True, unique=True, null=True)

    company = models.ForeignKey('Company', on_delete=models.PROTECT, verbose_name=_('الشركة'), null=True, blank=True)
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, verbose_name=_('الفرع'), null=True, blank=True)
    default_warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True,
                                          verbose_name=_('المستودع الافتراضي'), related_name='default_users')

    max_discount_percentage = models.DecimalField(_('نسبة الخصم المسموحة'), max_digits=5, decimal_places=2, default=0)
    signature = models.ImageField(_('التوقيع'), upload_to='signatures/', blank=True)

    ui_language = models.CharField(_('لغة الواجهة'), max_length=5, choices=[('ar', _('العربية')), ('en', _('English'))],
                                   default='ar')
    theme = models.CharField(_('المظهر'), max_length=20,
                             choices=[('light', _('فاتح')), ('dark', _('داكن')), ('auto', _('تلقائي'))],
                             default='light')

    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.get_full_name() or self.username

    def can_access_branch(self, branch):
        """التحقق من إمكانية الوصول للفرع"""
        if self.is_superuser:
            return True

        if self.company == branch.company:
            return True

        if hasattr(self, 'profile'):
            allowed_branches = self.profile.allowed_branches.all()
            if allowed_branches.exists():
                return branch in allowed_branches
            return True

        return False


class UserProfile(models.Model):
    """إعدادات إضافية للمستخدم"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # حدود الصلاحيات
    max_discount_percentage = models.DecimalField(_('نسبة الخصم المسموحة'), max_digits=5, decimal_places=2,
                                                  default=15.0)
    max_credit_limit = models.DecimalField(_('حد الائتمان المسموح'), max_digits=12, decimal_places=2, default=0)

    # قيود الفروع
    allowed_branches = models.ManyToManyField('Branch', verbose_name=_('الفروع المسموحة'), blank=True,
                                              help_text=_('فارغ = كل الفروع'))

    # قيود المستودعات
    allowed_warehouses = models.ManyToManyField('Warehouse', verbose_name=_('المستودعات المسموحة'), blank=True,
                                                help_text=_('فارغ = كل المستودعات'))

    permission_groups = models.ManyToManyField(
        'PermissionGroup',
        blank=True,
        verbose_name=_('مجموعات الصلاحيات'),
        help_text=_('مجموعات الصلاحيات التي ينتمي إليها المستخدم')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ملف المستخدم')
        verbose_name_plural = _('ملفات المستخدمين')

    def get_all_custom_permissions(self):
        """الحصول على جميع الصلاحيات المخصصة (مباشرة + من المجموعات)"""
        direct_permissions = set(CustomPermission.objects.filter(
            users=self.user,
            is_active=True
        ))

        group_permissions = set()
        for group in self.permission_groups.filter(is_active=True):
            group_permissions.update(group.get_active_custom_permissions())

        return list(direct_permissions | group_permissions)

    def get_all_django_permissions(self):
        """الحصول على جميع صلاحيات Django (مباشرة + من المجموعات + من Groups)"""
        django_permissions = set()
        for group in self.permission_groups.filter(is_active=True):
            django_permissions.update(group.django_permissions.all())

        for group in self.user.groups.all():
            django_permissions.update(group.permissions.all())

        django_permissions.update(self.user.user_permissions.all())

        return list(django_permissions)

    def has_custom_permission(self, permission_code):
        """التحقق من وجود صلاحية مخصصة"""
        if CustomPermission.objects.filter(
                users=self.user,
                code=permission_code,
                is_active=True
        ).exists():
            return True

        for group in self.permission_groups.filter(is_active=True):
            if group.permissions.filter(code=permission_code, is_active=True).exists():
                return True

        return False

    def has_custom_permission_with_limit(self, permission_code, amount=None):
        """التحقق من الصلاحية مع حد المبلغ"""
        permissions = CustomPermission.objects.filter(
            Q(users=self.user) | Q(permissiongroup__userprofile=self),
            code=permission_code,
            is_active=True
        ).distinct()

        for permission in permissions:
            if permission.max_amount is None:
                return True
            elif amount is None:
                return True
            elif amount <= permission.max_amount:
                return True

        return False

    def get_permission_max_amount(self, permission_code):
        """الحصول على الحد الأقصى للمبلغ لصلاحية معينة"""
        permissions = CustomPermission.objects.filter(
            Q(users=self.user) | Q(permissiongroup__userprofile=self),
            code=permission_code,
            is_active=True
        ).distinct()

        max_amounts = [p.max_amount for p in permissions if p.max_amount is not None]

        if not max_amounts:
            return None

        return max(max_amounts)

    def __str__(self):
        return f"ملف {self.user.username}"


class CustomPermission(models.Model):
    """صلاحيات مخصصة إضافية"""

    name = models.CharField(_('اسم الصلاحية'), max_length=100)
    code = models.CharField(_('رمز الصلاحية'), max_length=100, unique=True)
    description = models.TextField(_('الوصف'), blank=True)
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

    permission_type = models.CharField(
        _('نوع الصلاحية'),
        max_length=20,
        choices=[
            ('view', _('عرض')),
            ('add', _('إضافة')),
            ('change', _('تعديل')),
            ('delete', _('حذف')),
            ('approve', _('موافقة')),
            ('export', _('تصدير')),
            ('print', _('طباعة')),
            ('special', _('صلاحية خاصة')),
        ],
        default='view'
    )

    is_active = models.BooleanField(_('نشط'), default=True)

    requires_approval = models.BooleanField(
        _('يتطلب موافقة'),
        default=False,
        help_text=_('هل تحتاج هذه الصلاحية موافقة من مدير أعلى؟')
    )

    max_amount = models.DecimalField(
        _('الحد الأقصى للمبلغ'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('الحد الأقصى للمبلغ المسموح (للصلاحيات المالية)')
    )

    users = models.ManyToManyField(User, blank=True, verbose_name=_('المستخدمون'), related_name='custom_permissions')
    groups = models.ManyToManyField('auth.Group', blank=True, verbose_name=_('المجموعات'))

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = _('صلاحية مخصصة')
        verbose_name_plural = _('الصلاحيات المخصصة')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        """التحقق من صحة البيانات"""
        from django.core.exceptions import ValidationError

        if self.code:
            self.code = self.code.lower().replace(' ', '_')

        if self.max_amount and self.max_amount < 0:
            raise ValidationError(_('الحد الأقصى للمبلغ لا يمكن أن يكون سالباً'))


class PermissionGroup(models.Model):
    """مجموعات الصلاحيات المخصصة"""

    name = models.CharField(_('اسم المجموعة'), max_length=200, unique=True)
    description = models.TextField(_('الوصف'), blank=True)

    # الصلاحيات المخصصة
    permissions = models.ManyToManyField(
        CustomPermission,
        blank=True,
        verbose_name=_('الصلاحيات المخصصة'),
        help_text=_('الصلاحيات المخصصة المضمنة في هذه المجموعة')
    )

    # صلاحيات Django الأساسية
    django_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        verbose_name=_('صلاحيات Django'),
        help_text=_('صلاحيات Django الأساسية (CRUD) المضمنة في هذه المجموعة')
    )

    is_active = models.BooleanField(_('نشط'), default=True)

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('الشركة'),
        help_text=_('اتركها فارغة للمجموعات العامة')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('مجموعة صلاحيات')
        verbose_name_plural = _('مجموعات الصلاحيات')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_custom_permissions_count(self):
        """عدد الصلاحيات المخصصة النشطة"""
        return self.permissions.filter(is_active=True).count()

    def get_django_permissions_count(self):
        """عدد صلاحيات Django"""
        return self.django_permissions.count()

    def get_total_permissions_count(self):
        """إجمالي الصلاحيات"""
        return self.get_custom_permissions_count() + self.get_django_permissions_count()

    def get_active_custom_permissions(self):
        """الحصول على الصلاحيات المخصصة النشطة فقط"""
        return self.permissions.filter(is_active=True)

    def get_permissions_by_category(self):
        """تجميع الصلاحيات حسب التصنيف"""
        permissions = self.get_active_custom_permissions()
        categories = {}

        for perm in permissions:
            if perm.category not in categories:
                categories[perm.category] = []
            categories[perm.category].append(perm)

        return categories

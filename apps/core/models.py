# apps/core/models.py
"""
جميع نماذج النظام في مكان واحد - الإصدار النهائي المُصحح
17 نموذج - البنية التحتية + البيانات التجارية الأساسية
"""

from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class BaseModel(models.Model):
    """النموذج الأساسي الموحد - للأمواد والبيانات الأساسية"""

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

    code = models.CharField(
        _('الرمز'),
        max_length=20
    )

    name = models.CharField(
        _('الاسم'),
        max_length=50
    )

    is_cash = models.BooleanField(
        _('نقدي'),
        default=True
    )

    class Meta:
        verbose_name = _('طريقة دفع')
        verbose_name_plural = _('طرق الدفع')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name

class Company(models.Model):
    """الشركة"""

    name = models.CharField(_('اسم الشركة'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200)
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, unique=True)
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20)
    email = models.EmailField(_('البريد الإلكتروني'))
    address = models.TextField(_('العنوان'))
    city = models.CharField(_('المدينة'), max_length=50)
    country = models.CharField(_('الدولة'), max_length=50, default='الأردن')
    logo = models.ImageField(_('الشعار'), upload_to='company_logos/', blank=True)

    fiscal_year_start_month = models.IntegerField(_('شهر بداية السنة المالية'), default=1,
                                                  validators=[MinValueValidator(1), MaxValueValidator(12)])
    fiscal_year_start_day = models.IntegerField(_('يوم بداية السنة المالية'), default=1,
                                                validators=[MinValueValidator(1), MaxValueValidator(31)])

    base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('العملة الأساسية'),
                                      related_name='companies')
    default_tax_rate = models.DecimalField(_('نسبة الضريبة الافتراضية %'), max_digits=5, decimal_places=2, default=16.0)

    is_active = models.BooleanField(_('نشطة'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('شركة')
        verbose_name_plural = _('الشركات')

    def get_fiscal_year_start_month_display(self):
        """إرجاع اسم الشهر بدلاً من رقمه"""
        month_names = {
            1: _('يناير'), 2: _('فبراير'), 3: _('مارس'),
            4: _('أبريل'), 5: _('مايو'), 6: _('يونيو'),
            7: _('يوليو'), 8: _('أغسطس'), 9: _('سبتمبر'),
            10: _('أكتوبر'), 11: _('نوفمبر'), 12: _('ديسمبر')
        }
        return month_names.get(self.fiscal_year_start_month, str(self.fiscal_year_start_month))

    def __str__(self):
        return self.name

    # ✅ **إضافة هذه الدالة:**
    def create_default_sequences(self):
        """إنشاء تسلسلات الترقيم الافتراضية للشركة"""

        # قائمة بكل التسلسلات المطلوبة
        sequences = [
            # المبيعات
            {
                'document_type': 'sales_invoice',
                'prefix': 'SI',
                'description': 'فاتورة مبيعات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_return',
                'prefix': 'SR',
                'description': 'مرتجع مبيعات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_quotation',
                'prefix': 'QT',
                'description': 'عرض سعر',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_order',
                'prefix': 'SO',
                'description': 'أمر بيع',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المشتريات
            {
                'document_type': 'purchase_invoice',
                'prefix': 'PI',
                'description': 'فاتورة مشتريات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_return',
                'prefix': 'PR',
                'description': 'مرتجع مشتريات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_order',
                'prefix': 'PO',
                'description': 'أمر شراء',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_request',
                'prefix': 'PRQ',
                'description': 'طلب شراء',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المخازن
            {
                'document_type': 'stock_in',
                'prefix': 'SI',
                'description': 'سند إدخال',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_out',
                'prefix': 'SO',
                'description': 'سند إخراج',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_transfer',
                'prefix': 'ST',
                'description': 'سند تحويل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_count',
                'prefix': 'SC',
                'description': 'جرد',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المحاسبة
            {
                'document_type': 'journal_entry',
                'prefix': 'JV',
                'description': 'قيد يومية',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'payment_voucher',
                'prefix': 'PV',
                'description': 'سند صرف',
                'yearly_reset': True,
                'include_year': True,
                'include_month': True,
                'padding': 4
            },
            {
                'document_type': 'receipt_voucher',
                'prefix': 'RV',
                'description': 'سند قبض',
                'yearly_reset': True,
                'include_year': True,
                'include_month': True,
                'padding': 4
            },
            # الأصول
            {
                'document_type': 'asset',
                'prefix': 'AST',
                'description': 'أصل ثابت',
                'yearly_reset': False,
                'include_year': False,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'asset_transaction',
                'prefix': 'AT',
                'description': 'عملية على أصل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'asset_maintenance',
                'prefix': 'MAINT',
                'description': 'صيانة أصل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
        ]

        created_count = 0

        for seq_data in sequences:
            # التحقق من عدم وجود التسلسل
            if not NumberingSequence.objects.filter(
                    company=self,
                    document_type=seq_data['document_type']
            ).exists():
                NumberingSequence.objects.create(
                    company=self,
                    document_type=seq_data['document_type'],
                    prefix=seq_data['prefix'],
                    next_number=1,
                    padding=seq_data['padding'],
                    yearly_reset=seq_data['yearly_reset'],
                    include_year=seq_data['include_year'],
                    include_month=seq_data['include_month'],
                    separator='/',
                    is_active=True
                )
                created_count += 1

        return created_count

    # ✅ **إضافة دالة إنشاء الحسابات الافتراضية:**
    def create_default_accounts(self):
        """إنشاء دليل الحسابات الافتراضي"""
        from apps.accounting.models import AccountType, Account

        # التحقق من عدم وجود حسابات مسبقاً
        if Account.objects.filter(company=self).exists():
            return 0

        created_count = 0

        # إنشاء أنواع الحسابات إذا لم تكن موجودة
        account_types = {
            'assets': AccountType.objects.get_or_create(
                code='1',
                defaults={
                    'name': 'الأصول',
                    'type_category': 'assets',
                    'normal_balance': 'debit'
                }
            )[0],
            'liabilities': AccountType.objects.get_or_create(
                code='2',
                defaults={
                    'name': 'الخصوم',
                    'type_category': 'liabilities',
                    'normal_balance': 'credit'
                }
            )[0],
            'equity': AccountType.objects.get_or_create(
                code='3',
                defaults={
                    'name': 'حقوق الملكية',
                    'type_category': 'equity',
                    'normal_balance': 'credit'
                }
            )[0],
            'revenue': AccountType.objects.get_or_create(
                code='4',
                defaults={
                    'name': 'الإيرادات',
                    'type_category': 'revenue',
                    'normal_balance': 'credit'
                }
            )[0],
            'expenses': AccountType.objects.get_or_create(
                code='5',
                defaults={
                    'name': 'المصروفات',
                    'type_category': 'expenses',
                    'normal_balance': 'debit'
                }
            )[0],
        }

        # قائمة الحسابات الافتراضية
        default_accounts = [
            # الأصول المتداولة
            {'code': '110000', 'name': 'الأصول المتداولة', 'type': 'assets', 'parent': None, 'accept_entries': False},
            {'code': '110100', 'name': 'البنك', 'type': 'assets', 'parent': '110000', 'is_bank_account': True},
            {'code': '110200', 'name': 'الصندوق', 'type': 'assets', 'parent': '110000', 'is_cash_account': True},
            {'code': '120000', 'name': 'المخزون', 'type': 'assets', 'parent': None},
            {'code': '120300', 'name': 'سلف الموظفين', 'type': 'assets', 'parent': None},
            {'code': '220100', 'name': 'العملاء', 'type': 'assets', 'parent': None},

            # ✅ الأصول الثابتة
            {'code': '130000', 'name': 'الأصول الثابتة', 'type': 'assets', 'parent': None, 'accept_entries': False},
            {'code': '130100', 'name': 'الأصول الثابتة - التكلفة', 'type': 'assets', 'parent': '130000'},
            {'code': '131000', 'name': 'مجمع إهلاك الأصول الثابتة', 'type': 'assets', 'parent': None},

            # الخصوم
            {'code': '210000', 'name': 'الخصوم المتداولة', 'type': 'liabilities', 'parent': None,
             'accept_entries': False},
            {'code': '210100', 'name': 'الموردين', 'type': 'liabilities', 'parent': '210000'},
            {'code': '210300', 'name': 'التزامات الإيجار التمويلي', 'type': 'liabilities', 'parent': '210000'},

            # حقوق الملكية
            {'code': '310000', 'name': 'رأس المال', 'type': 'equity', 'parent': None},

            # الإيرادات
            {'code': '410000', 'name': 'إيرادات المبيعات', 'type': 'revenue', 'parent': None},
            {'code': '420000', 'name': 'خصم المبيعات', 'type': 'revenue', 'parent': None},
            {'code': '420100', 'name': 'أرباح بيع أصول ثابتة', 'type': 'revenue', 'parent': None},
            {'code': '420200', 'name': 'إيرادات تعويضات تأمين', 'type': 'revenue', 'parent': None},

            # ✅ المصروفات - الأصول
            {'code': '510000', 'name': 'تكلفة البضاعة المباعة', 'type': 'expenses', 'parent': None},
            {'code': '510100', 'name': 'مصروف الرواتب', 'type': 'expenses', 'parent': None},
            {'code': '520000', 'name': 'المصروفات العمومية', 'type': 'expenses', 'parent': None,
             'accept_entries': False},
            {'code': '520100', 'name': 'خسائر بيع أصول ثابتة', 'type': 'expenses', 'parent': '520000'},
            {'code': '520200', 'name': 'خسائر استبعاد أصول', 'type': 'expenses', 'parent': '520000'},
            {'code': '520300', 'name': 'مصروف الصيانة', 'type': 'expenses', 'parent': '520000'},
            {'code': '520400', 'name': 'مصروف الإيجار', 'type': 'expenses', 'parent': '520000'},
            {'code': '520500', 'name': 'مصروف فوائد', 'type': 'expenses', 'parent': '520000'},
            {'code': '520600', 'name': 'مصروف تحمل التأمين', 'type': 'expenses', 'parent': '520000'},
            {'code': '520700', 'name': 'مصروف الإهلاك', 'type': 'expenses', 'parent': '520000'},
            {'code': '530000', 'name': 'خصم المشتريات', 'type': 'expenses', 'parent': None},
        ]

        # إنشاء الحسابات
        accounts_dict = {}

        for acc_data in default_accounts:
            parent_obj = None
            if acc_data.get('parent'):
                parent_obj = accounts_dict.get(acc_data['parent'])

            account = Account.objects.create(
                company=self,
                code=acc_data['code'],
                name=acc_data['name'],
                account_type=account_types[acc_data['type']],
                parent=parent_obj,
                currency=self.base_currency,
                nature='both',
                accept_entries=acc_data.get('accept_entries', True),
                is_cash_account=acc_data.get('is_cash_account', False),
                is_bank_account=acc_data.get('is_bank_account', False),
                opening_balance=0
            )

            accounts_dict[acc_data['code']] = account
            created_count += 1

        return created_count


class Warehouse(BaseModel):
    """المستودعات"""

    code = models.CharField(_('رمز المستودع'), max_length=20)
    name = models.CharField(_('اسم المستودع'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    address = models.TextField(_('العنوان'), blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    is_main = models.BooleanField(_('المستودع الرئيسي'), default=False)
    allow_negative_stock = models.BooleanField(_('السماح بالرصيد السالب'), default=False)
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_('مدير المستودع'), related_name='managed_warehouses')
    notes = models.TextField(_('ملاحظات'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    class Meta:
        verbose_name = _('مستودع')
        verbose_name_plural = _('المستودعات')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_main:
            Warehouse.objects.filter(company=self.company, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    """الفرع"""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches', verbose_name=_('الشركة'))
    code = models.CharField(_('رمز الفرع'), max_length=10)
    name = models.CharField(_('اسم الفرع'), max_length=100)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    address = models.TextField(_('العنوان'), blank=True)

    default_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
                                          verbose_name=_('المستودع الافتراضي'), related_name='default_for_branches')

    is_main = models.BooleanField(_('الفرع الرئيسي'), default=False)
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('فرع')
        verbose_name_plural = _('الفروع')
        unique_together = [['company', 'code']]

    def save(self, *args, **kwargs):
        if self.is_main:
            Branch.objects.filter(company=self.company, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class User(AbstractUser):
    """المستخدم"""

    phone = models.CharField(_('رقم الهاتف'), max_length=20, blank=True)
    emp_number = models.CharField(_('رقم الموظف'), max_length=20, blank=True, unique=True, null=True)

    company = models.ForeignKey(Company, on_delete=models.PROTECT, verbose_name=_('الشركة'), null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name=_('الفرع'), null=True, blank=True)
    default_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
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
        # إذا كان superuser
        if self.is_superuser:
            return True

        # إذا كان من نفس الشركة
        if self.company == branch.company:
            return True

        # التحقق من الصلاحيات المخصصة
        if hasattr(self, 'profile'):
            allowed_branches = self.profile.allowed_branches.all()
            if allowed_branches.exists():
                return branch in allowed_branches
            # إذا لم يحدد فروع معينة = يصل لكل فروع الشركة
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
    allowed_branches = models.ManyToManyField(Branch, verbose_name=_('الفروع المسموحة'), blank=True,
                                              help_text=_('فارغ = كل الفروع'))

    # قيود المستودعات
    allowed_warehouses = models.ManyToManyField(Warehouse, verbose_name=_('المستودعات المسموحة'), blank=True,
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
        # الصلاحيات المباشرة من CustomPermission
        direct_permissions = set(CustomPermission.objects.filter(
            users=self.user,
            is_active=True
        ))

        # الصلاحيات من المجموعات
        group_permissions = set()
        for group in self.permission_groups.filter(is_active=True):
            group_permissions.update(group.get_active_permissions())

        return list(direct_permissions | group_permissions)

    def get_all_django_permissions(self):
        """الحصول على جميع صلاحيات Django (مباشرة + من المجموعات + من Groups)"""
        from django.contrib.auth.models import Permission

        # صلاحيات Django من مجموعات الصلاحيات المخصصة
        django_permissions = set()
        for group in self.permission_groups.filter(is_active=True):
            django_permissions.update(group.django_permissions.all())

        # صلاحيات Django من Groups العادية
        for group in self.user.groups.all():
            django_permissions.update(group.permissions.all())

        # الصلاحيات المباشرة للمستخدم
        django_permissions.update(self.user.user_permissions.all())

        return list(django_permissions)

    def has_custom_permission(self, permission_code):
        """التحقق من وجود صلاحية مخصصة"""
        # التحقق في الصلاحيات المباشرة
        if CustomPermission.objects.filter(
                users=self.user,
                code=permission_code,
                is_active=True
        ).exists():
            return True

        # التحقق في مجموعات الصلاحيات
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
                return True  # لا يوجد حد للمبلغ
            elif amount is None:
                return True  # لا يوجد مبلغ للتحقق منه
            elif amount <= permission.max_amount:
                return True  # المبلغ ضمن الحد المسموح

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
            return None  # لا يوجد حد

        return max(max_amounts)  # أعلى حد متاح

    def __str__(self):
        return f"ملف {self.user.username}"


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

    # إضافة جديد - نوع الصلاحية
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

    # إضافة جديد - حالة النشاط
    is_active = models.BooleanField(_('نشط'), default=True)

    # إضافة جديد - يتطلب موافقة
    requires_approval = models.BooleanField(
        _('يتطلب موافقة'),
        default=False,
        help_text=_('هل تحتاج هذه الصلاحية موافقة من مدير أعلى؟')
    )

    # إضافة جديد - حد المبلغ
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

    # إضافة جديد - تواريخ الإنشاء والتحديث مع null=True
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,  # ✅ يسمح بـ NULL
        blank=True  # ✅ يسمح بالفراغ
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,  # ✅ يسمح بـ NULL
        blank=True  # ✅ يسمح بالفراغ
    )

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

class UnitOfMeasure(BaseModel):
    """وحدات القياس"""

    code = models.CharField(_('الرمز'), max_length=10)
    name = models.CharField(_('الاسم'), max_length=50)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('وحدة قياس')
        verbose_name_plural = _('وحدات القياس')
        unique_together = [['code', 'company']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ItemCategory(BaseModel):
    """تصنيفات المواد - 4 مستويات"""

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                               verbose_name=_('التصنيف الأب'))
    code = models.CharField(_('رمز التصنيف'), max_length=20)
    name = models.CharField(_('اسم التصنيف'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    level = models.PositiveIntegerField(_('المستوى'), default=1, editable=False)
    description = models.TextField(_('الوصف'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    class Meta:
        verbose_name = _('تصنيف المواد')
        verbose_name_plural = _('تصنيفات المواد')
        unique_together = [['company', 'code']]
        ordering = ['level', 'name']

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
            if self.level > 4:
                raise ValueError(_('لا يمكن تجاوز 4 مستويات'))
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        indent = "  " * (self.level - 1)
        return f"{indent}{self.name}"


class Brand(BaseModel):
    """العلامات التجارية"""

    name = models.CharField(_('اسم العلامة التجارية'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    description = models.TextField(_('الوصف'), blank=True)
    logo = models.ImageField(_('الشعار'), upload_to='brands/logos/', blank=True, null=True)
    website = models.URLField(_('الموقع الإلكتروني'), blank=True)
    country = models.CharField(_('بلد المنشأ'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('علامة تجارية')
        verbose_name_plural = _('العلامات التجارية')
        unique_together = [['name', 'company']]
        ordering = ['name']

    def __str__(self):
        return self.name


class BusinessPartner(BaseModel):
    """العملاء - موحد للعملاء والموردين مع المرفقات والمندوبين المتعددين"""

    PARTNER_TYPES = [('customer', _('عميل')), ('supplier', _('مورد')), ('both', _('عميل ومورد'))]
    ACCOUNT_TYPE_CHOICES = [('cash', _('نقدي')), ('credit', _('ذمم'))]

    # تعديل خيارات الحالة الضريبية
    TAX_STATUS_CHOICES = [
        ('taxable', _('خاضع')),
        ('non_taxable', _('غير خاضع')),  # تم تغيير من 'exempt' إلى 'non_taxable'
        ('export', _('تصدير'))
    ]

    partner_type = models.CharField(_('نوع العميل'), max_length=10, choices=PARTNER_TYPES, default='customer')
    code = models.CharField(_('الرمز'), max_length=50)
    name = models.CharField(_('الاسم'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)
    account_type = models.CharField(_('نوع الحساب'), max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='credit')

    # معلومات الاتصال
    contact_person = models.CharField(_('جهة الاتصال'), max_length=100, blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    mobile = models.CharField(_('الموبايل'), max_length=20, blank=True)
    fax = models.CharField(_('الفاكس'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)

    # ملاحظة: sales_representative تم إزالته لاستبداله بنموذج منفصل للمندوبين المتعددين

    # العنوان
    address = models.TextField(_('العنوان'), blank=True)
    city = models.CharField(_('المدينة'), max_length=50, blank=True)
    region = models.CharField(_('المنطقة'), max_length=50, blank=True)

    # معلومات ضريبية مع فترة الإعفاء
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, blank=True)
    tax_status = models.CharField(_('الحالة الضريبية'), max_length=20, choices=TAX_STATUS_CHOICES, default='taxable')
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)

    # حقول جديدة لفترة الإعفاء الضريبي
    tax_exemption_start_date = models.DateField(_('تاريخ بداية الإعفاء'), null=True, blank=True)
    tax_exemption_end_date = models.DateField(_('تاريخ انتهاء الإعفاء'), null=True, blank=True)
    tax_exemption_reason = models.CharField(_('سبب الإعفاء'), max_length=200, blank=True)

    default_price_list = models.ForeignKey(
        'PriceList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('قائمة الأسعار الافتراضية'),
        help_text=_('قائمة الأسعار المستخدمة لهذا العميل')
    )

    # الحسابات المحاسبية
    customer_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('حساب العميل'),
        help_text=_('حساب المدينين الخاص بهذا العميل')
    )

    supplier_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suppliers',
        verbose_name=_('حساب المورد'),
        help_text=_('حساب الدائنين الخاص بهذا المورد')
    )

    # حدود الائتمان
    credit_limit = models.DecimalField(_('حد الائتمان'), max_digits=12, decimal_places=2, default=0)
    credit_period = models.PositiveIntegerField(_('فترة الائتمان (أيام)'), default=30)

    # المرفقات الأربعة المطلوبة
    commercial_register_file = models.FileField(
        _('ملف السجل التجاري'),
        upload_to='partners/commercial_register/',
        blank=True,
        null=True,
        help_text=_('ملف السجل التجاري للعميل')
    )
    payment_letter_file = models.FileField(
        _('كتاب التسديد'),
        upload_to='partners/payment_letters/',
        blank=True,
        null=True,
        help_text=_('كتاب التسديد من البنك')
    )
    tax_exemption_file = models.FileField(
        _('كتاب الإعفاء الضريبي'),
        upload_to='partners/tax_exemptions/',
        blank=True,
        null=True,
        help_text=_('كتاب الإعفاء الضريبي من الحكومة')
    )
    other_attachments = models.FileField(
        _('مرفقات أخرى'),
        upload_to='partners/other_attachments/',
        blank=True,
        null=True,
        help_text=_('مرفقات إضافية')
    )

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عميل')
        verbose_name_plural = _('العملاء')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_customer(self):
        return self.partner_type in ['customer', 'both']

    def is_supplier(self):
        return self.partner_type in ['supplier', 'both']

    def is_tax_exempt_active(self):
        """التحقق من صحة الإعفاء الضريبي حسب التاريخ"""
        if self.tax_status != 'non_taxable':
            return False

        if not self.tax_exemption_start_date or not self.tax_exemption_end_date:
            return False

        from django.utils import timezone
        today = timezone.now().date()
        return self.tax_exemption_start_date <= today <= self.tax_exemption_end_date

    def get_effective_tax_status(self):
        """الحصول على الحالة الضريبية الفعلية مع مراعاة انتهاء فترة الإعفاء"""
        if self.tax_status == 'non_taxable' and not self.is_tax_exempt_active():
            return 'taxable'  # انتهت فترة الإعفاء، يصبح خاضع للضريبة
        return self.tax_status

    def generate_code(self):
        """توليد كود العميل"""
        if self.partner_type == 'customer':
            prefix = 'CUS'
        elif self.partner_type == 'supplier':
            prefix = 'SUP'
        else:  # both
            prefix = 'PAR'

        last_partner = BusinessPartner.objects.filter(
            company=self.company,
            code__startswith=prefix
        ).order_by('-id').first()

        if last_partner:
            try:
                last_number = int(last_partner.code[3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:06d}"

    # دالة للحصول على الحساب المناسب:
    def get_account(self):
        """الحصول على الحساب المحاسبي المناسب"""
        if self.partner_type == 'customer':
            return self.customer_account or Account.objects.get(
                company=self.company, code='220100'
            )
        elif self.partner_type == 'supplier':
            return self.supplier_account or Account.objects.get(
                company=self.company, code='210100'
            )
        else:  # both
            # إرجاع حسب السياق أو الافتراضي
            return self.customer_account or self.supplier_account

# نموذج جديد للمندوبين المتعددين
class PartnerRepresentative(BaseModel):
    """مندوبي العميل - يمكن للعميل الواحد أن يكون له عدة مندوبين"""

    partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.CASCADE,
        related_name='representatives',
        verbose_name=_('العميل')
    )
    representative_name = models.CharField(
        _('اسم المندوب'),
        max_length=100,
        help_text=_('اسم المندوب المسؤول عن هذا العميل')
    )
    phone = models.CharField(_('هاتف المندوب'), max_length=20, blank=True)
    is_primary = models.BooleanField(_('المندوب الرئيسي'), default=False)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('مندوب العميل')
        verbose_name_plural = _('مندوبي العملاء')
        ordering = ['-is_primary', 'representative_name']

    def __str__(self):
        primary_text = _('(رئيسي)') if self.is_primary else ''
        return f"{self.partner.name} - {self.representative_name} {primary_text}"

    def save(self, *args, **kwargs):
        # إذا كان هذا المندوب رئيسي، اجعل الآخرين غير رئيسيين
        if self.is_primary:
            PartnerRepresentative.objects.filter(
                partner=self.partner,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)


class Item(BaseModel):
    """المواد"""

    code = models.CharField(_('رمز المادة'), max_length=50)
    item_code = models.CharField(_('رمز الكود'), max_length=100, blank=True, null=True)  # يدوي
    name = models.CharField(_('اسم المادة'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)
    catalog_number = models.CharField(_('رقم الكتالوج'), max_length=100, blank=True, null=True)
    barcode = models.CharField(_('الباركود'), max_length=100, blank=True, null=True)

    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT, related_name='items',
                                 verbose_name=_('التصنيف'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='items',
                              verbose_name=_('العلامة التجارية'))
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='items',
                                        verbose_name=_('وحدة القياس'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('العملة'), related_name='items')

    tax_rate = models.DecimalField(_('نسبة الضريبة %'), max_digits=5, decimal_places=2, default=16.0)

    # الوصف والمواصفات
    short_description = models.TextField(_('وصف مختصر'), max_length=300, blank=True)
    description = models.TextField(_('الوصف التفصيلي'), blank=True)
    specifications = models.JSONField(_('المواصفات الفنية'), default=dict, blank=True)
    features = models.TextField(_('المميزات'), blank=True)

    # المتغيرات
    has_variants = models.BooleanField(_('له متغيرات'), default=False)

    # الأبعاد الفيزيائية
    weight = models.DecimalField(_('الوزن (كغ)'), max_digits=10, decimal_places=3, null=True, blank=True)
    length = models.DecimalField(_('الطول (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(_('العرض (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(_('الارتفاع (سم)'), max_digits=10, decimal_places=2, null=True, blank=True)

    # معلومات إضافية
    manufacturer = models.CharField(_('الشركة المصنعة'), max_length=200, blank=True)
    model_number = models.CharField(_('رقم الموديل'), max_length=100, blank=True)

    # الملفات والصور
    image = models.ImageField(_('صورة المادة'), upload_to='items/images/', blank=True, null=True)
    attachment = models.FileField(_('ملف مرفق'), upload_to='items/attachments/', blank=True, null=True)
    attachment_name = models.CharField(_('اسم المرفق'), max_length=100, blank=True)

    # الملاحظات
    notes = models.TextField(_('ملاحظات'), blank=True)
    additional_notes = models.TextField(_('ملاحظات إضافية'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    sales_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_items',
        verbose_name=_('حساب المبيعات')
    )
    purchase_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_items',
        verbose_name=_('حساب المشتريات')
    )
    inventory_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('حساب المخزون')
    )
    cost_of_goods_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cogs_items',
        verbose_name=_('حساب تكلفة البضاعة المباعة')
    )

    class Meta:
        verbose_name = _('مادة')
        verbose_name_plural = _('المواد')
        ordering = ['name']
        unique_together = [['code', 'company'], ['barcode', 'company']]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        prefix = 'ITM'
        last_item = Item.objects.filter(company=self.company, code__startswith=prefix).order_by('-id').first()

        if last_item:
            try:
                last_number = int(last_item.code[3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:06d}"


class VariantAttribute(BaseModel):
    """خصائص المتغيرات"""

    name = models.CharField(_('اسم الخاصية'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    display_name = models.CharField(_('اسم العرض'), max_length=100, blank=True)
    is_required = models.BooleanField(_('إجباري'), default=True)
    sort_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    class Meta:
        verbose_name = _('خاصية المتغير')
        verbose_name_plural = _('خصائص المتغيرات')
        ordering = ['sort_order', 'name']
        unique_together = [['name', 'company']]

    def __str__(self):
        return self.display_name or self.name


class VariantValue(BaseModel):
    """قيم الخصائص"""

    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, related_name='values',
                                  verbose_name=_('الخاصية'))
    value = models.CharField(_('القيمة'), max_length=100)
    value_en = models.CharField(_('القيمة الإنجليزية'), max_length=100, blank=True)
    display_value = models.CharField(_('قيمة العرض'), max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    class Meta:
        verbose_name = _('قيمة المتغير')
        verbose_name_plural = _('قيم المتغيرات')
        ordering = ['attribute', 'sort_order', 'value']
        unique_together = [['attribute', 'value']]

    def __str__(self):
        return f"{self.attribute.name}: {self.display_value or self.value}"


class ItemVariant(BaseModel):
    """متغيرات المواد"""

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='variants', verbose_name=_('المادة'))
    code = models.CharField(_('كود المتغير'), max_length=50)
    catalog_number = models.CharField(_(' المتغير رقم الكتالوج'), max_length=100, blank=True, null=True)
    barcode = models.CharField(_('باركود المتغير'), max_length=100, blank=True)
    weight = models.DecimalField(_('الوزن الخاص'), max_digits=10, decimal_places=3, null=True, blank=True)
    image = models.ImageField(_('صورة المتغير'), upload_to='items/variants/', blank=True, null=True)
    notes = models.TextField(_('ملاحظات المتغير'), blank=True)

    class Meta:
        verbose_name = _('متغير المادة')
        verbose_name_plural = _('متغيرات المواد')
        ordering = ['item', 'code']
        unique_together = [['item', 'code']]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        base_code = self.item.code
        variant_count = self.item.variants.count() + 1
        return f"{base_code}-V{variant_count:03d}"

    def __str__(self):
        return f"{self.item.name} - متغير {self.code}"


class ItemVariantAttributeValue(BaseModel):
    """ربط متغير المادة بقيم الخصائص"""

    variant = models.ForeignKey(ItemVariant, on_delete=models.CASCADE, related_name='variant_attribute_values',
                                verbose_name=_('المتغير'))
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, verbose_name=_('الخاصية'))
    value = models.ForeignKey(VariantValue, on_delete=models.CASCADE, verbose_name=_('القيمة'))

    class Meta:
        verbose_name = _('قيمة خاصية المتغير')
        verbose_name_plural = _('قيم خصائص المتغيرات')
        unique_together = [['variant', 'attribute']]

    def __str__(self):
        return f"{self.variant} - {self.attribute.name}: {self.value.value}"


class SystemSettings(models.Model):
    """إعدادات النظام"""

    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name=_('الشركة'), related_name='settings')
    negative_stock_allowed = models.BooleanField(_('السماح بالرصيد السالب'), default=False)
    stock_valuation_method = models.CharField(_('طريقة تقييم المخزون'), max_length=20,
                                              choices=[('fifo', _('الوارد أولاً صادر أولاً')),
                                                       ('lifo', _('الوارد أخيراً صادر أولاً')),
                                                       ('average', _('متوسط التكلفة'))], default='average')
    customer_credit_check = models.BooleanField(_('فحص حد ائتمان العملاء'), default=True)
    auto_create_journal_entries = models.BooleanField(_('إنشاء قيود تلقائياً'), default=True)
    session_timeout = models.IntegerField(_('مهلة انتهاء الجلسة (دقائق)'), default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('إعدادات النظام')
        verbose_name_plural = _('إعدادات النظام')

    def __str__(self):
        return f"إعدادات {self.company.name}"


class AuditLog(models.Model):
    """سجل العمليات"""

    ACTION_CHOICES = [('CREATE', _('إنشاء')), ('UPDATE', _('تعديل')), ('DELETE', _('حذف')), ('VIEW', _('عرض')),
                      ('LOGIN', _('دخول')), ('LOGOUT', _('خروج'))]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_('المستخدم'))
    action = models.CharField(_('العملية'), max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(_('النموذج'), max_length=100)
    object_id = models.PositiveIntegerField(_('معرف السجل'), null=True, blank=True)
    object_repr = models.CharField(_('وصف السجل'), max_length=200)
    old_values = models.JSONField(_('القيم القديمة'), blank=True, null=True)
    new_values = models.JSONField(_('القيم الجديدة'), blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, verbose_name=_('الشركة'))
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, verbose_name=_('الفرع'))
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)
    timestamp = models.DateTimeField(_('التوقيت'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل عملية')
        verbose_name_plural = _('سجل العمليات')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr}"


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
        Company,
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


class PriceList(BaseModel):
    """قوائم الأسعار - مثل: جملة، تجزئة، VIP"""

    name = models.CharField(_('اسم القائمة'), max_length=100)
    code = models.CharField(_('رمز القائمة'), max_length=20)
    description = models.TextField(_('الوصف'), blank=True)
    is_default = models.BooleanField(_('قائمة افتراضية'), default=False)
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة'),
        related_name='price_lists'
    )

    class Meta:
        verbose_name = _('قائمة أسعار')
        verbose_name_plural = _('قوائم الأسعار')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def save(self, *args, **kwargs):
        """تأكد من وجود قائمة افتراضية واحدة فقط"""
        if self.is_default:
            PriceList.objects.filter(
                company=self.company,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class PriceListItem(models.Model):
    """أسعار الأمواد في كل قائمة"""

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('قائمة الأسعار')
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='price_list_items',
        verbose_name=_('المادة')
    )
    variant = models.ForeignKey(
        ItemVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='price_list_items',
        verbose_name=_('المتغير')
    )
    price = models.DecimalField(
        _('السعر'),
        max_digits=15,
        decimal_places=3
    )
    min_quantity = models.DecimalField(
        _('الكمية الأدنى'),
        max_digits=10,
        decimal_places=3,
        default=1
    )
    start_date = models.DateField(
        _('تاريخ البداية'),
        null=True,
        blank=True
    )
    end_date = models.DateField(
        _('تاريخ النهاية'),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('سعر مادة')
        verbose_name_plural = _('أسعار الأمواد')
        unique_together = [['price_list', 'item', 'variant']]
        ordering = ['item__name', 'variant__code']
        indexes = [
            models.Index(fields=['price_list', 'item']),
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]

    def clean(self):
        """التحقق من صحة البيانات"""
        from django.core.exceptions import ValidationError

        # إذا كان المادة له متغيرات، يجب تحديد متغير
        if self.item.has_variants and not self.variant:
            raise ValidationError(
                _('يجب تحديد متغير للمادة الذي له متغيرات')
            )

        # إذا كان المادة بدون متغيرات، لا يجب تحديد متغير
        if not self.item.has_variants and self.variant:
            raise ValidationError(
                _('لا يمكن تحديد متغير لمادة بدون متغيرات')
            )

        # التحقق من تواريخ الصلاحية
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                )

    def is_valid_date(self, check_date=None):
        """التحقق من صلاحية السعر في تاريخ معين"""
        from django.utils import timezone

        if not check_date:
            check_date = timezone.now().date()

        if not self.is_active:
            return False

        if self.start_date and check_date < self.start_date:
            return False

        if self.end_date and check_date > self.end_date:
            return False

        return True

    def __str__(self):
        variant_str = f" - {self.variant.code}" if self.variant else ""
        return f"{self.price_list.name}: {self.item.name}{variant_str} - {self.price}"


# دالة مساعدة للحصول على سعر مادة
def get_item_price(item, variant=None, price_list=None, quantity=1, check_date=None):
    """
    الحصول على سعر مادة أو متغير من قائمة أسعار معينة

    Args:
        item: المادة
        variant: المتغير (اختياري)
        price_list: قائمة الأسعار (إذا لم تحدد، ستستخدم القائمة الافتراضية)
        quantity: الكمية (للتحقق من الكمية الأدنى)
        check_date: تاريخ التحقق (افتراضياً اليوم)

    Returns:
        Decimal: السعر أو 0 إذا لم يوجد
    """
    from decimal import Decimal
    from django.utils import timezone

    if not check_date:
        check_date = timezone.now().date()

    # إذا لم تحدد قائمة أسعار، استخدم الافتراضية
    if not price_list:
        try:
            price_list = PriceList.objects.filter(
                company=item.company,
                is_default=True,
                is_active=True
            ).first()

            if not price_list:
                # إذا لم توجد قائمة افتراضية، استخدم أول قائمة نشطة
                price_list = PriceList.objects.filter(
                    company=item.company,
                    is_active=True
                ).first()

            if not price_list:
                return Decimal('0.000')
        except:
            return Decimal('0.000')

    try:
        # البحث عن السعر
        query = PriceListItem.objects.filter(
            price_list=price_list,
            item=item,
            is_active=True
        )

        # إضافة شرط المتغير
        if variant:
            query = query.filter(variant=variant)
        else:
            query = query.filter(variant__isnull=True)

        # البحث عن سعر صالح في التاريخ المحدد مع الكمية المناسبة
        prices = query.filter(
            min_quantity__lte=quantity
        ).order_by('-min_quantity')

        for price_item in prices:
            if price_item.is_valid_date(check_date):
                return price_item.price

        # إذا لم يوجد سعر صالح، أرجع 0
        return Decimal('0.000')

    except PriceListItem.DoesNotExist:
        return Decimal('0.000')
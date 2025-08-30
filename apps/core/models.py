# apps/core/models.py
"""
جميع نماذج النظام في مكان واحد - الإصدار النهائي المُصحح
17 نموذج - البنية التحتية + البيانات التجارية الأساسية
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class BaseModel(models.Model):
    """النموذج الأساسي الموحد"""

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, verbose_name=_('الشركة'))
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, null=True, blank=True, verbose_name=_('الفرع'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التعديل'))
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created',
                                   verbose_name=_('أنشأ بواسطة'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))

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

    def __str__(self):
        return self.name


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ملف المستخدم')
        verbose_name_plural = _('ملفات المستخدمين')

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

    class Meta:
        verbose_name = _('تسلسل ترقيم')
        verbose_name_plural = _('تسلسلات الترقيم')
        unique_together = [['company', 'branch', 'document_type']]

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

    users = models.ManyToManyField(User, blank=True, verbose_name=_('المستخدمون'), related_name='custom_permissions')
    groups = models.ManyToManyField('auth.Group', blank=True, verbose_name=_('المجموعات'))

    class Meta:
        verbose_name = _('صلاحية مخصصة')
        verbose_name_plural = _('الصلاحيات المخصصة')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


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
    """تصنيفات الأصناف - 4 مستويات"""

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
        verbose_name = _('تصنيف الأصناف')
        verbose_name_plural = _('تصنيفات الأصناف')
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
    """الشركاء التجاريين - موحد للعملاء والموردين"""

    PARTNER_TYPES = [('customer', _('عميل')), ('supplier', _('مورد')), ('both', _('عميل ومورد'))]
    ACCOUNT_TYPE_CHOICES = [('cash', _('نقدي')), ('credit', _('ذمم'))]
    TAX_STATUS_CHOICES = [('taxable', _('خاضع')), ('exempt', _('معفى')), ('export', _('تصدير'))]

    partner_type = models.CharField(_('نوع الشريك'), max_length=10, choices=PARTNER_TYPES, default='customer')
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

    # المندوب - مطلوب للمبيعات
    sales_representative = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اسم المندوب'),
        related_name='assigned_partners'
    )

    # العنوان
    address = models.TextField(_('العنوان'), blank=True)
    city = models.CharField(_('المدينة'), max_length=50, blank=True)
    region = models.CharField(_('المنطقة'), max_length=50, blank=True)

    # معلومات ضريبية
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, blank=True)
    tax_status = models.CharField(_('الحالة الضريبية'), max_length=20, choices=TAX_STATUS_CHOICES, default='taxable')
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)

    # حدود الائتمان
    credit_limit = models.DecimalField(_('حد الائتمان'), max_digits=12, decimal_places=2, default=0)
    credit_period = models.PositiveIntegerField(_('فترة الائتمان (أيام)'), default=30)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('شريك تجاري')
        verbose_name_plural = _('الشركاء التجاريون')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_customer(self):
        return self.partner_type in ['customer', 'both']

    def is_supplier(self):
        return self.partner_type in ['supplier', 'both']


class Item(BaseModel):
    """الأصناف"""

    code = models.CharField(_('رمز الصنف'), max_length=50)
    name = models.CharField(_('اسم الصنف'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)
    sku = models.CharField(_('SKU'), max_length=100, blank=True)
    barcode = models.CharField(_('الباركود'), max_length=100, blank=True, null=True)

    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT, related_name='items',
                                 verbose_name=_('التصنيف'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='items',
                              verbose_name=_('العلامة التجارية'))
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='items',
                                        verbose_name=_('وحدة القياس'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('العملة'), related_name='items')

    # المستودع الافتراضي - مطلوب للعمليات المخزنية
    default_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('المستودع الافتراضي'),
        related_name='default_items'
    )

    # الأسعار والضرائب
    # purchase_price = models.DecimalField(_('سعر الشراء'), max_digits=12, decimal_places=4, default=0)
    # sale_price = models.DecimalField(_('سعر البيع'), max_digits=12, decimal_places=4, default=0)
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
    image = models.ImageField(_('صورة الصنف'), upload_to='items/images/', blank=True, null=True)
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
        verbose_name = _('صنف')
        verbose_name_plural = _('الأصناف')
        ordering = ['name']
        unique_together = [['code', 'company'], ['sku', 'company'], ['barcode', 'company']]

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
    """متغيرات الأصناف"""

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='variants', verbose_name=_('الصنف'))
    code = models.CharField(_('كود المتغير'), max_length=50)
    sku = models.CharField(_('SKU المتغير'), max_length=100, blank=True)
    barcode = models.CharField(_('باركود المتغير'), max_length=100, blank=True)
    weight = models.DecimalField(_('الوزن الخاص'), max_digits=10, decimal_places=3, null=True, blank=True)
    image = models.ImageField(_('صورة المتغير'), upload_to='items/variants/', blank=True, null=True)
    notes = models.TextField(_('ملاحظات المتغير'), blank=True)

    class Meta:
        verbose_name = _('متغير الصنف')
        verbose_name_plural = _('متغيرات الأصناف')
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
    """ربط متغير الصنف بقيم الخصائص"""

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
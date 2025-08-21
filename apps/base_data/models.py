# apps/base_data/models.py
"""
نماذج البيانات الأساسية
يحتوي على: العملاء، الموردين، الأصناف، وحدات القياس، المستودعات
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from core.models import Company, Branch, User


class BaseModel(models.Model):
    """نموذج أساسي يحتوي على حقول مشتركة"""

    # الشركة والفرع
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    # التتبع
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        verbose_name=_('أنشأ بواسطة')
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated',
        verbose_name=_('عدّل بواسطة')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التعديل')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    class Meta:
        abstract = True


class UnitOfMeasure(BaseModel):
    """وحدات القياس"""

    code = models.CharField(
        _('الرمز'),
        max_length=10,
        unique=True
    )

    name = models.CharField(
        _('الاسم'),
        max_length=50
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=50,
        blank=True
    )

    class Meta:
        verbose_name = _('وحدة قياس')
        verbose_name_plural = _('وحدات القياس')

    def __str__(self):
        return f"{self.name} ({self.code})"


class ItemCategory(BaseModel):
    """تصنيفات الأصناف - 4 مستويات"""

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('التصنيف الأب')
    )

    code = models.CharField(
        _('رمز التصنيف'),
        max_length=20
    )

    name = models.CharField(
        _('اسم التصنيف'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
    )

    level = models.IntegerField(
        _('المستوى'),
        default=1,
        editable=False
    )

    class Meta:
        verbose_name = _('تصنيف الأصناف')
        verbose_name_plural = _('تصنيفات الأصناف')
        unique_together = [['company', 'code']]

    def save(self, *args, **kwargs):
        """حساب المستوى تلقائياً"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{'--' * (self.level - 1)} {self.name}"


class Item(BaseModel):
    """الأصناف/المواد"""

    # معلومات أساسية
    code = models.CharField(
        _('رمز الصنف'),
        max_length=50
    )

    name = models.CharField(
        _('اسم الصنف'),
        max_length=200
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=200,
        blank=True
    )

    barcode = models.CharField(
        _('الباركود'),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )

    # التصنيف والوحدة
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        verbose_name=_('التصنيف')
    )

    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name=_('وحدة القياس')
    )

    # الأسعار والضرائب
    purchase_price = models.DecimalField(
        _('سعر الشراء'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    sale_price = models.DecimalField(
        _('سعر البيع'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    tax_rate = models.DecimalField(
        _('نسبة الضريبة %'),
        max_digits=5,
        decimal_places=2,
        default=16.0
    )

    # معلومات إضافية
    manufacturer = models.CharField(
        _('الشركة المصنعة'),
        max_length=100,
        blank=True
    )

    weight = models.DecimalField(
        _('الوزن'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    image = models.ImageField(
        _('صورة الصنف'),
        upload_to='items/',
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # حدود المخزون
    minimum_quantity = models.DecimalField(
        _('الحد الأدنى'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    maximum_quantity = models.DecimalField(
        _('الحد الأعلى'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('صنف')
        verbose_name_plural = _('الأصناف')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(BaseModel):
    """المستودعات"""

    code = models.CharField(
        _('رمز المستودع'),
        max_length=20
    )

    name = models.CharField(
        _('اسم المستودع'),
        max_length=100
    )

    location = models.CharField(
        _('الموقع'),
        max_length=200,
        blank=True
    )

    keeper = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name=_('أمين المستودع')
    )

    class Meta:
        verbose_name = _('مستودع')
        verbose_name_plural = _('المستودعات')
        unique_together = [['company', 'branch', 'code']]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class CustomerSupplierBase(BaseModel):
    """نموذج أساسي للعملاء والموردين"""

    ACCOUNT_TYPE_CHOICES = [
        ('cash', _('نقدي')),
        ('credit', _('ذمم')),
    ]

    # معلومات أساسية
    code = models.CharField(
        _('الرمز'),
        max_length=50
    )

    name = models.CharField(
        _('الاسم'),
        max_length=200
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=200,
        blank=True
    )

    account_type = models.CharField(
        _('نوع الحساب'),
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default='credit'
    )

    # معلومات الاتصال
    contact_person = models.CharField(
        _('اسم جهة الاتصال'),
        max_length=100,
        blank=True
    )

    phone = models.CharField(
        _('الهاتف'),
        max_length=20,
        blank=True
    )

    mobile = models.CharField(
        _('الموبايل'),
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

    website = models.URLField(
        _('الموقع الإلكتروني'),
        blank=True
    )

    # العنوان
    address = models.TextField(
        _('العنوان'),
        blank=True
    )

    city = models.CharField(
        _('المدينة'),
        max_length=50,
        blank=True
    )

    region = models.CharField(
        _('المنطقة'),
        max_length=50,
        blank=True
    )

    # معلومات ضريبية
    tax_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=50,
        blank=True
    )

    tax_status = models.CharField(
        _('الحالة الضريبية'),
        max_length=20,
        choices=[
            ('taxable', _('خاضع')),
            ('exempt', _('معفى')),
            ('export', _('تصدير')),
        ],
        default='taxable'
    )

    commercial_register = models.CharField(
        _('السجل التجاري'),
        max_length=50,
        blank=True
    )

    # حدود الائتمان
    credit_limit = models.DecimalField(
        _('حد الائتمان'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    credit_period = models.IntegerField(
        _('فترة الائتمان (أيام)'),
        default=30
    )

    # معلومات إضافية
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        abstract = True


class Customer(CustomerSupplierBase):
    """العملاء"""

    salesperson = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('مندوب المبيعات')
    )

    discount_percentage = models.DecimalField(
        _('نسبة الخصم %'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = _('عميل')
        verbose_name_plural = _('العملاء')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(CustomerSupplierBase):
    """الموردين"""

    payment_terms = models.CharField(
        _('شروط الدفع'),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _('مورد')
        verbose_name_plural = _('الموردين')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"
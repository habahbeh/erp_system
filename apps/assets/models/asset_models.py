# apps/assets/models/asset_models.py
"""
النماذج الأساسية للأصول الثابتة
- فئات الأصول (هرمية)
- طرق الإهلاك
- حالات الأصول
- الأصل الرئيسي
- سجل الإهلاك
- المرفقات
- إعادة التقييم
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal
from apps.core.models import BaseModel, DocumentBaseModel, BusinessPartner
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()


class AssetCategory(BaseModel):
    """فئات الأصول الثابتة - هرمية"""

    code = models.CharField(_('رمز الفئة'), max_length=20)
    name = models.CharField(_('اسم الفئة'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)

    # التسلسل الهرمي
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('الفئة الأب')
    )
    level = models.IntegerField(_('المستوى'), default=1, editable=False)

    # الربط المحاسبي
    asset_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='asset_categories_asset',
        verbose_name=_('حساب الأصول'),
        null=True,
        blank=True,
        help_text=_('الحساب المحاسبي للأصول من هذه الفئة')
    )
    accumulated_depreciation_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='asset_categories_acc_dep',
        verbose_name=_('حساب مجمع الإهلاك'),
        null=True,
        blank=True
    )
    depreciation_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='asset_categories_dep_exp',
        verbose_name=_('حساب مصروف الإهلاك'),
        null=True,
        blank=True
    )

    # الإعدادات الافتراضية
    default_depreciation_method = models.ForeignKey(
        'DepreciationMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('طريقة الإهلاك الافتراضية')
    )
    default_useful_life_months = models.IntegerField(
        _('العمر الافتراضي الافتراضي (بالأشهر)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    default_salvage_value_rate = models.DecimalField(
        _('نسبة القيمة المتبقية الافتراضية %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    description = models.TextField(_('الوصف'), blank=True)

    class Meta:
        verbose_name = _('فئة أصول')
        verbose_name_plural = _('فئات الأصول')
        unique_together = [['company', 'code']]
        ordering = ['code']

    def save(self, *args, **kwargs):
        # حساب المستوى
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_full_path(self):
        """الحصول على المسار الكامل للفئة"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class DepreciationMethod(models.Model):
    """طرق الإهلاك المتاحة"""

    METHOD_TYPES = [
        ('straight_line', _('القسط الثابت - Straight Line')),
        ('declining_balance', _('القسط المتناقص - Declining Balance')),
        ('units_of_production', _('وحدات الإنتاج - Units of Production')),
    ]

    code = models.CharField(_('الرمز'), max_length=20, unique=True)
    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100)
    method_type = models.CharField(
        _('نوع الطريقة'),
        max_length=30,
        choices=METHOD_TYPES
    )

    # معدل الإهلاك (للقسط المتناقص)
    rate_percentage = models.DecimalField(
        _('معدل الإهلاك %'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('للقسط المتناقص فقط - مثال: 200 للقسط المتناقص المضاعف')
    )

    description = models.TextField(_('الوصف'), blank=True)
    is_active = models.BooleanField(_('نشطة'), default=True)

    class Meta:
        verbose_name = _('طريقة إهلاك')
        verbose_name_plural = _('طرق الإهلاك')
        ordering = ['code']

    def __str__(self):
        return self.name


class AssetCondition(models.Model):
    """حالات الأصول"""

    name = models.CharField(_('الحالة'), max_length=50, unique=True)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=50)
    color_code = models.CharField(
        _('رمز اللون'),
        max_length=7,
        default='#6c757d',
        help_text=_('مثال: #28a745 للأخضر')
    )
    description = models.TextField(_('الوصف'), blank=True)
    is_active = models.BooleanField(_('نشطة'), default=True)

    class Meta:
        verbose_name = _('حالة أصل')
        verbose_name_plural = _('حالات الأصول')
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(DocumentBaseModel):
    """الأصل الثابت - النموذج الرئيسي"""

    STATUS_CHOICES = [
        ('active', _('نشط')),
        ('inactive', _('غير نشط')),
        ('under_maintenance', _('تحت الصيانة')),
        ('disposed', _('مستبعد')),
        ('sold', _('مباع')),
    ]

    # المعلومات الأساسية
    asset_number = models.CharField(
        _('رقم الأصل'),
        max_length=50,
        editable=False,
        unique=True
    )
    name = models.CharField(_('اسم الأصل'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)

    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name=_('الفئة')
    )

    condition = models.ForeignKey(
        AssetCondition,
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name=_('الحالة'),
        null=True,
        blank=True
    )

    status = models.CharField(
        _('حالة النشاط'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # معلومات الشراء
    purchase_date = models.DateField(_('تاريخ الشراء'))
    purchase_invoice_number = models.CharField(
        _('رقم فاتورة الشراء'),
        max_length=50,
        blank=True
    )

    supplier = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        related_name='supplied_assets',
        verbose_name=_('المورد')
    )

    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        verbose_name=_('العملة'),
        related_name='assets',
        help_text=_('عملة التكلفة الأصلية')
    )

    # المعلومات المالية
    original_cost = models.DecimalField(
        _('التكلفة الأصلية'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    salvage_value = models.DecimalField(
        _('القيمة المتبقية (التخريدية)'),
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('القيمة المتوقعة في نهاية العمر الافتراضي')
    )
    accumulated_depreciation = models.DecimalField(
        _('الإهلاك المتراكم'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False
    )
    book_value = models.DecimalField(
        _('القيمة الدفترية'),
        max_digits=15,
        decimal_places=3,
        default=0,
        editable=False,
        help_text=_('التكلفة الأصلية - الإهلاك المتراكم')
    )

    # معلومات الإهلاك
    depreciation_method = models.ForeignKey(
        DepreciationMethod,
        on_delete=models.PROTECT,
        verbose_name=_('طريقة الإهلاك')
    )
    useful_life_months = models.IntegerField(
        _('العمر الافتراضي (بالأشهر)'),
        validators=[MinValueValidator(1)]
    )
    depreciation_start_date = models.DateField(
        _('تاريخ بدء الإهلاك'),
        help_text=_('عادة هو تاريخ الشراء أو تاريخ بدء الاستخدام')
    )

    # لوحدات الإنتاج فقط
    total_expected_units = models.IntegerField(
        _('إجمالي الوحدات المتوقعة'),
        null=True,
        blank=True,
        help_text=_('للإهلاك بطريقة وحدات الإنتاج - مثل: كيلومترات، ساعات تشغيل')
    )
    units_used = models.IntegerField(
        _('الوحدات المستخدمة'),
        default=0,
        help_text=_('الوحدات المستخدمة حتى الآن')
    )
    unit_name = models.CharField(
        _('اسم الوحدة'),
        max_length=30,
        blank=True,
        help_text=_('مثال: كيلومتر، ساعة، قطعة')
    )

    # الموقع والمسؤولية
    cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name=_('مركز التكلفة'),
        null=True,
        blank=True
    )
    responsible_employee = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_for_assets',
        verbose_name=_('الموظف المسؤول')
    )
    physical_location = models.CharField(
        _('الموقع الفعلي'),
        max_length=200,
        blank=True,
        help_text=_('مثال: مبنى أ - طابق 3 - مكتب 305')
    )

    # معلومات إضافية
    serial_number = models.CharField(_('الرقم التسلسلي'), max_length=100, blank=True)
    model = models.CharField(_('الموديل'), max_length=100, blank=True)
    manufacturer = models.CharField(_('الشركة المصنعة'), max_length=100, blank=True)

    # الضمان
    warranty_start_date = models.DateField(_('تاريخ بدء الضمان'), null=True, blank=True)
    warranty_end_date = models.DateField(_('تاريخ انتهاء الضمان'), null=True, blank=True)
    warranty_provider = models.CharField(_('مزود الضمان'), max_length=100, blank=True)

    # الباركود
    barcode = models.CharField(
        _('الباركود'),
        max_length=100,
        blank=True,
        unique=True,
        null=True
    )
    qr_code = models.TextField(_('QR Code'), blank=True, editable=False)

    # ملاحظات
    description = models.TextField(_('الوصف'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('أصل ثابت')
        verbose_name_plural = _('الأصول الثابتة')
        ordering = ['-purchase_date', '-asset_number']
        permissions = [
            ('can_purchase_asset', 'يمكنه شراء أصول'),
            ('can_sell_asset', 'يمكنه بيع أصول'),
            ('can_transfer_asset', 'يمكنه تحويل أصول'),
            ('can_revalue_asset', 'يمكنه إعادة تقييم أصول'),
            ('can_dispose_asset', 'يمكنه استبعاد أصول'),
            ('can_calculate_depreciation', 'يمكنه احتساب الإهلاك'),
        ]

    def save(self, *args, **kwargs):
        # إذا لم تحدد العملة، استخدم عملة الشركة
        if not self.currency_id:
            self.currency = self.company.base_currency

        # توليد رقم الأصل تلقائياً
        if not self.asset_number:
            from apps.core.models import NumberingSequence
            try:
                sequence = NumberingSequence.objects.get(
                    company=self.company,
                    document_type='asset'
                )
                self.asset_number = sequence.get_next_number()
            except NumberingSequence.DoesNotExist:
                # إنشاء تسلسل افتراضي
                sequence = NumberingSequence.objects.create(
                    company=self.company,
                    document_type='asset',
                    prefix='AST',
                    next_number=1,
                    padding=6,
                    created_by=self.created_by
                )
                self.asset_number = sequence.get_next_number()

        # استخدام الباركود = رقم الأصل إذا لم يكن محدداً
        if not self.barcode:
            self.barcode = self.asset_number

        # حساب القيمة الدفترية
        self.book_value = self.original_cost - self.accumulated_depreciation

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_number} - {self.name}"

    def get_absolute_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.pk})

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.salvage_value >= self.original_cost:
            raise ValidationError({
                'salvage_value': _('القيمة المتبقية يجب أن تكون أقل من التكلفة الأصلية')
            })

        if self.depreciation_method.method_type == 'units_of_production':
            if not self.total_expected_units:
                raise ValidationError({
                    'total_expected_units': _('يجب تحديد إجمالي الوحدات المتوقعة لطريقة وحدات الإنتاج')
                })

        if self.warranty_start_date and self.warranty_end_date:
            if self.warranty_end_date < self.warranty_start_date:
                raise ValidationError({
                    'warranty_end_date': _('تاريخ انتهاء الضمان يجب أن يكون بعد تاريخ البداية')
                })

    def get_depreciable_amount(self):
        """المبلغ القابل للإهلاك = التكلفة - القيمة المتبقية"""
        return self.original_cost - self.salvage_value

    def get_remaining_months(self):
        """الأشهر المتبقية من العمر الافتراضي"""
        today = datetime.date.today()
        months_passed = (today.year - self.depreciation_start_date.year) * 12
        months_passed += today.month - self.depreciation_start_date.month
        return max(0, self.useful_life_months - months_passed)

    def is_fully_depreciated(self):
        """هل تم إهلاك الأصل بالكامل"""
        return self.accumulated_depreciation >= self.get_depreciable_amount()

    def is_warranty_valid(self):
        """هل الضمان ساري"""
        if not self.warranty_end_date:
            return False
        return datetime.date.today() <= self.warranty_end_date

    # ✅ **إضافة دوال التحقق من الصلاحيات:**

    def can_user_purchase(self, user):
        """هل يمكن للمستخدم شراء أصول"""
        return user.has_perm('assets.can_purchase_asset')

    def can_user_sell(self, user):
        """هل يمكن للمستخدم بيع أصول"""
        return user.has_perm('assets.can_sell_asset')

    def can_user_transfer(self, user):
        """هل يمكن للمستخدم تحويل أصول"""
        return user.has_perm('assets.can_transfer_asset')

    def can_user_revalue(self, user):
        """هل يمكن للمستخدم إعادة تقييم أصول"""
        return user.has_perm('assets.can_revalue_asset')

    def can_user_dispose(self, user):
        """هل يمكن للمستخدم استبعاد أصول"""
        return user.has_perm('assets.can_dispose_asset')

    def can_user_calculate_depreciation(self, user):
        """هل يمكن للمستخدم احتساب الإهلاك"""
        return user.has_perm('assets.can_calculate_depreciation')

    # ✅ **دوال العمليات:**

    @transaction.atomic
    def calculate_monthly_depreciation(self, user=None):
        """احتساب الإهلاك الشهري"""
        from django.utils import timezone
        from decimal import Decimal

        if not self.can_user_calculate_depreciation(user):
            raise PermissionDenied(_('ليس لديك صلاحية احتساب الإهلاك'))

        if self.is_fully_depreciated():
            raise ValidationError(_('الأصل مُهلك بالكامل'))

        if self.status != 'active':
            raise ValidationError(_('الأصل غير نشط'))

        # حساب مبلغ الإهلاك الشهري
        depreciable_amount = self.get_depreciable_amount()

        if self.depreciation_method.method_type == 'straight_line':
            # القسط الثابت
            monthly_depreciation = depreciable_amount / self.useful_life_months

        elif self.depreciation_method.method_type == 'declining_balance':
            # القسط المتناقص
            rate = self.depreciation_method.rate_percentage / 100
            current_book_value = self.book_value
            monthly_depreciation = current_book_value * (rate / 12)

        elif self.depreciation_method.method_type == 'units_of_production':
            # وحدات الإنتاج - يحتاج تحديد الوحدات المستخدمة
            raise ValidationError(_('طريقة وحدات الإنتاج تحتاج تحديد الوحدات المستخدمة'))

        else:
            raise ValidationError(_('طريقة إهلاك غير مدعومة'))

        # التأكد من عدم تجاوز المبلغ القابل للإهلاك
        remaining = depreciable_amount - self.accumulated_depreciation
        if monthly_depreciation > remaining:
            monthly_depreciation = remaining

        # إنشاء سجل الإهلاك
        today = timezone.now().date()

        depreciation_record = AssetDepreciation.objects.create(
            asset=self,
            company=self.company,
            depreciation_date=today,
            depreciation_amount=monthly_depreciation,
            accumulated_depreciation_before=self.accumulated_depreciation,
            accumulated_depreciation_after=self.accumulated_depreciation + monthly_depreciation,
            book_value_after=self.book_value - monthly_depreciation,
            created_by=user
        )

        # تحديث الأصل
        self.accumulated_depreciation += monthly_depreciation
        self.book_value -= monthly_depreciation
        self.save()

        return depreciation_record

    @transaction.atomic
    def sell(self, sale_price, buyer, user=None):
        """بيع الأصل"""
        if not self.can_user_sell(user):
            raise PermissionDenied(_('ليس لديك صلاحية بيع الأصول'))

        if self.status != 'active':
            raise ValidationError(_('الأصل غير نشط'))

        from apps.assets.models import AssetTransaction

        # إنشاء معاملة البيع
        transaction = AssetTransaction.objects.create(
            company=self.company,
            branch=self.branch,
            transaction_date=timezone.now().date(),
            transaction_type='sale',
            asset=self,
            amount=sale_price,
            sale_price=sale_price,
            book_value_at_sale=self.book_value,
            business_partner=buyer,
            description=f"بيع الأصل {self.name}",
            created_by=user
        )

        # تحديث حالة الأصل
        self.status = 'sold'
        self.save()

        return transaction

    @transaction.atomic
    def dispose(self, reason, user=None):
        """استبعاد الأصل"""
        if not self.can_user_dispose(user):
            raise PermissionDenied(_('ليس لديك صلاحية استبعاد الأصول'))

        from apps.assets.models import AssetTransaction

        # إنشاء معاملة الاستبعاد
        transaction = AssetTransaction.objects.create(
            company=self.company,
            branch=self.branch,
            transaction_date=timezone.now().date(),
            transaction_type='disposal',
            asset=self,
            amount=0,
            description=reason,
            created_by=user
        )

        # تحديث حالة الأصل
        self.status = 'disposed'
        self.save()

        return transaction



class AssetDepreciation(BaseModel):
    """سجل الإهلاك التفصيلي"""

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='depreciation_records',
        verbose_name=_('الأصل')
    )

    # الفترة
    depreciation_date = models.DateField(_('تاريخ الإهلاك'))
    fiscal_year = models.ForeignKey(
        'accounting.FiscalYear',
        on_delete=models.PROTECT,
        verbose_name=_('السنة المالية'),
        null=True,
        blank=True
    )
    period = models.ForeignKey(
        'accounting.AccountingPeriod',
        on_delete=models.PROTECT,
        verbose_name=_('الفترة المحاسبية'),
        null=True,
        blank=True
    )

    # المبالغ
    depreciation_amount = models.DecimalField(
        _('مبلغ الإهلاك'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    accumulated_depreciation_before = models.DecimalField(
        _('الإهلاك المتراكم قبل'),
        max_digits=15,
        decimal_places=3,
        default=0
    )
    accumulated_depreciation_after = models.DecimalField(
        _('الإهلاك المتراكم بعد'),
        max_digits=15,
        decimal_places=3,
        default=0
    )
    book_value_after = models.DecimalField(
        _('القيمة الدفترية بعد الإهلاك'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    # لوحدات الإنتاج
    units_used_in_period = models.IntegerField(
        _('الوحدات المستخدمة في الفترة'),
        null=True,
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_depreciations',
        verbose_name=_('القيد المحاسبي')
    )


    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سجل إهلاك')
        verbose_name_plural = _('سجلات الإهلاك')
        ordering = ['-depreciation_date']
        unique_together = [['asset', 'depreciation_date']]

    def __str__(self):
        return f"{self.asset.asset_number} - {self.depreciation_date} - {self.depreciation_amount}"


class AssetAttachment(models.Model):
    """المرفقات والمستندات المتعلقة بالأصل"""

    ATTACHMENT_TYPES = [
        ('invoice', _('فاتورة')),
        ('image', _('صورة')),
        ('warranty', _('ضمان')),
        ('contract', _('عقد')),
        ('maintenance', _('مستند صيانة')),
        ('manual', _('دليل الاستخدام')),
        ('other', _('أخرى')),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('الأصل')
    )

    title = models.CharField(_('العنوان'), max_length=200)
    attachment_type = models.CharField(
        _('نوع المرفق'),
        max_length=20,
        choices=ATTACHMENT_TYPES
    )
    file = models.FileField(
        _('الملف'),
        upload_to='assets/attachments/%Y/%m/'
    )

    # للمرفقات ذات الصلاحية (مثل الضمانات والعقود)
    issue_date = models.DateField(_('تاريخ الإصدار'), null=True, blank=True)
    expiry_date = models.DateField(_('تاريخ الانتهاء'), null=True, blank=True)

    description = models.TextField(_('الوصف'), blank=True)

    uploaded_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('رفع بواسطة')
    )
    uploaded_at = models.DateTimeField(_('تاريخ الرفع'), auto_now_add=True)

    class Meta:
        verbose_name = _('مرفق أصل')
        verbose_name_plural = _('مرفقات الأصول')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.asset.asset_number} - {self.title}"

    def is_expired(self):
        """هل انتهت صلاحية المرفق"""
        if not self.expiry_date:
            return False
        return datetime.date.today() > self.expiry_date


class AssetValuation(models.Model):
    """إعادة تقييم الأصول"""

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='valuations',
        verbose_name=_('الأصل')
    )

    valuation_date = models.DateField(_('تاريخ التقييم'))
    old_value = models.DecimalField(
        _('القيمة السابقة'),
        max_digits=15,
        decimal_places=3
    )
    new_value = models.DecimalField(
        _('القيمة الجديدة'),
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    difference = models.DecimalField(
        _('الفرق'),
        max_digits=15,
        decimal_places=3,
        editable=False
    )

    reason = models.TextField(_('سبب إعادة التقييم'))

    # المُقيّم
    valuator_name = models.CharField(_('اسم المقيم'), max_length=100, blank=True)
    valuation_report = models.FileField(
        _('تقرير التقييم'),
        upload_to='assets/valuations/%Y/%m/',
        blank=True
    )

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_valuations',
        verbose_name=_('وافق عليه')
    )
    approved_at = models.DateTimeField(_('تاريخ الموافقة'), null=True, blank=True)
    is_approved = models.BooleanField(_('موافق عليه'), default=False)

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_valuations',
        verbose_name=_('القيد المحاسبي')
    )

    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_valuations',
        verbose_name=_('أنشأ بواسطة')
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('إعادة تقييم أصل')
        verbose_name_plural = _('إعادة تقييم الأصول')
        ordering = ['-valuation_date']

    def save(self, *args, **kwargs):
        # حساب الفرق
        self.difference = self.new_value - self.old_value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset.asset_number} - {self.valuation_date} - {self.difference:+,.2f}"
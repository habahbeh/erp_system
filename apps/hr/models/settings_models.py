# apps/hr/models/settings_models.py
"""
إعدادات الموارد البشرية - HR Settings Models
- HRSettings: الإعدادات العامة
- SocialSecuritySettings: إعدادات الضمان الاجتماعي
- LeaveSettings: إعدادات الإجازات
- PayrollAccountMapping: ربط حسابات الرواتب
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class HRSettings(models.Model):
    """
    الإعدادات العامة للموارد البشرية - HR General Settings
    إعدادات واحدة لكل شركة
    """

    company = models.OneToOneField(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='hr_settings',
        verbose_name=_('الشركة')
    )

    # === إعدادات ساعات العمل الافتراضية ===
    default_working_hours_per_day = models.DecimalField(
        _('ساعات العمل اليومية الافتراضية'),
        max_digits=4,
        decimal_places=2,
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(24)]
    )

    default_working_days_per_month = models.PositiveSmallIntegerField(
        _('أيام العمل الشهرية الافتراضية'),
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )

    # === إعدادات العمل الإضافي ===
    overtime_regular_rate = models.DecimalField(
        _('معامل العمل الإضافي - أيام الدوام'),
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.25'),
        help_text=_('نسبة الأجر الإضافي لأيام العمل العادية (مثال: 1.25 = 125%)')
    )

    overtime_holiday_rate = models.DecimalField(
        _('معامل العمل الإضافي - أيام العطل'),
        max_digits=4,
        decimal_places=2,
        default=Decimal('2.00'),
        help_text=_('نسبة الأجر الإضافي لأيام العطل (مثال: 2.0 = 200%)')
    )

    # === إعدادات الإجازات ===
    default_annual_leave_days = models.PositiveSmallIntegerField(
        _('أيام الإجازة السنوية الافتراضية'),
        default=14
    )

    default_sick_leave_days = models.PositiveSmallIntegerField(
        _('أيام الإجازة المرضية الافتراضية'),
        default=14
    )

    carry_forward_leave = models.BooleanField(
        _('ترحيل رصيد الإجازات'),
        default=True,
        help_text=_('هل يتم ترحيل رصيد الإجازات للسنة التالية؟')
    )

    max_carry_forward_days = models.PositiveSmallIntegerField(
        _('الحد الأقصى للترحيل'),
        default=14,
        help_text=_('الحد الأقصى لأيام الإجازة المرحلة')
    )

    sick_leave_medical_certificate_days = models.PositiveSmallIntegerField(
        _('أيام تتطلب تقرير طبي'),
        default=3,
        help_text=_('عدد أيام الإجازة المرضية التي تتطلب تقريراً طبياً')
    )

    # === إعدادات فترة التجربة ===
    default_probation_days = models.PositiveSmallIntegerField(
        _('فترة التجربة الافتراضية (بالأيام)'),
        default=90
    )

    # === إعدادات فترة الإشعار ===
    default_notice_period_days = models.PositiveSmallIntegerField(
        _('فترة الإشعار الافتراضية (بالأيام)'),
        default=30
    )

    # === إعدادات السلف ===
    max_advance_percentage = models.DecimalField(
        _('الحد الأقصى للسلفة (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text=_('نسبة الحد الأقصى للسلفة من الراتب')
    )

    max_installments = models.PositiveSmallIntegerField(
        _('الحد الأقصى لعدد الأقساط'),
        default=12
    )

    # === إعدادات عامة ===
    fiscal_year_start_month = models.PositiveSmallIntegerField(
        _('شهر بداية السنة المالية'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    auto_create_journal_entries = models.BooleanField(
        _('إنشاء القيود تلقائياً'),
        default=True,
        help_text=_('إنشاء القيود المحاسبية تلقائياً عند ترحيل الرواتب')
    )

    # === الطابع الزمني ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('إعدادات الموارد البشرية')
        verbose_name_plural = _('إعدادات الموارد البشرية')

    def __str__(self):
        return f"HR Settings - {self.company.name}"


class SocialSecuritySettings(models.Model):
    """
    إعدادات الضمان الاجتماعي - Social Security Settings
    النسب والحدود حسب الأنظمة الأردنية
    """

    company = models.OneToOneField(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='social_security_settings',
        verbose_name=_('الشركة')
    )

    # === نسب الاشتراك ===
    employee_contribution_rate = models.DecimalField(
        _('نسبة حصة الموظف (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('7.50'),
        help_text=_('نسبة الضمان الاجتماعي من راتب الموظف')
    )

    company_contribution_rate = models.DecimalField(
        _('نسبة حصة الشركة (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('14.25'),
        help_text=_('نسبة الضمان الاجتماعي التي تدفعها الشركة')
    )

    # === حدود الراتب ===
    minimum_insurable_salary = models.DecimalField(
        _('الحد الأدنى للراتب المؤمن'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('الحد الأدنى للراتب الخاضع للضمان')
    )

    maximum_insurable_salary = models.DecimalField(
        _('الحد الأقصى للراتب المؤمن'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('الحد الأقصى للراتب الخاضع للضمان')
    )

    # === التفعيل ===
    is_active = models.BooleanField(
        _('مفعل'),
        default=True,
        help_text=_('هل نظام الضمان الاجتماعي مفعل للشركة؟')
    )

    # === تاريخ السريان ===
    effective_date = models.DateField(
        _('تاريخ السريان'),
        null=True,
        blank=True,
        help_text=_('تاريخ بدء تطبيق هذه النسب')
    )

    # === الطابع الزمني ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('إعدادات الضمان الاجتماعي')
        verbose_name_plural = _('إعدادات الضمان الاجتماعي')

    @property
    def total_contribution_rate(self):
        """إجمالي نسبة الضمان"""
        return self.employee_contribution_rate + self.company_contribution_rate

    def calculate_employee_contribution(self, salary):
        """حساب حصة الموظف من الضمان"""
        if not self.is_active:
            return Decimal('0')

        # تطبيق الحدود
        insurable_salary = salary
        if self.minimum_insurable_salary and salary < self.minimum_insurable_salary:
            insurable_salary = self.minimum_insurable_salary
        if self.maximum_insurable_salary and salary > self.maximum_insurable_salary:
            insurable_salary = self.maximum_insurable_salary

        return insurable_salary * (self.employee_contribution_rate / 100)

    def calculate_company_contribution(self, salary):
        """حساب حصة الشركة من الضمان"""
        if not self.is_active:
            return Decimal('0')

        # تطبيق الحدود
        insurable_salary = salary
        if self.minimum_insurable_salary and salary < self.minimum_insurable_salary:
            insurable_salary = self.minimum_insurable_salary
        if self.maximum_insurable_salary and salary > self.maximum_insurable_salary:
            insurable_salary = self.maximum_insurable_salary

        return insurable_salary * (self.company_contribution_rate / 100)

    def __str__(self):
        return f"Social Security Settings - {self.company.name}"


class PayrollAccountMapping(models.Model):
    """
    ربط مكونات الراتب بالحسابات المحاسبية
    Payroll Account Mapping
    """

    COMPONENT_CHOICES = [
        # الاستحقاقات (مصروفات - مدين)
        ('basic_salary', _('الراتب الأساسي')),
        ('fuel_allowance', _('بدل الوقود')),
        ('other_allowances', _('بدلات أخرى')),
        ('overtime_regular', _('العمل الإضافي - أيام الدوام')),
        ('overtime_holidays', _('العمل الإضافي - أيام العطل')),
        ('other_earnings', _('أصناف أخرى (استحقاقات)')),

        # الخصومات (التزامات - دائن)
        ('advances', _('السلف')),
        ('early_leave_deductions', _('مغادرات الخصم')),
        ('administrative_deductions', _('احتزارت الخصم')),
        ('ss_employee', _('الضمان الاجتماعي - حصة الموظف')),

        # تكاليف الشركة (مصروفات)
        ('ss_company', _('الضمان الاجتماعي - حصة الشركة')),

        # حسابات الدفع
        ('salaries_payable', _('رواتب مستحقة الدفع')),
        ('ss_payable', _('ذمة الضمان الاجتماعي')),
        ('cash_bank', _('الصندوق/البنك')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='payroll_account_mappings',
        verbose_name=_('الشركة')
    )

    component = models.CharField(
        _('مكون الراتب'),
        max_length=30,
        choices=COMPONENT_CHOICES
    )

    account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        verbose_name=_('الحساب المحاسبي')
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ربط حساب راتب')
        verbose_name_plural = _('ربط حسابات الرواتب')
        unique_together = [['company', 'component']]

    @classmethod
    def get_account(cls, company, component):
        """الحصول على الحساب المرتبط بمكون معين"""
        try:
            mapping = cls.objects.get(
                company=company,
                component=component,
                is_active=True
            )
            return mapping.account
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.get_component_display()} -> {self.account.name}"


class LeaveType(models.Model):
    """
    أنواع الإجازات - Leave Types
    """

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='leave_types',
        verbose_name=_('الشركة')
    )

    code = models.CharField(
        _('الرمز'),
        max_length=20
    )

    name = models.CharField(
        _('اسم نوع الإجازة'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
    )

    # === إعدادات النوع ===
    is_paid = models.BooleanField(
        _('مدفوعة'),
        default=True,
        help_text=_('هل هذا النوع من الإجازات مدفوع؟')
    )

    affects_salary = models.BooleanField(
        _('تؤثر على الراتب'),
        default=False,
        help_text=_('هل تخصم من الراتب؟')
    )

    requires_approval = models.BooleanField(
        _('تتطلب موافقة'),
        default=True
    )

    requires_attachment = models.BooleanField(
        _('تتطلب مرفق'),
        default=False,
        help_text=_('مثل التقرير الطبي للإجازة المرضية')
    )

    # === الرصيد ===
    default_days = models.PositiveSmallIntegerField(
        _('الرصيد السنوي الافتراضي'),
        default=0
    )

    max_consecutive_days = models.PositiveSmallIntegerField(
        _('الحد الأقصى للأيام المتتالية'),
        default=0,
        help_text=_('0 = غير محدود')
    )

    allow_negative_balance = models.BooleanField(
        _('السماح بالرصيد السالب'),
        default=False
    )

    carry_forward = models.BooleanField(
        _('قابل للترحيل'),
        default=False,
        help_text=_('هل يمكن ترحيل الرصيد للسنة التالية؟')
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    description = models.TextField(
        _('الوصف'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('نوع إجازة')
        verbose_name_plural = _('أنواع الإجازات')
        unique_together = [['company', 'code']]
        ordering = ['code']

    def __str__(self):
        return self.name

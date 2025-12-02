# apps/hr/models/payroll_models.py
"""
نماذج الرواتب - المرحلة الثالثة
Payroll Models - Phase 3
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date


class Payroll(models.Model):
    """
    مسير الرواتب الشهري
    Monthly Payroll Run
    """

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('processing', _('قيد المعالجة')),
        ('calculated', _('تم الحساب')),
        ('approved', _('معتمد')),
        ('paid', _('مدفوع')),
        ('cancelled', _('ملغي')),
    ]

    MONTH_CHOICES = [
        (1, _('يناير')),
        (2, _('فبراير')),
        (3, _('مارس')),
        (4, _('أبريل')),
        (5, _('مايو')),
        (6, _('يونيو')),
        (7, _('يوليو')),
        (8, _('أغسطس')),
        (9, _('سبتمبر')),
        (10, _('أكتوبر')),
        (11, _('نوفمبر')),
        (12, _('ديسمبر')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payrolls',
        verbose_name=_('الفرع')
    )

    number = models.CharField(
        _('رقم المسير'),
        max_length=50,
        unique=True
    )

    period_year = models.PositiveIntegerField(
        _('السنة'),
        validators=[MinValueValidator(2020), MaxValueValidator(2100)]
    )

    period_month = models.PositiveIntegerField(
        _('الشهر'),
        choices=MONTH_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    from_date = models.DateField(
        _('من تاريخ')
    )

    to_date = models.DateField(
        _('إلى تاريخ')
    )

    # إجماليات
    total_basic = models.DecimalField(
        _('إجمالي الرواتب الأساسية'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_allowances = models.DecimalField(
        _('إجمالي البدلات'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_deductions = models.DecimalField(
        _('إجمالي الخصومات'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_net = models.DecimalField(
        _('صافي الرواتب'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_overtime = models.DecimalField(
        _('إجمالي العمل الإضافي'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_loans = models.DecimalField(
        _('إجمالي أقساط السلف'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_social_security = models.DecimalField(
        _('إجمالي الضمان الاجتماعي'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_income_tax = models.DecimalField(
        _('إجمالي ضريبة الدخل'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    employee_count = models.PositiveIntegerField(
        _('عدد الموظفين'),
        default=0
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payrolls',
        verbose_name=_('اعتمد بواسطة')
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # الربط المحاسبي
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payrolls',
        verbose_name=_('القيد المحاسبي')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_payrolls',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('كشف راتب')
        verbose_name_plural = _('كشوفات الرواتب')
        ordering = ['-period_year', '-period_month']
        unique_together = [['company', 'period_year', 'period_month', 'branch']]

    def __str__(self):
        return f"{self.number} - {self.get_period_month_display()} {self.period_year}"

    def clean(self):
        if self.from_date and self.to_date:
            if self.to_date < self.from_date:
                raise ValidationError({
                    'to_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

    @property
    def period_display(self):
        return f"{self.get_period_month_display()} {self.period_year}"

    def calculate_totals(self):
        """حساب الإجماليات من التفاصيل"""
        details = self.details.all()
        self.total_basic = sum(d.basic_salary for d in details)
        self.total_allowances = sum(d.total_allowances for d in details)
        self.total_deductions = sum(d.total_deductions for d in details)
        self.total_net = sum(d.net_salary for d in details)
        self.total_overtime = sum(d.overtime_amount for d in details)
        self.total_loans = sum(d.loan_deduction for d in details)
        self.total_social_security = sum(d.social_security_employee for d in details)
        self.total_income_tax = sum(d.income_tax for d in details)
        self.employee_count = details.count()
        self.save()


class PayrollDetail(models.Model):
    """
    تفاصيل راتب الموظف في الكشف
    Employee Payslip in Payroll
    """

    PAYMENT_METHOD_CHOICES = [
        ('cash', _('نقدي')),
        ('bank_transfer', _('تحويل بنكي')),
        ('check', _('شيك')),
    ]

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('مسير الرواتب')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_details',
        verbose_name=_('الموظف')
    )

    # الراتب الأساسي
    basic_salary = models.DecimalField(
        _('الراتب الأساسي'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # أيام العمل
    working_days = models.PositiveIntegerField(
        _('أيام العمل المستحقة'),
        default=30
    )

    actual_days = models.PositiveIntegerField(
        _('أيام العمل الفعلية'),
        default=30
    )

    absent_days = models.PositiveIntegerField(
        _('أيام الغياب'),
        default=0
    )

    # البدلات
    housing_allowance = models.DecimalField(
        _('بدل السكن'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    transport_allowance = models.DecimalField(
        _('بدل النقل'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    phone_allowance = models.DecimalField(
        _('بدل الهاتف'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    food_allowance = models.DecimalField(
        _('بدل الطعام'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    other_allowances = models.DecimalField(
        _('بدلات أخرى'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_allowances = models.DecimalField(
        _('إجمالي البدلات'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # العمل الإضافي
    overtime_hours = models.DecimalField(
        _('ساعات العمل الإضافي'),
        max_digits=6,
        decimal_places=2,
        default=0
    )

    overtime_amount = models.DecimalField(
        _('مبلغ العمل الإضافي'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # الخصومات
    absence_deduction = models.DecimalField(
        _('خصم الغياب'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    late_deduction = models.DecimalField(
        _('خصم التأخير'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    loan_deduction = models.DecimalField(
        _('قسط السلفة'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    social_security_employee = models.DecimalField(
        _('الضمان الاجتماعي (الموظف)'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    social_security_company = models.DecimalField(
        _('الضمان الاجتماعي (الشركة)'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    income_tax = models.DecimalField(
        _('ضريبة الدخل'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    other_deductions = models.DecimalField(
        _('خصومات أخرى'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_deductions = models.DecimalField(
        _('إجمالي الخصومات'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # الصافي
    gross_salary = models.DecimalField(
        _('إجمالي الراتب'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_salary = models.DecimalField(
        _('صافي الراتب'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # طريقة الدفع
    payment_method = models.CharField(
        _('طريقة الدفع'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer'
    )

    payment_reference = models.CharField(
        _('مرجع الدفع'),
        max_length=100,
        blank=True
    )

    is_paid = models.BooleanField(
        _('تم الدفع'),
        default=False
    )

    paid_date = models.DateField(
        _('تاريخ الدفع'),
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('تفاصيل الراتب')
        verbose_name_plural = _('تفاصيل الرواتب')
        unique_together = [['payroll', 'employee']]
        ordering = ['employee__first_name']

    def __str__(self):
        return f"{self.employee} - {self.payroll}"

    def calculate_allowances(self):
        """حساب إجمالي البدلات"""
        self.total_allowances = (
            self.housing_allowance +
            self.transport_allowance +
            self.phone_allowance +
            self.food_allowance +
            self.other_allowances
        )

    def calculate_deductions(self):
        """حساب إجمالي الخصومات"""
        self.total_deductions = (
            self.absence_deduction +
            self.late_deduction +
            self.loan_deduction +
            self.social_security_employee +
            self.income_tax +
            self.other_deductions
        )

    def calculate_net(self):
        """حساب صافي الراتب"""
        self.gross_salary = self.basic_salary + self.total_allowances + self.overtime_amount
        self.net_salary = self.gross_salary - self.total_deductions

    def save(self, *args, **kwargs):
        self.calculate_allowances()
        self.calculate_deductions()
        self.calculate_net()
        super().save(*args, **kwargs)


class PayrollAllowance(models.Model):
    """
    بدلات إضافية في كشف الراتب
    Additional Allowances in Payslip
    """

    ALLOWANCE_TYPE_CHOICES = [
        ('housing', _('بدل سكن')),
        ('transport', _('بدل مواصلات')),
        ('phone', _('بدل هاتف')),
        ('food', _('بدل طعام')),
        ('bonus', _('مكافأة')),
        ('commission', _('عمولة')),
        ('other', _('أخرى')),
    ]

    payroll_detail = models.ForeignKey(
        PayrollDetail,
        on_delete=models.CASCADE,
        related_name='allowances',
        verbose_name=_('تفاصيل الراتب')
    )

    allowance_type = models.CharField(
        _('نوع البدل'),
        max_length=50,
        choices=ALLOWANCE_TYPE_CHOICES,
        default='other'
    )

    description = models.CharField(
        _('الوصف'),
        max_length=200,
        blank=True
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('بدل في الراتب')
        verbose_name_plural = _('بدلات في الرواتب')

    def __str__(self):
        return f"{self.get_allowance_type_display()} - {self.amount}"


class PayrollDeduction(models.Model):
    """
    خصومات إضافية في كشف الراتب
    Additional Deductions in Payslip
    """

    DEDUCTION_TYPE_CHOICES = [
        ('absence', _('خصم غياب')),
        ('late', _('خصم تأخير')),
        ('social_security', _('ضمان اجتماعي')),
        ('income_tax', _('ضريبة دخل')),
        ('loan', _('قسط سلفة')),
        ('penalty', _('غرامة')),
        ('other', _('أخرى')),
    ]

    payroll_detail = models.ForeignKey(
        PayrollDetail,
        on_delete=models.CASCADE,
        related_name='deductions',
        verbose_name=_('تفاصيل الراتب')
    )

    deduction_type = models.CharField(
        _('نوع الخصم'),
        max_length=50,
        choices=DEDUCTION_TYPE_CHOICES,
        default='other'
    )

    description = models.CharField(
        _('الوصف'),
        max_length=200,
        blank=True
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('خصم في الراتب')
        verbose_name_plural = _('خصومات في الرواتب')

    def __str__(self):
        return f"{self.get_deduction_type_display()} - {self.amount}"


class PayrollLoanDeduction(models.Model):
    """
    خصم قسط السلفة في كشف الراتب
    Loan Installment Deduction in Payslip
    """

    payroll_detail = models.ForeignKey(
        PayrollDetail,
        on_delete=models.CASCADE,
        related_name='loan_deductions',
        verbose_name=_('تفاصيل الراتب')
    )

    advance = models.ForeignKey(
        'hr.Advance',
        on_delete=models.PROTECT,
        related_name='payroll_deductions',
        verbose_name=_('السلفة')
    )

    installment = models.ForeignKey(
        'hr.AdvanceInstallment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payroll_deductions',
        verbose_name=_('القسط')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        verbose_name = _('خصم سلفة في الراتب')
        verbose_name_plural = _('خصومات السلف في الرواتب')

    def __str__(self):
        return f"{self.advance} - {self.amount}"

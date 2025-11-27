# apps/hr/models/attendance_models.py
"""
نماذج الحضور والانصراف - Attendance Models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta


class Attendance(models.Model):
    """
    سجل الحضور والانصراف اليومي
    Daily Attendance Record
    """

    STATUS_CHOICES = [
        ('present', _('حاضر')),
        ('absent', _('غائب')),
        ('late', _('متأخر')),
        ('half_day', _('نصف يوم')),
        ('leave', _('إجازة')),
        ('holiday', _('عطلة')),
        ('weekend', _('عطلة نهاية الأسبوع')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('الموظف')
    )

    date = models.DateField(
        _('التاريخ')
    )

    # أوقات الحضور والانصراف
    check_in = models.TimeField(
        _('وقت الحضور'),
        null=True,
        blank=True
    )

    check_out = models.TimeField(
        _('وقت الانصراف'),
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='present'
    )

    # ساعات العمل
    working_hours = models.DecimalField(
        _('ساعات العمل'),
        max_digits=5,
        decimal_places=2,
        default=0,
        db_column='work_hours'
    )

    overtime_hours = models.DecimalField(
        _('ساعات العمل الإضافي'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    late_minutes = models.PositiveIntegerField(
        _('دقائق التأخير'),
        default=0
    )

    early_leave_minutes = models.PositiveIntegerField(
        _('دقائق المغادرة المبكرة'),
        default=0
    )

    # ملاحظات
    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # الربط بالإجازة إن وجدت
    leave_request = models.ForeignKey(
        'hr.LeaveRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records',
        verbose_name=_('طلب الإجازة')
    )

    # الطابع الزمني
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_attendances',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('سجل حضور')
        verbose_name_plural = _('سجلات الحضور')
        unique_together = [['employee', 'date']]
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee} - {self.date}"

    def calculate_working_hours(self):
        """حساب ساعات العمل"""
        if self.check_in and self.check_out:
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)

            # إذا كان الانصراف بعد منتصف الليل
            if check_out_dt < check_in_dt:
                check_out_dt += timedelta(days=1)

            diff = check_out_dt - check_in_dt
            hours = Decimal(str(diff.total_seconds() / 3600))
            return hours.quantize(Decimal('0.01'))
        return Decimal('0')

    def save(self, *args, **kwargs):
        # حساب ساعات العمل تلقائياً
        if self.check_in and self.check_out:
            self.working_hours = self.calculate_working_hours()
        super().save(*args, **kwargs)


class LeaveBalance(models.Model):
    """
    رصيد إجازات الموظف
    Employee Leave Balance
    """

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name=_('الشركة')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name=_('الموظف')
    )

    leave_type = models.ForeignKey(
        'hr.LeaveType',
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name=_('نوع الإجازة')
    )

    year = models.PositiveIntegerField(
        _('السنة')
    )

    # الرصيد
    opening_balance = models.DecimalField(
        _('الرصيد الافتتاحي'),
        max_digits=5,
        decimal_places=2,
        default=0,
        db_column='entitled_days'
    )

    used = models.DecimalField(
        _('المستخدم'),
        max_digits=5,
        decimal_places=2,
        default=0,
        db_column='used_days'
    )

    adjustment = models.DecimalField(
        _('التسوية'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('تعديلات يدوية على الرصيد')
    )

    carried_forward = models.DecimalField(
        _('المرحل'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('الرصيد المرحل من السنة السابقة')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('رصيد إجازة')
        verbose_name_plural = _('أرصدة الإجازات')
        unique_together = [['employee', 'leave_type', 'year']]
        ordering = ['-year', 'employee__first_name']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def total_entitled(self):
        """إجمالي الرصيد المستحق"""
        return self.opening_balance + self.adjustment + self.carried_forward

    @property
    def remaining_balance(self):
        """الرصيد المتبقي"""
        return self.total_entitled - self.used

    @property
    def used_percentage(self):
        """نسبة الاستخدام"""
        if self.total_entitled > 0:
            return (self.used / self.total_entitled) * 100
        return 0


class LeaveRequest(models.Model):
    """
    طلبات الإجازات
    Leave Requests
    """

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('pending', _('قيد الانتظار')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
        ('cancelled', _('ملغي')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name=_('الشركة')
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name=_('الفرع'),
        null=True,
        blank=True
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name=_('الموظف')
    )

    leave_type = models.ForeignKey(
        'hr.LeaveType',
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name=_('نوع الإجازة')
    )

    start_date = models.DateField(
        _('تاريخ البداية')
    )

    end_date = models.DateField(
        _('تاريخ النهاية')
    )

    days = models.DecimalField(
        _('عدد الأيام'),
        max_digits=5,
        decimal_places=2
    )

    reason = models.TextField(
        _('سبب الإجازة'),
        blank=True
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # بيانات الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        verbose_name=_('وافق عليه')
    )

    approval_date = models.DateTimeField(
        _('تاريخ الموافقة'),
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(
        _('سبب الرفض'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    # الطابع الزمني
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_leave_requests',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('طلب إجازة')
        verbose_name_plural = _('طلبات الإجازات')
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب إجازة #{self.pk} - {self.employee}"

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })

    def calculate_days(self):
        """حساب عدد أيام الإجازة"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days + 1
        return 0

    def save(self, *args, **kwargs):
        if not self.days:
            self.days = self.calculate_days()
        super().save(*args, **kwargs)


class EarlyLeave(models.Model):
    """
    المغادرات المبكرة
    Early Leaves / Permissions
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
    ]

    TYPE_CHOICES = [
        ('early_leave', _('مغادرة مبكرة')),
        ('late_arrival', _('تأخر عن الدوام')),
        ('personal', _('مغادرة شخصية')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='early_leaves',
        verbose_name=_('الشركة')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='early_leaves',
        verbose_name=_('الموظف')
    )

    date = models.DateField(
        _('التاريخ')
    )

    leave_type = models.CharField(
        _('نوع المغادرة'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='early_leave'
    )

    from_time = models.TimeField(
        _('من الوقت')
    )

    to_time = models.TimeField(
        _('إلى الوقت')
    )

    minutes = models.PositiveIntegerField(
        _('عدد الدقائق'),
        default=0
    )

    reason = models.TextField(
        _('السبب')
    )

    is_deductible = models.BooleanField(
        _('يخصم من الراتب'),
        default=False
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_early_leaves',
        verbose_name=_('وافق عليه')
    )

    approved_at = models.DateTimeField(
        _('تاريخ الموافقة'),
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_early_leaves',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('مغادرة')
        verbose_name_plural = _('المغادرات')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.minutes} دقيقة)"

    def calculate_minutes(self):
        """حساب عدد الدقائق"""
        if self.from_time and self.to_time:
            from_dt = datetime.combine(self.date, self.from_time)
            to_dt = datetime.combine(self.date, self.to_time)
            diff = to_dt - from_dt
            return int(diff.total_seconds() / 60)
        return 0

    def save(self, *args, **kwargs):
        if not self.minutes:
            self.minutes = self.calculate_minutes()
        super().save(*args, **kwargs)


class Overtime(models.Model):
    """
    العمل الإضافي
    Overtime Records
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
        ('paid', _('مدفوع')),
    ]

    TYPE_CHOICES = [
        ('regular', _('عمل إضافي عادي')),
        ('holiday', _('عمل في يوم عطلة')),
        ('weekend', _('عمل في نهاية الأسبوع')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='overtimes',
        verbose_name=_('الشركة')
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='overtimes',
        verbose_name=_('الموظف')
    )

    date = models.DateField(
        _('التاريخ')
    )

    overtime_type = models.CharField(
        _('نوع العمل الإضافي'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='regular'
    )

    start_time = models.TimeField(
        _('وقت البداية')
    )

    end_time = models.TimeField(
        _('وقت النهاية')
    )

    hours = models.DecimalField(
        _('عدد الساعات'),
        max_digits=5,
        decimal_places=2
    )

    rate = models.DecimalField(
        _('المعامل'),
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.25'),
        help_text=_('معامل الأجر الإضافي')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    reason = models.TextField(
        _('سبب العمل الإضافي')
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtimes',
        verbose_name=_('وافق عليه')
    )

    approved_at = models.DateTimeField(
        _('تاريخ الموافقة'),
        null=True,
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_overtimes',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('عمل إضافي')
        verbose_name_plural = _('العمل الإضافي')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.hours} ساعة)"

    def calculate_hours(self):
        """حساب عدد الساعات"""
        if self.start_time and self.end_time:
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)

            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            diff = end_dt - start_dt
            return Decimal(str(diff.total_seconds() / 3600)).quantize(Decimal('0.01'))
        return Decimal('0')

    def calculate_amount(self):
        """حساب مبلغ العمل الإضافي"""
        if self.employee and self.hours:
            hourly_rate = self.employee.basic_salary / Decimal('30') / Decimal('8')
            return (hourly_rate * self.hours * self.rate).quantize(Decimal('0.01'))
        return Decimal('0')

    def save(self, *args, **kwargs):
        if not self.hours:
            self.hours = self.calculate_hours()
        if not self.amount:
            self.amount = self.calculate_amount()
        super().save(*args, **kwargs)


class Advance(models.Model):
    """
    السلف والقروض
    Advances / Loans
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
        ('disbursed', _('تم الصرف')),
        ('partially_paid', _('مسدد جزئياً')),
        ('fully_paid', _('مسدد بالكامل')),
        ('cancelled', _('ملغي')),
    ]

    TYPE_CHOICES = [
        ('salary_advance', _('سلفة راتب')),
        ('loan', _('قرض')),
        ('emergency', _('سلفة طارئة')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='advances',
        verbose_name=_('الشركة')
    )

    advance_number = models.CharField(
        _('رقم السلفة'),
        max_length=50,
        unique=True
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='advances',
        verbose_name=_('الموظف')
    )

    advance_type = models.CharField(
        _('نوع السلفة'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='salary_advance'
    )

    request_date = models.DateField(
        _('تاريخ الطلب')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2
    )

    reason = models.TextField(
        _('سبب السلفة')
    )

    # خطة السداد
    installments = models.PositiveIntegerField(
        _('عدد الأقساط'),
        default=1
    )

    installment_amount = models.DecimalField(
        _('قيمة القسط'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    start_deduction_date = models.DateField(
        _('تاريخ بدء الخصم'),
        null=True,
        blank=True
    )

    # المبالغ
    paid_amount = models.DecimalField(
        _('المبلغ المسدد'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    remaining_amount = models.DecimalField(
        _('المبلغ المتبقي'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # الموافقة
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_advances',
        verbose_name=_('وافق عليه')
    )

    approved_at = models.DateTimeField(
        _('تاريخ الموافقة'),
        null=True,
        blank=True
    )

    disbursed_at = models.DateTimeField(
        _('تاريخ الصرف'),
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(
        _('سبب الرفض'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_advances',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('سلفة')
        verbose_name_plural = _('السلف')
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"{self.advance_number} - {self.employee}"

    def calculate_installment_amount(self):
        """حساب قيمة القسط"""
        if self.amount and self.installments:
            return (self.amount / self.installments).quantize(Decimal('0.01'))
        return Decimal('0')

    def save(self, *args, **kwargs):
        if not self.installment_amount:
            self.installment_amount = self.calculate_installment_amount()
        if not self.remaining_amount:
            self.remaining_amount = self.amount - self.paid_amount
        super().save(*args, **kwargs)


class AdvanceInstallment(models.Model):
    """
    أقساط السلف
    Advance Installments
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('deducted', _('تم الخصم')),
        ('paid', _('مدفوع نقداً')),
        ('skipped', _('تم تأجيله')),
    ]

    advance = models.ForeignKey(
        Advance,
        on_delete=models.CASCADE,
        related_name='installment_records',
        verbose_name=_('السلفة')
    )

    installment_number = models.PositiveIntegerField(
        _('رقم القسط')
    )

    due_date = models.DateField(
        _('تاريخ الاستحقاق')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2
    )

    paid_amount = models.DecimalField(
        _('المبلغ المدفوع'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    paid_date = models.DateField(
        _('تاريخ الدفع'),
        null=True,
        blank=True
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('قسط سلفة')
        verbose_name_plural = _('أقساط السلف')
        unique_together = [['advance', 'installment_number']]
        ordering = ['advance', 'installment_number']

    def __str__(self):
        return f"{self.advance} - قسط {self.installment_number}"

# apps/hr/models.py
"""
نماذج الموارد البشرية
يحتوي على: بيانات الموظفين، الرواتب، الإجازات، الحضور والانصراف، السلف والقروض
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, DocumentBaseModel, User, Branch, Currency
from apps.accounting.models import Account, JournalEntry


class Department(BaseModel):
    """الأقسام"""

    code = models.CharField(
        _('رمز القسم'),
        max_length=20
    )

    name = models.CharField(
        _('اسم القسم'),
        max_length=100
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('القسم الأب')
    )

    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('المدير')
    )

    class Meta:
        verbose_name = _('قسم')
        verbose_name_plural = _('الأقسام')
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class JobTitle(BaseModel):
    """المسميات الوظيفية"""

    code = models.CharField(
        _('رمز الوظيفة'),
        max_length=20
    )

    name = models.CharField(
        _('المسمى الوظيفي'),
        max_length=100
    )

    description = models.TextField(
        _('الوصف الوظيفي'),
        blank=True
    )

    class Meta:
        verbose_name = _('مسمى وظيفي')
        verbose_name_plural = _('المسميات الوظيفية')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name


class Employee(BaseModel):
    """بيانات الموظفين"""

    GENDER_CHOICES = [
        ('male', _('ذكر')),
        ('female', _('أنثى')),
    ]

    MARITAL_STATUS = [
        ('single', _('أعزب')),
        ('married', _('متزوج')),
        ('divorced', _('مطلق')),
        ('widowed', _('أرمل')),
    ]

    EMPLOYMENT_STATUS = [
        ('active', _('على رأس العمل')),
        ('vacation', _('في إجازة')),
        ('suspended', _('موقوف')),
        ('resigned', _('مستقيل')),
        ('terminated', _('منتهي الخدمة')),
    ]

    # معلومات أساسية
    employee_number = models.CharField(
        _('رقم الموظف'),
        max_length=20,
        unique=True
    )

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('المستخدم'),
        null=True,
        blank=True,
        related_name='employee_profile'
    )

    # البيانات الشخصية
    first_name = models.CharField(
        _('الاسم الأول'),
        max_length=50
    )

    last_name = models.CharField(
        _('اسم العائلة'),
        max_length=50
    )

    father_name = models.CharField(
        _('اسم الأب'),
        max_length=50,
        blank=True
    )

    mother_name = models.CharField(
        _('اسم الأم'),
        max_length=50,
        blank=True
    )

    national_id = models.CharField(
        _('الرقم الوطني'),
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    birth_date = models.DateField(
        _('تاريخ الميلاد'),
        null=True,
        blank=True
    )

    birth_place = models.CharField(
        _('مكان الميلاد'),
        max_length=100,
        blank=True
    )

    gender = models.CharField(
        _('الجنس'),
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    marital_status = models.CharField(
        _('الحالة الاجتماعية'),
        max_length=10,
        choices=MARITAL_STATUS,
        blank=True
    )

    # معلومات الاتصال
    phone = models.CharField(
        _('الهاتف'),
        max_length=20,
        blank=True
    )

    mobile = models.CharField(
        _('الموبايل'),
        max_length=20
    )

    email = models.EmailField(
        _('البريد الإلكتروني'),
        blank=True
    )

    address = models.TextField(
        _('العنوان'),
        blank=True
    )

    # معلومات التوظيف
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        verbose_name=_('القسم')
    )

    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.PROTECT,
        verbose_name=_('المسمى الوظيفي'),
        null=True,
        blank=True
    )

    hire_date = models.DateField(
        _('تاريخ التعيين')
    )

    contract_type = models.CharField(
        _('نوع العقد'),
        max_length=20,
        choices=[
            ('permanent', _('دائم')),
            ('temporary', _('مؤقت')),
            ('contract', _('عقد')),
            ('part_time', _('دوام جزئي')),
        ],
        default='permanent'
    )

    employment_status = models.CharField(
        _('حالة التوظيف'),
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='active'
    )

    resignation_date = models.DateField(
        _('تاريخ الاستقالة'),
        null=True,
        blank=True
    )

    # الراتب والمزايا
    basic_salary = models.DecimalField(
        _('الراتب الأساسي'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_('العملة'),
        null=True,
        blank=True
    )

    # الحسابات البنكية
    bank_name = models.CharField(
        _('اسم البنك'),
        max_length=100,
        blank=True
    )

    bank_account = models.CharField(
        _('رقم الحساب البنكي'),
        max_length=50,
        blank=True
    )

    iban = models.CharField(
        _('IBAN'),
        max_length=50,
        blank=True
    )

    # معلومات إضافية
    photo = models.ImageField(
        _('الصورة الشخصية'),
        upload_to='employees/photos/',
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('موظف')
        verbose_name_plural = _('الموظفون')
        unique_together = [['company', 'employee_number']]

    def get_full_name(self):
        """الاسم الكامل"""
        return f"{self.first_name} {self.father_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.employee_number} - {self.get_full_name()}"


class Allowance(BaseModel):
    """البدلات والعلاوات"""

    ALLOWANCE_TYPES = [
        ('fixed', _('ثابت')),
        ('percentage', _('نسبة من الراتب')),
    ]

    code = models.CharField(
        _('رمز البدل'),
        max_length=20
    )

    name = models.CharField(
        _('اسم البدل'),
        max_length=100
    )

    allowance_type = models.CharField(
        _('نوع البدل'),
        max_length=10,
        choices=ALLOWANCE_TYPES,
        default='fixed'
    )

    is_taxable = models.BooleanField(
        _('خاضع للضريبة'),
        default=True
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('الحساب المحاسبي'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('بدل')
        verbose_name_plural = _('البدلات')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name


class Deduction(BaseModel):
    """الاستقطاعات"""

    DEDUCTION_TYPES = [
        ('fixed', _('ثابت')),
        ('percentage', _('نسبة من الراتب')),
    ]

    code = models.CharField(
        _('رمز الاستقطاع'),
        max_length=20
    )

    name = models.CharField(
        _('اسم الاستقطاع'),
        max_length=100
    )

    deduction_type = models.CharField(
        _('نوع الاستقطاع'),
        max_length=10,
        choices=DEDUCTION_TYPES,
        default='fixed'
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name=_('الحساب المحاسبي'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('استقطاع')
        verbose_name_plural = _('الاستقطاعات')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name


class EmployeeAllowance(models.Model):
    """بدلات الموظف"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='allowances',
        verbose_name=_('الموظف')
    )

    allowance = models.ForeignKey(
        Allowance,
        on_delete=models.PROTECT,
        verbose_name=_('البدل')
    )

    amount = models.DecimalField(
        _('المبلغ/النسبة'),
        max_digits=12,
        decimal_places=2
    )

    start_date = models.DateField(
        _('تاريخ البداية')
    )

    end_date = models.DateField(
        _('تاريخ النهاية'),
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        _('نشط'),
        default=True
    )

    class Meta:
        verbose_name = _('بدل موظف')
        verbose_name_plural = _('بدلات الموظفين')
        unique_together = [['employee', 'allowance']]


class Payroll(DocumentBaseModel):
    """كشف الرواتب"""

    number = models.CharField(
        _('رقم الكشف'),
        max_length=50,
        editable=False
    )

    period_year = models.IntegerField(
        _('السنة')
    )

    period_month = models.IntegerField(
        _('الشهر'),
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    from_date = models.DateField(
        _('من تاريخ')
    )

    to_date = models.DateField(
        _('إلى تاريخ')
    )

    # المجاميع
    total_basic = models.DecimalField(
        _('مجموع الرواتب الأساسية'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_allowances = models.DecimalField(
        _('مجموع البدلات'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_deductions = models.DecimalField(
        _('مجموع الاستقطاعات'),
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

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('draft', _('مسودة')),
            ('calculated', _('محسوب')),
            ('approved', _('معتمد')),
            ('paid', _('مدفوع')),
            ('cancelled', _('ملغي')),
        ],
        default='draft'
    )

    # الموافقات
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='approved_payrolls'
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('كشف رواتب')
        verbose_name_plural = _('كشوف الرواتب')
        unique_together = [['company', 'number'], ['company', 'period_year', 'period_month']]
        ordering = ['-period_year', '-period_month']

    def save(self, *args, **kwargs):
        """توليد رقم الكشف"""
        if not self.number:
            self.number = f"PR/{self.period_year}/{self.period_month:02d}"

        super().save(*args, **kwargs)

    # إضافة دالة الترحيل:
    @transaction.atomic
    def post(self, user=None):
        """ترحيل كشف الرواتب وإنشاء القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, Account

        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد الكشف أولاً'))

        if self.journal_entry:
            raise ValidationError(_('الكشف مرحل مسبقاً'))

        # الحصول على السنة والفترة المالية
        from apps.accounting.models import FiscalYear, AccountingPeriod

        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.to_date,
                end_date__gte=self.to_date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.to_date,
                end_date__gte=self.to_date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.to_date,
            entry_type='auto',
            description=f"كشف رواتب {self.number} - {self.period_month}/{self.period_year}",
            reference=self.number,
            source_document='payroll',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # حساب الرواتب (مدين) - يجب تحديد حساب الرواتب في الإعدادات
        try:
            salary_expense_account = Account.objects.get(
                company=self.company,
                code='510100'  # مثال: حساب مصروف الرواتب
            )
        except Account.DoesNotExist:
            raise ValidationError(_('حساب مصروف الرواتب غير موجود'))

        # سطر إجمالي الرواتب (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=salary_expense_account,
            description=f"إجمالي الرواتب - {self.number}",
            debit_amount=self.total_net,
            credit_amount=0,
            currency=self.company.base_currency,
            reference=self.number
        )
        line_number += 1

        # حساب البنك أو الصندوق (دائن)
        try:
            cash_account = Account.objects.get(
                company=self.company,
                code='110100'  # مثال: حساب البنك
            )
        except Account.DoesNotExist:
            raise ValidationError(_('حساب البنك/الصندوق غير موجود'))

        # سطر الصندوق/البنك (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=cash_account,
            description=f"صرف رواتب - {self.number}",
            debit_amount=0,
            credit_amount=self.total_net,
            currency=self.company.base_currency,
            reference=self.number
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث الكشف
        self.journal_entry = journal_entry
        self.status = 'paid'
        self.save()

        return journal_entry

    def calculate_attendance(self):
        """حساب أيام الحضور الفعلية من سجل الحضور"""
        from django.db.models import Count, Q

        for detail in self.details.all():
            # حساب أيام الحضور
            attendance_data = Attendance.objects.filter(
                employee=detail.employee,
                date__gte=self.from_date,
                date__lte=self.to_date
            ).aggregate(
                present_days=Count('id', filter=Q(status='present')),
                absent_days=Count('id', filter=Q(status='absent')),
                late_days=Count('id', filter=Q(status='late')),
                leave_days=Count('id', filter=Q(status='leave'))
            )

            # تحديث التفاصيل
            detail.actual_days = attendance_data['present_days'] + attendance_data['late_days']

            # يمكن إضافة خصومات للتأخير/الغياب
            # detail.absence_deduction = ...

            detail.save()

    def process_loan_deductions(self):
        """معالجة استقطاعات السلف التلقائية"""
        for detail in self.details.all():
            # الحصول على السلف النشطة للموظف
            active_loans = Loan.objects.filter(
                employee=detail.employee,
                company=self.company,
                status='active',
                remaining_amount__gt=0
            )

            for loan in active_loans:
                # التحقق من عدم وجود استقطاع مسبق لنفس السلفة
                if not PayrollLoanDeduction.objects.filter(
                        payroll_detail=detail,
                        loan=loan
                ).exists():
                    # حساب مبلغ القسط
                    installment = min(
                        loan.installment_amount,
                        loan.remaining_amount
                    )

                    # إنشاء الاستقطاع
                    PayrollLoanDeduction.objects.create(
                        payroll_detail=detail,
                        loan=loan,
                        installment_amount=installment
                    )

                    # تسجيل الدفعة
                    LoanPayment.objects.create(
                        loan=loan,
                        payment_date=self.to_date,
                        amount=installment,
                        payment_method='salary',
                        reference=self.number
                    )

    # تعديل submit_for_approval:
    @transaction.atomic
    def submit_for_approval(self, user=None):
        if self.status != 'draft':
            raise ValidationError(_('يمكن تقديم المسودات فقط للموافقة'))

        if not self.details.exists():
            raise ValidationError(_('لا توجد تفاصيل في الكشف'))

        # حساب الحضور
        self.calculate_attendance()

        # 🆕 معالجة استقطاعات السلف
        self.process_loan_deductions()

        # حساب الإجمالي
        self.calculate_totals()

        self.status = 'pending_approval'
        self.save()

    def __str__(self):
        return f"{self.number} - {self.period_month}/{self.period_year}"


class PayrollDetail(models.Model):
    """تفاصيل كشف الرواتب"""

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('كشف الرواتب')
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name=_('الموظف')
    )

    # الراتب الأساسي
    basic_salary = models.DecimalField(
        _('الراتب الأساسي'),
        max_digits=12,
        decimal_places=2
    )

    # أيام العمل
    working_days = models.IntegerField(
        _('أيام العمل'),
        default=30
    )

    actual_days = models.IntegerField(
        _('الأيام الفعلية')
    )

    # البدلات
    total_allowances = models.DecimalField(
        _('مجموع البدلات'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # الاستقطاعات
    total_deductions = models.DecimalField(
        _('مجموع الاستقطاعات'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # الصافي
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
        choices=[
            ('bank', _('تحويل بنكي')),
            ('cash', _('نقدي')),
            ('check', _('شيك')),
        ],
        default='bank'
    )

    payment_reference = models.CharField(
        _('مرجع الدفع'),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _('تفصيل راتب')
        verbose_name_plural = _('تفاصيل الرواتب')
        unique_together = [['payroll', 'employee']]

    def calculate_totals(self):
        """حساب الإجماليات مع استقطاعات السلف"""

        # الاستقطاعات الأساسية
        base_deductions = self.total_deductions

        # استقطاعات السلف
        loan_deductions_total = sum(
            d.installment_amount for d in self.loan_deductions.all()
        )

        # الإجمالي
        self.total_deductions = base_deductions + loan_deductions_total

        # الصافي
        self.net_salary = (
                self.basic_salary +
                self.total_allowances -
                self.total_deductions
        )

        self.save()


class Leave(BaseModel):
    """الإجازات"""

    LEAVE_TYPES = [
        ('annual', _('سنوية')),
        ('sick', _('مرضية')),
        ('emergency', _('طارئة')),
        ('maternity', _('أمومة')),
        ('unpaid', _('بدون راتب')),
        ('other', _('أخرى')),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name=_('الموظف')
    )

    leave_type = models.CharField(
        _('نوع الإجازة'),
        max_length=20,
        choices=LEAVE_TYPES
    )

    from_date = models.DateField(
        _('من تاريخ')
    )

    to_date = models.DateField(
        _('إلى تاريخ')
    )

    days = models.IntegerField(
        _('عدد الأيام'),
        validators=[MinValueValidator(1)]
    )

    reason = models.TextField(
        _('السبب')
    )

    # الموافقات
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('pending', _('معلق')),
            ('approved', _('موافق')),
            ('rejected', _('مرفوض')),
            ('cancelled', _('ملغي')),
        ],
        default='pending'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='approved_leaves'
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

    class Meta:
        verbose_name = _('إجازة')
        verbose_name_plural = _('الإجازات')
        ordering = ['-from_date']


class Attendance(models.Model):
    """الحضور والانصراف"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name=_('الموظف')
    )

    date = models.DateField(
        _('التاريخ')
    )

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

    # الساعات
    work_hours = models.DecimalField(
        _('ساعات العمل'),
        max_digits=4,
        decimal_places=2,
        default=0
    )

    overtime_hours = models.DecimalField(
        _('ساعات إضافية'),
        max_digits=4,
        decimal_places=2,
        default=0
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('present', _('حاضر')),
            ('absent', _('غائب')),
            ('late', _('متأخر')),
            ('leave', _('إجازة')),
            ('holiday', _('عطلة')),
        ],
        default='present'
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('حضور')
        verbose_name_plural = _('الحضور والانصراف')
        unique_together = [['employee', 'date']]
        ordering = ['-date']


class Loan(DocumentBaseModel):
    """السلف والقروض"""

    LOAN_TYPES = [
        ('advance', _('سلفة')),
        ('loan', _('قرض')),
    ]

    number = models.CharField(
        _('رقم السلفة/القرض'),
        max_length=50,
        editable=False
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name=_('الموظف')
    )

    loan_type = models.CharField(
        _('النوع'),
        max_length=10,
        choices=LOAN_TYPES
    )

    date = models.DateField(
        _('التاريخ')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # السداد
    installments = models.IntegerField(
        _('عدد الأقساط'),
        default=1,
        validators=[MinValueValidator(1)]
    )

    installment_amount = models.DecimalField(
        _('قيمة القسط'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    start_date = models.DateField(
        _('تاريخ بداية السداد')
    )

    # المدفوع
    paid_amount = models.DecimalField(
        _('المبلغ المسدد'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    remaining_amount = models.DecimalField(
        _('المبلغ المتبقي'),
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=[
            ('pending', _('معلق')),
            ('approved', _('معتمد')),
            ('active', _('نشط')),
            ('completed', _('مسدد')),
            ('cancelled', _('ملغي')),
        ],
        default='pending'
    )

    # الموافقات
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('اعتمد بواسطة'),
        related_name='approved_loans'
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # القيد المحاسبي
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    reason = models.TextField(
        _('السبب')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سلفة/قرض')
        verbose_name_plural = _('السلف والقروض')
        unique_together = [['company', 'number']]
        ordering = ['-date']

    def save(self, *args, **kwargs):
        """توليد الرقم وحساب القسط"""
        if not self.number:
            prefix = 'ADV' if self.loan_type == 'advance' else 'LOAN'
            year = self.date.strftime('%Y')

            last_loan = Loan.objects.filter(
                company=self.company,
                loan_type=self.loan_type,
                number__startswith=f"{prefix}/{year}/"
            ).order_by('-number').first()

            if last_loan:
                last_number = int(last_loan.number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.number = f"{prefix}/{year}/{new_number:04d}"

        # حساب القسط
        if self.installments > 0:
            self.installment_amount = self.amount / self.installments

        # حساب المتبقي
        self.remaining_amount = self.amount - self.paid_amount

        super().save(*args, **kwargs)

    # إضافة دالة الترحيل:
    @transaction.atomic
    def post(self, user=None):
        """ترحيل السلفة/القرض وإنشاء القيد المحاسبي"""
        from django.utils import timezone
        from apps.accounting.models import JournalEntry, JournalEntryLine, Account

        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد السلفة أولاً'))

        if self.journal_entry:
            raise ValidationError(_('السلفة مرحلة مسبقاً'))

        # الحصول على السنة والفترة المالية
        from apps.accounting.models import FiscalYear, AccountingPeriod

        try:
            fiscal_year = FiscalYear.objects.get(
                company=self.company,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except FiscalYear.DoesNotExist:
            raise ValidationError(_('لا توجد سنة مالية نشطة'))

        try:
            period = AccountingPeriod.objects.get(
                fiscal_year=fiscal_year,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_closed=False
            )
        except AccountingPeriod.DoesNotExist:
            period = None

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',
            description=f"{self.get_loan_type_display()} رقم {self.number} - {self.employee.get_full_name()}",
            reference=self.number,
            source_document='loan',
            source_id=self.pk,
            created_by=user or self.created_by
        )

        line_number = 1

        # حساب سلف الموظفين (مدين)
        try:
            employee_loan_account = Account.objects.get(
                company=self.company,
                code='120300'  # مثال: حساب سلف الموظفين
            )
        except Account.DoesNotExist:
            raise ValidationError(_('حساب سلف الموظفين غير موجود'))

        # سطر السلفة (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=employee_loan_account,
            description=f"{self.get_loan_type_display()} - {self.employee.get_full_name()}",
            debit_amount=self.amount,
            credit_amount=0,
            currency=self.company.base_currency,
            reference=self.number
        )
        line_number += 1

        # حساب الصندوق (دائن)
        try:
            cash_account = Account.objects.get(
                company=self.company,
                code='110100'  # مثال: حساب الصندوق
            )
        except Account.DoesNotExist:
            raise ValidationError(_('حساب الصندوق غير موجود'))

        # سطر الصندوق (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=cash_account,
            description=f"صرف {self.get_loan_type_display()} - {self.employee.get_full_name()}",
            debit_amount=0,
            credit_amount=self.amount,
            currency=self.company.base_currency,
            reference=self.number
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث السلفة
        self.journal_entry = journal_entry
        self.status = 'active'
        self.save()

        return journal_entry

    def __str__(self):
        return f"{self.number} - {self.employee.get_full_name()}"


class LoanPayment(models.Model):
    """سداد السلف والقروض"""

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('السلفة/القرض')
    )

    payment_date = models.DateField(
        _('تاريخ السداد')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    payment_method = models.CharField(
        _('طريقة السداد'),
        max_length=20,
        choices=[
            ('salary', _('خصم من الراتب')),
            ('cash', _('نقدي')),
            ('bank', _('تحويل بنكي')),
        ],
        default='salary'
    )

    reference = models.CharField(
        _('المرجع'),
        max_length=100,
        blank=True,
        help_text=_('رقم كشف الراتب أو رقم الإيصال')
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('سداد سلفة/قرض')
        verbose_name_plural = _('سدادات السلف والقروض')
        ordering = ['-payment_date']

    def save(self, *args, **kwargs):
        """تحديث المبلغ المسدد في السلفة"""
        super().save(*args, **kwargs)

        # تحديث إجمالي المدفوع
        total_paid = self.loan.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        self.loan.paid_amount = total_paid
        self.loan.save()


class PayrollLoanDeduction(models.Model):
    """استقطاعات السلف من كشف الراتب"""

    payroll_detail = models.ForeignKey(
        PayrollDetail,
        on_delete=models.CASCADE,
        related_name='loan_deductions',
        verbose_name=_('تفصيل الراتب')
    )

    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name='payroll_deductions',
        verbose_name=_('السلفة/القرض')
    )

    installment_amount = models.DecimalField(
        _('مبلغ القسط'),
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        verbose_name = _('استقطاع سلفة من راتب')
        verbose_name_plural = _('استقطاعات السلف من الرواتب')
        unique_together = [['payroll_detail', 'loan']]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # تحديث total_deductions في PayrollDetail
        self.payroll_detail.calculate_totals()
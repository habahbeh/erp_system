# apps/hr/models/employee_models.py
"""
نماذج الموظفين - Employee Models
- Employee: بيانات الموظف الأساسية
- EmployeeDocument: مستندات الموظف
- EmployeeSalaryStructure: هيكل راتب الموظف (14 مكون)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from apps.core.models import BaseModel, Currency, Branch


class Employee(BaseModel):
    """
    نموذج الموظف - Employee Model
    يحتوي على جميع البيانات الأساسية للموظف
    """

    # === الثوابت ===
    GENDER_CHOICES = [
        ('male', _('ذكر')),
        ('female', _('أنثى')),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', _('أعزب')),
        ('married', _('متزوج')),
        ('divorced', _('مطلق')),
        ('widowed', _('أرمل')),
    ]

    STATUS_CHOICES = [
        ('active', _('نشط')),
        ('inactive', _('غير نشط')),
        ('terminated', _('مفصول')),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ('full_time', _('دوام كامل')),
        ('part_time', _('دوام جزئي')),
        ('contract', _('عقد مؤقت')),
    ]

    NATIONALITY_CHOICES = [
        ('jordanian', _('أردني')),
        ('palestinian', _('فلسطيني')),
        ('syrian', _('سوري')),
        ('iraqi', _('عراقي')),
        ('egyptian', _('مصري')),
        ('lebanese', _('لبناني')),
        ('saudi', _('سعودي')),
        ('other', _('أخرى')),
    ]

    # === رقم الموظف ===
    employee_number = models.CharField(
        _('رقم الموظف'),
        max_length=20,
        editable=False,
        help_text=_('يتم توليده تلقائياً')
    )

    # === ربط بحساب المستخدم (اختياري) ===
    user = models.OneToOneField(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile',
        verbose_name=_('حساب المستخدم')
    )

    # ======================================
    # البيانات الشخصية - Personal Information
    # ======================================
    first_name = models.CharField(
        _('الاسم الأول'),
        max_length=50
    )

    middle_name = models.CharField(
        _('اسم الأب'),
        max_length=50,
        blank=True
    )

    last_name = models.CharField(
        _('اسم العائلة'),
        max_length=50
    )

    full_name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=150,
        blank=True
    )

    date_of_birth = models.DateField(
        _('تاريخ الميلاد'),
        null=True,
        blank=True
    )

    nationality = models.CharField(
        _('الجنسية'),
        max_length=20,
        choices=NATIONALITY_CHOICES,
        default='jordanian',
        blank=True
    )

    national_id = models.CharField(
        _('الرقم الوطني'),
        max_length=20,
        help_text=_('الرقم الوطني أو رقم جواز السفر')
    )

    gender = models.CharField(
        _('الجنس'),
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    marital_status = models.CharField(
        _('الحالة الاجتماعية'),
        max_length=15,
        choices=MARITAL_STATUS_CHOICES,
        default='single',
        blank=True
    )

    # ======================================
    # معلومات الاتصال - Contact Information
    # ======================================
    mobile = models.CharField(
        _('رقم الموبايل'),
        max_length=20
    )

    phone = models.CharField(
        _('رقم الهاتف'),
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

    # ======================================
    # معلومات التوظيف - Employment Information
    # ======================================
    hire_date = models.DateField(
        _('تاريخ التعيين')
    )

    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('القسم/الإدارة')
    )

    job_title = models.ForeignKey(
        'hr.JobTitle',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('المسمى الوظيفي')
    )

    job_grade = models.ForeignKey(
        'hr.JobGrade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الدرجة الوظيفية')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('الفرع/المدينة')
    )

    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name=_('المدير المباشر')
    )

    social_security_number = models.CharField(
        _('رقم الضمان الاجتماعي'),
        max_length=20,
        blank=True
    )

    employment_status = models.CharField(
        _('حالة التوظيف'),
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='full_time'
    )

    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=STATUS_CHOICES,
        default='active'
    )

    termination_date = models.DateField(
        _('تاريخ إنهاء الخدمة'),
        null=True,
        blank=True
    )

    termination_reason = models.TextField(
        _('سبب إنهاء الخدمة'),
        blank=True
    )

    # ======================================
    # الراتب والمزايا - Salary & Benefits
    # (المكونات الـ 7 للاستحقاقات الثابتة)
    # ======================================

    # 1. الراتب الأساسي
    basic_salary = models.DecimalField(
        _('الراتب الأساسي'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المكون 1: الراتب الأساسي الشهري')
    )

    # 2. بدل الوقود
    fuel_allowance = models.DecimalField(
        _('بدل الوقود'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المكون 2: بدل الوقود الشهري')
    )

    # 3. بدلات أخرى
    other_allowances = models.DecimalField(
        _('بدلات أخرى'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المكون 3: بدلات إضافية أخرى')
    )

    # 4. راتب الضمان
    social_security_salary = models.DecimalField(
        _('راتب الضمان'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('المكون 4: الراتب المسجل في الضمان الاجتماعي')
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('العملة')
    )

    # ======================================
    # إعدادات ساعات العمل
    # ======================================
    working_hours_per_day = models.DecimalField(
        _('ساعات العمل اليومية'),
        max_digits=4,
        decimal_places=2,
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        help_text=_('عدد ساعات العمل اليومية')
    )

    working_days_per_month = models.PositiveSmallIntegerField(
        _('أيام العمل الشهرية'),
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_('عدد أيام العمل في الشهر')
    )

    # ======================================
    # أرصدة الإجازات
    # ======================================
    annual_leave_balance = models.DecimalField(
        _('رصيد الإجازات السنوية'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('الرصيد المتبقي من الإجازات السنوية')
    )

    sick_leave_balance = models.DecimalField(
        _('رصيد الإجازات المرضية'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('الرصيد المتبقي من الإجازات المرضية')
    )

    # ======================================
    # معلومات البنك - Bank Information
    # ======================================
    bank_name = models.CharField(
        _('اسم البنك'),
        max_length=100,
        blank=True
    )

    bank_branch = models.CharField(
        _('فرع البنك'),
        max_length=100,
        blank=True
    )

    bank_account = models.CharField(
        _('رقم الحساب البنكي'),
        max_length=50,
        blank=True
    )

    iban = models.CharField(
        _('رقم IBAN'),
        max_length=50,
        blank=True
    )

    # ======================================
    # معلومات إضافية
    # ======================================
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
        unique_together = [
            ['company', 'employee_number'],
            ['company', 'national_id']
        ]
        ordering = ['employee_number']
        indexes = [
            models.Index(fields=['employee_number']),
            models.Index(fields=['national_id']),
            models.Index(fields=['status']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['hire_date']),
        ]

    # === Properties ===
    @property
    def full_name(self):
        """الاسم الكامل"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)

    @property
    def age(self):
        """العمر"""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def years_of_service(self):
        """سنوات الخدمة"""
        end_date = self.termination_date or date.today()
        delta = end_date - self.hire_date
        return round(delta.days / 365.25, 2)

    @property
    def hourly_rate(self):
        """معدل الساعة = الراتب الأساسي / (أيام الشهر × ساعات اليوم)"""
        if self.working_days_per_month and self.working_hours_per_day:
            total_hours = self.working_days_per_month * self.working_hours_per_day
            if total_hours > 0:
                return self.basic_salary / Decimal(str(total_hours))
        return Decimal('0')

    @property
    def total_fixed_earnings(self):
        """مجموع الاستحقاقات الثابتة"""
        return self.basic_salary + self.fuel_allowance + self.other_allowances

    # === Methods ===
    def save(self, *args, **kwargs):
        """توليد رقم الموظف تلقائياً"""
        if not self.employee_number:
            self.employee_number = self.generate_employee_number()

        self.full_clean()
        super().save(*args, **kwargs)

    def generate_employee_number(self):
        """توليد رقم موظف جديد"""
        from apps.core.models import NumberingSequence
        try:
            sequence = NumberingSequence.objects.get(
                company=self.company,
                document_type='employee'
            )
            return sequence.get_next_number()
        except NumberingSequence.DoesNotExist:
            # Fallback: توليد رقم بسيط
            last_emp = Employee.objects.filter(
                company=self.company
            ).order_by('-id').first()

            if last_emp and last_emp.employee_number:
                try:
                    last_num = int(last_emp.employee_number.replace('EMP', ''))
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1

            return f"EMP{new_num:04d}"

    def clean(self):
        """التحقق من صحة البيانات"""
        # التحقق من تاريخ التعيين
        if self.hire_date and self.hire_date > date.today():
            raise ValidationError({
                'hire_date': _('تاريخ التعيين لا يمكن أن يكون في المستقبل')
            })

        # التحقق من تاريخ إنهاء الخدمة
        if self.termination_date:
            if self.termination_date < self.hire_date:
                raise ValidationError({
                    'termination_date': _('تاريخ إنهاء الخدمة يجب أن يكون بعد تاريخ التعيين')
                })

        # التحقق من راتب الضمان
        if self.social_security_salary > self.basic_salary:
            raise ValidationError({
                'social_security_salary': _('راتب الضمان لا يمكن أن يتجاوز الراتب الأساسي')
            })

    def can_edit(self):
        """هل يمكن تعديل بيانات الموظف"""
        return self.status != 'terminated'

    def terminate(self, termination_date=None, reason=''):
        """إنهاء خدمة الموظف"""
        self.status = 'terminated'
        self.termination_date = termination_date or date.today()
        self.termination_reason = reason
        self.save()

    def reinstate(self):
        """إعادة تفعيل الموظف"""
        self.status = 'active'
        self.termination_date = None
        self.termination_reason = ''
        self.save()

    def get_active_advances(self):
        """الحصول على السلف النشطة"""
        return self.advances.filter(
            status='active',
            remaining_amount__gt=0
        )

    def get_pending_leave_requests(self):
        """الحصول على طلبات الإجازة المعلقة"""
        return self.leave_requests.filter(status='pending')

    def __str__(self):
        return f"{self.employee_number} - {self.full_name}"


class EmployeeDocument(BaseModel):
    """
    مستندات الموظف - Employee Documents
    لحفظ الوثائق والشهادات
    """

    DOCUMENT_TYPES = [
        ('id_card', _('بطاقة هوية')),
        ('passport', _('جواز سفر')),
        ('cv', _('السيرة الذاتية')),
        ('certificate', _('شهادة')),
        ('contract', _('عقد عمل')),
        ('medical', _('تقرير طبي')),
        ('license', _('رخصة')),
        ('other', _('أخرى')),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('الموظف')
    )

    document_type = models.CharField(
        _('نوع المستند'),
        max_length=20,
        choices=DOCUMENT_TYPES
    )

    name = models.CharField(
        _('اسم المستند'),
        max_length=100
    )

    document_number = models.CharField(
        _('رقم المستند'),
        max_length=50,
        blank=True
    )

    issue_date = models.DateField(
        _('تاريخ الإصدار'),
        null=True,
        blank=True
    )

    expiry_date = models.DateField(
        _('تاريخ الانتهاء'),
        null=True,
        blank=True
    )

    file = models.FileField(
        _('الملف'),
        upload_to='employees/documents/',
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('مستند موظف')
        verbose_name_plural = _('مستندات الموظفين')
        ordering = ['-issue_date']

    @property
    def is_expired(self):
        """هل المستند منتهي الصلاحية"""
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False

    @property
    def days_until_expiry(self):
        """عدد الأيام حتى انتهاء الصلاحية"""
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    def __str__(self):
        return f"{self.employee.full_name} - {self.name}"

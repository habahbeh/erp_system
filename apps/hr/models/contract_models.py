# apps/hr/models/contract_models.py
"""
نماذج العقود والعلاوات - Contract Models
- EmployeeContract: عقد العمل
- SalaryIncrement: العلاوات
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from apps.core.models import BaseModel


class EmployeeContract(BaseModel):
    """
    عقد العمل - Employee Contract
    لتتبع عقود الموظفين وتجديداتها
    """

    CONTRACT_TYPES = [
        ('fixed_term', _('محدد المدة')),
        ('indefinite', _('غير محدد المدة')),
        ('temporary', _('عقد مؤقت')),
        ('probation', _('تحت التجربة')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('active', _('نشط')),
        ('expired', _('منتهي')),
        ('terminated', _('ملغي')),
        ('renewed', _('مُجدد')),
    ]

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name=_('الموظف')
    )

    contract_number = models.CharField(
        _('رقم العقد'),
        max_length=50,
        blank=True,
        help_text=_('يتم توليده تلقائياً')
    )

    contract_type = models.CharField(
        _('نوع العقد'),
        max_length=20,
        choices=CONTRACT_TYPES,
        default='fixed_term'
    )

    # === تواريخ العقد ===
    start_date = models.DateField(
        _('تاريخ بداية العقد')
    )

    end_date = models.DateField(
        _('تاريخ نهاية العقد'),
        null=True,
        blank=True,
        help_text=_('اتركه فارغاً للعقود غير محددة المدة')
    )

    # === الراتب في العقد ===
    contract_salary = models.DecimalField(
        _('راتب العقد'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('الراتب المتفق عليه في العقد')
    )

    # === معلومات إضافية ===
    probation_period = models.PositiveSmallIntegerField(
        _('فترة التجربة (بالأيام)'),
        default=90,
        help_text=_('فترة التجربة بالأيام')
    )

    notice_period = models.PositiveSmallIntegerField(
        _('فترة الإشعار (بالأيام)'),
        default=30,
        help_text=_('فترة الإشعار قبل إنهاء العقد')
    )

    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # === الملفات ===
    contract_file = models.FileField(
        _('ملف العقد'),
        upload_to='employees/contracts/',
        blank=True
    )

    # === ملاحظات ===
    terms_and_conditions = models.TextField(
        _('الشروط والأحكام'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    # === سجل التعديل ===
    signed_date = models.DateField(
        _('تاريخ التوقيع'),
        null=True,
        blank=True
    )

    signed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_contracts',
        verbose_name=_('وقع بواسطة')
    )

    class Meta:
        verbose_name = _('عقد عمل')
        verbose_name_plural = _('عقود العمل')
        unique_together = [['company', 'contract_number']]
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def save(self, *args, **kwargs):
        """توليد رقم العقد تلقائياً"""
        if not self.contract_number:
            year = self.start_date.strftime('%Y')
            last_contract = EmployeeContract.objects.filter(
                company=self.company,
                contract_number__startswith=f"CTR/{year}/"
            ).order_by('-contract_number').first()

            if last_contract:
                try:
                    last_num = int(last_contract.contract_number.split('/')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1

            self.contract_number = f"CTR/{year}/{new_num:04d}"

        super().save(*args, **kwargs)

    def clean(self):
        """التحقق من صحة البيانات"""
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('تاريخ نهاية العقد يجب أن يكون بعد تاريخ البداية')
            })

    @property
    def is_expired(self):
        """هل العقد منتهي"""
        if self.end_date:
            return self.end_date < date.today()
        return False

    @property
    def days_until_expiry(self):
        """عدد الأيام حتى انتهاء العقد"""
        if self.end_date:
            delta = self.end_date - date.today()
            return delta.days
        return None

    @property
    def is_in_probation(self):
        """هل الموظف تحت التجربة"""
        if self.probation_period:
            from datetime import timedelta
            probation_end = self.start_date + timedelta(days=self.probation_period)
            return date.today() < probation_end
        return False

    @transaction.atomic
    def activate(self, user=None):
        """تفعيل العقد"""
        if self.status != 'draft':
            raise ValidationError(_('يمكن تفعيل المسودات فقط'))

        # إلغاء العقود النشطة السابقة
        EmployeeContract.objects.filter(
            employee=self.employee,
            status='active'
        ).update(status='expired')

        self.status = 'active'
        self.save()

        # تحديث راتب الموظف
        self.employee.basic_salary = self.contract_salary
        self.employee.save()

    @transaction.atomic
    def renew(self, new_end_date, new_salary=None, user=None):
        """تجديد العقد"""
        if self.status != 'active':
            raise ValidationError(_('يمكن تجديد العقود النشطة فقط'))

        # إنشاء عقد جديد
        new_contract = EmployeeContract.objects.create(
            company=self.company,
            employee=self.employee,
            contract_type=self.contract_type,
            start_date=self.end_date or date.today(),
            end_date=new_end_date,
            contract_salary=new_salary or self.contract_salary,
            probation_period=0,  # لا تجربة عند التجديد
            notice_period=self.notice_period,
            status='active',
            created_by=user
        )

        # تحديث العقد القديم
        self.status = 'renewed'
        self.save()

        # تحديث راتب الموظف إذا تغير
        if new_salary:
            self.employee.basic_salary = new_salary
            self.employee.save()

        return new_contract

    def __str__(self):
        return f"{self.contract_number} - {self.employee.full_name}"


class SalaryIncrement(BaseModel):
    """
    العلاوات - Salary Increments
    لتتبع العلاوات والزيادات على الراتب
    """

    INCREMENT_TYPES = [
        ('annual', _('علاوة سنوية')),
        ('promotion', _('ترقية')),
        ('merit', _('علاوة تميز')),
        ('adjustment', _('تعديل راتب')),
        ('cost_of_living', _('بدل غلاء معيشة')),
        ('other', _('أخرى')),
    ]

    STATUS_CHOICES = [
        ('pending', _('معلق')),
        ('approved', _('معتمد')),
        ('applied', _('مطبق')),
        ('rejected', _('مرفوض')),
    ]

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='salary_increments',
        verbose_name=_('الموظف')
    )

    increment_type = models.CharField(
        _('نوع العلاوة'),
        max_length=20,
        choices=INCREMENT_TYPES,
        default='annual'
    )

    # === المبالغ ===
    old_salary = models.DecimalField(
        _('الراتب القديم'),
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    # طريقة الزيادة: مبلغ ثابت أو نسبة
    is_percentage = models.BooleanField(
        _('نسبة مئوية'),
        default=False,
        help_text=_('اختر إذا كانت الزيادة نسبة من الراتب')
    )

    increment_amount = models.DecimalField(
        _('قيمة العلاوة'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('المبلغ أو النسبة حسب الاختيار')
    )

    new_salary = models.DecimalField(
        _('الراتب الجديد'),
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    # === التواريخ ===
    effective_date = models.DateField(
        _('تاريخ السريان')
    )

    # === الموافقات ===
    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_increments',
        verbose_name=_('اعتمد بواسطة')
    )

    approval_date = models.DateTimeField(
        _('تاريخ الاعتماد'),
        null=True,
        blank=True
    )

    # === ملاحظات ===
    reason = models.TextField(
        _('السبب'),
        blank=True
    )

    notes = models.TextField(
        _('ملاحظات'),
        blank=True
    )

    class Meta:
        verbose_name = _('علاوة')
        verbose_name_plural = _('العلاوات')
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['effective_date']),
        ]

    def save(self, *args, **kwargs):
        """حساب الراتب الجديد"""
        # حفظ الراتب القديم
        if not self.pk:
            self.old_salary = self.employee.basic_salary

        # حساب الراتب الجديد
        if self.is_percentage:
            # الزيادة نسبة مئوية
            increment_value = self.old_salary * (self.increment_amount / 100)
        else:
            # الزيادة مبلغ ثابت
            increment_value = self.increment_amount

        self.new_salary = self.old_salary + increment_value

        super().save(*args, **kwargs)

    @transaction.atomic
    def approve(self, user):
        """اعتماد العلاوة"""
        from django.utils import timezone

        if self.status != 'pending':
            raise ValidationError(_('العلاوة ليست معلقة'))

        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    @transaction.atomic
    def apply_increment(self, user=None):
        """تطبيق العلاوة على راتب الموظف"""
        if self.status != 'approved':
            raise ValidationError(_('يجب اعتماد العلاوة أولاً'))

        if self.effective_date > date.today():
            raise ValidationError(_('تاريخ سريان العلاوة لم يحن بعد'))

        # تحديث راتب الموظف
        self.employee.basic_salary = self.new_salary
        self.employee.save()

        # تحديث حالة العلاوة
        self.status = 'applied'
        self.save()

    @transaction.atomic
    def reject(self, user, reason=''):
        """رفض العلاوة"""
        if self.status != 'pending':
            raise ValidationError(_('العلاوة ليست معلقة'))

        self.status = 'rejected'
        self.notes = reason
        self.save()

    @property
    def increment_percentage(self):
        """نسبة الزيادة"""
        if self.old_salary and self.old_salary > 0:
            increase = self.new_salary - self.old_salary
            return (increase / self.old_salary) * 100
        return 0

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_increment_type_display()} - {self.effective_date}"

# apps/hr/models/organization_models.py
"""
نماذج الهيكل التنظيمي - Organization Models
- Department: الأقسام
- JobTitle: المسميات الوظيفية
- JobGrade: الدرجات الوظيفية
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class Department(BaseModel):
    """
    الأقسام - Departments
    يدعم الهيكل الهرمي متعدد المستويات
    """

    code = models.CharField(
        _('رمز القسم'),
        max_length=20,
        help_text=_('رمز فريد للقسم')
    )

    name = models.CharField(
        _('اسم القسم'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
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
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('مدير القسم')
    )

    # ربط بمركز التكلفة للمحاسبة
    cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('مركز التكلفة')
    )

    level = models.PositiveSmallIntegerField(
        _('المستوى'),
        default=1,
        help_text=_('مستوى القسم في الهيكل التنظيمي')
    )

    description = models.TextField(
        _('الوصف'),
        blank=True
    )

    class Meta:
        verbose_name = _('قسم')
        verbose_name_plural = _('الأقسام')
        unique_together = [['company', 'code']]
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['company', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        """حساب المستوى تلقائياً"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

    @property
    def full_path(self):
        """المسار الكامل للقسم"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def employees_count(self):
        """عدد موظفي القسم"""
        return self.employees.filter(
            employment_status='active'
        ).count()

    def get_all_children(self):
        """الحصول على جميع الأقسام الفرعية"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children

    def __str__(self):
        return f"{self.code} - {self.name}"


class JobGrade(BaseModel):
    """
    الدرجات الوظيفية - Job Grades
    لتصنيف الموظفين حسب المستوى الوظيفي
    """

    code = models.CharField(
        _('رمز الدرجة'),
        max_length=20
    )

    name = models.CharField(
        _('اسم الدرجة'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
    )

    level = models.PositiveSmallIntegerField(
        _('المستوى'),
        default=1,
        help_text=_('ترتيب الدرجة (1 = الأعلى)')
    )

    # نطاق الراتب
    min_salary = models.DecimalField(
        _('الحد الأدنى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    max_salary = models.DecimalField(
        _('الحد الأعلى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # رصيد الإجازات
    annual_leave_days = models.PositiveSmallIntegerField(
        _('أيام الإجازة السنوية'),
        default=14
    )

    sick_leave_days = models.PositiveSmallIntegerField(
        _('أيام الإجازة المرضية'),
        default=14
    )

    description = models.TextField(
        _('الوصف'),
        blank=True
    )

    class Meta:
        verbose_name = _('درجة وظيفية')
        verbose_name_plural = _('الدرجات الوظيفية')
        unique_together = [['company', 'code']]
        ordering = ['level', 'code']
        indexes = [
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class JobTitle(BaseModel):
    """
    المسميات الوظيفية - Job Titles
    """

    code = models.CharField(
        _('رمز الوظيفة'),
        max_length=20
    )

    name = models.CharField(
        _('المسمى الوظيفي'),
        max_length=100
    )

    name_en = models.CharField(
        _('الاسم بالإنجليزية'),
        max_length=100,
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_titles',
        verbose_name=_('القسم')
    )

    job_grade = models.ForeignKey(
        JobGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_titles',
        verbose_name=_('الدرجة الوظيفية')
    )

    # نطاق الراتب للوظيفة
    min_salary = models.DecimalField(
        _('الحد الأدنى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    max_salary = models.DecimalField(
        _('الحد الأعلى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    description = models.TextField(
        _('الوصف الوظيفي'),
        blank=True
    )

    responsibilities = models.TextField(
        _('المسؤوليات'),
        blank=True
    )

    requirements = models.TextField(
        _('متطلبات الوظيفة'),
        blank=True
    )

    class Meta:
        verbose_name = _('مسمى وظيفي')
        verbose_name_plural = _('المسميات الوظيفية')
        unique_together = [['company', 'code']]
        ordering = ['code']
        indexes = [
            models.Index(fields=['department']),
        ]

    @property
    def employees_count(self):
        """عدد الموظفين بهذا المسمى"""
        return self.employees.filter(
            employment_status='active'
        ).count()

    def __str__(self):
        return self.name

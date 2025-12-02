# apps/hr/models/performance_models.py
"""
نماذج التقييم والأداء - المرحلة 5
Performance & Evaluation Models - Phase 5
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class PerformancePeriod(models.Model):
    """فترة التقييم"""
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
    ]

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('active', 'نشطة'),
        ('closed', 'مغلقة'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='performance_periods',
        verbose_name=_('الشركة')
    )
    name = models.CharField(max_length=100, verbose_name=_('اسم الفترة'))
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPE_CHOICES,
        default='annual',
        verbose_name=_('نوع الفترة')
    )
    year = models.PositiveIntegerField(verbose_name=_('السنة'))
    start_date = models.DateField(verbose_name=_('تاريخ البداية'))
    end_date = models.DateField(verbose_name=_('تاريخ النهاية'))
    evaluation_start = models.DateField(
        blank=True, null=True,
        verbose_name=_('بداية فترة التقييم'),
        help_text=_('تاريخ بدء إدخال التقييمات')
    )
    evaluation_end = models.DateField(
        blank=True, null=True,
        verbose_name=_('نهاية فترة التقييم'),
        help_text=_('آخر تاريخ لإدخال التقييمات')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_performance_periods',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('فترة تقييم')
        verbose_name_plural = _('فترات التقييم')
        ordering = ['-year', '-start_date']
        unique_together = ['company', 'name', 'year']

    def __str__(self):
        return f"{self.name} - {self.year}"


class PerformanceCriteria(models.Model):
    """معايير التقييم"""
    CRITERIA_TYPE_CHOICES = [
        ('competency', 'كفاءات'),
        ('objective', 'أهداف'),
        ('behavior', 'سلوكيات'),
        ('skill', 'مهارات'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='performance_criteria',
        verbose_name=_('الشركة')
    )
    name = models.CharField(max_length=200, verbose_name=_('المعيار'))
    name_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('المعيار بالإنجليزية')
    )
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    criteria_type = models.CharField(
        max_length=20,
        choices=CRITERIA_TYPE_CHOICES,
        default='competency',
        verbose_name=_('نوع المعيار')
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('الوزن'),
        help_text=_('وزن المعيار في التقييم الإجمالي')
    )
    max_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('5.00'),
        verbose_name=_('أعلى درجة')
    )
    is_required = models.BooleanField(default=True, verbose_name=_('إلزامي'))
    applies_to_all = models.BooleanField(
        default=True,
        verbose_name=_('ينطبق على الجميع'),
        help_text=_('هل ينطبق على جميع الموظفين أم أقسام محددة')
    )
    departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='performance_criteria',
        verbose_name=_('الأقسام'),
        help_text=_('الأقسام التي ينطبق عليها المعيار (إذا لم يكن للجميع)')
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name=_('ترتيب العرض'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('معيار تقييم')
        verbose_name_plural = _('معايير التقييم')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class PerformanceEvaluation(models.Model):
    """تقييم أداء الموظف"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('self_evaluation', 'تقييم ذاتي'),
        ('manager_evaluation', 'تقييم المدير'),
        ('pending_approval', 'بانتظار الموافقة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='performance_evaluations',
        verbose_name=_('الشركة')
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='performance_evaluations',
        verbose_name=_('الموظف')
    )
    period = models.ForeignKey(
        PerformancePeriod,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_('فترة التقييم')
    )
    evaluator = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evaluations_given',
        verbose_name=_('المقيّم')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )

    # درجات التقييم
    self_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('التقييم الذاتي')
    )
    manager_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('تقييم المدير')
    )
    final_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('الدرجة النهائية')
    )
    grade = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('التقدير'),
        help_text=_('ممتاز، جيد جداً، جيد، مقبول، ضعيف')
    )

    # التعليقات
    self_comments = models.TextField(
        blank=True,
        verbose_name=_('تعليقات الموظف')
    )
    manager_comments = models.TextField(
        blank=True,
        verbose_name=_('تعليقات المدير')
    )
    improvement_areas = models.TextField(
        blank=True,
        verbose_name=_('مجالات التحسين')
    )
    strengths = models.TextField(
        blank=True,
        verbose_name=_('نقاط القوة')
    )
    goals_next_period = models.TextField(
        blank=True,
        verbose_name=_('أهداف الفترة القادمة')
    )

    # التواريخ
    self_evaluation_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ التقييم الذاتي')
    )
    manager_evaluation_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ تقييم المدير')
    )
    approval_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ الاعتماد')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_evaluations',
        verbose_name=_('اعتمد بواسطة')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_evaluations',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('تقييم أداء')
        verbose_name_plural = _('تقييمات الأداء')
        ordering = ['-period__year', 'employee__first_name']
        unique_together = ['employee', 'period']

    def __str__(self):
        return f"{self.employee} - {self.period}"

    def calculate_final_score(self):
        """حساب الدرجة النهائية"""
        details = self.details.all()
        if not details.exists():
            return None

        total_weight = sum(d.criteria.weight for d in details)
        if total_weight == 0:
            return None

        weighted_score = sum(
            (d.final_score or 0) * d.criteria.weight
            for d in details
        )
        return round(weighted_score / total_weight, 2)

    def get_grade(self):
        """الحصول على التقدير بناءً على الدرجة"""
        if not self.final_score:
            return ''

        score = float(self.final_score)
        if score >= 4.5:
            return 'ممتاز'
        elif score >= 3.5:
            return 'جيد جداً'
        elif score >= 2.5:
            return 'جيد'
        elif score >= 1.5:
            return 'مقبول'
        else:
            return 'ضعيف'

    def save(self, *args, **kwargs):
        # حساب الدرجة النهائية تلقائياً
        if self.pk:
            calculated_score = self.calculate_final_score()
            if calculated_score:
                self.final_score = calculated_score
                self.grade = self.get_grade()
        super().save(*args, **kwargs)


class PerformanceEvaluationDetail(models.Model):
    """تفاصيل تقييم الأداء (لكل معيار)"""
    evaluation = models.ForeignKey(
        PerformanceEvaluation,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('التقييم')
    )
    criteria = models.ForeignKey(
        PerformanceCriteria,
        on_delete=models.CASCADE,
        related_name='evaluation_details',
        verbose_name=_('المعيار')
    )
    self_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('التقييم الذاتي')
    )
    manager_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('تقييم المدير')
    )
    final_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('الدرجة النهائية')
    )
    self_comments = models.TextField(blank=True, verbose_name=_('تعليق الموظف'))
    manager_comments = models.TextField(blank=True, verbose_name=_('تعليق المدير'))

    class Meta:
        verbose_name = _('تفصيل تقييم')
        verbose_name_plural = _('تفاصيل التقييم')
        unique_together = ['evaluation', 'criteria']

    def __str__(self):
        return f"{self.evaluation.employee} - {self.criteria.name}"

    def save(self, *args, **kwargs):
        # حساب الدرجة النهائية (متوسط أو تقييم المدير)
        if self.manager_score is not None:
            if self.self_score is not None:
                # متوسط مرجح (70% مدير، 30% ذاتي)
                self.final_score = Decimal('0.7') * self.manager_score + Decimal('0.3') * self.self_score
            else:
                self.final_score = self.manager_score
        elif self.self_score is not None:
            self.final_score = self.self_score
        super().save(*args, **kwargs)


class PerformanceGoal(models.Model):
    """أهداف الأداء"""
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('critical', 'حرجة'),
    ]

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('active', 'نشط'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='performance_goals',
        verbose_name=_('الشركة')
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='performance_goals',
        verbose_name=_('الموظف')
    )
    period = models.ForeignKey(
        PerformancePeriod,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='goals',
        verbose_name=_('فترة التقييم')
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان الهدف'))
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    key_results = models.TextField(
        blank=True,
        verbose_name=_('النتائج الرئيسية'),
        help_text=_('كيف سيتم قياس تحقيق الهدف')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('الأولوية')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('الوزن')
    )
    target_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('القيمة المستهدفة')
    )
    achieved_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('القيمة المحققة')
    )
    progress_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_('نسبة الإنجاز %')
    )
    start_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ البداية'))
    due_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الاستحقاق'))
    completion_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الإنجاز'))
    assigned_by = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_goals',
        verbose_name=_('أسند بواسطة')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('هدف أداء')
        verbose_name_plural = _('أهداف الأداء')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.title}"


class PerformanceNote(models.Model):
    """ملاحظات الأداء المستمرة"""
    NOTE_TYPE_CHOICES = [
        ('achievement', 'إنجاز'),
        ('improvement', 'تحسين مطلوب'),
        ('feedback', 'ملاحظة'),
        ('recognition', 'تقدير'),
        ('warning', 'تحذير'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='performance_notes',
        verbose_name=_('الشركة')
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='performance_notes',
        verbose_name=_('الموظف')
    )
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        default='feedback',
        verbose_name=_('نوع الملاحظة')
    )
    title = models.CharField(max_length=200, verbose_name=_('العنوان'))
    description = models.TextField(verbose_name=_('الوصف'))
    date = models.DateField(verbose_name=_('التاريخ'))
    noted_by = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notes_given',
        verbose_name=_('بواسطة')
    )
    is_visible_to_employee = models.BooleanField(
        default=True,
        verbose_name=_('مرئي للموظف')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_performance_notes',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('ملاحظة أداء')
        verbose_name_plural = _('ملاحظات الأداء')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.employee} - {self.title}"

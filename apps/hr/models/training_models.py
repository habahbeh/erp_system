# apps/hr/models/training_models.py
"""
نماذج التدريب والتطوير - المرحلة 6
Training & Development Models - Phase 6
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class TrainingCategory(models.Model):
    """فئات التدريب"""
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_categories',
        verbose_name=_('الشركة')
    )
    name = models.CharField(max_length=100, verbose_name=_('اسم الفئة'))
    name_en = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('الاسم بالإنجليزية')
    )
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('الفئة الأم')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('فئة تدريب')
        verbose_name_plural = _('فئات التدريب')
        ordering = ['name']

    def __str__(self):
        return self.name


class TrainingProvider(models.Model):
    """مزودي التدريب"""
    PROVIDER_TYPE_CHOICES = [
        ('internal', 'داخلي'),
        ('external', 'خارجي'),
        ('online', 'إلكتروني'),
        ('university', 'جامعة'),
        ('institute', 'معهد'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_providers',
        verbose_name=_('الشركة')
    )
    name = models.CharField(max_length=200, verbose_name=_('اسم المزود'))
    provider_type = models.CharField(
        max_length=20,
        choices=PROVIDER_TYPE_CHOICES,
        default='external',
        verbose_name=_('نوع المزود')
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('جهة الاتصال')
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('الهاتف'))
    email = models.EmailField(blank=True, verbose_name=_('البريد الإلكتروني'))
    website = models.URLField(blank=True, verbose_name=_('الموقع الإلكتروني'))
    address = models.TextField(blank=True, verbose_name=_('العنوان'))
    specializations = models.TextField(
        blank=True,
        verbose_name=_('التخصصات'),
        help_text=_('مجالات التدريب التي يقدمها')
    )
    rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))],
        verbose_name=_('التقييم')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('مزود تدريب')
        verbose_name_plural = _('مزودي التدريب')
        ordering = ['name']

    def __str__(self):
        return self.name


class TrainingCourse(models.Model):
    """الدورات التدريبية"""
    COURSE_TYPE_CHOICES = [
        ('mandatory', 'إلزامي'),
        ('optional', 'اختياري'),
        ('certification', 'شهادة مهنية'),
        ('workshop', 'ورشة عمل'),
        ('seminar', 'ندوة'),
        ('conference', 'مؤتمر'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('classroom', 'حضوري'),
        ('online', 'عن بعد'),
        ('blended', 'مدمج'),
        ('self_paced', 'ذاتي'),
    ]

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('planned', 'مخطط'),
        ('open', 'مفتوح للتسجيل'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_courses',
        verbose_name=_('الشركة')
    )
    code = models.CharField(max_length=50, verbose_name=_('رمز الدورة'))
    name = models.CharField(max_length=200, verbose_name=_('اسم الدورة'))
    name_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('الاسم بالإنجليزية')
    )
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    objectives = models.TextField(
        blank=True,
        verbose_name=_('الأهداف'),
        help_text=_('ما سيتعلمه المتدربون')
    )
    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses',
        verbose_name=_('الفئة')
    )
    provider = models.ForeignKey(
        TrainingProvider,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses',
        verbose_name=_('مزود التدريب')
    )
    course_type = models.CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='optional',
        verbose_name=_('نوع الدورة')
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        default='classroom',
        verbose_name=_('طريقة التدريب')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )
    start_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ البداية'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ النهاية'))
    duration_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('المدة (ساعات)')
    )
    duration_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_('المدة (أيام)')
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('المكان')
    )
    max_participants = models.PositiveIntegerField(
        default=0,
        verbose_name=_('الحد الأقصى للمشاركين'),
        help_text=_('0 يعني بدون حد')
    )
    min_participants = models.PositiveIntegerField(
        default=0,
        verbose_name=_('الحد الأدنى للمشاركين')
    )
    cost_per_participant = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('التكلفة لكل مشارك')
    )
    total_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('الميزانية الكلية')
    )
    trainer_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('اسم المدرب')
    )
    trainer_employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses_as_trainer',
        verbose_name=_('المدرب (موظف)')
    )
    prerequisites = models.TextField(
        blank=True,
        verbose_name=_('المتطلبات السابقة')
    )
    materials = models.TextField(
        blank=True,
        verbose_name=_('المواد التدريبية')
    )
    target_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='targeted_courses',
        verbose_name=_('الأقسام المستهدفة')
    )
    target_job_titles = models.ManyToManyField(
        'hr.JobTitle',
        blank=True,
        related_name='targeted_courses',
        verbose_name=_('المسميات الوظيفية المستهدفة')
    )
    certificate_issued = models.BooleanField(
        default=False,
        verbose_name=_('تصدر شهادة')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_courses',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('دورة تدريبية')
        verbose_name_plural = _('الدورات التدريبية')
        ordering = ['-start_date', 'name']
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def enrolled_count(self):
        """عدد المسجلين"""
        return self.enrollments.filter(status__in=['enrolled', 'attending', 'completed']).count()

    @property
    def available_seats(self):
        """المقاعد المتاحة"""
        if self.max_participants == 0:
            return float('inf')
        return max(0, self.max_participants - self.enrolled_count)


class TrainingEnrollment(models.Model):
    """تسجيل الموظفين في الدورات"""
    STATUS_CHOICES = [
        ('nominated', 'مرشح'),
        ('pending_approval', 'بانتظار الموافقة'),
        ('approved', 'موافق عليه'),
        ('enrolled', 'مسجل'),
        ('attending', 'يحضر'),
        ('completed', 'أكمل'),
        ('no_show', 'لم يحضر'),
        ('withdrawn', 'منسحب'),
        ('failed', 'لم ينجح'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_enrollments',
        verbose_name=_('الشركة')
    )
    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('الدورة')
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='training_enrollments',
        verbose_name=_('الموظف')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='nominated',
        verbose_name=_('الحالة')
    )
    nominated_by = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='nominations_made',
        verbose_name=_('رشح بواسطة')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='training_approvals',
        verbose_name=_('وافق عليه')
    )
    approval_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الموافقة'))
    enrollment_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ التسجيل'))
    completion_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الإكمال'))
    attendance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_('نسبة الحضور %')
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('الدرجة')
    )
    grade = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('التقدير')
    )
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('رقم الشهادة')
    )
    certificate_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ الشهادة')
    )
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('التكلفة الفعلية')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('تسجيل تدريب')
        verbose_name_plural = _('تسجيلات التدريب')
        ordering = ['-created_at']
        unique_together = ['course', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.course}"


class TrainingRequest(models.Model):
    """طلبات التدريب"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending', 'قيد الانتظار'),
        ('manager_approved', 'موافقة المدير'),
        ('hr_approved', 'موافقة الموارد البشرية'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('scheduled', 'تم الجدولة'),
        ('completed', 'مكتمل'),
    ]

    REQUEST_TYPE_CHOICES = [
        ('self', 'طلب ذاتي'),
        ('manager', 'ترشيح من المدير'),
        ('hr', 'من الموارد البشرية'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_requests',
        verbose_name=_('الشركة')
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='training_requests',
        verbose_name=_('الموظف')
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='self',
        verbose_name=_('نوع الطلب')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )
    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='requests',
        verbose_name=_('الدورة المطلوبة')
    )
    custom_course_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('اسم الدورة (إذا غير موجودة)')
    )
    training_category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='requests',
        verbose_name=_('فئة التدريب')
    )
    justification = models.TextField(
        verbose_name=_('مبررات الطلب'),
        help_text=_('لماذا تحتاج هذا التدريب')
    )
    expected_benefits = models.TextField(
        blank=True,
        verbose_name=_('الفوائد المتوقعة')
    )
    preferred_date_from = models.DateField(
        null=True, blank=True,
        verbose_name=_('التاريخ المفضل من')
    )
    preferred_date_to = models.DateField(
        null=True, blank=True,
        verbose_name=_('التاريخ المفضل إلى')
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('التكلفة التقديرية')
    )
    manager_comments = models.TextField(
        blank=True,
        verbose_name=_('ملاحظات المدير')
    )
    hr_comments = models.TextField(
        blank=True,
        verbose_name=_('ملاحظات الموارد البشرية')
    )
    manager_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='training_manager_approvals',
        verbose_name=_('موافقة المدير')
    )
    manager_approved_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ موافقة المدير')
    )
    hr_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='training_hr_approvals',
        verbose_name=_('موافقة HR')
    )
    hr_approved_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاريخ موافقة HR')
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('سبب الرفض')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_training_requests',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('طلب تدريب')
        verbose_name_plural = _('طلبات التدريب')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.course or self.custom_course_name}"


class TrainingPlan(models.Model):
    """خطة التدريب السنوية"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending_approval', 'بانتظار الموافقة'),
        ('approved', 'معتمدة'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='training_plans',
        verbose_name=_('الشركة')
    )
    name = models.CharField(max_length=200, verbose_name=_('اسم الخطة'))
    year = models.PositiveIntegerField(verbose_name=_('السنة'))
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='training_plans',
        verbose_name=_('القسم'),
        help_text=_('اتركه فارغاً للخطة على مستوى الشركة')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )
    total_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('الميزانية الإجمالية')
    )
    allocated_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('الميزانية المخصصة')
    )
    spent_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('الميزانية المصروفة')
    )
    objectives = models.TextField(
        blank=True,
        verbose_name=_('أهداف الخطة')
    )
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_training_plans',
        verbose_name=_('اعتمد بواسطة')
    )
    approved_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الاعتماد'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_training_plans',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('خطة تدريب')
        verbose_name_plural = _('خطط التدريب')
        ordering = ['-year', 'name']
        unique_together = ['company', 'year', 'department']

    def __str__(self):
        dept = f" - {self.department.name}" if self.department else ""
        return f"{self.name} ({self.year}){dept}"


class TrainingPlanItem(models.Model):
    """بنود خطة التدريب"""
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('critical', 'حرجة'),
    ]

    QUARTER_CHOICES = [
        (1, 'الربع الأول'),
        (2, 'الربع الثاني'),
        (3, 'الربع الثالث'),
        (4, 'الربع الرابع'),
    ]

    plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('الخطة')
    )
    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='plan_items',
        verbose_name=_('الدورة')
    )
    custom_course_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('اسم الدورة (إذا غير موجودة)')
    )
    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='plan_items',
        verbose_name=_('الفئة')
    )
    target_employees_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('عدد الموظفين المستهدفين')
    )
    target_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='plan_items',
        verbose_name=_('الأقسام المستهدفة')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('الأولوية')
    )
    planned_quarter = models.PositiveIntegerField(
        choices=QUARTER_CHOICES,
        null=True, blank=True,
        verbose_name=_('الربع المخطط')
    )
    planned_budget = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('الميزانية المخططة')
    )
    actual_budget = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        verbose_name=_('التكلفة الفعلية')
    )
    is_completed = models.BooleanField(default=False, verbose_name=_('مكتمل'))
    notes = models.TextField(blank=True, verbose_name=_('ملاحظات'))

    class Meta:
        verbose_name = _('بند خطة تدريب')
        verbose_name_plural = _('بنود خطط التدريب')
        ordering = ['planned_quarter', '-priority']

    def __str__(self):
        return f"{self.plan} - {self.course or self.custom_course_name}"


class TrainingFeedback(models.Model):
    """تقييم وتغذية راجعة للتدريب"""
    enrollment = models.OneToOneField(
        TrainingEnrollment,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name=_('التسجيل')
    )
    # تقييم الدورة
    content_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('تقييم المحتوى')
    )
    trainer_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('تقييم المدرب')
    )
    materials_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('تقييم المواد التدريبية')
    )
    organization_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('تقييم التنظيم')
    )
    relevance_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('مدى ارتباطه بالعمل')
    )
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name=_('التقييم العام')
    )
    strengths = models.TextField(
        blank=True,
        verbose_name=_('نقاط القوة')
    )
    improvements = models.TextField(
        blank=True,
        verbose_name=_('مقترحات التحسين')
    )
    knowledge_gained = models.TextField(
        blank=True,
        verbose_name=_('المعرفة المكتسبة')
    )
    application_plan = models.TextField(
        blank=True,
        verbose_name=_('خطة التطبيق'),
        help_text=_('كيف ستطبق ما تعلمته في عملك')
    )
    would_recommend = models.BooleanField(
        default=True,
        verbose_name=_('هل توصي بالدورة للآخرين')
    )
    additional_comments = models.TextField(
        blank=True,
        verbose_name=_('تعليقات إضافية')
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('تقييم تدريب')
        verbose_name_plural = _('تقييمات التدريب')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"تقييم: {self.enrollment}"

    @property
    def average_rating(self):
        """متوسط التقييم"""
        ratings = [
            self.content_rating, self.trainer_rating, self.materials_rating,
            self.organization_rating, self.relevance_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return None

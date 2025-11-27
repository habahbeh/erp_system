# apps/hr/migrations/0001_initial.py
# Migration stub to maintain backward compatibility with existing migrations
# This will be replaced with actual model creation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0010_businesspartner_customer_account_and_more'),
        ('accounting', '0005_alter_costcenter_cost_center_type'),
    ]

    operations = [
        # Department Model
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('code', models.CharField(help_text='رمز فريد للقسم', max_length=20, verbose_name='رمز القسم')),
                ('name', models.CharField(max_length=100, verbose_name='اسم القسم')),
                ('name_en', models.CharField(blank=True, max_length=100, verbose_name='الاسم بالإنجليزية')),
                ('level', models.PositiveSmallIntegerField(default=1, help_text='مستوى القسم في الهيكل التنظيمي', verbose_name='المستوى')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='hr.department', verbose_name='القسم الأب')),
                ('cost_center', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.costcenter', verbose_name='مركز التكلفة')),
            ],
            options={
                'verbose_name': 'قسم',
                'verbose_name_plural': 'الأقسام',
                'ordering': ['code'],
            },
        ),

        # JobGrade Model
        migrations.CreateModel(
            name='JobGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('code', models.CharField(max_length=20, verbose_name='رمز الدرجة')),
                ('name', models.CharField(max_length=100, verbose_name='اسم الدرجة')),
                ('name_en', models.CharField(blank=True, max_length=100, verbose_name='الاسم بالإنجليزية')),
                ('level', models.PositiveSmallIntegerField(default=1, help_text='ترتيب الدرجة (1 = الأعلى)', verbose_name='المستوى')),
                ('min_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأدنى للراتب')),
                ('max_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأعلى للراتب')),
                ('annual_leave_days', models.PositiveSmallIntegerField(default=14, verbose_name='أيام الإجازة السنوية')),
                ('sick_leave_days', models.PositiveSmallIntegerField(default=14, verbose_name='أيام الإجازة المرضية')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
            ],
            options={
                'verbose_name': 'درجة وظيفية',
                'verbose_name_plural': 'الدرجات الوظيفية',
                'ordering': ['level', 'code'],
            },
        ),

        # JobTitle Model
        migrations.CreateModel(
            name='JobTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('code', models.CharField(max_length=20, verbose_name='رمز الوظيفة')),
                ('name', models.CharField(max_length=100, verbose_name='المسمى الوظيفي')),
                ('name_en', models.CharField(blank=True, max_length=100, verbose_name='الاسم بالإنجليزية')),
                ('min_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأدنى للراتب')),
                ('max_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأعلى للراتب')),
                ('description', models.TextField(blank=True, verbose_name='الوصف الوظيفي')),
                ('responsibilities', models.TextField(blank=True, verbose_name='المسؤوليات')),
                ('requirements', models.TextField(blank=True, verbose_name='متطلبات الوظيفة')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_titles', to='hr.department', verbose_name='القسم')),
                ('job_grade', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_titles', to='hr.jobgrade', verbose_name='الدرجة الوظيفية')),
            ],
            options={
                'verbose_name': 'مسمى وظيفي',
                'verbose_name_plural': 'المسميات الوظيفية',
                'ordering': ['code'],
            },
        ),

        # Employee Model
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('employee_number', models.CharField(editable=False, help_text='يتم توليده تلقائياً', max_length=20, verbose_name='رقم الموظف')),
                ('first_name', models.CharField(max_length=50, verbose_name='الاسم الأول')),
                ('middle_name', models.CharField(blank=True, max_length=50, verbose_name='اسم الأب')),
                ('last_name', models.CharField(max_length=50, verbose_name='اسم العائلة')),
                ('full_name_en', models.CharField(blank=True, max_length=150, verbose_name='الاسم بالإنجليزية')),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='تاريخ الميلاد')),
                ('nationality', models.CharField(blank=True, choices=[('jordanian', 'أردني'), ('palestinian', 'فلسطيني'), ('syrian', 'سوري'), ('iraqi', 'عراقي'), ('egyptian', 'مصري'), ('lebanese', 'لبناني'), ('saudi', 'سعودي'), ('other', 'أخرى')], default='jordanian', max_length=20, verbose_name='الجنسية')),
                ('national_id', models.CharField(help_text='الرقم الوطني أو رقم جواز السفر', max_length=20, verbose_name='الرقم الوطني')),
                ('gender', models.CharField(blank=True, choices=[('male', 'ذكر'), ('female', 'أنثى')], max_length=10, verbose_name='الجنس')),
                ('marital_status', models.CharField(blank=True, choices=[('single', 'أعزب'), ('married', 'متزوج'), ('divorced', 'مطلق'), ('widowed', 'أرمل')], default='single', max_length=15, verbose_name='الحالة الاجتماعية')),
                ('mobile', models.CharField(max_length=20, verbose_name='رقم الموبايل')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='رقم الهاتف')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='البريد الإلكتروني')),
                ('address', models.TextField(blank=True, verbose_name='العنوان')),
                ('hire_date', models.DateField(verbose_name='تاريخ التعيين')),
                ('social_security_number', models.CharField(blank=True, max_length=20, verbose_name='رقم الضمان الاجتماعي')),
                ('employment_status', models.CharField(choices=[('full_time', 'دوام كامل'), ('part_time', 'دوام جزئي'), ('contract', 'عقد مؤقت')], default='full_time', max_length=20, verbose_name='حالة التوظيف')),
                ('status', models.CharField(choices=[('active', 'نشط'), ('inactive', 'غير نشط'), ('terminated', 'مفصول')], default='active', max_length=15, verbose_name='الحالة')),
                ('termination_date', models.DateField(blank=True, null=True, verbose_name='تاريخ إنهاء الخدمة')),
                ('termination_reason', models.TextField(blank=True, verbose_name='سبب إنهاء الخدمة')),
                ('basic_salary', models.DecimalField(decimal_places=2, default=0, help_text='المكون 1: الراتب الأساسي الشهري', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='الراتب الأساسي')),
                ('fuel_allowance', models.DecimalField(decimal_places=2, default=0, help_text='المكون 2: بدل الوقود الشهري', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='بدل الوقود')),
                ('other_allowances', models.DecimalField(decimal_places=2, default=0, help_text='المكون 3: بدلات إضافية أخرى', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='بدلات أخرى')),
                ('social_security_salary', models.DecimalField(decimal_places=2, default=0, help_text='المكون 4: الراتب المسجل في الضمان الاجتماعي', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='راتب الضمان')),
                ('working_hours_per_day', models.DecimalField(decimal_places=2, default=8, help_text='عدد ساعات العمل اليومية', max_digits=4, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(24)], verbose_name='ساعات العمل اليومية')),
                ('working_days_per_month', models.PositiveSmallIntegerField(default=30, help_text='عدد أيام العمل في الشهر', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(31)], verbose_name='أيام العمل الشهرية')),
                ('annual_leave_balance', models.DecimalField(decimal_places=2, default=0, help_text='الرصيد المتبقي من الإجازات السنوية', max_digits=5, verbose_name='رصيد الإجازات السنوية')),
                ('sick_leave_balance', models.DecimalField(decimal_places=2, default=0, help_text='الرصيد المتبقي من الإجازات المرضية', max_digits=5, verbose_name='رصيد الإجازات المرضية')),
                ('bank_name', models.CharField(blank=True, max_length=100, verbose_name='اسم البنك')),
                ('bank_branch', models.CharField(blank=True, max_length=100, verbose_name='فرع البنك')),
                ('bank_account', models.CharField(blank=True, max_length=50, verbose_name='رقم الحساب البنكي')),
                ('iban', models.CharField(blank=True, max_length=50, verbose_name='رقم IBAN')),
                ('photo', models.ImageField(blank=True, upload_to='employees/photos/', verbose_name='الصورة الشخصية')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.branch', verbose_name='الفرع/المدينة')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('currency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.currency', verbose_name='العملة')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='hr.department', verbose_name='القسم/الإدارة')),
                ('job_grade', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.jobgrade', verbose_name='الدرجة الوظيفية')),
                ('job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='hr.jobtitle', verbose_name='المسمى الوظيفي')),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subordinates', to='hr.employee', verbose_name='المدير المباشر')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employee_profile', to=settings.AUTH_USER_MODEL, verbose_name='حساب المستخدم')),
            ],
            options={
                'verbose_name': 'موظف',
                'verbose_name_plural': 'الموظفون',
                'ordering': ['employee_number'],
            },
        ),

        # Add manager field to Department
        migrations.AddField(
            model_name='department',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_departments', to='hr.employee', verbose_name='مدير القسم'),
        ),

        # Unique constraints
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(fields=['company', 'code'], name='unique_department_code'),
        ),
        migrations.AddConstraint(
            model_name='jobgrade',
            constraint=models.UniqueConstraint(fields=['company', 'code'], name='unique_jobgrade_code'),
        ),
        migrations.AddConstraint(
            model_name='jobtitle',
            constraint=models.UniqueConstraint(fields=['company', 'code'], name='unique_jobtitle_code'),
        ),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(fields=['company', 'employee_number'], name='unique_employee_number'),
        ),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(fields=['company', 'national_id'], name='unique_employee_national_id'),
        ),

        # Indexes
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['code'], name='hr_departme_code_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['company', 'is_active'], name='hr_departme_company_idx'),
        ),
        migrations.AddIndex(
            model_name='jobgrade',
            index=models.Index(fields=['level'], name='hr_jobgrade_level_idx'),
        ),
        migrations.AddIndex(
            model_name='jobtitle',
            index=models.Index(fields=['department'], name='hr_jobtitle_dept_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['employee_number'], name='hr_employee_empnum_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['national_id'], name='hr_employee_natid_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['status'], name='hr_employee_status_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['department', 'status'], name='hr_employee_dept_status_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['hire_date'], name='hr_employee_hire_idx'),
        ),
    ]

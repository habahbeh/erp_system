# apps/hr/migrations/0003_phase1_settings.py
# Phase 1 - HR Settings Models

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0002_phase1_documents_contracts'),
        ('accounting', '0005_alter_costcenter_cost_center_type'),
    ]

    operations = [
        # HRSettings Model
        migrations.CreateModel(
            name='HRSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_working_hours_per_day', models.DecimalField(decimal_places=2, default=8, max_digits=4, verbose_name='ساعات العمل اليومية الافتراضية')),
                ('default_working_days_per_month', models.PositiveSmallIntegerField(default=30, verbose_name='أيام العمل الشهرية الافتراضية')),
                ('overtime_regular_rate', models.DecimalField(decimal_places=2, default=Decimal('1.25'), help_text='نسبة الأجر الإضافي لأيام العمل العادية (مثال: 1.25 = 125%)', max_digits=4, verbose_name='معامل العمل الإضافي - أيام الدوام')),
                ('overtime_holiday_rate', models.DecimalField(decimal_places=2, default=Decimal('2.00'), help_text='نسبة الأجر الإضافي لأيام العطل (مثال: 2.0 = 200%)', max_digits=4, verbose_name='معامل العمل الإضافي - أيام العطل')),
                ('default_annual_leave_days', models.PositiveSmallIntegerField(default=14, verbose_name='أيام الإجازة السنوية الافتراضية')),
                ('default_sick_leave_days', models.PositiveSmallIntegerField(default=14, verbose_name='أيام الإجازة المرضية الافتراضية')),
                ('carry_forward_leave', models.BooleanField(default=True, help_text='هل يتم ترحيل رصيد الإجازات للسنة التالية؟', verbose_name='ترحيل رصيد الإجازات')),
                ('max_carry_forward_days', models.PositiveSmallIntegerField(default=14, help_text='الحد الأقصى لأيام الإجازة المرحلة', verbose_name='الحد الأقصى للترحيل')),
                ('sick_leave_medical_certificate_days', models.PositiveSmallIntegerField(default=3, help_text='عدد أيام الإجازة المرضية التي تتطلب تقريراً طبياً', verbose_name='أيام تتطلب تقرير طبي')),
                ('default_probation_days', models.PositiveSmallIntegerField(default=90, verbose_name='فترة التجربة الافتراضية (بالأيام)')),
                ('default_notice_period_days', models.PositiveSmallIntegerField(default=30, verbose_name='فترة الإشعار الافتراضية (بالأيام)')),
                ('max_advance_percentage', models.DecimalField(decimal_places=2, default=Decimal('50.00'), help_text='نسبة الحد الأقصى للسلفة من الراتب', max_digits=5, verbose_name='الحد الأقصى للسلفة (%)')),
                ('max_installments', models.PositiveSmallIntegerField(default=12, verbose_name='الحد الأقصى لعدد الأقساط')),
                ('fiscal_year_start_month', models.PositiveSmallIntegerField(default=1, verbose_name='شهر بداية السنة المالية')),
                ('auto_create_journal_entries', models.BooleanField(default=True, help_text='إنشاء القيود المحاسبية تلقائياً عند ترحيل الرواتب', verbose_name='إنشاء القيود تلقائياً')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hr_settings', to='core.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'إعدادات الموارد البشرية',
                'verbose_name_plural': 'إعدادات الموارد البشرية',
            },
        ),

        # SocialSecuritySettings Model
        migrations.CreateModel(
            name='SocialSecuritySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_contribution_rate', models.DecimalField(decimal_places=2, default=Decimal('7.50'), help_text='نسبة الضمان الاجتماعي من راتب الموظف', max_digits=5, verbose_name='نسبة حصة الموظف (%)')),
                ('company_contribution_rate', models.DecimalField(decimal_places=2, default=Decimal('14.25'), help_text='نسبة الضمان الاجتماعي التي تدفعها الشركة', max_digits=5, verbose_name='نسبة حصة الشركة (%)')),
                ('minimum_insurable_salary', models.DecimalField(blank=True, decimal_places=2, help_text='الحد الأدنى للراتب الخاضع للضمان', max_digits=10, null=True, verbose_name='الحد الأدنى للراتب المؤمن')),
                ('maximum_insurable_salary', models.DecimalField(blank=True, decimal_places=2, help_text='الحد الأقصى للراتب الخاضع للضمان', max_digits=10, null=True, verbose_name='الحد الأقصى للراتب المؤمن')),
                ('is_active', models.BooleanField(default=True, help_text='هل نظام الضمان الاجتماعي مفعل للشركة؟', verbose_name='مفعل')),
                ('effective_date', models.DateField(blank=True, help_text='تاريخ بدء تطبيق هذه النسب', null=True, verbose_name='تاريخ السريان')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='social_security_settings', to='core.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'إعدادات الضمان الاجتماعي',
                'verbose_name_plural': 'إعدادات الضمان الاجتماعي',
            },
        ),

        # PayrollAccountMapping Model
        migrations.CreateModel(
            name='PayrollAccountMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('component', models.CharField(choices=[('basic_salary', 'الراتب الأساسي'), ('fuel_allowance', 'بدل الوقود'), ('other_allowances', 'بدلات أخرى'), ('overtime_regular', 'العمل الإضافي - أيام الدوام'), ('overtime_holidays', 'العمل الإضافي - أيام العطل'), ('other_earnings', 'أصناف أخرى (استحقاقات)'), ('advances', 'السلف'), ('early_leave_deductions', 'مغادرات الخصم'), ('administrative_deductions', 'احتزارت الخصم'), ('ss_employee', 'الضمان الاجتماعي - حصة الموظف'), ('ss_company', 'الضمان الاجتماعي - حصة الشركة'), ('salaries_payable', 'رواتب مستحقة الدفع'), ('ss_payable', 'ذمة الضمان الاجتماعي'), ('cash_bank', 'الصندوق/البنك')], max_length=30, verbose_name='مكون الراتب')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.account', verbose_name='الحساب المحاسبي')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_account_mappings', to='core.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'ربط حساب راتب',
                'verbose_name_plural': 'ربط حسابات الرواتب',
            },
        ),

        # LeaveType Model
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, verbose_name='الرمز')),
                ('name', models.CharField(max_length=100, verbose_name='اسم نوع الإجازة')),
                ('name_en', models.CharField(blank=True, max_length=100, verbose_name='الاسم بالإنجليزية')),
                ('is_paid', models.BooleanField(default=True, help_text='هل هذا النوع من الإجازات مدفوع؟', verbose_name='مدفوعة')),
                ('affects_salary', models.BooleanField(default=False, help_text='هل تخصم من الراتب؟', verbose_name='تؤثر على الراتب')),
                ('requires_approval', models.BooleanField(default=True, verbose_name='تتطلب موافقة')),
                ('requires_attachment', models.BooleanField(default=False, help_text='مثل التقرير الطبي للإجازة المرضية', verbose_name='تتطلب مرفق')),
                ('default_days', models.PositiveSmallIntegerField(default=0, verbose_name='الرصيد السنوي الافتراضي')),
                ('max_consecutive_days', models.PositiveSmallIntegerField(default=0, help_text='0 = غير محدود', verbose_name='الحد الأقصى للأيام المتتالية')),
                ('allow_negative_balance', models.BooleanField(default=False, verbose_name='السماح بالرصيد السالب')),
                ('carry_forward', models.BooleanField(default=False, help_text='هل يمكن ترحيل الرصيد للسنة التالية؟', verbose_name='قابل للترحيل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_types', to='core.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'نوع إجازة',
                'verbose_name_plural': 'أنواع الإجازات',
                'ordering': ['code'],
            },
        ),

        # Unique constraints
        migrations.AddConstraint(
            model_name='payrollaccountmapping',
            constraint=models.UniqueConstraint(fields=['company', 'component'], name='unique_payroll_mapping'),
        ),
        migrations.AddConstraint(
            model_name='leavetype',
            constraint=models.UniqueConstraint(fields=['company', 'code'], name='unique_leavetype_code'),
        ),
    ]

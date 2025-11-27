# apps/hr/migrations/0002_phase1_documents_contracts.py
# Phase 1 - Employee Documents, Contracts, and Increments

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hr', '0001_initial'),
    ]

    operations = [
        # EmployeeDocument Model
        migrations.CreateModel(
            name='EmployeeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('document_type', models.CharField(choices=[('id_card', 'بطاقة هوية'), ('passport', 'جواز سفر'), ('cv', 'السيرة الذاتية'), ('certificate', 'شهادة'), ('contract', 'عقد عمل'), ('medical', 'تقرير طبي'), ('license', 'رخصة'), ('other', 'أخرى')], max_length=20, verbose_name='نوع المستند')),
                ('name', models.CharField(max_length=100, verbose_name='اسم المستند')),
                ('document_number', models.CharField(blank=True, max_length=50, verbose_name='رقم المستند')),
                ('issue_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الإصدار')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الانتهاء')),
                ('file', models.FileField(blank=True, upload_to='employees/documents/', verbose_name='الملف')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='hr.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'مستند موظف',
                'verbose_name_plural': 'مستندات الموظفين',
                'ordering': ['-issue_date'],
            },
        ),

        # EmployeeContract Model
        migrations.CreateModel(
            name='EmployeeContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('contract_number', models.CharField(blank=True, help_text='يتم توليده تلقائياً', max_length=50, verbose_name='رقم العقد')),
                ('contract_type', models.CharField(choices=[('fixed_term', 'محدد المدة'), ('indefinite', 'غير محدد المدة'), ('temporary', 'عقد مؤقت'), ('probation', 'تحت التجربة')], default='fixed_term', max_length=20, verbose_name='نوع العقد')),
                ('start_date', models.DateField(verbose_name='تاريخ بداية العقد')),
                ('end_date', models.DateField(blank=True, help_text='اتركه فارغاً للعقود غير محددة المدة', null=True, verbose_name='تاريخ نهاية العقد')),
                ('contract_salary', models.DecimalField(decimal_places=2, help_text='الراتب المتفق عليه في العقد', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='راتب العقد')),
                ('probation_period', models.PositiveSmallIntegerField(default=90, help_text='فترة التجربة بالأيام', verbose_name='فترة التجربة (بالأيام)')),
                ('notice_period', models.PositiveSmallIntegerField(default=30, help_text='فترة الإشعار قبل إنهاء العقد', verbose_name='فترة الإشعار (بالأيام)')),
                ('status', models.CharField(choices=[('draft', 'مسودة'), ('active', 'نشط'), ('expired', 'منتهي'), ('terminated', 'ملغي'), ('renewed', 'مُجدد')], default='draft', max_length=15, verbose_name='الحالة')),
                ('contract_file', models.FileField(blank=True, upload_to='employees/contracts/', verbose_name='ملف العقد')),
                ('terms_and_conditions', models.TextField(blank=True, verbose_name='الشروط والأحكام')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('signed_date', models.DateField(blank=True, null=True, verbose_name='تاريخ التوقيع')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='hr.employee', verbose_name='الموظف')),
                ('signed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signed_contracts', to=settings.AUTH_USER_MODEL, verbose_name='وقع بواسطة')),
            ],
            options={
                'verbose_name': 'عقد عمل',
                'verbose_name_plural': 'عقود العمل',
                'ordering': ['-start_date'],
            },
        ),

        # SalaryIncrement Model
        migrations.CreateModel(
            name='SalaryIncrement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('increment_type', models.CharField(choices=[('annual', 'علاوة سنوية'), ('promotion', 'ترقية'), ('merit', 'علاوة تميز'), ('adjustment', 'تعديل راتب'), ('cost_of_living', 'بدل غلاء معيشة'), ('other', 'أخرى')], default='annual', max_length=20, verbose_name='نوع العلاوة')),
                ('old_salary', models.DecimalField(decimal_places=2, editable=False, max_digits=10, verbose_name='الراتب القديم')),
                ('is_percentage', models.BooleanField(default=False, help_text='اختر إذا كانت الزيادة نسبة من الراتب', verbose_name='نسبة مئوية')),
                ('increment_amount', models.DecimalField(decimal_places=2, help_text='المبلغ أو النسبة حسب الاختيار', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='قيمة العلاوة')),
                ('new_salary', models.DecimalField(decimal_places=2, editable=False, max_digits=10, verbose_name='الراتب الجديد')),
                ('effective_date', models.DateField(verbose_name='تاريخ السريان')),
                ('status', models.CharField(choices=[('pending', 'معلق'), ('approved', 'معتمد'), ('applied', 'مطبق'), ('rejected', 'مرفوض')], default='pending', max_length=15, verbose_name='الحالة')),
                ('approval_date', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الاعتماد')),
                ('reason', models.TextField(blank=True, verbose_name='السبب')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_increments', to=settings.AUTH_USER_MODEL, verbose_name='اعتمد بواسطة')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='أنشأ بواسطة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_increments', to='hr.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'علاوة',
                'verbose_name_plural': 'العلاوات',
                'ordering': ['-effective_date'],
            },
        ),

        # Unique constraints and indexes
        migrations.AddConstraint(
            model_name='employeecontract',
            constraint=models.UniqueConstraint(fields=['company', 'contract_number'], name='unique_contract_number'),
        ),
        migrations.AddIndex(
            model_name='employeecontract',
            index=models.Index(fields=['employee', 'status'], name='hr_contract_emp_status_idx'),
        ),
        migrations.AddIndex(
            model_name='employeecontract',
            index=models.Index(fields=['start_date', 'end_date'], name='hr_contract_dates_idx'),
        ),
        migrations.AddIndex(
            model_name='salaryincrement',
            index=models.Index(fields=['employee', 'status'], name='hr_increment_emp_status_idx'),
        ),
        migrations.AddIndex(
            model_name='salaryincrement',
            index=models.Index(fields=['effective_date'], name='hr_increment_date_idx'),
        ),
    ]

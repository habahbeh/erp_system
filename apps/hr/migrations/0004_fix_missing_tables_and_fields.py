# apps/hr/migrations/0004_fix_missing_tables_and_fields.py
"""
إصلاح الجداول والحقول المفقودة
"""

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0003_phase1_settings'),
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # إنشاء جدول JobGrade
        migrations.CreateModel(
            name='JobGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
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
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_grades', to='core.company', verbose_name='الشركة')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='أنشئ بواسطة')),
            ],
            options={
                'verbose_name': 'درجة وظيفية',
                'verbose_name_plural': 'الدرجات الوظيفية',
                'ordering': ['level', 'code'],
                'unique_together': {('company', 'code')},
            },
        ),

        # إضافة الحقول الناقصة في JobTitle
        migrations.AddField(
            model_name='jobtitle',
            name='name_en',
            field=models.CharField(blank=True, max_length=100, verbose_name='الاسم بالإنجليزية'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_titles', to='hr.department', verbose_name='القسم'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='job_grade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_titles', to='hr.jobgrade', verbose_name='الدرجة الوظيفية'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='min_salary',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأدنى للراتب'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='max_salary',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='الحد الأعلى للراتب'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='responsibilities',
            field=models.TextField(blank=True, verbose_name='المسؤوليات'),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='requirements',
            field=models.TextField(blank=True, verbose_name='متطلبات الوظيفة'),
        ),

        # إضافة job_grade للموظف
        migrations.AddField(
            model_name='employee',
            name='job_grade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='hr.jobgrade', verbose_name='الدرجة الوظيفية'),
        ),

        # إضافة max_carry_forward لنوع الإجازة
        migrations.AddField(
            model_name='leavetype',
            name='max_carry_forward',
            field=models.PositiveSmallIntegerField(default=0, help_text='الحد الأقصى للأيام المرحلة (0 = غير محدود)', verbose_name='الحد الأقصى للترحيل'),
        ),
    ]

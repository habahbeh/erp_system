"""
أمر لتوليد بيانات تجريبية احترافية لنظام HR
Professional HR Demo Data Generator

الاستخدام:
python manage.py create_professional_hr_demo --company-id=1
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, datetime, timedelta, time
import random

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    Department, JobGrade, JobTitle, Employee,
    LeaveType, LeaveBalance, LeaveRequest,
    Attendance, EarlyLeave, Overtime, Advance,
    HRSettings, SocialSecuritySettings,
    BiometricDevice, SalaryIncrement,
    Payroll, PayrollDetail,
)
from apps.hr.models.performance_models import (
    PerformancePeriod, PerformanceCriteria, PerformanceEvaluation,
    PerformanceEvaluationDetail, PerformanceGoal, PerformanceNote,
)
from apps.hr.models.training_models import (
    TrainingCategory, TrainingProvider, TrainingCourse,
    TrainingEnrollment, TrainingRequest, TrainingPlan,
    TrainingPlanItem, TrainingFeedback,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية احترافية لنظام الموارد البشرية'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            default=1,
            help='رقم الشركة (افتراضي: 1)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='حذف البيانات الموجودة قبل الإنشاء'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        clear_data = options['clear']

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ الشركة برقم {company_id} غير موجودة'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n🚀 بدء إنشاء بيانات تجريبية احترافية للشركة: {company.name}\n'))

        try:
            with transaction.atomic():
                if clear_data:
                    self._clear_existing_data(company)

                # 1. إعدادات النظام
                self._create_hr_settings(company)

                # 2. الهيكل التنظيمي
                departments = self._create_departments(company)
                job_grades = self._create_job_grades(company)
                job_titles = self._create_job_titles(company, departments, job_grades)

                # 3. أنواع الإجازات
                leave_types = self._create_leave_types(company)

                # 4. الموظفين
                branches = company.branches.all()
                if not branches.exists():
                    self.stdout.write(self.style.WARNING('⚠️  لا توجد فروع، سيتم إنشاء فرع رئيسي'))
                    branch = self._create_main_branch(company)
                    branches = [branch]
                else:
                    branch = branches.first()

                currency = company.base_currency
                admin_user = self._get_or_create_admin_user(company, branch)

                employees = self._create_employees(company, branch, departments, job_titles,
                                                   job_grades, currency, admin_user)

                # 5. أرصدة الإجازات
                self._create_leave_balances(company, employees, leave_types)

                # 6. بيانات الحضور (آخر 30 يوم)
                self._create_attendance_data(company, employees)

                # 7. طلبات الإجازات
                self._create_leave_requests(company, employees, leave_types)

                # 8. العمل الإضافي
                self._create_overtime_records(company, employees)

                # 9. السلف
                self._create_advances(company, employees)

                # 10. العلاوات
                self._create_salary_increments(company, employees)

                # 11. المغادرات المبكرة
                self._create_early_leaves(company, employees)

                # 12. جهاز البصمة
                self._create_biometric_device(company, branch)

                # 13. كشوفات الرواتب
                self._create_payroll_data(company, branch, employees)

                # 14. التقييم والأداء
                self._create_performance_data(company, employees, admin_user)

                # 15. التدريب والتطوير
                self._create_training_data(company, employees, departments, job_titles, admin_user)

            self.stdout.write(self.style.SUCCESS('\n✅ تم إنشاء البيانات التجريبية بنجاح!\n'))
            self._print_summary(company, employees, departments)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ حدث خطأ: {str(e)}\n'))
            raise

    def _clear_existing_data(self, company):
        """حذف البيانات الموجودة"""
        self.stdout.write('🗑️  حذف البيانات الموجودة...')

        Employee.objects.filter(company=company).delete()
        Department.objects.filter(company=company).delete()
        JobGrade.objects.filter(company=company).delete()
        JobTitle.objects.filter(company=company).delete()
        LeaveType.objects.filter(company=company).delete()
        BiometricDevice.objects.filter(company=company).delete()

        self.stdout.write(self.style.SUCCESS('  ✓ تم حذف البيانات'))

    def _create_hr_settings(self, company):
        """إنشاء إعدادات HR"""
        self.stdout.write('⚙️  إنشاء إعدادات النظام...')

        hr_settings, created = HRSettings.objects.get_or_create(
            company=company,
            defaults={
                'default_working_hours_per_day': 8,
                'default_working_days_per_month': 30,
                'overtime_regular_rate': Decimal('1.25'),
                'overtime_holiday_rate': Decimal('2.00'),
                'default_annual_leave_days': 14,
                'default_sick_leave_days': 14,
                'carry_forward_leave': True,
                'max_carry_forward_days': 7,
                'default_probation_days': 90,
                'default_notice_period_days': 30,
                'max_advance_percentage': Decimal('50.00'),
                'max_installments': 12,
                'auto_create_journal_entries': True,
            }
        )

        ss_settings, created = SocialSecuritySettings.objects.get_or_create(
            company=company,
            defaults={
                'employee_contribution_rate': Decimal('7.50'),
                'company_contribution_rate': Decimal('14.25'),
                'is_active': True,
                'effective_date': date.today(),
            }
        )

        self.stdout.write(self.style.SUCCESS('  ✓ تم إنشاء الإعدادات'))
        return hr_settings, ss_settings

    def _create_departments(self, company):
        """إنشاء الأقسام"""
        self.stdout.write('🏢 إنشاء الأقسام...')

        departments_data = [
            ('MGT', 'الإدارة العامة', 'Management'),
            ('IT', 'تقنية المعلومات', 'Information Technology'),
            ('HR', 'الموارد البشرية', 'Human Resources'),
            ('FIN', 'المالية والمحاسبة', 'Finance & Accounting'),
            ('SALES', 'المبيعات', 'Sales'),
            ('MKT', 'التسويق', 'Marketing'),
            ('OPS', 'العمليات', 'Operations'),
            ('CS', 'خدمة العملاء', 'Customer Service'),
        ]

        departments = []
        for code, name, name_en in departments_data:
            dept, created = Department.objects.get_or_create(
                company=company,
                code=code,
                defaults={'name': name}
            )
            departments.append(dept)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(departments)} قسم'))
        return departments

    def _create_job_grades(self, company):
        """إنشاء الدرجات الوظيفية"""
        self.stdout.write('📊 إنشاء الدرجات الوظيفية...')

        grades_data = [
            ('JR', 'مبتدئ', 'Junior', 1, 400, 600, 14, 14),
            ('MID', 'متوسط', 'Mid-Level', 2, 600, 900, 18, 14),
            ('SR', 'أول', 'Senior', 3, 900, 1200, 21, 14),
            ('LD', 'قائد فريق', 'Team Lead', 4, 1200, 1500, 21, 14),
            ('MGR', 'مدير', 'Manager', 5, 1500, 2000, 24, 14),
            ('DIR', 'مدير إدارة', 'Director', 6, 2000, 3000, 28, 14),
        ]

        job_grades = []
        for code, name, name_en, level, min_sal, max_sal, annual, sick in grades_data:
            grade, created = JobGrade.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'name_en': name_en,
                    'level': level,
                    'min_salary': min_sal,
                    'max_salary': max_sal,
                    'annual_leave_days': annual,
                    'sick_leave_days': sick,
                }
            )
            job_grades.append(grade)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(job_grades)} درجة وظيفية'))
        return job_grades

    def _create_job_titles(self, company, departments, job_grades):
        """إنشاء المسميات الوظيفية"""
        self.stdout.write('💼 إنشاء المسميات الوظيفية...')

        # تصنيف الدرجات
        jr_grade = next(g for g in job_grades if g.code == 'JR')
        mid_grade = next(g for g in job_grades if g.code == 'MID')
        sr_grade = next(g for g in job_grades if g.code == 'SR')
        ld_grade = next(g for g in job_grades if g.code == 'LD')
        mgr_grade = next(g for g in job_grades if g.code == 'MGR')
        dir_grade = next(g for g in job_grades if g.code == 'DIR')

        # تصنيف الأقسام
        dept_dict = {d.code: d for d in departments}

        titles_data = [
            # الإدارة العامة
            ('CEO', 'المدير التنفيذي', 'Chief Executive Officer', 'MGT', dir_grade, 2500, 3000),
            ('GM', 'المدير العام', 'General Manager', 'MGT', dir_grade, 2000, 2500),

            # تقنية المعلومات
            ('IT-DIR', 'مدير تقنية المعلومات', 'IT Director', 'IT', dir_grade, 2000, 2500),
            ('DEV-MGR', 'مدير التطوير', 'Development Manager', 'IT', mgr_grade, 1500, 1800),
            ('SR-DEV', 'مطور أول', 'Senior Developer', 'IT', sr_grade, 1000, 1200),
            ('DEV', 'مطور', 'Developer', 'IT', mid_grade, 700, 900),
            ('JR-DEV', 'مطور مبتدئ', 'Junior Developer', 'IT', jr_grade, 450, 600),

            # الموارد البشرية
            ('HR-MGR', 'مدير الموارد البشرية', 'HR Manager', 'HR', mgr_grade, 1500, 1800),
            ('HR-SP', 'أخصائي موارد بشرية', 'HR Specialist', 'HR', mid_grade, 600, 800),
            ('REC', 'موظف توظيف', 'Recruiter', 'HR', mid_grade, 550, 750),

            # المالية
            ('FIN-DIR', 'المدير المالي', 'Financial Director', 'FIN', dir_grade, 2000, 2500),
            ('ACC-MGR', 'مدير المحاسبة', 'Accounting Manager', 'FIN', mgr_grade, 1500, 1800),
            ('SR-ACC', 'محاسب أول', 'Senior Accountant', 'FIN', sr_grade, 900, 1100),
            ('ACC', 'محاسب', 'Accountant', 'FIN', mid_grade, 600, 800),

            # المبيعات
            ('SALES-DIR', 'مدير المبيعات', 'Sales Director', 'SALES', dir_grade, 2000, 2500),
            ('SALES-MGR', 'مدير مبيعات', 'Sales Manager', 'SALES', mgr_grade, 1500, 1800),
            ('SR-SALES', 'مندوب مبيعات أول', 'Senior Sales Rep', 'SALES', sr_grade, 900, 1200),
            ('SALES', 'مندوب مبيعات', 'Sales Representative', 'SALES', mid_grade, 600, 900),

            # التسويق
            ('MKT-MGR', 'مدير التسويق', 'Marketing Manager', 'MKT', mgr_grade, 1500, 1800),
            ('MKT-SP', 'أخصائي تسويق', 'Marketing Specialist', 'MKT', mid_grade, 650, 850),

            # العمليات
            ('OPS-MGR', 'مدير العمليات', 'Operations Manager', 'OPS', mgr_grade, 1500, 1800),
            ('OPS-SUP', 'مشرف عمليات', 'Operations Supervisor', 'OPS', sr_grade, 900, 1100),

            # خدمة العملاء
            ('CS-MGR', 'مدير خدمة العملاء', 'CS Manager', 'CS', mgr_grade, 1300, 1600),
            ('CS-SUP', 'مشرف خدمة عملاء', 'CS Supervisor', 'CS', sr_grade, 800, 1000),
            ('CS-REP', 'موظف خدمة عملاء', 'CS Representative', 'CS', mid_grade, 500, 700),
        ]

        job_titles = []
        for code, name, name_en, dept_code, grade, min_sal, max_sal in titles_data:
            dept = dept_dict.get(dept_code)
            if dept:
                title, created = JobTitle.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'name_en': name_en,
                        'department': dept,
                        'job_grade': grade,
                        'min_salary': min_sal,
                        'max_salary': max_sal,
                    }
                )
                job_titles.append(title)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(job_titles)} مسمى وظيفي'))
        return job_titles

    def _create_leave_types(self, company):
        """إنشاء أنواع الإجازات"""
        self.stdout.write('🏖️  إنشاء أنواع الإجازات...')

        leave_types_data = [
            ('ANNUAL', 'إجازة سنوية', 'Annual Leave', True, False, True, False, 14, 0, False, True, 7),
            ('SICK', 'إجازة مرضية', 'Sick Leave', True, False, True, True, 14, 3, True, False, 0),
            ('CASUAL', 'إجازة طارئة', 'Casual Leave', True, False, True, False, 3, 0, False, False, 0),
            ('UNPAID', 'إجازة بدون راتب', 'Unpaid Leave', False, True, True, False, 0, 0, False, False, 0),
            ('MATERNITY', 'إجازة أمومة', 'Maternity Leave', True, False, True, True, 70, 0, False, False, 0),
        ]

        leave_types = []
        for code, name, name_en, is_paid, affects_salary, req_approval, req_attach, default_days, max_consecutive, allow_neg, carry_fwd, max_carry in leave_types_data:
            lt, created = LeaveType.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'name_en': name_en,
                    'is_paid': is_paid,
                    'affects_salary': affects_salary,
                    'requires_approval': req_approval,
                    'requires_attachment': req_attach,
                    'default_days': default_days,
                    'max_consecutive_days': max_consecutive,
                    'allow_negative_balance': allow_neg,
                    'carry_forward': carry_fwd,
                }
            )
            leave_types.append(lt)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(leave_types)} نوع إجازة'))
        return leave_types

    def _create_main_branch(self, company):
        """إنشاء فرع رئيسي"""
        branch, created = Branch.objects.get_or_create(
            company=company,
            code='MAIN',
            defaults={
                'name': 'الفرع الرئيسي',
                'is_main': True,
                'is_active': True,
            }
        )
        return branch

    def _get_or_create_admin_user(self, company, branch):
        """الحصول على أو إنشاء مستخدم إداري"""
        admin_user, created = User.objects.get_or_create(
            username='hr_admin',
            defaults={
                'email': 'hr@company.com',
                'first_name': 'مدير',
                'last_name': 'النظام',
                'is_staff': True,
                'is_superuser': False,
            }
        )
        if created:
            admin_user.set_password('admin123')
        admin_user.company = company
        admin_user.branch = branch
        admin_user.save()

        return admin_user

    def _create_employees(self, company, branch, departments, job_titles, job_grades, currency, admin_user):
        """إنشاء موظفين واقعيين"""
        self.stdout.write('👥 إنشاء الموظفين...')

        # أسماء عربية حقيقية
        first_names = [
            'محمد', 'أحمد', 'علي', 'حسن', 'خالد', 'عمر', 'يوسف', 'كريم',
            'فاطمة', 'مريم', 'سارة', 'نور', 'هند', 'ليلى', 'رنا', 'دينا'
        ]

        middle_names = [
            'عبدالله', 'محمود', 'حسين', 'سعيد', 'جمال', 'فيصل', 'طارق',
            'عبدالرحمن', 'ماجد', 'وليد', 'ناصر', 'عادل'
        ]

        last_names = [
            'العلي', 'الأحمد', 'الحسن', 'المحمد', 'الخطيب', 'السيد', 'العمر',
            'الحمد', 'الشريف', 'النجار', 'الصالح', 'الكريم', 'الحكيم'
        ]

        employees = []
        employee_count = 0

        # إنشاء موظف لكل مسمى وظيفي على الأقل
        for job_title in job_titles:
            if employee_count >= 40:  # حد أقصى 40 موظف
                break

            first_name = random.choice(first_names)
            middle_name = random.choice(middle_names)
            last_name = random.choice(last_names)

            # تحديد الراتب حسب الدرجة
            salary_range = job_title.job_grade.max_salary - job_title.job_grade.min_salary
            base_salary = job_title.job_grade.min_salary + (salary_range * Decimal(str(random.uniform(0.3, 0.9))))
            base_salary = round(float(base_salary) / 50) * 50  # تقريب لأقرب 50

            # بدل الوقود (5-10% من الراتب)
            fuel_allowance = round((base_salary * Decimal(str(random.uniform(0.05, 0.10)))) / 10) * 10

            # تاريخ توظيف واقعي (من سنة إلى 5 سنوات ماضية)
            days_ago = random.randint(365, 365 * 5)
            hire_date = date.today() - timedelta(days=days_ago)

            # تاريخ ميلاد واقعي (25-55 سنة)
            years_old = random.randint(25, 55)
            birth_date = date.today() - timedelta(days=years_old * 365)

            # توليد بريد إلكتروني صحيح
            email = f"employee{employee_count + 1:03d}@company.com"

            employee = Employee.objects.create(
                company=company,
                branch=branch,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                full_name_en=f"Employee {employee_count + 1}",
                date_of_birth=birth_date,
                national_id=f"{random.randint(1000000000, 9999999999)}",
                nationality='jordanian',
                gender=random.choice(['male', 'female']),
                marital_status=random.choice(['single', 'married']),
                mobile=f"0{random.randint(790000000, 799999999)}",
                email=email,
                hire_date=hire_date,
                department=job_title.department,
                job_title=job_title,
                job_grade=job_title.job_grade,
                employment_status='full_time',
                status='active',
                basic_salary=base_salary,
                fuel_allowance=fuel_allowance,
                currency=currency,
                created_by=admin_user,
            )
            employees.append(employee)
            employee_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(employees)} موظف'))
        return employees

    def _create_leave_balances(self, company, employees, leave_types):
        """إنشاء أرصدة الإجازات"""
        self.stdout.write('📋 إنشاء أرصدة الإجازات...')

        count = 0
        for employee in employees:
            for leave_type in leave_types:
                if leave_type.default_days > 0:
                    # رصيد مستخدم واقعي
                    used = random.randint(0, min(5, leave_type.default_days))

                    LeaveBalance.objects.create(
                        company=company,
                        employee=employee,
                        leave_type=leave_type,
                        year=date.today().year,
                        opening_balance=leave_type.default_days,
                        used=Decimal(str(used)),
                        adjustment=Decimal('0'),
                        carried_forward=Decimal('0'),
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} رصيد إجازة'))

    def _create_attendance_data(self, company, employees):
        """إنشاء بيانات حضور واقعية"""
        self.stdout.write('⏰ إنشاء بيانات الحضور...')

        count = 0
        # آخر 30 يوم عمل (استثناء الجمعة والسبت)
        today = date.today()

        for day_offset in range(30):
            attendance_date = today - timedelta(days=day_offset)

            # تخطي عطلة نهاية الأسبوع
            if attendance_date.weekday() in [4, 5]:  # الجمعة والسبت
                continue

            for employee in employees:
                # تحديد حالة الحضور
                rand_val = random.random()

                if rand_val < 0.02:  # 2% احتمال الغياب
                    Attendance.objects.create(
                        company=company,
                        employee=employee,
                        date=attendance_date,
                        status='absent',
                        notes='غياب بدون إذن',
                    )
                    count += 1

                elif rand_val < 0.05:  # 3% احتمال إجازة
                    Attendance.objects.create(
                        company=company,
                        employee=employee,
                        date=attendance_date,
                        status='leave',
                        notes='إجازة مرضية',
                    )
                    count += 1

                elif rand_val < 0.98:  # 93% احتمال الحضور
                    # وقت حضور واقعي (8:00 - 9:00)
                    check_in_hour = 8
                    check_in_minute = random.randint(0, 59)

                    # احتمال 15% للتأخير
                    is_late = random.random() < 0.15
                    if is_late:
                        check_in_hour = random.randint(9, 10)
                        check_in_minute = random.randint(0, 59)

                    check_in_time = time(check_in_hour, check_in_minute)

                    # وقت مغادرة واقعي (16:00 - 17:00)
                    check_out_hour = 16
                    check_out_minute = random.randint(0, 59)

                    # احتمال 5% للمغادرة المبكرة
                    if random.random() < 0.05:
                        check_out_hour = random.randint(14, 15)

                    check_out_time = time(check_out_hour, check_out_minute)

                    # حساب ساعات العمل
                    work_hours = check_out_hour - check_in_hour + (check_out_minute - check_in_minute) / 60
                    work_hours = Decimal(str(round(work_hours, 2)))

                    # التأخير
                    late_minutes = 0
                    if check_in_hour >= 9:
                        late_minutes = (check_in_hour - 8) * 60 + check_in_minute

                    # تحديد الحالة: متأخر أو حاضر
                    status = 'late' if is_late else 'present'

                    Attendance.objects.create(
                        company=company,
                        employee=employee,
                        date=attendance_date,
                        check_in=check_in_time,
                        check_out=check_out_time,
                        working_hours=work_hours,
                        late_minutes=late_minutes,
                        status=status,
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} سجل حضور'))

    def _create_leave_requests(self, company, employees, leave_types):
        """إنشاء طلبات إجازات"""
        self.stdout.write('📝 إنشاء طلبات الإجازات...')

        annual_leave = next((lt for lt in leave_types if lt.code == 'ANNUAL'), None)
        sick_leave = next((lt for lt in leave_types if lt.code == 'SICK'), None)

        count = 0
        # إنشاء 2-3 طلبات لكل موظف
        for employee in employees:
            num_requests = random.randint(2, 3)

            for _ in range(num_requests):
                leave_type = random.choice([annual_leave, sick_leave])
                if not leave_type:
                    continue

                # تاريخ بداية الإجازة (خلال آخر 3 أشهر أو الشهر القادم)
                days_offset = random.randint(-90, 30)
                start_date = date.today() + timedelta(days=days_offset)

                # عدد الأيام (1-7)
                days_count = random.randint(1, 7)
                end_date = start_date + timedelta(days=days_count - 1)

                # الحالة
                if days_offset < 0:  # إجازة ماضية
                    status = random.choice(['approved', 'approved'])  # معظمها موافق عليها
                else:  # إجازة مستقبلية
                    status = random.choice(['pending', 'approved', 'rejected'])

                LeaveRequest.objects.create(
                    company=company,
                    employee=employee,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    days=days_count,
                    status=status,
                    reason='طلب إجازة' if leave_type == annual_leave else 'ظرف صحي',
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} طلب إجازة'))

    def _create_overtime_records(self, company, employees):
        """إنشاء سجلات العمل الإضافي"""
        self.stdout.write('⏱️  إنشاء سجلات العمل الإضافي...')

        count = 0
        # 30% من الموظفين لديهم عمل إضافي
        overtime_employees = random.sample(employees, k=int(len(employees) * 0.3))

        for employee in overtime_employees:
            # 2-5 سجلات لكل موظف
            num_records = random.randint(2, 5)

            for _ in range(num_records):
                # تاريخ واقعي (آخر 30 يوم)
                days_ago = random.randint(1, 30)
                overtime_date = date.today() - timedelta(days=days_ago)

                # تخطي عطلة نهاية الأسبوع
                if overtime_date.weekday() in [4, 5]:
                    continue

                # ساعات عمل إضافي (1-4 ساعات)
                hours = random.randint(1, 4)

                # أوقات واقعية
                start_time = "17:00"
                end_hour = 17 + hours
                end_time = f"{end_hour:02d}:00"

                Overtime.objects.create(
                    company=company,
                    employee=employee,
                    date=overtime_date,
                    start_time=start_time,
                    end_time=end_time,
                    hours=hours,
                    overtime_type='regular',
                    status=random.choice(['approved', 'approved', 'pending']),
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} سجل عمل إضافي'))

    def _create_advances(self, company, employees):
        """إنشاء سلف"""
        self.stdout.write('💰 إنشاء السلف...')

        count = 0
        # 20% من الموظفين لديهم سلف
        advance_employees = random.sample(employees, k=int(len(employees) * 0.2))

        for employee in advance_employees:
            # مبلغ السلفة (20-40% من الراتب)
            amount = employee.basic_salary * Decimal(str(random.uniform(0.2, 0.4)))
            amount = Decimal(str(round(float(amount) / 50) * 50))  # تقريب لأقرب 50

            # عدد الأقساط (3-12)
            installments = random.randint(3, 12)

            # تاريخ الطلب (خلال آخر 60 يوم)
            request_date_val = date.today() - timedelta(days=random.randint(1, 60))

            # رقم السلفة
            advance_number = f"ADV-{random.randint(1000, 9999)}"

            Advance.objects.create(
                company=company,
                advance_number=advance_number,
                employee=employee,
                advance_type='salary_advance',
                request_date=request_date_val,
                amount=amount,
                installments=installments,
                start_deduction_date=request_date_val.replace(day=1) + timedelta(days=32),
                status=random.choice(['approved', 'approved', 'pending']),
                reason='ظرف عائلي',
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} سلفة'))

    def _create_salary_increments(self, company, employees):
        """إنشاء العلاوات"""
        self.stdout.write('📈 إنشاء العلاوات...')

        increment_types = [
            ('annual', 'علاوة سنوية', 5, 10),  # نسبة من 5% إلى 10%
            ('promotion', 'ترقية', 10, 20),  # نسبة من 10% إلى 20%
            ('merit', 'علاوة تميز', 8, 15),  # نسبة من 8% إلى 15%
            ('adjustment', 'تعديل راتب', 3, 8),  # نسبة من 3% إلى 8%
        ]

        count = 0
        # 40% من الموظفين لديهم علاوات
        increment_employees = random.sample(list(employees), k=int(len(employees) * 0.4))

        for employee in increment_employees:
            # عدد العلاوات لكل موظف (1-2)
            num_increments = random.randint(1, 2)

            for i in range(num_increments):
                # اختيار نوع عشوائي
                inc_type, reason, min_pct, max_pct = random.choice(increment_types)

                # حساب النسبة والمبلغ
                percentage = Decimal(str(random.uniform(min_pct, max_pct)))

                # الراتب القديم
                old_salary = employee.basic_salary

                # قيمة العلاوة
                increment_amount = percentage

                # الراتب الجديد
                new_salary = old_salary + (old_salary * percentage / Decimal('100'))
                new_salary = Decimal(str(round(float(new_salary) / 10) * 10))  # تقريب لأقرب 10

                # تاريخ السريان (خلال آخر سنة)
                days_ago = random.randint(30, 365) if i == 0 else random.randint(365, 730)
                effective_date = date.today() - timedelta(days=days_ago)

                # الحالة
                if days_ago > 180:
                    status = 'applied'  # مطبقة
                elif days_ago > 90:
                    status = random.choice(['applied', 'approved'])
                else:
                    status = random.choice(['pending', 'approved', 'applied'])

                SalaryIncrement.objects.create(
                    company=company,
                    employee=employee,
                    increment_type=inc_type,
                    old_salary=old_salary,
                    is_percentage=True,
                    increment_amount=increment_amount,
                    new_salary=new_salary,
                    effective_date=effective_date,
                    status=status,
                    reason=reason,
                    created_by=employee.created_by,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} علاوة'))

    def _create_early_leaves(self, company, employees):
        """إنشاء المغادرات المبكرة"""
        self.stdout.write('🚶 إنشاء المغادرات المبكرة...')

        leave_types = [
            ('early_leave', 'ظرف عائلي طارئ', 60, 180),  # 1-3 ساعات
            ('late_arrival', 'زحام مروري', 15, 60),  # 15 دقيقة - ساعة
            ('personal', 'موعد طبي', 30, 120),  # نصف ساعة - ساعتين
        ]

        count = 0
        # 30% من الموظفين لديهم مغادرات
        early_leave_employees = random.sample(list(employees), k=int(len(employees) * 0.3))

        for employee in early_leave_employees:
            # عدد المغادرات لكل موظف (1-3)
            num_leaves = random.randint(1, 3)

            for _ in range(num_leaves):
                # اختيار نوع عشوائي
                leave_type, reason, min_minutes, max_minutes = random.choice(leave_types)

                # تاريخ المغادرة (خلال آخر 60 يوم)
                days_ago = random.randint(1, 60)
                leave_date = date.today() - timedelta(days=days_ago)

                # أوقات المغادرة حسب النوع
                if leave_type == 'early_leave':
                    # مغادرة مبكرة - من وقت العمل إلى قبل نهاية الدوام
                    from_hour = random.randint(13, 15)
                    from_minute = random.choice([0, 15, 30, 45])
                    from_time_val = time(from_hour, from_minute)

                    # نهاية الدوام الطبيعي
                    to_time_val = time(16, 0)

                elif leave_type == 'late_arrival':
                    # تأخر - من بداية الدوام إلى وقت الوصول
                    from_time_val = time(8, 0)  # بداية الدوام

                    to_hour = random.randint(8, 9)
                    to_minute = random.choice([15, 30, 45])
                    to_time_val = time(to_hour, to_minute)

                else:  # personal
                    # مغادرة شخصية - أي وقت خلال الدوام
                    from_hour = random.randint(9, 14)
                    from_minute = random.choice([0, 30])
                    from_time_val = time(from_hour, from_minute)

                    duration_minutes = random.randint(min_minutes, max_minutes)
                    to_datetime = datetime.combine(leave_date, from_time_val) + timedelta(minutes=duration_minutes)
                    to_time_val = to_datetime.time()

                # الحالة
                if days_ago > 30:
                    status = random.choice(['approved', 'approved'])  # معظمها موافق عليها
                elif days_ago > 7:
                    status = random.choice(['approved', 'approved', 'rejected'])
                else:
                    status = random.choice(['pending', 'approved', 'rejected'])

                # هل يخصم من الراتب؟
                is_deductible = leave_type == 'late_arrival' or (leave_type == 'early_leave' and random.random() > 0.5)

                EarlyLeave.objects.create(
                    company=company,
                    employee=employee,
                    date=leave_date,
                    leave_type=leave_type,
                    from_time=from_time_val,
                    to_time=to_time_val,
                    reason=reason,
                    is_deductible=is_deductible,
                    status=status,
                    created_by=employee.created_by,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {count} مغادرة مبكرة'))

    def _create_biometric_device(self, company, branch):
        """إنشاء جهاز بصمة"""
        self.stdout.write('🖐️  إنشاء جهاز البصمة...')

        try:
            device, created = BiometricDevice.objects.get_or_create(
                company=company,
                ip_address='192.168.1.100',
                port=4370,
                defaults={
                    'serial_number': 'BIO-001',
                    'name': 'جهاز البصمة الرئيسي',
                    'branch': branch,
                    'location': 'المدخل الرئيسي',
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS('  ✓ تم إنشاء جهاز البصمة'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  جهاز البصمة موجود مسبقاً'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  تخطي جهاز البصمة: {str(e)}'))

    def _create_payroll_data(self, company, branch, employees):
        """إنشاء كشوفات رواتب تجريبية"""
        self.stdout.write('💼 إنشاء كشوفات الرواتب...')

        # الحصول على الموظفين النشطين فقط
        active_employees = [emp for emp in employees if emp.status == 'active']

        if not active_employees:
            self.stdout.write(self.style.WARNING('  ⚠️  لا يوجد موظفين نشطين'))
            return

        # إنشاء 3 كشوف رواتب (آخر 3 أشهر)
        today = date.today()
        payrolls_created = 0

        for months_ago in range(2, -1, -1):  # 2, 1, 0 (آخر 3 أشهر)
            # حساب الشهر والسنة
            target_date = today - timedelta(days=30 * months_ago)
            period_month = target_date.month
            period_year = target_date.year

            # تواريخ الفترة
            from_date = date(period_year, period_month, 1)
            if period_month == 12:
                to_date = date(period_year, 12, 31)
            else:
                to_date = date(period_year, period_month + 1, 1) - timedelta(days=1)

            # الحالة: الكشوف القديمة معتمدة ومدفوعة، الأخير قد يكون قيد المعالجة
            if months_ago >= 2:
                status = 'paid'
                approval_date = from_date + timedelta(days=random.randint(25, 28))
            elif months_ago == 1:
                status = 'approved'
                approval_date = from_date + timedelta(days=random.randint(25, 28))
            else:
                status = random.choice(['calculated', 'approved'])
                approval_date = None if status == 'calculated' else datetime.now()

            # رقم الكشف
            payroll_number = f'PR-{period_year}-{period_month:02d}-{branch.code}'

            try:
                # تحقق من عدم وجود كشف مسبق
                if Payroll.objects.filter(
                    company=company,
                    period_year=period_year,
                    period_month=period_month,
                    branch=branch
                ).exists():
                    continue
                # إنشاء كشف الراتب
                payroll = Payroll.objects.create(
                    company=company,
                    branch=branch,
                    number=payroll_number,
                    period_year=period_year,
                    period_month=period_month,
                    from_date=from_date,
                    to_date=to_date,
                    status=status,
                    approval_date=approval_date,
                    employee_count=len(active_employees),
                    created_by=active_employees[0].created_by,
                )

                # إنشاء تفاصيل الرواتب لكل موظف
                total_basic = Decimal('0')
                total_allowances = Decimal('0')
                total_deductions = Decimal('0')
                total_overtime = Decimal('0')
                total_loans = Decimal('0')

                for employee in active_employees:
                    # الراتب الأساسي
                    basic_salary = employee.basic_salary

                    # البدلات - مبلغ إجمالي
                    total_allowances_amt = Decimal(str(random.randint(200, 400)))

                    # أيام العمل
                    working_days = 30
                    actual_days = random.randint(28, 30)  # 28-30 يوم

                    # الخصومات - مبلغ إجمالي (تأمينات + ضرائب)
                    total_deductions_amt = basic_salary * Decimal('0.15')  # 15% تقريباً

                    # صافي الراتب
                    net_salary = basic_salary + total_allowances_amt - total_deductions_amt

                    # إنشاء تفاصيل الراتب
                    PayrollDetail.objects.create(
                        payroll=payroll,
                        employee=employee,
                        basic_salary=basic_salary,
                        working_days=working_days,
                        actual_days=actual_days,
                        total_allowances=total_allowances_amt,
                        total_deductions=total_deductions_amt,
                        net_salary=net_salary,
                    )

                    # تجميع الإجماليات
                    total_basic += basic_salary
                    total_allowances += total_allowances_amt
                    total_deductions += total_deductions_amt

                # تحديث إجماليات كشف الراتب
                payroll.total_basic = total_basic
                payroll.total_allowances = total_allowances
                payroll.total_deductions = total_deductions
                payroll.total_net = total_basic + total_allowances - total_deductions
                payroll.total_overtime = Decimal('0')
                payroll.total_loans = Decimal('0')
                payroll.total_social_security = total_deductions * Decimal('0.5')  # نصف الخصومات تقريباً
                payroll.total_income_tax = total_deductions * Decimal('0.3')  # ثلث الخصومات تقريباً
                payroll.save()

                payrolls_created += 1

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  خطأ في كشف {payroll_number}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {payrolls_created} كشف راتب'))

    def _print_summary(self, company, employees, departments):
        """طباعة ملخص البيانات"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 ملخص البيانات المنشأة'))
        self.stdout.write(self.style.SUCCESS('='*60))

        self.stdout.write(f'\n🏢 الشركة: {company.name}')
        self.stdout.write(f'👥 عدد الموظفين: {len(employees)}')
        self.stdout.write(f'🏢 عدد الأقسام: {len(departments)}')

        # إحصائيات الأقسام
        self.stdout.write(f'\n📊 توزيع الموظفين على الأقسام:')
        for dept in departments:
            emp_count = Employee.objects.filter(company=company, department=dept).count()
            self.stdout.write(f'  • {dept.name}: {emp_count} موظف')

        # متوسط الرواتب
        avg_salary = Employee.objects.filter(company=company).aggregate(
            models.Avg('basic_salary')
        )['basic_salary__avg']

        if avg_salary:
            self.stdout.write(f'\n💰 متوسط الرواتب: {avg_salary:.2f} دينار')

        # إحصائيات الحضور
        attendance_count = Attendance.objects.filter(company=company).count()
        self.stdout.write(f'\n⏰ سجلات الحضور: {attendance_count}')

        # إحصائيات الإجازات
        leave_requests = LeaveRequest.objects.filter(company=company)
        self.stdout.write(f'\n📝 طلبات الإجازات: {leave_requests.count()}')
        self.stdout.write(f'  • موافق عليها: {leave_requests.filter(status="approved").count()}')
        self.stdout.write(f'  • قيد المراجعة: {leave_requests.filter(status="pending").count()}')
        self.stdout.write(f'  • مرفوضة: {leave_requests.filter(status="rejected").count()}')

        # إحصائيات العمل الإضافي
        overtime_count = Overtime.objects.filter(company=company).count()
        total_overtime_hours = Overtime.objects.filter(company=company).aggregate(
            models.Sum('hours')
        )['hours__sum'] or 0
        self.stdout.write(f'\n⏱️  العمل الإضافي: {overtime_count} سجل ({total_overtime_hours} ساعة)')

        # إحصائيات السلف
        advances = Advance.objects.filter(company=company)
        total_advances = advances.aggregate(models.Sum('amount'))['amount__sum'] or 0
        self.stdout.write(f'\n💰 السلف: {advances.count()} سلفة (مجموع: {total_advances:.2f} دينار)')

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ تم الإنشاء بنجاح! البيانات جاهزة للعرض'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

    def _create_performance_data(self, company, employees, admin_user):
        """إنشاء بيانات التقييم والأداء"""
        self.stdout.write('📊 إنشاء بيانات التقييم والأداء...')

        # 1. فترات التقييم
        today = date.today()
        current_year = today.year

        periods = []
        for year_offset in range(2):  # السنة الحالية والسابقة
            year = current_year - year_offset

            # فترة سنوية
            period, created = PerformancePeriod.objects.get_or_create(
                company=company,
                name=f'التقييم السنوي {year}',
                year=year,
                defaults={
                    'period_type': 'annual',
                    'start_date': date(year, 1, 1),
                    'end_date': date(year, 12, 31),
                    'evaluation_start': date(year, 12, 1),
                    'evaluation_end': date(year, 12, 31),
                    'status': 'closed' if year_offset > 0 else 'active',
                    'created_by': admin_user,
                }
            )
            periods.append(period)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(periods)} فترة تقييم'))

        # 2. معايير التقييم
        criteria_data = [
            ('جودة العمل', 'competency', Decimal('2.0'), 'القدرة على إنجاز العمل بجودة عالية'),
            ('الالتزام بالوقت', 'behavior', Decimal('1.5'), 'الالتزام بمواعيد العمل والمهام'),
            ('العمل الجماعي', 'behavior', Decimal('1.5'), 'التعاون مع الزملاء والعمل ضمن فريق'),
            ('المبادرة والإبداع', 'competency', Decimal('2.0'), 'اقتراح أفكار جديدة وحلول مبتكرة'),
            ('الإنتاجية', 'objective', Decimal('2.5'), 'كمية ونوعية العمل المنجز'),
            ('مهارات التواصل', 'skill', Decimal('1.5'), 'القدرة على التواصل الفعال'),
        ]

        criteria = []
        for idx, (name, criteria_type, weight, description) in enumerate(criteria_data):
            criterion, created = PerformanceCriteria.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'description': description,
                    'criteria_type': criteria_type,
                    'weight': weight,
                    'max_score': Decimal('5.00'),
                    'is_required': True,
                    'applies_to_all': True,
                    'display_order': idx,
                }
            )
            criteria.append(criterion)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(criteria)} معيار تقييم'))

        # 3. تقييمات الموظفين
        evaluations_count = 0
        for period in periods:
            # تقييم 80% من الموظفين
            employees_to_evaluate = random.sample(list(employees), k=int(len(employees) * 0.8))

            for employee in employees_to_evaluate:
                # اختيار مقيّم (مدير من نفس القسم أو قسم آخر)
                potential_evaluators = [emp for emp in employees
                                       if emp != employee and emp.job_title.name in ['مدير', 'رئيس قسم', 'مشرف']]
                evaluator = random.choice(potential_evaluators) if potential_evaluators else None

                # حالة التقييم
                if period.status == 'closed':
                    status = 'approved'
                else:
                    status = random.choice(['draft', 'manager_evaluation', 'approved'])

                evaluation = PerformanceEvaluation.objects.create(
                    company=company,
                    employee=employee,
                    period=period,
                    evaluator=evaluator,
                    status=status,
                    self_comments='تقييم ذاتي: أرى أنني قدمت أداءً جيداً خلال هذه الفترة',
                    manager_comments='أداء جيد مع وجود مجالات للتحسين',
                    strengths='الالتزام، القدرة على حل المشكلات',
                    improvement_areas='تطوير مهارات التواصل',
                    goals_next_period='زيادة الإنتاجية بنسبة 10%',
                    self_evaluation_date=period.end_date if status != 'draft' else None,
                    manager_evaluation_date=period.end_date if status in ['manager_evaluation', 'approved'] else None,
                    approval_date=period.end_date if status == 'approved' else None,
                    approved_by=admin_user if status == 'approved' else None,
                    created_by=admin_user,
                )

                # تفاصيل التقييم لكل معيار
                for criterion in criteria:
                    self_score = Decimal(str(random.uniform(3.0, 5.0)))
                    manager_score = Decimal(str(random.uniform(2.5, 5.0))) if status != 'draft' else None

                    PerformanceEvaluationDetail.objects.create(
                        evaluation=evaluation,
                        criteria=criterion,
                        self_score=self_score,
                        manager_score=manager_score,
                        self_comments='أحاول بذل قصارى جهدي في هذا الجانب',
                        manager_comments='أداء مقبول' if manager_score else '',
                    )

                # حساب الدرجة النهائية
                evaluation.save()
                evaluations_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {evaluations_count} تقييم أداء'))

        # 4. أهداف الأداء
        goals_count = 0
        for employee in random.sample(list(employees), k=int(len(employees) * 0.7)):
            num_goals = random.randint(2, 4)

            goal_templates = [
                ('زيادة الإنتاجية', 'تحسين مستوى الإنتاجية', 'زيادة 10%', Decimal('100'), 'high'),
                ('تقليل الأخطاء', 'تقليل نسبة الأخطاء في العمل', 'أقل من 5%', Decimal('5'), 'medium'),
                ('تطوير المهارات', 'الحصول على شهادة مهنية', 'شهادة واحدة', Decimal('1'), 'high'),
                ('تحسين خدمة العملاء', 'رفع مستوى رضا العملاء', 'تقييم 90%', Decimal('90'), 'critical'),
                ('إنجاز المشاريع', 'إنجاز المشاريع في الموعد', '100% التزام', Decimal('100'), 'high'),
            ]

            for _ in range(num_goals):
                title, description, key_results, target_value, priority = random.choice(goal_templates)

                start_date = today - timedelta(days=random.randint(30, 180))
                due_date = start_date + timedelta(days=random.randint(90, 365))

                progress = Decimal(str(random.randint(0, 100)))
                achieved_value = (target_value * progress / 100) if target_value else None

                status_choices = ['active', 'in_progress', 'completed']
                weights = [0.3, 0.5, 0.2]  # احتماليات الحالات
                status = random.choices(status_choices, weights=weights)[0]

                PerformanceGoal.objects.create(
                    company=company,
                    employee=employee,
                    period=periods[0] if periods else None,
                    title=title,
                    description=description,
                    key_results=key_results,
                    priority=priority,
                    status=status,
                    weight=Decimal('1.00'),
                    target_value=target_value,
                    achieved_value=achieved_value,
                    progress_percentage=progress,
                    start_date=start_date,
                    due_date=due_date,
                    completion_date=today if status == 'completed' else None,
                    assigned_by=random.choice([emp for emp in employees if emp != employee]),
                )
                goals_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {goals_count} هدف أداء'))

        # 5. ملاحظات الأداء
        notes_count = 0
        note_templates = [
            ('achievement', 'إنجاز متميز', 'قام بإنجاز المشروع قبل الموعد المحدد'),
            ('recognition', 'تقدير', 'أظهر التزاماً عالياً في العمل'),
            ('feedback', 'ملاحظة', 'يحتاج إلى تحسين مهارات التواصل'),
            ('improvement', 'تحسين مطلوب', 'يجب الالتزام بمواعيد الاجتماعات'),
            ('achievement', 'مبادرة مميزة', 'اقترح فكرة أدت لتحسين الأداء'),
        ]

        for employee in random.sample(list(employees), k=int(len(employees) * 0.5)):
            num_notes = random.randint(1, 3)

            for _ in range(num_notes):
                note_type, title, description = random.choice(note_templates)
                note_date = today - timedelta(days=random.randint(1, 180))

                noted_by = random.choice([emp for emp in employees if emp != employee])

                PerformanceNote.objects.create(
                    company=company,
                    employee=employee,
                    note_type=note_type,
                    title=title,
                    description=description,
                    date=note_date,
                    noted_by=noted_by,
                    is_visible_to_employee=note_type != 'warning',
                    created_by=admin_user,
                )
                notes_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {notes_count} ملاحظة أداء'))

    def _create_training_data(self, company, employees, departments, job_titles, admin_user):
        """إنشاء بيانات التدريب والتطوير"""
        self.stdout.write('🎓 إنشاء بيانات التدريب والتطوير...')

        # 1. فئات التدريب
        categories_data = [
            ('المهارات الإدارية', 'Management Skills'),
            ('المهارات التقنية', 'Technical Skills'),
            ('المهارات الشخصية', 'Soft Skills'),
            ('اللغات', 'Languages'),
            ('السلامة والصحة المهنية', 'Health & Safety'),
            ('البرامج الحاسوبية', 'Computer Programs'),
        ]

        categories = []
        for name, name_en in categories_data:
            category, created = TrainingCategory.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'name_en': name_en,
                    'description': f'دورات في مجال {name}',
                }
            )
            categories.append(category)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(categories)} فئة تدريب'))

        # 2. مزودي التدريب
        providers_data = [
            ('الأكاديمية الوطنية', 'external', 'د. محمد العلي', '0791234567', 'info@academy.com', Decimal('4.5')),
            ('مركز التطوير المهني', 'institute', 'أ. سارة أحمد', '0797654321', 'contact@devcenter.com', Decimal('4.2')),
            ('قسم التدريب الداخلي', 'internal', '', '', '', Decimal('4.0')),
            ('منصة التعلم الإلكتروني', 'online', '', '', 'support@elearning.com', Decimal('4.7')),
        ]

        providers = []
        for name, provider_type, contact, phone, email, rating in providers_data:
            provider, created = TrainingProvider.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'provider_type': provider_type,
                    'contact_person': contact,
                    'phone': phone,
                    'email': email,
                    'rating': rating,
                    'specializations': 'تدريب احترافي في مختلف المجالات',
                }
            )
            providers.append(provider)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(providers)} مزود تدريب'))

        # 3. الدورات التدريبية
        courses_data = [
            ('MGT-101', 'مهارات القيادة الفعالة', 'Leadership Skills', categories[0], 'mandatory', 'classroom', 20, 3, 'قاعة التدريب', 15, 5, Decimal('500')),
            ('TECH-201', 'أساسيات البرمجة', 'Programming Basics', categories[1], 'optional', 'online', 40, 5, 'منصة إلكترونية', 20, 8, Decimal('800')),
            ('SOFT-301', 'مهارات التواصل', 'Communication Skills', categories[2], 'mandatory', 'blended', 16, 2, 'قاعة التدريب', 12, 5, Decimal('400')),
            ('LANG-401', 'اللغة الإنجليزية المتقدمة', 'Advanced English', categories[3], 'optional', 'classroom', 30, 4, 'قاعة التدريب', 10, 5, Decimal('600')),
            ('SAFE-501', 'السلامة في مكان العمل', 'Workplace Safety', categories[4], 'mandatory', 'workshop', 8, 1, 'قاعة المؤتمرات', 30, 10, Decimal('200')),
            ('IT-601', 'برنامج Excel المتقدم', 'Advanced Excel', categories[5], 'certification', 'classroom', 24, 3, 'معمل الحاسوب', 15, 5, Decimal('450')),
        ]

        today = date.today()
        courses = []

        for idx, course_data in enumerate(courses_data):
            code, name, name_en, category, course_type, delivery, duration_hours, duration_days, location, max_part, min_part, cost = course_data

            # تواريخ متنوعة: ماضية، جارية، مستقبلية
            if idx % 3 == 0:  # دورة ماضية
                start_date = today - timedelta(days=random.randint(60, 180))
                status = 'completed'
            elif idx % 3 == 1:  # دورة جارية
                start_date = today - timedelta(days=random.randint(1, 10))
                status = 'in_progress'
            else:  # دورة مستقبلية
                start_date = today + timedelta(days=random.randint(10, 90))
                status = 'open'

            end_date = start_date + timedelta(days=duration_days)

            # اختيار مدرب من الموظفين
            potential_trainers = [emp for emp in employees if 'مدير' in emp.job_title.name or 'رئيس' in emp.job_title.name]
            trainer_employee = random.choice(potential_trainers) if potential_trainers else None

            course, created = TrainingCourse.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'name_en': name_en,
                    'description': f'دورة تدريبية في {name}',
                    'objectives': 'تطوير المهارات والمعارف في المجال',
                    'category': category,
                    'provider': random.choice(providers),
                    'course_type': course_type,
                    'delivery_method': delivery,
                    'status': status,
                    'start_date': start_date,
                    'end_date': end_date,
                    'duration_hours': duration_hours,
                    'duration_days': duration_days,
                    'location': location,
                    'max_participants': max_part,
                    'min_participants': min_part,
                    'cost_per_participant': cost,
                    'total_budget': cost * Decimal(max_part),
                    'trainer_name': 'د. أحمد محمود' if not trainer_employee else '',
                    'trainer_employee': trainer_employee,
                    'certificate_issued': course_type == 'certification',
                    'created_by': admin_user,
                }
            )

            # إضافة الأقسام المستهدفة
            target_depts = random.sample(list(departments), k=random.randint(1, 3))
            course.target_departments.set(target_depts)

            courses.append(course)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(courses)} دورة تدريبية'))

        # 4. تسجيل الموظفين في الدورات
        enrollments_count = 0
        for course in courses:
            # عدد المسجلين (50-90% من الحد الأقصى)
            num_enrollments = random.randint(
                int(course.max_participants * 0.5),
                int(course.max_participants * 0.9)
            )

            enrolled_employees = random.sample(list(employees), k=min(num_enrollments, len(employees)))

            for employee in enrolled_employees:
                # تحديد الحالة بناءً على حالة الدورة
                if course.status == 'completed':
                    status = random.choice(['completed', 'completed', 'completed', 'no_show'])
                elif course.status == 'in_progress':
                    status = random.choice(['attending', 'enrolled'])
                else:  # open or planned
                    status = random.choice(['nominated', 'approved', 'enrolled'])

                # التواريخ
                enrollment_date = course.start_date - timedelta(days=random.randint(7, 30))
                completion_date = course.end_date if status == 'completed' else None

                # الدرجة والحضور
                attendance_pct = Decimal(str(random.randint(80, 100))) if status in ['completed', 'attending'] else None
                score = Decimal(str(random.uniform(70, 100))) if status == 'completed' else None
                grade = 'ممتاز' if score and score >= 90 else ('جيد جداً' if score and score >= 80 else 'جيد') if score else ''

                enrollment = TrainingEnrollment.objects.create(
                    company=company,
                    course=course,
                    employee=employee,
                    status=status,
                    nominated_by=random.choice([emp for emp in employees if emp != employee]),
                    approved_by=admin_user if status in ['approved', 'enrolled', 'attending', 'completed'] else None,
                    approval_date=enrollment_date if status in ['approved', 'enrolled', 'attending', 'completed'] else None,
                    enrollment_date=enrollment_date if status in ['enrolled', 'attending', 'completed'] else None,
                    completion_date=completion_date,
                    attendance_percentage=attendance_pct,
                    score=score,
                    grade=grade,
                    certificate_number=f'CERT-{course.code}-{random.randint(1000, 9999)}' if status == 'completed' and course.certificate_issued else '',
                    certificate_date=completion_date if status == 'completed' and course.certificate_issued else None,
                    actual_cost=course.cost_per_participant,
                )
                enrollments_count += 1

                # إضافة تقييم للدورات المكتملة
                if status == 'completed':
                    TrainingFeedback.objects.create(
                        enrollment=enrollment,
                        content_rating=random.randint(3, 5),
                        trainer_rating=random.randint(3, 5),
                        materials_rating=random.randint(3, 5),
                        organization_rating=random.randint(3, 5),
                        relevance_rating=random.randint(3, 5),
                        overall_rating=random.randint(3, 5),
                        strengths='محتوى قيم ومفيد، مدرب محترف',
                        improvements='يحتاج لمزيد من الأمثلة العملية',
                        knowledge_gained='اكتسبت مهارات جديدة مفيدة للعمل',
                        application_plan='سأطبق ما تعلمته في مشاريعي القادمة',
                        would_recommend=True,
                    )

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {enrollments_count} تسجيل تدريب'))

        # 5. طلبات التدريب
        requests_count = 0
        for employee in random.sample(list(employees), k=int(len(employees) * 0.4)):
            num_requests = random.randint(1, 2)

            for _ in range(num_requests):
                course = random.choice(courses)
                request_type = random.choice(['self', 'manager', 'hr'])
                status = random.choice(['pending', 'manager_approved', 'approved', 'rejected'])

                request_date = today - timedelta(days=random.randint(1, 60))

                TrainingRequest.objects.create(
                    company=company,
                    employee=employee,
                    request_type=request_type,
                    status=status,
                    course=course if random.random() < 0.8 else None,
                    custom_course_name='دورة خاصة' if not course or random.random() > 0.8 else '',
                    training_category=course.category if course else random.choice(categories),
                    justification='أحتاج هذا التدريب لتطوير مهاراتي في مجال عملي',
                    expected_benefits='سيساعدني على تحسين أدائي وإنتاجيتي',
                    preferred_date_from=today + timedelta(days=30),
                    preferred_date_to=today + timedelta(days=90),
                    estimated_cost=Decimal(str(random.randint(300, 1000))),
                    manager_comments='موافق على الطلب' if status != 'pending' else '',
                    hr_comments='معتمد' if status == 'approved' else ('مرفوض لعدم توفر الميزانية' if status == 'rejected' else ''),
                    manager_approved_by=admin_user if status in ['manager_approved', 'approved'] else None,
                    manager_approved_date=request_date + timedelta(days=3) if status in ['manager_approved', 'approved'] else None,
                    hr_approved_by=admin_user if status == 'approved' else None,
                    hr_approved_date=request_date + timedelta(days=7) if status == 'approved' else None,
                    rejection_reason='لا توجد ميزانية كافية' if status == 'rejected' else '',
                    created_by=admin_user,
                )
                requests_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {requests_count} طلب تدريب'))

        # 6. خطة التدريب السنوية
        current_year = today.year

        training_plan = TrainingPlan.objects.create(
            company=company,
            name=f'خطة التدريب لعام {current_year}',
            year=current_year,
            department=None,  # خطة على مستوى الشركة
            status='approved',
            total_budget=Decimal('50000'),
            allocated_budget=Decimal('45000'),
            spent_budget=Decimal('25000'),
            objectives='تطوير مهارات الموظفين وزيادة كفاءتهم',
            approved_by=admin_user,
            approved_date=date(current_year, 1, 15),
            created_by=admin_user,
        )

        # بنود خطة التدريب
        plan_items_count = 0
        for idx, course in enumerate(courses[:4]):  # 4 دورات في الخطة
            quarter = (idx % 4) + 1

            item = TrainingPlanItem.objects.create(
                plan=training_plan,
                course=course,
                category=course.category,
                target_employees_count=random.randint(10, 25),
                priority=random.choice(['high', 'medium', 'critical']),
                planned_quarter=quarter,
                planned_budget=course.total_budget,
                actual_budget=course.total_budget * Decimal('0.95') if course.status == 'completed' else Decimal('0'),
                is_completed=course.status == 'completed',
            )
            item.target_departments.set(random.sample(list(departments), k=2))
            plan_items_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء خطة تدريب مع {plan_items_count} بند'))

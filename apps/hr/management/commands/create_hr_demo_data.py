# apps/hr/management/commands/create_hr_demo_data.py
"""
أمر لإنشاء بيانات تجريبية لنظام الموارد البشرية
Management command to create HR demo data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    # Organization
    Department, JobGrade, JobTitle,
    # Employee
    Employee, EmployeeDocument,
    # Contract
    EmployeeContract, SalaryIncrement,
    # Settings
    HRSettings, SocialSecuritySettings, LeaveType, PayrollAccountMapping,
    # Attendance
    Attendance, LeaveBalance, LeaveRequest, Overtime, Advance, AdvanceInstallment,
    # Payroll
    Payroll, PayrollDetail,
    # Biometric
    BiometricDevice, EmployeeBiometricMapping,
    # Performance
    PerformancePeriod, PerformanceCriteria,
    # Training
    TrainingCategory, TrainingProvider, TrainingCourse,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية لنظام الموارد البشرية - Create HR demo data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف الشركة - Company ID (default: first company)',
        )
        parser.add_argument(
            '--employees',
            type=int,
            default=20,
            help='عدد الموظفين - Number of employees to create (default: 20)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 بدء إنشاء بيانات تجريبية للموارد البشرية...'))

        # Get company
        company_id = options.get('company_id')
        if company_id:
            try:
                self.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ الشركة {company_id} غير موجودة'))
                return
        else:
            self.company = Company.objects.first()
            if not self.company:
                self.stdout.write(self.style.ERROR('❌ لا توجد شركات في النظام'))
                return

        self.branch = Branch.objects.filter(company=self.company).first()
        if not self.branch:
            self.stdout.write(self.style.ERROR('❌ لا توجد فروع للشركة'))
            return

        self.currency = Currency.objects.filter(is_base=True).first()
        self.num_employees = options.get('employees', 20)

        # Get or create a default user for created_by field
        from apps.core.models import User
        self.user = User.objects.filter(is_superuser=True).first()
        if not self.user:
            self.user = User.objects.first()
        if not self.user:
            self.stdout.write(self.style.ERROR('❌ لا يوجد مستخدمين في النظام'))
            return

        self.stdout.write(f'📊 الشركة: {self.company.name}')
        self.stdout.write(f'📍 الفرع: {self.branch.name}')
        self.stdout.write(f'👥 عدد الموظفين: {self.num_employees}')

        # Create data
        self.create_settings()
        self.create_departments()
        self.create_job_grades()
        self.create_job_titles()
        self.create_leave_types()
        self.create_employees()
        self.create_contracts()
        self.create_attendance_records()
        self.create_leave_balances()
        self.create_leave_requests()
        self.create_overtime_records()
        self.create_advances()
        self.create_salary_increments()
        self.create_biometric_devices()
        self.create_performance_data()
        self.create_training_data()

        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء البيانات التجريبية بنجاح!'))

    def create_settings(self):
        """إنشاء إعدادات الموارد البشرية"""
        self.stdout.write('⚙️  إنشاء الإعدادات...')

        # HR Settings
        self.hr_settings, created = HRSettings.objects.get_or_create(
            company=self.company,
            defaults={
                'default_working_hours_per_day': 8,
                'default_working_days_per_month': 22,
                'overtime_regular_rate': Decimal('1.25'),
                'overtime_holiday_rate': Decimal('2.00'),
                'default_annual_leave_days': 14,
                'default_sick_leave_days': 14,
                'carry_forward_leave': True,
                'max_carry_forward_days': 5,
                'default_probation_period': 90,
                'default_notice_period': 30,
                'max_advance_percentage': 50,
                'max_advance_installments': 12,
                'fiscal_year_start_month': 1,
                'auto_create_journal_entries': False,
            }
        )

        # Social Security Settings
        self.ss_settings, created = SocialSecuritySettings.objects.get_or_create(
            company=self.company,
            defaults={
                'employee_contribution_rate': Decimal('7.50'),
                'company_contribution_rate': Decimal('14.25'),
                'minimum_insurable_salary': Decimal('220'),
                'maximum_insurable_salary': Decimal('3500'),
            }
        )

        self.stdout.write(self.style.SUCCESS('  ✓ تم إنشاء الإعدادات'))

    def create_departments(self):
        """إنشاء الأقسام"""
        self.stdout.write('🏢 إنشاء الأقسام...')

        departments_data = [
            {'code': 'IT', 'name': 'تقنية المعلومات', 'name_en': 'Information Technology'},
            {'code': 'HR', 'name': 'الموارد البشرية', 'name_en': 'Human Resources'},
            {'code': 'FIN', 'name': 'المالية', 'name_en': 'Finance'},
            {'code': 'SAL', 'name': 'المبيعات', 'name_en': 'Sales'},
            {'code': 'OPS', 'name': 'العمليات', 'name_en': 'Operations'},
            {'code': 'MKT', 'name': 'التسويق', 'name_en': 'Marketing'},
        ]

        self.departments = []
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                company=self.company,
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'name_en': dept_data['name_en'],
                }
            )
            self.departments.append(dept)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.departments)} قسم'))

    def create_job_grades(self):
        """إنشاء الدرجات الوظيفية"""
        self.stdout.write('📊 إنشاء الدرجات الوظيفية...')

        grades_data = [
            {'code': 'JR', 'name': 'مبتدئ', 'name_en': 'Junior', 'level': 1,
             'min_salary': 400, 'max_salary': 600, 'annual_leave': 14, 'sick_leave': 14},
            {'code': 'MID', 'name': 'متوسط', 'name_en': 'Mid-Level', 'level': 2,
             'min_salary': 600, 'max_salary': 900, 'annual_leave': 18, 'sick_leave': 14},
            {'code': 'SR', 'name': 'كبير', 'name_en': 'Senior', 'level': 3,
             'min_salary': 900, 'max_salary': 1500, 'annual_leave': 21, 'sick_leave': 14},
            {'code': 'LEAD', 'name': 'قائد', 'name_en': 'Lead', 'level': 4,
             'min_salary': 1200, 'max_salary': 2000, 'annual_leave': 25, 'sick_leave': 14},
            {'code': 'MGR', 'name': 'مدير', 'name_en': 'Manager', 'level': 5,
             'min_salary': 1800, 'max_salary': 3000, 'annual_leave': 30, 'sick_leave': 14},
        ]

        self.job_grades = []
        for grade_data in grades_data:
            grade, created = JobGrade.objects.get_or_create(
                company=self.company,
                code=grade_data['code'],
                defaults={
                    'name': grade_data['name'],
                    'name_en': grade_data['name_en'],
                    'level': grade_data['level'],
                    'min_salary': grade_data['min_salary'],
                    'max_salary': grade_data['max_salary'],
                    'annual_leave_days': grade_data['annual_leave'],
                    'sick_leave_days': grade_data['sick_leave'],
                }
            )
            self.job_grades.append(grade)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.job_grades)} درجة وظيفية'))

    def create_job_titles(self):
        """إنشاء المسميات الوظيفية"""
        self.stdout.write('💼 إنشاء المسميات الوظيفية...')

        titles_data = [
            {'code': 'DEV', 'name': 'مطور برمجيات', 'name_en': 'Software Developer', 'dept_code': 'IT'},
            {'code': 'DBA', 'name': 'مسؤول قواعد بيانات', 'name_en': 'Database Administrator', 'dept_code': 'IT'},
            {'code': 'HRSP', 'name': 'أخصائي موارد بشرية', 'name_en': 'HR Specialist', 'dept_code': 'HR'},
            {'code': 'ACC', 'name': 'محاسب', 'name_en': 'Accountant', 'dept_code': 'FIN'},
            {'code': 'SALES', 'name': 'مندوب مبيعات', 'name_en': 'Sales Representative', 'dept_code': 'SAL'},
            {'code': 'MKTSP', 'name': 'أخصائي تسويق', 'name_en': 'Marketing Specialist', 'dept_code': 'MKT'},
        ]

        self.job_titles = []
        for title_data in titles_data:
            dept = next((d for d in self.departments if d.code == title_data['dept_code']), None)
            if dept:
                grade = random.choice(self.job_grades[:3])  # Random grade from junior to senior
                title, created = JobTitle.objects.get_or_create(
                    company=self.company,
                    code=title_data['code'],
                    defaults={
                        'name': title_data['name'],
                        'name_en': title_data['name_en'],
                        'department': dept,
                        'job_grade': grade,
                        'min_salary': grade.min_salary,
                        'max_salary': grade.max_salary,
                    }
                )
                self.job_titles.append(title)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.job_titles)} مسمى وظيفي'))

    def create_leave_types(self):
        """إنشاء أنواع الإجازات"""
        self.stdout.write('🏖️  إنشاء أنواع الإجازات...')

        leave_types_data = [
            {'code': 'ANN', 'name': 'إجازة سنوية', 'name_en': 'Annual Leave',
             'is_paid': True, 'default_days': 14},
            {'code': 'SICK', 'name': 'إجازة مرضية', 'name_en': 'Sick Leave',
             'is_paid': True, 'default_days': 14, 'requires_attachment': True},
            {'code': 'UNPD', 'name': 'إجازة بدون راتب', 'name_en': 'Unpaid Leave',
             'is_paid': False, 'default_days': 0, 'affects_salary': True},
            {'code': 'MAT', 'name': 'إجازة أمومة', 'name_en': 'Maternity Leave',
             'is_paid': True, 'default_days': 70, 'requires_attachment': True},
        ]

        self.leave_types = []
        for lt_data in leave_types_data:
            lt, created = LeaveType.objects.get_or_create(
                company=self.company,
                code=lt_data['code'],
                defaults={
                    'name': lt_data['name'],
                    'name_en': lt_data['name_en'],
                    'is_paid': lt_data['is_paid'],
                    'default_days': lt_data['default_days'],
                    'requires_approval': True,
                    'affects_salary': lt_data.get('affects_salary', False),
                    'requires_attachment': lt_data.get('requires_attachment', False),
                    'max_consecutive_days': 10,
                    'allow_negative_balance': False,
                    'carry_forward': True,
                    'max_carry_forward': lt_data['default_days'],
                }
            )
            self.leave_types.append(lt)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.leave_types)} نوع إجازة'))

    def create_employees(self):
        """إنشاء الموظفين"""
        self.stdout.write(f'👥 إنشاء {self.num_employees} موظف...')

        first_names_ar = ['أحمد', 'محمد', 'علي', 'خالد', 'سعيد', 'عمر', 'يوسف', 'حسن',
                          'فاطمة', 'عائشة', 'مريم', 'زينب', 'نور', 'سارة', 'ليلى', 'هند']
        last_names_ar = ['العلي', 'المحمد', 'الخطيب', 'النجار', 'السعدي', 'القاسم', 'الزعبي', 'الحداد']

        first_names_en = ['Ahmad', 'Mohammed', 'Ali', 'Khaled', 'Saeed', 'Omar', 'Youssef', 'Hassan',
                          'Fatima', 'Aisha', 'Mariam', 'Zainab', 'Nour', 'Sara', 'Laila', 'Hind']
        last_names_en = ['Alali', 'Almohammed', 'Alkhatib', 'Alnajjar', 'Alsaadi', 'Alqasem', 'Alzubi', 'Alhaddad']

        self.employees = []

        for i in range(self.num_employees):
            idx = i % len(first_names_ar)

            first_name_ar = first_names_ar[idx]
            last_name_ar = last_names_ar[i % len(last_names_ar)]
            first_name_en = first_names_en[idx]
            last_name_en = last_names_en[i % len(last_names_en)]

            # Random hire date in the last 2 years
            days_ago = random.randint(30, 730)
            hire_date = (timezone.now() - timedelta(days=days_ago)).date()

            # Random birth date (25-50 years old)
            birth_year = timezone.now().year - random.randint(25, 50)
            birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))

            job_title = random.choice(self.job_titles)
            department = job_title.department
            job_grade = job_title.job_grade

            # Random salary within grade range
            salary = random.randint(int(job_grade.min_salary), int(job_grade.max_salary))

            employee = Employee.objects.create(
                company=self.company,
                branch=self.branch,
                created_by=self.user,
                first_name=first_name_ar,
                middle_name='محمد',
                last_name=last_name_ar,
                full_name_en=f'{first_name_en} Mohammed {last_name_en}',
                date_of_birth=birth_date,
                national_id=f'20{birth_year-2000:02d}{random.randint(100000, 999999)}',
                nationality='jordanian',
                gender=random.choice(['male', 'female']),
                marital_status=random.choice(['single', 'married', 'divorced', 'widowed']),
                mobile=f'079{random.randint(1000000, 9999999)}',
                email=f'{first_name_en.lower()}.{last_name_en.lower()}@company.com',
                hire_date=hire_date,
                department=department,
                job_title=job_title,
                job_grade=job_grade,
                employment_status='full_time',
                status='active',
                basic_salary=salary,
                fuel_allowance=50,
                other_allowances=random.choice([0, 25, 50, 75]),
                social_security_salary=salary,
                working_hours_per_day=8,
                working_days_per_month=22,
                annual_leave_balance=job_grade.annual_leave_days,
                sick_leave_balance=job_grade.sick_leave_days,
                bank_name='البنك العربي',
                bank_account=f'{random.randint(100000000, 999999999)}',
                currency=self.currency,
            )
            self.employees.append(employee)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.employees)} موظف'))

    def create_contracts(self):
        """إنشاء عقود الموظفين"""
        self.stdout.write('📄 إنشاء عقود الموظفين...')

        self.contracts = []
        for employee in self.employees:
            contract = EmployeeContract.objects.create(
                company=self.company,
                created_by=self.user,
                employee=employee,
                contract_type=random.choice(['fixed_term', 'indefinite', 'temporary', 'probation']),
                start_date=employee.hire_date,
                end_date=employee.hire_date + timedelta(days=365) if random.random() > 0.5 else None,
                contract_salary=employee.basic_salary,
                probation_period=90 if random.random() > 0.5 else 0,
                notice_period=30,
                status='active',
            )
            self.contracts.append(contract)

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.contracts)} عقد'))

    def create_attendance_records(self):
        """إنشاء سجلات الحضور"""
        self.stdout.write('📅 إنشاء سجلات الحضور (آخر 30 يوم)...')

        attendance_count = 0
        today = timezone.now().date()

        for employee in self.employees:
            # Create attendance for last 30 days
            for day_offset in range(30):
                attendance_date = today - timedelta(days=day_offset)

                # Skip weekends (Friday)
                if attendance_date.weekday() == 4:  # Friday
                    continue

                # Random attendance status
                if random.random() > 0.1:  # 90% present
                    check_in_time = datetime.combine(attendance_date, datetime.min.time()) + timedelta(hours=8, minutes=random.randint(0, 30))
                    check_out_time = check_in_time + timedelta(hours=8, minutes=random.randint(0, 60))

                    working_hours = (check_out_time - check_in_time).total_seconds() / 3600
                    late_minutes = max(0, (check_in_time.hour - 8) * 60 + check_in_time.minute)

                    Attendance.objects.create(
                        company=self.company,
                        employee=employee,
                        date=attendance_date,
                        check_in=check_in_time.time(),
                        check_out=check_out_time.time(),
                        status='late' if late_minutes > 0 else 'present',
                        working_hours=working_hours,
                        late_minutes=late_minutes,
                    )
                    attendance_count += 1
                elif random.random() > 0.5:  # Some absences
                    Attendance.objects.create(
                        company=self.company,
                        employee=employee,
                        date=attendance_date,
                        status='absent',
                    )
                    attendance_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {attendance_count} سجل حضور'))

    def create_leave_balances(self):
        """إنشاء أرصدة الإجازات"""
        self.stdout.write('📊 إنشاء أرصدة الإجازات...')

        current_year = timezone.now().year
        balance_count = 0

        for employee in self.employees:
            for leave_type in self.leave_types[:2]:  # Annual and Sick only
                LeaveBalance.objects.create(
                    company=self.company,
                    employee=employee,
                    leave_type=leave_type,
                    year=current_year,
                    opening_balance=leave_type.default_days,
                    used=random.randint(0, leave_type.default_days // 2),
                )
                balance_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {balance_count} رصيد إجازة'))

    def create_leave_requests(self):
        """إنشاء طلبات الإجازات"""
        self.stdout.write('🏖️  إنشاء طلبات إجازات...')

        leave_count = 0
        annual_leave = self.leave_types[0]  # Annual leave

        # Create 2-3 leave requests per employee
        for employee in self.employees:
            num_requests = random.randint(2, 3)
            for _ in range(num_requests):
                days_ago = random.randint(10, 60)
                start_date = (timezone.now() - timedelta(days=days_ago)).date()
                days = random.randint(2, 5)

                leave_request = LeaveRequest.objects.create(
                    company=self.company,
                    employee=employee,
                    leave_type=annual_leave,
                    start_date=start_date,
                    end_date=start_date + timedelta(days=days),
                    days=days,
                    reason='إجازة شخصية',
                    status=random.choice(['pending', 'approved', 'approved']),  # More approved
                )
                leave_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {leave_count} طلب إجازة'))

    def create_overtime_records(self):
        """إنشاء سجلات العمل الإضافي"""
        self.stdout.write('⏰ إنشاء سجلات العمل الإضافي...')

        overtime_count = 0

        # 30% of employees have overtime
        overtime_employees = random.sample(self.employees, k=int(self.num_employees * 0.3))

        for employee in overtime_employees:
            # 1-3 overtime records per employee
            num_records = random.randint(1, 3)
            for _ in range(num_records):
                days_ago = random.randint(1, 30)
                overtime_date = (timezone.now() - timedelta(days=days_ago)).date()
                hours = random.choice([1, 2, 3, 4])

                Overtime.objects.create(
                    company=self.company,
                    employee=employee,
                    date=overtime_date,
                    start_time=datetime.min.time().replace(hour=17),
                    end_time=datetime.min.time().replace(hour=17 + hours),
                    hours=hours,
                    overtime_type='regular',
                    rate=self.hr_settings.overtime_regular_rate,
                    amount=Decimal(hours) * employee.hourly_rate * self.hr_settings.overtime_regular_rate,
                    status=random.choice(['approved', 'paid']),
                )
                overtime_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {overtime_count} سجل عمل إضافي'))

    def create_advances(self):
        """إنشاء السلف والقروض"""
        self.stdout.write('💰 إنشاء السلف والقروض...')

        advance_count = 0

        # 20% of employees have advances
        advance_employees = random.sample(self.employees, k=int(self.num_employees * 0.2))

        for employee in advance_employees:
            amount = random.randint(100, 500)
            installments = random.choice([3, 6, 12])

            try:
                advance = Advance.objects.create(
                    company=self.company,
                    employee=employee,
                    advance_type=random.choice(['salary_advance', 'loan']),
                    request_date=timezone.now().date() - timedelta(days=random.randint(10, 60)),
                    amount=amount,
                    installments=installments,
                    installment_amount=Decimal(amount) / installments,
                    start_deduction_date=timezone.now().date() + timedelta(days=30),
                    status=random.choice(['approved', 'disbursed']),
                    paid_amount=0,
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  تخطي سلفة للموظف {employee}: {str(e)}'))
                continue

            # Create installments
            for i in range(installments):
                AdvanceInstallment.objects.create(
                    advance=advance,
                    installment_number=i + 1,
                    due_date=advance.start_deduction_date + timedelta(days=30 * i),
                    amount=advance.installment_amount,
                    status='pending',
                )

            advance_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {advance_count} سلفة/قرض'))

    def create_salary_increments(self):
        """إنشاء العلاوات"""
        self.stdout.write('📈 إنشاء العلاوات...')

        increment_count = 0

        # 15% of employees get increments
        increment_employees = random.sample(self.employees, k=int(self.num_employees * 0.15))

        for employee in increment_employees:
            increment_amount = Decimal(random.choice([25, 50, 75, 100]))

            SalaryIncrement.objects.create(
                company=self.company,
                employee=employee,
                increment_type=random.choice(['annual', 'merit', 'promotion']),
                old_salary=employee.basic_salary,
                is_percentage=False,
                increment_amount=increment_amount,
                new_salary=employee.basic_salary + increment_amount,
                effective_date=timezone.now().date() + timedelta(days=30),
                status=random.choice(['pending', 'approved']),
                reason='أداء متميز',
            )
            increment_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {increment_count} علاوة'))

    def create_biometric_devices(self):
        """إنشاء أجهزة البصمة"""
        self.stdout.write('🖐️  إنشاء أجهزة البصمة...')

        devices_data = [
            {'name': 'جهاز المدخل الرئيسي', 'ip': '192.168.1.100', 'location': 'المدخل الرئيسي'},
            {'name': 'جهاز الطابق الثاني', 'ip': '192.168.1.101', 'location': 'الطابق الثاني'},
        ]

        self.biometric_devices = []
        for device_data in devices_data:
            device, created = BiometricDevice.objects.get_or_create(
                company=self.company,
                ip_address=device_data['ip'],
                port=4370,
                defaults={
                    'branch': self.branch,
                    'name': device_data['name'],
                    'device_type': 'zkteco',
                    'connection_type': 'tcp',
                    'location': device_data['location'],
                    'status': 'active',
                    'auto_sync': True,
                    'sync_interval': 60,
                }
            )
            self.biometric_devices.append(device)

            # Map some employees to device
            for i, employee in enumerate(self.employees[:10]):
                EmployeeBiometricMapping.objects.get_or_create(
                    device=device,
                    device_user_id=str(i + 1),
                    defaults={
                        'company': self.company,
                        'employee': employee,
                        'is_enrolled': True,
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'  ✓ تم إنشاء {len(self.biometric_devices)} جهاز بصمة'))

    def create_performance_data(self):
        """إنشاء بيانات التقييم"""
        self.stdout.write('⭐ إنشاء بيانات التقييم...')

        # Create performance period
        current_year = timezone.now().year
        period, created = PerformancePeriod.objects.get_or_create(
            company=self.company,
            name=f'التقييم السنوي {current_year}',
            year=current_year,
            defaults={
                'period_type': 'annual',
                'start_date': date(current_year, 1, 1),
                'end_date': date(current_year, 12, 31),
                'evaluation_start': date(current_year, 12, 1),
                'evaluation_end': date(current_year, 12, 31),
                'status': 'active',
                'created_by': self.user,
            }
        )

        # Create criteria
        criteria_data = [
            {'name': 'جودة العمل', 'name_en': 'Work Quality', 'type': 'competency', 'weight': 30},
            {'name': 'الالتزام بالمواعيد', 'name_en': 'Punctuality', 'type': 'behavior', 'weight': 20},
            {'name': 'التعاون مع الفريق', 'name_en': 'Teamwork', 'type': 'behavior', 'weight': 25},
            {'name': 'المهارات التقنية', 'name_en': 'Technical Skills', 'type': 'skill', 'weight': 25},
        ]

        for crit_data in criteria_data:
            PerformanceCriteria.objects.create(
                company=self.company,
                name=crit_data['name'],
                name_en=crit_data['name_en'],
                criteria_type=crit_data['type'],
                weight=crit_data['weight'],
                max_score=100,
                applies_to_all=True,
            )

        self.stdout.write(self.style.SUCCESS('  ✓ تم إنشاء بيانات التقييم'))

    def create_training_data(self):
        """إنشاء بيانات التدريب"""
        self.stdout.write('🎓 إنشاء بيانات التدريب...')

        # Create category
        category, created = TrainingCategory.objects.get_or_create(
            company=self.company,
            name='التطوير التقني',
            defaults={
                'name_en': 'Technical Development',
            }
        )

        # Create provider
        provider, created = TrainingProvider.objects.get_or_create(
            company=self.company,
            name='أكاديمية التدريب الاحترافي',
            defaults={
                'provider_type': 'external',
                'contact_person': 'أحمد العلي',
                'email': 'info@academy.com',
                'phone': '0791234567',
            }
        )

        # Create courses
        courses_data = [
            {'code': 'PYTH', 'name': 'برمجة Python المتقدمة', 'name_en': 'Advanced Python Programming', 'duration': 40},
            {'code': 'LEAD', 'name': 'القيادة والإدارة', 'name_en': 'Leadership & Management', 'duration': 24},
        ]

        for course_data in courses_data:
            TrainingCourse.objects.get_or_create(
                company=self.company,
                code=course_data['code'],
                defaults={
                    'category': category,
                    'provider': provider,
                    'name': course_data['name'],
                    'name_en': course_data['name_en'],
                    'duration_hours': course_data['duration'],
                    'cost_per_participant': Decimal('500'),
                    'delivery_method': 'classroom',
                    'status': 'planned',
                }
            )

        self.stdout.write(self.style.SUCCESS('  ✓ تم إنشاء بيانات التدريب'))

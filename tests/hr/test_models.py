# tests/hr/test_models.py
"""
HR Models Test Suite
اختبارات نماذج الموارد البشرية
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    Department, JobGrade, JobTitle,
    Employee, EmployeeDocument, EmployeeContract, SalaryIncrement,
    HRSettings, SocialSecuritySettings, LeaveType,
    Attendance, LeaveBalance, LeaveRequest, Overtime, Advance, AdvanceInstallment,
    Payroll, PayrollDetail,
    BiometricDevice, EmployeeBiometricMapping,
)

User = get_user_model()


@pytest.fixture
def company(db, currency):
    """Create test company"""
    return Company.objects.create(
        name='Test Company',
        name_en='Test Company',
        tax_number='1234567890',
        phone='0791234567',
        email='test@company.com',
        address='Test Address',
        city='Amman',
        base_currency=currency,
    )


@pytest.fixture
def branch(company):
    """Create test branch"""
    return Branch.objects.create(
        company=company,
        code='MAIN',
        name='Main Branch',
        name_en='Main Branch',
    )


@pytest.fixture
def currency(db):
    """Create test currency"""
    return Currency.objects.create(
        code='JOD',
        name='Jordanian Dinar',
        name_en='Jordanian Dinar',
        symbol='د.أ',
        is_base=True,
    )


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
    )


@pytest.fixture
def hr_settings(company):
    """Create HR settings"""
    return HRSettings.objects.create(
        company=company,
        default_working_hours_per_day=8,
        default_working_days_per_month=22,
        overtime_regular_rate=Decimal('1.25'),
        overtime_holiday_rate=Decimal('2.00'),
        default_annual_leave_days=14,
        default_sick_leave_days=14,
    )


@pytest.fixture
def department(company):
    """Create test department"""
    return Department.objects.create(
        company=company,
        code='IT',
        name_ar='تقنية المعلومات',
        name_en='Information Technology',
    )


@pytest.fixture
def job_grade(company):
    """Create test job grade"""
    return JobGrade.objects.create(
        company=company,
        code='MID',
        name_ar='متوسط',
        name_en='Mid-Level',
        level=2,
        min_salary=600,
        max_salary=900,
        annual_leave_days=18,
        sick_leave_days=14,
    )


@pytest.fixture
def job_title(company, department, job_grade):
    """Create test job title"""
    return JobTitle.objects.create(
        company=company,
        code='DEV',
        name_ar='مطور برمجيات',
        name_en='Software Developer',
        department=department,
        job_grade=job_grade,
        min_salary=600,
        max_salary=900,
    )


@pytest.fixture
def employee(company, branch, department, job_title, job_grade, currency):
    """Create test employee"""
    return Employee.objects.create(
        company=company,
        branch=branch,
        first_name_ar='أحمد',
        middle_name_ar='محمد',
        last_name_ar='العلي',
        first_name_en='Ahmad',
        middle_name_en='Mohammed',
        last_name_en='Alali',
        date_of_birth=date(1990, 1, 1),
        national_id='1234567890',
        nationality='الأردن',
        gender='M',
        marital_status='S',
        mobile='0791234567',
        email='ahmad@test.com',
        hire_date=date(2020, 1, 1),
        department=department,
        job_title=job_title,
        job_grade=job_grade,
        employment_status='FT',
        status='active',
        basic_salary=750,
        fuel_allowance=50,
        other_allowances=0,
        social_security_salary=750,
        working_hours_per_day=8,
        working_days_per_month=22,
        annual_leave_balance=18,
        sick_leave_balance=14,
        currency=currency,
    )


# =======================
# Organization Model Tests
# =======================

class TestDepartment:
    """Test Department model"""

    def test_create_department(self, company):
        """Test creating a department"""
        dept = Department.objects.create(
            company=company,
            code='HR',
            name_ar='الموارد البشرية',
            name_en='Human Resources',
        )
        assert dept.code == 'HR'
        assert dept.name_ar == 'الموارد البشرية'
        assert dept.level == 1  # Root level

    def test_department_hierarchy(self, company):
        """Test department parent-child relationship"""
        parent = Department.objects.create(
            company=company,
            code='IT',
            name_ar='تقنية المعلومات',
            name_en='IT',
        )
        child = Department.objects.create(
            company=company,
            code='DEV',
            name_ar='التطوير',
            name_en='Development',
            parent=parent,
        )
        assert child.parent == parent
        assert child.level == 2
        assert parent in child.full_path

    def test_department_unique_code_per_company(self, company):
        """Test department code is unique per company"""
        Department.objects.create(company=company, code='IT', name_ar='IT', name_en='IT')
        with pytest.raises(IntegrityError):
            Department.objects.create(company=company, code='IT', name_ar='IT2', name_en='IT2')


class TestJobGrade:
    """Test JobGrade model"""

    def test_create_job_grade(self, company):
        """Test creating a job grade"""
        grade = JobGrade.objects.create(
            company=company,
            code='SR',
            name_ar='كبير',
            name_en='Senior',
            level=3,
            min_salary=900,
            max_salary=1500,
            annual_leave_days=21,
            sick_leave_days=14,
        )
        assert grade.code == 'SR'
        assert grade.min_salary == 900
        assert grade.max_salary == 1500


class TestJobTitle:
    """Test JobTitle model"""

    def test_create_job_title(self, company, department, job_grade):
        """Test creating a job title"""
        title = JobTitle.objects.create(
            company=company,
            code='DEV',
            name_ar='مطور',
            name_en='Developer',
            department=department,
            job_grade=job_grade,
            min_salary=600,
            max_salary=900,
        )
        assert title.code == 'DEV'
        assert title.department == department
        assert title.job_grade == job_grade


# =======================
# Employee Model Tests
# =======================

class TestEmployee:
    """Test Employee model"""

    def test_create_employee(self, employee):
        """Test creating an employee"""
        assert employee.first_name_ar == 'أحمد'
        assert employee.status == 'active'
        assert employee.basic_salary == 750

    def test_employee_full_name(self, employee):
        """Test employee full name property"""
        assert employee.full_name == 'أحمد محمد العلي'

    def test_employee_age(self, employee):
        """Test employee age calculation"""
        expected_age = timezone.now().year - 1990
        assert employee.age == expected_age or employee.age == expected_age - 1

    def test_employee_years_of_service(self, employee):
        """Test years of service calculation"""
        expected_years = timezone.now().year - 2020
        assert employee.years_of_service >= expected_years

    def test_employee_hourly_rate(self, employee):
        """Test hourly rate calculation"""
        # (750 + 50) / (22 * 8) = 800 / 176 ≈ 4.545
        expected_rate = (employee.basic_salary + employee.fuel_allowance) / (employee.working_days_per_month * employee.working_hours_per_day)
        assert abs(employee.hourly_rate - expected_rate) < Decimal('0.01')

    def test_employee_total_fixed_earnings(self, employee):
        """Test total fixed earnings calculation"""
        expected = employee.basic_salary + employee.fuel_allowance + employee.other_allowances
        assert employee.total_fixed_earnings == expected

    def test_employee_unique_national_id_per_company(self, company, branch, department, job_title, job_grade, currency):
        """Test national ID is unique per company"""
        Employee.objects.create(
            company=company, branch=branch, department=department,
            job_title=job_title, job_grade=job_grade, currency=currency,
            first_name_ar='أحمد', last_name_ar='علي', first_name_en='Ahmad', last_name_en='Ali',
            national_id='111222333', date_of_birth=date(1990, 1, 1),
            hire_date=date(2020, 1, 1), gender='M', marital_status='S',
            employment_status='FT', status='active', basic_salary=500,
        )
        with pytest.raises(IntegrityError):
            Employee.objects.create(
                company=company, branch=branch, department=department,
                job_title=job_title, job_grade=job_grade, currency=currency,
                first_name_ar='محمد', last_name_ar='خالد', first_name_en='Mohammed', last_name_en='Khaled',
                national_id='111222333',  # Duplicate
                date_of_birth=date(1991, 1, 1), hire_date=date(2021, 1, 1),
                gender='M', marital_status='S', employment_status='FT', status='active',
                basic_salary=500,
            )

    def test_employee_terminate(self, employee):
        """Test employee termination"""
        employee.terminate(date.today(), 'Resignation')
        assert employee.status == 'terminated'
        assert employee.termination_date == date.today()
        assert employee.termination_reason == 'Resignation'

    def test_employee_reinstate(self, employee):
        """Test employee reinstatement"""
        employee.terminate(date.today(), 'Test')
        employee.reinstate()
        assert employee.status == 'active'
        assert employee.termination_date is None
        assert employee.termination_reason is None


# =======================
# Contract Model Tests
# =======================

class TestEmployeeContract:
    """Test EmployeeContract model"""

    def test_create_contract(self, company, employee):
        """Test creating an employee contract"""
        contract = EmployeeContract.objects.create(
            company=company,
            employee=employee,
            contract_type='FT',
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
            contract_salary=750,
            probation_period=90,
            notice_period=30,
            status='draft',
        )
        assert contract.employee == employee
        assert contract.contract_type == 'FT'
        assert contract.status == 'draft'

    def test_contract_activate(self, company, employee, user):
        """Test contract activation"""
        contract = EmployeeContract.objects.create(
            company=company, employee=employee, contract_type='FT',
            start_date=date(2020, 1, 1), contract_salary=750,
            probation_period=90, notice_period=30, status='draft',
        )
        contract.activate(user)
        assert contract.status == 'active'

    def test_contract_is_expired(self, company, employee):
        """Test contract expiry check"""
        past_date = date.today() - timedelta(days=1)
        contract = EmployeeContract.objects.create(
            company=company, employee=employee, contract_type='FT',
            start_date=date(2020, 1, 1), end_date=past_date,
            contract_salary=750, status='active',
        )
        assert contract.is_expired is True

    def test_contract_is_in_probation(self, company, employee):
        """Test probation period check"""
        contract = EmployeeContract.objects.create(
            company=company, employee=employee, contract_type='FT',
            start_date=date.today() - timedelta(days=30),
            contract_salary=750, probation_period=90, status='active',
        )
        assert contract.is_in_probation is True


class TestSalaryIncrement:
    """Test SalaryIncrement model"""

    def test_create_salary_increment(self, company, employee):
        """Test creating a salary increment"""
        increment = SalaryIncrement.objects.create(
            company=company,
            employee=employee,
            increment_type='annual',
            old_salary=750,
            is_percentage=False,
            increment_amount=50,
            new_salary=800,
            effective_date=date.today() + timedelta(days=30),
            status='pending',
            reason='Annual increment',
        )
        assert increment.old_salary == 750
        assert increment.new_salary == 800
        assert increment.status == 'pending'

    def test_increment_percentage_calculation(self, company, employee):
        """Test increment percentage property"""
        increment = SalaryIncrement.objects.create(
            company=company, employee=employee, increment_type='annual',
            old_salary=750, is_percentage=False, increment_amount=75,
            new_salary=825, effective_date=date.today(), status='pending',
        )
        # 75 / 750 * 100 = 10%
        assert abs(increment.increment_percentage - 10) < 0.01

    def test_increment_approve(self, company, employee, user):
        """Test increment approval"""
        increment = SalaryIncrement.objects.create(
            company=company, employee=employee, increment_type='annual',
            old_salary=750, is_percentage=False, increment_amount=50,
            new_salary=800, effective_date=date.today(), status='pending',
        )
        increment.approve(user)
        assert increment.status == 'approved'
        assert increment.approved_by == user

    def test_increment_apply(self, company, employee, user):
        """Test applying increment to employee"""
        old_salary = employee.basic_salary
        increment = SalaryIncrement.objects.create(
            company=company, employee=employee, increment_type='annual',
            old_salary=old_salary, is_percentage=False, increment_amount=50,
            new_salary=old_salary + 50, effective_date=date.today() - timedelta(days=1),
            status='approved', approved_by=user,
        )
        increment.apply_increment(user)
        employee.refresh_from_db()
        assert employee.basic_salary == old_salary + 50
        assert increment.status == 'applied'


# =======================
# Settings Model Tests
# =======================

class TestHRSettings:
    """Test HRSettings model"""

    def test_create_hr_settings(self, company):
        """Test creating HR settings"""
        settings = HRSettings.objects.create(
            company=company,
            default_working_hours_per_day=8,
            default_working_days_per_month=22,
            overtime_regular_rate=Decimal('1.25'),
            default_annual_leave_days=14,
        )
        assert settings.default_working_hours_per_day == 8
        assert settings.overtime_regular_rate == Decimal('1.25')

    def test_one_hr_settings_per_company(self, company):
        """Test only one HR settings per company"""
        HRSettings.objects.create(company=company, default_working_hours_per_day=8)
        with pytest.raises(IntegrityError):
            HRSettings.objects.create(company=company, default_working_hours_per_day=9)


class TestSocialSecuritySettings:
    """Test SocialSecuritySettings model"""

    def test_create_ss_settings(self, company):
        """Test creating social security settings"""
        ss = SocialSecuritySettings.objects.create(
            company=company,
            employee_contribution_rate=Decimal('7.50'),
            company_contribution_rate=Decimal('14.25'),
            minimum_insurable_salary=Decimal('220'),
            maximum_insurable_salary=Decimal('3500'),
        )
        assert ss.employee_contribution_rate == Decimal('7.50')

    def test_calculate_employee_contribution(self, company):
        """Test employee contribution calculation"""
        ss = SocialSecuritySettings.objects.create(
            company=company,
            employee_contribution_rate=Decimal('7.50'),
            minimum_insurable_salary=Decimal('220'),
            maximum_insurable_salary=Decimal('3500'),
        )
        # Salary 1000, contribution = 1000 * 0.075 = 75
        contribution = ss.calculate_employee_contribution(Decimal('1000'))
        assert contribution == Decimal('75.00')

    def test_calculate_contribution_with_max_limit(self, company):
        """Test contribution calculation respects max limit"""
        ss = SocialSecuritySettings.objects.create(
            company=company,
            employee_contribution_rate=Decimal('7.50'),
            minimum_insurable_salary=Decimal('220'),
            maximum_insurable_salary=Decimal('3500'),
        )
        # Salary 5000, but max is 3500, contribution = 3500 * 0.075 = 262.50
        contribution = ss.calculate_employee_contribution(Decimal('5000'))
        assert contribution == Decimal('262.50')


class TestLeaveType:
    """Test LeaveType model"""

    def test_create_leave_type(self, company):
        """Test creating a leave type"""
        leave_type = LeaveType.objects.create(
            company=company,
            code='ANN',
            name_ar='إجازة سنوية',
            name_en='Annual Leave',
            is_paid=True,
            default_days=14,
            requires_approval=True,
        )
        assert leave_type.code == 'ANN'
        assert leave_type.is_paid is True


# =======================
# Attendance Model Tests
# =======================

class TestAttendance:
    """Test Attendance model"""

    def test_create_attendance(self, company, employee):
        """Test creating an attendance record"""
        attendance = Attendance.objects.create(
            company=company,
            employee=employee,
            date=date.today(),
            check_in=datetime.now().time().replace(hour=8, minute=0),
            check_out=datetime.now().time().replace(hour=17, minute=0),
            status='present',
            working_hours=9,
        )
        assert attendance.employee == employee
        assert attendance.status == 'present'

    def test_attendance_unique_per_employee_per_day(self, company, employee):
        """Test attendance is unique per employee per day"""
        Attendance.objects.create(
            company=company, employee=employee, date=date.today(), status='present',
        )
        with pytest.raises(IntegrityError):
            Attendance.objects.create(
                company=company, employee=employee, date=date.today(), status='present',
            )


class TestLeaveBalance:
    """Test LeaveBalance model"""

    def test_create_leave_balance(self, company, employee):
        """Test creating a leave balance"""
        leave_type = LeaveType.objects.create(
            company=company, code='ANN', name_ar='سنوية', name_en='Annual',
            is_paid=True, default_days=14,
        )
        balance = LeaveBalance.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            year=2024,
            opening_balance=14,
            used=5,
        )
        assert balance.total_entitled == 14
        assert balance.remaining_balance == 9

    def test_leave_balance_with_carried_forward(self, company, employee):
        """Test leave balance with carried forward days"""
        leave_type = LeaveType.objects.create(
            company=company, code='ANN', name_ar='سنوية', name_en='Annual',
            is_paid=True, default_days=14,
        )
        balance = LeaveBalance.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            year=2024,
            opening_balance=14,
            carried_forward=3,
            used=5,
        )
        # Total = opening (14) + carried_forward (3) = 17
        # Remaining = 17 - 5 = 12
        assert balance.total_entitled == 17
        assert balance.remaining_balance == 12


class TestLeaveRequest:
    """Test LeaveRequest model"""

    def test_create_leave_request(self, company, employee):
        """Test creating a leave request"""
        leave_type = LeaveType.objects.create(
            company=company, code='ANN', name_ar='سنوية', name_en='Annual',
            is_paid=True, default_days=14,
        )
        leave_request = LeaveRequest.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            days=3,
            reason='Personal',
            status='pending',
        )
        assert leave_request.days == 3
        assert leave_request.status == 'pending'


class TestOvertime:
    """Test Overtime model"""

    def test_create_overtime(self, company, employee, hr_settings):
        """Test creating an overtime record"""
        overtime = Overtime.objects.create(
            company=company,
            employee=employee,
            date=date.today(),
            start_time=datetime.now().time().replace(hour=17, minute=0),
            end_time=datetime.now().time().replace(hour=20, minute=0),
            hours=3,
            overtime_type='regular',
            rate=hr_settings.overtime_regular_rate,
            amount=Decimal('100'),
            status='pending',
        )
        assert overtime.hours == 3
        assert overtime.overtime_type == 'regular'


class TestAdvance:
    """Test Advance model"""

    def test_create_advance(self, company, employee):
        """Test creating an advance"""
        advance = Advance.objects.create(
            company=company,
            employee=employee,
            advance_type='salary_advance',
            request_date=date.today(),
            amount=300,
            installments=6,
            installment_amount=50,
            start_deduction_date=date.today() + timedelta(days=30),
            status='pending',
        )
        assert advance.amount == 300
        assert advance.installments == 6
        assert advance.remaining_amount == 300

    def test_advance_calculate_installment_amount(self, company, employee):
        """Test installment amount calculation"""
        advance = Advance.objects.create(
            company=company, employee=employee, advance_type='salary_advance',
            request_date=date.today(), amount=300, installments=6,
            start_deduction_date=date.today() + timedelta(days=30), status='pending',
        )
        advance.calculate_installment_amount()
        assert advance.installment_amount == Decimal('50')


# =======================
# Payroll Model Tests
# =======================

class TestPayroll:
    """Test Payroll model"""

    def test_create_payroll(self, company, branch):
        """Test creating a payroll"""
        payroll = Payroll.objects.create(
            company=company,
            branch=branch,
            period_year=2024,
            period_month=1,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 31),
            status='draft',
        )
        assert payroll.period_year == 2024
        assert payroll.period_month == 1
        assert payroll.status == 'draft'


class TestPayrollDetail:
    """Test PayrollDetail model"""

    def test_create_payroll_detail(self, company, branch, employee):
        """Test creating a payroll detail"""
        payroll = Payroll.objects.create(
            company=company, branch=branch, period_year=2024, period_month=1,
            from_date=date(2024, 1, 1), to_date=date(2024, 1, 31), status='draft',
        )
        detail = PayrollDetail.objects.create(
            payroll=payroll,
            employee=employee,
            basic_salary=750,
            fuel_allowance=50,
            other_allowances=0,
            gross_salary=800,
            social_security_employee=Decimal('56.25'),
            total_deductions=Decimal('56.25'),
            net_salary=Decimal('743.75'),
        )
        assert detail.basic_salary == 750
        assert detail.net_salary == Decimal('743.75')


# =======================
# Biometric Model Tests
# =======================

class TestBiometricDevice:
    """Test BiometricDevice model"""

    def test_create_biometric_device(self, company, branch):
        """Test creating a biometric device"""
        device = BiometricDevice.objects.create(
            company=company,
            branch=branch,
            name='Main Entrance Device',
            device_type='zkteco',
            connection_type='tcp',
            ip_address='192.168.1.100',
            port=4370,
            location='Main Entrance',
            status='active',
        )
        assert device.name == 'Main Entrance Device'
        assert device.device_type == 'zkteco'
        assert device.status == 'active'


class TestEmployeeBiometricMapping:
    """Test EmployeeBiometricMapping model"""

    def test_create_biometric_mapping(self, company, branch, employee):
        """Test creating employee biometric mapping"""
        device = BiometricDevice.objects.create(
            company=company, branch=branch, name='Device 1',
            device_type='zkteco', connection_type='tcp',
            ip_address='192.168.1.100', status='active',
        )
        mapping = EmployeeBiometricMapping.objects.create(
            company=company,
            employee=employee,
            device=device,
            device_user_id='123',
            enrollment_status='enrolled',
        )
        assert mapping.employee == employee
        assert mapping.device == device
        assert mapping.device_user_id == '123'

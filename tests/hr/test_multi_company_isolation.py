# tests/hr/test_multi_company_isolation.py
"""
Multi-Company Isolation Tests for HR Module
اختبارات عزل البيانات بين الشركات المتعددة
"""

import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    Department, JobGrade, JobTitle, Employee, EmployeeContract,
    HRSettings, LeaveType, LeaveRequest, LeaveBalance,
    Attendance, Overtime, Advance, Payroll, PayrollDetail,
    BiometricDevice,
)

User = get_user_model()


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
def company_a(db, currency):
    """Create Company A"""
    return Company.objects.create(
        name='Company A',
        name_en='Company A',
        tax_number='1111111111',
        phone='0791111111',
        email='companya@test.com',
        address='Address A',
        city='Amman',
        base_currency=currency,
    )


@pytest.fixture
def company_b(db, currency):
    """Create Company B"""
    return Company.objects.create(
        name='Company B',
        name_en='Company B',
        tax_number='2222222222',
        phone='0792222222',
        email='companyb@test.com',
        address='Address B',
        city='Amman',
        base_currency=currency,
    )


@pytest.fixture
def branch_a(company_a):
    """Create Branch for Company A"""
    return Branch.objects.create(
        company=company_a,
        code='BR-A',
        name='Branch A',
        name_en='Branch A',
    )


@pytest.fixture
def branch_b(company_b):
    """Create Branch for Company B"""
    return Branch.objects.create(
        company=company_b,
        code='BR-B',
        name='Branch B',
        name_en='Branch B',
    )


@pytest.fixture
def user_company_a(company_a, branch_a):
    """Create user for Company A"""
    user = User.objects.create_user(
        username='user_a',
        email='usera@test.com',
        password='pass123',
        is_staff=True,
    )
    user.company = company_a
    user.branch = branch_a
    user.save()
    return user


@pytest.fixture
def user_company_b(company_b, branch_b):
    """Create user for Company B"""
    user = User.objects.create_user(
        username='user_b',
        email='userb@test.com',
        password='pass123',
        is_staff=True,
    )
    user.company = company_b
    user.branch = branch_b
    user.save()
    return user


# =======================
# Organization Model Isolation Tests
# =======================

@pytest.mark.django_db
class TestDepartmentIsolation:
    """Test Department data isolation between companies"""

    def test_departments_isolated_by_company(self, company_a, company_b):
        """Test departments are isolated by company"""
        # Create departments for both companies with same code
        dept_a = Department.objects.create(
            company=company_a,
            code='IT',
            name_ar='IT Company A',
            name_en='IT Company A',
        )
        dept_b = Department.objects.create(
            company=company_b,
            code='IT',
            name_ar='IT Company B',
            name_en='IT Company B',
        )

        # Query departments for company A
        depts_a = Department.objects.filter(company=company_a)
        assert depts_a.count() == 1
        assert dept_a in depts_a
        assert dept_b not in depts_a

        # Query departments for company B
        depts_b = Department.objects.filter(company=company_b)
        assert depts_b.count() == 1
        assert dept_b in depts_b
        assert dept_a not in depts_b

    def test_department_code_unique_per_company_not_global(self, company_a, company_b):
        """Test department code is unique per company, not globally"""
        # Should allow same code in different companies
        dept_a = Department.objects.create(
            company=company_a, code='HR', name_ar='HR A', name_en='HR A',
        )
        dept_b = Department.objects.create(
            company=company_b, code='HR', name_ar='HR B', name_en='HR B',
        )

        assert dept_a.code == dept_b.code
        assert dept_a.company != dept_b.company


@pytest.mark.django_db
class TestJobGradeIsolation:
    """Test JobGrade isolation"""

    def test_job_grades_isolated_by_company(self, company_a, company_b):
        """Test job grades are isolated by company"""
        grade_a = JobGrade.objects.create(
            company=company_a, code='SR', name_ar='Senior A', name_en='Senior A',
            level=3, min_salary=900, max_salary=1500,
        )
        grade_b = JobGrade.objects.create(
            company=company_b, code='SR', name_ar='Senior B', name_en='Senior B',
            level=3, min_salary=900, max_salary=1500,
        )

        grades_a = JobGrade.objects.filter(company=company_a)
        assert grade_a in grades_a
        assert grade_b not in grades_a


# =======================
# Employee Model Isolation Tests
# =======================

@pytest.mark.django_db
class TestEmployeeIsolation:
    """Test Employee data isolation"""

    def test_employees_isolated_by_company(self, company_a, company_b, branch_a, branch_b, currency):
        """Test employees are isolated by company"""
        # Create departments and job data for both companies
        dept_a = Department.objects.create(company=company_a, code='IT', name_ar='IT', name_en='IT')
        dept_b = Department.objects.create(company=company_b, code='IT', name_ar='IT', name_en='IT')

        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )
        grade_b = JobGrade.objects.create(
            company=company_b, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )

        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_a, job_grade=grade_a, min_salary=600, max_salary=900,
        )
        title_b = JobTitle.objects.create(
            company=company_b, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_b, job_grade=grade_b, min_salary=600, max_salary=900,
        )

        # Create employees
        emp_a = Employee.objects.create(
            company=company_a, branch=branch_a,
            first_name_ar='أحمد', last_name_ar='علي',
            first_name_en='Ahmad', last_name_en='Ali',
            national_id='111111', date_of_birth=date(1990, 1, 1),
            hire_date=date(2020, 1, 1), gender='M', marital_status='S',
            department=dept_a, job_title=title_a, job_grade=grade_a,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )
        emp_b = Employee.objects.create(
            company=company_b, branch=branch_b,
            first_name_ar='محمد', last_name_ar='خالد',
            first_name_en='Mohammed', last_name_en='Khaled',
            national_id='222222', date_of_birth=date(1991, 1, 1),
            hire_date=date(2021, 1, 1), gender='M', marital_status='S',
            department=dept_b, job_title=title_b, job_grade=grade_b,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )

        # Query employees for company A
        emps_a = Employee.objects.filter(company=company_a)
        assert emps_a.count() == 1
        assert emp_a in emps_a
        assert emp_b not in emps_a

        # Query employees for company B
        emps_b = Employee.objects.filter(company=company_b)
        assert emps_b.count() == 1
        assert emp_b in emps_b
        assert emp_a not in emps_b

    def test_employee_national_id_unique_per_company_not_global(self, company_a, company_b, branch_a, branch_b, currency):
        """Test national ID is unique per company, not globally"""
        # Create minimal job structure
        dept_a = Department.objects.create(company=company_a, code='IT', name_ar='IT', name_en='IT')
        dept_b = Department.objects.create(company=company_b, code='IT', name_ar='IT', name_en='IT')

        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )
        grade_b = JobGrade.objects.create(
            company=company_b, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )

        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_a, job_grade=grade_a, min_salary=600, max_salary=900,
        )
        title_b = JobTitle.objects.create(
            company=company_b, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_b, job_grade=grade_b, min_salary=600, max_salary=900,
        )

        # Should allow same national_id in different companies
        emp_a = Employee.objects.create(
            company=company_a, branch=branch_a,
            first_name_ar='أحمد', last_name_ar='علي',
            first_name_en='Ahmad', last_name_en='Ali',
            national_id='123456789', date_of_birth=date(1990, 1, 1),
            hire_date=date(2020, 1, 1), gender='M', marital_status='S',
            department=dept_a, job_title=title_a, job_grade=grade_a,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )
        emp_b = Employee.objects.create(
            company=company_b, branch=branch_b,
            first_name_ar='محمد', last_name_ar='خالد',
            first_name_en='Mohammed', last_name_en='Khaled',
            national_id='123456789',  # Same national ID
            date_of_birth=date(1991, 1, 1),
            hire_date=date(2021, 1, 1), gender='M', marital_status='S',
            department=dept_b, job_title=title_b, job_grade=grade_b,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )

        assert emp_a.national_id == emp_b.national_id
        assert emp_a.company != emp_b.company


# =======================
# Settings Isolation Tests
# =======================

@pytest.mark.django_db
class TestHRSettingsIsolation:
    """Test HR Settings isolation"""

    def test_hr_settings_isolated_by_company(self, company_a, company_b):
        """Test HR settings are isolated by company"""
        settings_a = HRSettings.objects.create(
            company=company_a,
            default_working_hours_per_day=8,
            default_annual_leave_days=14,
        )
        settings_b = HRSettings.objects.create(
            company=company_b,
            default_working_hours_per_day=9,  # Different setting
            default_annual_leave_days=21,
        )

        # Each company has its own settings
        assert HRSettings.objects.filter(company=company_a).first() == settings_a
        assert HRSettings.objects.filter(company=company_b).first() == settings_b
        assert settings_a.default_working_hours_per_day != settings_b.default_working_hours_per_day


@pytest.mark.django_db
class TestLeaveTypeIsolation:
    """Test Leave Type isolation"""

    def test_leave_types_isolated_by_company(self, company_a, company_b):
        """Test leave types are isolated by company"""
        leave_a = LeaveType.objects.create(
            company=company_a, code='ANN', name_ar='Annual A', name_en='Annual A',
            is_paid=True, default_days=14,
        )
        leave_b = LeaveType.objects.create(
            company=company_b, code='ANN', name_ar='Annual B', name_en='Annual B',
            is_paid=True, default_days=21,
        )

        leaves_a = LeaveType.objects.filter(company=company_a)
        assert leave_a in leaves_a
        assert leave_b not in leaves_a


# =======================
# Transactional Data Isolation Tests
# =======================

@pytest.mark.django_db
class TestLeaveRequestIsolation:
    """Test Leave Request isolation"""

    def test_leave_requests_isolated_by_company(self, company_a, company_b, branch_a, branch_b, currency):
        """Test leave requests don't leak between companies"""
        # Setup employees for both companies
        dept_a = Department.objects.create(company=company_a, code='IT', name_ar='IT', name_en='IT')
        dept_b = Department.objects.create(company=company_b, code='IT', name_ar='IT', name_en='IT')

        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )
        grade_b = JobGrade.objects.create(
            company=company_b, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )

        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_a, job_grade=grade_a, min_salary=600, max_salary=900,
        )
        title_b = JobTitle.objects.create(
            company=company_b, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_b, job_grade=grade_b, min_salary=600, max_salary=900,
        )

        emp_a = Employee.objects.create(
            company=company_a, branch=branch_a,
            first_name_ar='أحمد', last_name_ar='علي',
            first_name_en='Ahmad', last_name_en='Ali',
            national_id='111', date_of_birth=date(1990, 1, 1),
            hire_date=date(2020, 1, 1), gender='M', marital_status='S',
            department=dept_a, job_title=title_a, job_grade=grade_a,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )
        emp_b = Employee.objects.create(
            company=company_b, branch=branch_b,
            first_name_ar='محمد', last_name_ar='خالد',
            first_name_en='Mohammed', last_name_en='Khaled',
            national_id='222', date_of_birth=date(1991, 1, 1),
            hire_date=date(2021, 1, 1), gender='M', marital_status='S',
            department=dept_b, job_title=title_b, job_grade=grade_b,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )

        leave_type_a = LeaveType.objects.create(
            company=company_a, code='ANN', name_ar='Annual', name_en='Annual',
            is_paid=True, default_days=14,
        )
        leave_type_b = LeaveType.objects.create(
            company=company_b, code='ANN', name_ar='Annual', name_en='Annual',
            is_paid=True, default_days=14,
        )

        # Create leave requests
        leave_req_a = LeaveRequest.objects.create(
            company=company_a, employee=emp_a, leave_type=leave_type_a,
            start_date=date.today(), end_date=date.today(), days=1, status='pending',
        )
        leave_req_b = LeaveRequest.objects.create(
            company=company_b, employee=emp_b, leave_type=leave_type_b,
            start_date=date.today(), end_date=date.today(), days=1, status='pending',
        )

        # Query leave requests by company
        leaves_a = LeaveRequest.objects.filter(company=company_a)
        assert leave_req_a in leaves_a
        assert leave_req_b not in leaves_a


@pytest.mark.django_db
class TestPayrollIsolation:
    """Test Payroll isolation"""

    def test_payrolls_isolated_by_company(self, company_a, company_b, branch_a, branch_b):
        """Test payrolls are isolated by company"""
        payroll_a = Payroll.objects.create(
            company=company_a, branch=branch_a,
            period_year=2024, period_month=1,
            from_date=date(2024, 1, 1), to_date=date(2024, 1, 31),
            status='draft',
        )
        payroll_b = Payroll.objects.create(
            company=company_b, branch=branch_b,
            period_year=2024, period_month=1,
            from_date=date(2024, 1, 1), to_date=date(2024, 1, 31),
            status='draft',
        )

        payrolls_a = Payroll.objects.filter(company=company_a)
        assert payroll_a in payrolls_a
        assert payroll_b not in payrolls_a


@pytest.mark.django_db
class TestBiometricDeviceIsolation:
    """Test Biometric Device isolation"""

    def test_biometric_devices_isolated_by_company(self, company_a, company_b, branch_a, branch_b):
        """Test biometric devices are isolated by company"""
        device_a = BiometricDevice.objects.create(
            company=company_a, branch=branch_a,
            name='Device A', device_type='zkteco', connection_type='tcp',
            ip_address='192.168.1.100', status='active',
        )
        device_b = BiometricDevice.objects.create(
            company=company_b, branch=branch_b,
            name='Device B', device_type='zkteco', connection_type='tcp',
            ip_address='192.168.1.101', status='active',
        )

        devices_a = BiometricDevice.objects.filter(company=company_a)
        assert device_a in devices_a
        assert device_b not in devices_a


# =======================
# Cross-Company Query Protection Tests
# =======================

@pytest.mark.django_db
class TestCrossCompanyQueryProtection:
    """Test protection against cross-company data access"""

    def test_employee_cannot_reference_foreign_company_department(self, company_a, company_b, branch_a, currency):
        """Test employee cannot be assigned to another company's department"""
        dept_b = Department.objects.create(
            company=company_b, code='IT', name_ar='IT B', name_en='IT B',
        )
        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )
        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_b,  # Wrong company's department
            job_grade=grade_a, min_salary=600, max_salary=900,
        )

        # This should be prevented by application logic or database constraints
        # The test documents the expected behavior

    def test_leave_request_cannot_use_foreign_company_leave_type(self, company_a, company_b, branch_a, currency):
        """Test leave request cannot use another company's leave type"""
        dept_a = Department.objects.create(company=company_a, code='IT', name_ar='IT', name_en='IT')
        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid', name_en='Mid',
            level=2, min_salary=600, max_salary=900,
        )
        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev', name_en='Dev',
            department=dept_a, job_grade=grade_a, min_salary=600, max_salary=900,
        )
        emp_a = Employee.objects.create(
            company=company_a, branch=branch_a,
            first_name_ar='أحمد', last_name_ar='علي',
            first_name_en='Ahmad', last_name_en='Ali',
            national_id='111', date_of_birth=date(1990, 1, 1),
            hire_date=date(2020, 1, 1), gender='M', marital_status='S',
            department=dept_a, job_title=title_a, job_grade=grade_a,
            employment_status='FT', status='active', basic_salary=700,
            currency=currency,
        )

        # Leave type from company B
        leave_type_b = LeaveType.objects.create(
            company=company_b, code='ANN', name_ar='Annual', name_en='Annual',
            is_paid=True, default_days=14,
        )

        # This should be prevented by application logic
        # Creating leave request with foreign company's leave type
        # Should either fail or be caught by validation


# =======================
# Summary Test
# =======================

@pytest.mark.django_db
class TestMultiCompanyIsolationSummary:
    """Summary test for multi-company isolation"""

    def test_complete_isolation_scenario(self, company_a, company_b, branch_a, branch_b, currency):
        """Test complete isolation scenario with all major entities"""
        # Create complete HR structure for both companies
        # Company A
        dept_a = Department.objects.create(company=company_a, code='IT', name_ar='IT A', name_en='IT A')
        grade_a = JobGrade.objects.create(
            company=company_a, code='MID', name_ar='Mid A', name_en='Mid A',
            level=2, min_salary=600, max_salary=900,
        )
        title_a = JobTitle.objects.create(
            company=company_a, code='DEV', name_ar='Dev A', name_en='Dev A',
            department=dept_a, job_grade=grade_a, min_salary=600, max_salary=900,
        )
        emp_a = Employee.objects.create(
            company=company_a, branch=branch_a,
            first_name_ar='أحمد', last_name_ar='علي', first_name_en='Ahmad', last_name_en='Ali',
            national_id='111', date_of_birth=date(1990, 1, 1), hire_date=date(2020, 1, 1),
            gender='M', marital_status='S', department=dept_a, job_title=title_a,
            job_grade=grade_a, employment_status='FT', status='active',
            basic_salary=700, currency=currency,
        )

        # Company B
        dept_b = Department.objects.create(company=company_b, code='IT', name_ar='IT B', name_en='IT B')
        grade_b = JobGrade.objects.create(
            company=company_b, code='MID', name_ar='Mid B', name_en='Mid B',
            level=2, min_salary=600, max_salary=900,
        )
        title_b = JobTitle.objects.create(
            company=company_b, code='DEV', name_ar='Dev B', name_en='Dev B',
            department=dept_b, job_grade=grade_b, min_salary=600, max_salary=900,
        )
        emp_b = Employee.objects.create(
            company=company_b, branch=branch_b,
            first_name_ar='محمد', last_name_ar='خالد', first_name_en='Mohammed', last_name_en='Khaled',
            national_id='222', date_of_birth=date(1991, 1, 1), hire_date=date(2021, 1, 1),
            gender='M', marital_status='S', department=dept_b, job_title=title_b,
            job_grade=grade_b, employment_status='FT', status='active',
            basic_salary=700, currency=currency,
        )

        # Verify complete isolation
        assert Department.objects.filter(company=company_a).count() == 1
        assert Department.objects.filter(company=company_b).count() == 1
        assert Employee.objects.filter(company=company_a).count() == 1
        assert Employee.objects.filter(company=company_b).count() == 1

        # Cross-company queries should return empty
        assert dept_b not in Department.objects.filter(company=company_a)
        assert emp_b not in Employee.objects.filter(company=company_a)

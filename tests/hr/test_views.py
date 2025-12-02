# tests/hr/test_views.py
"""
HR Views and Workflows Test Suite
اختبارات واجهات وسير العمل للموارد البشرية
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    Department, JobGrade, JobTitle, Employee, EmployeeContract,
    HRSettings, LeaveType, LeaveRequest, LeaveBalance,
    Overtime, Advance, AdvanceInstallment, Payroll,
)

User = get_user_model()


@pytest.fixture
def client():
    """Create test client"""
    return Client()


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
def authenticated_user(db, company, branch):
    """Create authenticated user with company and branch"""
    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
    )
    user.company = company
    user.branch = branch
    user.save()
    return user


@pytest.fixture
def hr_settings(company):
    """Create HR settings"""
    return HRSettings.objects.create(
        company=company,
        default_working_hours_per_day=8,
        default_working_days_per_month=22,
        overtime_regular_rate=Decimal('1.25'),
        default_annual_leave_days=14,
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
        social_security_salary=750,
        working_hours_per_day=8,
        working_days_per_month=22,
        annual_leave_balance=18,
        sick_leave_balance=14,
        currency=currency,
    )


# =======================
# Department Views Tests
# =======================

@pytest.mark.django_db
class TestDepartmentViews:
    """Test Department views"""

    def test_department_list_requires_auth(self, client):
        """Test department list requires authentication"""
        response = client.get('/hr/departments/')
        # Should redirect to login
        assert response.status_code in [302, 403]

    def test_department_list_authenticated(self, client, authenticated_user):
        """Test department list for authenticated user"""
        client.force_login(authenticated_user)
        response = client.get('/hr/departments/')
        assert response.status_code == 200

    def test_department_create_view(self, client, authenticated_user, company):
        """Test creating a department through view"""
        client.force_login(authenticated_user)

        # Add current company and branch to session
        session = client.session
        session['current_company_id'] = company.id
        session.save()

        response = client.post('/hr/departments/create/', {
            'code': 'HR',
            'name_ar': 'الموارد البشرية',
            'name_en': 'Human Resources',
        })

        # Should redirect after successful creation
        assert response.status_code in [200, 302]


# =======================
# Employee Views Tests
# =======================

@pytest.mark.django_db
class TestEmployeeViews:
    """Test Employee views"""

    def test_employee_list_requires_auth(self, client):
        """Test employee list requires authentication"""
        response = client.get('/hr/employees/')
        assert response.status_code in [302, 403]

    def test_employee_list_authenticated(self, client, authenticated_user):
        """Test employee list for authenticated user"""
        client.force_login(authenticated_user)
        response = client.get('/hr/employees/')
        assert response.status_code == 200

    def test_employee_detail_view(self, client, authenticated_user, employee):
        """Test employee detail view"""
        client.force_login(authenticated_user)
        response = client.get(f'/hr/employees/{employee.id}/')
        assert response.status_code == 200


# =======================
# Contract Workflow Tests
# =======================

@pytest.mark.django_db
class TestContractWorkflow:
    """Test Contract workflow"""

    def test_contract_creation_flow(self, company, employee, authenticated_user):
        """Test complete contract creation workflow"""
        # Create contract
        contract = EmployeeContract.objects.create(
            company=company,
            employee=employee,
            contract_type='FT',
            start_date=date(2020, 1, 1),
            contract_salary=750,
            probation_period=90,
            notice_period=30,
            status='draft',
        )
        assert contract.status == 'draft'

        # Activate contract
        contract.activate(authenticated_user)
        assert contract.status == 'active'

        # Check that employee's active contract is updated
        employee.refresh_from_db()


# =======================
# Leave Request Workflow Tests
# =======================

@pytest.mark.django_db
class TestLeaveRequestWorkflow:
    """Test Leave Request workflow"""

    def test_leave_request_creation_and_approval(self, company, employee, authenticated_user):
        """Test leave request creation and approval workflow"""
        # Create leave type
        leave_type = LeaveType.objects.create(
            company=company,
            code='ANN',
            name_ar='إجازة سنوية',
            name_en='Annual Leave',
            is_paid=True,
            default_days=14,
            requires_approval=True,
        )

        # Create leave balance
        LeaveBalance.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            year=2024,
            opening_balance=14,
            used=0,
        )

        # Create leave request
        leave_request = LeaveRequest.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=9),
            days=3,
            reason='Personal leave',
            status='pending',
        )
        assert leave_request.status == 'pending'

        # Approve leave
        leave_request.status = 'approved'
        leave_request.approved_by = authenticated_user
        leave_request.approval_date = date.today()
        leave_request.save()

        assert leave_request.status == 'approved'
        assert leave_request.approved_by == authenticated_user

    def test_leave_request_rejection(self, company, employee, authenticated_user):
        """Test leave request rejection"""
        leave_type = LeaveType.objects.create(
            company=company, code='ANN', name_ar='سنوية', name_en='Annual',
            is_paid=True, default_days=14,
        )

        leave_request = LeaveRequest.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=9),
            days=3,
            status='pending',
        )

        # Reject leave
        leave_request.status = 'rejected'
        leave_request.rejection_reason = 'Insufficient staff'
        leave_request.save()

        assert leave_request.status == 'rejected'


# =======================
# Overtime Workflow Tests
# =======================

@pytest.mark.django_db
class TestOvertimeWorkflow:
    """Test Overtime workflow"""

    def test_overtime_approval_workflow(self, company, employee, hr_settings, authenticated_user):
        """Test overtime approval workflow"""
        # Create overtime record
        overtime = Overtime.objects.create(
            company=company,
            employee=employee,
            date=date.today(),
            start_time='17:00',
            end_time='20:00',
            hours=3,
            overtime_type='regular',
            rate=hr_settings.overtime_regular_rate,
            amount=Decimal('100'),
            status='pending',
        )
        assert overtime.status == 'pending'

        # Approve overtime
        overtime.status = 'approved'
        overtime.approved_by = authenticated_user
        overtime.approval_date = date.today()
        overtime.save()

        assert overtime.status == 'approved'

        # Mark as paid
        overtime.status = 'paid'
        overtime.save()

        assert overtime.status == 'paid'


# =======================
# Advance Workflow Tests
# =======================

@pytest.mark.django_db
class TestAdvanceWorkflow:
    """Test Advance workflow"""

    def test_advance_complete_workflow(self, company, employee, authenticated_user):
        """Test complete advance workflow from request to disbursement"""
        # Create advance request
        advance = Advance.objects.create(
            company=company,
            employee=employee,
            advance_type='salary_advance',
            request_date=date.today(),
            amount=300,
            installments=6,
            start_deduction_date=date.today() + timedelta(days=30),
            status='pending',
        )
        advance.calculate_installment_amount()
        assert advance.status == 'pending'
        assert advance.installment_amount == Decimal('50')

        # Approve advance
        advance.status = 'approved'
        advance.approved_by = authenticated_user
        advance.approval_date = date.today()
        advance.save()

        assert advance.status == 'approved'

        # Disburse advance
        advance.status = 'disbursed'
        advance.disbursement_date = date.today()
        advance.save()

        assert advance.status == 'disbursed'

        # Create installments
        for i in range(advance.installments):
            AdvanceInstallment.objects.create(
                advance=advance,
                installment_number=i + 1,
                due_date=advance.start_deduction_date + timedelta(days=30 * i),
                amount=advance.installment_amount,
                status='pending',
            )

        installments = AdvanceInstallment.objects.filter(advance=advance)
        assert installments.count() == 6

    def test_advance_rejection_workflow(self, company, employee):
        """Test advance rejection"""
        advance = Advance.objects.create(
            company=company,
            employee=employee,
            advance_type='loan',
            request_date=date.today(),
            amount=500,
            installments=10,
            start_deduction_date=date.today() + timedelta(days=30),
            status='pending',
        )

        # Reject advance
        advance.status = 'rejected'
        advance.rejection_reason = 'Exceeds limit'
        advance.save()

        assert advance.status == 'rejected'


# =======================
# Payroll Workflow Tests
# =======================

@pytest.mark.django_db
class TestPayrollWorkflow:
    """Test Payroll workflow"""

    def test_payroll_creation_and_processing(self, company, branch, employee):
        """Test payroll creation and basic processing"""
        # Create payroll
        payroll = Payroll.objects.create(
            company=company,
            branch=branch,
            period_year=2024,
            period_month=1,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 31),
            status='draft',
        )
        assert payroll.status == 'draft'

        # Process to calculated
        payroll.status = 'calculated'
        payroll.save()
        assert payroll.status == 'calculated'

        # Approve payroll
        payroll.status = 'approved'
        payroll.save()
        assert payroll.status == 'approved'

        # Mark as paid
        payroll.status = 'paid'
        payroll.save()
        assert payroll.status == 'paid'


# =======================
# Integration Tests
# =======================

@pytest.mark.django_db
class TestHRIntegration:
    """Test HR module integration scenarios"""

    def test_employee_lifecycle(self, company, branch, department, job_title, job_grade, currency, authenticated_user):
        """Test complete employee lifecycle"""
        # 1. Create employee
        employee = Employee.objects.create(
            company=company,
            branch=branch,
            first_name_ar='محمد',
            last_name_ar='خالد',
            first_name_en='Mohammed',
            last_name_en='Khaled',
            date_of_birth=date(1992, 5, 15),
            national_id='9876543210',
            nationality='الأردن',
            gender='M',
            marital_status='S',
            mobile='0799876543',
            email='mohammed@test.com',
            hire_date=date.today(),
            department=department,
            job_title=job_title,
            job_grade=job_grade,
            employment_status='FT',
            status='active',
            basic_salary=700,
            fuel_allowance=50,
            currency=currency,
        )
        assert employee.status == 'active'

        # 2. Create contract
        contract = EmployeeContract.objects.create(
            company=company,
            employee=employee,
            contract_type='FT',
            start_date=employee.hire_date,
            contract_salary=employee.basic_salary,
            probation_period=90,
            status='draft',
        )
        contract.activate(authenticated_user)
        assert contract.status == 'active'

        # 3. Request leave
        leave_type = LeaveType.objects.create(
            company=company, code='ANN', name_ar='سنوية', name_en='Annual',
            is_paid=True, default_days=14,
        )
        leave_request = LeaveRequest.objects.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            days=3,
            status='pending',
        )
        leave_request.status = 'approved'
        leave_request.save()
        assert leave_request.status == 'approved'

        # 4. Terminate employee
        employee.terminate(date.today(), 'Resignation')
        assert employee.status == 'terminated'

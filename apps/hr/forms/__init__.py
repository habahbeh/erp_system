# apps/hr/forms/__init__.py
"""
HR Forms Package
المرحلة 1: النماذج الأساسية
المرحلة 2: الحضور والإجازات والسلف
"""

# Phase 1 Forms
from .employee_forms import EmployeeForm
from .organization_forms import JobGradeForm, JobTitleForm
from .contract_forms import EmployeeContractForm, SalaryIncrementForm
from .settings_forms import (
    LeaveTypeForm,
    HRSettingsForm,
    SocialSecuritySettingsForm,
    PayrollAccountMappingForm
)

# Phase 2 Forms
from .attendance_forms import (
    AttendanceForm,
    BulkAttendanceForm,
    LeaveBalanceForm,
    LeaveRequestForm,
    EarlyLeaveForm,
    OvertimeForm,
    AdvanceForm,
    AdvanceApprovalForm,
    LeaveApprovalForm,
)

__all__ = [
    # Phase 1
    'EmployeeForm',
    'JobGradeForm',
    'JobTitleForm',
    'EmployeeContractForm',
    'SalaryIncrementForm',
    'LeaveTypeForm',
    'HRSettingsForm',
    'SocialSecuritySettingsForm',
    'PayrollAccountMappingForm',
    # Phase 2
    'AttendanceForm',
    'BulkAttendanceForm',
    'LeaveBalanceForm',
    'LeaveRequestForm',
    'EarlyLeaveForm',
    'OvertimeForm',
    'AdvanceForm',
    'AdvanceApprovalForm',
    'LeaveApprovalForm',
]

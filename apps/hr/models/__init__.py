# apps/hr/models/__init__.py
"""
استيراد جميع نماذج الموارد البشرية
HR Models Package

المرحلة 1 - النماذج الأساسية:
- Organization Models: Department, JobTitle, JobGrade
- Employee Models: Employee, EmployeeDocument
- Contract Models: EmployeeContract, SalaryIncrement
- Settings Models: HRSettings, SocialSecuritySettings, PayrollAccountMapping, LeaveType

المرحلة 2 - الحضور والإجازات والسلف:
- Attendance Models: Attendance, LeaveBalance, LeaveRequest, EarlyLeave, Overtime, Advance
"""

# Organization Models - نماذج الهيكل التنظيمي
from .organization_models import (
    Department,
    JobGrade,
    JobTitle,
)

# Employee Models - نماذج الموظفين
from .employee_models import (
    Employee,
    EmployeeDocument,
)

# Contract Models - نماذج العقود والعلاوات
from .contract_models import (
    EmployeeContract,
    SalaryIncrement,
)

# Settings Models - نماذج الإعدادات
from .settings_models import (
    HRSettings,
    SocialSecuritySettings,
    PayrollAccountMapping,
    LeaveType,
)

# Attendance Models - نماذج الحضور والإجازات (المرحلة 2)
from .attendance_models import (
    Attendance,
    LeaveBalance,
    LeaveRequest,
    EarlyLeave,
    Overtime,
    Advance,
    AdvanceInstallment,
)

# Payroll Models - نماذج الرواتب (المرحلة 3)
from .payroll_models import (
    Payroll,
    PayrollDetail,
    PayrollAllowance,
    PayrollDeduction,
    PayrollLoanDeduction,
)

# Notification Models - نماذج الإشعارات
from .notification_models import (
    HRNotification,
    NotificationSetting,
)

# Biometric Models - نماذج أجهزة البصمة (المرحلة 4)
from .biometric_models import (
    BiometricDevice,
    BiometricLog,
    EmployeeBiometricMapping,
    BiometricSyncLog,
)

# Performance Models - نماذج التقييم والأداء (المرحلة 5)
from .performance_models import (
    PerformancePeriod,
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationDetail,
    PerformanceGoal,
    PerformanceNote,
)

# Training Models - نماذج التدريب والتطوير (المرحلة 6)
from .training_models import (
    TrainingCategory,
    TrainingProvider,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRequest,
    TrainingPlan,
    TrainingPlanItem,
    TrainingFeedback,
)


__all__ = [
    # Organization Models
    'Department',
    'JobGrade',
    'JobTitle',

    # Employee Models
    'Employee',
    'EmployeeDocument',

    # Contract Models
    'EmployeeContract',
    'SalaryIncrement',

    # Settings Models
    'HRSettings',
    'SocialSecuritySettings',
    'PayrollAccountMapping',
    'LeaveType',

    # Attendance Models (Phase 2)
    'Attendance',
    'LeaveBalance',
    'LeaveRequest',
    'EarlyLeave',
    'Overtime',
    'Advance',
    'AdvanceInstallment',

    # Payroll Models (Phase 3)
    'Payroll',
    'PayrollDetail',
    'PayrollAllowance',
    'PayrollDeduction',
    'PayrollLoanDeduction',

    # Notification Models
    'HRNotification',
    'NotificationSetting',

    # Biometric Models (Phase 4)
    'BiometricDevice',
    'BiometricLog',
    'EmployeeBiometricMapping',
    'BiometricSyncLog',

    # Performance Models (Phase 5)
    'PerformancePeriod',
    'PerformanceCriteria',
    'PerformanceEvaluation',
    'PerformanceEvaluationDetail',
    'PerformanceGoal',
    'PerformanceNote',

    # Training Models (Phase 6)
    'TrainingCategory',
    'TrainingProvider',
    'TrainingCourse',
    'TrainingEnrollment',
    'TrainingRequest',
    'TrainingPlan',
    'TrainingPlanItem',
    'TrainingFeedback',
]

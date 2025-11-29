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

# Phase 5 Forms - Performance & Evaluation
from .performance_forms import (
    PerformancePeriodForm,
    PerformanceCriteriaForm,
    PerformanceEvaluationForm,
    PerformanceEvaluationDetailForm,
    SelfEvaluationForm,
    ManagerEvaluationForm,
    PerformanceGoalForm,
    PerformanceNoteForm,
    GoalProgressUpdateForm,
    EvaluationApprovalForm,
    BulkEvaluationForm,
)

# Phase 6 Forms - Training & Development
from .training_forms import (
    TrainingCategoryForm,
    TrainingProviderForm,
    TrainingCourseForm,
    TrainingEnrollmentForm,
    BulkEnrollmentForm,
    TrainingRequestForm,
    TrainingRequestApprovalForm,
    TrainingPlanForm,
    TrainingPlanItemForm,
    TrainingFeedbackForm,
    CourseFilterForm,
    EnrollmentUpdateForm,
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
    # Phase 5 - Performance
    'PerformancePeriodForm',
    'PerformanceCriteriaForm',
    'PerformanceEvaluationForm',
    'PerformanceEvaluationDetailForm',
    'SelfEvaluationForm',
    'ManagerEvaluationForm',
    'PerformanceGoalForm',
    'PerformanceNoteForm',
    'GoalProgressUpdateForm',
    'EvaluationApprovalForm',
    'BulkEvaluationForm',
    # Phase 6 - Training
    'TrainingCategoryForm',
    'TrainingProviderForm',
    'TrainingCourseForm',
    'TrainingEnrollmentForm',
    'BulkEnrollmentForm',
    'TrainingRequestForm',
    'TrainingRequestApprovalForm',
    'TrainingPlanForm',
    'TrainingPlanItemForm',
    'TrainingFeedbackForm',
    'CourseFilterForm',
    'EnrollmentUpdateForm',
]

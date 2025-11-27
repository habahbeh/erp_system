# apps/hr/views/__init__.py
"""
HR Views Package
المرحلة 1: الهيكل التنظيمي والموظفين
المرحلة 2: الحضور والإجازات والسلف
المرحلة 3: الرواتب
المرحلة 4: التقارير
"""

# Phase 1 Views
from .department_views import *
from .employee_views import *
from .contract_views import *
from .settings_views import *
from .ajax_views import *

# Phase 2 Views
from .attendance_views import *
from .leave_views import *
from .advance_views import *
from .overtime_views import *

# Phase 3 Views
from .payroll_views import *

# Phase 4 Views - Reports
from .report_views import *

# Phase 5 Views - Accounting Integration
from .accounting_views import *

# Phase 6 Views - Notifications
from .notification_views import *

# Phase 7 Views - Self Service
from .self_service_views import *

__all__ = [
    # ============ Phase 1 ============
    # Department views
    'DepartmentListView', 'DepartmentCreateView', 'DepartmentUpdateView', 'DepartmentDeleteView',

    # Job Grade views
    'JobGradeListView', 'JobGradeCreateView', 'JobGradeUpdateView', 'JobGradeDeleteView',

    # Job Title views
    'JobTitleListView', 'JobTitleCreateView', 'JobTitleUpdateView', 'JobTitleDeleteView',

    # Employee views
    'EmployeeListView', 'EmployeeCreateView', 'EmployeeUpdateView', 'EmployeeDeleteView', 'EmployeeDetailView',

    # Contract views
    'ContractListView', 'ContractCreateView', 'ContractUpdateView', 'ContractDeleteView', 'ContractDetailView',

    # Increment views
    'IncrementListView', 'IncrementCreateView', 'IncrementUpdateView', 'IncrementDeleteView',

    # Leave Type views
    'LeaveTypeListView', 'LeaveTypeCreateView', 'LeaveTypeUpdateView', 'LeaveTypeDeleteView',

    # Settings views
    'HRSettingsView', 'PayrollMappingCreateView', 'PayrollMappingUpdateView', 'PayrollMappingDeleteView',

    # Ajax views
    'department_datatable_ajax', 'job_grade_datatable_ajax', 'job_title_datatable_ajax',
    'employee_datatable_ajax', 'contract_datatable_ajax', 'increment_datatable_ajax',
    'leave_type_datatable_ajax', 'employee_search_ajax', 'department_search_ajax',
    # Phase 2 Ajax views
    'attendance_datatable_ajax', 'leave_request_datatable_ajax', 'leave_balance_datatable_ajax',
    'advance_datatable_ajax', 'overtime_datatable_ajax', 'early_leave_datatable_ajax',
    # Phase 3 Ajax views
    'payroll_datatable_ajax',

    # ============ Phase 2 ============
    # Attendance views
    'AttendanceListView', 'AttendanceCreateView', 'AttendanceUpdateView', 'AttendanceDeleteView',
    'BulkAttendanceView', 'AttendanceReportView',

    # Leave Request views
    'LeaveRequestListView', 'LeaveRequestCreateView', 'LeaveRequestDetailView',
    'LeaveRequestUpdateView', 'LeaveRequestDeleteView',

    # Leave Balance views
    'LeaveBalanceListView', 'LeaveBalanceCreateView', 'LeaveBalanceUpdateView', 'InitializeBalancesView',

    # Advance views
    'AdvanceListView', 'AdvanceCreateView', 'AdvanceDetailView', 'AdvanceUpdateView', 'AdvanceDeleteView',
    'DisburseAdvanceView', 'AdvanceInstallmentsView',

    # Overtime views
    'OvertimeListView', 'OvertimeCreateView', 'OvertimeUpdateView', 'OvertimeDeleteView', 'OvertimeApproveView',

    # Early Leave views
    'EarlyLeaveListView', 'EarlyLeaveCreateView', 'EarlyLeaveUpdateView', 'EarlyLeaveDeleteView', 'EarlyLeaveApproveView',

    # ============ Phase 3 - Payroll ============
    # Payroll views
    'PayrollListView', 'PayrollCreateView', 'PayrollDetailView', 'PayrollUpdateView', 'PayrollDeleteView',
    'PayrollProcessView', 'PayrollApproveView', 'PayrollPaymentView',
    'PayrollDetailEditView', 'PayrollDetailDeleteView', 'PayslipView', 'PayrollReportView',

    # ============ Phase 4 - Reports ============
    'HRDashboardReportView', 'EmployeeReportView', 'AttendanceReportView', 'LeaveReportView',
    'PayrollSummaryReportView', 'AdvanceReportView', 'OvertimeReportView',
    'DepartmentAnalysisReportView', 'ContractExpiryReportView',

    # ============ Phase 5 - Accounting Integration ============
    'PayrollJournalEntryView', 'PayrollPaymentJournalView',
    'AdvanceJournalEntryView', 'AccountingIntegrationDashboardView',

    # ============ Excel Export Views ============
    'ExportEmployeesExcelView', 'ExportAttendanceExcelView', 'ExportLeavesExcelView',
    'ExportPayrollExcelView', 'ExportAdvancesExcelView', 'ExportOvertimeExcelView',
    'ExportContractsExcelView',

    # ============ Phase 6 - Notifications ============
    'NotificationListView', 'NotificationMarkReadView', 'NotificationMarkAllReadView',
    'NotificationDeleteView', 'NotificationCountView', 'NotificationDropdownView',
    'GenerateNotificationsView', 'NotificationSettingsView',

    # ============ Phase 7 - Self Service ============
    'SelfServiceDashboardView', 'SelfServiceAttendanceView', 'SelfServiceLeaveBalanceView',
    'SelfServiceLeaveRequestListView', 'SelfServiceLeaveRequestCreateView',
    'SelfServicePayslipListView', 'SelfServicePayslipDetailView',
    'SelfServiceAdvanceListView', 'SelfServiceProfileView',
]

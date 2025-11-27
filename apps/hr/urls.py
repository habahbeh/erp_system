# apps/hr/urls.py
"""
مسارات الموارد البشرية - HR URLs
المرحلة 1: الهيكل التنظيمي والموظفين
المرحلة 2: الحضور والإجازات والسلف
المرحلة 3: الرواتب
المرحلة 4: التقارير
"""

from django.urls import path
from .views import (
    # ============ Phase 1 Views ============
    # Department views
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView,
    # Job Grade views
    JobGradeListView, JobGradeCreateView, JobGradeUpdateView, JobGradeDeleteView,
    # Job Title views
    JobTitleListView, JobTitleCreateView, JobTitleUpdateView, JobTitleDeleteView,
    # Employee views
    EmployeeListView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView, EmployeeDetailView,
    # Contract views
    ContractListView, ContractCreateView, ContractUpdateView, ContractDeleteView, ContractDetailView,
    # Increment views
    IncrementListView, IncrementCreateView, IncrementUpdateView, IncrementDeleteView,
    # Leave Type views
    LeaveTypeListView, LeaveTypeCreateView, LeaveTypeUpdateView, LeaveTypeDeleteView,
    # Settings views
    HRSettingsView, PayrollMappingCreateView, PayrollMappingUpdateView, PayrollMappingDeleteView,
    # Ajax views
    department_datatable_ajax, job_grade_datatable_ajax, job_title_datatable_ajax,
    employee_datatable_ajax, contract_datatable_ajax, increment_datatable_ajax,
    leave_type_datatable_ajax, employee_search_ajax, department_search_ajax,
    # Phase 2 Ajax views
    attendance_datatable_ajax, leave_request_datatable_ajax, leave_balance_datatable_ajax,
    advance_datatable_ajax, overtime_datatable_ajax, early_leave_datatable_ajax,
    # Phase 3 Ajax views
    payroll_datatable_ajax,

    # ============ Phase 2 Views ============
    # Attendance views
    AttendanceListView, AttendanceCreateView, AttendanceUpdateView, AttendanceDeleteView,
    BulkAttendanceView, AttendanceReportView,
    # Leave Request views
    LeaveRequestListView, LeaveRequestCreateView, LeaveRequestDetailView,
    LeaveRequestUpdateView, LeaveRequestDeleteView,
    # Leave Balance views
    LeaveBalanceListView, LeaveBalanceCreateView, LeaveBalanceUpdateView, InitializeBalancesView,
    # Advance views
    AdvanceListView, AdvanceCreateView, AdvanceDetailView, AdvanceUpdateView, AdvanceDeleteView,
    DisburseAdvanceView, AdvanceInstallmentsView,
    # Overtime views
    OvertimeListView, OvertimeCreateView, OvertimeUpdateView, OvertimeDeleteView, OvertimeApproveView,
    # Early Leave views
    EarlyLeaveListView, EarlyLeaveCreateView, EarlyLeaveUpdateView, EarlyLeaveDeleteView, EarlyLeaveApproveView,

    # ============ Phase 3 Views ============
    # Payroll views
    PayrollListView, PayrollCreateView, PayrollDetailView, PayrollUpdateView, PayrollDeleteView,
    PayrollProcessView, PayrollApproveView, PayrollPaymentView,
    PayrollDetailEditView, PayrollDetailDeleteView, PayslipView, PayrollReportView,

    # ============ Phase 4 Views - Reports ============
    HRDashboardReportView, EmployeeReportView, AttendanceReportView as AttendanceReportViewPhase4,
    LeaveReportView, PayrollSummaryReportView, AdvanceReportView,
    OvertimeReportView, DepartmentAnalysisReportView, ContractExpiryReportView,

    # ============ Phase 5 Views - Accounting Integration ============
    PayrollJournalEntryView, PayrollPaymentJournalView,
    AdvanceJournalEntryView, AccountingIntegrationDashboardView,

    # ============ Excel Export Views ============
    ExportEmployeesExcelView, ExportAttendanceExcelView, ExportLeavesExcelView,
    ExportPayrollExcelView, ExportAdvancesExcelView, ExportOvertimeExcelView,
    ExportContractsExcelView,

    # ============ Phase 6 Views - Notifications ============
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
    NotificationDeleteView, NotificationCountView, NotificationDropdownView,
    GenerateNotificationsView, NotificationSettingsView,

    # ============ Phase 7 Views - Self Service ============
    SelfServiceDashboardView, SelfServiceAttendanceView, SelfServiceLeaveBalanceView,
    SelfServiceLeaveRequestListView, SelfServiceLeaveRequestCreateView,
    SelfServicePayslipListView, SelfServicePayslipDetailView,
    SelfServiceAdvanceListView, SelfServiceProfileView,
)

app_name = 'hr'

urlpatterns = [
    # ============================================
    # الأقسام
    # ============================================
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),

    # ============================================
    # الدرجات الوظيفية
    # ============================================
    path('job-grades/', JobGradeListView.as_view(), name='job_grade_list'),
    path('job-grades/create/', JobGradeCreateView.as_view(), name='job_grade_create'),
    path('job-grades/<int:pk>/edit/', JobGradeUpdateView.as_view(), name='job_grade_update'),
    path('job-grades/<int:pk>/delete/', JobGradeDeleteView.as_view(), name='job_grade_delete'),

    # ============================================
    # المسميات الوظيفية
    # ============================================
    path('job-titles/', JobTitleListView.as_view(), name='job_title_list'),
    path('job-titles/create/', JobTitleCreateView.as_view(), name='job_title_create'),
    path('job-titles/<int:pk>/edit/', JobTitleUpdateView.as_view(), name='job_title_update'),
    path('job-titles/<int:pk>/delete/', JobTitleDeleteView.as_view(), name='job_title_delete'),

    # ============================================
    # الموظفين
    # ============================================
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),

    # ============================================
    # عقود العمل
    # ============================================
    path('contracts/', ContractListView.as_view(), name='contract_list'),
    path('contracts/create/', ContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/edit/', ContractUpdateView.as_view(), name='contract_update'),
    path('contracts/<int:pk>/delete/', ContractDeleteView.as_view(), name='contract_delete'),

    # ============================================
    # العلاوات
    # ============================================
    path('increments/', IncrementListView.as_view(), name='increment_list'),
    path('increments/create/', IncrementCreateView.as_view(), name='increment_create'),
    path('increments/<int:pk>/edit/', IncrementUpdateView.as_view(), name='increment_update'),
    path('increments/<int:pk>/delete/', IncrementDeleteView.as_view(), name='increment_delete'),

    # ============================================
    # أنواع الإجازات
    # ============================================
    path('leave-types/', LeaveTypeListView.as_view(), name='leave_type_list'),
    path('leave-types/create/', LeaveTypeCreateView.as_view(), name='leave_type_create'),
    path('leave-types/<int:pk>/edit/', LeaveTypeUpdateView.as_view(), name='leave_type_update'),
    path('leave-types/<int:pk>/delete/', LeaveTypeDeleteView.as_view(), name='leave_type_delete'),

    # ============================================
    # الإعدادات
    # ============================================
    path('settings/', HRSettingsView.as_view(), name='hr_settings'),
    path('settings/payroll-mapping/create/', PayrollMappingCreateView.as_view(), name='payroll_mapping_create'),
    path('settings/payroll-mapping/<int:pk>/edit/', PayrollMappingUpdateView.as_view(), name='payroll_mapping_update'),
    path('settings/payroll-mapping/<int:pk>/delete/', PayrollMappingDeleteView.as_view(), name='payroll_mapping_delete'),

    # ============================================
    # Ajax Endpoints
    # ============================================
    path('ajax/departments/', department_datatable_ajax, name='department_datatable_ajax'),
    path('ajax/job-grades/', job_grade_datatable_ajax, name='job_grade_datatable_ajax'),
    path('ajax/job-titles/', job_title_datatable_ajax, name='job_title_datatable_ajax'),
    path('ajax/employees/', employee_datatable_ajax, name='employee_datatable_ajax'),
    path('ajax/contracts/', contract_datatable_ajax, name='contract_datatable_ajax'),
    path('ajax/increments/', increment_datatable_ajax, name='increment_datatable_ajax'),
    path('ajax/leave-types/', leave_type_datatable_ajax, name='leave_type_datatable_ajax'),

    # Search Ajax
    path('ajax/employees/search/', employee_search_ajax, name='employee_search_ajax'),
    path('ajax/departments/search/', department_search_ajax, name='department_search_ajax'),

    # ============================================
    # Phase 2 - Ajax Endpoints
    # ============================================
    path('ajax/attendance/', attendance_datatable_ajax, name='attendance_datatable_ajax'),
    path('ajax/leave-requests/', leave_request_datatable_ajax, name='leave_request_datatable_ajax'),
    path('ajax/leave-balances/', leave_balance_datatable_ajax, name='leave_balance_datatable_ajax'),
    path('ajax/advances/', advance_datatable_ajax, name='advance_datatable_ajax'),
    path('ajax/overtime/', overtime_datatable_ajax, name='overtime_datatable_ajax'),
    path('ajax/early-leaves/', early_leave_datatable_ajax, name='early_leave_datatable_ajax'),
    # Phase 3 Ajax
    path('ajax/payroll/', payroll_datatable_ajax, name='payroll_datatable_ajax'),

    # ============================================
    # المرحلة الثانية - Phase 2
    # ============================================

    # ============================================
    # الحضور والانصراف
    # ============================================
    path('attendance/', AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/create/', AttendanceCreateView.as_view(), name='attendance_create'),
    path('attendance/<int:pk>/edit/', AttendanceUpdateView.as_view(), name='attendance_update'),
    path('attendance/<int:pk>/delete/', AttendanceDeleteView.as_view(), name='attendance_delete'),
    path('attendance/bulk/', BulkAttendanceView.as_view(), name='bulk_attendance'),
    path('attendance/report/', AttendanceReportView.as_view(), name='attendance_report'),

    # ============================================
    # طلبات الإجازات
    # ============================================
    path('leave-requests/', LeaveRequestListView.as_view(), name='leave_request_list'),
    path('leave-requests/create/', LeaveRequestCreateView.as_view(), name='leave_request_create'),
    path('leave-requests/<int:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('leave-requests/<int:pk>/edit/', LeaveRequestUpdateView.as_view(), name='leave_request_update'),
    path('leave-requests/<int:pk>/delete/', LeaveRequestDeleteView.as_view(), name='leave_request_delete'),

    # ============================================
    # أرصدة الإجازات
    # ============================================
    path('leave-balances/', LeaveBalanceListView.as_view(), name='leave_balance_list'),
    path('leave-balances/create/', LeaveBalanceCreateView.as_view(), name='leave_balance_create'),
    path('leave-balances/<int:pk>/edit/', LeaveBalanceUpdateView.as_view(), name='leave_balance_update'),
    path('leave-balances/initialize/', InitializeBalancesView.as_view(), name='initialize_balances'),

    # ============================================
    # السلف
    # ============================================
    path('advances/', AdvanceListView.as_view(), name='advance_list'),
    path('advances/create/', AdvanceCreateView.as_view(), name='advance_create'),
    path('advances/<int:pk>/', AdvanceDetailView.as_view(), name='advance_detail'),
    path('advances/<int:pk>/edit/', AdvanceUpdateView.as_view(), name='advance_update'),
    path('advances/<int:pk>/delete/', AdvanceDeleteView.as_view(), name='advance_delete'),
    path('advances/<int:pk>/disburse/', DisburseAdvanceView.as_view(), name='advance_disburse'),
    path('advances/installments/', AdvanceInstallmentsView.as_view(), name='advance_installments'),

    # ============================================
    # العمل الإضافي
    # ============================================
    path('overtime/', OvertimeListView.as_view(), name='overtime_list'),
    path('overtime/create/', OvertimeCreateView.as_view(), name='overtime_create'),
    path('overtime/<int:pk>/edit/', OvertimeUpdateView.as_view(), name='overtime_update'),
    path('overtime/<int:pk>/delete/', OvertimeDeleteView.as_view(), name='overtime_delete'),
    path('overtime/approve/', OvertimeApproveView.as_view(), name='overtime_approve'),

    # ============================================
    # المغادرات
    # ============================================
    path('early-leaves/', EarlyLeaveListView.as_view(), name='early_leave_list'),
    path('early-leaves/create/', EarlyLeaveCreateView.as_view(), name='early_leave_create'),
    path('early-leaves/<int:pk>/edit/', EarlyLeaveUpdateView.as_view(), name='early_leave_update'),
    path('early-leaves/<int:pk>/delete/', EarlyLeaveDeleteView.as_view(), name='early_leave_delete'),
    path('early-leaves/approve/', EarlyLeaveApproveView.as_view(), name='early_leave_approve'),

    # ============================================
    # المرحلة الثالثة - Phase 3: الرواتب
    # ============================================

    # ============================================
    # مسيرات الرواتب
    # ============================================
    path('payroll/', PayrollListView.as_view(), name='payroll_list'),
    path('payroll/create/', PayrollCreateView.as_view(), name='payroll_create'),
    path('payroll/<int:pk>/', PayrollDetailView.as_view(), name='payroll_detail'),
    path('payroll/<int:pk>/edit/', PayrollUpdateView.as_view(), name='payroll_update'),
    path('payroll/<int:pk>/delete/', PayrollDeleteView.as_view(), name='payroll_delete'),
    path('payroll/<int:pk>/process/', PayrollProcessView.as_view(), name='payroll_process'),
    path('payroll/<int:pk>/approve/', PayrollApproveView.as_view(), name='payroll_approve'),
    path('payroll/<int:pk>/payment/', PayrollPaymentView.as_view(), name='payroll_payment'),
    path('payroll/report/', PayrollReportView.as_view(), name='payroll_report'),

    # ============================================
    # تفاصيل الرواتب
    # ============================================
    path('payroll/detail/<int:pk>/edit/', PayrollDetailEditView.as_view(), name='payroll_detail_edit'),
    path('payroll/detail/<int:pk>/delete/', PayrollDetailDeleteView.as_view(), name='payroll_detail_delete'),
    path('payroll/detail/<int:pk>/payslip/', PayslipView.as_view(), name='payslip'),

    # ============================================
    # المرحلة الرابعة - Phase 4: التقارير
    # ============================================
    path('reports/', HRDashboardReportView.as_view(), name='reports_dashboard'),
    path('reports/employees/', EmployeeReportView.as_view(), name='report_employees'),
    path('reports/attendance/', AttendanceReportViewPhase4.as_view(), name='report_attendance'),
    path('reports/leaves/', LeaveReportView.as_view(), name='report_leaves'),
    path('reports/payroll/', PayrollSummaryReportView.as_view(), name='report_payroll_summary'),
    path('reports/advances/', AdvanceReportView.as_view(), name='report_advances'),
    path('reports/overtime/', OvertimeReportView.as_view(), name='report_overtime'),
    path('reports/departments/', DepartmentAnalysisReportView.as_view(), name='report_departments'),
    path('reports/contracts/', ContractExpiryReportView.as_view(), name='report_contracts'),

    # ============================================
    # المرحلة الخامسة - Phase 5: التكامل المحاسبي
    # ============================================
    path('accounting/', AccountingIntegrationDashboardView.as_view(), name='accounting_dashboard'),
    path('payroll/<int:pk>/journal-entry/', PayrollJournalEntryView.as_view(), name='payroll_journal_entry'),
    path('payroll/<int:pk>/payment-journal/', PayrollPaymentJournalView.as_view(), name='payroll_payment_journal'),
    path('advances/<int:pk>/journal-entry/', AdvanceJournalEntryView.as_view(), name='advance_journal_entry'),

    # ============================================
    # تصدير Excel
    # ============================================
    path('export/employees/', ExportEmployeesExcelView.as_view(), name='export_employees_excel'),
    path('export/attendance/', ExportAttendanceExcelView.as_view(), name='export_attendance_excel'),
    path('export/leaves/', ExportLeavesExcelView.as_view(), name='export_leaves_excel'),
    path('export/payroll/', ExportPayrollExcelView.as_view(), name='export_payroll_excel'),
    path('export/advances/', ExportAdvancesExcelView.as_view(), name='export_advances_excel'),
    path('export/overtime/', ExportOvertimeExcelView.as_view(), name='export_overtime_excel'),
    path('export/contracts/', ExportContractsExcelView.as_view(), name='export_contracts_excel'),

    # ============================================
    # المرحلة السادسة - Phase 6: الإشعارات
    # ============================================
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/settings/', NotificationSettingsView.as_view(), name='notification_settings'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('notifications/<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification_delete'),
    path('notifications/generate/', GenerateNotificationsView.as_view(), name='generate_notifications'),

    # ============================================
    # Ajax Endpoints للإشعارات
    # ============================================
    path('ajax/notifications/count/', NotificationCountView.as_view(), name='notification_count'),
    path('ajax/notifications/dropdown/', NotificationDropdownView.as_view(), name='notification_dropdown'),

    # ============================================
    # المرحلة السابعة - Phase 7: الخدمة الذاتية
    # ============================================
    path('self-service/', SelfServiceDashboardView.as_view(), name='self_service_dashboard'),
    path('self-service/attendance/', SelfServiceAttendanceView.as_view(), name='self_service_attendance'),
    path('self-service/leave-balance/', SelfServiceLeaveBalanceView.as_view(), name='self_service_leave_balance'),
    path('self-service/leave-requests/', SelfServiceLeaveRequestListView.as_view(), name='self_service_leave_requests'),
    path('self-service/leave-requests/create/', SelfServiceLeaveRequestCreateView.as_view(), name='self_service_leave_request_create'),
    path('self-service/payslips/', SelfServicePayslipListView.as_view(), name='self_service_payslips'),
    path('self-service/payslips/<int:pk>/', SelfServicePayslipDetailView.as_view(), name='self_service_payslip_detail'),
    path('self-service/advances/', SelfServiceAdvanceListView.as_view(), name='self_service_advances'),
    path('self-service/profile/', SelfServiceProfileView.as_view(), name='self_service_profile'),
]

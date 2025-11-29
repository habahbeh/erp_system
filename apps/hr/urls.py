# apps/hr/urls.py
"""
مسارات الموارد البشرية - HR URLs
المرحلة 1: الهيكل التنظيمي والموظفين
المرحلة 2: الحضور والإجازات والسلف
المرحلة 3: الرواتب
المرحلة 4: التقارير
المرحلة 5: التكامل المحاسبي
المرحلة 6: الإشعارات
المرحلة 7: الخدمة الذاتية
المرحلة 8: أجهزة البصمة
المرحلة 9: التقييم والأداء
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

    # ============ Biometric Reports ============
    BiometricReportView, BiometricAttendanceReportView,
    ExportBiometricLogsExcelView, ExportBiometricAttendanceExcelView,

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

# ============ Phase 8 Views - Biometric ============
from .views.biometric_views import (
    BiometricDeviceListView, BiometricDeviceCreateView, BiometricDeviceUpdateView,
    BiometricDeviceDeleteView, BiometricDeviceDetailView,
    test_device_connection, sync_device, sync_all_devices,
    EmployeeMappingListView, EmployeeMappingCreateView, EmployeeMappingUpdateView,
    EmployeeMappingDeleteView, bulk_mapping_view,
    BiometricLogListView, process_unprocessed_logs,
    SyncLogListView,
)

# ============ Phase 9 Views - Performance ============
from .views.performance_views import (
    # Period views
    period_list, period_create, period_edit, period_delete,
    # Criteria views
    criteria_list, criteria_create, criteria_edit, criteria_delete,
    # Evaluation views
    evaluation_list, evaluation_create, evaluation_detail,
    self_evaluation, manager_evaluation, evaluation_approve,
    bulk_evaluation_create,
    # Goal views
    goal_list, goal_create, goal_edit, goal_detail, goal_update_progress, goal_delete,
    # Note views
    note_list, note_create, note_edit, note_delete,
    # Ajax views
    get_employees_by_department, get_employee_goals, get_evaluation_stats,
)

# ============ Phase 10 Views - Training ============
from .views.training_views import (
    # Category views
    category_list, category_create, category_edit, category_delete,
    # Provider views
    provider_list, provider_create, provider_edit, provider_delete,
    # Course views
    course_list, course_create, course_edit, course_detail, course_delete,
    # Enrollment views
    enrollment_list, enrollment_create, bulk_enrollment, enrollment_update, enrollment_delete,
    # Request views
    request_list, request_create, request_detail, request_approve,
    # Plan views
    plan_list, plan_create, plan_edit, plan_detail, plan_item_add,
    # Feedback views
    feedback_create,
    # Ajax views
    get_employees_for_enrollment, get_training_stats,
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

    # ============================================
    # المرحلة الثامنة - Phase 8: أجهزة البصمة
    # ============================================

    # أجهزة البصمة
    path('biometric/devices/', BiometricDeviceListView.as_view(), name='biometric_device_list'),
    path('biometric/devices/create/', BiometricDeviceCreateView.as_view(), name='biometric_device_create'),
    path('biometric/devices/<int:pk>/', BiometricDeviceDetailView.as_view(), name='biometric_device_detail'),
    path('biometric/devices/<int:pk>/edit/', BiometricDeviceUpdateView.as_view(), name='biometric_device_update'),
    path('biometric/devices/<int:pk>/delete/', BiometricDeviceDeleteView.as_view(), name='biometric_device_delete'),
    path('biometric/devices/<int:pk>/test/', test_device_connection, name='biometric_test_connection'),
    path('biometric/devices/<int:pk>/sync/', sync_device, name='biometric_sync_device'),
    path('biometric/sync-all/', sync_all_devices, name='biometric_sync_all'),

    # ربط الموظفين بأجهزة البصمة
    path('biometric/mappings/', EmployeeMappingListView.as_view(), name='biometric_mapping_list'),
    path('biometric/mappings/create/', EmployeeMappingCreateView.as_view(), name='biometric_mapping_create'),
    path('biometric/mappings/<int:pk>/edit/', EmployeeMappingUpdateView.as_view(), name='biometric_mapping_update'),
    path('biometric/mappings/<int:pk>/delete/', EmployeeMappingDeleteView.as_view(), name='biometric_mapping_delete'),
    path('biometric/mappings/bulk/', bulk_mapping_view, name='biometric_bulk_mapping'),

    # سجلات البصمة
    path('biometric/logs/', BiometricLogListView.as_view(), name='biometric_log_list'),
    path('biometric/logs/process/', process_unprocessed_logs, name='biometric_process_logs'),

    # سجلات المزامنة
    path('biometric/sync-logs/', SyncLogListView.as_view(), name='biometric_sync_log_list'),

    # تقارير البصمة
    path('reports/biometric/', BiometricReportView.as_view(), name='biometric_report'),
    path('reports/biometric/attendance/', BiometricAttendanceReportView.as_view(), name='biometric_attendance_report'),
    path('reports/biometric/export/logs/', ExportBiometricLogsExcelView.as_view(), name='export_biometric_logs_excel'),
    path('reports/biometric/export/attendance/', ExportBiometricAttendanceExcelView.as_view(), name='export_biometric_attendance_excel'),

    # ============================================
    # المرحلة التاسعة - Phase 9: التقييم والأداء
    # ============================================

    # ============================================
    # فترات التقييم
    # ============================================
    path('performance/periods/', period_list, name='period_list'),
    path('performance/periods/create/', period_create, name='period_create'),
    path('performance/periods/<int:pk>/edit/', period_edit, name='period_edit'),
    path('performance/periods/<int:pk>/delete/', period_delete, name='period_delete'),

    # ============================================
    # معايير التقييم
    # ============================================
    path('performance/criteria/', criteria_list, name='criteria_list'),
    path('performance/criteria/create/', criteria_create, name='criteria_create'),
    path('performance/criteria/<int:pk>/edit/', criteria_edit, name='criteria_edit'),
    path('performance/criteria/<int:pk>/delete/', criteria_delete, name='criteria_delete'),

    # ============================================
    # التقييمات
    # ============================================
    path('performance/evaluations/', evaluation_list, name='evaluation_list'),
    path('performance/evaluations/create/', evaluation_create, name='evaluation_create'),
    path('performance/evaluations/bulk-create/', bulk_evaluation_create, name='bulk_evaluation_create'),
    path('performance/evaluations/<int:pk>/', evaluation_detail, name='evaluation_detail'),
    path('performance/evaluations/<int:pk>/self/', self_evaluation, name='self_evaluation'),
    path('performance/evaluations/<int:pk>/manager/', manager_evaluation, name='manager_evaluation'),
    path('performance/evaluations/<int:pk>/approve/', evaluation_approve, name='evaluation_approve'),

    # ============================================
    # الأهداف
    # ============================================
    path('performance/goals/', goal_list, name='goal_list'),
    path('performance/goals/create/', goal_create, name='goal_create'),
    path('performance/goals/<int:pk>/', goal_detail, name='goal_detail'),
    path('performance/goals/<int:pk>/edit/', goal_edit, name='goal_edit'),
    path('performance/goals/<int:pk>/progress/', goal_update_progress, name='goal_update_progress'),
    path('performance/goals/<int:pk>/delete/', goal_delete, name='goal_delete'),

    # ============================================
    # الملاحظات
    # ============================================
    path('performance/notes/', note_list, name='note_list'),
    path('performance/notes/create/', note_create, name='note_create'),
    path('performance/notes/<int:pk>/edit/', note_edit, name='note_edit'),
    path('performance/notes/<int:pk>/delete/', note_delete, name='note_delete'),

    # ============================================
    # Ajax Endpoints للأداء
    # ============================================
    path('ajax/performance/employees-by-department/', get_employees_by_department, name='ajax_employees_by_department'),
    path('ajax/performance/employee-goals/', get_employee_goals, name='ajax_employee_goals'),
    path('ajax/performance/evaluation-stats/', get_evaluation_stats, name='ajax_evaluation_stats'),

    # ============================================
    # المرحلة العاشرة - Phase 10: التدريب والتطوير
    # ============================================

    # ============================================
    # تصنيفات التدريب
    # ============================================
    path('training/categories/', category_list, name='training_category_list'),
    path('training/categories/create/', category_create, name='training_category_create'),
    path('training/categories/<int:pk>/edit/', category_edit, name='training_category_edit'),
    path('training/categories/<int:pk>/delete/', category_delete, name='training_category_delete'),

    # ============================================
    # مقدمو التدريب
    # ============================================
    path('training/providers/', provider_list, name='training_provider_list'),
    path('training/providers/create/', provider_create, name='training_provider_create'),
    path('training/providers/<int:pk>/edit/', provider_edit, name='training_provider_edit'),
    path('training/providers/<int:pk>/delete/', provider_delete, name='training_provider_delete'),

    # ============================================
    # الدورات التدريبية
    # ============================================
    path('training/courses/', course_list, name='training_course_list'),
    path('training/courses/create/', course_create, name='training_course_create'),
    path('training/courses/<int:pk>/', course_detail, name='training_course_detail'),
    path('training/courses/<int:pk>/edit/', course_edit, name='training_course_edit'),
    path('training/courses/<int:pk>/delete/', course_delete, name='training_course_delete'),

    # ============================================
    # تسجيلات التدريب
    # ============================================
    path('training/enrollments/', enrollment_list, name='training_enrollment_list'),
    path('training/enrollments/create/', enrollment_create, name='training_enrollment_create'),
    path('training/enrollments/bulk/', bulk_enrollment, name='training_bulk_enrollment'),
    path('training/enrollments/<int:pk>/update/', enrollment_update, name='training_enrollment_update'),
    path('training/enrollments/<int:pk>/delete/', enrollment_delete, name='training_enrollment_delete'),

    # ============================================
    # طلبات التدريب
    # ============================================
    path('training/requests/', request_list, name='training_request_list'),
    path('training/requests/create/', request_create, name='training_request_create'),
    path('training/requests/<int:pk>/', request_detail, name='training_request_detail'),
    path('training/requests/<int:pk>/approve/', request_approve, name='training_request_approve'),

    # ============================================
    # خطط التدريب
    # ============================================
    path('training/plans/', plan_list, name='training_plan_list'),
    path('training/plans/create/', plan_create, name='training_plan_create'),
    path('training/plans/<int:pk>/', plan_detail, name='training_plan_detail'),
    path('training/plans/<int:pk>/edit/', plan_edit, name='training_plan_edit'),
    path('training/plans/<int:pk>/items/add/', plan_item_add, name='training_plan_item_add'),

    # ============================================
    # التغذية الراجعة
    # ============================================
    path('training/feedback/create/', feedback_create, name='training_feedback_create'),

    # ============================================
    # Ajax Endpoints للتدريب
    # ============================================
    path('ajax/training/employees/', get_employees_for_enrollment, name='ajax_training_employees'),
    path('ajax/training/stats/', get_training_stats, name='ajax_training_stats'),
]

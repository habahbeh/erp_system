# apps/hr/admin.py
"""
Django Admin Configuration for HR Module
المرحلة 1 - النماذج الأساسية
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    # Organization
    Department,
    JobGrade,
    JobTitle,
    # Employee
    Employee,
    EmployeeDocument,
    # Contract
    EmployeeContract,
    SalaryIncrement,
    # Settings
    HRSettings,
    SocialSecuritySettings,
    PayrollAccountMapping,
    LeaveType,
)


# ==========================================
# Organization Models Admin
# ==========================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'manager', 'level', 'company', 'is_active']
    list_filter = ['is_active', 'level', 'company']
    search_fields = ['code', 'name', 'name_en']
    raw_id_fields = ['parent', 'manager', 'cost_center', 'company', 'created_by']
    ordering = ['code']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': ('code', 'name', 'name_en', 'company')
        }),
        (_('الهيكل التنظيمي'), {
            'fields': ('parent', 'manager', 'level')
        }),
        (_('الربط المحاسبي'), {
            'fields': ('cost_center',),
            'classes': ('collapse',)
        }),
        (_('معلومات إضافية'), {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'level']


@admin.register(JobGrade)
class JobGradeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'level', 'min_salary', 'max_salary', 'annual_leave_days', 'company', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['code', 'name', 'name_en']
    raw_id_fields = ['company', 'created_by']
    ordering = ['level', 'code']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': ('code', 'name', 'name_en', 'level', 'company')
        }),
        (_('نطاق الراتب'), {
            'fields': ('min_salary', 'max_salary')
        }),
        (_('الإجازات'), {
            'fields': ('annual_leave_days', 'sick_leave_days')
        }),
        (_('معلومات إضافية'), {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'job_grade', 'min_salary', 'max_salary', 'company', 'is_active']
    list_filter = ['is_active', 'department', 'job_grade', 'company']
    search_fields = ['code', 'name', 'name_en']
    raw_id_fields = ['department', 'job_grade', 'company', 'created_by']
    ordering = ['code']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': ('code', 'name', 'name_en', 'company')
        }),
        (_('الربط التنظيمي'), {
            'fields': ('department', 'job_grade')
        }),
        (_('نطاق الراتب'), {
            'fields': ('min_salary', 'max_salary')
        }),
        (_('الوصف الوظيفي'), {
            'fields': ('description', 'responsibilities', 'requirements'),
            'classes': ('collapse',)
        }),
        (_('الحالة'), {
            'fields': ('is_active',)
        }),
    )


# ==========================================
# Employee Models Admin
# ==========================================

class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    fields = ['document_type', 'name', 'document_number', 'issue_date', 'expiry_date', 'file']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_number', 'full_name', 'department', 'job_title',
        'employment_status', 'status', 'basic_salary', 'hire_date', 'company', 'is_active'
    ]
    list_filter = [
        'status', 'employment_status', 'gender', 'marital_status',
        'department', 'job_title', 'job_grade', 'company', 'is_active'
    ]
    search_fields = [
        'employee_number', 'first_name', 'middle_name', 'last_name',
        'national_id', 'mobile', 'email', 'social_security_number'
    ]
    raw_id_fields = [
        'user', 'department', 'job_title', 'job_grade', 'branch',
        'manager', 'currency', 'company', 'created_by'
    ]
    readonly_fields = ['employee_number', 'created_at', 'updated_at']
    inlines = [EmployeeDocumentInline]
    date_hierarchy = 'hire_date'
    ordering = ['employee_number']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('employee_number', 'user', 'company', 'status', 'is_active')
        }),
        (_('البيانات الشخصية'), {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'full_name_en',
                'national_id', 'date_of_birth', 'nationality', 'gender', 'marital_status'
            )
        }),
        (_('معلومات الاتصال'), {
            'fields': ('mobile', 'phone', 'email', 'address')
        }),
        (_('معلومات التوظيف'), {
            'fields': (
                'hire_date', 'department', 'job_title', 'job_grade', 'branch',
                'manager', 'social_security_number', 'employment_status',
                'termination_date', 'termination_reason'
            )
        }),
        (_('الراتب والمزايا'), {
            'fields': (
                'basic_salary', 'fuel_allowance', 'other_allowances',
                'social_security_salary', 'currency',
                'working_hours_per_day', 'working_days_per_month'
            )
        }),
        (_('أرصدة الإجازات'), {
            'fields': ('annual_leave_balance', 'sick_leave_balance')
        }),
        (_('معلومات البنك'), {
            'fields': ('bank_name', 'bank_branch', 'bank_account', 'iban'),
            'classes': ('collapse',)
        }),
        (_('معلومات إضافية'), {
            'fields': ('photo', 'notes'),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('الاسم الكامل')


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'name', 'document_number', 'issue_date', 'expiry_date', 'is_expired']
    list_filter = ['document_type', 'company', 'is_active']
    search_fields = ['name', 'document_number', 'employee__first_name', 'employee__last_name']
    raw_id_fields = ['employee', 'company', 'created_by']

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.short_description = _('منتهي الصلاحية')
    is_expired.boolean = True


# ==========================================
# Contract Models Admin
# ==========================================

@admin.register(EmployeeContract)
class EmployeeContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_number', 'employee', 'contract_type', 'start_date',
        'end_date', 'contract_salary', 'status', 'is_expired'
    ]
    list_filter = ['status', 'contract_type', 'company']
    search_fields = ['contract_number', 'employee__first_name', 'employee__last_name', 'employee__employee_number']
    raw_id_fields = ['employee', 'signed_by', 'company', 'created_by']
    readonly_fields = ['contract_number', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'

    fieldsets = (
        (_('معلومات العقد'), {
            'fields': ('contract_number', 'employee', 'company', 'contract_type', 'status')
        }),
        (_('التواريخ'), {
            'fields': ('start_date', 'end_date', 'probation_period', 'notice_period')
        }),
        (_('الراتب'), {
            'fields': ('contract_salary',)
        }),
        (_('التوقيع'), {
            'fields': ('signed_date', 'signed_by', 'contract_file'),
            'classes': ('collapse',)
        }),
        (_('الشروط والملاحظات'), {
            'fields': ('terms_and_conditions', 'notes'),
            'classes': ('collapse',)
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.short_description = _('منتهي')
    is_expired.boolean = True


@admin.register(SalaryIncrement)
class SalaryIncrementAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'increment_type', 'old_salary', 'increment_amount',
        'new_salary', 'effective_date', 'status'
    ]
    list_filter = ['status', 'increment_type', 'is_percentage', 'company']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_number']
    raw_id_fields = ['employee', 'approved_by', 'company', 'created_by']
    readonly_fields = ['old_salary', 'new_salary', 'created_at', 'updated_at']
    date_hierarchy = 'effective_date'

    fieldsets = (
        (_('معلومات العلاوة'), {
            'fields': ('employee', 'company', 'increment_type', 'effective_date')
        }),
        (_('المبالغ'), {
            'fields': ('old_salary', 'is_percentage', 'increment_amount', 'new_salary')
        }),
        (_('الاعتماد'), {
            'fields': ('status', 'approved_by', 'approval_date')
        }),
        (_('ملاحظات'), {
            'fields': ('reason', 'notes'),
            'classes': ('collapse',)
        }),
    )


# ==========================================
# Settings Models Admin
# ==========================================

@admin.register(HRSettings)
class HRSettingsAdmin(admin.ModelAdmin):
    list_display = ['company', 'default_working_hours_per_day', 'default_annual_leave_days', 'auto_create_journal_entries']
    list_filter = ['auto_create_journal_entries', 'carry_forward_leave']

    fieldsets = (
        (_('الشركة'), {
            'fields': ('company',)
        }),
        (_('ساعات العمل'), {
            'fields': ('default_working_hours_per_day', 'default_working_days_per_month')
        }),
        (_('العمل الإضافي'), {
            'fields': ('overtime_regular_rate', 'overtime_holiday_rate')
        }),
        (_('الإجازات'), {
            'fields': (
                'default_annual_leave_days', 'default_sick_leave_days',
                'carry_forward_leave', 'max_carry_forward_days',
                'sick_leave_medical_certificate_days'
            )
        }),
        (_('إعدادات العقود'), {
            'fields': ('default_probation_days', 'default_notice_period_days')
        }),
        (_('إعدادات السلف'), {
            'fields': ('max_advance_percentage', 'max_installments')
        }),
        (_('إعدادات عامة'), {
            'fields': ('fiscal_year_start_month', 'auto_create_journal_entries')
        }),
    )


@admin.register(SocialSecuritySettings)
class SocialSecuritySettingsAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'employee_contribution_rate', 'company_contribution_rate',
        'minimum_insurable_salary', 'maximum_insurable_salary', 'is_active'
    ]
    list_filter = ['is_active']

    fieldsets = (
        (_('الشركة'), {
            'fields': ('company', 'is_active', 'effective_date')
        }),
        (_('نسب الاشتراك'), {
            'fields': ('employee_contribution_rate', 'company_contribution_rate')
        }),
        (_('حدود الراتب'), {
            'fields': ('minimum_insurable_salary', 'maximum_insurable_salary')
        }),
    )


@admin.register(PayrollAccountMapping)
class PayrollAccountMappingAdmin(admin.ModelAdmin):
    list_display = ['company', 'component', 'account', 'is_active']
    list_filter = ['is_active', 'component', 'company']
    raw_id_fields = ['account', 'company']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'is_paid', 'affects_salary', 'default_days',
        'requires_approval', 'carry_forward', 'company', 'is_active'
    ]
    list_filter = ['is_paid', 'affects_salary', 'requires_approval', 'carry_forward', 'is_active', 'company']
    search_fields = ['code', 'name', 'name_en']
    raw_id_fields = ['company']

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': ('code', 'name', 'name_en', 'company')
        }),
        (_('إعدادات النوع'), {
            'fields': ('is_paid', 'affects_salary', 'requires_approval', 'requires_attachment')
        }),
        (_('الرصيد'), {
            'fields': ('default_days', 'max_consecutive_days', 'allow_negative_balance', 'carry_forward')
        }),
        (_('معلومات إضافية'), {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
    )

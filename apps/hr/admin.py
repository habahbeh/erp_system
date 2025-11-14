from django.contrib import admin
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'company', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['code', 'name']
    raw_id_fields = ['parent', 'manager', 'company', 'created_by']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_number', 'first_name', 'last_name', 'department', 'job_title', 'employment_status', 'company', 'is_active']
    list_filter = ['employment_status', 'gender', 'is_active', 'company', 'department']
    search_fields = ['employee_number', 'first_name', 'last_name', 'national_id', 'phone', 'email']
    raw_id_fields = ['user', 'department', 'job_title', 'company', 'created_by']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('employee_number', 'user', 'company', 'employment_status', 'is_active')
        }),
        ('البيانات الشخصية', {
            'fields': ('first_name', 'last_name', 'father_name', 'gender', 'date_of_birth', 'national_id', 'marital_status')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'mobile', 'email', 'address')
        }),
        ('معلومات الوظيفة', {
            'fields': ('department', 'job_title', 'hire_date', 'contract_type')
        }),
        ('معلومات النظام', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

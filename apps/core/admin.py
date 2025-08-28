# apps/core/admin.py
"""
إعدادات لوحة التحكم لتطبيق النواة
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Company, Branch, AuditLog, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """إدارة المستخدمين"""

    # إضافة الحقول الجديدة
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('phone', 'company', 'branch', 'max_discount_percentage')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('phone', 'company', 'branch')
        }),
    )

    list_display = ['username', 'email', 'first_name', 'last_name', 'company', 'branch', 'is_active']
    list_filter = BaseUserAdmin.list_filter + ('company', 'branch')
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """إدارة الشركات"""

    list_display = ['name', 'tax_number', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_en', 'tax_number', 'commercial_register']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'name_en', 'logo')
        }),
        (_('معلومات قانونية'), {
            'fields': ('tax_number', 'commercial_register')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('phone', 'email', 'address')
        }),
        (_('الحالة'), {
            'fields': ('is_active',)
        }),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """إدارة الفروع"""

    list_display = ['code', 'name', 'company', 'is_main', 'is_active']
    list_filter = ['company', 'is_main', 'is_active']
    search_fields = ['code', 'name', 'company__name']

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('company', 'code', 'name')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('phone', 'address')
        }),
        (_('الإعدادات'), {
            'fields': ('is_main', 'is_active')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """إدارة سجل العمليات"""

    list_display = ['user', 'action', 'model_name', 'object_repr', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'model_name']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr',
                       'old_values', 'new_values', 'ip_address', 'user_agent', 'timestamp']

    def has_add_permission(self, request):
        """منع الإضافة اليدوية"""
        return False

    def has_delete_permission(self, request, obj=None):
        """منع الحذف"""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """إدارة ملفات المستخدمين"""

    list_display = ['user', 'max_discount_percentage', 'max_credit_limit']
    list_filter = ['allowed_branches']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('حدود الصلاحيات'), {
            'fields': ('max_discount_percentage', 'max_credit_limit')
        }),
        (_('قيود الفروع'), {
            'fields': ('allowed_branches',)
        }),
    )
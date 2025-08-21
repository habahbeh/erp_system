# apps/core/context_processors.py
"""
معالجات السياق المخصصة
توفر متغيرات عامة لجميع القوالب
"""

from django.conf import settings


def system_settings(request):
    """إعدادات النظام العامة"""
    return {
        'SYSTEM_NAME': 'نظام ERP',
        'SYSTEM_VERSION': '1.0.0',
        'COMPANY_NAME': request.current_company.name if hasattr(request, 'current_company') and request.current_company else '',
        'BRANCH_NAME': request.current_branch.name if hasattr(request, 'current_branch') and request.current_branch else '',
        'CURRENCY': 'د.أ',  # الدينار الأردني
    }
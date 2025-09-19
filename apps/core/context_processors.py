# apps/core/context_processors.py
"""
معالجات السياق المخصصة
توفر متغيرات عامة لجميع القوالب
"""

from django.conf import settings
from .models import Company


def system_settings(request):
    """إعدادات النظام العامة"""
    return {
        'SYSTEM_NAME': 'نظام ERP',
        'SYSTEM_VERSION': '1.0.0',
        'COMPANY_NAME': request.current_company.name if hasattr(request, 'current_company') and request.current_company else '',
        'BRANCH_NAME': request.current_branch.name if hasattr(request, 'current_branch') and request.current_branch else '',
        'CURRENCY': 'د.أ',  # الدينار الأردني
    }


def companies_processor(request):
    """إضافة الشركات المتاحة للسياق"""
    context = {}

    if hasattr(request, 'user') and request.user.is_authenticated:
        # للـ superuser - عرض كل الشركات
        if request.user.is_superuser:
            context['available_companies'] = Company.objects.filter(is_active=True).order_by('name')
            context['can_switch_companies'] = True
        else:
            # للمستخدمين العاديين - الشركة الواحدة فقط
            context['available_companies'] = Company.objects.filter(
                id=request.user.company.id if request.user.company else None
            )
            context['can_switch_companies'] = False

        # الشركة الحالية
        if hasattr(request, 'current_company'):
            context['current_company'] = request.current_company

        # الفرع الحالي
        if hasattr(request, 'current_branch'):
            context['current_branch'] = request.current_branch

    return context
# apps/core/decorators.py
"""
Decorators مخصصة للتطبيق
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


def branch_required(view_func):
    """التأكد من وجود فرع للمستخدم"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'current_branch') or not request.current_branch:
            messages.error(request, _('يجب اختيار فرع للمتابعة'))
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def company_required(view_func):
    """التأكد من وجود شركة للمستخدم"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'current_company') or not request.current_company:
            messages.error(request, _('يجب اختيار شركة للمتابعة'))
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def permission_required_with_message(perm, message=None):
    """
    صلاحية مطلوبة مع رسالة خطأ مخصصة
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                error_message = message or _('ليس لديك صلاحية للوصول لهذه الصفحة')

                # للطلبات AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HttpResponseForbidden(error_message)

                messages.error(request, error_message)
                return redirect('core:dashboard')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def ajax_login_required(view_func):
    """تسجيل دخول مطلوب للطلبات AJAX"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden(_('تسجيل الدخول مطلوب'))
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def superuser_required(view_func):
    """مطلوب صلاحيات مدير نظام"""

    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, _('هذا القسم مخصص لمديري النظام فقط'))
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def check_user_branch_access(view_func):
    """التحقق من صلاحية الوصول للفرع"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # تنفيذ منطق التحقق من الفرع هنا
        # يمكن تخصيصه حسب احتياجات المشروع
        return view_func(request, *args, **kwargs)

    return _wrapped_view
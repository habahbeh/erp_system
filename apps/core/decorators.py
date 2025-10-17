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


# في apps/core/decorators.py (إضافة في النهاية)

def custom_permission_required(permission_code, max_amount=None):
    """
    ديكوريتر للتحقق من الصلاحيات المخصصة

    الاستخدام:
    @custom_permission_required('approve_invoice')
    @custom_permission_required('approve_invoice', max_amount=10000)
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # التحقق من وجود profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, _('ملف المستخدم غير موجود'))
                return redirect('core:dashboard')

            # التحقق من الصلاحية
            if not request.user.profile.has_custom_permission(permission_code):
                messages.error(
                    request,
                    _('ليس لديك صلاحية: %(perm)s') % {'perm': permission_code}
                )
                return redirect('core:dashboard')

            # التحقق من حد المبلغ إذا وجد
            if max_amount is not None:
                user_max_amount = request.user.profile.get_permission_max_amount(permission_code)
                if user_max_amount and max_amount > user_max_amount:
                    messages.error(
                        request,
                        _('المبلغ يتجاوز الحد المسموح (%(max)s)') % {'max': user_max_amount}
                    )
                    return redirect('core:dashboard')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def amount_permission_required(permission_code, amount_field='amount'):
    """
    ديكوريتر للتحقق من الصلاحية مع المبلغ من الكائن

    الاستخدام:
    @amount_permission_required('approve_invoice', amount_field='total_amount')
    def approve_invoice(request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # الحصول على الكائن (افترض أن pk في kwargs)
            pk = kwargs.get('pk')
            if not pk:
                return view_func(request, *args, **kwargs)

            # محاولة الحصول على المبلغ من الكائن
            # هذا يحتاج تحسين حسب نوع الكائن

            # التحقق من الصلاحية
            if not hasattr(request.user, 'profile'):
                messages.error(request, _('ملف المستخدم غير موجود'))
                return redirect('core:dashboard')

            if not request.user.profile.has_custom_permission(permission_code):
                messages.error(
                    request,
                    _('ليس لديك صلاحية: %(perm)s') % {'perm': permission_code}
                )
                return redirect('core:dashboard')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
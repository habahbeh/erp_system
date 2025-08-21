# apps/core/decorators.py
"""
ديكوريترز مخصصة للصلاحيات والتحقق
توفر طرق سهلة للتحقق من الصلاحيات
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _


def branch_required(view_func):
    """التأكد من وجود فرع محدد للمستخدم"""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.current_branch:
            messages.error(request, _('يجب تحديد الفرع أولاً'))
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required_with_message(perm, message=None):
    """فحص الصلاحية مع رسالة مخصصة"""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_perm(perm) or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            error_message = message or _('ليس لديك صلاحية للوصول لهذه الصفحة')
            messages.error(request, error_message)
            return redirect('core:dashboard')

        return wrapper

    return decorator


def max_discount_required(discount_field='discount_percentage'):
    """التحقق من حد الخصم المسموح"""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                discount = float(request.POST.get(discount_field, 0))
                if not request.user.can_approve_discount(discount):
                    messages.error(
                        request,
                        _('الخصم المطلوب (%(discount)s%%) يتجاوز الحد المسموح لك (%(max)s%%)') % {
                            'discount': discount,
                            'max': request.user.profile.max_discount_percentage
                        }
                    )
                    return redirect(request.path)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
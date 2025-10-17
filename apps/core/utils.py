# apps/core/utils.py
"""
Utility functions للمشروع
"""

import string
import random
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from functools import wraps


def generate_code(prefix='', company=None, length=6):
    """توليد كود فريد"""

    # إنشاء رقم عشوائي
    chars = string.digits + string.ascii_uppercase
    random_part = ''.join(random.choices(chars, k=length))

    # إنشاء الكود النهائي
    if prefix:
        code = f"{prefix}-{random_part}"
    else:
        code = random_part

    return code


def export_to_excel(data, filename='export'):
    """تصدير البيانات إلى Excel"""
    pass  # سيتم تطويره لاحقاً


def export_to_pdf(data, filename='export'):
    """تصدير البيانات إلى PDF"""
    pass  # سيتم تطويره لاحقاً


def export_to_csv(data, filename='export'):
    """تصدير البيانات إلى CSV"""
    pass  # سيتم تطويره لاحقاً


def require_permission(permission_name):
    """
    ديكوريتر للدوال في الموديلات للتحقق من الصلاحيات

    الاستخدام:
    class MyModel(models.Model):
        @require_permission('can_approve')
        def approve(self, user):
            ...
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # استخراج user من args
            user = kwargs.get('user')
            if not user and args:
                user = args[0]

            if not user:
                raise ValueError('User parameter is required')

            # التحقق من الصلاحية
            full_permission = f'{self._meta.app_label}.{permission_name}'
            if not user.has_perm(full_permission):
                raise PermissionDenied(
                    f'User does not have permission: {full_permission}'
                )

            return method(self, *args, **kwargs)

        return wrapper

    return decorator


def require_custom_permission(permission_code, amount_field=None):
    """
    ديكوريتر للدوال في الموديلات للتحقق من الصلاحيات المخصصة

    الاستخدام:
    class Invoice(models.Model):
        @require_custom_permission('approve_invoice', amount_field='total_amount')
        def approve(self, user):
            ...
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # استخراج user
            user = kwargs.get('user')
            if not user and args:
                user = args[0]

            if not user:
                raise ValueError('User parameter is required')

            # التحقق من الصلاحية المخصصة
            if not hasattr(user, 'profile'):
                raise PermissionDenied('User profile not found')

            # التحقق من الصلاحية
            if not user.profile.has_custom_permission(permission_code):
                raise PermissionDenied(
                    f'User does not have custom permission: {permission_code}'
                )

            # التحقق من حد المبلغ إذا وجد
            if amount_field:
                amount = getattr(self, amount_field, None)
                if amount and not user.profile.has_custom_permission_with_limit(
                        permission_code, amount
                ):
                    max_amount = user.profile.get_permission_max_amount(permission_code)
                    raise PermissionDenied(
                        f'Amount {amount} exceeds user limit: {max_amount}'
                    )

            return method(self, *args, **kwargs)

        return wrapper

    return decorator
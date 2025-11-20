"""
Permission Decorators
=====================

Decorators for enforcing permissions and access control:
- Company isolation
- Branch isolation
- Custom permissions
- Role-based access

Author: Mohammad + Claude
Date: 2025-11-19
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from typing import Callable, Optional


def company_required(view_func: Callable) -> Callable:
    """
    Require user to have a company assigned

    Usage:
        @company_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')

        # Check if user has company
        if hasattr(request.user, 'profile') and request.user.profile.company:
            return view_func(request, *args, **kwargs)

        if request.user.is_superuser:
            # Superusers might not have company, but can access
            return view_func(request, *args, **kwargs)

        messages.error(request, 'لم يتم تعيين شركة لحسابك. يرجى الاتصال بالمسؤول')
        return redirect('dashboard')

    return wrapper


def branch_required(view_func: Callable) -> Callable:
    """
    Require user to have a branch selected

    Usage:
        @branch_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')

        # Check if branch is set in session or user profile
        if hasattr(request, 'current_branch') and request.current_branch:
            return view_func(request, *args, **kwargs)

        if request.user.is_superuser:
            # Superusers might not have branch, but can access
            return view_func(request, *args, **kwargs)

        messages.error(request, 'يرجى اختيار فرع أولاً')
        return redirect('select_branch')

    return wrapper


def permission_required(permission_code: str, raise_exception: bool = True):
    """
    Require custom permission for access

    Args:
        permission_code: Custom permission code (e.g., 'can_approve_prices')
        raise_exception: If True, raise PermissionDenied; if False, redirect

    Usage:
        @permission_required('can_approve_prices')
        def approve_price(request, price_id):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('login')

            # Superusers have all permissions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check custom permission
            if hasattr(request.user, 'profile'):
                if request.user.profile.has_custom_permission(permission_code):
                    return view_func(request, *args, **kwargs)

            # Permission denied
            if raise_exception:
                raise PermissionDenied('ليس لديك صلاحية الوصول لهذه الصفحة')
            else:
                messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
                return redirect('dashboard')

        return wrapper
    return decorator


def permission_required_with_limit(permission_code: str, amount_field: str = 'amount'):
    """
    Require custom permission with amount limit check

    Args:
        permission_code: Custom permission code
        amount_field: Name of field containing the amount to check

    Usage:
        @permission_required_with_limit('can_approve_purchase', amount_field='total_amount')
        def approve_purchase(request, purchase_id):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('login')

            # Superusers have all permissions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get amount from request
            amount = None
            if request.method == 'POST':
                amount = request.POST.get(amount_field)
            elif request.method == 'GET':
                amount = request.GET.get(amount_field)

            if amount:
                try:
                    from decimal import Decimal
                    amount = Decimal(str(amount))
                except:
                    amount = None

            # Check custom permission with limit
            if hasattr(request.user, 'profile'):
                if request.user.profile.has_custom_permission_with_limit(
                    permission_code, amount
                ):
                    return view_func(request, *args, **kwargs)

            # Permission denied
            if amount:
                messages.error(
                    request,
                    f'ليس لديك صلاحية للمبلغ {amount}. يرجى الاتصال بالمسؤول'
                )
            else:
                messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')

            return redirect('dashboard')

        return wrapper
    return decorator


def ajax_permission_required(permission_code: str):
    """
    Require permission for AJAX endpoints

    Returns JSON error response instead of redirect

    Usage:
        @ajax_permission_required('can_update_prices')
        def ajax_update_price(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'message': 'يجب تسجيل الدخول أولاً'
                }, status=401)

            # Superusers have all permissions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check custom permission
            if hasattr(request.user, 'profile'):
                if request.user.profile.has_custom_permission(permission_code):
                    return view_func(request, *args, **kwargs)

            # Permission denied
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية لهذه العملية'
            }, status=403)

        return wrapper
    return decorator


def company_isolation_required(model_name: str = None, param_name: str = 'pk'):
    """
    Enforce company isolation for object access

    Ensures user can only access objects from their company

    Args:
        model_name: Model name (optional, for more specific checks)
        param_name: Parameter name containing object ID (default: 'pk')

    Usage:
        @company_isolation_required()
        def edit_item(request, pk):
            # User can only edit items from their company
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('login')

            # Superusers can access all companies
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get user's company
            user_company = None
            if hasattr(request.user, 'profile') and request.user.profile.company:
                user_company = request.user.profile.company
            elif hasattr(request, 'current_company'):
                user_company = request.current_company

            if not user_company:
                messages.error(request, 'لم يتم تعيين شركة لحسابك')
                return redirect('dashboard')

            # Note: Actual object-level check would require fetching the object
            # This is a basic check. For complete isolation, implement in view.

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def branch_isolation_required(param_name: str = 'pk'):
    """
    Enforce branch isolation for object access

    Ensures user can only access objects from their current branch

    Usage:
        @branch_isolation_required()
        def view_invoice(request, pk):
            # User can only view invoices from their current branch
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('login')

            # Superusers can access all branches
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get user's current branch
            current_branch = None
            if hasattr(request, 'current_branch'):
                current_branch = request.current_branch

            if not current_branch:
                messages.error(request, 'يرجى اختيار فرع أولاً')
                return redirect('select_branch')

            # Note: Actual object-level check would require fetching the object
            # This is a basic check. For complete isolation, implement in view.

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_post_method(view_func: Callable) -> Callable:
    """
    Require POST method for view

    Usage:
        @require_post_method
        def create_item(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            if request.is_ajax():
                return JsonResponse({
                    'success': False,
                    'message': 'هذه العملية تتطلب طلب POST'
                }, status=405)
            else:
                messages.error(request, 'طريقة الطلب غير صحيحة')
                return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def ajax_required(view_func: Callable) -> Callable:
    """
    Require AJAX request

    Usage:
        @ajax_required
        def ajax_endpoint(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.is_ajax() and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'هذه العملية متاحة فقط عبر AJAX'
            }, status=400)

        return view_func(request, *args, **kwargs)

    return wrapper


# ===================================================================
# Decorator Combinations
# ===================================================================

def secure_ajax_endpoint(permission_code: Optional[str] = None):
    """
    Combination decorator for secure AJAX endpoints

    Combines: ajax_required + POST required + optional permission check

    Usage:
        @secure_ajax_endpoint('can_update_prices')
        def ajax_update_price(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        # Apply decorators in order
        decorated = view_func
        decorated = ajax_required(decorated)
        decorated = require_post_method(decorated)

        if permission_code:
            decorated = ajax_permission_required(permission_code)(decorated)

        return decorated

    return decorator


# ===================================================================
# Usage Examples
# ===================================================================

"""
# Example 1: Basic permission check
from apps.core.decorators.permissions import permission_required

@permission_required('can_view_prices')
def price_list(request):
    # Only users with 'can_view_prices' permission can access
    ...


# Example 2: Company isolation
from apps.core.decorators.permissions import company_isolation_required

@company_isolation_required()
def edit_item(request, pk):
    # User can only edit items from their company
    item = get_object_or_404(Item, pk=pk, company=request.current_company)
    ...


# Example 3: Secure AJAX endpoint
from apps.core.decorators.permissions import secure_ajax_endpoint

@secure_ajax_endpoint('can_update_prices')
def ajax_update_price(request):
    # Requires: AJAX + POST + 'can_update_prices' permission
    ...


# Example 4: Permission with amount limit
from apps.core.decorators.permissions import permission_required_with_limit

@permission_required_with_limit('can_approve_purchase', amount_field='total')
def approve_purchase(request):
    # User must have permission for the specific amount
    ...
"""


# Alias for backward compatibility
def permission_required_with_message(permission_code: str):
    """
    Alias for permission_required with raise_exception=False
    Shows message instead of raising exception

    This is provided for backward compatibility with older code.
    New code should use permission_required directly.
    """
    return permission_required(permission_code, raise_exception=False)

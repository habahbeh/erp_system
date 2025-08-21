"""
Views الأساسية لتطبيق النواة
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import Branch


@login_required
def dashboard(request):
    """الصفحة الرئيسية"""
    context = {
        'title': _('لوحة التحكم'),
        'current_branch': request.current_branch,
        'current_company': request.current_company,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def switch_branch(request, branch_id):
    """تبديل الفرع الحالي"""
    try:
        branch = Branch.objects.get(id=branch_id)
        if request.user.can_access_branch(branch):
            request.session['current_branch'] = branch_id
            messages.success(
                request,
                _('تم التبديل إلى فرع: %(branch)s') % {'branch': branch.name}
            )
        else:
            messages.error(request, _('ليس لديك صلاحية للوصول لهذا الفرع'))
    except Branch.DoesNotExist:
        messages.error(request, _('الفرع غير موجود'))

    return redirect('core:dashboard')
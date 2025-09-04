# apps/core/views/base_views.py
"""
Views الأساسية - Dashboard والتنقل
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import Branch, Item, BusinessPartner, ItemCategory, Warehouse


@login_required
def dashboard(request):
    """الصفحة الرئيسية"""

    # الحصول على الإحصائيات
    context = {
        'title': _('لوحة التحكم'),
        'current_branch': request.current_branch,
        'current_company': request.current_company,
    }

    # إضافة إحصائيات إذا كان هناك شركة حالية
    if hasattr(request, 'current_company') and request.current_company:
        company = request.current_company

        # إحصائيات الأصناف
        if request.user.has_perm('core.view_item'):
            context['items_count'] = Item.objects.filter(company=company).count()
            context['recent_items'] = Item.objects.filter(company=company).order_by('-created_at')[:5]

        # إحصائيات الشركاء التجاريين
        if request.user.has_perm('core.view_businesspartner'):
            context['partners_count'] = BusinessPartner.objects.filter(company=company).count()

        # إحصائيات التصنيفات
        if request.user.has_perm('core.view_itemcategory'):
            context['categories_count'] = ItemCategory.objects.filter(company=company).count()

        # إحصائيات المستودعات
        if request.user.has_perm('core.view_warehouse'):
            context['warehouses_count'] = Warehouse.objects.filter(company=company).count()

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
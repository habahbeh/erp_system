# apps/core/views/base_views.py
"""
Views الأساسية - Dashboard والتنقل
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from ..models import Branch, Item, BusinessPartner, ItemCategory, Warehouse, Brand, UnitOfMeasure, Currency, NumberingSequence, VariantAttribute

User = get_user_model()


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

        # إحصائيات العلامات التجارية
        if request.user.has_perm('core.view_brand'):
            context['brands_count'] = Brand.objects.filter(company=company).count()

        # إحصائيات وحدات القياس
        if request.user.has_perm('core.view_unitofmeasure'):
            context['units_count'] = UnitOfMeasure.objects.filter(company=company).count()

        # إحصائيات العملات
        if request.user.has_perm('core.view_currency'):
            context['currencies_count'] = Currency.objects.filter(is_active=True).count()
            context['base_currency'] = Currency.objects.filter(is_base=True).first()

        # إحصائيات الفروع
        if request.user.has_perm('core.view_branch'):
            context['branches_count'] = Branch.objects.filter(company=company).count()

        # إحصائيات تسلسل الترقيم
        if request.user.has_perm('core.view_numberingsequence'):
            context['numbering_sequences_count'] = NumberingSequence.objects.filter(company=company).count()
            context['total_document_types'] = len(NumberingSequence.DOCUMENT_TYPES)

        if request.user.has_perm('core.view_variantattribute'):
            context['variant_attributes_count'] = VariantAttribute.objects.filter(company=company).count()

        # إحصائيات المستخدمين - إضافة جديد
        if request.user.has_perm('auth.view_user'):
            context['users_count'] = User.objects.filter(company=company, is_active=True).count()
            context['total_users_count'] = User.objects.filter(company=company).count()
            context['superuser_count'] = User.objects.filter(company=company, is_superuser=True).count()
            context['staff_count'] = User.objects.filter(company=company, is_staff=True, is_superuser=False).count()
            context['recent_users'] = User.objects.filter(company=company).order_by('-date_joined')[:5]

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
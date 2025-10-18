# apps/assets/views/settings_views.py
"""
Settings Views - إعدادات نظام الأصول
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import AssetCategory, DepreciationMethod, AssetCondition, MaintenanceType
from ..forms import AssetCategoryForm, DepreciationMethodForm, AssetConditionForm, MaintenanceTypeForm


# ==================== Asset Category Views ====================

class AssetCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة فئات الأصول"""

    template_name = 'assets/settings/category_list.html'
    permission_required = 'assets.view_assetcategory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_categories = AssetCategory.objects.filter(company=self.request.current_company).count()
        root_categories = AssetCategory.objects.filter(
            company=self.request.current_company,
            parent__isnull=True
        ).count()

        context.update({
            'title': _('فئات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assetcategory'),
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'total_categories': total_categories,
            'root_categories': root_categories,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الإعدادات'), 'url': '#'},
                {'title': _('فئات الأصول'), 'url': ''}
            ],
        })
        return context


class AssetCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء فئة أصول جديدة"""

    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/settings/category_form.html'
    permission_required = 'assets.add_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء فئة الأصول {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء فئة أصول'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AssetCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل فئة أصول"""

    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/settings/category_form.html'
    permission_required = 'assets.change_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث فئة الأصول {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': f'تعديل {self.object.name}', 'url': ''}
            ],
        })
        return context


class AssetCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف فئة أصول"""

    model = AssetCategory
    template_name = 'assets/settings/category_confirm_delete.html'
    permission_required = 'assets.delete_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود أصول أو فئات فرعية
        if self.object.assets.exists():
            messages.error(request, 'لا يمكن حذف الفئة لوجود أصول مرتبطة')
            return redirect('assets:category_list')

        if self.object.children.exists():
            messages.error(request, 'لا يمكن حذف الفئة لوجود فئات فرعية')
            return redirect('assets:category_list')

        category_name = self.object.name
        messages.success(request, f'تم حذف فئة الأصول {category_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Depreciation Method Views ====================

class DepreciationMethodListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة طرق الإهلاك"""

    template_name = 'assets/settings/depreciation_method_list.html'
    permission_required = 'assets.view_depreciationmethod'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_methods = DepreciationMethod.objects.count()
        active_methods = DepreciationMethod.objects.filter(is_active=True).count()

        context.update({
            'title': _('طرق الإهلاك'),
            'can_add': self.request.user.has_perm('assets.add_depreciationmethod'),
            'can_edit': self.request.user.has_perm('assets.change_depreciationmethod'),
            'can_delete': self.request.user.has_perm('assets.delete_depreciationmethod'),
            'total_methods': total_methods,
            'active_methods': active_methods,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الإعدادات'), 'url': '#'},
                {'title': _('طرق الإهلاك'), 'url': ''}
            ],
        })
        return context


class DepreciationMethodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء طريقة إهلاك جديدة"""

    model = DepreciationMethod
    form_class = DepreciationMethodForm
    template_name = 'assets/settings/depreciation_method_form.html'
    permission_required = 'assets.add_depreciationmethod'
    success_url = reverse_lazy('assets:depreciation_method_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء طريقة الإهلاك {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء طريقة إهلاك'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('طرق الإهلاك'), 'url': reverse('assets:depreciation_method_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class DepreciationMethodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل طريقة إهلاك"""

    model = DepreciationMethod
    form_class = DepreciationMethodForm
    template_name = 'assets/settings/depreciation_method_form.html'
    permission_required = 'assets.change_depreciationmethod'
    success_url = reverse_lazy('assets:depreciation_method_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث طريقة الإهلاك {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('طرق الإهلاك'), 'url': reverse('assets:depreciation_method_list')},
                {'title': f'تعديل {self.object.name}', 'url': ''}
            ],
        })
        return context


class DepreciationMethodDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف طريقة إهلاك"""

    model = DepreciationMethod
    template_name = 'assets/settings/depreciation_method_confirm_delete.html'
    permission_required = 'assets.delete_depreciationmethod'
    success_url = reverse_lazy('assets:depreciation_method_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود أصول تستخدم هذه الطريقة
        from ..models import Asset
        if Asset.objects.filter(depreciation_method=self.object).exists():
            messages.error(request, 'لا يمكن حذف طريقة الإهلاك لوجود أصول تستخدمها')
            return redirect('assets:depreciation_method_list')

        method_name = self.object.name
        messages.success(request, f'تم حذف طريقة الإهلاك {method_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Asset Condition Views ====================

class AssetConditionListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة حالات الأصول"""

    template_name = 'assets/settings/condition_list.html'
    permission_required = 'assets.view_assetcondition'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_conditions = AssetCondition.objects.count()
        active_conditions = AssetCondition.objects.filter(is_active=True).count()

        context.update({
            'title': _('حالات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assetcondition'),
            'can_edit': self.request.user.has_perm('assets.change_assetcondition'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcondition'),
            'total_conditions': total_conditions,
            'active_conditions': active_conditions,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الإعدادات'), 'url': '#'},
                {'title': _('حالات الأصول'), 'url': ''}
            ],
        })
        return context


class AssetConditionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء حالة أصل جديدة"""

    model = AssetCondition
    form_class = AssetConditionForm
    template_name = 'assets/settings/condition_form.html'
    permission_required = 'assets.add_assetcondition'
    success_url = reverse_lazy('assets:condition_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء حالة الأصل {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء حالة أصل'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('حالات الأصول'), 'url': reverse('assets:condition_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AssetConditionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل حالة أصل"""

    model = AssetCondition
    form_class = AssetConditionForm
    template_name = 'assets/settings/condition_form.html'
    permission_required = 'assets.change_assetcondition'
    success_url = reverse_lazy('assets:condition_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث حالة الأصل {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('حالات الأصول'), 'url': reverse('assets:condition_list')},
                {'title': f'تعديل {self.object.name}', 'url': ''}
            ],
        })
        return context


class AssetConditionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف حالة أصل"""

    model = AssetCondition
    template_name = 'assets/settings/condition_confirm_delete.html'
    permission_required = 'assets.delete_assetcondition'
    success_url = reverse_lazy('assets:condition_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود أصول بهذه الحالة
        from ..models import Asset
        if Asset.objects.filter(condition=self.object).exists():
            messages.error(request, 'لا يمكن حذف حالة الأصل لوجود أصول بهذه الحالة')
            return redirect('assets:condition_list')

        condition_name = self.object.name
        messages.success(request, f'تم حذف حالة الأصل {condition_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Maintenance Type Views ====================

class MaintenanceTypeListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة أنواع الصيانة"""

    template_name = 'assets/settings/maintenance_type_list.html'
    permission_required = 'assets.view_maintenancetype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_types = MaintenanceType.objects.count()
        active_types = MaintenanceType.objects.filter(is_active=True).count()

        context.update({
            'title': _('أنواع الصيانة'),
            'can_add': self.request.user.has_perm('assets.add_maintenancetype'),
            'can_edit': self.request.user.has_perm('assets.change_maintenancetype'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenancetype'),
            'total_types': total_types,
            'active_types': active_types,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الإعدادات'), 'url': '#'},
                {'title': _('أنواع الصيانة'), 'url': ''}
            ],
        })
        return context


class MaintenanceTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء نوع صيانة جديد"""

    model = MaintenanceType
    form_class = MaintenanceTypeForm
    template_name = 'assets/settings/maintenance_type_form.html'
    permission_required = 'assets.add_maintenancetype'
    success_url = reverse_lazy('assets:maintenance_type_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء نوع الصيانة {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء نوع صيانة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('أنواع الصيانة'), 'url': reverse('assets:maintenance_type_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class MaintenanceTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل نوع صيانة"""

    model = MaintenanceType
    form_class = MaintenanceTypeForm
    template_name = 'assets/settings/maintenance_type_form.html'
    permission_required = 'assets.change_maintenancetype'
    success_url = reverse_lazy('assets:maintenance_type_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث نوع الصيانة {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('أنواع الصيانة'), 'url': reverse('assets:maintenance_type_list')},
                {'title': f'تعديل {self.object.name}', 'url': ''}
            ],
        })
        return context


class MaintenanceTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف نوع صيانة"""

    model = MaintenanceType
    template_name = 'assets/settings/maintenance_type_confirm_delete.html'
    permission_required = 'assets.delete_maintenancetype'
    success_url = reverse_lazy('assets:maintenance_type_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود صيانات بهذا النوع
        from ..models import AssetMaintenance, MaintenanceSchedule
        if AssetMaintenance.objects.filter(maintenance_type=self.object).exists():
            messages.error(request, 'لا يمكن حذف نوع الصيانة لوجود سجلات صيانة مرتبطة')
            return redirect('assets:maintenance_type_list')

        if MaintenanceSchedule.objects.filter(maintenance_type=self.object).exists():
            messages.error(request, 'لا يمكن حذف نوع الصيانة لوجود جداول صيانة مرتبطة')
            return redirect('assets:maintenance_type_list')

        type_name = self.object.name
        messages.success(request, f'تم حذف نوع الصيانة {type_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.view_assetcategory')
@require_http_methods(["GET"])
def asset_category_datatable_ajax(request):
    """Ajax endpoint لجدول فئات الأصول"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = AssetCategory.objects.filter(
            company=request.current_company
        ).select_related('parent', 'default_depreciation_method').annotate(
            assets_count=Count('assets')
        )

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        queryset = queryset.order_by('level', 'code')

        total_records = AssetCategory.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_assetcategory')
        can_delete = request.user.has_perm('assets.delete_assetcategory')

        for category in queryset:
            indent = '  ' * (category.level - 1)

            actions = []
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:category_update', args=[category.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and category.assets_count == 0 and not category.children.exists():
                actions.append(f'''
                    <a href="{reverse('assets:category_delete', args=[category.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                category.code,
                indent + category.name,
                category.parent.name if category.parent else '--',
                f'المستوى {category.level}',
                category.default_depreciation_method.name if category.default_depreciation_method else '--',
                f'<span class="badge bg-secondary">{category.assets_count}</span>',
                ' '.join(actions) if actions else '--'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_depreciationmethod')
@require_http_methods(["GET"])
def depreciation_method_datatable_ajax(request):
    """Ajax endpoint لجدول طرق الإهلاك"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = DepreciationMethod.objects.all()

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        queryset = queryset.order_by('code')

        total_records = DepreciationMethod.objects.count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_depreciationmethod')
        can_delete = request.user.has_perm('assets.delete_depreciationmethod')

        for method in queryset:
            status_badge = '<span class="badge bg-success">نشط</span>' if method.is_active else '<span class="badge bg-secondary">غير نشط</span>'

            actions = []
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:depreciation_method_update', args=[method.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('assets:depreciation_method_delete', args=[method.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                method.code,
                method.name,
                method.get_method_type_display(),
                f'{method.rate_percentage}%' if method.rate_percentage else '--',
                status_badge,
                ' '.join(actions) if actions else '--'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_assetcondition')
@require_http_methods(["GET"])
def asset_condition_datatable_ajax(request):
    """Ajax endpoint لجدول حالات الأصول"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = AssetCondition.objects.all()

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value)
            )

        queryset = queryset.order_by('name')

        total_records = AssetCondition.objects.count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_assetcondition')
        can_delete = request.user.has_perm('assets.delete_assetcondition')

        for condition in queryset:
            status_badge = '<span class="badge bg-success">نشط</span>' if condition.is_active else '<span class="badge bg-secondary">غير نشط</span>'
            color_preview = f'<span class="badge" style="background-color: {condition.color_code}">{condition.color_code}</span>'

            actions = []
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:condition_update', args=[condition.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('assets:condition_delete', args=[condition.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                condition.name,
                condition.name_en,
                color_preview,
                status_badge,
                ' '.join(actions) if actions else '--'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_maintenancetype')
@require_http_methods(["GET"])
def maintenance_type_datatable_ajax(request):
    """Ajax endpoint لجدول أنواع الصيانة"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    try:
        queryset = MaintenanceType.objects.all()

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        queryset = queryset.order_by('code')

        total_records = MaintenanceType.objects.count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_maintenancetype')
        can_delete = request.user.has_perm('assets.delete_maintenancetype')

        for mtype in queryset:
            status_badge = '<span class="badge bg-success">نشط</span>' if mtype.is_active else '<span class="badge bg-secondary">غير نشط</span>'

            actions = []
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_type_update', args=[mtype.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_type_delete', args=[mtype.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                mtype.code,
                mtype.name,
                mtype.name_en,
                status_badge,
                ' '.join(actions) if actions else '--'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ: {str(e)}'
        })
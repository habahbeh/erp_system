# apps/assets/views/asset_views.py
"""
Views الأصول الثابتة
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q, Count, Sum, Prefetch
from django.core.paginator import Paginator
import json

from ..models import (
    Asset, AssetCategory, AssetDepreciation, AssetAttachment,
    AssetTransaction, AssetMaintenance
)
from ..forms import AssetForm, AssetCategoryForm, AssetFilterForm
from apps.core.mixins import CompanyMixin, AuditLogMixin


class AssetListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الأصول الثابتة"""

    template_name = 'assets/assets/asset_list.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # نموذج الفلترة
        filter_form = AssetFilterForm(
            self.request.GET,
            company=self.request.user.company
        )

        context.update({
            'title': 'سجل الأصول الثابتة',
            'filter_form': filter_form,
            'can_add': self.request.user.has_perm('assets.add_asset'),
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الأصول', 'url': ''}
            ],
        })

        return context


class AssetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء أصل ثابت جديد"""

    model = Asset
    form_class = AssetForm
    template_name = 'assets/assets/asset_form.html'
    permission_required = 'assets.add_asset'
    success_url = reverse_lazy('assets:asset_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['branch'] = self.request.user.branch
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم إنشاء الأصل {self.object.asset_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'إضافة أصل ثابت جديد',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الأصول', 'url': reverse('assets:asset_list')},
                {'title': 'إضافة جديد', 'url': ''}
            ],
        })
        return context


class AssetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل أصل ثابت"""

    model = Asset
    form_class = AssetForm
    template_name = 'assets/assets/asset_form.html'
    permission_required = 'assets.change_asset'
    success_url = reverse_lazy('assets:asset_list')

    def get_queryset(self):
        return Asset.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['branch'] = self.request.user.branch
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم تحديث الأصل {self.object.asset_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الأصل: {self.object.name}',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الأصول', 'url': reverse('assets:asset_list')},
                {'title': 'تعديل', 'url': ''}
            ],
        })
        return context


class AssetDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل أصل ثابت"""

    model = Asset
    template_name = 'assets/assets/asset_detail.html'
    permission_required = 'assets.view_asset'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.filter(
            company=self.request.user.company
        ).select_related(
            'category', 'condition', 'depreciation_method',
            'supplier', 'cost_center', 'responsible_employee'
        ).prefetch_related(
            'attachments',
            'depreciation_records',
            'transactions',
            'maintenances',
            'transfers',
            'valuations'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        # آخر 5 سجلات إهلاك
        recent_depreciations = asset.depreciation_records.order_by('-depreciation_date')[:5]

        # آخر 5 عمليات
        recent_transactions = asset.transactions.order_by('-transaction_date')[:5]

        # آخر 5 صيانة
        recent_maintenances = asset.maintenances.select_related(
            'maintenance_type'
        ).order_by('-scheduled_date')[:5]

        # المرفقات
        attachments = asset.attachments.order_by('-uploaded_at')

        # إحصائيات
        total_depreciation = asset.accumulated_depreciation
        total_maintenance_cost = asset.maintenances.filter(
            status='completed'
        ).aggregate(total=Sum('total_cost'))['total'] or 0

        context.update({
            'title': f'تفاصيل الأصل: {asset.name}',
            'recent_depreciations': recent_depreciations,
            'recent_transactions': recent_transactions,
            'recent_maintenances': recent_maintenances,
            'attachments': attachments,
            'total_maintenance_cost': total_maintenance_cost,
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الأصول', 'url': reverse('assets:asset_list')},
                {'title': asset.asset_number, 'url': ''}
            ],
        })

        return context


class AssetDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف أصل ثابت"""

    model = Asset
    template_name = 'assets/assets/asset_confirm_delete.html'
    permission_required = 'assets.delete_asset'
    success_url = reverse_lazy('assets:asset_list')

    def get_queryset(self):
        return Asset.objects.filter(company=self.request.user.company)

    def delete(self, request, *args, **kwargs):
        asset = self.get_object()
        asset_number = asset.asset_number

        # التحقق من عدم وجود عمليات مرتبطة
        if asset.transactions.exists():
            messages.error(
                request,
                f'لا يمكن حذف الأصل {asset_number} لوجود عمليات مرتبطة به'
            )
            return redirect('assets:asset_detail', pk=asset.pk)

        response = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            f'تم حذف الأصل {asset_number} بنجاح'
        )

        return response


@login_required
@permission_required('assets.view_asset', raise_exception=True)
def asset_datatable_ajax(request):
    """Ajax endpoint لجدول الأصول مع DataTables"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    cost_center_id = request.GET.get('cost_center', '')
    purchase_date_from = request.GET.get('purchase_date_from', '')
    purchase_date_to = request.GET.get('purchase_date_to', '')

    # القاعدة الأساسية
    queryset = Asset.objects.filter(
        company=request.user.company
    ).select_related(
        'category', 'condition', 'branch', 'cost_center'
    )

    # البحث
    if search_value:
        queryset = queryset.filter(
            Q(asset_number__icontains=search_value) |
            Q(name__icontains=search_value) |
            Q(serial_number__icontains=search_value) |
            Q(barcode__icontains=search_value)
        )

    # الفلاتر
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if status:
        queryset = queryset.filter(status=status)

    if cost_center_id:
        queryset = queryset.filter(cost_center_id=cost_center_id)

    if purchase_date_from:
        queryset = queryset.filter(purchase_date__gte=purchase_date_from)

    if purchase_date_to:
        queryset = queryset.filter(purchase_date__lte=purchase_date_to)

    # العد
    total_records = Asset.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    # الترتيب
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')

    order_columns = ['asset_number', 'name', 'category__name', 'purchase_date', 'original_cost', 'book_value', 'status']

    if order_column_index < len(order_columns):
        order_field = order_columns[order_column_index]
        if order_direction == 'desc':
            order_field = f'-{order_field}'
        queryset = queryset.order_by(order_field)

    # التقسيم
    queryset = queryset[start:start + length]

    # البيانات
    data = []
    for asset in queryset:
        # حالة الأصل مع لون
        status_colors = {
            'active': 'success',
            'inactive': 'secondary',
            'under_maintenance': 'warning',
            'disposed': 'danger',
            'sold': 'info'
        }
        status_badge = f'<span class="badge bg-{status_colors.get(asset.status, "secondary")}">{asset.get_status_display()}</span>'

        # الإجراءات
        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="{reverse("assets:asset_detail", args=[asset.pk])}" 
                   class="btn btn-info" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if request.user.has_perm('assets.change_asset'):
            actions += f'''
                <a href="{reverse("assets:asset_update", args=[asset.pk])}" 
                   class="btn btn-primary" title="تعديل">
                    <i class="fas fa-edit"></i>
                </a>
            '''

        if request.user.has_perm('assets.delete_asset'):
            actions += f'''
                <a href="{reverse("assets:asset_delete", args=[asset.pk])}" 
                   class="btn btn-danger" title="حذف"
                   onclick="return confirm('هل أنت متأكد من حذف هذا الأصل؟')">
                    <i class="fas fa-trash"></i>
                </a>
            '''

        actions += '</div>'

        data.append([
            asset.asset_number,
            f'<strong>{asset.name}</strong>',
            asset.category.name if asset.category else '-',
            asset.purchase_date.strftime('%Y-%m-%d'),
            f'{asset.original_cost:,.3f}',
            f'{asset.book_value:,.3f}',
            status_badge,
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


# ═══════════════════════════════════════════════════════════
# فئات الأصول
# ═══════════════════════════════════════════════════════════

class AssetCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة فئات الأصول"""

    template_name = 'assets/categories/category_list.html'
    permission_required = 'assets.view_assetcategory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'فئات الأصول',
            'can_add': self.request.user.has_perm('assets.add_assetcategory'),
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'فئات الأصول', 'url': ''}
            ],
        })
        return context


class AssetCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إنشاء فئة أصول"""

    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/categories/category_form.html'
    permission_required = 'assets.add_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'تم إنشاء فئة الأصول بنجاح')
        return response


class AssetCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل فئة أصول"""

    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/categories/category_form.html'
    permission_required = 'assets.change_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث فئة الأصول بنجاح')
        return response


@login_required
def asset_category_datatable_ajax(request):
    """Ajax endpoint لجدول فئات الأصول"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = AssetCategory.objects.filter(
        company=request.user.company
    ).annotate(
        assets_count=Count('assets')
    ).select_related('parent')

    if search_value:
        queryset = queryset.filter(
            Q(code__icontains=search_value) |
            Q(name__icontains=search_value)
        )

    total_records = AssetCategory.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset[start:start + length]

    data = []
    for category in queryset:
        actions = f'''
            <a href="{reverse("assets:category_update", args=[category.pk])}" 
               class="btn btn-sm btn-primary">
                <i class="fas fa-edit"></i> تعديل
            </a>
        '''

        data.append([
            category.code,
            category.name,
            category.parent.name if category.parent else '-',
            category.level,
            category.assets_count,
            '<span class="badge bg-success">نشط</span>' if category.is_active else '<span class="badge bg-secondary">غير نشط</span>',
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })
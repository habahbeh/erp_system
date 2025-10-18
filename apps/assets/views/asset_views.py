# apps/assets/views/asset_views.py
"""
Asset Views - إدارة الأصول الثابتة والفئات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Prefetch
from django.utils.translation import gettext_lazy as _
import json
import qrcode
from io import BytesIO
import barcode
from barcode.writer import ImageWriter

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, AssetDepreciation, AssetAttachment,
    AssetTransaction, AssetMaintenance
)
from ..forms import AssetForm, AssetCategoryForm, AssetFilterForm


# =============================================================================
# Asset CRUD Views
# =============================================================================

class AssetListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الأصول الثابتة"""

    template_name = 'assets/assets/asset_list.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        company = self.request.user.company
        stats = Asset.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            total_cost=Sum('original_cost'),
            total_book_value=Sum('book_value')
        )

        context.update({
            'title': _('سجل الأصول الثابتة'),
            'filter_form': AssetFilterForm(self.request.GET, company=company),
            'can_add': self.request.user.has_perm('assets.add_asset'),
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'can_export': self.request.user.has_perm('assets.view_asset'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجل الأصول'), 'url': ''}
            ],
        })
        return context


class AssetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء أصل ثابت جديد"""

    model = Asset
    form_class = AssetForm
    template_name = 'assets/assets/asset_form.html'
    permission_required = 'assets.add_asset'

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

    def get_success_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة أصل ثابت جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجل الأصول'), 'url': reverse('assets:asset_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
        })
        return context


class AssetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل أصل ثابت"""

    model = Asset
    form_class = AssetForm
    template_name = 'assets/assets/asset_form.html'
    permission_required = 'assets.change_asset'

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

    def get_success_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الأصل: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجل الأصول'), 'url': reverse('assets:asset_list')},
                {'title': _('تعديل'), 'url': ''}
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
            'supplier', 'cost_center', 'responsible_employee',
            'branch', 'currency'
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

        # استخدام helper methods من Model
        context.update({
            'title': f'تفاصيل الأصل: {asset.name}',

            # Asset Status Checks
            'is_fully_depreciated': asset.is_fully_depreciated(),
            'is_warranty_valid': asset.is_warranty_valid(),
            'remaining_months': asset.get_remaining_months(),
            'depreciable_amount': asset.get_depreciable_amount(),

            # Recent Records
            'recent_depreciations': asset.depreciation_records.order_by('-depreciation_date')[:5],
            'recent_transactions': asset.transactions.order_by('-transaction_date')[:5],
            'recent_maintenances': asset.maintenances.select_related('maintenance_type').order_by('-scheduled_date')[
                                   :5],
            'attachments': asset.attachments.order_by('-uploaded_at'),

            # Statistics
            'total_maintenance_cost': asset.maintenances.filter(
                status='completed'
            ).aggregate(total=Sum('total_cost'))['total'] or 0,

            # Permissions
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'can_sell': asset.can_user_sell(self.request.user),
            'can_dispose': asset.can_user_dispose(self.request.user),
            'can_transfer': asset.can_user_transfer(self.request.user),
            'can_revalue': asset.can_user_revalue(self.request.user),
            'can_calculate_depreciation': asset.can_user_calculate_depreciation(self.request.user),

            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجل الأصول'), 'url': reverse('assets:asset_list')},
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

        # التحقق من عدم وجود إهلاك
        if asset.depreciation_records.exists():
            messages.error(
                request,
                f'لا يمكن حذف الأصل {asset_number} لوجود سجلات إهلاك'
            )
            return redirect('assets:asset_detail', pk=asset.pk)

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'تم حذف الأصل {asset_number} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'حذف الأصل: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سجل الأصول'), 'url': reverse('assets:asset_list')},
                {'title': _('حذف'), 'url': ''}
            ],
        })
        return context


# =============================================================================
# Asset Category CRUD Views
# =============================================================================

class AssetCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة فئات الأصول"""

    template_name = 'assets/categories/category_list.html'
    permission_required = 'assets.view_assetcategory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        stats = AssetCategory.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            with_assets=Count('id', filter=Q(assets__isnull=False))
        )

        context.update({
            'title': _('فئات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assetcategory'),
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': ''}
            ],
        })
        return context


class AssetCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
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
        messages.success(self.request, f'تم إنشاء فئة الأصول {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة فئة أصول'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': _('إضافة'), 'url': ''}
            ],
        })
        return context


class AssetCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
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
        messages.success(self.request, f'تم تحديث فئة الأصول {self.object.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class AssetCategoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل فئة الأصول"""

    model = AssetCategory
    template_name = 'assets/categories/category_detail.html'
    permission_required = 'assets.view_assetcategory'
    context_object_name = 'category'

    def get_queryset(self):
        return AssetCategory.objects.filter(
            company=self.request.user.company
        ).select_related(
            'parent',
            'default_depreciation_method',
            'asset_account',
            'accumulated_depreciation_account',
            'depreciation_expense_account'
        ).prefetch_related('assets')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # إحصائيات الفئة
        assets_stats = category.assets.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            total_cost=Sum('original_cost'),
            total_book_value=Sum('book_value')
        )

        context.update({
            'title': f'تفاصيل الفئة: {category.name}',
            'assets_stats': assets_stats,
            'full_path': category.get_full_path(),
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': category.name, 'url': ''}
            ],
        })
        return context


class AssetCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف فئة أصول"""

    model = AssetCategory
    template_name = 'assets/categories/category_confirm_delete.html'
    permission_required = 'assets.delete_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.user.company)

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name

        # التحقق من عدم وجود أصول
        if category.assets.exists():
            messages.error(
                request,
                f'لا يمكن حذف الفئة {category_name} لوجود أصول مرتبطة بها'
            )
            return redirect('assets:category_detail', pk=category.pk)

        # التحقق من عدم وجود فئات فرعية
        if category.children.exists():
            messages.error(
                request,
                f'لا يمكن حذف الفئة {category_name} لوجود فئات فرعية'
            )
            return redirect('assets:category_detail', pk=category.pk)

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'تم حذف الفئة {category_name} بنجاح')
        return response


# =============================================================================
# Ajax DataTables Endpoints
# =============================================================================

@login_required
@permission_required('assets.view_asset', raise_exception=True)
def asset_datatable_ajax(request):
    """Ajax endpoint لجدول الأصول"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    cost_center_id = request.GET.get('cost_center', '')
    branch_id = request.GET.get('branch', '')
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
    if branch_id:
        queryset = queryset.filter(branch_id=branch_id)
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

    # البيانات - استخدام helper methods
    data = []
    for asset in queryset:
        # حالة الأصل
        status_colors = {
            'active': 'success',
            'inactive': 'secondary',
            'under_maintenance': 'warning',
            'disposed': 'danger',
            'sold': 'info'
        }
        status_badge = f'<span class="badge bg-{status_colors.get(asset.status, "secondary")}">{asset.get_status_display()}</span>'

        # تحذيرات
        warnings = []
        if asset.is_fully_depreciated():
            warnings.append('<i class="fas fa-exclamation-triangle text-warning" title="مهلك بالكامل"></i>')
        if not asset.is_warranty_valid() and asset.warranty_end_date:
            warnings.append('<i class="fas fa-shield-alt text-danger" title="الضمان منتهي"></i>')

        warnings_html = ' '.join(warnings) if warnings else ''

        # الإجراءات
        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="{reverse("assets:asset_detail", args=[asset.pk])}" 
                   class="btn btn-info" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if request.user.has_perm('assets.change_asset'):
            actions += f'''
                <a href="{reverse("assets:asset_update", args=[asset.pk])}" 
                   class="btn btn-primary" title="تعديل" data-bs-toggle="tooltip">
                    <i class="fas fa-edit"></i>
                </a>
            '''

        if request.user.has_perm('assets.delete_asset'):
            actions += f'''
                <a href="{reverse("assets:asset_delete", args=[asset.pk])}" 
                   class="btn btn-danger" title="حذف" data-bs-toggle="tooltip"
                   onclick="return confirm('هل أنت متأكد من حذف هذا الأصل؟')">
                    <i class="fas fa-trash"></i>
                </a>
            '''

        actions += '</div>'

        data.append([
            f'{asset.asset_number} {warnings_html}',
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


@login_required
@permission_required('assets.view_assetcategory', raise_exception=True)
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
    ).select_related('parent', 'default_depreciation_method')

    if search_value:
        queryset = queryset.filter(
            Q(code__icontains=search_value) |
            Q(name__icontains=search_value)
        )

    total_records = AssetCategory.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('level', 'code')[start:start + length]

    data = []
    for category in queryset:
        # المسافة البادئة حسب المستوى
        indent = '&nbsp;&nbsp;&nbsp;' * (category.level - 1)

        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="{reverse("assets:category_detail", args=[category.pk])}" 
                   class="btn btn-info" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if request.user.has_perm('assets.change_assetcategory'):
            actions += f'''
                <a href="{reverse("assets:category_update", args=[category.pk])}" 
                   class="btn btn-primary" title="تعديل">
                    <i class="fas fa-edit"></i>
                </a>
            '''

        if request.user.has_perm('assets.delete_assetcategory') and category.assets_count == 0:
            actions += f'''
                <a href="{reverse("assets:category_delete", args=[category.pk])}" 
                   class="btn btn-danger" title="حذف"
                   onclick="return confirm('هل أنت متأكد؟')">
                    <i class="fas fa-trash"></i>
                </a>
            '''

        actions += '</div>'

        data.append([
            category.code,
            f'{indent}{category.name}',
            category.parent.name if category.parent else '-',
            f'<span class="badge bg-secondary">{category.level}</span>',
            f'<span class="badge bg-primary">{category.assets_count}</span>',
            category.default_depreciation_method.name if category.default_depreciation_method else '-',
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


# =============================================================================
# Ajax Helper Functions
# =============================================================================

@login_required
@permission_required('assets.view_asset', raise_exception=True)
def asset_search_ajax(request):
    """بحث عن الأصول للـ Autocomplete"""

    term = request.GET.get('term', '').strip()

    if len(term) < 2:
        return JsonResponse([], safe=False)

    # فلاتر إضافية
    only_active = request.GET.get('only_active', '1') == '1'
    category_id = request.GET.get('category', '')

    assets = Asset.objects.filter(
        company=request.user.company
    ).filter(
        Q(asset_number__icontains=term) |
        Q(name__icontains=term) |
        Q(barcode__icontains=term)
    )

    if only_active:
        assets = assets.filter(status='active')

    if category_id:
        assets = assets.filter(category_id=category_id)

    assets = assets.select_related('category', 'branch')[:20]

    results = []
    for asset in assets:
        results.append({
            'id': asset.id,
            'text': f"{asset.asset_number} - {asset.name}",
            'asset_number': asset.asset_number,
            'name': asset.name,
            'category': asset.category.name if asset.category else '',
            'book_value': float(asset.book_value),
            'status': asset.status,
        })

    return JsonResponse(results, safe=False)


@login_required
@permission_required('assets.view_asset', raise_exception=True)
@require_http_methods(["POST"])
def asset_barcode_generate(request, pk):
    """توليد باركود للأصل"""

    asset = get_object_or_404(
        Asset,
        pk=pk,
        company=request.user.company
    )

    # توليد Barcode
    from barcode import Code128
    from barcode.writer import ImageWriter

    buffer = BytesIO()
    Code128(asset.barcode or asset.asset_number, writer=ImageWriter()).write(buffer)

    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="barcode_{asset.asset_number}.png"'

    return response


@login_required
@permission_required('assets.view_asset', raise_exception=True)
@require_http_methods(["GET"])
def asset_qr_print(request, pk):
    """طباعة QR Code للأصل"""

    asset = get_object_or_404(
        Asset,
        pk=pk,
        company=request.user.company
    )

    # توليد QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr_data = f"ASSET:{asset.asset_number}|{asset.name}|{asset.company.name}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{asset.asset_number}.png"'

    return response
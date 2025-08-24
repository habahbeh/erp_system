# apps/base_data/views/warehouse_views.py
"""
Views للمستودعات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse
from django_datatables_view.base_datatable_view import BaseDatatableView

from ..models import Warehouse
from ..forms import WarehouseForm


class WarehouseMixin(LoginRequiredMixin):
    """Mixin مشترك للمستودعات"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'breadcrumbs': self.get_breadcrumbs(),
            'page_title': self.get_page_title(),
            'can_add': self.request.user.has_perm('base_data.add_warehouse'),
            'can_change': self.request.user.has_perm('base_data.change_warehouse'),
            'can_delete': self.request.user.has_perm('base_data.delete_warehouse'),
        })
        return context

    def get_breadcrumbs(self):
        return [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('البيانات الأساسية'), 'url': '#'},
        ]

    def get_page_title(self):
        return _('المستودعات')


class WarehouseListView(WarehouseMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة المستودعات"""
    model = Warehouse
    template_name = 'base_data/warehouses/warehouse_list.html'
    permission_required = 'base_data.view_warehouse'
    context_object_name = 'warehouses'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({'title': _('المستودعات'), 'url': None})
        return breadcrumbs

    def get_queryset(self):
        return Warehouse.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('company', 'branch', 'keeper')


class WarehouseCreateView(WarehouseMixin, PermissionRequiredMixin, CreateView):
    """إضافة مستودع جديد"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouses/warehouse_form.html'
    permission_required = 'base_data.add_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
            {'title': _('إضافة جديد'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('إضافة مستودع جديد')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        if not form.instance.branch:
            form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة المستودع بنجاح'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class WarehouseUpdateView(WarehouseMixin, PermissionRequiredMixin, UpdateView):
    """تعديل مستودع"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouses/warehouse_form.html'
    permission_required = 'base_data.change_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
            {'title': _('تعديل'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تعديل مستودع')

    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('تم تحديث المستودع بنجاح'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class WarehouseDetailView(WarehouseMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل مستودع"""
    model = Warehouse
    template_name = 'base_data/warehouses/warehouse_detail.html'
    permission_required = 'base_data.view_warehouse'
    context_object_name = 'warehouse'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
            {'title': self.object.name, 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تفاصيل المستودع')

    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # إضافة معلومات إضافية مثل إحصائيات المستودع
        warehouse = self.object

        # TODO: إضافة إحصائيات المستودع عند إنشاء نموذج المخزون
        context.update({
            'total_items': 0,  # سيتم تحديثه لاحقاً
            'total_value': 0,  # سيتم تحديثه لاحقاً
            'low_stock_items': 0,  # سيتم تحديثه لاحقاً
        })
        return context


class WarehouseDeleteView(WarehouseMixin, PermissionRequiredMixin, DeleteView):
    """حذف مستودع"""
    model = Warehouse
    template_name = 'base_data/warehouses/warehouse_confirm_delete.html'
    permission_required = 'base_data.delete_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
            {'title': _('حذف'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('حذف مستودع')

    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.user.company)

    def delete(self, request, *args, **kwargs):
        # التحقق من عدم وجود حركات مخزنية مرتبطة بالمستودع
        warehouse = self.get_object()

        # TODO: إضافة التحقق من الحركات المخزنية عند إنشاء نموذج المخزون
        # if warehouse.stock_movements.exists():
        #     messages.error(request, _('لا يمكن حذف المستودع لوجود حركات مخزنية مرتبطة به'))
        #     return redirect('base_data:warehouse_list')

        messages.success(request, _('تم حذف المستودع بنجاح'))
        return super().delete(request, *args, **kwargs)


# ========== DataTables Ajax Views ==========

class WarehouseDataTableView(LoginRequiredMixin, PermissionRequiredMixin, BaseDatatableView):
    """DataTables Ajax للمستودعات"""
    model = Warehouse
    permission_required = 'base_data.view_warehouse'
    columns = ['code', 'name', 'branch', 'warehouse_type', 'keeper', 'location', 'is_active']
    order_columns = ['code', 'name', 'branch__name', 'warehouse_type', 'keeper__username', 'location', 'is_active']
    max_display_length = 100

    def get_initial_queryset(self):
        return Warehouse.objects.filter(
            company=self.request.user.company
        ).select_related('company', 'branch', 'keeper')

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(branch__name__icontains=search) |
                Q(keeper__username__icontains=search)
            )

        # فلترة حسب الفرع إذا كان المستخدم مقيد بفرع معين
        if self.request.user.branch and not self.request.user.is_superuser:
            qs = qs.filter(branch=self.request.user.branch)

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            json_data.append([
                item.code,
                item.name,
                item.branch.name if item.branch else '',
                item.get_warehouse_type_display(),
                item.keeper.get_full_name() if item.keeper else '',
                item.location or '',
                '<span class="badge bg-success">نشط</span>' if item.is_active else '<span class="badge bg-danger">غير نشط</span>',
                self._get_actions_html(item)
            ])
        return json_data

    def _get_actions_html(self, item):
        """إنشاء HTML للإجراءات"""
        actions = []

        if self.request.user.has_perm('base_data.view_warehouse'):
            actions.append(
                f'<a href="{reverse("base_data:warehouse_detail", kwargs={"pk": item.pk})}" class="btn btn-sm btn-info" title="عرض"><i class="fas fa-eye"></i></a>')

        if self.request.user.has_perm('base_data.change_warehouse'):
            actions.append(
                f'<a href="{reverse("base_data:warehouse_update", kwargs={"pk": item.pk})}" class="btn btn-sm btn-warning" title="تعديل"><i class="fas fa-edit"></i></a>')

        if self.request.user.has_perm('base_data.delete_warehouse'):
            actions.append(
                f'<a href="{reverse("base_data:warehouse_delete", kwargs={"pk": item.pk})}" class="btn btn-sm btn-danger" title="حذف"><i class="fas fa-trash"></i></a>')

        return ' '.join(actions)


# ========== Ajax Helper Views ==========

class WarehouseAjaxView(LoginRequiredMixin, PermissionRequiredMixin):
    """Views مساعدة للـ Ajax"""
    permission_required = 'base_data.view_warehouse'

    def get_warehouses_by_branch(self, request):
        """الحصول على المستودعات حسب الفرع"""
        branch_id = request.GET.get('branch_id')
        warehouses = Warehouse.objects.filter(
            company=request.user.company,
            branch_id=branch_id,
            is_active=True
        ).values('id', 'name', 'code')

        return JsonResponse({'warehouses': list(warehouses)})

    def get_warehouse_info(self, request):
        """الحصول على معلومات مستودع معين"""
        warehouse_id = request.GET.get('warehouse_id')
        try:
            warehouse = Warehouse.objects.get(
                id=warehouse_id,
                company=request.user.company
            )
            data = {
                'id': warehouse.id,
                'code': warehouse.code,
                'name': warehouse.name,
                'location': warehouse.location,
                'warehouse_type': warehouse.warehouse_type,
                'keeper': warehouse.keeper.get_full_name() if warehouse.keeper else '',
                'branch': warehouse.branch.name if warehouse.branch else '',
            }
            return JsonResponse({'success': True, 'warehouse': data})
        except Warehouse.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'المستودع غير موجود'})


def get_warehouses_by_branch_ajax(request):
    """دالة مساعدة للحصول على المستودعات حسب الفرع"""
    if not request.user.has_perm('base_data.view_warehouse'):
        return JsonResponse({'error': 'ليس لديك صلاحية'}, status=403)

    branch_id = request.GET.get('branch_id')
    if not branch_id:
        return JsonResponse({'warehouses': []})

    warehouses = Warehouse.objects.filter(
        company=request.user.company,
        branch_id=branch_id,
        is_active=True
    ).values('id', 'name', 'code').order_by('name')

    return JsonResponse({'warehouses': list(warehouses)})


def get_warehouse_info_ajax(request):
    """دالة مساعدة للحصول على معلومات مستودع"""
    if not request.user.has_perm('base_data.view_warehouse'):
        return JsonResponse({'error': 'ليس لديك صلاحية'}, status=403)

    warehouse_id = request.GET.get('warehouse_id')
    if not warehouse_id:
        return JsonResponse({'error': 'معرف المستودع مطلوب'})

    try:
        warehouse = Warehouse.objects.select_related('branch', 'keeper').get(
            id=warehouse_id,
            company=request.user.company
        )

        data = {
            'id': warehouse.id,
            'code': warehouse.code,
            'name': warehouse.name,
            'location': warehouse.location or '',
            'warehouse_type': warehouse.warehouse_type,
            'warehouse_type_display': warehouse.get_warehouse_type_display(),
            'keeper_name': warehouse.keeper.get_full_name() if warehouse.keeper else '',
            'branch_name': warehouse.branch.name if warehouse.branch else '',
        }
        return JsonResponse({'success': True, 'warehouse': data})

    except Warehouse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المستودع غير موجود'})
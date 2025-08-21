# apps/base_data/views/warehouse_views.py
"""
Views الخاصة بالمستودعات
"""

from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import Warehouse
from ..forms import WarehouseForm


class WarehouseListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة المستودعات"""
    model = Warehouse
    template_name = 'base_data/warehouse/list.html'
    context_object_name = 'warehouses'
    permission_required = 'base_data.view_warehouse'
    paginate_by = 20

    def get_queryset(self):
        """فلترة والبحث"""
        queryset = super().get_queryset()

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search)
            )

        # فلترة حسب الفرع
        branch_id = self.request.GET.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # فلترة حسب الحالة
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')

        return queryset.select_related('branch', 'keeper')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('المستودعات')
        context['can_add'] = self.request.user.has_perm('base_data.add_warehouse')

        # قائمة الفروع للفلترة
        context['branches'] = self.request.user.get_allowed_branches()

        return context


class WarehouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة مستودع جديد"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouse/form.html'
    permission_required = 'base_data.add_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_form_kwargs(self):
        """إضافة الشركة والفرع للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['branch'] = self.request.current_branch
        return kwargs

    def form_valid(self, form):
        """إضافة البيانات التلقائية"""
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('تم إضافة المستودع %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة مستودع جديد')
        context['submit_text'] = _('حفظ')
        return context


class WarehouseDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل المستودع"""
    model = Warehouse
    template_name = 'base_data/warehouse/detail.html'
    context_object_name = 'warehouse'
    permission_required = 'base_data.view_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name

        # صلاحيات الأزرار
        context['can_edit'] = self.request.user.has_perm('base_data.change_warehouse')
        context['can_delete'] = self.request.user.has_perm('base_data.delete_warehouse')

        # إحصائيات المستودع (سيتم تطويرها لاحقاً)
        context['total_items'] = 0
        context['total_value'] = 0
        context['movements_count'] = 0

        return context


class WarehouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل المستودع"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouse/form.html'
    permission_required = 'base_data.change_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_form_kwargs(self):
        """إضافة الشركة والفرع للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['branch'] = self.object.branch
        return kwargs

    def form_valid(self, form):
        """تحديث المستخدم الذي عدّل"""
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            _('تم تعديل المستودع %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل المستودع: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class WarehouseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف المستودع"""
    model = Warehouse
    template_name = 'base_data/warehouse/confirm_delete.html'
    permission_required = 'base_data.delete_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def delete(self, request, *args, **kwargs):
        """رسالة نجاح عند الحذف"""
        warehouse = self.get_object()
        messages.success(
            self.request,
            _('تم حذف المستودع %(name)s بنجاح') % {'name': warehouse.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف المستودع')
        context['message'] = _('هل أنت متأكد من حذف المستودع %(name)s؟') % {'name': self.object.name}
        return context
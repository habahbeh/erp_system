# apps/core/views/warehouse_views.py
"""
Views للمستودعات
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django_filters.views import FilterView
from django.shortcuts import redirect

from ..models import Warehouse
from ..forms.warehouse_forms import WarehouseForm
from ..mixins import CompanyMixin, AuditLogMixin
from ..filters import WarehouseFilter


class WarehouseListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة المستودعات مع DataTable"""
    template_name = 'core/warehouses/warehouse_list.html'
    permission_required = 'core.view_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة المستودعات'),
            'can_add': self.request.user.has_perm('core.add_warehouse'),
            'add_url': reverse('core:warehouse_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستودعات'), 'url': ''}
            ],
        })
        return context


class WarehouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة مستودع جديد"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'core/warehouses/warehouse_form.html'
    permission_required = 'core.add_warehouse'
    success_url = reverse_lazy('core:warehouse_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة مستودع جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستودعات'), 'url': reverse('core:warehouse_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ المستودع'),
            'cancel_url': reverse('core:warehouse_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة المستودع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class WarehouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل مستودع"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'core/warehouses/warehouse_form.html'
    permission_required = 'core.change_warehouse'
    success_url = reverse_lazy('core:warehouse_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل المستودع: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستودعات'), 'url': reverse('core:warehouse_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:warehouse_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث المستودع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class WarehouseDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل المستودع"""
    model = Warehouse
    template_name = 'core/warehouses/warehouse_detail.html'
    context_object_name = 'warehouse'
    permission_required = 'core.view_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تفاصيل المستودع: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_warehouse'),
            'can_delete': self.request.user.has_perm('core.delete_warehouse'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستودعات'), 'url': reverse('core:warehouse_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:warehouse_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:warehouse_delete', kwargs={'pk': self.object.pk}),
        })
        return context


class WarehouseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف مستودع"""
    model = Warehouse
    template_name = 'core/warehouses/warehouse_confirm_delete.html'
    permission_required = 'core.delete_warehouse'
    success_url = reverse_lazy('core:warehouse_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف المستودع: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستودعات'), 'url': reverse('core:warehouse_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:warehouse_list'),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        warehouse_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف المستودع "%(name)s" بنجاح') % {'name': warehouse_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا المستودع لوجود بيانات مرتبطة به')
            )
            return redirect('core:warehouse_list')
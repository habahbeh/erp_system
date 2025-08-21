# apps/base_data/views/unit_views.py
"""
Views الخاصة بوحدات القياس
"""

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import UnitOfMeasure
from ..forms import UnitOfMeasureForm


class UnitListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة وحدات القياس"""
    model = UnitOfMeasure
    template_name = 'base_data/unit/list.html'
    context_object_name = 'units'
    permission_required = 'base_data.view_unitofmeasure'
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
                Q(name_en__icontains=search)
            )

        # فلترة حسب الحالة
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('وحدات القياس')
        context['can_add'] = self.request.user.has_perm('base_data.add_unitofmeasure')
        return context


class UnitCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة وحدة قياس جديدة"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'base_data/unit/form.html'
    permission_required = 'base_data.add_unitofmeasure'
    success_url = reverse_lazy('base_data:unit_list')

    def form_valid(self, form):
        """إضافة البيانات التلقائية"""
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('تم إضافة وحدة القياس %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة وحدة قياس جديدة')
        context['submit_text'] = _('حفظ')
        return context


class UnitUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل وحدة القياس"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'base_data/unit/form.html'
    permission_required = 'base_data.change_unitofmeasure'
    success_url = reverse_lazy('base_data:unit_list')

    def form_valid(self, form):
        """تحديث المستخدم الذي عدّل"""
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            _('تم تعديل وحدة القياس %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل وحدة القياس: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class UnitDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف وحدة القياس"""
    model = UnitOfMeasure
    template_name = 'base_data/unit/confirm_delete.html'
    permission_required = 'base_data.delete_unitofmeasure'
    success_url = reverse_lazy('base_data:unit_list')

    def delete(self, request, *args, **kwargs):
        """رسالة نجاح عند الحذف"""
        unit = self.get_object()

        # التحقق من عدم استخدام الوحدة في أصناف
        if unit.item_set.exists():
            messages.error(
                self.request,
                _('لا يمكن حذف وحدة القياس %(name)s لأنها مستخدمة في أصناف') % {'name': unit.name}
            )
            return self.get(request, *args, **kwargs)

        messages.success(
            self.request,
            _('تم حذف وحدة القياس %(name)s بنجاح') % {'name': unit.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف وحدة القياس')
        context['message'] = _('هل أنت متأكد من حذف وحدة القياس %(name)s؟') % {'name': self.object.name}
        return context
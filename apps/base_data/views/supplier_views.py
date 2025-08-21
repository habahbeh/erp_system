# apps/base_data/views/supplier_views.py
"""
Views الخاصة بالموردين
"""

from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import Supplier
from ..forms import SupplierForm


class SupplierListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة الموردين"""
    model = Supplier
    template_name = 'base_data/supplier/list.html'
    context_object_name = 'suppliers'
    permission_required = 'base_data.view_supplier'
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
                Q(phone__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search)
            )

        # فلترة حسب النوع
        account_type = self.request.GET.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)

        # فلترة حسب الحالة
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الموردين')
        context['can_add'] = self.request.user.has_perm('base_data.add_supplier')
        return context


class SupplierCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة مورد جديد"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'base_data/supplier/form.html'
    permission_required = 'base_data.add_supplier'
    success_url = reverse_lazy('base_data:supplier_list')

    def get_form_kwargs(self):
        """إضافة الشركة للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        """إضافة البيانات التلقائية"""
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('تم إضافة المورد %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة مورد جديد')
        context['submit_text'] = _('حفظ')
        return context


class SupplierDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل المورد"""
    model = Supplier
    template_name = 'base_data/supplier/detail.html'
    context_object_name = 'supplier'
    permission_required = 'base_data.view_supplier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name

        # صلاحيات الأزرار
        context['can_edit'] = self.request.user.has_perm('base_data.change_supplier')
        context['can_delete'] = self.request.user.has_perm('base_data.delete_supplier')

        # إحصائيات المورد (سيتم تطويرها لاحقاً)
        context['total_purchases'] = 0
        context['total_amount'] = 0
        context['balance'] = 0

        return context


class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل المورد"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'base_data/supplier/form.html'
    permission_required = 'base_data.change_supplier'
    success_url = reverse_lazy('base_data:supplier_list')

    def get_form_kwargs(self):
        """إضافة الشركة للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        """تحديث المستخدم الذي عدّل"""
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            _('تم تعديل المورد %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل المورد: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف المورد"""
    model = Supplier
    template_name = 'base_data/supplier/confirm_delete.html'
    permission_required = 'base_data.delete_supplier'
    success_url = reverse_lazy('base_data:supplier_list')

    def delete(self, request, *args, **kwargs):
        """رسالة نجاح عند الحذف"""
        supplier = self.get_object()
        messages.success(
            self.request,
            _('تم حذف المورد %(name)s بنجاح') % {'name': supplier.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف المورد')
        context['message'] = _('هل أنت متأكد من حذف المورد %(name)s؟') % {'name': self.object.name}
        return context
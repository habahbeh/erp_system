# apps/base_data/views/customer_views.py
"""
Views الخاصة بالعملاء
"""

from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import Customer
from ..forms import CustomerForm


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة العملاء"""
    model = Customer
    template_name = 'base_data/customer/list.html'
    context_object_name = 'customers'
    permission_required = 'base_data.view_customer'
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

        return queryset.select_related('salesperson')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('العملاء')
        context['can_add'] = self.request.user.has_perm('base_data.add_customer')
        return context


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة عميل جديد"""
    model = Customer
    form_class = CustomerForm
    template_name = 'base_data/customer/form.html'
    permission_required = 'base_data.add_customer'
    success_url = reverse_lazy('base_data:customer_list')

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
            _('تم إضافة العميل %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة عميل جديد')
        context['submit_text'] = _('حفظ')
        return context


class CustomerDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل العميل"""
    model = Customer
    template_name = 'base_data/customer/detail.html'
    context_object_name = 'customer'
    permission_required = 'base_data.view_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name

        # صلاحيات الأزرار
        context['can_edit'] = self.request.user.has_perm('base_data.change_customer')
        context['can_delete'] = self.request.user.has_perm('base_data.delete_customer')

        # إحصائيات العميل (سيتم تطويرها لاحقاً)
        context['total_invoices'] = 0
        context['total_amount'] = 0
        context['balance'] = 0

        return context


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل العميل"""
    model = Customer
    form_class = CustomerForm
    template_name = 'base_data/customer/form.html'
    permission_required = 'base_data.change_customer'
    success_url = reverse_lazy('base_data:customer_list')

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
            _('تم تعديل العميل %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل العميل: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف العميل"""
    model = Customer
    template_name = 'base_data/customer/confirm_delete.html'
    permission_required = 'base_data.delete_customer'
    success_url = reverse_lazy('base_data:customer_list')

    def delete(self, request, *args, **kwargs):
        """رسالة نجاح عند الحذف"""
        customer = self.get_object()
        messages.success(
            self.request,
            _('تم حذف العميل %(name)s بنجاح') % {'name': customer.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف العميل')
        context['message'] = _('هل أنت متأكد من حذف العميل %(name)s؟') % {'name': self.object.name}
        return context
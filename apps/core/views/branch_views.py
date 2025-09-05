# apps/core/views/branch_views.py
"""
Views للفروع
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect

from ..models import Branch, User, Warehouse
from ..forms.branch_forms import BranchForm
from ..mixins import CompanyMixin, AuditLogMixin


class BranchListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الفروع مع DataTable"""
    template_name = 'core/branches/branch_list.html'
    permission_required = 'core.view_branch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة الفروع'),
            'can_add': self.request.user.has_perm('core.add_branch'),
            'add_url': reverse('core:branch_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الفروع'), 'url': ''}
            ],
        })
        return context


class BranchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة فرع جديد"""
    model = Branch
    form_class = BranchForm
    template_name = 'core/branches/branch_form.html'
    permission_required = 'core.add_branch'
    success_url = reverse_lazy('core:branch_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة فرع جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الفروع'), 'url': reverse('core:branch_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الفرع'),
            'cancel_url': reverse('core:branch_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة الفرع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BranchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل فرع"""
    model = Branch
    form_class = BranchForm
    template_name = 'core/branches/branch_form.html'
    permission_required = 'core.change_branch'
    success_url = reverse_lazy('core:branch_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل الفرع: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الفروع'), 'url': reverse('core:branch_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:branch_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث الفرع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BranchDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل الفرع"""
    model = Branch
    template_name = 'core/branches/branch_detail.html'
    context_object_name = 'branch'
    permission_required = 'core.view_branch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الفرع
        users_count = User.objects.filter(branch=self.object, is_active=True).count()
        warehouses_count = Warehouse.objects.filter(company=self.object.company).count()

        context.update({
            'title': _('تفاصيل الفرع: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_branch'),
            'can_delete': self.request.user.has_perm('core.delete_branch'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الفروع'), 'url': reverse('core:branch_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:branch_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:branch_delete', kwargs={'pk': self.object.pk}),
            'users_count': users_count,
            'warehouses_count': warehouses_count,
        })
        return context


class BranchDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف فرع"""
    model = Branch
    template_name = 'core/branches/branch_confirm_delete.html'
    permission_required = 'core.delete_branch'
    success_url = reverse_lazy('core:branch_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد المستخدمين المرتبطين
        users_count = User.objects.filter(branch=self.object).count()

        context.update({
            'title': _('حذف الفرع: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الفروع'), 'url': reverse('core:branch_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:branch_list'),
            'users_count': users_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        branch_name = self.object.name

        # التحقق من أن الفرع ليس الرئيسي
        if self.object.is_main:
            messages.error(
                request,
                _('لا يمكن حذف الفرع الرئيسي')
            )
            return redirect('core:branch_list')

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف الفرع "%(name)s" بنجاح') % {'name': branch_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا الفرع لوجود بيانات مرتبطة به')
            )
            return redirect('core:branch_list')
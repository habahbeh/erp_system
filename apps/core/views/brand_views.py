# apps/core/views/brand_views.py
"""
Views للعلامات التجارية
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django_filters.views import FilterView
from django.shortcuts import redirect

from ..models import Brand
from ..forms.brand_forms import BrandForm
from ..mixins import CompanyMixin, AuditLogMixin
from ..filters import BrandFilter


class BrandListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة العلامات التجارية مع DataTable"""
    template_name = 'core/brands/brand_list.html'
    permission_required = 'core.view_brand'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة العلامات التجارية'),
            'can_add': self.request.user.has_perm('core.add_brand'),
            'add_url': reverse('core:brand_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العلامات التجارية'), 'url': ''}
            ],
        })
        return context


class BrandCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة علامة تجارية جديدة"""
    model = Brand
    form_class = BrandForm
    template_name = 'core/brands/brand_form.html'
    permission_required = 'core.add_brand'
    success_url = reverse_lazy('core:brand_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة علامة تجارية جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العلامات التجارية'), 'url': reverse('core:brand_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ العلامة التجارية'),
            'cancel_url': reverse('core:brand_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة العلامة التجارية "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BrandUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل علامة تجارية"""
    model = Brand
    form_class = BrandForm
    template_name = 'core/brands/brand_form.html'
    permission_required = 'core.change_brand'
    success_url = reverse_lazy('core:brand_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل العلامة التجارية: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العلامات التجارية'), 'url': reverse('core:brand_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:brand_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث العلامة التجارية "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BrandDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل العلامة التجارية"""
    model = Brand
    template_name = 'core/brands/brand_detail.html'
    context_object_name = 'brand'
    permission_required = 'core.view_brand'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات العلامة التجارية
        items_count = self.object.items.filter(company=self.request.current_company).count()

        context.update({
            'title': _('تفاصيل العلامة التجارية: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_brand'),
            'can_delete': self.request.user.has_perm('core.delete_brand'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العلامات التجارية'), 'url': reverse('core:brand_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:brand_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:brand_delete', kwargs={'pk': self.object.pk}),
            'items_count': items_count,
        })
        return context


class BrandDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف علامة تجارية"""
    model = Brand
    template_name = 'core/brands/brand_confirm_delete.html'
    permission_required = 'core.delete_brand'
    success_url = reverse_lazy('core:brand_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد الأصناف المرتبطة
        items_count = self.object.items.filter(company=self.request.current_company).count()

        context.update({
            'title': _('حذف العلامة التجارية: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العلامات التجارية'), 'url': reverse('core:brand_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:brand_list'),
            'items_count': items_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        brand_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف العلامة التجارية "%(name)s" بنجاح') % {'name': brand_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه العلامة التجارية لوجود أصناف مرتبطة بها')
            )
            return redirect('core:brand_list')
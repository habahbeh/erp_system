# apps/core/views/unit_views.py
"""
Views لوحدات القياس
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect

from ..models import UnitOfMeasure
from ..forms.unit_forms import UnitOfMeasureForm
from ..mixins import CompanyMixin, AuditLogMixin


class UnitOfMeasureListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة وحدات القياس مع DataTable"""
    template_name = 'core/units/unit_list.html'
    permission_required = 'core.view_unitofmeasure'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة وحدات القياس'),
            'can_add': self.request.user.has_perm('core.add_unitofmeasure'),
            'add_url': reverse('core:unit_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('وحدات القياس'), 'url': ''}
            ],
        })
        return context


class UnitOfMeasureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة وحدة قياس جديدة"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'core/units/unit_form.html'
    permission_required = 'core.add_unitofmeasure'
    success_url = reverse_lazy('core:unit_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة وحدة قياس جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('core:unit_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ وحدة القياس'),
            'cancel_url': reverse('core:unit_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة وحدة القياس "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class UnitOfMeasureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل وحدة قياس"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'core/units/unit_form.html'
    permission_required = 'core.change_unitofmeasure'
    success_url = reverse_lazy('core:unit_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل وحدة القياس: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('core:unit_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:unit_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث وحدة القياس "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class UnitOfMeasureDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل وحدة القياس"""
    model = UnitOfMeasure
    template_name = 'core/units/unit_detail.html'
    context_object_name = 'unit'
    permission_required = 'core.view_unitofmeasure'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات وحدة القياس
        items_count = self.object.items.filter(company=self.request.current_company).count()

        context.update({
            'title': _('تفاصيل وحدة القياس: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_unitofmeasure'),
            'can_delete': self.request.user.has_perm('core.delete_unitofmeasure'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('core:unit_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:unit_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:unit_delete', kwargs={'pk': self.object.pk}),
            'items_count': items_count,
        })
        return context


class UnitOfMeasureDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف وحدة قياس"""
    model = UnitOfMeasure
    template_name = 'core/units/unit_confirm_delete.html'
    permission_required = 'core.delete_unitofmeasure'
    success_url = reverse_lazy('core:unit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد الأصناف المرتبطة
        items_count = self.object.items.filter(company=self.request.current_company).count()

        context.update({
            'title': _('حذف وحدة القياس: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('core:unit_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:unit_list'),
            'items_count': items_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        unit_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف وحدة القياس "%(name)s" بنجاح') % {'name': unit_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه الوحدة لوجود أصناف مرتبطة بها')
            )
            return redirect('core:unit_list')
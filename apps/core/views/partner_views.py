# apps/core/views/partner_views.py
"""
Views للشركاء التجاريين (العملاء والموردين)
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django_filters.views import FilterView
from django.shortcuts import redirect

from ..models import BusinessPartner
from ..forms.partner_forms import BusinessPartnerForm
from ..mixins import CompanyBranchMixin, AuditLogMixin
from ..filters import BusinessPartnerFilter


class BusinessPartnerListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, TemplateView):
    """قائمة الشركاء التجاريين مع DataTable"""
    template_name = 'core/partners/partner_list.html'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة الشركاء التجاريين'),
            'can_add': self.request.user.has_perm('core.add_businesspartner'),
            'add_url': reverse('core:partner_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': ''}
            ],
        })
        return context


class BusinessPartnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin, CreateView):
    """إضافة شريك تجاري جديد"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'core/partners/partner_form.html'
    permission_required = 'core.add_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة شريك تجاري جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('core:partner_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الشريك'),
            'cancel_url': reverse('core:partner_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة الشريك التجاري "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin, UpdateView):
    """تعديل شريك تجاري"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'core/partners/partner_form.html'
    permission_required = 'core.change_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل الشريك: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('core:partner_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:partner_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث الشريك التجاري "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل الشريك التجاري"""
    model = BusinessPartner
    template_name = 'core/partners/partner_detail.html'
    context_object_name = 'partner'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تفاصيل الشريك: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_businesspartner'),
            'can_delete': self.request.user.has_perm('core.delete_businesspartner'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('core:partner_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:partner_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:partner_delete', kwargs={'pk': self.object.pk}),
        })
        return context


class BusinessPartnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin, DeleteView):
    """حذف شريك تجاري"""
    model = BusinessPartner
    template_name = 'core/partners/partner_confirm_delete.html'
    permission_required = 'core.delete_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف الشريك: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('core:partner_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:partner_list'),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        partner_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف الشريك التجاري "%(name)s" بنجاح') % {'name': partner_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا الشريك لوجود بيانات مرتبطة به')
            )
            return redirect('core:partner_list')
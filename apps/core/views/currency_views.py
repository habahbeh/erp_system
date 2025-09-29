# apps/core/views/currency_views.py
"""
Views للعملات
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect

from ..models import Currency
from ..forms.currency_forms import CurrencyForm
from ..mixins import AuditLogMixin
from django.http import JsonResponse


class CurrencyListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة العملات مع DataTable"""
    template_name = 'core/currencies/currency_list.html'
    permission_required = 'core.view_currency'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة العملات'),
            'can_add': self.request.user.has_perm('core.add_currency'),
            'add_url': reverse('core:currency_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملات'), 'url': ''}
            ],
        })
        return context


class CurrencyCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة عملة جديدة"""
    model = Currency
    form_class = CurrencyForm
    template_name = 'core/currencies/currency_form.html'
    permission_required = 'core.add_currency'
    success_url = reverse_lazy('core:currency_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة عملة جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملات'), 'url': reverse('core:currency_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ العملة'),
            'cancel_url': reverse('core:currency_list'),
        })
        return context

    def get_template_names(self):
        if self.request.GET.get('modal') or self.request.headers.get('X-Requested-With'):
            return ['core/currencies/currency_form_modal.html']
        return ['core/currencies/currency_form.html']

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.request.headers.get('X-Requested-With'):
            return JsonResponse({
                'success': True,
                'currency_id': self.object.id,
                'currency_name': self.object.name
            })

        messages.success(
            self.request,
            _('تم إضافة العملة "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With'):
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else ''

            return JsonResponse({
                'success': False,
                'error': 'يرجى تصحيح الأخطاء',
                'errors': errors
            })

        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class CurrencyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل عملة"""
    model = Currency
    form_class = CurrencyForm
    template_name = 'core/currencies/currency_form.html'
    permission_required = 'core.change_currency'
    success_url = reverse_lazy('core:currency_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل العملة: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملات'), 'url': reverse('core:currency_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:currency_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث العملة "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class CurrencyDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل العملة"""
    model = Currency
    template_name = 'core/currencies/currency_detail.html'
    context_object_name = 'currency'
    permission_required = 'core.view_currency'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات العملة
        items_count = self.object.items.count() if hasattr(self.object, 'items') else 0
        companies_count = self.object.companies.count() if hasattr(self.object, 'companies') else 0

        context.update({
            'title': _('تفاصيل العملة: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_currency'),
            'can_delete': self.request.user.has_perm('core.delete_currency'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملات'), 'url': reverse('core:currency_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:currency_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:currency_delete', kwargs={'pk': self.object.pk}),
            'items_count': items_count,
            'companies_count': companies_count,
        })
        return context


class CurrencyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف عملة"""
    model = Currency
    template_name = 'core/currencies/currency_confirm_delete.html'
    permission_required = 'core.delete_currency'
    success_url = reverse_lazy('core:currency_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد البيانات المرتبطة
        items_count = self.object.items.count() if hasattr(self.object, 'items') else 0
        companies_count = self.object.companies.count() if hasattr(self.object, 'companies') else 0

        context.update({
            'title': _('حذف العملة: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملات'), 'url': reverse('core:currency_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:currency_list'),
            'items_count': items_count,
            'companies_count': companies_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        currency_name = self.object.name

        # منع حذف العملة الأساسية
        if self.object.is_base:
            messages.error(
                request,
                _('لا يمكن حذف العملة الأساسية')
            )
            return redirect('core:currency_list')

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف العملة "%(name)s" بنجاح') % {'name': currency_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه العملة لوجود بيانات مرتبطة بها')
            )
            return redirect('core:currency_list')
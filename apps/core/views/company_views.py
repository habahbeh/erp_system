# apps/core/views/company_views.py
"""
Views للشركة
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView
from django.shortcuts import get_object_or_404

from ..models import Company
from ..forms.company_forms import CompanyForm
from ..mixins import AuditLogMixin


class CompanyDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل الشركة"""
    model = Company
    template_name = 'core/company/company_detail.html'
    context_object_name = 'company'
    permission_required = 'core.view_company'

    def get_object(self):
        """الحصول على الشركة الحالية للمستخدم"""
        if hasattr(self.request, 'current_company') and self.request.current_company:
            return self.request.current_company
        elif hasattr(self.request.user, 'company') and self.request.user.company:
            return self.request.user.company
        else:
            # استخدام أول شركة متاحة
            return get_object_or_404(Company, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الشركة
        company = self.object
        stats = {
            'branches_count': company.branches.filter(is_active=True).count(),
            'users_count': company.user_set.filter(is_active=True).count(),
            'warehouses_count': company.warehouse_set.filter(is_active=True).count(),
            'items_count': company.item_set.filter(is_active=True).count(),
            'partners_count': company.businesspartner_set.filter(is_active=True).count(),
        }

        context.update({
            'title': _('بيانات الشركة: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_company'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('بيانات الشركة'), 'url': ''}
            ],
            'edit_url': reverse('core:company_update'),
            'stats': stats,
        })
        return context


class CompanyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل بيانات الشركة"""
    model = Company
    form_class = CompanyForm
    template_name = 'core/company/company_form.html'
    permission_required = 'core.change_company'
    success_url = reverse_lazy('core:company_detail')

    def get_object(self):
        """الحصول على الشركة الحالية للمستخدم"""
        if hasattr(self.request, 'current_company') and self.request.current_company:
            return self.request.current_company
        elif hasattr(self.request.user, 'company') and self.request.user.company:
            return self.request.user.company
        else:
            # استخدام أول شركة متاحة
            return get_object_or_404(Company, is_active=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل بيانات الشركة: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('بيانات الشركة'), 'url': reverse('core:company_detail')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:company_detail'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث بيانات الشركة "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)
# في apps/core/views/partner_views.py - استبدال بالكامل

"""
Views للعملاء (العملاء والموردين) مع المرفقات والمندوبين المتعددين
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect
from django.db import transaction

from ..models import BusinessPartner, PartnerRepresentative
from ..forms.partner_forms import BusinessPartnerForm, PartnerRepresentativeFormSet
from ..mixins import CompanyBranchMixin, AuditLogMixin


class BusinessPartnerListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, TemplateView):
    """قائمة العملاء مع DataTable"""
    template_name = 'core/partners/partner_list.html'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة العملاء'),
            'can_add': self.request.user.has_perm('core.add_businesspartner'),
            'add_url': reverse('core:partner_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': ''}
            ],
        })
        return context


class BusinessPartnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                CreateView):
    """إضافة عميل جديد مع المندوبين"""
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

        if self.request.POST:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                self.request.POST
            )
        else:
            # للإنشاء الجديد - إنشاء FormSet فارغ
            context['representative_formset'] = PartnerRepresentativeFormSet(
                queryset=PartnerRepresentative.objects.none()
            )

        context.update({
            'title': _('إضافة عميل جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ العميل'),
            'cancel_url': reverse('core:partner_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        representative_formset = context['representative_formset']

        with transaction.atomic():
            # حفظ العميل أولاً
            self.object = form.save()

            # ربط FormSet بالعميل المحفوظ
            representative_formset.instance = self.object

            if representative_formset.is_valid():
                # حفظ المندوبين
                representatives = representative_formset.save(commit=False)
                for representative in representatives:
                    representative.company = self.request.current_company
                    representative.branch = self.request.current_branch
                    representative.created_by = self.request.user
                    representative.save()

                # حذف المندوبين المحذوفين
                for obj in representative_formset.deleted_objects:
                    obj.delete()

                messages.success(
                    self.request,
                    _('تم إضافة العميل "%(name)s" بنجاح مع %(count)d مندوب') % {
                        'name': self.object.name,
                        'count': len(representatives)
                    }
                )
                return super().form_valid(form)
            else:
                # إذا فشل FormSet، احذف العميل المحفوظ
                transaction.set_rollback(True)
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                UpdateView):
    """تعديل عميل مع المندوبين"""
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                instance=self.object
            )

        context.update({
            'title': _('تعديل العميل: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:partner_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        representative_formset = context['representative_formset']

        with transaction.atomic():
            # حفظ العميل
            self.object = form.save()

            if representative_formset.is_valid():
                # حفظ المندوبين
                representatives = representative_formset.save(commit=False)
                for representative in representatives:
                    if not representative.company:
                        representative.company = self.request.current_company
                    if not representative.branch:
                        representative.branch = self.request.current_branch
                    if not representative.created_by:
                        representative.created_by = self.request.user
                    representative.save()

                # حذف المندوبين المحذوفين
                for obj in representative_formset.deleted_objects:
                    obj.delete()

                messages.success(
                    self.request,
                    _('تم تحديث العميل "%(name)s" بنجاح') % {'name': self.object.name}
                )
                return super().form_valid(form)
            else:
                transaction.set_rollback(True)
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل العميل مع المندوبين والمرفقات"""
    model = BusinessPartner
    template_name = 'core/partners/partner_detail.html'
    context_object_name = 'partner'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # جلب المندوبين
        representatives = self.object.representatives.all().order_by('-is_primary', 'representative_name')

        context.update({
            'title': _('تفاصيل العميل: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_businesspartner'),
            'can_delete': self.request.user.has_perm('core.delete_businesspartner'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:partner_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:partner_delete', kwargs={'pk': self.object.pk}),
            'representatives': representatives,
            'effective_tax_status': self.object.get_effective_tax_status(),
            'is_tax_exempt_active': self.object.is_tax_exempt_active(),
        })
        return context


class BusinessPartnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                DeleteView):
    """حذف عميل"""
    model = BusinessPartner
    template_name = 'core/partners/partner_confirm_delete.html'
    permission_required = 'core.delete_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عد المندوبين المرتبطين
        representatives_count = self.object.representatives.count()

        context.update({
            'title': _('حذف العميل: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:partner_list'),
            'representatives_count': representatives_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        partner_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف العميل "%(name)s" بنجاح') % {'name': partner_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا العميل لوجود بيانات مرتبطة به')
            )
            return redirect('core:partner_list')
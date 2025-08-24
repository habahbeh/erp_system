# apps/base_data/views/partner_views.py
"""
Views للشركاء التجاريين (العملاء والموردين)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse
from django_datatables_view.base_datatable_view import BaseDatatableView

from ..models import BusinessPartner, Customer, Supplier
from ..forms import BusinessPartnerForm, CustomerForm, SupplierForm


class PartnerMixin(LoginRequiredMixin):
    """Mixin مشترك للشركاء التجاريين"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'breadcrumbs': self.get_breadcrumbs(),
            'page_title': self.get_page_title(),
            'can_add': self.request.user.has_perm('base_data.add_businesspartner'),
            'can_change': self.request.user.has_perm('base_data.change_businesspartner'),
            'can_delete': self.request.user.has_perm('base_data.delete_businesspartner'),
        })
        return context

    def get_breadcrumbs(self):
        return [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('البيانات الأساسية'), 'url': '#'},
        ]

    def get_page_title(self):
        return _('الشركاء التجاريون')


class BusinessPartnerListView(PartnerMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة الشركاء التجاريين"""
    model = BusinessPartner
    template_name = 'base_data/partners/partner_list.html'
    permission_required = 'base_data.view_businesspartner'
    context_object_name = 'partners'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({'title': _('الشركاء التجاريون'), 'url': None})
        return breadcrumbs

    def get_queryset(self):
        return BusinessPartner.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('company', 'branch')


class BusinessPartnerCreateView(PartnerMixin, PermissionRequiredMixin, CreateView):
    """إضافة شريك تجاري جديد"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'base_data/partners/partner_form.html'
    permission_required = 'base_data.add_businesspartner'
    success_url = reverse_lazy('base_data:partner_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
            {'title': _('إضافة جديد'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('إضافة شريك تجاري جديد')

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة الشريك التجاري بنجاح'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerUpdateView(PartnerMixin, PermissionRequiredMixin, UpdateView):
    """تعديل شريك تجاري"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'base_data/partners/partner_form.html'
    permission_required = 'base_data.change_businesspartner'
    success_url = reverse_lazy('base_data:partner_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
            {'title': _('تعديل'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تعديل شريك تجاري')

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('تم تحديث الشريك التجاري بنجاح'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerDetailView(PartnerMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل شريك تجاري"""
    model = BusinessPartner
    template_name = 'base_data/partners/partner_detail.html'
    permission_required = 'base_data.view_businesspartner'
    context_object_name = 'partner'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
            {'title': self.object.name, 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تفاصيل الشريك التجاري')

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)


class BusinessPartnerDeleteView(PartnerMixin, PermissionRequiredMixin, DeleteView):
    """حذف شريك تجاري"""
    model = BusinessPartner
    template_name = 'base_data/partners/partner_confirm_delete.html'
    permission_required = 'base_data.delete_businesspartner'
    success_url = reverse_lazy('base_data:partner_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
            {'title': _('حذف'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('حذف شريك تجاري')

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف الشريك التجاري بنجاح'))
        return super().delete(request, *args, **kwargs)


# ========== العملاء ==========

class CustomerListView(PartnerMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة العملاء"""
    model = Customer
    template_name = 'base_data/partners/customer_list.html'
    permission_required = 'base_data.view_businesspartner'
    context_object_name = 'customers'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({'title': _('العملاء'), 'url': None})
        return breadcrumbs

    def get_page_title(self):
        return _('العملاء')

    def get_queryset(self):
        return Customer.customers.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('company', 'branch')


class CustomerCreateView(PartnerMixin, PermissionRequiredMixin, CreateView):
    """إضافة عميل جديد"""
    model = Customer
    form_class = CustomerForm
    template_name = 'base_data/partners/customer_form.html'
    permission_required = 'base_data.add_businesspartner'
    success_url = reverse_lazy('base_data:customer_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('العملاء'), 'url': reverse('base_data:customer_list')},
            {'title': _('إضافة جديد'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('إضافة عميل جديد')

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.partner_type = 'customer'
        messages.success(self.request, _('تم إضافة العميل بنجاح'))
        return super().form_valid(form)


class CustomerUpdateView(PartnerMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عميل"""
    model = Customer
    form_class = CustomerForm
    template_name = 'base_data/partners/customer_form.html'
    permission_required = 'base_data.change_businesspartner'
    success_url = reverse_lazy('base_data:customer_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('العملاء'), 'url': reverse('base_data:customer_list')},
            {'title': _('تعديل'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تعديل عميل')

    def get_queryset(self):
        return Customer.customers.filter(company=self.request.user.company)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('تم تحديث العميل بنجاح'))
        return super().form_valid(form)


# ========== الموردين ==========

class SupplierListView(PartnerMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة الموردين"""
    model = Supplier
    template_name = 'base_data/partners/supplier_list.html'
    permission_required = 'base_data.view_businesspartner'
    context_object_name = 'suppliers'

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({'title': _('الموردين'), 'url': None})
        return breadcrumbs

    def get_page_title(self):
        return _('الموردين')

    def get_queryset(self):
        return Supplier.suppliers.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('company', 'branch')


class SupplierCreateView(PartnerMixin, PermissionRequiredMixin, CreateView):
    """إضافة مورد جديد"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'base_data/partners/supplier_form.html'
    permission_required = 'base_data.add_businesspartner'
    success_url = reverse_lazy('base_data:supplier_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الموردين'), 'url': reverse('base_data:supplier_list')},
            {'title': _('إضافة جديد'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('إضافة مورد جديد')

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.partner_type = 'supplier'
        messages.success(self.request, _('تم إضافة المورد بنجاح'))
        return super().form_valid(form)


class SupplierUpdateView(PartnerMixin, PermissionRequiredMixin, UpdateView):
    """تعديل مورد"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'base_data/partners/supplier_form.html'
    permission_required = 'base_data.change_businesspartner'
    success_url = reverse_lazy('base_data:supplier_list')

    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.extend([
            {'title': _('الموردين'), 'url': reverse('base_data:supplier_list')},
            {'title': _('تعديل'), 'url': None}
        ])
        return breadcrumbs

    def get_page_title(self):
        return _('تعديل مورد')

    def get_queryset(self):
        return Supplier.suppliers.filter(company=self.request.user.company)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('تم تحديث المورد بنجاح'))
        return super().form_valid(form)


# ========== DataTables Ajax Views ==========

class BusinessPartnerDataTableView(LoginRequiredMixin, PermissionRequiredMixin, BaseDatatableView):
    """DataTables Ajax للشركاء التجاريين"""
    model = BusinessPartner
    permission_required = 'base_data.view_businesspartner'
    columns = ['code', 'name', 'partner_type', 'phone', 'email', 'city', 'is_active']
    order_columns = ['code', 'name', 'partner_type', 'phone', 'email', 'city', 'is_active']
    max_display_length = 100

    def get_initial_queryset(self):
        return BusinessPartner.objects.filter(
            company=self.request.user.company
        ).select_related('company')

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            json_data.append([
                item.code,
                item.name,
                item.get_partner_type_display(),
                item.phone or '',
                item.email or '',
                item.city or '',
                '<span class="badge bg-success">نشط</span>' if item.is_active else '<span class="badge bg-danger">غير نشط</span>',
                self._get_actions_html(item)
            ])
        return json_data

    def _get_actions_html(self, item):
        """إنشاء HTML للإجراءات"""
        actions = []

        if self.request.user.has_perm('base_data.view_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:partner_detail", kwargs={"pk": item.pk})}" class="btn btn-sm btn-info" title="عرض"><i class="fas fa-eye"></i></a>')

        if self.request.user.has_perm('base_data.change_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:partner_update", kwargs={"pk": item.pk})}" class="btn btn-sm btn-warning" title="تعديل"><i class="fas fa-edit"></i></a>')

        if self.request.user.has_perm('base_data.delete_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:partner_delete", kwargs={"pk": item.pk})}" class="btn btn-sm btn-danger" title="حذف"><i class="fas fa-trash"></i></a>')

        return ' '.join(actions)


class CustomerDataTableView(BusinessPartnerDataTableView):
    """DataTables Ajax للعملاء"""

    def get_initial_queryset(self):
        return Customer.customers.filter(
            company=self.request.user.company
        ).select_related('company')

    def _get_actions_html(self, item):
        """إنشاء HTML للإجراءات - العملاء"""
        actions = []

        if self.request.user.has_perm('base_data.view_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:customer_detail", kwargs={"pk": item.pk})}" class="btn btn-sm btn-info" title="عرض"><i class="fas fa-eye"></i></a>')

        if self.request.user.has_perm('base_data.change_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:customer_update", kwargs={"pk": item.pk})}" class="btn btn-sm btn-warning" title="تعديل"><i class="fas fa-edit"></i></a>')

        if self.request.user.has_perm('base_data.delete_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:customer_delete", kwargs={"pk": item.pk})}" class="btn btn-sm btn-danger" title="حذف"><i class="fas fa-trash"></i></a>')

        return ' '.join(actions)


class SupplierDataTableView(BusinessPartnerDataTableView):
    """DataTables Ajax للموردين"""

    def get_initial_queryset(self):
        return Supplier.suppliers.filter(
            company=self.request.user.company
        ).select_related('company')

    def _get_actions_html(self, item):
        """إنشاء HTML للإجراءات - الموردين"""
        actions = []

        if self.request.user.has_perm('base_data.view_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:supplier_detail", kwargs={"pk": item.pk})}" class="btn btn-sm btn-info" title="عرض"><i class="fas fa-eye"></i></a>')

        if self.request.user.has_perm('base_data.change_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:supplier_update", kwargs={"pk": item.pk})}" class="btn btn-sm btn-warning" title="تعديل"><i class="fas fa-edit"></i></a>')

        if self.request.user.has_perm('base_data.delete_businesspartner'):
            actions.append(
                f'<a href="{reverse("base_data:supplier_delete", kwargs={"pk": item.pk})}" class="btn btn-sm btn-danger" title="حذف"><i class="fas fa-trash"></i></a>')

        return ' '.join(actions)
# apps/core/views/uom_group_views.py
"""
Views for UoM Group management

⭐ NEW Week 2

Handles CRUD operations for Unit of Measure Groups
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _

from apps.core.models import UoMGroup, UnitOfMeasure
from apps.core.forms.uom_forms import UoMGroupForm


class UoMGroupListView(LoginRequiredMixin, ListView):
    """
    List view for UoM Groups with filtering and statistics.

    ⭐ NEW Week 2
    """
    model = UoMGroup
    template_name = 'core/uom_groups/group_list.html'
    context_object_name = 'groups'
    paginate_by = 25

    def get_queryset(self):
        queryset = UoMGroup.objects.filter(
            company=self.request.current_company
        ).annotate(
            unit_count=Count('units', filter=Q(units__is_active=True))
        ).order_by('name')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )

        # Active filter
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('مجموعات وحدات القياس')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('مجموعات وحدات القياس'), 'url': ''}
        ]

        context['can_add'] = self.request.user.has_perm('core.add_uomgroup')
        context['can_change'] = self.request.user.has_perm('core.change_uomgroup')
        context['can_delete'] = self.request.user.has_perm('core.delete_uomgroup')

        # Statistics
        all_groups = UoMGroup.objects.filter(company=self.request.current_company)
        context['total_groups'] = all_groups.count()
        context['active_groups'] = all_groups.filter(is_active=True).count()

        return context


class UoMGroupDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single UoM Group.
    Shows all units in the group.

    ⭐ NEW Week 2
    """
    model = UoMGroup
    template_name = 'core/uom_groups/group_detail.html'
    context_object_name = 'group'

    def get_queryset(self):
        return UoMGroup.objects.filter(
            company=self.request.current_company
        ).annotate(
            unit_count=Count('units', filter=Q(units__is_active=True))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        context['title'] = group.name
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('مجموعات وحدات القياس'), 'url': reverse('core:uom_group_list')},
            {'title': group.name, 'url': ''}
        ]

        # Get all units in this group
        context['units'] = UnitOfMeasure.objects.filter(
            company=self.request.current_company,
            uom_group=group
        ).order_by('name')

        # Get all conversions for units in this group
        context['conversions'] = group.get_all_conversions()

        context['can_change'] = self.request.user.has_perm('core.change_uomgroup')
        context['can_delete'] = self.request.user.has_perm('core.delete_uomgroup')

        context['edit_url'] = reverse('core:uom_group_update', args=[group.pk])
        context['delete_url'] = reverse('core:uom_group_delete', args=[group.pk])

        return context


class UoMGroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for new UoM Group.

    ⭐ NEW Week 2
    """
    model = UoMGroup
    form_class = UoMGroupForm
    template_name = 'core/uom_groups/group_form.html'
    permission_required = 'core.add_uomgroup'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        messages.success(
            self.request,
            _('تم إنشاء مجموعة وحدات القياس بنجاح: %(name)s') % {
                'name': self.object.name
            }
        )

        return response

    def get_success_url(self):
        return reverse('core:uom_group_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة مجموعة وحدات قياس جديدة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('مجموعات وحدات القياس'), 'url': reverse('core:uom_group_list')},
            {'title': _('إضافة جديدة'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء المجموعة')
        context['cancel_url'] = reverse('core:uom_group_list')

        return context


class UoMGroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for existing UoM Group.

    ⭐ NEW Week 2
    """
    model = UoMGroup
    form_class = UoMGroupForm
    template_name = 'core/uom_groups/group_form.html'
    permission_required = 'core.change_uomgroup'

    def get_queryset(self):
        return UoMGroup.objects.filter(
            company=self.request.current_company
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            _('تم تحديث مجموعة وحدات القياس بنجاح')
        )

        return response

    def get_success_url(self):
        return reverse('core:uom_group_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تعديل مجموعة وحدات القياس')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('مجموعات وحدات القياس'), 'url': reverse('core:uom_group_list')},
            {'title': self.object.name, 'url': reverse('core:uom_group_detail', args=[self.object.pk])},
            {'title': _('تعديل'), 'url': ''}
        ]

        context['submit_text'] = _('حفظ التعديلات')
        context['cancel_url'] = reverse('core:uom_group_detail', args=[self.object.pk])

        return context


class UoMGroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for UoM Group.

    ⭐ NEW Week 2
    """
    model = UoMGroup
    template_name = 'core/uom_groups/group_confirm_delete.html'
    permission_required = 'core.delete_uomgroup'
    success_url = reverse_lazy('core:uom_group_list')

    def get_queryset(self):
        return UoMGroup.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        group = self.get_object()

        # Check if group has units
        unit_count = group.units.count()
        if unit_count > 0:
            messages.error(
                request,
                _('لا يمكن حذف المجموعة لأنها تحتوي على %(count)d وحدة. قم بحذف الوحدات أولاً.') % {
                    'count': unit_count
                }
            )
            return redirect('core:uom_group_detail', pk=group.pk)

        messages.success(
            request,
            _('تم حذف مجموعة وحدات القياس بنجاح: %(name)s') % {
                'name': group.name
            }
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تأكيد حذف المجموعة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('مجموعات وحدات القياس'), 'url': reverse('core:uom_group_list')},
            {'title': self.object.name, 'url': reverse('core:uom_group_detail', args=[self.object.pk])},
            {'title': _('حذف'), 'url': ''}
        ]

        context['cancel_url'] = reverse('core:uom_group_detail', args=[self.object.pk])

        # Show warning if group has units
        context['unit_count'] = self.object.units.count()
        context['has_units'] = context['unit_count'] > 0

        return context

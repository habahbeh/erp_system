# apps/core/views/uom_views.py
"""
Views for Unit of Measure (UoM) Conversion management
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count, F
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.utils.translation import gettext_lazy as _

from apps.core.models import UoMConversion, UnitOfMeasure, Item, ItemVariant
from apps.core.forms.uom_forms import UoMConversionForm, UoMConversionBulkForm


class UoMConversionListView(LoginRequiredMixin, ListView):
    """
    List view for UoM Conversions with filtering.
    """
    model = UoMConversion
    template_name = 'core/uom_conversions/conversion_list.html'
    context_object_name = 'conversions'
    paginate_by = 25

    def get_queryset(self):
        queryset = UoMConversion.objects.filter(
            company=self.request.current_company
        ).select_related(
            'from_uom', 'to_uom', 'item', 'variant'
        ).order_by('-created_at')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(from_uom__name__icontains=search) |
                Q(to_uom__name__icontains=search) |
                Q(item__name__icontains=search) |
                Q(variant__code__icontains=search)
            )

        # From UoM filter
        from_uom = self.request.GET.get('from_uom')
        if from_uom:
            queryset = queryset.filter(from_uom_id=from_uom)

        # To UoM filter
        to_uom = self.request.GET.get('to_uom')
        if to_uom:
            queryset = queryset.filter(to_uom_id=to_uom)

        # Item filter
        item = self.request.GET.get('item')
        if item:
            queryset = queryset.filter(item_id=item)

        # Scope filter (global vs specific)
        scope = self.request.GET.get('scope')
        if scope == 'global':
            queryset = queryset.filter(item__isnull=True, variant__isnull=True)
        elif scope == 'item':
            queryset = queryset.filter(item__isnull=False, variant__isnull=True)
        elif scope == 'variant':
            queryset = queryset.filter(variant__isnull=False)

        # Active filter
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تحويلات وحدات القياس')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': ''}
        ]

        # Filter options
        context['uom_list'] = UnitOfMeasure.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context['can_add'] = self.request.user.has_perm('core.add_uomconversion')
        context['can_change'] = self.request.user.has_perm('core.change_uomconversion')
        context['can_delete'] = self.request.user.has_perm('core.delete_uomconversion')

        # Statistics
        context['total_conversions'] = self.get_queryset().count()
        context['global_conversions'] = self.get_queryset().filter(
            item__isnull=True, variant__isnull=True
        ).count()

        return context


class UoMConversionDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single UoM Conversion.
    """
    model = UoMConversion
    template_name = 'core/uom/conversion_detail.html'
    context_object_name = 'conversion'

    def get_queryset(self):
        return UoMConversion.objects.filter(
            company=self.request.current_company
        ).select_related(
            'from_uom', 'to_uom', 'item', 'variant', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversion = self.object

        context['title'] = _('تفاصيل التحويل')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': reverse('core:uom_conversion_list')},
            {'title': _('التفاصيل'), 'url': ''}
        ]

        # Calculate example conversions
        context['examples'] = [
            {
                'from_qty': 1,
                'to_qty': conversion.convert(1)
            },
            {
                'from_qty': 5,
                'to_qty': conversion.convert(5)
            },
            {
                'from_qty': 10,
                'to_qty': conversion.convert(10)
            },
            {
                'from_qty': 100,
                'to_qty': conversion.convert(100)
            }
        ]

        context['can_change'] = self.request.user.has_perm('core.change_uomconversion')
        context['can_delete'] = self.request.user.has_perm('core.delete_uomconversion')

        context['edit_url'] = reverse('core:uom_conversion_update', args=[conversion.pk])
        context['delete_url'] = reverse('core:uom_conversion_delete', args=[conversion.pk])

        return context


class UoMConversionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for new UoM Conversion.
    """
    model = UoMConversion
    form_class = UoMConversionForm
    template_name = 'core/uom/conversion_form.html'
    permission_required = 'core.add_uomconversion'

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
            _('تم إنشاء التحويل بنجاح: %(from)s → %(to)s') % {
                'from': self.object.from_uom.name,
                'to': self.object.to_uom.name
            }
        )

        return response

    def get_success_url(self):
        return reverse('core:uom_conversion_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة تحويل جديد')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': reverse('core:uom_conversion_list')},
            {'title': _('إضافة جديد'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء التحويل')
        context['cancel_url'] = reverse('core:uom_conversion_list')

        return context


class UoMConversionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for existing UoM Conversion.
    """
    model = UoMConversion
    form_class = UoMConversionForm
    template_name = 'core/uom/conversion_form.html'
    permission_required = 'core.change_uomconversion'

    def get_queryset(self):
        return UoMConversion.objects.filter(
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
            _('تم تحديث التحويل بنجاح')
        )

        return response

    def get_success_url(self):
        return reverse('core:uom_conversion_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تعديل التحويل')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': reverse('core:uom_conversion_list')},
            {'title': self.object.__str__(), 'url': reverse('core:uom_conversion_detail', args=[self.object.pk])},
            {'title': _('تعديل'), 'url': ''}
        ]

        context['submit_text'] = _('حفظ التعديلات')
        context['cancel_url'] = reverse('core:uom_conversion_detail', args=[self.object.pk])

        return context


class UoMConversionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for UoM Conversion.
    """
    model = UoMConversion
    template_name = 'core/uom/conversion_confirm_delete.html'
    permission_required = 'core.delete_uomconversion'
    success_url = reverse_lazy('core:uom_conversion_list')

    def get_queryset(self):
        return UoMConversion.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        conversion = self.get_object()
        messages.success(
            request,
            _('تم حذف التحويل بنجاح: %(from)s → %(to)s') % {
                'from': conversion.from_uom.name,
                'to': conversion.to_uom.name
            }
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تأكيد حذف التحويل')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': reverse('core:uom_conversion_list')},
            {'title': self.object.__str__(), 'url': reverse('core:uom_conversion_detail', args=[self.object.pk])},
            {'title': _('حذف'), 'url': ''}
        ]

        context['cancel_url'] = reverse('core:uom_conversion_detail', args=[self.object.pk])

        return context


class UoMConversionBulkCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Bulk create view for creating multiple UoM conversions at once.
    """
    form_class = UoMConversionBulkForm
    template_name = 'core/uom/conversion_bulk_form.html'
    permission_required = 'core.add_uomconversion'
    success_url = reverse_lazy('core:uom_conversion_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        conversions = form.save()

        if conversions:
            messages.success(
                self.request,
                _('تم إنشاء %(count)d تحويل بنجاح') % {'count': len(conversions)}
            )
        else:
            messages.warning(
                self.request,
                _('لم يتم إنشاء أي تحويلات. قد تكون موجودة مسبقاً.')
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إنشاء تحويلات متعددة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('تحويلات وحدات القياس'), 'url': reverse('core:uom_conversion_list')},
            {'title': _('إنشاء متعدد'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء التحويلات')
        context['cancel_url'] = reverse('core:uom_conversion_list')

        return context

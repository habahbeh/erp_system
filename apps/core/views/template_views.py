# apps/core/views/template_views.py
"""
Views for Item Template management
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import ItemTemplate, Item, ItemCategory
from apps.core.forms.template_forms import (
    ItemTemplateForm, ItemTemplateWizardForm, UseTemplateForm
)


class ItemTemplateListView(LoginRequiredMixin, ListView):
    """
    List view for Item Templates with filtering.
    """
    model = ItemTemplate
    template_name = 'core/templates/template_list.html'
    context_object_name = 'templates'
    paginate_by = 25

    def get_queryset(self):
        queryset = ItemTemplate.objects.filter(
            company=self.request.current_company
        ).select_related('category', 'created_by').annotate(
            items_created=Count('created_items')  # Assuming related_name in Item model
        ).order_by('-created_at')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Active filter
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        # Sort by usage
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'most_used':
            queryset = queryset.order_by('-usage_count')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-last_used_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('قوالب المواد')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': ''}
        ]

        # Filter options
        context['categories'] = ItemCategory.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context['can_add'] = self.request.user.has_perm('core.add_itemtemplate')
        context['can_change'] = self.request.user.has_perm('core.change_itemtemplate')
        context['can_delete'] = self.request.user.has_perm('core.delete_itemtemplate')

        # Statistics
        context['total_templates'] = self.get_queryset().count()
        context['total_usage'] = sum(t.usage_count for t in self.get_queryset())

        return context


class ItemTemplateDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single Item Template.
    """
    model = ItemTemplate
    template_name = 'core/templates/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        return ItemTemplate.objects.filter(
            company=self.request.current_company
        ).select_related('category', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object

        context['title'] = template.name
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
            {'title': template.name, 'url': ''}
        ]

        # Parse template_data for display
        import json
        context['template_data_pretty'] = json.dumps(
            template.template_data, indent=2, ensure_ascii=False
        )

        # Get recently created items from this template (if tracking exists)
        # context['recent_items'] = Item.objects.filter(
        #     template=template
        # ).order_by('-created_at')[:10]

        context['can_change'] = self.request.user.has_perm('core.change_itemtemplate')
        context['can_delete'] = self.request.user.has_perm('core.delete_itemtemplate')
        context['can_use'] = self.request.user.has_perm('core.add_item')

        context['edit_url'] = reverse('core:item_template_update', args=[template.pk])
        context['delete_url'] = reverse('core:item_template_delete', args=[template.pk])
        context['clone_url'] = reverse('core:item_template_clone', args=[template.pk])
        context['use_url'] = reverse('core:item_template_use', args=[template.pk])

        return context


class ItemTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for new Item Template.
    """
    model = ItemTemplate
    form_class = ItemTemplateForm
    template_name = 'core/templates/template_form.html'
    permission_required = 'core.add_itemtemplate'

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
            _('تم إنشاء القالب بنجاح: %(name)s') % {'name': self.object.name}
        )

        return response

    def get_success_url(self):
        return reverse('core:item_template_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة قالب جديد')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
            {'title': _('إضافة جديد'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء القالب')
        context['cancel_url'] = reverse('core:item_template_list')
        context['mode'] = 'create'

        return context


class ItemTemplateWizardCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Wizard-based create view for Item Template (user-friendly).
    """
    form_class = ItemTemplateWizardForm
    template_name = 'core/templates/template_wizard.html'
    permission_required = 'core.add_itemtemplate'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        # Create template from wizard form
        template = form.save(company=self.request.current_company)

        messages.success(
            self.request,
            _('تم إنشاء القالب بنجاح: %(name)s') % {'name': template.name}
        )

        return redirect('core:item_template_detail', pk=template.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إنشاء قالب (معالج)')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
            {'title': _('معالج الإنشاء'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء القالب')
        context['cancel_url'] = reverse('core:item_template_list')

        return context


class ItemTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for existing Item Template.
    """
    model = ItemTemplate
    form_class = ItemTemplateForm
    template_name = 'core/templates/template_form.html'
    permission_required = 'core.change_itemtemplate'

    def get_queryset(self):
        return ItemTemplate.objects.filter(
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
            _('تم تحديث القالب بنجاح')
        )

        return response

    def get_success_url(self):
        return reverse('core:item_template_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تعديل القالب')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
            {'title': self.object.name, 'url': reverse('core:item_template_detail', args=[self.object.pk])},
            {'title': _('تعديل'), 'url': ''}
        ]

        context['submit_text'] = _('حفظ التعديلات')
        context['cancel_url'] = reverse('core:item_template_detail', args=[self.object.pk])
        context['mode'] = 'edit'

        return context


class ItemTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for Item Template.
    """
    model = ItemTemplate
    template_name = 'core/templates/template_confirm_delete.html'
    permission_required = 'core.delete_itemtemplate'
    success_url = reverse_lazy('core:item_template_list')

    def get_queryset(self):
        return ItemTemplate.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        template = self.get_object()

        # Check if template has been used
        if template.usage_count > 0:
            messages.warning(
                request,
                _('تحذير: هذا القالب تم استخدامه %(count)d مرة. الحذف لن يؤثر على المواد المنشأة منه.') % {
                    'count': template.usage_count
                }
            )

        messages.success(
            request,
            _('تم حذف القالب بنجاح: %(name)s') % {'name': template.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تأكيد حذف القالب')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
            {'title': self.object.name, 'url': reverse('core:item_template_detail', args=[self.object.pk])},
            {'title': _('حذف'), 'url': ''}
        ]

        context['cancel_url'] = reverse('core:item_template_detail', args=[self.object.pk])

        # Warning if template has been used
        if self.object.usage_count > 0:
            context['has_usage'] = True
            context['usage_count'] = self.object.usage_count

        return context


class ItemTemplateCloneView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Clone view for duplicating an item template.
    """
    model = ItemTemplate
    permission_required = 'core.add_itemtemplate'

    def get_queryset(self):
        return ItemTemplate.objects.filter(
            company=self.request.current_company
        )

    def get(self, request, *args, **kwargs):
        original_template = self.get_object()

        # Create a copy
        new_template = ItemTemplate.objects.get(pk=original_template.pk)
        new_template.pk = None  # This will create a new instance
        new_template.code = f"{original_template.code}-COPY"
        new_template.name = f"{original_template.name} (نسخة)"
        new_template.is_active = False  # Inactive by default
        new_template.usage_count = 0
        new_template.last_used_at = None
        new_template.created_by = request.user
        new_template.save()

        messages.success(
            request,
            _('تم نسخ القالب بنجاح. يمكنك الآن تعديله.')
        )

        return redirect('core:item_template_update', pk=new_template.pk)


class ItemTemplateUseView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Use template view for creating an item from a template.
    """
    form_class = UseTemplateForm
    template_name = 'core/templates/template_use.html'
    permission_required = 'core.add_item'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select the template from URL
        template_id = self.kwargs.get('pk')
        if template_id:
            initial['template'] = template_id
        return initial

    def form_valid(self, form):
        template = form.cleaned_data['template']
        item_name = form.cleaned_data['item_name']
        item_code = form.cleaned_data.get('item_code')

        # Create item from template
        # This is a placeholder - actual implementation would be more complex
        custom_data = {
            'name': item_name,
        }
        if item_code:
            custom_data['item_code'] = item_code

        # TODO: Implement create_item_from_template function
        # item = create_item_from_template(template, custom_data)

        # Update template usage stats
        template.usage_count += 1
        template.last_used_at = timezone.now()
        template.save(update_fields=['usage_count', 'last_used_at'])

        messages.success(
            self.request,
            _('تم إنشاء المادة بنجاح من القالب')
        )

        # Redirect to item edit page
        # return redirect('core:item_update', pk=item.pk)
        return redirect('core:item_template_list')  # Temporary

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        template_id = self.kwargs.get('pk')
        template = None
        if template_id:
            template = ItemTemplate.objects.filter(
                company=self.request.current_company,
                pk=template_id
            ).first()

        context['title'] = _('استخدام القالب')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قوالب المواد'), 'url': reverse('core:item_template_list')},
        ]

        if template:
            context['breadcrumbs'].append(
                {'title': template.name, 'url': reverse('core:item_template_detail', args=[template.pk])}
            )
            context['template'] = template

        context['breadcrumbs'].append({'title': _('استخدام'), 'url': ''})

        context['submit_text'] = _('إنشاء المادة')
        context['cancel_url'] = reverse('core:item_template_list')

        return context

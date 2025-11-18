# apps/core/views/pricing_views.py
"""
Views for Pricing Rules management
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from apps.core.models import PricingRule, PriceList, ItemCategory, Item
from apps.core.forms.pricing_forms import PricingRuleForm, PricingRuleTestForm
from apps.core.utils.pricing_engine import PricingEngine


class PricingRuleListView(LoginRequiredMixin, ListView):
    """
    List view for Pricing Rules with filtering.
    """
    model = PricingRule
    template_name = 'core/pricing/rule_list.html'
    context_object_name = 'rules'
    paginate_by = 25

    def get_queryset(self):
        queryset = PricingRule.objects.filter(
            company=self.request.current_company
        ).prefetch_related(
            'apply_to_categories', 'apply_to_items', 'apply_to_price_lists'
        ).order_by('-priority', 'name')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        # Rule type filter
        rule_type = self.request.GET.get('rule_type')
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)

        # Priority filter
        priority_min = self.request.GET.get('priority_min')
        if priority_min:
            queryset = queryset.filter(priority__gte=priority_min)

        # Active filter
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == '1')

        # Date validity filter
        show_active_only = self.request.GET.get('show_active_only')
        if show_active_only == '1':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=today)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('قواعد التسعير')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': ''}
        ]

        # Filter options
        context['rule_types'] = PricingRule.RULE_TYPE_CHOICES
        context['price_lists'] = PriceList.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context['can_add'] = self.request.user.has_perm('core.add_pricingrule')
        context['can_change'] = self.request.user.has_perm('core.change_pricingrule')
        context['can_delete'] = self.request.user.has_perm('core.delete_pricingrule')

        # Statistics
        context['total_rules'] = self.get_queryset().count()
        context['active_rules'] = self.get_queryset().filter(is_active=True).count()

        return context


class PricingRuleDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single Pricing Rule.
    """
    model = PricingRule
    template_name = 'core/pricing/rule_detail.html'
    context_object_name = 'rule'

    def get_queryset(self):
        return PricingRule.objects.filter(
            company=self.request.current_company
        ).prefetch_related(
            'apply_to_categories', 'apply_to_items', 'apply_to_price_lists'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rule = self.object

        context['title'] = rule.name
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': rule.name, 'url': ''}
        ]

        # Applicability summary
        context['applies_to'] = {
            'categories': rule.apply_to_categories.count(),
            'items': rule.apply_to_items.count(),
            'price_lists': rule.apply_to_price_lists.count(),
            'all_items': rule.apply_to_all_items,
        }

        # Rule type display
        context['rule_type_display'] = rule.get_rule_type_display()

        # Date validity status
        if rule.start_date or rule.end_date:
            from django.utils import timezone
            today = timezone.now().date()

            if rule.start_date and today < rule.start_date:
                context['validity_status'] = 'future'
                context['validity_message'] = _('سيبدأ من %(date)s') % {'date': rule.start_date}
            elif rule.end_date and today > rule.end_date:
                context['validity_status'] = 'expired'
                context['validity_message'] = _('انتهى في %(date)s') % {'date': rule.end_date}
            else:
                context['validity_status'] = 'active'
                context['validity_message'] = _('نشط حالياً')

        context['can_change'] = self.request.user.has_perm('core.change_pricingrule')
        context['can_delete'] = self.request.user.has_perm('core.delete_pricingrule')

        context['edit_url'] = reverse('core:pricing_rule_update', args=[rule.pk])
        context['delete_url'] = reverse('core:pricing_rule_delete', args=[rule.pk])
        context['test_url'] = reverse('core:pricing_rule_test', args=[rule.pk])
        context['clone_url'] = reverse('core:pricing_rule_clone', args=[rule.pk])

        return context


class PricingRuleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for new Pricing Rule.
    """
    model = PricingRule
    form_class = PricingRuleForm
    template_name = 'core/pricing/rule_form.html'
    permission_required = 'core.add_pricingrule'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        response = super().form_valid(form)

        messages.success(
            self.request,
            _('تم إنشاء قاعدة التسعير بنجاح: %(name)s') % {'name': self.object.name}
        )

        return response

    def get_success_url(self):
        return reverse('core:pricing_rule_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة قاعدة تسعير جديدة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': _('إضافة جديد'), 'url': ''}
        ]

        context['submit_text'] = _('إنشاء القاعدة')
        context['cancel_url'] = reverse('core:pricing_rule_list')

        return context


class PricingRuleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for existing Pricing Rule.
    """
    model = PricingRule
    form_class = PricingRuleForm
    template_name = 'core/pricing/rule_form.html'
    permission_required = 'core.change_pricingrule'

    def get_queryset(self):
        return PricingRule.objects.filter(
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
            _('تم تحديث قاعدة التسعير بنجاح')
        )

        return response

    def get_success_url(self):
        return reverse('core:pricing_rule_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تعديل قاعدة التسعير')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': self.object.name, 'url': reverse('core:pricing_rule_detail', args=[self.object.pk])},
            {'title': _('تعديل'), 'url': ''}
        ]

        context['submit_text'] = _('حفظ التعديلات')
        context['cancel_url'] = reverse('core:pricing_rule_detail', args=[self.object.pk])

        return context


class PricingRuleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for Pricing Rule.
    """
    model = PricingRule
    template_name = 'core/pricing/rule_confirm_delete.html'
    permission_required = 'core.delete_pricingrule'
    success_url = reverse_lazy('core:pricing_rule_list')

    def get_queryset(self):
        return PricingRule.objects.filter(
            company=self.request.current_company
        )

    def delete(self, request, *args, **kwargs):
        rule = self.get_object()
        messages.success(
            request,
            _('تم حذف قاعدة التسعير بنجاح: %(name)s') % {'name': rule.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تأكيد حذف قاعدة التسعير')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': self.object.name, 'url': reverse('core:pricing_rule_detail', args=[self.object.pk])},
            {'title': _('حذف'), 'url': ''}
        ]

        context['cancel_url'] = reverse('core:pricing_rule_detail', args=[self.object.pk])

        return context


class PricingRuleTestView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Test view for trying out a pricing rule on a specific item.
    """
    form_class = PricingRuleTestForm
    template_name = 'core/pricing/rule_test.html'
    permission_required = 'core.view_pricingrule'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select the rule from URL
        rule_id = self.kwargs.get('pk')
        if rule_id:
            initial['pricing_rule'] = rule_id
        return initial

    def form_valid(self, form):
        rule = form.cleaned_data['pricing_rule']
        item = form.cleaned_data['item']
        quantity = form.cleaned_data.get('quantity', 1)
        cost_price = form.cleaned_data.get('cost_price')

        # Calculate price using rule
        calculated_price = rule.calculate_price(
            base_price=item.base_price if hasattr(item, 'base_price') else None,
            quantity=quantity,
            cost_price=cost_price
        )

        # Store result in session for display
        self.request.session['test_result'] = {
            'rule_name': rule.name,
            'item_name': item.name,
            'quantity': str(quantity),
            'cost_price': str(cost_price) if cost_price else None,
            'calculated_price': str(calculated_price),
        }

        messages.success(
            self.request,
            _('السعر المحسوب: %(price)s') % {'price': calculated_price}
        )

        return self.render_to_response(self.get_context_data(
            form=form,
            result=self.request.session['test_result']
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        rule_id = self.kwargs.get('pk')
        rule = None
        if rule_id:
            rule = PricingRule.objects.filter(
                company=self.request.current_company,
                pk=rule_id
            ).first()

        context['title'] = _('اختبار قاعدة التسعير')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
        ]

        if rule:
            context['breadcrumbs'].append(
                {'title': rule.name, 'url': reverse('core:pricing_rule_detail', args=[rule.pk])}
            )
            context['rule'] = rule

        context['breadcrumbs'].append({'title': _('اختبار'), 'url': ''})

        context['submit_text'] = _('حساب السعر')
        context['cancel_url'] = reverse('core:pricing_rule_list')

        # Get test result from session if exists
        if 'test_result' in self.request.session and 'result' not in kwargs:
            context['result'] = self.request.session.pop('test_result')

        return context


class PricingRuleCloneView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Clone view for duplicating a pricing rule.
    """
    model = PricingRule
    permission_required = 'core.add_pricingrule'

    def get_queryset(self):
        return PricingRule.objects.filter(
            company=self.request.current_company
        )

    def get(self, request, *args, **kwargs):
        original_rule = self.get_object()

        # Create a copy
        new_rule = PricingRule.objects.get(pk=original_rule.pk)
        new_rule.pk = None  # This will create a new instance
        new_rule.name = f"{original_rule.name} (نسخة)"
        new_rule.code = f"{original_rule.code}_COPY"
        new_rule.is_active = False  # Inactive by default
        new_rule.save()

        # Copy M2M relationships
        new_rule.apply_to_categories.set(original_rule.apply_to_categories.all())
        new_rule.apply_to_items.set(original_rule.apply_to_items.all())
        new_rule.apply_to_price_lists.set(original_rule.apply_to_price_lists.all())

        messages.success(
            request,
            _('تم نسخ قاعدة التسعير بنجاح. يمكنك الآن تعديلها.')
        )

        return redirect('core:pricing_rule_update', pk=new_rule.pk)

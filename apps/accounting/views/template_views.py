# apps/accounting/views/template_views.py
"""
Views قوالب القيود اليومية
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import CompanyMixin, AuditLogMixin
from ..models import JournalEntryTemplate, JournalEntryTemplateLine
from ..forms.journal_forms import (
    JournalEntryTemplateForm, JournalEntryTemplateFilterForm,
    UseTemplateForm, JournalEntryTemplateLineForm
)


class JournalEntryTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة قوالب القيود"""
    model = JournalEntryTemplate
    template_name = 'accounting/templates/template_list.html'
    context_object_name = 'templates'
    permission_required = 'accounting.view_journalentrytemplate'
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntryTemplate.objects.filter(
            company=self.request.current_company
        ).prefetch_related('template_lines').order_by('display_order', 'name')

        # تطبيق الفلاتر
        form = JournalEntryTemplateFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('entry_type'):
                queryset = queryset.filter(entry_type=form.cleaned_data['entry_type'])

            if form.cleaned_data.get('status') == 'active':
                queryset = queryset.filter(is_active=True)
            elif form.cleaned_data.get('status') == 'inactive':
                queryset = queryset.filter(is_active=False)

            if form.cleaned_data.get('category'):
                queryset = queryset.filter(category__icontains=form.cleaned_data['category'])

            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(code__icontains=search)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('قوالب القيود'),
            'filter_form': JournalEntryTemplateFilterForm(self.request.GET),
            'can_add': self.request.user.has_perm('accounting.add_journalentrytemplate'),
            'can_edit': self.request.user.has_perm('accounting.change_journalentrytemplate'),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentrytemplate'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': ''},
            ]
        })
        return context


class JournalEntryTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء قالب قيد جديد"""
    model = JournalEntryTemplate
    form_class = JournalEntryTemplateForm
    template_name = 'accounting/templates/template_form.html'
    permission_required = 'accounting.add_journalentrytemplate'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء القالب {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:template_detail', kwargs={'pk': self.object.pk})


class JournalEntryTemplateDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل قالب القيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/templates/template_detail.html'
    context_object_name = 'template'
    permission_required = 'accounting.view_journalentrytemplate'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(
            company=self.request.current_company
        ).prefetch_related('template_lines__account')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'قالب: {self.object.name}',
            'can_edit': self.request.user.has_perm('accounting.change_journalentrytemplate'),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentrytemplate'),
            'can_use': self.request.user.has_perm('accounting.add_journalentry'),
        })
        return context


class JournalEntryTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل قالب القيد"""
    model = JournalEntryTemplate
    form_class = JournalEntryTemplateForm
    template_name = 'accounting/templates/template_form.html'
    permission_required = 'accounting.change_journalentrytemplate'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث القالب {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:template_detail', kwargs={'pk': self.object.pk})


class JournalEntryTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف قالب القيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/templates/template_confirm_delete.html'
    permission_required = 'accounting.delete_journalentrytemplate'
    success_url = reverse_lazy('accounting:template_list')

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        template_name = self.get_object().name
        messages.success(request, f'تم حذف القالب {template_name} بنجاح')
        return super().delete(request, *args, **kwargs)


class UseTemplateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """استخدام قالب لإنشاء قيد"""
    template_name = 'accounting/templates/use_template.html'
    permission_required = 'accounting.add_journalentry'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('display_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('استخدام قالب لإنشاء قيد'),
            'form': UseTemplateForm(request=self.request),
        })
        return context

    def post(self, request, *args, **kwargs):
        form = UseTemplateForm(request.POST, request=request)
        if form.is_valid():
            template = form.cleaned_data['template']
            journal_entry = template.create_journal_entry(
                entry_date=form.cleaned_data['entry_date'],
                description=form.cleaned_data['description'] or template.default_description,
                reference=form.cleaned_data['reference'] or template.default_reference
            )
            messages.success(request, f'تم إنشاء القيد {journal_entry.number} من القالب بنجاح')
            return redirect('accounting:journal_entry_detail', pk=journal_entry.pk)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
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
from django.db import transaction
import json

from apps.core.mixins import CompanyMixin, AuditLogMixin
from ..models import JournalEntryTemplate, JournalEntryTemplateLine, Account
from ..models.account_models import CostCenter
from ..forms.journal_forms import (
    JournalEntryTemplateForm, JournalEntryTemplateFilterForm,
    UseTemplateForm, JournalEntryTemplateLineForm
)


class JournalEntryTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة قوالب القيود"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/journal_entry_template_list.html'  # ✅ محدث
    context_object_name = 'templates'
    permission_required = 'accounting.view_journalentrytemplate'
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntryTemplate.objects.filter(
            company=self.request.current_company
        ).prefetch_related('template_lines__account').order_by('display_order', 'name')

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

        # إحصائيات
        all_templates = JournalEntryTemplate.objects.filter(company=self.request.current_company)
        stats = {
            'total': all_templates.count(),
            'active': all_templates.filter(is_active=True).count(),
            'inactive': all_templates.filter(is_active=False).count(),
            'categories': all_templates.values('category').distinct().count()
        }

        context.update({
            'title': _('قوالب القيود اليومية'),
            'stats': stats,
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


class JournalEntryTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                     CreateView):
    """إنشاء قالب قيد جديد"""
    model = JournalEntryTemplate
    form_class = JournalEntryTemplateForm
    template_name = 'accounting/journal/journal_entry_template_form.html'  # ✅ محدث
    permission_required = 'accounting.add_journalentrytemplate'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        self.object = form.save()

        # معالجة سطور القالب
        lines_data = self.request.POST.get('lines_data')
        if lines_data:
            try:
                lines = json.loads(lines_data)

                for line_data in lines:
                    account_id = line_data.get('account')
                    if not account_id:
                        continue

                    try:
                        account = Account.objects.get(
                            id=account_id,
                            company=self.request.current_company
                        )

                        debit = float(line_data.get('debit_amount', 0) or 0)
                        credit = float(line_data.get('credit_amount', 0) or 0)

                        JournalEntryTemplateLine.objects.create(
                            template=self.object,
                            line_number=line_data.get('line_number', 1),
                            account=account,
                            description=line_data.get('description', ''),
                            debit_amount=debit,
                            credit_amount=credit,
                            reference=line_data.get('reference', ''),
                            default_cost_center_id=line_data.get('default_cost_center') if line_data.get(
                                'default_cost_center') else None,
                            is_required=line_data.get('is_required', True),
                            amount_editable=line_data.get('amount_editable', True)
                        )

                    except Account.DoesNotExist:
                        continue

                messages.success(self.request, f'تم إنشاء القالب {self.object.name} بنجاح')

            except json.JSONDecodeError as e:
                messages.error(self.request, f'خطأ في بيانات السطور: {str(e)}')
                self.object.delete()
                return self.form_invalid(form)
        else:
            messages.warning(self.request, 'تم إنشاء القالب بدون سطور. يمكنك إضافة السطور لاحقاً.')

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('accounting:journal_template_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحسابات المتاحة
        accounts = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True,
            is_suspended=False
        ).order_by('code')

        # مراكز التكلفة
        cost_centers = CostCenter.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('code')

        context.update({
            'title': _('إنشاء قالب قيد جديد'),
            'accounts': accounts,
            'cost_centers': cost_centers,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': reverse('accounting:template_list')},
                {'title': _('إنشاء قالب جديد'), 'url': ''},
            ]
        })
        return context


class JournalEntryTemplateDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل قالب القيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/journal_entry_template_detail.html'  # ✅ محدث
    context_object_name = 'template'
    permission_required = 'accounting.view_journalentrytemplate'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(
            company=self.request.current_company
        ).prefetch_related('template_lines__account', 'template_lines__default_cost_center')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # حساب عدد مرات الاستخدام (من القيود المرتبطة)
        usage_count = self.object.journalentry_set.count() if hasattr(self.object, 'journalentry_set') else 0

        context.update({
            'title': f'قالب: {self.object.name}',
            'usage_count': usage_count,
            'can_edit': self.request.user.has_perm('accounting.change_journalentrytemplate'),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentrytemplate'),
            'can_use': self.request.user.has_perm('accounting.add_journalentry'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': reverse('accounting:template_list')},
                {'title': self.object.name, 'url': ''},
            ]
        })
        return context


class JournalEntryTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                     UpdateView):
    """تعديل قالب القيد"""
    model = JournalEntryTemplate
    form_class = JournalEntryTemplateForm
    template_name = 'accounting/journal/journal_entry_template_form.html'  # ✅ محدث
    permission_required = 'accounting.change_journalentrytemplate'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        # حذف السطور القديمة
        self.object.template_lines.all().delete()

        # معالجة السطور الجديدة
        lines_data = self.request.POST.get('lines_data')
        if lines_data:
            try:
                lines = json.loads(lines_data)

                for line_data in lines:
                    account_id = line_data.get('account')
                    if not account_id:
                        continue

                    try:
                        account = Account.objects.get(
                            id=account_id,
                            company=self.request.current_company
                        )

                        debit = float(line_data.get('debit_amount', 0) or 0)
                        credit = float(line_data.get('credit_amount', 0) or 0)

                        JournalEntryTemplateLine.objects.create(
                            template=self.object,
                            line_number=line_data.get('line_number', 1),
                            account=account,
                            description=line_data.get('description', ''),
                            debit_amount=debit,
                            credit_amount=credit,
                            reference=line_data.get('reference', ''),
                            default_cost_center_id=line_data.get('default_cost_center') if line_data.get(
                                'default_cost_center') else None,
                            is_required=line_data.get('is_required', True),
                            amount_editable=line_data.get('amount_editable', True)
                        )

                    except Account.DoesNotExist:
                        continue

                messages.success(self.request, f'تم تحديث القالب {self.object.name} بنجاح')

            except json.JSONDecodeError as e:
                messages.error(self.request, f'خطأ في بيانات السطور: {str(e)}')
                return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('accounting:journal_template_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحسابات المتاحة
        accounts = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True,
            is_suspended=False
        ).order_by('code')

        # مراكز التكلفة
        cost_centers = CostCenter.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('code')

        context.update({
            'title': f'تعديل القالب: {self.object.name}',
            'accounts': accounts,
            'cost_centers': cost_centers,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': reverse('accounting:template_list')},
                {'title': self.object.name,
                 'url': reverse('accounting:journal_template_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class JournalEntryTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف قالب القيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/journal_entry_template_confirm_delete.html'  # ✅ محدث
    permission_required = 'accounting.delete_journalentrytemplate'
    success_url = reverse_lazy('accounting:template_list')

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # حساب عدد مرات الاستخدام
        usage_count = self.object.journalentry_set.count() if hasattr(self.object, 'journalentry_set') else 0

        context.update({
            'title': f'حذف القالب: {self.object.name}',
            'usage_count': usage_count,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': reverse('accounting:template_list')},
                {'title': self.object.name,
                 'url': reverse('accounting:journal_template_detail', kwargs={'pk': self.object.pk})},
                {'title': _('حذف'), 'url': ''},
            ]
        })
        return context

    def delete(self, request, *args, **kwargs):
        template_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'تم حذف القالب {template_name} بنجاح')
        return response


class UseTemplateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """استخدام قالب لإنشاء قيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/use_template.html'  # ✅ محدث
    permission_required = 'accounting.add_journalentry'
    context_object_name = 'object_list'

    def get_queryset(self):
        return JournalEntryTemplate.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).prefetch_related('template_lines__account').order_by('display_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('استخدام قالب لإنشاء قيد'),
            'form': UseTemplateForm(request=self.request),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('قوالب القيود'), 'url': reverse('accounting:template_list')},
                {'title': _('استخدام قالب'), 'url': ''},
            ]
        })
        return context

    def post(self, request, *args, **kwargs):
        form = UseTemplateForm(request.POST, request=request)
        if form.is_valid():
            template = form.cleaned_data['template']

            # إنشاء قيد من القالب
            journal_entry = template.create_journal_entry(
                branch=request.current_branch,
                entry_date=form.cleaned_data['entry_date'],
                description=form.cleaned_data['description'] or template.default_description,
                reference=form.cleaned_data['reference'] or template.default_reference,
                created_by=request.user
            )

            messages.success(request, f'تم إنشاء القيد {journal_entry.number} من القالب بنجاح')
            return redirect('accounting:journal_entry_detail', pk=journal_entry.pk)

        # إذا فشل الـ validation
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
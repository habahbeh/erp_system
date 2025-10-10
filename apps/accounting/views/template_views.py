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


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from apps.core.decorators import permission_required_with_message

class JournalEntryTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة قوالب القيود"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/journal_entry_template_list.html'
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
    template_name = 'accounting/journal/journal_entry_template_form.html'
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
        return reverse('accounting:template_detail', kwargs={'pk': self.object.pk})

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
    template_name = 'accounting/journal/journal_entry_template_detail.html'
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
    template_name = 'accounting/journal/journal_entry_template_form.html'
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
        return reverse('accounting:template_detail', kwargs={'pk': self.object.pk})

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
                {'title': self.object.name, 'url': reverse('accounting:template_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class JournalEntryTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف قالب القيد"""
    model = JournalEntryTemplate
    template_name = 'accounting/journal/journal_entry_template_confirm_delete.html'
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
                {'title': self.object.name, 'url': reverse('accounting:template_detail', kwargs={'pk': self.object.pk})},
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
    template_name = 'accounting/journal/use_template.html'
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


@login_required
@permission_required_with_message('accounting.view_journalentrytemplate')
@require_http_methods(["GET"])
def template_datatable_ajax(request):
    """Ajax endpoint لجدول القوالب"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    entry_type = request.GET.get('entry_type', '')
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')

    try:
        # البحث والفلترة
        queryset = JournalEntryTemplate.objects.filter(
            company=request.current_company
        ).select_related('created_by').prefetch_related('template_lines')

        # تطبيق الفلاتر
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)

        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        if category:
            queryset = queryset.filter(category__icontains=category)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(description__icontains=search_value)
            )

        # الترتيب
        queryset = queryset.order_by('display_order', 'name')

        # العد الإجمالي
        total_records = JournalEntryTemplate.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_journalentrytemplate')
        can_delete = request.user.has_perm('accounting.delete_journalentrytemplate')

        for template in queryset:
            # اسم القالب
            name_html = f'<strong>{template.name}</strong>'
            if template.description:
                desc_truncated = template.description[:50] + ('...' if len(template.description) > 50 else '')
                name_html += f'<br><small class="text-muted">{desc_truncated}</small>'

            # الرمز
            code_html = f'<code>{template.code}</code>' if template.code else '<span class="text-muted">-</span>'

            # النوع
            entry_type_choices = dict(JournalEntryTemplate._meta.get_field('entry_type').choices)
            entry_type_display = entry_type_choices.get(template.entry_type, template.entry_type)
            type_html = f'<span class="badge bg-info">{entry_type_display}</span>'

            # الفئة
            category_html = f'<span class="badge bg-secondary">{template.category}</span>' if template.category else '<span class="text-muted">-</span>'

            # عدد السطور
            lines_count = template.template_lines.count()
            lines_html = f'<span class="badge bg-primary">{lines_count} سطر</span>'

            # الحالة
            status_html = '<span class="badge bg-success">نشط</span>' if template.is_active else '<span class="badge bg-secondary">معطل</span>'

            # أزرار الإجراءات
            actions = []

            actions.append(f'''
                <a href="{reverse('accounting:template_detail', args=[template.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions.append(f'''
                <a href="{reverse('accounting:use_template')}?template={template.pk}" 
                   class="btn btn-outline-success btn-sm" title="استخدام" data-bs-toggle="tooltip">
                    <i class="fas fa-magic"></i>
                </a>
            ''')

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('accounting:template_update', args=[template.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('accounting:template_delete', args=[template.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = '<div class="btn-group btn-group-sm">' + ''.join(actions) + '</div>'

            data.append([
                name_html,
                code_html,
                type_html,
                category_html,
                lines_html,
                status_html,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })
# apps/accounting/views/journal_views.py
"""
Views القيود اليومية - محسنة لسهولة الاستخدام
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.template.loader import render_to_string
import json
from datetime import date, timedelta

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import JournalEntry, JournalEntryLine, JournalEntryTemplate, Account
from ..forms.journal_forms import (
    JournalEntryForm, JournalEntryLineForm, JournalEntryTemplateForm,
    QuickJournalEntryForm, JournalEntryLineFormSet
)
from django.views.generic import FormView
from django.db import transaction


class JournalEntryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة القيود اليومية"""

    model = JournalEntry
    template_name = 'accounting/journal/journal_entry_list.html'
    context_object_name = 'journal_entries'
    permission_required = 'accounting.view_journalentry'
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntry.objects.filter(
            company=self.request.current_company
        ).select_related('fiscal_year', 'period', 'created_by', 'posted_by').prefetch_related('lines')

        # الفلترة
        status = self.request.GET.get('status')
        entry_type = self.request.GET.get('entry_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)

        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(description__icontains=search) |
                Q(reference__icontains=search)
            )

        return queryset.order_by('-entry_date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('القيود اليومية'),
            'can_add': self.request.user.has_perm('accounting.add_journalentry'),
            'can_edit': self.request.user.has_perm('accounting.change_journalentry'),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentry'),
            'status_choices': JournalEntry.STATUS_CHOICES,
            'entry_type_choices': JournalEntry.ENTRY_TYPES,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': ''},
            ]
        })
        return context



class JournalEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء قيد يومية جديد"""

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journal/journal_entry_form.html'
    permission_required = 'accounting.add_journalentry'
    success_url = reverse_lazy('accounting:journal_entry_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        # حفظ القيد
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'  # مسودة افتراضياً

        self.object = form.save()

        # معالجة السطور
        lines_data = self.request.POST.get('lines_data')
        if lines_data:
            try:
                lines = json.loads(lines_data)
                line_number = 1

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

                        # تخطي السطور الفارغة
                        if debit == 0 and credit == 0:
                            continue

                        # إنشاء السطر
                        JournalEntryLine.objects.create(
                            journal_entry=self.object,
                            line_number=line_number,
                            account=account,
                            description=line_data.get('description', self.object.description),
                            debit_amount=debit,
                            credit_amount=credit,
                            currency=account.currency,
                            reference=line_data.get('reference', ''),
                            cost_center_id=line_data.get('cost_center') if line_data.get('cost_center') else None
                        )
                        line_number += 1

                    except Account.DoesNotExist:
                        continue

                # إعادة حساب الإجماليات
                self.object.calculate_totals()

                messages.success(self.request, f'تم إنشاء القيد {self.object.number} بنجاح')

            except json.JSONDecodeError as e:
                messages.error(self.request, f'خطأ في بيانات السطور: {str(e)}')
                self.object.delete()
                return self.form_invalid(form)
        else:
            messages.error(self.request, 'لم يتم إضافة أي سطور للقيد')
            self.object.delete()
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('accounting:journal_entry_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء قيد يومية جديد'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': reverse('accounting:journal_entry_list')},
                {'title': _('إنشاء قيد جديد'), 'url': ''},
            ]
        })
        return context


class JournalEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل قيد يومية"""

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journal/journal_entry_form.html'
    permission_required = 'accounting.change_journalentry'

    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if not self.object.can_edit():
            messages.error(self.request, _('لا يمكن تعديل قيد مرحل'))
            return redirect('accounting:journal_entry_detail', pk=self.object.pk)

        # حفظ القيد
        self.object = form.save()

        # حذف السطور القديمة
        self.object.lines.all().delete()

        # معالجة السطور الجديدة
        lines_data = self.request.POST.get('lines_data')
        if lines_data:
            try:
                lines = json.loads(lines_data)
                line_number = 1

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

                        if debit == 0 and credit == 0:
                            continue

                        JournalEntryLine.objects.create(
                            journal_entry=self.object,
                            line_number=line_number,
                            account=account,
                            description=line_data.get('description', self.object.description),
                            debit_amount=debit,
                            credit_amount=credit,
                            currency=account.currency,
                            reference=line_data.get('reference', ''),
                            cost_center_id=line_data.get('cost_center') if line_data.get('cost_center') else None
                        )
                        line_number += 1

                    except Account.DoesNotExist:
                        continue

                # إعادة حساب الإجماليات
                self.object.calculate_totals()

                messages.success(self.request, f'تم تحديث القيد {self.object.number} بنجاح')

            except json.JSONDecodeError as e:
                messages.error(self.request, f'خطأ في بيانات السطور: {str(e)}')
                return self.form_invalid(form)
        else:
            messages.error(self.request, 'لم يتم إضافة أي سطور للقيد')
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('accounting:journal_entry_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة سطور القيد الموجودة
        existing_lines = []
        for line in self.object.lines.all().order_by('line_number'):
            existing_lines.append({
                'account_id': line.account.id,
                'account_text': f"{line.account.code} - {line.account.name}",
                'description': line.description,
                'debit_amount': str(line.debit_amount),
                'credit_amount': str(line.credit_amount),
                'reference': line.reference,
                'cost_center_id': line.cost_center.id if line.cost_center else None,
                'cost_center_text': f"{line.cost_center.code} - {line.cost_center.name}" if line.cost_center else None
            })

        context.update({
            'title': f'تعديل القيد {self.object.number}',
            'existing_lines': json.dumps(existing_lines),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': reverse('accounting:journal_entry_list')},
                {'title': f'تعديل {self.object.number}', 'url': ''},
            ]
        })
        return context


class JournalEntryDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل القيد"""

    model = JournalEntry
    template_name = 'accounting/journal/journal_entry_detail.html'
    context_object_name = 'journal_entry'
    permission_required = 'accounting.view_journalentry'

    def get_queryset(self):
        return JournalEntry.objects.filter(
            company=self.request.current_company
        ).select_related('fiscal_year', 'period', 'created_by', 'posted_by').prefetch_related('lines__account')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'القيد {self.object.number}',
            'can_edit': self.request.user.has_perm('accounting.change_journalentry') and self.object.can_edit(),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentry') and self.object.can_edit(),
            'can_post': self.request.user.has_perm('accounting.change_journalentry') and self.object.can_post(),
            'can_unpost': self.request.user.has_perm('accounting.change_journalentry') and self.object.can_unpost(),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': reverse('accounting:journal_entry_list')},
                {'title': self.object.number, 'url': ''},
            ]
        })
        return context


class JournalEntryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف قيد يومية"""

    model = JournalEntry
    template_name = 'accounting/journal/journal_entry_confirm_delete.html'
    permission_required = 'accounting.delete_journalentry'
    success_url = reverse_lazy('accounting:journal_entry_list')

    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if not self.object.can_edit():
            messages.error(request, _('لا يمكن حذف قيد مرحل'))
            return redirect('accounting:journal_entry_detail', pk=self.object.pk)

        messages.success(request, f'تم حذف القيد {self.object.number} بنجاح')
        return super().delete(request, *args, **kwargs)


# Views للقيد السريع
class QuickJournalEntryView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FormView):
    """إنشاء قيد سريع (سطرين فقط)"""

    form_class = QuickJournalEntryForm
    template_name = 'accounting/journal/quick_journal_entry.html'
    permission_required = 'accounting.add_journalentry'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        try:
            # الحصول على البيانات
            debit_account = form.cleaned_data['debit_account']
            credit_account = form.cleaned_data['credit_account']
            amount = form.cleaned_data['amount']

            # إنشاء القيد
            journal_entry = JournalEntry.objects.create(
                company=self.request.current_company,
                branch=self.request.current_branch,
                entry_date=form.cleaned_data['entry_date'],
                description=form.cleaned_data['description'],
                reference=form.cleaned_data.get('reference', ''),
                entry_type='manual',
                status='draft',
                created_by=self.request.user
            )

            # سطر المدين
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=1,
                account=debit_account,
                description=form.cleaned_data['description'],
                debit_amount=amount,
                credit_amount=0,
                currency=debit_account.currency,
                reference=form.cleaned_data.get('reference', '')
            )

            # سطر الدائن
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=2,
                account=credit_account,
                description=form.cleaned_data['description'],
                debit_amount=0,
                credit_amount=amount,
                currency=credit_account.currency,
                reference=form.cleaned_data.get('reference', '')
            )

            # إعادة حساب الإجماليات
            journal_entry.calculate_totals()

            messages.success(self.request, f'تم إنشاء القيد {journal_entry.number} بنجاح')
            return redirect('accounting:journal_entry_detail', pk=journal_entry.pk)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(self.request, f'خطأ في إنشاء القيد: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # طباعة الأخطاء للتشخيص
        print("Form Errors:", form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('قيد سريع'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': reverse('accounting:journal_entry_list')},
                {'title': _('قيد سريع'), 'url': ''},
            ]
        })
        return context

# Ajax Views
@login_required
@permission_required_with_message('accounting.view_journalentry')
@require_http_methods(["GET"])
def journal_entry_datatable_ajax(request):
    """Ajax endpoint لجدول القيود"""

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
    status = request.GET.get('status', '')
    entry_type = request.GET.get('entry_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        # البحث والفلترة
        queryset = JournalEntry.objects.filter(
            company=request.current_company
        ).select_related('created_by', 'posted_by')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)

        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(number__icontains=search_value) |
                Q(description__icontains=search_value) |
                Q(reference__icontains=search_value)
            )

        # الترتيب
        queryset = queryset.order_by('-entry_date', '-number')

        # العد الإجمالي
        total_records = JournalEntry.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_journalentry')
        can_delete = request.user.has_perm('accounting.delete_journalentry')

        for entry in queryset:
            # حالة القيد
            if entry.status == 'draft':
                status_badge = '<span class="badge bg-warning">مسودة</span>'
            elif entry.status == 'posted':
                status_badge = '<span class="badge bg-success">مرحل</span>'
            else:
                status_badge = '<span class="badge bg-danger">ملغي</span>'

            # نوع القيد
            entry_type_display = dict(JournalEntry.ENTRY_TYPES).get(entry.entry_type, entry.entry_type)

            # أزرار الإجراءات
            actions = []

            # رابط العرض
            actions.append(f'''
                <a href="{reverse('accounting:journal_entry_detail', args=[entry.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            # رابط التعديل
            if can_edit and entry.can_edit():
                actions.append(f'''
                    <a href="{reverse('accounting:journal_entry_update', args=[entry.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            # زر الترحيل/إلغاء الترحيل
            if can_edit:
                if entry.can_post():
                    actions.append(f'''
                        <button type="button" class="btn btn-outline-success btn-sm" 
                                onclick="postJournalEntry({entry.pk})" title="ترحيل" data-bs-toggle="tooltip">
                            <i class="fas fa-check"></i>
                        </button>
                    ''')
                elif entry.can_unpost():
                    actions.append(f'''
                        <button type="button" class="btn btn-outline-warning btn-sm" 
                                onclick="unpostJournalEntry({entry.pk})" title="إلغاء ترحيل" data-bs-toggle="tooltip">
                            <i class="fas fa-undo"></i>
                        </button>
                    ''')

            # رابط الحذف
            if can_delete and entry.can_edit():
                actions.append(f'''
                    <button type="button" class="btn btn-outline-danger btn-sm" 
                            onclick="deleteJournalEntry({entry.pk})" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </button>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                entry.number,
                entry.entry_date.strftime('%Y-%m-%d'),
                entry_type_display,
                entry.description[:50] + ('...' if len(entry.description) > 50 else ''),
                f"{entry.total_debit:,.2f}",
                status_badge,
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


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def account_autocomplete(request):
    """البحث التلقائي للحسابات"""

    query = request.GET.get('term', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse([], safe=False)

    accounts = Account.objects.filter(
        company=request.current_company,
        accept_entries=True,
        is_suspended=False
    ).filter(
        Q(code__icontains=query) | Q(name__icontains=query)
    )[:20]

    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'text': f"{account.code} - {account.name}",
            'code': account.code,
            'name': account.name
        })

    return JsonResponse(results, safe=False)


@login_required
@permission_required_with_message('accounting.change_journalentry')
@require_http_methods(["POST"])
def post_journal_entry(request, pk):
    """ترحيل القيد"""

    try:
        journal_entry = get_object_or_404(
            JournalEntry,
            pk=pk,
            company=request.current_company
        )

        if not journal_entry.can_post():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن ترحيل هذا القيد'
            })

        journal_entry.post(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل القيد {journal_entry.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل القيد: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_journalentry')
@require_http_methods(["POST"])
def unpost_journal_entry(request, pk):
    """إلغاء ترحيل القيد"""

    try:
        journal_entry = get_object_or_404(
            JournalEntry,
            pk=pk,
            company=request.current_company
        )

        if not journal_entry.can_unpost():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن إلغاء ترحيل هذا القيد'
            })

        journal_entry.unpost()

        return JsonResponse({
            'success': True,
            'message': f'تم إلغاء ترحيل القيد {journal_entry.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إلغاء ترحيل القيد: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.view_journalentrytemplate')
@require_http_methods(["GET"])
def get_template_lines(request, template_id):
    """الحصول على سطور القالب"""

    try:
        template = get_object_or_404(
            JournalEntryTemplate,
            pk=template_id,
            company=request.current_company
        )

        lines = []
        for line in template.template_lines.all().order_by('line_number'):
            lines.append({
                'account_id': line.account.id,
                'account_text': f"{line.account.code} - {line.account.name}",
                'description': line.description,
                'debit_amount': str(line.debit_amount),
                'credit_amount': str(line.credit_amount),
                'reference': line.reference
            })

        return JsonResponse({
            'success': True,
            'lines': lines,
            'description': template.default_description
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في تحميل القالب: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.add_journalentry')
@require_http_methods(["POST"])
def copy_journal_entry(request, pk):
    """نسخ قيد يومية"""

    try:
        # الحصول على القيد الأصلي
        original_entry = get_object_or_404(
            JournalEntry,
            pk=pk,
            company=request.current_company
        )

        # إنشاء نسخة جديدة
        with transaction.atomic():
            # نسخ القيد
            new_entry = JournalEntry.objects.create(
                company=request.current_company,
                branch=request.current_branch,
                entry_date=date.today(),  # تاريخ اليوم
                entry_type=original_entry.entry_type,
                description=f"{original_entry.description} (نسخة)",
                reference=f"{original_entry.reference}_COPY" if original_entry.reference else "",
                notes=original_entry.notes,
                template=original_entry.template,
                status='draft',  # مسودة
                created_by=request.user
            )

            # نسخ السطور
            for line in original_entry.lines.all().order_by('line_number'):
                JournalEntryLine.objects.create(
                    journal_entry=new_entry,
                    line_number=line.line_number,
                    account=line.account,
                    description=line.description,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    currency=line.currency,
                    exchange_rate=line.exchange_rate,
                    reference=line.reference,
                    cost_center=line.cost_center,
                    partner_type=line.partner_type,
                    partner_id=line.partner_id
                )

            # إعادة حساب الإجماليات
            new_entry.calculate_totals()

        return JsonResponse({
            'success': True,
            'message': f'تم نسخ القيد بنجاح',
            'redirect_url': reverse('accounting:journal_entry_detail', kwargs={'pk': new_entry.pk})
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في نسخ القيد: {str(e)}'
        }, status=500)
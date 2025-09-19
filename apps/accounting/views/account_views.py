# apps/accounting/views/account_views.py
"""
Account Views - إدارة الحسابات ودليل الحسابات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.db.models import Q, Count, Sum, F
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message, company_required
from ..models import Account, AccountType
from ..forms.account_forms import AccountForm, AccountFilterForm


class AccountListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الحسابات"""

    template_name = 'accounting/accounts/account_list.html'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة مع تحسين الأداء
        company = self.request.current_company
        stats = Account.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_suspended=False)),
            suspended=Count('id', filter=Q(is_suspended=True)),
            parent_accounts=Count('id', filter=Q(children__isnull=False)),
            leaf_accounts=Count('id', filter=Q(children__isnull=True)),
            total_opening_balance=Sum('opening_balance')
        )

        context.update({
            'title': _('دليل الحسابات'),
            'can_add': self.request.user.has_perm('accounting.add_account'),
            'can_edit': self.request.user.has_perm('accounting.change_account'),
            'can_delete': self.request.user.has_perm('accounting.delete_account'),
            'can_export': self.request.user.has_perm('accounting.view_account'),
            'can_import': self.request.user.has_perm('accounting.add_account'),
            'add_url': reverse('accounting:account_create'),
            'export_url': reverse('accounting:export_accounts'),
            'import_url': reverse('accounting:import_accounts'),
            'hierarchy_url': reverse('accounting:account_hierarchy_ajax'),
            'account_types': AccountType.objects.all(),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('دليل الحسابات'), 'url': ''}
            ],
        })
        return context


class AccountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء حساب جديد"""

    model = Account
    form_class = AccountForm
    template_name = 'accounting/accounts/account_form.html'
    permission_required = 'accounting.add_account'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء الحساب {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        if 'save_and_add' in self.request.POST:
            return reverse('accounting:account_create')
        return reverse('accounting:account_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء حساب جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('دليل الحسابات'), 'url': reverse('accounting:account_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AccountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل حساب"""

    model = Account
    form_class = AccountForm
    template_name = 'accounting/accounts/account_form.html'
    permission_required = 'accounting.change_account'

    def get_queryset(self):
        return Account.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        account = form.instance

        # التحقق الإضافي قبل الحفظ
        if account.children.exists() and account.accept_entries:
            account.accept_entries = False
            messages.warning(
                self.request,
                'تم تعديل "يقبل قيود مباشرة" تلقائياً لأن الحساب له حسابات فرعية'
            )

        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث الحساب {account.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:account_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الحساب: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('دليل الحسابات'), 'url': reverse('accounting:account_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''}
            ],
        })
        return context


class AccountDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل الحساب"""

    model = Account
    template_name = 'accounting/accounts/account_detail.html'
    context_object_name = 'account'
    permission_required = 'accounting.view_account'

    def get_queryset(self):
        return Account.objects.filter(
            company=self.request.current_company
        ).select_related('account_type', 'parent', 'currency').prefetch_related('children')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.object

        # إحصائيات الحساب
        account_stats = {
            'children_count': account.children.count(),
            'current_balance': account.get_balance(),  # سيتم تطويرها لاحقاً
            'entries_count': 0,  # سيتم تطويرها مع القيود
        }

        context.update({
            'title': f'تفاصيل الحساب: {account.name}',
            'can_edit': self.request.user.has_perm('accounting.change_account'),
            'can_delete': self.request.user.has_perm('accounting.delete_account') and account.children.count() == 0,
            'account_stats': account_stats,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('دليل الحسابات'), 'url': reverse('accounting:account_list')},
                {'title': account.name, 'url': ''}
            ],
        })
        return context


class AccountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف حساب"""

    model = Account
    template_name = 'accounting/accounts/account_confirm_delete.html'
    permission_required = 'accounting.delete_account'
    success_url = reverse_lazy('accounting:account_list')

    def get_queryset(self):
        return Account.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'حذف الحساب: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('دليل الحسابات'), 'url': reverse('accounting:account_list')},
                {'title': f'حذف: {self.object.name}', 'url': ''}
            ],
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود حسابات فرعية
        if self.object.children.exists():
            messages.error(request, 'لا يمكن حذف الحساب لوجود حسابات فرعية')
            return redirect('accounting:account_list')

        # التحقق من وجود قيود محاسبية (سيتم تفعيلها لاحقاً)
        # if hasattr(self.object, 'journal_entry_lines') and self.object.journal_entry_lines.exists():
        #     messages.error(request, 'لا يمكن حذف الحساب لوجود قيود محاسبية')
        #     return redirect('accounting:account_list')

        account_name = self.object.name
        messages.success(request, f'تم حذف الحساب {account_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views
@company_required
@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def account_datatable_ajax(request):
    """Ajax endpoint لجدول الحسابات"""

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
    account_type_id = request.GET.get('account_type', '')
    is_active = request.GET.get('is_active', '')
    has_children = request.GET.get('has_children', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        # البحث والفلترة مع تحسين الأداء
        queryset = Account.objects.filter(
            company=request.current_company
        ).select_related('account_type', 'parent', 'currency').annotate(
            children_count=Count('children')
        )

        # تطبيق الفلاتر
        if account_type_id:
            queryset = queryset.filter(account_type_id=account_type_id)

        if is_active == '1':
            queryset = queryset.filter(is_suspended=False)
        elif is_active == '0':
            queryset = queryset.filter(is_suspended=True)

        if has_children == '1':
            queryset = queryset.filter(children_count__gt=0)
        elif has_children == '0':
            queryset = queryset.filter(children_count=0)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(code__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(name_en__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['code', 'name', 'account_type__name', 'parent__name', 'opening_balance', 'is_suspended']
            if int(order_column) < len(columns):
                order_field = columns[int(order_column)]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('code')

        # العد الإجمالي
        total_records = Account.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_account')
        can_delete = request.user.has_perm('accounting.delete_account')
        can_view = request.user.has_perm('accounting.view_account')

        for account in queryset:
            # حالة الحساب
            if account.is_suspended:
                status_badge = '<span class="badge bg-danger">موقوف</span>'
            elif not account.accept_entries:
                status_badge = '<span class="badge bg-warning">حساب أب</span>'
            else:
                status_badge = '<span class="badge bg-success">نشط</span>'

            # الحساب الأب
            parent_display = ''
            if account.parent:
                parent_display = f'<small class="text-muted">{account.parent.code}</small><br>{account.parent.name}'
            else:
                parent_display = '-'

            # عدد الحسابات الفرعية
            children_info = ''
            if account.children_count > 0:
                children_info = f' <span class="badge bg-info">{account.children_count} فرعي</span>'

            # اسم الحساب مع المستوى الهرمي
            indent = '&nbsp;&nbsp;&nbsp;' * (account.level - 1)
            account_name = f'{indent}{account.name}{children_info}'

            # أزرار الإجراءات
            actions = []

            # عرض التفاصيل
            if can_view:
                actions.append(f'''
                    <a href="{reverse('accounting:account_detail', args=[account.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('accounting:account_update', args=[account.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and account.children_count == 0:
                actions.append(f'''
                    <a href="{reverse('accounting:account_delete', args=[account.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                account.code,
                account_name,
                account.account_type.name,
                parent_display,
                f"{account.opening_balance:,.3f}",
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
            'error': str(e)
        })


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def account_hierarchy_ajax(request):
    """Ajax endpoint لعرض هيكل الحسابات الهرمي"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'})

    try:
        def build_tree(parent=None, level=0):
            accounts = Account.objects.filter(
                company=request.current_company,
                parent=parent
            ).select_related('account_type').order_by('code')

            result = []
            for account in accounts:
                children = build_tree(account, level + 1) if account.children.exists() else []

                item = {
                    'id': account.pk,
                    'code': account.code,
                    'name': account.name,
                    'type': account.account_type.name,
                    'level': level,
                    'has_children': account.children.exists(),
                    'is_suspended': account.is_suspended,
                    'accept_entries': account.accept_entries,
                    'opening_balance': float(account.opening_balance),
                    'children': children
                }
                result.append(item)
            return result

        tree = build_tree()
        return JsonResponse({'success': True, 'tree': tree})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def account_search_ajax(request):
    """البحث السريع في الحسابات للـ autocomplete"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse([])

    query = request.GET.get('term', '').strip()
    if len(query) < 2:
        return JsonResponse([])

    # فلترة إضافية
    only_leaf = request.GET.get('only_leaf', '') == '1'  # حسابات فرعية فقط
    only_active = request.GET.get('only_active', '') == '1'  # حسابات نشطة فقط

    accounts = Account.objects.filter(
        company=request.current_company
    ).filter(
        Q(code__icontains=query) | Q(name__icontains=query)
    )

    if only_leaf:
        accounts = accounts.filter(children__isnull=True, accept_entries=True)

    if only_active:
        accounts = accounts.filter(is_suspended=False)

    accounts = accounts.select_related('account_type')[:20]

    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'text': f"{account.code} - {account.name}",
            'code': account.code,
            'name': account.name,
            'type': account.account_type.name,
            'level': account.level,
            'accept_entries': account.accept_entries
        })

    return JsonResponse(results, safe=False)


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def account_stats_ajax(request):
    """Ajax endpoint لإحصائيات الحسابات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'})

    try:
        company = request.current_company

        # إحصائيات عامة
        stats = Account.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_suspended=False)),
            suspended=Count('id', filter=Q(is_suspended=True)),
            parent_accounts=Count('id', filter=Q(children__isnull=False)),
            leaf_accounts=Count('id', filter=Q(children__isnull=True)),
            total_opening_balance=Sum('opening_balance')
        )

        # إحصائيات حسب نوع الحساب
        by_type = {}
        for account_type in AccountType.objects.all():
            count = Account.objects.filter(
                company=company,
                account_type=account_type
            ).count()
            by_type[account_type.name] = count

        # إحصائيات حسب المستوى
        by_level = {}
        for level in range(1, 5):  # حتى 4 مستويات
            count = Account.objects.filter(
                company=company,
                level=level
            ).count()
            if count > 0:
                by_level[f'المستوى {level}'] = count

        return JsonResponse({
            'success': True,
            'stats': stats,
            'by_type': by_type,
            'by_level': by_level
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
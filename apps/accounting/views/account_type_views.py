# apps/accounting/views/account_type_views.py
"""
Account Type Views - إدارة أنواع الحسابات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import AccountType
from ..forms.account_type_forms import AccountTypeForm


class AccountTypeListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """قائمة أنواع الحسابات"""

    template_name = 'accounting/account_types/account_type_list.html'
    permission_required = 'accounting.view_accounttype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        total_types = AccountType.objects.count()
        assets_types = AccountType.objects.filter(type_category='assets').count()
        liabilities_types = AccountType.objects.filter(type_category='liabilities').count()

        context.update({
            'title': _('أنواع الحسابات'),
            'can_add': self.request.user.has_perm('accounting.add_accounttype'),
            'can_edit': self.request.user.has_perm('accounting.change_accounttype'),
            'can_delete': self.request.user.has_perm('accounting.delete_accounttype'),
            'can_export': self.request.user.has_perm('accounting.view_accounttype'),
            'can_import': self.request.user.has_perm('accounting.add_accounttype'),
            'add_url': reverse('accounting:account_type_create'),
            'export_url': reverse('accounting:export_account_types'),
            'import_url': reverse('accounting:import_account_types'),
            'total_types': total_types,
            'assets_types': assets_types,
            'liabilities_types': liabilities_types,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('أنواع الحسابات'), 'url': ''}
            ],
        })
        return context


class AccountTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إنشاء نوع حساب جديد"""

    model = AccountType
    form_class = AccountTypeForm
    template_name = 'accounting/account_types/account_type_form.html'
    permission_required = 'accounting.add_accounttype'
    success_url = reverse_lazy('accounting:account_type_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم إنشاء نوع الحساب بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء نوع حساب جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('أنواع الحسابات'), 'url': reverse('accounting:account_type_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AccountTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل نوع حساب"""

    model = AccountType
    form_class = AccountTypeForm
    template_name = 'accounting/account_types/account_type_form.html'
    permission_required = 'accounting.change_accounttype'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم تحديث نوع الحساب بنجاح'))
        return response

    def get_success_url(self):
        return reverse('accounting:account_type_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('أنواع الحسابات'), 'url': reverse('accounting:account_type_list')},
                {'title': f'تعديل {self.object.name}', 'url': ''}
            ],
        })
        return context


class AccountTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف نوع حساب"""

    model = AccountType
    template_name = 'accounting/account_types/account_type_confirm_delete.html'
    permission_required = 'accounting.delete_accounttype'
    success_url = reverse_lazy('accounting:account_type_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'حذف نوع الحساب: {self.object.name}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('أنواع الحسابات'), 'url': reverse('accounting:account_type_list')},
                {'title': f'حذف {self.object.name}', 'url': ''}
            ],
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من وجود حسابات مرتبطة
        if self.object.accounts.exists():
            messages.error(request, _('لا يمكن حذف نوع الحساب لوجود حسابات مرتبطة'))
            return redirect('accounting:account_type_list')

        type_name = self.object.name
        messages.success(request, f'تم حذف نوع الحساب {type_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views
@login_required
@permission_required_with_message('accounting.view_accounttype')
@require_http_methods(["GET"])
def account_type_datatable_ajax(request):
    """Ajax endpoint لجدول أنواع الحسابات"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    type_category = request.GET.get('type_category', '')
    normal_balance = request.GET.get('normal_balance', '')

    try:
        # البحث والفلترة مع annotations للأداء
        queryset = AccountType.objects.annotate(
            accounts_count=Count('accounts')
        )

        # تطبيق الفلاتر
        if type_category:
            queryset = queryset.filter(type_category=type_category)

        if normal_balance:
            queryset = queryset.filter(normal_balance=normal_balance)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['code', 'name', 'type_category', 'normal_balance', 'accounts_count']
            if int(order_column) < len(columns):
                order_field = columns[int(order_column)]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('code')

        # العد الإجمالي
        total_records = AccountType.objects.count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_accounttype')
        can_delete = request.user.has_perm('accounting.delete_accounttype')

        for account_type in queryset:
            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('accounting:account_type_update', args=[account_type.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and account_type.accounts_count == 0:
                actions.append(f'''
                    <a href="{reverse('accounting:account_type_delete', args=[account_type.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            # تحديد لون badge حسب النوع
            category_badges = {
                'assets': '<span class="badge bg-success">أصول</span>',
                'liabilities': '<span class="badge bg-warning">خصوم</span>',
                'equity': '<span class="badge bg-info">حقوق ملكية</span>',
                'revenue': '<span class="badge bg-primary">إيرادات</span>',
                'expenses': '<span class="badge bg-danger">مصروفات</span>',
            }

            balance_badges = {
                'debit': '<span class="badge bg-success">مدين</span>',
                'credit': '<span class="badge bg-primary">دائن</span>',
            }

            data.append([
                account_type.code,
                account_type.name,
                category_badges.get(account_type.type_category, account_type.get_type_category_display()),
                balance_badges.get(account_type.normal_balance, account_type.get_normal_balance_display()),
                f'<span class="badge bg-secondary">{account_type.accounts_count}</span>',
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
@permission_required_with_message('accounting.view_accounttype')
@require_http_methods(["GET"])
def account_type_stats_ajax(request):
    """Ajax endpoint لإحصائيات أنواع الحسابات"""

    try:
        stats = {
            'total': AccountType.objects.count(),
            'by_category': {},
            'by_balance': {}
        }

        # إحصائيات حسب التصنيف
        for category, display in AccountType.ACCOUNT_TYPES:
            count = AccountType.objects.filter(type_category=category).count()
            stats['by_category'][category] = {
                'count': count,
                'display': display
            }

        # إحصائيات حسب الرصيد الطبيعي
        for balance in ['debit', 'credit']:
            count = AccountType.objects.filter(normal_balance=balance).count()
            stats['by_balance'][balance] = count

        return JsonResponse({'success': True, 'stats': stats})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
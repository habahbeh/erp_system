# apps/accounting/views/fiscal_views.py
"""
واجهات السنوات والفترات المالية
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message

from ..models.account_models import CostCenter
from ..models import FiscalYear, AccountingPeriod
from ..forms.fiscal_forms import (FiscalYearForm, FiscalYearFilterForm, CreatePeriodsForm,
                                 AccountingPeriodForm, AccountingPeriodFilterForm, PeriodClosingForm,
                                 CostCenterForm, CostCenterFilterForm)

class FiscalYearListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة السنوات المالية"""

    model = FiscalYear
    template_name = 'accounting/fiscal/fiscal_year_list.html'
    context_object_name = 'fiscal_years'
    permission_required = 'accounting.view_fiscalyear'
    paginate_by = 25

    def get_queryset(self):
        queryset = FiscalYear.objects.filter(
            company=self.request.current_company
        ).order_by('-start_date')

        # تطبيق الفلاتر
        form = FiscalYearFilterForm(self.request.GET, request=self.request)
        if form.is_valid():
            if form.cleaned_data.get('status') == 'active':
                queryset = queryset.filter(is_closed=False)
            elif form.cleaned_data.get('status') == 'closed':
                queryset = queryset.filter(is_closed=True)

            if form.cleaned_data.get('year'):
                queryset = queryset.filter(start_date__year=form.cleaned_data['year'])

            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(code__icontains=search)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        stats = FiscalYear.objects.filter(
            company=self.request.current_company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_closed=False)),
            closed=Count('id', filter=Q(is_closed=True))
        )

        context.update({
            'title': _('السنوات المالية'),
            'filter_form': FiscalYearFilterForm(self.request.GET, request=self.request),
            'can_add': self.request.user.has_perm('accounting.add_fiscalyear'),
            'can_edit': self.request.user.has_perm('accounting.change_fiscalyear'),
            'can_delete': self.request.user.has_perm('accounting.delete_fiscalyear'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('السنوات المالية'), 'url': ''},
            ]
        })
        return context


class FiscalYearCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سنة مالية جديدة"""

    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal/fiscal_year_form.html'
    permission_required = 'accounting.add_fiscalyear'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء السنة المالية {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:fiscal_year_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء سنة مالية جديدة'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('السنوات المالية'), 'url': reverse('accounting:fiscal_year_list')},
                {'title': _('إنشاء جديد'), 'url': ''},
            ]
        })
        return context


class FiscalYearDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل السنة المالية"""

    model = FiscalYear
    template_name = 'accounting/fiscal/fiscal_year_detail.html'
    context_object_name = 'fiscal_year'
    permission_required = 'accounting.view_fiscalyear'

    def get_queryset(self):
        return FiscalYear.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الفترات المحاسبية لهذه السنة
        periods = self.object.periods.all().order_by('start_date')

        # إحصائيات
        # حساب عدد الأيام بين التاريخين
        date_diff = self.object.end_date - self.object.start_date
        days_count = date_diff.days + 1

        stats = {
            'periods_count': periods.count(),
            'active_periods': periods.filter(is_closed=False).count(),
            'closed_periods': periods.filter(is_closed=True).count(),
            'days_count': days_count  # عدد صحيح بالأيام
        }

        context.update({
            'title': f'تفاصيل السنة المالية: {self.object.name}',
            'periods': periods,
            'stats': stats,
            'can_edit': self.request.user.has_perm('accounting.change_fiscalyear') and not self.object.is_closed,
            'can_delete': self.request.user.has_perm('accounting.delete_fiscalyear') and not self.object.is_closed,
            'can_create_periods': self.request.user.has_perm(
                'accounting.add_accountingperiod') and not periods.exists(),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('السنوات المالية'), 'url': reverse('accounting:fiscal_year_list')},
                {'title': self.object.name, 'url': ''},
            ]
        })
        return context


class FiscalYearUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل السنة المالية"""

    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal/fiscal_year_form.html'
    permission_required = 'accounting.change_fiscalyear'

    def get_queryset(self):
        return FiscalYear.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if self.object.is_closed:
            messages.error(self.request, 'لا يمكن تعديل سنة مالية مقفلة')
            return redirect('accounting:fiscal_year_detail', pk=self.object.pk)

        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث السنة المالية {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:fiscal_year_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل السنة المالية: {self.object.name}',
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('السنوات المالية'), 'url': reverse('accounting:fiscal_year_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''},
            ]
        })
        return context


class FiscalYearDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف السنة المالية"""

    model = FiscalYear
    template_name = 'accounting/fiscal/fiscal_year_confirm_delete.html'
    permission_required = 'accounting.delete_fiscalyear'
    success_url = reverse_lazy('accounting:fiscal_year_list')

    def get_queryset(self):
        return FiscalYear.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.is_closed:
            messages.error(request, 'لا يمكن حذف سنة مالية مقفلة')
            return redirect('accounting:fiscal_year_detail', pk=self.object.pk)

        if self.object.periods.exists():
            messages.error(request, 'لا يمكن حذف السنة المالية لوجود فترات محاسبية مرتبطة')
            return redirect('accounting:fiscal_year_detail', pk=self.object.pk)

        fiscal_year_name = self.object.name
        messages.success(request, f'تم حذف السنة المالية {fiscal_year_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views
@login_required
@permission_required_with_message('accounting.view_fiscalyear')
@require_http_methods(["GET"])
def fiscal_year_datatable_ajax(request):
    """Ajax endpoint لجدول السنوات المالية"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    # ✅ إذا كان الطلب لجلب قائمة السنوات للفلتر
    if request.GET.get('get_years'):
        years = FiscalYear.objects.filter(
            company=request.current_company
        ).dates('start_date', 'year', order='DESC')

        years_list = [year.year for year in years]
        return JsonResponse({'years': years_list})

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    status = request.GET.get('status', '')
    year = request.GET.get('year', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        # البحث والفلترة
        queryset = FiscalYear.objects.filter(
            company=request.current_company
        ).annotate(
            periods_count=Count('periods')
        )

        # الفلاتر
        if status == 'active':
            queryset = queryset.filter(is_closed=False)
        elif status == 'closed':
            queryset = queryset.filter(is_closed=True)

        if year:
            queryset = queryset.filter(start_date__year=year)

        # البحث
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['code', 'name', 'start_date', 'end_date', None, None, 'is_closed']
            col_index = int(order_column)
            if col_index < len(columns) and columns[col_index]:
                order_field = columns[col_index]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-start_date')

        # العدد الإجمالي
        total_records = FiscalYear.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_fiscalyear')
        can_delete = request.user.has_perm('accounting.delete_fiscalyear')

        for fiscal_year in queryset:
            # حالة السنة
            status_badge = '<span class="badge bg-success">نشطة</span>' if not fiscal_year.is_closed else '<span class="badge bg-danger">مقفلة</span>'

            # المدة
            duration_days = (fiscal_year.end_date - fiscal_year.start_date).days + 1
            duration_badge = f'<span class="badge bg-info">{duration_days}</span>'

            # عدد الفترات
            periods_badge = f'<span class="badge bg-secondary">{fiscal_year.periods_count}</span>'

            # الاسم مع رابط
            name_link = f'<a href="{reverse("accounting:fiscal_year_detail", args=[fiscal_year.pk])}" class="text-decoration-none fw-bold">{fiscal_year.name}</a>'

            # أزرار الإجراءات
            actions = []

            actions.append(f'''
                <a href="{reverse('accounting:fiscal_year_detail', args=[fiscal_year.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if not fiscal_year.is_closed and can_edit:
                actions.append(f'''
                    <a href="{reverse('accounting:fiscal_year_update', args=[fiscal_year.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if not fiscal_year.periods.exists() and can_delete:
                actions.append(f'''
                    <button type="button" class="btn btn-outline-danger btn-sm" 
                            onclick="deleteFiscalYear({fiscal_year.pk}, '{fiscal_year.name}')" 
                            title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </button>
                ''')

            actions_html = ' '.join(actions)

            data.append([
                f'<code class="text-primary">{fiscal_year.code}</code>',
                name_link,
                fiscal_year.start_date.strftime('%Y/%m/%d'),
                fiscal_year.end_date.strftime('%Y/%m/%d'),
                duration_badge,
                periods_badge,
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
@permission_required_with_message('accounting.add_accountingperiod')
@require_http_methods(["POST"])
def create_periods_ajax(request, fiscal_year_id):
    """إنشاء فترات محاسبية تلقائياً للسنة المالية"""

    try:
        fiscal_year = get_object_or_404(
            FiscalYear,
            pk=fiscal_year_id,
            company=request.current_company
        )

        if fiscal_year.periods.exists():
            return JsonResponse({
                'success': False,
                'message': 'توجد فترات محاسبية لهذه السنة مسبقاً'
            })

        form = CreatePeriodsForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'بيانات النموذج غير صحيحة'
            })

        period_type = form.cleaned_data['period_type']
        create_adjustment = form.cleaned_data['create_adjustment_period']

        with transaction.atomic():
            periods_created = []
            start_date = fiscal_year.start_date
            end_date = fiscal_year.end_date

            if period_type == 'monthly':
                # إنشاء 12 فترة شهرية
                current_date = start_date
                month_num = 1

                while current_date <= end_date:
                    month_end = min(
                        current_date + relativedelta(months=1) - timedelta(days=1),
                        end_date
                    )

                    period = AccountingPeriod.objects.create(
                        company=request.current_company,
                        fiscal_year=fiscal_year,
                        name=f'الشهر {month_num:02d} - {current_date.strftime("%B %Y")}',
                        start_date=current_date,
                        end_date=month_end,
                        created_by=request.user
                    )
                    periods_created.append(period.name)

                    current_date = month_end + timedelta(days=1)
                    month_num += 1

            elif period_type == 'quarterly':
                # إنشاء 4 فترات ربع سنوية
                quarter_months = [
                    (1, 3, 'الربع الأول'),
                    (4, 6, 'الربع الثاني'),
                    (7, 9, 'الربع الثالث'),
                    (10, 12, 'الربع الرابع')
                ]

                for start_month, end_month, quarter_name in quarter_months:
                    quarter_start = date(start_date.year, start_month, 1)
                    quarter_end = date(start_date.year, end_month, 1) + relativedelta(months=1) - timedelta(days=1)

                    # تعديل التواريخ لتكون داخل السنة المالية
                    quarter_start = max(quarter_start, start_date)
                    quarter_end = min(quarter_end, end_date)

                    if quarter_start <= end_date:
                        period = AccountingPeriod.objects.create(
                            company=request.current_company,
                            fiscal_year=fiscal_year,
                            name=f'{quarter_name} {start_date.year}',
                            start_date=quarter_start,
                            end_date=quarter_end,
                            created_by=request.user
                        )
                        periods_created.append(period.name)

            elif period_type == 'semi_annual':
                # إنشاء فترتين نصف سنويتين
                mid_date = start_date + relativedelta(months=6)

                # النصف الأول
                period1 = AccountingPeriod.objects.create(
                    company=request.current_company,
                    fiscal_year=fiscal_year,
                    name=f'النصف الأول {start_date.year}',
                    start_date=start_date,
                    end_date=mid_date - timedelta(days=1),
                    created_by=request.user
                )
                periods_created.append(period1.name)

                # النصف الثاني
                period2 = AccountingPeriod.objects.create(
                    company=request.current_company,
                    fiscal_year=fiscal_year,
                    name=f'النصف الثاني {start_date.year}',
                    start_date=mid_date,
                    end_date=end_date,
                    created_by=request.user
                )
                periods_created.append(period2.name)

            elif period_type == 'annual':
                # إنشاء فترة سنوية واحدة
                period = AccountingPeriod.objects.create(
                    company=request.current_company,
                    fiscal_year=fiscal_year,
                    name=f'السنة الكاملة {start_date.year}',
                    start_date=start_date,
                    end_date=end_date,
                    created_by=request.user
                )
                periods_created.append(period.name)

            # إنشاء فترة التسويات إذا طُلبت
            if create_adjustment:
                adjustment_period = AccountingPeriod.objects.create(
                    company=request.current_company,
                    fiscal_year=fiscal_year,
                    name=f'فترة التسويات {start_date.year}',
                    start_date=end_date,
                    end_date=end_date,
                    is_adjustment=True,
                    created_by=request.user
                )
                periods_created.append(adjustment_period.name)

        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء {len(periods_created)} فترة محاسبية بنجاح',
            'periods_created': periods_created
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إنشاء الفترات: {str(e)}'
        })


class AccountingPeriodListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة الفترات المحاسبية"""

    model = AccountingPeriod
    template_name = 'accounting/fiscal/period_list.html'
    context_object_name = 'periods'
    permission_required = 'accounting.view_accountingperiod'
    paginate_by = 25

    def get_queryset(self):
        queryset = AccountingPeriod.objects.filter(
            company=self.request.current_company
        ).select_related('fiscal_year').order_by('-fiscal_year__start_date', 'start_date')

        # تطبيق الفلاتر
        form = AccountingPeriodFilterForm(self.request.GET, request=self.request)
        if form.is_valid():
            if form.cleaned_data.get('fiscal_year'):
                queryset = queryset.filter(fiscal_year=form.cleaned_data['fiscal_year'])

            if form.cleaned_data.get('status') == 'active':
                queryset = queryset.filter(is_closed=False)
            elif form.cleaned_data.get('status') == 'closed':
                queryset = queryset.filter(is_closed=True)

            if form.cleaned_data.get('period_type') == 'normal':
                queryset = queryset.filter(is_adjustment=False)
            elif form.cleaned_data.get('period_type') == 'adjustment':
                queryset = queryset.filter(is_adjustment=True)

            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        stats = AccountingPeriod.objects.filter(
            company=self.request.current_company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_closed=False)),
            closed=Count('id', filter=Q(is_closed=True)),
            adjustment=Count('id', filter=Q(is_adjustment=True))
        )

        context.update({
            'title': _('الفترات المحاسبية'),
            'filter_form': AccountingPeriodFilterForm(self.request.GET, request=self.request),
            'can_add': self.request.user.has_perm('accounting.add_accountingperiod'),
            'can_edit': self.request.user.has_perm('accounting.change_accountingperiod'),
            'can_delete': self.request.user.has_perm('accounting.delete_accountingperiod'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('الفترات المحاسبية'), 'url': ''},
            ]
        })
        return context


class AccountingPeriodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء فترة محاسبية جديدة"""

    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'accounting/fiscal/period_form.html'
    permission_required = 'accounting.add_accountingperiod'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء الفترة المحاسبية {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:period_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء فترة محاسبية جديدة'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('الفترات المحاسبية'), 'url': reverse('accounting:period_list')},
                {'title': _('إنشاء جديد'), 'url': ''},
            ]
        })
        return context


class AccountingPeriodDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل الفترة المحاسبية"""

    model = AccountingPeriod
    template_name = 'accounting/fiscal/period_detail.html'
    context_object_name = 'period'
    permission_required = 'accounting.view_accountingperiod'

    def get_queryset(self):
        return AccountingPeriod.objects.filter(
            company=self.request.current_company
        ).select_related('fiscal_year')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات القيود في هذه الفترة
        from ..models import JournalEntry

        journal_entries = JournalEntry.objects.filter(
            company=self.request.current_company,
            period=self.object
        )

        stats = {
            'duration_days': (self.object.end_date - self.object.start_date).days + 1,
            'journal_entries_count': journal_entries.count(),
            'posted_entries': journal_entries.filter(status='posted').count(),
            'draft_entries': journal_entries.filter(status='draft').count(),
        }

        context.update({
            'title': f'تفاصيل الفترة: {self.object.name}',
            'stats': stats,
            'can_edit': self.request.user.has_perm('accounting.change_accountingperiod') and not self.object.is_closed,
            'can_delete': self.request.user.has_perm(
                'accounting.delete_accountingperiod') and not self.object.is_closed,
            'can_close': self.request.user.has_perm('accounting.change_accountingperiod') and not self.object.is_closed,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('الفترات المحاسبية'), 'url': reverse('accounting:period_list')},
                {'title': self.object.name, 'url': ''},
            ]
        })
        return context


class AccountingPeriodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل الفترة المحاسبية"""

    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'accounting/fiscal/period_form.html'
    permission_required = 'accounting.change_accountingperiod'

    def get_queryset(self):
        return AccountingPeriod.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if self.object.is_closed:
            messages.error(self.request, 'لا يمكن تعديل فترة محاسبية مقفلة')
            return redirect('accounting:period_detail', pk=self.object.pk)

        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث الفترة المحاسبية {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:period_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الفترة: {self.object.name}',
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('الفترات المحاسبية'), 'url': reverse('accounting:period_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''},
            ]
        })
        return context


class AccountingPeriodDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف الفترة المحاسبية"""

    model = AccountingPeriod
    template_name = 'accounting/fiscal/period_confirm_delete.html'
    permission_required = 'accounting.delete_accountingperiod'
    success_url = reverse_lazy('accounting:period_list')

    def get_queryset(self):
        return AccountingPeriod.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.is_closed:
            messages.error(request, 'لا يمكن حذف فترة محاسبية مقفلة')
            return redirect('accounting:period_detail', pk=self.object.pk)

        # التحقق من وجود قيود مرتبطة
        from ..models import JournalEntry
        if JournalEntry.objects.filter(period=self.object).exists():
            messages.error(request, 'لا يمكن حذف الفترة المحاسبية لوجود قيود محاسبية مرتبطة')
            return redirect('accounting:period_detail', pk=self.object.pk)

        period_name = self.object.name
        messages.success(request, f'تم حذف الفترة المحاسبية {period_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views للفترات المحاسبية
@login_required
@permission_required_with_message('accounting.change_accountingperiod')
@require_http_methods(["POST"])
def close_period_ajax(request, period_id):
    """إقفال الفترة المحاسبية"""

    try:
        period = get_object_or_404(
            AccountingPeriod,
            pk=period_id,
            company=request.current_company
        )

        if period.is_closed:
            return JsonResponse({
                'success': False,
                'message': 'الفترة مقفلة مسبقاً'
            })

        form = PeriodClosingForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'بيانات النموذج غير صحيحة'
            })

        # التحقق من وجود قيود غير مرحلة
        from ..models import JournalEntry
        draft_entries = JournalEntry.objects.filter(
            period=period,
            status='draft'
        ).count()

        if draft_entries > 0:
            return JsonResponse({
                'success': False,
                'message': f'يوجد {draft_entries} قيد غير مرحل في هذه الفترة. يجب ترحيل جميع القيود أولاً'
            })

        with transaction.atomic():
            # إقفال الفترة
            period.is_closed = True
            period.save()

            # تسجيل تاريخ الإقفال في AuditLog
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='AccountingPeriod',
                object_id=period.id,
                object_repr=f'إقفال الفترة المحاسبية: {period.name}',
                old_values={'is_closed': False},
                new_values={'is_closed': True, 'closing_notes': form.cleaned_data.get('closing_notes', '')},
                company=request.current_company,
                branch=request.current_branch if hasattr(request, 'current_branch') else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return JsonResponse({
            'success': True,
            'message': f'تم إقفال الفترة {period.name} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إقفال الفترة: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_accountingperiod')
@require_http_methods(["POST"])
def reopen_period_ajax(request, period_id):
    """إعادة فتح الفترة المحاسبية"""

    try:
        period = get_object_or_404(
            AccountingPeriod,
            pk=period_id,
            company=request.current_company
        )

        if not period.is_closed:
            return JsonResponse({
                'success': False,
                'message': 'الفترة مفتوحة مسبقاً'
            })

        # التحقق من أن السنة المالية غير مقفلة
        if period.fiscal_year.is_closed:
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن إعادة فتح فترة في سنة مالية مقفلة'
            })

        with transaction.atomic():
            # إعادة فتح الفترة
            period.is_closed = False
            period.save()

            # تسجيل في AuditLog
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='AccountingPeriod',
                object_id=period.id,
                object_repr=f'إعادة فتح الفترة المحاسبية: {period.name}',
                old_values={'is_closed': True},
                new_values={'is_closed': False},
                company=request.current_company,
                branch=request.current_branch if hasattr(request, 'current_branch') else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return JsonResponse({
            'success': True,
            'message': f'تم إعادة فتح الفترة {period.name} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في إعادة فتح الفترة: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.view_accountingperiod')
@require_http_methods(["GET"])
def period_datatable_ajax(request):
    """Ajax endpoint لجدول الفترات المحاسبية"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    # ✅ إذا كان الطلب لجلب قائمة السنوات المالية للفلتر
    if request.GET.get('get_fiscal_years'):
        fiscal_years = FiscalYear.objects.filter(
            company=request.current_company
        ).order_by('-start_date').values('id', 'name')

        return JsonResponse({
            'fiscal_years': list(fiscal_years)
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    fiscal_year_id = request.GET.get('fiscal_year', '')
    status = request.GET.get('status', '')
    period_type = request.GET.get('period_type', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        # ✅ البحث والفلترة مع تحسين الأداء - استخدام journalentry بدلاً من journal_entries
        queryset = AccountingPeriod.objects.filter(
            company=request.current_company
        ).select_related('fiscal_year').annotate(
            journal_entries_count=Count('journalentry', filter=Q(journalentry__status='posted')),
            draft_entries_count=Count('journalentry', filter=Q(journalentry__status='draft'))
        )

        # تطبيق الفلاتر
        if fiscal_year_id:
            queryset = queryset.filter(fiscal_year_id=fiscal_year_id)

        if status == 'active':
            queryset = queryset.filter(is_closed=False)
        elif status == 'closed':
            queryset = queryset.filter(is_closed=True)

        if period_type == 'normal':
            queryset = queryset.filter(is_adjustment=False)
        elif period_type == 'adjustment':
            queryset = queryset.filter(is_adjustment=True)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(fiscal_year__name__icontains=search_term) |
                Q(fiscal_year__code__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['fiscal_year__name', 'name', 'start_date', 'end_date', None, None, 'is_closed']
            col_index = int(order_column)
            if col_index < len(columns) and columns[col_index]:
                order_field = columns[col_index]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-fiscal_year__start_date', 'start_date')

        # العد الإجمالي
        total_records = AccountingPeriod.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_accountingperiod')
        can_delete = request.user.has_perm('accounting.delete_accountingperiod')
        can_view = request.user.has_perm('accounting.view_accountingperiod')

        for period in queryset:
            # حساب المدة
            duration = (period.end_date - period.start_date).days + 1
            duration_badge = f'<span class="badge bg-info">{duration} يوم</span>'

            # نوع الفترة
            if period.is_adjustment:
                type_badge = '<span class="badge bg-warning text-dark">تسويات</span>'
            else:
                type_badge = '<span class="badge bg-info">عادية</span>'

            # حالة الفترة
            if period.is_closed:
                status_badge = '<span class="badge bg-danger">مقفلة</span>'
            else:
                status_badge = '<span class="badge bg-success">نشطة</span>'

            # إحصائيات القيود
            total_entries = period.journal_entries_count + period.draft_entries_count
            entries_info = ''
            if total_entries > 0:
                if period.journal_entries_count > 0:
                    entries_info = f'<small class="text-success d-block">{period.journal_entries_count} مرحل</small>'
                if period.draft_entries_count > 0:
                    if entries_info:
                        entries_info += f'<small class="text-warning d-block">{period.draft_entries_count} مسودة</small>'
                    else:
                        entries_info = f'<small class="text-warning d-block">{period.draft_entries_count} مسودة</small>'
            else:
                entries_info = '<small class="text-muted">لا توجد قيود</small>'

            # اسم الفترة مع الرابط
            period_name = f'<a href="{reverse("accounting:period_detail", args=[period.pk])}" class="text-decoration-none fw-bold">{period.name}</a><br>{type_badge}'

            # اسم السنة المالية مع الرابط
            fiscal_year_name = f'<a href="{reverse("accounting:fiscal_year_detail", args=[period.fiscal_year.pk])}" class="text-decoration-none text-muted">{period.fiscal_year.name}</a>'

            # أزرار الإجراءات
            actions = []

            # عرض التفاصيل
            if can_view:
                actions.append(f'''
                    <a href="{reverse('accounting:period_detail', args=[period.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            # تعديل
            if can_edit and not period.is_closed:
                actions.append(f'''
                    <a href="{reverse('accounting:period_update', args=[period.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            # إقفال/إعادة فتح
            if can_edit:
                if not period.is_closed and period.draft_entries_count == 0:
                    actions.append(f'''
                        <button type="button" class="btn btn-outline-warning btn-sm" 
                                onclick="closePeriod({period.pk})" title="إقفال الفترة" data-bs-toggle="tooltip">
                            <i class="fas fa-lock"></i>
                        </button>
                    ''')
                elif period.is_closed and not period.fiscal_year.is_closed:
                    actions.append(f'''
                        <button type="button" class="btn btn-outline-success btn-sm" 
                                onclick="reopenPeriod({period.pk})" title="إعادة فتح الفترة" data-bs-toggle="tooltip">
                            <i class="fas fa-unlock"></i>
                        </button>
                    ''')

            # حذف
            if can_delete and not period.is_closed and total_entries == 0:
                actions.append(f'''
                    <a href="{reverse('accounting:period_delete', args=[period.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '<span class="text-muted">-</span>'

            data.append([
                fiscal_year_name,
                period_name,
                period.start_date.strftime('%Y/%m/%d'),
                period.end_date.strftime('%Y/%m/%d'),
                duration_badge,
                entries_info,
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
        import traceback
        print(f"Error in period_datatable_ajax: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


class CostCenterListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة مراكز التكلفة"""

    model = CostCenter
    template_name = 'accounting/fiscal/cost_center_list.html'
    context_object_name = 'cost_centers'
    permission_required = 'accounting.view_costcenter'
    paginate_by = 25

    def get_queryset(self):
        queryset = CostCenter.objects.filter(
            company=self.request.current_company
        ).select_related('parent', 'manager').order_by('code')

        # تطبيق الفلاتر
        form = CostCenterFilterForm(self.request.GET, request=self.request)
        if form.is_valid():
            if form.cleaned_data.get('cost_center_type'):
                queryset = queryset.filter(cost_center_type=form.cleaned_data['cost_center_type'])

            if form.cleaned_data.get('level'):
                queryset = queryset.filter(level=form.cleaned_data['level'])

            if form.cleaned_data.get('status') == 'active':
                queryset = queryset.filter(is_active=True)
            elif form.cleaned_data.get('status') == 'inactive':
                queryset = queryset.filter(is_active=False)

            if form.cleaned_data.get('parent'):
                queryset = queryset.filter(parent=form.cleaned_data['parent'])

            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(code__icontains=search)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        stats = CostCenter.objects.filter(
            company=self.request.current_company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            inactive=Count('id', filter=Q(is_active=False)),
            level_1=Count('id', filter=Q(level=1)),
            level_2=Count('id', filter=Q(level=2)),
            level_3=Count('id', filter=Q(level=3)),
            level_4=Count('id', filter=Q(level=4))
        )

        context.update({
            'title': _('مراكز التكلفة'),
            'filter_form': CostCenterFilterForm(self.request.GET, request=self.request),
            'can_add': self.request.user.has_perm('accounting.add_costcenter'),
            'can_edit': self.request.user.has_perm('accounting.change_costcenter'),
            'can_delete': self.request.user.has_perm('accounting.delete_costcenter'),
            'stats': stats,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('مراكز التكلفة'), 'url': ''},
            ]
        })
        return context


class CostCenterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء مركز تكلفة جديد"""

    model = CostCenter
    form_class = CostCenterForm
    template_name = 'accounting/fiscal/cost_center_form.html'
    permission_required = 'accounting.add_costcenter'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء مركز التكلفة {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:cost_center_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء مركز تكلفة جديد'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('مراكز التكلفة'), 'url': reverse('accounting:cost_center_list')},
                {'title': _('إنشاء جديد'), 'url': ''},
            ]
        })
        return context


class CostCenterDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل مركز التكلفة"""

    model = CostCenter
    template_name = 'accounting/fiscal/cost_center_detail.html'
    context_object_name = 'cost_center'
    permission_required = 'accounting.view_costcenter'

    def get_queryset(self):
        return CostCenter.objects.filter(
            company=self.request.current_company
        ).select_related('parent', 'manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المراكز الفرعية
        children = self.object.children.filter(is_active=True).order_by('code')

        # إحصائيات استخدام المركز
        from ..models import JournalEntryLine

        usage_stats = {
            'journal_entries_count': JournalEntryLine.objects.filter(
                cost_center=self.object,
                journal_entry__company=self.request.current_company
            ).count(),
            'children_count': children.count(),
            'total_descendants': self.get_total_descendants(self.object)
        }

        context.update({
            'title': f'تفاصيل مركز التكلفة: {self.object.name}',
            'children': children,
            'usage_stats': usage_stats,
            'can_edit': self.request.user.has_perm('accounting.change_costcenter'),
            'can_delete': self.request.user.has_perm('accounting.delete_costcenter') and usage_stats[
                'journal_entries_count'] == 0,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('مراكز التكلفة'), 'url': reverse('accounting:cost_center_list')},
                {'title': self.object.name, 'url': ''},
            ]
        })
        return context

    def get_total_descendants(self, cost_center):
        """حساب عدد المراكز التابعة (جميع المستويات)"""
        total = 0
        for child in cost_center.children.all():
            total += 1 + self.get_total_descendants(child)
        return total


class CostCenterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل مركز التكلفة"""

    model = CostCenter
    form_class = CostCenterForm
    template_name = 'accounting/fiscal/cost_center_form.html'
    permission_required = 'accounting.change_costcenter'

    def get_queryset(self):
        return CostCenter.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث مركز التكلفة {self.object.name} بنجاح')
        return response

    def get_success_url(self):
        return reverse('accounting:cost_center_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل مركز التكلفة: {self.object.name}',
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('مراكز التكلفة'), 'url': reverse('accounting:cost_center_list')},
                {'title': f'تعديل: {self.object.name}', 'url': ''},
            ]
        })
        return context



class CostCenterDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف مركز تكلفة"""
    model = CostCenter
    template_name = 'accounting/fiscal/cost_center_confirm_delete.html'
    success_url = reverse_lazy('accounting:cost_center_list')
    permission_required = 'accounting.delete_costcenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cost_center = self.get_object()

        # عنوان الصفحة
        context['title'] = f'حذف مركز التكلفة - {cost_center.name}'

        # Breadcrumbs
        context['breadcrumbs'] = [
            {'title': 'لوحة التحكم', 'url': reverse('accounting:dashboard')},
            {'title': 'مراكز التكلفة', 'url': reverse('accounting:cost_center_list')},
            {'title': cost_center.name, 'url': reverse('accounting:cost_center_detail', args=[cost_center.pk])},
            {'title': 'حذف', 'url': ''}
        ]

        # التحقق من المراكز الفرعية
        children_count = cost_center.children.count()
        context['has_children'] = children_count > 0
        context['children_count'] = children_count

        # التحقق من الاستخدام في القيود المحاسبية
        # تأكد من اسم الحقل الصحيح في JournalEntry model
        try:
            from apps.accounting.models import JournalEntry
            # إذا كان الحقل اسمه cost_center
            usage_count = JournalEntry.objects.filter(cost_center=cost_center).count()
        except:
            # إذا لم يكن هناك ربط
            usage_count = 0

        context['usage_count'] = usage_count
        context['can_delete'] = (children_count == 0 and usage_count == 0)

        # الصلاحيات
        context['can_edit'] = self.request.user.has_perm('accounting.change_costcenter')
        context['can_view'] = self.request.user.has_perm('accounting.view_costcenter')

        return context

    def get_queryset(self):
        """التأكد من أن المركز يخص الشركة الحالية"""
        return super().get_queryset().filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        """التحقق قبل الحذف"""
        cost_center = self.get_object()

        # التحقق من المراكز الفرعية
        if cost_center.children.exists():
            messages.error(
                request,
                f'لا يمكن حذف مركز التكلفة "{cost_center.name}" لأنه يحتوي على {cost_center.children.count()} مركز فرعي. '
                'يرجى حذف أو نقل المراكز الفرعية أولاً.'
            )
            return redirect('accounting:cost_center_detail', pk=cost_center.pk)

        # التحقق من الاستخدام في القيود
        try:
            from apps.accounting.models import JournalEntry
            usage_count = JournalEntry.objects.filter(cost_center=cost_center).count()

            if usage_count > 0:
                messages.error(
                    request,
                    f'لا يمكن حذف مركز التكلفة "{cost_center.name}" لأنه مستخدم في {usage_count} قيد محاسبي. '
                    'يرجى حذف أو تحديث القيود أولاً.'
                )
                return redirect('accounting:cost_center_detail', pk=cost_center.pk)
        except:
            pass

        # حفظ الاسم قبل الحذف
        cost_center_name = cost_center.name

        # تسجيل في AuditLog
        try:
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='DELETE',
                model_name='CostCenter',
                object_id=cost_center.pk,
                object_repr=f'حذف مركز التكلفة: {cost_center_name} ({cost_center.code})',
                old_values={
                    'name': cost_center_name,
                    'code': cost_center.code,
                    'type': cost_center.cost_center_type,
                    'level': cost_center.level
                },
                new_values=None,
                company=request.current_company,
                branch=request.current_branch if hasattr(request, 'current_branch') else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error logging activity: {e}")

        # الحذف
        messages.success(
            request,
            f'تم حذف مركز التكلفة "{cost_center_name}" بنجاح'
        )

        return super().delete(request, *args, **kwargs)


# Ajax Views
@login_required
@permission_required_with_message('accounting.view_costcenter')
@require_http_methods(["GET"])
def cost_center_datatable_ajax(request):
    """Ajax endpoint لجدول مراكز التكلفة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    # ✅ إذا كان الطلب لجلب قائمة المراكز الأب للفلتر
    if request.GET.get('get_parents'):
        parents = CostCenter.objects.filter(
            company=request.current_company,
            level=1
        ).order_by('name').values('id', 'name')

        return JsonResponse({
            'parents': list(parents)
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    type_filter = request.GET.get('type', '')
    level_filter = request.GET.get('level', '')
    status_filter = request.GET.get('status', '')
    parent_filter = request.GET.get('parent', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        # البحث والفلترة
        queryset = CostCenter.objects.filter(
            company=request.current_company
        ).select_related('parent', 'manager')

        # تطبيق الفلاتر
        if type_filter:
            queryset = queryset.filter(cost_center_type=type_filter)

        if level_filter:
            queryset = queryset.filter(level=int(level_filter))

        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        if parent_filter:
            queryset = queryset.filter(parent_id=parent_filter)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(description__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['code', 'name', 'cost_center_type', 'parent__name', 'level', None, 'is_active']
            col_index = int(order_column)
            if col_index < len(columns) and columns[col_index]:
                order_field = columns[col_index]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('level', 'code')

        # العد الإجمالي
        total_records = CostCenter.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('accounting.change_costcenter')
        can_delete = request.user.has_perm('accounting.delete_costcenter')
        can_view = request.user.has_perm('accounting.view_costcenter')

        for center in queryset:
            # نوع المركز
            type_colors = {
                'administration': 'primary',
                'production': 'success',
                'sales': 'info',
                'services': 'secondary',
                'marketing': 'purple',
                'maintenance': 'warning'
            }
            type_color = type_colors.get(center.cost_center_type, 'secondary')
            type_badge = f'<span class="badge bg-{type_color}">{center.get_cost_center_type_display()}</span>'

            # المركز الأب
            parent_text = '--'
            if center.parent:
                parent_text = f'<a href="{reverse("accounting:cost_center_detail", args=[center.parent.pk])}" class="text-decoration-none text-muted">{center.parent.name}</a>'

            # المستوى
            level_badge = f'<span class="badge bg-info">المستوى {center.level}</span>'

            # المدير
            manager_text = '--'
            if center.manager:
                manager_text = f'<small>{center.manager.get_full_name() or center.manager.username}</small>'

            # الحالة
            if center.is_active:
                status_badge = '<span class="badge bg-success">نشط</span>'
            else:
                status_badge = '<span class="badge bg-danger">غير نشط</span>'

            # اسم المركز مع المسافات الهرمية
            indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * (center.level - 1)
            icon = '<i class="fas fa-level-down-alt text-muted me-1"></i>' if center.level > 1 else ''
            name_html = f'{indent}{icon}<a href="{reverse("accounting:cost_center_detail", args=[center.pk])}" class="text-decoration-none fw-bold">{center.name}</a>'

            # أزرار الإجراءات
            actions = []

            # عرض
            if can_view:
                actions.append(f'''
                    <a href="{reverse('accounting:cost_center_detail', args=[center.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            # تعديل
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('accounting:cost_center_update', args=[center.pk])}" 
                       class="btn btn-outline-warning btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            # حذف
            if can_delete and not center.children.exists():
                actions.append(f'''
                    <a href="{reverse('accounting:cost_center_delete', args=[center.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '<span class="text-muted">-</span>'

            data.append([
                f'<code>{center.code}</code>',
                name_html,
                type_badge,
                parent_text,
                level_badge,
                manager_text,
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
        import traceback
        print(f"Error in cost_center_datatable_ajax: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.change_costcenter')
@require_http_methods(["POST"])
def toggle_cost_center_status(request, pk):
    """تفعيل/إلغاء تفعيل مركز التكلفة"""

    try:
        cost_center = get_object_or_404(
            CostCenter,
            pk=pk,
            company=request.current_company
        )

        new_status = request.POST.get('status') == 'true'
        old_status = cost_center.is_active

        cost_center.is_active = new_status
        cost_center.save()

        # تسجيل في AuditLog
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            model_name='CostCenter',
            object_id=cost_center.id,
            object_repr=f'تغيير حالة مركز التكلفة: {cost_center.name}',
            old_values={'is_active': old_status},
            new_values={'is_active': new_status},
            company=request.current_company,
            branch=request.current_branch if hasattr(request, 'current_branch') else None,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        status_text = "تفعيل" if new_status else "إلغاء تفعيل"
        return JsonResponse({
            'success': True,
            'message': f'تم {status_text} مركز التكلفة {cost_center.name} بنجاح',
            'new_status': new_status
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في تغيير حالة مركز التكلفة: {str(e)}'
        })


@login_required
@permission_required_with_message('accounting.view_costcenter')
@require_http_methods(["GET"])
def cost_center_search_ajax(request):
    """البحث عن مراكز التكلفة للـ Ajax"""

    query = request.GET.get('term', '')

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse([], safe=False)

    cost_centers = CostCenter.objects.filter(
        company=request.current_company,
        is_active=True
    )

    if query:
        cost_centers = cost_centers.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )

    cost_centers = cost_centers.order_by('code')[:20]

    results = []
    for center in cost_centers:
        results.append({
            'id': center.id,
            'text': f"{center.code} - {center.name}",
            'code': center.code,
            'name': center.name
        })

    return JsonResponse(results, safe=False)
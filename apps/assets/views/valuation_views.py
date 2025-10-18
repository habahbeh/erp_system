# apps/assets/views/valuation_views.py
"""
Valuation Views - إدارة إعادة تقييم الأصول
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, DetailView, DeleteView, TemplateView
from django.db.models import Q, Sum, Count, Avg
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from datetime import date, datetime
import json

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message, company_required
from ..models import Asset, AssetValuation
from ..forms import AssetValuationForm


class AssetValuationListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة إعادات تقييم الأصول"""

    template_name = 'assets/valuation/valuation_list.html'
    permission_required = 'assets.view_assetvaluation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_valuations = AssetValuation.objects.filter(
            asset__company=self.request.current_company
        ).count()

        pending_approval = AssetValuation.objects.filter(
            asset__company=self.request.current_company,
            is_approved=False
        ).count()

        approved = AssetValuation.objects.filter(
            asset__company=self.request.current_company,
            is_approved=True
        ).count()

        # إجمالي الفروقات
        total_difference = AssetValuation.objects.filter(
            asset__company=self.request.current_company,
            is_approved=True
        ).aggregate(total=Sum('difference'))['total'] or Decimal('0.00')

        context.update({
            'title': _('إعادة تقييم الأصول'),
            'can_add': self.request.user.has_perm('assets.can_revalue_asset'),
            'can_approve': self.request.user.has_perm('assets.can_revalue_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_assetvaluation'),
            'total_valuations': total_valuations,
            'pending_approval': pending_approval,
            'approved': approved,
            'total_difference': total_difference,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('إعادة التقييم'), 'url': ''}
            ],
        })
        return context


class AssetValuationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء إعادة تقييم جديدة"""

    model = AssetValuation
    form_class = AssetValuationForm
    template_name = 'assets/valuation/valuation_form.html'
    permission_required = 'assets.can_revalue_asset'
    success_url = reverse_lazy('assets:valuation_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # حساب القيمة القديمة من الأصل
        asset = form.instance.asset
        form.instance.old_value = asset.book_value

        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء طلب إعادة تقييم للأصل {asset.name} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء إعادة تقييم'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('إعادة التقييم'), 'url': reverse('assets:valuation_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AssetValuationDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل إعادة تقييم"""

    model = AssetValuation
    template_name = 'assets/valuation/valuation_detail.html'
    context_object_name = 'valuation'
    permission_required = 'assets.view_assetvaluation'

    def get_queryset(self):
        return AssetValuation.objects.filter(
            asset__company=self.request.current_company
        ).select_related('asset', 'approved_by', 'created_by', 'journal_entry')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # حساب النسبة المئوية للتغيير
        if self.object.old_value > 0:
            change_percentage = (self.object.difference / self.object.old_value) * 100
        else:
            change_percentage = 0

        context.update({
            'title': f'إعادة تقييم {self.object.asset.name}',
            'can_approve': (
                    self.request.user.has_perm('assets.can_revalue_asset') and
                    not self.object.is_approved
            ),
            'can_delete': (
                    self.request.user.has_perm('assets.delete_assetvaluation') and
                    not self.object.is_approved
            ),
            'change_percentage': change_percentage,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('إعادة التقييم'), 'url': reverse('assets:valuation_list')},
                {'title': f'تقييم {self.object.asset.name}', 'url': ''}
            ],
        })
        return context


class AssetValuationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف إعادة تقييم"""

    model = AssetValuation
    template_name = 'assets/valuation/valuation_confirm_delete.html'
    permission_required = 'assets.delete_assetvaluation'
    success_url = reverse_lazy('assets:valuation_list')

    def get_queryset(self):
        return AssetValuation.objects.filter(asset__company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.is_approved:
            messages.error(request, 'لا يمكن حذف إعادة تقييم معتمدة')
            return redirect('assets:valuation_detail', pk=self.object.pk)

        asset_name = self.object.asset.name
        messages.success(request, f'تم حذف إعادة تقييم الأصل {asset_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views

@login_required
@permission_required_with_message('assets.view_assetvaluation')
@require_http_methods(["GET"])
def asset_valuation_datatable_ajax(request):
    """Ajax endpoint لجدول إعادات التقييم"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    approval_status = request.GET.get('approval_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        queryset = AssetValuation.objects.filter(
            asset__company=request.current_company
        ).select_related('asset', 'approved_by', 'created_by')

        # تطبيق الفلاتر
        if approval_status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif approval_status == 'pending':
            queryset = queryset.filter(is_approved=False)

        if date_from:
            queryset = queryset.filter(valuation_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(valuation_date__lte=date_to)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value) |
                Q(valuator_name__icontains=search_value)
            )

        queryset = queryset.order_by('-valuation_date')

        total_records = AssetValuation.objects.filter(asset__company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_approve = request.user.has_perm('assets.can_revalue_asset')
        can_delete = request.user.has_perm('assets.delete_assetvaluation')

        for valuation in queryset:
            # الحالة
            if valuation.is_approved:
                status_badge = '<span class="badge bg-success">معتمد</span>'
            else:
                status_badge = '<span class="badge bg-warning">معلق</span>'

            # الفرق
            if valuation.difference > 0:
                difference_display = f'<span class="text-success">+{valuation.difference:,.3f}</span>'
            elif valuation.difference < 0:
                difference_display = f'<span class="text-danger">{valuation.difference:,.3f}</span>'
            else:
                difference_display = f'{valuation.difference:,.3f}'

            # الأزرار
            actions = []
            actions.append(f'''
                <a href="{reverse('assets:valuation_detail', args=[valuation.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if can_approve and not valuation.is_approved:
                actions.append(f'''
                    <button type="button" class="btn btn-outline-success btn-sm" 
                            onclick="approveValuation({valuation.pk})" title="اعتماد">
                        <i class="fas fa-check"></i>
                    </button>
                ''')

            if can_delete and not valuation.is_approved:
                actions.append(f'''
                    <a href="{reverse('assets:valuation_delete', args=[valuation.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                valuation.valuation_date.strftime('%Y-%m-%d'),
                f"{valuation.asset.asset_number} - {valuation.asset.name}",
                f"{valuation.old_value:,.3f}",
                f"{valuation.new_value:,.3f}",
                difference_display,
                valuation.valuator_name or '--',
                status_badge,
                ' '.join(actions)
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.can_revalue_asset')
@require_http_methods(["POST"])
def approve_valuation_ajax(request, pk):
    """اعتماد إعادة تقييم"""

    try:
        valuation = get_object_or_404(
            AssetValuation,
            pk=pk,
            asset__company=request.current_company
        )

        if valuation.is_approved:
            return JsonResponse({
                'success': False,
                'message': 'إعادة التقييم معتمدة بالفعل'
            })

        with transaction.atomic():
            # اعتماد التقييم
            valuation.is_approved = True
            valuation.approved_by = request.user
            valuation.approved_at = datetime.now()
            valuation.save()

            # تحديث قيمة الأصل
            asset = valuation.asset
            old_cost = asset.original_cost
            asset.original_cost = valuation.new_value
            asset.book_value = valuation.new_value - asset.accumulated_depreciation
            asset.save()

            # إنشاء القيد المحاسبي (إذا كانت هناك زيادة أو نقص)
            if valuation.difference != 0:
                from apps.accounting.models import JournalEntry, JournalEntryLine, FiscalYear, AccountingPeriod

                # الحصول على السنة والفترة
                try:
                    fiscal_year = FiscalYear.objects.get(
                        company=request.current_company,
                        start_date__lte=valuation.valuation_date,
                        end_date__gte=valuation.valuation_date,
                        is_closed=False
                    )
                except FiscalYear.DoesNotExist:
                    raise Exception('لا توجد سنة مالية نشطة')

                period = AccountingPeriod.objects.filter(
                    fiscal_year=fiscal_year,
                    start_date__lte=valuation.valuation_date,
                    end_date__gte=valuation.valuation_date,
                    is_closed=False
                ).first()

                # إنشاء القيد
                journal_entry = JournalEntry.objects.create(
                    company=request.current_company,
                    branch=request.current_branch,
                    fiscal_year=fiscal_year,
                    period=period,
                    entry_date=valuation.valuation_date,
                    entry_type='auto',
                    description=f'إعادة تقييم أصل - {asset.name}',
                    reference=f'VAL-{valuation.pk}',
                    source_document='asset_valuation',
                    source_id=valuation.pk,
                    created_by=request.user
                )

                line_number = 1

                if valuation.difference > 0:
                    # زيادة في القيمة
                    # مدين: حساب الأصل
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=line_number,
                        account=asset.category.asset_account,
                        description=f'زيادة قيمة أصل - {asset.name}',
                        debit_amount=abs(valuation.difference),
                        credit_amount=0,
                        currency=asset.currency
                    )
                    line_number += 1

                    # دائن: احتياطي إعادة تقييم
                    from apps.accounting.models import Account
                    revaluation_reserve = Account.objects.get(
                        company=request.current_company,
                        code='310200'  # احتياطي إعادة تقييم
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=line_number,
                        account=revaluation_reserve,
                        description=f'احتياطي إعادة تقييم - {asset.name}',
                        debit_amount=0,
                        credit_amount=abs(valuation.difference),
                        currency=asset.currency
                    )

                else:
                    # نقص في القيمة
                    # مدين: خسارة إعادة تقييم
                    from apps.accounting.models import Account
                    revaluation_loss = Account.objects.get(
                        company=request.current_company,
                        code='520300'  # خسائر إعادة تقييم
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=line_number,
                        account=revaluation_loss,
                        description=f'خسارة إعادة تقييم - {asset.name}',
                        debit_amount=abs(valuation.difference),
                        credit_amount=0,
                        currency=asset.currency
                    )
                    line_number += 1

                    # دائن: حساب الأصل
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        line_number=line_number,
                        account=asset.category.asset_account,
                        description=f'نقص قيمة أصل - {asset.name}',
                        debit_amount=0,
                        credit_amount=abs(valuation.difference),
                        currency=asset.currency
                    )

                # ترحيل القيد
                journal_entry.calculate_totals()
                journal_entry.post(user=request.user)

                # ربط القيد بالتقييم
                valuation.journal_entry = journal_entry
                valuation.save()

        return JsonResponse({
            'success': True,
            'message': f'تم اعتماد إعادة تقييم الأصل {asset.name} بنجاح',
            'data': {
                'old_value': float(valuation.old_value),
                'new_value': float(valuation.new_value),
                'difference': float(valuation.difference)
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في اعتماد التقييم: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_assetvaluation')
@require_http_methods(["GET"])
def valuation_stats_ajax(request):
    """إحصائيات إعادة التقييم"""

    try:
        current_year = date.today().year

        # إحصائيات السنة الحالية
        year_valuations = AssetValuation.objects.filter(
            asset__company=request.current_company,
            valuation_date__year=current_year,
            is_approved=True
        )

        total_increase = year_valuations.filter(difference__gt=0).aggregate(
            total=Sum('difference')
        )['total'] or Decimal('0.00')

        total_decrease = year_valuations.filter(difference__lt=0).aggregate(
            total=Sum('difference')
        )['total'] or Decimal('0.00')

        net_change = total_increase + total_decrease

        # عدد الأصول المُقيمة
        assets_revalued = year_valuations.values('asset').distinct().count()

        return JsonResponse({
            'success': True,
            'stats': {
                'total_increase': float(total_increase),
                'total_decrease': float(abs(total_decrease)),
                'net_change': float(net_change),
                'assets_revalued': assets_revalued,
                'pending_approval': AssetValuation.objects.filter(
                    asset__company=request.current_company,
                    is_approved=False
                ).count()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def get_asset_current_value_ajax(request, asset_id):
    """الحصول على القيمة الحالية للأصل"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=asset_id,
            company=request.current_company
        )

        return JsonResponse({
            'success': True,
            'data': {
                'asset_number': asset.asset_number,
                'asset_name': asset.name,
                'original_cost': float(asset.original_cost),
                'accumulated_depreciation': float(asset.accumulated_depreciation),
                'book_value': float(asset.book_value),
                'last_valuation': None
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
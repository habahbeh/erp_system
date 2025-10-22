# apps/assets/views/physical_count_views.py
"""
Views الجرد الفعلي للأصول
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
from django.db import transaction
from django.core.exceptions import ValidationError
import json
from datetime import date, timedelta
from decimal import Decimal

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine,
    PhysicalCountAdjustment, Asset, AssetCategory
)


# ==================== Physical Count Cycles ====================

class PhysicalCountCycleListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة دورات الجرد"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_list.html'
    context_object_name = 'cycles'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 25

    def get_queryset(self):
        queryset = PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        ).prefetch_related('branches', 'asset_categories')

        # الفلترة
        status = self.request.GET.get('status')
        cycle_type = self.request.GET.get('cycle_type')

        if status:
            queryset = queryset.filter(status=status)

        if cycle_type:
            queryset = queryset.filter(cycle_type=cycle_type)

        return queryset.order_by('-start_date', '-cycle_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title': _('دورات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'can_edit': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCountCycle.STATUS_CHOICES,
            'cycle_types': PhysicalCountCycle.CYCLE_TYPES,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                   CreateView):
    """إنشاء دورة جرد"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'name', 'cycle_type', 'start_date', 'end_date',
        'planned_completion_date', 'branches', 'asset_categories',
        'team_leader', 'team_members', 'description', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['start_date'].initial = date.today()
        form.fields['end_date'].initial = date.today() + timedelta(days=30)
        form.fields['planned_completion_date'].initial = date.today() + timedelta(days=30)

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        form.instance.status = 'planning'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء دورة الجرد {self.object.cycle_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:cycle_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة دورة جرد'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل دورة الجرد"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_detail.html'
    context_object_name = 'cycle'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        ).prefetch_related(
            'branches', 'asset_categories', 'team_members',
            'physical_counts'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عمليات الجرد
        counts = self.object.physical_counts.all()

        context.update({
            'title': f'دورة الجرد {self.object.cycle_number}',
            'can_edit': self.request.user.has_perm(
                'assets.can_conduct_physical_count') and self.object.status == 'planning',
            'counts': counts,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': self.object.cycle_number, 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                   UpdateView):
    """تعديل دورة جرد"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'name', 'cycle_type', 'start_date', 'end_date',
        'planned_completion_date', 'status', 'branches', 'asset_categories',
        'team_leader', 'team_members', 'description', 'notes'
    ]

    def get_queryset(self):
        return PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        ).exclude(status='completed')

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث دورة الجرد {self.object.cycle_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:cycle_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل دورة الجرد {self.object.cycle_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': self.object.cycle_number, 'url': reverse('assets:cycle_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Physical Counts ====================

class PhysicalCountListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة عمليات الجرد"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_list.html'
    context_object_name = 'counts'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 25

    def get_queryset(self):
        queryset = PhysicalCount.objects.filter(
            company=self.request.current_company
        ).select_related('cycle', 'branch', 'supervisor', 'approved_by')

        # الفلترة
        status = self.request.GET.get('status')
        cycle = self.request.GET.get('cycle')
        branch = self.request.GET.get('branch')

        if status:
            queryset = queryset.filter(status=status)

        if cycle:
            queryset = queryset.filter(cycle_id=cycle)

        if branch:
            queryset = queryset.filter(branch_id=branch)

        return queryset.order_by('-count_date', '-count_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الدورات النشطة
        active_cycles = PhysicalCountCycle.objects.filter(
            company=self.request.current_company,
            status='in_progress'
        )

        context.update({
            'title': _('عمليات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCount.STATUS_CHOICES,
            'active_cycles': active_cycles,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء عملية جرد"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'cycle', 'count_date', 'branch', 'location',
        'responsible_team', 'supervisor', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['cycle'].queryset = PhysicalCountCycle.objects.filter(
            company=self.request.current_company,
            status__in=['planning', 'in_progress']
        )

        form.fields['count_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        # إنشاء سطور الجرد للأصول
        assets = Asset.objects.filter(
            company=self.request.current_company,
            branch=self.object.branch,
            status='active'
        )

        line_number = 1
        for asset in assets:
            PhysicalCountLine.objects.create(
                physical_count=self.object,
                line_number=line_number,
                asset=asset,
                expected_location=asset.physical_location or '',
                expected_condition=asset.condition,
                expected_responsible=asset.responsible_employee
            )
            line_number += 1

        # تحديث الإحصائيات
        self.object.update_statistics()

        messages.success(
            self.request,
            f'تم إنشاء عملية الجرد {self.object.count_number} بنجاح مع {assets.count()} أصل'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة عملية جرد'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل عملية الجرد"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_detail.html'
    context_object_name = 'count'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCount.objects.filter(
            company=self.request.current_company
        ).select_related(
            'cycle', 'branch', 'supervisor', 'approved_by'
        ).prefetch_related('lines', 'responsible_team')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # سطور الجرد
        lines = self.object.lines.select_related(
            'asset', 'expected_condition', 'actual_condition'
        ).order_by('line_number')

        # الفروقات
        variances = lines.filter(
            Q(has_location_variance=True) |
            Q(has_condition_variance=True) |
            Q(has_responsible_variance=True) |
            Q(is_found=False)
        )

        context.update({
            'title': f'عملية الجرد {self.object.count_number}',
            'can_edit': self.request.user.has_perm(
                'assets.can_conduct_physical_count') and self.object.status == 'draft',
            'can_approve': self.request.user.has_perm(
                'assets.can_conduct_physical_count') and self.object.status == 'completed',
            'lines': lines[:50],  # أول 50 سطر
            'variances': variances,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': self.object.count_number, 'url': ''},
            ]
        })
        return context


class PhysicalCountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل عملية جرد"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'cycle', 'count_date', 'branch', 'location',
        'responsible_team', 'supervisor', 'status', 'notes'
    ]

    def get_queryset(self):
        return PhysicalCount.objects.filter(
            company=self.request.current_company
        ).exclude(status='approved')

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث عملية الجرد {self.object.count_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل عملية الجرد {self.object.count_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': self.object.count_number, 'url': reverse('assets:count_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Physical Count Lines ====================

class PhysicalCountLineUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تحديث سطر جرد"""

    model = PhysicalCountLine
    template_name = 'assets/physical_count/line_update.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'is_found', 'is_counted', 'actual_location',
        'actual_condition', 'actual_responsible', 'notes'
    ]

    def get_queryset(self):
        return PhysicalCountLine.objects.filter(
            physical_count__company=self.request.current_company,
            physical_count__status__in=['draft', 'in_progress']
        )

    @transaction.atomic
    def form_valid(self, form):
        from django.utils import timezone

        form.instance.is_counted = True
        form.instance.counted_date = timezone.now()
        form.instance.counted_by = self.request.user

        self.object = form.save()

        # تحديث إحصائيات الجرد
        self.object.physical_count.update_statistics()

        messages.success(self.request, 'تم تحديث سطر الجرد بنجاح')

        return redirect('assets:count_detail', pk=self.object.physical_count.pk)


# ==================== Physical Count Adjustments ====================

class PhysicalCountAdjustmentListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة تسويات الجرد"""

    model = PhysicalCountAdjustment
    template_name = 'assets/physical_count/adjustment_list.html'
    context_object_name = 'adjustments'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 25

    def get_queryset(self):
        queryset = PhysicalCountAdjustment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'physical_count_line', 'physical_count_line__asset',
            'approved_by', 'journal_entry'
        )

        # الفلترة
        status = self.request.GET.get('status')
        adjustment_type = self.request.GET.get('adjustment_type')

        if status:
            queryset = queryset.filter(status=status)

        if adjustment_type:
            queryset = queryset.filter(adjustment_type=adjustment_type)

        return queryset.order_by('-adjustment_date', '-adjustment_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title': _('تسويات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCountAdjustment.STATUS_CHOICES,
            'adjustment_types': PhysicalCountAdjustment.ADJUSTMENT_TYPES,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountAdjustmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                        CreateView):
    """إنشاء تسوية جرد"""

    model = PhysicalCountAdjustment
    template_name = 'assets/physical_count/adjustment_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'physical_count_line', 'adjustment_type',
        'adjustment_date', 'reason', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # فقط سطور الجرد التي تحتاج تسوية
        form.fields['physical_count_line'].queryset = PhysicalCountLine.objects.filter(
            physical_count__company=self.request.current_company,
            requires_adjustment=True
        ).select_related('asset', 'physical_count')

        form.fields['adjustment_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء التسوية {self.object.adjustment_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:adjustment_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة تسوية جرد'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': reverse('assets:adjustment_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountAdjustmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل تسوية الجرد"""

    model = PhysicalCountAdjustment
    template_name = 'assets/physical_count/adjustment_detail.html'
    context_object_name = 'adjustment'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCountAdjustment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'physical_count_line', 'physical_count_line__asset',
            'approved_by', 'journal_entry'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'التسوية {self.object.adjustment_number}',
            'can_approve': self.request.user.has_perm(
                'assets.can_conduct_physical_count') and self.object.status == 'draft',
            'can_post': self.request.user.has_perm(
                'assets.can_conduct_physical_count') and self.object.status == 'approved',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': reverse('assets:adjustment_list')},
                {'title': self.object.adjustment_number, 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def approve_physical_count(request, pk):
    """اعتماد عملية جرد"""

    try:
        count = get_object_or_404(
            PhysicalCount,
            pk=pk,
            company=request.current_company,
            status='completed'
        )

        # اعتماد الجرد
        count.approve(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم اعتماد عملية الجرد {count.count_number} بنجاح'
        })

    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في اعتماد الجرد: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def post_adjustment(request, pk):
    """ترحيل تسوية جرد"""

    try:
        adjustment = get_object_or_404(
            PhysicalCountAdjustment,
            pk=pk,
            company=request.current_company,
            status='approved'
        )

        # ترحيل التسوية
        adjustment.post(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل التسوية {adjustment.adjustment_number} بنجاح'
        })

    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل التسوية: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def count_datatable_ajax(request):
    """Ajax endpoint لجدول عمليات الجرد"""

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

    try:
        queryset = PhysicalCount.objects.filter(
            company=request.current_company
        ).select_related('cycle', 'branch')

        if search_value:
            queryset = queryset.filter(
                Q(count_number__icontains=search_value) |
                Q(location__icontains=search_value)
            )

        queryset = queryset.order_by('-count_date', '-count_number')

        total_records = PhysicalCount.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for count in queryset:
            status_map = {
                'draft': '<span class="badge bg-secondary">مسودة</span>',
                'in_progress': '<span class="badge bg-info">جاري</span>',
                'completed': '<span class="badge bg-warning">مكتمل</span>',
                'approved': '<span class="badge bg-success">معتمد</span>',
                'cancelled': '<span class="badge bg-danger">ملغي</span>',
            }
            status_badge = status_map.get(count.status, count.status)

            # نسبة الإنجاز
            completion = 0
            if count.total_assets > 0:
                completion = (count.counted_assets / count.total_assets) * 100

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:count_detail', args=[count.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                count.count_number,
                count.count_date.strftime('%Y-%m-%d'),
                count.branch.name if count.branch else '-',
                f"{count.counted_assets} / {count.total_assets}",
                f"{completion:.1f}%",
                count.variance_count,
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
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def cycle_datatable_ajax(request):
    """Ajax endpoint لجدول دورات الجرد"""

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

    try:
        queryset = PhysicalCountCycle.objects.filter(
            company=request.current_company
        )

        if search_value:
            queryset = queryset.filter(
                Q(cycle_number__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        queryset = queryset.order_by('-start_date', '-cycle_number')

        total_records = PhysicalCountCycle.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for cycle in queryset:
            status_map = {
                'planning': '<span class="badge bg-secondary">تخطيط</span>',
                'in_progress': '<span class="badge bg-info">جارية</span>',
                'completed': '<span class="badge bg-success">مكتملة</span>',
                'cancelled': '<span class="badge bg-danger">ملغاة</span>',
            }
            status_badge = status_map.get(cycle.status, cycle.status)

            # نسبة الإنجاز
            completion = cycle.get_completion_percentage()

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:cycle_detail', args=[cycle.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                cycle.cycle_number,
                cycle.name,
                cycle.get_cycle_type_display(),
                cycle.start_date.strftime('%Y-%m-%d'),
                f"{cycle.counted_assets} / {cycle.total_assets}",
                f"{completion:.1f}%",
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
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def count_line_ajax(request, pk):
    """تحديث سطر جرد عبر Ajax"""

    try:
        line = get_object_or_404(
            PhysicalCountLine,
            pk=pk,
            physical_count__company=request.current_company
        )

        from django.utils import timezone

        # تحديث البيانات
        line.is_found = request.POST.get('is_found') == '1'
        line.is_counted = True
        line.actual_location = request.POST.get('actual_location', '')
        line.notes = request.POST.get('notes', '')
        line.counted_date = timezone.now()
        line.counted_by = request.user

        if request.POST.get('actual_condition_id'):
            line.actual_condition_id = request.POST.get('actual_condition_id')

        line.save()

        # تحديث إحصائيات الجرد
        line.physical_count.update_statistics()

        return JsonResponse({
            'success': True,
            'message': 'تم تحديث سطر الجرد بنجاح',
            'line': {
                'is_found': line.is_found,
                'is_counted': line.is_counted,
                'has_variance': line.has_any_variance()
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في تحديث السطر: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def barcode_scan_ajax(request):
    """البحث عن أصل بالباركود"""

    barcode = request.POST.get('barcode', '').strip()

    if not barcode:
        return JsonResponse({'error': 'يجب إدخال الباركود'}, status=400)

    try:
        asset = Asset.objects.filter(
            company=request.current_company,
            barcode=barcode
        ).select_related('category', 'condition').first()

        if not asset:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم العثور على الأصل'
            })

        return JsonResponse({
            'success': True,
            'asset': {
                'id': asset.id,
                'asset_number': asset.asset_number,
                'name': asset.name,
                'category': asset.category.name,
                'condition': asset.condition.name if asset.condition else '',
                'location': asset.physical_location or '',
                'responsible': asset.responsible_employee.get_full_name() if asset.responsible_employee else ''
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في البحث: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def adjustment_datatable_ajax(request):
    """Ajax endpoint لجدول تسويات الجرد"""

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

    try:
        queryset = PhysicalCountAdjustment.objects.filter(
            company=request.current_company
        ).select_related('physical_count_line__asset', 'journal_entry')

        if search_value:
            queryset = queryset.filter(
                Q(adjustment_number__icontains=search_value) |
                Q(physical_count_line__asset__asset_number__icontains=search_value)
            )

        queryset = queryset.order_by('-adjustment_date', '-adjustment_number')

        total_records = PhysicalCountAdjustment.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for adj in queryset:
            status_map = {
                'draft': '<span class="badge bg-secondary">مسودة</span>',
                'approved': '<span class="badge bg-warning">معتمد</span>',
                'posted': '<span class="badge bg-success">مرحّل</span>',
                'cancelled': '<span class="badge bg-danger">ملغي</span>',
            }
            status_badge = status_map.get(adj.status, adj.status)

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:adjustment_detail', args=[adj.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                adj.adjustment_number,
                adj.adjustment_date.strftime('%Y-%m-%d'),
                adj.get_adjustment_type_display(),
                adj.physical_count_line.asset.asset_number,
                f"{adj.loss_amount:,.2f}",
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
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def upload_count_photo(request):
    """رفع صورة للجرد"""

    try:
        line_id = request.POST.get('line_id')
        photo = request.FILES.get('photo')

        if not line_id or not photo:
            return JsonResponse({'error': 'بيانات غير كاملة'}, status=400)

        line = get_object_or_404(
            PhysicalCountLine,
            pk=line_id,
            physical_count__company=request.current_company
        )

        # حفظ الصورة (يمكن تحسينه باستخدام storage)
        # هنا مثال بسيط
        photo_url = f"/media/count_photos/{line.physical_count.count_number}/{photo.name}"

        # إضافة الرابط للصور
        photos = line.photos if line.photos else []
        photos.append(photo_url)
        line.photos = photos
        line.save()

        return JsonResponse({
            'success': True,
            'message': 'تم رفع الصورة بنجاح',
            'photo_url': photo_url
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في رفع الصورة: {str(e)}'
        }, status=500)
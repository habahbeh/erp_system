# apps/assets/views/physical_count_views.py
"""
Views الجرد الفعلي للأصول - محسّنة وشاملة
- دورات الجرد
- عمليات الجرد الفعلي
- تسويات الجرد
- تحليل الفروقات
- تقارير الجرد
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView,
    DetailView, TemplateView
)
from django.db.models import (
    Q, Sum, Count, Avg, Max, Min, F,
    DecimalField, Case, When, Value
)
from django.db.models.functions import Coalesce, TruncMonth, TruncDate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
import json
from datetime import date, timedelta, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import os

from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine,
    PhysicalCountAdjustment, Asset, AssetCategory, AssetCondition
)
from apps.core.models import Branch


# ==================== Physical Count Cycles ====================

class PhysicalCountCycleListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة دورات الجرد - محسّنة"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_list.html'
    context_object_name = 'cycles'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 50

    def get_queryset(self):
        queryset = PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        ).prefetch_related('branches', 'asset_categories')

        # الفلترة المتقدمة
        status = self.request.GET.get('status')
        cycle_type = self.request.GET.get('cycle_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if cycle_type:
            queryset = queryset.filter(cycle_type=cycle_type)

        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(cycle_number__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # الترتيب
        sort_by = self.request.GET.get('sort', '-start_date')
        queryset = queryset.order_by(sort_by, '-cycle_number')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات مفصّلة
        cycles = PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        )

        stats = cycles.aggregate(
            total_count=Count('id'),
            planning_count=Count('id', filter=Q(status='planning')),
            in_progress_count=Count('id', filter=Q(status='in_progress')),
            completed_count=Count('id', filter=Q(status='completed')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),
            total_assets=Coalesce(Sum('total_assets'), 0),
            total_counted=Coalesce(Sum('counted_assets'), 0),
            total_variances=Coalesce(Sum('variance_count'), 0),
        )

        # دورة هذا العام
        this_year = cycles.filter(
            start_date__year=date.today().year
        ).count()

        stats['this_year'] = this_year

        # نسبة الإنجاز العامة
        if stats['total_assets'] > 0:
            completion_rate = (stats['total_counted'] / stats['total_assets']) * 100
        else:
            completion_rate = 0

        stats['completion_rate'] = round(completion_rate, 2)

        context.update({
            'title': _('دورات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'can_edit': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'can_export': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCountCycle.STATUS_CHOICES,
            'cycle_types': PhysicalCountCycle.CYCLE_TYPES,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                   CreateView):
    """إنشاء دورة جرد - محسّن"""

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

        # القيم الافتراضية
        form.fields['start_date'].initial = date.today()
        form.fields['end_date'].initial = date.today() + timedelta(days=30)
        form.fields['planned_completion_date'].initial = date.today() + timedelta(days=30)
        form.fields['cycle_type'].initial = 'annual'

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'CheckboxSelectMultiple', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            form.instance.company = self.request.current_company
            form.instance.created_by = self.request.user
            form.instance.status = 'planning'

            self.object = form.save()

            self.log_action('create', self.object)

            messages.success(
                self.request,
                f'✅ تم إنشاء دورة الجرد {self.object.cycle_number} بنجاح'
            )

            return redirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, f'❌ {str(e)}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('assets:cycle_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة دورة جرد'),
            'submit_text': _('إنشاء الدورة'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل دورة الجرد - محسّن"""

    model = PhysicalCountCycle
    template_name = 'assets/physical_count/cycle_detail.html'
    context_object_name = 'cycle'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCountCycle.objects.filter(
            company=self.request.current_company
        ).prefetch_related(
            'branches', 'asset_categories', 'team_members',
            'physical_counts', 'team_leader'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عمليات الجرد
        counts = self.object.physical_counts.select_related(
            'branch', 'supervisor'
        ).order_by('-count_date')

        # إحصائيات عمليات الجرد
        count_stats = counts.aggregate(
            total_count=Count('id'),
            draft_count=Count('id', filter=Q(status='draft')),
            in_progress_count=Count('id', filter=Q(status='in_progress')),
            completed_count=Count('id', filter=Q(status='completed')),
            approved_count=Count('id', filter=Q(status='approved')),
        )

        # نسبة الإنجاز
        completion_pct = self.object.get_completion_percentage()

        # الأيام المتبقية
        if self.object.planned_completion_date:
            days_remaining = (self.object.planned_completion_date - date.today()).days
        else:
            days_remaining = None

        # التحذيرات
        warnings = []
        if self.object.status == 'in_progress' and days_remaining and days_remaining < 7:
            warnings.append({
                'type': 'warning',
                'icon': 'fa-clock',
                'message': f'باقي {days_remaining} أيام فقط على الموعد المخطط'
            })

        if self.object.variance_count > 0:
            warnings.append({
                'type': 'danger',
                'icon': 'fa-exclamation-triangle',
                'message': f'يوجد {self.object.variance_count} فروقات تحتاج معالجة'
            })

        context.update({
            'title': f'دورة الجرد {self.object.cycle_number}',
            'can_edit': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_edit()  # ✅ استخدام method من Model
            ),
            'can_delete': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_delete()  # ✅ استخدام method من Model
            ),
            'can_start': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_start()  # ✅ استخدام method من Model
            ),
            'can_complete': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_complete()  # ✅ استخدام method من Model
            ),
            'counts': counts[:10],
            'count_stats': count_stats,
            'completion_pct': completion_pct,
            'days_remaining': days_remaining,
            'warnings': warnings,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': self.object.cycle_number, 'url': ''},
            ]
        })
        return context


class PhysicalCountCycleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                   UpdateView):
    """تعديل دورة جرد - محسّن"""

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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'CheckboxSelectMultiple', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            # ✅ التحقق من إمكانية التعديل
            if not self.object.can_edit():
                messages.error(
                    self.request,
                    '❌ لا يمكن تعديل هذه الدورة. قد تكون مكتملة أو لديها جرد معتمد'
                )
                return self.form_invalid(form)

            self.object = form.save()

            self.log_action('update', self.object)

            messages.success(
                self.request,
                f'✅ تم تحديث دورة الجرد {self.object.cycle_number} بنجاح'
            )

            return redirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, f'❌ {str(e)}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('assets:cycle_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل دورة الجرد {self.object.cycle_number}',
            'submit_text': _('حفظ التعديلات'),
            'is_update': True,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دورات الجرد'), 'url': reverse('assets:cycle_list')},
                {'title': self.object.cycle_number, 'url': reverse('assets:cycle_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class StartCycleView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """بدء دورة الجرد - جديد"""

    template_name = 'assets/physical_count/start_cycle.html'
    permission_required = 'assets.can_conduct_physical_count'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            cycle_id = kwargs.get('pk')
            cycle = get_object_or_404(
                PhysicalCountCycle,
                pk=cycle_id,
                company=request.current_company
            )

            # ✅ بدء الدورة باستخدام model method
            cycle.start_cycle(user=request.user)

            messages.success(
                request,
                f'✅ تم بدء دورة الجرد {cycle.cycle_number} بنجاح'
            )

            return redirect('assets:cycle_detail', pk=cycle.pk)

        except ValidationError as e:
            messages.error(request, f'❌ {str(e)}')
            return redirect('assets:cycle_detail', pk=cycle_id)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ خطأ في بدء الدورة: {str(e)}')
            return redirect('assets:cycle_detail', pk=cycle_id)


class CompleteCycleView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """إكمال دورة الجرد - جديد"""

    template_name = 'assets/physical_count/complete_cycle.html'
    permission_required = 'assets.can_conduct_physical_count'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            cycle_id = kwargs.get('pk')
            cycle = get_object_or_404(
                PhysicalCountCycle,
                pk=cycle_id,
                company=request.current_company
            )

            # ✅ إكمال الدورة باستخدام model method
            cycle.complete_cycle(user=request.user)

            messages.success(
                request,
                f'✅ تم إكمال دورة الجرد {cycle.cycle_number} بنجاح'
            )

            return redirect('assets:cycle_detail', pk=cycle.pk)

        except ValidationError as e:
            messages.error(request, f'❌ {str(e)}')
            return redirect('assets:cycle_detail', pk=cycle_id)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ خطأ في إكمال الدورة: {str(e)}')
            return redirect('assets:cycle_detail', pk=cycle_id)


# ==================== Physical Counts ====================

class PhysicalCountListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة عمليات الجرد - محسّنة"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_list.html'
    context_object_name = 'counts'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 50

    def get_queryset(self):
        queryset = PhysicalCount.objects.filter(
            company=self.request.current_company
        ).select_related('cycle', 'branch', 'supervisor', 'approved_by')

        # الفلترة المتقدمة
        status = self.request.GET.get('status')
        cycle = self.request.GET.get('cycle')
        branch = self.request.GET.get('branch')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        has_variances = self.request.GET.get('has_variances')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if cycle:
            queryset = queryset.filter(cycle_id=cycle)

        if branch:
            queryset = queryset.filter(branch_id=branch)

        if date_from:
            queryset = queryset.filter(count_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(count_date__lte=date_to)

        if has_variances == '1':
            queryset = queryset.filter(variance_count__gt=0)

        if search:
            queryset = queryset.filter(
                Q(count_number__icontains=search) |
                Q(location__icontains=search)
            )

        # الترتيب
        sort_by = self.request.GET.get('sort', '-count_date')
        queryset = queryset.order_by(sort_by, '-count_number')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الدورات النشطة
        active_cycles = PhysicalCountCycle.objects.filter(
            company=self.request.current_company,
            status__in=['planning', 'in_progress']
        ).order_by('-start_date')

        # الفروع
        branches = Branch.objects.filter(
            company=self.request.current_company
        ).order_by('code')

        # إحصائيات مفصّلة
        counts = PhysicalCount.objects.filter(
            company=self.request.current_company
        )

        stats = counts.aggregate(
            total_count=Count('id'),
            draft_count=Count('id', filter=Q(status='draft')),
            in_progress_count=Count('id', filter=Q(status='in_progress')),
            completed_count=Count('id', filter=Q(status='completed')),
            approved_count=Count('id', filter=Q(status='approved')),
            total_assets=Coalesce(Sum('total_assets'), 0),
            total_counted=Coalesce(Sum('counted_assets'), 0),
            total_found=Coalesce(Sum('found_assets'), 0),
            total_missing=Coalesce(Sum('missing_assets'), 0),
            total_variances=Coalesce(Sum('variance_count'), 0),
        )

        # نسبة الإنجاز
        if stats['total_assets'] > 0:
            completion_rate = (stats['total_counted'] / stats['total_assets']) * 100
            found_rate = (stats['total_found'] / stats['total_assets']) * 100
        else:
            completion_rate = 0
            found_rate = 0

        stats['completion_rate'] = round(completion_rate, 2)
        stats['found_rate'] = round(found_rate, 2)

        context.update({
            'title': _('عمليات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'can_export': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCount.STATUS_CHOICES,
            'active_cycles': active_cycles,
            'branches': branches,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء عملية جرد - محسّن"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_form.html'
    permission_required = 'assets.can_conduct_physical_count'
    fields = [
        'cycle', 'count_date', 'branch', 'location',
        'responsible_team', 'supervisor', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        company = self.request.current_company

        form.fields['cycle'].queryset = PhysicalCountCycle.objects.filter(
            company=company,
            status__in=['planning', 'in_progress']
        ).order_by('-start_date')

        # القيم الافتراضية
        form.fields['count_date'].initial = date.today()

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'CheckboxSelectMultiple', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            form.instance.company = self.request.current_company
            form.instance.created_by = self.request.user
            form.instance.status = 'draft'

            self.object = form.save()

            # إنشاء سطور الجرد للأصول
            assets = Asset.objects.filter(
                company=self.request.current_company,
                branch=self.object.branch,
                status='active'
            ).select_related('condition', 'responsible_employee')

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

            self.log_action('create', self.object)

            messages.success(
                self.request,
                f'✅ تم إنشاء عملية الجرد {self.object.count_number} بنجاح مع {assets.count()} أصل'
            )

            return redirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, f'❌ {str(e)}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('assets:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة عملية جرد'),
            'submit_text': _('إنشاء العملية'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل عملية الجرد - محسّن"""

    model = PhysicalCount
    template_name = 'assets/physical_count/count_detail.html'
    context_object_name = 'count'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCount.objects.filter(
            company=self.request.current_company
        ).select_related(
            'cycle', 'branch', 'supervisor', 'approved_by', 'created_by'
        ).prefetch_related('lines', 'responsible_team')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # سطور الجرد
        lines = self.object.lines.select_related(
            'asset', 'asset__category', 'expected_condition',
            'actual_condition', 'counted_by'
        ).order_by('line_number')

        # الفروقات
        variances = lines.filter(
            Q(has_location_variance=True) |
            Q(has_condition_variance=True) |
            Q(has_responsible_variance=True) |
            Q(is_found=False)
        )

        # إحصائيات الفروقات
        variance_stats = {
            'location': variances.filter(has_location_variance=True).count(),
            'condition': variances.filter(has_condition_variance=True).count(),
            'responsible': variances.filter(has_responsible_variance=True).count(),
            'missing': variances.filter(is_found=False).count(),
        }

        # نسبة الإنجاز
        if self.object.total_assets > 0:
            completion_pct = (self.object.counted_assets / self.object.total_assets) * 100
            found_pct = (self.object.found_assets / self.object.total_assets) * 100
        else:
            completion_pct = 0
            found_pct = 0

        # Timeline
        timeline = []
        if self.object.created_at:
            timeline.append({
                'date': self.object.created_at,
                'user': self.object.created_by,
                'action': 'إنشاء العملية',
                'icon': 'fa-plus-circle',
                'color': 'primary'
            })

        if self.object.status == 'approved' and self.object.approved_by:
            timeline.append({
                'date': self.object.approved_at,
                'user': self.object.approved_by,
                'action': 'اعتماد العملية',
                'icon': 'fa-check-circle',
                'color': 'success'
            })

        # التحذيرات
        warnings = []
        if variances.exists():
            warnings.append({
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'message': f'يوجد {variances.count()} فروقات تحتاج معالجة'
            })

        if self.object.missing_assets > 0:
            warnings.append({
                'type': 'danger',
                'icon': 'fa-exclamation-circle',
                'message': f'{self.object.missing_assets} أصول مفقودة'
            })

        context.update({
            'title': f'عملية الجرد {self.object.count_number}',
            'can_edit': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_edit()  # ✅ استخدام method من Model
            ),
            'can_delete': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_delete()  # ✅ استخدام method من Model
            ),
            'can_start': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_start()  # ✅ استخدام method من Model
            ),
            'can_complete': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_complete()  # ✅ استخدام method من Model
            ),
            'can_approve': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.can_approve()  # ✅ استخدام method من Model
            ),
            'lines': lines[:50],  # أول 50 سطر
            'variances': variances[:20],
            'variance_stats': variance_stats,
            'completion_pct': round(completion_pct, 2),
            'found_pct': round(found_pct, 2),
            'timeline': sorted(timeline, key=lambda x: x['date']),
            'warnings': warnings,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': self.object.count_number, 'url': ''},
            ]
        })
        return context


class PhysicalCountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل عملية جرد - محسّن"""

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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        company = self.request.current_company

        form.fields['cycle'].queryset = PhysicalCountCycle.objects.filter(
            company=company
        ).order_by('-start_date')

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'CheckboxSelectMultiple', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            self.object = form.save()

            self.log_action('update', self.object)

            messages.success(
                self.request,
                f'✅ تم تحديث عملية الجرد {self.object.count_number} بنجاح'
            )

            return redirect(self.get_success_url())

        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('assets:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل عملية الجرد {self.object.count_number}',
            'submit_text': _('حفظ التعديلات'),
            'is_update': True,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عمليات الجرد'), 'url': reverse('assets:count_list')},
                {'title': self.object.count_number, 'url': reverse('assets:count_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class StartCountView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """بدء عملية الجرد - جديد"""

    template_name = 'assets/physical_count/start_count.html'
    permission_required = 'assets.can_conduct_physical_count'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            count_id = kwargs.get('pk')
            count = get_object_or_404(
                PhysicalCount,
                pk=count_id,
                company=request.current_company,
                status='draft'
            )

            # بدء العملية
            count.status = 'in_progress'
            count.save()

            messages.success(
                request,
                f'✅ تم بدء عملية الجرد {count.count_number} بنجاح'
            )

            return redirect('assets:count_detail', pk=count.pk)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ خطأ في بدء العملية: {str(e)}')
            return redirect('assets:count_detail', pk=count_id)


class CompleteCountView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """إكمال عملية الجرد - جديد"""

    template_name = 'assets/physical_count/complete_count.html'
    permission_required = 'assets.can_conduct_physical_count'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            count_id = kwargs.get('pk')
            count = get_object_or_404(
                PhysicalCount,
                pk=count_id,
                company=request.current_company,
                status='in_progress'
            )

            # التحقق من الجرد الكامل
            uncounted = count.lines.filter(is_counted=False).count()

            if uncounted > 0:
                messages.warning(
                    request,
                    f'⚠️ يوجد {uncounted} أصول لم يتم جردها بعد'
                )

            # إكمال العملية
            count.status = 'completed'
            count.save()

            messages.success(
                request,
                f'✅ تم إكمال عملية الجرد {count.count_number} بنجاح'
            )

            return redirect('assets:count_detail', pk=count.pk)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ خطأ في إكمال العملية: {str(e)}')
            return redirect('assets:count_detail', pk=count_id)


# ==================== Physical Count Lines ====================

class PhysicalCountLineUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تحديث سطر جرد - محسّن"""

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
        ).select_related('asset', 'physical_count')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            form.instance.is_counted = True
            form.instance.counted_date = timezone.now()
            form.instance.counted_by = self.request.user

            self.object = form.save()

            # تحديث إحصائيات الجرد
            self.object.physical_count.update_statistics()

            messages.success(self.request, '✅ تم تحديث سطر الجرد بنجاح')

            return redirect('assets:count_detail', pk=self.object.physical_count.pk)

        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)


# ==================== Physical Count Adjustments ====================

class PhysicalCountAdjustmentListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة تسويات الجرد - محسّنة"""

    model = PhysicalCountAdjustment
    template_name = 'assets/physical_count/adjustment_list.html'
    context_object_name = 'adjustments'
    permission_required = 'assets.can_conduct_physical_count'
    paginate_by = 50

    def get_queryset(self):
        queryset = PhysicalCountAdjustment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'physical_count_line', 'physical_count_line__asset',
            'approved_by', 'journal_entry', 'created_by'
        )

        # الفلترة المتقدمة
        status = self.request.GET.get('status')
        adjustment_type = self.request.GET.get('adjustment_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if adjustment_type:
            queryset = queryset.filter(adjustment_type=adjustment_type)

        if date_from:
            queryset = queryset.filter(adjustment_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(adjustment_date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(adjustment_number__icontains=search) |
                Q(physical_count_line__asset__asset_number__icontains=search) |
                Q(reason__icontains=search)
            )

        # الترتيب
        sort_by = self.request.GET.get('sort', '-adjustment_date')
        queryset = queryset.order_by(sort_by, '-adjustment_number')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات مفصّلة
        adjustments = PhysicalCountAdjustment.objects.filter(
            company=self.request.current_company
        )

        stats = adjustments.aggregate(
            total_count=Count('id'),
            draft_count=Count('id', filter=Q(status='draft')),
            approved_count=Count('id', filter=Q(status='approved')),
            posted_count=Count('id', filter=Q(status='posted')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),

            # حسب النوع
            location_count=Count('id', filter=Q(adjustment_type='location')),
            condition_count=Count('id', filter=Q(adjustment_type='condition')),
            responsible_count=Count('id', filter=Q(adjustment_type='responsible')),
            missing_count=Count('id', filter=Q(adjustment_type='missing')),

            # المبالغ
            total_loss=Coalesce(Sum('loss_amount'), Decimal('0')),
        )

        context.update({
            'title': _('تسويات الجرد'),
            'can_add': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'can_export': self.request.user.has_perm('assets.can_conduct_physical_count'),
            'status_choices': PhysicalCountAdjustment.STATUS_CHOICES,
            'adjustment_types': PhysicalCountAdjustment.ADJUSTMENT_TYPES,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': ''},
            ]
        })
        return context


class PhysicalCountAdjustmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                        CreateView):
    """إنشاء تسوية جرد - محسّن"""

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

        # القيم الافتراضية
        form.fields['adjustment_date'].initial = date.today()

        # إضافة classes
        for field_name, field in form.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'Textarea']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ == 'Textarea':
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})

        return form

    @transaction.atomic
    def form_valid(self, form):
        try:
            form.instance.company = self.request.current_company
            form.instance.branch = self.request.current_branch
            form.instance.created_by = self.request.user
            form.instance.status = 'draft'

            self.object = form.save()

            self.log_action('create', self.object)

            messages.success(
                self.request,
                f'✅ تم إنشاء التسوية {self.object.adjustment_number} بنجاح'
            )

            return redirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, f'❌ {str(e)}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'❌ خطأ: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('assets:adjustment_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة تسوية جرد'),
            'submit_text': _('إنشاء التسوية'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': reverse('assets:adjustment_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class PhysicalCountAdjustmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل تسوية الجرد - محسّن"""

    model = PhysicalCountAdjustment
    template_name = 'assets/physical_count/adjustment_detail.html'
    context_object_name = 'adjustment'
    permission_required = 'assets.can_conduct_physical_count'

    def get_queryset(self):
        return PhysicalCountAdjustment.objects.filter(
            company=self.request.current_company
        ).select_related(
            'physical_count_line', 'physical_count_line__asset',
            'physical_count_line__asset__category',
            'approved_by', 'journal_entry', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Timeline
        timeline = []
        if self.object.created_at:
            timeline.append({
                'date': self.object.created_at,
                'user': self.object.created_by,
                'action': 'إنشاء التسوية',
                'icon': 'fa-plus-circle',
                'color': 'primary'
            })

        if self.object.status in ['approved', 'posted'] and self.object.approved_by:
            timeline.append({
                'date': self.object.approved_at,
                'user': self.object.approved_by,
                'action': 'اعتماد التسوية',
                'icon': 'fa-check-circle',
                'color': 'success'
            })

        context.update({
            'title': f'التسوية {self.object.adjustment_number}',
            'can_approve': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.status == 'draft'
            ),
            'can_post': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.status == 'approved'
            ),
            'can_cancel': (
                    self.request.user.has_perm('assets.can_conduct_physical_count') and
                    self.object.status in ['draft', 'approved']
            ),
            'timeline': sorted(timeline, key=lambda x: x['date']),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('تسويات الجرد'), 'url': reverse('assets:adjustment_list')},
                {'title': self.object.adjustment_number, 'url': ''},
            ]
        })
        return context


class ApproveAdjustmentView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """اعتماد التسوية - جديد"""

    template_name = 'assets/physical_count/approve_adjustment.html'
    permission_required = 'assets.can_conduct_physical_count'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            adjustment_id = kwargs.get('pk')
            adjustment = get_object_or_404(
                PhysicalCountAdjustment,
                pk=adjustment_id,
                company=request.current_company,
                status='draft'
            )

            approval_notes = request.POST.get('approval_notes', '')

            # اعتماد التسوية
            adjustment.status = 'approved'
            adjustment.approved_by = request.user
            adjustment.approved_at = timezone.now()
            if approval_notes:
                adjustment.notes = f"{adjustment.notes}\nملاحظات: {approval_notes}" if adjustment.notes else f"ملاحظات: {approval_notes}"
            adjustment.save()

            messages.success(
                request,
                f'✅ تم اعتماد التسوية {adjustment.adjustment_number} بنجاح'
            )

            return redirect('assets:adjustment_detail', pk=adjustment.pk)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ خطأ في الاعتماد: {str(e)}')
            return redirect('assets:adjustment_detail', pk=adjustment_id)


# ==================== Ajax Views - محسّنة ====================

@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def approve_physical_count(request, pk):
    """اعتماد عملية جرد - محسّن"""

    try:
        count = get_object_or_404(
            PhysicalCount,
            pk=pk,
            company=request.current_company,
            status='completed'
        )

        approval_notes = request.POST.get('approval_notes', '')

        # اعتماد الجرد
        count.approve(user=request.user)

        if approval_notes:
            count.notes = f"{count.notes}\nملاحظات: {approval_notes}" if count.notes else f"ملاحظات: {approval_notes}"
            count.save()

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
    """ترحيل تسوية جرد - محسّن"""

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
@require_http_methods(["POST"])
def count_line_ajax(request, pk):
    """تحديث سطر جرد عبر Ajax - محسّن"""

    try:
        line = get_object_or_404(
            PhysicalCountLine,
            pk=pk,
            physical_count__company=request.current_company,
            physical_count__status__in=['draft', 'in_progress']
        )

        # تحديث البيانات
        line.is_found = request.POST.get('is_found') == '1'
        line.is_counted = True
        line.actual_location = request.POST.get('actual_location', '')
        line.notes = request.POST.get('notes', '')
        line.counted_date = timezone.now()
        line.counted_by = request.user

        if request.POST.get('actual_condition_id'):
            line.actual_condition_id = request.POST.get('actual_condition_id')

        if request.POST.get('actual_responsible_id'):
            line.actual_responsible_id = request.POST.get('actual_responsible_id')

        line.save()

        # تحديث إحصائيات الجرد
        line.physical_count.update_statistics()

        return JsonResponse({
            'success': True,
            'message': 'تم تحديث سطر الجرد بنجاح',
            'line': {
                'is_found': line.is_found,
                'is_counted': line.is_counted,
                'has_variance': line.has_any_variance(),
                'requires_adjustment': line.requires_adjustment
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
def bulk_count_lines_ajax(request):
    """جرد جماعي للأصول - جديد"""

    try:
        line_ids = request.POST.getlist('line_ids[]')
        is_found = request.POST.get('is_found') == '1'

        if not line_ids:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم تحديد سطور'
            }, status=400)

        success_count = 0
        error_count = 0

        for line_id in line_ids:
            try:
                line = PhysicalCountLine.objects.get(
                    pk=line_id,
                    physical_count__company=request.current_company,
                    physical_count__status__in=['draft', 'in_progress']
                )

                line.is_found = is_found
                line.is_counted = True
                line.counted_date = timezone.now()
                line.counted_by = request.user
                line.save()

                success_count += 1
            except Exception:
                error_count += 1

        # تحديث الإحصائيات
        if success_count > 0:
            first_line = PhysicalCountLine.objects.get(pk=line_ids[0])
            first_line.physical_count.update_statistics()

        return JsonResponse({
            'success': True,
            'message': f'تم جرد {success_count} أصول بنجاح',
            'processed': success_count,
            'errors': error_count
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في الجرد الجماعي: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def barcode_scan_ajax(request):
    """البحث عن أصل بالباركود - محسّن"""

    barcode = request.POST.get('barcode', '').strip()
    count_id = request.POST.get('count_id')

    if not barcode:
        return JsonResponse({'error': 'يجب إدخال الباركود'}, status=400)

    try:
        # البحث عن الأصل
        asset = Asset.objects.filter(
            company=request.current_company,
            barcode=barcode
        ).select_related('category', 'condition', 'responsible_employee').first()

        if not asset:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم العثور على الأصل'
            })

        # البحث عن سطر الجرد
        count_line = None
        if count_id:
            count_line = PhysicalCountLine.objects.filter(
                physical_count_id=count_id,
                asset=asset
            ).first()

        return JsonResponse({
            'success': True,
            'asset': {
                'id': asset.id,
                'asset_number': asset.asset_number,
                'name': asset.name,
                'category': asset.category.name,
                'condition': asset.condition.name if asset.condition else '',
                'location': asset.physical_location or '',
                'responsible': asset.responsible_employee.get_full_name() if asset.responsible_employee else '',
                'barcode': asset.barcode,
            },
            'count_line': {
                'id': count_line.id if count_line else None,
                'is_counted': count_line.is_counted if count_line else False,
                'is_found': count_line.is_found if count_line else None,
            } if count_line else None
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في البحث: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["POST"])
def upload_count_photo(request):
    """رفع صورة للجرد - محسّن"""

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

        # حفظ الملف
        from django.conf import settings

        upload_dir = os.path.join(
            settings.MEDIA_ROOT,
            'count_photos',
            line.physical_count.count_number
        )
        os.makedirs(upload_dir, exist_ok=True)

        # اسم فريد للملف
        import uuid
        file_extension = os.path.splitext(photo.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        photo_path = os.path.join(upload_dir, unique_filename)

        with open(photo_path, 'wb+') as destination:
            for chunk in photo.chunks():
                destination.write(chunk)

        photo_url = f"/media/count_photos/{line.physical_count.count_number}/{unique_filename}"

        # إضافة للقائمة
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
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في رفع الصورة: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def count_datatable_ajax(request):
    """Ajax endpoint لجدول عمليات الجرد - محسّن"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        # الفلاتر
        status = request.GET.get('status', '')

        # Query
        queryset = PhysicalCount.objects.filter(
            company=request.current_company
        ).select_related('cycle', 'branch')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(count_number__icontains=search_value) |
                Q(location__icontains=search_value)
            )

        # الترتيب
        order_column_index = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'desc')

        order_columns = {
            '0': 'count_number',
            '1': 'count_date',
            '2': 'branch__name',
        }

        if order_column_index and order_column_index in order_columns:
            order_field = order_columns[order_column_index]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field, '-count_number')
        else:
            queryset = queryset.order_by('-count_date', '-count_number')

        # العد
        total_records = PhysicalCount.objects.filter(
            company=request.current_company
        ).count()
        filtered_records = queryset.count()

        # Pagination
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_view = request.user.has_perm('assets.can_conduct_physical_count')

        for count in queryset:
            # الحالة
            status_map = {
                'draft': '<span class="badge bg-secondary"><i class="fas fa-file"></i> مسودة</span>',
                'in_progress': '<span class="badge bg-info"><i class="fas fa-spinner fa-spin"></i> جاري</span>',
                'completed': '<span class="badge bg-warning"><i class="fas fa-check"></i> مكتمل</span>',
                'approved': '<span class="badge bg-success"><i class="fas fa-check-double"></i> معتمد</span>',
                'cancelled': '<span class="badge bg-danger"><i class="fas fa-ban"></i> ملغي</span>',
            }
            status_badge = status_map.get(count.status, count.status)

            # نسبة الإنجاز
            completion = 0
            if count.total_assets > 0:
                completion = (count.counted_assets / count.total_assets) * 100

            completion_html = f'''
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar {'bg-success' if completion == 100 else 'bg-info'}" 
                         role="progressbar" 
                         style="width: {completion}%"
                         aria-valuenow="{completion}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        {completion:.0f}%
                    </div>
                </div>
            '''

            # الفروقات
            variance_html = f'''<span class="badge {'bg-danger' if count.variance_count > 0 else 'bg-success'}">
                {count.variance_count}
            </span>'''

            # أزرار الإجراءات
            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('assets:count_detail', args=[count.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            actions_html = '<div class="btn-group" role="group">' + ' '.join(actions) + '</div>' if actions else '-'

            data.append([
                f'<a href="{reverse("assets:count_detail", args=[count.pk])}">{count.count_number}</a>',
                count.count_date.strftime('%Y-%m-%d'),
                count.branch.name if count.branch else '-',
                f"{count.counted_assets} / {count.total_assets}",
                completion_html,
                variance_html,
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
        }, status=500)


# أضف هذا الكود في نهاية ملف physical_count_views.py قبل export_count_excel

@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def cycle_datatable_ajax(request):
    """Ajax endpoint لجدول دورات الجرد - محسّن"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        # الفلاتر
        status = request.GET.get('status', '')

        # Query
        queryset = PhysicalCountCycle.objects.filter(
            company=request.current_company
        )

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(cycle_number__icontains=search_value) |
                Q(name__icontains=search_value)
            )

        # الترتيب
        order_column_index = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'desc')

        order_columns = {
            '0': 'cycle_number',
            '1': 'name',
            '2': 'cycle_type',
            '3': 'start_date',
        }

        if order_column_index and order_column_index in order_columns:
            order_field = order_columns[order_column_index]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field, '-cycle_number')
        else:
            queryset = queryset.order_by('-start_date', '-cycle_number')

        # العد
        total_records = PhysicalCountCycle.objects.filter(
            company=request.current_company
        ).count()
        filtered_records = queryset.count()

        # Pagination
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_view = request.user.has_perm('assets.can_conduct_physical_count')

        for cycle in queryset:
            # الحالة
            status_map = {
                'planning': '<span class="badge bg-secondary"><i class="fas fa-clipboard-list"></i> تخطيط</span>',
                'in_progress': '<span class="badge bg-info"><i class="fas fa-spinner fa-spin"></i> جارية</span>',
                'completed': '<span class="badge bg-success"><i class="fas fa-check-circle"></i> مكتملة</span>',
                'cancelled': '<span class="badge bg-danger"><i class="fas fa-ban"></i> ملغاة</span>',
            }
            status_badge = status_map.get(cycle.status, cycle.status)

            # نسبة الإنجاز
            completion = cycle.get_completion_percentage()

            completion_html = f'''
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar {'bg-success' if completion == 100 else 'bg-info'}" 
                         role="progressbar" 
                         style="width: {completion}%"
                         aria-valuenow="{completion}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        {completion:.0f}%
                    </div>
                </div>
            '''

            # أزرار الإجراءات
            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('assets:cycle_detail', args=[cycle.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            actions_html = '<div class="btn-group" role="group">' + ' '.join(actions) + '</div>' if actions else '-'

            data.append([
                f'<a href="{reverse("assets:cycle_detail", args=[cycle.pk])}">{cycle.cycle_number}</a>',
                f'''<div>
                    <strong>{cycle.name}</strong>
                    <br><small class="text-muted">{cycle.get_cycle_type_display()}</small>
                </div>''',
                cycle.start_date.strftime('%Y-%m-%d'),
                f"{cycle.counted_assets} / {cycle.total_assets}",
                completion_html,
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
        }, status=500)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
@require_http_methods(["GET"])
def adjustment_datatable_ajax(request):
    """Ajax endpoint لجدول تسويات الجرد - محسّن"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        # الفلاتر
        status = request.GET.get('status', '')
        adjustment_type = request.GET.get('adjustment_type', '')

        # Query
        queryset = PhysicalCountAdjustment.objects.filter(
            company=request.current_company
        ).select_related(
            'physical_count_line__asset',
            'physical_count_line__asset__category',
            'journal_entry',
            'approved_by'
        )

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if adjustment_type:
            queryset = queryset.filter(adjustment_type=adjustment_type)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(adjustment_number__icontains=search_value) |
                Q(physical_count_line__asset__asset_number__icontains=search_value) |
                Q(reason__icontains=search_value)
            )

        # الترتيب
        order_column_index = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'desc')

        order_columns = {
            '0': 'adjustment_number',
            '1': 'adjustment_date',
            '2': 'adjustment_type',
            '3': 'physical_count_line__asset__asset_number',
            '4': 'loss_amount',
        }

        if order_column_index and order_column_index in order_columns:
            order_field = order_columns[order_column_index]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field, '-adjustment_number')
        else:
            queryset = queryset.order_by('-adjustment_date', '-adjustment_number')

        # العد
        total_records = PhysicalCountAdjustment.objects.filter(
            company=request.current_company
        ).count()
        filtered_records = queryset.count()

        # Pagination
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_view = request.user.has_perm('assets.can_conduct_physical_count')

        for adj in queryset:
            # الحالة
            status_map = {
                'draft': '<span class="badge bg-secondary"><i class="fas fa-file"></i> مسودة</span>',
                'approved': '<span class="badge bg-warning"><i class="fas fa-check"></i> معتمد</span>',
                'posted': '<span class="badge bg-success"><i class="fas fa-check-double"></i> مرحّل</span>',
                'cancelled': '<span class="badge bg-danger"><i class="fas fa-ban"></i> ملغي</span>',
            }
            status_badge = status_map.get(adj.status, adj.status)

            # النوع
            type_icons = {
                'location': '<i class="fas fa-map-marker-alt text-primary"></i>',
                'condition': '<i class="fas fa-wrench text-warning"></i>',
                'responsible': '<i class="fas fa-user text-info"></i>',
                'missing': '<i class="fas fa-exclamation-triangle text-danger"></i>',
            }
            type_icon = type_icons.get(adj.adjustment_type, '')
            type_display = adj.get_adjustment_type_display()

            # أزرار الإجراءات
            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('assets:adjustment_detail', args=[adj.pk])}" 
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            actions_html = '<div class="btn-group" role="group">' + ' '.join(actions) + '</div>' if actions else '-'

            data.append([
                f'<a href="{reverse("assets:adjustment_detail", args=[adj.pk])}">{adj.adjustment_number}</a>',
                adj.adjustment_date.strftime('%Y-%m-%d'),
                f'{type_icon} {type_display}',
                f'''<div>
                    <strong><a href="{reverse("assets:asset_detail", args=[adj.physical_count_line.asset.pk])}">{adj.physical_count_line.asset.asset_number}</a></strong>
                    <br><small class="text-muted">{adj.physical_count_line.asset.name}</small>
                </div>''',
                f'<div class="text-end"><strong class="text-danger">{adj.loss_amount:,.2f}</strong></div>',
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
        }, status=500)
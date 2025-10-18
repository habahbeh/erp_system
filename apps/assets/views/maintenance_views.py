# apps/assets/views/maintenance_views.py
"""
Maintenance Views - إدارة الصيانة
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q, Sum, Count, Avg, F
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from decimal import Decimal
from datetime import date, datetime, timedelta
import json

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message, company_required
from ..models import (
    Asset, AssetMaintenance, MaintenanceSchedule, MaintenanceType
)
from ..forms import AssetMaintenanceForm, MaintenanceScheduleForm


class MaintenanceScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة جداول الصيانة الدورية"""

    template_name = 'assets/maintenance/schedule_list.html'
    permission_required = 'assets.view_maintenanceschedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_schedules = MaintenanceSchedule.objects.filter(
            company=self.request.current_company
        ).count()

        active_schedules = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).count()

        # الصيانات القادمة خلال 7 أيام
        upcoming = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True,
            next_maintenance_date__lte=date.today() + timedelta(days=7)
        ).count()

        context.update({
            'title': _('جداول الصيانة'),
            'can_add': self.request.user.has_perm('assets.add_maintenanceschedule'),
            'can_edit': self.request.user.has_perm('assets.change_maintenanceschedule'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenanceschedule'),
            'total_schedules': total_schedules,
            'active_schedules': active_schedules,
            'upcoming': upcoming,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('جداول الصيانة'), 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    CreateView):
    """إنشاء جدول صيانة جديد"""

    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.add_maintenanceschedule'
    success_url = reverse_lazy('assets:maintenance_schedule_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء جدول الصيانة {self.object.schedule_number} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء جدول صيانة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('جداول الصيانة'), 'url': reverse('assets:maintenance_schedule_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    UpdateView):
    """تعديل جدول صيانة"""

    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.change_maintenanceschedule'

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث جدول الصيانة {self.object.schedule_number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('assets:maintenance_schedule_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.schedule_number}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('جداول الصيانة'), 'url': reverse('assets:maintenance_schedule_list')},
                {'title': f'تعديل {self.object.schedule_number}', 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل جدول صيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_detail.html'
    context_object_name = 'schedule'
    permission_required = 'assets.view_maintenanceschedule'

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'maintenance_type', 'assigned_to', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الصيانات المنفذة من هذا الجدول
        completed_maintenances = AssetMaintenance.objects.filter(
            maintenance_schedule=self.object
        ).order_by('-scheduled_date')

        context.update({
            'title': f'جدول الصيانة {self.object.schedule_number}',
            'can_edit': self.request.user.has_perm('assets.change_maintenanceschedule'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenanceschedule'),
            'completed_maintenances': completed_maintenances,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('جداول الصيانة'), 'url': reverse('assets:maintenance_schedule_list')},
                {'title': self.object.schedule_number, 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف جدول صيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_confirm_delete.html'
    permission_required = 'assets.delete_maintenanceschedule'
    success_url = reverse_lazy('assets:maintenance_schedule_list')

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        schedule_number = self.object.schedule_number
        messages.success(request, f'تم حذف جدول الصيانة {schedule_number} بنجاح')
        return super().delete(request, *args, **kwargs)


class AssetMaintenanceListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الصيانات المنفذة"""

    template_name = 'assets/maintenance/maintenance_list.html'
    permission_required = 'assets.view_assetmaintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_maintenances = AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).count()

        completed = AssetMaintenance.objects.filter(
            company=self.request.current_company,
            status='completed'
        ).count()

        in_progress = AssetMaintenance.objects.filter(
            company=self.request.current_company,
            status='in_progress'
        ).count()

        # التكلفة الإجمالية هذا الشهر
        this_month_cost = AssetMaintenance.objects.filter(
            company=self.request.current_company,
            scheduled_date__year=date.today().year,
            scheduled_date__month=date.today().month
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

        context.update({
            'title': _('سجلات الصيانة'),
            'can_add': self.request.user.has_perm('assets.add_assetmaintenance'),
            'can_edit': self.request.user.has_perm('assets.change_assetmaintenance'),
            'can_delete': self.request.user.has_perm('assets.delete_assetmaintenance'),
            'total_maintenances': total_maintenances,
            'completed': completed,
            'in_progress': in_progress,
            'this_month_cost': this_month_cost,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الصيانة'), 'url': ''}
            ],
        })
        return context


class AssetMaintenanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سجل صيانة جديد"""

    model = AssetMaintenance
    form_class = AssetMaintenanceForm
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.add_assetmaintenance'
    success_url = reverse_lazy('assets:maintenance_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء سجل الصيانة {self.object.maintenance_number} بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء سجل صيانة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الصيانة'), 'url': reverse('assets:maintenance_list')},
                {'title': _('إنشاء جديد'), 'url': ''}
            ],
        })
        return context


class AssetMaintenanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سجل صيانة"""

    model = AssetMaintenance
    form_class = AssetMaintenanceForm
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.change_assetmaintenance'

    def get_queryset(self):
        return AssetMaintenance.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث سجل الصيانة {self.object.maintenance_number} بنجاح')
        return response

    def get_success_url(self):
        return reverse('assets:maintenance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل {self.object.maintenance_number}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الصيانة'), 'url': reverse('assets:maintenance_list')},
                {'title': f'تعديل {self.object.maintenance_number}', 'url': ''}
            ],
        })
        return context


class AssetMaintenanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل سجل صيانة"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_detail.html'
    context_object_name = 'maintenance'
    permission_required = 'assets.view_assetmaintenance'

    def get_queryset(self):
        return AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'maintenance_type', 'maintenance_schedule',
            'performed_by', 'external_vendor', 'journal_entry', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'سجل الصيانة {self.object.maintenance_number}',
            'can_edit': self.request.user.has_perm('assets.change_assetmaintenance'),
            'can_delete': self.request.user.has_perm('assets.delete_assetmaintenance'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('سجلات الصيانة'), 'url': reverse('assets:maintenance_list')},
                {'title': self.object.maintenance_number, 'url': ''}
            ],
        })
        return context


class AssetMaintenanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف سجل صيانة"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_confirm_delete.html'
    permission_required = 'assets.delete_assetmaintenance'
    success_url = reverse_lazy('assets:maintenance_list')

    def get_queryset(self):
        return AssetMaintenance.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status == 'completed' and self.object.journal_entry:
            messages.error(request, 'لا يمكن حذف صيانة مكتملة ولها قيد محاسبي')
            return redirect('assets:maintenance_detail', pk=self.object.pk)

        maintenance_number = self.object.maintenance_number
        messages.success(request, f'تم حذف سجل الصيانة {maintenance_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views

@login_required
@permission_required_with_message('assets.view_maintenanceschedule')
@require_http_methods(["GET"])
def maintenance_schedule_datatable_ajax(request):
    """Ajax endpoint لجدول جداول الصيانة"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    status = request.GET.get('status', '')
    frequency = request.GET.get('frequency', '')

    try:
        queryset = MaintenanceSchedule.objects.filter(
            company=request.current_company
        ).select_related('asset', 'maintenance_type', 'assigned_to')

        # تطبيق الفلاتر
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        if frequency:
            queryset = queryset.filter(frequency=frequency)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(schedule_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('next_maintenance_date')

        total_records = MaintenanceSchedule.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_maintenanceschedule')
        can_delete = request.user.has_perm('assets.delete_maintenanceschedule')

        for schedule in queryset:
            # حالة النشاط
            status_badge = '<span class="badge bg-success">نشط</span>' if schedule.is_active else '<span class="badge bg-secondary">غير نشط</span>'

            # تنبيه إذا كانت قريبة
            if schedule.is_due_soon():
                next_date = f'<span class="text-warning fw-bold">{schedule.next_maintenance_date.strftime("%Y-%m-%d")}</span>'
            elif schedule.is_overdue():
                next_date = f'<span class="text-danger fw-bold">{schedule.next_maintenance_date.strftime("%Y-%m-%d")}</span>'
            else:
                next_date = schedule.next_maintenance_date.strftime('%Y-%m-%d')

            # الأزرار
            actions = []
            actions.append(f'''
                <a href="{reverse('assets:maintenance_schedule_detail', args=[schedule.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_schedule_update', args=[schedule.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_schedule_delete', args=[schedule.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                schedule.schedule_number,
                f"{schedule.asset.asset_number} - {schedule.asset.name}",
                schedule.maintenance_type.name,
                schedule.get_frequency_display(),
                next_date,
                schedule.assigned_to.get_full_name() if schedule.assigned_to else '--',
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
@permission_required_with_message('assets.view_assetmaintenance')
@require_http_methods(["GET"])
def asset_maintenance_datatable_ajax(request):
    """Ajax endpoint لجدول سجلات الصيانة"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        queryset = AssetMaintenance.objects.filter(
            company=request.current_company
        ).select_related('asset', 'maintenance_type', 'performed_by')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if category:
            queryset = queryset.filter(maintenance_category=category)

        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(maintenance_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-scheduled_date')

        total_records = AssetMaintenance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_assetmaintenance')
        can_delete = request.user.has_perm('assets.delete_assetmaintenance')

        for maintenance in queryset:
            # حالة الصيانة
            status_badges = {
                'scheduled': '<span class="badge bg-info">مجدولة</span>',
                'in_progress': '<span class="badge bg-warning">جارية</span>',
                'completed': '<span class="badge bg-success">مكتملة</span>',
                'cancelled': '<span class="badge bg-danger">ملغاة</span>',
            }
            status_badge = status_badges.get(maintenance.status, maintenance.status)

            # الأزرار
            actions = []
            actions.append(f'''
                <a href="{reverse('assets:maintenance_detail', args=[maintenance.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if can_edit and maintenance.status != 'completed':
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_update', args=[maintenance.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and maintenance.status != 'completed':
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_delete', args=[maintenance.pk])}" 
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                maintenance.maintenance_number,
                maintenance.scheduled_date.strftime('%Y-%m-%d'),
                f"{maintenance.asset.asset_number} - {maintenance.asset.name}",
                maintenance.maintenance_type.name,
                maintenance.get_maintenance_category_display(),
                f"{maintenance.total_cost:,.3f}",
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
@permission_required_with_message('assets.change_assetmaintenance')
@require_http_methods(["POST"])
def mark_maintenance_completed_ajax(request, pk):
    """وضع علامة مكتمل على الصيانة"""

    try:
        maintenance = get_object_or_404(
            AssetMaintenance,
            pk=pk,
            company=request.current_company
        )

        if maintenance.status == 'completed':
            return JsonResponse({
                'success': False,
                'message': 'الصيانة مكتملة بالفعل'
            })

        completion_date = request.POST.get('completion_date', date.today().strftime('%Y-%m-%d'))
        maintenance.mark_as_completed(completion_date=datetime.strptime(completion_date, '%Y-%m-%d').date())

        return JsonResponse({
            'success': True,
            'message': f'تم وضع علامة مكتمل على الصيانة {maintenance.maintenance_number}'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })
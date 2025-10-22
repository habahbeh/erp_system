# apps/assets/views/maintenance_views.py
"""
Views إدارة الصيانة
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
    MaintenanceType, MaintenanceSchedule, AssetMaintenance, Asset
)
from apps.core.models import BusinessPartner


# ==================== Maintenance Types ====================

class MaintenanceTypeListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة أنواع الصيانة"""

    model = MaintenanceType
    template_name = 'assets/maintenance/type_list.html'
    context_object_name = 'maintenance_types'
    permission_required = 'assets.view_maintenancetype'
    paginate_by = 50

    def get_queryset(self):
        return MaintenanceType.objects.filter(is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('أنواع الصيانة'),
            'can_add': self.request.user.has_perm('assets.add_maintenancetype'),
            'can_edit': self.request.user.has_perm('assets.change_maintenancetype'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenancetype'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('أنواع الصيانة'), 'url': ''},
            ]
        })
        return context


class MaintenanceTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء نوع صيانة"""

    model = MaintenanceType
    template_name = 'assets/maintenance/type_form.html'
    permission_required = 'assets.add_maintenancetype'
    fields = ['code', 'name', 'name_en', 'description', 'is_active']
    success_url = reverse_lazy('assets:maintenance_type_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم إنشاء نوع الصيانة {form.instance.name} بنجاح')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة نوع صيانة'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('أنواع الصيانة'), 'url': reverse('assets:maintenance_type_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class MaintenanceTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل نوع صيانة"""

    model = MaintenanceType
    template_name = 'assets/maintenance/type_form.html'
    permission_required = 'assets.change_maintenancetype'
    fields = ['code', 'name', 'name_en', 'description', 'is_active']
    success_url = reverse_lazy('assets:maintenance_type_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث نوع الصيانة {form.instance.name} بنجاح')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل نوع الصيانة {self.object.name}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('أنواع الصيانة'), 'url': reverse('assets:maintenance_type_list')},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class MaintenanceTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف نوع صيانة"""

    model = MaintenanceType
    template_name = 'assets/maintenance/type_confirm_delete.html'
    permission_required = 'assets.delete_maintenancetype'
    success_url = reverse_lazy('assets:maintenance_type_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.schedules.exists() or self.object.maintenances.exists():
            messages.error(request, _('لا يمكن حذف نوع صيانة مستخدم'))
            return redirect('assets:maintenance_type_list')

        messages.success(request, f'تم حذف نوع الصيانة {self.object.name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Maintenance Schedules ====================

class MaintenanceScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة جدولة الصيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_list.html'
    context_object_name = 'schedules'
    permission_required = 'assets.view_maintenanceschedule'
    paginate_by = 25

    def get_queryset(self):
        queryset = MaintenanceSchedule.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'maintenance_type', 'assigned_to'
        )

        # الفلترة
        asset = self.request.GET.get('asset')
        maintenance_type = self.request.GET.get('maintenance_type')
        is_active = self.request.GET.get('is_active')
        overdue = self.request.GET.get('overdue')

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if maintenance_type:
            queryset = queryset.filter(maintenance_type_id=maintenance_type)

        if is_active:
            queryset = queryset.filter(is_active=(is_active == '1'))

        if overdue == '1':
            queryset = queryset.filter(next_maintenance_date__lt=date.today())

        return queryset.order_by('next_maintenance_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # أنواع الصيانة
        maintenance_types = MaintenanceType.objects.filter(is_active=True)

        # الصيانات المتأخرة
        overdue_count = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True,
            next_maintenance_date__lt=date.today()
        ).count()

        context.update({
            'title': _('جدولة الصيانة'),
            'can_add': self.request.user.has_perm('assets.add_maintenanceschedule'),
            'can_edit': self.request.user.has_perm('assets.change_maintenanceschedule'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenanceschedule'),
            'maintenance_types': maintenance_types,
            'overdue_count': overdue_count,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('جدولة الصيانة'), 'url': ''},
            ]
        })
        return context


class MaintenanceScheduleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    CreateView):
    """إنشاء جدولة صيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.add_maintenanceschedule'
    fields = [
        'asset', 'maintenance_type', 'frequency', 'custom_days',
        'start_date', 'end_date', 'alert_before_days',
        'assigned_to', 'estimated_cost', 'description', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        form.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
            is_active=True
        )

        form.fields['start_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء جدولة الصيانة {self.object.schedule_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:schedule_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة جدولة صيانة'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('جدولة الصيانة'), 'url': reverse('assets:schedule_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class MaintenanceScheduleDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل جدولة الصيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_detail.html'
    context_object_name = 'schedule'
    permission_required = 'assets.view_maintenanceschedule'

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'maintenance_type', 'assigned_to'
        ).prefetch_related('maintenances')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الصيانات المنفذة
        maintenances = self.object.maintenances.order_by('-scheduled_date')[:10]

        context.update({
            'title': f'الجدولة {self.object.schedule_number}',
            'can_edit': self.request.user.has_perm('assets.change_maintenanceschedule'),
            'can_delete': self.request.user.has_perm('assets.delete_maintenanceschedule'),
            'maintenances': maintenances,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('جدولة الصيانة'), 'url': reverse('assets:schedule_list')},
                {'title': self.object.schedule_number, 'url': ''},
            ]
        })
        return context


class MaintenanceScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    UpdateView):
    """تعديل جدولة صيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.change_maintenanceschedule'
    fields = [
        'asset', 'maintenance_type', 'frequency', 'custom_days',
        'start_date', 'end_date', 'alert_before_days',
        'assigned_to', 'estimated_cost', 'is_active', 'description', 'notes'
    ]

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(company=self.request.current_company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company
        )

        form.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
            is_active=True
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث الجدولة {self.object.schedule_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:schedule_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الجدولة {self.object.schedule_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('جدولة الصيانة'), 'url': reverse('assets:schedule_list')},
                {'title': self.object.schedule_number, 'url': reverse('assets:schedule_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class MaintenanceScheduleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف جدولة صيانة"""

    model = MaintenanceSchedule
    template_name = 'assets/maintenance/schedule_confirm_delete.html'
    permission_required = 'assets.delete_maintenanceschedule'
    success_url = reverse_lazy('assets:schedule_list')

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'تم حذف الجدولة {self.object.schedule_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Asset Maintenance ====================

class AssetMaintenanceListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة صيانة الأصول"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_list.html'
    context_object_name = 'maintenances'
    permission_required = 'assets.view_assetmaintenance'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'asset__category', 'maintenance_type',
            'maintenance_schedule', 'performed_by', 'external_vendor'
        )

        # الفلترة
        status = self.request.GET.get('status')
        asset = self.request.GET.get('asset')
        maintenance_type = self.request.GET.get('maintenance_type')
        maintenance_category = self.request.GET.get('maintenance_category')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if maintenance_type:
            queryset = queryset.filter(maintenance_type_id=maintenance_type)

        if maintenance_category:
            queryset = queryset.filter(maintenance_category=maintenance_category)

        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)

        if search:
            queryset = queryset.filter(
                Q(maintenance_number__icontains=search) |
                Q(asset__asset_number__icontains=search) |
                Q(asset__name__icontains=search)
            )

        return queryset.order_by('-scheduled_date', '-maintenance_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # أنواع الصيانة
        maintenance_types = MaintenanceType.objects.filter(is_active=True)

        context.update({
            'title': _('صيانة الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assetmaintenance'),
            'can_edit': self.request.user.has_perm('assets.change_assetmaintenance'),
            'status_choices': AssetMaintenance.STATUS_CHOICES,
            'category_choices': AssetMaintenance.MAINTENANCE_CATEGORY,
            'maintenance_types': maintenance_types,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('صيانة الأصول'), 'url': ''},
            ]
        })
        return context


class AssetMaintenanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء صيانة أصل"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.add_assetmaintenance'
    fields = [
        'asset', 'maintenance_type', 'maintenance_category',
        'maintenance_schedule', 'scheduled_date', 'start_date',
        'performed_by', 'external_vendor', 'vendor_invoice_number',
        'labor_cost', 'parts_cost', 'other_cost',
        'is_capital_improvement', 'parts_description',
        'description', 'issues_found', 'recommendations', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            status__in=['active', 'under_maintenance']
        )

        form.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
            is_active=True
        )

        form.fields['maintenance_schedule'].queryset = MaintenanceSchedule.objects.filter(
            company=self.request.current_company,
            is_active=True
        )

        form.fields['external_vendor'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both']
        )

        form.fields['scheduled_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'scheduled'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء الصيانة {self.object.maintenance_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:maintenance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة صيانة أصل'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('صيانة الأصول'), 'url': reverse('assets:maintenance_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class AssetMaintenanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل صيانة الأصل"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_detail.html'
    context_object_name = 'maintenance'
    permission_required = 'assets.view_assetmaintenance'

    def get_queryset(self):
        return AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).select_related(
            'asset', 'maintenance_type', 'maintenance_schedule',
            'performed_by', 'external_vendor', 'journal_entry'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'الصيانة {self.object.maintenance_number}',
            'can_edit': self.request.user.has_perm(
                'assets.change_assetmaintenance') and self.object.status != 'completed',
            'can_complete': self.request.user.has_perm(
                'assets.change_assetmaintenance') and self.object.status == 'in_progress',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('صيانة الأصول'), 'url': reverse('assets:maintenance_list')},
                {'title': self.object.maintenance_number, 'url': ''},
            ]
        })
        return context


class AssetMaintenanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل صيانة أصل"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.change_assetmaintenance'
    fields = [
        'asset', 'maintenance_type', 'maintenance_category',
        'maintenance_schedule', 'scheduled_date', 'start_date', 'completion_date',
        'status', 'performed_by', 'external_vendor', 'vendor_invoice_number',
        'labor_cost', 'parts_cost', 'other_cost',
        'is_capital_improvement', 'parts_description',
        'description', 'issues_found', 'recommendations', 'notes'
    ]

    def get_queryset(self):
        return AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).exclude(status='completed')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company
        )

        form.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
            is_active=True
        )

        form.fields['maintenance_schedule'].queryset = MaintenanceSchedule.objects.filter(
            company=self.request.current_company
        )

        form.fields['external_vendor'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both']
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث الصيانة {self.object.maintenance_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:maintenance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الصيانة {self.object.maintenance_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('صيانة الأصول'), 'url': reverse('assets:maintenance_list')},
                {'title': self.object.maintenance_number,
                 'url': reverse('assets:maintenance_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.change_assetmaintenance')
@require_http_methods(["POST"])
def complete_maintenance(request, pk):
    """إكمال صيانة أصل"""

    try:
        maintenance = get_object_or_404(
            AssetMaintenance,
            pk=pk,
            company=request.current_company
        )

        completion_date = date.today()

        # إكمال الصيانة
        maintenance.mark_as_completed(
            completion_date=completion_date,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'تم إكمال الصيانة {maintenance.maintenance_number} بنجاح'
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
            'message': f'خطأ في إكمال الصيانة: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_assetmaintenance')
@require_http_methods(["GET"])
def maintenance_datatable_ajax(request):
    """Ajax endpoint لجدول الصيانة"""

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
        queryset = AssetMaintenance.objects.filter(
            company=request.current_company
        ).select_related('asset', 'maintenance_type', 'journal_entry')

        if search_value:
            queryset = queryset.filter(
                Q(maintenance_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-scheduled_date', '-maintenance_number')

        total_records = AssetMaintenance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for maint in queryset:
            status_map = {
                'scheduled': '<span class="badge bg-info">مجدولة</span>',
                'in_progress': '<span class="badge bg-warning">جارية</span>',
                'completed': '<span class="badge bg-success">مكتملة</span>',
                'cancelled': '<span class="badge bg-danger">ملغاة</span>',
            }
            status_badge = status_map.get(maint.status, maint.status)

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:maintenance_detail', args=[maint.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if maint.status != 'completed':
                actions.append(f'''
                    <a href="{reverse('assets:maintenance_update', args=[maint.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions)

            data.append([
                maint.maintenance_number,
                maint.scheduled_date.strftime('%Y-%m-%d'),
                maint.asset.asset_number,
                maint.asset.name,
                maint.maintenance_type.name,
                f"{maint.total_cost:,.2f}",
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
@permission_required_with_message('assets.view_maintenanceschedule')
@require_http_methods(["GET"])
def schedule_datatable_ajax(request):
    """Ajax endpoint لجدول جدولة الصيانة"""

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
        queryset = MaintenanceSchedule.objects.filter(
            company=request.current_company
        ).select_related('asset', 'maintenance_type')

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

        for schedule in queryset:
            # حالة الجدولة
            if schedule.is_overdue():
                status = '<span class="badge bg-danger">متأخرة</span>'
            elif schedule.is_due_soon():
                status = '<span class="badge bg-warning">قريبة</span>'
            elif schedule.is_active:
                status = '<span class="badge bg-success">نشطة</span>'
            else:
                status = '<span class="badge bg-secondary">غير نشطة</span>'

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:schedule_detail', args=[schedule.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                schedule.schedule_number,
                schedule.asset.asset_number,
                schedule.maintenance_type.name,
                schedule.get_frequency_display(),
                schedule.next_maintenance_date.strftime('%Y-%m-%d'),
                status,
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
@permission_required_with_message('assets.view_maintenanceschedule')
@require_http_methods(["GET"])
def generate_schedule_dates(request):
    """توليد تواريخ الصيانة المستقبلية لجدولة معينة"""

    schedule_id = request.GET.get('schedule_id')
    months = int(request.GET.get('months', 12))

    if not schedule_id:
        return JsonResponse({'error': 'يجب تحديد الجدولة'}, status=400)

    try:
        schedule = get_object_or_404(
            MaintenanceSchedule,
            pk=schedule_id,
            company=request.current_company
        )

        dates = []
        current_date = schedule.next_maintenance_date

        for i in range(months):
            if not current_date:
                break

            dates.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'month': current_date.strftime('%B %Y'),
                'estimated_cost': float(schedule.estimated_cost)
            })

            # حساب التاريخ التالي
            next_date = schedule.calculate_next_maintenance_date()
            if not next_date:
                break

            current_date = next_date

        return JsonResponse({
            'success': True,
            'dates': dates,
            'schedule': {
                'schedule_number': schedule.schedule_number,
                'asset': schedule.asset.name,
                'maintenance_type': schedule.maintenance_type.name
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في توليد التواريخ: {str(e)}'
        }, status=500)
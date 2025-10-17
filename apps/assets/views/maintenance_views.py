# apps/assets/views/maintenance_views.py
"""
Views الصيانة
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView
from django.db.models import Q, Sum
from django.db import transaction as db_transaction
import datetime

from ..models import MaintenanceSchedule, AssetMaintenance, Asset, MaintenanceType
from ..forms import MaintenanceScheduleForm, AssetMaintenanceForm, MaintenanceFilterForm
from apps.core.mixins import CompanyMixin, AuditLogMixin


class MaintenanceScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة جدولة الصيانة"""

    template_name = 'assets/maintenance/schedule_list.html'
    permission_required = 'assets.view_maintenanceschedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'جدولة الصيانة الدورية',
            'can_add': self.request.user.has_perm('assets.add_maintenanceschedule'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'جدولة الصيانة', 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    CreateView):
    """إنشاء جدولة صيانة"""

    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.add_maintenanceschedule'
    success_url = reverse_lazy('assets:maintenance_schedule_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'تم إنشاء جدولة الصيانة {self.object.schedule_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'إضافة جدولة صيانة',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'جدولة الصيانة', 'url': reverse('assets:maintenance_schedule_list')},
                {'title': 'إضافة جديد', 'url': ''}
            ],
        })
        return context


class MaintenanceScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                    UpdateView):
    """تعديل جدولة صيانة"""

    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'assets/maintenance/schedule_form.html'
    permission_required = 'assets.change_maintenanceschedule'
    success_url = reverse_lazy('assets:maintenance_schedule_list')

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث جدولة الصيانة بنجاح')
        return response


class AssetMaintenanceListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة سجلات الصيانة"""

    template_name = 'assets/maintenance/maintenance_list.html'
    permission_required = 'assets.view_assetmaintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # نموذج الفلترة
        filter_form = MaintenanceFilterForm(
            self.request.GET,
            company=self.request.user.company
        )

        context.update({
            'title': 'سجل الصيانة',
            'filter_form': filter_form,
            'can_add': self.request.user.has_perm('assets.add_assetmaintenance'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الصيانة', 'url': ''}
            ],
        })

        return context


class AssetMaintenanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سجل صيانة"""

    model = AssetMaintenance
    form_class = AssetMaintenanceForm
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.add_assetmaintenance'
    success_url = reverse_lazy('assets:maintenance_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user

        response = super().form_valid(form)

        # تحديث حالة الأصل إذا كانت الصيانة جارية
        if form.instance.status == 'in_progress':
            asset = form.instance.asset
            asset.status = 'under_maintenance'
            asset.save()

        messages.success(
            self.request,
            f'تم إنشاء سجل الصيانة {self.object.maintenance_number} بنجاح'
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'إضافة سجل صيانة',
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الصيانة', 'url': reverse('assets:maintenance_list')},
                {'title': 'إضافة جديد', 'url': ''}
            ],
        })
        return context


class AssetMaintenanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سجل صيانة"""

    model = AssetMaintenance
    form_class = AssetMaintenanceForm
    template_name = 'assets/maintenance/maintenance_form.html'
    permission_required = 'assets.change_assetmaintenance'
    success_url = reverse_lazy('assets:maintenance_list')

    def get_queryset(self):
        return AssetMaintenance.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        # حفظ الحالة القديمة
        old_status = self.object.status

        response = super().form_valid(form)

        # تحديث حالة الأصل
        asset = form.instance.asset
        new_status = form.instance.status

        if old_status != new_status:
            if new_status == 'in_progress':
                asset.status = 'under_maintenance'
                asset.save()
            elif new_status == 'completed':
                # إعادة الأصل للحالة النشطة
                if asset.status == 'under_maintenance':
                    asset.status = 'active'
                    asset.save()

                # تحديث جدولة الصيانة
                form.instance.mark_as_completed()

        messages.success(self.request, 'تم تحديث سجل الصيانة بنجاح')
        return response


class AssetMaintenanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل سجل صيانة"""

    model = AssetMaintenance
    template_name = 'assets/maintenance/maintenance_detail.html'
    permission_required = 'assets.view_assetmaintenance'
    context_object_name = 'maintenance'

    def get_queryset(self):
        return AssetMaintenance.objects.filter(
            company=self.request.user.company
        ).select_related(
            'asset', 'maintenance_type', 'maintenance_schedule',
            'performed_by', 'external_vendor'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance = self.object

        context.update({
            'title': f'تفاصيل الصيانة: {maintenance.maintenance_number}',
            'can_edit': self.request.user.has_perm('assets.change_assetmaintenance'),
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'سجل الصيانة', 'url': reverse('assets:maintenance_list')},
                {'title': maintenance.maintenance_number, 'url': ''}
            ],
        })

        return context


@login_required
@permission_required('assets.view_assetmaintenance', raise_exception=True)
def maintenance_datatable_ajax(request):
    """Ajax endpoint لجدول الصيانة"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر
    asset_id = request.GET.get('asset', '')
    maintenance_type_id = request.GET.get('maintenance_type', '')
    status = request.GET.get('status', '')
    maintenance_category = request.GET.get('maintenance_category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    overdue_only = request.GET.get('overdue_only', '') == 'true'

    queryset = AssetMaintenance.objects.filter(
        company=request.user.company
    ).select_related('asset', 'maintenance_type', 'branch')

    # البحث
    if search_value:
        queryset = queryset.filter(
            Q(maintenance_number__icontains=search_value) |
            Q(asset__asset_number__icontains=search_value) |
            Q(asset__name__icontains=search_value)
        )

    # الفلاتر
    if asset_id:
        queryset = queryset.filter(asset_id=asset_id)

    if maintenance_type_id:
        queryset = queryset.filter(maintenance_type_id=maintenance_type_id)

    if status:
        queryset = queryset.filter(status=status)

    if maintenance_category:
        queryset = queryset.filter(maintenance_category=maintenance_category)

    if date_from:
        queryset = queryset.filter(scheduled_date__gte=date_from)

    if date_to:
        queryset = queryset.filter(scheduled_date__lte=date_to)

    if overdue_only:
        today = datetime.date.today()
        queryset = queryset.filter(
            status='scheduled',
            scheduled_date__lt=today
        )

    total_records = AssetMaintenance.objects.filter(company=request.user.company).count()
    filtered_records = queryset.count()

    queryset = queryset.order_by('-scheduled_date')[start:start + length]

    data = []
    for maintenance in queryset:
        # الحالة مع لون
        status_colors = {
            'scheduled': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'danger'
        }
        status_badge = f'<span class="badge bg-{status_colors.get(maintenance.status, "secondary")}">{maintenance.get_status_display()}</span>'

        # التصنيف
        category_colors = {
            'preventive': 'info',
            'corrective': 'warning',
            'emergency': 'danger',
            'improvement': 'success'
        }
        category_badge = f'<span class="badge bg-{category_colors.get(maintenance.maintenance_category, "secondary")}">{maintenance.get_maintenance_category_display()}</span>'

        # المتأخر
        is_overdue = maintenance.is_overdue()
        overdue_text = '<span class="badge bg-danger">متأخر</span>' if is_overdue else ''

        # الإجراءات
        actions = f'''
            <div class="btn-group btn-group-sm">
                <a href="{reverse("assets:maintenance_detail", args=[maintenance.pk])}" 
                   class="btn btn-info" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
        '''

        if request.user.has_perm('assets.change_assetmaintenance'):
            actions += f'''
                <a href="{reverse("assets:maintenance_update", args=[maintenance.pk])}" 
                   class="btn btn-primary" title="تعديل">
                    <i class="fas fa-edit"></i>
                </a>
            '''

        actions += '</div>'

        data.append([
            maintenance.maintenance_number,
            f'{maintenance.scheduled_date.strftime("%Y-%m-%d")} {overdue_text}',
            f'<strong>{maintenance.asset.asset_number}</strong><br><small>{maintenance.asset.name}</small>',
            maintenance.maintenance_type.name,
            category_badge,
            f'{maintenance.total_cost:,.3f}',
            status_badge,
            actions
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })
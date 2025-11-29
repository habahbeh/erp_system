# apps/hr/views/biometric_views.py
"""
واجهات إدارة أجهزة البصمة
Biometric Device Management Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator

from ..models import (
    BiometricDevice,
    BiometricLog,
    EmployeeBiometricMapping,
    BiometricSyncLog,
    Employee,
    Attendance
)
from ..forms.biometric_forms import (
    BiometricDeviceForm,
    EmployeeBiometricMappingForm,
    BiometricMappingBulkForm
)
from ..services.biometric_service import BiometricService


class BiometricDeviceListView(LoginRequiredMixin, ListView):
    """قائمة أجهزة البصمة"""
    model = BiometricDevice
    template_name = 'hr/biometric/device_list.html'
    context_object_name = 'devices'
    paginate_by = 20

    def get_queryset(self):
        queryset = BiometricDevice.objects.filter(
            company=self.request.current_company
        ).select_related('branch', 'created_by')

        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة حسب النوع
        device_type = self.request.GET.get('device_type')
        if device_type:
            queryset = queryset.filter(device_type=device_type)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(serial_number__icontains=search)
            )

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('أجهزة البصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة')}
        ]

        # إحصائيات
        devices = BiometricDevice.objects.filter(company=self.request.current_company)
        context['stats'] = {
            'total': devices.count(),
            'active': devices.filter(status='active').count(),
            'offline': devices.filter(status='offline').count(),
            'maintenance': devices.filter(status='maintenance').count(),
        }

        context['status_choices'] = BiometricDevice.STATUS_CHOICES
        context['device_types'] = BiometricDevice.DEVICE_TYPE_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('device_type', '')
        context['search_query'] = self.request.GET.get('search', '')

        return context


class BiometricDeviceCreateView(LoginRequiredMixin, CreateView):
    """إضافة جهاز بصمة جديد"""
    model = BiometricDevice
    form_class = BiometricDeviceForm
    template_name = 'hr/biometric/device_form.html'
    success_url = reverse_lazy('hr:biometric_device_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إضافة الجهاز بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة جهاز بصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('إضافة جهاز')}
        ]
        return context


class BiometricDeviceUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل جهاز بصمة"""
    model = BiometricDevice
    form_class = BiometricDeviceForm
    template_name = 'hr/biometric/device_form.html'
    success_url = reverse_lazy('hr:biometric_device_list')

    def get_queryset(self):
        return BiometricDevice.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الجهاز بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل جهاز بصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('تعديل جهاز')}
        ]
        return context


class BiometricDeviceDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل جهاز البصمة"""
    model = BiometricDevice
    template_name = 'hr/biometric/device_detail.html'
    context_object_name = 'device'

    def get_queryset(self):
        return BiometricDevice.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.object

        context['title'] = device.name
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': device.name}
        ]

        # آخر سجلات المزامنة
        context['sync_logs'] = BiometricSyncLog.objects.filter(
            device=device
        ).order_by('-created_at')[:10]

        # عدد الموظفين المرتبطين
        context['mapped_employees'] = EmployeeBiometricMapping.objects.filter(
            device=device, is_active=True
        ).count()

        # آخر سجلات البصمة
        context['recent_logs'] = BiometricLog.objects.filter(
            device=device
        ).select_related('employee').order_by('-punch_time')[:20]

        return context


class BiometricDeviceDeleteView(LoginRequiredMixin, DeleteView):
    """حذف جهاز بصمة"""
    model = BiometricDevice
    template_name = 'hr/biometric/device_confirm_delete.html'
    success_url = reverse_lazy('hr:biometric_device_list')

    def get_queryset(self):
        return BiometricDevice.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف الجهاز بنجاح'))
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف جهاز بصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('حذف جهاز')}
        ]
        return context


@login_required
def test_device_connection(request, pk):
    """اختبار الاتصال بالجهاز"""
    device = get_object_or_404(
        BiometricDevice,
        pk=pk,
        company=request.current_company
    )

    success, message = BiometricService.test_device_connection(device)

    # تحديث حالة الجهاز
    if success:
        device.status = 'active'
        device.last_connection = timezone.now()
    else:
        device.status = 'offline'
    device.save()

    return JsonResponse({
        'success': success,
        'message': message
    })


@login_required
def sync_device(request, pk):
    """مزامنة بيانات الجهاز"""
    device = get_object_or_404(
        BiometricDevice,
        pk=pk,
        company=request.current_company
    )

    if request.method == 'POST':
        result = BiometricService.sync_device_attendance(device, request.user)

        if result['success']:
            messages.success(
                request,
                _('تمت المزامنة بنجاح. السجلات المجلوبة: %(fetched)s، المعالجة: %(processed)s') % {
                    'fetched': result['records_fetched'],
                    'processed': result['records_processed']
                }
            )
        else:
            messages.error(request, _('فشلت المزامنة: %(error)s') % {'error': result['error']})

        return JsonResponse(result)

    return JsonResponse({'success': False, 'error': _('طريقة غير مدعومة')})


@login_required
def sync_all_devices(request):
    """مزامنة جميع الأجهزة"""
    if request.method == 'POST':
        result = BiometricService.sync_all_devices(request.current_company, request.user)

        messages.success(
            request,
            _('تمت المزامنة. الأجهزة: %(total)s، الناجحة: %(success)s، الفاشلة: %(failed)s') % {
                'total': result['total_devices'],
                'success': result['successful'],
                'failed': result['failed']
            }
        )

        return JsonResponse(result)

    return JsonResponse({'success': False, 'error': _('طريقة غير مدعومة')})


# ============== إدارة ربط الموظفين بأجهزة البصمة ==============

class EmployeeMappingListView(LoginRequiredMixin, ListView):
    """قائمة ربط الموظفين بأجهزة البصمة"""
    model = EmployeeBiometricMapping
    template_name = 'hr/biometric/mapping_list.html'
    context_object_name = 'mappings'
    paginate_by = 30

    def get_queryset(self):
        queryset = EmployeeBiometricMapping.objects.filter(
            company=self.request.current_company
        ).select_related('employee', 'device')

        # فلترة حسب الجهاز
        device_id = self.request.GET.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        # فلترة حسب الموظف
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employee_number__icontains=search) |
                Q(device_user_id__icontains=search)
            )

        return queryset.order_by('employee__first_name', 'employee__last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('ربط الموظفين بأجهزة البصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('ربط الموظفين')}
        ]

        context['devices'] = BiometricDevice.objects.filter(
            company=self.request.current_company, is_active=True
        )
        context['employees'] = Employee.objects.filter(
            company=self.request.current_company, is_active=True
        )

        # إحصائيات
        context['stats'] = {
            'total_mappings': EmployeeBiometricMapping.objects.filter(
                company=self.request.current_company
            ).count(),
            'enrolled': EmployeeBiometricMapping.objects.filter(
                company=self.request.current_company, is_enrolled=True
            ).count(),
            'not_enrolled': EmployeeBiometricMapping.objects.filter(
                company=self.request.current_company, is_enrolled=False
            ).count(),
        }

        return context


class EmployeeMappingCreateView(LoginRequiredMixin, CreateView):
    """إضافة ربط موظف بجهاز"""
    model = EmployeeBiometricMapping
    form_class = EmployeeBiometricMappingForm
    template_name = 'hr/biometric/mapping_form.html'
    success_url = reverse_lazy('hr:biometric_mapping_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.current_company
        messages.success(self.request, _('تم ربط الموظف بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('ربط موظف بجهاز')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('ربط الموظفين'), 'url': reverse_lazy('hr:biometric_mapping_list')},
            {'title': _('إضافة ربط')}
        ]
        return context


class EmployeeMappingUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل ربط موظف"""
    model = EmployeeBiometricMapping
    form_class = EmployeeBiometricMappingForm
    template_name = 'hr/biometric/mapping_form.html'
    success_url = reverse_lazy('hr:biometric_mapping_list')

    def get_queryset(self):
        return EmployeeBiometricMapping.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الربط بنجاح'))
        return super().form_valid(form)


class EmployeeMappingDeleteView(LoginRequiredMixin, DeleteView):
    """حذف ربط موظف"""
    model = EmployeeBiometricMapping
    template_name = 'hr/biometric/mapping_confirm_delete.html'
    success_url = reverse_lazy('hr:biometric_mapping_list')

    def get_queryset(self):
        return EmployeeBiometricMapping.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف الربط بنجاح'))
        return super().delete(request, *args, **kwargs)


@login_required
def bulk_mapping_view(request):
    """ربط مجموعة موظفين"""
    if request.method == 'POST':
        form = BiometricMappingBulkForm(request.POST, company=request.current_company)
        if form.is_valid():
            device = form.cleaned_data['device']
            employees = form.cleaned_data['employees']
            start_id = form.cleaned_data['start_id']

            created = 0
            for i, employee in enumerate(employees):
                device_user_id = str(start_id + i)
                mapping, is_new = EmployeeBiometricMapping.objects.get_or_create(
                    company=request.current_company,
                    employee=employee,
                    device=device,
                    defaults={'device_user_id': device_user_id}
                )
                if is_new:
                    created += 1

            messages.success(request, _('تم ربط %(count)s موظفين') % {'count': created})
            return redirect('hr:biometric_mapping_list')
    else:
        form = BiometricMappingBulkForm(company=request.current_company)

    return render(request, 'hr/biometric/bulk_mapping_form.html', {
        'form': form,
        'title': _('ربط مجموعة موظفين'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('ربط الموظفين'), 'url': reverse_lazy('hr:biometric_mapping_list')},
            {'title': _('ربط مجموعة')}
        ]
    })


# ============== سجلات البصمة ==============

class BiometricLogListView(LoginRequiredMixin, ListView):
    """سجلات البصمة"""
    model = BiometricLog
    template_name = 'hr/biometric/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = BiometricLog.objects.filter(
            company=self.request.current_company
        ).select_related('device', 'employee', 'attendance')

        # فلترة حسب الجهاز
        device_id = self.request.GET.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        # فلترة حسب الموظف
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # فلترة حسب التاريخ
        from_date = self.request.GET.get('from_date')
        if from_date:
            queryset = queryset.filter(punch_time__date__gte=from_date)

        to_date = self.request.GET.get('to_date')
        if to_date:
            queryset = queryset.filter(punch_time__date__lte=to_date)

        # فلترة حسب نوع البصمة
        punch_type = self.request.GET.get('punch_type')
        if punch_type:
            queryset = queryset.filter(punch_type=punch_type)

        # فلترة حسب المعالجة
        is_processed = self.request.GET.get('is_processed')
        if is_processed == 'yes':
            queryset = queryset.filter(is_processed=True)
        elif is_processed == 'no':
            queryset = queryset.filter(is_processed=False)

        return queryset.order_by('-punch_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('سجلات البصمة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('سجلات البصمة')}
        ]

        context['devices'] = BiometricDevice.objects.filter(
            company=self.request.current_company
        )
        context['employees'] = Employee.objects.filter(
            company=self.request.current_company, is_active=True
        )
        context['punch_types'] = BiometricLog.PUNCH_TYPE_CHOICES

        # إحصائيات اليوم
        today = timezone.now().date()
        today_logs = BiometricLog.objects.filter(
            company=self.request.current_company,
            punch_time__date=today
        )
        context['stats'] = {
            'today_total': today_logs.count(),
            'today_in': today_logs.filter(punch_type='in').count(),
            'today_out': today_logs.filter(punch_type='out').count(),
            'unprocessed': BiometricLog.objects.filter(
                company=self.request.current_company,
                is_processed=False
            ).count(),
        }

        return context


@login_required
def process_unprocessed_logs(request):
    """معالجة السجلات غير المعالجة"""
    if request.method == 'POST':
        result = BiometricService.process_unprocessed_logs(request.current_company)

        messages.success(
            request,
            _('تمت المعالجة. السجلات المعالجة: %(processed)s، الفاشلة: %(failed)s') % {
                'processed': result.get('processed', 0),
                'failed': result.get('failed', 0)
            }
        )

        return JsonResponse(result)

    return JsonResponse({'success': False, 'error': _('طريقة غير مدعومة')})


# ============== سجلات المزامنة ==============

class SyncLogListView(LoginRequiredMixin, ListView):
    """سجلات المزامنة"""
    model = BiometricSyncLog
    template_name = 'hr/biometric/sync_log_list.html'
    context_object_name = 'logs'
    paginate_by = 30

    def get_queryset(self):
        queryset = BiometricSyncLog.objects.filter(
            company=self.request.current_company
        ).select_related('device', 'created_by')

        # فلترة حسب الجهاز
        device_id = self.request.GET.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('سجلات المزامنة')
        context['breadcrumbs'] = [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أجهزة البصمة'), 'url': reverse_lazy('hr:biometric_device_list')},
            {'title': _('سجلات المزامنة')}
        ]

        context['devices'] = BiometricDevice.objects.filter(
            company=self.request.current_company
        )
        context['status_choices'] = BiometricSyncLog.STATUS_CHOICES

        return context

# apps/assets/views/workflow_views.py
"""
Views سير العمل والموافقات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.forms import inlineformset_factory
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
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest, ApprovalHistory
)


# ==================== Approval Workflows ====================

class ApprovalWorkflowListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سير العمل"""

    model = ApprovalWorkflow
    template_name = 'assets/workflow/workflow_list.html'
    context_object_name = 'workflows'
    permission_required = 'assets.view_approvalworkflow'
    paginate_by = 50

    def get_queryset(self):
        queryset = ApprovalWorkflow.objects.filter(
            company=self.request.current_company
        ).prefetch_related('levels')

        # الفلترة
        document_type = self.request.GET.get('document_type')
        is_active = self.request.GET.get('is_active')

        if document_type:
            queryset = queryset.filter(document_type=document_type)

        if is_active:
            queryset = queryset.filter(is_active=(is_active == '1'))

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate statistics
        workflows = ApprovalWorkflow.objects.filter(company=self.request.current_company)
        stats = {
            'total': workflows.count(),
            'active': workflows.filter(is_active=True).count(),
            'inactive': workflows.filter(is_active=False).count(),
            'total_levels': ApprovalLevel.objects.filter(
                workflow__company=self.request.current_company
            ).count()
        }

        context.update({
            'title': _('سير العمل'),
            'can_add': self.request.user.has_perm('assets.add_approvalworkflow'),
            'can_edit': self.request.user.has_perm('assets.change_approvalworkflow'),
            'can_delete': self.request.user.has_perm('assets.delete_approvalworkflow'),
            'document_types': ApprovalWorkflow.DOCUMENT_TYPES,
            'stats': stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': ''},
            ]
        })
        return context


class ApprovalWorkflowCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء سير عمل"""

    model = ApprovalWorkflow
    template_name = 'assets/workflow/workflow_form.html'
    permission_required = 'assets.add_approvalworkflow'
    fields = ['code', 'name', 'document_type', 'is_sequential', 'description', 'is_active']
    success_url = reverse_lazy('assets:workflow_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all groups for the dropdown
        from django.contrib.auth.models import Group
        groups = Group.objects.all().order_by('name')

        if self.request.POST:
            context['formset'] = inlineformset_factory(
                ApprovalWorkflow,
                ApprovalLevel,
                fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
                extra=1,
                can_delete=True
            )(self.request.POST, instance=self.object)
        else:
            context['formset'] = inlineformset_factory(
                ApprovalWorkflow,
                ApprovalLevel,
                fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
                extra=1,
                can_delete=True
            )(instance=self.object)

        context.update({
            'title': _('إضافة سير عمل'),
            'groups': groups,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': reverse('assets:workflow_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        self.object = form.save()

        # Save formset
        formset = inlineformset_factory(
            ApprovalWorkflow,
            ApprovalLevel,
            fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
            extra=1,
            can_delete=True
        )(self.request.POST, instance=self.object)

        if formset.is_valid():
            formset.save()
            messages.success(self.request, f'تم إنشاء سير العمل {self.object.name} بنجاح')
            return redirect('assets:workflow_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)


class ApprovalWorkflowDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل سير العمل"""

    model = ApprovalWorkflow
    template_name = 'assets/workflow/workflow_detail.html'
    context_object_name = 'workflow'
    permission_required = 'assets.view_approvalworkflow'

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(
            company=self.request.current_company
        ).prefetch_related('levels', 'levels__approver_role')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المستويات
        levels = self.object.levels.order_by('level_order')

        context.update({
            'title': f'سير العمل {self.object.name}',
            'can_edit': self.request.user.has_perm('assets.change_approvalworkflow'),
            'can_delete': self.request.user.has_perm('assets.delete_approvalworkflow'),
            'levels': levels,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': reverse('assets:workflow_list')},
                {'title': self.object.name, 'url': ''},
            ]
        })
        return context


class ApprovalWorkflowUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سير عمل"""

    model = ApprovalWorkflow
    template_name = 'assets/workflow/workflow_form.html'
    permission_required = 'assets.change_approvalworkflow'
    fields = ['code', 'name', 'document_type', 'is_sequential', 'description', 'is_active']

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all groups for the dropdown
        from django.contrib.auth.models import Group
        groups = Group.objects.all().order_by('name')

        if self.request.POST:
            context['formset'] = inlineformset_factory(
                ApprovalWorkflow,
                ApprovalLevel,
                fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
                extra=0,
                can_delete=True
            )(self.request.POST, instance=self.object)
        else:
            context['formset'] = inlineformset_factory(
                ApprovalWorkflow,
                ApprovalLevel,
                fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
                extra=0,
                can_delete=True
            )(instance=self.object)

        context.update({
            'title': f'تعديل سير العمل {self.object.name}',
            'groups': groups,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': reverse('assets:workflow_list')},
                {'title': self.object.name, 'url': reverse('assets:workflow_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        # Save formset
        formset = inlineformset_factory(
            ApprovalWorkflow,
            ApprovalLevel,
            fields=['level_order', 'name', 'approver_role', 'amount_from', 'amount_to', 'is_required'],
            extra=0,
            can_delete=True
        )(self.request.POST, instance=self.object)

        if formset.is_valid():
            formset.save()
            messages.success(self.request, f'تم تحديث سير العمل {self.object.name} بنجاح')
            return redirect('assets:workflow_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)


class ApprovalWorkflowDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف سير عمل"""

    model = ApprovalWorkflow
    template_name = 'assets/workflow/workflow_confirm_delete.html'
    permission_required = 'assets.delete_approvalworkflow'
    success_url = reverse_lazy('assets:workflow_list')

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.approval_requests.exists():
            messages.error(request, _('لا يمكن حذف سير عمل له طلبات موافقة'))
            return redirect('assets:workflow_list')

        messages.success(request, f'تم حذف سير العمل {self.object.name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Approval Requests ====================

class ApprovalRequestListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة طلبات الموافقة"""

    model = ApprovalRequest
    template_name = 'assets/workflow/request_list.html'
    context_object_name = 'requests'
    permission_required = 'assets.view_approvalrequest'
    paginate_by = 25

    def get_queryset(self):
        queryset = ApprovalRequest.objects.filter(
            company=self.request.current_company
        ).select_related('workflow', 'requested_by', 'current_level', 'current_level__approver_role')

        # الفلترة
        status = self.request.GET.get('status')
        workflow = self.request.GET.get('workflow')
        my_requests = self.request.GET.get('my_requests')
        pending_my_approval = self.request.GET.get('pending_my_approval')

        if status:
            queryset = queryset.filter(status=status)

        if workflow:
            queryset = queryset.filter(workflow_id=workflow)

        if my_requests == '1':
            queryset = queryset.filter(requested_by=self.request.user)

        if pending_my_approval == '1':
            # Filter by current level's approver role
            queryset = queryset.filter(
                status='pending',
                current_level__approver_role__user=self.request.user
            )

        return queryset.order_by('-requested_date', '-request_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # العدادات
        pending_my_approval = ApprovalRequest.objects.filter(
            company=self.request.current_company,
            status='pending',
            current_level__approver_role__user=self.request.user
        ).count()

        # قائمة سير العمل
        workflows = ApprovalWorkflow.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context.update({
            'title': _('طلبات الموافقة'),
            'status_choices': ApprovalRequest.STATUS_CHOICES,
            'pending_my_approval': pending_my_approval,
            'workflows': workflows,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('طلبات الموافقة'), 'url': ''},
            ]
        })
        return context


class ApprovalRequestDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل طلب الموافقة"""

    model = ApprovalRequest
    template_name = 'assets/workflow/request_detail.html'
    context_object_name = 'request'
    permission_required = 'assets.view_approvalrequest'

    def get_queryset(self):
        return ApprovalRequest.objects.filter(
            company=self.request.current_company
        ).select_related('workflow', 'requested_by', 'current_level', 'current_level__approver_role')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # سجل الموافقات
        history = self.object.history.select_related('approver', 'level').order_by('action_date')

        # هل يمكن للمستخدم الموافقة
        can_approve = (
                self.object.status == 'pending' and
                self.object.current_level and
                self.request.user.groups.filter(id=self.object.current_level.approver_role_id).exists()
        )

        context.update({
            'title': f'طلب الموافقة {self.object.request_number}',
            'can_approve': can_approve,
            'history': history,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('طلبات الموافقة'), 'url': reverse('assets:request_list')},
                {'title': self.object.request_number, 'url': ''},
            ]
        })
        return context


# ==================== Approval Levels ====================

class ApprovalLevelCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء مستوى موافقة"""

    model = ApprovalLevel
    template_name = 'assets/workflow/level_form.html'
    permission_required = 'assets.change_approvalworkflow'
    fields = [
        'workflow', 'level_order', 'level_name',
        'approver_role', 'specific_approver',
        'min_amount', 'max_amount',
        'required_approval_count', 'is_final_level'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['workflow'].queryset = ApprovalWorkflow.objects.filter(
            company=self.request.current_company
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'تم إضافة المستوى {self.object.level_name} بنجاح')
        return redirect('assets:workflow_detail', pk=self.object.workflow.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        workflow_id = self.request.GET.get('workflow_id')
        workflow = None

        if workflow_id:
            workflow = get_object_or_404(
                ApprovalWorkflow,
                pk=workflow_id,
                company=self.request.current_company
            )

        context.update({
            'title': _('إضافة مستوى موافقة'),
            'workflow': workflow,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': reverse('assets:workflow_list')},
                {'title': _('إضافة مستوى'), 'url': ''},
            ]
        })
        return context


class ApprovalLevelUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل مستوى موافقة"""

    model = ApprovalLevel
    template_name = 'assets/workflow/level_form.html'
    permission_required = 'assets.change_approvalworkflow'
    fields = [
        'level_order', 'level_name',
        'approver_role', 'specific_approver',
        'min_amount', 'max_amount',
        'required_approval_count', 'is_final_level'
    ]

    def get_queryset(self):
        return ApprovalLevel.objects.filter(
            workflow__company=self.request.current_company
        )

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'تم تحديث المستوى {self.object.level_name} بنجاح')
        return redirect('assets:workflow_detail', pk=self.object.workflow.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل المستوى {self.object.level_name}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('سير العمل'), 'url': reverse('assets:workflow_list')},
                {'title': self.object.workflow.name,
                 'url': reverse('assets:workflow_detail', args=[self.object.workflow.pk])},
                {'title': _('تعديل مستوى'), 'url': ''},
            ]
        })
        return context


class ApprovalLevelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف مستوى موافقة"""

    model = ApprovalLevel
    template_name = 'assets/workflow/level_confirm_delete.html'
    permission_required = 'assets.delete_approvalworkflow'

    def get_queryset(self):
        return ApprovalLevel.objects.filter(
            workflow__company=self.request.current_company
        )

    def get_success_url(self):
        return reverse('assets:workflow_detail', kwargs={'pk': self.object.workflow.pk})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'تم حذف المستوى {self.object.level_name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.change_approvalrequest')
@require_http_methods(["POST"])
def approve_request(request, pk):
    """الموافقة على طلب"""

    try:
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            company=request.current_company,
            status='pending',
            current_approver=request.user
        )

        comments = request.POST.get('comments', '')

        # الموافقة
        approval_request.approve(
            approver=request.user,
            comments=comments
        )

        return JsonResponse({
            'success': True,
            'message': f'تم الموافقة على الطلب {approval_request.request_number} بنجاح'
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
            'message': f'خطأ في الموافقة: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.change_approvalrequest')
@require_http_methods(["POST"])
def reject_request(request, pk):
    """رفض طلب"""

    try:
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            company=request.current_company,
            status='pending',
            current_approver=request.user
        )

        comments = request.POST.get('comments', '')

        if not comments:
            return JsonResponse({
                'success': False,
                'message': 'يجب إدخال سبب الرفض'
            }, status=400)

        # الرفض
        approval_request.reject(
            approver=request.user,
            comments=comments
        )

        return JsonResponse({
            'success': True,
            'message': f'تم رفض الطلب {approval_request.request_number}'
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
            'message': f'خطأ في الرفض: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_approvalrequest')
@require_http_methods(["GET"])
def request_datatable_ajax(request):
    """Ajax endpoint لجدول طلبات الموافقة"""

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

    # الفلاتر الجديدة
    status = request.GET.get('status', '')
    workflow = request.GET.get('workflow', '')
    quick_filter = request.GET.get('quick_filter', '')
    search_filter = request.GET.get('search_filter', '').strip()

    try:
        queryset = ApprovalRequest.objects.filter(
            company=request.current_company
        ).select_related('workflow', 'requested_by', 'current_level', 'current_level__approver_role')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if workflow:
            queryset = queryset.filter(workflow_id=workflow)

        if quick_filter == 'my_requests':
            queryset = queryset.filter(requested_by=request.user)
        elif quick_filter == 'pending_my_approval':
            queryset = queryset.filter(
                status='pending',
                current_level__approver_role__user=request.user
            )

        # البحث
        search_text = search_filter or search_value
        if search_text:
            queryset = queryset.filter(
                Q(request_number__icontains=search_text) |
                Q(document_number__icontains=search_text) |
                Q(requested_by__first_name__icontains=search_text) |
                Q(requested_by__last_name__icontains=search_text)
            )

        queryset = queryset.order_by('-requested_date', '-request_number')

        total_records = ApprovalRequest.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for req in queryset:
            status_map = {
                'pending': '<span class="badge bg-warning">معلق</span>',
                'approved': '<span class="badge bg-success">موافق عليه</span>',
                'rejected': '<span class="badge bg-danger">مرفوض</span>',
                'cancelled': '<span class="badge bg-secondary">ملغي</span>',
            }
            status_badge = status_map.get(req.status, req.status)

            # المعتمد الحالي (من المستوى الحالي)
            current_approver = req.current_level.approver_role.name if req.current_level else '-'

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:request_detail', args=[req.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            # زر الموافقة
            if req.status == 'pending' and req.current_level and request.user.groups.filter(id=req.current_level.approver_role_id).exists():
                actions.append(f'''
                    <button type="button" class="btn btn-outline-success btn-sm" 
                            onclick="approveRequest({req.pk})" title="موافقة" data-bs-toggle="tooltip">
                        <i class="fas fa-check"></i>
                    </button>
                ''')
                actions.append(f'''
                    <button type="button" class="btn btn-outline-danger btn-sm" 
                            onclick="rejectRequest({req.pk})" title="رفض" data-bs-toggle="tooltip">
                        <i class="fas fa-times"></i>
                    </button>
                ''')

            actions_html = ' '.join(actions)

            data.append([
                req.request_number,
                req.requested_date.strftime('%Y-%m-%d'),
                req.workflow.name,
                req.document_number or '-',
                req.requested_by.get_full_name(),
                current_approver,
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
@permission_required_with_message('assets.view_approvalrequest')
@require_http_methods(["GET"])
def approval_stats_ajax(request):
    """إحصائيات طلبات الموافقة"""

    try:
        requests = ApprovalRequest.objects.filter(
            company=request.current_company
        )

        stats = {
            'total': requests.count(),
            'pending': requests.filter(status='pending').count(),
            'approved': requests.filter(status='approved').count(),
            'rejected': requests.filter(status='rejected').count(),
            'cancelled': requests.filter(status='cancelled').count(),
        }

        return JsonResponse({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في تحميل الإحصائيات: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_approvalrequest')
@require_http_methods(["GET"])
def request_export(request):
    """تصدير طلبات الموافقة إلى Excel"""

    try:
        import pandas as pd
        from datetime import datetime

        # تطبيق نفس الفلاتر المستخدمة في العرض
        queryset = ApprovalRequest.objects.filter(
            company=request.current_company
        ).select_related('workflow', 'requested_by', 'current_level', 'current_level__approver_role')

        status = request.GET.get('status', '')
        workflow = request.GET.get('workflow', '')
        quick_filter = request.GET.get('quick_filter', '')

        if status:
            queryset = queryset.filter(status=status)
        if workflow:
            queryset = queryset.filter(workflow_id=workflow)
        if quick_filter == 'my_requests':
            queryset = queryset.filter(requested_by=request.user)
        elif quick_filter == 'pending_my_approval':
            queryset = queryset.filter(
                status='pending',
                current_level__approver_role__user=request.user
            )

        # تحضير البيانات
        data = []
        for req in queryset.order_by('-requested_date'):
            data.append({
                'رقم الطلب': req.request_number,
                'تاريخ الطلب': req.requested_date.strftime('%Y-%m-%d'),
                'نوع سير العمل': req.workflow.name,
                'رقم المستند': req.document_number or '-',
                'مقدم الطلب': req.requested_by.get_full_name(),
                'المعتمد الحالي': req.current_level.approver_role.name if req.current_level else '-',
                'الحالة': req.get_status_display(),
                'القيمة': float(req.amount) if req.amount else 0,
                'المستوى الحالي': req.current_level or '-',
            })

        # إنشاء ملف Excel
        df = pd.DataFrame(data)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="approval_requests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='طلبات الموافقة')

            # تنسيق الأعمدة
            worksheet = writer.sheets['طلبات الموافقة']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'خطأ في تصدير البيانات: {str(e)}')
        return redirect('assets:request_list')


@login_required
@permission_required_with_message('assets.view_approvalrequest')
@require_http_methods(["GET"])
def my_pending_approvals_ajax(request):
    """طلبات الموافقة المعلقة للمستخدم الحالي"""

    try:
        requests = ApprovalRequest.objects.filter(
            company=request.current_company,
            status='pending',
            current_level__approver_role__user=request.user
        ).select_related('workflow', 'requested_by', 'current_level').order_by('requested_date')[:10]

        results = []
        for req in requests:
            results.append({
                'id': req.pk,
                'request_number': req.request_number,
                'request_date': req.requested_date.strftime('%Y-%m-%d'),
                'workflow': req.workflow.name,
                'document_number': req.document_number or '',
                'requested_by': req.requested_by.get_full_name(),
                'amount': float(req.amount) if req.amount else 0,
                'url': reverse('assets:request_detail', args=[req.pk])
            })

        return JsonResponse({
            'success': True,
            'requests': results
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        }, status=500)
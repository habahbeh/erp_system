# apps/assets/views/lease_views.py
"""
Views إدارة عقود الإيجار
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
from dateutil.relativedelta import relativedelta

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import AssetLease, LeasePayment, Asset
from apps.core.models import BusinessPartner


# ==================== Asset Leases ====================

class AssetLeaseListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة عقود الإيجار"""

    model = AssetLease
    template_name = 'assets/lease/lease_list.html'
    context_object_name = 'leases'
    permission_required = 'assets.view_assetlease'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetLease.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'lessor')

        # الفلترة
        status = self.request.GET.get('status')
        lease_type = self.request.GET.get('lease_type')
        asset = self.request.GET.get('asset')
        lessor = self.request.GET.get('lessor')

        if status:
            queryset = queryset.filter(status=status)

        if lease_type:
            queryset = queryset.filter(lease_type=lease_type)

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if lessor:
            queryset = queryset.filter(lessor_id=lessor)

        return queryset.order_by('-start_date', '-lease_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الموردين/المؤجرين
        lessors = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both']
        )

        context.update({
            'title': _('عقود الإيجار'),
            'can_add': self.request.user.has_perm('assets.add_assetlease'),
            'can_edit': self.request.user.has_perm('assets.change_assetlease'),
            'status_choices': AssetLease.STATUS_CHOICES,
            'lease_types': AssetLease.LEASE_TYPES,
            'lessors': lessors,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عقود الإيجار'), 'url': ''},
            ]
        })
        return context


class AssetLeaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء عقد إيجار"""

    model = AssetLease
    template_name = 'assets/lease/lease_form.html'
    permission_required = 'assets.add_assetlease'
    fields = [
        'asset', 'lease_type', 'lessor',
        'start_date', 'end_date',
        'monthly_payment', 'security_deposit',
        'interest_rate', 'residual_value', 'purchase_option_price',
        'status', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            is_leased=True
        )

        form.fields['lessor'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both']
        )

        form.fields['start_date'].initial = date.today()
        form.fields['end_date'].initial = date.today() + relativedelta(years=1)

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user

        self.object = form.save()

        # إنشاء دفعات الإيجار
        self.create_lease_payments()

        messages.success(
            self.request,
            f'تم إنشاء عقد الإيجار {self.object.lease_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def create_lease_payments(self):
        """إنشاء دفعات الإيجار المستقبلية"""

        current_date = self.object.start_date
        payment_number = 1

        # حساب الفائدة للإيجار التمويلي
        if self.object.lease_type == 'finance' and self.object.interest_rate:
            remaining_principal = self.object.total_payments
            monthly_rate = self.object.interest_rate / 100 / 12

        while current_date <= self.object.end_date:
            # حساب الأصل والفائدة للإيجار التمويلي
            if self.object.lease_type == 'finance' and self.object.interest_rate:
                interest_amount = remaining_principal * monthly_rate
                principal_amount = self.object.monthly_payment - interest_amount
                remaining_principal -= principal_amount
            else:
                interest_amount = Decimal('0')
                principal_amount = Decimal('0')

            LeasePayment.objects.create(
                lease=self.object,
                payment_number=payment_number,
                payment_date=current_date,
                amount=self.object.monthly_payment,
                principal_amount=principal_amount,
                interest_amount=interest_amount
            )

            payment_number += 1

            # الانتقال للشهر التالي
            if self.object.payment_frequency == 'monthly':
                current_date += relativedelta(months=1)
            elif self.object.payment_frequency == 'quarterly':
                current_date += relativedelta(months=3)
            elif self.object.payment_frequency == 'semi_annual':
                current_date += relativedelta(months=6)
            elif self.object.payment_frequency == 'annual':
                current_date += relativedelta(years=1)

    def get_success_url(self):
        return reverse('assets:lease_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة عقد إيجار'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عقود الإيجار'), 'url': reverse('assets:lease_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class AssetLeaseDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل عقد الإيجار"""

    model = AssetLease
    template_name = 'assets/lease/lease_detail.html'
    context_object_name = 'lease'
    permission_required = 'assets.view_assetlease'

    def get_queryset(self):
        return AssetLease.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'lessor', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الدفعات
        payments = self.object.payments.order_by('payment_number')

        # الدفعات المدفوعة
        paid_payments = payments.filter(is_paid=True)

        # الدفعات المستحقة
        upcoming_payments = payments.filter(
            is_paid=False,
            payment_date__gte=date.today()
        ).order_by('payment_date')[:5]

        context.update({
            'title': f'عقد الإيجار {self.object.lease_number}',
            'can_edit': self.request.user.has_perm('assets.change_assetlease') and self.object.status == 'draft',
            'can_pay': self.request.user.has_perm('assets.change_assetlease'),
            'payments': payments[:12],  # أول 12 دفعة
            'paid_count': paid_payments.count(),
            'upcoming_payments': upcoming_payments,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عقود الإيجار'), 'url': reverse('assets:lease_list')},
                {'title': self.object.lease_number, 'url': ''},
            ]
        })
        return context


class AssetLeaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل عقد إيجار"""

    model = AssetLease
    template_name = 'assets/lease/lease_form.html'
    permission_required = 'assets.change_assetlease'
    fields = [
        'asset', 'lease_type', 'lessor',
        'start_date', 'end_date',
        'monthly_payment', 'security_deposit',
        'interest_rate', 'residual_value', 'purchase_option_price',
        'status', 'notes'
    ]

    def get_queryset(self):
        return AssetLease.objects.filter(
            company=self.request.current_company
        ).exclude(status='completed')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company
        )

        form.fields['lessor'].queryset = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both']
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث عقد الإيجار {self.object.lease_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:lease_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل عقد الإيجار {self.object.lease_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('عقود الإيجار'), 'url': reverse('assets:lease_list')},
                {'title': self.object.lease_number, 'url': reverse('assets:lease_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Lease Payments ====================

class LeasePaymentListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة دفعات الإيجار"""

    model = LeasePayment
    template_name = 'assets/lease/payment_list.html'
    context_object_name = 'payments'
    permission_required = 'assets.view_assetlease'
    paginate_by = 25

    def get_queryset(self):
        queryset = LeasePayment.objects.filter(
            lease__company=self.request.current_company
        ).select_related('lease', 'lease__asset', 'journal_entry')

        # الفلترة
        is_paid = self.request.GET.get('is_paid')
        lease = self.request.GET.get('lease')
        overdue = self.request.GET.get('overdue')

        if is_paid:
            queryset = queryset.filter(is_paid=(is_paid == '1'))

        if lease:
            queryset = queryset.filter(lease_id=lease)

        if overdue == '1':
            queryset = queryset.filter(
                is_paid=False,
                payment_date__lt=date.today()
            )

        return queryset.order_by('payment_date', 'lease', 'payment_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # العقود النشطة
        active_leases = AssetLease.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        # الدفعات المتأخرة
        overdue_count = LeasePayment.objects.filter(
            lease__company=self.request.current_company,
            is_paid=False,
            payment_date__lt=date.today()
        ).count()

        context.update({
            'title': _('دفعات الإيجار'),
            'can_pay': self.request.user.has_perm('assets.change_assetlease'),
            'active_leases': active_leases,
            'overdue_count': overdue_count,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دفعات الإيجار'), 'url': ''},
            ]
        })
        return context


class LeasePaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إضافة دفعة إيجار يدوياً"""

    model = LeasePayment
    template_name = 'assets/lease/payment_form.html'
    permission_required = 'assets.change_assetlease'
    fields = [
        'lease', 'payment_number', 'payment_date',
        'amount', 'principal_amount', 'interest_amount',
        'notes'
    ]
    success_url = reverse_lazy('assets:payment_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['lease'].queryset = AssetLease.objects.filter(
            company=self.request.current_company,
            status='active'
        )

        form.fields['payment_date'].initial = date.today()

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة دفعة إيجار'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('دفعات الإيجار'), 'url': reverse('assets:payment_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.change_assetlease')
@require_http_methods(["POST"])
def process_lease_payment(request, pk):
    """معالجة دفعة إيجار"""

    try:
        payment = get_object_or_404(
            LeasePayment,
            pk=pk,
            lease__company=request.current_company,
            is_paid=False
        )

        # معالجة الدفع
        payment.process_payment(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم معالجة دفعة الإيجار رقم {payment.payment_number} بنجاح'
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
            'message': f'خطأ في معالجة الدفع: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_assetlease')
@require_http_methods(["GET"])
def lease_datatable_ajax(request):
    """Ajax endpoint لجدول عقود الإيجار"""

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
        queryset = AssetLease.objects.filter(
            company=request.current_company
        ).select_related('asset', 'lessor')

        if search_value:
            queryset = queryset.filter(
                Q(lease_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-start_date', '-lease_number')

        total_records = AssetLease.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for lease in queryset:
            status_map = {
                'draft': '<span class="badge bg-secondary">مسودة</span>',
                'active': '<span class="badge bg-success">نشط</span>',
                'completed': '<span class="badge bg-info">مكتمل</span>',
                'terminated': '<span class="badge bg-warning">منهي</span>',
                'cancelled': '<span class="badge bg-danger">ملغي</span>',
            }
            status_badge = status_map.get(lease.status, lease.status)

            # الأشهر المتبقية
            remaining_months = lease.get_remaining_months()

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:lease_detail', args=[lease.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                lease.lease_number,
                lease.asset.asset_number,
                lease.get_lease_type_display(),
                lease.lessor.name,
                f"{lease.monthly_payment:,.2f}",
                f"{remaining_months} شهر",
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
@permission_required_with_message('assets.view_assetlease')
@require_http_methods(["GET"])
def payment_datatable_ajax(request):
    """Ajax endpoint لجدول دفعات الإيجار"""

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
        queryset = LeasePayment.objects.filter(
            lease__company=request.current_company
        ).select_related('lease__asset', 'journal_entry')

        if search_value:
            queryset = queryset.filter(
                Q(lease__lease_number__icontains=search_value) |
                Q(lease__asset__asset_number__icontains=search_value)
            )

        queryset = queryset.order_by('payment_date', 'lease', 'payment_number')

        total_records = LeasePayment.objects.filter(lease__company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_pay = request.user.has_perm('assets.change_assetlease')

        for payment in queryset:
            # الحالة
            if payment.is_paid:
                status_badge = '<span class="badge bg-success">مدفوع</span>'
            elif payment.payment_date < date.today():
                status_badge = '<span class="badge bg-danger">متأخر</span>'
            else:
                status_badge = '<span class="badge bg-warning">مستحق</span>'

            actions = []

            if not payment.is_paid and can_pay:
                actions.append(f'''
                    <button type="button" class="btn btn-outline-success btn-sm" 
                            onclick="processPayment({payment.pk})" title="دفع" data-bs-toggle="tooltip">
                        <i class="fas fa-dollar-sign"></i>
                    </button>
                ''')

            if payment.journal_entry:
                actions.append(f'''
                    <a href="{reverse('accounting:journal_entry_detail', args=[payment.journal_entry.pk])}" 
                       class="btn btn-outline-info btn-sm" title="القيد" data-bs-toggle="tooltip">
                        <i class="fas fa-file-invoice"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                payment.lease.lease_number,
                f"قسط {payment.payment_number}",
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.lease.asset.asset_number,
                f"{payment.amount:,.2f}",
                f"{payment.paid_date.strftime('%Y-%m-%d')}" if payment.paid_date else '-',
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
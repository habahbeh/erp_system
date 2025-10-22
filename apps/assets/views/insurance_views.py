# apps/assets/views/insurance_views.py
"""
Views إدارة التأمين على الأصول
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
from ..models import InsuranceCompany, AssetInsurance, InsuranceClaim, Asset


# ==================== Insurance Companies ====================

class InsuranceCompanyListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة شركات التأمين"""

    model = InsuranceCompany
    template_name = 'assets/insurance/company_list.html'
    context_object_name = 'companies'
    permission_required = 'assets.view_insurancecompany'
    paginate_by = 50

    def get_queryset(self):
        queryset = InsuranceCompany.objects.filter(
            company=self.request.current_company
        )

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search)
            )

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('شركات التأمين'),
            'can_add': self.request.user.has_perm('assets.add_insurancecompany'),
            'can_edit': self.request.user.has_perm('assets.change_insurancecompany'),
            'can_delete': self.request.user.has_perm('assets.delete_insurancecompany'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('شركات التأمين'), 'url': ''},
            ]
        })
        return context


class InsuranceCompanyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء شركة تأمين"""

    model = InsuranceCompany
    template_name = 'assets/insurance/company_form.html'
    permission_required = 'assets.add_insurancecompany'
    fields = [
        'code', 'name', 'name_en', 'contact_person',
        'phone', 'mobile', 'email', 'fax',
        'address', 'city', 'country',
        'website', 'license_number', 'notes'
    ]
    success_url = reverse_lazy('assets:insurance_company_list')

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        self.object = form.save()

        messages.success(self.request, f'تم إنشاء شركة التأمين {self.object.name} بنجاح')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة شركة تأمين'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('شركات التأمين'), 'url': reverse('assets:insurance_company_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class InsuranceCompanyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل شركة تأمين"""

    model = InsuranceCompany
    template_name = 'assets/insurance/company_form.html'
    permission_required = 'assets.change_insurancecompany'
    fields = [
        'code', 'name', 'name_en', 'contact_person',
        'phone', 'mobile', 'email', 'fax',
        'address', 'city', 'country',
        'website', 'license_number', 'notes'
    ]
    success_url = reverse_lazy('assets:insurance_company_list')

    def get_queryset(self):
        return InsuranceCompany.objects.filter(company=self.request.current_company)

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'تم تحديث شركة التأمين {self.object.name} بنجاح')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل شركة التأمين {self.object.name}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('شركات التأمين'), 'url': reverse('assets:insurance_company_list')},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class InsuranceCompanyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف شركة تأمين"""

    model = InsuranceCompany
    template_name = 'assets/insurance/company_confirm_delete.html'
    permission_required = 'assets.delete_insurancecompany'
    success_url = reverse_lazy('assets:insurance_company_list')

    def get_queryset(self):
        return InsuranceCompany.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.insurance_policies.exists():
            messages.error(request, _('لا يمكن حذف شركة تأمين لديها بوليصات'))
            return redirect('assets:insurance_company_list')

        messages.success(request, f'تم حذف شركة التأمين {self.object.name} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Asset Insurance ====================

class AssetInsuranceListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة بوليصات التأمين"""

    model = AssetInsurance
    template_name = 'assets/insurance/insurance_list.html'
    context_object_name = 'insurances'
    permission_required = 'assets.view_assetinsurance'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetInsurance.objects.filter(
            company=self.request.current_company
        ).select_related('insurance_company', 'asset')

        # الفلترة
        status = self.request.GET.get('status')
        insurance_company = self.request.GET.get('insurance_company')
        asset = self.request.GET.get('asset')
        expiring_soon = self.request.GET.get('expiring_soon')

        if status:
            queryset = queryset.filter(status=status)

        if insurance_company:
            queryset = queryset.filter(insurance_company_id=insurance_company)

        if asset:
            queryset = queryset.filter(asset_id=asset)

        if expiring_soon == '1':
            expiry_date = date.today() + timedelta(days=30)
            queryset = queryset.filter(
                status='active',
                end_date__lte=expiry_date
            )

        return queryset.order_by('-start_date', '-policy_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # شركات التأمين
        insurance_companies = InsuranceCompany.objects.filter(
            company=self.request.current_company
        )

        # البوليصات المنتهية قريباً
        expiring_count = AssetInsurance.objects.filter(
            company=self.request.current_company,
            status='active',
            end_date__lte=date.today() + timedelta(days=30)
        ).count()

        context.update({
            'title': _('بوليصات التأمين'),
            'can_add': self.request.user.has_perm('assets.add_assetinsurance'),
            'can_edit': self.request.user.has_perm('assets.change_assetinsurance'),
            'status_choices': AssetInsurance.STATUS_CHOICES,
            'insurance_companies': insurance_companies,
            'expiring_count': expiring_count,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('بوليصات التأمين'), 'url': ''},
            ]
        })
        return context


class AssetInsuranceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء بوليصة تأمين"""

    model = AssetInsurance
    template_name = 'assets/insurance/insurance_form.html'
    permission_required = 'assets.add_assetinsurance'
    fields = [
        'insurance_company', 'asset', 'coverage_type', 'coverage_description',
        'coverage_amount', 'premium_amount', 'deductible_amount',
        'payment_frequency', 'next_payment_date',
        'start_date', 'end_date', 'renewal_date',
        'status', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['insurance_company'].queryset = InsuranceCompany.objects.filter(
            company=self.request.current_company
        )

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company,
            status='active'
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
            f'تم إنشاء البوليصة {self.object.policy_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:insurance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة بوليصة تأمين'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('بوليصات التأمين'), 'url': reverse('assets:insurance_list')},
                {'title': _('إضافة'), 'url': ''},
            ]
        })
        return context


class AssetInsuranceDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل بوليصة التأمين"""

    model = AssetInsurance
    template_name = 'assets/insurance/insurance_detail.html'
    context_object_name = 'insurance'
    permission_required = 'assets.view_assetinsurance'

    def get_queryset(self):
        return AssetInsurance.objects.filter(
            company=self.request.current_company
        ).select_related('insurance_company', 'asset', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المطالبات
        claims = self.object.claims.order_by('-filed_date')

        context.update({
            'title': f'البوليصة {self.object.policy_number}',
            'can_edit': self.request.user.has_perm('assets.change_assetinsurance'),
            'can_add_claim': self.request.user.has_perm('assets.add_insuranceclaim'),
            'claims': claims,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('بوليصات التأمين'), 'url': reverse('assets:insurance_list')},
                {'title': self.object.policy_number, 'url': ''},
            ]
        })
        return context


class AssetInsuranceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل بوليصة تأمين"""

    model = AssetInsurance
    template_name = 'assets/insurance/insurance_form.html'
    permission_required = 'assets.change_assetinsurance'
    fields = [
        'insurance_company', 'asset', 'coverage_type', 'coverage_description',
        'coverage_amount', 'premium_amount', 'deductible_amount',
        'payment_frequency', 'next_payment_date',
        'start_date', 'end_date', 'renewal_date',
        'status', 'notes'
    ]

    def get_queryset(self):
        return AssetInsurance.objects.filter(company=self.request.current_company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['insurance_company'].queryset = InsuranceCompany.objects.filter(
            company=self.request.current_company
        )

        form.fields['asset'].queryset = Asset.objects.filter(
            company=self.request.current_company
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث البوليصة {self.object.policy_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:insurance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل البوليصة {self.object.policy_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('بوليصات التأمين'), 'url': reverse('assets:insurance_list')},
                {'title': self.object.policy_number, 'url': reverse('assets:insurance_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Insurance Claims ====================

class InsuranceClaimListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة مطالبات التأمين"""

    model = InsuranceClaim
    template_name = 'assets/insurance/claim_list.html'
    context_object_name = 'claims'
    permission_required = 'assets.view_insuranceclaim'
    paginate_by = 25

    def get_queryset(self):
        queryset = InsuranceClaim.objects.filter(
            company=self.request.current_company
        ).select_related('insurance', 'insurance__asset', 'filed_by', 'reviewed_by')

        # الفلترة
        status = self.request.GET.get('status')
        claim_type = self.request.GET.get('claim_type')
        insurance = self.request.GET.get('insurance')

        if status:
            queryset = queryset.filter(status=status)

        if claim_type:
            queryset = queryset.filter(claim_type=claim_type)

        if insurance:
            queryset = queryset.filter(insurance_id=insurance)

        return queryset.order_by('-filed_date', '-claim_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title': _('مطالبات التأمين'),
            'can_add': self.request.user.has_perm('assets.add_insuranceclaim'),
            'can_edit': self.request.user.has_perm('assets.change_insuranceclaim'),
            'status_choices': InsuranceClaim.STATUS_CHOICES,
            'claim_types': InsuranceClaim.CLAIM_TYPES,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('مطالبات التأمين'), 'url': ''},
            ]
        })
        return context


class InsuranceClaimCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء مطالبة تأمين"""

    model = InsuranceClaim
    template_name = 'assets/insurance/claim_form.html'
    permission_required = 'assets.add_insuranceclaim'
    fields = [
        'insurance', 'claim_type', 'incident_date', 'incident_time',
        'incident_location', 'incident_description',
        'estimated_damage', 'claim_amount',
        'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['insurance'].queryset = AssetInsurance.objects.filter(
            company=self.request.current_company,
            status='active'
        ).select_related('asset', 'insurance_company')

        form.fields['incident_date'].initial = date.today()

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.filed_by = self.request.user
        form.instance.status = 'filed'

        self.object = form.save()

        messages.success(
            self.request,
            f'تم تقديم المطالبة {self.object.claim_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:claim_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تقديم مطالبة تأمين'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('مطالبات التأمين'), 'url': reverse('assets:claim_list')},
                {'title': _('تقديم مطالبة'), 'url': ''},
            ]
        })
        return context


class InsuranceClaimDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل مطالبة التأمين"""

    model = InsuranceClaim
    template_name = 'assets/insurance/claim_detail.html'
    context_object_name = 'claim'
    permission_required = 'assets.view_insuranceclaim'

    def get_queryset(self):
        return InsuranceClaim.objects.filter(
            company=self.request.current_company
        ).select_related(
            'insurance', 'insurance__asset', 'insurance__insurance_company',
            'filed_by', 'reviewed_by', 'journal_entry'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'المطالبة {self.object.claim_number}',
            'can_edit': self.request.user.has_perm('assets.change_insuranceclaim') and self.object.status in ['filed',
                                                                                                              'under_review'],
            'can_approve': self.request.user.has_perm('assets.change_insuranceclaim') and self.object.status in [
                'filed', 'under_review'],
            'can_pay': self.request.user.has_perm('assets.change_insuranceclaim') and self.object.status == 'approved',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('مطالبات التأمين'), 'url': reverse('assets:claim_list')},
                {'title': self.object.claim_number, 'url': ''},
            ]
        })
        return context


class InsuranceClaimUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل مطالبة تأمين"""

    model = InsuranceClaim
    template_name = 'assets/insurance/claim_form.html'
    permission_required = 'assets.change_insuranceclaim'
    fields = [
        'insurance', 'claim_type', 'incident_date', 'incident_time',
        'incident_location', 'incident_description',
        'estimated_damage', 'claim_amount', 'approved_amount',
        'deductible_applied', 'status', 'rejection_reason', 'notes'
    ]

    def get_queryset(self):
        return InsuranceClaim.objects.filter(
            company=self.request.current_company
        ).exclude(status__in=['paid', 'cancelled'])

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['insurance'].queryset = AssetInsurance.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'insurance_company')

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث المطالبة {self.object.claim_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:claim_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل المطالبة {self.object.claim_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('مطالبات التأمين'), 'url': reverse('assets:claim_list')},
                {'title': self.object.claim_number, 'url': reverse('assets:claim_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.change_insuranceclaim')
@require_http_methods(["POST"])
def approve_insurance_claim(request, pk):
    """اعتماد مطالبة تأمين"""

    try:
        claim = get_object_or_404(
            InsuranceClaim,
            pk=pk,
            company=request.current_company
        )

        approved_amount = Decimal(request.POST.get('approved_amount', 0))

        if not approved_amount:
            return JsonResponse({
                'success': False,
                'message': 'يجب تحديد المبلغ المعتمد'
            }, status=400)

        # اعتماد المطالبة
        claim.approve(
            approved_amount=approved_amount,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'تم اعتماد المطالبة {claim.claim_number} بمبلغ {approved_amount:,.2f}'
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
            'message': f'خطأ في اعتماد المطالبة: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.change_insuranceclaim')
@require_http_methods(["POST"])
def process_claim_payment(request, pk):
    """معالجة دفع مطالبة تأمين"""

    try:
        claim = get_object_or_404(
            InsuranceClaim,
            pk=pk,
            company=request.current_company,
            status='approved'
        )

        # معالجة الدفع
        claim.process_payment(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم معالجة دفع المطالبة {claim.claim_number} بنجاح'
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
@permission_required_with_message('assets.view_assetinsurance')
@require_http_methods(["GET"])
def insurance_datatable_ajax(request):
    """Ajax endpoint لجدول بوليصات التأمين"""

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
        queryset = AssetInsurance.objects.filter(
            company=request.current_company
        ).select_related('insurance_company', 'asset')

        if search_value:
            queryset = queryset.filter(
                Q(policy_number__icontains=search_value) |
                Q(asset__asset_number__icontains=search_value) |
                Q(asset__name__icontains=search_value)
            )

        queryset = queryset.order_by('-start_date', '-policy_number')

        total_records = AssetInsurance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for insurance in queryset:
            status_map = {
                'draft': '<span class="badge bg-secondary">مسودة</span>',
                'active': '<span class="badge bg-success">نشط</span>',
                'expired': '<span class="badge bg-danger">منتهي</span>',
                'cancelled': '<span class="badge bg-dark">ملغي</span>',
            }
            status_badge = status_map.get(insurance.status, insurance.status)

            # التحقق من قرب الانتهاء
            if insurance.is_expiring_soon():
                status_badge += ' <span class="badge bg-warning">قريب الانتهاء</span>'

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:insurance_detail', args=[insurance.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                insurance.policy_number,
                insurance.asset.asset_number,
                insurance.insurance_company.name,
                insurance.get_coverage_type_display(),
                f"{insurance.coverage_amount:,.2f}",
                insurance.end_date.strftime('%Y-%m-%d'),
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
@permission_required_with_message('assets.view_insuranceclaim')
@require_http_methods(["GET"])
def claim_datatable_ajax(request):
    """Ajax endpoint لجدول مطالبات التأمين"""

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
        queryset = InsuranceClaim.objects.filter(
            company=request.current_company
        ).select_related('insurance__asset')

        if search_value:
            queryset = queryset.filter(
                Q(claim_number__icontains=search_value) |
                Q(insurance__asset__asset_number__icontains=search_value)
            )

        queryset = queryset.order_by('-filed_date', '-claim_number')

        total_records = InsuranceClaim.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []

        for claim in queryset:
            status_map = {
                'filed': '<span class="badge bg-info">مقدم</span>',
                'under_review': '<span class="badge bg-warning">قيد المراجعة</span>',
                'approved': '<span class="badge bg-primary">معتمد</span>',
                'rejected': '<span class="badge bg-danger">مرفوض</span>',
                'paid': '<span class="badge bg-success">مدفوع</span>',
                'cancelled': '<span class="badge bg-dark">ملغي</span>',
            }
            status_badge = status_map.get(claim.status, claim.status)

            actions = []
            actions.append(f'''
                <a href="{reverse('assets:claim_detail', args=[claim.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            actions_html = ' '.join(actions)

            data.append([
                claim.claim_number,
                claim.filed_date.strftime('%Y-%m-%d'),
                claim.get_claim_type_display(),
                claim.insurance.asset.asset_number,
                f"{claim.claim_amount:,.2f}",
                f"{claim.approved_amount:,.2f}" if claim.approved_amount else '-',
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
@permission_required_with_message('assets.view_assetinsurance')
@require_http_methods(["GET"])
def insurance_expiring_ajax(request):
    """البوليصات المنتهية قريباً"""

    days = int(request.GET.get('days', 30))

    try:
        expiry_date = date.today() + timedelta(days=days)

        insurances = AssetInsurance.objects.filter(
            company=request.current_company,
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=date.today()
        ).select_related('asset', 'insurance_company').order_by('end_date')

        results = []
        for insurance in insurances:
            remaining_days = (insurance.end_date - date.today()).days
            results.append({
                'policy_number': insurance.policy_number,
                'asset': insurance.asset.name,
                'insurance_company': insurance.insurance_company.name,
                'end_date': insurance.end_date.strftime('%Y-%m-%d'),
                'remaining_days': remaining_days,
                'coverage_amount': float(insurance.coverage_amount)
            })

        return JsonResponse({
            'success': True,
            'insurances': results
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في تحميل البيانات: {str(e)}'
        }, status=500)
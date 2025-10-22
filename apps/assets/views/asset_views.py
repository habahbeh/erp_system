# apps/assets/views/asset_views.py
"""
Views الأصول الثابتة - محسنة لسهولة الاستخدام
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Sum, Count, F, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from django.core.exceptions import ValidationError
import json
from datetime import date, timedelta
from decimal import Decimal

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, DepreciationMethod, AssetCondition,
    AssetAttachment, AssetValuation
)
from apps.accounting.models import Account, CostCenter


class AssetListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة الأصول الثابتة"""

    model = Asset
    template_name = 'assets/asset/asset_list.html'
    context_object_name = 'assets'
    permission_required = 'assets.view_asset'
    paginate_by = 25

    def get_queryset(self):
        queryset = Asset.objects.filter(
            company=self.request.current_company
        ).select_related(
            'category', 'condition', 'depreciation_method',
            'cost_center', 'responsible_employee', 'supplier'
        )

        # الفلترة
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        branch = self.request.GET.get('branch')
        cost_center = self.request.GET.get('cost_center')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)

        if category:
            queryset = queryset.filter(category_id=category)

        if branch:
            queryset = queryset.filter(branch_id=branch)

        if cost_center:
            queryset = queryset.filter(cost_center_id=cost_center)

        if search:
            queryset = queryset.filter(
                Q(asset_number__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(barcode__icontains=search)
            )

        return queryset.order_by('-purchase_date', '-asset_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الفئات للفلترة
        categories = AssetCategory.objects.filter(
            company=self.request.current_company
        ).order_by('code')

        context.update({
            'title': _('الأصول الثابتة'),
            'can_add': self.request.user.has_perm('assets.add_asset'),
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'status_choices': Asset.STATUS_CHOICES,
            'categories': categories,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': ''},
            ]
        })
        return context


class AssetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء أصل جديد"""

    model = Asset
    template_name = 'assets/asset/asset_form.html'
    permission_required = 'assets.add_asset'
    fields = [
        'name', 'name_en', 'category', 'condition', 'status',
        'purchase_date', 'purchase_invoice_number', 'supplier',
        'currency', 'original_cost', 'salvage_value',
        'depreciation_method', 'useful_life_months', 'depreciation_start_date',
        'cost_center', 'responsible_employee', 'physical_location',
        'serial_number', 'model', 'manufacturer',
        'warranty_start_date', 'warranty_end_date', 'warranty_provider',
        'barcode', 'description', 'notes'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تخصيص الحقول
        form.fields['category'].queryset = AssetCategory.objects.filter(
            company=self.request.current_company
        )
        form.fields['depreciation_method'].queryset = DepreciationMethod.objects.filter(
            is_active=True
        )
        form.fields['condition'].queryset = AssetCondition.objects.filter(
            is_active=True
        )

        if 'cost_center' in form.fields:
            form.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

        # القيم الافتراضية
        form.fields['purchase_date'].initial = date.today()
        form.fields['depreciation_start_date'].initial = date.today()
        form.fields['status'].initial = 'active'

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user

        # إذا لم تحدد العملة، استخدم عملة الشركة
        if not form.instance.currency:
            form.instance.currency = self.request.current_company.base_currency

        self.object = form.save()

        messages.success(
            self.request,
            f'تم إنشاء الأصل {self.object.asset_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة أصل جديد'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': _('إضافة أصل'), 'url': ''},
            ]
        })
        return context


class AssetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل أصل"""

    model = Asset
    template_name = 'assets/asset/asset_form.html'
    permission_required = 'assets.change_asset'
    fields = [
        'name', 'name_en', 'category', 'condition', 'status',
        'purchase_date', 'purchase_invoice_number', 'supplier',
        'currency', 'original_cost', 'salvage_value',
        'depreciation_method', 'useful_life_months', 'depreciation_start_date',
        'cost_center', 'responsible_employee', 'physical_location',
        'serial_number', 'model', 'manufacturer',
        'warranty_start_date', 'warranty_end_date', 'warranty_provider',
        'barcode', 'description', 'notes'
    ]

    def get_queryset(self):
        return Asset.objects.filter(company=self.request.current_company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تخصيص الحقول
        form.fields['category'].queryset = AssetCategory.objects.filter(
            company=self.request.current_company
        )
        form.fields['depreciation_method'].queryset = DepreciationMethod.objects.filter(
            is_active=True
        )
        form.fields['condition'].queryset = AssetCondition.objects.filter(
            is_active=True
        )

        if 'cost_center' in form.fields:
            form.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        messages.success(
            self.request,
            f'تم تحديث الأصل {self.object.asset_number} بنجاح'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الأصل {self.object.asset_number}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': self.object.asset_number, 'url': reverse('assets:asset_detail', args=[self.object.pk])},
                {'title': _('تعديل'), 'url': ''},
            ]
        })
        return context


class AssetDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل الأصل"""

    model = Asset
    template_name = 'assets/asset/asset_detail.html'
    context_object_name = 'asset'
    permission_required = 'assets.view_asset'

    def get_queryset(self):
        return Asset.objects.filter(
            company=self.request.current_company
        ).select_related(
            'category', 'condition', 'depreciation_method',
            'cost_center', 'responsible_employee', 'supplier',
            'created_by'
        ).prefetch_related(
            'attachments', 'valuations', 'depreciation_records',
            'maintenances', 'transactions'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # سجل الإهلاك
        depreciation_records = self.object.depreciation_records.order_by('-depreciation_date')[:10]

        # الصيانات
        maintenances = self.object.maintenances.order_by('-scheduled_date')[:5]

        # المرفقات
        attachments = self.object.attachments.order_by('-uploaded_at')

        # المعاملات
        transactions = self.object.transactions.order_by('-transaction_date')[:5]

        context.update({
            'title': f'الأصل {self.object.asset_number}',
            'can_edit': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.delete_asset'),
            'can_calculate_depreciation': self.request.user.has_perm('assets.can_calculate_depreciation'),
            'can_sell': self.request.user.has_perm('assets.can_sell_asset'),
            'can_dispose': self.request.user.has_perm('assets.can_dispose_asset'),
            'depreciation_records': depreciation_records,
            'maintenances': maintenances,
            'attachments': attachments,
            'transactions': transactions,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': self.object.asset_number, 'url': ''},
            ]
        })
        return context


class AssetDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف أصل"""

    model = Asset
    template_name = 'assets/asset/asset_confirm_delete.html'
    permission_required = 'assets.delete_asset'
    success_url = reverse_lazy('assets:asset_list')

    def get_queryset(self):
        return Asset.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.status in ['sold', 'disposed']:
            messages.error(request, _('لا يمكن حذف أصل مباع أو مستبعد'))
            return redirect('assets:asset_detail', pk=self.object.pk)

        if self.object.depreciation_records.exists():
            messages.error(request, _('لا يمكن حذف أصل له سجلات إهلاك'))
            return redirect('assets:asset_detail', pk=self.object.pk)

        messages.success(request, f'تم حذف الأصل {self.object.asset_number} بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Asset Categories ====================

class AssetCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة فئات الأصول"""

    model = AssetCategory
    template_name = 'assets/category/category_list.html'
    context_object_name = 'categories'
    permission_required = 'assets.view_assetcategory'
    paginate_by = 50

    def get_queryset(self):
        return AssetCategory.objects.filter(
            company=self.request.current_company
        ).select_related('parent', 'default_depreciation_method').order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('فئات الأصول'),
            'can_add': self.request.user.has_perm('assets.add_assetcategory'),
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': ''},
            ]
        })
        return context


class AssetCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء فئة أصول جديدة"""

    model = AssetCategory
    template_name = 'assets/category/category_form.html'
    permission_required = 'assets.add_assetcategory'
    fields = [
        'code', 'name', 'name_en', 'parent',
        'asset_account', 'accumulated_depreciation_account',
        'depreciation_expense_account', 'loss_on_disposal_account',
        'gain_on_sale_account', 'maintenance_expense_account',
        'default_depreciation_method', 'default_useful_life_months',
        'default_salvage_value_rate', 'default_physical_count_frequency',
        'description'
    ]
    success_url = reverse_lazy('assets:category_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تخصيص الحقول
        form.fields['parent'].queryset = AssetCategory.objects.filter(
            company=self.request.current_company
        )

        form.fields['asset_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['accumulated_depreciation_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['depreciation_expense_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['loss_on_disposal_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['gain_on_sale_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['maintenance_expense_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )

        form.fields['default_depreciation_method'].queryset = DepreciationMethod.objects.filter(
            is_active=True
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user
        self.object = form.save()

        messages.success(self.request, f'تم إنشاء الفئة {self.object.code} بنجاح')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة فئة أصول'),
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': _('إضافة فئة'), 'url': ''},
            ]
        })
        return context


class AssetCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل فئة أصول"""

    model = AssetCategory
    template_name = 'assets/category/category_form.html'
    permission_required = 'assets.change_assetcategory'
    fields = [
        'code', 'name', 'name_en', 'parent',
        'asset_account', 'accumulated_depreciation_account',
        'depreciation_expense_account', 'loss_on_disposal_account',
        'gain_on_sale_account', 'maintenance_expense_account',
        'default_depreciation_method', 'default_useful_life_months',
        'default_salvage_value_rate', 'default_physical_count_frequency',
        'description'
    ]
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.current_company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # تخصيص الحقول - نفس الـ CreateView
        form.fields['parent'].queryset = AssetCategory.objects.filter(
            company=self.request.current_company
        ).exclude(pk=self.object.pk)  # منع اختيار نفسه كأب

        form.fields['asset_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['accumulated_depreciation_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['depreciation_expense_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['loss_on_disposal_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['gain_on_sale_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )
        form.fields['maintenance_expense_account'].queryset = Account.objects.filter(
            company=self.request.current_company,
            accept_entries=True
        )

        form.fields['default_depreciation_method'].queryset = DepreciationMethod.objects.filter(
            is_active=True
        )

        return form

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'تم تحديث الفئة {self.object.code} بنجاح')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'تعديل الفئة {self.object.code}',
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': self.object.code, 'url': ''},
            ]
        })
        return context


class AssetCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف فئة أصول"""

    model = AssetCategory
    template_name = 'assets/category/category_confirm_delete.html'
    permission_required = 'assets.delete_assetcategory'
    success_url = reverse_lazy('assets:category_list')

    def get_queryset(self):
        return AssetCategory.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.assets.exists():
            messages.error(request, _('لا يمكن حذف فئة لديها أصول'))
            return redirect('assets:category_list')

        if self.object.children.exists():
            messages.error(request, _('لا يمكن حذف فئة لديها فئات فرعية'))
            return redirect('assets:category_list')

        messages.success(request, f'تم حذف الفئة {self.object.code} بنجاح')
        return super().delete(request, *args, **kwargs)


class AssetCategoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل فئة الأصول"""

    model = AssetCategory
    template_name = 'assets/category/category_detail.html'
    context_object_name = 'category'
    permission_required = 'assets.view_assetcategory'

    def get_queryset(self):
        return AssetCategory.objects.filter(
            company=self.request.current_company
        ).select_related(
            'parent', 'default_depreciation_method',
            'asset_account', 'accumulated_depreciation_account'
        ).prefetch_related('assets', 'children')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الفئة
        assets_stats = self.object.assets.filter(status='active').aggregate(
            total_count=Count('id'),
            total_original_cost=Coalesce(Sum('original_cost'), Decimal('0')),
            total_accumulated_depreciation=Coalesce(Sum('accumulated_depreciation'), Decimal('0')),
            total_book_value=Coalesce(Sum('book_value'), Decimal('0'))
        )

        context.update({
            'title': f'الفئة {self.object.code}',
            'can_edit': self.request.user.has_perm('assets.change_assetcategory'),
            'can_delete': self.request.user.has_perm('assets.delete_assetcategory'),
            'assets_stats': assets_stats,
            'breadcrumbs': [
                {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
                {'title': _('فئات الأصول'), 'url': reverse('assets:category_list')},
                {'title': self.object.code, 'url': ''},
            ]
        })
        return context


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_datatable_ajax(request):
    """Ajax endpoint لجدول الأصول"""

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

    # الفلاتر المخصصة
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')

    try:
        # البحث والفلترة
        queryset = Asset.objects.filter(
            company=request.current_company
        ).select_related('category', 'condition', 'cost_center')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if category:
            queryset = queryset.filter(category_id=category)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(asset_number__icontains=search_value) |
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(serial_number__icontains=search_value) |
                Q(barcode__icontains=search_value)
            )

        # الترتيب
        queryset = queryset.order_by('-purchase_date', '-asset_number')

        # العد الإجمالي
        total_records = Asset.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('assets.change_asset')
        can_delete = request.user.has_perm('assets.delete_asset')

        for asset in queryset:
            # حالة الأصل
            status_map = {
                'active': '<span class="badge bg-success">نشط</span>',
                'inactive': '<span class="badge bg-secondary">غير نشط</span>',
                'under_maintenance': '<span class="badge bg-warning">تحت الصيانة</span>',
                'disposed': '<span class="badge bg-danger">مستبعد</span>',
                'sold': '<span class="badge bg-info">مباع</span>',
                'lost': '<span class="badge bg-dark">مفقود</span>',
                'damaged': '<span class="badge bg-danger">تالف</span>',
            }
            status_badge = status_map.get(asset.status, asset.status)

            # أزرار الإجراءات
            actions = []

            # رابط العرض
            actions.append(f'''
                <a href="{reverse('assets:asset_detail', args=[asset.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            # رابط التعديل
            if can_edit and asset.status not in ['sold', 'disposed']:
                actions.append(f'''
                    <a href="{reverse('assets:asset_update', args=[asset.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            # رابط الحذف
            if can_delete and asset.status not in ['sold', 'disposed']:
                actions.append(f'''
                    <button type="button" class="btn btn-outline-danger btn-sm" 
                            onclick="deleteAsset({asset.pk})" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </button>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                asset.asset_number,
                f"{asset.name}",
                f"{asset.category.code} - {asset.category.name}",
                asset.purchase_date.strftime('%Y-%m-%d'),
                f"{asset.book_value:,.2f}",
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
@permission_required_with_message('assets.view_asset')
def asset_autocomplete(request):
    """
    Autocomplete للأصول
    """
    term = request.GET.get('term', '').strip()

    if len(term) < 2:
        return JsonResponse([], safe=False)

    # فلترة إضافية
    only_active = request.GET.get('only_active', '1') == '1'

    assets = Asset.objects.filter(
        company=request.current_company,
    ).filter(
        Q(asset_number__icontains=term) |
        Q(name__icontains=term) |
        Q(name_en__icontains=term) |
        Q(barcode__icontains=term)
    )

    # فلترة الأصول النشطة
    if only_active:
        assets = assets.filter(status='active')

    assets = assets.select_related('category')[:20]

    results = []
    for asset in assets:
        results.append({
            'id': asset.id,
            'text': f"{asset.asset_number} - {asset.name}",
            'asset_number': asset.asset_number,
            'name': asset.name,
            'name_en': asset.name_en or '',
            'category': asset.category.name,
            'book_value': float(asset.book_value),
            'status': asset.status,
        })

    return JsonResponse(results, safe=False)


@login_required
@permission_required_with_message('assets.view_assetcategory')
@require_http_methods(["GET"])
def asset_category_datatable_ajax(request):
    """Ajax endpoint لجدول فئات الأصول"""

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
        queryset = AssetCategory.objects.filter(
            company=request.current_company
        ).select_related('parent')

        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value)
            )

        queryset = queryset.order_by('code')

        total_records = AssetCategory.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('assets.change_assetcategory')
        can_delete = request.user.has_perm('assets.delete_assetcategory')

        for category in queryset:
            # عدد الأصول
            asset_count = category.assets.filter(status='active').count()

            # أزرار الإجراءات
            actions = []

            actions.append(f'''
                <a href="{reverse('assets:category_detail', args=[category.pk])}" 
                   class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('assets:category_update', args=[category.pk])}" 
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and asset_count == 0:
                actions.append(f'''
                    <button type="button" class="btn btn-outline-danger btn-sm" 
                            onclick="deleteCategory({category.pk})" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </button>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                category.code,
                category.name,
                category.parent.name if category.parent else '-',
                asset_count,
                f"المستوى {category.level}",
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
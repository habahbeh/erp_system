# apps/inventory/views.py
"""
Views للمخازن
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from .models import (
    StockIn, StockOut, StockTransfer, StockCount, StockCountLine, StockMovement,
    ItemStock, StockDocumentLine, StockTransferLine, StockCountLine, Batch
)
from .forms import (
    StockInForm, StockOutForm, StockTransferForm, StockCountForm,
    StockInLineFormSet, StockOutLineFormSet, StockTransferLineFormSet,
    StockCountLineFormSet, ItemStockForm, BatchForm
)
from apps.core.models import Item, ItemVariant, Warehouse
from apps.core.mixins import CompanyMixin, AuditLogMixin

logger = logging.getLogger(__name__)


# ====== Dashboard ======

class InventoryDashboardView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم المخازن"""
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.current_company

        # إحصائيات
        context.update({
            'title': _('لوحة تحكم المخازن'),
            'total_warehouses': Warehouse.objects.filter(company=company, is_active=True).count(),
            'total_items_in_stock': ItemStock.objects.filter(company=company, quantity__gt=0).count(),
            'low_stock_items': ItemStock.objects.filter(
                company=company,
                quantity__lte=F('min_level')
            ).exclude(min_level__isnull=True).count(),
            'stock_in_count': StockIn.objects.filter(company=company).count(),
            'stock_out_count': StockOut.objects.filter(company=company).count(),
            'transfer_count': StockTransfer.objects.filter(company=company).count(),
        })

        return context


# ====== Stock In (سند إدخال) ======

class StockInListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سندات الإدخال"""
    model = StockIn
    template_name = 'inventory/stock_in/stock_in_list.html'
    context_object_name = 'stock_ins'
    permission_required = 'inventory.view_stockin'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'warehouse', 'supplier', 'created_by', 'posted_by'
        ).prefetch_related('lines')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(reference__icontains=search) |
                Q(supplier__name__icontains=search)
            )

        # التصفية حسب الحالة
        status = self.request.GET.get('status')
        if status == 'posted':
            queryset = queryset.filter(is_posted=True)
        elif status == 'draft':
            queryset = queryset.filter(is_posted=False)

        return queryset.order_by('-date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('سندات الإدخال'),
            'can_add': self.request.user.has_perm('inventory.add_stockin'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإدخال'), 'url': ''}
            ],
        })
        return context


class StockInCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة سند إدخال جديد"""
    model = StockIn
    form_class = StockInForm
    template_name = 'inventory/stock_in/stock_in_form.html'
    permission_required = 'inventory.add_stockin'
    success_url = reverse_lazy('inventory:stock_in_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockInLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockInLineFormSet(instance=self.object)

        # إضافة قائمة المواد
        company = self.current_company
        context['items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).select_related('base_uom').order_by('name')

        context.update({
            'title': _('إضافة سند إدخال'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإدخال'), 'url': reverse('inventory:stock_in_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ السند'),
            'cancel_url': reverse('inventory:stock_in_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.company = self.current_company
            self.object.branch = getattr(self.request, 'current_branch', None)
            self.object.created_by = self.request.user
            self.object.save()

            lines_formset.instance = self.object
            lines_formset.save()

            messages.success(
                self.request,
                _('تم إضافة سند الإدخال "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            # Add formset errors to messages
            for i, form_errors in enumerate(lines_formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(
                                self.request,
                                f'الصف {i+1} - {field}: {error}'
                            )

            # Add non-form errors
            if lines_formset.non_form_errors():
                for error in lines_formset.non_form_errors():
                    messages.error(self.request, error)

            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        """Handle invalid form submission"""
        # Show form errors in messages
        for field, errors in form.errors.items():
            for error in errors:
                field_label = form.fields.get(field).label if field in form.fields else field
                messages.error(
                    self.request,
                    f'{field_label}: {error}'
                )
        return super().form_invalid(form)


class StockInUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سند إدخال"""
    model = StockIn
    form_class = StockInForm
    template_name = 'inventory/stock_in/stock_in_form.html'
    permission_required = 'inventory.change_stockin'
    success_url = reverse_lazy('inventory:stock_in_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockInLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockInLineFormSet(instance=self.object)

        company = self.current_company
        context['items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).select_related('base_uom').order_by('name')

        context.update({
            'title': _('تعديل سند الإدخال: %(number)s') % {'number': self.object.number},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإدخال'), 'url': reverse('inventory:stock_in_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('inventory:stock_in_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        # التحقق من أن السند غير مرحل
        if self.object.is_posted:
            messages.error(self.request, _('لا يمكن تعديل سند مرحل'))
            return redirect(self.success_url)

        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save()
            lines_formset.save()

            messages.success(
                self.request,
                _('تم تحديث سند الإدخال "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class StockInDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل سند إدخال"""
    model = StockIn
    template_name = 'inventory/stock_in/stock_in_detail.html'
    context_object_name = 'stock_in'
    permission_required = 'inventory.view_stockin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('سند الإدخال: %(number)s') % {'number': self.object.number},
            'can_change': self.request.user.has_perm('inventory.change_stockin'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockin'),
            'can_post': self.request.user.has_perm('inventory.can_post_stock_document'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإدخال'), 'url': reverse('inventory:stock_in_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
        })
        return context


class StockInPostView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """ترحيل سند إدخال"""
    model = StockIn
    permission_required = 'inventory.can_post_stock_document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.post(user=request.user)
            messages.success(
                request,
                _('تم ترحيل سند الإدخال "%(number)s" بنجاح') % {'number': self.object.number}
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect('inventory:stock_in_detail', pk=self.object.pk)


class StockInUnpostView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """إلغاء ترحيل سند إدخال"""
    model = StockIn
    permission_required = 'inventory.can_post_stock_document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.unpost()
            messages.success(
                request,
                _('تم إلغاء ترحيل سند الإدخال "%(number)s" بنجاح') % {'number': self.object.number}
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect('inventory:stock_in_detail', pk=self.object.pk)


# ====== Stock Out (سند إخراج) ======

class StockOutListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة سندات الإخراج"""
    model = StockOut
    template_name = 'inventory/stock_out/stock_out_list.html'
    context_object_name = 'stock_outs'
    permission_required = 'inventory.view_stockout'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'warehouse', 'customer', 'created_by', 'posted_by'
        ).prefetch_related('lines')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(reference__icontains=search) |
                Q(customer__name__icontains=search)
            )

        status = self.request.GET.get('status')
        if status == 'posted':
            queryset = queryset.filter(is_posted=True)
        elif status == 'draft':
            queryset = queryset.filter(is_posted=False)

        return queryset.order_by('-date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('سندات الإخراج'),
            'can_add': self.request.user.has_perm('inventory.add_stockout'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإخراج'), 'url': ''}
            ],
        })
        return context


class StockOutCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة سند إخراج جديد"""
    model = StockOut
    form_class = StockOutForm
    template_name = 'inventory/stock_out/stock_out_form.html'
    permission_required = 'inventory.add_stockout'
    success_url = reverse_lazy('inventory:stock_out_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockOutLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockOutLineFormSet(instance=self.object)

        company = self.current_company
        context['items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).select_related('base_uom').order_by('name')

        context.update({
            'title': _('إضافة سند إخراج'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإخراج'), 'url': reverse('inventory:stock_out_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ السند'),
            'cancel_url': reverse('inventory:stock_out_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.company = self.current_company
            self.object.branch = getattr(self.request, 'current_branch', None)
            self.object.created_by = self.request.user
            self.object.save()

            lines_formset.instance = self.object
            lines_formset.save()

            messages.success(
                self.request,
                _('تم إضافة سند الإخراج "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class StockOutUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل سند إخراج"""
    model = StockOut
    form_class = StockOutForm
    template_name = 'inventory/stock_out/stock_out_form.html'
    permission_required = 'inventory.change_stockout'
    success_url = reverse_lazy('inventory:stock_out_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockOutLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockOutLineFormSet(instance=self.object)

        company = self.current_company
        context['items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).select_related('base_uom').order_by('name')

        context.update({
            'title': _('تعديل سند الإخراج: %(number)s') % {'number': self.object.number},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإخراج'), 'url': reverse('inventory:stock_out_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('inventory:stock_out_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        if self.object.is_posted:
            messages.error(self.request, _('لا يمكن تعديل سند مرحل'))
            return redirect(self.success_url)

        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save()
            lines_formset.save()

            messages.success(
                self.request,
                _('تم تحديث سند الإخراج "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class StockOutDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل سند إخراج"""
    model = StockOut
    template_name = 'inventory/stock_out/stock_out_detail.html'
    context_object_name = 'stock_out'
    permission_required = 'inventory.view_stockout'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('سند الإخراج: %(number)s') % {'number': self.object.number},
            'can_change': self.request.user.has_perm('inventory.change_stockout'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockout'),
            'can_post': self.request.user.has_perm('inventory.can_post_stock_document'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('سندات الإخراج'), 'url': reverse('inventory:stock_out_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
        })
        return context


class StockOutPostView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """ترحيل سند إخراج"""
    model = StockOut
    permission_required = 'inventory.can_post_stock_document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.post(user=request.user)
            messages.success(
                request,
                _('تم ترحيل سند الإخراج "%(number)s" بنجاح') % {'number': self.object.number}
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect('inventory:stock_out_detail', pk=self.object.pk)


class StockOutUnpostView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """إلغاء ترحيل سند إخراج"""
    model = StockOut
    permission_required = 'inventory.can_post_stock_document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.unpost()
            messages.success(
                request,
                _('تم إلغاء ترحيل سند الإخراج "%(number)s" بنجاح') % {'number': self.object.number}
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect('inventory:stock_out_detail', pk=self.object.pk)


# ====== Stock Transfers (التحويلات) ======

class StockTransferListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة التحويلات"""
    model = StockTransfer
    template_name = 'inventory/transfer/transfer_list.html'
    context_object_name = 'transfers'
    permission_required = 'inventory.view_stocktransfer'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'warehouse', 'destination_warehouse', 'created_by',
            'approved_by', 'received_by', 'posted_by'
        ).prefetch_related('lines')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(reference__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('التحويلات المخزنية'),
            'can_add': self.request.user.has_perm('inventory.add_stocktransfer'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('التحويلات'), 'url': ''}
            ],
        })
        return context


class StockTransferCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة تحويل جديد"""
    model = StockTransfer
    form_class = StockTransferForm
    template_name = 'inventory/transfer/transfer_form.html'
    permission_required = 'inventory.add_stocktransfer'
    success_url = reverse_lazy('inventory:transfer_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockTransferLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockTransferLineFormSet(instance=self.object)

        company = self.current_company
        context['items'] = Item.objects.filter(
            company=company,
            is_active=True
        ).select_related('base_uom').order_by('name')

        context.update({
            'title': _('إضافة تحويل مخزني'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('التحويلات'), 'url': reverse('inventory:transfer_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ التحويل'),
            'cancel_url': reverse('inventory:transfer_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.company = self.current_company
            self.object.branch = getattr(self.request, 'current_branch', None)
            self.object.created_by = self.request.user
            self.object.status = 'draft'
            self.object.save()

            lines_formset.instance = self.object
            lines_formset.save()

            messages.success(
                self.request,
                _('تم إضافة التحويل "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class StockTransferDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل التحويل"""
    model = StockTransfer
    template_name = 'inventory/transfer/transfer_detail.html'
    context_object_name = 'transfer'
    permission_required = 'inventory.view_stocktransfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('التحويل: %(number)s') % {'number': self.object.number},
            'can_change': self.request.user.has_perm('inventory.change_stocktransfer'),
            'can_approve': self.request.user.has_perm('inventory.can_approve_transfer'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('التحويلات'), 'url': reverse('inventory:transfer_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
        })
        return context


# ====== Stock Reports ======

class StockReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير المخزون"""
    template_name = 'inventory/reports/stock_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.current_company

        # الحصول على الفلاتر
        warehouse_id = self.request.GET.get('warehouse')
        item_id = self.request.GET.get('item')

        # بناء الاستعلام
        stock_query = ItemStock.objects.filter(company=company)

        if warehouse_id:
            stock_query = stock_query.filter(warehouse_id=warehouse_id)

        if item_id:
            stock_query = stock_query.filter(item_id=item_id)

        stock_items = stock_query.select_related(
            'item', 'item_variant', 'warehouse'
        ).order_by('warehouse__name', 'item__name')

        context.update({
            'title': _('تقرير المخزون'),
            'stock_items': stock_items,
            'warehouses': Warehouse.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('تقرير المخزون'), 'url': ''}
            ],
        })
        return context


class StockMovementReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير حركة المواد"""
    template_name = 'inventory/reports/movement_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.current_company

        # الفلاتر
        item_id = self.request.GET.get('item')
        warehouse_id = self.request.GET.get('warehouse')
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')

        movements = StockMovement.objects.filter(company=company)

        if item_id:
            movements = movements.filter(item_id=item_id)
        if warehouse_id:
            movements = movements.filter(warehouse_id=warehouse_id)
        if from_date:
            movements = movements.filter(date__gte=from_date)
        if to_date:
            movements = movements.filter(date__lte=to_date)

        movements = movements.select_related(
            'item', 'item_variant', 'warehouse', 'created_by'
        ).order_by('-date')

        context.update({
            'title': _('تقرير حركة المواد'),
            'movements': movements,
            'warehouses': Warehouse.objects.filter(company=company, is_active=True),
            'items': Item.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('تقرير الحركات'), 'url': ''}
            ],
        })
        return context


# ========== Stock Count Views (نظام الجرد) ==========

class StockCountListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة الجرد"""
    model = StockCount
    template_name = 'inventory/stock_count/count_list.html'
    context_object_name = 'counts'
    permission_required = 'inventory.view_stockcount'
    paginate_by = 20

    def get_queryset(self):
        queryset = StockCount.objects.filter(company=self.current_company)

        # Filters
        warehouse_id = self.request.GET.get('warehouse')
        status = self.request.GET.get('status')
        count_type = self.request.GET.get('count_type')

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if status:
            queryset = queryset.filter(status=status)
        if count_type:
            queryset = queryset.filter(count_type=count_type)

        return queryset.select_related('warehouse', 'supervisor').order_by('-date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('الجرد'),
            'warehouses': Warehouse.objects.filter(company=self.current_company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الجرد'), 'url': ''}
            ],
        })
        return context


class StockCountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء جرد جديد"""
    model = StockCount
    form_class = StockCountForm
    template_name = 'inventory/stock_count/count_form.html'
    permission_required = 'inventory.add_stockcount'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.current_company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.current_company
        form.instance.created_by = self.request.user

        response = super().form_valid(form)

        # Auto-populate lines with current stock
        warehouse = form.instance.warehouse
        stocks = ItemStock.objects.filter(
            company=self.current_company,
            warehouse=warehouse,
            quantity__gt=0
        ).select_related('item')

        for stock in stocks:
            StockCountLine.objects.create(
                count=self.object,
                item=stock.item,
                system_quantity=stock.quantity,
                counted_quantity=0,
                unit_cost=stock.average_cost,
                system_value=stock.total_value,
                counted_value=0,
                difference_quantity=0,
                difference_value=0
            )

        messages.success(self.request, _('تم إنشاء الجرد بنجاح'))
        return response

    def get_success_url(self):
        return reverse('inventory:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('جرد جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الجرد'), 'url': reverse('inventory:count_list')},
                {'title': _('جديد'), 'url': ''}
            ],
        })
        return context


class StockCountDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل الجرد"""
    model = StockCount
    template_name = 'inventory/stock_count/count_detail.html'
    context_object_name = 'count'
    permission_required = 'inventory.view_stockcount'

    def get_queryset(self):
        return StockCount.objects.filter(company=self.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'{self.object.number}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الجرد'), 'url': reverse('inventory:count_list')},
                {'title': self.object.number, 'url': ''}
            ],
        })
        return context


class StockCountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل الجرد"""
    model = StockCount
    form_class = StockCountForm
    template_name = 'inventory/stock_count/count_form.html'
    permission_required = 'inventory.change_stockcount'

    def get_queryset(self):
        return StockCount.objects.filter(
            company=self.current_company,
            status__in=['planned', 'in_progress']
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.current_company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم تحديث الجرد بنجاح'))
        return response

    def get_success_url(self):
        return reverse('inventory:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل جرد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الجرد'), 'url': reverse('inventory:count_list')},
                {'title': self.object.number, 'url': reverse('inventory:count_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class StockCountProcessView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """معالجة الجرد وإنشاء التسويات"""
    model = StockCount
    permission_required = 'inventory.change_stockcount'

    def get_queryset(self):
        return StockCount.objects.filter(company=self.current_company)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status not in ['completed', 'approved']:
            messages.error(request, _('يجب أن يكون الجرد مكتملاً أو معتمداً'))
            return redirect('inventory:count_detail', pk=self.object.pk)

        try:
            with transaction.atomic():
                # Process each line
                for line in self.object.lines.all():
                    if line.difference_quantity != 0:
                        # Get or create item stock
                        stock, created = ItemStock.objects.get_or_create(
                            company=self.current_company,
                            item=line.item,
                            warehouse=self.object.warehouse,
                            defaults={
                                'quantity': 0,
                                'average_cost': line.unit_cost,
                                'total_value': 0,
                                'created_by': request.user
                            }
                        )

                        # Adjust stock
                        old_quantity = stock.quantity
                        old_value = stock.total_value

                        stock.quantity = line.counted_quantity
                        stock.total_value = line.counted_value

                        if stock.quantity > 0:
                            stock.average_cost = stock.total_value / stock.quantity
                        else:
                            stock.average_cost = 0

                        stock.save()

                        # Create stock movement
                        StockMovement.objects.create(
                            company=self.current_company,
                            item=line.item,
                            warehouse=self.object.warehouse,
                            movement_type='in' if line.difference_quantity > 0 else 'out',
                            quantity=abs(line.difference_quantity),
                            unit_cost=line.unit_cost,
                            total_cost=abs(line.difference_value),
                            balance_before=old_quantity,
                            balance_quantity=stock.quantity,
                            balance_value=stock.total_value,
                            reference_type='stock_count',
                            reference_id=self.object.pk,
                            reference_number=self.object.number,
                            created_by=request.user
                        )

                # Update status
                self.object.status = 'approved'
                self.object.approved_by = request.user
                self.object.approval_date = timezone.now()
                self.object.save()

                messages.success(request, _('تم معالجة الجرد وتحديث الأرصدة بنجاح'))

        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')

        return redirect('inventory:count_detail', pk=self.object.pk)


# ========== Batch Views (نظام الدفعات) ==========

class BatchListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة الدفعات"""
    model = Batch
    template_name = 'inventory/batches/batch_list.html'
    context_object_name = 'batches'
    permission_required = 'inventory.view_batch'
    paginate_by = 50

    def get_queryset(self):
        queryset = Batch.objects.filter(company=self.current_company).select_related(
            'item', 'item_variant', 'warehouse', 'created_by'
        )

        # Filters
        warehouse_id = self.request.GET.get('warehouse')
        item_id = self.request.GET.get('item')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if search:
            queryset = queryset.filter(
                Q(batch_number__icontains=search) |
                Q(item__name__icontains=search)
            )

        # Filter by expiry status
        if status == 'expired':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date())
        elif status == 'expiring_soon':
            # الدفعات التي ستنتهي خلال 30 يوم
            from datetime import timedelta
            future_date = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                expiry_date__gte=timezone.now().date(),
                expiry_date__lte=future_date
            )
        elif status == 'active':
            # الدفعات النشطة (غير منتهية ولديها كمية)
            queryset = queryset.filter(
                Q(expiry_date__isnull=True) | Q(expiry_date__gte=timezone.now().date())
            ).filter(quantity__gt=0)

        return queryset.order_by('expiry_date', 'received_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Count expired batches
        expired_count = Batch.objects.filter(
            company=self.current_company,
            expiry_date__lt=timezone.now().date(),
            quantity__gt=0
        ).count()

        # Count expiring soon (within 30 days)
        from datetime import timedelta
        future_date = timezone.now().date() + timedelta(days=30)
        expiring_soon_count = Batch.objects.filter(
            company=self.current_company,
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=future_date,
            quantity__gt=0
        ).count()

        context.update({
            'title': _('الدفعات'),
            'warehouses': Warehouse.objects.filter(company=self.current_company, is_active=True),
            'items': Item.objects.filter(company=self.current_company, is_active=True),
            'expired_count': expired_count,
            'expiring_soon_count': expiring_soon_count,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الدفعات'), 'url': ''}
            ],
        })
        return context


class BatchDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل الدفعة"""
    model = Batch
    template_name = 'inventory/batches/batch_detail.html'
    context_object_name = 'batch'
    permission_required = 'inventory.view_batch'

    def get_queryset(self):
        return Batch.objects.filter(company=self.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'{_("الدفعة")}: {self.object.batch_number}',
            'can_change': self.request.user.has_perm('inventory.change_batch'),
            'can_delete': self.request.user.has_perm('inventory.delete_batch'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الدفعات'), 'url': reverse('inventory:batch_list')},
                {'title': self.object.batch_number, 'url': ''}
            ],
        })
        return context


class BatchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة دفعة جديدة"""
    model = Batch
    form_class = BatchForm
    template_name = 'inventory/batches/batch_form.html'
    permission_required = 'inventory.add_batch'
    success_url = reverse_lazy('inventory:batch_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.current_company
        form.instance.created_by = self.request.user

        # Calculate total value
        form.instance.total_value = form.instance.quantity * form.instance.unit_cost

        response = super().form_valid(form)
        messages.success(self.request, _('تم إضافة الدفعة بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة دفعة جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الدفعات'), 'url': reverse('inventory:batch_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الدفعة'),
            'cancel_url': reverse('inventory:batch_list'),
        })
        return context


class BatchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل دفعة"""
    model = Batch
    form_class = BatchForm
    template_name = 'inventory/batches/batch_form.html'
    permission_required = 'inventory.change_batch'
    success_url = reverse_lazy('inventory:batch_list')

    def get_queryset(self):
        return Batch.objects.filter(company=self.current_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # Recalculate total value
        form.instance.total_value = form.instance.quantity * form.instance.unit_cost

        response = super().form_valid(form)
        messages.success(self.request, _('تم تحديث الدفعة بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'{_("تعديل الدفعة")}: {self.object.batch_number}',
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الدفعات'), 'url': reverse('inventory:batch_list')},
                {'title': self.object.batch_number, 'url': reverse('inventory:batch_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('inventory:batch_list'),
            'is_update': True,
        })
        return context


class BatchExpiredReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الدفعات المنتهية أو القريبة من الانتهاء"""
    template_name = 'inventory/batches/expired_batches_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.current_company

        # Get filter parameters
        warehouse_id = self.request.GET.get('warehouse')
        days_threshold = int(self.request.GET.get('days', 30))  # Default: 30 days

        # Base queryset
        batches = Batch.objects.filter(
            company=company,
            expiry_date__isnull=False,
            quantity__gt=0
        ).select_related('item', 'item_variant', 'warehouse')

        if warehouse_id:
            batches = batches.filter(warehouse_id=warehouse_id)

        # Separate into categories
        today = timezone.now().date()
        from datetime import timedelta
        future_date = today + timedelta(days=days_threshold)

        expired_batches = batches.filter(expiry_date__lt=today).order_by('expiry_date')
        expiring_soon_batches = batches.filter(
            expiry_date__gte=today,
            expiry_date__lte=future_date
        ).order_by('expiry_date')

        # Calculate totals
        expired_total_value = sum(b.total_value for b in expired_batches)
        expiring_total_value = sum(b.total_value for b in expiring_soon_batches)

        context.update({
            'title': _('تقرير الدفعات المنتهية'),
            'expired_batches': expired_batches,
            'expiring_soon_batches': expiring_soon_batches,
            'expired_total_value': expired_total_value,
            'expiring_total_value': expiring_total_value,
            'days_threshold': days_threshold,
            'warehouses': Warehouse.objects.filter(company=company, is_active=True),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('تقرير الدفعات المنتهية'), 'url': ''}
            ],
        })
        return context

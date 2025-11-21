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
    StockIn, StockOut, StockTransfer, StockCount, StockMovement,
    ItemStock, StockDocumentLine, StockTransferLine, StockCountLine
)
from .forms import (
    StockInForm, StockOutForm, StockTransferForm, StockCountForm,
    StockInLineFormSet, StockOutLineFormSet, StockTransferLineFormSet,
    StockCountLineFormSet, ItemStockForm
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
            return self.render_to_response(self.get_context_data(form=form))


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

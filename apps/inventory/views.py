# apps/inventory/views.py
"""
Views للمخازن
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, View
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta
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
        company = self.current_company

        # Get current month start and end dates
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Statistics
        base_queryset = StockIn.objects.filter(company=company)

        context.update({
            'title': _('سندات الإدخال'),
            'can_add': self.request.user.has_perm('inventory.add_stockin'),
            'can_edit': self.request.user.has_perm('inventory.change_stockin'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockin'),
            # Statistics
            'total_count': base_queryset.count(),
            'draft_count': base_queryset.filter(is_posted=False).count(),
            'posted_count': base_queryset.filter(is_posted=True).count(),
            'this_month_count': base_queryset.filter(date__gte=month_start).count(),
            'warehouses': Warehouse.objects.filter(company=company, is_active=True).order_by('name'),
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


class StockInDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف سند إدخال"""
    model = StockIn
    template_name = 'inventory/stock_in/stock_in_confirm_delete.html'
    permission_required = 'inventory.delete_stockin'
    success_url = reverse_lazy('inventory:stock_in_list')

    def get_queryset(self):
        # يمكن حذف السندات غير المرحلة فقط
        return StockIn.objects.filter(company=self.current_company, is_posted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_posted:
            messages.error(request, _('لا يمكن حذف سند مرحل'))
            return redirect('inventory:stock_in_list')

        number = self.object.number
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('تم حذف سند الإدخال "%(number)s" بنجاح') % {'number': number})
        return response


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
        company = self.current_company

        # Get current month start and end dates
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Statistics
        base_queryset = StockOut.objects.filter(company=company)

        context.update({
            'title': _('سندات الإخراج'),
            'can_add': self.request.user.has_perm('inventory.add_stockout'),
            'can_edit': self.request.user.has_perm('inventory.change_stockout'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockout'),
            # Statistics
            'total_count': base_queryset.count(),
            'draft_count': base_queryset.filter(is_posted=False).count(),
            'posted_count': base_queryset.filter(is_posted=True).count(),
            'this_month_count': base_queryset.filter(date__gte=month_start).count(),
            'warehouses': Warehouse.objects.filter(company=company, is_active=True).order_by('name'),
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


class StockOutDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف سند إخراج"""
    model = StockOut
    template_name = 'inventory/stock_out/stock_out_confirm_delete.html'
    permission_required = 'inventory.delete_stockout'
    success_url = reverse_lazy('inventory:stock_out_list')

    def get_queryset(self):
        # يمكن حذف السندات غير المرحلة فقط
        return StockOut.objects.filter(company=self.current_company, is_posted=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_posted:
            messages.error(request, _('لا يمكن حذف سند مرحل'))
            return redirect('inventory:stock_out_list')

        number = self.object.number
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('تم حذف سند الإخراج "%(number)s" بنجاح') % {'number': number})
        return response


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
        company = self.current_company

        # Get current month start and end dates
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Statistics
        base_queryset = StockTransfer.objects.filter(company=company)

        context.update({
            'title': _('التحويلات المخزنية'),
            'can_add': self.request.user.has_perm('inventory.add_stocktransfer'),
            'can_edit': self.request.user.has_perm('inventory.change_stocktransfer'),
            'can_delete': self.request.user.has_perm('inventory.delete_stocktransfer'),
            # Statistics
            'total_count': base_queryset.count(),
            'draft_count': base_queryset.filter(status='draft').count(),
            'approved_count': base_queryset.filter(status='approved').count(),
            'in_transit_count': base_queryset.filter(status='in_transit').count(),
            'received_count': base_queryset.filter(status='received').count(),
            'this_month_count': base_queryset.filter(date__gte=month_start).count(),
            'warehouses': Warehouse.objects.filter(company=company, is_active=True).order_by('name'),
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


class StockTransferUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل تحويل"""
    model = StockTransfer
    form_class = StockTransferForm
    template_name = 'inventory/transfer/transfer_form.html'
    permission_required = 'inventory.change_stocktransfer'
    success_url = reverse_lazy('inventory:transfer_list')

    def get_queryset(self):
        # يمكن تعديل التحويلات في حالة draft فقط
        return StockTransfer.objects.filter(company=self.current_company, status='draft')

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
            'title': _('تعديل التحويل: %(number)s') % {'number': self.object.number},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('التحويلات'), 'url': reverse('inventory:transfer_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('inventory:transfer_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        if self.object.status != 'draft':
            messages.error(self.request, _('لا يمكن تعديل تحويل معتمد'))
            return redirect(self.success_url)

        context = self.get_context_data()
        lines_formset = context['lines_formset']

        if lines_formset.is_valid():
            self.object = form.save()
            lines_formset.save()

            messages.success(
                self.request,
                _('تم تحديث التحويل "%(number)s" بنجاح') % {'number': self.object.number}
            )
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class StockTransferDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف تحويل"""
    model = StockTransfer
    template_name = 'inventory/transfer/transfer_confirm_delete.html'
    permission_required = 'inventory.delete_stocktransfer'
    success_url = reverse_lazy('inventory:transfer_list')

    def get_queryset(self):
        # يمكن حذف التحويلات في حالة draft فقط
        return StockTransfer.objects.filter(company=self.current_company, status='draft')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status != 'draft':
            messages.error(request, _('لا يمكن حذف تحويل معتمد'))
            return redirect('inventory:transfer_list')

        number = self.object.number
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('تم حذف التحويل "%(number)s" بنجاح') % {'number': number})
        return response


class StockTransferApproveView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """اعتماد تحويل"""
    model = StockTransfer
    permission_required = 'inventory.can_approve_transfer'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status != 'draft':
            messages.error(request, _('هذا التحويل تم اعتماده مسبقاً أو في مرحلة أخرى'))
            return redirect('inventory:transfer_detail', pk=self.object.pk)

        try:
            with transaction.atomic():
                # Update status to approved
                self.object.status = 'approved'
                self.object.approved_by = request.user
                self.object.approval_date = timezone.now()
                self.object.save()

                messages.success(
                    request,
                    _('تم اعتماد التحويل "%(number)s" بنجاح') % {'number': self.object.number}
                )
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')

        return redirect('inventory:transfer_detail', pk=self.object.pk)


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
        company = self.current_company

        # Get current month start and end dates
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Statistics
        base_queryset = StockCount.objects.filter(company=company)

        context.update({
            'title': _('الجرد'),
            'can_add': self.request.user.has_perm('inventory.add_stockcount'),
            'can_edit': self.request.user.has_perm('inventory.change_stockcount'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockcount'),
            # Statistics
            'total_count': base_queryset.count(),
            'planned_count': base_queryset.filter(status='planned').count(),
            'in_progress_count': base_queryset.filter(status='in_progress').count(),
            'completed_count': base_queryset.filter(status='completed').count(),
            'approved_count': base_queryset.filter(status='approved').count(),
            'processed_count': base_queryset.filter(status='processed').count(),
            'this_month_count': base_queryset.filter(date__gte=month_start).count(),
            'warehouses': Warehouse.objects.filter(company=company, is_active=True).order_by('name'),
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

        # التحقق من وجود المستودع
        warehouse = form.cleaned_data.get('warehouse')
        if not warehouse:
            messages.error(self.request, _('يجب تحديد المستودع لإنشاء جرد المخزون'))
            return self.form_invalid(form)

        try:
            response = super().form_valid(form)

            # Auto-populate lines with current stock
            stocks = ItemStock.objects.filter(
                company=self.current_company,
                warehouse=warehouse,
                quantity__gt=0
            ).select_related('item')

            # التحقق من وجود مخزون
            if not stocks.exists():
                messages.warning(
                    self.request,
                    _('تم إنشاء الجرد بنجاح، لكن المستودع "{}" فارغ حالياً. لا توجد مواد للجرد.').format(warehouse.name)
                )
                return response

            # إنشاء سطور الجرد
            lines_created = 0
            for stock in stocks:
                try:
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
                    lines_created += 1
                except Exception as e:
                    # تسجيل الخطأ ولكن المتابعة
                    print(f"خطأ في إنشاء سطر الجرد للمادة {stock.item.name}: {str(e)}")
                    continue

            if lines_created > 0:
                messages.success(
                    self.request,
                    _('تم إنشاء الجرد بنجاح وتم إضافة {} مادة للجرد').format(lines_created)
                )
            else:
                messages.warning(
                    self.request,
                    _('تم إنشاء الجرد لكن لم يتم إضافة أي مواد بسبب أخطاء. يرجى المحاولة مرة أخرى.')
                )

        except Exception as e:
            messages.error(
                self.request,
                _('حدث خطأ أثناء إنشاء الجرد: {}').format(str(e))
            )
            return self.form_invalid(form)

        return response

    def get_success_url(self):
        return reverse('inventory:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('جرد جديد'),
            'submit_text': _('إنشاء الجرد'),
            'cancel_url': reverse('inventory:count_list'),
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
    context_object_name = 'stock_count'
    permission_required = 'inventory.view_stockcount'

    def get_queryset(self):
        return StockCount.objects.filter(company=self.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'{self.object.number}',
            'can_change': self.request.user.has_perm('inventory.change_stockcount'),
            'can_delete': self.request.user.has_perm('inventory.delete_stockcount'),
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
        context = self.get_context_data()
        formset = context['lines_formset']

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, _('تم تحديث الجرد والمواد بنجاح'))
            return redirect(self.get_success_url())
        else:
            # طباعة الأخطاء للمطور
            print("Formset Errors:", formset.errors)
            print("Formset Non-Form Errors:", formset.non_form_errors())

            # رسالة خطأ مفصلة للمستخدم
            error_details = []
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    error_details.append(f"السطر {i+1}: {form_errors}")

            error_message = _('يرجى تصحيح الأخطاء في المواد')
            if error_details:
                error_message += ': ' + ', '.join(error_details)

            messages.error(self.request, error_message)
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('inventory:count_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['lines_formset'] = StockCountLineFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['lines_formset'] = StockCountLineFormSet(
                instance=self.object
            )

        context.update({
            'title': _('تعديل جرد'),
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('inventory:count_detail', kwargs={'pk': self.object.pk}),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الجرد'), 'url': reverse('inventory:count_list')},
                {'title': self.object.number, 'url': reverse('inventory:count_detail', kwargs={'pk': self.object.pk})},
                {'title': _('تعديل'), 'url': ''}
            ],
        })
        return context


class StockCountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف جرد"""
    model = StockCount
    template_name = 'inventory/stock_count/count_confirm_delete.html'
    permission_required = 'inventory.delete_stockcount'
    success_url = reverse_lazy('inventory:count_list')

    def get_queryset(self):
        # يمكن حذف الجرد في حالات planned أو in_progress فقط
        return StockCount.objects.filter(
            company=self.current_company,
            status__in=['planned', 'in_progress']
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status not in ['planned', 'in_progress']:
            messages.error(request, _('لا يمكن حذف جرد مكتمل أو معتمد'))
            return redirect('inventory:count_list')

        number = self.object.number
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('تم حذف الجرد "%(number)s" بنجاح') % {'number': number})
        return response


class StockCountProcessView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, View):
    """معالجة الجرد وإنشاء التسويات"""
    permission_required = 'inventory.change_stockcount'

    def get(self, request, pk):
        """Redirect GET requests to detail page"""
        messages.warning(request, _('يجب استخدام زر "معالجة الجرد" من صفحة التفاصيل'))
        return redirect('inventory:count_detail', pk=pk)

    def post(self, request, pk):
        stock_count = get_object_or_404(
            StockCount,
            pk=pk,
            company=self.current_company
        )

        if stock_count.status != 'approved':
            messages.error(request, _('يجب أن يكون الجرد معتمداً لمعالجته'))
            return redirect('inventory:count_detail', pk=stock_count.pk)

        try:
            with transaction.atomic():
                # Process each line
                for line in stock_count.lines.all():
                    if line.difference_quantity != 0:
                        # Get or create item stock (handle duplicates)
                        try:
                            stock, created = ItemStock.objects.get_or_create(
                                company=self.current_company,
                                item=line.item,
                                warehouse=stock_count.warehouse,
                                defaults={
                                    'quantity': 0,
                                    'average_cost': line.unit_cost,
                                    'total_value': 0,
                                    'created_by': request.user
                                }
                            )
                        except ItemStock.MultipleObjectsReturned:
                            # Handle duplicate records - use the first one and merge quantities
                            stocks = ItemStock.objects.filter(
                                company=self.current_company,
                                item=line.item,
                                warehouse=stock_count.warehouse
                            ).order_by('id')

                            # Keep the first, merge quantities from others
                            stock = stocks.first()
                            duplicates = stocks[1:]

                            # Merge quantities
                            for dup in duplicates:
                                stock.quantity += dup.quantity
                                stock.total_value += dup.total_value

                                # Zero out duplicate before deleting (bypass signal)
                                dup.quantity = Decimal('0')
                                dup.total_value = Decimal('0')
                                dup.average_cost = Decimal('0')
                                dup.save()
                                dup.delete()

                            # Recalculate average cost
                            if stock.quantity > 0:
                                stock.average_cost = stock.total_value / stock.quantity
                            stock.save()

                            created = False

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
                            warehouse=stock_count.warehouse,
                            movement_type='in' if line.difference_quantity > 0 else 'out',
                            quantity=abs(line.difference_quantity),
                            unit_cost=line.unit_cost,
                            total_cost=abs(line.difference_value),
                            balance_before=old_quantity,
                            balance_quantity=stock.quantity,
                            balance_value=stock.total_value,
                            reference_type='stock_count',
                            reference_id=stock_count.pk,
                            reference_number=stock_count.number,
                            created_by=request.user
                        )

                # Update status to processed
                stock_count.status = 'processed'
                stock_count.processed_by = request.user
                stock_count.processed_at = timezone.now()
                stock_count.save()

                messages.success(request, _('تم معالجة الجرد وتحديث الأرصدة بنجاح'))

        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')

        return redirect('inventory:count_detail', pk=stock_count.pk)


class StockCountStartView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, View):
    """بدء عملية الجرد (planned → in_progress)"""
    permission_required = 'inventory.change_stockcount'

    def get(self, request, pk):
        """Redirect GET requests to detail page"""
        messages.warning(request, _('يجب استخدام زر "بدء الجرد" من صفحة التفاصيل'))
        return redirect('inventory:count_detail', pk=pk)

    def post(self, request, pk):
        stock_count = get_object_or_404(
            StockCount,
            pk=pk,
            company=self.current_company
        )

        if stock_count.status != 'planned':
            messages.error(request, _('لا يمكن بدء الجرد في الحالة الحالية'))
            return redirect('inventory:count_detail', pk=pk)

        stock_count.status = 'in_progress'
        stock_count.started_at = timezone.now()
        stock_count.save()

        messages.success(request, _('تم بدء عملية الجرد بنجاح'))
        return redirect('inventory:count_detail', pk=pk)


class StockCountCompleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, View):
    """إتمام عملية الجرد (in_progress → completed)"""
    permission_required = 'inventory.change_stockcount'

    def get(self, request, pk):
        """Redirect GET requests to detail page"""
        messages.warning(request, _('يجب استخدام زر "إتمام الجرد" من صفحة التفاصيل'))
        return redirect('inventory:count_detail', pk=pk)

    def post(self, request, pk):
        stock_count = get_object_or_404(
            StockCount,
            pk=pk,
            company=self.current_company
        )

        if stock_count.status != 'in_progress':
            messages.error(request, _('لا يمكن إتمام الجرد في الحالة الحالية'))
            return redirect('inventory:count_detail', pk=pk)

        # التحقق من أن جميع الكميات تم جردها
        uncounted_lines = stock_count.lines.filter(counted_quantity__isnull=True)
        if uncounted_lines.exists():
            messages.error(
                request,
                _('يرجى إدخال الكميات المجرودة لجميع المواد قبل إتمام الجرد')
            )
            return redirect('inventory:count_update', pk=pk)

        stock_count.status = 'completed'
        stock_count.completed_at = timezone.now()
        stock_count.save()

        messages.success(request, _('تم إتمام عملية الجرد بنجاح. يمكنك الآن معالجة الجرد لتحديث المخزون.'))
        return redirect('inventory:count_detail', pk=pk)


class StockCountApproveView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, View):
    """اعتماد الجرد (completed → approved)"""
    permission_required = 'inventory.change_stockcount'

    def get(self, request, pk):
        """Redirect GET requests to detail page"""
        messages.warning(request, _('يجب استخدام زر "اعتماد الجرد" من صفحة التفاصيل'))
        return redirect('inventory:count_detail', pk=pk)

    def post(self, request, pk):
        stock_count = get_object_or_404(
            StockCount,
            pk=pk,
            company=self.current_company
        )

        if stock_count.status != 'completed':
            messages.error(request, _('لا يمكن اعتماد الجرد في الحالة الحالية'))
            return redirect('inventory:count_detail', pk=pk)

        stock_count.status = 'approved'
        stock_count.approved_by = request.user
        stock_count.approval_date = timezone.now()
        stock_count.save()

        messages.success(request, _('تم اعتماد الجرد بنجاح'))
        return redirect('inventory:count_detail', pk=pk)


class StockCountCancelView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, View):
    """إلغاء الجرد"""
    permission_required = 'inventory.delete_stockcount'

    def get(self, request, pk):
        """Redirect GET requests to detail page"""
        messages.warning(request, _('يجب استخدام زر "إلغاء الجرد" من صفحة التفاصيل'))
        return redirect('inventory:count_detail', pk=pk)

    def post(self, request, pk):
        stock_count = get_object_or_404(
            StockCount,
            pk=pk,
            company=self.current_company
        )

        if stock_count.status in ['approved', 'processed']:
            messages.error(request, _('لا يمكن إلغاء جرد معتمد أو معالج'))
            return redirect('inventory:count_detail', pk=pk)

        stock_count.status = 'cancelled'
        stock_count.save()

        messages.success(request, _('تم إلغاء الجرد بنجاح'))
        return redirect('inventory:count_list')


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
        company = self.current_company

        # Get today's date
        today = timezone.now().date()
        future_date = today + timedelta(days=30)

        # Statistics
        base_queryset = Batch.objects.filter(company=company)

        # Count batches by expiry status
        expired_count = base_queryset.filter(
            expiry_date__isnull=False,
            expiry_date__lt=today
        ).count()

        # Count expiring soon (within 30 days)
        expiring_soon = base_queryset.filter(
            expiry_date__isnull=False,
            expiry_date__gte=today,
            expiry_date__lte=future_date
        ).count()

        # Active batches (not expired or no expiry date)
        active_count = base_queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
        ).count()

        context.update({
            'title': _('الدفعات'),
            'can_add': self.request.user.has_perm('inventory.add_batch'),
            'can_edit': self.request.user.has_perm('inventory.change_batch'),
            'can_delete': self.request.user.has_perm('inventory.delete_batch'),
            # Statistics
            'total_count': base_queryset.count(),
            'active_count': active_count,
            'expired_count': expired_count,
            'expiring_soon': expiring_soon,
            'warehouses': Warehouse.objects.filter(company=company, is_active=True).order_by('name'),
            'items': Item.objects.filter(company=company, is_active=True).order_by('name'),
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


class BatchDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف دفعة"""
    model = Batch
    template_name = 'inventory/batches/batch_confirm_delete.html'
    permission_required = 'inventory.delete_batch'
    success_url = reverse_lazy('inventory:batch_list')

    def get_queryset(self):
        return Batch.objects.filter(company=self.current_company)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # التحقق من عدم وجود كمية في الدفعة
        if self.object.quantity > 0:
            messages.error(request, _('لا يمكن حذف دفعة تحتوي على كمية. الرجاء تصفير الكمية أولاً'))
            return redirect('inventory:batch_list')

        batch_number = self.object.batch_number
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('تم حذف الدفعة "%(number)s" بنجاح') % {'number': batch_number})
        return response


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


# ====== Alerts & Notifications ======

class InventoryAlertsView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """عرض تنبيهات المخزون"""
    template_name = 'inventory/alerts/alerts_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.current_company

        from .services import InventoryAlertService

        # Get filter parameters
        warehouse_id = self.request.GET.get('warehouse')
        days_threshold = int(self.request.GET.get('days', 30))
        severity_filter = self.request.GET.get('severity')

        warehouse = None
        if warehouse_id:
            warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company=company)

        # Get alerts
        alerts = InventoryAlertService.get_all_alerts(
            company,
            warehouse=warehouse,
            days_threshold=days_threshold
        )

        # Filter by severity if specified
        if severity_filter and severity_filter in ['critical', 'high', 'medium', 'low']:
            filtered_alerts = {
                'critical': alerts['critical'] if severity_filter == 'critical' else [],
                'high': alerts['high'] if severity_filter == 'high' else [],
                'medium': alerts['medium'] if severity_filter == 'medium' else [],
                'low': alerts['low'] if severity_filter == 'low' else [],
                'total_count': len(alerts.get(severity_filter, []))
            }
            alerts = filtered_alerts

        context.update({
            'title': _('تنبيهات المخزون'),
            'alerts': alerts,
            'warehouses': Warehouse.objects.filter(company=company, is_active=True),
            'selected_warehouse': warehouse_id,
            'days_threshold': days_threshold,
            'severity_filter': severity_filter,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('التنبيهات'), 'url': ''}
            ],
        })
        return context


class InventoryAlertsAPIView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """API للحصول على تنبيهات المخزون (JSON)"""

    def get(self, request, *args, **kwargs):
        from .services import InventoryAlertService

        company = self.current_company
        warehouse_id = request.GET.get('warehouse')
        days_threshold = int(request.GET.get('days', 30))
        summary_only = request.GET.get('summary', 'false').lower() == 'true'

        warehouse = None
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(pk=warehouse_id, company=company)
            except Warehouse.DoesNotExist:
                return JsonResponse({'error': 'Warehouse not found'}, status=404)

        if summary_only:
            data = InventoryAlertService.get_alerts_summary(company)
        else:
            alerts = InventoryAlertService.get_all_alerts(
                company,
                warehouse=warehouse,
                days_threshold=days_threshold
            )
            # Convert to JSON-serializable format
            data = {
                'critical': [self._serialize_alert(a) for a in alerts['critical']],
                'high': [self._serialize_alert(a) for a in alerts['high']],
                'medium': [self._serialize_alert(a) for a in alerts['medium']],
                'low': [self._serialize_alert(a) for a in alerts['low']],
                'total_count': alerts['total_count']
            }

        return JsonResponse(data)

    def _serialize_alert(self, alert):
        """تحويل التنبيه لصيغة JSON"""
        result = {
            'type': alert.get('type'),
            'severity': alert.get('severity'),
            'message': alert.get('message'),
        }

        if 'item' in alert and alert['item']:
            result['item'] = {
                'id': alert['item'].pk,
                'name': alert['item'].name,
                'code': alert['item'].code
            }

        if 'warehouse' in alert and alert['warehouse']:
            result['warehouse'] = {
                'id': alert['warehouse'].pk,
                'name': alert['warehouse'].name
            }

        # Add numeric fields
        for field in ['current_qty', 'min_level', 'max_level', 'reorder_point',
                      'quantity', 'days_left']:
            if field in alert:
                result[field] = float(alert[field]) if alert[field] is not None else None

        if 'expiry_date' in alert and alert['expiry_date']:
            result['expiry_date'] = alert['expiry_date'].isoformat()

        if 'batch_number' in alert:
            result['batch_number'] = alert['batch_number']

        return result


# ====== Stock Reservations ======

class StockReservationListView(LoginRequiredMixin, CompanyMixin, ListView):
    """قائمة الحجوزات"""
    template_name = 'inventory/reservations/reservation_list.html'
    context_object_name = 'reservations'
    paginate_by = 50

    def get_queryset(self):
        from .models import StockReservation

        queryset = StockReservation.objects.filter(
            company=self.current_company
        ).select_related(
            'item', 'item_variant', 'warehouse', 'reserved_by'
        )

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by item
        item_id = self.request.GET.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import StockReservation

        # Count by status
        company = self.current_company
        context.update({
            'title': _('حجوزات المخزون'),
            'active_count': StockReservation.objects.filter(
                company=company, status='active'
            ).count(),
            'expired_count': StockReservation.objects.filter(
                company=company, status='expired'
            ).count(),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
                {'title': _('الحجوزات'), 'url': ''}
            ],
        })
        return context


def release_reservation_view(request, pk):
    """إلغاء حجز"""
    from .models import StockReservation
    from .services import ReservationService

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        reservation = get_object_or_404(StockReservation, pk=pk)
        ReservationService.release_reservation(reservation)
        messages.success(request, _('تم إلغاء الحجز بنجاح'))
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ====== AJAX Views ======

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET"])
def ajax_get_item_stock(request):
    """الحصول على رصيد مادة في مستودع محدد"""
    try:
        item_id = request.GET.get('item_id')
        warehouse_id = request.GET.get('warehouse_id')
        variant_id = request.GET.get('variant_id')

        if not item_id or not warehouse_id:
            return JsonResponse({
                'success': False,
                'error': _('معاملات مفقودة: item_id و warehouse_id مطلوبة')
            }, status=400)

        # الحصول على الرصيد
        stock_query = ItemStock.objects.filter(
            item_id=item_id,
            warehouse_id=warehouse_id,
            company=request.current_company
        )

        if variant_id:
            stock_query = stock_query.filter(item_variant_id=variant_id)
        else:
            stock_query = stock_query.filter(item_variant__isnull=True)

        stock = stock_query.first()

        if stock:
            return JsonResponse({
                'success': True,
                'stock': {
                    'id': stock.id,
                    'quantity': float(stock.quantity),
                    'reserved_quantity': float(stock.reserved_quantity),
                    'available_quantity': float(stock.quantity - stock.reserved_quantity),
                    'average_cost': float(stock.average_cost),
                    'total_value': float(stock.total_value),
                    'min_level': float(stock.min_level) if stock.min_level else None,
                    'max_level': float(stock.max_level) if stock.max_level else None,
                    'reorder_point': float(stock.reorder_point) if stock.reorder_point else None,
                    'last_movement_date': stock.last_movement_date.isoformat() if stock.last_movement_date else None,
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'stock': None,
                'message': _('لا يوجد رصيد لهذه المادة في المستودع المحدد')
            })

    except Exception as e:
        logger.error(f"Error in ajax_get_item_stock: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_get_batches(request):
    """الحصول على دفعات مادة في مستودع محدد"""
    try:
        item_id = request.GET.get('item_id')
        warehouse_id = request.GET.get('warehouse_id')
        variant_id = request.GET.get('variant_id')
        include_empty = request.GET.get('include_empty', 'false').lower() == 'true'

        if not item_id or not warehouse_id:
            return JsonResponse({
                'success': False,
                'error': _('معاملات مفقودة: item_id و warehouse_id مطلوبة')
            }, status=400)

        # البحث عن الدفعات
        batches_query = Batch.objects.filter(
            item_id=item_id,
            warehouse_id=warehouse_id,
            company=request.current_company,
            is_active=True
        )

        if variant_id:
            batches_query = batches_query.filter(item_variant_id=variant_id)
        else:
            batches_query = batches_query.filter(item_variant__isnull=True)

        # تصفية الدفعات الفارغة
        if not include_empty:
            batches_query = batches_query.filter(quantity__gt=0)

        batches_query = batches_query.order_by('received_date')  # FIFO

        batches_data = []
        for batch in batches_query:
            batches_data.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'quantity': float(batch.quantity),
                'reserved_quantity': float(batch.reserved_quantity),
                'available_quantity': float(batch.get_available_quantity()),
                'unit_cost': float(batch.unit_cost),
                'total_value': float(batch.total_value),
                'manufacturing_date': batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                'received_date': batch.received_date.isoformat() if batch.received_date else None,
                'is_expired': batch.is_expired(),
                'days_to_expiry': batch.days_to_expiry(),
                'expiry_status': batch.get_expiry_status(),
            })

        return JsonResponse({
            'success': True,
            'batches': batches_data,
            'count': len(batches_data)
        })

    except Exception as e:
        logger.error(f"Error in ajax_get_batches: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ajax_check_availability(request):
    """التحقق من توفر كمية من مادة"""
    try:
        import json
        data = json.loads(request.body)

        item_id = data.get('item_id')
        warehouse_id = data.get('warehouse_id')
        variant_id = data.get('variant_id')
        required_quantity = Decimal(str(data.get('quantity', 0)))

        if not item_id or not warehouse_id or required_quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': _('بيانات غير صحيحة')
            }, status=400)

        # الحصول على الرصيد
        stock_query = ItemStock.objects.filter(
            item_id=item_id,
            warehouse_id=warehouse_id,
            company=request.current_company
        )

        if variant_id:
            stock_query = stock_query.filter(item_variant_id=variant_id)
        else:
            stock_query = stock_query.filter(item_variant__isnull=True)

        stock = stock_query.first()

        if not stock:
            return JsonResponse({
                'success': True,
                'available': False,
                'message': _('لا يوجد رصيد لهذه المادة'),
                'current_quantity': 0,
                'available_quantity': 0,
                'required_quantity': float(required_quantity)
            })

        available_quantity = stock.quantity - stock.reserved_quantity
        is_available = available_quantity >= required_quantity

        return JsonResponse({
            'success': True,
            'available': is_available,
            'current_quantity': float(stock.quantity),
            'reserved_quantity': float(stock.reserved_quantity),
            'available_quantity': float(available_quantity),
            'required_quantity': float(required_quantity),
            'shortage': float(required_quantity - available_quantity) if not is_available else 0,
            'message': _('الكمية متوفرة') if is_available else _('الكمية غير كافية')
        })

    except Exception as e:
        logger.error(f"Error in ajax_check_availability: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_item_search(request):
    """البحث عن المواد - Autocomplete"""
    try:
        search_term = request.GET.get('q', '').strip()
        warehouse_id = request.GET.get('warehouse_id')
        only_in_stock = request.GET.get('only_in_stock', 'false').lower() == 'true'
        limit = int(request.GET.get('limit', 20))

        if len(search_term) < 2:
            return JsonResponse({
                'success': True,
                'items': [],
                'message': _('الرجاء إدخال حرفين على الأقل')
            })

        # البحث عن المواد
        items_query = Item.objects.filter(
            company=request.current_company,
            is_active=True
        ).filter(
            Q(name__icontains=search_term) |
            Q(name_en__icontains=search_term) |
            Q(code__icontains=search_term) |
            Q(barcode__icontains=search_term)
        )

        # تصفية المواد المتوفرة في المخزون
        if only_in_stock and warehouse_id:
            items_with_stock = ItemStock.objects.filter(
                company=request.current_company,
                warehouse_id=warehouse_id,
                quantity__gt=0
            ).values_list('item_id', flat=True)
            items_query = items_query.filter(id__in=items_with_stock)

        items_query = items_query[:limit]

        items_data = []
        for item in items_query:
            item_dict = {
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'barcode': item.barcode,
                'category': item.category.name if item.category else None,
            }

            # إضافة معلومات الرصيد إذا تم تحديد مستودع
            if warehouse_id:
                stock = ItemStock.objects.filter(
                    item=item,
                    warehouse_id=warehouse_id,
                    company=request.current_company
                ).first()

                if stock:
                    item_dict['stock'] = {
                        'quantity': float(stock.quantity),
                        'available': float(stock.quantity - stock.reserved_quantity),
                        'cost': float(stock.average_cost)
                    }
                else:
                    item_dict['stock'] = None

            items_data.append(item_dict)

        return JsonResponse({
            'success': True,
            'items': items_data,
            'count': len(items_data)
        })

    except Exception as e:
        logger.error(f"Error in ajax_item_search: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

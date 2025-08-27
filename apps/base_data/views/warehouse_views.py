# apps/base_data/views/warehouse_views.py
"""
Views المستودعات ووحدات القياس + تحويلات المخزون
CRUD كامل + Bootstrap 5 + RTL + DataTables server-side
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.db.models import Q, Count, Sum, F, Avg
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from decimal import Decimal

from ..models import Warehouse, WarehouseItem, UnitOfMeasure, Item
from ..forms import (
    WarehouseForm, UnitOfMeasureForm, WarehouseFilterForm, WarehouseItemForm,
    WarehouseTransferForm, WarehouseQuickAddForm, UnitQuickAddForm,
    InventoryAdjustmentForm, StockReportForm
)
from core.mixins import CompanyMixin, AjaxResponseMixin
from core.utils import generate_code


class WarehouseListView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض قائمة المستودعات"""
    model = Warehouse
    template_name = 'base_data/warehouses/list.html'
    context_object_name = 'warehouses'
    paginate_by = 25

    def get_queryset(self):
        queryset = Warehouse.objects.filter(
            company=self.request.user.company
        ).select_related('branch', 'keeper')

        # تطبيق الفلاتر
        self.filter_form = WarehouseFilterForm(
            data=self.request.GET or None,
            company=self.request.user.company,
            user=self.request.user
        )

        if self.filter_form.is_valid():
            queryset = self.filter_form.get_queryset(queryset)

        return queryset.order_by('warehouse_type', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        stats = Warehouse.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            main_warehouses=Count('id', filter=Q(warehouse_type='main')),
            branch_warehouses=Count('id', filter=Q(warehouse_type='branch')),
        )

        context.update({
            'filter_form': self.filter_form,
            'page_title': _('المستودعات'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('المستودعات'), 'active': True}
            ],
            'stats': stats,
            'can_add': self.request.user.has_perm('base_data.add_warehouse'),
            'can_change': self.request.user.has_perm('base_data.change_warehouse'),
            'can_delete': self.request.user.has_perm('base_data.delete_warehouse'),
        })
        return context


class WarehouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء مستودع جديد"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouses/form.html'
    permission_required = 'base_data.add_warehouse'
    success_url = reverse_lazy('base_data:warehouse_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('إضافة مستودع جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ المستودع'),
            'cancel_url': reverse('base_data:warehouse_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            form.instance.code = generate_code('WH', self.request.user.company)

        self.object = form.save()
        messages.success(
            self.request,
            _('تم إنشاء المستودع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('base_data:warehouse_detail', kwargs={'pk': self.object.pk})


class WarehouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل مستودع"""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'base_data/warehouses/form.html'
    permission_required = 'base_data.change_warehouse'
    context_object_name = 'warehouse'

    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تعديل المستودع: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
                {'title': self.object.name, 'active': True}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('base_data:warehouse_detail', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:warehouse_delete', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تحديث المستودع "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return redirect('base_data:warehouse_detail', pk=self.object.pk)


class WarehouseDetailView(LoginRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل المستودع"""
    model = Warehouse
    template_name = 'base_data/warehouses/detail.html'
    context_object_name = 'warehouse'

    def get_queryset(self):
        return Warehouse.objects.filter(
            company=self.request.user.company
        ).select_related('branch', 'keeper', 'created_by', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المستودع
        warehouse_items = WarehouseItem.objects.filter(
            warehouse=self.object
        ).select_related('item')

        stats = warehouse_items.aggregate(
            total_items=Count('item'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('average_cost')),
            avg_cost=Avg('average_cost')
        )

        # أعلى 10 أصناف حسب الكمية
        top_items = warehouse_items.order_by('-quantity')[:10]

        context.update({
            'page_title': self.object.name,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
                {'title': self.object.name, 'active': True}
            ],
            'stats': stats,
            'top_items': top_items,
            'can_change': self.request.user.has_perm('base_data.change_warehouse'),
            'can_delete': self.request.user.has_perm('base_data.delete_warehouse'),
            'edit_url': reverse('base_data:warehouse_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:warehouse_delete', kwargs={'pk': self.object.pk}),
            'inventory_url': reverse('base_data:warehouse_inventory', kwargs={'pk': self.object.pk}),
        })
        return context


class WarehouseInventoryView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض مخزون المستودع"""
    model = WarehouseItem
    template_name = 'base_data/warehouses/inventory.html'
    context_object_name = 'warehouse_items'
    paginate_by = 50

    def get_queryset(self):
        self.warehouse = get_object_or_404(
            Warehouse,
            pk=self.kwargs['pk'],
            company=self.request.user.company
        )

        queryset = WarehouseItem.objects.filter(
            warehouse=self.warehouse
        ).select_related('item', 'item__category', 'item__unit')

        # فلترة
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(item__code__icontains=search) |
                Q(item__name__icontains=search) |
                Q(item__barcode__icontains=search)
            )

        # عرض الأصناف بكمية فقط
        show_zero = self.request.GET.get('show_zero', '') == '1'
        if not show_zero:
            queryset = queryset.filter(quantity__gt=0)

        return queryset.order_by('-quantity', 'item__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إجمالي القيم
        totals = self.get_queryset().aggregate(
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('average_cost'))
        )

        context.update({
            'warehouse': self.warehouse,
            'page_title': _('مخزون المستودع: %(name)s') % {'name': self.warehouse.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
                {'title': self.warehouse.name,
                 'url': reverse('base_data:warehouse_detail', kwargs={'pk': self.warehouse.pk})},
                {'title': _('المخزون'), 'active': True}
            ],
            'totals': totals,
            'search': self.request.GET.get('search', ''),
            'show_zero': self.request.GET.get('show_zero', '') == '1',
        })
        return context


class WarehouseTransferView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """تحويل بين المستودعات"""
    model = None  # سيكون جدول التحويلات لاحقاً
    form_class = WarehouseTransferForm
    template_name = 'base_data/warehouses/transfer.html'
    permission_required = 'base_data.change_warehouse'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تحويل بين المستودعات'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('المستودعات'), 'url': reverse('base_data:warehouse_list')},
                {'title': _('التحويلات'), 'active': True}
            ],
            'submit_text': _('تنفيذ التحويل'),
            'cancel_url': reverse('base_data:warehouse_list'),
        })
        return context

    def form_valid(self, form):
        # تنفيذ التحويل
        from_warehouse = form.cleaned_data['from_warehouse']
        to_warehouse = form.cleaned_data['to_warehouse']
        item = form.cleaned_data['item']
        quantity = form.cleaned_data['quantity']
        notes = form.cleaned_data.get('notes', '')

        with transaction.atomic():
            # خصم من المستودع المصدر
            from_warehouse_item, _ = WarehouseItem.objects.get_or_create(
                warehouse=from_warehouse,
                item=item,
                defaults={'quantity': 0, 'average_cost': 0}
            )
            from_warehouse_item.quantity -= quantity
            from_warehouse_item.save()

            # إضافة للمستودع المستقبل
            to_warehouse_item, _ = WarehouseItem.objects.get_or_create(
                warehouse=to_warehouse,
                item=item,
                defaults={'quantity': 0, 'average_cost': from_warehouse_item.average_cost}
            )

            # حساب متوسط التكلفة الجديد
            if to_warehouse_item.quantity > 0:
                total_cost = (to_warehouse_item.quantity * to_warehouse_item.average_cost) + \
                             (quantity * from_warehouse_item.average_cost)
                total_quantity = to_warehouse_item.quantity + quantity
                to_warehouse_item.average_cost = total_cost / total_quantity
            else:
                to_warehouse_item.average_cost = from_warehouse_item.average_cost

            to_warehouse_item.quantity += quantity
            to_warehouse_item.save()

            # تسجيل سند التحويل (يمكن إضافة جدول منفصل للتحويلات)

        messages.success(
            self.request,
            _('تم تحويل %(quantity)s %(unit)s من %(item)s من %(from_warehouse)s إلى %(to_warehouse)s') % {
                'quantity': quantity,
                'unit': item.unit.name,
                'item': item.name,
                'from_warehouse': from_warehouse.name,
                'to_warehouse': to_warehouse.name
            }
        )
        return redirect('base_data:warehouse_list')


# Views وحدات القياس
class UnitOfMeasureListView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض قائمة وحدات القياس"""
    model = UnitOfMeasure
    template_name = 'base_data/units/list.html'
    context_object_name = 'units'
    paginate_by = 50

    def get_queryset(self):
        queryset = UnitOfMeasure.objects.filter(
            company=self.request.user.company
        )

        # بحث
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_en__icontains=search)
            )

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = UnitOfMeasure.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True))
        )

        context.update({
            'page_title': _('وحدات القياس'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('وحدات القياس'), 'active': True}
            ],
            'stats': stats,
            'search': self.request.GET.get('search', ''),
            'can_add': self.request.user.has_perm('base_data.add_unitofmeasure'),
            'can_change': self.request.user.has_perm('base_data.change_unitofmeasure'),
            'can_delete': self.request.user.has_perm('base_data.delete_unitofmeasure'),
        })
        return context


class UnitOfMeasureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء وحدة قياس جديدة"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'base_data/units/form.html'
    permission_required = 'base_data.add_unitofmeasure'
    success_url = reverse_lazy('base_data:unit_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('إضافة وحدة قياس جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('base_data:unit_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ الوحدة'),
            'cancel_url': reverse('base_data:unit_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            form.instance.code = generate_code('UNIT', self.request.user.company)

        self.object = form.save()
        messages.success(
            self.request,
            _('تم إنشاء وحدة القياس "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return super().form_valid(form)


class UnitOfMeasureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل وحدة قياس"""
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'base_data/units/form.html'
    permission_required = 'base_data.change_unitofmeasure'
    success_url = reverse_lazy('base_data:unit_list')
    context_object_name = 'unit'

    def get_queryset(self):
        return UnitOfMeasure.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تعديل وحدة القياس: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('وحدات القياس'), 'url': reverse('base_data:unit_list')},
                {'title': self.object.name, 'active': True}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('base_data:unit_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تحديث وحدة القياس "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return super().form_valid(form)


# AJAX Views
class WarehouseSelectView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """بحث المستودعات للـ Select2"""

    def get(self, request):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        page_size = 20

        queryset = Warehouse.objects.filter(
            company=request.user.company,
            is_active=True
        ).select_related('branch')

        if term:
            queryset = queryset.filter(
                Q(code__icontains=term) |
                Q(name__icontains=term) |
                Q(location__icontains=term)
            )

        total_count = queryset.count()
        start = (page - 1) * page_size
        warehouses = queryset[start:start + page_size]

        results = []
        for warehouse in warehouses:
            branch_name = warehouse.branch.name if warehouse.branch else _('الرئيسي')
            results.append({
                'id': warehouse.pk,
                'text': f"{warehouse.code} - {warehouse.name} ({branch_name})",
                'warehouse_type': warehouse.get_warehouse_type_display(),
                'location': warehouse.location or '',
                'keeper': warehouse.keeper.get_full_name() if warehouse.keeper else '',
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': start + page_size < total_count
            }
        })


class UnitSelectView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """بحث وحدات القياس للـ Select2"""

    def get(self, request):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        page_size = 20

        queryset = UnitOfMeasure.objects.filter(
            company=request.user.company,
            is_active=True
        )

        if term:
            queryset = queryset.filter(
                Q(code__icontains=term) |
                Q(name__icontains=term) |
                Q(name_en__icontains=term)
            )

        total_count = queryset.count()
        start = (page - 1) * page_size
        units = queryset[start:start + page_size]

        results = []
        for unit in units:
            text = f"{unit.name}"
            if unit.code:
                text = f"{unit.code} - {text}"
            if unit.name_en:
                text = f"{text} ({unit.name_en})"

            results.append({
                'id': unit.pk,
                'text': text,
                'code': unit.code or '',
                'name': unit.name,
                'name_en': unit.name_en or '',
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': start + page_size < total_count
            }
        })
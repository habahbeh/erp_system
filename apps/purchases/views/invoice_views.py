# apps/purchases/views/invoice_views.py
"""
Views for Purchase Invoices
Complete CRUD operations + Posting functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from decimal import Decimal
from datetime import datetime, date
import json

from ..models import PurchaseInvoice, PurchaseInvoiceItem
from ..forms import (
    PurchaseInvoiceForm,
    PurchaseInvoiceItemForm,
    PurchaseInvoiceItemFormSet,
)
from apps.core.models import BusinessPartner, Item


class PurchaseInvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """قائمة فواتير المشتريات"""
    model = PurchaseInvoice
    template_name = 'purchases/invoices/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 50
    permission_required = 'purchases.view_purchaseinvoice'

    def get_queryset(self):
        queryset = PurchaseInvoice.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'warehouse', 'currency', 'payment_method', 'branch'
        ).prefetch_related('lines').order_by('-date', '-number')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(receipt_number__icontains=search) |
                Q(supplier_invoice_number__icontains=search)
            )

        # فلترة حسب المورد
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        # فلترة حسب المستودع
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        # فلترة حسب الحالة
        is_posted = self.request.GET.get('is_posted')
        if is_posted == '1':
            queryset = queryset.filter(is_posted=True)
        elif is_posted == '0':
            queryset = queryset.filter(is_posted=False)

        # فلترة حسب نوع الفاتورة
        invoice_type = self.request.GET.get('invoice_type')
        if invoice_type:
            queryset = queryset.filter(invoice_type=invoice_type)

        # فلترة حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['title'] = _('فواتير المشتريات')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('فواتير المشتريات'), 'url': ''},
        ]

        # الإحصائيات
        invoices = self.get_queryset()
        context['stats'] = {
            'total_count': invoices.count(),
            'posted_count': invoices.filter(is_posted=True).count(),
            'draft_count': invoices.filter(is_posted=False).count(),
            'purchase_count': invoices.filter(invoice_type='purchase').count(),
            'return_count': invoices.filter(invoice_type='return').count(),
            'total_amount': invoices.aggregate(
                total=Sum('total_with_tax')
            )['total'] or Decimal('0.000'),
        }

        # قائمة الموردين للفلترة
        context['suppliers'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both'],
            is_active=True
        ).order_by('name')

        # الصلاحيات
        context['can_add'] = self.request.user.has_perm('purchases.add_purchaseinvoice')
        context['can_edit'] = self.request.user.has_perm('purchases.change_purchaseinvoice')
        context['can_delete'] = self.request.user.has_perm('purchases.delete_purchaseinvoice')
        context['can_post'] = self.request.user.has_perm('purchases.add_purchaseinvoice')

        return context


class PurchaseInvoiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل فاتورة المشتريات"""
    model = PurchaseInvoice
    template_name = 'purchases/invoices/invoice_detail.html'
    context_object_name = 'invoice'
    permission_required = 'purchases.view_purchaseinvoice'

    def get_queryset(self):
        return PurchaseInvoice.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'warehouse', 'currency', 'payment_method',
            'branch', 'journal_entry', 'discount_account', 'supplier_account'
        ).prefetch_related('lines__item', 'lines__unit')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        invoice = self.object
        context['title'] = f'{_("فاتورة مشتريات")} {invoice.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('فواتير المشتريات'), 'url': reverse('purchases:invoice_list')},
            {'title': invoice.number, 'url': ''},
        ]

        # الصلاحيات
        context['can_edit'] = (
            self.request.user.has_perm('purchases.change_purchaseinvoice') and
            not invoice.is_posted
        )
        context['can_delete'] = (
            self.request.user.has_perm('purchases.delete_purchaseinvoice') and
            not invoice.is_posted
        )
        context['can_post'] = (
            self.request.user.has_perm('purchases.add_purchaseinvoice') and
            not invoice.is_posted
        )
        context['can_unpost'] = (
            self.request.user.has_perm('purchases.change_purchaseinvoice') and
            invoice.is_posted
        )

        return context


class PurchaseInvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء فاتورة مشتريات جديدة"""
    model = PurchaseInvoice
    form_class = PurchaseInvoiceForm
    template_name = 'purchases/invoices/invoice_form.html'
    permission_required = 'purchases.add_purchaseinvoice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['title'] = _('إضافة فاتورة مشتريات')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('فواتير المشتريات'), 'url': reverse('purchases:invoice_list')},
            {'title': _('إضافة فاتورة'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseInvoiceItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseInvoiceItemFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        # بيانات للجافاسكربت
        context['items_data'] = list(
            Item.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).values(
                'id', 'name', 'code', 'barcode',
                'tax_rate', 'unit_of_measure__name',
                'unit_of_measure__code'
            )
        )

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # ربط الفاتورة بالشركة والفرع
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # حساب المجاميع
            self.object.calculate_totals()
            self.object.save()

            messages.success(
                self.request,
                _('تم إضافة فاتورة المشتريات بنجاح')
            )
            return redirect('purchases:invoice_detail', pk=self.object.pk)
        else:
            # عرض أخطاء الـ formset بوضوح
            error_messages = []

            # أخطاء النموذج الرئيسي
            if form.errors:
                error_messages.append(f"أخطاء النموذج الرئيسي: {form.errors.as_text()}")

            # أخطاء الـ formset
            if formset.non_form_errors():
                error_messages.append(f"أخطاء عامة: {formset.non_form_errors()}")

            # أخطاء كل صف
            for i, form_item in enumerate(formset):
                if form_item.errors:
                    error_messages.append(f"الصف {i+1}: {form_item.errors.as_text()}")

            # عرض جميع الأخطاء
            for msg in error_messages:
                messages.error(self.request, msg)

            if not error_messages:
                messages.error(
                    self.request,
                    _('يرجى تصحيح الأخطاء في النموذج')
                )

            return self.render_to_response(self.get_context_data(form=form))


class PurchaseInvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل فاتورة مشتريات"""
    model = PurchaseInvoice
    form_class = PurchaseInvoiceForm
    template_name = 'purchases/invoices/invoice_form.html'
    permission_required = 'purchases.change_purchaseinvoice'

    def get_queryset(self):
        return PurchaseInvoice.objects.filter(
            company=self.request.current_company,
            is_posted=False  # لا يمكن تعديل فاتورة مرحلة
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        invoice = self.object
        context['title'] = f'{_("تعديل فاتورة")} {invoice.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('فواتير المشتريات'), 'url': reverse('purchases:invoice_list')},
            {'title': invoice.number, 'url': reverse('purchases:invoice_detail', kwargs={'pk': invoice.pk})},
            {'title': _('تعديل'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseInvoiceItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseInvoiceItemFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        # بيانات للجافاسكربت
        context['items_data'] = list(
            Item.objects.filter(
                company=self.request.current_company,
                is_active=True
            ).values(
                'id', 'name', 'code', 'barcode',
                'tax_rate', 'unit_of_measure__name',
                'unit_of_measure__code'
            )
        )

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # إعادة حساب المجاميع
            self.object.calculate_totals()
            self.object.save()

            messages.success(
                self.request,
                _('تم تعديل فاتورة المشتريات بنجاح')
            )
            return redirect('purchases:invoice_detail', pk=self.object.pk)
        else:
            messages.error(
                self.request,
                _('يرجى تصحيح الأخطاء في النموذج')
            )
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseInvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف فاتورة مشتريات"""
    model = PurchaseInvoice
    template_name = 'purchases/invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('purchases:invoice_list')
    permission_required = 'purchases.delete_purchaseinvoice'

    def get_queryset(self):
        return PurchaseInvoice.objects.filter(
            company=self.request.current_company,
            is_posted=False  # لا يمكن حذف فاتورة مرحلة
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف فاتورة المشتريات بنجاح'))
        return super().delete(request, *args, **kwargs)


@login_required
@permission_required('purchases.add_purchaseinvoice', raise_exception=True)
@transaction.atomic
def post_invoice(request, pk):
    """ترحيل فاتورة المشتريات"""
    invoice = get_object_or_404(
        PurchaseInvoice,
        pk=pk,
        company=request.current_company
    )

    if invoice.is_posted:
        messages.error(request, _('الفاتورة مرحلة مسبقاً'))
        return redirect('purchases:invoice_detail', pk=pk)

    try:
        invoice.post(user=request.user)
        messages.success(
            request,
            _('تم ترحيل الفاتورة وإنشاء سند الإدخال والقيد المحاسبي بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الترحيل")}: {str(e)}')

    return redirect('purchases:invoice_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaseinvoice', raise_exception=True)
@transaction.atomic
def unpost_invoice(request, pk):
    """إلغاء ترحيل فاتورة المشتريات"""
    invoice = get_object_or_404(
        PurchaseInvoice,
        pk=pk,
        company=request.current_company
    )

    if not invoice.is_posted:
        messages.error(request, _('الفاتورة غير مرحلة'))
        return redirect('purchases:invoice_detail', pk=pk)

    try:
        invoice.unpost()
        messages.success(
            request,
            _('تم إلغاء ترحيل الفاتورة وحذف سند الإدخال والقيد المحاسبي بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في إلغاء الترحيل")}: {str(e)}')

    return redirect('purchases:invoice_detail', pk=pk)


@login_required
@permission_required('purchases.view_purchaseinvoice', raise_exception=True)
def invoice_datatable_ajax(request):
    """AJAX endpoint for DataTables"""
    from django.urls import reverse

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر من الواجهة
    invoice_type = request.GET.get('invoice_type', '')
    posted = request.GET.get('posted', '')
    supplier_id = request.GET.get('supplier', '')
    warehouse_id = request.GET.get('warehouse', '')
    search_filter = request.GET.get('search_filter', '')

    queryset = PurchaseInvoice.objects.filter(
        company=request.current_company
    ).select_related('supplier', 'warehouse', 'currency')

    # تطبيق الفلاتر
    if invoice_type:
        queryset = queryset.filter(invoice_type=invoice_type)

    if posted == '1':
        queryset = queryset.filter(is_posted=True)
    elif posted == '0':
        queryset = queryset.filter(is_posted=False)

    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    if warehouse_id:
        queryset = queryset.filter(warehouse_id=warehouse_id)

    # البحث العام
    if search_filter:
        queryset = queryset.filter(
            Q(number__icontains=search_filter) |
            Q(supplier__name__icontains=search_filter) |
            Q(receipt_number__icontains=search_filter)
        )

    # البحث من DataTable
    if search_value:
        queryset = queryset.filter(
            Q(number__icontains=search_value) |
            Q(supplier__name__icontains=search_value) |
            Q(receipt_number__icontains=search_value)
        )

    # العدد الكلي
    total_records = queryset.count()

    # الترتيب
    queryset = queryset.order_by('-date', '-number')

    # Pagination
    if length > 0:
        queryset = queryset[start:start + length]

    # البيانات - يجب أن تكون array وليس dictionary
    data = []
    for invoice in queryset:
        # تحديد نوع الفاتورة
        invoice_type_display = 'شراء' if invoice.invoice_type == 'purchase' else 'مرتجع'

        # تحديد الحالة
        if invoice.is_posted:
            status_badge = '<span class="badge bg-success">مرحلة</span>'
        else:
            status_badge = '<span class="badge bg-warning text-dark">مسودة</span>'

        # أزرار الإجراءات
        actions = f'''
        <div class="btn-group" role="group">
            <a href="{reverse('purchases:invoice_detail', args=[invoice.pk])}"
               class="btn btn-sm btn-info"
               data-bs-toggle="tooltip"
               title="عرض">
                <i class="fas fa-eye"></i>
            </a>
        '''

        if not invoice.is_posted:
            actions += f'''
            <a href="{reverse('purchases:invoice_update', args=[invoice.pk])}"
               class="btn btn-sm btn-primary"
               data-bs-toggle="tooltip"
               title="تعديل">
                <i class="fas fa-edit"></i>
            </a>
            <button onclick="postInvoice({invoice.pk}, '{invoice.number}')"
                    class="btn btn-sm btn-success"
                    data-bs-toggle="tooltip"
                    title="ترحيل">
                <i class="fas fa-check"></i>
            </button>
            <button onclick="deleteInvoice({invoice.pk}, '{invoice.number}')"
                    class="btn btn-sm btn-danger"
                    data-bs-toggle="tooltip"
                    title="حذف">
                <i class="fas fa-trash"></i>
            </button>
            '''
        else:
            actions += f'''
            <button onclick="unpostInvoice({invoice.pk}, '{invoice.number}')"
                    class="btn btn-sm btn-warning"
                    data-bs-toggle="tooltip"
                    title="إلغاء الترحيل">
                <i class="fas fa-undo"></i>
            </button>
            '''

        actions += '</div>'

        # إضافة البيانات كـ array وليس dictionary
        data.append([
            invoice.number or '-',  # 0: رقم الفاتورة
            invoice.date.strftime('%Y-%m-%d'),  # 1: التاريخ
            invoice.supplier.name if invoice.supplier else '-',  # 2: المورد
            invoice_type_display,  # 3: النوع
            invoice.warehouse.name if invoice.warehouse else '-',  # 4: المستودع
            f'{float(invoice.total_with_tax):,.3f}',  # 5: الإجمالي
            status_badge,  # 6: الحالة
            actions  # 7: الإجراءات
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


@login_required
@permission_required('purchases.view_purchaseinvoice', raise_exception=True)
def export_invoices_excel(request):
    """تصدير فواتير المشتريات إلى Excel"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from io import BytesIO

    # استرجاع البيانات
    queryset = PurchaseInvoice.objects.filter(
        company=request.current_company
    ).select_related(
        'supplier', 'warehouse', 'currency'
    ).order_by('-date', '-number')

    # تطبيق الفلاتر من GET parameters
    supplier_id = request.GET.get('supplier')
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    is_posted = request.GET.get('is_posted')
    if is_posted == '1':
        queryset = queryset.filter(is_posted=True)
    elif is_posted == '0':
        queryset = queryset.filter(is_posted=False)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)

    # إنشاء ملف Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "فواتير المشتريات"

    # الأنماط
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # العناوين
    headers = [
        'رقم الفاتورة', 'التاريخ', 'المورد', 'المستودع',
        'رقم الإيصال', 'الإجمالي', 'الضريبة', 'الإجمالي مع الضريبة',
        'العملة', 'الحالة'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # البيانات
    for row_num, invoice in enumerate(queryset, 2):
        ws.cell(row=row_num, column=1, value=invoice.number).border = border
        ws.cell(row=row_num, column=2, value=invoice.date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row_num, column=3, value=invoice.supplier.name).border = border
        ws.cell(row=row_num, column=4, value=invoice.warehouse.name).border = border
        ws.cell(row=row_num, column=5, value=invoice.receipt_number).border = border
        ws.cell(row=row_num, column=6, value=float(invoice.total_amount)).border = border
        ws.cell(row=row_num, column=7, value=float(invoice.tax_amount)).border = border
        ws.cell(row=row_num, column=8, value=float(invoice.total_with_tax)).border = border
        ws.cell(row=row_num, column=9, value=invoice.currency.code).border = border
        ws.cell(row=row_num, column=10, value='مرحل' if invoice.is_posted else 'مسودة').border = border

    # ضبط عرض الأعمدة
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 18
    ws.column_dimensions['I'].width = 10
    ws.column_dimensions['J'].width = 12

    # حفظ الملف
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # إرجاع الملف
    filename = f"purchase_invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

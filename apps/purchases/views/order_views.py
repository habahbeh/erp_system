# apps/purchases/views/order_views.py
"""
Views for Purchase Orders
Complete CRUD operations + Approval Workflow + Convert to Invoice
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
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from datetime import datetime, date

from ..models import PurchaseOrder, PurchaseOrderItem, PurchaseRequest
from ..forms import (
    PurchaseOrderForm,
    PurchaseOrderItemForm,
    PurchaseOrderItemFormSet,
    PurchaseOrderFilterForm,
)
from apps.core.models import BusinessPartner, Item


class PurchaseOrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """قائمة أوامر الشراء"""
    model = PurchaseOrder
    template_name = 'purchases/orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 50
    permission_required = 'purchases.view_purchaseorder'

    def get_queryset(self):
        queryset = PurchaseOrder.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'warehouse', 'currency', 'purchase_request',
            'requested_by', 'approved_by', 'created_by'
        ).prefetch_related('lines').order_by('-date', '-number')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(purchase_request__number__icontains=search)
            )

        # فلترة حسب المورد
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

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

        context['title'] = _('أوامر الشراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('أوامر الشراء'), 'url': ''},
        ]

        # الإحصائيات
        orders = self.get_queryset()
        context['stats'] = {
            'total_count': orders.count(),
            'draft_count': orders.filter(status='draft').count(),
            'pending_count': orders.filter(status='pending_approval').count(),
            'approved_count': orders.filter(status='approved').count(),
            'sent_count': orders.filter(status='sent').count(),
            'completed_count': orders.filter(status='completed').count(),
            'total_amount': orders.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.000'),
        }

        # قائمة الموردين للفلترة
        context['suppliers'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['supplier', 'both'],
            is_active=True
        ).order_by('name')

        # Filter form
        context['filter_form'] = PurchaseOrderFilterForm(
            self.request.GET,
            company=self.request.current_company
        )

        # الصلاحيات
        context['can_add'] = self.request.user.has_perm('purchases.add_purchaseorder')
        context['can_edit'] = self.request.user.has_perm('purchases.change_purchaseorder')
        context['can_delete'] = self.request.user.has_perm('purchases.delete_purchaseorder')
        context['can_approve'] = self.request.user.has_perm('purchases.change_purchaseorder')

        return context


class PurchaseOrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل أمر الشراء"""
    model = PurchaseOrder
    template_name = 'purchases/orders/order_detail.html'
    context_object_name = 'order'
    permission_required = 'purchases.view_purchaseorder'

    def get_queryset(self):
        return PurchaseOrder.objects.filter(
            company=self.request.current_company
        ).select_related(
            'supplier', 'warehouse', 'currency', 'purchase_request',
            'requested_by', 'approved_by', 'created_by'
        ).prefetch_related('lines__item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = self.object
        context['title'] = f'{_("أمر شراء")} {order.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('أوامر الشراء'), 'url': reverse('purchases:order_list')},
            {'title': order.number, 'url': ''},
        ]

        # الصلاحيات
        context['can_edit'] = (
            self.request.user.has_perm('purchases.change_purchaseorder') and
            order.status in ['draft', 'rejected']
        )
        context['can_delete'] = (
            self.request.user.has_perm('purchases.delete_purchaseorder') and
            order.status == 'draft'
        )
        context['can_approve'] = (
            self.request.user.has_perm('purchases.change_purchaseorder') and
            order.status == 'pending_approval'
        )
        context['can_reject'] = (
            self.request.user.has_perm('purchases.change_purchaseorder') and
            order.status == 'pending_approval'
        )
        context['can_send'] = (
            self.request.user.has_perm('purchases.change_purchaseorder') and
            order.status == 'approved'
        )
        context['can_convert'] = (
            self.request.user.has_perm('purchases.add_purchaseinvoice') and
            order.status in ['sent', 'approved', 'partial'] and
            not order.is_invoiced
        )

        return context


class PurchaseOrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء أمر شراء جديد"""
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/orders/order_form.html'
    permission_required = 'purchases.add_purchaseorder'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة أمر شراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('أوامر الشراء'), 'url': reverse('purchases:order_list')},
            {'title': _('إضافة أمر'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseOrderItemFormSet(
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

        # إذا كان من طلب شراء
        request_id = self.request.GET.get('from_request')
        if request_id:
            try:
                purchase_request = PurchaseRequest.objects.get(
                    pk=request_id,
                    company=self.request.current_company
                )
                context['purchase_request'] = purchase_request
            except PurchaseRequest.DoesNotExist:
                pass

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # ربط الأمر بالشركة
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # حساب المجاميع
            self.object.calculate_total()
            self.object.save()

            messages.success(
                self.request,
                _('تم إضافة أمر الشراء بنجاح')
            )
            return redirect('purchases:order_detail', pk=self.object.pk)
        else:
            messages.error(
                self.request,
                _('يرجى تصحيح الأخطاء في النموذج')
            )
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseOrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل أمر شراء"""
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/orders/order_form.html'
    permission_required = 'purchases.change_purchaseorder'

    def get_queryset(self):
        # يمكن تعديل الأمر في حالة مسودة أو مرفوض فقط
        return PurchaseOrder.objects.filter(
            company=self.request.current_company,
            status__in=['draft', 'rejected']
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = self.object
        context['title'] = f'{_("تعديل أمر")} {order.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('أوامر الشراء'), 'url': reverse('purchases:order_list')},
            {'title': order.number, 'url': reverse('purchases:order_detail', kwargs={'pk': order.pk})},
            {'title': _('تعديل'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseOrderItemFormSet(
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
            self.object.calculate_total()
            self.object.save()

            messages.success(
                self.request,
                _('تم تعديل أمر الشراء بنجاح')
            )
            return redirect('purchases:order_detail', pk=self.object.pk)
        else:
            messages.error(
                self.request,
                _('يرجى تصحيح الأخطاء في النموذج')
            )
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseOrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف أمر شراء"""
    model = PurchaseOrder
    template_name = 'purchases/orders/order_confirm_delete.html'
    success_url = reverse_lazy('purchases:order_list')
    permission_required = 'purchases.delete_purchaseorder'

    def get_queryset(self):
        # يمكن حذف الأمر في حالة مسودة فقط
        return PurchaseOrder.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف أمر الشراء بنجاح'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Workflow Actions
# ============================================================================

@login_required
@permission_required('purchases.change_purchaseorder', raise_exception=True)
@transaction.atomic
def submit_for_approval(request, pk):
    """إرسال أمر الشراء للاعتماد"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status != 'draft':
        messages.error(request, _('يمكن إرسال الأمر للاعتماد في حالة مسودة فقط'))
        return redirect('purchases:order_detail', pk=pk)

    try:
        order.submit_for_approval()
        messages.success(
            request,
            _('تم إرسال أمر الشراء للاعتماد بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الإرسال")}: {str(e)}')

    return redirect('purchases:order_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaseorder', raise_exception=True)
@transaction.atomic
def approve_order(request, pk):
    """اعتماد أمر الشراء"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status != 'pending_approval':
        messages.error(request, _('يمكن اعتماد الأمر في حالة بانتظار الموافقة فقط'))
        return redirect('purchases:order_detail', pk=pk)

    try:
        order.approve(user=request.user)
        messages.success(
            request,
            _('تم اعتماد أمر الشراء بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الاعتماد")}: {str(e)}')

    return redirect('purchases:order_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaseorder', raise_exception=True)
@transaction.atomic
def reject_order(request, pk):
    """رفض أمر الشراء"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status != 'pending_approval':
        messages.error(request, _('يمكن رفض الأمر في حالة بانتظار الموافقة فقط'))
        return redirect('purchases:order_detail', pk=pk)

    # الحصول على سبب الرفض
    rejection_reason = request.POST.get('rejection_reason', '')

    try:
        order.reject(user=request.user, reason=rejection_reason)
        messages.success(
            request,
            _('تم رفض أمر الشراء')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الرفض")}: {str(e)}')

    return redirect('purchases:order_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaseorder', raise_exception=True)
@transaction.atomic
def send_to_supplier(request, pk):
    """إرسال أمر الشراء للمورد"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status not in ['approved', 'sent']:
        messages.error(request, _('يجب أن يكون الأمر معتمد لإرساله للمورد'))
        return redirect('purchases:order_detail', pk=pk)

    try:
        order.send_to_supplier()
        messages.success(
            request,
            _('تم تعليم الأمر كمرسل للمورد بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الإرسال")}: {str(e)}')

    return redirect('purchases:order_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaseorder', raise_exception=True)
@transaction.atomic
def cancel_order(request, pk):
    """إلغاء أمر الشراء"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status in ['completed', 'cancelled']:
        messages.error(request, _('لا يمكن إلغاء أمر مكتمل أو ملغي'))
        return redirect('purchases:order_detail', pk=pk)

    try:
        order.cancel()
        messages.success(
            request,
            _('تم إلغاء أمر الشراء بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الإلغاء")}: {str(e)}')

    return redirect('purchases:order_detail', pk=pk)


@login_required
@permission_required('purchases.add_purchaseinvoice', raise_exception=True)
@transaction.atomic
def convert_to_invoice(request, pk):
    """تحويل أمر الشراء إلى فاتورة"""
    order = get_object_or_404(
        PurchaseOrder,
        pk=pk,
        company=request.current_company
    )

    if order.status not in ['sent', 'approved', 'partial']:
        messages.error(
            request,
            _('يجب أن يكون الأمر معتمد أو مرسل لتحويله إلى فاتورة')
        )
        return redirect('purchases:order_detail', pk=pk)

    try:
        invoice = order.convert_to_invoice(user=request.user)
        messages.success(
            request,
            _('تم تحويل أمر الشراء إلى فاتورة بنجاح')
        )
        return redirect('purchases:invoice_detail', pk=invoice.pk)
    except Exception as e:
        messages.error(request, f'{_("خطأ في التحويل")}: {str(e)}')
        return redirect('purchases:order_detail', pk=pk)


# ============================================================================
# AJAX & Export
# ============================================================================

@login_required
@permission_required('purchases.view_purchaseorder', raise_exception=True)
def order_datatable_ajax(request):
    """AJAX endpoint for DataTables"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = PurchaseOrder.objects.filter(
        company=request.current_company
    ).select_related('supplier', 'currency')

    # البحث
    if search_value:
        queryset = queryset.filter(
            Q(number__icontains=search_value) |
            Q(supplier__name__icontains=search_value)
        )

    # العدد الكلي
    total_records = queryset.count()

    # الترتيب
    queryset = queryset.order_by('-date', '-number')

    # Pagination
    queryset = queryset[start:start + length]

    # البيانات
    data = []
    for order in queryset:
        data.append({
            'number': order.number,
            'date': order.date.strftime('%Y-%m-%d'),
            'supplier': order.supplier.name,
            'total': float(order.total_amount),
            'status': order.get_status_display(),
            'status_code': order.status,
            'pk': order.pk,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


@login_required
@permission_required('purchases.view_purchaseorder', raise_exception=True)
def export_orders_excel(request):
    """تصدير أوامر الشراء إلى Excel"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from io import BytesIO

    # استرجاع البيانات
    queryset = PurchaseOrder.objects.filter(
        company=request.current_company
    ).select_related(
        'supplier', 'currency'
    ).order_by('-date', '-number')

    # تطبيق الفلاتر من GET parameters
    supplier_id = request.GET.get('supplier')
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)

    # إنشاء ملف Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "أوامر الشراء"

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
        'رقم الأمر', 'التاريخ', 'المورد', 'تاريخ التسليم المتوقع',
        'الإجمالي', 'الضريبة', 'الإجمالي مع الضريبة',
        'العملة', 'الحالة'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # البيانات
    for row_num, order in enumerate(queryset, 2):
        ws.cell(row=row_num, column=1, value=order.number).border = border
        ws.cell(row=row_num, column=2, value=order.date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row_num, column=3, value=order.supplier.name).border = border
        ws.cell(row=row_num, column=4, value=order.expected_delivery_date.strftime('%Y-%m-%d') if order.expected_delivery_date else '').border = border
        ws.cell(row=row_num, column=5, value=float(order.total_amount)).border = border
        ws.cell(row=row_num, column=6, value='').border = border  # Tax amount not stored in PurchaseOrder
        ws.cell(row=row_num, column=7, value=float(order.total_amount)).border = border
        ws.cell(row=row_num, column=8, value=order.currency.code).border = border
        ws.cell(row=row_num, column=9, value=order.get_status_display()).border = border

    # ضبط عرض الأعمدة
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 10
    ws.column_dimensions['I'].width = 15

    # حفظ الملف
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # إرجاع الملف
    filename = f"purchase_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

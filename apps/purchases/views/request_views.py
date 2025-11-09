# apps/purchases/views/request_views.py
"""
Views for Purchase Requests
Complete CRUD operations + Workflow (Submit, Approve, Reject)
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

from ..models import PurchaseRequest, PurchaseRequestItem
from ..forms import (
    PurchaseRequestForm,
    PurchaseRequestItemForm,
    PurchaseRequestItemFormSet,
    PurchaseRequestFilterForm,
)
from apps.core.models import Item, User


class PurchaseRequestListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """قائمة طلبات الشراء"""
    model = PurchaseRequest
    template_name = 'purchases/requests/request_list.html'
    context_object_name = 'requests'
    paginate_by = 50
    permission_required = 'purchases.view_purchaserequest'

    def get_queryset(self):
        queryset = PurchaseRequest.objects.filter(
            company=self.request.current_company
        ).select_related(
            'requested_by', 'created_by'
        ).prefetch_related('lines').order_by('-date', '-number')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(department__icontains=search) |
                Q(purpose__icontains=search) |
                Q(requested_by__first_name__icontains=search) |
                Q(requested_by__last_name__icontains=search)
            )

        # فلترة حسب الموظف الطالب
        requested_by_id = self.request.GET.get('requested_by')
        if requested_by_id:
            queryset = queryset.filter(requested_by_id=requested_by_id)

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

        context['title'] = _('طلبات الشراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('طلبات الشراء'), 'url': ''},
        ]

        # الإحصائيات
        requests = self.get_queryset()
        context['stats'] = {
            'total_count': requests.count(),
            'draft_count': requests.filter(status='draft').count(),
            'submitted_count': requests.filter(status='submitted').count(),
            'approved_count': requests.filter(status='approved').count(),
            'rejected_count': requests.filter(status='rejected').count(),
            'ordered_count': requests.filter(status='ordered').count(),
        }

        # قائمة المستخدمين النشطين للفلترة
        context['employees'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

        # Filter form
        context['filter_form'] = PurchaseRequestFilterForm(
            self.request.GET,
            company=self.request.current_company
        )

        # الصلاحيات
        context['can_add'] = self.request.user.has_perm('purchases.add_purchaserequest')
        context['can_edit'] = self.request.user.has_perm('purchases.change_purchaserequest')
        context['can_delete'] = self.request.user.has_perm('purchases.delete_purchaserequest')
        context['can_approve'] = self.request.user.has_perm('purchases.change_purchaserequest')

        return context


class PurchaseRequestDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تفاصيل طلب الشراء"""
    model = PurchaseRequest
    template_name = 'purchases/requests/request_detail.html'
    context_object_name = 'request_obj'
    permission_required = 'purchases.view_purchaserequest'

    def get_queryset(self):
        return PurchaseRequest.objects.filter(
            company=self.request.current_company
        ).select_related(
            'requested_by', 'created_by'
        ).prefetch_related('lines__item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request_obj = self.object
        context['title'] = f'{_("طلب شراء")} {request_obj.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('طلبات الشراء'), 'url': reverse('purchases:request_list')},
            {'title': request_obj.number, 'url': ''},
        ]

        # الصلاحيات
        context['can_edit'] = (
            self.request.user.has_perm('purchases.change_purchaserequest') and
            request_obj.status in ['draft', 'rejected']
        )
        context['can_delete'] = (
            self.request.user.has_perm('purchases.delete_purchaserequest') and
            request_obj.status == 'draft'
        )
        context['can_submit'] = (
            self.request.user.has_perm('purchases.change_purchaserequest') and
            request_obj.status == 'draft'
        )
        context['can_approve'] = (
            self.request.user.has_perm('purchases.change_purchaserequest') and
            request_obj.status == 'submitted'
        )
        context['can_reject'] = (
            self.request.user.has_perm('purchases.change_purchaserequest') and
            request_obj.status == 'submitted'
        )
        context['can_create_order'] = (
            self.request.user.has_perm('purchases.add_purchaseorder') and
            request_obj.status == 'approved'
        )

        # أوامر الشراء المرتبطة
        context['related_orders'] = request_obj.purchase_orders.all()

        return context


class PurchaseRequestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء طلب شراء جديد"""
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'purchases/requests/request_form.html'
    permission_required = 'purchases.add_purchaserequest'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('إضافة طلب شراء')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('طلبات الشراء'), 'url': reverse('purchases:request_list')},
            {'title': _('إضافة طلب'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseRequestItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseRequestItemFormSet(
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
                'unit_of_measure__name',
                'unit_of_measure__code'
            )
        )

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # ربط الطلب بالشركة
        form.instance.company = self.request.current_company
        form.instance.created_by = self.request.user

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                _('تم إضافة طلب الشراء بنجاح')
            )
            return redirect('purchases:request_detail', pk=self.object.pk)
        else:
            messages.error(
                self.request,
                _('يرجى تصحيح الأخطاء في النموذج')
            )
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseRequestUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل طلب شراء"""
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'purchases/requests/request_form.html'
    permission_required = 'purchases.change_purchaserequest'

    def get_queryset(self):
        # يمكن تعديل الطلب في حالة مسودة أو مرفوض فقط
        return PurchaseRequest.objects.filter(
            company=self.request.current_company,
            status__in=['draft', 'rejected']
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request_obj = self.object
        context['title'] = f'{_("تعديل طلب")} {request_obj.number}'
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المشتريات'), 'url': '#'},
            {'title': _('طلبات الشراء'), 'url': reverse('purchases:request_list')},
            {'title': request_obj.number, 'url': reverse('purchases:request_detail', kwargs={'pk': request_obj.pk})},
            {'title': _('تعديل'), 'url': ''},
        ]

        if self.request.POST:
            context['formset'] = PurchaseRequestItemFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['formset'] = PurchaseRequestItemFormSet(
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
                'unit_of_measure__name',
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

            messages.success(
                self.request,
                _('تم تعديل طلب الشراء بنجاح')
            )
            return redirect('purchases:request_detail', pk=self.object.pk)
        else:
            messages.error(
                self.request,
                _('يرجى تصحيح الأخطاء في النموذج')
            )
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseRequestDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف طلب شراء"""
    model = PurchaseRequest
    template_name = 'purchases/requests/request_confirm_delete.html'
    success_url = reverse_lazy('purchases:request_list')
    permission_required = 'purchases.delete_purchaserequest'

    def get_queryset(self):
        # يمكن حذف الطلب في حالة مسودة فقط
        return PurchaseRequest.objects.filter(
            company=self.request.current_company,
            status='draft'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف طلب الشراء بنجاح'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Workflow Actions
# ============================================================================

@login_required
@permission_required('purchases.change_purchaserequest', raise_exception=True)
@transaction.atomic
def submit_request(request, pk):
    """تقديم طلب الشراء"""
    request_obj = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        company=request.current_company
    )

    if request_obj.status != 'draft':
        messages.error(request, _('يمكن تقديم الطلب في حالة مسودة فقط'))
        return redirect('purchases:request_detail', pk=pk)

    try:
        request_obj.submit()
        messages.success(
            request,
            _('تم تقديم طلب الشراء بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في التقديم")}: {str(e)}')

    return redirect('purchases:request_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaserequest', raise_exception=True)
@transaction.atomic
def approve_request(request, pk):
    """اعتماد طلب الشراء"""
    request_obj = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        company=request.current_company
    )

    if request_obj.status != 'submitted':
        messages.error(request, _('يمكن اعتماد الطلب في حالة مقدم فقط'))
        return redirect('purchases:request_detail', pk=pk)

    try:
        request_obj.approve()
        messages.success(
            request,
            _('تم اعتماد طلب الشراء بنجاح')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الاعتماد")}: {str(e)}')

    return redirect('purchases:request_detail', pk=pk)


@login_required
@permission_required('purchases.change_purchaserequest', raise_exception=True)
@transaction.atomic
def reject_request(request, pk):
    """رفض طلب الشراء"""
    request_obj = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        company=request.current_company
    )

    if request_obj.status != 'submitted':
        messages.error(request, _('يمكن رفض الطلب في حالة مقدم فقط'))
        return redirect('purchases:request_detail', pk=pk)

    try:
        request_obj.reject()
        messages.success(
            request,
            _('تم رفض طلب الشراء')
        )
    except Exception as e:
        messages.error(request, f'{_("خطأ في الرفض")}: {str(e)}')

    return redirect('purchases:request_detail', pk=pk)


@login_required
@permission_required('purchases.add_purchaseorder', raise_exception=True)
def create_order_from_request(request, pk):
    """إنشاء أمر شراء من طلب الشراء"""
    request_obj = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        company=request.current_company
    )

    if request_obj.status != 'approved':
        messages.error(request, _('يجب اعتماد الطلب أولاً لإنشاء أمر شراء منه'))
        return redirect('purchases:request_detail', pk=pk)

    # إعادة توجيه إلى صفحة إنشاء أمر الشراء مع معرف الطلب
    return redirect(f"{reverse('purchases:order_create')}?from_request={pk}")


# ============================================================================
# AJAX & Export
# ============================================================================

@login_required
@permission_required('purchases.view_purchaserequest', raise_exception=True)
def request_datatable_ajax(request):
    """AJAX endpoint for DataTables"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = PurchaseRequest.objects.filter(
        company=request.current_company
    ).select_related('requested_by')

    # البحث
    if search_value:
        queryset = queryset.filter(
            Q(number__icontains=search_value) |
            Q(department__icontains=search_value) |
            Q(requested_by__first_name__icontains=search_value)
        )

    # العدد الكلي
    total_records = queryset.count()

    # الترتيب
    queryset = queryset.order_by('-date', '-number')

    # Pagination
    queryset = queryset[start:start + length]

    # البيانات
    data = []
    for req in queryset:
        data.append({
            'number': req.number,
            'date': req.date.strftime('%Y-%m-%d'),
            'requested_by': req.requested_by.get_full_name() if req.requested_by else '',
            'department': req.department or '',
            'status': req.get_status_display(),
            'status_code': req.status,
            'pk': req.pk,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


@login_required
@permission_required('purchases.view_purchaserequest', raise_exception=True)
def export_requests_excel(request):
    """تصدير طلبات الشراء إلى Excel"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from io import BytesIO

    # استرجاع البيانات
    queryset = PurchaseRequest.objects.filter(
        company=request.current_company
    ).select_related(
        'requested_by'
    ).order_by('-date', '-number')

    # تطبيق الفلاتر من GET parameters
    requested_by_id = request.GET.get('requested_by')
    if requested_by_id:
        queryset = queryset.filter(requested_by_id=requested_by_id)

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
    ws.title = "طلبات الشراء"

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
        'رقم الطلب', 'التاريخ', 'طلب بواسطة', 'القسم',
        'الغرض', 'التاريخ المطلوب', 'الحالة'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # البيانات
    for row_num, req in enumerate(queryset, 2):
        ws.cell(row=row_num, column=1, value=req.number).border = border
        ws.cell(row=row_num, column=2, value=req.date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row_num, column=3, value=req.requested_by.get_full_name() if req.requested_by else '').border = border
        ws.cell(row=row_num, column=4, value=req.department or '').border = border
        ws.cell(row=row_num, column=5, value=req.purpose or '').border = border
        ws.cell(row=row_num, column=6, value=req.required_date.strftime('%Y-%m-%d') if req.required_date else '').border = border
        ws.cell(row=row_num, column=7, value=req.get_status_display()).border = border

    # ضبط عرض الأعمدة
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 40
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 15

    # حفظ الملف
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # إرجاع الملف
    filename = f"purchase_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

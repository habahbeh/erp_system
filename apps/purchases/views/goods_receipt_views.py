# apps/purchases/views/goods_receipt_views.py
"""
Views for Goods Receipt (استلام البضاعة)
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ..models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder
from ..forms import GoodsReceiptForm, GoodsReceiptLineFormSet


class GoodsReceiptListView(LoginRequiredMixin, ListView):
    """قائمة محاضر استلام البضاعة"""
    model = GoodsReceipt
    template_name = 'purchases/goods_receipt/goods_receipt_list.html'
    context_object_name = 'goods_receipts'
    paginate_by = 50

    def get_queryset(self):
        queryset = GoodsReceipt.objects.filter(
            company=self.request.current_company
        ).select_related(
            'purchase_order', 'supplier', 'warehouse', 'received_by'
        ).order_by('-date', '-number')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('محاضر استلام البضاعة')
        return context


class GoodsReceiptDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل محضر استلام البضاعة"""
    model = GoodsReceipt
    template_name = 'purchases/goods_receipt/goods_receipt_detail.html'
    context_object_name = 'goods_receipt'

    def get_queryset(self):
        return GoodsReceipt.objects.filter(
            company=self.request.current_company
        ).select_related(
            'purchase_order', 'supplier', 'warehouse', 'received_by', 'invoice'
        ).prefetch_related('lines__item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تفاصيل محضر الاستلام')
        return context


class GoodsReceiptCreateView(LoginRequiredMixin, CreateView):
    """إنشاء محضر استلام جديد"""
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'purchases/goods_receipt/goods_receipt_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('محضر استلام جديد')

        if self.request.POST:
            context['lines'] = GoodsReceiptLineFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['lines'] = GoodsReceiptLineFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']

        with transaction.atomic():
            # حفظ الرأس
            self.object = form.save(commit=False)
            self.object.company = self.request.current_company
            self.object.branch = self.request.current_branch
            self.object.created_by = self.request.user
            self.object.save()

            # حفظ السطور
            if lines.is_valid():
                lines.instance = self.object
                lines.save()
            else:
                return self.form_invalid(form)

        messages.success(
            self.request,
            _('تم إنشاء محضر الاستلام %(number)s بنجاح') % {'number': self.object.number}
        )
        return redirect('purchases:goods_receipt_detail', pk=self.object.pk)


class GoodsReceiptUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل محضر استلام"""
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'purchases/goods_receipt/goods_receipt_form.html'

    def get_queryset(self):
        return GoodsReceipt.objects.filter(
            company=self.request.current_company,
            status='draft'  # يمكن تعديل المسودات فقط
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['branch'] = self.request.current_branch
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل محضر الاستلام')

        if self.request.POST:
            context['lines'] = GoodsReceiptLineFormSet(
                self.request.POST,
                instance=self.object,
                company=self.request.current_company
            )
        else:
            context['lines'] = GoodsReceiptLineFormSet(
                instance=self.object,
                company=self.request.current_company
            )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']

        with transaction.atomic():
            self.object = form.save()

            if lines.is_valid():
                lines.instance = self.object
                lines.save()
            else:
                return self.form_invalid(form)

        messages.success(self.request, _('تم تعديل محضر الاستلام بنجاح'))
        return redirect('purchases:goods_receipt_detail', pk=self.object.pk)


class GoodsReceiptDeleteView(LoginRequiredMixin, DeleteView):
    """حذف محضر استلام"""
    model = GoodsReceipt
    template_name = 'purchases/goods_receipt/goods_receipt_confirm_delete.html'
    success_url = reverse_lazy('purchases:goods_receipt_list')

    def get_queryset(self):
        return GoodsReceipt.objects.filter(
            company=self.request.current_company,
            status='draft',  # يمكن حذف المسودات فقط
            is_posted=False
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(
            request,
            _('تم حذف محضر الاستلام %(number)s بنجاح') % {'number': self.object.number}
        )
        return super().delete(request, *args, **kwargs)


@login_required
def confirm_goods_receipt(request, pk):
    """تأكيد محضر الاستلام"""
    goods_receipt = get_object_or_404(
        GoodsReceipt,
        pk=pk,
        company=request.current_company
    )

    try:
        goods_receipt.confirm(user=request.user)
        messages.success(
            request,
            _('تم تأكيد محضر الاستلام %(number)s') % {'number': goods_receipt.number}
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('purchases:goods_receipt_detail', pk=pk)


@login_required
def post_goods_receipt(request, pk):
    """ترحيل محضر الاستلام للمخزون"""
    goods_receipt = get_object_or_404(
        GoodsReceipt,
        pk=pk,
        company=request.current_company
    )

    try:
        stock_in = goods_receipt.post(user=request.user)
        messages.success(
            request,
            _('تم ترحيل محضر الاستلام %(number)s للمخزون') % {'number': goods_receipt.number}
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('purchases:goods_receipt_detail', pk=pk)


@login_required
def unpost_goods_receipt(request, pk):
    """إلغاء ترحيل محضر الاستلام"""
    goods_receipt = get_object_or_404(
        GoodsReceipt,
        pk=pk,
        company=request.current_company
    )

    try:
        goods_receipt.unpost()
        messages.success(
            request,
            _('تم إلغاء ترحيل محضر الاستلام %(number)s') % {'number': goods_receipt.number}
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('purchases:goods_receipt_detail', pk=pk)


@login_required
def goods_receipt_datatable_ajax(request):
    """AJAX endpoint for DataTables"""
    # TODO: Implement DataTables server-side processing
    return JsonResponse({'data': [], 'recordsTotal': 0, 'recordsFiltered': 0})


@login_required
def export_goods_receipts_excel(request):
    """تصدير محاضر الاستلام لملف Excel"""
    # TODO: Implement Excel export
    messages.info(request, _('ميزة التصدير قيد التطوير'))
    return redirect('purchases:goods_receipt_list')

# apps/sales/views/order_views.py
"""
Views لطلبات البيع
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.http import JsonResponse
from decimal import Decimal

from apps.sales.models import SalesOrder, SalesOrderItem, SalesInvoice, InvoiceItem
from apps.sales.forms import SalesOrderForm, SalesOrderItemFormSet


class SalesOrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة طلبات البيع"""
    model = SalesOrder
    template_name = 'sales/orders/order_list.html'
    context_object_name = 'orders'
    permission_required = 'sales.view_salesorder'
    paginate_by = 50

    def get_queryset(self):
        """الحصول على طلبات البيع للشركة الحالية"""
        queryset = SalesOrder.objects.filter(
            company=self.request.current_company
        ).select_related(
            'customer',
            'warehouse',
            'salesperson',
            'quotation',
            'created_by'
        ).prefetch_related('lines')

        # الفلاتر
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)

        is_approved = self.request.GET.get('is_approved')
        if is_approved:
            queryset = queryset.filter(is_approved=is_approved == 'true')

        is_delivered = self.request.GET.get('is_delivered')
        if is_delivered:
            queryset = queryset.filter(is_delivered=is_delivered == 'true')

        is_invoiced = self.request.GET.get('is_invoiced')
        if is_invoiced:
            queryset = queryset.filter(is_invoiced=is_invoiced == 'true')

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(number__icontains=search) |
                models.Q(customer__name__icontains=search) |
                models.Q(notes__icontains=search)
            )

        return queryset.order_by('-date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('طلبات البيع')

        # إحصائيات
        orders = self.get_queryset()
        context['total_orders'] = orders.count()
        context['approved_orders'] = orders.filter(is_approved=True).count()
        context['pending_orders'] = orders.filter(is_approved=False).count()
        context['delivered_orders'] = orders.filter(is_delivered=True).count()
        context['invoiced_orders'] = orders.filter(is_invoiced=True).count()

        return context


class SalesOrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء طلب بيع جديد"""
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/orders/order_form.html'
    permission_required = 'sales.add_salesorder'
    success_url = reverse_lazy('sales:order_list')

    def get_form_kwargs(self):
        """إضافة company و user للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة طلب بيع جديد')

        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )
        else:
            context['formset'] = SalesOrderItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الطلب والسطور"""
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # حفظ الطلب
            self.object = form.save(commit=False)
            self.object.company = self.request.current_company
            self.object.created_by = self.request.user
            self.object.save()

            # حفظ السطور
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                _('تم إنشاء طلب البيع {} بنجاح').format(self.object.number)
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, _('يرجى تصحيح الأخطاء في النموذج'))
            return self.form_invalid(form)


class SalesOrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل طلب بيع"""
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/orders/order_form.html'
    permission_required = 'sales.change_salesorder'
    success_url = reverse_lazy('sales:order_list')

    def get_queryset(self):
        """الحصول على طلبات البيع للشركة الحالية فقط"""
        return SalesOrder.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        """إضافة company و user للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل طلب البيع {}').format(self.object.number)

        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )
        else:
            context['formset'] = SalesOrderItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الطلب والسطور"""
        context = self.get_context_data()
        formset = context['formset']

        # التحقق من إمكانية التعديل
        if self.object.is_delivered:
            messages.error(
                self.request,
                _('لا يمكن تعديل طلب بيع مسلم')
            )
            return redirect('sales:order_detail', pk=self.object.pk)

        if self.object.is_invoiced:
            messages.error(
                self.request,
                _('لا يمكن تعديل طلب بيع تم إصدار فاتورة له')
            )
            return redirect('sales:order_detail', pk=self.object.pk)

        if formset.is_valid():
            # حفظ الطلب
            self.object = form.save()

            # حفظ السطور
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                _('تم تعديل طلب البيع {} بنجاح').format(self.object.number)
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, _('يرجى تصحيح الأخطاء في النموذج'))
            return self.form_invalid(form)


class SalesOrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل طلب البيع"""
    model = SalesOrder
    template_name = 'sales/orders/order_detail.html'
    context_object_name = 'order'
    permission_required = 'sales.view_salesorder'

    def get_queryset(self):
        """الحصول على طلبات البيع للشركة الحالية فقط"""
        return SalesOrder.objects.filter(
            company=self.request.current_company
        ).select_related(
            'customer',
            'warehouse',
            'salesperson',
            'quotation',
            'created_by'
        ).prefetch_related('lines__item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('طلب البيع {}').format(self.object.number)

        # حساب الإجماليات
        lines = self.object.lines.all()
        context['lines'] = lines

        # حساب الإجمالي
        total = Decimal('0')
        for line in lines:
            line_total = line.quantity * line.unit_price
            total += line_total

        context['total_amount'] = total

        return context


class SalesOrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف طلب بيع"""
    model = SalesOrder
    template_name = 'sales/orders/order_confirm_delete.html'
    permission_required = 'sales.delete_salesorder'
    success_url = reverse_lazy('sales:order_list')

    def get_queryset(self):
        """الحصول على طلبات البيع للشركة الحالية فقط"""
        return SalesOrder.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        """التحقق قبل الحذف"""
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.is_delivered:
            messages.error(
                request,
                _('لا يمكن حذف طلب بيع مسلم')
            )
            return redirect('sales:order_detail', pk=self.object.pk)

        if self.object.is_invoiced:
            messages.error(
                request,
                _('لا يمكن حذف طلب بيع تم إصدار فاتورة له')
            )
            return redirect('sales:order_detail', pk=self.object.pk)

        if self.object.is_approved:
            messages.warning(
                request,
                _('تحذير: حذف طلب بيع معتمد')
            )

        messages.success(
            request,
            _('تم حذف طلب البيع {} بنجاح').format(self.object.number)
        )
        return super().delete(request, *args, **kwargs)


class ApproveSalesOrderView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """اعتماد طلب البيع"""
    permission_required = 'sales.change_salesorder'

    def post(self, request, pk):
        """اعتماد الطلب"""
        order = get_object_or_404(
            SalesOrder,
            pk=pk,
            company=request.current_company
        )

        if order.is_approved:
            messages.warning(request, _('طلب البيع معتمد مسبقاً'))
        else:
            order.is_approved = True
            order.save()
            messages.success(
                request,
                _('تم اعتماد طلب البيع {} بنجاح').format(order.number)
            )

        return redirect('sales:order_detail', pk=order.pk)


class ConvertToInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """تحويل طلب البيع إلى فاتورة"""
    permission_required = 'sales.add_salesinvoice'

    def get_queryset(self):
        """الحصول على طلبات البيع للشركة الحالية"""
        return SalesOrder.objects.filter(
            company=self.request.current_company,
            is_approved=True,
            is_invoiced=False
        )

    @transaction.atomic
    def post(self, request, pk):
        """تحويل الطلب لفاتورة"""
        try:
            order = self.get_queryset().get(pk=pk)
        except SalesOrder.DoesNotExist:
            messages.error(request, _('طلب البيع غير موجود أو غير معتمد أو تم إصدار فاتورة له مسبقاً'))
            return redirect('sales:order_list')

        # التحقق من وجود سطور
        if not order.lines.exists():
            messages.error(request, _('لا توجد سطور في طلب البيع'))
            return redirect('sales:order_detail', pk=order.pk)

        # الحصول على البيانات المطلوبة
        from apps.core.models import PaymentMethod, Currency
        payment_method = PaymentMethod.objects.filter(is_active=True).first()
        currency = Currency.objects.filter(is_active=True).first()

        if not payment_method:
            messages.error(request, _('لا توجد طريقة دفع متاحة'))
            return redirect('sales:order_detail', pk=order.pk)

        # إنشاء فاتورة المبيعات
        invoice = SalesInvoice.objects.create(
            company=request.current_company,
            branch=request.current_branch,
            date=order.date,
            customer=order.customer,
            warehouse=order.warehouse,
            salesperson=order.salesperson,
            payment_method=payment_method,
            currency=currency or order.customer.currency if hasattr(order.customer, 'currency') else None,
            receipt_number=f"RCP-{order.number}",
            notes=order.notes or "",
            created_by=request.user
        )

        # نسخ سطور طلب البيع لفاتورة المبيعات
        for order_line in order.lines.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                item=order_line.item,
                quantity=order_line.quantity,
                unit_price=order_line.unit_price,
                subtotal=order_line.quantity * order_line.unit_price
            )

        # حساب الإجماليات
        invoice.calculate_totals()

        # تحديث حالة طلب البيع
        order.is_invoiced = True
        order.save()

        messages.success(
            request,
            _('تم تحويل طلب البيع {} إلى فاتورة {} بنجاح').format(
                order.number,
                invoice.number
            )
        )
        return redirect('sales:invoice_detail', pk=invoice.pk)

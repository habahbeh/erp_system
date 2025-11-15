# apps/sales/views/pos_views.py
"""
Views لنقاط البيع POS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from datetime import date, datetime

from apps.sales.models import POSSession, SalesInvoice, InvoiceItem
from apps.sales.forms.pos_forms import POSSessionForm, CloseSessionForm, POSInvoiceQuickForm, POSInvoiceItemForm
from apps.core.models import Item, BusinessPartner, PaymentMethod, Warehouse


class POSSessionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة جلسات POS"""
    model = POSSession
    template_name = 'sales/pos/pos_session_list.html'
    context_object_name = 'sessions'
    permission_required = 'sales.view_possession'
    paginate_by = 25

    def get_queryset(self):
        """الحصول على جلسات POS للشركة الحالية"""
        queryset = POSSession.objects.filter(
            company=self.request.current_company
        ).select_related('cashier', 'branch')

        # الفلاتر
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        cashier_id = self.request.GET.get('cashier')
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(opening_datetime__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(opening_datetime__date__lte=date_to)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(session_number__icontains=search) |
                Q(cashier__first_name__icontains=search) |
                Q(cashier__last_name__icontains=search) |
                Q(pos_location__icontains=search)
            )

        return queryset.order_by('-opening_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('جلسات نقاط البيع')

        # إحصائيات
        sessions = self.get_queryset()

        # عدد الجلسات حسب الحالة
        context['total_sessions'] = sessions.count()
        context['open_sessions'] = sessions.filter(status='open').count()
        context['closed_sessions'] = sessions.filter(status='closed').count()

        # إجمالي المبيعات
        totals = sessions.aggregate(
            total_sales=Sum('total_sales'),
            total_cash_sales=Sum('total_cash_sales'),
            total_card_sales=Sum('total_card_sales'),
            total_transactions=Sum('transactions_count')
        )

        context['total_sales'] = totals['total_sales'] or Decimal('0')
        context['total_cash_sales'] = totals['total_cash_sales'] or Decimal('0')
        context['total_card_sales'] = totals['total_card_sales'] or Decimal('0')
        context['total_transactions'] = totals['total_transactions'] or 0

        # قائمة الكاشيرات للفلتر
        from apps.core.models import User
        context['cashiers'] = User.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('first_name', 'last_name')

        # التحقق من وجود جلسة مفتوحة للمستخدم الحالي
        context['user_has_open_session'] = POSSession.objects.filter(
            cashier=self.request.user,
            company=self.request.current_company,
            status='open'
        ).exists()

        # الحصول على الجلسة المفتوحة للمستخدم إن وجدت
        context['user_open_session'] = POSSession.objects.filter(
            cashier=self.request.user,
            company=self.request.current_company,
            status='open'
        ).first()

        return context


class POSSessionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """فتح جلسة POS جديدة"""
    model = POSSession
    form_class = POSSessionForm
    template_name = 'sales/pos/pos_session_form.html'
    permission_required = 'sales.add_possession'
    success_url = reverse_lazy('sales:pos_session_list')

    def dispatch(self, request, *args, **kwargs):
        """التحقق من عدم وجود جلسة مفتوحة للمستخدم"""
        existing_open = POSSession.objects.filter(
            cashier=request.user,
            company=request.current_company,
            status='open'
        ).first()

        if existing_open:
            messages.warning(
                request,
                _('لديك جلسة POS مفتوحة بالفعل ({}). يجب إغلاقها أولاً أو المتابعة إلى واجهة البيع.').format(
                    existing_open.session_number
                )
            )
            return redirect('sales:pos_interface', pk=existing_open.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """إضافة company و user للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('فتح جلسة POS جديدة')
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الجلسة الجديدة"""
        self.object = form.save()

        messages.success(
            self.request,
            _('تم فتح جلسة POS بنجاح: {}').format(self.object.session_number)
        )

        # إعادة التوجيه إلى واجهة البيع
        return redirect('sales:pos_interface', pk=self.object.pk)


class POSSessionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل جلسة POS"""
    model = POSSession
    template_name = 'sales/pos/pos_session_detail.html'
    context_object_name = 'session'
    permission_required = 'sales.view_possession'

    def get_queryset(self):
        """الحصول على الجلسات للشركة الحالية فقط"""
        return POSSession.objects.filter(
            company=self.request.current_company
        ).select_related('cashier', 'branch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('جلسة POS: {}').format(self.object.session_number)

        # الحصول على فواتير الجلسة
        context['invoices'] = SalesInvoice.objects.filter(
            pos_session=self.object
        ).select_related('customer', 'payment_method').order_by('-date', '-number')

        # إحصائيات الجلسة
        context['invoices_count'] = context['invoices'].count()

        # حساب الفرق النقدي كنسبة مئوية
        if self.object.expected_cash > 0:
            context['cash_difference_percentage'] = (
                self.object.cash_difference / self.object.expected_cash * 100
            )
        else:
            context['cash_difference_percentage'] = 0

        # التحقق من إمكانية الإغلاق
        context['can_close'] = (
            self.object.status == 'open' and
            self.object.cashier == self.request.user
        )

        return context


class POSSessionCloseView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """إغلاق جلسة POS"""
    model = POSSession
    form_class = CloseSessionForm
    template_name = 'sales/pos/pos_session_close.html'
    permission_required = 'sales.change_possession'

    def dispatch(self, request, *args, **kwargs):
        """التحقق من صلاحية إغلاق الجلسة"""
        self.object = self.get_object()

        # التحقق من أن الجلسة مفتوحة
        if self.object.status == 'closed':
            messages.error(request, _('الجلسة مغلقة بالفعل'))
            return redirect('sales:pos_session_detail', pk=self.object.pk)

        # التحقق من أن المستخدم هو الكاشير
        if self.object.cashier != request.user:
            messages.error(
                request,
                _('لا يمكنك إغلاق هذه الجلسة. فقط الكاشير {} يمكنه إغلاقها.').format(
                    self.object.cashier.get_full_name()
                )
            )
            return redirect('sales:pos_session_detail', pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """الحصول على الجلسات للشركة الحالية فقط"""
        return POSSession.objects.filter(
            company=self.request.current_company,
            status='open'
        )

    def get_form_kwargs(self):
        """إضافة session للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['session'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إغلاق جلسة POS: {}').format(self.object.session_number)

        # حساب الإحصائيات قبل الإغلاق
        self.object.calculate_totals()

        return context

    @transaction.atomic
    def form_valid(self, form):
        """إغلاق الجلسة"""
        closing_cash = form.cleaned_data['closing_cash']
        closing_notes = form.cleaned_data.get('closing_notes', '')

        # إغلاق الجلسة
        self.object.close_session(closing_cash, closing_notes)

        # رسالة النجاح مع تفاصيل
        if self.object.cash_difference == 0:
            messages.success(
                self.request,
                _('تم إغلاق الجلسة بنجاح. النقد متطابق تماماً!')
            )
        elif self.object.cash_difference > 0:
            messages.warning(
                self.request,
                _('تم إغلاق الجلسة. يوجد فائض نقدي: {} دينار').format(
                    abs(self.object.cash_difference)
                )
            )
        else:
            messages.warning(
                self.request,
                _('تم إغلاق الجلسة. يوجد عجز نقدي: {} دينار').format(
                    abs(self.object.cash_difference)
                )
            )

        return redirect('sales:pos_session_detail', pk=self.object.pk)


class POSInterfaceView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """واجهة البيع الرئيسية لنقاط البيع"""
    model = POSSession
    template_name = 'sales/pos/pos_interface.html'
    context_object_name = 'session'
    permission_required = 'sales.view_possession'

    def dispatch(self, request, *args, **kwargs):
        """التحقق من صلاحية استخدام الجلسة"""
        self.object = self.get_object()

        # التحقق من أن الجلسة مفتوحة
        if self.object.status == 'closed':
            messages.error(request, _('الجلسة مغلقة. لا يمكن إجراء مبيعات.'))
            return redirect('sales:pos_session_detail', pk=self.object.pk)

        # التحقق من أن المستخدم هو الكاشير
        if self.object.cashier != request.user:
            messages.error(
                request,
                _('هذه الجلسة تابعة للكاشير {}').format(
                    self.object.cashier.get_full_name()
                )
            )
            return redirect('sales:pos_session_list')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """الحصول على الجلسات للشركة الحالية فقط"""
        return POSSession.objects.filter(
            company=self.request.current_company
        ).select_related('cashier', 'branch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('نقطة البيع - {}').format(self.object.session_number)

        # الحصول على طرق الدفع
        context['payment_methods'] = PaymentMethod.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        # الحصول على العملاء
        context['customers'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            is_customer=True,
            is_active=True
        ).order_by('name')[:100]  # أول 100 عميل

        # الحصول على العميل النقدي الافتراضي
        context['default_customer'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            code='CASH',
            is_customer=True
        ).first()

        # طريقة الدفع النقدية الافتراضية
        context['default_payment_method'] = PaymentMethod.objects.filter(
            company=self.request.current_company,
            code='CASH',
            is_active=True
        ).first()

        # تحديث إحصائيات الجلسة
        self.object.calculate_totals()

        return context


class POSSearchItemView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """البحث عن مادة بالكود أو الباركود (AJAX)"""
    permission_required = 'sales.view_possession'

    def get(self, request, *args, **kwargs):
        """البحث عن المادة"""
        search_term = request.GET.get('q', '').strip()

        if not search_term:
            return JsonResponse({
                'success': False,
                'message': _('يجب إدخال كود أو باركود للبحث')
            })

        # البحث عن المادة
        item = Item.objects.filter(
            company=request.current_company,
            is_active=True
        ).filter(
            Q(code=search_term) | Q(barcode=search_term)
        ).select_related('category', 'unit').first()

        if not item:
            return JsonResponse({
                'success': False,
                'message': _('المادة غير موجودة')
            })

        # إرجاع بيانات المادة
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'code': item.code,
                'barcode': item.barcode or '',
                'name': item.name,
                'name_en': item.name_en or '',
                'selling_price': str(item.selling_price),
                'unit': item.unit.name if item.unit else '',
                'category': item.category.name if item.category else '',
                'description': item.description or '',
            }
        })


class POSCreateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """إنشاء فاتورة بيع من POS (AJAX)"""
    permission_required = 'sales.add_salesinvoice'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """إنشاء الفاتورة"""
        import json

        try:
            # الحصول على الجلسة
            session_id = kwargs.get('session_id')
            session = get_object_or_404(
                POSSession,
                pk=session_id,
                company=request.current_company,
                status='open',
                cashier=request.user
            )

            # الحصول على البيانات من الطلب
            data = json.loads(request.body)

            customer_id = data.get('customer_id')
            payment_method_id = data.get('payment_method_id')
            items_data = data.get('items', [])
            discount_type = data.get('discount_type', 'percentage')
            discount_value = Decimal(data.get('discount_value', '0'))
            notes = data.get('notes', '')

            # التحقق من وجود مواد
            if not items_data:
                return JsonResponse({
                    'success': False,
                    'message': _('يجب إضافة مادة واحدة على الأقل')
                })

            # الحصول على العميل
            if customer_id:
                customer = get_object_or_404(
                    BusinessPartner,
                    pk=customer_id,
                    company=request.current_company,
                    is_customer=True
                )
            else:
                # العميل النقدي الافتراضي
                customer = BusinessPartner.objects.filter(
                    company=request.current_company,
                    code='CASH',
                    is_customer=True
                ).first()

                if not customer:
                    return JsonResponse({
                        'success': False,
                        'message': _('لا يوجد عميل نقدي افتراضي')
                    })

            # الحصول على طريقة الدفع
            payment_method = get_object_or_404(
                PaymentMethod,
                pk=payment_method_id,
                company=request.current_company,
                is_active=True
            )

            # إنشاء الفاتورة
            invoice = SalesInvoice.objects.create(
                company=request.current_company,
                branch=request.current_branch,
                customer=customer,
                date=timezone.now().date(),
                payment_method=payment_method,
                payment_term='cash',
                pos_session=session,
                notes=notes,
                created_by=request.user
            )

            # إضافة المواد
            subtotal = Decimal('0')
            for item_data in items_data:
                item = get_object_or_404(
                    Item,
                    pk=item_data['item_id'],
                    company=request.current_company,
                    is_active=True
                )

                quantity = Decimal(item_data['quantity'])
                unit_price = Decimal(item_data['unit_price'])
                discount_percentage = Decimal(item_data.get('discount_percentage', '0'))

                # حساب الصافي
                line_total = quantity * unit_price
                discount_amount = line_total * discount_percentage / 100
                net_amount = line_total - discount_amount

                # إنشاء سطر الفاتورة
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item=item,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percentage=discount_percentage,
                    discount_amount=discount_amount,
                    net_amount=net_amount
                )

                subtotal += net_amount

            # حساب الخصم الإجمالي
            if discount_type == 'percentage':
                invoice.discount_percentage = discount_value
                invoice.discount_amount = subtotal * discount_value / 100
            else:
                invoice.discount_amount = discount_value
                if subtotal > 0:
                    invoice.discount_percentage = (discount_value / subtotal * 100)

            # حساب الإجمالي
            invoice.subtotal = subtotal
            invoice.total_amount = subtotal - invoice.discount_amount
            invoice.save()

            # ترحيل الفاتورة تلقائياً
            invoice.post_invoice()

            # تحديث إحصائيات الجلسة
            session.calculate_totals()

            return JsonResponse({
                'success': True,
                'message': _('تم إنشاء الفاتورة بنجاح'),
                'invoice_id': invoice.id,
                'invoice_number': invoice.number,
                'invoice_total': str(invoice.total_amount),
                'session_total_sales': str(session.total_sales),
                'session_transactions_count': session.transactions_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


class POSSessionReopenView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """إعادة فتح جلسة POS مغلقة"""
    permission_required = 'sales.change_possession'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """إعادة فتح الجلسة"""
        session = get_object_or_404(
            POSSession,
            pk=kwargs.get('pk'),
            company=request.current_company,
            status='closed'
        )

        # إعادة فتح الجلسة
        session.reopen_session()

        messages.success(
            request,
            _('تم إعادة فتح الجلسة بنجاح: {}').format(session.session_number)
        )

        return redirect('sales:pos_interface', pk=session.pk)


class POSSessionPrintReportView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """طباعة تقرير جلسة POS"""
    model = POSSession
    template_name = 'sales/pos/pos_session_print.html'
    context_object_name = 'session'
    permission_required = 'sales.view_possession'

    def get_queryset(self):
        """الحصول على الجلسات للشركة الحالية فقط"""
        return POSSession.objects.filter(
            company=self.request.current_company
        ).select_related('cashier', 'branch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تقرير جلسة POS')

        # الحصول على فواتير الجلسة
        context['invoices'] = SalesInvoice.objects.filter(
            pos_session=self.object
        ).select_related('customer', 'payment_method').order_by('number')

        # تحديث الإحصائيات
        self.object.calculate_totals()

        return context

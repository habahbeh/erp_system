# apps/sales/views/quotation_views.py
"""
Views لعروض الأسعار
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

from apps.sales.models import Quotation, QuotationItem, SalesOrder, SalesOrderItem
from apps.sales.forms import QuotationForm, QuotationItemFormSet
from apps.core.models import Warehouse


class QuotationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة عروض الأسعار"""
    model = Quotation
    template_name = 'sales/quotations/quotation_list.html'
    context_object_name = 'quotations'
    permission_required = 'sales.view_quotation'
    paginate_by = 50

    def get_queryset(self):
        """الحصول على عروض الأسعار للشركة الحالية"""
        from datetime import date, timedelta

        queryset = Quotation.objects.filter(
            company=self.request.current_company
        ).select_related(
            'customer',
            'salesperson',
            'currency',
            'created_by'
        ).prefetch_related('lines')

        # فلتر الحالة
        status = self.request.GET.get('status')
        if status:
            if status == 'pending':
                queryset = queryset.filter(is_approved=False, converted_to_order=False)
            elif status == 'approved':
                queryset = queryset.filter(is_approved=True, converted_to_order=False)
            elif status == 'converted':
                queryset = queryset.filter(converted_to_order=True)
            elif status == 'expired':
                queryset = queryset.filter(expiry_date__lt=date.today(), converted_to_order=False)

        # فلتر العميل
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # فلتر موظف المبيعات
        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)

        # فلتر التاريخ
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # فلتر قارب على الانتهاء
        expiring = self.request.GET.get('expiring')
        if expiring:
            days = int(expiring)
            today = date.today()
            queryset = queryset.filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=days),
                converted_to_order=False
            )

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
        context['title'] = _('عروض الأسعار')

        # إحصائيات شاملة
        from datetime import date, timedelta
        from django.db.models import Sum, Count

        quotations = Quotation.objects.filter(company=self.request.current_company)
        today = date.today()

        # إحصائيات الحالة
        stats = {
            'total_count': quotations.count(),
            'pending_count': quotations.filter(is_approved=False, converted_to_order=False).count(),
            'approved_count': quotations.filter(is_approved=True, converted_to_order=False).count(),
            'converted_count': quotations.filter(converted_to_order=True).count(),
            'expired_count': quotations.filter(expiry_date__lt=today, converted_to_order=False).count(),

            # الإحصائيات المالية
            'total_value': quotations.aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'approved_value': quotations.filter(is_approved=True).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'converted_value': quotations.filter(converted_to_order=True).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),

            # عروض قاربت على الانتهاء (خلال 7 أيام)
            'expiring_soon': quotations.filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=7),
                converted_to_order=False
            ).count(),
        }

        context['stats'] = stats

        # قائمة العملاء للفلتر
        from apps.core.models import BusinessPartner
        context['customers'] = BusinessPartner.objects.filter(
            company=self.request.current_company,
            partner_type__in=['customer', 'both'],
            is_active=True
        ).order_by('name')

        # قائمة موظفي المبيعات
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['salespeople'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

        # صلاحيات
        context['can_add'] = self.request.user.has_perm('sales.add_quotation')
        context['can_edit'] = self.request.user.has_perm('sales.change_quotation')
        context['can_delete'] = self.request.user.has_perm('sales.delete_quotation')

        # Breadcrumbs
        from django.urls import reverse
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المبيعات'), 'url': reverse('sales:dashboard')},
            {'title': _('عروض الأسعار'), 'url': ''},
        ]

        return context


class QuotationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء عرض سعر جديد"""
    model = Quotation
    form_class = QuotationForm
    template_name = 'sales/quotations/quotation_form.html'
    permission_required = 'sales.add_quotation'
    success_url = reverse_lazy('sales:quotation_list')

    def get_form_kwargs(self):
        """إضافة company و user للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة عرض سعر جديد')

        if self.request.POST:
            context['formset'] = QuotationItemFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )
        else:
            context['formset'] = QuotationItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ العرض والسطور"""
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # حفظ العرض
            self.object = form.save(commit=False)
            self.object.company = self.request.current_company
            self.object.created_by = self.request.user
            self.object.save()

            # حفظ السطور
            formset.instance = self.object
            formset.save()

            # حساب الإجمالي
            total = Decimal('0')
            for line in self.object.lines.all():
                line_total = line.quantity * line.unit_price
                if line.discount_percentage > 0:
                    line_total = line_total * (1 - line.discount_percentage / 100)
                line.total = line_total
                line.save()
                total += line_total

            self.object.total_amount = total
            self.object.save()

            messages.success(
                self.request,
                _('تم إنشاء عرض السعر {} بنجاح').format(self.object.number)
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, _('يرجى تصحيح الأخطاء في النموذج'))
            return self.form_invalid(form)


class QuotationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل عرض سعر"""
    model = Quotation
    form_class = QuotationForm
    template_name = 'sales/quotations/quotation_form.html'
    permission_required = 'sales.change_quotation'
    success_url = reverse_lazy('sales:quotation_list')

    def get_queryset(self):
        """الحصول على عروض الأسعار للشركة الحالية فقط"""
        return Quotation.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        """إضافة company و user للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل عرض السعر {}').format(self.object.number)

        if self.request.POST:
            context['formset'] = QuotationItemFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )
        else:
            context['formset'] = QuotationItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.request.current_company}
            )

        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ العرض والسطور"""
        context = self.get_context_data()
        formset = context['formset']

        # التحقق من إمكانية التعديل
        if self.object.converted_to_order:
            messages.error(
                self.request,
                _('لا يمكن تعديل عرض سعر محول لطلب')
            )
            return redirect('sales:quotation_detail', pk=self.object.pk)

        if formset.is_valid():
            # حفظ العرض
            self.object = form.save()

            # حفظ السطور
            formset.instance = self.object
            formset.save()

            # إعادة حساب الإجمالي
            total = Decimal('0')
            for line in self.object.lines.all():
                line_total = line.quantity * line.unit_price
                if line.discount_percentage > 0:
                    line_total = line_total * (1 - line.discount_percentage / 100)
                line.total = line_total
                line.save()
                total += line_total

            self.object.total_amount = total
            self.object.save()

            messages.success(
                self.request,
                _('تم تعديل عرض السعر {} بنجاح').format(self.object.number)
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, _('يرجى تصحيح الأخطاء في النموذج'))
            return self.form_invalid(form)


class QuotationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل عرض السعر"""
    model = Quotation
    template_name = 'sales/quotations/quotation_detail.html'
    context_object_name = 'quotation'
    permission_required = 'sales.view_quotation'

    def get_queryset(self):
        """الحصول على عروض الأسعار للشركة الحالية فقط"""
        return Quotation.objects.filter(
            company=self.request.current_company
        ).select_related(
            'customer',
            'salesperson',
            'currency',
            'created_by'
        ).prefetch_related('lines__item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('عرض السعر {}').format(self.object.number)

        # حساب الإجماليات
        lines = self.object.lines.all()
        context['lines'] = lines

        # حساب الإجمالي الفرعي والخصم
        subtotal = Decimal('0')
        total_discount = Decimal('0')

        for line in lines:
            line_subtotal = line.quantity * line.unit_price
            line_discount = line_subtotal * (line.discount_percentage / 100) if line.discount_percentage else Decimal('0')
            subtotal += line_subtotal
            total_discount += line_discount

        context['subtotal'] = subtotal
        context['total_discount'] = total_discount

        # التحقق من انتهاء الصلاحية
        from datetime import date
        if self.object.expiry_date:
            context['is_expired'] = self.object.expiry_date < date.today()
        else:
            context['is_expired'] = False

        # الحصول على طلبات البيع المرتبطة
        context['related_orders'] = SalesOrder.objects.filter(
            quotation=self.object
        ).select_related('customer', 'warehouse')

        # Breadcrumbs
        from django.urls import reverse
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المبيعات'), 'url': reverse('sales:dashboard')},
            {'title': _('عروض الأسعار'), 'url': reverse('sales:quotation_list')},
            {'title': self.object.number, 'url': ''},
        ]

        return context


class QuotationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف عرض سعر"""
    model = Quotation
    template_name = 'sales/quotations/quotation_confirm_delete.html'
    success_url = reverse_lazy('sales:quotation_list')
    permission_required = 'sales.delete_quotation'

    def get_queryset(self):
        """الحصول على عروض الأسعار للشركة الحالية فقط"""
        return Quotation.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        """التحقق قبل الحذف"""
        self.object = self.get_object()

        # التحقق من إمكانية الحذف
        if self.object.converted_to_order:
            messages.error(
                request,
                _('لا يمكن حذف عرض سعر محول لطلب')
            )
            return redirect('sales:quotation_detail', pk=self.object.pk)

        quotation_number = self.object.number
        messages.success(
            request,
            _('تم حذف عرض السعر {} بنجاح').format(quotation_number)
        )
        return super().delete(request, *args, **kwargs)


class ConvertToOrderView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """تحويل عرض السعر إلى طلب بيع"""
    permission_required = 'sales.add_salesorder'

    def get_queryset(self):
        """الحصول على عروض الأسعار للشركة الحالية"""
        return Quotation.objects.filter(
            company=self.request.current_company,
            converted_to_order=False
        )

    @transaction.atomic
    def post(self, request, pk):
        """تحويل العرض لطلب"""
        try:
            quotation = self.get_queryset().get(pk=pk)
        except Quotation.DoesNotExist:
            messages.error(request, _('عرض السعر غير موجود أو محول مسبقاً'))
            return redirect('sales:quotation_list')

        # التحقق من وجود سطور
        if not quotation.lines.exists():
            messages.error(request, _('لا توجد سطور في عرض السعر'))
            return redirect('sales:quotation_detail', pk=quotation.pk)

        # الحصول على المستودع (يمكن اختياره من الطلب أو استخدام الافتراضي)
        warehouse_id = request.POST.get('warehouse')
        if warehouse_id:
            warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company=request.current_company)
        else:
            # استخدام المستودع الافتراضي
            warehouse = Warehouse.objects.filter(
                company=request.current_company,
                is_active=True
            ).first()

            if not warehouse:
                messages.error(request, _('لا يوجد مستودع متاح'))
                return redirect('sales:quotation_detail', pk=quotation.pk)

        # إنشاء طلب البيع
        order = SalesOrder.objects.create(
            company=request.current_company,
            date=quotation.date,
            customer=quotation.customer,
            warehouse=warehouse,
            salesperson=quotation.salesperson,
            quotation=quotation,
            notes=quotation.notes,
            created_by=request.user
        )

        # نسخ سطور عرض السعر لطلب البيع
        for quote_line in quotation.lines.all():
            # حساب السعر الفعلي بعد الخصم
            # إذا كان هناك خصم، نحسب السعر الجديد
            if quote_line.discount_percentage and quote_line.discount_percentage > 0:
                # السعر الفعلي = السعر الأصلي - (السعر الأصلي * نسبة الخصم / 100)
                effective_price = quote_line.unit_price * (1 - quote_line.discount_percentage / 100)
            else:
                effective_price = quote_line.unit_price

            SalesOrderItem.objects.create(
                order=order,
                item=quote_line.item,
                quantity=quote_line.quantity,
                unit_price=effective_price
            )

        # تحديث حالة عرض السعر
        quotation.converted_to_order = True
        quotation.save()

        messages.success(
            request,
            _('تم تحويل عرض السعر {} إلى طلب بيع {} بنجاح').format(
                quotation.number,
                order.number
            )
        )
        return redirect('sales:order_detail', pk=order.pk)


class ApproveQuotationView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """اعتماد عرض السعر"""
    permission_required = 'sales.change_quotation'

    def post(self, request, pk):
        """اعتماد العرض"""
        quotation = get_object_or_404(
            Quotation,
            pk=pk,
            company=request.current_company
        )

        if quotation.is_approved:
            messages.warning(request, _('عرض السعر معتمد مسبقاً'))
        else:
            quotation.is_approved = True
            quotation.save()
            messages.success(
                request,
                _('تم اعتماد عرض السعر {} بنجاح').format(quotation.number)
            )

        return redirect('sales:quotation_detail', pk=quotation.pk)

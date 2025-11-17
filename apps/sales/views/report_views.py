# apps/sales/views/report_views.py
"""
Views التقارير - Sales Reports
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, Max, Min, Value, DecimalField
from django.db.models.functions import TruncMonth, TruncYear, TruncDate, Coalesce
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta, datetime
from decimal import Decimal
import io

from apps.core.decorators import permission_required_with_message
from apps.core.models import BusinessPartner, Item
from ..models import (
    SalesInvoice, SalesOrder, Quotation,
    SalespersonCommission,
    InvoiceItem
)


@login_required
@permission_required_with_message('sales.view_salesinvoice')
def customer_statement_report(request):
    """كشف حساب عميل - Customer Statement"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    customer_id = request.GET.get('customer')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # بيانات العميل
    customer = None
    if customer_id:
        try:
            customer = BusinessPartner.objects.get(
                id=customer_id,
                company=company,
                is_customer=True
            )
        except BusinessPartner.DoesNotExist:
            messages.error(request, 'العميل غير موجود')
            return redirect('sales:reports_menu')

    # الفواتير
    invoices = None
    stats = None
    transactions = []

    if customer:
        # فواتير المبيعات
        invoices = SalesInvoice.objects.filter(
            company=company,
            customer=customer,
            is_posted=True
        ).select_related('payment_method', 'currency', 'branch', 'salesperson')

        if date_from:
            invoices = invoices.filter(date__gte=date_from)

        if date_to:
            invoices = invoices.filter(date__lte=date_to)

        # الإحصائيات
        stats = invoices.aggregate(
            total_invoices=Count('id'),
            total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
            total_tax=Coalesce(Sum('tax_amount'), Decimal('0')),
            total_discount=Coalesce(Sum('discount_amount'), Decimal('0')),
            total_paid=Coalesce(Sum('paid_amount'), Decimal('0')),
            total_remaining=Coalesce(Sum('remaining_amount'), Decimal('0'))
        )

        # تجهيز المعاملات (Transactions) للكشف
        for invoice in invoices.order_by('date', 'number'):
            transactions.append({
                'date': invoice.date,
                'type': 'فاتورة مبيعات',
                'number': invoice.number,
                'description': invoice.notes or '-',
                'debit': invoice.total_amount,  # مدين
                'credit': invoice.paid_amount,  # دائن
                'balance': invoice.remaining_amount,  # الرصيد
                'reference': invoice,
            })

        # حساب الرصيد التراكمي
        running_balance = Decimal('0')
        for trans in transactions:
            running_balance += trans['debit'] - trans['credit']
            trans['running_balance'] = running_balance

    # العملاء للاختيار
    customers = BusinessPartner.objects.filter(
        company=company,
        is_customer=True,
        is_active=True
    ).order_by('name')

    context = {
        'title': _('كشف حساب عميل'),
        'customer': customer,
        'customers': customers,
        'transactions': transactions,
        'stats': stats,
        'date_from': date_from,
        'date_to': date_to,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('كشف حساب عميل'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/customer_statement.html', context)


@login_required
@permission_required_with_message('sales.view_salesinvoice')
def sales_detailed_report(request):
    """كشف مبيعات تفصيلي - Detailed Sales Report"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    customer_id = request.GET.get('customer')
    item_id = request.GET.get('item')
    salesperson_id = request.GET.get('salesperson')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    payment_status = request.GET.get('payment_status')

    # سطور الفواتير (تفصيلي لكل مادة)
    invoice_items = InvoiceItem.objects.filter(
        invoice__company=company,
        invoice__is_posted=True
    ).select_related(
        'invoice',
        'invoice__customer',
        'invoice__salesperson',
        'invoice__payment_method',
        'item',
        'item__category'
    )

    if customer_id:
        invoice_items = invoice_items.filter(invoice__customer_id=customer_id)

    if item_id:
        invoice_items = invoice_items.filter(item_id=item_id)

    if salesperson_id:
        invoice_items = invoice_items.filter(invoice__salesperson_id=salesperson_id)

    if date_from:
        invoice_items = invoice_items.filter(invoice__date__gte=date_from)

    if date_to:
        invoice_items = invoice_items.filter(invoice__date__lte=date_to)

    if payment_status:
        invoice_items = invoice_items.filter(invoice__payment_status=payment_status)

    # الإحصائيات الإجمالية
    stats = invoice_items.aggregate(
        total_items=Count('id'),
        total_quantity=Coalesce(Sum('quantity'), Decimal('0')),
        total_amount=Coalesce(Sum('net_amount'), Decimal('0')),
        total_discount=Coalesce(Sum('discount_amount'), Decimal('0')),
        avg_unit_price=Coalesce(Avg('unit_price'), Decimal('0'))
    )

    # حسب المادة
    by_item = invoice_items.values(
        'item__id',
        'item__code',
        'item__name',
        'item__category__name'
    ).annotate(
        quantity=Coalesce(Sum('quantity'), Decimal('0')),
        total_amount=Coalesce(Sum('net_amount'), Decimal('0')),
        avg_price=Coalesce(Avg('unit_price'), Decimal('0'))
    ).order_by('-total_amount')[:50]

    # حسب العميل
    by_customer = invoice_items.values(
        'invoice__customer__id',
        'invoice__customer__name',
        'invoice__customer__code'
    ).annotate(
        quantity=Coalesce(Sum('quantity'), Decimal('0')),
        total_amount=Coalesce(Sum('net_amount'), Decimal('0')),
        invoice_count=Count('invoice__id', distinct=True)
    ).order_by('-total_amount')[:20]

    # حسب المندوب
    by_salesperson = invoice_items.filter(
        invoice__salesperson__isnull=False
    ).values(
        'invoice__salesperson__id',
        'invoice__salesperson__first_name',
        'invoice__salesperson__last_name'
    ).annotate(
        quantity=Coalesce(Sum('quantity'), Decimal('0')),
        total_amount=Coalesce(Sum('net_amount'), Decimal('0')),
        invoice_count=Count('invoice__id', distinct=True)
    ).order_by('-total_amount')

    # حسب التاريخ (شهري)
    by_month = invoice_items.annotate(
        month=TruncMonth('invoice__date')
    ).values('month').annotate(
        quantity=Coalesce(Sum('quantity'), Decimal('0')),
        total_amount=Coalesce(Sum('net_amount'), Decimal('0')),
        invoice_count=Count('invoice__id', distinct=True)
    ).order_by('month')

    # البيانات للاختيارات
    customers = BusinessPartner.objects.filter(
        company=company,
        is_customer=True,
        is_active=True
    ).order_by('name')

    items = Item.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')[:100]

    from apps.hr.models import Employee
    salespersons = Employee.objects.filter(
        company=company,
        is_active=True
    ).order_by('first_name', 'last_name')

    context = {
        'title': _('كشف مبيعات تفصيلي'),
        'invoice_items': invoice_items.order_by('-invoice__date', '-invoice__number')[:500],
        'stats': stats,
        'by_item': by_item,
        'by_customer': by_customer,
        'by_salesperson': by_salesperson,
        'by_month': list(by_month),
        'customers': customers,
        'items': items,
        'salespersons': salespersons,
        'selected_customer': customer_id,
        'selected_item': item_id,
        'selected_salesperson': salesperson_id,
        'date_from': date_from,
        'date_to': date_to,
        'payment_status': payment_status,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('كشف مبيعات تفصيلي'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/sales_detailed.html', context)


@login_required
@permission_required_with_message('sales.view_salesinvoice')
def profit_loss_report(request):
    """تقرير الأرباح والخسائر - Profit & Loss Report"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    customer_id = request.GET.get('customer')
    item_id = request.GET.get('item')

    # سطور الفواتير
    invoice_items = InvoiceItem.objects.filter(
        invoice__company=company,
        invoice__is_posted=True
    ).select_related('invoice', 'item', 'invoice__customer')

    if date_from:
        invoice_items = invoice_items.filter(invoice__date__gte=date_from)

    if date_to:
        invoice_items = invoice_items.filter(invoice__date__lte=date_to)

    if customer_id:
        invoice_items = invoice_items.filter(invoice__customer_id=customer_id)

    if item_id:
        invoice_items = invoice_items.filter(item_id=item_id)

    # حساب الأرباح والخسائر
    profit_loss_data = []
    total_revenue = Decimal('0')
    total_cost = Decimal('0')
    total_profit = Decimal('0')
    total_margin_percent = Decimal('0')

    for item_line in invoice_items:
        # سعر البيع (الإيرادات)
        revenue = item_line.net_amount

        # التكلفة (سعر الشراء × الكمية)
        cost = item_line.item.cost_price * item_line.quantity

        # الربح
        profit = revenue - cost

        # هامش الربح %
        if revenue > 0:
            margin_percent = (profit / revenue) * 100
        else:
            margin_percent = Decimal('0')

        profit_loss_data.append({
            'invoice': item_line.invoice,
            'item': item_line.item,
            'quantity': item_line.quantity,
            'unit_price': item_line.unit_price,
            'cost_price': item_line.item.cost_price,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin_percent': margin_percent,
        })

        total_revenue += revenue
        total_cost += cost
        total_profit += profit

    # حساب هامش الربح الإجمالي
    if total_revenue > 0:
        total_margin_percent = (total_profit / total_revenue) * 100

    # الإحصائيات
    stats = {
        'total_items': len(profit_loss_data),
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'total_margin_percent': total_margin_percent,
    }

    # حسب المادة
    by_item = {}
    for data in profit_loss_data:
        item_id = data['item'].id
        if item_id not in by_item:
            by_item[item_id] = {
                'item': data['item'],
                'quantity': Decimal('0'),
                'revenue': Decimal('0'),
                'cost': Decimal('0'),
                'profit': Decimal('0'),
            }

        by_item[item_id]['quantity'] += data['quantity']
        by_item[item_id]['revenue'] += data['revenue']
        by_item[item_id]['cost'] += data['cost']
        by_item[item_id]['profit'] += data['profit']

    # حساب هامش الربح لكل مادة
    for item_data in by_item.values():
        if item_data['revenue'] > 0:
            item_data['margin_percent'] = (item_data['profit'] / item_data['revenue']) * 100
        else:
            item_data['margin_percent'] = Decimal('0')

    # ترتيب حسب الربح
    by_item_sorted = sorted(by_item.values(), key=lambda x: x['profit'], reverse=True)[:30]

    # حسب العميل
    by_customer = {}
    for data in profit_loss_data:
        customer_id = data['invoice'].customer.id
        if customer_id not in by_customer:
            by_customer[customer_id] = {
                'customer': data['invoice'].customer,
                'revenue': Decimal('0'),
                'cost': Decimal('0'),
                'profit': Decimal('0'),
                'invoice_count': set(),
            }

        by_customer[customer_id]['revenue'] += data['revenue']
        by_customer[customer_id]['cost'] += data['cost']
        by_customer[customer_id]['profit'] += data['profit']
        by_customer[customer_id]['invoice_count'].add(data['invoice'].id)

    # حساب هامش الربح لكل عميل
    for customer_data in by_customer.values():
        if customer_data['revenue'] > 0:
            customer_data['margin_percent'] = (customer_data['profit'] / customer_data['revenue']) * 100
        else:
            customer_data['margin_percent'] = Decimal('0')
        customer_data['invoice_count'] = len(customer_data['invoice_count'])

    # ترتيب حسب الربح
    by_customer_sorted = sorted(by_customer.values(), key=lambda x: x['profit'], reverse=True)[:20]

    # البيانات للاختيارات
    customers = BusinessPartner.objects.filter(
        company=company,
        is_customer=True,
        is_active=True
    ).order_by('name')

    items = Item.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')[:100]

    context = {
        'title': _('تقرير الأرباح والخسائر'),
        'profit_loss_data': profit_loss_data[:100],
        'stats': stats,
        'by_item': by_item_sorted,
        'by_customer': by_customer_sorted,
        'customers': customers,
        'items': items,
        'selected_customer': customer_id,
        'selected_item': item_id,
        'date_from': date_from,
        'date_to': date_to,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('الأرباح والخسائر'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/profit_loss.html', context)


@login_required
@permission_required_with_message('sales.view_salesinvoice')
def tax_report(request):
    """تقرير الضريبة - Tax Report
    دعم 8 نسب ضريبية: 0%, 1%, 4%, 5%, 6%, 10%, 12%, 16%
    """

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tax_rate = request.GET.get('tax_rate')

    # الفواتير المرحلة
    invoices = SalesInvoice.objects.filter(
        company=company,
        is_posted=True
    ).select_related('customer', 'payment_method')

    if date_from:
        invoices = invoices.filter(date__gte=date_from)

    if date_to:
        invoices = invoices.filter(date__lte=date_to)

    if tax_rate:
        invoices = invoices.filter(tax_rate=Decimal(tax_rate))

    # الإحصائيات حسب نسبة الضريبة
    # النسب المدعومة: 0%, 1%, 4%, 5%, 6%, 10%, 12%, 16%
    tax_rates = [
        Decimal('0.00'),
        Decimal('1.00'),
        Decimal('4.00'),
        Decimal('5.00'),
        Decimal('6.00'),
        Decimal('10.00'),
        Decimal('12.00'),
        Decimal('16.00'),
    ]

    by_tax_rate = []
    total_base = Decimal('0')
    total_tax = Decimal('0')
    total_with_tax = Decimal('0')

    for rate in tax_rates:
        rate_invoices = invoices.filter(tax_rate=rate)

        stats = rate_invoices.aggregate(
            invoice_count=Count('id'),
            base_amount=Coalesce(Sum('subtotal'), Decimal('0')),
            tax_amount=Coalesce(Sum('tax_amount'), Decimal('0')),
            total_amount=Coalesce(Sum('total_amount'), Decimal('0'))
        )

        if stats['invoice_count'] > 0:
            by_tax_rate.append({
                'rate': rate,
                'rate_display': f"{rate}%",
                'invoice_count': stats['invoice_count'],
                'base_amount': stats['base_amount'],
                'tax_amount': stats['tax_amount'],
                'total_amount': stats['total_amount'],
            })

            total_base += stats['base_amount']
            total_tax += stats['tax_amount']
            total_with_tax += stats['total_amount']

    # الإحصائيات الإجمالية
    grand_total_stats = {
        'total_invoices': invoices.count(),
        'total_base': total_base,
        'total_tax': total_tax,
        'total_with_tax': total_with_tax,
    }

    # تفاصيل الفواتير
    invoice_details = invoices.values(
        'id',
        'number',
        'date',
        'customer__name',
        'tax_rate',
        'subtotal',
        'tax_amount',
        'total_amount'
    ).order_by('-date')[:200]

    # حسب الشهر
    by_month = invoices.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        invoice_count=Count('id'),
        base_amount=Coalesce(Sum('subtotal'), Decimal('0')),
        tax_amount=Coalesce(Sum('tax_amount'), Decimal('0')),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0'))
    ).order_by('month')

    context = {
        'title': _('تقرير الضريبة'),
        'by_tax_rate': by_tax_rate,
        'grand_total_stats': grand_total_stats,
        'invoice_details': invoice_details,
        'by_month': list(by_month),
        'tax_rates': tax_rates,
        'selected_tax_rate': tax_rate,
        'date_from': date_from,
        'date_to': date_to,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('تقرير الضريبة'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/tax_report.html', context)


@login_required
@permission_required_with_message('sales.view_salesinvoice')
def invoice_search_report(request):
    """بحث الفواتير المتقدم - Advanced Invoice Search"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر المتعددة
    search_query = request.GET.get('search', '').strip()
    customer_id = request.GET.get('customer')
    salesperson_id = request.GET.get('salesperson')
    payment_method_id = request.GET.get('payment_method')
    payment_status = request.GET.get('payment_status')
    payment_term = request.GET.get('payment_term')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    is_posted = request.GET.get('is_posted')

    # الفواتير
    invoices = SalesInvoice.objects.filter(
        company=company
    ).select_related(
        'customer',
        'salesperson',
        'payment_method',
        'currency',
        'branch'
    )

    # البحث النصي
    if search_query:
        invoices = invoices.filter(
            Q(number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__code__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلاتر الأخرى
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)

    if salesperson_id:
        invoices = invoices.filter(salesperson_id=salesperson_id)

    if payment_method_id:
        invoices = invoices.filter(payment_method_id=payment_method_id)

    if payment_status:
        invoices = invoices.filter(payment_status=payment_status)

    if payment_term:
        invoices = invoices.filter(payment_term=payment_term)

    if date_from:
        invoices = invoices.filter(date__gte=date_from)

    if date_to:
        invoices = invoices.filter(date__lte=date_to)

    if min_amount:
        invoices = invoices.filter(total_amount__gte=Decimal(min_amount))

    if max_amount:
        invoices = invoices.filter(total_amount__lte=Decimal(max_amount))

    if is_posted == 'yes':
        invoices = invoices.filter(is_posted=True)
    elif is_posted == 'no':
        invoices = invoices.filter(is_posted=False)

    # الإحصائيات
    stats = invoices.aggregate(
        total_count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
        total_paid=Coalesce(Sum('paid_amount'), Decimal('0')),
        total_remaining=Coalesce(Sum('remaining_amount'), Decimal('0')),
        avg_invoice=Coalesce(Avg('total_amount'), Decimal('0'))
    )

    # عدد حسب الحالة
    posted_count = invoices.filter(is_posted=True).count()
    draft_count = invoices.filter(is_posted=False).count()

    # عدد حسب حالة الدفع
    unpaid_count = invoices.filter(payment_status='unpaid').count()
    partial_count = invoices.filter(payment_status='partial').count()
    paid_count = invoices.filter(payment_status='paid').count()

    # البيانات للاختيارات
    customers = BusinessPartner.objects.filter(
        company=company,
        is_customer=True,
        is_active=True
    ).order_by('name')

    from apps.hr.models import Employee
    salespersons = Employee.objects.filter(
        company=company,
        is_active=True
    ).order_by('first_name', 'last_name')

    from apps.core.models import PaymentMethod
    payment_methods = PaymentMethod.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')

    context = {
        'title': _('بحث الفواتير المتقدم'),
        'invoices': invoices.order_by('-date', '-number')[:200],
        'stats': stats,
        'posted_count': posted_count,
        'draft_count': draft_count,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
        'paid_count': paid_count,
        'customers': customers,
        'salespersons': salespersons,
        'payment_methods': payment_methods,
        'search_query': search_query,
        'selected_customer': customer_id,
        'selected_salesperson': salesperson_id,
        'selected_payment_method': payment_method_id,
        'payment_status': payment_status,
        'payment_term': payment_term,
        'date_from': date_from,
        'date_to': date_to,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'is_posted': is_posted,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('بحث الفواتير'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/invoice_search.html', context)


@login_required
@permission_required_with_message('sales.view_quotation')
def quotation_comparison_report(request):
    """مقارنة عروض الأسعار - Quotation Comparison"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    customer_id = request.GET.get('customer')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    item_id = request.GET.get('item')

    # عروض الأسعار
    quotations = Quotation.objects.filter(
        company=company
    ).select_related('customer', 'salesperson', 'currency')

    if customer_id:
        quotations = quotations.filter(customer_id=customer_id)

    if date_from:
        quotations = quotations.filter(date__gte=date_from)

    if date_to:
        quotations = quotations.filter(date__lte=date_to)

    if status:
        quotations = quotations.filter(status=status)

    # الإحصائيات
    stats = quotations.aggregate(
        total_count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
        avg_amount=Coalesce(Avg('total_amount'), Decimal('0'))
    )

    # حسب الحالة
    by_status = quotations.values('status').annotate(
        count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0'))
    ).order_by('status')

    # حسب العميل
    by_customer = quotations.values(
        'customer__id',
        'customer__name',
        'customer__code'
    ).annotate(
        count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
        avg_amount=Coalesce(Avg('total_amount'), Decimal('0'))
    ).order_by('-total_amount')[:20]

    # حسب المندوب
    by_salesperson = quotations.filter(
        salesperson__isnull=False
    ).values(
        'salesperson__id',
        'salesperson__first_name',
        'salesperson__last_name'
    ).annotate(
        count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
        avg_amount=Coalesce(Avg('total_amount'), Decimal('0'))
    ).order_by('-count')

    # معدل التحويل (من عرض سعر إلى طلب)
    total_quotations = quotations.count()
    converted_quotations = quotations.filter(status='converted').count()
    conversion_rate = (converted_quotations / total_quotations * 100) if total_quotations > 0 else 0

    # البيانات للاختيارات
    customers = BusinessPartner.objects.filter(
        company=company,
        is_customer=True,
        is_active=True
    ).order_by('name')

    items = Item.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')[:100]

    context = {
        'title': _('مقارنة عروض الأسعار'),
        'quotations': quotations.order_by('-date', '-number')[:100],
        'stats': stats,
        'by_status': by_status,
        'by_customer': by_customer,
        'by_salesperson': by_salesperson,
        'conversion_rate': conversion_rate,
        'converted_quotations': converted_quotations,
        'total_quotations': total_quotations,
        'customers': customers,
        'items': items,
        'selected_customer': customer_id,
        'selected_item': item_id,
        'date_from': date_from,
        'date_to': date_to,
        'status': status,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('مقارنة عروض الأسعار'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/quotation_comparison.html', context)


@login_required
@permission_required_with_message('sales.view_salespersoncommission')
def commission_report(request):
    """تقرير عمولات المندوبين - Salesperson Commission Report"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('core:dashboard')

    company = request.current_company

    # الفلاتر
    salesperson_id = request.GET.get('salesperson')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    payment_status = request.GET.get('payment_status')

    # العمولات
    commissions = SalespersonCommission.objects.filter(
        company=company
    ).select_related(
        'salesperson',
        'invoice',
        'invoice__customer',
        'payment_voucher'
    )

    if salesperson_id:
        commissions = commissions.filter(salesperson_id=salesperson_id)

    if date_from:
        commissions = commissions.filter(calculation_date__gte=date_from)

    if date_to:
        commissions = commissions.filter(calculation_date__lte=date_to)

    if payment_status:
        commissions = commissions.filter(payment_status=payment_status)

    # الإحصائيات
    stats = commissions.aggregate(
        total_commissions=Count('id'),
        total_base_amount=Coalesce(Sum('base_amount'), Decimal('0')),
        total_commission_amount=Coalesce(Sum('commission_amount'), Decimal('0')),
        total_paid_amount=Coalesce(Sum('paid_amount'), Decimal('0')),
        total_remaining_amount=Coalesce(Sum('remaining_amount'), Decimal('0')),
        avg_commission_rate=Coalesce(Avg('commission_rate'), Decimal('0'))
    )

    # حسب المندوب
    from apps.hr.models import Employee
    salespersons = Employee.objects.filter(
        company=company,
        is_active=True
    ).order_by('first_name', 'last_name')

    salespersons_data = []
    for salesperson in salespersons:
        salesperson_commissions = commissions.filter(salesperson=salesperson)

        if salesperson_commissions.exists():
            sp_stats = salesperson_commissions.aggregate(
                commission_count=Count('id'),
                base_amount=Coalesce(Sum('base_amount'), Decimal('0')),
                commission_amount=Coalesce(Sum('commission_amount'), Decimal('0')),
                paid_amount=Coalesce(Sum('paid_amount'), Decimal('0')),
                remaining_amount=Coalesce(Sum('remaining_amount'), Decimal('0'))
            )

            salespersons_data.append({
                'salesperson': salesperson,
                'commission_count': sp_stats['commission_count'],
                'base_amount': sp_stats['base_amount'],
                'commission_amount': sp_stats['commission_amount'],
                'paid_amount': sp_stats['paid_amount'],
                'remaining_amount': sp_stats['remaining_amount'],
                'commissions': salesperson_commissions.order_by('-calculation_date')
            })

    # حسب حالة الدفع
    unpaid_commissions = commissions.filter(payment_status='unpaid').count()
    partial_commissions = commissions.filter(payment_status='partial').count()
    paid_commissions = commissions.filter(payment_status='paid').count()

    context = {
        'title': _('تقرير عمولات المندوبين'),
        'commissions': commissions.order_by('-calculation_date')[:200],
        'stats': stats,
        'salespersons_data': salespersons_data,
        'unpaid_commissions': unpaid_commissions,
        'partial_commissions': partial_commissions,
        'paid_commissions': paid_commissions,
        'salespersons': salespersons,
        'selected_salesperson': salesperson_id,
        'date_from': date_from,
        'date_to': date_to,
        'payment_status': payment_status,
        'today': datetime.now(),
        'breadcrumbs': [
            {'title': _('المبيعات'), 'url': reverse('core:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('عمولات المندوبين'), 'url': ''},
        ]
    }

    return render(request, 'sales/reports/commission_report.html', context)



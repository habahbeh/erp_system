# apps/sales/views/dashboard_views.py
"""
لوحة تحكم المبيعات - Sales Dashboard
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg, F, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal

from apps.core.decorators import permission_required_with_message
from ..models import (
    SalesInvoice, SalesOrder, Quotation,
    InvoiceItem, SalespersonCommission
)


@login_required
def sales_dashboard(request):
    """لوحة تحكم المبيعات"""

    company = request.current_company
    today = date.today()

    # الفترة الزمنية - آخر 30 يوم
    date_from = today - timedelta(days=30)

    # ==================== إحصائيات الفواتير ====================

    # جميع الفواتير في الفترة
    invoices = SalesInvoice.objects.filter(
        company=company,
        date__gte=date_from,
        date__lte=today
    )

    # إحصائيات الفواتير
    invoice_stats = invoices.aggregate(
        total_count=Count('id'),
        posted_count=Count('id', filter=Q(is_posted=True)),
        total_amount=Coalesce(Sum('total_with_tax'), Decimal('0')),
        total_paid=Coalesce(Sum('paid_amount'), Decimal('0')),
        total_remaining=Coalesce(Sum('remaining_amount'), Decimal('0')),
    )

    invoice_stats['draft_count'] = invoice_stats['total_count'] - invoice_stats['posted_count']

    # حساب نسبة التحصيل
    if invoice_stats['total_amount'] > 0:
        invoice_stats['collection_rate'] = (invoice_stats['total_paid'] / invoice_stats['total_amount']) * 100
    else:
        invoice_stats['collection_rate'] = 0

    # حساب نسب الفواتير
    if invoice_stats['total_count'] > 0:
        invoice_stats['posted_percentage'] = (invoice_stats['posted_count'] / invoice_stats['total_count']) * 100
        invoice_stats['draft_percentage'] = (invoice_stats['draft_count'] / invoice_stats['total_count']) * 100
    else:
        invoice_stats['posted_percentage'] = 0
        invoice_stats['draft_percentage'] = 0

    # ==================== إحصائيات أوامر البيع ====================

    orders = SalesOrder.objects.filter(
        company=company,
        date__gte=date_from,
        date__lte=today
    )

    order_stats = orders.aggregate(
        total_count=Count('id'),
        approved_count=Count('id', filter=Q(is_approved=True)),
        pending_count=Count('id', filter=Q(is_approved=False)),
        delivered_count=Count('id', filter=Q(is_delivered=True)),
        invoiced_count=Count('id', filter=Q(is_invoiced=True)),
    )

    # ==================== إحصائيات عروض الأسعار ====================

    quotations = Quotation.objects.filter(
        company=company,
        date__gte=date_from,
        date__lte=today
    )

    quotation_stats = quotations.aggregate(
        total_count=Count('id'),
        approved_count=Count('id', filter=Q(is_approved=True)),
        pending_count=Count('id', filter=Q(is_approved=False)),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0')),
    )

    # حساب نسبة التحويل (العروض المعتمدة من الإجمالي)
    if quotation_stats['total_count'] > 0:
        quotation_stats['conversion_rate'] = (quotation_stats['approved_count'] / quotation_stats['total_count']) * 100
    else:
        quotation_stats['conversion_rate'] = 0

    # ==================== أفضل المنتجات مبيعاً ====================

    top_products = InvoiceItem.objects.filter(
        invoice__company=company,
        invoice__date__gte=date_from,
        invoice__date__lte=today,
        invoice__is_posted=True
    ).values(
        'item__id',
        'item__code',
        'item__name',
    ).annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('subtotal')
    ).order_by('-total_amount')[:10]

    # ==================== أفضل العملاء ====================

    top_customers = SalesInvoice.objects.filter(
        company=company,
        date__gte=date_from,
        date__lte=today,
        is_posted=True
    ).values(
        'customer__id',
        'customer__code',
        'customer__name',
    ).annotate(
        invoice_count=Count('id'),
        total_amount=Sum('total_with_tax')
    ).order_by('-total_amount')[:10]

    # ==================== المبيعات حسب الشهر ====================

    # آخر 6 أشهر
    six_months_ago = today - timedelta(days=180)

    monthly_sales = SalesInvoice.objects.filter(
        company=company,
        date__gte=six_months_ago,
        date__lte=today,
        is_posted=True
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_amount=Sum('total_with_tax'),
        invoice_count=Count('id')
    ).order_by('month')

    # ==================== إحصائيات العمولات ====================

    commission_stats = SalespersonCommission.objects.filter(
        company=company,
        invoice__date__gte=date_from,
        invoice__date__lte=today
    ).aggregate(
        total_commissions=Coalesce(Sum('commission_amount'), Decimal('0')),
        paid_commissions=Coalesce(Sum('paid_amount'), Decimal('0')),
        pending_commissions=Coalesce(Sum('remaining_amount'), Decimal('0')),
    )

    # ==================== آخر الفواتير ====================

    recent_invoices = SalesInvoice.objects.filter(
        company=company
    ).select_related(
        'customer', 'payment_method', 'created_by'
    ).order_by('-created_at')[:10]

    # ==================== Breadcrumbs ====================

    breadcrumbs = [
        {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
        {'title': _('المبيعات'), 'url': '#'},
        {'title': _('لوحة المبيعات'), 'url': ''},
    ]

    context = {
        'title': _('لوحة تحكم المبيعات'),
        'breadcrumbs': breadcrumbs,
        'today': today,
        'date_from': date_from,

        # الإحصائيات
        'invoice_stats': invoice_stats,
        'order_stats': order_stats,
        'quotation_stats': quotation_stats,
        'pos_stats': pos_stats,
        'commission_stats': commission_stats,

        # البيانات
        'top_products': top_products,
        'top_customers': top_customers,
        'monthly_sales': monthly_sales,
        'active_campaigns': active_campaigns,
        'recent_invoices': recent_invoices,
    }

    return render(request, 'sales/dashboard.html', context)

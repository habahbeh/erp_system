# apps/inventory/report_views.py
"""
تقارير المخزون - بنفس أسلوب تقارير الأصول الثابتة
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, F, Case, When, DecimalField, Max, Min, Value
from django.db.models.functions import TruncMonth, TruncDate, Coalesce
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
import json

from .models import (
    ItemStock, StockMovement, StockIn, StockOut, StockTransfer,
    StockCount, Batch, StockReservation
)
from apps.core.models import Item, Warehouse, ItemCategory


# ==================== قائمة التقارير ====================

@login_required
def reports_list(request):
    """صفحة فهرس التقارير"""

    reports = [
        {
            'title': 'تقرير حالة المخزون',
            'description': 'تقرير شامل بحالة المخزون الحالي في جميع المستودعات',
            'icon': 'fas fa-boxes',
            'color': 'primary',
            'url': reverse('inventory:report_stock_status')
        },
        {
            'title': 'تقرير حركة المخزون',
            'description': 'تقرير تفصيلي بجميع حركات الإدخال والإخراج والتحويلات',
            'icon': 'fas fa-exchange-alt',
            'color': 'info',
            'url': reverse('inventory:report_stock_movement')
        },
        {
            'title': 'تقرير تقييم المخزون',
            'description': 'تقرير بقيمة المخزون الإجمالية وتوزيعها',
            'icon': 'fas fa-dollar-sign',
            'color': 'success',
            'url': reverse('inventory:report_stock_valuation')
        },
        {
            'title': 'تقرير المخزون المنخفض',
            'description': 'تقرير بالمواد التي وصلت أو قاربت الحد الأدنى',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning',
            'url': reverse('inventory:report_low_stock')
        },
        {
            'title': 'تقرير الدفعات والصلاحية',
            'description': 'تقرير بالدفعات المنتهية وقريبة الانتهاء',
            'icon': 'fas fa-calendar-times',
            'color': 'danger',
            'url': reverse('inventory:report_batch_expiry')
        },
    ]

    context = {
        'title': _('التقارير'),
        'reports': reports,
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/reports_list.html', context)


# ==================== 1. تقرير حالة المخزون ====================

@login_required
def stock_status_report(request):
    """تقرير حالة المخزون الحالي"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('inventory:dashboard')

    # الفلاتر
    warehouse_id = request.GET.get('warehouse', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock_status', '')  # all, in_stock, out_of_stock, low_stock

    # البيانات الأساسية
    stocks = ItemStock.objects.filter(
        company=request.current_company
    ).select_related('item', 'item__category', 'warehouse', 'item_variant')

    # تطبيق الفلاتر
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    if category_id:
        stocks = stocks.filter(item__category_id=category_id)

    if stock_status == 'in_stock':
        stocks = stocks.filter(quantity__gt=0)
    elif stock_status == 'out_of_stock':
        stocks = stocks.filter(quantity=0)
    elif stock_status == 'low_stock':
        stocks = stocks.filter(
            Q(quantity__lte=F('min_level')) & Q(min_level__isnull=False) & Q(quantity__gt=0)
        )

    # الإحصائيات العامة
    stats = stocks.aggregate(
        total_items=Count('id'),
        items_in_stock=Count('id', filter=Q(quantity__gt=0)),
        items_out_of_stock=Count('id', filter=Q(quantity=0)),
        items_low_stock=Count('id', filter=Q(quantity__lte=F('min_level')) & Q(min_level__isnull=False)),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField()),
        avg_cost=Avg('average_cost')
    )

    totals = {
        'total_items': stats.get('total_items') or 0,
        'items_in_stock': stats.get('items_in_stock') or 0,
        'items_out_of_stock': stats.get('items_out_of_stock') or 0,
        'items_low_stock': stats.get('items_low_stock') or 0,
        'total_quantity': stats.get('total_quantity') or Decimal('0'),
        'total_value': stats.get('total_value') or Decimal('0'),
        'avg_cost': stats.get('avg_cost') or Decimal('0')
    }

    # حسب المستودع
    by_warehouse = stocks.values(
        'warehouse__name'
    ).annotate(
        items_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField())
    ).order_by('-total_value')

    # حسب الفئة
    by_category = stocks.values(
        'item__category__name'
    ).annotate(
        items_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField())
    ).order_by('-total_value')

    # أعلى المواد قيمة
    top_items_by_value = stocks.order_by('-total_value')[:20]

    # المواد منخفضة المخزون
    low_stock_items = stocks.filter(
        Q(quantity__lte=F('min_level')) & Q(min_level__isnull=False)
    ).order_by('quantity')[:20]

    # للفلاتر
    warehouses = Warehouse.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    categories = ItemCategory.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    # سجلات المخزون للعرض
    stock_records = stocks.order_by('-total_value', 'item__name')[:100]

    context = {
        'title': _('تقرير حالة المخزون'),
        'stock_records': stock_records,
        'totals': totals,
        'by_warehouse': by_warehouse,
        'by_category': by_category,
        'top_items_by_value': top_items_by_value,
        'low_stock_items': low_stock_items,
        'warehouses': warehouses,
        'categories': categories,
        'selected_warehouse': warehouse_id,
        'selected_category': category_id,
        'selected_stock_status': stock_status,
        'today': timezone.now(),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''},
            {'title': _('تقرير حالة المخزون'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/stock_status_report.html', context)


# ==================== 2. تقرير حركة المخزون ====================

@login_required
def stock_movement_report(request):
    """تقرير حركة المخزون"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('inventory:dashboard')

    # الفلاتر
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    warehouse_id = request.GET.get('warehouse', '')
    item_id = request.GET.get('item', '')
    movement_type = request.GET.get('movement_type', '')

    # البيانات الأساسية
    movements = StockMovement.objects.filter(
        company=request.current_company
    ).select_related('item', 'warehouse', 'created_by')

    # تطبيق الفلاتر
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            movements = movements.filter(date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            movements = movements.filter(date__lte=date_to_obj)
        except ValueError:
            pass

    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)

    if item_id:
        movements = movements.filter(item_id=item_id)

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    # الإحصائيات العامة
    stats = movements.aggregate(
        total_movements=Count('id'),
        total_in=Count('id', filter=Q(movement_type__in=['in', 'transfer_in'])),
        total_out=Count('id', filter=Q(movement_type__in=['out', 'transfer_out'])),
        total_value_in=Sum('total_cost', filter=Q(quantity__gt=0)),
        total_value_out=Sum('total_cost', filter=Q(quantity__lt=0))
    )

    totals = {
        'total_movements': stats.get('total_movements') or 0,
        'total_in': stats.get('total_in') or 0,
        'total_out': stats.get('total_out') or 0,
        'total_value_in': abs(stats.get('total_value_in') or Decimal('0')),
        'total_value_out': abs(stats.get('total_value_out') or Decimal('0'))
    }

    # حسب النوع
    by_type = movements.values(
        'movement_type'
    ).annotate(
        count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum('total_cost')
    ).order_by('-count')

    # حسب المستودع
    by_warehouse = movements.values(
        'warehouse__name'
    ).annotate(
        count=Count('id'),
        total_in=Count('id', filter=Q(quantity__gt=0)),
        total_out=Count('id', filter=Q(quantity__lt=0))
    ).order_by('-count')

    # حسب اليوم - آخر 30 يوم
    by_date = movements.annotate(
        date_only=TruncDate('date')
    ).values('date_only').annotate(
        count=Count('id'),
        total_in=Count('id', filter=Q(quantity__gt=0)),
        total_out=Count('id', filter=Q(quantity__lt=0))
    ).order_by('-date_only')[:30]

    # للفلاتر
    warehouses = Warehouse.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    # سجلات الحركات للعرض
    movement_records = movements.order_by('-date', '-id')[:100]

    # بيانات الرسم البياني
    date_labels = [item['date_only'].strftime('%Y-%m-%d') if item['date_only'] else '' for item in by_date]
    date_in_counts = [item['total_in'] for item in by_date]
    date_out_counts = [item['total_out'] for item in by_date]

    context = {
        'title': _('تقرير حركة المخزون'),
        'movement_records': movement_records,
        'totals': totals,
        'by_type': by_type,
        'by_warehouse': by_warehouse,
        'by_date': by_date,
        'warehouses': warehouses,
        'date_from': date_from,
        'date_to': date_to,
        'selected_warehouse': warehouse_id,
        'selected_item': item_id,
        'selected_movement_type': movement_type,
        'date_labels': json.dumps(date_labels[::-1]),  # عكس الترتيب للرسم
        'date_in_counts': json.dumps(date_in_counts[::-1]),
        'date_out_counts': json.dumps(date_out_counts[::-1]),
        'today': timezone.now(),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''},
            {'title': _('تقرير حركة المخزون'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/stock_movement_report.html', context)


# ==================== 3. تقرير تقييم المخزون ====================

@login_required
def stock_valuation_report(request):
    """تقرير تقييم المخزون"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('inventory:dashboard')

    # الفلاتر
    warehouse_id = request.GET.get('warehouse', '')
    category_id = request.GET.get('category', '')

    # البيانات الأساسية
    stocks = ItemStock.objects.filter(
        company=request.current_company,
        quantity__gt=0
    ).select_related('item', 'item__category', 'warehouse')

    # تطبيق الفلاتر
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    if category_id:
        stocks = stocks.filter(item__category_id=category_id)

    # الإحصائيات العامة
    stats = stocks.aggregate(
        total_items=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField()),
        avg_unit_cost=Avg('average_cost'),
        max_value=Max(F('quantity') * F('average_cost'), output_field=DecimalField()),
        min_value=Min(F('quantity') * F('average_cost'), output_field=DecimalField())
    )

    totals = {
        'total_items': stats.get('total_items') or 0,
        'total_quantity': stats.get('total_quantity') or Decimal('0'),
        'total_value': stats.get('total_value') or Decimal('0'),
        'avg_unit_cost': stats.get('avg_unit_cost') or Decimal('0'),
        'max_value': stats.get('max_value') or Decimal('0'),
        'min_value': stats.get('min_value') or Decimal('0')
    }

    # حسب المستودع
    by_warehouse = stocks.values(
        'warehouse__name'
    ).annotate(
        items_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField())
    ).order_by('-total_value')

    # حسب الفئة
    by_category = stocks.values(
        'item__category__name'
    ).annotate(
        items_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('average_cost'), output_field=DecimalField())
    ).order_by('-total_value')

    # أعلى 20 مادة قيمة
    top_items = stocks.order_by('-total_value')[:20]

    # للفلاتر
    warehouses = Warehouse.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    categories = ItemCategory.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    # سجلات المخزون للعرض
    stock_records = stocks.order_by('-total_value')[:100]

    # بيانات الرسم البياني - حسب الفئة
    category_labels = [item['item__category__name'] or 'غير مصنف' for item in by_category[:10]]
    category_values = [float(item['total_value'] or 0) for item in by_category[:10]]

    context = {
        'title': _('تقرير تقييم المخزون'),
        'stock_records': stock_records,
        'totals': totals,
        'by_warehouse': by_warehouse,
        'by_category': by_category,
        'top_items': top_items,
        'warehouses': warehouses,
        'categories': categories,
        'selected_warehouse': warehouse_id,
        'selected_category': category_id,
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'today': timezone.now(),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''},
            {'title': _('تقرير تقييم المخزون'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/stock_valuation_report.html', context)


# ==================== 4. تقرير المخزون المنخفض ====================

@login_required
def low_stock_report(request):
    """تقرير المخزون المنخفض"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('inventory:dashboard')

    # الفلاتر
    warehouse_id = request.GET.get('warehouse', '')
    category_id = request.GET.get('category', '')
    alert_level = request.GET.get('alert_level', 'all')  # all, critical, warning

    # البيانات الأساسية - المواد التي لديها min_level محدد
    stocks = ItemStock.objects.filter(
        company=request.current_company,
        min_level__isnull=False
    ).select_related('item', 'item__category', 'warehouse')

    # تطبيق الفلاتر
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    if category_id:
        stocks = stocks.filter(item__category_id=category_id)

    if alert_level == 'critical':
        stocks = stocks.filter(quantity=0)
    elif alert_level == 'warning':
        stocks = stocks.filter(quantity__gt=0, quantity__lte=F('min_level'))
    else:  # all
        stocks = stocks.filter(quantity__lte=F('min_level'))

    # الإحصائيات العامة
    stats = stocks.aggregate(
        total_items=Count('id'),
        critical_items=Count('id', filter=Q(quantity=0)),
        warning_items=Count('id', filter=Q(quantity__gt=0) & Q(quantity__lte=F('min_level'))),
        total_shortage=Sum(F('min_level') - F('quantity'), output_field=DecimalField())
    )

    totals = {
        'total_items': stats.get('total_items') or 0,
        'critical_items': stats.get('critical_items') or 0,
        'warning_items': stats.get('warning_items') or 0,
        'total_shortage': stats.get('total_shortage') or Decimal('0')
    }

    # حسب المستودع
    by_warehouse = stocks.values(
        'warehouse__name'
    ).annotate(
        items_count=Count('id'),
        critical_count=Count('id', filter=Q(quantity=0)),
        warning_count=Count('id', filter=Q(quantity__gt=0) & Q(quantity__lte=F('min_level')))
    ).order_by('-items_count')

    # حسب الفئة
    by_category = stocks.values(
        'item__category__name'
    ).annotate(
        items_count=Count('id'),
        critical_count=Count('id', filter=Q(quantity=0)),
        warning_count=Count('id', filter=Q(quantity__gt=0) & Q(quantity__lte=F('min_level')))
    ).order_by('-items_count')

    # للفلاتر
    warehouses = Warehouse.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    categories = ItemCategory.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    # سجلات المخزون للعرض
    stock_records = stocks.annotate(
        shortage=F('min_level') - F('quantity')
    ).order_by('quantity', '-min_level')[:100]

    context = {
        'title': _('تقرير المخزون المنخفض'),
        'stock_records': stock_records,
        'totals': totals,
        'by_warehouse': by_warehouse,
        'by_category': by_category,
        'warehouses': warehouses,
        'categories': categories,
        'selected_warehouse': warehouse_id,
        'selected_category': category_id,
        'selected_alert_level': alert_level,
        'today': timezone.now(),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''},
            {'title': _('تقرير المخزون المنخفض'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/low_stock_report.html', context)


# ==================== 5. تقرير الدفعات والصلاحية ====================

@login_required
def batch_expiry_report(request):
    """تقرير الدفعات والصلاحية"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('inventory:dashboard')

    # الفلاتر
    warehouse_id = request.GET.get('warehouse', '')
    expiry_status = request.GET.get('expiry_status', 'all')  # all, expired, expiring_soon, active
    days_threshold = int(request.GET.get('days_threshold', '90'))

    # البيانات الأساسية
    batches = Batch.objects.filter(
        company=request.current_company,
        is_active=True,
        expiry_date__isnull=False
    ).select_related('item', 'warehouse')

    # تطبيق الفلاتر
    if warehouse_id:
        batches = batches.filter(warehouse_id=warehouse_id)

    today = timezone.now().date()

    if expiry_status == 'expired':
        batches = batches.filter(expiry_date__lt=today)
    elif expiry_status == 'expiring_soon':
        threshold_date = today + timedelta(days=days_threshold)
        batches = batches.filter(expiry_date__gte=today, expiry_date__lte=threshold_date)
    elif expiry_status == 'active':
        threshold_date = today + timedelta(days=days_threshold)
        batches = batches.filter(expiry_date__gt=threshold_date)

    # الإحصائيات العامة
    stats = batches.aggregate(
        total_batches=Count('id'),
        expired_batches=Count('id', filter=Q(expiry_date__lt=today)),
        expiring_soon=Count('id', filter=Q(expiry_date__gte=today) & Q(expiry_date__lte=today + timedelta(days=days_threshold))),
        total_quantity=Sum('quantity'),
        expired_quantity=Sum('quantity', filter=Q(expiry_date__lt=today)),
        total_value=Sum(F('quantity') * F('unit_cost'), output_field=DecimalField()),
        expired_value=Sum(F('quantity') * F('unit_cost'), filter=Q(expiry_date__lt=today), output_field=DecimalField())
    )

    totals = {
        'total_batches': stats.get('total_batches') or 0,
        'expired_batches': stats.get('expired_batches') or 0,
        'expiring_soon': stats.get('expiring_soon') or 0,
        'total_quantity': stats.get('total_quantity') or Decimal('0'),
        'expired_quantity': stats.get('expired_quantity') or Decimal('0'),
        'total_value': stats.get('total_value') or Decimal('0'),
        'expired_value': stats.get('expired_value') or Decimal('0')
    }

    # حسب المستودع
    by_warehouse = batches.values(
        'warehouse__name'
    ).annotate(
        batches_count=Count('id'),
        expired_count=Count('id', filter=Q(expiry_date__lt=today)),
        expiring_soon_count=Count('id', filter=Q(expiry_date__gte=today) & Q(expiry_date__lte=today + timedelta(days=days_threshold)))
    ).order_by('-batches_count')

    # للفلاتر
    warehouses = Warehouse.objects.filter(
        company=request.current_company,
        is_active=True
    ).order_by('name')

    # سجلات الدفعات للعرض
    batch_records = batches.order_by('expiry_date')[:100]

    context = {
        'title': _('تقرير الدفعات والصلاحية'),
        'batch_records': batch_records,
        'totals': totals,
        'by_warehouse': by_warehouse,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'selected_expiry_status': expiry_status,
        'days_threshold': days_threshold,
        'today': timezone.now(),
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المخازن'), 'url': reverse('inventory:dashboard')},
            {'title': _('التقارير'), 'url': ''},
            {'title': _('تقرير الدفعات والصلاحية'), 'url': ''}
        ],
    }

    return render(request, 'inventory/reports/batch_expiry_report.html', context)

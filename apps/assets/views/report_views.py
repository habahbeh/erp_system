# apps/assets/views/report_views.py
"""
Views التقارير
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, Avg, F, Max, Min
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import TruncMonth, TruncYear
import json
from datetime import date, timedelta
from decimal import Decimal
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, AssetDepreciation, AssetMaintenance,
    AssetTransaction, PhysicalCount, AssetInsurance
)


@login_required
@permission_required_with_message('assets.view_asset')
def asset_register_report(request):
    """تقرير سجل الأصول"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الفلاتر
    category = request.GET.get('category')
    branch = request.GET.get('branch')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    assets = Asset.objects.filter(
        company=request.current_company
    ).select_related('category', 'branch', 'condition')

    if category:
        assets = assets.filter(category_id=category)

    if branch:
        assets = assets.filter(branch_id=branch)

    if status:
        assets = assets.filter(status=status)

    if date_from:
        assets = assets.filter(acquisition_date__gte=date_from)

    if date_to:
        assets = assets.filter(acquisition_date__lte=date_to)

    # الإحصائيات
    stats = assets.aggregate(
        total_count=Count('id'),
        total_cost=Sum('acquisition_cost'),
        total_accumulated=Sum('accumulated_depreciation'),
        total_book_value=Sum(F('acquisition_cost') - F('accumulated_depreciation'))
    )

    # حسب الفئة
    by_category = assets.values(
        'category__name'
    ).annotate(
        count=Count('id'),
        total_cost=Sum('acquisition_cost'),
        total_book_value=Sum(F('acquisition_cost') - F('accumulated_depreciation'))
    ).order_by('-total_cost')

    # حسب الحالة
    by_status = assets.values('status').annotate(
        count=Count('id'),
        total_cost=Sum('acquisition_cost')
    ).order_by('-count')

    context = {
        'title': _('تقرير سجل الأصول'),
        'assets': assets.order_by('category', 'asset_number')[:100],
        'stats': stats,
        'by_category': by_category,
        'by_status': by_status,
        'categories': AssetCategory.objects.filter(is_active=True),
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('سجل الأصول'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/asset_register.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def depreciation_report(request):
    """تقرير الإهلاك"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الفلاتر
    year = request.GET.get('year', date.today().year)
    month = request.GET.get('month')
    category = request.GET.get('category')

    depreciation_records = AssetDepreciation.objects.filter(
        company=request.current_company,
        depreciation_date__year=year
    ).select_related('asset', 'asset__category')

    if month:
        depreciation_records = depreciation_records.filter(depreciation_date__month=month)

    if category:
        depreciation_records = depreciation_records.filter(asset__category_id=category)

    # الإحصائيات
    stats = depreciation_records.aggregate(
        total_depreciation=Sum('depreciation_amount'),
        total_accumulated=Sum('accumulated_depreciation_after'),
        count=Count('id')
    )

    # حسب الشهر
    by_month = depreciation_records.annotate(
        month=TruncMonth('depreciation_date')
    ).values('month').annotate(
        total=Sum('depreciation_amount'),
        count=Count('id')
    ).order_by('month')

    # حسب الفئة
    by_category = depreciation_records.values(
        'asset__category__name'
    ).annotate(
        total=Sum('depreciation_amount'),
        count=Count('id')
    ).order_by('-total')

    context = {
        'title': _('تقرير الإهلاك'),
        'records': depreciation_records.order_by('-depreciation_date')[:100],
        'stats': stats,
        'by_month': by_month,
        'by_category': by_category,
        'year': year,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('تقرير الإهلاك'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/depreciation_report.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def maintenance_report(request):
    """تقرير الصيانة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الفلاتر
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    asset = request.GET.get('asset')

    maintenances = AssetMaintenance.objects.filter(
        company=request.current_company
    ).select_related('asset', 'maintenance_type')

    if date_from:
        maintenances = maintenances.filter(scheduled_date__gte=date_from)

    if date_to:
        maintenances = maintenances.filter(scheduled_date__lte=date_to)

    if asset:
        maintenances = maintenances.filter(asset_id=asset)

    # الإحصائيات
    stats = maintenances.aggregate(
        total_cost=Sum(F('labor_cost') + F('parts_cost') + F('other_cost')),
        avg_cost=Avg(F('labor_cost') + F('parts_cost') + F('other_cost')),
        count=Count('id')
    )

    # حسب النوع
    by_type = maintenances.values(
        'maintenance_type__name'
    ).annotate(
        total_cost=Sum(F('labor_cost') + F('parts_cost') + F('other_cost')),
        count=Count('id')
    ).order_by('-total_cost')

    # حسب الأصل
    by_asset = maintenances.values(
        'asset__asset_number',
        'asset__name'
    ).annotate(
        total_cost=Sum(F('labor_cost') + F('parts_cost') + F('other_cost')),
        count=Count('id')
    ).order_by('-total_cost')[:10]

    context = {
        'title': _('تقرير الصيانة'),
        'maintenances': maintenances.order_by('-scheduled_date')[:100],
        'stats': stats,
        'by_type': by_type,
        'by_asset': by_asset,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('تقرير الصيانة'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/maintenance_report.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def asset_movement_report(request):
    """تقرير حركة الأصول"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الفلاتر
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    transaction_type = request.GET.get('transaction_type')

    transactions = AssetTransaction.objects.filter(
        company=request.current_company
    ).select_related('asset', 'business_partner')

    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)

    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # الإحصائيات
    stats = transactions.aggregate(
        total_amount=Sum('amount'),
        count=Count('id')
    )

    # حسب النوع
    by_type = transactions.values('transaction_type').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    ).order_by('-count')

    context = {
        'title': _('تقرير حركة الأصول'),
        'transactions': transactions.order_by('-transaction_date')[:100],
        'stats': stats,
        'by_type': by_type,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('حركة الأصول'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/movement_report.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def valuation_report(request):
    """تقرير تقييم الأصول"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    category = request.GET.get('category')
    branch = request.GET.get('branch')

    assets = Asset.objects.filter(
        company=request.current_company,
        status='active'
    ).select_related('category', 'branch')

    if category:
        assets = assets.filter(category_id=category)

    if branch:
        assets = assets.filter(branch_id=branch)

    # الإحصائيات
    stats = assets.aggregate(
        total_cost=Sum('acquisition_cost'),
        total_accumulated=Sum('accumulated_depreciation'),
        total_book_value=Sum(F('acquisition_cost') - F('accumulated_depreciation')),
        count=Count('id')
    )

    # حسب الفئة
    by_category = assets.values(
        'category__name'
    ).annotate(
        total_cost=Sum('acquisition_cost'),
        total_accumulated=Sum('accumulated_depreciation'),
        total_book_value=Sum(F('acquisition_cost') - F('accumulated_depreciation')),
        count=Count('id')
    ).order_by('-total_book_value')

    # حسب الفرع
    by_branch = assets.values(
        'branch__name'
    ).annotate(
        total_cost=Sum('acquisition_cost'),
        total_book_value=Sum(F('acquisition_cost') - F('accumulated_depreciation')),
        count=Count('id')
    ).order_by('-total_book_value')

    context = {
        'title': _('تقرير تقييم الأصول'),
        'assets': assets.order_by('-book_value')[:50],
        'stats': stats,
        'by_category': by_category,
        'by_branch': by_branch,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('تقييم الأصول'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/valuation_report.html', context)


@login_required
@permission_required_with_message('assets.can_conduct_physical_count')
def physical_count_report(request):
    """تقرير الجرد الفعلي"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الفلاتر
    cycle_id = request.GET.get('cycle')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    counts = PhysicalCount.objects.filter(
        company=request.current_company
    ).select_related('cycle', 'branch')

    if cycle_id:
        counts = counts.filter(cycle_id=cycle_id)

    if date_from:
        counts = counts.filter(count_date__gte=date_from)

    if date_to:
        counts = counts.filter(count_date__lte=date_to)

    # الإحصائيات
    stats = counts.aggregate(
        total_assets=Sum('total_assets'),
        total_counted=Sum('counted_assets'),
        total_variances=Sum('variance_count'),
        count=Count('id')
    )

    context = {
        'title': _('تقرير الجرد الفعلي'),
        'counts': counts.order_by('-count_date')[:50],
        'stats': stats,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': reverse('assets:reports')},
            {'title': _('الجرد الفعلي'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/physical_count_report.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def reports_dashboard(request):
    """لوحة التقارير"""

    context = {
        'title': _('التقارير'),
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': ''},
        ]
    }

    return render(request, 'assets/reports/dashboard.html', context)


# ==================== Export to Excel ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def export_asset_register_excel(request):
    """تصدير سجل الأصول إلى Excel"""

    try:
        assets = Asset.objects.filter(
            company=request.current_company
        ).select_related('category', 'branch', 'condition').order_by('category', 'asset_number')

        # إنشاء Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "سجل الأصول"

        # التنسيق
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # العناوين
        headers = [
            'رقم الأصل', 'الاسم', 'الفئة', 'الفرع', 'تاريخ الاقتناء',
            'تكلفة الاقتناء', 'الإهلاك المتراكم', 'القيمة الدفترية', 'الحالة'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # البيانات
        for row_num, asset in enumerate(assets, 2):
            ws.cell(row=row_num, column=1, value=asset.asset_number).border = border
            ws.cell(row=row_num, column=2, value=asset.name).border = border
            ws.cell(row=row_num, column=3, value=asset.category.name).border = border
            ws.cell(row=row_num, column=4, value=asset.branch.name if asset.branch else '').border = border
            ws.cell(row=row_num, column=5,
                    value=asset.acquisition_date.strftime('%Y-%m-%d') if asset.acquisition_date else '').border = border
            ws.cell(row=row_num, column=6, value=float(asset.acquisition_cost)).border = border
            ws.cell(row=row_num, column=7, value=float(asset.accumulated_depreciation)).border = border
            ws.cell(row=row_num, column=8, value=float(asset.book_value)).border = border
            ws.cell(row=row_num, column=9, value=asset.get_status_display()).border = border

        # تعديل عرض الأعمدة
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        # الحفظ
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="asset_register_{date.today()}.xlsx"'

        return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:asset_register_report')


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def export_depreciation_excel(request):
    """تصدير تقرير الإهلاك إلى Excel"""

    try:
        year = request.GET.get('year', date.today().year)

        records = AssetDepreciation.objects.filter(
            company=request.current_company,
            depreciation_date__year=year
        ).select_related('asset').order_by('depreciation_date')

        wb = Workbook()
        ws = wb.active
        ws.title = f"إهلاك {year}"

        # التنسيق
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # العناوين
        headers = [
            'التاريخ', 'رقم الأصل', 'اسم الأصل', 'مبلغ الإهلاك',
            'الإهلاك المتراكم', 'القيمة الدفترية'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # البيانات
        for row_num, record in enumerate(records, 2):
            ws.cell(row=row_num, column=1, value=record.depreciation_date.strftime('%Y-%m-%d')).border = border
            ws.cell(row=row_num, column=2, value=record.asset.asset_number).border = border
            ws.cell(row=row_num, column=3, value=record.asset.name).border = border
            ws.cell(row=row_num, column=4, value=float(record.depreciation_amount)).border = border
            ws.cell(row=row_num, column=5, value=float(record.accumulated_depreciation_after)).border = border
            ws.cell(row=row_num, column=6, value=float(record.book_value_after)).border = border

        # تعديل عرض الأعمدة
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        # الحفظ
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="depreciation_{year}.xlsx"'

        return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:depreciation_report')
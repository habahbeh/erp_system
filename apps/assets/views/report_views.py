# apps/assets/views/report_views.py
"""
Report Views - تقارير إدارة الأصول
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django.db.models import Q, Sum, Count, F, Case, When, DecimalField
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, datetime
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, AssetDepreciation, AssetTransaction,
    AssetMaintenance, AssetValuation, AssetTransfer
)
from .base_report_views import BaseAssetReportView, BaseAssetReportExportView


# ==================== Asset Register Report ====================

class AssetRegisterReportView(BaseAssetReportView):
    """تقرير سجل الأصول الكامل"""

    template_name = 'assets/reports/asset_register.html'
    report_title = 'سجل الأصول'

    def get_report_data(self):
        filters = self.get_report_filters()

        queryset = Asset.objects.filter(
            company=self.request.current_company
        ).select_related(
            'category', 'depreciation_method', 'condition',
            'cost_center', 'responsible_employee', 'supplier'
        )

        # تطبيق الفلاتر
        if filters['category_id']:
            queryset = queryset.filter(category_id=filters['category_id'])

        if filters['status']:
            queryset = queryset.filter(status=filters['status'])

        if filters['cost_center_id']:
            queryset = queryset.filter(cost_center_id=filters['cost_center_id'])

        if filters['date_from']:
            queryset = queryset.filter(purchase_date__gte=filters['date_from'])

        if filters['date_to']:
            queryset = queryset.filter(purchase_date__lte=filters['date_to'])

        queryset = queryset.order_by('category__code', 'asset_number')

        # حساب الإجماليات
        totals = queryset.aggregate(
            total_original_cost=Sum('original_cost'),
            total_accumulated_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
            count=Count('id')
        )

        return {
            'assets': queryset,
            'totals': totals
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة قوائم للفلاتر
        from apps.accounting.models import CostCenter
        context['categories'] = AssetCategory.objects.filter(
            company=self.request.current_company
        ).order_by('code')
        context['cost_centers'] = CostCenter.objects.filter(
            company=self.request.current_company
        ).order_by('code')
        context['status_choices'] = Asset.STATUS_CHOICES

        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('سجل الأصول'), 'url': ''}
        ]

        return context


@login_required
@permission_required_with_message('assets.view_asset')
def export_asset_register(request):
    """تصدير سجل الأصول إلى Excel"""

    try:
        company = request.current_company

        # الفلاتر
        category_id = request.GET.get('category_id', '')
        status = request.GET.get('status', '')
        cost_center_id = request.GET.get('cost_center_id', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # البيانات
        queryset = Asset.objects.filter(company=company).select_related(
            'category', 'depreciation_method', 'condition',
            'cost_center', 'responsible_employee'
        )

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if status:
            queryset = queryset.filter(status=status)
        if cost_center_id:
            queryset = queryset.filter(cost_center_id=cost_center_id)
        if date_from:
            queryset = queryset.filter(purchase_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(purchase_date__lte=date_to)

        queryset = queryset.order_by('category__code', 'asset_number')

        # إنشاء Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "سجل الأصول"

        # التنسيق
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        title_font = Font(bold=True, size=14, color="366092")
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )

        # العنوان
        ws.merge_cells('A1:M1')
        ws['A1'] = f"سجل الأصول - {company.name}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        ws.merge_cells('A2:M2')
        ws['A2'] = f"تاريخ التقرير: {date.today().strftime('%Y-%m-%d')}"
        ws['A2'].font = Font(size=10)
        ws['A2'].alignment = Alignment(horizontal='center')

        # العناوين
        headers = [
            'رقم الأصل', 'اسم الأصل', 'الفئة', 'تاريخ الشراء',
            'التكلفة الأصلية', 'الإهلاك المتراكم', 'القيمة الدفترية',
            'طريقة الإهلاك', 'الحالة', 'مركز التكلفة',
            'المسؤول', 'الموقع', 'الحالة'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # البيانات
        row_num = 5
        total_cost = Decimal('0.00')
        total_depreciation = Decimal('0.00')
        total_book_value = Decimal('0.00')

        for asset in queryset:
            data = [
                asset.asset_number,
                asset.name,
                asset.category.name,
                asset.purchase_date.strftime('%Y-%m-%d'),
                float(asset.original_cost),
                float(asset.accumulated_depreciation),
                float(asset.book_value),
                asset.depreciation_method.name,
                asset.condition.name if asset.condition else '--',
                asset.cost_center.name if asset.cost_center else '--',
                asset.responsible_employee.get_full_name() if asset.responsible_employee else '--',
                asset.physical_location or '--',
                asset.get_status_display()
            ]

            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')

                # تنسيق الأرقام
                if col_num in [5, 6, 7]:
                    cell.number_format = '#,##0.000'

            total_cost += asset.original_cost
            total_depreciation += asset.accumulated_depreciation
            total_book_value += asset.book_value
            row_num += 1

        # الإجمالي
        ws.merge_cells(f'A{row_num}:D{row_num}')
        total_cell = ws.cell(row=row_num, column=1)
        total_cell.value = "الإجمالي"
        total_cell.font = Font(bold=True, size=11)
        total_cell.fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")
        total_cell.alignment = Alignment(horizontal='center')
        total_cell.border = thin_border

        for col in range(2, 5):
            ws.cell(row=row_num, column=col).border = thin_border
            ws.cell(row=row_num, column=col).fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF",
                                                                fill_type="solid")

        # قيم الإجمالي
        totals = [float(total_cost), float(total_depreciation), float(total_book_value)]
        for col_num, value in enumerate(totals, 5):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")
            cell.number_format = '#,##0.000'
            cell.border = thin_border

        # ضبط العرض
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 20
        ws.column_dimensions['I'].width = 15
        ws.column_dimensions['J'].width = 20
        ws.column_dimensions['K'].width = 20
        ws.column_dimensions['L'].width = 25
        ws.column_dimensions['M'].width = 12

        # الاستجابة
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"asset_register_{date.today().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:asset_register_report')


# ==================== Depreciation Report ====================

class DepreciationReportView(BaseAssetReportView):
    """تقرير الإهلاك"""

    template_name = 'assets/reports/depreciation_report.html'
    report_title = 'تقرير الإهلاك'

    def get_report_data(self):
        filters = self.get_report_filters()

        queryset = AssetDepreciation.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'asset__category', 'fiscal_year', 'period')

        # تطبيق الفلاتر
        if filters['date_from']:
            queryset = queryset.filter(depreciation_date__gte=filters['date_from'])

        if filters['date_to']:
            queryset = queryset.filter(depreciation_date__lte=filters['date_to'])

        if filters['category_id']:
            queryset = queryset.filter(asset__category_id=filters['category_id'])

        queryset = queryset.order_by('-depreciation_date', 'asset__asset_number')

        # الإجماليات
        totals = queryset.aggregate(
            total_depreciation=Sum('depreciation_amount'),
            count=Count('id')
        )

        # حسب الفئة
        by_category = queryset.values(
            'asset__category__name'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('-total')

        return {
            'records': queryset,
            'totals': totals,
            'by_category': by_category
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = AssetCategory.objects.filter(
            company=self.request.current_company
        ).order_by('code')

        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('تقرير الإهلاك'), 'url': ''}
        ]

        return context


@login_required
@permission_required_with_message('assets.view_assetdepreciation')
def export_depreciation_report(request):
    """تصدير تقرير الإهلاك"""

    try:
        company = request.current_company

        # الفلاتر
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        category_id = request.GET.get('category_id', '')

        # البيانات
        queryset = AssetDepreciation.objects.filter(
            company=company
        ).select_related('asset', 'asset__category', 'fiscal_year')

        if date_from:
            queryset = queryset.filter(depreciation_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(depreciation_date__lte=date_to)
        if category_id:
            queryset = queryset.filter(asset__category_id=category_id)

        queryset = queryset.order_by('-depreciation_date')

        # إنشاء Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "تقرير الإهلاك"

        # التنسيق
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="198754", end_color="198754", fill_type="solid")
        title_font = Font(bold=True, size=14)
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )

        # العنوان
        ws.merge_cells('A1:H1')
        ws['A1'] = f"تقرير الإهلاك - {company.name}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        # الفترة
        period_text = f"من {date_from} إلى {date_to}" if date_from and date_to else "جميع الفترات"
        ws.merge_cells('A2:H2')
        ws['A2'] = period_text
        ws['A2'].alignment = Alignment(horizontal='center')

        # العناوين
        headers = [
            'التاريخ', 'رقم الأصل', 'اسم الأصل', 'الفئة',
            'مبلغ الإهلاك', 'الإهلاك المتراكم', 'القيمة الدفترية', 'السنة المالية'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        # البيانات
        row_num = 5
        total_depreciation = Decimal('0.00')

        for record in queryset:
            data = [
                record.depreciation_date.strftime('%Y-%m-%d'),
                record.asset.asset_number,
                record.asset.name,
                record.asset.category.name,
                float(record.depreciation_amount),
                float(record.accumulated_depreciation_after),
                float(record.book_value_after),
                record.fiscal_year.name if record.fiscal_year else '--'
            ]

            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center')

                if col_num in [5, 6, 7]:
                    cell.number_format = '#,##0.000'

            total_depreciation += record.depreciation_amount
            row_num += 1

        # الإجمالي
        ws.merge_cells(f'A{row_num}:D{row_num}')
        ws.cell(row=row_num, column=1).value = "الإجمالي"
        ws.cell(row=row_num, column=1).font = Font(bold=True)
        ws.cell(row=row_num, column=5).value = float(total_depreciation)
        ws.cell(row=row_num, column=5).font = Font(bold=True)
        ws.cell(row=row_num, column=5).number_format = '#,##0.000'

        # ضبط العرض
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 18

        # الاستجابة
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"depreciation_report_{date.today().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:depreciation_report')


# ==================== Asset Movement Report ====================

class AssetMovementReportView(BaseAssetReportView):
    """تقرير حركة الأصول"""

    template_name = 'assets/reports/asset_movement_report.html'
    report_title = 'تقرير حركة الأصول'

    def get_report_data(self):
        filters = self.get_report_filters()

        queryset = AssetTransaction.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'asset__category', 'business_partner')

        if filters['date_from']:
            queryset = queryset.filter(transaction_date__gte=filters['date_from'])

        if filters['date_to']:
            queryset = queryset.filter(transaction_date__lte=filters['date_to'])

        queryset = queryset.order_by('-transaction_date')

        # الإجماليات حسب النوع
        by_type = queryset.values('transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

        return {
            'transactions': queryset,
            'by_type': by_type
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('حركة الأصول'), 'url': ''}
        ]

        return context


@login_required
@permission_required_with_message('assets.view_assettransaction')
def export_asset_movement_report(request):
    """تصدير تقرير حركة الأصول"""

    try:
        company = request.current_company
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        queryset = AssetTransaction.objects.filter(
            company=company
        ).select_related('asset', 'business_partner')

        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)

        queryset = queryset.order_by('-transaction_date')

        # إنشاء Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "حركة الأصول"

        # التنسيق
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0d6efd", end_color="0d6efd", fill_type="solid")
        title_font = Font(bold=True, size=14)

        # العنوان
        ws.merge_cells('A1:G1')
        ws['A1'] = f"تقرير حركة الأصول - {company.name}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        # العناوين
        headers = [
            'رقم العملية', 'التاريخ', 'نوع العملية',
            'الأصل', 'المبلغ', 'الطرف الآخر', 'الحالة'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        # البيانات
        row_num = 5
        for trans in queryset:
            data = [
                trans.transaction_number,
                trans.transaction_date.strftime('%Y-%m-%d'),
                trans.get_transaction_type_display(),
                f"{trans.asset.asset_number} - {trans.asset.name}",
                float(trans.amount),
                trans.business_partner.name if trans.business_partner else '--',
                trans.get_status_display()
            ]

            for col_num, value in enumerate(data, 1):
                ws.cell(row=row_num, column=col_num, value=value)

            row_num += 1

        # ضبط العرض
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            ws.column_dimensions[col].width = 20

        # الاستجابة
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"asset_movement_{date.today().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:asset_movement_report')


# ==================== Maintenance Report ====================

class MaintenanceReportView(BaseAssetReportView):
    """تقرير الصيانة"""

    template_name = 'assets/reports/maintenance_report.html'
    report_title = 'تقرير الصيانة'
    permission_required = 'assets.view_assetmaintenance'

    def get_report_data(self):
        filters = self.get_report_filters()

        queryset = AssetMaintenance.objects.filter(
            company=self.request.current_company
        ).select_related('asset', 'asset__category', 'maintenance_type')

        if filters['date_from']:
            queryset = queryset.filter(scheduled_date__gte=filters['date_from'])

        if filters['date_to']:
            queryset = queryset.filter(scheduled_date__lte=filters['date_to'])

        if filters['category_id']:
            queryset = queryset.filter(asset__category_id=filters['category_id'])

        queryset = queryset.order_by('-scheduled_date')

        # الإجماليات
        totals = queryset.aggregate(
            total_cost=Sum('total_cost'),
            labor_cost=Sum('labor_cost'),
            parts_cost=Sum('parts_cost'),
            count=Count('id')
        )

        # حسب النوع
        by_category = queryset.values('maintenance_category').annotate(
            total=Sum('total_cost'),
            count=Count('id')
        )

        return {
            'maintenances': queryset,
            'totals': totals,
            'by_category': by_category
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = AssetCategory.objects.filter(
            company=self.request.current_company
        ).order_by('code')

        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
            {'title': _('التقارير'), 'url': '#'},
            {'title': _('تقرير الصيانة'), 'url': ''}
        ]

        return context


@login_required
@permission_required_with_message('assets.view_assetmaintenance')
def export_maintenance_report(request):
    """تصدير تقرير الصيانة"""

    try:
        company = request.current_company
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        queryset = AssetMaintenance.objects.filter(
            company=company
        ).select_related('asset', 'maintenance_type')

        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)

        queryset = queryset.order_by('-scheduled_date')

        # إنشاء Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "تقرير الصيانة"

        # التنسيق
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="6f42c1", end_color="6f42c1", fill_type="solid")
        title_font = Font(bold=True, size=14)

        # العنوان
        ws.merge_cells('A1:I1')
        ws['A1'] = f"تقرير الصيانة - {company.name}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        # العناوين
        headers = [
            'رقم الصيانة', 'التاريخ', 'الأصل', 'نوع الصيانة',
            'التصنيف', 'تكلفة العمالة', 'تكلفة القطع', 'التكلفة الكلية', 'الحالة'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        # البيانات
        row_num = 5
        total_cost = Decimal('0.00')

        for maint in queryset:
            data = [
                maint.maintenance_number,
                maint.scheduled_date.strftime('%Y-%m-%d'),
                f"{maint.asset.asset_number} - {maint.asset.name}",
                maint.maintenance_type.name,
                maint.get_maintenance_category_display(),
                float(maint.labor_cost),
                float(maint.parts_cost),
                float(maint.total_cost),
                maint.get_status_display()
            ]

            for col_num, value in enumerate(data, 1):
                ws.cell(row=row_num, column=col_num, value=value)

            total_cost += maint.total_cost
            row_num += 1

        # الإجمالي
        ws.merge_cells(f'A{row_num}:G{row_num}')
        ws.cell(row=row_num, column=1).value = "الإجمالي"
        ws.cell(row=row_num, column=1).font = Font(bold=True)
        ws.cell(row=row_num, column=8).value = float(total_cost)
        ws.cell(row=row_num, column=8).font = Font(bold=True)

        # ضبط العرض
        for col in range(1, 10):
            ws.column_dimensions[get_column_letter(col)].width = 18

        # الاستجابة
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"maintenance_report_{date.today().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'خطأ في التصدير: {str(e)}')
        return redirect('assets:maintenance_report')
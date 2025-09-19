# apps/accounting/views/report_views.py
"""
Report Views - تقارير التصدير والاستيراد
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from apps.core.decorators import permission_required_with_message, company_required
from apps.core.models import Currency
from ..models import Account, AccountType
from ..forms.account_forms import AccountImportForm


@login_required
@permission_required_with_message('accounting.view_accounttype')
def export_account_types(request):
    """تصدير أنواع الحسابات إلى Excel"""

    wb = Workbook()
    ws = wb.active
    ws.title = "أنواع الحسابات"

    # تنسيق الرأس
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # إضافة الرأس
    headers = ['الرمز', 'الاسم', 'التصنيف', 'الرصيد الطبيعي']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # إضافة البيانات
    for row, account_type in enumerate(AccountType.objects.order_by('code'), 2):
        ws.cell(row=row, column=1, value=account_type.code).border = thin_border
        ws.cell(row=row, column=2, value=account_type.name).border = thin_border
        ws.cell(row=row, column=3, value=account_type.get_type_category_display()).border = thin_border
        ws.cell(row=row, column=4, value=account_type.get_normal_balance_display()).border = thin_border

    # تعديل عرض الأعمدة
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # إعداد الاستجابة
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="account_types.xlsx"'

    wb.save(response)
    return response


@company_required
@login_required
@permission_required_with_message('accounting.view_account')
def export_accounts(request):
    """تصدير الحسابات إلى Excel"""

    company = request.current_company

    wb = Workbook()
    ws = wb.active
    ws.title = "دليل الحسابات"

    # تنسيق الرأس
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # إضافة الرأس
    headers = [
        'رمز الحساب', 'اسم الحساب', 'الاسم الإنجليزي', 'نوع الحساب',
        'الحساب الأب', 'العملة', 'طبيعة الحساب', 'الرصيد الافتتاحي',
        'المستوى', 'حساب نقدي', 'حساب بنكي', 'يقبل قيود', 'الحالة'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # إضافة البيانات
    queryset = Account.objects.filter(
        company=company
    ).select_related('account_type', 'parent', 'currency').order_by('code')

    for row, account in enumerate(queryset, 2):
        data = [
            account.code,
            account.name,
            account.name_en or '',
            account.account_type.name,
            account.parent.name if account.parent else '',
            account.currency.name,
            account.get_nature_display(),
            float(account.opening_balance),
            account.level,
            'نعم' if account.is_cash_account else 'لا',
            'نعم' if account.is_bank_account else 'لا',
            'نعم' if account.accept_entries else 'لا',
            'موقوف' if account.is_suspended else 'نشط'
        ]

        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value).border = thin_border

    # تعديل عرض الأعمدة
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # إعداد الاستجابة
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="accounts_{company.name}.xlsx"'

    wb.save(response)
    return response


@login_required
@permission_required_with_message('accounting.add_accounttype')
def import_account_types(request):
    """استيراد أنواع الحسابات"""

    if request.method == 'POST':
        # منطق الاستيراد هنا
        pass

    return redirect('accounting:account_type_list')


@company_required
@login_required
@permission_required_with_message('accounting.add_account')
def import_accounts(request):
    """استيراد الحسابات"""

    if request.method == 'POST':
        # منطق الاستيراد هنا
        pass

    return redirect('accounting:account_list')
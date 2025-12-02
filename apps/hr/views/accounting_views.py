# apps/hr/views/accounting_views.py
"""
التكامل المحاسبي للموارد البشرية - المرحلة الخامسة
HR Accounting Integration Views - Phase 5

ملاحظة: تم تبسيط هذه الـ Views للعمل مع بنية قاعدة البيانات الحالية
حيث أن PayrollAccountMapping يحتوي على:
- component: نوع المكون (basic_salary, allowances, etc)
- account: الحساب المرتبط
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from decimal import Decimal

from ..models import (
    Payroll, PayrollDetail, HRSettings, PayrollAccountMapping,
    Advance, AdvanceInstallment
)

# استيراد نماذج المحاسبة إذا كانت متوفرة
try:
    from apps.accounting.models import (
        JournalEntry, JournalEntryLine, Account, AccountingPeriod
    )
    ACCOUNTING_AVAILABLE = True
except ImportError:
    ACCOUNTING_AVAILABLE = False


class AccountingIntegrationDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """لوحة تحكم التكامل المحاسبي"""
    template_name = 'hr/accounting/integration_dashboard.html'
    permission_required = 'hr.view_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.current_company

        # الربط المحاسبي - استخدام component بدلاً من item_type
        mappings = PayrollAccountMapping.objects.filter(
            company=company,
            is_active=True
        ).select_related('account')

        # أنواع الربط المطلوبة
        required_components = [
            ('basic_salary', 'الراتب الأساسي'),
            ('allowances', 'البدلات'),
            ('deductions', 'الخصومات'),
            ('net_salary', 'صافي الراتب'),
            ('social_security', 'الضمان الاجتماعي'),
            ('advance', 'السلف'),
        ]

        existing_components = set(mappings.values_list('component', flat=True))
        missing_mappings = [
            (code, name) for code, name in required_components
            if code not in existing_components
        ]

        # كشوفات الرواتب المعتمدة
        payrolls_approved = Payroll.objects.filter(
            company=company,
            status__in=['approved', 'paid']
        ).count()

        # السلف المصروفة
        advances_disbursed = Advance.objects.filter(
            employee__company=company,
            status='disbursed'
        ).count()

        context.update({
            'title': _('التكامل المحاسبي'),
            'mappings': mappings,
            'missing_mappings': missing_mappings,
            'mapping_complete': len(missing_mappings) == 0,
            'payrolls_approved': payrolls_approved,
            'advances_disbursed': advances_disbursed,
            'accounting_available': ACCOUNTING_AVAILABLE,
            'required_components': required_components,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('التكامل المحاسبي'), 'url': None},
            ],
        })
        return context


class PayrollJournalEntryView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """عرض القيد المحاسبي لمسير الرواتب"""
    template_name = 'hr/accounting/payroll_journal_entry.html'
    permission_required = 'hr.view_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=self.request.current_company
        )

        company = self.request.current_company

        # الحصول على الربط المحاسبي
        mappings = PayrollAccountMapping.objects.filter(
            company=company,
            is_active=True
        ).select_related('account')
        mapping_dict = {m.component: m for m in mappings}

        # بناء بنود القيد المقترحة
        journal_lines = []

        # الراتب الأساسي (مدين)
        if payroll.total_basic and 'basic_salary' in mapping_dict:
            journal_lines.append({
                'description': _('الرواتب الأساسية'),
                'account': mapping_dict['basic_salary'].account,
                'debit': payroll.total_basic,
                'credit': Decimal('0'),
            })

        # البدلات (مدين)
        if payroll.total_allowances and 'allowances' in mapping_dict:
            journal_lines.append({
                'description': _('البدلات'),
                'account': mapping_dict['allowances'].account,
                'debit': payroll.total_allowances,
                'credit': Decimal('0'),
            })

        # صافي الراتب المستحق (دائن)
        if payroll.total_net and 'net_salary' in mapping_dict:
            journal_lines.append({
                'description': _('الرواتب المستحقة'),
                'account': mapping_dict['net_salary'].account,
                'debit': Decimal('0'),
                'credit': payroll.total_net,
            })

        # الخصومات (دائن)
        if payroll.total_deductions and 'deductions' in mapping_dict:
            journal_lines.append({
                'description': _('الخصومات'),
                'account': mapping_dict['deductions'].account,
                'debit': Decimal('0'),
                'credit': payroll.total_deductions,
            })

        total_debit = sum([line['debit'] for line in journal_lines])
        total_credit = sum([line['credit'] for line in journal_lines])

        context.update({
            'title': _('القيد المحاسبي للرواتب'),
            'payroll': payroll,
            'journal_lines': journal_lines,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': abs(total_debit - total_credit) < Decimal('0.01'),
            'accounting_available': ACCOUNTING_AVAILABLE,
            'has_mappings': mappings.exists(),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': '/hr/payroll/'},
                {'title': payroll.number, 'url': f'/hr/payroll/{payroll.pk}/'},
                {'title': _('القيد المحاسبي'), 'url': None},
            ],
        })
        return context


class PayrollPaymentJournalView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """عرض قيد صرف الرواتب"""
    template_name = 'hr/accounting/payroll_payment_journal.html'
    permission_required = 'hr.view_payroll'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = get_object_or_404(
            Payroll,
            pk=self.kwargs['pk'],
            company=self.request.current_company
        )

        company = self.request.current_company
        mappings = PayrollAccountMapping.objects.filter(
            company=company,
            is_active=True
        ).select_related('account')
        mapping_dict = {m.component: m for m in mappings}

        journal_lines = []

        # صافي الراتب (مدين - إلغاء الالتزام)
        if payroll.total_net and 'net_salary' in mapping_dict:
            journal_lines.append({
                'description': _('صرف الرواتب المستحقة'),
                'account': mapping_dict['net_salary'].account,
                'debit': payroll.total_net,
                'credit': Decimal('0'),
            })

        # سيتم إضافة حساب البنك/الصندوق لاحقاً

        total_debit = sum([line['debit'] for line in journal_lines])
        total_credit = sum([line['credit'] for line in journal_lines])

        context.update({
            'title': _('قيد صرف الرواتب'),
            'payroll': payroll,
            'journal_lines': journal_lines,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': abs(total_debit - total_credit) < Decimal('0.01'),
            'accounting_available': ACCOUNTING_AVAILABLE,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('كشوفات الرواتب'), 'url': '/hr/payroll/'},
                {'title': payroll.number, 'url': f'/hr/payroll/{payroll.pk}/'},
                {'title': _('قيد الصرف'), 'url': None},
            ],
        })
        return context


class AdvanceJournalEntryView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """عرض القيد المحاسبي للسلفة"""
    template_name = 'hr/accounting/advance_journal_entry.html'
    permission_required = 'hr.view_advance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        advance = get_object_or_404(
            Advance,
            pk=self.kwargs['pk'],
            employee__company=self.request.current_company
        )

        company = self.request.current_company
        mappings = PayrollAccountMapping.objects.filter(
            company=company,
            is_active=True
        ).select_related('account')
        mapping_dict = {m.component: m for m in mappings}

        journal_lines = []

        # سلفة الموظفين (مدين)
        if 'advance' in mapping_dict:
            journal_lines.append({
                'description': f"سلفة للموظف {advance.employee}",
                'account': mapping_dict['advance'].account,
                'debit': advance.amount,
                'credit': Decimal('0'),
            })

        total_debit = sum([line['debit'] for line in journal_lines])
        total_credit = sum([line['credit'] for line in journal_lines])

        context.update({
            'title': _('القيد المحاسبي للسلفة'),
            'advance': advance,
            'journal_lines': journal_lines,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': abs(total_debit - total_credit) < Decimal('0.01'),
            'accounting_available': ACCOUNTING_AVAILABLE,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': '/'},
                {'title': _('الموارد البشرية'), 'url': '/hr/'},
                {'title': _('السلف'), 'url': '/hr/advances/'},
                {'title': str(advance), 'url': f'/hr/advances/{advance.pk}/'},
                {'title': _('القيد المحاسبي'), 'url': None},
            ],
        })
        return context


# Export views
__all__ = [
    'AccountingIntegrationDashboardView',
    'PayrollJournalEntryView',
    'PayrollPaymentJournalView',
    'AdvanceJournalEntryView',
]

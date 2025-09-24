# apps/accounting/views/dashboard.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta
from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message
from ..models import Account, JournalEntry, PaymentVoucher, ReceiptVoucher, AccountType


class AccountingDashboardView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """لوحة المحاسبة المحسنة"""
    template_name = 'accounting/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'لوحة المحاسبة',
        })
        return context


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API endpoint للحصول على إحصائيات الداشبورد"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    company = request.current_company
    today = date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    try:
        # إحصائيات الحسابات
        accounts_stats = Account.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_suspended=False)),
            suspended=Count('id', filter=Q(is_suspended=True)),
            leaf_accounts=Count('id', filter=Q(children__isnull=True))
        )

        # إحصائيات القيود
        entries_stats = JournalEntry.objects.filter(company=company).aggregate(
            total=Count('id'),
            monthly=Count('id', filter=Q(entry_date__gte=month_start)),
            yearly=Count('id', filter=Q(entry_date__gte=year_start)),
            draft=Count('id', filter=Q(status='draft')),
            posted=Count('id', filter=Q(status='posted')),
            monthly_posted=Count('id', filter=Q(
                status='posted',
                entry_date__gte=month_start
            ))
        )

        # إحصائيات السندات
        payment_vouchers = PaymentVoucher.objects.filter(company=company).aggregate(
            total=Count('id'),
            monthly=Count('id', filter=Q(date__gte=month_start)),
            monthly_amount=Sum('amount', filter=Q(date__gte=month_start, status='posted')) or 0,
            posted=Count('id', filter=Q(status='posted'))
        )

        receipt_vouchers = ReceiptVoucher.objects.filter(company=company).aggregate(
            total=Count('id'),
            monthly=Count('id', filter=Q(date__gte=month_start)),
            monthly_amount=Sum('amount', filter=Q(date__gte=month_start, status='posted')) or 0,
            posted=Count('id', filter=Q(status='posted'))
        )

        # إحصائيات حسب نوع الحساب
        accounts_by_type = list(AccountType.objects.annotate(
            accounts_count=Count('accounts', filter=Q(accounts__company=company))
        ).values('name', 'accounts_count', 'type_category')[:5])

        return JsonResponse({
            'success': True,
            'stats': {
                'accounts': accounts_stats,
                'entries': entries_stats,
                'payment_vouchers': payment_vouchers,
                'receipt_vouchers': receipt_vouchers,
                'accounts_by_type': accounts_by_type,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في تحميل الإحصائيات: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('accounting.view_journalentry')
@require_http_methods(["GET"])
def recent_entries_api(request):
    """API endpoint لآخر القيود"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    company = request.current_company
    limit = int(request.GET.get('limit', 5))

    try:
        # آخر القيود
        recent_entries = JournalEntry.objects.filter(
            company=company
        ).select_related('created_by', 'fiscal_year').order_by('-entry_date', '-created_at')[:limit]

        entries_data = []
        for entry in recent_entries:
            entries_data.append({
                'id': entry.pk,
                'number': entry.number,
                'date': entry.entry_date.strftime('%Y/%m/%d'),
                'description': entry.description,
                'total_debit': float(entry.total_debit),
                'total_credit': float(entry.total_credit),
                'status': entry.status,
                'status_display': entry.get_status_display(),
                'entry_type': entry.get_entry_type_display(),
                'created_by': entry.created_by.get_full_name() if entry.created_by else 'غير محدد',
                'created_at': entry.created_at.strftime('%Y/%m/%d %H:%M') if entry.created_at else '',
                'url': f'/accounting/journal-entries/{entry.pk}/',
                'can_edit': entry.can_edit(),
                'can_post': entry.can_post(),
                'can_unpost': entry.can_unpost(),
            })

        return JsonResponse({
            'success': True,
            'entries': entries_data,
            'count': len(entries_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في تحميل القيود: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('accounting.view_account')
@require_http_methods(["GET"])
def quick_tasks_api(request):
    """API endpoint للمهام السريعة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    company = request.current_company

    try:
        # عد المسودات
        draft_entries = JournalEntry.objects.filter(
            company=company,
            status='draft'
        ).count()

        # عد الحسابات النشطة
        active_accounts = Account.objects.filter(
            company=company,
            is_suspended=False
        ).count()

        # عد السندات غير المرحلة
        unposted_payment_vouchers = PaymentVoucher.objects.filter(
            company=company,
            status='confirmed'
        ).count()

        unposted_receipt_vouchers = ReceiptVoucher.objects.filter(
            company=company,
            status='confirmed'
        ).count()

        tasks = [
            {
                'title': 'مراجعة المسودات',
                'count': draft_entries,
                'icon': 'edit',
                'color': 'warning',
                'url': '/accounting/journal-entries/?status=draft',
                'description': f'{draft_entries} مسودة تحتاج مراجعة'
            },
            {
                'title': 'عرض جميع القيود',
                'count': None,
                'icon': 'list',
                'color': 'primary',
                'url': '/accounting/journal-entries/',
                'description': 'استعراض جميع القيود المحاسبية'
            },
            {
                'title': 'دليل الحسابات',
                'count': active_accounts,
                'icon': 'account_tree',
                'color': 'success',
                'url': '/accounting/accounts/',
                'description': f'{active_accounts} حساب نشط'
            },
            {
                'title': 'سندات غير مرحلة',
                'count': unposted_payment_vouchers + unposted_receipt_vouchers,
                'icon': 'pending_actions',
                'color': 'info',
                'url': '/accounting/payment-vouchers/?status=confirmed',
                'description': f'{unposted_payment_vouchers + unposted_receipt_vouchers} سند يحتاج ترحيل'
            }
        ]

        return JsonResponse({
            'success': True,
            'tasks': tasks
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في تحميل المهام: {str(e)}'
        }, status=500)
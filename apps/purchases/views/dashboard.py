# apps/purchases/views/dashboard.py
"""
لوحة تحكم نظام المشتريات - Purchase Dashboard
- إحصائيات شاملة ومفصّلة
- رسوم بيانية تفاعلية
- تنبيهات ذكية
- متابعة الأداء
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.db.models import (
    Sum, Count, Q, F, DecimalField, Case, When, Value, Avg,
    Max, Min, FloatField
)
from django.db.models.functions import Coalesce, TruncMonth, TruncDate
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta, datetime
from collections import defaultdict

from apps.core.mixins import CompanyMixin
from apps.core.decorators import permission_required_with_message

from ..models import (
    PurchaseInvoice, PurchaseOrder, PurchaseRequest,
    PurchaseQuotation, PurchaseQuotationRequest,
    PurchaseContract, GoodsReceipt
)
from apps.core.models import BusinessPartner


class PurchaseDashboardView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """لوحة تحكم المشتريات - محسّنة وشاملة"""

    template_name = 'purchases/dashboard.html'
    permission_required = 'purchases.view_purchaseinvoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            company = self.request.current_company

            # الإحصائيات الأساسية
            stats = self.get_basic_stats()

            # الإحصائيات المالية
            financial_stats = self.get_financial_stats()

            # إحصائيات الفواتير
            invoice_stats = self.get_invoice_stats()

            # إحصائيات الأوامر
            order_stats = self.get_order_stats()

            # إحصائيات الطلبات
            request_stats = self.get_request_stats()

            # إحصائيات العقود
            contract_stats = self.get_contract_stats()

            # إحصائيات محاضر الاستلام
            goods_receipt_stats = self.get_goods_receipt_stats()

            # أفضل الموردين
            top_suppliers = self.get_top_suppliers()

            # المشتريات حسب الفئة
            purchases_by_category = self.get_purchases_by_category()

            # المشتريات الشهرية (آخر 12 شهر)
            monthly_purchases = self.get_monthly_purchases()

            # الفواتير الأخيرة
            recent_invoices = self.get_recent_invoices()

            # الطلبات المعلقة
            pending_requests = self.get_pending_requests()

            # الأوامر النشطة
            active_orders = self.get_active_orders()

            # محاضر الاستلام المعلقة
            pending_receipts = self.get_pending_receipts()

            # العقود المنتهية قريباً
            expiring_contracts = self.get_expiring_contracts()

            # التنبيهات
            alerts = self.get_alerts()

            # إجراءات سريعة
            quick_actions = self.get_quick_actions()

            context.update({
                'title': _('لوحة تحكم المشتريات'),
                'stats': stats,
                'financial_stats': financial_stats,
                'invoice_stats': invoice_stats,
                'order_stats': order_stats,
                'request_stats': request_stats,
                'contract_stats': contract_stats,
                'goods_receipt_stats': goods_receipt_stats,
                'top_suppliers': top_suppliers,
                'purchases_by_category': purchases_by_category,
                'monthly_purchases': monthly_purchases,
                'recent_invoices': recent_invoices,
                'pending_requests': pending_requests,
                'active_orders': active_orders,
                'pending_receipts': pending_receipts,
                'expiring_contracts': expiring_contracts,
                'alerts': alerts,
                'quick_actions': quick_actions,
                'breadcrumbs': [
                    {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                    {'title': _('لوحة المشتريات'), 'url': ''},
                ]
            })

        except Exception as e:
            import traceback
            print(f"Error in purchase dashboard: {traceback.format_exc()}")
            context['error'] = str(e)

        return context

    def get_basic_stats(self):
        """الإحصائيات الأساسية"""
        company = self.request.current_company

        # عدد الموردين النشطين
        active_suppliers = BusinessPartner.objects.filter(
            company=company,
            partner_type__in=['supplier', 'both'],
            is_active=True
        ).count()

        # عدد الفواتير
        total_invoices = PurchaseInvoice.objects.filter(company=company).count()
        posted_invoices = PurchaseInvoice.objects.filter(company=company, is_posted=True).count()

        # عدد الأوامر
        total_orders = PurchaseOrder.objects.filter(company=company).count()
        active_orders = PurchaseOrder.objects.filter(
            company=company,
            status__in=['approved', 'sent', 'partial']
        ).count()

        # عدد الطلبات
        total_requests = PurchaseRequest.objects.filter(company=company).count()
        pending_requests = PurchaseRequest.objects.filter(
            company=company,
            status='pending_approval'
        ).count()

        # عدد العقود النشطة
        active_contracts = PurchaseContract.objects.filter(
            company=company,
            status='active'
        ).count()

        return {
            'active_suppliers': active_suppliers,
            'total_invoices': total_invoices,
            'posted_invoices': posted_invoices,
            'total_orders': total_orders,
            'active_orders': active_orders,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'active_contracts': active_contracts,
        }

    def get_financial_stats(self):
        """الإحصائيات المالية"""
        company = self.request.current_company
        today = date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        # إجمالي المشتريات (الفواتير المرحلة)
        invoices = PurchaseInvoice.objects.filter(
            company=company,
            is_posted=True,
            invoice_type='purchase'
        )

        total_purchases = invoices.aggregate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0'))
        )['total']

        monthly_purchases = invoices.filter(
            date__gte=month_start
        ).aggregate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0'))
        )['total']

        yearly_purchases = invoices.filter(
            date__gte=year_start
        ).aggregate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0'))
        )['total']

        # إجمالي المرتجعات
        returns = PurchaseInvoice.objects.filter(
            company=company,
            is_posted=True,
            invoice_type='return'
        ).aggregate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0'))
        )['total']

        # صافي المشتريات
        net_purchases = total_purchases - returns

        # متوسط قيمة الفاتورة
        avg_invoice = invoices.aggregate(
            avg=Coalesce(Avg('total_with_tax'), Decimal('0'))
        )['avg']

        # إجمالي الضرائب
        total_tax = invoices.aggregate(
            total=Coalesce(Sum('tax_amount'), Decimal('0'))
        )['total']

        # إجمالي الخصومات
        total_discount = invoices.aggregate(
            total=Coalesce(Sum('discount_amount'), Decimal('0'))
        )['total']

        # حساب نسبة النمو الشهري
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        last_month_purchases = invoices.filter(
            date__gte=last_month_start,
            date__lte=last_month_end
        ).aggregate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0'))
        )['total']

        if last_month_purchases > 0:
            growth_rate = ((monthly_purchases - last_month_purchases) / last_month_purchases * 100)
        else:
            growth_rate = 0 if monthly_purchases == 0 else 100

        return {
            'total_purchases': total_purchases,
            'monthly_purchases': monthly_purchases,
            'yearly_purchases': yearly_purchases,
            'total_returns': returns,
            'net_purchases': net_purchases,
            'avg_invoice': avg_invoice,
            'total_tax': total_tax,
            'total_discount': total_discount,
            'growth_rate': round(growth_rate, 2),
        }

    def get_invoice_stats(self):
        """إحصائيات الفواتير"""
        company = self.request.current_company

        stats = PurchaseInvoice.objects.filter(company=company).aggregate(
            total=Count('id'),
            posted=Count('id', filter=Q(is_posted=True)),
            draft=Count('id', filter=Q(is_posted=False)),
            purchases=Count('id', filter=Q(invoice_type='purchase')),
            returns=Count('id', filter=Q(invoice_type='return')),
        )

        return stats

    def get_order_stats(self):
        """إحصائيات الأوامر"""
        company = self.request.current_company

        stats = PurchaseOrder.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            pending_approval=Count('id', filter=Q(status='pending_approval')),
            approved=Count('id', filter=Q(status='approved')),
            sent=Count('id', filter=Q(status='sent')),
            partial=Count('id', filter=Q(status='partial')),
            completed=Count('id', filter=Q(status='completed')),
            cancelled=Count('id', filter=Q(status='cancelled')),
            rejected=Count('id', filter=Q(status='rejected')),
        )

        return stats

    def get_request_stats(self):
        """إحصائيات الطلبات"""
        company = self.request.current_company

        stats = PurchaseRequest.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            pending_approval=Count('id', filter=Q(status='pending_approval')),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
            converted=Count('id', filter=Q(status='converted')),
            cancelled=Count('id', filter=Q(status='cancelled')),
        )

        return stats

    def get_contract_stats(self):
        """إحصائيات العقود"""
        company = self.request.current_company
        today = date.today()

        stats = PurchaseContract.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            active=Count('id', filter=Q(status='active')),
            suspended=Count('id', filter=Q(status='suspended')),
            completed=Count('id', filter=Q(status='completed')),
            terminated=Count('id', filter=Q(status='terminated')),
            expired=Count('id', filter=Q(status='expired')),
            total_value=Coalesce(Sum('contract_value'), Decimal('0')),
        )

        # العقود المنتهية في 30 يوم
        expiring_soon = PurchaseContract.objects.filter(
            company=company,
            status='active',
            end_date__lte=today + timedelta(days=30),
            end_date__gte=today
        ).count()

        stats['expiring_soon'] = expiring_soon

        return stats

    def get_goods_receipt_stats(self):
        """إحصائيات محاضر الاستلام"""
        company = self.request.current_company

        stats = GoodsReceipt.objects.filter(company=company).aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            confirmed=Count('id', filter=Q(status='confirmed')),
            posted=Count('id', filter=Q(is_posted=True)),
            invoiced=Count('id', filter=Q(status='invoiced')),
        )

        return stats

    def get_top_suppliers(self, limit=10):
        """أفضل الموردين حسب قيمة المشتريات"""
        company = self.request.current_company

        suppliers = PurchaseInvoice.objects.filter(
            company=company,
            is_posted=True,
            invoice_type='purchase'
        ).values(
            'supplier__id',
            'supplier__name',
            'supplier__code'
        ).annotate(
            total_purchases=Coalesce(Sum('total_with_tax'), Decimal('0')),
            invoice_count=Count('id'),
            avg_invoice=Coalesce(Avg('total_with_tax'), Decimal('0'))
        ).order_by('-total_purchases')[:limit]

        return list(suppliers)

    def get_purchases_by_category(self):
        """المشتريات حسب فئة المواد"""
        company = self.request.current_company

        from apps.purchases.models import PurchaseInvoiceItem

        categories = PurchaseInvoiceItem.objects.filter(
            invoice__company=company,
            invoice__is_posted=True,
            invoice__invoice_type='purchase',
            item__category__isnull=False
        ).values(
            'item__category__name'
        ).annotate(
            total=Coalesce(Sum(F('subtotal') + F('tax_amount')), Decimal('0')),
            quantity=Coalesce(Sum('quantity'), Decimal('0'))
        ).order_by('-total')[:10]

        return list(categories)

    def get_monthly_purchases(self):
        """المشتريات الشهرية لآخر 12 شهر"""
        company = self.request.current_company
        today = date.today()
        twelve_months_ago = today - timedelta(days=365)

        monthly_data = PurchaseInvoice.objects.filter(
            company=company,
            is_posted=True,
            invoice_type='purchase',
            date__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Coalesce(Sum('total_with_tax'), Decimal('0')),
            count=Count('id')
        ).order_by('month')

        return list(monthly_data)

    def get_recent_invoices(self, limit=10):
        """الفواتير الأخيرة"""
        company = self.request.current_company

        invoices = PurchaseInvoice.objects.filter(
            company=company
        ).select_related('supplier', 'created_by').order_by('-date', '-created_at')[:limit]

        return invoices

    def get_pending_requests(self, limit=10):
        """الطلبات المعلقة"""
        company = self.request.current_company

        requests = PurchaseRequest.objects.filter(
            company=company,
            status__in=['draft', 'pending_approval']
        ).select_related('requested_by', 'created_by').order_by('-date')[:limit]

        return requests

    def get_active_orders(self, limit=10):
        """الأوامر النشطة"""
        company = self.request.current_company

        orders = PurchaseOrder.objects.filter(
            company=company,
            status__in=['approved', 'sent', 'partial']
        ).select_related('supplier', 'created_by').order_by('-date')[:limit]

        return orders

    def get_pending_receipts(self, limit=10):
        """محاضر الاستلام المعلقة"""
        company = self.request.current_company

        receipts = GoodsReceipt.objects.filter(
            company=company,
            status__in=['draft', 'confirmed'],
            is_posted=False
        ).select_related('purchase_order', 'supplier').order_by('-date')[:limit]

        return receipts

    def get_expiring_contracts(self, days=30):
        """العقود المنتهية قريباً"""
        company = self.request.current_company
        today = date.today()
        expiry_date = today + timedelta(days=days)

        contracts = PurchaseContract.objects.filter(
            company=company,
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('supplier').order_by('end_date')

        return contracts

    def get_alerts(self):
        """التنبيهات والإشعارات"""
        company = self.request.current_company
        alerts = []

        # طلبات تحتاج موافقة
        pending_requests_count = PurchaseRequest.objects.filter(
            company=company,
            status='pending_approval'
        ).count()

        if pending_requests_count > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-clipboard-list',
                'title': 'طلبات شراء معلقة',
                'message': f'يوجد {pending_requests_count} طلب شراء بانتظار الموافقة',
                'url': reverse('purchases:request_list') + '?status=pending_approval',
                'count': pending_requests_count
            })

        # أوامر تحتاج إرسال
        pending_orders_count = PurchaseOrder.objects.filter(
            company=company,
            status='approved'
        ).count()

        if pending_orders_count > 0:
            alerts.append({
                'type': 'info',
                'icon': 'fa-file-invoice',
                'title': 'أوامر جاهزة للإرسال',
                'message': f'يوجد {pending_orders_count} أمر شراء جاهز للإرسال للمورد',
                'url': reverse('purchases:order_list') + '?status=approved',
                'count': pending_orders_count
            })

        # محاضر استلام معلقة
        pending_receipts_count = GoodsReceipt.objects.filter(
            company=company,
            status='confirmed',
            is_posted=False
        ).count()

        if pending_receipts_count > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-boxes',
                'title': 'محاضر استلام غير مرحلة',
                'message': f'يوجد {pending_receipts_count} محضر استلام بحاجة للترحيل',
                'url': reverse('purchases:goods_receipt_list') + '?status=confirmed',
                'count': pending_receipts_count
            })

        # عقود منتهية قريباً
        expiring_contracts_count = self.get_expiring_contracts(30).count()

        if expiring_contracts_count > 0:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-file-contract',
                'title': 'عقود منتهية قريباً',
                'message': f'يوجد {expiring_contracts_count} عقد ينتهي خلال 30 يوم',
                'url': reverse('purchases:contract_list') + '?expiring=30',
                'count': expiring_contracts_count
            })

        return alerts

    def get_quick_actions(self):
        """الإجراءات السريعة"""
        user = self.request.user

        actions = []

        if user.has_perm('purchases.add_purchaserequest'):
            actions.append({
                'icon': 'fa-plus-circle',
                'title': 'طلب شراء جديد',
                'url': reverse('purchases:request_create'),
                'color': 'primary'
            })

        if user.has_perm('purchases.add_purchaseorder'):
            actions.append({
                'icon': 'fa-file-invoice',
                'title': 'أمر شراء جديد',
                'url': reverse('purchases:order_create'),
                'color': 'success'
            })

        if user.has_perm('purchases.add_purchaseinvoice'):
            actions.append({
                'icon': 'fa-file-alt',
                'title': 'فاتورة مشتريات',
                'url': reverse('purchases:invoice_create'),
                'color': 'info'
            })

        if user.has_perm('purchases.add_goodsreceipt'):
            actions.append({
                'icon': 'fa-boxes',
                'title': 'محضر استلام',
                'url': reverse('purchases:goods_receipt_create'),
                'color': 'warning'
            })

        if user.has_perm('purchases.add_purchasecontract'):
            actions.append({
                'icon': 'fa-file-contract',
                'title': 'عقد جديد',
                'url': reverse('purchases:contract_create'),
                'color': 'secondary'
            })

        if user.has_perm('purchases.add_purchasequotationrequest'):
            actions.append({
                'icon': 'fa-clipboard-list',
                'title': 'طلب عروض أسعار',
                'url': reverse('purchases:rfq_create'),
                'color': 'dark'
            })

        return actions


# ==================== API Endpoints ====================

@login_required
@permission_required_with_message('purchases.view_purchaseinvoice')
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API للحصول على إحصائيات الداشبورد"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        view = PurchaseDashboardView()
        view.request = request

        stats = {
            'basic': view.get_basic_stats(),
            'financial': view.get_financial_stats(),
            'invoices': view.get_invoice_stats(),
            'orders': view.get_order_stats(),
            'requests': view.get_request_stats(),
            'contracts': view.get_contract_stats(),
            'goods_receipts': view.get_goods_receipt_stats(),
        }

        # تحويل Decimal إلى float للـ JSON
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj

        stats = convert_decimals(stats)

        return JsonResponse({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required_with_message('purchases.view_purchaseinvoice')
@require_http_methods(["GET"])
def monthly_chart_api(request):
    """API لبيانات الرسم البياني الشهري"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        view = PurchaseDashboardView()
        view.request = request

        monthly_data = view.get_monthly_purchases()

        # تنسيق البيانات للرسم البياني
        labels = []
        values = []

        for item in monthly_data:
            month_date = item['month']
            labels.append(month_date.strftime('%Y-%m'))
            values.append(float(item['total']))

        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required_with_message('purchases.view_purchaseinvoice')
@require_http_methods(["GET"])
def top_suppliers_api(request):
    """API لأفضل الموردين"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({'error': 'لا توجد شركة محددة'}, status=400)

    try:
        view = PurchaseDashboardView()
        view.request = request

        limit = int(request.GET.get('limit', 10))
        suppliers = view.get_top_suppliers(limit)

        # تحويل Decimal إلى float
        for supplier in suppliers:
            supplier['total_purchases'] = float(supplier['total_purchases'])
            supplier['avg_invoice'] = float(supplier['avg_invoice'])

        return JsonResponse({
            'success': True,
            'suppliers': suppliers
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

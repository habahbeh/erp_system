# apps/base_data/views/report_views.py
"""
Views التقارير والإحصائيات - Bootstrap 5 + RTL + Charts
تقارير الأصناف، المخزون، الشركاء، المستودعات
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Sum, F, Avg, Max, Min
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from datetime import datetime, timedelta
from django.views import View

from ..models import Item, BusinessPartner, Warehouse, ItemCategory, UnitOfMeasure, WarehouseItem
from ..forms import StockReportForm
from apps.core.mixins import CompanyMixin


class ReportsIndexView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """صفحة التقارير الرئيسية"""
    template_name = 'base_data/reports/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات سريعة
        quick_stats = self.get_quick_stats()

        context.update({
            'page_title': _('التقارير والإحصائيات'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'active': True}
            ],
            'quick_stats': quick_stats,
            'available_reports': self.get_available_reports(),
        })
        return context

    def get_quick_stats(self):
        """الإحصائيات السريعة"""
        company = self.request.user.company

        stats = {
            'items': {
                'total': Item.objects.filter(company=company).count(),
                'active': Item.objects.filter(company=company, is_active=True, is_inactive=False).count(),
                'with_stock': Item.objects.filter(
                    company=company,
                    warehouse_items__quantity__gt=0
                ).distinct().count(),
                'low_stock': Item.objects.filter(
                    company=company,
                    warehouse_items__quantity__lte=F('minimum_quantity'),
                    minimum_quantity__gt=0
                ).distinct().count(),
            },
            'partners': {
                'total': BusinessPartner.objects.filter(company=company).count(),
                'customers': BusinessPartner.objects.filter(
                    company=company,
                    partner_type__in=['customer', 'both']
                ).count(),
                'suppliers': BusinessPartner.objects.filter(
                    company=company,
                    partner_type__in=['supplier', 'both']
                ).count(),
                'active': BusinessPartner.objects.filter(company=company, is_active=True).count(),
            },
            'warehouses': {
                'total': Warehouse.objects.filter(company=company).count(),
                'active': Warehouse.objects.filter(company=company, is_active=True).count(),
                'main': Warehouse.objects.filter(company=company, warehouse_type='main').count(),
                'branch': Warehouse.objects.filter(company=company, warehouse_type='branch').count(),
            },
            'stock': {
                'total_value': WarehouseItem.objects.filter(
                    warehouse__company=company
                ).aggregate(
                    total=Coalesce(Sum(F('quantity') * F('average_cost')), 0)
                )['total'],
                'total_items': WarehouseItem.objects.filter(
                    warehouse__company=company
                ).aggregate(
                    total=Count('item', distinct=True)
                )['total'],
            }
        }

        return stats

    def get_available_reports(self):
        """التقارير المتاحة"""
        return [
            {
                'title': _('تقرير الأصناف'),
                'description': _('تقرير شامل بجميع الأصناف وبياناتها'),
                'icon': 'fas fa-boxes',
                'url': reverse('base_data:items_report'),
                'color': 'primary'
            },
            {
                'title': _('تقرير المخزون'),
                'description': _('أرصدة المخزون وحركات الأصناف'),
                'icon': 'fas fa-warehouse',
                'url': reverse('base_data:stock_report'),
                'color': 'success'
            },
            {
                'title': _('تقرير الشركاء'),
                'description': _('بيانات العملاء والموردين'),
                'icon': 'fas fa-users',
                'url': reverse('base_data:partners_report'),
                'color': 'info'
            },
            {
                'title': _('تقرير التصنيفات'),
                'description': _('تحليل الأصناف حسب التصنيفات'),
                'icon': 'fas fa-sitemap',
                'url': reverse('base_data:categories_report'),
                'color': 'warning'
            },
            {
                'title': _('الأصناف منخفضة المخزون'),
                'description': _('الأصناف التي وصلت للحد الأدنى'),
                'icon': 'fas fa-exclamation-triangle',
                'url': reverse('base_data:low_stock_report'),
                'color': 'danger'
            },
        ]


class ItemsReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الأصناف"""
    template_name = 'base_data/reports/items_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الأصناف
        items_stats = self.get_items_statistics()

        # الأصناف حسب التصنيف
        category_stats = self.get_category_statistics()

        # الأصناف حسب المصنع
        manufacturer_stats = self.get_manufacturer_statistics()

        context.update({
            'page_title': _('تقرير الأصناف'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'url': reverse('base_data:reports_index')},
                {'title': _('تقرير الأصناف'), 'active': True}
            ],
            'items_stats': items_stats,
            'category_stats': category_stats,
            'manufacturer_stats': manufacturer_stats,
        })
        return context

    def get_items_statistics(self):
        """إحصائيات الأصناف"""
        company = self.request.user.company

        stats = Item.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True, is_inactive=False)),
            inactive=Count('id', filter=Q(is_inactive=True)),
            with_barcode=Count('id', filter=~Q(barcode='')),
            with_image=Count('id', filter=~Q(image='')),
            avg_purchase_price=Avg('purchase_price'),
            avg_sale_price=Avg('sale_price'),
            max_sale_price=Max('sale_price'),
            min_sale_price=Min('sale_price'),
        )

        # إضافة حسابات إضافية
        stats['percentage_active'] = (stats['active'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['with_stock'] = Item.objects.filter(
            company=company,
            warehouse_items__quantity__gt=0
        ).distinct().count()

        return stats

    def get_category_statistics(self):
        """إحصائيات التصنيفات"""
        return ItemCategory.objects.filter(
            company=self.request.user.company
        ).annotate(
            items_count=Count('items', filter=Q(items__is_active=True))
        ).order_by('-items_count')[:10]

    def get_manufacturer_statistics(self):
        """إحصائيات الشركات المصنعة"""
        return Item.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).exclude(
            manufacturer=''
        ).values('manufacturer').annotate(
            items_count=Count('id')
        ).order_by('-items_count')[:10]


class StockReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير المخزون"""
    template_name = 'base_data/reports/stock_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # نموذج الفلترة
        form = StockReportForm(
            data=self.request.GET or None,
            company=self.request.user.company
        )

        # إحصائيات المخزون
        stock_stats = self.get_stock_statistics(form)

        # المخزون حسب المستودع
        warehouse_stats = self.get_warehouse_statistics(form)

        # أعلى الأصناف قيمة
        top_value_items = self.get_top_value_items(form)

        # الأصناف منخفضة المخزون
        low_stock_items = self.get_low_stock_items(form)

        context.update({
            'page_title': _('تقرير المخزون'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'url': reverse('base_data:reports_index')},
                {'title': _('تقرير المخزون'), 'active': True}
            ],
            'form': form,
            'stock_stats': stock_stats,
            'warehouse_stats': warehouse_stats,
            'top_value_items': top_value_items,
            'low_stock_items': low_stock_items,
        })
        return context

    def get_stock_statistics(self, form):
        """إحصائيات المخزون الإجمالية"""
        queryset = WarehouseItem.objects.filter(
            warehouse__company=self.request.user.company,
            warehouse__is_active=True
        )

        # تطبيق الفلاتر
        if form.is_valid():
            warehouse = form.cleaned_data.get('warehouse')
            if warehouse:
                queryset = queryset.filter(warehouse=warehouse)

            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(item__category=category)

        stats = queryset.aggregate(
            total_items=Count('item', distinct=True),
            total_quantity=Coalesce(Sum('quantity'), 0),
            total_value=Coalesce(Sum(F('quantity') * F('average_cost')), 0),
            avg_cost=Avg('average_cost'),
            zero_stock_items=Count('item', filter=Q(quantity=0)),
            negative_stock_items=Count('item', filter=Q(quantity__lt=0)),
        )

        return stats

    def get_warehouse_statistics(self, form):
        """إحصائيات المخزون حسب المستودع"""
        queryset = Warehouse.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).annotate(
            items_count=Count('warehouse_items', filter=Q(warehouse_items__quantity__gt=0)),
            total_quantity=Coalesce(Sum('warehouse_items__quantity'), 0),
            total_value=Coalesce(Sum(F('warehouse_items__quantity') * F('warehouse_items__average_cost')), 0)
        ).order_by('-total_value')

        return queryset

    def get_top_value_items(self, form):
        """أعلى الأصناف قيمة"""
        queryset = WarehouseItem.objects.filter(
            warehouse__company=self.request.user.company,
            warehouse__is_active=True,
            quantity__gt=0
        ).select_related('item', 'warehouse').annotate(
            total_value=F('quantity') * F('average_cost')
        ).order_by('-total_value')[:20]

        return queryset

    def get_low_stock_items(self, form):
        """الأصناف منخفضة المخزون"""
        return WarehouseItem.objects.filter(
            warehouse__company=self.request.user.company,
            warehouse__is_active=True,
            quantity__lte=F('item__minimum_quantity'),
            item__minimum_quantity__gt=0
        ).select_related('item', 'warehouse').order_by('quantity')[:50]


class PartnersReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الشركاء التجاريين"""
    template_name = 'base_data/reports/partners_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الشركاء
        partners_stats = self.get_partners_statistics()

        # التوزيع الجغرافي
        geographic_stats = self.get_geographic_statistics()

        # إحصائيات الائتمان
        credit_stats = self.get_credit_statistics()

        context.update({
            'page_title': _('تقرير الشركاء التجاريين'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'url': reverse('base_data:reports_index')},
                {'title': _('تقرير الشركاء'), 'active': True}
            ],
            'partners_stats': partners_stats,
            'geographic_stats': geographic_stats,
            'credit_stats': credit_stats,
        })
        return context

    def get_partners_statistics(self):
        """إحصائيات الشركاء"""
        company = self.request.user.company

        stats = BusinessPartner.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            customers=Count('id', filter=Q(partner_type__in=['customer', 'both'])),
            suppliers=Count('id', filter=Q(partner_type__in=['supplier', 'both'])),
            both=Count('id', filter=Q(partner_type='both')),
            with_email=Count('id', filter=~Q(email='')),
            with_tax_number=Count('id', filter=~Q(tax_number='')),
            companies=Count('id', filter=Q(account_type='company')),
            individuals=Count('id', filter=Q(account_type='individual')),
        )

        # حسابات النسب المئوية
        if stats['total'] > 0:
            stats['customers_percentage'] = (stats['customers'] / stats['total']) * 100
            stats['suppliers_percentage'] = (stats['suppliers'] / stats['total']) * 100
            stats['active_percentage'] = (stats['active'] / stats['total']) * 100

        return stats

    def get_geographic_statistics(self):
        """التوزيع الجغرافي للشركاء"""
        return BusinessPartner.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).exclude(
            city=''
        ).values('city').annotate(
            partners_count=Count('id')
        ).order_by('-partners_count')[:15]

    def get_credit_statistics(self):
        """إحصائيات الائتمان"""
        return BusinessPartner.objects.filter(
            company=self.request.user.company,
            credit_limit__gt=0
        ).aggregate(
            total_credit_limit=Sum('credit_limit'),
            avg_credit_limit=Avg('credit_limit'),
            max_credit_limit=Max('credit_limit'),
            partners_with_credit=Count('id')
        )


class CategoriesReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير التصنيفات"""
    template_name = 'base_data/reports/categories_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات التصنيفات
        categories_stats = self.get_categories_statistics()

        # التوزيع الهرمي
        hierarchy_stats = self.get_hierarchy_statistics()

        context.update({
            'page_title': _('تقرير التصنيفات'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'url': reverse('base_data:reports_index')},
                {'title': _('تقرير التصنيفات'), 'active': True}
            ],
            'categories_stats': categories_stats,
            'hierarchy_stats': hierarchy_stats,
        })
        return context

    def get_categories_statistics(self):
        """إحصائيات التصنيفات"""
        return ItemCategory.objects.filter(
            company=self.request.user.company
        ).annotate(
            items_count=Count('items'),
            active_items_count=Count('items', filter=Q(items__is_active=True, items__is_inactive=False))
        ).order_by('-items_count')

    def get_hierarchy_statistics(self):
        """إحصائيات التوزيع الهرمي"""
        stats = {}

        for level in range(1, 5):  # 4 مستويات
            stats[f'level_{level}'] = ItemCategory.objects.filter(
                company=self.request.user.company,
                level=level
            ).count()

        return stats


class LowStockReportView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """تقرير الأصناف منخفضة المخزون"""
    template_name = 'base_data/reports/low_stock_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الأصناف منخفضة المخزون
        low_stock_items = self.get_low_stock_items()

        # الأصناف بدون مخزون
        zero_stock_items = self.get_zero_stock_items()

        # إحصائيات
        stats = self.get_low_stock_statistics()

        context.update({
            'page_title': _('الأصناف منخفضة المخزون'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('التقارير'), 'url': reverse('base_data:reports_index')},
                {'title': _('منخفضة المخزون'), 'active': True}
            ],
            'low_stock_items': low_stock_items,
            'zero_stock_items': zero_stock_items,
            'stats': stats,
        })
        return context

    def get_low_stock_items(self):
        """الأصناف منخفضة المخزون"""
        return WarehouseItem.objects.filter(
            warehouse__company=self.request.user.company,
            warehouse__is_active=True,
            quantity__lte=F('item__minimum_quantity'),
            item__minimum_quantity__gt=0,
            quantity__gt=0
        ).select_related(
            'item', 'warehouse', 'item__category', 'item__unit'
        ).order_by('quantity', 'item__name')

    def get_zero_stock_items(self):
        """الأصناف بدون مخزون"""
        items_with_stock = WarehouseItem.objects.filter(
            warehouse__company=self.request.user.company,
            quantity__gt=0
        ).values_list('item_id', flat=True)

        return Item.objects.filter(
            company=self.request.user.company,
            is_active=True,
            is_inactive=False
        ).exclude(
            id__in=items_with_stock
        ).select_related(
            'category', 'unit'
        ).order_by('name')[:100]

    def get_low_stock_statistics(self):
        """إحصائيات منخفضة المخزون"""
        company = self.request.user.company

        return {
            'low_stock_count': WarehouseItem.objects.filter(
                warehouse__company=company,
                warehouse__is_active=True,
                quantity__lte=F('item__minimum_quantity'),
                item__minimum_quantity__gt=0,
                quantity__gt=0
            ).count(),
            'zero_stock_count': Item.objects.filter(
                company=company,
                is_active=True,
                is_inactive=False
            ).exclude(
                warehouse_items__quantity__gt=0
            ).count(),
            'critical_items': WarehouseItem.objects.filter(
                warehouse__company=company,
                warehouse__is_active=True,
                quantity__lte=F('item__minimum_quantity') / 2,
                item__minimum_quantity__gt=0
            ).count(),
        }


# AJAX Views للرسوم البيانية
class ReportChartsView(LoginRequiredMixin, CompanyMixin, View):
    """بيانات الرسوم البيانية للتقارير"""

    def get(self, request, chart_type):
        if chart_type == 'items_by_category':
            return self.items_by_category_chart()
        elif chart_type == 'stock_by_warehouse':
            return self.stock_by_warehouse_chart()
        elif chart_type == 'partners_by_type':
            return self.partners_by_type_chart()
        elif chart_type == 'items_by_manufacturer':
            return self.items_by_manufacturer_chart()
        elif chart_type == 'stock_trends':
            return self.stock_trends_chart()
        else:
            return JsonResponse({'error': _('نوع رسم بياني غير مدعوم')}, status=400)

    def items_by_category_chart(self):
        """رسم بياني الأصناف حسب التصنيف"""
        data = ItemCategory.objects.filter(
            company=self.request.user.company
        ).annotate(
            items_count=Count('items', filter=Q(items__is_active=True))
        ).order_by('-items_count')[:10]

        labels = [cat.name for cat in data]
        values = [cat.items_count for cat in data]
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'data': values,
                'backgroundColor': colors[:len(values)],
                'borderColor': colors[:len(values)],
                'borderWidth': 1
            }]
        })

    def stock_by_warehouse_chart(self):
        """رسم بياني المخزون حسب المستودع"""
        data = Warehouse.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).annotate(
            total_value=Coalesce(
                Sum(F('warehouse_items__quantity') * F('warehouse_items__average_cost')),
                0
            )
        ).order_by('-total_value')[:8]

        labels = [warehouse.name for warehouse in data]
        values = [float(warehouse.total_value) for warehouse in data]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('قيمة المخزون'),
                'data': values,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 2
            }]
        })

    def partners_by_type_chart(self):
        """رسم بياني الشركاء حسب النوع"""
        stats = BusinessPartner.objects.filter(
            company=self.request.user.company
        ).aggregate(
            customers=Count('id', filter=Q(partner_type='customer')),
            suppliers=Count('id', filter=Q(partner_type='supplier')),
            both=Count('id', filter=Q(partner_type='both'))
        )

        return JsonResponse({
            'labels': [_('العملاء'), _('الموردين'), _('كليهما')],
            'datasets': [{
                'data': [stats['customers'], stats['suppliers'], stats['both']],
                'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56'],
                'borderColor': ['#FF6384', '#36A2EB', '#FFCE56'],
                'borderWidth': 1
            }]
        })

    def items_by_manufacturer_chart(self):
        """رسم بياني الأصناف حسب الشركة المصنعة"""
        data = Item.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).exclude(
            manufacturer=''
        ).values('manufacturer').annotate(
            items_count=Count('id')
        ).order_by('-items_count')[:8]

        labels = [item['manufacturer'] for item in data]
        values = [item['items_count'] for item in data]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('عدد الأصناف'),
                'data': values,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 2
            }]
        })
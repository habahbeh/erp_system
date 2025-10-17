# apps/assets/views/report_views.py
"""
Views التقارير مع دعم التصدير
"""

from django.urls import reverse
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
import datetime

from ..models import Asset, AssetDepreciation, AssetMaintenance, AssetTransaction, AssetCategory
from apps.core.models import Branch
from .base_report_views import BaseReportView
from apps.assets.utils import format_currency, format_date

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from apps.core.mixins import CompanyMixin



class ReportsListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """صفحة قائمة التقارير الرئيسية"""

    template_name = 'assets/reports/reports_list.html'
    permission_required = 'assets.view_asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # قائمة التقارير المتاحة
        reports = [
            {
                'title': 'تقرير سجل الأصول الثابتة',
                'description': 'عرض شامل لجميع الأصول مع التفاصيل المالية والتشغيلية',
                'icon': 'fas fa-list-alt',
                'color': 'primary',
                'url': reverse('assets:report_asset_register'),
                'features': [
                    'التكلفة الأصلية والقيمة الدفترية',
                    'الإهلاك المتراكم',
                    'التوزيع حسب الفئات',
                    'معلومات الموقع والمسؤولية'
                ]
            },
            {
                'title': 'تقرير الإهلاك',
                'description': 'تقرير مفصل عن الإهلاك الشهري والسنوي للأصول',
                'icon': 'fas fa-chart-line',
                'color': 'warning',
                'url': reverse('assets:report_depreciation'),
                'features': [
                    'الإهلاك الشهري لكل أصل',
                    'التحليل حسب الفئات',
                    'المقارنة السنوية',
                    'التوقعات المستقبلية'
                ]
            },
            {
                'title': 'تقرير حركة الأصول',
                'description': 'تتبع جميع العمليات: الشراء، البيع، التحويل، الاستبعاد',
                'icon': 'fas fa-exchange-alt',
                'color': 'success',
                'url': reverse('assets:report_movement'),
                'features': [
                    'عمليات الشراء والبيع',
                    'حساب الأرباح والخسائر',
                    'التحويلات بين الفروع',
                    'سجل الاستبعاد'
                ]
            },
            {
                'title': 'تقرير الصيانة',
                'description': 'تتبع تكاليف ومواعيد الصيانة الدورية والطارئة',
                'icon': 'fas fa-tools',
                'color': 'info',
                'url': reverse('assets:report_maintenance'),
                'features': [
                    'تكاليف الصيانة التفصيلية',
                    'الصيانة الدورية المجدولة',
                    'أعلى الأصول تكلفة',
                    'معدلات إتمام الصيانة'
                ]
            },
            {
                'title': 'تقرير الأصول حسب مركز التكلفة',
                'description': 'توزيع الأصول والقيم على مراكز التكلفة',
                'icon': 'fas fa-building',
                'color': 'secondary',
                'url': reverse('assets:report_by_cost_center'),
                'features': [
                    'توزيع الأصول',
                    'القيم الدفترية',
                    'التحليل المقارن',
                    'نسب التوزيع'
                ]
            },
            {
                'title': 'تقرير الأصول القريبة من نهاية العمر',
                'description': 'الأصول التي تقترب من نهاية عمرها الافتراضي',
                'icon': 'fas fa-exclamation-triangle',
                'color': 'danger',
                'url': reverse('assets:report_near_end_of_life'),
                'features': [
                    'الأصول خلال 6 أشهر',
                    'خطط الاستبدال',
                    'التكاليف المتوقعة',
                    'الأولويات'
                ]
            },
            {
                'title': 'تقرير القيمة العادلة',
                'description': 'مقارنة القيمة الدفترية بالقيمة العادلة للأصول',
                'icon': 'fas fa-balance-scale',
                'color': 'dark',
                'url': reverse('assets:report_fair_value'),
                'features': [
                    'القيمة العادلة الحالية',
                    'الفروق والانحرافات',
                    'نسب التغيير',
                    'توصيات إعادة التقييم'
                ]
            },
        ]

        context.update({
            'title': 'تقارير الأصول الثابتة',
            'reports': reports,
            'breadcrumbs': [
                {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
                {'title': 'الأصول الثابتة', 'url': reverse('assets:dashboard')},
                {'title': 'التقارير', 'url': ''},
            ],
        })

        return context


class AssetRegisterReportView(BaseReportView):
    """تقرير سجل الأصول الثابتة"""

    template_name = 'assets/reports/asset_register.html'
    permission_required = 'assets.view_asset'
    report_name = 'asset_register'
    report_title = 'تقرير سجل الأصول الثابتة'
    pdf_orientation = 'landscape'  # عرضي للجدول الواسع

    def get_filters_from_request(self):
        """استخراج الفلاتر من الـ Request"""
        filters = super().get_filters_from_request()

        # فلاتر إضافية خاصة بهذا التقرير
        if self.request.GET.get('status'):
            filters['status'] = self.request.GET.get('status')

        if self.request.GET.get('condition'):
            filters['condition_id'] = self.request.GET.get('condition')

        if self.request.GET.get('cost_center'):
            filters['cost_center_id'] = self.request.GET.get('cost_center')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet مع تطبيق الفلاتر"""
        company = self.request.user.company

        assets = Asset.objects.filter(
            company=company
        ).select_related(
            'category',
            'condition',
            'depreciation_method',
            'branch',
            'cost_center',
            'responsible_employee'
        ).order_by('category__name', 'asset_number')

        # تطبيق الفلاتر
        if filters.get('category_id'):
            assets = assets.filter(category_id=filters['category_id'])

        if filters.get('status'):
            assets = assets.filter(status=filters['status'])

        if filters.get('condition_id'):
            assets = assets.filter(condition_id=filters['condition_id'])

        if filters.get('branch_id'):
            assets = assets.filter(branch_id=filters['branch_id'])

        if filters.get('cost_center_id'):
            assets = assets.filter(cost_center_id=filters['cost_center_id'])

        if filters.get('date_from'):
            assets = assets.filter(purchase_date__gte=filters['date_from'])

        if filters.get('date_to'):
            assets = assets.filter(purchase_date__lte=filters['date_to'])

        return assets

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        # الإحصائيات الإجمالية
        totals = queryset.aggregate(
            total_count=Count('id'),
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
            avg_book_value=Avg('book_value')
        )

        # حسب الفئة
        by_category = queryset.values(
            'category__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        ).order_by('category__name')

        # حسب الحالة
        by_status = queryset.values('status').annotate(
            count=Count('id')
        )

        # حسب الفرع
        by_branch = queryset.values(
            'branch__name'
        ).annotate(
            count=Count('id'),
            total_book_value=Sum('book_value')
        ).order_by('branch__name')

        return {
            'totals': totals,
            'by_category': by_category,
            'by_status': by_status,
            'by_branch': by_branch,
        }

    def get_report_filters(self):
        """الحصول على الفلاتر المطبقة للعرض"""
        filters_display = {}

        if self.request.GET.get('category'):
            try:
                category = AssetCategory.objects.get(id=self.request.GET.get('category'))
                filters_display['الفئة'] = category.name
            except:
                pass

        if self.request.GET.get('branch'):
            try:
                branch = Branch.objects.get(id=self.request.GET.get('branch'))
                filters_display['الفرع'] = branch.name
            except:
                pass

        if self.request.GET.get('status'):
            status_dict = dict(Asset.STATUS_CHOICES)
            filters_display['الحالة'] = status_dict.get(self.request.GET.get('status'), '')

        if self.request.GET.get('date_from'):
            filters_display['من تاريخ'] = self.request.GET.get('date_from')

        if self.request.GET.get('date_to'):
            filters_display['إلى تاريخ'] = self.request.GET.get('date_to')

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة للتصدير"""
        return [
            'رقم الأصل',
            'اسم الأصل',
            'الفئة',
            'تاريخ الشراء',
            'التكلفة الأصلية',
            'الإهلاك المتراكم',
            'القيمة الدفترية',
            'الحالة',
            'الفرع',
            'مركز التكلفة',
            'الموظف المسؤول',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات للتصدير"""
        data = []

        for asset in queryset:
            data.append([
                asset.asset_number,
                asset.name,
                asset.category.name,
                format_date(asset.purchase_date),
                float(asset.original_cost),
                float(asset.accumulated_depreciation),
                float(asset.book_value),
                asset.get_status_display(),
                asset.branch.name if asset.branch else '-',
                asset.cost_center.name if asset.cost_center else '-',
                asset.responsible_employee.get_full_name() if asset.responsible_employee else '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        totals = stats['totals']

        return [
            'الإجمالي',
            f"{totals['total_count']} أصل",
            '',
            '',
            float(totals['total_cost'] or 0),
            float(totals['total_depreciation'] or 0),
            float(totals['total_book_value'] or 0),
            '',
            '',
            '',
            '',
        ]


class DepreciationReportView(BaseReportView):
    """تقرير الإهلاك"""

    template_name = 'assets/reports/depreciation_report.html'
    permission_required = 'assets.view_assetdepreciation'
    report_name = 'depreciation_report'
    report_title = 'تقرير الإهلاك'

    def get_filters_from_request(self):
        """استخراج الفلاتر"""
        filters = super().get_filters_from_request()

        filters['year'] = self.request.GET.get('year', str(datetime.date.today().year))

        if self.request.GET.get('month'):
            filters['month'] = self.request.GET.get('month')

        if self.request.GET.get('asset'):
            filters['asset_id'] = self.request.GET.get('asset')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        company = self.request.user.company

        depreciations = AssetDepreciation.objects.filter(
            asset__company=company,
        ).select_related(
            'asset',
            'asset__category',
            'asset__branch'
        ).order_by('-depreciation_date', 'asset__asset_number')

        # تطبيق الفلاتر
        if filters.get('year'):
            depreciations = depreciations.filter(
                depreciation_date__year=filters['year']
            )

        if filters.get('month'):
            depreciations = depreciations.filter(
                depreciation_date__month=filters['month']
            )

        if filters.get('category_id'):
            depreciations = depreciations.filter(
                asset__category_id=filters['category_id']
            )

        if filters.get('asset_id'):
            depreciations = depreciations.filter(
                asset_id=filters['asset_id']
            )

        return depreciations

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        # الإجمالي
        total_depreciation = queryset.aggregate(
            total=Sum('depreciation_amount')
        )['total'] or Decimal('0')

        # حسب الشهر
        by_month = queryset.values(
            'depreciation_date__month'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('depreciation_date__month')

        # حسب الفئة
        by_category = queryset.values(
            'asset__category__name'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('-total')

        # حسب الأصل (أعلى 10)
        by_asset = queryset.values(
            'asset__asset_number',
            'asset__name'
        ).annotate(
            total=Sum('depreciation_amount'),
            count=Count('id')
        ).order_by('-total')[:10]

        return {
            'total_depreciation': total_depreciation,
            'total_records': queryset.count(),
            'by_month': by_month,
            'by_category': by_category,
            'by_asset': by_asset,
        }

    def get_report_filters(self):
        """الفلاتر المطبقة"""
        filters_display = {}

        if self.request.GET.get('year'):
            filters_display['السنة'] = self.request.GET.get('year')

        if self.request.GET.get('month'):
            months = {
                '1': 'يناير', '2': 'فبراير', '3': 'مارس', '4': 'أبريل',
                '5': 'مايو', '6': 'يونيو', '7': 'يوليو', '8': 'أغسطس',
                '9': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر'
            }
            filters_display['الشهر'] = months.get(self.request.GET.get('month'), '')

        if self.request.GET.get('category'):
            try:
                category = AssetCategory.objects.get(id=self.request.GET.get('category'))
                filters_display['الفئة'] = category.name
            except:
                pass

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'التاريخ',
            'رقم الأصل',
            'اسم الأصل',
            'الفئة',
            'مبلغ الإهلاك',
            'الإهلاك المتراكم',
            'القيمة الدفترية',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        for dep in queryset:
            data.append([
                format_date(dep.depreciation_date),
                dep.asset.asset_number,
                dep.asset.name,
                dep.asset.category.name,
                float(dep.depreciation_amount),
                float(dep.accumulated_depreciation),
                float(dep.book_value),
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        return [
            'الإجمالي',
            '',
            f"{stats['total_records']} سجل",
            '',
            float(stats['total_depreciation']),
            '',
            '',
        ]


class MaintenanceReportView(BaseReportView):
    """تقرير الصيانة"""

    template_name = 'assets/reports/maintenance_report.html'
    permission_required = 'assets.view_assetmaintenance'
    report_name = 'maintenance_report'
    report_title = 'تقرير الصيانة'

    def get_filters_from_request(self):
        """استخراج الفلاتر"""
        filters = super().get_filters_from_request()

        if self.request.GET.get('asset'):
            filters['asset_id'] = self.request.GET.get('asset')

        if self.request.GET.get('status'):
            filters['status'] = self.request.GET.get('status')

        if self.request.GET.get('maintenance_type'):
            filters['maintenance_type_id'] = self.request.GET.get('maintenance_type')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        company = self.request.user.company

        maintenances = AssetMaintenance.objects.filter(
            company=company
        ).select_related(
            'asset',
            'maintenance_type',
            'branch'
        ).order_by('-scheduled_date')

        # تطبيق الفلاتر
        if filters.get('date_from'):
            maintenances = maintenances.filter(
                scheduled_date__gte=filters['date_from']
            )

        if filters.get('date_to'):
            maintenances = maintenances.filter(
                scheduled_date__lte=filters['date_to']
            )

        if filters.get('asset_id'):
            maintenances = maintenances.filter(asset_id=filters['asset_id'])

        if filters.get('status'):
            maintenances = maintenances.filter(status=filters['status'])

        if filters.get('maintenance_type_id'):
            maintenances = maintenances.filter(
                maintenance_type_id=filters['maintenance_type_id']
            )

        return maintenances

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        # التكلفة الإجمالية (للصيانات المكتملة فقط)
        total_cost = queryset.filter(
            status='completed'
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')

        # العدد حسب الحالة
        by_status = queryset.values('status').annotate(
            count=Count('id'),
            total_cost=Sum('total_cost')
        )

        # أعلى 10 أصول من حيث تكاليف الصيانة
        by_asset = queryset.filter(
            status='completed'
        ).values(
            'asset__asset_number',
            'asset__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-total_cost')[:10]

        # حسب النوع
        by_type = queryset.values(
            'maintenance_type__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-count')

        return {
            'total_cost': total_cost,
            'total_count': queryset.count(),
            'completed_count': queryset.filter(status='completed').count(),
            'pending_count': queryset.filter(status='scheduled').count(),
            'by_status': by_status,
            'by_asset': by_asset,
            'by_type': by_type,
        }

    def get_report_filters(self):
        """الفلاتر المطبقة"""
        filters_display = {}

        if self.request.GET.get('date_from'):
            filters_display['من تاريخ'] = self.request.GET.get('date_from')

        if self.request.GET.get('date_to'):
            filters_display['إلى تاريخ'] = self.request.GET.get('date_to')

        if self.request.GET.get('status'):
            status_dict = dict(AssetMaintenance.STATUS_CHOICES)
            filters_display['الحالة'] = status_dict.get(self.request.GET.get('status'), '')

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'رقم الصيانة',
            'التاريخ المجدول',
            'رقم الأصل',
            'اسم الأصل',
            'نوع الصيانة',
            'الحالة',
            'التكلفة الإجمالية',
            'تاريخ الإكمال',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        for maint in queryset:
            data.append([
                maint.maintenance_number,
                format_date(maint.scheduled_date),
                maint.asset.asset_number,
                maint.asset.name,
                maint.maintenance_type.name,
                maint.get_status_display(),
                float(maint.total_cost),
                format_date(maint.completion_date) if maint.completion_date else '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        return [
            'الإجمالي',
            '',
            '',
            f"{stats['total_count']} صيانة",
            '',
            f"مكتمل: {stats['completed_count']}",
            float(stats['total_cost']),
            '',
        ]


class AssetMovementReportView(BaseReportView):
    """تقرير حركة الأصول"""

    template_name = 'assets/reports/movement_report.html'
    permission_required = 'assets.view_assettransaction'
    report_name = 'asset_movement'
    report_title = 'تقرير حركة الأصول'

    def get_filters_from_request(self):
        """استخراج الفلاتر"""
        filters = super().get_filters_from_request()

        if self.request.GET.get('transaction_type'):
            filters['transaction_type'] = self.request.GET.get('transaction_type')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        company = self.request.user.company

        transactions = AssetTransaction.objects.filter(
            company=company
        ).select_related(
            'asset',
            'asset__category',
            'branch'
        ).order_by('-transaction_date')

        # تطبيق الفلاتر
        if filters.get('date_from'):
            transactions = transactions.filter(
                transaction_date__gte=filters['date_from']
            )

        if filters.get('date_to'):
            transactions = transactions.filter(
                transaction_date__lte=filters['date_to']
            )

        if filters.get('transaction_type'):
            transactions = transactions.filter(
                transaction_type=filters['transaction_type']
            )

        if filters.get('branch_id'):
            transactions = transactions.filter(
                branch_id=filters['branch_id']
            )

        return transactions

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        # إجمالي المبالغ
        total_amount = queryset.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # حسب النوع
        by_type = queryset.values(
            'transaction_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # عمليات الشراء
        purchases = queryset.filter(transaction_type='purchase')
        purchase_total = purchases.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # عمليات البيع
        sales = queryset.filter(transaction_type='sale')
        sale_total = sales.aggregate(
            total=Sum('sale_price')
        )['total'] or Decimal('0')

        total_gain_loss = sales.aggregate(
            total=Sum('gain_loss')
        )['total'] or Decimal('0')

        return {
            'total_amount': total_amount,
            'total_count': queryset.count(),
            'by_type': by_type,
            'purchase_count': purchases.count(),
            'purchase_total': purchase_total,
            'sale_count': sales.count(),
            'sale_total': sale_total,
            'total_gain_loss': total_gain_loss,
        }

    def get_report_filters(self):
        """الفلاتر المطبقة"""
        filters_display = {}

        if self.request.GET.get('transaction_type'):
            type_dict = dict(AssetTransaction.TRANSACTION_TYPES)
            filters_display['نوع العملية'] = type_dict.get(
                self.request.GET.get('transaction_type'), ''
            )

        if self.request.GET.get('date_from'):
            filters_display['من تاريخ'] = self.request.GET.get('date_from')

        if self.request.GET.get('date_to'):
            filters_display['إلى تاريخ'] = self.request.GET.get('date_to')

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'رقم العملية',
            'التاريخ',
            'نوع العملية',
            'رقم الأصل',
            'اسم الأصل',
            'المبلغ',
            'سعر البيع',
            'الربح/الخسارة',
            'الفرع',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        for trans in queryset:
            data.append([
                trans.transaction_number,
                format_date(trans.transaction_date),
                trans.get_transaction_type_display(),
                trans.asset.asset_number,
                trans.asset.name,
                float(trans.amount),
                float(trans.sale_price or 0),
                float(trans.gain_loss or 0),
                trans.branch.name if trans.branch else '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        return [
            'الإجمالي',
            '',
            f"{stats['total_count']} عملية",
            '',
            '',
            float(stats['total_amount']),
            float(stats['sale_total']),
            float(stats['total_gain_loss']),
            '',
        ]


class AssetByCostCenterReportView(BaseReportView):
    """تقرير الأصول حسب مركز التكلفة"""

    template_name = 'assets/reports/by_cost_center_report.html'
    permission_required = 'assets.view_asset'
    report_name = 'asset_by_cost_center'
    report_title = 'تقرير الأصول حسب مركز التكلفة'
    pdf_orientation = 'landscape'

    def get_filters_from_request(self):
        """استخراج الفلاتر"""
        filters = super().get_filters_from_request()

        if self.request.GET.get('cost_center'):
            filters['cost_center_id'] = self.request.GET.get('cost_center')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        company = self.request.user.company

        assets = Asset.objects.filter(
            company=company
        ).select_related(
            'category',
            'cost_center',
            'branch',
            'condition'
        ).order_by('cost_center__name', 'category__name', 'asset_number')

        # تطبيق الفلاتر
        if filters.get('cost_center_id'):
            assets = assets.filter(cost_center_id=filters['cost_center_id'])

        if filters.get('category_id'):
            assets = assets.filter(category_id=filters['category_id'])

        if filters.get('branch_id'):
            assets = assets.filter(branch_id=filters['branch_id'])

        return assets

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        from apps.accounting.models import CostCenter

        # حسب مركز التكلفة
        by_cost_center = queryset.values(
            'cost_center__code',
            'cost_center__name'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        ).order_by('cost_center__name')

        # حسب مركز التكلفة والفئة
        by_cost_center_category = queryset.values(
            'cost_center__name',
            'category__name'
        ).annotate(
            count=Count('id'),
            total_book_value=Sum('book_value')
        ).order_by('cost_center__name', 'category__name')

        # الإجماليات
        totals = queryset.aggregate(
            total_count=Count('id'),
            total_cost=Sum('original_cost'),
            total_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value')
        )

        # عدد مراكز التكلفة
        cost_centers_count = queryset.values('cost_center').distinct().count()

        return {
            'by_cost_center': by_cost_center,
            'by_cost_center_category': by_cost_center_category,
            'totals': totals,
            'cost_centers_count': cost_centers_count,
        }

    def get_report_filters(self):
        """الفلاتر المطبقة"""
        from apps.accounting.models import CostCenter

        filters_display = {}

        if self.request.GET.get('cost_center'):
            try:
                cost_center = CostCenter.objects.get(
                    id=self.request.GET.get('cost_center')
                )
                filters_display['مركز التكلفة'] = cost_center.name
            except:
                pass

        if self.request.GET.get('category'):
            try:
                category = AssetCategory.objects.get(
                    id=self.request.GET.get('category')
                )
                filters_display['الفئة'] = category.name
            except:
                pass

        if self.request.GET.get('branch'):
            try:
                branch = Branch.objects.get(id=self.request.GET.get('branch'))
                filters_display['الفرع'] = branch.name
            except:
                pass

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'مركز التكلفة',
            'رقم الأصل',
            'اسم الأصل',
            'الفئة',
            'التكلفة الأصلية',
            'الإهلاك المتراكم',
            'القيمة الدفترية',
            'الحالة',
            'الفرع',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        for asset in queryset:
            data.append([
                asset.cost_center.name if asset.cost_center else 'غير محدد',
                asset.asset_number,
                asset.name,
                asset.category.name,
                float(asset.original_cost),
                float(asset.accumulated_depreciation),
                float(asset.book_value),
                asset.get_status_display(),
                asset.branch.name if asset.branch else '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        totals = stats['totals']

        return [
            'الإجمالي',
            '',
            f"{totals['total_count']} أصل",
            '',
            float(totals['total_cost'] or 0),
            float(totals['total_depreciation'] or 0),
            float(totals['total_book_value'] or 0),
            '',
            '',
        ]


class AssetNearEndOfLifeReportView(BaseReportView):
    """تقرير الأصول القريبة من نهاية العمر الافتراضي"""

    template_name = 'assets/reports/near_end_of_life_report.html'
    permission_required = 'assets.view_asset'
    report_name = 'asset_near_end_of_life'
    report_title = 'تقرير الأصول القريبة من نهاية العمر الافتراضي'

    def get_filters_from_request(self):
        """استخراج الفلاتر"""
        filters = super().get_filters_from_request()

        # عدد الأشهر المتبقية (افتراضي: 6 أشهر)
        filters['months_remaining'] = int(
            self.request.GET.get('months_remaining', 6)
        )

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        from datetime import date
        from dateutil.relativedelta import relativedelta

        company = self.request.user.company

        # الأصول النشطة فقط
        assets = Asset.objects.filter(
            company=company,
            status='active'
        ).select_related(
            'category',
            'branch',
            'cost_center',
            'condition'
        )

        # تطبيق الفلاتر الأساسية
        if filters.get('category_id'):
            assets = assets.filter(category_id=filters['category_id'])

        if filters.get('branch_id'):
            assets = assets.filter(branch_id=filters['branch_id'])

        # حساب الأصول القريبة من نهاية العمر
        months_threshold = filters.get('months_remaining', 6)
        today = date.today()

        near_end_assets = []
        for asset in assets:
            # حساب تاريخ نهاية العمر
            end_of_life_date = asset.depreciation_start_date + relativedelta(
                months=asset.useful_life_months
            )

            # حساب الأشهر المتبقية
            months_left = (end_of_life_date.year - today.year) * 12 + \
                          (end_of_life_date.month - today.month)

            # إذا كان قريب من النهاية
            if 0 <= months_left <= months_threshold:
                asset.end_of_life_date = end_of_life_date
                asset.months_remaining = months_left
                asset.days_remaining = (end_of_life_date - today).days
                near_end_assets.append(asset)

        # ترتيب حسب الأشهر المتبقية (الأقرب أولاً)
        near_end_assets.sort(key=lambda x: x.months_remaining)

        return near_end_assets

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        # الإجماليات
        total_count = len(queryset)

        if queryset:
            total_original_cost = sum(asset.original_cost for asset in queryset)
            total_book_value = sum(asset.book_value for asset in queryset)

            # حسب الفئة
            by_category = {}
            for asset in queryset:
                cat_name = asset.category.name
                if cat_name not in by_category:
                    by_category[cat_name] = {
                        'count': 0,
                        'total_book_value': Decimal('0')
                    }
                by_category[cat_name]['count'] += 1
                by_category[cat_name]['total_book_value'] += asset.book_value

            # حسب الأشهر المتبقية
            by_months = {
                '0-3': 0,
                '4-6': 0,
                '7-12': 0,
            }

            for asset in queryset:
                if asset.months_remaining <= 3:
                    by_months['0-3'] += 1
                elif asset.months_remaining <= 6:
                    by_months['4-6'] += 1
                else:
                    by_months['7-12'] += 1
        else:
            total_original_cost = Decimal('0')
            total_book_value = Decimal('0')
            by_category = {}
            by_months = {'0-3': 0, '4-6': 0, '7-12': 0}

        return {
            'total_count': total_count,
            'total_original_cost': total_original_cost,
            'total_book_value': total_book_value,
            'by_category': by_category,
            'by_months': by_months,
        }

    def prepare_report_data(self, queryset):
        """تحضير بيانات التقرير للعرض"""
        # نعيد القائمة كما هي لأنها معالجة مسبقاً
        return queryset

    def get_report_filters(self):
        """الفلاتر المطبقة"""
        filters_display = {}

        filters_display['الأشهر المتبقية'] = self.request.GET.get(
            'months_remaining', '6'
        ) + ' أشهر أو أقل'

        if self.request.GET.get('category'):
            try:
                category = AssetCategory.objects.get(
                    id=self.request.GET.get('category')
                )
                filters_display['الفئة'] = category.name
            except:
                pass

        if self.request.GET.get('branch'):
            try:
                branch = Branch.objects.get(id=self.request.GET.get('branch'))
                filters_display['الفرع'] = branch.name
            except:
                pass

        return filters_display

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'رقم الأصل',
            'اسم الأصل',
            'الفئة',
            'تاريخ بداية الإهلاك',
            'العمر الافتراضي (شهر)',
            'تاريخ نهاية العمر',
            'الأشهر المتبقية',
            'الأيام المتبقية',
            'القيمة الدفترية',
            'الفرع',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        for asset in queryset:
            data.append([
                asset.asset_number,
                asset.name,
                asset.category.name,
                format_date(asset.depreciation_start_date),
                asset.useful_life_months,
                format_date(asset.end_of_life_date),
                asset.months_remaining,
                asset.days_remaining,
                float(asset.book_value),
                asset.branch.name if asset.branch else '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        return [
            'الإجمالي',
            f"{stats['total_count']} أصل",
            '',
            '',
            '',
            '',
            '',
            '',
            float(stats['total_book_value']),
            '',
        ]


class FairValueReportView(BaseReportView):
    """تقرير القيمة العادلة مقابل القيمة الدفترية"""

    template_name = 'assets/reports/fair_value_report.html'
    permission_required = 'assets.view_asset'
    report_name = 'fair_value_report'
    report_title = 'تقرير القيمة العادلة مقابل القيمة الدفترية'
    pdf_orientation = 'landscape'

    def get_report_queryset(self, filters):
        """الحصول على QuerySet"""
        from ..models import AssetValuation

        company = self.request.user.company

        # الحصول على آخر تقييم لكل أصل
        latest_valuations = AssetValuation.objects.filter(
            asset__company=company,
            status='approved'
        ).values('asset').annotate(
            latest_date=Max('valuation_date')
        )

        # الأصول مع التقييمات
        assets = Asset.objects.filter(
            company=company,
            id__in=[v['asset'] for v in latest_valuations]
        ).select_related(
            'category',
            'branch'
        ).prefetch_related('valuations')

        # تطبيق الفلاتر
        if filters.get('category_id'):
            assets = assets.filter(category_id=filters['category_id'])

        if filters.get('branch_id'):
            assets = assets.filter(branch_id=filters['branch_id'])

        return assets

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        total_book_value = Decimal('0')
        total_fair_value = Decimal('0')
        total_difference = Decimal('0')

        overvalued_count = 0  # القيمة الدفترية > القيمة العادلة
        undervalued_count = 0  # القيمة الدفترية < القيمة العادلة

        for asset in queryset:
            # الحصول على آخر تقييم
            latest_valuation = asset.valuations.filter(
                status='approved'
            ).order_by('-valuation_date').first()

            if latest_valuation:
                book_value = asset.book_value
                fair_value = latest_valuation.new_value
                difference = fair_value - book_value

                total_book_value += book_value
                total_fair_value += fair_value
                total_difference += difference

                if difference < 0:
                    overvalued_count += 1
                elif difference > 0:
                    undervalued_count += 1

        return {
            'total_count': queryset.count(),
            'total_book_value': total_book_value,
            'total_fair_value': total_fair_value,
            'total_difference': total_difference,
            'overvalued_count': overvalued_count,
            'undervalued_count': undervalued_count,
            'variance_percentage': (
                (total_difference / total_book_value * 100)
                if total_book_value > 0 else 0
            ),
        }

    def prepare_report_data(self, queryset):
        """تحضير البيانات للعرض"""
        data = []

        for asset in queryset:
            # الحصول على آخر تقييم
            latest_valuation = asset.valuations.filter(
                status='approved'
            ).order_by('-valuation_date').first()

            if latest_valuation:
                data.append({
                    'asset': asset,
                    'valuation': latest_valuation,
                    'difference': latest_valuation.new_value - asset.book_value,
                    'variance_percentage': (
                        ((latest_valuation.new_value - asset.book_value) / asset.book_value * 100)
                        if asset.book_value > 0 else 0
                    )
                })

        return data

    def get_export_headers(self):
        """رؤوس الأعمدة"""
        return [
            'رقم الأصل',
            'اسم الأصل',
            'الفئة',
            'القيمة الدفترية',
            'القيمة العادلة',
            'الفرق',
            'نسبة الفرق %',
            'تاريخ التقييم',
            'المقيّم',
        ]

    def prepare_export_data(self, queryset):
        """تحضير البيانات"""
        data = []

        report_data = self.prepare_report_data(queryset)

        for item in report_data:
            asset = item['asset']
            valuation = item['valuation']

            data.append([
                asset.asset_number,
                asset.name,
                asset.category.name,
                float(asset.book_value),
                float(valuation.new_value),
                float(item['difference']),
                f"{item['variance_percentage']:.2f}%",
                format_date(valuation.valuation_date),
                valuation.appraiser_name or '-',
            ])

        return data

    def get_report_summary(self):
        """صف الإجماليات"""
        filters = self.get_filters_from_request()
        queryset = self.get_report_queryset(filters)
        stats = self.get_report_statistics(queryset)

        return [
            'الإجمالي',
            f"{stats['total_count']} أصل",
            '',
            float(stats['total_book_value']),
            float(stats['total_fair_value']),
            float(stats['total_difference']),
            f"{stats['variance_percentage']:.2f}%",
            '',
            '',
        ]
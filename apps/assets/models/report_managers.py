# apps/assets/models/report_managers.py
"""
مديرو التقارير للأصول الثابتة
- استعلامات معقدة للتقارير
"""

from django.db import models
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
import datetime


class AssetReportManager(models.Manager):
    """مدير تقارير الأصول"""

    def by_category(self, company, date=None):
        """تقرير الأصول حسب الفئة"""
        from .asset_models import Asset, AssetCategory

        if date is None:
            date = datetime.date.today()

        # الأصول النشطة فقط
        assets = self.filter(
            company=company,
            status='active'
        )

        report = assets.values(
            'category__code',
            'category__name'
        ).annotate(
            asset_count=Count('id'),
            total_original_cost=Sum('original_cost'),
            total_accumulated_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
        ).order_by('category__code')

        return report

    def by_branch(self, company, date=None):
        """تقرير الأصول حسب الفرع"""
        if date is None:
            date = datetime.date.today()

        assets = self.filter(
            company=company,
            status='active'
        )

        report = assets.values(
            'branch__code',
            'branch__name'
        ).annotate(
            asset_count=Count('id'),
            total_original_cost=Sum('original_cost'),
            total_accumulated_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
        ).order_by('branch__code')

        return report

    def by_cost_center(self, company, date=None):
        """تقرير الأصول حسب مركز التكلفة"""
        if date is None:
            date = datetime.date.today()

        assets = self.filter(
            company=company,
            status='active',
            cost_center__isnull=False
        )

        report = assets.values(
            'cost_center__code',
            'cost_center__name'
        ).annotate(
            asset_count=Count('id'),
            total_original_cost=Sum('original_cost'),
            total_accumulated_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
        ).order_by('cost_center__code')

        return report

    def depreciation_schedule(self, company, months=12):
        """جدول الإهلاك المستقبلي"""
        from .asset_models import Asset
        from dateutil.relativedelta import relativedelta

        today = datetime.date.today()
        assets = self.filter(
            company=company,
            status='active',
            depreciation_status='active'
        ).exclude(
            depreciation_method__method_type='units_of_production'
        )

        schedule = []

        for i in range(months):
            month_date = today + relativedelta(months=i)
            month_name = month_date.strftime('%Y-%m')

            monthly_depreciation = Decimal('0')

            for asset in assets:
                # حساب الإهلاك الشهري لكل أصل
                if asset.depreciation_method.method_type == 'straight_line':
                    depreciable_amount = asset.get_depreciable_amount()
                    monthly_dep = depreciable_amount / asset.useful_life_months
                elif asset.depreciation_method.method_type == 'declining_balance':
                    rate = asset.depreciation_method.rate_percentage / 100
                    current_book_value = asset.book_value
                    monthly_dep = current_book_value * (rate / 12)
                else:
                    continue

                # التأكد من عدم تجاوز المبلغ القابل للإهلاك
                remaining = asset.get_depreciable_amount() - asset.accumulated_depreciation
                if monthly_dep > remaining:
                    monthly_dep = remaining

                if monthly_dep > 0:
                    monthly_depreciation += monthly_dep

            schedule.append({
                'month': month_name,
                'depreciation_amount': monthly_depreciation
            })

        return schedule

    def book_value_summary(self, company, date=None):
        """ملخص القيمة الدفترية"""
        if date is None:
            date = datetime.date.today()

        summary = self.filter(
            company=company,
            status='active'
        ).aggregate(
            total_assets=Count('id'),
            total_original_cost=Sum('original_cost'),
            total_accumulated_depreciation=Sum('accumulated_depreciation'),
            total_book_value=Sum('book_value'),
            total_salvage_value=Sum('salvage_value'),
        )

        # حساب نسبة الإهلاك
        if summary['total_original_cost']:
            summary['depreciation_percentage'] = (
                summary['total_accumulated_depreciation'] /
                summary['total_original_cost']
            ) * 100
        else:
            summary['depreciation_percentage'] = 0

        return summary

    def disposed_assets(self, company, start_date, end_date):
        """الأصول المستبعدة خلال فترة"""
        from .transaction_models import AssetTransaction

        transactions = AssetTransaction.objects.filter(
            company=company,
            transaction_type__in=['sale', 'disposal'],
            transaction_date__range=[start_date, end_date],
            status='completed'
        ).select_related('asset', 'business_partner')

        report = []
        for trans in transactions:
            report.append({
                'transaction_number': trans.transaction_number,
                'transaction_date': trans.transaction_date,
                'asset_number': trans.asset.asset_number,
                'asset_name': trans.asset.name,
                'transaction_type': trans.get_transaction_type_display(),
                'original_cost': trans.asset.original_cost,
                'accumulated_depreciation': trans.asset.accumulated_depreciation,
                'book_value': trans.book_value_at_sale or trans.asset.book_value,
                'sale_price': trans.sale_price or Decimal('0'),
                'gain_loss': trans.gain_loss or Decimal('0'),
            })

        return report

    def fully_depreciated_assets(self, company):
        """الأصول المهلكة بالكامل"""
        assets = self.filter(
            company=company,
            status='active'
        ).annotate(
            depreciable_amount=F('original_cost') - F('salvage_value'),
            depreciation_percentage=Case(
                When(original_cost=0, then=Value(0)),
                default=(F('accumulated_depreciation') * 100.0) / F('original_cost'),
                output_field=DecimalField()
            )
        ).filter(
            depreciation_percentage__gte=90
        ).order_by('-depreciation_percentage')

        return assets

    def maintenance_due(self, company, days=30):
        """الأصول التي تحتاج صيانة قريباً"""
        from .maintenance_models import MaintenanceSchedule

        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=days)

        schedules = MaintenanceSchedule.objects.filter(
            company=company,
            is_active=True,
            next_maintenance_date__lte=due_date,
            next_maintenance_date__gte=today
        ).select_related('asset', 'maintenance_type').order_by('next_maintenance_date')

        return schedules

    def maintenance_cost_analysis(self, company, start_date, end_date):
        """تحليل تكاليف الصيانة"""
        from .maintenance_models import AssetMaintenance

        maintenances = AssetMaintenance.objects.filter(
            company=company,
            status='completed',
            completion_date__range=[start_date, end_date]
        )

        # حسب الأصل
        by_asset = maintenances.values(
            'asset__asset_number',
            'asset__name'
        ).annotate(
            maintenance_count=Count('id'),
            total_cost=Sum('total_cost'),
            avg_cost=models.Avg('total_cost')
        ).order_by('-total_cost')

        # حسب النوع
        by_type = maintenances.values(
            'maintenance_type__name'
        ).annotate(
            maintenance_count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-total_cost')

        # حسب التصنيف
        by_category = maintenances.values(
            'maintenance_category'
        ).annotate(
            maintenance_count=Count('id'),
            total_cost=Sum('total_cost')
        ).order_by('-total_cost')

        return {
            'by_asset': list(by_asset),
            'by_type': list(by_type),
            'by_category': list(by_category),
            'total_cost': maintenances.aggregate(total=Sum('total_cost'))['total'] or Decimal('0'),
            'total_count': maintenances.count()
        }

    def warranty_expiring_soon(self, company, days=30):
        """الأصول التي ستنتهي ضماناتها قريباً"""
        today = datetime.date.today()
        expiry_date = today + datetime.timedelta(days=days)

        assets = self.filter(
            company=company,
            status='active',
            warranty_end_date__isnull=False,
            warranty_end_date__lte=expiry_date,
            warranty_end_date__gte=today
        ).order_by('warranty_end_date')

        return assets

    def insurance_expiring_soon(self, company, days=30):
        """الأصول التي ستنتهي تأميناتها قريباً"""
        from .insurance_models import AssetInsurance

        today = datetime.date.today()
        expiry_date = today + datetime.timedelta(days=days)

        insurances = AssetInsurance.objects.filter(
            company=company,
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('asset', 'insurance_company').order_by('end_date')

        return insurances

    def assets_needing_physical_count(self, company):
        """الأصول التي تحتاج جرد"""
        from .asset_models import Asset

        assets = []
        for asset in self.filter(company=company, status='active'):
            if asset.needs_physical_count():
                assets.append(asset)

        return assets

    def inactive_assets(self, company, days=30):
        """الأصول المعطلة لفترة طويلة"""
        threshold_date = datetime.date.today() - datetime.timedelta(days=days)

        assets = self.filter(
            company=company,
            status='under_maintenance'
        ).annotate(
            last_maintenance_date=models.Max('maintenances__start_date')
        ).filter(
            last_maintenance_date__lt=threshold_date
        )

        return assets

    def asset_movement_report(self, company, start_date, end_date):
        """تقرير حركة الأصول (شراء/بيع/تحويل)"""
        from .transaction_models import AssetTransaction, AssetTransfer

        # المعاملات
        transactions = AssetTransaction.objects.filter(
            company=company,
            transaction_date__range=[start_date, end_date]
        ).values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # التحويلات
        transfers = AssetTransfer.objects.filter(
            company=company,
            transfer_date__range=[start_date, end_date],
            status='completed'
        ).count()

        return {
            'transactions': list(transactions),
            'transfers': transfers
        }
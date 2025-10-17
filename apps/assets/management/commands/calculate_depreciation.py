# Path: apps/assets/management/commands/calculate_depreciation.py
"""
Management Command لاحتساب الإهلاك الشهري التلقائي
يمكن جدولته في Cron للتنفيذ التلقائي نهاية كل شهر
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal
import datetime

from apps.assets.models import Asset, AssetDepreciation
from apps.assets.utils import DepreciationCalculator, generate_depreciation_journal_entry
from apps.core.models import Company


class Command(BaseCommand):
    help = 'احتساب الإهلاك الشهري للأصول الثابتة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='تاريخ الاحتساب (YYYY-MM-DD) - افتراضي: آخر يوم من الشهر الماضي'
        )
        parser.add_argument(
            '--company',
            type=int,
            help='معرف الشركة - اتركه فارغاً لجميع الشركات'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='تجربة بدون حفظ (للاختبار فقط)'
        )

    def handle(self, *args, **options):
        # تحديد تاريخ الاحتساب
        if options['date']:
            try:
                calculation_date = datetime.datetime.strptime(
                    options['date'],
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                raise CommandError('تنسيق التاريخ غير صحيح. استخدم YYYY-MM-DD')
        else:
            # آخر يوم من الشهر الماضي
            today = datetime.date.today()
            first_day_this_month = today.replace(day=1)
            calculation_date = first_day_this_month - datetime.timedelta(days=1)

        self.stdout.write(
            self.style.WARNING(f'📅 تاريخ الاحتساب: {calculation_date}')
        )

        # تحديد الشركات
        if options['company']:
            companies = Company.objects.filter(id=options['company'], is_active=True)
            if not companies.exists():
                raise CommandError(f'الشركة #{options["company"]} غير موجودة')
        else:
            companies = Company.objects.filter(is_active=True)

        self.stdout.write(
            self.style.WARNING(f'🏢 عدد الشركات: {companies.count()}')
        )

        # احتساب لكل شركة
        total_assets = 0
        total_depreciation = Decimal('0.00')
        total_errors = 0

        for company in companies:
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(
                self.style.HTTP_INFO(f'🏢 الشركة: {company.name}')
            )
            self.stdout.write(f'{"=" * 60}')

            result = self._calculate_for_company(
                company,
                calculation_date,
                options['dry_run']
            )

            total_assets += result['assets_count']
            total_depreciation += result['total_depreciation']
            total_errors += result['errors_count']

        # النتيجة النهائية
        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.SUCCESS('✅ اكتمل الاحتساب'))
        self.stdout.write(f'{"=" * 60}')
        self.stdout.write(f'📊 إجمالي الأصول: {total_assets}')
        self.stdout.write(f'💰 إجمالي الإهلاك: {total_depreciation:,.3f} د.أ')
        if total_errors > 0:
            self.stdout.write(
                self.style.ERROR(f'⚠️  الأخطاء: {total_errors}')
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n⚠️  تجربة فقط - لم يتم حفظ أي بيانات')
            )

    def _calculate_for_company(self, company, calculation_date, dry_run):
        """احتساب الإهلاك لشركة واحدة"""

        # الأصول النشطة
        assets = Asset.objects.filter(
            company=company,
            status='active',
            is_active=True
        ).select_related('category', 'depreciation_method', 'branch')

        self.stdout.write(f'📦 الأصول النشطة: {assets.count()}')

        depreciation_records = []
        total_depreciation = Decimal('0.00')
        errors = []
        skipped = 0

        for asset in assets:
            try:
                # التحقق من عدم وجود إهلاك لنفس التاريخ
                existing = AssetDepreciation.objects.filter(
                    asset=asset,
                    depreciation_date=calculation_date
                ).exists()

                if existing:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⏭️  {asset.asset_number}: موجود مسبقاً'
                        )
                    )
                    continue

                # احتساب الإهلاك
                calculator = DepreciationCalculator(asset)
                depreciation_amount = calculator.calculate_monthly_depreciation(
                    calculation_date
                )

                # تخطي الأصول المهلكة بالكامل
                if depreciation_amount == Decimal('0.00'):
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⏭️  {asset.asset_number}: مهلك بالكامل'
                        )
                    )
                    continue

                # إنشاء سجل الإهلاك
                accumulated_before = asset.accumulated_depreciation
                accumulated_after = accumulated_before + depreciation_amount
                book_value_after = asset.original_cost - accumulated_after

                if not dry_run:
                    depreciation_record = AssetDepreciation.objects.create(
                        asset=asset,
                        depreciation_date=calculation_date,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation_before=accumulated_before,
                        accumulated_depreciation_after=accumulated_after,
                        book_value_after=book_value_after,
                        calculated_by=None  # System
                    )

                    # تحديث الأصل
                    asset.accumulated_depreciation = accumulated_after
                    asset.book_value = book_value_after
                    asset.save()

                    depreciation_records.append(depreciation_record)

                total_depreciation += depreciation_amount

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ {asset.asset_number}: {depreciation_amount:,.3f} د.أ'
                    )
                )

            except Exception as e:
                errors.append(f'{asset.asset_number}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {asset.asset_number}: {str(e)}')
                )

        # توليد القيد المحاسبي
        if depreciation_records and not dry_run:
            try:
                # اختيار أول فرع متاح
                branch = company.branches.filter(is_active=True).first()

                if branch:
                    journal_entry = generate_depreciation_journal_entry(
                        company,
                        branch,
                        calculation_date,
                        depreciation_records
                    )

                    # ربط القيد بسجلات الإهلاك
                    for record in depreciation_records:
                        record.journal_entry = journal_entry
                        record.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n💼 القيد المحاسبي: {journal_entry.number}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️  لم يتم إنشاء قيد: لا يوجد فرع نشط')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ خطأ في القيد المحاسبي: {str(e)}')
                )

        # ملخص النتائج
        self.stdout.write(f'\n📈 النتائج:')
        self.stdout.write(f'  ✅ تم احتسابه: {len(depreciation_records)}')
        self.stdout.write(f'  ⏭️  تم تخطيه: {skipped}')
        self.stdout.write(f'  ❌ أخطاء: {len(errors)}')
        self.stdout.write(f'  💰 الإجمالي: {total_depreciation:,.3f} د.أ')

        return {
            'assets_count': len(depreciation_records),
            'total_depreciation': total_depreciation,
            'errors_count': len(errors)
        }
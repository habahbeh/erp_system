# apps/assets/management/commands/generate_test_data.py
"""
Management Command لتوليد بيانات تجريبية شاملة لنظام الأصول الثابتة
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import random

from apps.core.models import Company, Branch, User
from apps.accounting.models import Account, AccountType, CostCenter
from apps.assets.models import (
    AssetCategory,
    DepreciationMethod,
    AssetCondition,
    Asset,
    AssetTransaction,
    AssetDepreciation,
    AssetMaintenance,
    MaintenanceType,
    AssetValuation,
)
from apps.assets.utils import DepreciationCalculator


class Command(BaseCommand):
    help = 'توليد بيانات تجريبية شاملة لنظام الأصول الثابتة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assets',
            type=int,
            default=50,
            help='عدد الأصول المراد توليدها (افتراضي: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='حذف البيانات الموجودة قبل التوليد'
        )

    def handle(self, *args, **options):
        assets_count = options['assets']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 بدء توليد البيانات التجريبية لنظام الأصول الثابتة'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        try:
            with transaction.atomic():
                # الحصول على الشركة والمستخدم
                company = Company.objects.first()
                if not company:
                    self.stdout.write(self.style.ERROR('❌ لا توجد شركة في النظام!'))
                    return

                user = User.objects.filter(company=company, is_superuser=True).first()
                if not user:
                    user = User.objects.filter(company=company).first()

                if not user:
                    self.stdout.write(self.style.ERROR('❌ لا يوجد مستخدمون في النظام!'))
                    return

                # حذف البيانات إذا طُلب ذلك
                if clear_data:
                    self.clear_existing_data(company)

                # 1. إنشاء الإعدادات الأساسية
                self.stdout.write('\n📋 المرحلة 1: إنشاء الإعدادات الأساسية...')
                depreciation_methods = self.create_depreciation_methods(company)
                conditions = self.create_conditions()
                categories = self.create_categories(company, depreciation_methods)
                maintenance_types = self.create_maintenance_types()

                # 2. إنشاء الأصول
                self.stdout.write('\n🏢 المرحلة 2: إنشاء الأصول...')
                assets = self.create_assets(
                    company, user, categories, conditions, assets_count
                )

                # 3. إنشاء عمليات الشراء
                self.stdout.write('\n💰 المرحلة 3: إنشاء عمليات الشراء...')
                self.create_purchase_transactions(company, user, assets)

                # 4. إنشاء سجلات الإهلاك
                self.stdout.write('\n📉 المرحلة 4: حساب وتسجيل الإهلاك...')
                self.create_depreciation_records(assets)

                # 5. إنشاء الصيانة
                self.stdout.write('\n🔧 المرحلة 5: إنشاء سجلات الصيانة...')
                self.create_maintenance_records(company, user, assets, maintenance_types)

                # 6. إنشاء بعض عمليات البيع
                self.stdout.write('\n💵 المرحلة 6: إنشاء عمليات البيع...')
                self.create_sale_transactions(company, user, assets)

                # 7. إنشاء تقييمات
                self.stdout.write('\n📊 المرحلة 7: إنشاء تقييمات الأصول...')
                self.create_valuations(assets)

                # ملخص نهائي
                self.print_summary(company)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ خطأ: {str(e)}'))
            import traceback
            traceback.print_exc()

    def clear_existing_data(self, company):
        """حذف البيانات الموجودة"""
        self.stdout.write(self.style.WARNING('🗑️  حذف البيانات الموجودة...'))

        AssetDepreciation.objects.filter(asset__company=company).delete()
        AssetValuation.objects.filter(asset__company=company).delete()
        AssetMaintenance.objects.filter(asset__company=company).delete()
        AssetTransaction.objects.filter(asset__company=company).delete()
        Asset.objects.filter(company=company).delete()
        AssetCategory.objects.filter(company=company).delete()

        # حذف بدون company
        DepreciationMethod.objects.all().delete()
        AssetCondition.objects.all().delete()
        MaintenanceType.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('   ✅ تم حذف البيانات'))

    def create_depreciation_methods(self, company):
        """إنشاء طرق الإهلاك"""
        methods_data = [
            {
                'code': 'SL',
                'name': 'القسط الثابت',
                'name_en': 'Straight Line',
                'method_type': 'straight_line',
                'description': 'طريقة القسط الثابت - الأكثر شيوعاً'
            },
            {
                'code': 'DB',
                'name': 'القسط المتناقص المضاعف',
                'name_en': 'Double Declining Balance',
                'method_type': 'declining_balance',
                'rate_percentage': Decimal('200'),
                'description': 'طريقة القسط المتناقص بمعدل مضاعف'
            },
            {
                'code': 'UP',
                'name': 'وحدات الإنتاج',
                'name_en': 'Units of Production',
                'method_type': 'units_of_production',
                'description': 'الإهلاك حسب وحدات الإنتاج أو الاستخدام'
            },
        ]

        methods = []
        for data in methods_data:
            method, created = DepreciationMethod.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'name_en': data['name_en'],
                    'method_type': data['method_type'],
                    'description': data.get('description', ''),
                    'rate_percentage': data.get('rate_percentage', Decimal('100')),
                }
            )
            methods.append(method)
            if created:
                self.stdout.write(f'   ✅ تم إنشاء طريقة الإهلاك: {method.name}')

        return methods

    def create_conditions(self):
        """إنشاء حالات الأصول"""
        conditions_data = [
            {'name': 'جديد', 'name_en': 'New', 'color_code': '#28a745'},
            {'name': 'ممتاز', 'name_en': 'Excellent', 'color_code': '#20c997'},
            {'name': 'جيد جداً', 'name_en': 'Very Good', 'color_code': '#17a2b8'},
            {'name': 'جيد', 'name_en': 'Good', 'color_code': '#007bff'},
            {'name': 'مقبول', 'name_en': 'Fair', 'color_code': '#ffc107'},
        ]

        conditions = []
        for data in conditions_data:
            condition, created = AssetCondition.objects.get_or_create(
                name=data['name'],
                defaults={
                    'name_en': data['name_en'],
                    'color_code': data['color_code'],
                }
            )
            conditions.append(condition)
            if created:
                self.stdout.write(f'   ✅ تم إنشاء الحالة: {condition.name}')

        return conditions

    def create_categories(self, company, depreciation_methods):
        """إنشاء فئات الأصول"""

        # الحصول على الحسابات
        asset_type = AccountType.objects.filter(type_category='assets').first()
        expense_type = AccountType.objects.filter(type_category='expenses').first()

        asset_account = None
        accumulated_dep_account = None
        dep_expense_account = None

        if asset_type and expense_type:
            asset_account, _ = Account.objects.get_or_create(
                company=company,
                code='1200',
                defaults={
                    'name': 'الأصول الثابتة',
                    'account_type': asset_type,
                    'currency': company.base_currency,
                }
            )

            accumulated_dep_account, _ = Account.objects.get_or_create(
                company=company,
                code='1290',
                defaults={
                    'name': 'مجمع الإهلاك',
                    'account_type': asset_type,
                    'currency': company.base_currency,
                }
            )

            dep_expense_account, _ = Account.objects.get_or_create(
                company=company,
                code='5200',
                defaults={
                    'name': 'مصروف الإهلاك',
                    'account_type': expense_type,
                    'currency': company.base_currency,
                }
            )

        categories_data = [
            {'code': 'BLD', 'name': 'مباني ومنشآت', 'life': 25, 'salvage': 10},
            {'code': 'VEH', 'name': 'سيارات ومركبات', 'life': 5, 'salvage': 15},
            {'code': 'FUR', 'name': 'أثاث ومفروشات', 'life': 10, 'salvage': 5},
            {'code': 'COM', 'name': 'أجهزة كمبيوتر', 'life': 3, 'salvage': 0},
            {'code': 'MAC', 'name': 'معدات وآلات', 'life': 10, 'salvage': 10},
            {'code': 'ELE', 'name': 'أجهزة كهربائية', 'life': 7, 'salvage': 5},
        ]

        categories = []
        for data in categories_data:
            category, created = AssetCategory.objects.get_or_create(
                company=company,
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'default_depreciation_method': depreciation_methods[0],
                    'default_useful_life_months': data['life'] * 12,
                    'default_salvage_value_rate': Decimal(str(data['salvage'])),
                    'asset_account': asset_account,
                    'accumulated_depreciation_account': accumulated_dep_account,
                    'depreciation_expense_account': dep_expense_account,
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'   ✅ تم إنشاء الفئة: {category.name}')

        return categories

    def create_maintenance_types(self):
        """إنشاء أنواع الصيانة"""
        types_data = [
            {'code': 'PREV', 'name': 'صيانة وقائية', 'name_en': 'Preventive'},
            {'code': 'CORR', 'name': 'صيانة تصحيحية', 'name_en': 'Corrective'},
            {'code': 'EMER', 'name': 'صيانة طارئة', 'name_en': 'Emergency'},
        ]

        types = []
        for data in types_data:
            mtype, created = MaintenanceType.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'name_en': data['name_en']
                }
            )
            types.append(mtype)
            if created:
                self.stdout.write(f'   ✅ تم إنشاء نوع الصيانة: {mtype.name}')

        return types

    def create_assets(self, company, user, categories, conditions, count):
        """إنشاء الأصول"""

        branch = Branch.objects.filter(company=company).first()
        cost_center = CostCenter.objects.filter(company=company).first()

        asset_names = {
            'BLD': ['مبنى المكتب الرئيسي', 'مستودع رقم 1', 'فرع الجنوب'],
            'VEH': ['سيارة نيسان', 'حافلة نقل', 'شاحنة توصيل', 'جيب تويوتا'],
            'FUR': ['مكتب مدير', 'كراسي مكتبية', 'طاولة اجتماعات', 'خزانة ملفات'],
            'COM': ['حاسوب Dell', 'لابتوب HP', 'سيرفر IBM', 'طابعة شبكية'],
            'MAC': ['ماكينة تصوير', 'معدات إنتاج', 'مولد كهربائي', 'رافعة شوكية'],
            'ELE': ['مكيف هواء', 'ثلاجة عرض', 'شاشة عرض', 'كاميرات مراقبة'],
        }

        cost_ranges = {
            'BLD': (500000, 2000000),
            'VEH': (15000, 50000),
            'FUR': (500, 5000),
            'COM': (800, 3000),
            'MAC': (10000, 100000),
            'ELE': (2000, 20000),
        }

        assets = []
        asset_counter = 1

        for i in range(count):
            category = random.choice(categories)
            names_list = asset_names.get(category.code, ['أصل'])
            name = random.choice(names_list) + f' #{asset_counter}'
            asset_number = f"{category.code}-{asset_counter:04d}"

            min_cost, max_cost = cost_ranges.get(category.code, (1000, 10000))
            original_cost = Decimal(random.randint(min_cost, max_cost))
            salvage_value = original_cost * (category.default_salvage_value_rate / 100)

            days_ago = random.randint(30, 730)
            purchase_date = date.today() - timedelta(days=days_ago)
            depreciation_start = purchase_date + timedelta(days=random.randint(0, 30))
            useful_life_months = category.default_useful_life_months or 60
            condition = random.choice(conditions)

            asset = Asset.objects.create(
                company=company,
                branch=branch,
                asset_number=asset_number,
                name=name,
                category=category,
                condition=condition,
                purchase_date=purchase_date,
                purchase_invoice_number=f"INV-{random.randint(1000, 9999)}",
                original_cost=original_cost,
                salvage_value=salvage_value,
                depreciation_method=category.default_depreciation_method,
                useful_life_months=useful_life_months,
                depreciation_start_date=depreciation_start,
                cost_center=cost_center,
                physical_location=f"الطابق {random.randint(1, 5)}",
                status='active',
                created_by=user,
            )

            assets.append(asset)
            asset_counter += 1

            if (i + 1) % 10 == 0:
                self.stdout.write(f'   📦 تم إنشاء {i + 1} أصل...')

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {len(assets)} أصل'))
        return assets

    def create_purchase_transactions(self, company, user, assets):
        """إنشاء عمليات الشراء"""
        branch = Branch.objects.filter(company=company).first()

        count = 0
        for asset in assets:
            AssetTransaction.objects.create(
                company=company,
                branch=branch,
                asset=asset,
                transaction_type='purchase',
                transaction_date=asset.purchase_date,
                amount=asset.original_cost,
                payment_method=random.choice(['cash', 'bank', 'credit']),
                description=f'شراء {asset.name}',
                created_by=user,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {count} عملية شراء'))

    def create_depreciation_records(self, assets):
        """حساب وتسجيل الإهلاك"""

        total_records = 0
        for asset in assets:
            calculator = DepreciationCalculator(asset)

            current_date = asset.depreciation_start_date
            end_date = date.today()
            accumulated = Decimal('0')

            while current_date <= end_date:
                monthly_dep = calculator.calculate_monthly_depreciation(current_date)

                if monthly_dep > 0:
                    accumulated += monthly_dep
                    book_value = asset.original_cost - accumulated

                    AssetDepreciation.objects.create(
                        asset=asset,
                        depreciation_date=current_date,
                        depreciation_amount=monthly_dep,
                        accumulated_depreciation_before=accumulated - monthly_dep,
                        accumulated_depreciation_after=accumulated,
                        book_value_after=book_value,
                    )
                    total_records += 1

                current_date = current_date + relativedelta(months=1)

            asset.accumulated_depreciation = accumulated
            asset.book_value = asset.original_cost - accumulated
            asset.save()

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {total_records} سجل إهلاك'))

    def create_maintenance_records(self, company, user, assets, maintenance_types):
        """إنشاء سجلات الصيانة"""
        branch = Branch.objects.filter(company=company).first()
        maintenance_assets = random.sample(assets, int(len(assets) * 0.6))

        count = 0
        for asset in maintenance_assets:
            num_maintenances = random.randint(1, 3)

            for i in range(num_maintenances):
                days_ago = random.randint(10, 365)
                maintenance_date = date.today() - timedelta(days=days_ago)
                mtype = random.choice(maintenance_types)

                labor_cost = Decimal(random.randint(50, 500))
                parts_cost = Decimal(random.randint(0, 1000))
                total_cost = labor_cost + parts_cost
                status = random.choice(['completed', 'completed', 'scheduled'])

                AssetMaintenance.objects.create(
                    company=company,
                    branch=branch,
                    asset=asset,
                    maintenance_type=mtype,
                    scheduled_date=maintenance_date,
                    completion_date=maintenance_date if status == 'completed' else None,
                    status=status,
                    description=f'{mtype.name} - {asset.name}',
                    labor_cost=labor_cost if status == 'completed' else Decimal('0'),
                    parts_cost=parts_cost if status == 'completed' else Decimal('0'),
                    total_cost=total_cost if status == 'completed' else Decimal('0'),
                    created_by=user,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {count} سجل صيانة'))

    def create_sale_transactions(self, company, user, assets):
        """إنشاء عمليات بيع"""
        branch = Branch.objects.filter(company=company).first()
        sale_assets = random.sample(assets, max(1, int(len(assets) * 0.1)))

        count = 0
        for asset in sale_assets:
            days_after = random.randint(180, 500)
            sale_date = asset.purchase_date + timedelta(days=days_after)
            sale_price = asset.book_value * Decimal(random.uniform(0.5, 0.9))
            gain_loss = sale_price - asset.book_value

            AssetTransaction.objects.create(
                company=company,
                branch=branch,
                asset=asset,
                transaction_type='sale',
                transaction_date=sale_date,
                amount=asset.book_value,
                sale_price=sale_price,
                gain_loss=gain_loss,
                payment_method=random.choice(['cash', 'bank']),
                description=f'بيع {asset.name}',
                created_by=user,
            )

            asset.status = 'sold'
            asset.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {count} عملية بيع'))

    def create_valuations(self, assets):
        """إنشاء تقييمات"""
        active_assets = [a for a in assets if a.status == 'active']
        valuation_assets = random.sample(active_assets, max(1, int(len(active_assets) * 0.2)))

        count = 0
        for asset in valuation_assets:
            days_ago = random.randint(30, 180)
            valuation_date = date.today() - timedelta(days=days_ago)
            new_value = asset.book_value * Decimal(random.uniform(0.8, 1.2))
            difference = new_value - asset.book_value

            AssetValuation.objects.create(
                asset=asset,
                valuation_date=valuation_date,
                old_value=asset.book_value,
                new_value=new_value,
                difference=difference,
                reason='تقييم دوري',
                valuator_name=f'مقيّم {random.choice(["أحمد", "محمد"])}',
                is_approved=True,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء {count} تقييم'))

    def print_summary(self, company):
        """طباعة ملخص"""
        from django.db.models import Sum

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('📊 ملخص البيانات التجريبية'))
        self.stdout.write('=' * 70)

        total_assets = Asset.objects.filter(company=company).count()
        active = Asset.objects.filter(company=company, status='active').count()

        totals = Asset.objects.filter(company=company).aggregate(
            cost=Sum('original_cost'),
            dep=Sum('accumulated_depreciation'),
            book=Sum('book_value')
        )

        self.stdout.write(f'\n✅ إجمالي الأصول: {total_assets} (نشطة: {active})')
        self.stdout.write(f'💰 التكلفة: {totals["cost"] or 0:,.2f} دينار')
        self.stdout.write(f'📉 الإهلاك: {totals["dep"] or 0:,.2f} دينار')
        self.stdout.write(f'📊 القيمة الدفترية: {totals["book"] or 0:,.2f} دينار')

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('🎉 تم توليد البيانات بنجاح!'))
        self.stdout.write('=' * 70 + '\n')
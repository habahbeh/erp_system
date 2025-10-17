# Path: apps/assets/management/commands/create_sample_assets.py
"""
إنشاء بيانات تجريبية شاملة لنظام الأصول الثابتة
50+ أصل متنوع، عمليات، صيانة، قيود محاسبية
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import datetime
import random

from apps.assets.models import (
    AssetCategory, DepreciationMethod, AssetCondition,
    Asset, AssetDepreciation, AssetTransaction,
    MaintenanceType, MaintenanceSchedule, AssetMaintenance
)
from apps.accounting.models import Account, AccountType, CostCenter
from apps.core.models import Company, Branch, User


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية شاملة للأصول الثابتة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            default=1,
            help='معرف الشركة (افتراضي: 1)'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ الشركة #{company_id} غير موجودة'))
            return

        self.stdout.write(self.style.SUCCESS(f'🏢 الشركة: {company.name}'))
        self.stdout.write('=' * 60)

        with transaction.atomic():
            # 1. طرق الإهلاك
            self.stdout.write('\n📊 إنشاء طرق الإهلاك...')
            depreciation_methods = self._create_depreciation_methods()
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(depreciation_methods)} طريقة'))

            # 2. حالات الأصول
            self.stdout.write('\n🎨 إنشاء حالات الأصول...')
            conditions = self._create_asset_conditions()
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(conditions)} حالة'))

            # 3. فئات الأصول
            self.stdout.write('\n📁 إنشاء فئات الأصول...')
            categories = self._create_asset_categories(company, depreciation_methods)
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(categories)} فئة'))

            # 4. أنواع الصيانة
            self.stdout.write('\n🔧 إنشاء أنواع الصيانة...')
            maintenance_types = self._create_maintenance_types()
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(maintenance_types)} نوع'))

            # 5. الأصول الثابتة
            self.stdout.write('\n📦 إنشاء الأصول الثابتة...')
            assets = self._create_assets(
                company,
                categories,
                conditions,
                depreciation_methods
            )
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(assets)} أصل'))

            # 6. سجلات الإهلاك
            self.stdout.write('\n📉 إنشاء سجلات الإهلاك...')
            depreciation_count = self._create_depreciation_records(assets)
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {depreciation_count} سجل إهلاك'))

            # 7. جدولة الصيانة
            self.stdout.write('\n📅 إنشاء جدولة الصيانة...')
            schedules = self._create_maintenance_schedules(
                company,
                assets,
                maintenance_types
            )
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(schedules)} جدول'))

            # 8. سجلات الصيانة
            self.stdout.write('\n🔧 إنشاء سجلات الصيانة...')
            maintenance_count = self._create_maintenance_records(
                company,
                assets,
                maintenance_types
            )
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {maintenance_count} سجل صيانة'))

            # 9. عمليات على الأصول
            self.stdout.write('\n💼 إنشاء العمليات...')
            transactions_count = self._create_transactions(company, assets)
            self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {transactions_count} عملية'))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 تم إنشاء جميع البيانات التجريبية بنجاح!'))
        self.stdout.write('=' * 60)
        self._print_summary(company)

    def _create_depreciation_methods(self):
        """إنشاء طرق الإهلاك"""
        methods = [
            {
                'code': 'SL',
                'name': 'القسط الثابت',
                'name_en': 'Straight Line',
                'method_type': 'straight_line',
                'rate_percentage': None,
                'description': 'توزيع متساوٍ للإهلاك على مدى العمر الافتراضي'
            },
            {
                'code': 'DB',
                'name': 'القسط المتناقص',
                'name_en': 'Declining Balance',
                'method_type': 'declining_balance',
                'rate_percentage': Decimal('200.00'),
                'description': 'إهلاك أسرع في السنوات الأولى'
            },
            {
                'code': 'UOP',
                'name': 'وحدات الإنتاج',
                'name_en': 'Units of Production',
                'method_type': 'units_of_production',
                'rate_percentage': None,
                'description': 'الإهلاك حسب الاستخدام الفعلي'
            },
        ]

        created = []
        for data in methods:
            method, _ = DepreciationMethod.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            created.append(method)

        return created

    def _create_asset_conditions(self):
        """إنشاء حالات الأصول"""
        conditions_data = [
            {'name': 'جديد', 'name_en': 'New', 'color_code': '#28a745'},
            {'name': 'ممتاز', 'name_en': 'Excellent', 'color_code': '#20c997'},
            {'name': 'جيد جداً', 'name_en': 'Very Good', 'color_code': '#17a2b8'},
            {'name': 'جيد', 'name_en': 'Good', 'color_code': '#ffc107'},
            {'name': 'مقبول', 'name_en': 'Fair', 'color_code': '#fd7e14'},
            {'name': 'يحتاج صيانة', 'name_en': 'Needs Maintenance', 'color_code': '#dc3545'},
        ]

        created = []
        for data in conditions_data:
            condition, _ = AssetCondition.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            created.append(condition)

        return created

    def _create_asset_categories(self, company, depreciation_methods):
        """إنشاء فئات الأصول الهرمية"""
        straight_line = depreciation_methods[0]

        categories_data = [
            # عقارات
            {'code': 'PROP', 'name': 'عقارات', 'name_en': 'Properties', 'parent': None, 'life': 300},
            {'code': 'BLDG', 'name': 'مباني', 'name_en': 'Buildings', 'parent': 'PROP', 'life': 300},
            {'code': 'LAND', 'name': 'أراضي', 'name_en': 'Lands', 'parent': 'PROP', 'life': 0},

            # معدات
            {'code': 'EQUIP', 'name': 'معدات', 'name_en': 'Equipment', 'parent': None, 'life': 84},
            {'code': 'MACH', 'name': 'آلات ومعدات', 'name_en': 'Machinery', 'parent': 'EQUIP', 'life': 84},
            {'code': 'TOOLS', 'name': 'أدوات', 'name_en': 'Tools', 'parent': 'EQUIP', 'life': 36},

            # مركبات
            {'code': 'VEH', 'name': 'مركبات', 'name_en': 'Vehicles', 'parent': None, 'life': 60},
            {'code': 'CAR', 'name': 'سيارات', 'name_en': 'Cars', 'parent': 'VEH', 'life': 60},
            {'code': 'TRUCK', 'name': 'شاحنات', 'name_en': 'Trucks', 'parent': 'VEH', 'life': 84},

            # أثاث
            {'code': 'FURN', 'name': 'أثاث ومفروشات', 'name_en': 'Furniture', 'parent': None, 'life': 84},
            {'code': 'OFF_FURN', 'name': 'أثاث مكتبي', 'name_en': 'Office Furniture', 'parent': 'FURN', 'life': 84},

            # تكنولوجيا
            {'code': 'IT', 'name': 'تكنولوجيا المعلومات', 'name_en': 'IT', 'parent': None, 'life': 36},
            {'code': 'COMP', 'name': 'أجهزة كمبيوتر', 'name_en': 'Computers', 'parent': 'IT', 'life': 36},
            {'code': 'SERV', 'name': 'سيرفرات', 'name_en': 'Servers', 'parent': 'IT', 'life': 60},
        ]

        created = {}
        user = User.objects.filter(company=company).first()

        for data in categories_data:
            parent = created.get(data['parent']) if data['parent'] else None

            category, _ = AssetCategory.objects.get_or_create(
                company=company,
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'name_en': data['name_en'],
                    'parent': parent,
                    'default_depreciation_method': straight_line,
                    'default_useful_life_months': data['life'],
                    'default_salvage_value_rate': Decimal('10.00'),
                    'created_by': user
                }
            )
            created[data['code']] = category

        return list(created.values())

    def _create_maintenance_types(self):
        """إنشاء أنواع الصيانة"""
        types_data = [
            {'code': 'PREV', 'name': 'صيانة وقائية', 'name_en': 'Preventive'},
            {'code': 'CORR', 'name': 'صيانة تصحيحية', 'name_en': 'Corrective'},
            {'code': 'EMRG', 'name': 'صيانة طارئة', 'name_en': 'Emergency'},
            {'code': 'IMPR', 'name': 'تحسين', 'name_en': 'Improvement'},
        ]

        created = []
        for data in types_data:
            mtype, _ = MaintenanceType.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            created.append(mtype)

        return created

    def _create_assets(self, company, categories, conditions, depreciation_methods):
        """إنشاء 50+ أصل متنوع"""
        branch = company.branches.first()
        user = User.objects.filter(company=company).first()
        cost_center = CostCenter.objects.filter(company=company, is_active=True).first()

        assets_data = [
            # مباني
            {'name': 'مبنى المقر الرئيسي', 'category': 'BLDG', 'cost': 500000, 'life': 300},
            {'name': 'مبنى الفرع الشمالي', 'category': 'BLDG', 'cost': 300000, 'life': 300},

            # سيارات
            {'name': 'سيارة مازدا 6 - 2023', 'category': 'CAR', 'cost': 25000, 'life': 60},
            {'name': 'سيارة تويوتا كامري - 2022', 'category': 'CAR', 'cost': 28000, 'life': 60},
            {'name': 'سيارة هيونداي إلنترا - 2024', 'category': 'CAR', 'cost': 22000, 'life': 60},
            {'name': 'سيارة كيا أوبتيما - 2023', 'category': 'CAR', 'cost': 24000, 'life': 60},

            # شاحنات
            {'name': 'شاحنة نقل 5 طن', 'category': 'TRUCK', 'cost': 45000, 'life': 84},
            {'name': 'شاحنة نقل 10 طن', 'category': 'TRUCK', 'cost': 65000, 'life': 84},

            # معدات
            {'name': 'رافعة شوكية 3 طن', 'category': 'MACH', 'cost': 35000, 'life': 84},
            {'name': 'مولد كهربائي 100 كيلو واط', 'category': 'MACH', 'cost': 18000, 'life': 120},
            {'name': 'ضاغط هواء صناعي', 'category': 'MACH', 'cost': 8000, 'life': 84},

            # أجهزة كمبيوتر
            {'name': 'جهاز كمبيوتر Dell - مكتب المدير', 'category': 'COMP', 'cost': 1200, 'life': 36},
            {'name': 'جهاز كمبيوتر HP - المحاسبة', 'category': 'COMP', 'cost': 900, 'life': 36},
            {'name': 'لابتوب Lenovo ThinkPad', 'category': 'COMP', 'cost': 1500, 'life': 36},
            {'name': 'لابتوب MacBook Pro', 'category': 'COMP', 'cost': 2500, 'life': 48},

            # سيرفرات
            {'name': 'سيرفر Dell PowerEdge', 'category': 'SERV', 'cost': 12000, 'life': 60},
            {'name': 'سيرفر HP ProLiant', 'category': 'SERV', 'cost': 10000, 'life': 60},

            # أثاث مكتبي
            {'name': 'مكتب تنفيذي - خشب', 'category': 'OFF_FURN', 'cost': 1200, 'life': 84},
            {'name': 'كرسي مدير جلد', 'category': 'OFF_FURN', 'cost': 450, 'life': 60},
            {'name': 'طاولة اجتماعات 12 شخص', 'category': 'OFF_FURN', 'cost': 2500, 'life': 120},
            {'name': 'خزانة ملفات معدنية', 'category': 'OFF_FURN', 'cost': 600, 'life': 120},
        ]

        # إضافة المزيد من الأصول
        for i in range(1, 31):
            assets_data.append({
                'name': f'أصل تجريبي رقم {i}',
                'category': random.choice(['COMP', 'OFF_FURN', 'TOOLS', 'CAR']),
                'cost': random.randint(500, 50000),
                'life': random.choice([36, 60, 84, 120])
            })

        created_assets = []
        category_map = {c.code: c for c in categories}

        for idx, data in enumerate(assets_data, 1):
            category = category_map.get(data['category'])
            if not category:
                continue

            purchase_date = datetime.date.today() - datetime.timedelta(
                days=random.randint(30, 730)
            )

            asset = Asset.objects.create(
                company=company,
                branch=branch,
                name=data['name'],
                category=category,
                condition=random.choice(conditions),
                status='active',
                purchase_date=purchase_date,
                original_cost=Decimal(str(data['cost'])),
                salvage_value=Decimal(str(data['cost'])) * Decimal('0.10'),
                depreciation_method=depreciation_methods[0],  # القسط الثابت
                useful_life_months=data['life'],
                depreciation_start_date=purchase_date,
                cost_center=cost_center,
                serial_number=f'SN-{2024}-{idx:05d}',
                created_by=user
            )
            created_assets.append(asset)

        return created_assets

    def _create_depreciation_records(self, assets):
        """إنشاء سجلات إهلاك تجريبية"""
        from apps.assets.utils import DepreciationCalculator

        count = 0
        today = datetime.date.today()

        for asset in assets[:20]:  # أول 20 أصل فقط
            # احتساب إهلاك الأشهر الماضية
            start_date = asset.depreciation_start_date
            current_date = start_date

            while current_date < today:
                # آخر يوم في الشهر
                next_month = current_date.replace(day=28) + datetime.timedelta(days=4)
                depreciation_date = next_month - datetime.timedelta(days=next_month.day)

                if depreciation_date > today:
                    break

                calculator = DepreciationCalculator(asset)
                depreciation_amount = calculator.calculate_monthly_depreciation(depreciation_date)

                if depreciation_amount > 0:
                    accumulated_before = asset.accumulated_depreciation
                    accumulated_after = accumulated_before + depreciation_amount
                    book_value_after = asset.original_cost - accumulated_after

                    AssetDepreciation.objects.create(
                        asset=asset,
                        depreciation_date=depreciation_date,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation_before=accumulated_before,
                        accumulated_depreciation_after=accumulated_after,
                        book_value_after=book_value_after
                    )

                    asset.accumulated_depreciation = accumulated_after
                    asset.book_value = book_value_after
                    asset.save()

                    count += 1

                # الشهر التالي
                current_date = depreciation_date + datetime.timedelta(days=1)

        return count

    def _create_maintenance_schedules(self, company, assets, maintenance_types):
        """إنشاء جداول صيانة دورية"""
        branch = company.branches.first()
        user = User.objects.filter(company=company).first()
        preventive = maintenance_types[0]

        schedules = []
        for asset in assets[:15]:  # أول 15 أصل
            schedule = MaintenanceSchedule.objects.create(
                company=company,
                branch=branch,
                asset=asset,
                maintenance_type=preventive,
                frequency=random.choice(['monthly', 'quarterly', 'semi_annual', 'annual']),
                start_date=asset.purchase_date,
                next_maintenance_date=datetime.date.today() + datetime.timedelta(days=random.randint(10, 60)),
                alert_before_days=7,
                estimated_cost=Decimal(str(random.randint(100, 1000))),
                description=f'صيانة دورية - {asset.name}',
                created_by=user
            )
            schedules.append(schedule)

        return schedules

    def _create_maintenance_records(self, company, assets, maintenance_types):
        """إنشاء سجلات صيانة فعلية"""
        branch = company.branches.first()
        user = User.objects.filter(company=company).first()

        count = 0
        for asset in assets[:20]:
            for _ in range(random.randint(1, 3)):
                scheduled_date = asset.purchase_date + datetime.timedelta(
                    days=random.randint(30, 300)
                )

                AssetMaintenance.objects.create(
                    company=company,
                    branch=branch,
                    asset=asset,
                    maintenance_type=random.choice(maintenance_types),
                    maintenance_category=random.choice(['preventive', 'corrective']),
                    scheduled_date=scheduled_date,
                    start_date=scheduled_date,
                    completion_date=scheduled_date + datetime.timedelta(days=random.randint(1, 5)),
                    status='completed',
                    labor_cost=Decimal(str(random.randint(50, 500))),
                    parts_cost=Decimal(str(random.randint(0, 300))),
                    other_cost=Decimal(str(random.randint(0, 100))),
                    description=f'صيانة {asset.name}',
                    created_by=user
                )
                count += 1

        return count

    def _create_transactions(self, company, assets):
        """إنشاء عمليات على الأصول"""
        branch = company.branches.first()
        user = User.objects.filter(company=company).first()

        count = 0
        # عمليات شراء للأصول الجديدة
        for asset in assets[:5]:
            AssetTransaction.objects.create(
                company=company,
                branch=branch,
                transaction_date=asset.purchase_date,
                transaction_type='purchase',
                status='completed',
                asset=asset,
                amount=asset.original_cost,
                payment_method='bank',
                description=f'شراء {asset.name}',
                created_by=user
            )
            count += 1

        return count

    def _print_summary(self, company):
        """طباعة ملخص البيانات"""
        assets_count = Asset.objects.filter(company=company).count()
        depreciation_count = AssetDepreciation.objects.filter(asset__company=company).count()
        maintenance_count = AssetMaintenance.objects.filter(company=company).count()
        transactions_count = AssetTransaction.objects.filter(company=company).count()

        self.stdout.write('\n📊 ملخص البيانات:')
        self.stdout.write(f'  📦 الأصول: {assets_count}')
        self.stdout.write(f'  📉 سجلات الإهلاك: {depreciation_count}')
        self.stdout.write(f'  🔧 سجلات الصيانة: {maintenance_count}')
        self.stdout.write(f'  💼 العمليات: {transactions_count}')
        self.stdout.write('\n✨ يمكنك الآن تصفح النظام وتجربة جميع المزايا!')
# apps/core/management/commands/create_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import *

User = get_user_model()

class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية'

    def handle(self, *args, **options):
        # إنشاء عملة
        currency, created = Currency.objects.get_or_create(
            code='JOD',
            defaults={
                'name': 'الدينار الأردني',
                'name_en': 'Jordanian Dinar',
                'symbol': 'د.أ',
                'is_base': True
            }
        )

        # إنشاء شركة
        company, created = Company.objects.get_or_create(
            name='شركة تجريبية',
            defaults={
                'name_en': 'Test Company',
                'tax_number': '123456789',
                'phone': '+962-6-1234567',
                'email': 'info@test.com',
                'address': 'عمان، الأردن',
                'city': 'عمان',
                'base_currency': currency
            }
        )

        # إنشاء مستودع
        warehouse, created = Warehouse.objects.get_or_create(
            company=company,
            code='WH001',
            defaults={
                'name': 'المستودع الرئيسي',
                'name_en': 'Main Warehouse',
                'is_main': True
            }
        )

        # إنشاء فرع
        branch, created = Branch.objects.get_or_create(
            company=company,
            code='BR001',
            defaults={
                'name': 'الفرع الرئيسي',
                'is_main': True,
                'default_warehouse': warehouse
            }
        )

        # إنشاء وحدة قياس
        unit, created = UnitOfMeasure.objects.get_or_create(
            company=company,
            code='PCS',
            defaults={
                'name': 'قطعة',
                'name_en': 'Piece'
            }
        )

        # إنشاء تصنيف
        category, created = ItemCategory.objects.get_or_create(
            company=company,
            code='CAT001',
            defaults={
                'name': 'إلكترونيات',
                'name_en': 'Electronics'
            }
        )

        # إنشاء علامة تجارية
        brand, created = Brand.objects.get_or_create(
            company=company,
            name='سامسونغ',
            defaults={
                'name_en': 'Samsung',
                'country': 'كوريا الجنوبية'
            }
        )

        # إنشاء أصناف تجريبية
        for i in range(1, 6):
            Item.objects.get_or_create(
                company=company,
                code=f'ITM00{i}',
                defaults={
                    'name': f'صنف تجريبي {i}',
                    'name_en': f'Test Item {i}',
                    'sku': f'SKU00{i}',
                    'barcode': f'123456789{i}',
                    'category': category,
                    'brand': brand,
                    'unit_of_measure': unit,
                    'currency': currency,
                    'default_warehouse': warehouse,
                    'purchase_price': 10.00 + i,
                    'sale_price': 15.00 + i,
                    'tax_rate': 16.0,
                    'short_description': f'وصف مختصر للصنف رقم {i}'
                }
            )

        self.stdout.write(
            self.style.SUCCESS('تم إنشاء البيانات التجريبية بنجاح')
        )
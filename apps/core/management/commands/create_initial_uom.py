# apps/core/management/commands/create_initial_uom.py
"""
إنشاء وحدات القياس الأولية للنظام
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Company, UnitOfMeasure
from decimal import Decimal


class Command(BaseCommand):
    help = 'إنشاء وحدات القياس الأولية للشركة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف الشركة (اختياري - سيتم إنشاء لكل الشركات إذا لم يحدد)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')

        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
            if not companies.exists():
                self.stdout.write(self.style.ERROR(f'الشركة {company_id} غير موجودة'))
                return
        else:
            companies = Company.objects.filter(is_active=True)

        if not companies.exists():
            self.stdout.write(self.style.ERROR('لا توجد شركات نشطة'))
            return

        # وحدات القياس الأساسية
        uom_data = [
            # وحدات العد (UNIT)
            {
                'code': 'PCS',
                'name': 'قطعة',
                'name_en': 'Piece',
                'uom_type': 'UNIT',
                'symbol': 'قطعة',
                'rounding_precision': Decimal('1'),
                'is_base_unit': True
            },
            {
                'code': 'DOZEN',
                'name': 'دزينة',
                'name_en': 'Dozen',
                'uom_type': 'UNIT',
                'symbol': 'دز',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            {
                'code': 'CARTON',
                'name': 'كرتون',
                'name_en': 'Carton',
                'uom_type': 'UNIT',
                'symbol': 'كرتون',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            {
                'code': 'BOX',
                'name': 'صندوق',
                'name_en': 'Box',
                'uom_type': 'UNIT',
                'symbol': 'صندوق',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            {
                'code': 'PACK',
                'name': 'عبوة',
                'name_en': 'Pack',
                'uom_type': 'UNIT',
                'symbol': 'عبوة',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            {
                'code': 'SET',
                'name': 'طقم',
                'name_en': 'Set',
                'uom_type': 'UNIT',
                'symbol': 'طقم',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            # وحدات الوزن (WEIGHT)
            {
                'code': 'KG',
                'name': 'كيلو جرام',
                'name_en': 'Kilogram',
                'uom_type': 'WEIGHT',
                'symbol': 'كجم',
                'rounding_precision': Decimal('0.001'),
                'is_base_unit': True
            },
            {
                'code': 'G',
                'name': 'جرام',
                'name_en': 'Gram',
                'uom_type': 'WEIGHT',
                'symbol': 'جم',
                'rounding_precision': Decimal('0.001'),
                'is_base_unit': False
            },
            {
                'code': 'TON',
                'name': 'طن',
                'name_en': 'Ton',
                'uom_type': 'WEIGHT',
                'symbol': 'طن',
                'rounding_precision': Decimal('0.001'),
                'is_base_unit': False
            },
            # وحدات الطول (LENGTH)
            {
                'code': 'M',
                'name': 'متر',
                'name_en': 'Meter',
                'uom_type': 'LENGTH',
                'symbol': 'م',
                'rounding_precision': Decimal('0.01'),
                'is_base_unit': True
            },
            {
                'code': 'CM',
                'name': 'سنتيمتر',
                'name_en': 'Centimeter',
                'uom_type': 'LENGTH',
                'symbol': 'سم',
                'rounding_precision': Decimal('0.1'),
                'is_base_unit': False
            },
            {
                'code': 'MM',
                'name': 'مليمتر',
                'name_en': 'Millimeter',
                'uom_type': 'LENGTH',
                'symbol': 'ملم',
                'rounding_precision': Decimal('0.1'),
                'is_base_unit': False
            },
            # وحدات الحجم (VOLUME)
            {
                'code': 'L',
                'name': 'لتر',
                'name_en': 'Liter',
                'uom_type': 'VOLUME',
                'symbol': 'ل',
                'rounding_precision': Decimal('0.01'),
                'is_base_unit': True
            },
            {
                'code': 'ML',
                'name': 'مليلتر',
                'name_en': 'Milliliter',
                'uom_type': 'VOLUME',
                'symbol': 'مل',
                'rounding_precision': Decimal('1'),
                'is_base_unit': False
            },
            # وحدات المساحة (AREA)
            {
                'code': 'SQM',
                'name': 'متر مربع',
                'name_en': 'Square Meter',
                'uom_type': 'AREA',
                'symbol': 'م²',
                'rounding_precision': Decimal('0.01'),
                'is_base_unit': True
            },
        ]

        total_created = 0

        with transaction.atomic():
            for company in companies:
                created_count = 0

                for uom_info in uom_data:
                    # التحقق من عدم وجود الوحدة مسبقاً
                    if not UnitOfMeasure.objects.filter(
                        company=company,
                        code=uom_info['code']
                    ).exists():
                        UnitOfMeasure.objects.create(
                            company=company,
                            code=uom_info['code'],
                            name=uom_info['name'],
                            name_en=uom_info['name_en'],
                            uom_type=uom_info['uom_type'],
                            symbol=uom_info['symbol'],
                            rounding_precision=uom_info['rounding_precision'],
                            is_base_unit=uom_info['is_base_unit'],
                            is_active=True
                        )
                        created_count += 1

                total_created += created_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ تم إنشاء {created_count} وحدة قياس للشركة: {company.name}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ تم إنشاء {total_created} وحدة قياس إجمالاً'
            )
        )

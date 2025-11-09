# apps/core/management/commands/create_payment_methods.py
"""
أمر لإنشاء طرق الدفع الافتراضية
"""

from django.core.management.base import BaseCommand
from apps.core.models import Company, PaymentMethod


class Command(BaseCommand):
    help = 'إنشاء طرق الدفع الافتراضية لجميع الشركات'

    def handle(self, *args, **options):
        # طرق الدفع الافتراضية
        payment_methods = [
            {
                'code': 'CASH',
                'name': 'نقدي',
                'is_cash': True,
                'is_active': True,
            },
            {
                'code': 'BANK',
                'name': 'تحويل بنكي',
                'is_cash': False,
                'is_active': True,
            },
            {
                'code': 'CHECK',
                'name': 'شيك',
                'is_cash': False,
                'is_active': True,
            },
            {
                'code': 'CREDIT',
                'name': 'آجل',
                'is_cash': False,
                'is_active': True,
            },
            {
                'code': 'CARD',
                'name': 'بطاقة ائتمان',
                'is_cash': False,
                'is_active': True,
            },
        ]

        companies = Company.objects.filter(is_active=True)

        if not companies.exists():
            self.stdout.write(self.style.ERROR('لا توجد شركات نشطة في النظام'))
            return

        total_created = 0

        for company in companies:
            self.stdout.write(f'\nمعالجة الشركة: {company.name}')

            for method_data in payment_methods:
                payment_method, created = PaymentMethod.objects.get_or_create(
                    company=company,
                    code=method_data['code'],
                    defaults={
                        'name': method_data['name'],
                        'is_cash': method_data['is_cash'],
                        'is_active': method_data['is_active'],
                    }
                )

                if created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ تم إنشاء: {method_data["name"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - موجود مسبقاً: {method_data["name"]}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ تم الانتهاء! تم إنشاء {total_created} طريقة دفع جديدة')
        )

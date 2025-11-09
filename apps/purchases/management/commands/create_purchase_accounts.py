# apps/purchases/management/commands/create_purchase_accounts.py
"""
أمر إداري لإنشاء الحسابات الافتراضية اللازمة لنظام المشتريات
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from apps.core.models import Company
from apps.accounting.models import Account, AccountType


class Command(BaseCommand):
    help = 'إنشاء الحسابات الافتراضية لنظام المشتريات'

    def handle(self, *args, **options):
        """تنفيذ الأمر"""

        # الحصول على أنواع الحسابات
        try:
            asset_type = AccountType.objects.get(code='ASSETS')
            liability_type = AccountType.objects.get(code='LIABILITIES')
            expense_type = AccountType.objects.get(code='EXPENSES')
        except AccountType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('خطأ: أنواع الحسابات غير موجودة. يرجى إنشاء AccountTypes أولاً.')
            )
            return

        # الحسابات المطلوبة لنظام المشتريات
        purchase_accounts = [
            {
                'code': '120000',
                'name': 'المخزون',
                'name_en': 'Inventory',
                'account_type': asset_type,
                'parent_code': None,
                'level': 1
            },
            {
                'code': '120400',
                'name': 'ضريبة المشتريات القابلة للخصم',
                'name_en': 'Input VAT',
                'account_type': asset_type,
                'parent_code': None,
                'level': 1
            },
            {
                'code': '210000',
                'name': 'الموردون',
                'name_en': 'Accounts Payable',
                'account_type': liability_type,
                'parent_code': None,
                'level': 1
            },
            {
                'code': '530000',
                'name': 'خصم مشتريات',
                'name_en': 'Purchase Discount',
                'account_type': expense_type,
                'parent_code': None,
                'level': 1
            },
        ]

        # الحصول على جميع الشركات النشطة
        companies = Company.objects.filter(is_active=True)

        total_created = 0
        total_exists = 0

        for company in companies:
            self.stdout.write(self.style.SUCCESS(f'\n▶ معالجة الشركة: {company.name}'))

            # Get company's default currency
            if hasattr(company, 'default_currency') and company.default_currency:
                currency = company.default_currency
            else:
                # Try to get first available currency
                from apps.core.models import Currency
                currency = Currency.objects.filter(companies=company, is_active=True).first()
                if not currency:
                    self.stdout.write(
                        self.style.ERROR(f'  خطأ: لا توجد عملة افتراضية للشركة {company.name}')
                    )
                    continue

            for account_data in purchase_accounts:
                # التحقق من وجود الحساب
                account, created = Account.objects.get_or_create(
                    company=company,
                    code=account_data['code'],
                    defaults={
                        'name': account_data['name'],
                        'name_en': account_data['name_en'],
                        'account_type': account_data['account_type'],
                        'currency': currency,
                        'level': account_data['level'],
                        'is_active': True,
                        'accept_entries': True,
                        'can_have_children': False,
                        'created_by': None
                    }
                )

                if created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ تم إنشاء الحساب: {account.code} - {account.name}'
                        )
                    )
                else:
                    total_exists += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ○ الحساب موجود مسبقاً: {account.code} - {account.name}'
                        )
                    )

        # النتيجة النهائية
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ تم إنشاء {total_created} حساب جديد'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f'○ {total_exists} حساب موجود مسبقاً'
            )
        )
        self.stdout.write('=' * 60 + '\n')

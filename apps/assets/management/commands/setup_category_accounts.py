# apps/assets/management/commands/setup_category_accounts.py
"""
أمر لإعداد الحسابات المحاسبية لفئات الأصول
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Company
from apps.assets.models import AssetCategory
from apps.accounting.models import Account


class Command(BaseCommand):
    help = 'إعداد الحسابات المحاسبية لفئات الأصول'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف الشركة (اختياري - سيتم استخدام أول شركة إذا لم يحدد)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        company_id = options.get('company_id')

        # الحصول على الشركة
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'الشركة برقم {company_id} غير موجودة'))
                return
        else:
            company = Company.objects.filter(is_active=True).first()
            if not company:
                self.stdout.write(self.style.ERROR('لا توجد شركات نشطة في النظام'))
                return

        self.stdout.write(f'العمل على الشركة: {company.name}')

        # البحث عن الحسابات المناسبة
        accounts = Account.objects.filter(company=company, is_active=True)

        # حسابات الأصول والإهلاك
        asset_account = accounts.filter(code__istartswith='1').filter(
            name__icontains='أصول'
        ).first() or accounts.filter(code__istartswith='12').first()

        accumulated_dep_account = accounts.filter(
            name__icontains='مجمع'
        ).first() or accounts.filter(name__icontains='إهلاك').first()

        depreciation_expense_account = accounts.filter(code__istartswith='5').filter(
            name__icontains='إهلاك'
        ).first() or accounts.filter(name__icontains='مصروف').first()

        # حسابات الربح والخسارة
        gain_account = accounts.filter(code__istartswith='4').filter(
            name__icontains='أرباح'
        ).first() or accounts.filter(code__istartswith='41').first() or \
                      accounts.filter(name__icontains='إيراد').first()

        loss_account = accounts.filter(code__istartswith='5').filter(
            name__icontains='خسائر'
        ).first() or accounts.filter(code__istartswith='58').first() or \
                     accounts.filter(name__icontains='مصروف').first()

        maintenance_account = accounts.filter(code__istartswith='5').filter(
            name__icontains='صيانة'
        ).first()

        if not asset_account:
            self.stdout.write(self.style.ERROR('❌ لم يتم العثور على حساب أصول مناسب'))
            return

        if not loss_account:
            self.stdout.write(self.style.ERROR('❌ لم يتم العثور على حساب خسائر مناسب'))
            return

        if not gain_account:
            self.stdout.write(self.style.ERROR('❌ لم يتم العثور على حساب أرباح مناسب'))
            return

        # تحديث فئات الأصول
        categories = AssetCategory.objects.filter(company=company)
        updated_count = 0

        for category in categories:
            updated = False

            if not category.asset_account:
                category.asset_account = asset_account
                updated = True

            if not category.accumulated_depreciation_account and accumulated_dep_account:
                category.accumulated_depreciation_account = accumulated_dep_account
                updated = True

            if not category.depreciation_expense_account and depreciation_expense_account:
                category.depreciation_expense_account = depreciation_expense_account
                updated = True

            if not category.gain_on_sale_account:
                category.gain_on_sale_account = gain_account
                updated = True

            if not category.loss_on_disposal_account:
                category.loss_on_disposal_account = loss_account
                updated = True

            if not category.maintenance_expense_account and maintenance_account:
                category.maintenance_expense_account = maintenance_account
                updated = True

            if updated:
                category.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ تم تحديث الفئة: {category.name}'))
                if category.loss_on_disposal_account:
                    self.stdout.write(f'    - حساب الخسائر: {category.loss_on_disposal_account.code} - {category.loss_on_disposal_account.name}')
                if category.gain_on_sale_account:
                    self.stdout.write(f'    - حساب الأرباح: {category.gain_on_sale_account.code} - {category.gain_on_sale_account.name}')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ تم تحديث {updated_count} فئة من أصل {categories.count()} فئة'))
        self.stdout.write('\nالحسابات المستخدمة:')
        self.stdout.write(f'  - حساب الأصول: {asset_account.code} - {asset_account.name}')
        if accumulated_dep_account:
            self.stdout.write(f'  - مجمع الإهلاك: {accumulated_dep_account.code} - {accumulated_dep_account.name}')
        if depreciation_expense_account:
            self.stdout.write(f'  - مصروف الإهلاك: {depreciation_expense_account.code} - {depreciation_expense_account.name}')
        self.stdout.write(f'  - حساب الأرباح: {gain_account.code} - {gain_account.name}')
        self.stdout.write(f'  - حساب الخسائر: {loss_account.code} - {loss_account.name}')
        if maintenance_account:
            self.stdout.write(f'  - مصروف الصيانة: {maintenance_account.code} - {maintenance_account.name}')

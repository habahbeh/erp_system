# apps/assets/management/commands/create_asset_accounting_config.py
"""
أمر لإنشاء بيانات تجريبية لإعدادات الحسابات المحاسبية للأصول
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Company
from apps.assets.models import AssetAccountingConfiguration
from apps.accounting.models import Account


class Command(BaseCommand):
    help = 'إنشاء إعدادات حسابات محاسبية تجريبية للأصول'

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

        # التحقق من وجود إعدادات مسبقة
        existing_config = AssetAccountingConfiguration.objects.filter(company=company).first()
        if existing_config:
            self.stdout.write(self.style.WARNING(f'توجد إعدادات مسبقة للشركة {company.name}'))
            self.stdout.write('سيتم تحديث الإعدادات الموجودة...')
            config = existing_config
        else:
            config = AssetAccountingConfiguration(company=company)
            self.stdout.write('إنشاء إعدادات جديدة...')

        # البحث عن الحسابات المناسبة
        accounts = Account.objects.filter(company=company, is_active=True)

        # حسابات عامة (مطلوبة)
        cash_account = accounts.filter(code__icontains='1010').first() or \
                      accounts.filter(name__icontains='صندوق').first() or \
                      accounts.filter(name__icontains='نقدية').first()

        bank_account = accounts.filter(code__icontains='1020').first() or \
                      accounts.filter(name__icontains='بنك').first() or \
                      accounts.filter(name__icontains='حساب جاري').first()

        supplier_account = accounts.filter(code__icontains='2010').first() or \
                          accounts.filter(name__icontains='موردين').first() or \
                          accounts.filter(name__icontains='دائنون').first()

        # حسابات الصيانة
        maintenance_expense = accounts.filter(code__icontains='5').filter(
            name__icontains='صيانة'
        ).first() or accounts.filter(name__icontains='مصروف').first()

        capital_improvement = accounts.filter(code__icontains='1').filter(
            name__icontains='أصول'
        ).first()

        # حسابات الإيجار
        lease_expense = accounts.filter(code__icontains='5').filter(
            name__icontains='إيجار'
        ).first()

        lease_liability = accounts.filter(code__icontains='2').filter(
            name__icontains='التزام'
        ).first()

        lease_interest = accounts.filter(code__icontains='5').filter(
            name__icontains='فائدة'
        ).first() or accounts.filter(name__icontains='فوائد').first()

        # حسابات التأمين
        insurance_expense = accounts.filter(code__icontains='5').filter(
            name__icontains='تأمين'
        ).first()

        insurance_deductible = accounts.filter(code__icontains='5').filter(
            name__icontains='تحمل'
        ).first()

        insurance_income = accounts.filter(code__icontains='4').filter(
            name__icontains='تعويض'
        ).first() or accounts.filter(name__icontains='إيراد').first()

        # تعيين الحسابات
        if cash_account:
            config.default_cash_account = cash_account
            self.stdout.write(self.style.SUCCESS(f'  ✓ حساب النقدية: {cash_account.code} - {cash_account.name}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ لم يتم العثور على حساب نقدية مناسب'))

        if bank_account:
            config.default_bank_account = bank_account
            self.stdout.write(self.style.SUCCESS(f'  ✓ حساب البنك: {bank_account.code} - {bank_account.name}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ لم يتم العثور على حساب بنك مناسب'))

        if supplier_account:
            config.default_supplier_account = supplier_account
            self.stdout.write(self.style.SUCCESS(f'  ✓ حساب الموردين: {supplier_account.code} - {supplier_account.name}'))

        if maintenance_expense:
            config.default_maintenance_expense_account = maintenance_expense
            self.stdout.write(self.style.SUCCESS(f'  ✓ مصروف الصيانة: {maintenance_expense.code} - {maintenance_expense.name}'))

        if capital_improvement:
            config.capital_improvement_account = capital_improvement
            self.stdout.write(self.style.SUCCESS(f'  ✓ التحسينات الرأسمالية: {capital_improvement.code} - {capital_improvement.name}'))

        if lease_expense:
            config.operating_lease_expense_account = lease_expense
            self.stdout.write(self.style.SUCCESS(f'  ✓ مصروف الإيجار: {lease_expense.code} - {lease_expense.name}'))

        if lease_liability:
            config.finance_lease_liability_account = lease_liability
            self.stdout.write(self.style.SUCCESS(f'  ✓ التزامات الإيجار: {lease_liability.code} - {lease_liability.name}'))

        if lease_interest:
            config.finance_lease_interest_expense_account = lease_interest
            self.stdout.write(self.style.SUCCESS(f'  ✓ فوائد الإيجار: {lease_interest.code} - {lease_interest.name}'))

        if insurance_expense:
            config.insurance_expense_account = insurance_expense
            self.stdout.write(self.style.SUCCESS(f'  ✓ مصروف التأمين: {insurance_expense.code} - {insurance_expense.name}'))

        if insurance_deductible:
            config.insurance_deductible_expense_account = insurance_deductible
            self.stdout.write(self.style.SUCCESS(f'  ✓ مصروف التحمل: {insurance_deductible.code} - {insurance_deductible.name}'))

        if insurance_income:
            config.insurance_claim_income_account = insurance_income
            self.stdout.write(self.style.SUCCESS(f'  ✓ إيرادات التعويض: {insurance_income.code} - {insurance_income.name}'))

        # حفظ الإعدادات
        config.save()

        # التحقق من الحسابات المطلوبة
        self.stdout.write('\n' + '='*60)
        if not config.default_cash_account and not config.default_bank_account:
            self.stdout.write(self.style.ERROR('❌ تحذير: لم يتم تحديد حساب بنك أو نقدية!'))
            self.stdout.write(self.style.ERROR('   يجب تحديد أحدهما على الأقل لإتمام المعاملات'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ تم تحديد حسابات البنك/النقدية بنجاح'))

        self.stdout.write('\n' + self.style.SUCCESS('✅ تم إنشاء/تحديث إعدادات الحسابات المحاسبية بنجاح'))
        self.stdout.write(f'   معرف الإعدادات: {config.id}')
        self.stdout.write(f'   الشركة: {config.company.name}')

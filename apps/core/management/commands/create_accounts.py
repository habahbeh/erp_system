# في apps/core/management/commands/create_accounts.py
"""
أمر إداري لإنشاء دليل الحسابات الافتراضي
python manage.py create_accounts
"""

from django.core.management.base import BaseCommand
from apps.core.models import Company


class Command(BaseCommand):
    help = 'إنشاء دليل الحسابات الافتراضي للشركات'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف شركة محددة (اختياري)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')

        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                companies = [company]
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'الشركة برقم {company_id} غير موجودة')
                )
                return
        else:
            companies = Company.objects.filter(is_active=True)

        total_accounts = 0

        for company in companies:
            self.stdout.write(f'\n📦 معالجة الشركة: {company.name}')

            # إنشاء الحسابات
            count = company.create_default_accounts()
            total_accounts += count

            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ تم إنشاء {count} حساب')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  الحسابات موجودة مسبقاً')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✨ اكتمل! تم إنشاء {total_accounts} حساب إجمالاً'
            )
        )
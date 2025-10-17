# في apps/core/management/commands/create_sequences.py
"""
أمر إداري لإنشاء تسلسلات الترقيم للشركات الموجودة
python manage.py create_sequences
"""


"""
# إنشاء تسلسلات لكل الشركات
python manage.py create_sequences

# إنشاء تسلسلات لشركة محددة
python manage.py create_sequences --company-id=1

# إنشاء حسابات لكل الشركات
python manage.py create_accounts

# إنشاء حسابات لشركة محددة
python manage.py create_accounts --company-id=1
"""


from django.core.management.base import BaseCommand
from apps.core.models import Company


class Command(BaseCommand):
    help = 'إنشاء تسلسلات الترقيم الافتراضية للشركات الموجودة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='معرف شركة محددة (اختياري)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')

        if company_id:
            # شركة محددة
            try:
                company = Company.objects.get(id=company_id)
                companies = [company]
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'الشركة برقم {company_id} غير موجودة')
                )
                return
        else:
            # كل الشركات
            companies = Company.objects.filter(is_active=True)

        total_sequences = 0

        for company in companies:
            self.stdout.write(f'\n📦 معالجة الشركة: {company.name}')

            # إنشاء التسلسلات
            count = company.create_default_sequences()
            total_sequences += count

            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ تم إنشاء {count} تسلسل')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  التسلسلات موجودة مسبقاً')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✨ اكتمل! تم إنشاء {total_sequences} تسلسل إجمالاً'
            )
        )
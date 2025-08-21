# apps/core/management/commands/setup_initial_data.py
"""
أمر لإنشاء البيانات الأولية للنظام
يشمل: الشركات، الفروع، المجموعات، المستخدمين التجريبيين
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from core.models import Company, Branch, User


class Command(BaseCommand):
    help = 'إنشاء البيانات الأولية للنظام'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('بدء إنشاء البيانات الأولية...')

        # إنشاء الشركة الافتراضية
        company, created = Company.objects.get_or_create(
            tax_number='17915619',  # من الملف المرفق
            defaults={
                'name': 'شركة المخازن الهندسية',
                'name_en': 'Engineering Stores Company',
                'phone': '0775599466',
                'email': 'info@eng-stores.com',
                'address': 'الأردن - عمان - سحاب - مقابل مدينة الملك عبدالله الثاني الصناعية - بجانب الملعب البلدي',
                'commercial_register': '12345',  # عدّل حسب الرقم الحقيقي
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء الشركة: {company.name}'))

        # إنشاء الفروع
        branches_data = [
            {
                'code': 'MAIN',
                'name': 'الفرع الرئيسي - سحاب',
                'phone': '4027888',
                'address': 'سحاب - مقابل مدينة الملك عبدالله الثاني الصناعية - بجانب الملعب البلدي',
                'is_main': True
            },
            {
                'code': 'BR01',
                'name': 'فرع أبو علندا',
                'phone': '',
                'address': 'أبو علندا - شارع عبدالكريم الحديد - بجانب بنك الأردن',
                'is_main': False
            },
            {
                'code': 'BR02',
                'name': 'فرع الشحن الجوي',
                'phone': '0777041605',
                'address': 'شارع الشحن الجوي - مجمع الجعبري 3',
                'is_main': False
            },
        ]

        for branch_data in branches_data:
            branch, created = Branch.objects.get_or_create(
                company=company,
                code=branch_data['code'],
                defaults={
                    'name': branch_data['name'],
                    'phone': branch_data['phone'],
                    'address': branch_data['address'],
                    'is_main': branch_data['is_main'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء الفرع: {branch.name}'))

        # إنشاء المجموعات
        groups_permissions = {
            'المدراء': [
                # كل الصلاحيات تقريباً
                'add_', 'change_', 'delete_', 'view_'
            ],
            'المحاسبون': [
                # صلاحيات المحاسبة والتقارير
                'view_', 'add_journalentry', 'change_journalentry',
                'view_account', 'view_salesinvoice', 'view_purchaseinvoice'
            ],
            'موظفو المبيعات': [
                # صلاحيات المبيعات فقط
                'view_customer', 'add_customer', 'change_customer',
                'view_salesinvoice', 'add_salesinvoice', 'change_salesinvoice',
                'view_quotation', 'add_quotation', 'change_quotation'
            ],
            'موظفو المشتريات': [
                # صلاحيات المشتريات
                'view_supplier', 'add_supplier', 'change_supplier',
                'view_purchaseorder', 'add_purchaseorder', 'change_purchaseorder',
                'view_purchaseinvoice', 'add_purchaseinvoice'
            ],
            'أمناء المخازن': [
                # صلاحيات المخزون
                'view_item', 'change_item',
                'view_warehouse', 'view_stockmovement',
                'add_stockmovement', 'change_stockmovement'
            ],
        }

        for group_name, permission_patterns in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                # إضافة الصلاحيات للمجموعة
                permissions = Permission.objects.filter(
                    codename__icontains=permission_patterns[0] if len(permission_patterns) == 1 else ''
                )
                for pattern in permission_patterns:
                    if pattern.endswith('_'):
                        # صلاحية عامة مثل view_
                        perms = Permission.objects.filter(codename__startswith=pattern)
                    else:
                        # صلاحية محددة
                        perms = Permission.objects.filter(codename=pattern)
                    group.permissions.add(*perms)

                self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء المجموعة: {group_name}'))

        # إنشاء مستخدمين تجريبيين
        main_branch = Branch.objects.get(code='MAIN')

        test_users = [
            {
                'username': 'admin',
                'email': 'admin@demo.com',
                'first_name': 'المدير',
                'last_name': 'العام',
                'is_superuser': True,
                'is_staff': True,
            },
            {
                'username': 'accountant',
                'email': 'accountant@demo.com',
                'first_name': 'محمد',
                'last_name': 'المحاسب',
                'groups': ['المحاسبون'],
            },
            {
                'username': 'sales',
                'email': 'sales@demo.com',
                'first_name': 'أحمد',
                'last_name': 'البائع',
                'groups': ['موظفو المبيعات'],
            },
        ]

        for user_data in test_users:
            username = user_data.pop('username')
            groups = user_data.pop('groups', [])
            password = 'demo1234'  # كلمة مرور افتراضية

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    **user_data,
                    'company': company,
                    'branch': main_branch,
                }
            )

            if created:
                user.set_password(password)
                user.save()

                # إضافة المستخدم للمجموعات
                for group_name in groups:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ تم إنشاء المستخدم: {username} (كلمة المرور: {password})'
                    )
                )

        self.stdout.write(self.style.SUCCESS('\n✅ تم إنشاء جميع البيانات الأولية بنجاح!'))
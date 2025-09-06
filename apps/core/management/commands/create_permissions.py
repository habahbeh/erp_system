# apps/core/management/commands/create_permissions.py
"""
أمر لإنشاء الصلاحيات الأساسية والمجموعات
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.core.models import CustomPermission, PermissionGroup


class Command(BaseCommand):
    help = 'إنشاء الصلاحيات الأساسية ومجموعاتها'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 بدء إنشاء الصلاحيات المخصصة ومجموعاتها...')
        )

        # إنشاء الصلاحيات المخصصة
        self.create_custom_permissions()

        # إنشاء مجموعات الصلاحيات
        self.create_permission_groups()

        self.stdout.write(
            self.style.SUCCESS('✅ تم إنجاز جميع العمليات بنجاح!')
        )

    def create_custom_permissions(self):
        """إنشاء الصلاحيات المخصصة التجارية"""
        self.stdout.write('\n📝 إنشاء الصلاحيات المخصصة...')

        # صلاحيات المبيعات المتقدمة
        sales_permissions = [
            {
                'code': 'apply_discount',
                'name': 'تطبيق خصم على المبيعات',
                'description': 'السماح بتطبيق خصومات على فواتير المبيعات',
                'category': 'sales',
                'permission_type': 'special',
                'max_amount': 1000.00
            },
            {
                'code': 'void_sales_invoice',
                'name': 'إلغاء فاتورة مبيعات',
                'description': 'إلغاء فواتير المبيعات المؤكدة',
                'category': 'sales',
                'permission_type': 'delete',
                'requires_approval': True
            },
            {
                'code': 'modify_sales_price',
                'name': 'تعديل سعر البيع',
                'description': 'تعديل أسعار البيع في الفواتير',
                'category': 'sales',
                'permission_type': 'change'
            },
            {
                'code': 'view_sales_profit',
                'name': 'عرض أرباح المبيعات',
                'description': 'عرض هوامش الربح في فواتير المبيعات',
                'category': 'sales',
                'permission_type': 'view'
            }
        ]

        # صلاحيات المشتريات المتقدمة
        purchase_permissions = [
            {
                'code': 'approve_purchase_order',
                'name': 'موافقة أمر شراء',
                'description': 'الموافقة على أوامر الشراء',
                'category': 'purchases',
                'permission_type': 'approve',
                'requires_approval': True,
                'max_amount': 10000.00
            },
            {
                'code': 'urgent_purchase',
                'name': 'شراء عاجل',
                'description': 'إجراء مشتريات عاجلة بدون موافقة مسبقة',
                'category': 'purchases',
                'permission_type': 'special',
                'max_amount': 5000.00
            },
            {
                'code': 'change_supplier',
                'name': 'تغيير المورد',
                'description': 'تغيير المورد في أوامر الشراء المؤكدة',
                'category': 'purchases',
                'permission_type': 'change'
            }
        ]

        # صلاحيات المخزون المتقدمة
        inventory_permissions = [
            {
                'code': 'stock_adjustment',
                'name': 'تسوية المخزون',
                'description': 'إجراء تسويات على أرصدة المخزون',
                'category': 'inventory',
                'permission_type': 'change'
            },
            {
                'code': 'negative_stock',
                'name': 'السماح بالرصيد السالب',
                'description': 'السماح بإخراج مخزون أكثر من المتاح',
                'category': 'inventory',
                'permission_type': 'special'
            },
            {
                'code': 'bulk_stock_transfer',
                'name': 'تحويل مخزون بالجملة',
                'description': 'تحويل كميات كبيرة بين المستودعات',
                'category': 'inventory',
                'permission_type': 'change'
            },
            {
                'code': 'inventory_count',
                'name': 'جرد المخزون',
                'description': 'إجراء جرد شامل أو جزئي للمخزون',
                'category': 'inventory',
                'permission_type': 'special'
            }
        ]

        # صلاحيات المحاسبة الحساسة
        accounting_permissions = [
            {
                'code': 'manual_journal_entry',
                'name': 'قيد يومية يدوي',
                'description': 'إنشاء قيود يومية يدوية',
                'category': 'accounting',
                'permission_type': 'add',
                'requires_approval': True
            },
            {
                'code': 'close_accounting_period',
                'name': 'إقفال فترة محاسبية',
                'description': 'إقفال الفترات المحاسبية',
                'category': 'accounting',
                'permission_type': 'special',
                'requires_approval': True
            },
            {
                'code': 'view_cost_analysis',
                'name': 'عرض تحليل التكاليف',
                'description': 'عرض تقارير تحليل التكاليف التفصيلية',
                'category': 'accounting',
                'permission_type': 'view'
            }
        ]

        # صلاحيات التقارير الحساسة
        report_permissions = [
            {
                'code': 'financial_reports',
                'name': 'التقارير المالية',
                'description': 'عرض التقارير المالية الحساسة',
                'category': 'reports',
                'permission_type': 'view'
            },
            {
                'code': 'export_sensitive_data',
                'name': 'تصدير البيانات الحساسة',
                'description': 'تصدير البيانات المالية والتجارية الحساسة',
                'category': 'reports',
                'permission_type': 'export'
            },
            {
                'code': 'profit_loss_report',
                'name': 'تقرير الأرباح والخسائر',
                'description': 'عرض تقارير الأرباح والخسائر التفصيلية',
                'category': 'reports',
                'permission_type': 'view'
            }
        ]

        # صلاحيات إدارية متقدمة
        admin_permissions = [
            {
                'code': 'system_backup',
                'name': 'نسخ احتياطي للنظام',
                'description': 'إنشاء واستعادة النسخ الاحتياطية',
                'category': 'system',
                'permission_type': 'special'
            },
            {
                'code': 'bulk_data_import',
                'name': 'استيراد البيانات بالجملة',
                'description': 'استيراد كميات كبيرة من البيانات',
                'category': 'system',
                'permission_type': 'add'
            },
            {
                'code': 'view_audit_trail',
                'name': 'عرض سجل المراجعة',
                'description': 'عرض سجل جميع العمليات والتغييرات',
                'category': 'system',
                'permission_type': 'view'
            }
        ]

        # دمج جميع الصلاحيات
        all_permissions = (
                sales_permissions + purchase_permissions +
                inventory_permissions + accounting_permissions +
                report_permissions + admin_permissions
        )

        # إنشاء الصلاحيات
        created_count = 0
        for perm_data in all_permissions:
            permission, created = CustomPermission.objects.get_or_create(
                code=perm_data['code'],
                defaults=perm_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ {permission.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f'📊 تم إنشاء {created_count} صلاحية مخصصة من أصل {len(all_permissions)}'
            )
        )

    def create_permission_groups(self):
        """إنشاء مجموعات الصلاحيات الأساسية"""
        self.stdout.write('\n👥 إنشاء مجموعات الصلاحيات...')

        groups_data = [
            {
                'name': 'موظف مبيعات',
                'description': 'صلاحيات أساسية للمبيعات - بدون خصومات كبيرة',
                'custom_permissions': ['modify_sales_price'],
                'django_permissions': [
                    'core.view_item', 'core.view_businesspartner', 'core.view_warehouse'
                ]
            },
            {
                'name': 'مدير مبيعات',
                'description': 'صلاحيات متقدمة للمبيعات مع خصومات وإلغاءات',
                'custom_permissions': [
                    'apply_discount', 'void_sales_invoice', 'modify_sales_price', 'view_sales_profit'
                ],
                'django_permissions': [
                    'core.add_item', 'core.change_item', 'core.view_item',
                    'core.view_businesspartner', 'core.add_businesspartner'
                ]
            },
            {
                'name': 'موظف مشتريات',
                'description': 'صلاحيات أساسية للمشتريات',
                'custom_permissions': ['change_supplier'],
                'django_permissions': [
                    'core.view_item', 'core.view_businesspartner', 'core.view_warehouse'
                ]
            },
            {
                'name': 'مدير مشتريات',
                'description': 'صلاحيات كاملة للمشتريات مع موافقات',
                'custom_permissions': [
                    'approve_purchase_order', 'urgent_purchase', 'change_supplier'
                ],
                'django_permissions': [
                    'core.add_item', 'core.change_item', 'core.view_item',
                    'core.add_businesspartner', 'core.change_businesspartner'
                ]
            },
            {
                'name': 'أمين مخزون',
                'description': 'إدارة المخزون والتحويلات',
                'custom_permissions': [
                    'stock_adjustment', 'bulk_stock_transfer', 'inventory_count'
                ],
                'django_permissions': [
                    'core.view_item', 'core.change_item', 'core.view_warehouse'
                ]
            },
            {
                'name': 'محاسب',
                'description': 'صلاحيات المحاسبة الأساسية',
                'custom_permissions': ['manual_journal_entry', 'view_cost_analysis'],
                'django_permissions': [
                    'core.view_item', 'core.view_businesspartner'
                ]
            },
            {
                'name': 'مدير مالي',
                'description': 'صلاحيات مالية متقدمة مع تقارير حساسة',
                'custom_permissions': [
                    'manual_journal_entry', 'close_accounting_period',
                    'view_cost_analysis', 'financial_reports', 'profit_loss_report'
                ],
                'django_permissions': [
                    'core.view_item', 'core.view_businesspartner', 'core.view_currency'
                ]
            },
            {
                'name': 'مدير عام',
                'description': 'صلاحيات إدارية شاملة',
                'custom_permissions': [
                    'view_sales_profit', 'approve_purchase_order', 'inventory_count',
                    'financial_reports', 'view_audit_trail'
                ],
                'django_permissions': [
                    'core.view_item', 'core.change_item', 'core.view_businesspartner',
                    'core.view_warehouse', 'core.view_user'
                ]
            },
            {
                'name': 'مدير تقني',
                'description': 'صلاحيات تقنية للنظام',
                'custom_permissions': [
                    'system_backup', 'bulk_data_import', 'view_audit_trail'
                ],
                'django_permissions': [
                    'core.add_user', 'core.change_user', 'core.view_user'
                ]
            }
        ]

        created_groups = 0
        for group_data in groups_data:
            group, created = PermissionGroup.objects.get_or_create(
                name=group_data['name'],
                defaults={
                    'description': group_data['description']
                }
            )

            if created:
                created_groups += 1

                # إضافة الصلاحيات المخصصة
                if 'custom_permissions' in group_data:
                    custom_permissions = CustomPermission.objects.filter(
                        code__in=group_data['custom_permissions']
                    )
                    group.permissions.set(custom_permissions)

                # إضافة صلاحيات Django
                if 'django_permissions' in group_data:
                    django_permissions = []
                    for perm_string in group_data['django_permissions']:
                        try:
                            app_label, codename = perm_string.split('.')
                            permission = Permission.objects.get(
                                content_type__app_label=app_label,
                                codename=codename
                            )
                            django_permissions.append(permission)
                        except (Permission.DoesNotExist, ValueError):
                            self.stdout.write(
                                self.style.WARNING(f"⚠️  صلاحية غير موجودة: {perm_string}")
                            )

                    group.django_permissions.set(django_permissions)

                total_perms = group.get_total_permissions_count()
                self.stdout.write(f"  ✅ {group.name} ({total_perms} صلاحيات)")

        self.stdout.write(
            self.style.SUCCESS(
                f'📊 تم إنشاء {created_groups} مجموعة من أصل {len(groups_data)}'
            )
        )
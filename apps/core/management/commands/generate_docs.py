# apps/core/management/commands/generate_docs.py
"""
Generate System Documentation
Creates comprehensive documentation for the ERP system
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.urls import get_resolver
from django.conf import settings
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Generate comprehensive system documentation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating system documentation...'))

        # Create docs directory
        docs_dir = os.path.join(settings.BASE_DIR, 'DOCS')
        os.makedirs(docs_dir, exist_ok=True)

        # Generate model documentation
        self._generate_models_doc(docs_dir)

        # Generate URL documentation
        self._generate_urls_doc(docs_dir)

        # Generate API documentation
        self._generate_api_doc(docs_dir)

        # Generate user guide
        self._generate_user_guide(docs_dir)

        self.stdout.write(self.style.SUCCESS(f'\n✅ Documentation generated in: {docs_dir}'))

    def _generate_models_doc(self, docs_dir):
        """Generate models documentation"""
        self.stdout.write('Generating models documentation...')

        content = "# نماذج البيانات (Database Models)\n\n"
        content += f"**تاريخ التوليد:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        for app_config in apps.get_app_configs():
            if app_config.name.startswith('apps.'):
                content += f"## {app_config.verbose_name}\n\n"

                models = app_config.get_models()
                for model in models:
                    content += f"### {model.__name__}\n\n"
                    content += f"**الجدول:** `{model._meta.db_table}`\n\n"

                    # Fields
                    content += "**الحقول:**\n\n"
                    content += "| الحقل | النوع | الوصف |\n"
                    content += "|-------|------|-------|\n"

                    for field in model._meta.get_fields():
                        field_type = field.__class__.__name__
                        field_name = field.name
                        content += f"| `{field_name}` | {field_type} | - |\n"

                    content += "\n---\n\n"

        # Save to file
        filepath = os.path.join(docs_dir, 'MODELS.md')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'  ✓ Models documentation saved'))

    def _generate_urls_doc(self, docs_dir):
        """Generate URL patterns documentation"""
        self.stdout.write('Generating URLs documentation...')

        content = "# مسارات النظام (URL Patterns)\n\n"
        content += f"**تاريخ التوليد:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        resolver = get_resolver()

        content += "## Core URLs\n\n"
        content += "| المسار | الاسم | العرض |\n"
        content += "|--------|------|-------|\n"

        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'name') and pattern.name:
                content += f"| `{pattern.pattern}` | {pattern.name} | - |\n"

        content += "\n"

        # Save to file
        filepath = os.path.join(docs_dir, 'URLS.md')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'  ✓ URLs documentation saved'))

    def _generate_api_doc(self, docs_dir):
        """Generate API documentation"""
        self.stdout.write('Generating API documentation...')

        content = "# واجهات برمجية (API Endpoints)\n\n"
        content += f"**تاريخ التوليد:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        content += "## AJAX Endpoints\n\n"
        content += "### Chart Data APIs\n\n"
        content += "```\nGET /charts/price-trend/\nGET /charts/price-distribution/\nGET /charts/category-comparison/\nGET /charts/pricelist-comparison/\n```\n\n"

        content += "### DataTables APIs\n\n"
        content += "```\nGET /datatables/pricing-rules/\nGET /datatables/price-list-items/\nGET /datatables/item-prices/\n```\n\n"

        content += "### Price Operations\n\n"
        content += "```\nPOST /ajax/update-price/\nPOST /ajax/bulk-update-prices/\nPOST /ajax/calculate-price/\n```\n\n"

        # Save to file
        filepath = os.path.join(docs_dir, 'API.md')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'  ✓ API documentation saved'))

    def _generate_user_guide(self, docs_dir):
        """Generate user guide"""
        self.stdout.write('Generating user guide...')

        content = "# دليل المستخدم\n\n"
        content += f"**تاريخ التوليد:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        content += "## البدء السريع\n\n"
        content += "### 1. تسجيل الدخول\n"
        content += "- افتح المتصفح واذهب إلى رابط النظام\n"
        content += "- أدخل اسم المستخدم وكلمة المرور\n"
        content += "- اضغط على \"تسجيل الدخول\"\n\n"

        content += "### 2. لوحة التحكم\n"
        content += "- بعد تسجيل الدخول، ستظهر لوحة التحكم الرئيسية\n"
        content += "- من هنا يمكنك الوصول إلى جميع أقسام النظام\n\n"

        content += "## إدارة التسعير\n\n"
        content += "### قوائم الأسعار\n"
        content += "1. من القائمة الجانبية، اختر \"إدارة التسعير\" → \"قوائم الأسعار\"\n"
        content += "2. لإنشاء قائمة جديدة، اضغط \"إضافة قائمة أسعار\"\n"
        content += "3. املأ البيانات المطلوبة\n"
        content += "4. احفظ\n\n"

        content += "### استيراد الأسعار\n"
        content += "1. اختر \"استيراد الأسعار\" من القائمة\n"
        content += "2. حمّل قالب Excel أو CSV\n"
        content += "3. املأ البيانات في القالب\n"
        content += "4. ارفع الملف\n"
        content += "5. راجع النتائج\n\n"

        content += "### تصدير الأسعار\n"
        content += "1. اختر \"تصدير الأسعار\"\n"
        content += "2. اختر التنسيق (Excel أو CSV)\n"
        content += "3. حمّل الملف\n\n"

        content += "## الدعم الفني\n\n"
        content += "للحصول على المساعدة:\n"
        content += "- راجع التوثيق الكامل\n"
        content += "- اتصل بالدعم الفني\n\n"

        # Save to file
        filepath = os.path.join(docs_dir, 'USER_GUIDE.md')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'  ✓ User guide saved'))

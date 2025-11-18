# apps/core/management/commands/check_system.py
"""
System Health Check Command
Comprehensive system health and readiness check
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Perform comprehensive system health check'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ERP SYSTEM HEALTH CHECK'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        checks_passed = 0
        checks_failed = 0

        # 1. Database Check
        self.stdout.write('\n📊 Database Check:')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('  ✓ Database connection OK'))
                checks_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Database error: {str(e)}'))
            checks_failed += 1

        # 2. Cache Check
        self.stdout.write('\n🗄️  Cache Check:')
        try:
            cache.set('health_check', 'OK', 10)
            result = cache.get('health_check')
            if result == 'OK':
                self.stdout.write(self.style.SUCCESS('  ✓ Cache system OK'))
                checks_passed += 1
            else:
                self.stdout.write(self.style.WARNING('  ⚠ Cache not working properly'))
                checks_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Cache error: {str(e)}'))
            checks_failed += 1

        # 3. Static Files Check
        self.stdout.write('\n📁 Static Files Check:')
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            file_count = sum(len(files) for _, _, files in os.walk(static_root))
            self.stdout.write(self.style.SUCCESS(f'  ✓ Static files OK ({file_count} files)'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING('  ⚠ Static files not collected'))
            checks_failed += 1

        # 4. Media Files Check
        self.stdout.write('\n🖼️  Media Files Check:')
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            self.stdout.write(self.style.SUCCESS('  ✓ Media directory exists'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING('  ⚠ Media directory not found'))
            checks_failed += 1

        # 5. Debug Mode Check
        self.stdout.write('\n🔍 Debug Mode Check:')
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('  ⚠ DEBUG is ON (should be OFF in production)'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ DEBUG is OFF'))
            checks_passed += 1

        # 6. Secret Key Check
        self.stdout.write('\n🔐 Secret Key Check:')
        if settings.SECRET_KEY and len(settings.SECRET_KEY) >= 50:
            self.stdout.write(self.style.SUCCESS('  ✓ Secret key OK'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('  ✗ Secret key too short or missing'))
            checks_failed += 1

        # 7. Installed Apps Check
        self.stdout.write('\n📦 Installed Apps Check:')
        required_apps = ['apps.core', 'apps.accounting', 'apps.assets', 'apps.reports']
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {app}'))
                checks_passed += 1
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ {app} not installed'))
                checks_failed += 1

        # 8. Database Tables Check
        self.stdout.write('\n🗃️  Database Tables Check:')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_count = len(tables)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {table_count} tables found'))
                checks_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
            checks_failed += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        total_checks = checks_passed + checks_failed
        percentage = (checks_passed / total_checks * 100) if total_checks > 0 else 0

        self.stdout.write(f'\n📊 SUMMARY:')
        self.stdout.write(f'  Total Checks: {total_checks}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Passed: {checks_passed}'))
        if checks_failed > 0:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {checks_failed}'))
        self.stdout.write(f'  Health Score: {percentage:.1f}%')

        if percentage >= 90:
            self.stdout.write(self.style.SUCCESS('\n✅ System is HEALTHY and ready for production!'))
        elif percentage >= 70:
            self.stdout.write(self.style.WARNING('\n⚠️  System is MOSTLY HEALTHY but needs attention'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ System has CRITICAL ISSUES - not ready for production'))

        self.stdout.write('=' * 60 + '\n')

# apps/core/management/commands/optimize_database.py
"""
Database Optimization Command
Optimizes database tables and indexes for better performance
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Optimize database tables and create missing indexes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze tables instead of optimizing',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database optimization...'))

        # Get all models
        models = apps.get_models()

        with connection.cursor() as cursor:
            for model in models:
                table_name = model._meta.db_table

                try:
                    if options['analyze']:
                        # Analyze table
                        self.stdout.write(f'Analyzing {table_name}...')
                        cursor.execute(f'ANALYZE TABLE `{table_name}`')
                    else:
                        # Optimize table
                        self.stdout.write(f'Optimizing {table_name}...')
                        cursor.execute(f'OPTIMIZE TABLE `{table_name}`')

                    self.stdout.write(self.style.SUCCESS(f'✓ {table_name}'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ {table_name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Database optimization complete!'))

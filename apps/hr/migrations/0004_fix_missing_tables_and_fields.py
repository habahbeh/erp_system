# apps/hr/migrations/0004_fix_missing_tables_and_fields.py
"""
إصلاح الجداول والحقول المفقودة - تم إفراغه لأن المحتويات موجودة في migrations أخرى
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0003_phase1_settings'),
    ]

    operations = [
        # كل العمليات موجودة بالفعل في 0001_initial و 0003_phase1_settings
        # تم إفراغ هذا الملف لتجنب التكرار
    ]

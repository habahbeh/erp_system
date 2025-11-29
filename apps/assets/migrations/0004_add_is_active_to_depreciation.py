# Generated manually to add is_active field to AssetDepreciation

from django.db import migrations, connection


def add_is_active_field(apps, schema_editor):
    """إضافة حقل is_active حسب نوع قاعدة البيانات"""
    with connection.cursor() as cursor:
        if connection.vendor == 'mysql':
            # تحقق من وجود العمود
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'assets_assetdepreciation'
                AND COLUMN_NAME = 'is_active'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE assets_assetdepreciation
                    ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1
                """)
        else:
            # SQLite
            cursor.execute("PRAGMA table_info(assets_assetdepreciation)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'is_active' not in columns:
                cursor.execute("""
                    ALTER TABLE assets_assetdepreciation
                    ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1
                """)


def reverse_is_active_field(apps, schema_editor):
    """عكس الترحيل"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_add_basemodel_fields'),
    ]

    operations = [
        migrations.RunPython(add_is_active_field, reverse_is_active_field),
    ]

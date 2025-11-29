# Generated manually to add BaseModel fields to existing tables

from django.conf import settings
from django.db import migrations, models, connection
import django.db.models.deletion
import django.utils.timezone


def add_basemodel_fields_mysql(apps, schema_editor):
    """إضافة حقول BaseModel لـ MySQL"""
    if connection.vendor != 'mysql':
        return

    with connection.cursor() as cursor:
        # التحقق من وجود الأعمدة أولاً
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'assets_assetdepreciation'
            AND COLUMN_NAME = 'created_at'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE assets_assetdepreciation
                ADD COLUMN created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                ADD COLUMN updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                ADD COLUMN created_by_id INT NULL,
                ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1
            """)


def add_basemodel_fields_sqlite(apps, schema_editor):
    """إضافة حقول BaseModel لـ SQLite"""
    from django.db import connection as db_conn
    if db_conn.vendor != 'sqlite':
        return

    # في SQLite، نستخدم نهج مختلف
    with db_conn.cursor() as cursor:
        # التحقق من وجود الأعمدة
        cursor.execute("PRAGMA table_info(assets_assetdepreciation)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE assets_assetdepreciation ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE assets_assetdepreciation ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if 'created_by_id' not in columns:
            cursor.execute("ALTER TABLE assets_assetdepreciation ADD COLUMN created_by_id INTEGER NULL")
        if 'is_active' not in columns:
            cursor.execute("ALTER TABLE assets_assetdepreciation ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")


def add_basemodel_fields(apps, schema_editor):
    """إضافة الحقول حسب نوع قاعدة البيانات"""
    if connection.vendor == 'mysql':
        add_basemodel_fields_mysql(apps, schema_editor)
    else:
        add_basemodel_fields_sqlite(apps, schema_editor)


def reverse_basemodel_fields(apps, schema_editor):
    """عكس الترحيل - حذف الحقول"""
    # SQLite لا يدعم DROP COLUMN بشكل مباشر في الإصدارات القديمة
    # نترك الحقول كما هي في حالة reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0002_alter_asset_options_asset_actual_location_and_more'),
    ]

    operations = [
        migrations.RunPython(add_basemodel_fields, reverse_basemodel_fields),
    ]

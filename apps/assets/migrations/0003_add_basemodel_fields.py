# Generated manually to add BaseModel fields to existing tables

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0002_alter_asset_options_asset_actual_location_and_more'),
    ]

    operations = [
        # Add BaseModel fields to AssetDepreciation
        migrations.RunSQL(
            sql="""
                ALTER TABLE assets_assetdepreciation
                ADD COLUMN IF NOT EXISTS created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                ADD COLUMN IF NOT EXISTS updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                ADD COLUMN IF NOT EXISTS created_by_id INT NULL,
                ADD COLUMN IF NOT EXISTS is_active TINYINT(1) NOT NULL DEFAULT 1,
                ADD INDEX IF NOT EXISTS assets_assetdepreciation_created_by_id_fk (created_by_id);
            """,
            reverse_sql="""
                ALTER TABLE assets_assetdepreciation
                DROP INDEX IF EXISTS assets_assetdepreciation_created_by_id_fk,
                DROP COLUMN IF EXISTS is_active,
                DROP COLUMN IF EXISTS created_by_id,
                DROP COLUMN IF EXISTS updated_at,
                DROP COLUMN IF EXISTS created_at;
            """,
        ),
    ]

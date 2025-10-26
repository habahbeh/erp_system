# Generated manually to add is_active field to AssetDepreciation

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_add_basemodel_fields'),
    ]

    operations = [
        # Add is_active field to AssetDepreciation
        migrations.RunSQL(
            sql="""
                ALTER TABLE assets_assetdepreciation
                ADD COLUMN IF NOT EXISTS is_active TINYINT(1) NOT NULL DEFAULT 1;
            """,
            reverse_sql="""
                ALTER TABLE assets_assetdepreciation
                DROP COLUMN IF EXISTS is_active;
            """,
        ),
    ]

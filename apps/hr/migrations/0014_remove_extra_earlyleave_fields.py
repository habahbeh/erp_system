# Generated manually to align database with model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0013_add_notes_to_earlyleave'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE hr_earlyleave
            DROP COLUMN IF EXISTS leave_time,
            DROP COLUMN IF EXISTS expected_return,
            DROP COLUMN IF EXISTS actual_return,
            DROP COLUMN IF EXISTS duration_hours,
            DROP COLUMN IF EXISTS approval_date,
            DROP COLUMN IF EXISTS is_active;
            """,
            reverse_sql="""
            ALTER TABLE hr_earlyleave
            ADD COLUMN leave_time time(6) NOT NULL,
            ADD COLUMN expected_return time(6),
            ADD COLUMN actual_return time(6),
            ADD COLUMN duration_hours decimal(4,2) NOT NULL DEFAULT 0.00,
            ADD COLUMN approval_date datetime(6),
            ADD COLUMN is_active tinyint(1) NOT NULL DEFAULT 1;
            """,
        ),
    ]

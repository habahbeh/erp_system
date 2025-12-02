# Generated manually to add missing Payroll fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0015_alter_payroll_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE hr_payroll
            ADD COLUMN IF NOT EXISTS total_overtime decimal(15,2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_loans decimal(15,2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_social_security decimal(15,2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_income_tax decimal(15,2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS employee_count int(11) NOT NULL DEFAULT 0;
            """,
            reverse_sql="""
            ALTER TABLE hr_payroll
            DROP COLUMN IF EXISTS total_overtime,
            DROP COLUMN IF EXISTS total_loans,
            DROP COLUMN IF EXISTS total_social_security,
            DROP COLUMN IF EXISTS total_income_tax,
            DROP COLUMN IF EXISTS employee_count;
            """,
        ),
    ]

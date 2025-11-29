# apps/hr/migrations/0011_fix_employee_nullable_fields.py
"""
إصلاح الحقول المطلوبة في جدول الموظفين
"""

from django.db import migrations


def fix_nullable_fields(apps, schema_editor):
    """Fix nullable fields only if they exist"""
    # Skip for SQLite (used in tests)
    if schema_editor.connection.vendor == 'sqlite':
        return

    # Only run for MySQL
    if schema_editor.connection.vendor != 'mysql':
        return

    with schema_editor.connection.cursor() as cursor:
        # Get list of existing columns
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'hr_employee'
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}

        # List of fields to make nullable
        fields_to_fix = {
            'father_name': 'VARCHAR(50)',
            'mother_name': 'VARCHAR(50)',
            'birth_place': 'VARCHAR(100)',
            'phone': 'VARCHAR(20)',
            'email': 'VARCHAR(254)',
            'address': 'LONGTEXT',
            'hire_date': 'DATE',
            'contract_type': 'VARCHAR(20)',
            'employment_status': 'VARCHAR(20)',
            'bank_name': 'VARCHAR(100)',
            'gender': 'VARCHAR(10)',
            'marital_status': 'VARCHAR(10)',
        }

        # Only modify fields that exist
        for field_name, field_type in fields_to_fix.items():
            if field_name in existing_columns:
                cursor.execute(
                    f"ALTER TABLE hr_employee MODIFY {field_name} {field_type} NULL;"
                )


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0010_remove_leavebalance_earned_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_nullable_fields,
            reverse_code=migrations.RunPython.noop
        ),
    ]

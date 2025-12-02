# Generated manually to fix missing PayrollDetail fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0017_remove_jobgrade_unique_jobgrade_code_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add missing fields to hr_payrolldetail if they don't exist
            SET @dbname = DATABASE();
            SET @tablename = 'hr_payrolldetail';

            -- Check and add working_days
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'working_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN working_days int(11) NOT NULL DEFAULT 30',
                'SELECT "Column working_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Check and add actual_days
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'actual_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN actual_days int(11) NOT NULL DEFAULT 30',
                'SELECT "Column actual_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Check and add absent_days
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'absent_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN absent_days int(11) NOT NULL DEFAULT 0',
                'SELECT "Column absent_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """,
            reverse_sql="""
            -- Note: Reverse migration would drop these columns
            -- ALTER TABLE hr_payrolldetail DROP COLUMN IF EXISTS working_days;
            -- ALTER TABLE hr_payrolldetail DROP COLUMN IF EXISTS actual_days;
            -- ALTER TABLE hr_payrolldetail DROP COLUMN IF EXISTS absent_days;
            SELECT "Reverse migration not implemented to prevent data loss";
            """,
        ),
    ]

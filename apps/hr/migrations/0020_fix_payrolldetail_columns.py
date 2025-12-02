# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0019_add_all_missing_payrolldetail_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            SET @dbname = DATABASE();
            SET @tablename = 'hr_payrolldetail';

            -- Add working_days column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'working_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN working_days int(11) NOT NULL DEFAULT 30',
                'SELECT "Column working_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add actual_days column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'actual_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN actual_days int(11) NOT NULL DEFAULT 30',
                'SELECT "Column actual_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add absent_days column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'absent_days');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN absent_days int(11) NOT NULL DEFAULT 0',
                'SELECT "Column absent_days already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add housing_allowance column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'housing_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN housing_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column housing_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add transport_allowance column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'transport_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN transport_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column transport_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add phone_allowance column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'phone_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN phone_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column phone_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add food_allowance column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'food_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN food_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column food_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add other_allowances column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'other_allowances');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN other_allowances decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column other_allowances already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add total_allowances column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'total_allowances');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN total_allowances decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column total_allowances already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add overtime_hours column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'overtime_hours');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN overtime_hours decimal(6,2) NOT NULL DEFAULT 0',
                'SELECT "Column overtime_hours already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add overtime_amount column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'overtime_amount');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN overtime_amount decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column overtime_amount already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add absence_deduction column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'absence_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN absence_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column absence_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add late_deduction column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'late_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN late_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column late_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add loan_deduction column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'loan_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN loan_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column loan_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add social_security_employee column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'social_security_employee');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN social_security_employee decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column social_security_employee already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add social_security_company column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'social_security_company');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN social_security_company decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column social_security_company already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add income_tax column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'income_tax');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN income_tax decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column income_tax already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add other_deductions column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'other_deductions');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN other_deductions decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column other_deductions already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add total_deductions column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'total_deductions');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN total_deductions decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column total_deductions already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add gross_salary column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'gross_salary');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN gross_salary decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column gross_salary already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add payment_method column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'payment_method');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN payment_method varchar(20) NOT NULL DEFAULT "bank_transfer"',
                'SELECT "Column payment_method already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add payment_reference column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'payment_reference');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN payment_reference varchar(100) DEFAULT ""',
                'SELECT "Column payment_reference already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add is_paid column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'is_paid');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN is_paid tinyint(1) NOT NULL DEFAULT 0',
                'SELECT "Column is_paid already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add paid_date column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'paid_date');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN paid_date date NULL',
                'SELECT "Column paid_date already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Add notes column
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'notes');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN notes longtext',
                'SELECT "Column notes already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

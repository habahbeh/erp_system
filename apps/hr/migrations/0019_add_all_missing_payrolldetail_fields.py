# Generated manually to add ALL missing PayrollDetail fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0018_fix_missing_payrolldetail_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add all missing fields to hr_payrolldetail if they don't exist
            SET @dbname = DATABASE();
            SET @tablename = 'hr_payrolldetail';

            -- Basic salary
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'basic_salary');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN basic_salary decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column basic_salary already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Housing allowance
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'housing_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN housing_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column housing_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Transport allowance
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'transport_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN transport_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column transport_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Phone allowance
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'phone_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN phone_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column phone_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Food allowance
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'food_allowance');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN food_allowance decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column food_allowance already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Other allowances
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'other_allowances');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN other_allowances decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column other_allowances already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Total allowances
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'total_allowances');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN total_allowances decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column total_allowances already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Overtime hours
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'overtime_hours');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN overtime_hours decimal(6,2) NOT NULL DEFAULT 0',
                'SELECT "Column overtime_hours already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Overtime amount
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'overtime_amount');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN overtime_amount decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column overtime_amount already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Absence deduction
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'absence_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN absence_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column absence_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Late deduction
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'late_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN late_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column late_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Loan deduction
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'loan_deduction');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN loan_deduction decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column loan_deduction already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Social security employee
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'social_security_employee');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN social_security_employee decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column social_security_employee already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Social security company
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'social_security_company');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN social_security_company decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column social_security_company already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Income tax
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'income_tax');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN income_tax decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column income_tax already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Other deductions
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'other_deductions');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN other_deductions decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column other_deductions already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Total deductions
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'total_deductions');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN total_deductions decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column total_deductions already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Gross salary
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'gross_salary');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN gross_salary decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column gross_salary already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Net salary
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'net_salary');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN net_salary decimal(12,2) NOT NULL DEFAULT 0',
                'SELECT "Column net_salary already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Payment method
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'payment_method');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN payment_method varchar(20) NOT NULL DEFAULT "bank_transfer"',
                'SELECT "Column payment_method already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Payment reference
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'payment_reference');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN payment_reference varchar(100) NOT NULL DEFAULT ""',
                'SELECT "Column payment_reference already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Is paid
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'is_paid');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN is_paid tinyint(1) NOT NULL DEFAULT 0',
                'SELECT "Column is_paid already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Paid date
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'paid_date');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN paid_date date NULL',
                'SELECT "Column paid_date already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Notes
            SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'notes');
            SET @sql = IF(@col_exists = 0,
                'ALTER TABLE hr_payrolldetail ADD COLUMN notes longtext NOT NULL DEFAULT ""',
                'SELECT "Column notes already exists"');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """,
            reverse_sql="""
            SELECT "Reverse migration not implemented to prevent data loss";
            """,
        ),
    ]

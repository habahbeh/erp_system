#!/usr/bin/env python
"""
Create Demo Data for Accounting System
For server 138.68.146.118 only
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, date, timedelta

# Setup Django environment
sys.path.append('/var/www/erp_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import Company, Branch, Currency
from apps.accounting.models import (
    AccountType, Account, FiscalYear, AccountingPeriod,
    CostCenter, JournalEntry, JournalEntryLine,
    PaymentVoucher, ReceiptVoucher
)

User = get_user_model()

def create_demo_data():
    """Create comprehensive demo data for accounting system"""

    print("=" * 60)
    print("Creating Accounting Demo Data")
    print("=" * 60)

    # Get or create admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✓ Using existing admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("✗ Admin user not found. Please create admin user first.")
        return

    # Create or get base currency first
    currency, created = Currency.objects.get_or_create(
        code='JOD',
        defaults={
            'name': 'دينار أردني',
            'name_en': 'Jordanian Dinar',
            'symbol': 'د.أ',
            'exchange_rate': Decimal('1.00'),
            'is_base': True,
            'is_active': True
        }
    )

    if created:
        print(f"✓ Created currency: {currency.name}")
    else:
        print(f"✓ Using existing currency: {currency.name}")

    # Get or create demo company
    company, created = Company.objects.get_or_create(
        name='شركة التجارة العامة التجريبية',
        defaults={
            'name_en': 'Demo General Trading Company',
            'city': 'عمان',
            'phone': '+962-6-1234567',
            'email': 'info@demo-company.com',
            'base_currency': currency,
            'is_active': True,
            'fiscal_year_start_month': 1,
            'fiscal_year_start_day': 1
        }
    )

    if created:
        print(f"✓ Created demo company: {company.name}")
        # Create default sequences and accounts
        company.create_default_sequences()
        company.create_default_accounts()
    else:
        print(f"✓ Using existing company: {company.name}")

    # Get or create main branch
    branch, created = Branch.objects.get_or_create(
        company=company,
        code='MAIN',
        defaults={
            'name': 'الفرع الرئيسي',
            'address': 'شارع الملك عبدالله الثاني، عمان',
            'phone': '+962-6-1234567',
            'is_main': True,
            'is_active': True
        }
    )

    if created:
        print(f"✓ Created main branch: {branch.name}")
    else:
        print(f"✓ Using existing branch: {branch.name}")

    # Get currency (skip if not needed - Company might already have default currency)

    # Create Fiscal Year
    current_year = datetime.now().year
    fiscal_year, created = FiscalYear.objects.get_or_create(
        company=company,
        code=str(current_year),
        defaults={
            'name': f'السنة المالية {current_year}',
            'start_date': date(current_year, 1, 1),
            'end_date': date(current_year, 12, 31),
            'is_closed': False
        }
    )

    if created:
        print(f"✓ Created fiscal year: {fiscal_year.name}")
    else:
        print(f"✓ Using existing fiscal year: {fiscal_year.name}")

    # Create Accounting Periods (12 months)
    print("\n--- Creating Accounting Periods ---")
    periods_created = 0
    for month in range(1, 13):
        period_name = f"فترة {month:02d}/{current_year}"

        # Calculate start and end dates for the month
        start_date = date(current_year, month, 1)
        if month == 12:
            end_date = date(current_year, 12, 31)
        else:
            end_date = date(current_year, month + 1, 1) - timedelta(days=1)

        period, created = AccountingPeriod.objects.get_or_create(
            company=company,
            fiscal_year=fiscal_year,
            name=period_name,
            defaults={
                'start_date': start_date,
                'end_date': end_date,
                'is_closed': False
            }
        )

        if created:
            periods_created += 1

    print(f"✓ Created {periods_created} accounting periods")

    # Create Cost Centers
    print("\n--- Creating Cost Centers ---")
    cost_centers_data = [
        ('ADM', 'الإدارة العامة', None),
        ('SAL', 'المبيعات', None),
        ('PUR', 'المشتريات', None),
        ('PRD', 'الإنتاج', None),
        ('IT', 'تقنية المعلومات', 'ADM'),
        ('HR', 'الموارد البشرية', 'ADM'),
    ]

    cost_centers = {}
    for code, name, parent_code in cost_centers_data:
        parent = cost_centers.get(parent_code) if parent_code else None

        cc, created = CostCenter.objects.get_or_create(
            company=company,
            code=code,
            defaults={
                'name': name,
                'parent': parent,
                'is_active': True
            }
        )
        cost_centers[code] = cc

        if created:
            print(f"✓ Created cost center: {name}")

    # Get current period
    current_period = AccountingPeriod.objects.filter(
        company=company,
        fiscal_year=fiscal_year,
        start_date__lte=date.today(),
        end_date__gte=date.today(),
        is_closed=False
    ).first()

    if not current_period:
        current_period = AccountingPeriod.objects.filter(
            company=company,
            fiscal_year=fiscal_year,
            is_closed=False
        ).first()

    if not current_period:
        print("✗ No active accounting period found")
        return

    # Get some accounts for journal entries
    try:
        cash_account = Account.objects.filter(
            company=company,
            code__startswith='101'
        ).first()

        bank_account = Account.objects.filter(
            company=company,
            code__startswith='102'
        ).first()

        sales_account = Account.objects.filter(
            company=company,
            code__startswith='401'
        ).first()

        cost_of_sales = Account.objects.filter(
            company=company,
            code__startswith='501'
        ).first()

        expenses_account = Account.objects.filter(
            company=company,
            code__startswith='510'
        ).first()

        capital_account = Account.objects.filter(
            company=company,
            code__startswith='301'
        ).first()

    except Exception as e:
        print(f"✗ Error getting accounts: {e}")
        return

    # Create Journal Entries
    print("\n--- Creating Journal Entries ---")

    # Entry 1: Opening Balance
    if capital_account and bank_account:
        je1, created = JournalEntry.objects.get_or_create(
            company=company,
            reference='JE-2025-001',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date(current_year, 1, 1),
                'description': 'قيد افتتاحي - رأس المال',
                'status': 'posted',
                'created_by': admin_user
            }
        )

        if created:
            JournalEntryLine.objects.create(
                entry=je1,
                account=bank_account,
                debit=Decimal('100000.00'),
                credit=Decimal('0.00'),
                description='رصيد افتتاحي - البنك',
                created_by=admin_user
            )

            JournalEntryLine.objects.create(
                entry=je1,
                account=capital_account,
                debit=Decimal('0.00'),
                credit=Decimal('100000.00'),
                description='رأس المال',
                created_by=admin_user
            )

            print("✓ Created opening balance journal entry")

    # Entry 2: Sales Transaction
    if sales_account and cash_account:
        je2, created = JournalEntry.objects.get_or_create(
            company=company,
            reference='JE-2025-002',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date.today() - timedelta(days=5),
                'description': 'مبيعات نقدية',
                'cost_center': cost_centers.get('SAL'),
                'status': 'posted',
                'created_by': admin_user
            }
        )

        if created:
            JournalEntryLine.objects.create(
                entry=je2,
                account=cash_account,
                debit=Decimal('15000.00'),
                credit=Decimal('0.00'),
                description='مبيعات نقدية',
                cost_center=cost_centers.get('SAL'),
                created_by=admin_user
            )

            JournalEntryLine.objects.create(
                entry=je2,
                account=sales_account,
                debit=Decimal('0.00'),
                credit=Decimal('15000.00'),
                description='إيرادات مبيعات',
                cost_center=cost_centers.get('SAL'),
                created_by=admin_user
            )

            print("✓ Created sales journal entry")

    # Entry 3: Expenses
    if expenses_account and bank_account:
        je3, created = JournalEntry.objects.get_or_create(
            company=company,
            reference='JE-2025-003',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date.today() - timedelta(days=3),
                'description': 'مصاريف إدارية وعمومية',
                'cost_center': cost_centers.get('ADM'),
                'status': 'posted',
                'created_by': admin_user
            }
        )

        if created:
            JournalEntryLine.objects.create(
                entry=je3,
                account=expenses_account,
                debit=Decimal('5000.00'),
                credit=Decimal('0.00'),
                description='مصاريف إدارية',
                cost_center=cost_centers.get('ADM'),
                created_by=admin_user
            )

            JournalEntryLine.objects.create(
                entry=je3,
                account=bank_account,
                debit=Decimal('0.00'),
                credit=Decimal('5000.00'),
                description='الدفع من البنك',
                created_by=admin_user
            )

            print("✓ Created expenses journal entry")

    # Entry 4: Bank to Cash Transfer
    if cash_account and bank_account:
        je4, created = JournalEntry.objects.get_or_create(
            company=company,
            reference='JE-2025-004',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date.today() - timedelta(days=1),
                'description': 'سحب نقدي من البنك',
                'status': 'posted',
                'created_by': admin_user
            }
        )

        if created:
            JournalEntryLine.objects.create(
                entry=je4,
                account=cash_account,
                debit=Decimal('10000.00'),
                credit=Decimal('0.00'),
                description='سحب نقدي',
                created_by=admin_user
            )

            JournalEntryLine.objects.create(
                entry=je4,
                account=bank_account,
                debit=Decimal('0.00'),
                credit=Decimal('10000.00'),
                description='سحب من البنك',
                created_by=admin_user
            )

            print("✓ Created bank transfer journal entry")

    # Create Payment Vouchers
    print("\n--- Creating Payment Vouchers ---")

    if expenses_account and cash_account:
        pv1, created = PaymentVoucher.objects.get_or_create(
            company=company,
            voucher_number='PV-2025-001',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date.today() - timedelta(days=2),
                'account': expenses_account,
                'payment_method': 'cash',
                'amount': Decimal('2000.00'),
                'description': 'دفع مصاريف كهرباء ومياه',
                'payee_name': 'شركة الكهرباء الوطنية',
                'status': 'paid',
                'created_by': admin_user
            }
        )

        if created:
            print("✓ Created payment voucher PV-2025-001")

    # Create Receipt Vouchers
    print("\n--- Creating Receipt Vouchers ---")

    if sales_account and cash_account:
        rv1, created = ReceiptVoucher.objects.get_or_create(
            company=company,
            voucher_number='RV-2025-001',
            defaults={
                'branch': branch,
                'fiscal_year': fiscal_year,
                'period': current_period,
                'date': date.today() - timedelta(days=1),
                'account': sales_account,
                'payment_method': 'cash',
                'amount': Decimal('8000.00'),
                'description': 'قبض من عميل نقداً',
                'payer_name': 'شركة التجارة الأولى',
                'status': 'received',
                'created_by': admin_user
            }
        )

        if created:
            print("✓ Created receipt voucher RV-2025-001")

    print("\n" + "=" * 60)
    print("✓ Demo Data Creation Completed Successfully!")
    print("=" * 60)
    print(f"\nCompany: {company.name}")
    print(f"Branch: {branch.name}")
    print(f"Fiscal Year: {fiscal_year.name}")
    print(f"Current Period: {current_period.name}")
    print(f"\nJournal Entries: {JournalEntry.objects.filter(company=company).count()}")
    print(f"Payment Vouchers: {PaymentVoucher.objects.filter(company=company).count()}")
    print(f"Receipt Vouchers: {ReceiptVoucher.objects.filter(company=company).count()}")
    print(f"Cost Centers: {CostCenter.objects.filter(company=company).count()}")
    print("\nYou can now login to http://138.68.146.118/ and explore the demo data!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        create_demo_data()
    except Exception as e:
        print(f"\n✗ Error creating demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

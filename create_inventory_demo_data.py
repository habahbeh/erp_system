#!/usr/bin/env python
"""
Script to create demo data for Inventory Management System
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import (
    Company, Branch, Warehouse, Item, BusinessPartner,
    ItemCategory, Currency, UnitOfMeasure, UoMGroup
)
from apps.inventory.models import (
    StockIn, StockOut, StockTransfer, StockDocumentLine,
    StockTransferLine, ItemStock
)

User = get_user_model()

def create_inventory_demo_data():
    print("=" * 80)
    print("Creating Inventory Demo Data")
    print("=" * 80)

    # Get or create superuser
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("Creating superuser...")
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print(f"✓ Superuser created: {user.username}")
        else:
            print(f"✓ Using existing superuser: {user.username}")
    except Exception as e:
        print(f"✗ Error with user: {e}")
        return

    # Get or create company
    try:
        company = Company.objects.first()
        if not company:
            print("Creating company...")
            company = Company.objects.create(
                name='شركة النظام التجريبية',
                name_en='Demo System Company',
                tax_number='123456789',
                email='info@demo.com',
                phone='0123456789'
            )
            # Create default sequences and accounts
            company.create_default_sequences()
            company.create_default_accounts()
            print(f"✓ Company created: {company.name}")
        else:
            print(f"✓ Using existing company: {company.name}")
    except Exception as e:
        print(f"✗ Error with company: {e}")
        return

    # Get or create branch
    try:
        branch = Branch.objects.filter(company=company).first()
        if not branch:
            print("Creating branch...")
            branch = Branch.objects.create(
                company=company,
                name='الفرع الرئيسي',
                name_en='Main Branch',
                code='MAIN',
                is_active=True,
                created_by=user
            )
            print(f"✓ Branch created: {branch.name}")
        else:
            print(f"✓ Using existing branch: {branch.name}")
    except Exception as e:
        print(f"✗ Error with branch: {e}")
        return

    # Get or create warehouses
    warehouses = []
    warehouse_data = [
        {'name': 'المستودع الرئيسي', 'name_en': 'Main Warehouse', 'code': 'WH-MAIN'},
        {'name': 'مستودع الفرع الأول', 'name_en': 'Branch 1 Warehouse', 'code': 'WH-B1'},
        {'name': 'مستودع الفرع الثاني', 'name_en': 'Branch 2 Warehouse', 'code': 'WH-B2'},
    ]

    print("\nCreating/Getting Warehouses:")
    for wh_data in warehouse_data:
        try:
            warehouse, created = Warehouse.objects.get_or_create(
                company=company,
                code=wh_data['code'],
                defaults={
                    'name': wh_data['name'],
                    'name_en': wh_data['name_en'],
                    'branch': branch,
                    'is_active': True,
                    'created_by': user
                }
            )
            warehouses.append(warehouse)
            status = "Created" if created else "Exists"
            print(f"  {status}: {warehouse.name} ({warehouse.code})")
        except Exception as e:
            print(f"  ✗ Error with warehouse {wh_data['code']}: {e}")

    # Get or create category
    print("\nCreating/Getting Item Category:")
    try:
        category, created = ItemCategory.objects.get_or_create(
            company=company,
            code='CAT-001',
            defaults={
                'name': 'مواد عامة',
                'name_en': 'General Items',
                'is_active': True,
                'created_by': user
            }
        )
        status = "Created" if created else "Exists"
        print(f"  {status}: {category.name}")
    except Exception as e:
        print(f"  ✗ Error with category: {e}")
        return

    # Get or create currency
    print("\nCreating/Getting Currency:")
    try:
        currency, created = Currency.objects.get_or_create(
            code='JOD',
            defaults={
                'name': 'دينار أردني',
                'name_en': 'Jordanian Dinar',
                'symbol': 'د.أ',
                'exchange_rate': Decimal('1.0'),
                'is_base': True,
                'is_active': True
            }
        )
        status = "Created" if created else "Exists"
        print(f"  {status}: {currency.name}")
    except Exception as e:
        print(f"  ✗ Error with currency: {e}")
        return

    # Get or create UoM Group
    print("\nCreating/Getting UoM Group:")
    try:
        uom_group, created = UoMGroup.objects.get_or_create(
            company=company,
            code='UNIT',
            defaults={
                'name': 'وحدات',
                'name_en': 'Units',
                'is_active': True,
                'created_by': user
            }
        )
        status = "Created" if created else "Exists"
        print(f"  {status}: {uom_group.name}")
    except Exception as e:
        print(f"  ✗ Error with UoM Group: {e}")
        return

    # Get or create UOM
    print("\nCreating/Getting Unit of Measure:")
    try:
        uom, created = UnitOfMeasure.objects.get_or_create(
            company=company,
            code='PCS',
            defaults={
                'name': 'قطعة',
                'name_en': 'Piece',
                'uom_type': 'UNIT',
                'uom_group': uom_group,
                'is_active': True,
                'created_by': user
            }
        )
        status = "Created" if created else "Exists"
        print(f"  {status}: {uom.name}")
    except Exception as e:
        print(f"  ✗ Error with UOM: {e}")
        return

    # Get or create items
    items = []
    item_data = [
        {'name': 'لابتوب Dell XPS 15', 'code': 'ITEM-001', 'cost': 15000},
        {'name': 'شاشة Samsung 27 بوصة', 'code': 'ITEM-002', 'cost': 2500},
        {'name': 'كيبورد لوجيتك', 'code': 'ITEM-003', 'cost': 350},
        {'name': 'ماوس لاسلكي', 'code': 'ITEM-004', 'cost': 150},
        {'name': 'طابعة HP LaserJet', 'code': 'ITEM-005', 'cost': 3500},
        {'name': 'كرسي مكتب', 'code': 'ITEM-006', 'cost': 1200},
        {'name': 'مكتب خشبي', 'code': 'ITEM-007', 'cost': 2800},
        {'name': 'خزانة ملفات', 'code': 'ITEM-008', 'cost': 1800},
    ]

    print("\nCreating/Getting Items:")
    for item_info in item_data:
        try:
            item, created = Item.objects.get_or_create(
                company=company,
                code=item_info['code'],
                defaults={
                    'name': item_info['name'],
                    'name_en': item_info['name'],
                    'category': category,
                    'currency': currency,
                    'base_uom': uom,
                    'is_active': True,
                    'tax_rate': Decimal('16.0'),
                    'created_by': user
                }
            )
            items.append(item)
            status = "Created" if created else "Exists"
            print(f"  {status}: {item.name} ({item.code})")
        except Exception as e:
            print(f"  ✗ Error with item {item_info['code']}: {e}")

    # Get or create suppliers
    print("\nCreating/Getting Suppliers:")
    suppliers = []
    supplier_data = [
        {'name': 'مورد الأجهزة الإلكترونية', 'code': 'SUP-001'},
        {'name': 'مورد الأثاث المكتبي', 'code': 'SUP-002'},
    ]

    for sup_data in supplier_data:
        try:
            supplier, created = BusinessPartner.objects.get_or_create(
                company=company,
                code=sup_data['code'],
                defaults={
                    'name': sup_data['name'],
                    'name_en': sup_data['name'],
                    'partner_type': 'supplier',
                    'is_active': True,
                    'created_by': user
                }
            )
            suppliers.append(supplier)
            status = "Created" if created else "Exists"
            print(f"  {status}: {supplier.name} ({supplier.code})")
        except Exception as e:
            print(f"  ✗ Error with supplier {sup_data['code']}: {e}")

    # Create Stock In documents
    print("\n" + "=" * 80)
    print("Creating Stock In Documents (سندات الإدخال)")
    print("=" * 80)

    stock_ins = []
    for i in range(3):
        try:
            # Create Stock In
            stock_in = StockIn.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouses[0],  # Main warehouse
                date=date.today() - timedelta(days=30-i*5),
                source_type='purchase',
                supplier=suppliers[0] if i < 2 else suppliers[1],
                reference=f'PO-2025-{100+i}',
                notes=f'إدخال مخزون رقم {i+1}',
                created_by=user
            )

            # Add lines to Stock In
            lines_data = [
                (items[i*2], 10 + i*5, item_data[i*2]['cost']),
                (items[i*2 + 1], 20 + i*3, item_data[i*2 + 1]['cost']),
            ]

            for item, qty, cost in lines_data:
                StockDocumentLine.objects.create(
                    stock_in=stock_in,
                    item=item,
                    quantity=Decimal(str(qty)),
                    unit_cost=Decimal(str(cost)),
                    notes=f'استلام {item.name}'
                )

            stock_ins.append(stock_in)
            print(f"✓ Created Stock In: {stock_in.number} - {stock_in.date}")
            print(f"  Lines: {stock_in.lines.count()}")

            # Post the document
            try:
                stock_in.post(user=user)
                print(f"  ✓ Posted successfully")
            except Exception as e:
                print(f"  ✗ Error posting: {e}")

        except Exception as e:
            print(f"✗ Error creating Stock In {i+1}: {e}")

    # Create Stock Out documents
    print("\n" + "=" * 80)
    print("Creating Stock Out Documents (سندات الإخراج)")
    print("=" * 80)

    stock_outs = []
    for i in range(2):
        try:
            # Create Stock Out
            stock_out = StockOut.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouses[0],  # Main warehouse
                date=date.today() - timedelta(days=15-i*5),
                destination_type='sale',
                reference=f'SO-2025-{100+i}',
                notes=f'إخراج مخزون رقم {i+1}',
                created_by=user
            )

            # Add lines to Stock Out
            lines_data = [
                (items[i*2], 5 + i*2, item_data[i*2]['cost']),
                (items[i*2 + 1], 8 + i*3, item_data[i*2 + 1]['cost']),
            ]

            for item, qty, cost in lines_data:
                StockDocumentLine.objects.create(
                    stock_out=stock_out,
                    item=item,
                    quantity=Decimal(str(qty)),
                    unit_cost=Decimal(str(cost)),
                    notes=f'صرف {item.name}'
                )

            stock_outs.append(stock_out)
            print(f"✓ Created Stock Out: {stock_out.number} - {stock_out.date}")
            print(f"  Lines: {stock_out.lines.count()}")

            # Post the document
            try:
                stock_out.post(user=user)
                print(f"  ✓ Posted successfully")
            except Exception as e:
                print(f"  ✗ Error posting: {e}")

        except Exception as e:
            print(f"✗ Error creating Stock Out {i+1}: {e}")

    # Create Stock Transfer documents
    print("\n" + "=" * 80)
    print("Creating Stock Transfer Documents (التحويلات المخزنية)")
    print("=" * 80)

    stock_transfers = []
    for i in range(2):
        try:
            # Create Stock Transfer
            transfer = StockTransfer.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouses[0],  # From main warehouse
                destination_warehouse=warehouses[i+1],  # To branch warehouses
                date=date.today() - timedelta(days=10-i*3),
                reference=f'TR-2025-{100+i}',
                notes=f'تحويل مخزون رقم {i+1}',
                created_by=user
            )

            # Add lines to Transfer
            lines_data = [
                (items[i*2], 3 + i),
                (items[i*2 + 1], 5 + i*2),
            ]

            for item, qty in lines_data:
                StockTransferLine.objects.create(
                    transfer=transfer,
                    item=item,
                    quantity=Decimal(str(qty)),
                    notes=f'تحويل {item.name}'
                )

            stock_transfers.append(transfer)
            print(f"✓ Created Transfer: {transfer.number} - {transfer.date}")
            print(f"  From: {transfer.warehouse.name}")
            print(f"  To: {transfer.destination_warehouse.name}")
            print(f"  Lines: {transfer.lines.count()}")

            # Post and approve the transfer
            try:
                transfer.post(user=user)
                print(f"  ✓ Posted successfully")
                transfer.approve(user=user)
                print(f"  ✓ Approved successfully")
            except Exception as e:
                print(f"  ✗ Error posting/approving: {e}")

        except Exception as e:
            print(f"✗ Error creating Transfer {i+1}: {e}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY - الملخص")
    print("=" * 80)
    print(f"✓ Warehouses: {len(warehouses)}")
    print(f"✓ Items: {len(items)}")
    print(f"✓ Suppliers: {len(suppliers)}")
    print(f"✓ Stock In Documents: {len(stock_ins)}")
    print(f"✓ Stock Out Documents: {len(stock_outs)}")
    print(f"✓ Transfer Documents: {len(stock_transfers)}")

    # Check ItemStock
    print("\n" + "=" * 80)
    print("Current Stock Levels (المخزون الحالي)")
    print("=" * 80)

    stocks = ItemStock.objects.filter(company=company).select_related('item', 'warehouse')
    if stocks.exists():
        for stock in stocks:
            if stock.quantity > 0:
                print(f"  {stock.item.name[:40]:<40} | {stock.warehouse.name[:20]:<20} | Qty: {stock.quantity:>8.2f}")
    else:
        print("  No stock records found")

    print("\n" + "=" * 80)
    print("Demo Data Creation Complete! ✓")
    print("=" * 80)
    print("\nYou can now login with:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nAccess inventory at: http://localhost:8000/inventory/")
    print("=" * 80)

if __name__ == '__main__':
    try:
        create_inventory_demo_data()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

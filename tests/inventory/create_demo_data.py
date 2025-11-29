# tests/inventory/create_demo_data.py
"""
سكريبت إنشاء بيانات تجريبية لنظام المخزون
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta
import random

# إعداد Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.core.models import (
    Company, Branch, User, Warehouse, Item, ItemCategory,
    UnitOfMeasure, UOMGroup, Currency, BusinessPartner
)
from apps.inventory.models import (
    StockIn, StockOut, StockTransfer, StockDocumentLine,
    StockTransferLine, ItemStock, Batch, StockCount, StockCountLine
)


def create_demo_data():
    """إنشاء بيانات تجريبية شاملة"""

    print("=" * 60)
    print("إنشاء بيانات تجريبية لنظام المخزون")
    print("=" * 60)

    with transaction.atomic():
        # 1. الحصول على الشركة أو إنشاءها
        print("\n[1/10] إعداد الشركة والفرع...")
        company = Company.objects.first()
        if not company:
            currency, _ = Currency.objects.get_or_create(
                code='JOD',
                defaults={
                    'name': 'دينار أردني',
                    'symbol': 'د.أ',
                    'exchange_rate': Decimal('1.0'),
                    'is_base': True
                }
            )
            company = Company.objects.create(
                name='شركة الاختبار',
                code='TEST',
                base_currency=currency,
                is_active=True
            )

        branch = Branch.objects.filter(company=company).first()
        if not branch:
            branch = Branch.objects.create(
                company=company,
                name='الفرع الرئيسي',
                code='MAIN',
                is_main=True,
                is_active=True
            )

        # 2. الحصول على المستخدم
        print("[2/10] إعداد المستخدم...")
        user = User.objects.filter(company=company).first()
        if not user:
            user = User.objects.create_user(
                username='demo_user',
                email='demo@test.com',
                password='demo123',
                company=company,
                branch=branch
            )

        # 3. إنشاء المستودعات
        print("[3/10] إنشاء المستودعات...")
        warehouses = []
        warehouse_names = [
            ('المستودع الرئيسي', 'WH-MAIN'),
            ('مستودع المواد الخام', 'WH-RAW'),
            ('مستودع المنتجات الجاهزة', 'WH-FINISH'),
            ('مستودع قطع الغيار', 'WH-SPARE'),
        ]

        for name, code in warehouse_names:
            wh, created = Warehouse.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'branch': branch,
                    'name': name,
                    'is_active': True,
                    'allow_negative_stock': False,
                    'created_by': user
                }
            )
            warehouses.append(wh)
            if created:
                print(f"   + تم إنشاء: {name}")

        # 4. إنشاء وحدات القياس
        print("[4/10] إنشاء وحدات القياس...")
        uom_group, _ = UOMGroup.objects.get_or_create(
            company=company,
            name='مجموعة الوحدات الأساسية',
            defaults={'created_by': user}
        )

        uom_data = [
            ('قطعة', 'PC', Decimal('1')),
            ('كرتونة', 'CTN', Decimal('12')),
            ('كيلو', 'KG', Decimal('1')),
            ('متر', 'M', Decimal('1')),
            ('لتر', 'L', Decimal('1')),
        ]

        uoms = {}
        for name, code, factor in uom_data:
            uom, created = UnitOfMeasure.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'group': uom_group,
                    'name': name,
                    'symbol': name,
                    'is_base_unit': True,
                    'conversion_factor': factor,
                    'created_by': user
                }
            )
            uoms[code] = uom

        # 5. إنشاء التصنيفات
        print("[5/10] إنشاء التصنيفات...")
        categories = []
        category_names = [
            'مواد كهربائية',
            'مواد ميكانيكية',
            'مواد استهلاكية',
            'قطع غيار',
            'معدات',
        ]

        for i, name in enumerate(category_names):
            cat, created = ItemCategory.objects.get_or_create(
                company=company,
                code=f'CAT-{i+1:02d}',
                defaults={
                    'name': name,
                    'created_by': user
                }
            )
            categories.append(cat)

        # 6. إنشاء الموردين والعملاء
        print("[6/10] إنشاء الموردين والعملاء...")
        suppliers = []
        customers = []

        supplier_names = ['مورد الكهرباء', 'مورد الميكانيكا', 'مورد العام']
        customer_names = ['عميل أ', 'عميل ب', 'عميل ج']

        for i, name in enumerate(supplier_names):
            sup, _ = BusinessPartner.objects.get_or_create(
                company=company,
                code=f'SUP-{i+1:03d}',
                defaults={
                    'name': name,
                    'partner_type': 'supplier',
                    'is_active': True,
                    'created_by': user
                }
            )
            suppliers.append(sup)

        for i, name in enumerate(customer_names):
            cust, _ = BusinessPartner.objects.get_or_create(
                company=company,
                code=f'CUST-{i+1:03d}',
                defaults={
                    'name': name,
                    'partner_type': 'customer',
                    'is_active': True,
                    'created_by': user
                }
            )
            customers.append(cust)

        # 7. إنشاء المواد
        print("[7/10] إنشاء المواد...")
        currency = Currency.objects.filter(code='JOD').first() or Currency.objects.first()

        items = []
        item_data = [
            ('سلك كهربائي 2.5mm', categories[0], uoms['M'], Decimal('0.5')),
            ('مفتاح كهربائي', categories[0], uoms['PC'], Decimal('3.0')),
            ('لمبة LED', categories[0], uoms['PC'], Decimal('5.0')),
            ('برغي 6mm', categories[1], uoms['PC'], Decimal('0.1')),
            ('صامولة 6mm', categories[1], uoms['PC'], Decimal('0.05')),
            ('شحم صناعي', categories[2], uoms['KG'], Decimal('8.0')),
            ('زيت محركات', categories[2], uoms['L'], Decimal('12.0')),
            ('فلتر هواء', categories[3], uoms['PC'], Decimal('15.0')),
            ('فلتر زيت', categories[3], uoms['PC'], Decimal('10.0')),
            ('مثقاب كهربائي', categories[4], uoms['PC'], Decimal('85.0')),
        ]

        for i, (name, category, uom, cost) in enumerate(item_data):
            item, created = Item.objects.get_or_create(
                company=company,
                code=f'ITEM-{i+1:03d}',
                defaults={
                    'name': name,
                    'category': category,
                    'base_uom': uom,
                    'currency': currency,
                    'tax_rate': Decimal('16.0'),
                    'has_variants': False,
                    'is_active': True,
                    'created_by': user
                }
            )
            items.append((item, cost))
            if created:
                print(f"   + تم إنشاء: {name}")

        # 8. إنشاء سندات إدخال (أرصدة افتتاحية)
        print("[8/10] إنشاء سندات الإدخال...")
        main_warehouse = warehouses[0]

        for item, cost in items:
            # سند إدخال رصيد افتتاحي
            stock_in = StockIn.objects.create(
                company=company,
                branch=branch,
                date=date.today() - timedelta(days=30),
                warehouse=main_warehouse,
                source_type='opening',
                notes=f'رصيد افتتاحي - {item.name}',
                created_by=user
            )

            qty = Decimal(str(random.randint(50, 200)))
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=item,
                quantity=qty,
                unit_cost=cost
            )

            # إنشاء رصيد مباشر
            ItemStock.objects.get_or_create(
                company=company,
                item=item,
                warehouse=main_warehouse,
                defaults={
                    'quantity': qty,
                    'average_cost': cost,
                    'total_value': qty * cost,
                    'min_level': Decimal('10'),
                    'max_level': Decimal('500'),
                    'reorder_point': Decimal('20'),
                    'created_by': user
                }
            )

        print(f"   + تم إنشاء {len(items)} سند إدخال")

        # 9. إنشاء دفعات
        print("[9/10] إنشاء الدفعات...")
        batch_count = 0
        for item, cost in items[:5]:  # أول 5 مواد فقط
            for j in range(3):
                Batch.objects.get_or_create(
                    company=company,
                    item=item,
                    warehouse=main_warehouse,
                    batch_number=f'BATCH-{item.code}-{j+1:02d}',
                    defaults={
                        'manufacturing_date': date.today() - timedelta(days=random.randint(30, 180)),
                        'expiry_date': date.today() + timedelta(days=random.randint(30, 365)),
                        'quantity': Decimal(str(random.randint(20, 50))),
                        'unit_cost': cost,
                        'total_value': Decimal(str(random.randint(20, 50))) * cost,
                        'received_date': date.today() - timedelta(days=random.randint(1, 30)),
                        'created_by': user
                    }
                )
                batch_count += 1

        print(f"   + تم إنشاء {batch_count} دفعة")

        # 10. إنشاء تحويل
        print("[10/10] إنشاء التحويلات...")
        if len(warehouses) >= 2:
            transfer = StockTransfer.objects.create(
                company=company,
                branch=branch,
                date=date.today(),
                warehouse=warehouses[0],
                destination_warehouse=warehouses[1],
                status='draft',
                notes='تحويل تجريبي',
                created_by=user
            )

            # إضافة سطر للتحويل
            item, cost = items[0]
            StockTransferLine.objects.create(
                transfer=transfer,
                item=item,
                quantity=Decimal('10'),
                unit_cost=cost
            )

            print("   + تم إنشاء 1 تحويل")

        print("\n" + "=" * 60)
        print("تم إنشاء البيانات التجريبية بنجاح!")
        print("=" * 60)

        # إحصائيات
        print("\nإحصائيات:")
        print(f"  - المستودعات: {len(warehouses)}")
        print(f"  - المواد: {len(items)}")
        print(f"  - الموردين: {len(suppliers)}")
        print(f"  - العملاء: {len(customers)}")
        print(f"  - الدفعات: {batch_count}")


if __name__ == '__main__':
    create_demo_data()

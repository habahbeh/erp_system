#!/usr/bin/env python
"""
Script to clear all items and create 10 sample items with different configurations
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import (
    Item, ItemVariant, ItemVariantAttributeValue, ItemCategory, Brand,
    UnitOfMeasure, Company, Currency, VariantAttribute, VariantValue,
    PriceList, PriceListItem
)
from decimal import Decimal

def clear_all_data():
    """حذف جميع البيانات المرتبطة بالمواد"""
    print("=" * 60)
    print("🗑️  حذف البيانات المرتبطة...")
    print("=" * 60)

    # 1. حذف بيانات المخزون
    try:
        from apps.inventory.models import StockDocumentLine, StockMovement
        count1 = StockMovement.objects.all().delete()[0]
        count2 = StockDocumentLine.objects.all().delete()[0]
        print(f"✅ حذف {count1} حركة مخزون و {count2} سطر مستند مخزون")
    except Exception as e:
        print(f"⚠️  المخزون: {e}")

    # 2. حذف بيانات المشتريات
    try:
        from apps.purchases.models import (
            PurchaseInvoiceItem, PurchaseOrderItem, PurchaseRequestItem,
            PurchaseQuotationItem, PurchaseQuotationRequestItem, PurchaseContractItem
        )
        counts = []
        counts.append(PurchaseInvoiceItem.objects.all().delete()[0])
        counts.append(PurchaseOrderItem.objects.all().delete()[0])
        counts.append(PurchaseRequestItem.objects.all().delete()[0])
        counts.append(PurchaseQuotationItem.objects.all().delete()[0])
        counts.append(PurchaseQuotationRequestItem.objects.all().delete()[0])
        counts.append(PurchaseContractItem.objects.all().delete()[0])
        print(f"✅ حذف {sum(counts)} سجل من المشتريات")
    except Exception as e:
        print(f"⚠️  المشتريات: {e}")

    # 3. حذف بيانات المبيعات
    try:
        from apps.sales.models import InvoiceItem, QuotationItem, SalesOrderItem
        counts = []
        counts.append(InvoiceItem.objects.all().delete()[0])
        counts.append(QuotationItem.objects.all().delete()[0])
        counts.append(SalesOrderItem.objects.all().delete()[0])
        print(f"✅ حذف {sum(counts)} سجل من المبيعات")
    except Exception as e:
        print(f"⚠️  المبيعات: {e}")

    # 4. حذف أسعار المواد
    count = PriceListItem.objects.all().delete()[0]
    print(f"✅ حذف {count} سعر")

    # 5. حذف قيم خصائص المتغيرات
    count = ItemVariantAttributeValue.objects.all().delete()[0]
    print(f"✅ حذف {count} قيمة خاصية متغير")

    # 6. حذف المتغيرات
    count = ItemVariant.objects.all().delete()[0]
    print(f"✅ حذف {count} متغير")

    # 7. حذف المواد
    count = Item.objects.all().delete()[0]
    print(f"✅ حذف {count} مادة")

    print("\n✅ تم حذف جميع البيانات بنجاح\n")


def create_sample_items():
    """إنشاء 10 مواد نموذجية"""
    print("=" * 60)
    print("📦 إنشاء مواد نموذجية...")
    print("=" * 60)

    # الحصول على البيانات الأساسية
    company = Company.objects.first()
    categories = list(ItemCategory.objects.filter(company=company, is_active=True)[:3])
    brands = list(Brand.objects.filter(company=company, is_active=True)[:3])
    uom_piece = UnitOfMeasure.objects.filter(company=company, name__icontains='قطعة').first()
    uom_kg = UnitOfMeasure.objects.filter(company=company, name__icontains='كيلو').first()
    uom_meter = UnitOfMeasure.objects.filter(company=company, name__icontains='متر').first()
    currency = Currency.objects.filter(code='JOD').first()

    if not uom_piece:
        uom_piece = UnitOfMeasure.objects.filter(company=company).first()

    # الحصول على قوائم الأسعار
    price_lists = list(PriceList.objects.filter(company=company, is_active=True)[:2])

    # الحصول على خصائص المتغيرات
    color_attr = VariantAttribute.objects.filter(company=company, name__icontains='لون').first()
    size_attr = VariantAttribute.objects.filter(company=company, name__icontains='مقاس').first()

    print(f"✅ Company: {company.name}")
    print(f"✅ Categories: {len(categories)}")
    print(f"✅ Brands: {len(brands)}")
    print(f"✅ Price Lists: {len(price_lists)}")
    print(f"✅ Color Attribute: {color_attr.name if color_attr else 'لا يوجد'}")
    print(f"✅ Size Attribute: {size_attr.name if size_attr else 'لا يوجد'}")
    print()

    items_data = [
        {
            'name': 'لابتوب ديل انسبيرون 15',
            'name_en': 'Dell Inspiron 15 Laptop',
            'category': categories[0] if categories else None,
            'brand': brands[0] if brands else None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'لابتوب ديل انسبيرون 15 بوصة، معالج Intel Core i7، رام 16GB، هارد 512GB SSD',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('2.500'),
            'prices': {price_lists[0].id: Decimal('850.000'), price_lists[1].id: Decimal('820.000')} if price_lists else {}
        },
        {
            'name': 'ماوس لاسلكي لوجيتك',
            'name_en': 'Logitech Wireless Mouse',
            'category': categories[0] if categories else None,
            'brand': brands[1] if len(brands) > 1 else brands[0] if brands else None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'ماوس لاسلكي بتقنية البلوتوث، بطارية تدوم 18 شهر',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('0.150'),
            'prices': {price_lists[0].id: Decimal('25.000')} if price_lists else {}
        },
        {
            'name': 'قميص رجالي قطن',
            'name_en': 'Men Cotton Shirt',
            'category': categories[1] if len(categories) > 1 else categories[0] if categories else None,
            'brand': brands[2] if len(brands) > 2 else brands[0] if brands else None,
            'base_uom': uom_piece,
            'has_variants': True,  # سيكون له متغيرات (ألوان ومقاسات)
            'description': 'قميص رجالي قطن 100%، متوفر بألوان ومقاسات متعددة',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('0.300'),
            'create_variants': True,
            'prices': {}  # الأسعار للمتغيرات
        },
        {
            'name': 'طاولة مكتب خشبية',
            'name_en': 'Wooden Office Desk',
            'category': categories[2] if len(categories) > 2 else categories[0] if categories else None,
            'brand': None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'طاولة مكتب خشبية بتصميم عصري، الأبعاد: 120x60x75 سم',
            'tax_rate': Decimal('16.00'),
            'length': Decimal('120.00'),
            'width': Decimal('60.00'),
            'height': Decimal('75.00'),
            'weight': Decimal('25.000'),
            'prices': {price_lists[0].id: Decimal('180.000')} if price_lists else {}
        },
        {
            'name': 'كرسي مكتب دوار',
            'name_en': 'Office Swivel Chair',
            'category': categories[2] if len(categories) > 2 else categories[0] if categories else None,
            'brand': None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'كرسي مكتب دوار مع مسند ظهر قابل للتعديل',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('12.000'),
            'prices': {price_lists[0].id: Decimal('95.000'), price_lists[1].id: Decimal('90.000')} if price_lists else {}
        },
        {
            'name': 'كابل HDMI',
            'name_en': 'HDMI Cable',
            'category': categories[0] if categories else None,
            'brand': brands[0] if brands else None,
            'base_uom': uom_meter if uom_meter else uom_piece,
            'has_variants': False,
            'description': 'كابل HDMI عالي الجودة 4K، طول 2 متر',
            'tax_rate': Decimal('16.00'),
            'length': Decimal('200.00'),
            'weight': Decimal('0.150'),
            'prices': {price_lists[0].id: Decimal('12.500')} if price_lists else {}
        },
        {
            'name': 'سماعة بلوتوث محمولة',
            'name_en': 'Portable Bluetooth Speaker',
            'category': categories[0] if categories else None,
            'brand': brands[1] if len(brands) > 1 else brands[0] if brands else None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'سماعة بلوتوث محمولة مقاومة للماء، بطارية 10 ساعات',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('0.500'),
            'prices': {price_lists[0].id: Decimal('45.000'), price_lists[1].id: Decimal('42.000')} if price_lists else {}
        },
        {
            'name': 'حقيبة لابتوب جلد',
            'name_en': 'Leather Laptop Bag',
            'category': categories[1] if len(categories) > 1 else categories[0] if categories else None,
            'brand': None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'حقيبة لابتوب جلد طبيعي، تناسب شاشات حتى 15.6 بوصة',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('0.800'),
            'prices': {price_lists[0].id: Decimal('65.000')} if price_lists else {}
        },
        {
            'name': 'ورق طباعة A4',
            'name_en': 'A4 Printing Paper',
            'category': categories[0] if categories else None,
            'brand': None,
            'base_uom': uom_kg if uom_kg else uom_piece,
            'has_variants': False,
            'description': 'ورق طباعة A4 أبيض، 80 جرام، 500 ورقة',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('2.500'),
            'prices': {price_lists[0].id: Decimal('4.500'), price_lists[1].id: Decimal('4.200')} if price_lists else {}
        },
        {
            'name': 'حبر طابعة HP',
            'name_en': 'HP Printer Ink',
            'category': categories[0] if categories else None,
            'brand': brands[0] if brands else None,
            'base_uom': uom_piece,
            'has_variants': False,
            'description': 'حبر طابعة HP أصلي، أسود، سعة عالية',
            'tax_rate': Decimal('16.00'),
            'weight': Decimal('0.200'),
            'prices': {price_lists[0].id: Decimal('28.000')} if price_lists else {}
        },
    ]

    created_items = []

    for idx, item_data in enumerate(items_data, 1):
        try:
            # استخراج بيانات الأسعار
            prices = item_data.pop('prices', {})
            create_variants = item_data.pop('create_variants', False)

            # إنشاء المادة
            item = Item.objects.create(
                company=company,
                currency=currency,
                **item_data
            )

            # إضافة الأسعار للمواد بدون متغيرات
            if not item.has_variants and prices:
                for price_list_id, price in prices.items():
                    PriceListItem.objects.create(
                        price_list_id=price_list_id,
                        item=item,
                        variant=None,
                        uom=item.base_uom,
                        price=price,
                        min_quantity=Decimal('1.000')
                    )

            # إنشاء متغيرات للقميص
            if create_variants and color_attr:
                colors = list(VariantValue.objects.filter(attribute=color_attr, is_active=True)[:3])

                # إذا كان هناك مقاسات، استخدمها
                if size_attr:
                    sizes = list(VariantValue.objects.filter(attribute=size_attr, is_active=True)[:3])
                else:
                    # إنشاء متغيرات بدون مقاسات
                    sizes = [None]

                variant_num = 1
                for color in colors:
                    for size in sizes:
                        if size:
                            notes = f"{color.value} - {size.value}"
                        else:
                            notes = f"{color.value}"

                        variant = ItemVariant.objects.create(
                            item=item,
                            company=company,
                            code=f"{item.code}-V{variant_num:03d}",
                            notes=notes,
                            cost_price=Decimal('15.000'),
                            base_price=Decimal('25.000')
                        )

                        # ربط اللون
                        ItemVariantAttributeValue.objects.create(
                            variant=variant,
                            attribute=color_attr,
                            value=color,
                            company=company
                        )

                        # ربط المقاس إذا كان موجوداً
                        if size and size_attr:
                            ItemVariantAttributeValue.objects.create(
                                variant=variant,
                                attribute=size_attr,
                                value=size,
                                company=company
                            )

                        # إضافة أسعار للمتغير
                        if price_lists:
                            PriceListItem.objects.create(
                                price_list=price_lists[0],
                                item=item,
                                variant=variant,
                                uom=item.base_uom,
                                price=Decimal('25.000'),
                                min_quantity=Decimal('1.000')
                            )

                        variant_num += 1

                print(f"  ✅ تم إنشاء {variant_num - 1} متغير للمادة")

            created_items.append(item)
            print(f"{idx}. ✅ {item.code} - {item.name}")

        except Exception as e:
            print(f"{idx}. ❌ خطأ في إنشاء {item_data.get('name', 'مادة')}: {e}")

    print(f"\n✅ تم إنشاء {len(created_items)} مادة بنجاح")
    return created_items


if __name__ == '__main__':
    clear_all_data()
    items = create_sample_items()

    print("\n" + "=" * 60)
    print("📊 إحصائيات النظام:")
    print("=" * 60)
    print(f"✅ إجمالي المواد: {Item.objects.count()}")
    print(f"✅ مواد بمتغيرات: {Item.objects.filter(has_variants=True).count()}")
    print(f"✅ مواد بدون متغيرات: {Item.objects.filter(has_variants=False).count()}")
    print(f"✅ إجمالي المتغيرات: {ItemVariant.objects.count()}")
    print(f"✅ إجمالي الأسعار: {PriceListItem.objects.count()}")
    print("=" * 60)

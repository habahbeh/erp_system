#!/usr/bin/env python
"""
Script to delete old variants and create new variant attributes with values
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import (
    Item, ItemVariant, ItemVariantAttributeValue, Company,
    VariantAttribute, VariantValue, PriceList, PriceListItem
)
from decimal import Decimal

def clear_variants():
    """حذف جميع المتغيرات القديمة"""
    print("=" * 60)
    print("🗑️  حذف المتغيرات القديمة...")
    print("=" * 60)

    # حذف أسعار المتغيرات
    count1 = PriceListItem.objects.filter(variant__isnull=False).delete()[0]
    print(f"✅ حذف {count1} سعر متغير")

    # حذف قيم خصائص المتغيرات
    count2 = ItemVariantAttributeValue.objects.all().delete()[0]
    print(f"✅ حذف {count2} قيمة خاصية متغير")

    # حذف المتغيرات
    count3 = ItemVariant.objects.all().delete()[0]
    print(f"✅ حذف {count3} متغير")

    # حذف قيم الخصائص القديمة
    count4 = VariantValue.objects.all().delete()[0]
    print(f"✅ حذف {count4} قيمة خاصية")

    # حذف الخصائص القديمة
    count5 = VariantAttribute.objects.all().delete()[0]
    print(f"✅ حذف {count5} خاصية")

    print("\n✅ تم حذف جميع المتغيرات القديمة بنجاح\n")


def create_variant_attributes():
    """إنشاء خصائص المتغيرات وقيمها"""
    print("=" * 60)
    print("📝 إنشاء خصائص المتغيرات...")
    print("=" * 60)

    company = Company.objects.first()

    # 1. خاصية اللون
    color_attr = VariantAttribute.objects.create(
        company=company,
        name='اللون',
        name_en='Color',
        display_name='اللون',
        sort_order=1,
        is_required=True
    )

    colors = [
        ('أبيض', 'White'),
        ('أسود', 'Black'),
        ('أحمر', 'Red'),
        ('أزرق', 'Blue'),
        ('أخضر', 'Green'),
        ('فضي', 'Silver'),
        ('ذهبي', 'Gold'),
    ]

    for idx, (name_ar, name_en) in enumerate(colors, 1):
        VariantValue.objects.create(
            attribute=color_attr,
            company=company,
            value=name_ar,
            value_en=name_en,
            display_value=name_ar,
            sort_order=idx
        )

    print(f"✅ خاصية اللون: {len(colors)} قيمة")

    # 2. خاصية المقاس
    size_attr = VariantAttribute.objects.create(
        company=company,
        name='المقاس',
        name_en='Size',
        display_name='المقاس',
        sort_order=2,
        is_required=True
    )

    sizes = [
        ('صغير جداً', 'XS'),
        ('صغير', 'Small'),
        ('وسط', 'Medium'),
        ('كبير', 'Large'),
        ('كبير جداً', 'XL'),
        ('كبير جداً جداً', 'XXL'),
    ]

    for idx, (name_ar, name_en) in enumerate(sizes, 1):
        VariantValue.objects.create(
            attribute=size_attr,
            company=company,
            value=name_ar,
            value_en=name_en,
            display_value=name_ar,
            sort_order=idx
        )

    print(f"✅ خاصية المقاس: {len(sizes)} قيمة")

    # 3. خاصية السعة (للإلكترونيات)
    storage_attr = VariantAttribute.objects.create(
        company=company,
        name='السعة التخزينية',
        name_en='Storage',
        display_name='السعة',
        sort_order=3,
        is_required=False
    )

    storages = [
        ('128 جيجا', '128GB'),
        ('256 جيجا', '256GB'),
        ('512 جيجا', '512GB'),
        ('1 تيرا', '1TB'),
    ]

    for idx, (name_ar, name_en) in enumerate(storages, 1):
        VariantValue.objects.create(
            attribute=storage_attr,
            company=company,
            value=name_ar,
            value_en=name_en,
            display_value=name_ar,
            sort_order=idx
        )

    print(f"✅ خاصية السعة التخزينية: {len(storages)} قيمة")

    # 4. خاصية المادة (للأثاث)
    material_attr = VariantAttribute.objects.create(
        company=company,
        name='المادة',
        name_en='Material',
        display_name='المادة',
        sort_order=4,
        is_required=False
    )

    materials = [
        ('خشب', 'Wood'),
        ('معدن', 'Metal'),
        ('بلاستيك', 'Plastic'),
        ('جلد', 'Leather'),
        ('قماش', 'Fabric'),
    ]

    for idx, (name_ar, name_en) in enumerate(materials, 1):
        VariantValue.objects.create(
            attribute=material_attr,
            company=company,
            value=name_ar,
            value_en=name_en,
            display_value=name_ar,
            sort_order=idx
        )

    print(f"✅ خاصية المادة: {len(materials)} قيمة")

    print(f"\n✅ تم إنشاء {VariantAttribute.objects.count()} خاصية")
    print(f"✅ تم إنشاء {VariantValue.objects.count()} قيمة\n")

    return {
        'color': color_attr,
        'size': size_attr,
        'storage': storage_attr,
        'material': material_attr,
    }


def create_item_variants(attributes):
    """إنشاء متغيرات للمواد وربطها"""
    print("=" * 60)
    print("🔗 إنشاء متغيرات المواد...")
    print("=" * 60)

    company = Company.objects.first()
    price_list = PriceList.objects.filter(company=company, is_active=True).first()

    # الحصول على القيم
    color_white = VariantValue.objects.get(attribute=attributes['color'], value='أبيض')
    color_black = VariantValue.objects.get(attribute=attributes['color'], value='أسود')
    color_red = VariantValue.objects.get(attribute=attributes['color'], value='أحمر')
    color_blue = VariantValue.objects.get(attribute=attributes['color'], value='أزرق')
    color_silver = VariantValue.objects.get(attribute=attributes['color'], value='فضي')

    size_s = VariantValue.objects.get(attribute=attributes['size'], value='صغير')
    size_m = VariantValue.objects.get(attribute=attributes['size'], value='وسط')
    size_l = VariantValue.objects.get(attribute=attributes['size'], value='كبير')
    size_xl = VariantValue.objects.get(attribute=attributes['size'], value='كبير جداً')

    storage_256 = VariantValue.objects.get(attribute=attributes['storage'], value='256 جيجا')
    storage_512 = VariantValue.objects.get(attribute=attributes['storage'], value='512 جيجا')
    storage_1tb = VariantValue.objects.get(attribute=attributes['storage'], value='1 تيرا')

    material_wood = VariantValue.objects.get(attribute=attributes['material'], value='خشب')
    material_metal = VariantValue.objects.get(attribute=attributes['material'], value='معدن')
    material_fabric = VariantValue.objects.get(attribute=attributes['material'], value='قماش')

    total_variants = 0

    # 1. لابتوب - سعة تخزينية
    laptop = Item.objects.get(code='ITM000001')
    laptop.has_variants = True
    laptop.save()

    laptop_variants = [
        ([storage_256], '256 جيجا', Decimal('850.000')),
        ([storage_512], '512 جيجا', Decimal('950.000')),
        ([storage_1tb], '1 تيرا', Decimal('1100.000')),
    ]

    for attrs_list, desc, price in laptop_variants:
        variant = create_variant(laptop, attrs_list, company, desc, price, price_list)
        total_variants += 1

    print(f"1. ✅ لابتوب: {len(laptop_variants)} متغير (سعة تخزينية)")

    # 2. ماوس - ألوان
    mouse = Item.objects.get(code='ITM000002')
    mouse.has_variants = True
    mouse.save()

    mouse_variants = [
        ([color_white], 'أبيض', Decimal('25.000')),
        ([color_black], 'أسود', Decimal('25.000')),
        ([color_red], 'أحمر', Decimal('27.000')),
    ]

    for attrs_list, desc, price in mouse_variants:
        variant = create_variant(mouse, attrs_list, company, desc, price, price_list)
        total_variants += 1

    print(f"2. ✅ ماوس: {len(mouse_variants)} متغير (ألوان)")

    # 3. قميص - ألوان ومقاسات
    shirt = Item.objects.get(code='ITM000003')
    shirt.has_variants = True
    shirt.save()

    shirt_colors = [color_white, color_black, color_blue]
    shirt_sizes = [size_m, size_l, size_xl]

    shirt_count = 0
    for color in shirt_colors:
        for size in shirt_sizes:
            desc = f"{color.value} - {size.value}"
            variant = create_variant(shirt, [color, size], company, desc, Decimal('25.000'), price_list)
            shirt_count += 1
            total_variants += 1

    print(f"3. ✅ قميص: {shirt_count} متغير ({len(shirt_colors)} ألوان × {len(shirt_sizes)} مقاسات)")

    # 4. طاولة - ألوان ومواد
    table = Item.objects.get(code='ITM000004')
    table.has_variants = True
    table.save()

    table_variants = [
        ([material_wood, color_white], 'خشب أبيض', Decimal('180.000')),
        ([material_wood, color_black], 'خشب أسود', Decimal('185.000')),
        ([material_metal, color_silver], 'معدن فضي', Decimal('200.000')),
    ]

    for attrs_list, desc, price in table_variants:
        variant = create_variant(table, attrs_list, company, desc, price, price_list)
        total_variants += 1

    print(f"4. ✅ طاولة: {len(table_variants)} متغير (مادة + لون)")

    # 5. كرسي - ألوان ومواد
    chair = Item.objects.get(code='ITM000005')
    chair.has_variants = True
    chair.save()

    chair_variants = [
        ([material_fabric, color_black], 'قماش أسود', Decimal('95.000')),
        ([material_fabric, color_blue], 'قماش أزرق', Decimal('95.000')),
        ([material_fabric, color_red], 'قماش أحمر', Decimal('98.000')),
    ]

    for attrs_list, desc, price in chair_variants:
        variant = create_variant(chair, attrs_list, company, desc, price, price_list)
        total_variants += 1

    print(f"5. ✅ كرسي: {len(chair_variants)} متغير (مادة + لون)")

    # 6. حقيبة لابتوب - ألوان
    bag = Item.objects.get(code='ITM000008')
    bag.has_variants = True
    bag.save()

    bag_variants = [
        ([color_black], 'أسود', Decimal('65.000')),
        ([color_white], 'أبيض', Decimal('65.000')),
        ([color_blue], 'أزرق', Decimal('67.000')),
    ]

    for attrs_list, desc, price in bag_variants:
        variant = create_variant(bag, attrs_list, company, desc, price, price_list)
        total_variants += 1

    print(f"6. ✅ حقيبة: {len(bag_variants)} متغير (ألوان)")

    print(f"\n✅ إجمالي المتغيرات المنشأة: {total_variants}\n")


def create_variant(item, attributes_list, company, description, price, price_list):
    """إنشاء متغير واحد مع خصائصه"""
    # توليد الكود
    variant_count = item.variants.count() + 1
    code = f"{item.code}-V{variant_count:03d}"

    # إنشاء المتغير
    variant = ItemVariant.objects.create(
        item=item,
        company=company,
        code=code,
        notes=description,
        cost_price=price * Decimal('0.7'),  # التكلفة 70% من السعر
        base_price=price
    )

    # ربط الخصائص
    for attr_value in attributes_list:
        ItemVariantAttributeValue.objects.create(
            variant=variant,
            attribute=attr_value.attribute,
            value=attr_value,
            company=company
        )

    # إضافة السعر
    if price_list:
        PriceListItem.objects.create(
            price_list=price_list,
            item=item,
            variant=variant,
            uom=item.base_uom,
            price=price,
            min_quantity=Decimal('1.000')
        )

    return variant


if __name__ == '__main__':
    clear_variants()
    attributes = create_variant_attributes()
    create_item_variants(attributes)

    print("=" * 60)
    print("📊 إحصائيات النهائية:")
    print("=" * 60)
    print(f"✅ إجمالي المواد: {Item.objects.count()}")
    print(f"✅ مواد بمتغيرات: {Item.objects.filter(has_variants=True).count()}")
    print(f"✅ مواد بدون متغيرات: {Item.objects.filter(has_variants=False).count()}")
    print(f"✅ خصائص المتغيرات: {VariantAttribute.objects.count()}")
    print(f"✅ قيم الخصائص: {VariantValue.objects.count()}")
    print(f"✅ إجمالي المتغيرات: {ItemVariant.objects.count()}")
    print(f"✅ إجمالي الأسعار: {PriceListItem.objects.count()}")
    print("=" * 60)

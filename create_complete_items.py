"""
سكريبت إنشاء مواد كاملة مع المتغيرات والأسعار وتحويلات وحدات القياس
Script to create complete items with variants, prices, and UOM conversions
"""

import os
import django
from decimal import Decimal

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.core.models import (
    Company, Currency, Item, ItemCategory, Brand,
    ItemVariant, VariantAttribute, VariantValue, ItemVariantAttributeValue,
    UoMGroup, UnitOfMeasure, UoMConversion,
    PriceList, PriceListItem
)


def clear_all_items():
    """حذف جميع المواد الموجودة"""
    print("=" * 60)
    print("🗑️  حذف جميع المواد الموجودة...")
    print("=" * 60)

    # حذف المتغيرات أولاً
    variant_count = ItemVariant.objects.all().count()
    ItemVariant.objects.all().delete()
    print(f"✅ تم حذف {variant_count} متغير")

    # حذف المواد
    item_count = Item.objects.all().count()
    Item.objects.all().delete()
    print(f"✅ تم حذف {item_count} مادة")

    print()


def get_or_create_category(company, name, code):
    """إنشاء أو الحصول على تصنيف"""
    category, created = ItemCategory.objects.get_or_create(
        company=company,
        code=code,
        defaults={
            'name': name,
            'name_en': name,
            'is_active': True,
            'created_by': None
        }
    )
    return category


def get_or_create_brand(company, name):
    """إنشاء أو الحصول على علامة تجارية"""
    brand, created = Brand.objects.get_or_create(
        company=company,
        name=name,
        defaults={
            'name_en': name,
            'is_active': True,
            'created_by': None
        }
    )
    return brand


def setup_uom_groups_and_units(company):
    """إنشاء مجموعات ووحدات القياس"""
    print("=" * 60)
    print("📏 إعداد وحدات القياس...")
    print("=" * 60)

    # مجموعة الوحدات (Units)
    unit_group, _ = UoMGroup.objects.get_or_create(
        company=company,
        code='UNITS',
        defaults={
            'name': 'الوحدات',
            'allow_decimal': False,
            'is_active': True,
            'created_by': None
        }
    )

    # مجموعة الوزن (Weight)
    weight_group, _ = UoMGroup.objects.get_or_create(
        company=company,
        code='WEIGHT',
        defaults={
            'name': 'الوزن',
            'allow_decimal': True,
            'is_active': True,
            'created_by': None
        }
    )

    # مجموعة الحجم (Volume)
    volume_group, _ = UoMGroup.objects.get_or_create(
        company=company,
        code='VOLUME',
        defaults={
            'name': 'الحجم',
            'allow_decimal': True,
            'is_active': True,
            'created_by': None
        }
    )

    # إنشاء وحدات الوحدات (Units Group)
    piece, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='PC',
        defaults={
            'name': 'قطعة',
            'name_en': 'Piece',
            'uom_group': unit_group,
            'uom_type': 'UNIT',
            'is_base_unit': True,
            'symbol': 'قطعة',
            'rounding_precision': Decimal('1'),
            'is_active': True,
            'created_by': None
        }
    )
    unit_group.base_uom = piece
    unit_group.save()

    box, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='BOX',
        defaults={
            'name': 'صندوق',
            'name_en': 'Box',
            'uom_group': unit_group,
            'uom_type': 'UNIT',
            'is_base_unit': False,
            'symbol': 'صندوق',
            'rounding_precision': Decimal('1'),
            'is_active': True,
            'created_by': None
        }
    )

    carton, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='CTN',
        defaults={
            'name': 'كرتون',
            'name_en': 'Carton',
            'uom_group': unit_group,
            'uom_type': 'UNIT',
            'is_base_unit': False,
            'symbol': 'كرتون',
            'rounding_precision': Decimal('1'),
            'is_active': True,
            'created_by': None
        }
    )

    dozen, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='DZ',
        defaults={
            'name': 'دزينة',
            'name_en': 'Dozen',
            'uom_group': unit_group,
            'uom_type': 'UNIT',
            'is_base_unit': False,
            'symbol': 'دزينة',
            'rounding_precision': Decimal('1'),
            'is_active': True,
            'created_by': None
        }
    )

    # إنشاء وحدات الوزن (Weight Group)
    kg, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='KG',
        defaults={
            'name': 'كيلوجرام',
            'name_en': 'Kilogram',
            'uom_group': weight_group,
            'uom_type': 'WEIGHT',
            'is_base_unit': True,
            'symbol': 'كجم',
            'rounding_precision': Decimal('0.001'),
            'is_active': True,
            'created_by': None
        }
    )
    weight_group.base_uom = kg
    weight_group.save()

    gram, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='G',
        defaults={
            'name': 'جرام',
            'name_en': 'Gram',
            'uom_group': weight_group,
            'uom_type': 'WEIGHT',
            'is_base_unit': False,
            'symbol': 'جم',
            'rounding_precision': Decimal('0.001'),
            'is_active': True,
            'created_by': None
        }
    )

    ton, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='TON',
        defaults={
            'name': 'طن',
            'name_en': 'Ton',
            'uom_group': weight_group,
            'uom_type': 'WEIGHT',
            'is_base_unit': False,
            'symbol': 'طن',
            'rounding_precision': Decimal('0.001'),
            'is_active': True,
            'created_by': None
        }
    )

    # إنشاء وحدات الحجم (Volume Group)
    liter, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='L',
        defaults={
            'name': 'لتر',
            'name_en': 'Liter',
            'uom_group': volume_group,
            'uom_type': 'VOLUME',
            'is_base_unit': True,
            'symbol': 'ل',
            'rounding_precision': Decimal('0.001'),
            'is_active': True,
            'created_by': None
        }
    )
    volume_group.base_uom = liter
    volume_group.save()

    ml, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='ML',
        defaults={
            'name': 'ميليلتر',
            'name_en': 'Milliliter',
            'uom_group': volume_group,
            'uom_type': 'VOLUME',
            'is_base_unit': False,
            'symbol': 'مل',
            'rounding_precision': Decimal('0.001'),
            'is_active': True,
            'created_by': None
        }
    )

    print(f"✅ تم إنشاء 3 مجموعات و 9 وحدات قياس")
    print()

    return {
        'piece': piece, 'box': box, 'carton': carton, 'dozen': dozen,
        'kg': kg, 'gram': gram, 'ton': ton,
        'liter': liter, 'ml': ml
    }


def setup_variant_attributes(company):
    """إنشاء خصائص المتغيرات"""
    print("=" * 60)
    print("🎨 إعداد خصائص المتغيرات...")
    print("=" * 60)

    # الحجم
    size_attr, _ = VariantAttribute.objects.get_or_create(
        company=company,
        name='الحجم',
        defaults={
            'name_en': 'Size',
            'display_name': 'الحجم',
            'is_required': True,
            'sort_order': 1,
            'is_active': True,
            'created_by': None
        }
    )

    # اللون
    color_attr, _ = VariantAttribute.objects.get_or_create(
        company=company,
        name='اللون',
        defaults={
            'name_en': 'Color',
            'display_name': 'اللون',
            'is_required': True,
            'sort_order': 2,
            'is_active': True,
            'created_by': None
        }
    )

    # النوع/الطعم
    flavor_attr, _ = VariantAttribute.objects.get_or_create(
        company=company,
        name='الطعم',
        defaults={
            'name_en': 'Flavor',
            'display_name': 'الطعم',
            'is_required': True,
            'sort_order': 3,
            'is_active': True,
            'created_by': None
        }
    )

    # قيم الحجم
    sizes = ['صغير', 'متوسط', 'كبير', 'XL', 'XXL']
    size_values = []
    for i, size in enumerate(sizes, 1):
        val, _ = VariantValue.objects.get_or_create(
            attribute=size_attr,
            value=size,
            defaults={
                'value_en': size,
                'display_value': size,
                'sort_order': i,
                'company': company,
                'is_active': True,
                'created_by': None
            }
        )
        size_values.append(val)

    # قيم اللون
    colors = ['أحمر', 'أزرق', 'أخضر', 'أصفر', 'أسود', 'أبيض']
    color_values = []
    for i, color in enumerate(colors, 1):
        val, _ = VariantValue.objects.get_or_create(
            attribute=color_attr,
            value=color,
            defaults={
                'value_en': color,
                'display_value': color,
                'sort_order': i,
                'company': company,
                'is_active': True,
                'created_by': None
            }
        )
        color_values.append(val)

    # قيم الطعم
    flavors = ['فانيلا', 'شوكولاتة', 'فراولة', 'ليمون', 'برتقال']
    flavor_values = []
    for i, flavor in enumerate(flavors, 1):
        val, _ = VariantValue.objects.get_or_create(
            attribute=flavor_attr,
            value=flavor,
            defaults={
                'value_en': flavor,
                'display_value': flavor,
                'sort_order': i,
                'company': company,
                'is_active': True,
                'created_by': None
            }
        )
        flavor_values.append(val)

    print(f"✅ تم إنشاء 3 خصائص و {len(sizes) + len(colors) + len(flavors)} قيمة")
    print()

    return {
        'size': (size_attr, size_values),
        'color': (color_attr, color_values),
        'flavor': (flavor_attr, flavor_values)
    }


def create_items_with_everything(company, currency, uoms, attributes):
    """إنشاء 5 مواد كاملة مع المتغيرات والأسعار والتحويلات"""
    print("=" * 60)
    print("📦 إنشاء المواد الكاملة...")
    print("=" * 60)

    # الحصول على قائمة الأسعار
    price_list, _ = PriceList.objects.get_or_create(
        company=company,
        code='DEFAULT',
        defaults={
            'name': 'قائمة أسعار افتراضية',
            'is_default': True,
            'currency': currency,
            'is_active': True,
            'created_by': None
        }
    )

    items_data = [
        {
            'name': 'قميص قطني',
            'code': 'SHIRT001',
            'category_name': 'ملابس',
            'category_code': 'CLOTH',
            'brand': 'أديداس',
            'base_uom': uoms['piece'],
            'has_variants': True,
            'variant_attrs': ['size', 'color'],
            'variant_combos': [
                (['صغير', 'أحمر'], Decimal('25.000')),
                (['متوسط', 'أزرق'], Decimal('30.000')),
                (['كبير', 'أخضر'], Decimal('35.000')),
            ],
            'conversions': [
                (uoms['dozen'], Decimal('12')),  # 1 دزينة = 12 قطعة
                (uoms['box'], Decimal('24')),    # 1 صندوق = 24 قطعة
            ]
        },
        {
            'name': 'حليب طازج',
            'code': 'MILK001',
            'category_name': 'منتجات ألبان',
            'category_code': 'DAIRY',
            'brand': 'المراعي',
            'base_uom': uoms['liter'],
            'has_variants': True,
            'variant_attrs': ['size'],
            'variant_combos': [
                (['صغير'], Decimal('2.500')),    # 500ml
                (['متوسط'], Decimal('4.000')),   # 1L
                (['كبير'], Decimal('7.000')),    # 2L
            ],
            'conversions': [
                (uoms['ml'], Decimal('0.001')),   # 1 مل = 0.001 لتر
            ]
        },
        {
            'name': 'أرز بسمتي',
            'code': 'RICE001',
            'category_name': 'بقالة',
            'category_code': 'GROC',
            'brand': 'العلالي',
            'base_uom': uoms['kg'],
            'has_variants': True,
            'variant_attrs': ['size'],
            'variant_combos': [
                (['صغير'], Decimal('8.000')),    # 1 كجم
                (['متوسط'], Decimal('22.000')),  # 5 كجم
                (['كبير'], Decimal('85.000')),   # 25 كجم
            ],
            'conversions': [
                (uoms['gram'], Decimal('0.001')),  # 1 جم = 0.001 كجم
                (uoms['ton'], Decimal('1000')),    # 1 طن = 1000 كجم
            ]
        },
        {
            'name': 'عصير طبيعي',
            'code': 'JUICE001',
            'category_name': 'مشروبات',
            'category_code': 'BEV',
            'brand': 'الربيع',
            'base_uom': uoms['liter'],
            'has_variants': True,
            'variant_attrs': ['flavor', 'size'],
            'variant_combos': [
                (['برتقال', 'صغير'], Decimal('3.500')),
                (['برتقال', 'كبير'], Decimal('6.500')),
                (['فراولة', 'صغير'], Decimal('4.000')),
                (['ليمون', 'متوسط'], Decimal('5.000')),
            ],
            'conversions': [
                (uoms['ml'], Decimal('0.001')),
            ]
        },
        {
            'name': 'شامبو',
            'code': 'SHMP001',
            'category_name': 'عناية شخصية',
            'category_code': 'CARE',
            'brand': 'بانتين',
            'base_uom': uoms['ml'],
            'has_variants': True,
            'variant_attrs': ['size'],
            'variant_combos': [
                (['صغير'], Decimal('12.000')),    # 200ml
                (['متوسط'], Decimal('25.000')),   # 500ml
                (['كبير'], Decimal('45.000')),    # 1000ml
            ],
            'conversions': [
                (uoms['liter'], Decimal('1000')),  # 1 لتر = 1000 مل
                (uoms['carton'], Decimal('12000')), # 1 كرتون = 12 زجاجة × 1000 مل
            ]
        }
    ]

    created_items = []

    for item_data in items_data:
        # إنشاء التصنيف
        category = get_or_create_category(
            company,
            item_data['category_name'],
            item_data['category_code']
        )

        # إنشاء العلامة التجارية
        brand = get_or_create_brand(company, item_data['brand'])

        # إنشاء المادة
        item = Item.objects.create(
            company=company,
            code=item_data['code'],
            name=item_data['name'],
            name_en=item_data['name'],
            category=category,
            brand=brand,
            base_uom=item_data['base_uom'],
            currency=currency,
            has_variants=item_data['has_variants'],
            is_active=True,
            created_by=None
        )

        print(f"\n📦 {item.name} ({item.code})")

        # إنشاء المتغيرات
        for combo_values, base_price in item_data['variant_combos']:
            variant = ItemVariant.objects.create(
                company=company,
                item=item,
                base_price=base_price,
                cost_price=base_price * Decimal('0.7'),  # 70% من السعر
                is_active=True,
                created_by=None
            )

            # ربط الخصائص بالمتغير
            variant_name_parts = []
            for i, attr_name in enumerate(item_data['variant_attrs']):
                attr, values = attributes[attr_name]
                value_name = combo_values[i]
                value_obj = next(v for v in values if v.value == value_name)

                ItemVariantAttributeValue.objects.create(
                    company=company,
                    variant=variant,
                    attribute=attr,
                    value=value_obj,
                    is_active=True,
                    created_by=None
                )
                variant_name_parts.append(value_name)

            print(f"  └─ متغير: {' - '.join(variant_name_parts)} (السعر: {base_price})")

            # إنشاء سعر للمتغير في قائمة الأسعار
            PriceListItem.objects.create(
                price_list=price_list,
                item=item,
                variant=variant,
                uom=None,  # السعر الأساسي بدون UoM محدد
                price=base_price,
                min_quantity=Decimal('1'),
                is_active=True
            )

            # إنشاء أسعار إضافية لوحدات مختلفة (إن وجدت)
            if item_data['conversions']:
                for uom, factor in item_data['conversions']:
                    # السعر بالوحدة = السعر الأساسي × معامل التحويل
                    uom_price = base_price * factor
                    PriceListItem.objects.create(
                        price_list=price_list,
                        item=item,
                        variant=variant,
                        uom=uom,
                        price=uom_price,
                        min_quantity=Decimal('1'),
                        is_active=True
                    )
                    print(f"      └─ سعر {uom.name}: {uom_price}")

        # إنشاء تحويلات وحدات القياس
        for uom, factor in item_data['conversions']:
            UoMConversion.objects.create(
                company=company,
                item=item,
                variant=None,  # تحويل عام للمادة
                from_uom=uom,
                conversion_factor=factor,
                formula_expression=f"1 {uom.name} = {factor} {item.base_uom.name}",
                is_active=True,
                created_by=None
            )
            print(f"  └─ تحويل: 1 {uom.name} = {factor} {item.base_uom.name}")

        created_items.append(item)

    print()
    print(f"✅ تم إنشاء {len(created_items)} مواد بنجاح")
    return created_items


def main():
    """الوظيفة الرئيسية"""
    try:
        # الحصول على الشركة الأولى
        company = Company.objects.first()
        if not company:
            print("❌ لا توجد شركة في النظام!")
            return

        print(f"🏢 الشركة: {company.name}")
        print()

        # الحصول على العملة
        currency = Currency.objects.filter(is_active=True).first()
        if not currency:
            print("❌ لا توجد عملة في النظام!")
            return

        with transaction.atomic():
            # 1. حذف المواد القديمة
            clear_all_items()

            # 2. إعداد وحدات القياس
            uoms = setup_uom_groups_and_units(company)

            # 3. إعداد خصائص المتغيرات
            attributes = setup_variant_attributes(company)

            # 4. إنشاء المواد مع كل شيء
            items = create_items_with_everything(company, currency, uoms, attributes)

            print()
            print("=" * 60)
            print("✅ تم الانتهاء بنجاح!")
            print("=" * 60)
            print(f"📊 ملخص:")
            print(f"   - عدد المواد: {len(items)}")
            print(f"   - عدد المتغيرات: {ItemVariant.objects.count()}")
            print(f"   - عدد الأسعار: {PriceListItem.objects.count()}")
            print(f"   - عدد التحويلات: {UoMConversion.objects.count()}")
            print()
            print("🌐 يمكنك الآن زيارة: http://127.0.0.1:8000/items")
            print()

    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

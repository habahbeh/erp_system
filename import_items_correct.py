#!/usr/bin/env python
"""
سكريبت استيراد المواد الصحيح
يستورد المواد مع متغيراتها (Variants) والأسعار
"""

import os
import sys
import django
import pandas as pd
import re
from decimal import Decimal
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import (
    Item, ItemVariant, ItemCategory, UnitOfMeasure, Company,
    PriceList, PriceListItem, Currency
)
from django.contrib.auth import get_user_model

User = get_user_model()


def extract_size_value(size_str):
    """استخراج قيمة رقمية من المقاس"""
    if pd.isna(size_str):
        return 1.0

    size_str = str(size_str)

    # محاولة استخراج الأرقام وضربها (مثل 2*6)
    multiply_pattern = r'(\d+\.?\d*)\s*[*×xX]\s*(\d+\.?\d*)'
    match = re.search(multiply_pattern, size_str)
    if match:
        num1 = float(match.group(1))
        num2 = float(match.group(2))
        return num1 * num2

    # محاولة استخراج أول رقم (مثل 200mm)
    number_pattern = r'(\d+\.?\d*)'
    match = re.search(number_pattern, size_str)
    if match:
        return float(match.group(1))

    return 1.0


def calculate_price_by_size(size_str, base_price=0.05):
    """حساب السعر بناءً على الحجم"""
    size_value = extract_size_value(size_str)
    price = size_value * base_price
    if price < 0.10:
        price = 0.10
    return round(price, 2)


def import_item_1_with_variants():
    """استيراد المواد من item_1.xlsx"""
    print('\n📥 استيراد المواد من item_1.xlsx...')
    print('='*60)

    df = pd.read_excel('item_1.xlsx')

    # تجميع المواد حسب الوصف الأساسي
    grouped_items = defaultdict(list)

    for idx, row in df.iterrows():
        description = str(row['DESCRIPTION']).strip() if pd.notna(row['DESCRIPTION']) else 'Unknown'
        # تنظيف الاسم: إزالة المسافات الزائدة
        description = ' '.join(description.split())
        grouped_items[description].append(row)

    items_created = 0
    variants_created = 0
    prices_created = 0
    errors = 0

    for base_name, rows in grouped_items.items():
        try:
            # إنشاء المادة الأساسية
            item_code = f'TOOL-{items_created+1:04d}'

            item = Item.objects.create(
                company=company,
                item_code=item_code,
                code=item_code,
                name=base_name[:200],
                name_en=base_name[:200],
                category=default_category,
                base_uom=default_uom,
                currency=default_currency,
                has_variants=len(rows) > 1,
                is_active=True,
                created_by=admin_user,
            )
            items_created += 1

            # إنشاء المتغيرات
            for row in rows:
                try:
                    size = str(row['SIZE']) if pd.notna(row['SIZE']) else ''
                    cost_price = float(row['سعر التكلفة ']) if pd.notna(row['سعر التكلفة ']) else 0.0
                    selling_price = float(row['سعر البيع ']) if pd.notna(row['سعر البيع ']) else cost_price * 1.5
                    barcode = str(int(row['BARCODE'])) if pd.notna(row['BARCODE']) else ''
                    item_no = str(row['ITEM No.']) if pd.notna(row['ITEM No.']) else ''

                    # إنشاء المتغير
                    variant = ItemVariant.objects.create(
                        company=company,
                        item=item,
                        code=size[:50] if size else item_no[:50],
                        barcode=barcode[:50] if barcode else None,
                        cost_price=Decimal(str(cost_price)),
                        base_price=Decimal(str(selling_price)),
                        is_active=True,
                        created_by=admin_user,
                    )
                    variants_created += 1

                    # إنشاء السعر
                    if default_price_list and selling_price > 0:
                        PriceListItem.objects.create(
                            price_list=default_price_list,
                            item=item,
                            variant=variant,
                            uom=default_uom,
                            price=Decimal(str(selling_price)),
                            is_active=True,
                        )
                        prices_created += 1

                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f'  ✗ خطأ في متغير: {str(e)}')

            if (items_created % 50) == 0:
                print(f'  ✓ تم استيراد {items_created} مادة...')

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f'  ✗ خطأ في المادة {base_name}: {str(e)}')

    print(f'\n✅ اكتمل استيراد item_1.xlsx:')
    print(f'   - المواد: {items_created}')
    print(f'   - المتغيرات: {variants_created}')
    print(f'   - الأسعار: {prices_created}')
    print(f'   - الأخطاء: {errors}')

    return items_created, variants_created, prices_created


def import_item_2_with_variants():
    """استيراد المواد من item_2.xlsx"""
    print('\n📥 استيراد المواد من item_2.xlsx...')
    print('='*60)

    df = pd.read_excel('item_2.xlsx', header=1)

    # تجميع المواد حسب الاسم
    grouped_items = defaultdict(list)

    for idx, row in df.iterrows():
        item_name = str(row['اسم المادة']).strip() if pd.notna(row['اسم المادة']) else 'Unknown'
        # تنظيف الاسم: إزالة المسافات الزائدة
        item_name = ' '.join(item_name.split())
        grouped_items[item_name].append(row)

    items_created = 0
    variants_created = 0
    prices_created = 0
    errors = 0

    for base_name, rows in grouped_items.items():
        try:
            # إنشاء المادة الأساسية
            item_code = f'BR-{items_created+1:04d}'

            item = Item.objects.create(
                company=company,
                item_code=item_code,
                code=item_code,
                name=base_name[:200],
                name_en=base_name[:200],
                category=default_category,
                base_uom=default_uom,
                currency=default_currency,
                has_variants=True,
                is_active=True,
                created_by=admin_user,
            )
            items_created += 1

            # إنشاء المتغيرات
            for row in rows:
                try:
                    size = str(row['المقاس']) if pd.notna(row['المقاس']) else ''
                    cost_price = float(row['تكلفة']) if pd.notna(row['تكلفة']) else None
                    selling_price = float(row['سعر البيع']) if pd.notna(row['سعر البيع']) else None

                    # حساب السعر التقريبي إذا لم يكن موجود
                    if cost_price is None or cost_price == 0:
                        cost_price = calculate_price_by_size(size, base_price=0.05)

                    if selling_price is None or selling_price == 0:
                        selling_price = cost_price * 1.5

                    # إنشاء المتغير
                    variant = ItemVariant.objects.create(
                        company=company,
                        item=item,
                        code=size[:50],
                        cost_price=Decimal(str(cost_price)),
                        base_price=Decimal(str(selling_price)),
                        is_active=True,
                        created_by=admin_user,
                    )
                    variants_created += 1

                    # إنشاء السعر
                    if default_price_list:
                        PriceListItem.objects.create(
                            price_list=default_price_list,
                            item=item,
                            variant=variant,
                            uom=default_uom,
                            price=Decimal(str(selling_price)),
                            is_active=True,
                        )
                        prices_created += 1

                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f'  ✗ خطأ في متغير: {str(e)}')

            if (items_created % 20) == 0:
                print(f'  ✓ تم استيراد {items_created} مادة...')

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f'  ✗ خطأ في المادة {base_name}: {str(e)}')

    print(f'\n✅ اكتمل استيراد item_2.xlsx:')
    print(f'   - المواد: {items_created}')
    print(f'   - المتغيرات: {variants_created}')
    print(f'   - الأسعار: {prices_created}')
    print(f'   - الأخطاء: {errors}')

    return items_created, variants_created, prices_created


def main():
    global company, admin_user, default_uom, default_category, default_price_list, default_currency

    print('🚀 بدء عملية استيراد المواد (مع المتغيرات)')
    print('='*60)

    # الحصول على الشركة
    company = Company.objects.first()
    if not company:
        print('❌ خطأ: لا توجد شركة في النظام!')
        return

    print(f'📌 الشركة: {company.name}')

    # الحصول على المستخدم
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()

    print(f'👤 المستخدم: {admin_user.username}')

    # وحدة القياس
    default_uom, _ = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='PCE',
        defaults={
            'name': 'قطعة',
            'name_en': 'Piece',
            'created_by': admin_user,
        }
    )

    print(f'📏 وحدة القياس: {default_uom.name}')

    # التصنيف
    default_category, _ = ItemCategory.objects.get_or_create(
        company=company,
        code='GEN',
        defaults={
            'name': 'عام',
            'name_en': 'General',
            'level': 1,
            'created_by': admin_user,
        }
    )

    print(f'📂 التصنيف: {default_category.name}')

    # العملة
    default_currency = Currency.objects.filter(is_base=True).first()
    if not default_currency:
        default_currency = Currency.objects.first()

    print(f'💵 العملة: {default_currency.code}')

    # قائمة الأسعار
    default_price_list = PriceList.objects.filter(
        company=company,
        is_default=True
    ).first()

    if not default_price_list:
        print('⚠️  تحذير: لا توجد قائمة أسعار افتراضية - لن يتم إضافة أسعار')
    else:
        print(f'💰 قائمة الأسعار: {default_price_list.name}')

    print()

    # الاستيراد
    try:
        # الملف الأول
        items1, variants1, prices1 = import_item_1_with_variants()

        # الملف الثاني
        items2, variants2, prices2 = import_item_2_with_variants()

        # النتائج
        print('\n' + '='*60)
        print('🎉 اكتملت عملية الاستيراد بنجاح!')
        print('='*60)
        print(f'📊 الإحصائيات النهائية:')
        print(f'   المواد الأساسية: {items1 + items2}')
        print(f'   المتغيرات (المقاسات): {variants1 + variants2}')
        print(f'   الأسعار: {prices1 + prices2}')
        print('='*60)

    except Exception as e:
        print(f'\n❌ خطأ: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

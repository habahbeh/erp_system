#!/usr/bin/env python
"""
سكريبت استيراد المواد من ملفات Excel
يستورد المواد من item_1.xlsx و item_2.xlsx
ويحسب الأسعار التقريبية بناءً على الحجم/المقاس
"""

import os
import sys
import django
import pandas as pd
import re
from decimal import Decimal

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import (
    Item, ItemCategory, UnitOfMeasure, Company,
    PriceList, PriceListItem, Currency
)
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


def extract_size_value(size_str):
    """
    استخراج قيمة رقمية من المقاس لحساب السعر
    مثال: "2*6" -> 12, "200mm/8\"" -> 200
    """
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
    """
    حساب السعر التقريبي بناءً على الحجم/المقاس
    """
    size_value = extract_size_value(size_str)

    # معادلة بسيطة: السعر = حجم المقاس * سعر أساسي
    price = size_value * base_price

    # حد أدنى للسعر
    if price < 0.10:
        price = 0.10

    return round(price, 2)


def import_item_1():
    """استيراد المواد من item_1.xlsx"""
    print('\n📥 استيراد المواد من item_1.xlsx...')
    print('='*60)

    df = pd.read_excel('item_1.xlsx')

    imported = 0
    errors = 0

    for idx, row in df.iterrows():
        try:
            # تحضير البيانات
            item_no = str(row['ITEM No.']) if pd.notna(row['ITEM No.']) else f'ITEM-{idx+1:04d}'
            description = str(row['DESCRIPTION']) if pd.notna(row['DESCRIPTION']) else 'بدون وصف'
            size = str(row['SIZE']) if pd.notna(row['SIZE']) else ''
            features = str(row['DESCRIPTION & FEATURES']) if pd.notna(row['DESCRIPTION & FEATURES']) else ''
            cost_price = float(row['سعر التكلفة ']) if pd.notna(row['سعر التكلفة ']) else 0.0
            selling_price = float(row['سعر البيع ']) if pd.notna(row['سعر البيع ']) else cost_price * 1.5
            wholesale_price = float(row['سعر الجملة ']) if pd.notna(row['سعر الجملة ']) else cost_price * 1.2
            barcode = str(int(row['BARCODE'])) if pd.notna(row['BARCODE']) else ''

            # إنشاء اسم كامل للمادة
            full_name = f"{description}"
            if size:
                full_name += f" - {size}"

            # إنشاء المادة
            item_data = {
                'company': company,
                'item_code': item_no,
                'code': item_no,
                'name': full_name[:200],
                'name_en': full_name[:200],
                'description': features[:500] if features else '',
                'category': default_category,
                'base_uom': default_uom,
                'currency': default_currency,
                'barcode': barcode[:50] if barcode else None,
                'is_active': True,
                'created_by': admin_user,
            }

            item = Item.objects.create(**item_data)

            # إنشاء الأسعار في قائمة الأسعار
            if default_price_list:
                PriceListItem.objects.create(
                    company=company,
                    price_list=default_price_list,
                    item=item,
                    price=Decimal(str(selling_price)),
                    cost_price=Decimal(str(cost_price)),
                    created_by=admin_user,
                )

            imported += 1

            if (imported % 100) == 0:
                print(f'  ✓ تم استيراد {imported} مادة...')

        except Exception as e:
            errors += 1
            print(f'  ✗ خطأ في الصف {idx+1}: {str(e)}')

    print(f'\n✅ اكتمل استيراد item_1.xlsx:')
    print(f'   - تم الاستيراد: {imported} مادة')
    print(f'   - أخطاء: {errors}')

    return imported, errors


def import_item_2():
    """استيراد المواد من item_2.xlsx"""
    print('\n📥 استيراد المواد من item_2.xlsx...')
    print('='*60)

    df = pd.read_excel('item_2.xlsx', header=1)

    imported = 0
    errors = 0

    for idx, row in df.iterrows():
        try:
            # تحضير البيانات
            item_name = str(row['اسم المادة']) if pd.notna(row['اسم المادة']) else 'بدون اسم'
            size = str(row['المقاس']) if pd.notna(row['المقاس']) else ''
            cost_price = float(row['تكلفة']) if pd.notna(row['تكلفة']) else None
            selling_price = float(row['سعر البيع']) if pd.notna(row['سعر البيع']) else None

            # إذا لم يكن هناك سعر، احسب سعر تقريبي بناءً على الحجم
            if cost_price is None or cost_price == 0:
                cost_price = calculate_price_by_size(size, base_price=0.05)

            if selling_price is None or selling_price == 0:
                selling_price = cost_price * 1.5  # هامش ربح 50%

            # إنشاء كود فريد للمادة
            item_code = f'BR-{idx+1:05d}'

            # إنشاء اسم كامل للمادة
            full_name = f"{item_name}"
            if size:
                full_name += f" {size}"

            # إنشاء المادة
            item_data = {
                'company': company,
                'item_code': item_code,
                'code': item_code,
                'name': full_name[:200],
                'name_en': full_name[:200],
                'description': f'المقاس: {size}' if size else '',
                'category': default_category,
                'base_uom': default_uom,
                'currency': default_currency,
                'is_active': True,
                'created_by': admin_user,
            }

            item = Item.objects.create(**item_data)

            # إنشاء الأسعار في قائمة الأسعار
            if default_price_list:
                PriceListItem.objects.create(
                    company=company,
                    price_list=default_price_list,
                    item=item,
                    price=Decimal(str(selling_price)),
                    cost_price=Decimal(str(cost_price)),
                    created_by=admin_user,
                )

            imported += 1

            if (imported % 500) == 0:
                print(f'  ✓ تم استيراد {imported} مادة...')

        except Exception as e:
            errors += 1
            if errors < 10:  # طباعة أول 10 أخطاء فقط
                print(f'  ✗ خطأ في الصف {idx+1}: {str(e)}')

    print(f'\n✅ اكتمل استيراد item_2.xlsx:')
    print(f'   - تم الاستيراد: {imported} مادة')
    print(f'   - أخطاء: {errors}')

    return imported, errors


def main():
    global company, admin_user, default_uom, default_category, default_price_list, default_currency

    print('🚀 بدء عملية استيراد المواد')
    print('='*60)

    # الحصول على الشركة الأولى
    company = Company.objects.first()
    if not company:
        print('❌ خطأ: لا توجد شركة في النظام!')
        return

    print(f'📌 الشركة: {company.name}')

    # الحصول على المستخدم الإداري
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()

    print(f'👤 المستخدم: {admin_user.username}')

    # الحصول على أو إنشاء وحدة القياس الافتراضية
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

    # الحصول على أو إنشاء التصنيف الافتراضي
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

    # الحصول على العملة الأساسية
    default_currency = Currency.objects.filter(is_base=True).first()
    if not default_currency:
        default_currency = Currency.objects.first()

    print(f'💵 العملة: {default_currency.code}')

    # الحصول على قائمة الأسعار الافتراضية
    default_price_list = PriceList.objects.filter(
        company=company,
        is_default=True
    ).first()

    if not default_price_list:
        # إنشاء قائمة أسعار افتراضية
        default_price_list = PriceList.objects.create(
            company=company,
            name='قائمة الأسعار الافتراضية',
            name_en='Default Price List',
            currency='JOD',
            is_default=True,
            is_active=True,
            created_by=admin_user,
        )

    print(f'💰 قائمة الأسعار: {default_price_list.name}')
    print()

    # بدء الاستيراد
    try:
        # استيراد الملف الأول
        total1, errors1 = import_item_1()

        # استيراد الملف الثاني
        total2, errors2 = import_item_2()

        # النتائج النهائية
        print('\n' + '='*60)
        print('🎉 اكتملت عملية الاستيراد بنجاح!')
        print('='*60)
        print(f'📊 إحصائيات الاستيراد:')
        print(f'   - item_1.xlsx: {total1} مادة')
        print(f'   - item_2.xlsx: {total2} مادة')
        print(f'   - الإجمالي: {total1 + total2} مادة')
        print(f'   - الأخطاء: {errors1 + errors2}')
        print('='*60)

    except Exception as e:
        print(f'\n❌ خطأ كبير في عملية الاستيراد: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

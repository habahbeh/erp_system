#!/usr/bin/env python
"""
سكريبت لحذف قوائم الأسعار الحالية وإضافة قوائم جديدة
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import PriceList, Company, Currency, User
from django.db import transaction

def update_price_lists():
    """حذف قوائم الأسعار الحالية وإضافة القوائم الجديدة"""

    # الحصول على الشركة والعملة الافتراضية
    company = Company.objects.first()
    if not company:
        print("❌ لا توجد شركة في النظام!")
        return

    # الحصول على العملة الأساسية
    currency = Currency.objects.filter(is_base=True, is_active=True).first()
    if not currency:
        # إذا لم توجد عملة أساسية، استخدم أول عملة نشطة
        currency = Currency.objects.filter(is_active=True).first()

    if not currency:
        print("❌ لا توجد عملة نشطة في النظام!")
        return

    # الحصول على مستخدم للتسجيل (أول مستخدم نشط)
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ لا يوجد مستخدم نشط في النظام!")
        return

    print(f"الشركة: {company.name}")
    print(f"العملة: {currency.name}")
    print(f"المستخدم: {user.username}")
    print("-" * 50)

    # قوائم الأسعار الجديدة المطلوبة
    new_price_lists = [
        {'name': 'سعر البيع', 'code': 'SELL', 'description': 'سعر البيع الأساسي', 'is_default': True},
        {'name': 'نصف جملة', 'code': 'HALF_WHOLE', 'description': 'سعر نصف جملة'},
        {'name': 'سعر الجملة', 'code': 'WHOLESALE', 'description': 'سعر الجملة'},
        {'name': 'سعر التصدير', 'code': 'EXPORT', 'description': 'سعر التصدير'},
        {'name': 'سعر التوزيع', 'code': 'DISTRIBUTION', 'description': 'سعر التوزيع'},
        {'name': 'سعر آخر شراء', 'code': 'LAST_PURCHASE', 'description': 'سعر آخر شراء'},
        {'name': 'سعر آخر شراء – إجمالي', 'code': 'LAST_PURCHASE_TOTAL', 'description': 'سعر آخر شراء – إجمالي'},
        {'name': 'سعر آخر بيع', 'code': 'LAST_SALE', 'description': 'سعر آخر بيع'},
    ]

    try:
        with transaction.atomic():
            # 1. حذف جميع قوائم الأسعار الحالية
            old_count = PriceList.objects.filter(company=company).count()
            print(f"🗑️  حذف {old_count} قائمة أسعار قديمة...")
            PriceList.objects.filter(company=company).delete()
            print("✅ تم حذف قوائم الأسعار القديمة")
            print("-" * 50)

            # 2. إضافة قوائم الأسعار الجديدة
            print("➕ إضافة قوائم الأسعار الجديدة:")
            created_lists = []

            for idx, price_list_data in enumerate(new_price_lists, 1):
                price_list = PriceList.objects.create(
                    company=company,
                    currency=currency,
                    name=price_list_data['name'],
                    code=price_list_data['code'],
                    description=price_list_data.get('description', ''),
                    is_default=price_list_data.get('is_default', False),
                    is_active=True,
                    created_by=user
                )
                created_lists.append(price_list)
                default_marker = " [افتراضية]" if price_list.is_default else ""
                print(f"  {idx}. ✅ {price_list.name} ({price_list.code}){default_marker}")

            print("-" * 50)
            print(f"✅ تم إنشاء {len(created_lists)} قائمة أسعار جديدة بنجاح!")

            # عرض ملخص
            print("\n" + "=" * 50)
            print("📋 قوائم الأسعار الجديدة:")
            print("=" * 50)
            for pl in PriceList.objects.filter(company=company).order_by('id'):
                default_marker = " ⭐" if pl.is_default else ""
                print(f"  • {pl.name} ({pl.code}){default_marker}")

    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 50)
    print("تحديث قوائم الأسعار")
    print("=" * 50)
    update_price_lists()
    print("\n✅ انتهت العملية بنجاح!")

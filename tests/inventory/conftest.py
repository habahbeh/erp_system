# tests/inventory/conftest.py
"""
إعدادات pytest المشتركة لاختبارات المخزون
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone


@pytest.fixture
def company(db):
    """إنشاء شركة للاختبار"""
    from apps.core.models import Company, Currency

    # إنشاء عملة
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
        name_en='Test Company',
        tax_number='TEST123456',
        phone='0123456789',
        email='test@test.com',
        address='العنوان للاختبار',
        city='عمّان',
        base_currency=currency,
        is_active=True
    )
    return company


@pytest.fixture
def branch(company):
    """إنشاء فرع للاختبار"""
    from apps.core.models import Branch

    branch = Branch.objects.create(
        company=company,
        name='الفرع الرئيسي',
        code='MAIN',
        is_active=True,
        is_main=True
    )
    return branch


@pytest.fixture
def user(company, branch):
    """إنشاء مستخدم للاختبار"""
    from apps.core.models import User

    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
        company=company,
        branch=branch,
        is_active=True,
        is_staff=True,
        is_superuser=True  # مستخدم مميز لديه كافة الصلاحيات
    )
    return user


@pytest.fixture
def warehouse(company, branch, user):
    """إنشاء مستودع للاختبار"""
    from apps.core.models import Warehouse

    warehouse = Warehouse.objects.create(
        company=company,
        branch=branch,
        name='المستودع الرئيسي',
        code='WH-MAIN',
        is_active=True,
        allow_negative_stock=False,
        created_by=user
    )
    return warehouse


@pytest.fixture
def warehouse2(company, branch, user):
    """إنشاء مستودع ثاني للتحويلات"""
    from apps.core.models import Warehouse

    warehouse = Warehouse.objects.create(
        company=company,
        branch=branch,
        name='المستودع الفرعي',
        code='WH-SUB',
        is_active=True,
        allow_negative_stock=False,
        created_by=user
    )
    return warehouse


@pytest.fixture
def uom(company, user):
    """إنشاء وحدة قياس"""
    from apps.core.models import UnitOfMeasure, UoMGroup

    group, _ = UoMGroup.objects.get_or_create(
        company=company,
        code='UNIT',
        defaults={
            'name': 'مجموعة الوحدات',
            'created_by': user
        }
    )

    uom = UnitOfMeasure.objects.create(
        company=company,
        uom_group=group,
        name='قطعة',
        code='PC',
        symbol='قطعة',
        uom_type='UNIT',
        is_base_unit=True,
        created_by=user
    )
    return uom


@pytest.fixture
def category(company, user):
    """إنشاء تصنيف للمواد"""
    from apps.core.models import ItemCategory

    category = ItemCategory.objects.create(
        company=company,
        code='CAT-001',
        name='تصنيف اختبار',
        created_by=user
    )
    return category


@pytest.fixture
def item(company, category, uom, user):
    """إنشاء مادة للاختبار"""
    from apps.core.models import Item, Currency

    currency = Currency.objects.get(code='JOD')

    item = Item.objects.create(
        company=company,
        code='ITEM-001',
        name='مادة اختبار',
        category=category,
        base_uom=uom,
        currency=currency,
        tax_rate=Decimal('16.0'),
        has_variants=False,
        is_active=True,
        created_by=user
    )
    return item


@pytest.fixture
def item_with_variants(company, category, uom, user):
    """إنشاء مادة مع متغيرات"""
    from apps.core.models import Item, ItemVariant, Currency

    currency = Currency.objects.get(code='JOD')

    item = Item.objects.create(
        company=company,
        code='ITEM-VAR',
        name='مادة مع متغيرات',
        category=category,
        base_uom=uom,
        currency=currency,
        tax_rate=Decimal('16.0'),
        has_variants=True,
        is_active=True,
        created_by=user
    )

    # إنشاء متغيرات
    variant1 = ItemVariant.objects.create(
        company=company,
        item=item,
        code='VAR-RED',
        barcode='1234567890',
        is_active=True,
        created_by=user
    )

    variant2 = ItemVariant.objects.create(
        company=company,
        item=item,
        code='VAR-BLUE',
        barcode='0987654321',
        is_active=True,
        created_by=user
    )

    return item, variant1, variant2


@pytest.fixture
def supplier(company, user):
    """إنشاء مورد للاختبار"""
    from apps.core.models import BusinessPartner

    supplier = BusinessPartner.objects.create(
        company=company,
        code='SUP-001',
        name='مورد اختبار',
        partner_type='supplier',
        is_active=True,
        created_by=user
    )
    return supplier


@pytest.fixture
def customer(company, user):
    """إنشاء عميل للاختبار"""
    from apps.core.models import BusinessPartner

    customer = BusinessPartner.objects.create(
        company=company,
        code='CUST-001',
        name='عميل اختبار',
        partner_type='customer',
        is_active=True,
        created_by=user
    )
    return customer


@pytest.fixture
def fiscal_year(company, user):
    """إنشاء سنة مالية للاختبار"""
    from apps.accounting.models import FiscalYear, AccountingPeriod

    today = date.today()
    start_date = date(today.year, 1, 1)
    end_date = date(today.year, 12, 31)

    fiscal_year = FiscalYear.objects.create(
        company=company,
        name=f'سنة {today.year}',
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        is_closed=False,
        created_by=user
    )

    # إنشاء الفترات المحاسبية
    for month in range(1, 13):
        from calendar import monthrange
        period_start = date(today.year, month, 1)
        period_end = date(today.year, month, monthrange(today.year, month)[1])

        AccountingPeriod.objects.create(
            company=company,
            fiscal_year=fiscal_year,
            name=f'شهر {month}',
            start_date=period_start,
            end_date=period_end,
            is_closed=False,
            created_by=user
        )

    return fiscal_year


@pytest.fixture
def accounts(company, user):
    """إنشاء الحسابات المحاسبية الأساسية"""
    from apps.accounting.models import Account, AccountType

    # إنشاء أنواع الحسابات (بدون company)
    asset_type, _ = AccountType.objects.get_or_create(
        code='1',
        defaults={
            'name': 'أصول',
            'normal_balance': 'debit',
        }
    )

    liability_type, _ = AccountType.objects.get_or_create(
        code='2',
        defaults={
            'name': 'التزامات',
            'normal_balance': 'credit',
        }
    )

    expense_type, _ = AccountType.objects.get_or_create(
        code='5',
        defaults={
            'name': 'مصروفات',
            'normal_balance': 'debit',
        }
    )

    # حساب المخزون
    inventory_account, _ = Account.objects.get_or_create(
        company=company,
        code='120000',
        defaults={
            'name': 'المخزون',
            'account_type': asset_type,
            'is_active': True,
            'created_by': user
        }
    )

    # حساب الموردين
    supplier_account, _ = Account.objects.get_or_create(
        company=company,
        code='210000',
        defaults={
            'name': 'الموردين',
            'account_type': liability_type,
            'is_active': True,
            'created_by': user
        }
    )

    # حساب تكلفة البضاعة المباعة
    cogs_account, _ = Account.objects.get_or_create(
        company=company,
        code='510000',
        defaults={
            'name': 'تكلفة البضاعة المباعة',
            'account_type': expense_type,
            'is_active': True,
            'created_by': user
        }
    )

    return {
        'inventory': inventory_account,
        'supplier': supplier_account,
        'cogs': cogs_account
    }


@pytest.fixture
def stock_in(company, branch, warehouse, item, supplier, user):
    """إنشاء سند إدخال للاختبار"""
    from apps.inventory.models import StockIn, StockDocumentLine

    stock_in = StockIn.objects.create(
        company=company,
        branch=branch,
        date=date.today(),
        warehouse=warehouse,
        source_type='purchase',
        supplier=supplier,
        created_by=user
    )

    StockDocumentLine.objects.create(
        stock_in=stock_in,
        item=item,
        quantity=Decimal('100'),
        unit_cost=Decimal('10.000')
    )

    return stock_in


@pytest.fixture
def item_stock(company, item, warehouse, user):
    """إنشاء رصيد مادة للاختبار"""
    from apps.inventory.models import ItemStock

    stock = ItemStock.objects.create(
        company=company,
        item=item,
        warehouse=warehouse,
        quantity=Decimal('100'),
        reserved_quantity=Decimal('0'),
        average_cost=Decimal('10.000'),
        total_value=Decimal('1000.000'),
        min_level=Decimal('10'),
        max_level=Decimal('500'),
        reorder_point=Decimal('20'),
        created_by=user
    )
    return stock

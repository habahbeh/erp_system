"""
إعدادات pytest لاختبارات نظام المشتريات
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def company(db, currency):
    """إنشاء شركة تجريبية"""
    from apps.core.models import Company
    company, created = Company.objects.get_or_create(
        tax_number='TEST123456',
        defaults={
            'name': 'شركة الاختبار',
            'name_en': 'Test Company',
            'phone': '0123456789',
            'email': 'test@test.com',
            'address': 'العنوان للاختبار',
            'city': 'عمّان',
            'base_currency': currency,
            'is_active': True,
        }
    )
    return company


@pytest.fixture
def branch(company):
    """إنشاء فرع تجريبي"""
    from apps.core.models import Branch
    branch, created = Branch.objects.get_or_create(
        company=company,
        code='MAIN',
        defaults={
            'name': 'الفرع الرئيسي',
            'name_en': 'Main Branch',
            'is_active': True,
        }
    )
    return branch


@pytest.fixture
def warehouse(company, branch):
    """إنشاء مستودع تجريبي"""
    from apps.core.models import Warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        company=company,
        code='MAIN-WH',
        defaults={
            'name': 'المستودع الرئيسي',
            'name_en': 'Main Warehouse',
            'is_active': True,
        }
    )
    return warehouse


@pytest.fixture
def currency():
    """إنشاء عملة تجريبية"""
    from apps.core.models import Currency
    currency, created = Currency.objects.get_or_create(
        code='JOD',
        defaults={
            'name': 'دينار أردني',
            'name_en': 'Jordanian Dinar',
            'symbol': 'د.أ',
            'exchange_rate': Decimal('1.000000'),
            'is_active': True,
        }
    )
    return currency


@pytest.fixture
def payment_method(company):
    """إنشاء طريقة دفع تجريبية"""
    from apps.core.models import PaymentMethod
    method, created = PaymentMethod.objects.get_or_create(
        company=company,
        code='CASH',
        defaults={
            'name': 'نقدي',
            'name_en': 'Cash',
            'is_active': True,
        }
    )
    return method


@pytest.fixture
def credit_payment_method(company):
    """طريقة دفع آجل"""
    from apps.core.models import PaymentMethod
    method, created = PaymentMethod.objects.get_or_create(
        company=company,
        code='CREDIT',
        defaults={
            'name': 'آجل',
            'name_en': 'Credit',
            'is_active': True,
        }
    )
    return method


@pytest.fixture
def uom(company):
    """إنشاء وحدة قياس تجريبية"""
    from apps.core.models import UnitOfMeasure
    uom, created = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='PC',
        defaults={
            'name': 'قطعة',
            'name_en': 'Piece',
            'is_active': True,
        }
    )
    return uom


@pytest.fixture
def uom_box(company):
    """وحدة قياس كرتونة"""
    from apps.core.models import UnitOfMeasure
    uom, created = UnitOfMeasure.objects.get_or_create(
        company=company,
        code='BOX',
        defaults={
            'name': 'كرتونة',
            'name_en': 'Box',
            'is_active': True,
        }
    )
    return uom


@pytest.fixture
def category(company):
    """إنشاء فئة تجريبية"""
    from apps.core.models import ItemCategory
    category, created = ItemCategory.objects.get_or_create(
        company=company,
        code='GEN',
        defaults={
            'name': 'عام',
            'name_en': 'General',
            'level': 1,
        }
    )
    return category


@pytest.fixture
def supplier(company):
    """إنشاء مورد تجريبي"""
    from apps.core.models import BusinessPartner
    supplier, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='SUP001',
        defaults={
            'name': 'مورد الاختبار',
            'name_en': 'Test Supplier',
            'partner_type': 'supplier',
            'is_active': True,
        }
    )
    return supplier


@pytest.fixture
def inactive_supplier(company):
    """مورد غير نشط"""
    from apps.core.models import BusinessPartner
    supplier, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='SUP-INACTIVE',
        defaults={
            'name': 'مورد غير نشط',
            'name_en': 'Inactive Supplier',
            'partner_type': 'supplier',
            'is_active': False,
        }
    )
    return supplier


@pytest.fixture
def item(company, category, uom):
    """إنشاء مادة تجريبية"""
    from apps.core.models import Item
    item, created = Item.objects.get_or_create(
        company=company,
        code='ITEM001',
        defaults={
            'name': 'مادة اختبار',
            'name_en': 'Test Item',
            'category': category,
            'base_uom': uom,
            'item_type': 'stock',
            'is_active': True,
        }
    )
    return item


@pytest.fixture
def item_with_variants(company, category, uom):
    """مادة مع متغيرات"""
    from apps.core.models import Item, ItemVariant
    item, created = Item.objects.get_or_create(
        company=company,
        code='ITEM-VAR',
        defaults={
            'name': 'مادة مع متغيرات',
            'name_en': 'Item with Variants',
            'category': category,
            'base_uom': uom,
            'item_type': 'stock',
            'has_variants': True,
            'is_active': True,
        }
    )

    # إنشاء متغير
    variant, _ = ItemVariant.objects.get_or_create(
        item=item,
        code='VAR001',
        defaults={
            'name': 'أحمر - L',
            'is_active': True,
        }
    )

    return item


@pytest.fixture
def admin_user(company, branch):
    """إنشاء مستخدم مدير"""
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    return user


@pytest.fixture
def regular_user(company, branch):
    """إنشاء مستخدم عادي"""
    user, created = User.objects.get_or_create(
        username='user_test',
        defaults={
            'email': 'user@test.com',
            'is_staff': False,
            'is_superuser': False,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    return user


@pytest.fixture
def fiscal_year(company):
    """إنشاء سنة مالية"""
    from apps.accounting.models import FiscalYear
    today = date.today()
    fy, created = FiscalYear.objects.get_or_create(
        company=company,
        year=today.year,
        defaults={
            'name': f'السنة المالية {today.year}',
            'start_date': date(today.year, 1, 1),
            'end_date': date(today.year, 12, 31),
            'is_closed': False,
        }
    )
    return fy


@pytest.fixture
def accounting_period(company, fiscal_year):
    """إنشاء فترة محاسبية"""
    from apps.accounting.models import AccountingPeriod
    today = date.today()
    period, created = AccountingPeriod.objects.get_or_create(
        fiscal_year=fiscal_year,
        period_number=today.month,
        defaults={
            'name': f'فترة {today.month}/{today.year}',
            'start_date': date(today.year, today.month, 1),
            'end_date': date(today.year, today.month, 28),  # simplified
            'is_closed': False,
        }
    )
    return period


@pytest.fixture
def inventory_account(company):
    """حساب المخزون"""
    from apps.accounting.models import Account, AccountType
    acc_type, _ = AccountType.objects.get_or_create(
        name='أصول',
        defaults={'nature': 'debit'}
    )
    account, created = Account.objects.get_or_create(
        company=company,
        code='120000',
        defaults={
            'name': 'المخزون',
            'account_type': acc_type,
            'is_active': True,
        }
    )
    return account


@pytest.fixture
def supplier_account(company):
    """حساب الموردين"""
    from apps.accounting.models import Account, AccountType
    acc_type, _ = AccountType.objects.get_or_create(
        name='خصوم',
        defaults={'nature': 'credit'}
    )
    account, created = Account.objects.get_or_create(
        company=company,
        code='210000',
        defaults={
            'name': 'الموردون',
            'account_type': acc_type,
            'is_active': True,
        }
    )
    return account


@pytest.fixture
def purchase_invoice(company, branch, warehouse, supplier, currency, payment_method, admin_user):
    """إنشاء فاتورة مشتريات تجريبية"""
    from apps.purchases.models import PurchaseInvoice
    invoice = PurchaseInvoice.objects.create(
        company=company,
        branch=branch,
        warehouse=warehouse,
        supplier=supplier,
        currency=currency,
        payment_method=payment_method,
        date=date.today(),
        invoice_type='purchase',
        created_by=admin_user,
    )
    return invoice


@pytest.fixture
def purchase_order(company, branch, warehouse, supplier, currency, admin_user):
    """إنشاء أمر شراء تجريبي"""
    from apps.purchases.models import PurchaseOrder
    order = PurchaseOrder.objects.create(
        company=company,
        branch=branch,
        warehouse=warehouse,
        supplier=supplier,
        currency=currency,
        date=date.today(),
        status='draft',
        created_by=admin_user,
    )
    return order


@pytest.fixture
def client_logged_in(client, admin_user):
    """عميل HTTP مسجل الدخول"""
    client.login(username='admin_test', password='testpass123')
    return client


@pytest.fixture
def request_factory():
    """مصنع الطلبات"""
    from django.test import RequestFactory
    return RequestFactory()


# Mark all tests to use database
pytestmark = pytest.mark.django_db

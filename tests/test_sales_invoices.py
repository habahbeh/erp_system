"""
اختبارات فواتير المبيعات
Sales Invoice Tests
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError


pytestmark = pytest.mark.django_db


# ============================================
# Fixtures خاصة بالمبيعات
# ============================================

@pytest.fixture
def customer(company):
    """إنشاء عميل تجريبي"""
    from apps.core.models import BusinessPartner
    customer, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='CUST001',
        defaults={
            'name': 'عميل الاختبار',
            'name_en': 'Test Customer',
            'partner_type': 'customer',
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def customer_with_credit_limit(company):
    """عميل مع حد ائتماني"""
    from apps.core.models import BusinessPartner
    customer, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='CUST-CREDIT',
        defaults={
            'name': 'عميل بحد ائتماني',
            'name_en': 'Customer with Credit Limit',
            'partner_type': 'customer',
            'credit_limit': Decimal('5000.000'),
            'is_active': True,
        }
    )
    return customer


@pytest.fixture
def inactive_customer(company):
    """عميل غير نشط"""
    from apps.core.models import BusinessPartner
    customer, created = BusinessPartner.objects.get_or_create(
        company=company,
        code='CUST-INACTIVE',
        defaults={
            'name': 'عميل غير نشط',
            'name_en': 'Inactive Customer',
            'partner_type': 'customer',
            'is_active': False,
        }
    )
    return customer


@pytest.fixture
def revenue_account(company):
    """حساب الإيرادات"""
    from apps.accounting.models import Account, AccountType
    acc_type, _ = AccountType.objects.get_or_create(
        name='إيرادات',
        defaults={'nature': 'credit'}
    )
    account, created = Account.objects.get_or_create(
        company=company,
        code='410000',
        defaults={
            'name': 'إيرادات المبيعات',
            'account_type': acc_type,
            'is_active': True,
            'accept_entries': True,
        }
    )
    return account


@pytest.fixture
def customer_account(company):
    """حساب العملاء"""
    from apps.accounting.models import Account, AccountType
    acc_type, _ = AccountType.objects.get_or_create(
        name='أصول',
        defaults={'nature': 'debit'}
    )
    account, created = Account.objects.get_or_create(
        company=company,
        code='130000',
        defaults={
            'name': 'العملاء',
            'account_type': acc_type,
            'is_active': True,
            'accept_entries': True,
        }
    )
    return account


@pytest.fixture
def tax_account(company):
    """حساب الضريبة"""
    from apps.accounting.models import Account, AccountType
    acc_type, _ = AccountType.objects.get_or_create(
        name='خصوم',
        defaults={'nature': 'credit'}
    )
    account, created = Account.objects.get_or_create(
        company=company,
        code='210200',
        defaults={
            'name': 'ضريبة المبيعات المستحقة',
            'account_type': acc_type,
            'is_active': True,
            'accept_entries': True,
        }
    )
    return account


@pytest.fixture
def item_with_stock(company, category, uom, warehouse):
    """مادة مع رصيد مخزني"""
    from apps.core.models import Item
    from apps.inventory.models import ItemStock

    item, created = Item.objects.get_or_create(
        company=company,
        code='ITEM-STOCK',
        defaults={
            'name': 'مادة مع رصيد',
            'name_en': 'Item with Stock',
            'category': category,
            'base_uom': uom,
            'item_type': 'stock',
            'is_active': True,
            'cost_price': Decimal('50.000'),
        }
    )

    # إنشاء رصيد مخزني
    stock, _ = ItemStock.objects.get_or_create(
        company=company,
        item=item,
        warehouse=warehouse,
        defaults={
            'quantity': Decimal('100.000'),
            'average_cost': Decimal('50.000'),
        }
    )

    return item


@pytest.fixture
def sales_invoice(company, branch, warehouse, customer, currency, payment_method, admin_user):
    """إنشاء فاتورة مبيعات تجريبية"""
    from apps.sales.models import SalesInvoice
    invoice = SalesInvoice.objects.create(
        company=company,
        branch=branch,
        warehouse=warehouse,
        customer=customer,
        currency=currency,
        payment_method=payment_method,
        salesperson=admin_user,
        date=date.today(),
        receipt_number='REC-001',
        invoice_type='sales',
        created_by=admin_user,
    )
    return invoice


@pytest.fixture
def sales_invoice_with_items(sales_invoice, item_with_stock, uom):
    """فاتورة مبيعات مع سطور"""
    from apps.sales.models import InvoiceItem

    InvoiceItem.objects.create(
        invoice=sales_invoice,
        item=item_with_stock,
        quantity=Decimal('10.000'),
        unit=uom,
        unit_price=Decimal('100.000'),
        tax_rate=Decimal('16.00'),
    )

    sales_invoice.calculate_totals()
    sales_invoice.save()

    return sales_invoice


# ============================================
# اختبارات إنشاء الفاتورة
# ============================================

class TestSalesInvoiceCreation:
    """اختبارات إنشاء فاتورة المبيعات"""

    def test_create_basic_invoice(self, company, branch, warehouse, customer,
                                   currency, payment_method, admin_user):
        """اختبار إنشاء فاتورة أساسية"""
        from apps.sales.models import SalesInvoice

        invoice = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-TEST-001',
            created_by=admin_user,
        )

        assert invoice.pk is not None
        assert invoice.number.startswith('SI/')
        assert invoice.invoice_type == 'sales'
        assert invoice.is_posted == False
        assert invoice.payment_status == 'unpaid'

    def test_auto_generate_invoice_number(self, company, branch, warehouse, customer,
                                          currency, payment_method, admin_user):
        """اختبار توليد رقم الفاتورة تلقائياً"""
        from apps.sales.models import SalesInvoice

        invoice1 = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-AUTO-001',
            created_by=admin_user,
        )

        invoice2 = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-AUTO-002',
            created_by=admin_user,
        )

        # التحقق من أن الأرقام تسلسلية
        num1 = int(invoice1.number.split('/')[-1])
        num2 = int(invoice2.number.split('/')[-1])
        assert num2 == num1 + 1

    def test_create_return_invoice(self, company, branch, warehouse, customer,
                                   currency, payment_method, admin_user):
        """اختبار إنشاء فاتورة مرتجع"""
        from apps.sales.models import SalesInvoice

        invoice = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-RET-001',
            invoice_type='return',
            created_by=admin_user,
        )

        assert invoice.number.startswith('SR/')  # Sales Return

    def test_unique_invoice_number_per_company(self, company, branch, warehouse, customer,
                                               currency, payment_method, admin_user):
        """اختبار أن رقم الفاتورة فريد لكل شركة"""
        from apps.sales.models import SalesInvoice

        # إنشاء فاتورة بنفس الرقم في نفس الشركة يجب أن يفشل
        invoice1 = SalesInvoice.objects.create(
            company=company,
            branch=branch,
            warehouse=warehouse,
            customer=customer,
            currency=currency,
            payment_method=payment_method,
            salesperson=admin_user,
            date=date.today(),
            receipt_number='REC-UNIQUE-001',
            created_by=admin_user,
        )

        # محاولة إنشاء فاتورة بنفس الرقم
        with pytest.raises(IntegrityError):
            SalesInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                customer=customer,
                currency=currency,
                payment_method=payment_method,
                salesperson=admin_user,
                date=date.today(),
                number=invoice1.number,  # نفس الرقم
                receipt_number='REC-UNIQUE-002',
                created_by=admin_user,
            )


# ============================================
# اختبارات سطور الفاتورة
# ============================================

class TestInvoiceItems:
    """اختبارات سطور الفاتورة"""

    def test_add_item_to_invoice(self, sales_invoice, item, uom):
        """اختبار إضافة سطر للفاتورة"""
        from apps.sales.models import InvoiceItem

        line = InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('5.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        assert line.pk is not None
        assert line.subtotal == Decimal('500.000')

    def test_calculate_line_with_discount_percentage(self, sales_invoice, item, uom):
        """اختبار حساب السطر مع خصم نسبي"""
        from apps.sales.models import InvoiceItem

        line = InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
            discount_percentage=Decimal('10.00'),
        )

        # 10 * 100 = 1000
        # خصم 10% = 100
        # الإجمالي = 900
        assert line.discount_amount == Decimal('100.000')
        assert line.subtotal == Decimal('900.000')

    def test_calculate_line_with_tax(self, sales_invoice, item, uom):
        """اختبار حساب السطر مع ضريبة"""
        from apps.sales.models import InvoiceItem

        line = InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
            tax_rate=Decimal('16.00'),
            tax_included=False,
        )

        # الإجمالي = 1000
        # الضريبة = 1000 * 16% = 160
        assert line.subtotal == Decimal('1000.000')
        assert line.tax_amount == Decimal('160.000')

    def test_calculate_line_with_tax_included(self, sales_invoice, item, uom):
        """اختبار حساب السطر مع ضريبة مشمولة"""
        from apps.sales.models import InvoiceItem

        line = InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('1.000'),
            unit=uom,
            unit_price=Decimal('116.000'),  # شامل الضريبة
            tax_rate=Decimal('16.00'),
            tax_included=True,
        )

        # السعر شامل = 116
        # الضريبة = 116 - (116 / 1.16) = 116 - 100 = 16
        assert abs(line.tax_amount - Decimal('16.000')) < Decimal('0.01')

    def test_invoice_calculates_totals(self, sales_invoice, item, uom):
        """اختبار حساب مجاميع الفاتورة"""
        from apps.sales.models import InvoiceItem

        # إضافة سطرين
        InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
            tax_rate=Decimal('16.00'),
        )

        InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('5.000'),
            unit=uom,
            unit_price=Decimal('200.000'),
            tax_rate=Decimal('16.00'),
        )

        sales_invoice.calculate_totals()

        # السطر 1: 10 * 100 = 1000, ضريبة = 160
        # السطر 2: 5 * 200 = 1000, ضريبة = 160
        # المجموع = 2000, الضريبة = 320
        assert sales_invoice.subtotal_before_discount == Decimal('2000.000')
        assert sales_invoice.tax_amount == Decimal('320.000')
        assert sales_invoice.total_with_tax == Decimal('2320.000')

    def test_invoice_discount_percentage(self, sales_invoice, item, uom):
        """اختبار خصم الفاتورة بالنسبة المئوية"""
        from apps.sales.models import InvoiceItem

        InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        sales_invoice.discount_type = 'percentage'
        sales_invoice.discount_value = Decimal('10.00')
        sales_invoice.calculate_totals()

        # المجموع = 1000
        # خصم 10% = 100
        assert sales_invoice.discount_amount == Decimal('100.000')
        assert sales_invoice.subtotal_after_discount == Decimal('900.000')

    def test_invoice_discount_amount(self, sales_invoice, item, uom):
        """اختبار خصم الفاتورة بالقيمة"""
        from apps.sales.models import InvoiceItem

        InvoiceItem.objects.create(
            invoice=sales_invoice,
            item=item,
            quantity=Decimal('10.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        sales_invoice.discount_type = 'amount'
        sales_invoice.discount_value = Decimal('150.000')
        sales_invoice.calculate_totals()

        assert sales_invoice.discount_amount == Decimal('150.000')
        assert sales_invoice.subtotal_after_discount == Decimal('850.000')


# ============================================
# اختبارات حالة الدفع
# ============================================

class TestPaymentStatus:
    """اختبارات حالة الدفع"""

    def test_initial_payment_status_unpaid(self, sales_invoice_with_items):
        """اختبار أن الحالة الأولية غير مدفوعة"""
        assert sales_invoice_with_items.payment_status == 'unpaid'
        assert sales_invoice_with_items.paid_amount == Decimal('0')

    def test_partial_payment(self, sales_invoice_with_items):
        """اختبار الدفع الجزئي"""
        total = sales_invoice_with_items.total_with_tax
        partial = total / 2

        sales_invoice_with_items.paid_amount = partial
        sales_invoice_with_items.update_payment_status()

        assert sales_invoice_with_items.payment_status == 'partial'
        assert sales_invoice_with_items.remaining_amount == total - partial

    def test_full_payment(self, sales_invoice_with_items):
        """اختبار الدفع الكامل"""
        sales_invoice_with_items.paid_amount = sales_invoice_with_items.total_with_tax
        sales_invoice_with_items.update_payment_status()

        assert sales_invoice_with_items.payment_status == 'paid'
        assert sales_invoice_with_items.remaining_amount == Decimal('0')

    def test_overpayment_corrected(self, sales_invoice_with_items):
        """اختبار تصحيح الدفع الزائد"""
        total = sales_invoice_with_items.total_with_tax
        sales_invoice_with_items.paid_amount = total + Decimal('100')
        sales_invoice_with_items.update_payment_status()

        # يجب تصحيح المبلغ المدفوع
        assert sales_invoice_with_items.paid_amount == total
        assert sales_invoice_with_items.payment_status == 'paid'


# ============================================
# اختبارات العمولة
# ============================================

class TestCommission:
    """اختبارات العمولة"""

    def test_calculate_commission(self, sales_invoice_with_items):
        """اختبار حساب العمولة"""
        sales_invoice_with_items.salesperson_commission_rate = Decimal('5.00')
        sales_invoice_with_items.calculate_commission()

        expected = sales_invoice_with_items.total_with_tax * Decimal('0.05')
        assert sales_invoice_with_items.salesperson_commission_amount == expected

    def test_zero_commission_rate(self, sales_invoice_with_items):
        """اختبار عمولة صفر"""
        sales_invoice_with_items.salesperson_commission_rate = Decimal('0')
        sales_invoice_with_items.calculate_commission()

        assert sales_invoice_with_items.salesperson_commission_amount == Decimal('0')


# ============================================
# اختبارات الصلاحيات
# ============================================

class TestInvoicePermissions:
    """اختبارات الصلاحيات"""

    def test_superuser_can_create(self, sales_invoice, admin_user):
        """اختبار أن المسؤول يمكنه الإنشاء"""
        assert sales_invoice.can_user_create(admin_user) == True

    def test_superuser_can_edit_unposted(self, sales_invoice, admin_user):
        """اختبار أن المسؤول يمكنه التعديل"""
        assert sales_invoice.can_user_edit(admin_user) == True

    def test_cannot_edit_posted_invoice(self, sales_invoice_with_items, admin_user):
        """اختبار عدم إمكانية تعديل فاتورة مرحلة"""
        sales_invoice_with_items.is_posted = True
        sales_invoice_with_items.save()

        assert sales_invoice_with_items.can_user_edit(admin_user) == False

    def test_cannot_delete_posted_invoice(self, sales_invoice_with_items, admin_user):
        """اختبار عدم إمكانية حذف فاتورة مرحلة"""
        sales_invoice_with_items.is_posted = True
        sales_invoice_with_items.save()

        assert sales_invoice_with_items.can_user_delete(admin_user) == False

    def test_superuser_can_post(self, sales_invoice_with_items, admin_user):
        """اختبار أن المسؤول يمكنه الترحيل"""
        assert sales_invoice_with_items.can_user_post(admin_user) == True


# ============================================
# اختبارات Validation
# ============================================

class TestInvoiceValidation:
    """اختبارات التحقق من الصحة"""

    def test_cannot_post_empty_invoice(self, sales_invoice, admin_user):
        """اختبار عدم إمكانية ترحيل فاتورة فارغة"""
        with pytest.raises(ValidationError) as exc_info:
            sales_invoice.post(user=admin_user)

        assert 'لا توجد سطور' in str(exc_info.value)

    def test_cannot_post_twice(self, sales_invoice_with_items, admin_user,
                               fiscal_year, revenue_account, customer_account):
        """اختبار عدم إمكانية ترحيل مرتين"""
        # ترحيل أول
        sales_invoice_with_items.is_posted = True
        sales_invoice_with_items.save()

        # محاولة ترحيل ثانية
        with pytest.raises(ValidationError) as exc_info:
            sales_invoice_with_items.post(user=admin_user)

        assert 'مرحلة مسبقاً' in str(exc_info.value)

    def test_item_variant_validation(self, sales_invoice, item_with_variants, uom):
        """اختبار التحقق من المتغيرات"""
        from apps.sales.models import InvoiceItem

        # إنشاء سطر لمادة ذات متغيرات بدون تحديد المتغير
        line = InvoiceItem(
            invoice=sales_invoice,
            item=item_with_variants,
            quantity=Decimal('1.000'),
            unit=uom,
            unit_price=Decimal('100.000'),
        )

        with pytest.raises(ValidationError):
            line.clean()


# ============================================
# اختبارات الأداء
# ============================================

class TestInvoicePerformance:
    """اختبارات الأداء"""

    def test_bulk_create_lines(self, sales_invoice, item, uom):
        """اختبار إنشاء سطور متعددة"""
        from apps.sales.models import InvoiceItem

        lines = []
        for i in range(50):
            lines.append(InvoiceItem(
                invoice=sales_invoice,
                item=item,
                quantity=Decimal('1.000'),
                unit=uom,
                unit_price=Decimal('100.000'),
            ))

        InvoiceItem.objects.bulk_create(lines)

        assert sales_invoice.lines.count() == 50

    def test_calculate_totals_performance(self, sales_invoice, item, uom):
        """اختبار أداء حساب المجاميع"""
        from apps.sales.models import InvoiceItem
        import time

        # إنشاء 100 سطر
        lines = []
        for i in range(100):
            lines.append(InvoiceItem(
                invoice=sales_invoice,
                item=item,
                quantity=Decimal('1.000'),
                unit=uom,
                unit_price=Decimal('100.000'),
                tax_rate=Decimal('16.00'),
            ))
        InvoiceItem.objects.bulk_create(lines)

        # قياس وقت حساب المجاميع
        start = time.time()
        sales_invoice.calculate_totals()
        elapsed = time.time() - start

        # يجب أن يكون أقل من ثانية
        assert elapsed < 1.0
        assert sales_invoice.subtotal_before_discount == Decimal('10000.000')

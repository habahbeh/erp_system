# apps/purchases/tests/test_base.py
"""
Base Test Classes and Utilities
الأساس المشترك للاختبارات
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from apps.core.models import (
    Company, Branch, Warehouse, BusinessPartner,
    Item, ItemCategory, UnitOfMeasure, Currency, PaymentMethod
)
from apps.purchases.models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseQuotationRequest, PurchaseQuotationRequestItem,
    PurchaseQuotation, PurchaseQuotationItem,
    PurchaseContract, PurchaseContractItem,
    GoodsReceipt, GoodsReceiptLine,
)

User = get_user_model()


class PurchaseTestBase(TestCase):
    """Base class for all purchase tests with common setup"""

    @classmethod
    def setUpTestData(cls):
        """Set up data for all tests - runs once per test class"""
        # Create currency first
        cls.currency = Currency.objects.create(
            code='JOD',
            name='دينار أردني',
            name_en='Jordanian Dinar',
            symbol='د.أ',
            is_base=True,
            is_active=True,
            exchange_rate=Decimal('1.000')
        )

        # Create company (without code and currency - not in model)
        cls.company = Company.objects.create(
            name='شركة اختبار',
            name_en='Test Company',
            tax_number='123456789',
            base_currency=cls.currency,
            is_active=True
        )

        # Create branch
        cls.branch = Branch.objects.create(
            company=cls.company,
            name='الفرع الرئيسي',
            code='MAIN',
            is_active=True,
            is_main=True
        )

        # Create admin user first (needed for warehouse created_by)
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

        # Create payment method (after company)
        cls.payment_method = PaymentMethod.objects.create(
            company=cls.company,
            name='نقدي',
            code='CASH',
            is_active=True,
            created_by=cls.admin_user
        )

        # Create warehouse
        cls.warehouse = Warehouse.objects.create(
            company=cls.company,
            branch=cls.branch,
            name='المستودع الرئيسي',
            code='WH01',
            is_active=True,
            created_by=cls.admin_user
        )

        # Create user with permissions
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            is_active=True
        )
        # Set user profile if exists
        if hasattr(cls.user, 'profile'):
            cls.user.profile.company = cls.company
            cls.user.profile.branch = cls.branch
            cls.user.profile.save()

        # Create supplier
        cls.supplier = BusinessPartner.objects.create(
            company=cls.company,
            name='مورد اختبار',
            code='SUP001',
            partner_type='supplier',
            is_active=True,
            created_by=cls.admin_user
        )

        # Create second supplier for comparison tests
        cls.supplier2 = BusinessPartner.objects.create(
            company=cls.company,
            name='مورد ثاني',
            code='SUP002',
            partner_type='supplier',
            is_active=True,
            created_by=cls.admin_user
        )

        # Create item category
        cls.category = ItemCategory.objects.create(
            company=cls.company,
            name='مواد خام',
            code='RAW',
            created_by=cls.admin_user
        )

        # Create unit of measure
        cls.uom = UnitOfMeasure.objects.create(
            company=cls.company,
            name='قطعة',
            code='PC',
            is_base_unit=True,
            created_by=cls.admin_user
        )

        # Create items
        cls.item1 = Item.objects.create(
            company=cls.company,
            name='مادة اختبار 1',
            code='ITEM001',
            category=cls.category,
            base_uom=cls.uom,
            currency=cls.currency,
            is_active=True,
            created_by=cls.admin_user
        )

        cls.item2 = Item.objects.create(
            company=cls.company,
            name='مادة اختبار 2',
            code='ITEM002',
            category=cls.category,
            base_uom=cls.uom,
            currency=cls.currency,
            is_active=True,
            created_by=cls.admin_user
        )

        cls.item3 = Item.objects.create(
            company=cls.company,
            name='مادة اختبار 3',
            code='ITEM003',
            category=cls.category,
            base_uom=cls.uom,
            currency=cls.currency,
            is_active=True,
            created_by=cls.admin_user
        )

    def setUp(self):
        """Set up for each test - runs before each test method"""
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def create_purchase_request(self, status='draft', **kwargs):
        """Helper to create a purchase request"""
        defaults = {
            'company': self.company,
            'date': date.today(),
            'required_date': date.today() + timedelta(days=7),
            'status': status,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return PurchaseRequest.objects.create(**defaults)

    def create_purchase_order(self, status='draft', **kwargs):
        """Helper to create a purchase order"""
        defaults = {
            'company': self.company,
            'branch': self.branch,
            'warehouse': self.warehouse,
            'supplier': self.supplier,
            'date': date.today(),
            'expected_delivery_date': date.today() + timedelta(days=14),
            'currency': self.currency,
            'status': status,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return PurchaseOrder.objects.create(**defaults)

    def create_purchase_invoice(self, status='draft', **kwargs):
        """Helper to create a purchase invoice"""
        defaults = {
            'company': self.company,
            'branch': self.branch,
            'warehouse': self.warehouse,
            'supplier': self.supplier,
            'date': date.today(),
            'payment_method': self.payment_method,
            'currency': self.currency,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return PurchaseInvoice.objects.create(**defaults)

    def create_goods_receipt(self, purchase_order=None, status='draft', **kwargs):
        """Helper to create a goods receipt"""
        if not purchase_order:
            purchase_order = self.create_purchase_order(status='approved')

        defaults = {
            'company': self.company,
            'branch': self.branch,
            'purchase_order': purchase_order,
            'supplier': purchase_order.supplier,
            'warehouse': self.warehouse,
            'date': date.today(),
            'received_by': self.admin_user,
            'status': status,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return GoodsReceipt.objects.create(**defaults)

    def create_rfq(self, status='draft', **kwargs):
        """Helper to create a quotation request (RFQ)"""
        defaults = {
            'company': self.company,
            'date': date.today(),
            'submission_deadline': date.today() + timedelta(days=7),
            'currency': self.currency,
            'status': status,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return PurchaseQuotationRequest.objects.create(**defaults)

    def create_quotation(self, rfq=None, status='draft', **kwargs):
        """Helper to create a quotation"""
        if not rfq:
            rfq = self.create_rfq()

        defaults = {
            'company': self.company,
            'quotation_request': rfq,
            'supplier': kwargs.get('supplier', self.supplier),
            'date': date.today(),
            'valid_until': date.today() + timedelta(days=30),
            'currency': self.currency,
            'status': status,
            'created_by': self.admin_user,
        }
        # Remove supplier from kwargs if it was passed
        kwargs.pop('supplier', None)
        defaults.update(kwargs)
        return PurchaseQuotation.objects.create(**defaults)

    def create_contract(self, status='draft', **kwargs):
        """Helper to create a purchase contract"""
        defaults = {
            'company': self.company,
            'supplier': self.supplier,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'currency': self.currency,
            'status': status,
            'created_by': self.admin_user,
        }
        defaults.update(kwargs)
        return PurchaseContract.objects.create(**defaults)

    def add_items_to_request(self, pr_request, items=None):
        """Helper to add items to a purchase request"""
        if items is None:
            items = [(self.item1, 10), (self.item2, 20)]

        for item, qty in items:
            PurchaseRequestItem.objects.create(
                request=pr_request,
                item=item,
                quantity=Decimal(str(qty)),
                unit=self.uom.name,
                estimated_price=Decimal('100.000')
            )

    def add_items_to_order(self, po_order, items=None):
        """Helper to add items to a purchase order"""
        if items is None:
            items = [(self.item1, 10, 100), (self.item2, 20, 50)]

        for item, qty, price in items:
            PurchaseOrderItem.objects.create(
                order=po_order,
                item=item,
                quantity=Decimal(str(qty)),
                unit=self.uom,
                unit_price=Decimal(str(price))
            )

    def add_items_to_invoice(self, invoice, items=None):
        """Helper to add items to a purchase invoice"""
        if items is None:
            items = [(self.item1, 10, 100), (self.item2, 20, 50)]

        for item, qty, price in items:
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=Decimal(str(qty)),
                unit_price=Decimal(str(price))
            )

    def assertResponseSuccess(self, response, status_code=200):
        """Assert response is successful"""
        self.assertEqual(response.status_code, status_code)

    def assertResponseRedirect(self, response, expected_url=None):
        """Assert response is a redirect"""
        self.assertIn(response.status_code, [301, 302])
        if expected_url:
            self.assertRedirects(response, expected_url)

    def assertFormError(self, response, form_name, field, error_message):
        """Assert form has specific error"""
        form = response.context.get(form_name)
        self.assertIsNotNone(form)
        self.assertIn(field, form.errors)
        self.assertIn(error_message, str(form.errors[field]))

    def assertMessageContains(self, response, text):
        """Assert response messages contain text"""
        messages = list(response.wsgi_request._messages)
        message_texts = [str(m) for m in messages]
        self.assertTrue(
            any(text in msg for msg in message_texts),
            f"'{text}' not found in messages: {message_texts}"
        )

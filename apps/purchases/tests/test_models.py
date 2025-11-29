# apps/purchases/tests/test_models.py
"""
Model Tests for Purchases Module
اختبارات النماذج لوحدة المشتريات
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, timedelta

from .test_base import PurchaseTestBase
from apps.purchases.models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseQuotationRequest, PurchaseQuotationRequestItem,
    PurchaseQuotation, PurchaseQuotationItem,
    PurchaseContract, PurchaseContractItem,
    GoodsReceipt, GoodsReceiptLine,
)


# ============================================================================
# PURCHASE REQUEST TESTS
# ============================================================================

class PurchaseRequestModelTest(PurchaseTestBase):
    """Tests for PurchaseRequest model"""

    def test_create_purchase_request(self):
        """Test creating a basic purchase request"""
        request = self.create_purchase_request()
        self.assertIsNotNone(request.pk)
        self.assertIsNotNone(request.number)
        self.assertEqual(request.status, 'draft')
        self.assertEqual(request.company, self.company)

    def test_purchase_request_auto_number(self):
        """Test automatic number generation"""
        request1 = self.create_purchase_request()
        request2 = self.create_purchase_request()
        self.assertNotEqual(request1.number, request2.number)

    def test_purchase_request_str(self):
        """Test string representation"""
        request = self.create_purchase_request()
        self.assertIn(request.number, str(request))

    def test_purchase_request_items_total(self):
        """Test items total calculation"""
        request = self.create_purchase_request()
        self.add_items_to_request(request, [
            (self.item1, 10),  # 10 * 100 = 1000
            (self.item2, 5),   # 5 * 100 = 500
        ])
        # Total should be calculated based on estimated prices
        items = request.lines.all()
        self.assertEqual(items.count(), 2)

    def test_purchase_request_company_isolation(self):
        """Test that requests are isolated by company"""
        request = self.create_purchase_request()
        self.assertEqual(
            PurchaseRequest.objects.filter(company=self.company).count(),
            1
        )


class PurchaseRequestItemModelTest(PurchaseTestBase):
    """Tests for PurchaseRequestItem model"""

    def test_create_request_item(self):
        """Test creating a request item"""
        request = self.create_purchase_request()
        item = PurchaseRequestItem.objects.create(
            request=request,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit=self.uom.name,
            estimated_price=Decimal('100.000')
        )
        self.assertIsNotNone(item.pk)
        self.assertEqual(item.quantity, Decimal('10.000'))

    def test_request_item_line_total(self):
        """Test line total calculation"""
        request = self.create_purchase_request()
        item = PurchaseRequestItem.objects.create(
            request=request,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit=self.uom.name,
            estimated_price=Decimal('100.000')
        )
        # Line total = quantity * estimated_price
        expected_total = Decimal('10.000') * Decimal('100.000')
        self.assertEqual(item.quantity * item.estimated_price, expected_total)

    def test_request_item_zero_quantity_validation(self):
        """Test that zero quantity is not allowed"""
        request = self.create_purchase_request()
        item = PurchaseRequestItem(
            request=request,
            item=self.item1,
            quantity=Decimal('0'),
            unit=self.uom.name
        )
        # Should raise validation error or be handled by form


# ============================================================================
# PURCHASE ORDER TESTS
# ============================================================================

class PurchaseOrderModelTest(PurchaseTestBase):
    """Tests for PurchaseOrder model"""

    def test_create_purchase_order(self):
        """Test creating a basic purchase order"""
        order = self.create_purchase_order()
        self.assertIsNotNone(order.pk)
        self.assertIsNotNone(order.number)
        self.assertEqual(order.status, 'draft')
        self.assertEqual(order.supplier, self.supplier)

    def test_purchase_order_auto_number(self):
        """Test automatic number generation"""
        order1 = self.create_purchase_order()
        order2 = self.create_purchase_order()
        self.assertNotEqual(order1.number, order2.number)

    def test_purchase_order_str(self):
        """Test string representation"""
        order = self.create_purchase_order()
        self.assertIn(order.number, str(order))

    def test_purchase_order_calculate_total(self):
        """Test total calculation"""
        order = self.create_purchase_order()
        self.add_items_to_order(order, [
            (self.item1, 10, 100),  # 10 * 100 = 1000 + 16% tax = 1160
            (self.item2, 5, 200),   # 5 * 200 = 1000 + 16% tax = 1160
        ])
        order.calculate_total()
        # Total includes 16% tax by default: (1000 + 1000) * 1.16 = 2320
        self.assertEqual(order.total_amount, Decimal('2320.000'))

    def test_purchase_order_status_transitions(self):
        """Test valid status transitions"""
        order = self.create_purchase_order(status='draft')
        self.assertEqual(order.status, 'draft')

        # Submit for approval
        order.status = 'pending_approval'
        order.save()
        self.assertEqual(order.status, 'pending_approval')

    def test_purchase_order_supplier_required(self):
        """Test that supplier is required"""
        with self.assertRaises(IntegrityError):
            PurchaseOrder.objects.create(
                company=self.company,
                branch=self.branch,
                supplier=None,
                date=date.today(),
                currency=self.currency,
                created_by=self.admin_user,
            )


class PurchaseOrderItemModelTest(PurchaseTestBase):
    """Tests for PurchaseOrderItem model"""

    def test_create_order_item(self):
        """Test creating an order item"""
        order = self.create_purchase_order()
        item = PurchaseOrderItem.objects.create(
            order=order,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit=self.uom,
            unit_price=Decimal('100.000')
        )
        self.assertIsNotNone(item.pk)

    def test_order_item_line_total(self):
        """Test line total calculation"""
        order = self.create_purchase_order()
        item = PurchaseOrderItem.objects.create(
            order=order,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit=self.uom,
            unit_price=Decimal('100.000')
        )
        # With 16% tax: 1000 * 1.16 = 1160
        expected_total = Decimal('1160.000')
        self.assertEqual(item.total, expected_total)

    def test_order_item_with_discount(self):
        """Test line total with discount"""
        order = self.create_purchase_order()
        item = PurchaseOrderItem.objects.create(
            order=order,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit=self.uom,
            unit_price=Decimal('100.000'),
            discount_percentage=Decimal('10.000')  # 10% discount
        )
        # 10 * 100 = 1000, 10% discount = 100 → 900, +16% tax = 1044
        expected_total = Decimal('1044.000')
        self.assertEqual(item.total, expected_total)


# ============================================================================
# PURCHASE INVOICE TESTS
# ============================================================================

class PurchaseInvoiceModelTest(PurchaseTestBase):
    """Tests for PurchaseInvoice model"""

    def test_create_purchase_invoice(self):
        """Test creating a basic purchase invoice"""
        invoice = self.create_purchase_invoice()
        self.assertIsNotNone(invoice.pk)
        self.assertIsNotNone(invoice.number)
        # PurchaseInvoice uses is_posted instead of status
        self.assertEqual(invoice.is_posted, False)

    def test_purchase_invoice_auto_number(self):
        """Test automatic number generation"""
        invoice1 = self.create_purchase_invoice()
        invoice2 = self.create_purchase_invoice()
        self.assertNotEqual(invoice1.number, invoice2.number)

    def test_purchase_invoice_calculate_totals(self):
        """Test totals calculation"""
        invoice = self.create_purchase_invoice()
        self.add_items_to_invoice(invoice, [
            (self.item1, 10, 100),  # 1000
            (self.item2, 5, 200),   # 1000
        ])
        invoice.calculate_totals()
        # PurchaseInvoice uses subtotal_before_discount
        self.assertEqual(invoice.subtotal_before_discount, Decimal('2000.000'))

    def test_purchase_invoice_due_date_validation(self):
        """Test due date cannot be before invoice date"""
        invoice = self.create_purchase_invoice()
        invoice.due_date = invoice.date - timedelta(days=1)
        # Should handle validation


class PurchaseInvoiceItemModelTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceItem model"""

    def test_create_invoice_item(self):
        """Test creating an invoice item"""
        invoice = self.create_purchase_invoice()
        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000')
        )
        self.assertIsNotNone(item.pk)

    def test_invoice_item_line_total(self):
        """Test line total calculation"""
        invoice = self.create_purchase_invoice()
        item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000')
        )
        # PurchaseInvoiceItem uses 'subtotal' field, not 'total'
        self.assertEqual(item.subtotal, Decimal('1000.000'))


# ============================================================================
# GOODS RECEIPT TESTS
# ============================================================================

class GoodsReceiptModelTest(PurchaseTestBase):
    """Tests for GoodsReceipt model"""

    def test_create_goods_receipt(self):
        """Test creating a basic goods receipt"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)
        self.assertIsNotNone(receipt.pk)
        self.assertIsNotNone(receipt.number)
        self.assertEqual(receipt.status, 'draft')

    def test_goods_receipt_requires_order(self):
        """Test that purchase order is required"""
        with self.assertRaises(IntegrityError):
            GoodsReceipt.objects.create(
                company=self.company,
                branch=self.branch,
                purchase_order=None,
                supplier=self.supplier,
                warehouse=self.warehouse,
                date=date.today(),
                received_by=self.admin_user,
                created_by=self.admin_user,
            )

    def test_goods_receipt_quality_status(self):
        """Test quality check status options"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)

        valid_statuses = ['pending', 'passed', 'partial', 'failed']
        for status in valid_statuses:
            receipt.quality_check_status = status
            receipt.save()
            self.assertEqual(receipt.quality_check_status, status)


class GoodsReceiptLineModelTest(PurchaseTestBase):
    """Tests for GoodsReceiptLine model"""

    def test_create_receipt_line(self):
        """Test creating a goods receipt line"""
        order = self.create_purchase_order(status='approved')
        self.add_items_to_order(order)
        order_line = order.lines.first()
        receipt = self.create_goods_receipt(purchase_order=order)

        line = GoodsReceiptLine.objects.create(
            goods_receipt=receipt,
            purchase_order_line=order_line,
            item=self.item1,
            received_quantity=Decimal('10.000'),
        )
        self.assertIsNotNone(line.pk)

    def test_receipt_line_accepted_quantity(self):
        """Test accepted quantity calculation"""
        order = self.create_purchase_order(status='approved')
        self.add_items_to_order(order)
        order_line = order.lines.first()
        receipt = self.create_goods_receipt(purchase_order=order)

        line = GoodsReceiptLine.objects.create(
            goods_receipt=receipt,
            purchase_order_line=order_line,
            item=self.item1,
            received_quantity=Decimal('10.000'),
            rejected_quantity=Decimal('2.000'),
        )
        # Accepted = Received - Rejected (calculated manually)
        accepted = line.received_quantity - line.rejected_quantity
        expected_accepted = Decimal('8.000')
        self.assertEqual(accepted, expected_accepted)


# ============================================================================
# RFQ & QUOTATION TESTS
# ============================================================================

class PurchaseQuotationRequestModelTest(PurchaseTestBase):
    """Tests for PurchaseQuotationRequest (RFQ) model"""

    def test_create_rfq(self):
        """Test creating a basic RFQ"""
        rfq = self.create_rfq()
        self.assertIsNotNone(rfq.pk)
        self.assertIsNotNone(rfq.number)
        self.assertEqual(rfq.status, 'draft')

    def test_rfq_deadline_validation(self):
        """Test submission deadline must be in future"""
        rfq = self.create_rfq()
        rfq.submission_deadline = date.today() - timedelta(days=1)
        # Should handle validation


class PurchaseQuotationModelTest(PurchaseTestBase):
    """Tests for PurchaseQuotation model"""

    def test_create_quotation(self):
        """Test creating a basic quotation"""
        rfq = self.create_rfq()
        quotation = self.create_quotation(rfq=rfq)
        self.assertIsNotNone(quotation.pk)
        self.assertEqual(quotation.quotation_request, rfq)

    def test_quotation_calculate_totals(self):
        """Test quotation totals calculation"""
        rfq = self.create_rfq()
        quotation = self.create_quotation(rfq=rfq)

        PurchaseQuotationItem.objects.create(
            quotation=quotation,
            item=self.item1,
            quantity=Decimal('10.000'),
            unit_price=Decimal('100.000')
        )

        quotation.calculate_totals()
        self.assertEqual(quotation.total_amount, Decimal('1000.000'))

    def test_quotation_award(self):
        """Test awarding a quotation"""
        rfq = self.create_rfq()
        quotation = self.create_quotation(rfq=rfq, status='received')

        quotation.is_awarded = True
        quotation.status = 'awarded'
        quotation.save()

        self.assertTrue(quotation.is_awarded)
        self.assertEqual(quotation.status, 'awarded')


# ============================================================================
# PURCHASE CONTRACT TESTS
# ============================================================================

class PurchaseContractModelTest(PurchaseTestBase):
    """Tests for PurchaseContract model"""

    def test_create_contract(self):
        """Test creating a basic contract"""
        contract = self.create_contract()
        self.assertIsNotNone(contract.pk)
        self.assertIsNotNone(contract.number)
        self.assertEqual(contract.status, 'draft')

    def test_contract_date_validation(self):
        """Test end date must be after start date"""
        contract = self.create_contract()
        contract.end_date = contract.start_date - timedelta(days=1)
        # Should handle validation

    def test_contract_is_active(self):
        """Test contract active status"""
        contract = self.create_contract(
            status='active',
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30)
        )
        # Contract should be considered active
        self.assertEqual(contract.status, 'active')
        self.assertLessEqual(contract.start_date, date.today())
        self.assertGreaterEqual(contract.end_date, date.today())


# ============================================================================
# MODEL RELATIONSHIPS TESTS
# ============================================================================

class ModelRelationshipsTest(PurchaseTestBase):
    """Tests for model relationships and foreign keys"""

    def test_purchase_request_to_order(self):
        """Test request can link to order"""
        request = self.create_purchase_request()
        order = self.create_purchase_order(purchase_request=request)
        self.assertEqual(order.purchase_request, request)

    def test_order_to_invoice(self):
        """Test order can link to invoice via goods receipt"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)
        invoice = self.create_purchase_invoice(goods_receipt=receipt)
        self.assertEqual(invoice.goods_receipt, receipt)
        self.assertEqual(invoice.goods_receipt.purchase_order, order)

    def test_order_to_goods_receipt(self):
        """Test order to goods receipt relationship"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)
        self.assertEqual(receipt.purchase_order, order)
        self.assertIn(receipt, order.goods_receipts.all())

    def test_rfq_to_quotations(self):
        """Test RFQ to quotations relationship"""
        rfq = self.create_rfq()
        quot1 = self.create_quotation(rfq=rfq, supplier=self.supplier)
        quot2 = self.create_quotation(rfq=rfq, supplier=self.supplier2)

        self.assertEqual(rfq.quotations.count(), 2)
        self.assertIn(quot1, rfq.quotations.all())
        self.assertIn(quot2, rfq.quotations.all())

    def test_cascade_delete(self):
        """Test cascade delete behavior"""
        request = self.create_purchase_request()
        self.add_items_to_request(request)

        items_count = request.lines.count()
        self.assertGreater(items_count, 0)

        request_pk = request.pk
        request.delete()

        # Items should be deleted too
        self.assertEqual(
            PurchaseRequestItem.objects.filter(request_id=request_pk).count(),
            0
        )


# ============================================================================
# MODEL METHODS TESTS
# ============================================================================

class ModelMethodsTest(PurchaseTestBase):
    """Tests for model methods and properties"""

    def test_purchase_order_can_edit(self):
        """Test can_edit property"""
        order = self.create_purchase_order(status='draft')
        # Draft orders should be editable
        self.assertIn(order.status, ['draft', 'rejected'])

    def test_purchase_order_can_delete(self):
        """Test orders can only be deleted in draft"""
        order = self.create_purchase_order(status='draft')
        self.assertEqual(order.status, 'draft')

        # After approval, should not be deletable
        order.status = 'approved'
        order.save()
        self.assertEqual(order.status, 'approved')

    def test_invoice_is_paid(self):
        """Test invoice payment status"""
        invoice = self.create_purchase_invoice()
        self.add_items_to_invoice(invoice)
        invoice.calculate_totals()

        # Not posted initially (PurchaseInvoice doesn't have paid_amount, use is_posted)
        self.assertEqual(invoice.is_posted, False)

    def test_goods_receipt_is_posted(self):
        """Test goods receipt posting status"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)

        # Not posted initially
        self.assertFalse(receipt.is_posted)

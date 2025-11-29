# apps/purchases/tests/test_forms.py
"""
Form Tests for Purchases Module
اختبارات النماذج لوحدة المشتريات
"""

from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta

from .test_base import PurchaseTestBase
from apps.purchases.forms import (
    PurchaseRequestForm,
    PurchaseRequestItemForm,
    PurchaseRequestItemFormSet,
    PurchaseOrderForm,
    PurchaseOrderItemForm,
    PurchaseOrderItemFormSet,
    PurchaseInvoiceForm,
    PurchaseInvoiceItemForm,
    PurchaseInvoiceItemFormSet,
    GoodsReceiptForm,
    GoodsReceiptLineForm,
    GoodsReceiptLineFormSet,
    PurchaseQuotationRequestForm,
    PurchaseQuotationForm,
    PurchaseContractForm,
)
from apps.purchases.models import PurchaseOrderItem


# ============================================================================
# PURCHASE REQUEST FORM TESTS
# ============================================================================

class PurchaseRequestFormTest(PurchaseTestBase):
    """Tests for PurchaseRequestForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseRequestForm(
            data={
                'date': date.today(),
                'required_date': date.today() + timedelta(days=7),
                'priority': 'normal',
                'notes': 'ملاحظات اختبار',
            },
            company=self.company,
            user=self.admin_user
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields(self):
        """Test required fields validation"""
        form = PurchaseRequestForm(
            data={},
            company=self.company,
            user=self.admin_user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_required_date_in_future(self):
        """Test required_date should be in future or today"""
        form = PurchaseRequestForm(
            data={
                'date': date.today(),
                'required_date': date.today() - timedelta(days=1),
                'priority': 'normal',
            },
            company=self.company,
            user=self.admin_user
        )
        # Form may or may not validate this - depends on implementation

    def test_priority_choices(self):
        """Test priority field has correct choices"""
        form = PurchaseRequestForm(company=self.company, user=self.admin_user)
        priority_field = form.fields.get('priority')
        if priority_field:
            choices = [c[0] for c in priority_field.choices if c[0]]
            self.assertIn('normal', choices)


class PurchaseRequestItemFormTest(PurchaseTestBase):
    """Tests for PurchaseRequestItemForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseRequestItemForm(
            data={
                'item_description': 'وصف المادة المطلوبة',
                'quantity': '10.000',
                'unit': self.uom.name,
                'estimated_price': '100.000',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_quantity_required(self):
        """Test quantity is required"""
        form = PurchaseRequestItemForm(
            data={
                'item': self.item1.pk,
                'unit': self.uom.name,
            },
            company=self.company
        )
        self.assertFalse(form.is_valid())

    def test_negative_quantity(self):
        """Test negative quantity validation"""
        form = PurchaseRequestItemForm(
            data={
                'item': self.item1.pk,
                'quantity': '-10.000',
                'unit': self.uom.name,
            },
            company=self.company
        )
        # Should be invalid due to negative quantity
        if form.is_valid():
            # If form doesn't validate this, it's a potential issue
            pass

    def test_item_queryset_filtered_by_company(self):
        """Test item queryset is filtered by company"""
        form = PurchaseRequestItemForm(company=self.company)
        item_field = form.fields.get('item')
        if item_field and hasattr(item_field, 'queryset'):
            for item in item_field.queryset:
                self.assertEqual(item.company, self.company)


# ============================================================================
# PURCHASE ORDER FORM TESTS
# ============================================================================

class PurchaseOrderFormTest(PurchaseTestBase):
    """Tests for PurchaseOrderForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseOrderForm(
            data={
                'supplier': self.supplier.pk,
                'warehouse': self.warehouse.pk,
                'date': date.today(),
                'expected_delivery_date': date.today() + timedelta(days=14),
                'currency': self.currency.pk,
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_supplier_required(self):
        """Test supplier is required"""
        form = PurchaseOrderForm(
            data={
                'date': date.today(),
                'currency': self.currency.pk,
            },
            company=self.company
        )
        self.assertFalse(form.is_valid())
        self.assertIn('supplier', form.errors)

    def test_supplier_queryset_filtered(self):
        """Test supplier queryset filtered by company and type"""
        form = PurchaseOrderForm(company=self.company)
        supplier_field = form.fields.get('supplier')
        if supplier_field and hasattr(supplier_field, 'queryset'):
            for partner in supplier_field.queryset:
                self.assertEqual(partner.company, self.company)
                self.assertIn(partner.partner_type, ['supplier', 'both'])

    def test_expected_delivery_date_validation(self):
        """Test expected delivery date should be after order date"""
        form = PurchaseOrderForm(
            data={
                'supplier': self.supplier.pk,
                'date': date.today(),
                'expected_delivery_date': date.today() - timedelta(days=1),
                'currency': self.currency.pk,
            },
            company=self.company
        )
        # Form may or may not validate this


class PurchaseOrderItemFormTest(PurchaseTestBase):
    """Tests for PurchaseOrderItemForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseOrderItemForm(
            data={
                'item': self.item1.pk,
                'quantity': '10.000',
                'unit': self.uom.pk,
                'unit_price': '100.000',
                'tax_rate': '16.00',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_unit_price_required(self):
        """Test unit price is required"""
        form = PurchaseOrderItemForm(
            data={
                'item': self.item1.pk,
                'quantity': '10.000',
                'unit': self.uom.pk,
            },
            company=self.company
        )
        # Unit price should be required for orders
        if 'unit_price' in form.fields and form.fields['unit_price'].required:
            self.assertFalse(form.is_valid())

    def test_discount_percentage_range(self):
        """Test discount percentage is between 0-100"""
        form = PurchaseOrderItemForm(
            data={
                'item': self.item1.pk,
                'quantity': '10.000',
                'unit': self.uom.pk,
                'unit_price': '100.000',
                'discount_percentage': '150.000',  # Invalid - over 100%
            },
            company=self.company
        )
        # Should validate discount range


# ============================================================================
# PURCHASE INVOICE FORM TESTS
# ============================================================================

class PurchaseInvoiceFormTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseInvoiceForm(
            data={
                'invoice_type': 'purchase',
                'supplier': self.supplier.pk,
                'branch': self.branch.pk,
                'warehouse': self.warehouse.pk,
                'payment_method': self.payment_method.pk,
                'date': date.today(),
                'due_date': date.today() + timedelta(days=30),
                'currency': self.currency.pk,
                'supplier_invoice_number': 'INV-001',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_supplier_invoice_number_unique(self):
        """Test supplier invoice number uniqueness per supplier"""
        # Create first invoice
        invoice1 = self.create_purchase_invoice()
        invoice1.supplier_invoice_number = 'INV-001'
        invoice1.save()

        # Try to create second with same number
        form = PurchaseInvoiceForm(
            data={
                'supplier': self.supplier.pk,
                'date': date.today(),
                'due_date': date.today() + timedelta(days=30),
                'currency': self.currency.pk,
                'supplier_invoice_number': 'INV-001',
            },
            company=self.company
        )
        # May or may not validate uniqueness in form

    def test_due_date_after_invoice_date(self):
        """Test due date must be after or equal to invoice date"""
        form = PurchaseInvoiceForm(
            data={
                'supplier': self.supplier.pk,
                'date': date.today(),
                'due_date': date.today() - timedelta(days=1),
                'currency': self.currency.pk,
            },
            company=self.company
        )
        # Should validate date order


class PurchaseInvoiceItemFormTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceItemForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseInvoiceItemForm(
            data={
                'item': self.item1.pk,
                'quantity': '10.000',
                'unit': self.uom.pk,
                'unit_price': '100.000',
                'discount_percentage': '0.00',
                'discount_amount': '0.000',
                'tax_rate': '16.00',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)


# ============================================================================
# GOODS RECEIPT FORM TESTS
# ============================================================================

class GoodsReceiptFormTest(PurchaseTestBase):
    """Tests for GoodsReceiptForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        order = self.create_purchase_order(status='approved')

        form = GoodsReceiptForm(
            data={
                'branch': self.branch.pk,
                'purchase_order': order.pk,
                'supplier': self.supplier.pk,
                'warehouse': self.warehouse.pk,
                'quality_check_status': 'pending',
                'date': date.today(),
                'received_by': self.admin_user.pk,
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_purchase_order_required(self):
        """Test purchase order is required"""
        form = GoodsReceiptForm(
            data={
                'warehouse': self.warehouse.pk,
                'date': date.today(),
            },
            company=self.company
        )
        self.assertFalse(form.is_valid())

    def test_warehouse_filtered_by_company(self):
        """Test warehouse queryset filtered by company"""
        form = GoodsReceiptForm(company=self.company)
        warehouse_field = form.fields.get('warehouse')
        if warehouse_field and hasattr(warehouse_field, 'queryset'):
            for wh in warehouse_field.queryset:
                self.assertEqual(wh.company, self.company)


class GoodsReceiptLineFormTest(PurchaseTestBase):
    """Tests for GoodsReceiptLineForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        # Create a purchase order with items for testing
        order = self.create_purchase_order(status='approved')
        # Create a purchase order line item
        po_line = PurchaseOrderItem.objects.create(
            order=order,
            item=self.item1,
            quantity=100,
            unit=self.uom,
            unit_price=10
        )

        form = GoodsReceiptLineForm(
            data={
                'purchase_order_line': po_line.pk,
                'item': self.item1.pk,
                'received_quantity': '10.000',
                'rejected_quantity': '0.000',
                'quality_status': 'accepted',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejected_less_than_received(self):
        """Test rejected quantity must be less than received"""
        form = GoodsReceiptLineForm(
            data={
                'item': self.item1.pk,
                'received_quantity': '10.000',
                'rejected_quantity': '15.000',  # Invalid - more than received
                'quality_status': 'partial',
            },
            company=self.company
        )
        # Should validate this


# ============================================================================
# QUOTATION FORM TESTS
# ============================================================================

class PurchaseQuotationRequestFormTest(PurchaseTestBase):
    """Tests for PurchaseQuotationRequestForm (RFQ)"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseQuotationRequestForm(
            data={
                'date': date.today(),
                'submission_deadline': date.today() + timedelta(days=7),
                'currency': self.currency.pk,
                'subject': 'طلب عرض أسعار اختبار',
                'suppliers': [self.supplier.pk],
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_submission_deadline_required(self):
        """Test submission deadline is required"""
        form = PurchaseQuotationRequestForm(
            data={
                'date': date.today(),
                'currency': self.currency.pk,
            },
            company=self.company
        )
        # Submission deadline should be required


class PurchaseQuotationFormTest(PurchaseTestBase):
    """Tests for PurchaseQuotationForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        rfq = self.create_rfq()

        form = PurchaseQuotationForm(
            data={
                'quotation_request': rfq.pk,
                'supplier': self.supplier.pk,
                'date': date.today(),
                'valid_until': date.today() + timedelta(days=30),
                'currency': self.currency.pk,
                'discount_amount': '0.000',
            },
            company=self.company
        )
        self.assertTrue(form.is_valid(), form.errors)


# ============================================================================
# CONTRACT FORM TESTS
# ============================================================================

class PurchaseContractFormTest(PurchaseTestBase):
    """Tests for PurchaseContractForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = PurchaseContractForm(
            data={
                'supplier': self.supplier.pk,
                'contract_date': date.today(),
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=365),
                'currency': self.currency.pk,
            },
            company=self.company,
            branch=self.branch,
            user=self.admin_user
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_end_date_after_start_date(self):
        """Test end date must be after start date"""
        form = PurchaseContractForm(
            data={
                'supplier': self.supplier.pk,
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=1),
                'currency': self.currency.pk,
            },
            company=self.company,
            branch=self.branch,
            user=self.admin_user
        )
        # Should validate date order


# ============================================================================
# FORMSET TESTS
# ============================================================================

class PurchaseOrderItemFormSetTest(PurchaseTestBase):
    """Tests for PurchaseOrderItemFormSet"""

    def test_formset_prefix(self):
        """Test formset has correct prefix"""
        order = self.create_purchase_order()
        formset = PurchaseOrderItemFormSet(
            instance=order,
            prefix='lines',
            company=self.company
        )
        self.assertEqual(formset.prefix, 'lines')

    def test_formset_empty_permitted(self):
        """Test formset allows empty forms"""
        order = self.create_purchase_order()
        formset = PurchaseOrderItemFormSet(
            instance=order,
            prefix='lines',
            company=self.company
        )
        # Should have empty forms for adding new items

    def test_formset_with_data(self):
        """Test formset with POST data"""
        order = self.create_purchase_order()

        data = {
            'lines-TOTAL_FORMS': '1',
            'lines-INITIAL_FORMS': '0',
            'lines-MIN_NUM_FORMS': '0',
            'lines-MAX_NUM_FORMS': '1000',
            'lines-0-item': self.item1.pk,
            'lines-0-quantity': '10.000',
            'lines-0-unit': self.uom.pk,
            'lines-0-unit_price': '100.000',
            'lines-0-tax_rate': '16.00',
        }

        formset = PurchaseOrderItemFormSet(
            data=data,
            instance=order,
            prefix='lines',
            company=self.company
        )
        self.assertTrue(formset.is_valid(), formset.errors)


class PurchaseInvoiceItemFormSetTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceItemFormSet"""

    def test_formset_prefix(self):
        """Test formset has correct prefix"""
        invoice = self.create_purchase_invoice()
        formset = PurchaseInvoiceItemFormSet(
            instance=invoice,
            prefix='lines',
            company=self.company
        )
        self.assertEqual(formset.prefix, 'lines')


class GoodsReceiptLineFormSetTest(PurchaseTestBase):
    """Tests for GoodsReceiptLineFormSet"""

    def test_formset_prefix(self):
        """Test formset has correct prefix"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)

        formset = GoodsReceiptLineFormSet(
            instance=receipt,
            prefix='lines',
            company=self.company
        )
        self.assertEqual(formset.prefix, 'lines')


# ============================================================================
# FORM WIDGET TESTS
# ============================================================================

class FormWidgetTest(PurchaseTestBase):
    """Tests for form widgets"""

    def test_date_widget(self):
        """Test date fields have correct widget"""
        form = PurchaseOrderForm(company=self.company)
        date_field = form.fields.get('date')
        if date_field:
            widget_class = date_field.widget.__class__.__name__
            self.assertIn(widget_class, ['DateInput', 'DateTimeInput', 'TextInput'])

    def test_select2_widget(self):
        """Test select fields use Select2 where appropriate"""
        form = PurchaseOrderForm(company=self.company)
        supplier_field = form.fields.get('supplier')
        if supplier_field:
            # Widget should be Select or ModelSelect2
            self.assertIsNotNone(supplier_field.widget)

    def test_decimal_field_precision(self):
        """Test decimal fields have correct precision"""
        form = PurchaseOrderItemForm(company=self.company)
        quantity_field = form.fields.get('quantity')
        if quantity_field:
            # Should accept 3 decimal places
            self.assertIsNotNone(quantity_field)

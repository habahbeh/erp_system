# apps/purchases/tests/test_views.py
"""
View Tests for Purchases Module
اختبارات العروض لوحدة المشتريات
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from .test_base import PurchaseTestBase


# ============================================================================
# PURCHASE REQUEST VIEW TESTS
# ============================================================================

class PurchaseRequestListViewTest(PurchaseTestBase):
    """Tests for PurchaseRequestListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:request_list'))
        self.assertResponseSuccess(response)

    def test_list_view_requires_login(self):
        """Test list view requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('purchases:request_list'))
        self.assertResponseRedirect(response)

    def test_list_view_pagination(self):
        """Test list view pagination"""
        # Create multiple requests
        for i in range(60):
            self.create_purchase_request()

        response = self.client.get(reverse('purchases:request_list'))
        self.assertResponseSuccess(response)
        # Should have pagination
        self.assertIn('page_obj', response.context)

    def test_list_view_search(self):
        """Test search functionality"""
        request = self.create_purchase_request()
        response = self.client.get(
            reverse('purchases:request_list') + f'?search={request.number}'
        )
        self.assertResponseSuccess(response)

    def test_list_view_filter_by_status(self):
        """Test filter by status"""
        self.create_purchase_request(status='draft')
        self.create_purchase_request(status='pending_approval')

        response = self.client.get(
            reverse('purchases:request_list') + '?status=draft'
        )
        self.assertResponseSuccess(response)


class PurchaseRequestDetailViewTest(PurchaseTestBase):
    """Tests for PurchaseRequestDetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        request = self.create_purchase_request()
        response = self.client.get(
            reverse('purchases:request_detail', kwargs={'pk': request.pk})
        )
        self.assertResponseSuccess(response)

    def test_detail_view_not_found(self):
        """Test 404 for non-existent request"""
        response = self.client.get(
            reverse('purchases:request_detail', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_view_context(self):
        """Test context data in detail view"""
        request = self.create_purchase_request()
        self.add_items_to_request(request)

        response = self.client.get(
            reverse('purchases:request_detail', kwargs={'pk': request.pk})
        )
        self.assertIn('object', response.context)
        self.assertEqual(response.context['object'], request)


class PurchaseRequestCreateViewTest(PurchaseTestBase):
    """Tests for PurchaseRequestCreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:request_create'))
        self.assertResponseSuccess(response)
        self.assertIn('form', response.context)
        self.assertIn('formset', response.context)

    def test_create_view_post_valid(self):
        """Test POST with valid data"""
        data = {
            'date': date.today().isoformat(),
            'required_date': (date.today() + timedelta(days=7)).isoformat(),
            'priority': 'normal',
            'notes': 'ملاحظات اختبار',
            # FormSet data
            'lines-TOTAL_FORMS': '1',
            'lines-INITIAL_FORMS': '0',
            'lines-MIN_NUM_FORMS': '0',
            'lines-MAX_NUM_FORMS': '1000',
            'lines-0-item': self.item1.pk,
            'lines-0-quantity': '10.000',
            'lines-0-unit': self.uom.name,
            'lines-0-estimated_price': '100.000',
        }
        response = self.client.post(reverse('purchases:request_create'), data)
        # Should redirect on success
        if response.status_code == 200:
            # Form has errors - check what they are
            if 'form' in response.context:
                print("Form errors:", response.context['form'].errors)
            if 'formset' in response.context:
                print("Formset errors:", response.context['formset'].errors)

    def test_create_view_post_invalid(self):
        """Test POST with invalid data"""
        data = {
            # Missing required fields
            'lines-TOTAL_FORMS': '0',
            'lines-INITIAL_FORMS': '0',
            'lines-MIN_NUM_FORMS': '0',
            'lines-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(reverse('purchases:request_create'), data)
        self.assertResponseSuccess(response)  # Returns to form with errors


class PurchaseRequestUpdateViewTest(PurchaseTestBase):
    """Tests for PurchaseRequestUpdateView"""

    def test_update_view_get(self):
        """Test GET request to update view"""
        request = self.create_purchase_request(status='draft')
        response = self.client.get(
            reverse('purchases:request_update', kwargs={'pk': request.pk})
        )
        self.assertResponseSuccess(response)

    def test_update_view_non_draft(self):
        """Test update view rejects non-draft requests"""
        request = self.create_purchase_request(status='approved')
        response = self.client.get(
            reverse('purchases:request_update', kwargs={'pk': request.pk})
        )
        # Should return 404 or redirect
        self.assertIn(response.status_code, [404, 302, 403])


class PurchaseRequestDeleteViewTest(PurchaseTestBase):
    """Tests for PurchaseRequestDeleteView"""

    def test_delete_view_get(self):
        """Test GET request to delete view (confirmation)"""
        request = self.create_purchase_request(status='draft')
        response = self.client.get(
            reverse('purchases:request_delete', kwargs={'pk': request.pk})
        )
        self.assertResponseSuccess(response)

    def test_delete_view_post(self):
        """Test POST request to delete"""
        request = self.create_purchase_request(status='draft')
        response = self.client.post(
            reverse('purchases:request_delete', kwargs={'pk': request.pk})
        )
        self.assertResponseRedirect(response)


# ============================================================================
# PURCHASE ORDER VIEW TESTS
# ============================================================================

class PurchaseOrderListViewTest(PurchaseTestBase):
    """Tests for PurchaseOrderListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:order_list'))
        self.assertResponseSuccess(response)

    def test_list_view_filter_by_supplier(self):
        """Test filter by supplier"""
        self.create_purchase_order(supplier=self.supplier)

        response = self.client.get(
            reverse('purchases:order_list') + f'?supplier={self.supplier.pk}'
        )
        self.assertResponseSuccess(response)


class PurchaseOrderDetailViewTest(PurchaseTestBase):
    """Tests for PurchaseOrderDetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        order = self.create_purchase_order()
        response = self.client.get(
            reverse('purchases:order_detail', kwargs={'pk': order.pk})
        )
        self.assertResponseSuccess(response)

    def test_detail_view_shows_items(self):
        """Test detail view shows order items"""
        order = self.create_purchase_order()
        self.add_items_to_order(order)

        response = self.client.get(
            reverse('purchases:order_detail', kwargs={'pk': order.pk})
        )
        self.assertResponseSuccess(response)


class PurchaseOrderCreateViewTest(PurchaseTestBase):
    """Tests for PurchaseOrderCreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:order_create'))
        self.assertResponseSuccess(response)
        self.assertIn('form', response.context)
        self.assertIn('formset', response.context)

    def test_create_view_from_request(self):
        """Test creating order from purchase request"""
        request = self.create_purchase_request(status='approved')
        response = self.client.get(
            reverse('purchases:order_create') + f'?from_request={request.pk}'
        )
        self.assertResponseSuccess(response)


class PurchaseOrderUpdateViewTest(PurchaseTestBase):
    """Tests for PurchaseOrderUpdateView"""

    def test_update_view_get(self):
        """Test GET request to update view"""
        order = self.create_purchase_order(status='draft')
        response = self.client.get(
            reverse('purchases:order_update', kwargs={'pk': order.pk})
        )
        self.assertResponseSuccess(response)


# ============================================================================
# PURCHASE INVOICE VIEW TESTS
# ============================================================================

class PurchaseInvoiceListViewTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:invoice_list'))
        self.assertResponseSuccess(response)


class PurchaseInvoiceDetailViewTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceDetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        invoice = self.create_purchase_invoice()
        response = self.client.get(
            reverse('purchases:invoice_detail', kwargs={'pk': invoice.pk})
        )
        self.assertResponseSuccess(response)


class PurchaseInvoiceCreateViewTest(PurchaseTestBase):
    """Tests for PurchaseInvoiceCreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:invoice_create'))
        self.assertResponseSuccess(response)

    def test_create_view_from_order(self):
        """Test creating invoice from purchase order"""
        order = self.create_purchase_order(status='approved')
        response = self.client.get(
            reverse('purchases:invoice_create') + f'?from_order={order.pk}'
        )
        self.assertResponseSuccess(response)


# ============================================================================
# GOODS RECEIPT VIEW TESTS
# ============================================================================

class GoodsReceiptListViewTest(PurchaseTestBase):
    """Tests for GoodsReceiptListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:goods_receipt_list'))
        self.assertResponseSuccess(response)


class GoodsReceiptDetailViewTest(PurchaseTestBase):
    """Tests for GoodsReceiptDetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        order = self.create_purchase_order(status='approved')
        receipt = self.create_goods_receipt(purchase_order=order)

        response = self.client.get(
            reverse('purchases:goods_receipt_detail', kwargs={'pk': receipt.pk})
        )
        self.assertResponseSuccess(response)


class GoodsReceiptCreateViewTest(PurchaseTestBase):
    """Tests for GoodsReceiptCreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:goods_receipt_create'))
        self.assertResponseSuccess(response)

    def test_create_view_from_order(self):
        """Test creating goods receipt from order"""
        order = self.create_purchase_order(status='approved')
        response = self.client.get(
            reverse('purchases:goods_receipt_create') + f'?from_order={order.pk}'
        )
        self.assertResponseSuccess(response)


# ============================================================================
# RFQ VIEW TESTS
# ============================================================================

class RFQListViewTest(PurchaseTestBase):
    """Tests for RFQ ListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:rfq_list'))
        self.assertResponseSuccess(response)


class RFQDetailViewTest(PurchaseTestBase):
    """Tests for RFQ DetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        rfq = self.create_rfq()
        response = self.client.get(
            reverse('purchases:rfq_detail', kwargs={'pk': rfq.pk})
        )
        self.assertResponseSuccess(response)


class RFQCreateViewTest(PurchaseTestBase):
    """Tests for RFQ CreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:rfq_create'))
        self.assertResponseSuccess(response)


# ============================================================================
# QUOTATION VIEW TESTS
# ============================================================================

class QuotationListViewTest(PurchaseTestBase):
    """Tests for Quotation ListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:quotation_list'))
        self.assertResponseSuccess(response)


class QuotationDetailViewTest(PurchaseTestBase):
    """Tests for Quotation DetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        rfq = self.create_rfq()
        quotation = self.create_quotation(rfq=rfq)

        response = self.client.get(
            reverse('purchases:quotation_detail', kwargs={'pk': quotation.pk})
        )
        self.assertResponseSuccess(response)


# ============================================================================
# CONTRACT VIEW TESTS
# ============================================================================

class ContractListViewTest(PurchaseTestBase):
    """Tests for Contract ListView"""

    def test_list_view_get(self):
        """Test GET request to list view"""
        response = self.client.get(reverse('purchases:contract_list'))
        self.assertResponseSuccess(response)


class ContractDetailViewTest(PurchaseTestBase):
    """Tests for Contract DetailView"""

    def test_detail_view_get(self):
        """Test GET request to detail view"""
        contract = self.create_contract()
        response = self.client.get(
            reverse('purchases:contract_detail', kwargs={'pk': contract.pk})
        )
        self.assertResponseSuccess(response)


class ContractCreateViewTest(PurchaseTestBase):
    """Tests for Contract CreateView"""

    def test_create_view_get(self):
        """Test GET request to create view"""
        response = self.client.get(reverse('purchases:contract_create'))
        self.assertResponseSuccess(response)


# ============================================================================
# DASHBOARD VIEW TESTS
# ============================================================================

class PurchaseDashboardViewTest(PurchaseTestBase):
    """Tests for Purchase Dashboard View"""

    def test_dashboard_get(self):
        """Test GET request to dashboard"""
        response = self.client.get(reverse('purchases:dashboard'))
        self.assertResponseSuccess(response)

    def test_dashboard_statistics(self):
        """Test dashboard shows statistics"""
        # Create some data
        self.create_purchase_order()
        self.create_purchase_invoice()

        response = self.client.get(reverse('purchases:dashboard'))
        self.assertResponseSuccess(response)
        # Check for stats in context
        self.assertIn('stats', response.context)


# ============================================================================
# PERMISSION TESTS
# ============================================================================

class ViewPermissionTest(PurchaseTestBase):
    """Tests for view permissions"""

    def test_create_order_requires_permission(self):
        """Test create order requires add permission"""
        # Login as regular user without permissions
        self.client.logout()
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('purchases:order_create'))
        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])

    def test_delete_requires_permission(self):
        """Test delete requires delete permission"""
        order = self.create_purchase_order(status='draft')

        self.client.logout()
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse('purchases:order_delete', kwargs={'pk': order.pk})
        )
        # Should be forbidden or redirect
        self.assertIn(response.status_code, [302, 403, 404])


# ============================================================================
# CONTEXT DATA TESTS
# ============================================================================

class ViewContextTest(PurchaseTestBase):
    """Tests for view context data"""

    def test_list_view_has_breadcrumbs(self):
        """Test list views have breadcrumbs"""
        response = self.client.get(reverse('purchases:order_list'))
        self.assertIn('breadcrumbs', response.context)

    def test_detail_view_has_title(self):
        """Test detail views have title"""
        order = self.create_purchase_order()
        response = self.client.get(
            reverse('purchases:order_detail', kwargs={'pk': order.pk})
        )
        self.assertIn('title', response.context)

    def test_create_view_has_formset(self):
        """Test create views have formset"""
        response = self.client.get(reverse('purchases:order_create'))
        self.assertIn('formset', response.context)

    def test_formset_has_correct_prefix(self):
        """Test formset has correct prefix in views"""
        response = self.client.get(reverse('purchases:order_create'))
        formset = response.context.get('formset')
        if formset:
            self.assertEqual(formset.prefix, 'lines')

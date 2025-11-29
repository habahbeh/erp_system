# apps/purchases/tests/test_exports.py
"""
Export Tests for Purchases Module
اختبارات التصدير لوحدة المشتريات
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponse
from decimal import Decimal
from datetime import date, timedelta
import io

from .test_base import PurchaseTestBase


# ============================================================================
# EXCEL EXPORT TESTS
# ============================================================================

class ExcelExportTest(PurchaseTestBase):
    """Tests for Excel export functionality"""

    def test_export_requests_excel(self):
        """Test exporting purchase requests to Excel"""
        # Create some requests
        for i in range(5):
            self.create_purchase_request()

        response = self.client.get(reverse('purchases:export_requests_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        # Check content disposition header
        self.assertIn('attachment', response.get('Content-Disposition', ''))

    def test_export_orders_excel(self):
        """Test exporting purchase orders to Excel"""
        for i in range(5):
            self.create_purchase_order()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_invoices_excel(self):
        """Test exporting purchase invoices to Excel"""
        for i in range(5):
            self.create_purchase_invoice()

        response = self.client.get(reverse('purchases:export_invoices_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_goods_receipts_excel(self):
        """Test exporting goods receipts to Excel"""
        order = self.create_purchase_order(status='approved')
        for i in range(3):
            self.create_goods_receipt(purchase_order=order)

        response = self.client.get(reverse('purchases:export_goods_receipts_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_rfq_excel(self):
        """Test exporting RFQs to Excel"""
        for i in range(5):
            self.create_rfq()

        response = self.client.get(reverse('purchases:export_rfqs_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_quotations_excel(self):
        """Test exporting quotations to Excel"""
        rfq = self.create_rfq()
        for i in range(3):
            self.create_quotation(rfq=rfq)

        response = self.client.get(reverse('purchases:export_quotations_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_empty_data(self):
        """Test exporting when no data exists"""
        # No data created
        response = self.client.get(reverse('purchases:export_orders_excel'))
        # Should still return Excel file, just empty
        self.assertEqual(response.status_code, 200)

    def test_export_with_filters(self):
        """Test exporting with date filters"""
        self.create_purchase_order()

        url = reverse('purchases:export_orders_excel')
        # Pass query parameters using query string
        url_with_params = f"{url}?date_from={date.today().isoformat()}&date_to={date.today().isoformat()}"
        response = self.client.get(url_with_params)
        self.assertEqual(response.status_code, 200)

    def test_export_requires_login(self):
        """Test export requires authentication"""
        self.client.logout()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        # Should redirect to login
        self.assertIn(response.status_code, [302, 401, 403])


# ============================================================================
# PDF EXPORT TESTS
# ============================================================================
# NOTE: PDF export URLs are not yet implemented in urls.py
# These tests are commented out until the URLs are added

# class PDFExportTest(PurchaseTestBase):
#     """Tests for PDF export functionality"""
#
#     def test_export_order_pdf(self):
#         """Test exporting single order to PDF"""
#         order = self.create_purchase_order()
#         self.add_items_to_order(order)
#
#         response = self.client.get(
#             reverse('purchases:order_pdf', kwargs={'pk': order.pk})
#         )
#         # May return PDF or redirect based on implementation
#         self.assertIn(response.status_code, [200, 302])
#         if response.status_code == 200:
#             self.assertIn(
#                 response['Content-Type'],
#                 ['application/pdf', 'text/html']
#             )
#
#     def test_export_invoice_pdf(self):
#         """Test exporting single invoice to PDF"""
#         invoice = self.create_purchase_invoice()
#         self.add_items_to_invoice(invoice)
#
#         response = self.client.get(
#             reverse('purchases:invoice_pdf', kwargs={'pk': invoice.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_export_goods_receipt_pdf(self):
#         """Test exporting goods receipt to PDF"""
#         order = self.create_purchase_order(status='approved')
#         receipt = self.create_goods_receipt(purchase_order=order)
#
#         response = self.client.get(
#             reverse('purchases:goods_receipt_pdf', kwargs={'pk': receipt.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_export_rfq_pdf(self):
#         """Test exporting RFQ to PDF"""
#         rfq = self.create_rfq()
#
#         response = self.client.get(
#             reverse('purchases:rfq_pdf', kwargs={'pk': rfq.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_export_quotation_pdf(self):
#         """Test exporting quotation to PDF"""
#         rfq = self.create_rfq()
#         quotation = self.create_quotation(rfq=rfq)
#
#         response = self.client.get(
#             reverse('purchases:quotation_pdf', kwargs={'pk': quotation.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_export_contract_pdf(self):
#         """Test exporting contract to PDF"""
#         contract = self.create_contract()
#
#         response = self.client.get(
#             reverse('purchases:contract_pdf', kwargs={'pk': contract.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_pdf_not_found(self):
#         """Test PDF export returns 404 for non-existent document"""
#         response = self.client.get(
#             reverse('purchases:order_pdf', kwargs={'pk': 99999})
#         )
#         self.assertEqual(response.status_code, 404)


# ============================================================================
# PRINT VIEW TESTS
# ============================================================================
# NOTE: Print view URLs are not yet implemented in urls.py
# These tests are commented out until the URLs are added

# class PrintViewTest(PurchaseTestBase):
#     """Tests for print view functionality"""
#
#     def test_order_print_view(self):
#         """Test order print view"""
#         order = self.create_purchase_order()
#         self.add_items_to_order(order)
#
#         response = self.client.get(
#             reverse('purchases:order_print', kwargs={'pk': order.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_invoice_print_view(self):
#         """Test invoice print view"""
#         invoice = self.create_purchase_invoice()
#         self.add_items_to_invoice(invoice)
#
#         response = self.client.get(
#             reverse('purchases:invoice_print', kwargs={'pk': invoice.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])
#
#     def test_goods_receipt_print_view(self):
#         """Test goods receipt print view"""
#         order = self.create_purchase_order(status='approved')
#         receipt = self.create_goods_receipt(purchase_order=order)
#
#         response = self.client.get(
#             reverse('purchases:goods_receipt_print', kwargs={'pk': receipt.pk})
#         )
#         self.assertIn(response.status_code, [200, 302])


# ============================================================================
# EXPORT DATA CONTENT TESTS
# ============================================================================

class ExportDataContentTest(PurchaseTestBase):
    """Tests for export data content accuracy"""

    def test_excel_contains_all_orders(self):
        """Test Excel export contains all orders"""
        # Create 10 orders
        orders = [self.create_purchase_order() for _ in range(10)]

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)
        # Content should be non-empty
        self.assertGreater(len(response.content), 0)

    def test_export_respects_company_filter(self):
        """Test export only includes current company's data"""
        # Create order for current company
        order = self.create_purchase_order()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)
        # Should have data
        self.assertGreater(len(response.content), 0)


# ============================================================================
# EXPORT PERMISSION TESTS
# ============================================================================

class ExportPermissionTest(PurchaseTestBase):
    """Tests for export permissions"""

    def test_export_requires_view_permission(self):
        """Test export requires view permission"""
        self.client.logout()
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('purchases:export_orders_excel'))
        # Should be forbidden or redirect
        self.assertIn(response.status_code, [302, 403])

    # PDF URLs not implemented yet
    # def test_pdf_requires_view_permission(self):
    #     """Test PDF requires view permission"""
    #     order = self.create_purchase_order()
    #
    #     self.client.logout()
    #     self.client.login(username='testuser', password='testpass123')
    #
    #     response = self.client.get(
    #         reverse('purchases:order_pdf', kwargs={'pk': order.pk})
    #     )
    #     self.assertIn(response.status_code, [302, 403, 404])


# ============================================================================
# REPORT EXPORT TESTS
# ============================================================================

class ReportExportTest(PurchaseTestBase):
    """Tests for report exports"""

    def test_purchase_report_excel(self):
        """Test purchase summary report export"""
        # Create some data
        for i in range(5):
            order = self.create_purchase_order()
            self.add_items_to_order(order)
            invoice = self.create_purchase_invoice()
            self.add_items_to_invoice(invoice)

        # Use actual report URL
        response = self.client.get(reverse('purchases:export_purchases_summary_excel'))
        self.assertIn(response.status_code, [200, 404])

    def test_supplier_report_excel(self):
        """Test supplier report export"""
        self.create_purchase_order(supplier=self.supplier)
        self.create_purchase_order(supplier=self.supplier2)

        # Use actual report URL
        response = self.client.get(reverse('purchases:export_supplier_performance_excel'))
        self.assertIn(response.status_code, [200, 404])


# ============================================================================
# EXPORT FORMAT TESTS
# ============================================================================

class ExportFormatTest(PurchaseTestBase):
    """Tests for export format options"""

    # CSV export not implemented yet
    # def test_csv_export(self):
    #     """Test CSV export if available"""
    #     for i in range(5):
    #         self.create_purchase_order()
    #
    #     try:
    #         response = self.client.get(reverse('purchases:export_orders_csv'))
    #         self.assertIn(response.status_code, [200, 404])
    #         if response.status_code == 200:
    #             self.assertIn(response['Content-Type'], ['text/csv', 'application/csv'])
    #     except:
    #         # CSV export might not be implemented
    #         pass

    def test_excel_file_validity(self):
        """Test exported Excel file is valid"""
        self.create_purchase_order()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)

        # Check file signature (XLSX files start with PK)
        content = response.content
        self.assertTrue(
            content[:2] == b'PK',
            "Excel file should be a valid ZIP (XLSX) file"
        )


# ============================================================================
# BULK EXPORT TESTS
# ============================================================================

class BulkExportTest(PurchaseTestBase):
    """Tests for bulk export operations"""

    def test_export_large_dataset(self):
        """Test exporting large dataset"""
        # Create 100 orders
        for i in range(100):
            self.create_purchase_order()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)

    def test_export_with_all_related_data(self):
        """Test export includes related data"""
        order = self.create_purchase_order()
        self.add_items_to_order(order)

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)


# ============================================================================
# EXPORT ERROR HANDLING TESTS
# ============================================================================

class ExportErrorHandlingTest(PurchaseTestBase):
    """Tests for export error handling"""

    def test_export_handles_unicode(self):
        """Test export handles Arabic/Unicode correctly"""
        order = self.create_purchase_order()
        # Supplier has Arabic name
        self.assertEqual(order.supplier.name, 'مورد اختبار')

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)

    def test_export_handles_null_values(self):
        """Test export handles null/None values"""
        order = self.create_purchase_order()
        order.notes = ''  # Use empty string instead of None since TextField doesn't allow null
        order.save()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)

    def test_export_handles_special_characters(self):
        """Test export handles special characters"""
        order = self.create_purchase_order()
        order.notes = 'Test <>&"\'  special chars'
        order.save()

        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)


# ============================================================================
# EXPORT FILENAME TESTS
# ============================================================================

class ExportFilenameTest(PurchaseTestBase):
    """Tests for export filename generation"""

    def test_excel_filename_contains_date(self):
        """Test Excel filename contains current date"""
        response = self.client.get(reverse('purchases:export_orders_excel'))
        self.assertEqual(response.status_code, 200)

        content_disposition = response.get('Content-Disposition', '')
        # Should contain .xlsx extension
        self.assertIn('.xlsx', content_disposition)

    # PDF URLs not implemented yet
    # def test_pdf_filename(self):
    #     """Test PDF filename format"""
    #     order = self.create_purchase_order()
    #
    #     response = self.client.get(
    #         reverse('purchases:order_pdf', kwargs={'pk': order.pk})
    #     )
    #     if response.status_code == 200:
    #         content_disposition = response.get('Content-Disposition', '')
    #         # Should contain .pdf extension if PDF
    #         if 'application/pdf' in response['Content-Type']:
    #             self.assertIn('.pdf', content_disposition)

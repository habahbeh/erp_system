# apps/core/tests/test_pricing_views.py
"""
Tests for Pricing Views
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.core.models import (
    Company, Branch, Currency, PricingRule, PriceList,
    Item, ItemCategory, UnitOfMeasure
)

User = get_user_model()


class PricingRuleViewsTestCase(TestCase):
    """Test cases for Pricing Rule views"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create currency
        cls.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_active=True
        )

        # Create company
        cls.company = Company.objects.create(
            name='Test Company',
            name_en='Test Company',
            currency=cls.currency
        )

        # Create branch
        cls.branch = Branch.objects.create(
            name='Main Branch',
            company=cls.company,
            is_active=True
        )

        # Create user
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            company=cls.company
        )

        # Create UoM
        cls.uom = UnitOfMeasure.objects.create(
            name='Piece',
            code='PCS',
            company=cls.company
        )

        # Create category
        cls.category = ItemCategory.objects.create(
            name='Test Category',
            code='CAT01',
            company=cls.company
        )

        # Create item
        cls.item = Item.objects.create(
            name='Test Item',
            code='ITEM01',
            company=cls.company,
            category=cls.category,
            base_uom=cls.uom,
            currency=cls.currency
        )

        # Create price list
        cls.price_list = PriceList.objects.create(
            name='Standard',
            code='STD',
            company=cls.company,
            currency=cls.currency
        )

        # Create pricing rule
        cls.pricing_rule = PricingRule.objects.create(
            name='Test Rule',
            code='RULE01',
            company=cls.company,
            rule_type='MARKUP_PERCENTAGE',
            percentage_value=Decimal('10.00'),
            priority=10,
            is_active=True
        )

    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Set session variables
        session = self.client.session
        session['company_id'] = self.company.id
        session['branch_id'] = self.branch.id
        session.save()

    def test_pricing_rule_list_view(self):
        """Test pricing rule list view"""
        url = reverse('core:pricing_rule_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/rule_list.html')
        self.assertContains(response, 'Test Rule')

    def test_pricing_rule_detail_view(self):
        """Test pricing rule detail view"""
        url = reverse('core:pricing_rule_detail', args=[self.pricing_rule.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/rule_detail.html')
        self.assertContains(response, 'Test Rule')
        self.assertContains(response, '10.00')

    def test_pricing_rule_create_view_get(self):
        """Test pricing rule create view GET request"""
        url = reverse('core:pricing_rule_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/rule_form.html')

    def test_pricing_rule_create_view_post(self):
        """Test pricing rule create view POST request"""
        url = reverse('core:pricing_rule_create')
        data = {
            'name': 'New Rule',
            'code': 'NEW01',
            'rule_type': 'DISCOUNT_PERCENTAGE',
            'percentage_value': '5.00',
            'priority': 5,
            'is_active': True
        }
        response = self.client.post(url, data)

        # Should redirect to detail view
        self.assertEqual(response.status_code, 302)

        # Check rule was created
        self.assertTrue(
            PricingRule.objects.filter(code='NEW01').exists()
        )

    def test_pricing_rule_update_view(self):
        """Test pricing rule update view"""
        url = reverse('core:pricing_rule_update', args=[self.pricing_rule.pk])
        data = {
            'name': 'Updated Rule',
            'code': 'RULE01',
            'rule_type': 'MARKUP_PERCENTAGE',
            'percentage_value': '15.00',
            'priority': 10,
            'is_active': True
        }
        response = self.client.post(url, data)

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Check rule was updated
        self.pricing_rule.refresh_from_db()
        self.assertEqual(self.pricing_rule.name, 'Updated Rule')
        self.assertEqual(self.pricing_rule.percentage_value, Decimal('15.00'))

    def test_pricing_rule_delete_view(self):
        """Test pricing rule delete view"""
        url = reverse('core:pricing_rule_delete', args=[self.pricing_rule.pk])
        response = self.client.post(url)

        # Should redirect to list
        self.assertEqual(response.status_code, 302)

        # Check rule was deleted
        self.assertFalse(
            PricingRule.objects.filter(pk=self.pricing_rule.pk).exists()
        )

    def test_pricing_rule_test_view_get(self):
        """Test pricing rule test view GET request"""
        url = reverse('core:pricing_rule_test', args=[self.pricing_rule.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/rule_test.html')

    def test_pricing_rule_test_view_post(self):
        """Test pricing rule test view POST request"""
        url = reverse('core:pricing_rule_test', args=[self.pricing_rule.pk])
        data = {
            'pricing_rule': self.pricing_rule.pk,
            'item': self.item.pk,
            'quantity': '1',
            'cost_price': '100.00'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        # Should show result
        self.assertContains(response, 'نتيجة الاختبار')

    def test_pricing_rule_clone_view(self):
        """Test pricing rule clone view"""
        url = reverse('core:pricing_rule_clone', args=[self.pricing_rule.pk])
        response = self.client.get(url)

        # Should redirect to update view of new rule
        self.assertEqual(response.status_code, 302)

        # Check new rule was created
        cloned_rules = PricingRule.objects.filter(
            name__contains='نسخة'
        )
        self.assertTrue(cloned_rules.exists())


class BulkPriceUpdateViewTestCase(TestCase):
    """Test cases for Bulk Price Update view"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create currency
        cls.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_active=True
        )

        # Create company
        cls.company = Company.objects.create(
            name='Test Company',
            name_en='Test Company',
            currency=cls.currency
        )

        # Create branch
        cls.branch = Branch.objects.create(
            name='Main Branch',
            company=cls.company,
            is_active=True
        )

        # Create user
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            company=cls.company
        )

        # Create UoM
        cls.uom = UnitOfMeasure.objects.create(
            name='Piece',
            code='PCS',
            company=cls.company
        )

        # Create category
        cls.category = ItemCategory.objects.create(
            name='Test Category',
            code='CAT01',
            company=cls.company
        )

        # Create items
        for i in range(5):
            Item.objects.create(
                name=f'Test Item {i}',
                code=f'ITEM{i:02d}',
                company=cls.company,
                category=cls.category,
                base_uom=cls.uom,
                currency=cls.currency
            )

        # Create price list
        cls.price_list = PriceList.objects.create(
            name='Standard',
            code='STD',
            company=cls.company,
            currency=cls.currency
        )

    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Set session variables
        session = self.client.session
        session['company_id'] = self.company.id
        session['branch_id'] = self.branch.id
        session.save()

    def test_bulk_price_update_view_get(self):
        """Test bulk price update view GET request"""
        url = reverse('core:bulk_price_update')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/bulk_update.html')

    def test_bulk_price_update_preview(self):
        """Test bulk price update in preview mode"""
        url = reverse('core:bulk_price_update')
        data = {
            'operation_type': 'PERCENTAGE_CHANGE',
            'percentage_change': '10',
            'categories': [self.category.pk],
            'apply_changes': False  # Preview mode
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        # Should show preview
        self.assertContains(response, 'معاينة')


class PriceSimulatorViewTestCase(TestCase):
    """Test cases for Price Simulator view"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data - similar to above"""
        cls.currency = Currency.objects.create(
            code='USD', name='US Dollar', symbol='$', is_active=True
        )
        cls.company = Company.objects.create(
            name='Test Company', name_en='Test Company', currency=cls.currency
        )
        cls.branch = Branch.objects.create(
            name='Main Branch', company=cls.company, is_active=True
        )
        cls.user = User.objects.create_user(
            username='testuser', password='testpass123', company=cls.company
        )

    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        session = self.client.session
        session['company_id'] = self.company.id
        session['branch_id'] = self.branch.id
        session.save()

    def test_price_simulator_view_get(self):
        """Test price simulator view GET request"""
        url = reverse('core:price_simulator')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/simulator.html')


class PriceComparisonViewTestCase(TestCase):
    """Test cases for Price Comparison view"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.currency = Currency.objects.create(
            code='USD', name='US Dollar', symbol='$', is_active=True
        )
        cls.company = Company.objects.create(
            name='Test Company', name_en='Test Company', currency=cls.currency
        )
        cls.branch = Branch.objects.create(
            name='Main Branch', company=cls.company, is_active=True
        )
        cls.user = User.objects.create_user(
            username='testuser', password='testpass123', company=cls.company
        )

    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        session = self.client.session
        session['company_id'] = self.company.id
        session['branch_id'] = self.branch.id
        session.save()

    def test_price_comparison_view_get(self):
        """Test price comparison view GET request"""
        url = reverse('core:price_comparison')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/comparison.html')


class PriceReportViewTestCase(TestCase):
    """Test cases for Price Report view"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.currency = Currency.objects.create(
            code='USD', name='US Dollar', symbol='$', is_active=True
        )
        cls.company = Company.objects.create(
            name='Test Company', name_en='Test Company', currency=cls.currency
        )
        cls.branch = Branch.objects.create(
            name='Main Branch', company=cls.company, is_active=True
        )
        cls.user = User.objects.create_user(
            username='testuser', password='testpass123', company=cls.company
        )

    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        session = self.client.session
        session['company_id'] = self.company.id
        session['branch_id'] = self.branch.id
        session.save()

    def test_price_report_view_get(self):
        """Test price report view GET request"""
        url = reverse('core:price_report')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/pricing/report.html')

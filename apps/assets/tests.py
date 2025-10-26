# apps/assets/tests.py
"""
Tests شاملة لتطبيق الأصول الثابتة
Test Coverage: Models, Views, Forms, Utils, Signals
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import json

from .models import (
    AssetCategory, DepreciationMethod, AssetCondition, Asset,
    AssetDepreciation, AssetTransaction, AssetTransfer,
    MaintenanceType, MaintenanceSchedule, AssetMaintenance,
    PhysicalCountCycle, PhysicalCount, PhysicalCountLine,
    InsuranceCompany, AssetInsurance, InsuranceClaim,
    AssetLease, LeasePayment,
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest,
)
from .forms import (
    AssetCategoryForm, AssetForm, AssetTransactionForm,
    MaintenanceScheduleForm, ApprovalWorkflowForm,
)
from .utils import DepreciationCalculator

User = get_user_model()


# ==================== Model Tests ====================

class AssetCategoryModelTest(TestCase):
    """
    اختبارات نموذج فئة الأصول
    """

    def setUp(self):
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line',
            rate_percentage=Decimal('10.00')
        )

    def test_create_asset_category(self):
        """اختبار إنشاء فئة أصل"""
        category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة حاسب',
            depreciation_method=self.depreciation_method,
            useful_life_years=5
        )
        self.assertEqual(str(category), 'CAT001 - أجهزة حاسب')
        self.assertTrue(category.is_active)

    def test_parent_child_relationship(self):
        """اختبار العلاقة بين الفئات الرئيسية والفرعية"""
        parent = AssetCategory.objects.create(
            code='PARENT',
            name='فئة رئيسية',
            depreciation_method=self.depreciation_method
        )
        child = AssetCategory.objects.create(
            code='CHILD',
            name='فئة فرعية',
            parent=parent,
            depreciation_method=self.depreciation_method
        )
        self.assertEqual(child.parent, parent)


class AssetModelTest(TestCase):
    """
    اختبارات نموذج الأصل
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line',
            rate_percentage=Decimal('10.00')
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة حاسب',
            depreciation_method=self.depreciation_method,
            useful_life_years=5
        )

    def test_create_asset(self):
        """اختبار إنشاء أصل"""
        asset = Asset.objects.create(
            name='لابتوب Dell',
            category=self.category,
            original_cost=Decimal('5000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method,
            useful_life_years=5
        )
        self.assertIsNotNone(asset.asset_number)
        self.assertEqual(asset.status, 'active')
        self.assertEqual(asset.book_value, asset.original_cost)

    def test_book_value_calculation(self):
        """اختبار حساب القيمة الدفترية"""
        asset = Asset.objects.create(
            name='سيارة',
            category=self.category,
            original_cost=Decimal('100000.000'),
            accumulated_depreciation=Decimal('20000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method
        )
        self.assertEqual(asset.book_value, Decimal('80000.000'))

    def test_is_fully_depreciated(self):
        """اختبار فحص الإهلاك الكامل"""
        asset = Asset.objects.create(
            name='أصل قديم',
            category=self.category,
            original_cost=Decimal('10000.000'),
            accumulated_depreciation=Decimal('10000.000'),
            purchase_date=date.today() - timedelta(days=365*5),
            depreciation_method=self.depreciation_method
        )
        self.assertTrue(asset.is_fully_depreciated())


class AssetDepreciationModelTest(TestCase):
    """
    اختبارات نموذج الإهلاك
    """

    def setUp(self):
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line',
            rate_percentage=Decimal('10.00')
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )
        self.asset = Asset.objects.create(
            name='جهاز',
            category=self.category,
            original_cost=Decimal('10000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method,
            useful_life_years=5
        )

    def test_create_depreciation(self):
        """اختبار إنشاء قيد إهلاك"""
        depreciation = AssetDepreciation.objects.create(
            asset=self.asset,
            depreciation_date=date.today(),
            depreciation_amount=Decimal('166.667'),
            calculation_method='straight_line'
        )
        self.assertEqual(depreciation.accumulated_depreciation, Decimal('166.667'))
        self.assertFalse(depreciation.is_posted)


# ==================== Form Tests ====================

class AssetCategoryFormTest(TestCase):
    """
    اختبارات نموذج فئة الأصول
    """

    def setUp(self):
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )

    def test_valid_category_form(self):
        """اختبار نموذج صحيح"""
        form_data = {
            'code': 'CAT001',
            'name': 'أجهزة حاسب',
            'depreciation_method': self.depreciation_method.id,
            'useful_life_years': 5,
            'is_active': True
        }
        form = AssetCategoryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_category_form(self):
        """اختبار نموذج غير صحيح"""
        form_data = {
            'code': '',  # Required field
            'name': 'أجهزة',
        }
        form = AssetCategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)


class AssetFormTest(TestCase):
    """
    اختبارات نموذج الأصل
    """

    def setUp(self):
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )

    def test_valid_asset_form(self):
        """اختبار نموذج صحيح"""
        form_data = {
            'name': 'لابتوب Dell',
            'category': self.category.id,
            'original_cost': '5000.000',
            'purchase_date': date.today().isoformat(),
            'depreciation_method': self.depreciation_method.id,
            'useful_life_years': 5,
            'status': 'active'
        }
        form = AssetForm(data=form_data)
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())


# ==================== View Tests ====================

class AssetViewsTest(TestCase):
    """
    اختبارات عرض الأصول
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )
        self.asset = Asset.objects.create(
            name='جهاز اختبار',
            category=self.category,
            original_cost=Decimal('5000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method
        )

    def test_asset_list_view(self):
        """اختبار عرض قائمة الأصول"""
        response = self.client.get(reverse('assets:asset_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'جهاز اختبار')

    def test_asset_detail_view(self):
        """اختبار عرض تفاصيل الأصل"""
        response = self.client.get(
            reverse('assets:asset_detail', args=[self.asset.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.name)

    def test_asset_create_view(self):
        """اختبار إنشاء أصل جديد"""
        response = self.client.get(reverse('assets:asset_create'))
        self.assertEqual(response.status_code, 200)


class DashboardViewTest(TestCase):
    """
    اختبارات لوحة التحكم
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_view(self):
        """اختبار لوحة التحكم"""
        response = self.client.get(reverse('assets:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة التحكم')


# ==================== Utils Tests ====================

class DepreciationCalculatorTest(TestCase):
    """
    اختبارات حاسبة الإهلاك
    """

    def test_straight_line_calculation(self):
        """اختبار طريقة القسط الثابت"""
        calculator = DepreciationCalculator(
            asset_cost=Decimal('12000.000'),
            salvage_value=Decimal('2000.000'),
            useful_life_years=5,
            method='straight_line'
        )
        annual_depreciation = calculator.calculate_annual_depreciation()
        self.assertEqual(annual_depreciation, Decimal('2000.000'))

    def test_declining_balance_calculation(self):
        """اختبار طريقة الرصيد المتناقص"""
        calculator = DepreciationCalculator(
            asset_cost=Decimal('10000.000'),
            salvage_value=Decimal('1000.000'),
            useful_life_years=5,
            method='declining_balance',
            rate_percentage=Decimal('20.00')
        )
        annual_depreciation = calculator.calculate_annual_depreciation()
        self.assertGreater(annual_depreciation, Decimal('0'))

    def test_monthly_depreciation(self):
        """اختبار حساب الإهلاك الشهري"""
        calculator = DepreciationCalculator(
            asset_cost=Decimal('12000.000'),
            salvage_value=Decimal('0'),
            useful_life_years=5,
            method='straight_line'
        )
        monthly_depreciation = calculator.calculate_monthly_depreciation()
        self.assertEqual(monthly_depreciation, Decimal('200.000'))


# ==================== Integration Tests ====================

class AssetLifecycleTest(TestCase):
    """
    اختبارات دورة حياة الأصل الكاملة
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line',
            rate_percentage=Decimal('10.00')
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )

    def test_complete_asset_lifecycle(self):
        """اختبار دورة حياة كاملة للأصل"""
        # 1. إنشاء الأصل
        asset = Asset.objects.create(
            name='جهاز كامل',
            category=self.category,
            original_cost=Decimal('10000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method,
            useful_life_years=5
        )
        self.assertEqual(asset.status, 'active')

        # 2. حساب الإهلاك
        depreciation = AssetDepreciation.objects.create(
            asset=asset,
            depreciation_date=date.today(),
            depreciation_amount=Decimal('166.667'),
            calculation_method='straight_line'
        )
        asset.accumulated_depreciation = depreciation.depreciation_amount
        asset.save()
        self.assertGreater(asset.accumulated_depreciation, Decimal('0'))

        # 3. إجراء صيانة
        maintenance_type = MaintenanceType.objects.create(
            code='MAINT001',
            name='صيانة دورية'
        )
        maintenance = AssetMaintenance.objects.create(
            asset=asset,
            maintenance_type=maintenance_type,
            scheduled_date=date.today(),
            status='completed',
            labor_cost=Decimal('500.000')
        )
        self.assertEqual(maintenance.status, 'completed')

        # 4. بيع الأصل
        transaction = AssetTransaction.objects.create(
            asset=asset,
            transaction_type='sale',
            transaction_date=date.today(),
            amount=Decimal('8000.000'),
            status='posted'
        )
        asset.status = 'sold'
        asset.save()
        self.assertEqual(asset.status, 'sold')


class MaintenanceWorkflowTest(TestCase):
    """
    اختبارات سير عمل الصيانة
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )
        self.asset = Asset.objects.create(
            name='جهاز للصيانة',
            category=self.category,
            original_cost=Decimal('5000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method
        )
        self.maintenance_type = MaintenanceType.objects.create(
            code='PREV',
            name='صيانة وقائية'
        )

    def test_schedule_maintenance(self):
        """اختبار جدولة الصيانة"""
        schedule = MaintenanceSchedule.objects.create(
            asset=self.asset,
            maintenance_type=self.maintenance_type,
            frequency='monthly',
            next_maintenance_date=date.today() + timedelta(days=30)
        )
        self.assertTrue(schedule.is_active)

    def test_execute_maintenance(self):
        """اختبار تنفيذ الصيانة"""
        maintenance = AssetMaintenance.objects.create(
            asset=self.asset,
            maintenance_type=self.maintenance_type,
            scheduled_date=date.today(),
            status='scheduled'
        )
        # تحديث الحالة
        maintenance.status = 'completed'
        maintenance.actual_end_date = date.today()
        maintenance.labor_cost = Decimal('300.000')
        maintenance.save()
        self.assertEqual(maintenance.status, 'completed')
        self.assertEqual(maintenance.total_cost, Decimal('300.000'))


class PhysicalCountTest(TestCase):
    """
    اختبارات الجرد الفعلي
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )
        self.asset = Asset.objects.create(
            name='جهاز للجرد',
            category=self.category,
            original_cost=Decimal('5000.000'),
            purchase_date=date.today(),
            depreciation_method=self.depreciation_method
        )

    def test_create_count_cycle(self):
        """اختبار إنشاء دورة جرد"""
        cycle = PhysicalCountCycle.objects.create(
            name='جرد سنوي 2025',
            cycle_type='annual',
            start_date=date.today(),
            responsible_user=self.user
        )
        self.assertEqual(cycle.status, 'planned')

    def test_perform_count(self):
        """اختبار إجراء الجرد"""
        cycle = PhysicalCountCycle.objects.create(
            name='جرد اختبار',
            cycle_type='spot',
            start_date=date.today(),
            responsible_user=self.user,
            status='in_progress'
        )
        count = PhysicalCount.objects.create(
            cycle=cycle,
            count_date=date.today(),
            counter=self.user
        )
        count_line = PhysicalCountLine.objects.create(
            count=count,
            asset=self.asset,
            expected_quantity=1,
            actual_quantity=1
        )
        self.assertEqual(count_line.variance, 0)


# ==================== Performance Tests ====================

class PerformanceTest(TestCase):
    """
    اختبارات الأداء
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.depreciation_method = DepreciationMethod.objects.create(
            code='SL',
            name='القسط الثابت',
            method_type='straight_line'
        )
        self.category = AssetCategory.objects.create(
            code='CAT001',
            name='أجهزة',
            depreciation_method=self.depreciation_method
        )

    def test_bulk_asset_creation(self):
        """اختبار إنشاء عدد كبير من الأصول"""
        assets = []
        for i in range(100):
            assets.append(Asset(
                name=f'Asset {i}',
                category=self.category,
                original_cost=Decimal('1000.000'),
                purchase_date=date.today(),
                depreciation_method=self.depreciation_method
            ))
        Asset.objects.bulk_create(assets)
        self.assertEqual(Asset.objects.count(), 100)


# ==================== Command Tests ====================

class ManagementCommandTest(TestCase):
    """
    اختبارات أوامر الإدارة
    """

    def test_calculate_depreciation_command(self):
        """اختبار أمر حساب الإهلاك"""
        # يمكن اختبار management commands هنا
        pass


# ==================== Signal Tests ====================

class SignalTest(TestCase):
    """
    اختبارات الإشارات (Signals)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_asset_save_signal(self):
        """اختبار إشارة حفظ الأصل"""
        # يمكن اختبار signals هنا
        pass

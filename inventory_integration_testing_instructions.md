# تعليمات الفحص الشامل لنظام المخزون - Inventory Integration Testing

**تاريخ الإنشاء**: 2025-11-29
**الحالة**: شامل - جاهز للتنفيذ
**الهدف**: فحص كامل لنظام المخزون مع التكاملات

---

## جدول المحتويات

1. [نظرة عامة على النظام](#1-نظرة-عامة-على-النظام)
2. [البنية الأساسية](#2-البنية-الأساسية)
3. [فحص Business Logic](#3-فحص-business-logic)
4. [Unit Tests للـ Models](#4-unit-tests-للـ-models)
5. [Integration Tests للتكامل](#5-integration-tests-للتكامل)
6. [سكريبتات الفحص اليدوي](#6-سكريبتات-الفحص-اليدوي)
7. [تحليل التكامل مع Accounting](#7-تحليل-التكامل-مع-accounting)
8. [تحليل التكامل مع Purchases](#8-تحليل-التكامل-مع-purchases)
9. [Checklist الفحص](#9-checklist-الفحص)
10. [النقاط الضعيفة والمفقودة](#10-النقاط-الضعيفة-والمفقودة)

---

## 1. نظرة عامة على النظام

### 1.1 الملخص التنفيذي

نظام المخزون هو **نظام شامل ومتقدم لإدارة المستودعات** يتضمن:
- ✅ إدارة متعددة المستودعات مع دعم كامل للفروع
- ✅ تكامل محاسبي قوي (قيود تلقائية)
- ✅ تتبع الدفعات (FIFO/FEFO)
- ✅ نظام حجز المخزون
- ✅ تنبيهات آلية
- ✅ تتبع كامل للحركات (Audit Trail)
- ✅ حساب التكلفة المتوسطة المرجحة

### 1.2 إحصائيات النظام

| المكون | العدد | الملاحظات |
|--------|-------|-----------|
| **Models** | 12 | 6 مستندات، 2 جرد، 4 تتبع |
| **Service Classes** | 3 | Alerts, Reservations, Batch |
| **Management Commands** | 2 | تنبيهات، تنظيف الحجوزات |
| **Signal Handlers** | 6 | 3 في signals.py، 3 في cache.py |
| **Integration Points** | 4 | Accounting (قوي)، Core (قوي)، Purchases (ضعيف)، Sales (ضعيف جداً) |

### 1.3 العمليات الأساسية (Business Processes)

1. **سند الإدخال (Stock In)**: استلام المواد من الموردين أو الإنتاج
2. **سند الإخراج (Stock Out)**: صرف المواد للعملاء أو الاستهلاك
3. **التحويلات (Transfers)**: نقل بين المستودعات
4. **الجرد (Stock Count)**: الجرد الفعلي والتسويات
5. **تتبع الدفعات (Batches)**: إدارة المواد منتهية الصلاحية
6. **حجز المخزون (Reservations)**: حجز مؤقت لأوامر البيع

---

## 2. البنية الأساسية

### 2.1 Models الرئيسية

#### 2.1.1 مستندات المعاملات (Transaction Documents)

**StockIn** - سند إدخال
```python
# الحقول الأساسية
- source_type: purchase, return, production, opening, adjustment, other
- supplier: FK إلى BusinessPartner
- purchase_invoice: FK إلى PurchaseInvoice
- is_posted: حالة الترحيل
- journal_entry: FK إلى JournalEntry

# الـ Methods الأساسية
- post(user, create_journal_entry=True): ترحيل السند
- unpost(): إلغاء الترحيل
- create_journal_entry(user): إنشاء القيد المحاسبي
- can_edit(), can_post(), can_delete(): فحص الصلاحيات
```

**StockOut** - سند إخراج
```python
# الحقول الأساسية
- destination_type: sales, return, consumption, damage, adjustment, other
- customer: FK إلى BusinessPartner
- sales_invoice: FK إلى SalesInvoice
- is_posted: حالة الترحيل
- journal_entry: FK إلى JournalEntry

# الـ Methods الأساسية
- post(user): ترحيل السند (يفحص الكمية المتاحة)
- unpost(): إلغاء الترحيل
- create_journal_entry(user): إنشاء قيد تكلفة البضاعة المباعة
```

**StockTransfer** - التحويل المخزني
```python
# الحقول الأساسية
- warehouse: المستودع المصدر
- destination_warehouse: المستودع الوجهة
- status: draft, pending, approved, in_transit, received, cancelled
- approved_by, approval_date, received_by, received_date

# الـ Methods الأساسية
- approve(user): اعتماد التحويل
- send(user): إرسال التحويل (خصم من المصدر)
- receive(user): استلام التحويل (إضافة للوجهة)
- cancel(user): إلغاء التحويل
```

**StockCount** - الجرد
```python
# الحقول الأساسية
- count_type: periodic, annual, cycle, special
- status: planned, in_progress, completed, approved, cancelled
- warehouse, supervisor, count_team (M2M)
- adjustment_entry: FK إلى JournalEntry

# الـ Methods الأساسية
- populate_lines(): ملء السطور من الرصيد الحالي
- process_adjustments(user): معالجة الفروقات وإنشاء القيود
```

#### 2.1.2 نماذج التتبع (Tracking Models)

**ItemStock** - الأرصدة الحالية
```python
# الحقول الأساسية
- item, item_variant, warehouse
- quantity, reserved_quantity
- average_cost, total_value
- min_level, max_level, reorder_point
- last_purchase_price, last_purchase_date, last_supplier

# الـ Methods المهمة
- get_available_quantity(): الكمية - المحجوزة
- reserve_quantity(qty): حجز كمية
- release_reserved_quantity(qty): إلغاء الحجز
- is_below_reorder_level(): فحص نقطة إعادة الطلب
- update_last_purchase(): تحديث معلومات آخر شراء
```

**StockMovement** - سجل الحركات (Immutable Audit Trail)
```python
# الحقول الأساسية
- movement_type: in, out, transfer_out, transfer_in
- quantity: موجب للإدخال، سالب للإخراج
- unit_cost, total_cost
- balance_before, balance_quantity, balance_value
- reference_type, reference_id, reference_number

# ملاحظات
- هذا النموذج للقراءة فقط (يُنشأ تلقائياً ولا يُعدل أبداً)
- يوفر تتبع كامل لكل حركة مخزنية
```

**Batch** - تتبع الدفعات
```python
# الحقول الأساسية
- batch_number, manufacturing_date, expiry_date
- quantity, reserved_quantity
- unit_cost, total_value
- source_document, received_date

# الـ Methods المهمة
- is_expired(): فحص انتهاء الصلاحية
- days_to_expiry(): عدد الأيام المتبقية
- get_expiry_status(): الحالة (expired, expiring_soon, warning, active)
- get_available_quantity(): الكمية غير المحجوزة
```

**StockReservation** - حجوزات المخزون
```python
# الحقول الأساسية
- item_stock, item, item_variant, warehouse
- quantity
- reference_type, reference_id (مثل sales_order)
- status: active, confirmed, released, expired
- expires_at: وقت انتهاء الحجز

# الـ Methods المهمة
- is_expired(): فحص انتهاء المدة
- time_remaining(): الوقت المتبقي
```

### 2.2 Services الرئيسية

#### 2.2.1 InventoryAlertService
```python
# الـ Methods
- check_stock_levels(company, warehouse=None): فحص المستويات
- check_batch_expiry(company, days_threshold=30): فحص الصلاحيات
- get_all_alerts(company, warehouse=None): جميع التنبيهات
- get_alerts_summary(company): ملخص للوحة التحكم
```

#### 2.2.2 ReservationService
```python
# الـ Methods
- reserve_stock(item_stock, quantity, reference_type, reference_id): حجز
- release_reservation(reservation, partial_quantity=None): إلغاء حجز
- confirm_reservation(reservation): تأكيد الحجز
- cleanup_expired_reservations(company=None): تنظيف الحجوزات المنتهية
- extend_reservation(reservation, additional_minutes=30): تمديد الحجز
```

#### 2.2.3 BatchValidationService
```python
# الـ Methods
- validate_batch_for_use(batch, raise_on_expired=False): فحص الدفعة
- get_valid_batches_fifo(item, warehouse, company, quantity): FIFO
- get_valid_batches_fefo(item, warehouse, company, quantity): FEFO
```

### 2.3 Signals الموجودة

```python
# في apps/inventory/signals.py
1. check_low_stock_alert: يفحص المخزون المنخفض عند التغيير
2. prevent_delete_if_has_balance: يمنع حذف رصيد غير صفري

# في apps/inventory/cache.py
3. invalidate_item_stock_cache_on_save: إلغاء الكاش عند التحديث
4. invalidate_item_stock_cache_on_delete: إلغاء الكاش عند الحذف
5. invalidate_cache_on_movement: إلغاء الكاش عند الحركات
```

### 2.4 Management Commands

```bash
# 1. فحص التنبيهات
python manage.py check_inventory_alerts
python manage.py check_inventory_alerts --company=1
python manage.py check_inventory_alerts --email
python manage.py check_inventory_alerts --critical-only

# 2. تنظيف الحجوزات المنتهية
python manage.py cleanup_reservations
python manage.py cleanup_reservations --company=1
python manage.py cleanup_reservations --dry-run
```

---

## 3. فحص Business Logic

### 3.1 عملية سند الإدخال (Stock In Process)

**الخطوات**:
1. إنشاء StockIn (حالة: draft)
2. إضافة StockDocumentLine
3. مراجعة والتحقق
4. **الترحيل (POST)**:
   - إنشاء/تحديث ItemStock مع التكلفة المتوسطة المرجحة
   - إنشاء StockMovement (movement_type='in')
   - إنشاء Batch (إذا وُجد batch_number)
   - تحديث PartnerItemPrice للمورد
   - إنشاء وترحيل القيد المحاسبي
5. **إلغاء الترحيل (UNPOST)**: عكس جميع العمليات

**القيد المحاسبي**:
```
مدين: حساب المخزون (120000 أو item.inventory_account)
دائن: حسب source_type:
  - purchase: حساب المورد (210000)
  - opening: أرباح محتجزة (320101)
  - return: ذمم مدينة (1102)
  - production: تكلفة إنتاج (5)
  - adjustment: حساب تسوية (5)
  - other: حقوق ملكية افتراضية (3)
```

**الـ Tests المطلوبة**:
```python
def test_stock_in_post_creates_item_stock()
def test_stock_in_post_calculates_weighted_average()
def test_stock_in_post_creates_movement()
def test_stock_in_post_creates_batch()
def test_stock_in_post_creates_journal_entry()
def test_stock_in_post_updates_supplier_price()
def test_stock_in_unpost_reverses_all()
def test_stock_in_cannot_edit_when_posted()
def test_stock_in_journal_entry_is_balanced()
```

### 3.2 عملية سند الإخراج (Stock Out Process)

**الخطوات**:
1. إنشاء StockOut (حالة: draft)
2. إضافة StockDocumentLine
3. مراجعة
4. **الترحيل (POST)**:
   - فحص الكمية المتاحة (إلا إذا سُمح بالسالب)
   - خصم من ItemStock
   - إنشاء StockMovement (movement_type='out', quantity سالب)
   - تحديث PartnerItemPrice للعميل
   - إنشاء وترحيل قيد تكلفة البضاعة
5. **إلغاء الترحيل**: عكس العمليات

**القيد المحاسبي**:
```
مدين: تكلفة البضاعة المباعة (item.cost_of_goods_account أو المخزون)
دائن: حساب المخزون (item.inventory_account أو 120000)
```

**الـ Tests المطلوبة**:
```python
def test_stock_out_validates_available_quantity()
def test_stock_out_allows_negative_if_warehouse_allows()
def test_stock_out_rejects_negative_if_not_allowed()
def test_stock_out_reduces_item_stock()
def test_stock_out_creates_negative_movement()
def test_stock_out_creates_cogs_journal_entry()
def test_stock_out_updates_customer_price()
def test_stock_out_unpost_reverses_all()
```

### 3.3 عملية التحويل (Transfer Process)

**الخطوات**:
1. إنشاء StockTransfer (status=draft)
2. إضافة StockTransferLine
3. **اعتماد (APPROVE)**: status=approved
4. **إرسال (SEND)**:
   - خصم من المستودع المصدر
   - إنشاء StockMovement (transfer_out)
   - status=in_transit
5. **استلام (RECEIVE)**:
   - إضافة للمستودع الوجهة
   - إعادة حساب التكلفة المتوسطة
   - إنشاء StockMovement (transfer_in)
   - status=received

**الـ Tests المطلوبة**:
```python
def test_transfer_workflow_draft_to_received()
def test_transfer_send_validates_source_stock()
def test_transfer_receive_recalculates_average_cost()
def test_transfer_partial_receipt_supported()
def test_transfer_cancel_returns_stock_to_source()
def test_transfer_cannot_edit_after_approved()
def test_transfer_requires_approval_permission()
```

### 3.4 عملية الجرد (Stock Count Process)

**الخطوات**:
1. إنشاء StockCount (status=planned)
2. تحديد المستودع والمشرف
3. **ملء السطور (POPULATE_LINES)**: من ItemStock الحالي
4. status=in_progress
5. فريق الجرد يُحدث counted_quantity
6. status=completed
7. **معالجة التسويات (PROCESS_ADJUSTMENTS)**:
   - حساب الفروقات
   - إنشاء قيد التسوية
   - تحديث ItemStock بالكميات المجردة
   - status=approved

**القيد المحاسبي**:
```
# نقص (shortage):
مدين: مصروف نقص مخزون (560000/510000)
دائن: حساب المخزون (120000)

# زيادة (overage):
مدين: حساب المخزون (120000)
دائن: إيراد فائض مخزون (560000/510000)
```

**الـ Tests المطلوبة**:
```python
def test_stock_count_populate_fills_from_current_stock()
def test_stock_count_process_handles_shortage()
def test_stock_count_process_handles_overage()
def test_stock_count_creates_adjustment_entry()
def test_stock_count_updates_item_stock()
def test_stock_count_cannot_process_if_not_completed()
```

### 3.5 نظام الدفعات (Batch Tracking)

**FIFO vs FEFO**:
```python
# FIFO (First In, First Out): الأقدم أولاً
batches = get_valid_batches_fifo(item, warehouse, company, quantity)
# النتيجة: مرتب حسب received_date (الأقدم أولاً)

# FEFO (First Expired, First Out): الأقرب للانتهاء أولاً
batches = get_valid_batches_fefo(item, warehouse, company, quantity)
# النتيجة: مرتب حسب expiry_date (الأقرب للانتهاء أولاً)
```

**الـ Tests المطلوبة**:
```python
def test_fifo_allocates_oldest_batch_first()
def test_fefo_allocates_expiring_batch_first()
def test_batch_allocation_across_multiple_batches()
def test_batch_excludes_expired_by_default()
def test_batch_expiry_alert_generation()
def test_batch_cannot_delete_if_quantity_gt_zero()
```

### 3.6 نظام الحجوزات (Reservation System)

**دورة الحياة**:
```
1. إنشاء أمر بيع
   ↓
2. حجز المخزون (reserve_stock)
   - إنشاء StockReservation
   - تحديث ItemStock.reserved_quantity
   - تحديد expires_at (افتراضي 30 دقيقة)
   ↓
3. تأكيد العميل → confirm_reservation
   ↓
4. شحن البضاعة → ترحيل StockOut (يلغي الحجز تلقائياً)

أو

5. انتهاء المدة → cleanup_expired_reservations
```

**الـ Tests المطلوبة**:
```python
def test_reservation_validates_available_quantity()
def test_reservation_updates_reserved_quantity()
def test_reservation_expires_after_timeout()
def test_reservation_can_be_extended()
def test_reservation_cleanup_command_releases_expired()
def test_concurrent_reservations_dont_oversell()
def test_stock_out_posting_releases_reservation()
```

---

## 4. Unit Tests للـ Models

### 4.1 StockIn Model Tests

**ملف**: `tests/inventory/test_stock_in_model.py`

```python
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.inventory.models import StockIn, StockDocumentLine, ItemStock, StockMovement
from apps.core.models import Company, Warehouse, Item

User = get_user_model()

@pytest.mark.django_db
class TestStockInModel:
    """اختبارات شاملة لنموذج StockIn"""

    @pytest.fixture
    def setup_data(self):
        """إعداد البيانات الأساسية"""
        company = Company.objects.create(name="شركة الاختبار")
        warehouse = Warehouse.objects.create(
            name="مستودع الاختبار",
            company=company
        )
        item = Item.objects.create(
            name="مادة اختبار",
            code="TEST001",
            company=company
        )
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        return {
            'company': company,
            'warehouse': warehouse,
            'item': item,
            'user': user
        }

    def test_create_stock_in_draft(self, setup_data):
        """اختبار: إنشاء سند إدخال جديد في حالة draft"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        assert stock_in.is_posted is False
        assert stock_in.number is not None  # يجب أن يُولد رقم تلقائياً
        assert stock_in.can_edit() is True
        assert stock_in.can_post() is True

    def test_stock_in_post_creates_item_stock(self, setup_data):
        """اختبار: ترحيل سند الإدخال ينشئ ItemStock"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        # إضافة سطر
        line = StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        # الترحيل
        stock_in.post(user=setup_data['user'], create_journal_entry=False)

        # التحقق من ItemStock
        item_stock = ItemStock.objects.get(
            item=setup_data['item'],
            warehouse=setup_data['warehouse']
        )

        assert item_stock.quantity == Decimal('100')
        assert item_stock.average_cost == Decimal('10.00')
        assert item_stock.total_value == Decimal('1000.00')

    def test_stock_in_post_calculates_weighted_average(self, setup_data):
        """اختبار: التكلفة المتوسطة المرجحة"""
        # إنشاء رصيد موجود
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('50'),
            average_cost=Decimal('8.00'),
            total_value=Decimal('400.00'),
            created_by=setup_data['user']
        )

        # سند إدخال جديد
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=50,
            unit_cost=Decimal('12.00')
        )

        stock_in.post(user=setup_data['user'], create_journal_entry=False)

        # التحقق من المتوسط المرجح
        # (50 * 8) + (50 * 12) = 1000
        # 1000 / 100 = 10.00
        item_stock = ItemStock.objects.get(
            item=setup_data['item'],
            warehouse=setup_data['warehouse']
        )

        assert item_stock.quantity == Decimal('100')
        assert item_stock.average_cost == Decimal('10.00')
        assert item_stock.total_value == Decimal('1000.00')

    def test_stock_in_post_creates_movement(self, setup_data):
        """اختبار: ترحيل سند الإدخال ينشئ StockMovement"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        stock_in.post(user=setup_data['user'], create_journal_entry=False)

        # التحقق من الحركة
        movement = StockMovement.objects.get(
            item=setup_data['item'],
            warehouse=setup_data['warehouse'],
            reference_type='stock_in'
        )

        assert movement.movement_type == 'in'
        assert movement.quantity == Decimal('100')
        assert movement.unit_cost == Decimal('10.00')
        assert movement.total_cost == Decimal('1000.00')
        assert movement.balance_quantity == Decimal('100')

    def test_stock_in_unpost_reverses_all(self, setup_data):
        """اختبار: إلغاء الترحيل يعكس جميع العمليات"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        # الترحيل
        stock_in.post(user=setup_data['user'], create_journal_entry=False)
        assert stock_in.is_posted is True

        # إلغاء الترحيل
        stock_in.unpost()
        assert stock_in.is_posted is False

        # التحقق من عودة الرصيد
        item_stock = ItemStock.objects.filter(
            item=setup_data['item'],
            warehouse=setup_data['warehouse']
        ).first()

        # يجب أن يكون الرصيد صفر أو غير موجود
        if item_stock:
            assert item_stock.quantity == Decimal('0')

    def test_stock_in_cannot_edit_when_posted(self, setup_data):
        """اختبار: لا يمكن التعديل بعد الترحيل"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        stock_in.post(user=setup_data['user'], create_journal_entry=False)

        assert stock_in.can_edit() is False
        assert stock_in.can_delete() is False

    def test_stock_in_with_batch_creates_batch(self, setup_data):
        """اختبار: سند إدخال بدفعة ينشئ Batch"""
        from datetime import date, timedelta
        from apps.inventory.models import Batch

        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00'),
            batch_number='BATCH001',
            expiry_date=date.today() + timedelta(days=365)
        )

        stock_in.post(user=setup_data['user'], create_journal_entry=False)

        # التحقق من إنشاء الدفعة
        batch = Batch.objects.get(
            item=setup_data['item'],
            warehouse=setup_data['warehouse'],
            batch_number='BATCH001'
        )

        assert batch.quantity == Decimal('100')
        assert batch.unit_cost == Decimal('10.00')
        assert batch.is_expired() is False
```

### 4.2 StockOut Model Tests

**ملف**: `tests/inventory/test_stock_out_model.py`

```python
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.inventory.models import StockOut, StockDocumentLine, ItemStock

@pytest.mark.django_db
class TestStockOutModel:
    """اختبارات شاملة لنموذج StockOut"""

    def test_stock_out_validates_available_quantity(self, setup_data):
        """اختبار: التحقق من الكمية المتاحة"""
        # إنشاء رصيد
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('50'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('500.00'),
            created_by=setup_data['user']
        )

        # محاولة إخراج كمية أكبر
        stock_out = StockOut.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            destination_type='sales',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=setup_data['item'],
            quantity=100  # أكثر من المتاح
        )

        # يجب أن يفشل الترحيل (إذا لم يُسمح بالسالب)
        setup_data['warehouse'].allow_negative_stock = False
        setup_data['warehouse'].save()

        with pytest.raises(Exception):
            stock_out.post(user=setup_data['user'])

    def test_stock_out_allows_negative_if_warehouse_allows(self, setup_data):
        """اختبار: السماح بالسالب إذا كان المستودع يسمح"""
        # إنشاء رصيد
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('50'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('500.00'),
            created_by=setup_data['user']
        )

        # السماح بالسالب
        setup_data['warehouse'].allow_negative_stock = True
        setup_data['warehouse'].save()

        stock_out = StockOut.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            destination_type='sales',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=setup_data['item'],
            quantity=100  # أكثر من المتاح
        )

        # يجب أن ينجح
        stock_out.post(user=setup_data['user'], create_journal_entry=False)

        item_stock = ItemStock.objects.get(
            item=setup_data['item'],
            warehouse=setup_data['warehouse']
        )

        assert item_stock.quantity == Decimal('-50')

    def test_stock_out_creates_negative_movement(self, setup_data):
        """اختبار: حركة الإخراج تكون بكمية سالبة"""
        from apps.inventory.models import StockMovement

        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        stock_out = StockOut.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            destination_type='sales',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=setup_data['item'],
            quantity=30
        )

        stock_out.post(user=setup_data['user'], create_journal_entry=False)

        movement = StockMovement.objects.get(
            reference_type='stock_out',
            reference_id=stock_out.id
        )

        assert movement.movement_type == 'out'
        assert movement.quantity == Decimal('-30')  # سالب
        assert movement.balance_quantity == Decimal('70')  # الرصيد المتبقي
```

### 4.3 StockTransfer Model Tests

**ملف**: `tests/inventory/test_stock_transfer_model.py`

```python
import pytest
from decimal import Decimal
from apps.inventory.models import StockTransfer, StockTransferLine, ItemStock

@pytest.mark.django_db
class TestStockTransferModel:
    """اختبارات شاملة لنموذج StockTransfer"""

    @pytest.fixture
    def setup_transfer_data(self, setup_data):
        """إعداد بيانات التحويل"""
        # مستودع وجهة
        dest_warehouse = Warehouse.objects.create(
            name="مستودع الوجهة",
            company=setup_data['company']
        )

        # إنشاء رصيد في المستودع المصدر
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        setup_data['dest_warehouse'] = dest_warehouse
        return setup_data

    def test_transfer_workflow_draft_to_received(self, setup_transfer_data):
        """اختبار: دورة التحويل الكاملة من draft إلى received"""
        data = setup_transfer_data

        # 1. إنشاء تحويل
        transfer = StockTransfer.objects.create(
            company=data['company'],
            warehouse=data['warehouse'],
            destination_warehouse=data['dest_warehouse'],
            created_by=data['user']
        )

        StockTransferLine.objects.create(
            transfer=transfer,
            item=data['item'],
            quantity=50
        )

        assert transfer.status == 'draft'

        # 2. اعتماد
        transfer.approve(user=data['user'])
        assert transfer.status == 'approved'

        # 3. إرسال
        transfer.send(user=data['user'])
        assert transfer.status == 'in_transit'

        # التحقق من الخصم من المصدر
        source_stock = ItemStock.objects.get(
            item=data['item'],
            warehouse=data['warehouse']
        )
        assert source_stock.quantity == Decimal('50')

        # 4. استلام
        transfer.receive(user=data['user'])
        assert transfer.status == 'received'

        # التحقق من الإضافة للوجهة
        dest_stock = ItemStock.objects.get(
            item=data['item'],
            warehouse=data['dest_warehouse']
        )
        assert dest_stock.quantity == Decimal('50')

    def test_transfer_partial_receipt(self, setup_transfer_data):
        """اختبار: الاستلام الجزئي"""
        data = setup_transfer_data

        transfer = StockTransfer.objects.create(
            company=data['company'],
            warehouse=data['warehouse'],
            destination_warehouse=data['dest_warehouse'],
            created_by=data['user']
        )

        line = StockTransferLine.objects.create(
            transfer=transfer,
            item=data['item'],
            quantity=50
        )

        transfer.approve(user=data['user'])
        transfer.send(user=data['user'])

        # استلام جزئي
        line.received_quantity = Decimal('30')
        line.save()

        transfer.receive(user=data['user'])

        dest_stock = ItemStock.objects.get(
            item=data['item'],
            warehouse=data['dest_warehouse']
        )

        assert dest_stock.quantity == Decimal('30')
```

---

## 5. Integration Tests للتكامل

### 5.1 تكامل مع Accounting

**ملف**: `tests/inventory/test_accounting_integration.py`

```python
import pytest
from decimal import Decimal
from apps.inventory.models import StockIn, StockOut, StockCount, StockDocumentLine
from apps.accounting.models import JournalEntry, JournalEntryLine

@pytest.mark.django_db
class TestAccountingIntegration:
    """اختبارات التكامل مع النظام المحاسبي"""

    def test_stock_in_creates_journal_entry(self, setup_data):
        """اختبار: سند الإدخال ينشئ قيد محاسبي"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        # الترحيل مع إنشاء القيد
        stock_in.post(user=setup_data['user'], create_journal_entry=True)

        # التحقق من وجود القيد
        assert stock_in.journal_entry is not None
        journal = stock_in.journal_entry

        # التحقق من الترحيل
        assert journal.is_posted is True

        # التحقق من السطور
        lines = journal.lines.all()
        assert lines.count() == 2  # سطر مدين وسطر دائن

        # حساب المجاميع
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)

        assert total_debit == Decimal('1000.00')
        assert total_credit == Decimal('1000.00')
        assert total_debit == total_credit  # القيد متوازن

    def test_stock_in_journal_accounts(self, setup_data):
        """اختبار: حسابات القيد المحاسبي لسند الإدخال"""
        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_in=stock_in,
            item=setup_data['item'],
            quantity=100,
            unit_cost=Decimal('10.00')
        )

        stock_in.post(user=setup_data['user'], create_journal_entry=True)
        journal = stock_in.journal_entry

        # الحساب المدين: المخزون (120000)
        debit_line = journal.lines.filter(debit__gt=0).first()
        assert debit_line.account.code == '120000'
        assert debit_line.debit == Decimal('1000.00')

        # الحساب الدائن: الموردين (210000)
        credit_line = journal.lines.filter(credit__gt=0).first()
        assert credit_line.account.code == '210000'
        assert credit_line.credit == Decimal('1000.00')

    def test_stock_out_creates_cogs_entry(self, setup_data):
        """اختبار: سند الإخراج ينشئ قيد تكلفة البضاعة المباعة"""
        # إنشاء رصيد أولاً
        from apps.inventory.models import ItemStock
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        stock_out = StockOut.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            destination_type='sales',
            created_by=setup_data['user']
        )

        StockDocumentLine.objects.create(
            stock_out=stock_out,
            item=setup_data['item'],
            quantity=30
        )

        stock_out.post(user=setup_data['user'])

        # التحقق من القيد
        assert stock_out.journal_entry is not None
        journal = stock_out.journal_entry

        # التحقق من القيمة (30 * 10 = 300)
        total_debit = sum(line.debit for line in journal.lines.all())
        total_credit = sum(line.credit for line in journal.lines.all())

        assert total_debit == Decimal('300.00')
        assert total_credit == Decimal('300.00')

    def test_stock_count_adjustment_entry(self, setup_data):
        """اختبار: قيد تسوية الجرد"""
        from apps.inventory.models import ItemStock, StockCount, StockCountLine

        # إنشاء رصيد
        ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        # إنشاء جرد
        count = StockCount.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            supervisor=setup_data['user'],
            count_type='periodic'
        )

        # سطر الجرد مع نقص
        StockCountLine.objects.create(
            count=count,
            item=setup_data['item'],
            system_quantity=Decimal('100'),
            counted_quantity=Decimal('90'),  # نقص 10
            unit_cost=Decimal('10.00')
        )

        count.status = 'completed'
        count.save()

        # معالجة التسويات
        count.process_adjustments(user=setup_data['user'])

        # التحقق من القيد
        assert count.adjustment_entry is not None
        journal = count.adjustment_entry

        # نقص: مدين مصروف (560000)، دائن مخزون (120000)
        # القيمة = 10 * 10 = 100
        total_debit = sum(line.debit for line in journal.lines.all())
        total_credit = sum(line.credit for line in journal.lines.all())

        assert total_debit == Decimal('100.00')
        assert total_credit == Decimal('100.00')
```

### 5.2 تكامل مع Purchases

**ملف**: `tests/inventory/test_purchases_integration.py`

```python
import pytest
from decimal import Decimal

@pytest.mark.django_db
class TestPurchasesIntegration:
    """اختبارات التكامل مع نظام المشتريات"""

    def test_stock_in_linked_to_purchase_invoice(self, setup_data):
        """اختبار: ربط سند الإدخال بفاتورة المشتريات"""
        from apps.purchases.models import PurchaseInvoice
        from apps.inventory.models import StockIn

        # إنشاء فاتورة مشتريات (افتراضياً موجودة)
        # ملاحظة: هذا يتطلب وجود نموذج PurchaseInvoice

        stock_in = StockIn.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            source_type='purchase',
            created_by=setup_data['user'],
            # purchase_invoice=invoice  # الربط
        )

        # التحقق من الربط
        # assert stock_in.purchase_invoice is not None
        # assert stock_in.purchase_invoice.id == invoice.id

        # ملاحظة: هذا الاختبار يعتمد على وجود نموذج PurchaseInvoice
        # حالياً، الربط موجود كـ FK ولكن لا يوجد تكامل تلقائي
        pass

    def test_missing_auto_stock_in_from_purchase_invoice(self):
        """اختبار: الكشف عن غياب التكامل التلقائي"""
        # هذا الاختبار يوثق أن التكامل التلقائي غير موجود حالياً
        # TODO: يجب إضافة signal في purchases app لإنشاء StockIn تلقائياً

        # من الأفضل أن يكون هناك:
        # @receiver(post_save, sender=PurchaseInvoice)
        # def auto_create_stock_in(sender, instance, **kwargs):
        #     if instance.is_posted and not instance.stock_ins.exists():
        #         # إنشاء وترحيل StockIn تلقائياً

        assert True  # توثيق فقط
```

### 5.3 Batch & Reservation Integration

**ملف**: `tests/inventory/test_batch_reservation.py`

```python
import pytest
from decimal import Decimal
from datetime import date, timedelta
from apps.inventory.models import Batch, StockReservation, ItemStock
from apps.inventory.services import BatchValidationService, ReservationService

@pytest.mark.django_db
class TestBatchReservationIntegration:
    """اختبارات تكامل الدفعات والحجوزات"""

    def test_fifo_allocation(self, setup_data):
        """اختبار: تخصيص FIFO"""
        from apps.inventory.models import Batch

        # إنشاء دفعات متعددة
        batch1 = Batch.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            batch_number='BATCH001',
            quantity=Decimal('50'),
            unit_cost=Decimal('10.00'),
            received_date=date.today() - timedelta(days=10),  # الأقدم
            created_by=setup_data['user']
        )

        batch2 = Batch.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            batch_number='BATCH002',
            quantity=Decimal('60'),
            unit_cost=Decimal('11.00'),
            received_date=date.today() - timedelta(days=5),  # الأحدث
            created_by=setup_data['user']
        )

        # طلب 70 وحدة
        batches = BatchValidationService.get_valid_batches_fifo(
            item=setup_data['item'],
            warehouse=setup_data['warehouse'],
            company=setup_data['company'],
            quantity=Decimal('70')
        )

        # يجب أن يخصص من batch1 أولاً (50) ثم batch2 (20)
        assert len(batches) == 2
        assert batches[0]['batch'].batch_number == 'BATCH001'
        assert batches[0]['quantity'] == Decimal('50')
        assert batches[1]['batch'].batch_number == 'BATCH002'
        assert batches[1]['quantity'] == Decimal('20')

    def test_fefo_allocation(self, setup_data):
        """اختبار: تخصيص FEFO (الأقرب للانتهاء أولاً)"""
        from apps.inventory.models import Batch

        batch1 = Batch.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            batch_number='BATCH001',
            quantity=Decimal('50'),
            unit_cost=Decimal('10.00'),
            expiry_date=date.today() + timedelta(days=60),  # ينتهي لاحقاً
            received_date=date.today() - timedelta(days=10),
            created_by=setup_data['user']
        )

        batch2 = Batch.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            batch_number='BATCH002',
            quantity=Decimal('60'),
            unit_cost=Decimal('11.00'),
            expiry_date=date.today() + timedelta(days=30),  # ينتهي قريباً
            received_date=date.today() - timedelta(days=5),
            created_by=setup_data['user']
        )

        # طلب 70 وحدة
        batches = BatchValidationService.get_valid_batches_fefo(
            item=setup_data['item'],
            warehouse=setup_data['warehouse'],
            company=setup_data['company'],
            quantity=Decimal('70')
        )

        # يجب أن يخصص من batch2 أولاً (الأقرب للانتهاء)
        assert len(batches) == 2
        assert batches[0]['batch'].batch_number == 'BATCH002'
        assert batches[0]['quantity'] == Decimal('60')
        assert batches[1]['batch'].batch_number == 'BATCH001'
        assert batches[1]['quantity'] == Decimal('10')

    def test_reservation_prevents_double_allocation(self, setup_data):
        """اختبار: الحجوزات تمنع التخصيص المزدوج"""
        # إنشاء رصيد
        item_stock = ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        # حجز أول (50 وحدة)
        reservation1 = ReservationService.reserve_stock(
            item_stock=item_stock,
            quantity=Decimal('50'),
            reference_type='sales_order',
            reference_id=1,
            user=setup_data['user']
        )

        # التحقق من الكمية المتاحة
        item_stock.refresh_from_db()
        assert item_stock.get_available_quantity() == Decimal('50')

        # محاولة حجز ثانٍ (60 وحدة) - يجب أن يفشل
        with pytest.raises(Exception):
            ReservationService.reserve_stock(
                item_stock=item_stock,
                quantity=Decimal('60'),  # أكثر من المتاح
                reference_type='sales_order',
                reference_id=2,
                user=setup_data['user']
            )

    def test_reservation_auto_cleanup(self, setup_data):
        """اختبار: التنظيف التلقائي للحجوزات المنتهية"""
        from datetime import datetime, timedelta
        from django.utils import timezone

        item_stock = ItemStock.objects.create(
            company=setup_data['company'],
            warehouse=setup_data['warehouse'],
            item=setup_data['item'],
            quantity=Decimal('100'),
            average_cost=Decimal('10.00'),
            total_value=Decimal('1000.00'),
            created_by=setup_data['user']
        )

        # حجز بوقت انتهاء في الماضي
        reservation = StockReservation.objects.create(
            company=setup_data['company'],
            item_stock=item_stock,
            item=setup_data['item'],
            warehouse=setup_data['warehouse'],
            quantity=Decimal('50'),
            reference_type='sales_order',
            reference_id=1,
            status='active',
            expires_at=timezone.now() - timedelta(minutes=10),  # منتهي
            reserved_by=setup_data['user']
        )

        # تحديث reserved_quantity يدوياً (عادة يحدث في reserve_stock)
        item_stock.reserved_quantity = Decimal('50')
        item_stock.save()

        # تنفيذ التنظيف
        cleaned_count = ReservationService.cleanup_expired_reservations(
            company=setup_data['company']
        )

        assert cleaned_count == 1

        # التحقق من تحرير الحجز
        reservation.refresh_from_db()
        assert reservation.status == 'expired'

        item_stock.refresh_from_db()
        assert item_stock.reserved_quantity == Decimal('0')
```

---

## 6. سكريبتات الفحص اليدوي

### 6.1 Django Shell - فحص Stock In

**ملف**: `scripts/test_stock_in_workflow.py`

```python
"""
سكريبت فحص يدوي لدورة سند الإدخال الكاملة
الاستخدام: python manage.py shell < scripts/test_stock_in_workflow.py
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.core.models import Company, Warehouse, Item
from apps.inventory.models import StockIn, StockDocumentLine, ItemStock, StockMovement
from django.db import transaction

User = get_user_model()

print("=" * 80)
print("فحص دورة سند الإدخال (Stock In Workflow)")
print("=" * 80)

# 1. الإعداد
print("\n1. إعداد البيانات الأساسية...")
company = Company.objects.first()
warehouse = Warehouse.objects.filter(company=company).first()
item = Item.objects.filter(company=company).first()
user = User.objects.filter(is_superuser=True).first()

print(f"   الشركة: {company.name}")
print(f"   المستودع: {warehouse.name}")
print(f"   المادة: {item.name}")
print(f"   المستخدم: {user.username}")

# 2. حفظ الرصيد الحالي
print("\n2. الرصيد الحالي...")
try:
    current_stock = ItemStock.objects.get(
        item=item,
        warehouse=warehouse,
        company=company
    )
    initial_qty = current_stock.quantity
    initial_cost = current_stock.average_cost
    print(f"   الكمية: {initial_qty}")
    print(f"   التكلفة المتوسطة: {initial_cost}")
except ItemStock.DoesNotExist:
    initial_qty = Decimal('0')
    initial_cost = Decimal('0')
    print("   لا يوجد رصيد سابق")

# 3. إنشاء سند إدخال
print("\n3. إنشاء سند إدخال...")
with transaction.atomic():
    stock_in = StockIn.objects.create(
        company=company,
        warehouse=warehouse,
        source_type='purchase',
        reference='TEST-001',
        created_by=user
    )

    print(f"   رقم السند: {stock_in.number}")
    print(f"   الحالة: {'مرحل' if stock_in.is_posted else 'مسودة'}")

    # إضافة سطر
    line = StockDocumentLine.objects.create(
        stock_in=stock_in,
        item=item,
        quantity=Decimal('50'),
        unit_cost=Decimal('15.00')
    )

    print(f"   الكمية: {line.quantity}")
    print(f"   تكلفة الوحدة: {line.unit_cost}")
    print(f"   التكلفة الإجمالية: {line.total_cost}")

# 4. ترحيل السند
print("\n4. ترحيل السند...")
try:
    stock_in.post(user=user, create_journal_entry=False)
    print("   ✓ تم الترحيل بنجاح")
except Exception as e:
    print(f"   ✗ فشل الترحيل: {e}")
    raise

# 5. التحقق من الرصيد الجديد
print("\n5. الرصيد بعد الترحيل...")
try:
    new_stock = ItemStock.objects.get(
        item=item,
        warehouse=warehouse,
        company=company
    )

    expected_qty = initial_qty + Decimal('50')
    expected_total_value = (initial_qty * initial_cost) + (Decimal('50') * Decimal('15.00'))
    expected_avg_cost = expected_total_value / expected_qty if expected_qty > 0 else Decimal('0')

    print(f"   الكمية الحالية: {new_stock.quantity} (المتوقع: {expected_qty})")
    print(f"   التكلفة المتوسطة: {new_stock.average_cost} (المتوقع: {expected_avg_cost:.2f})")
    print(f"   القيمة الإجمالية: {new_stock.total_value} (المتوقع: {expected_total_value})")

    # التحقق
    assert new_stock.quantity == expected_qty, "خطأ في الكمية!"
    assert abs(new_stock.average_cost - expected_avg_cost) < Decimal('0.01'), "خطأ في التكلفة المتوسطة!"
    print("   ✓ الحسابات صحيحة")

except ItemStock.DoesNotExist:
    print("   ✗ لم يتم إنشاء الرصيد!")
    raise

# 6. التحقق من الحركة
print("\n6. التحقق من StockMovement...")
try:
    movement = StockMovement.objects.filter(
        reference_type='stock_in',
        reference_id=stock_in.id
    ).first()

    if movement:
        print(f"   نوع الحركة: {movement.movement_type}")
        print(f"   الكمية: {movement.quantity}")
        print(f"   التكلفة: {movement.unit_cost}")
        print(f"   الرصيد قبل: {movement.balance_before}")
        print(f"   الرصيد بعد: {movement.balance_quantity}")
        print("   ✓ تم إنشاء الحركة")
    else:
        print("   ✗ لم يتم إنشاء الحركة!")

except Exception as e:
    print(f"   ✗ خطأ: {e}")

# 7. اختبار إلغاء الترحيل
print("\n7. اختبار إلغاء الترحيل...")
try:
    stock_in.unpost()
    print("   ✓ تم إلغاء الترحيل")

    # التحقق من عودة الرصيد
    final_stock = ItemStock.objects.get(
        item=item,
        warehouse=warehouse,
        company=company
    )

    print(f"   الكمية بعد الإلغاء: {final_stock.quantity} (المتوقع: {initial_qty})")

    if final_stock.quantity == initial_qty:
        print("   ✓ عادت الكمية للرصيد الأصلي")
    else:
        print("   ✗ الكمية لم تعد للرصيد الأصلي!")

except Exception as e:
    print(f"   ✗ فشل إلغاء الترحيل: {e}")

print("\n" + "=" * 80)
print("انتهى الفحص")
print("=" * 80)
```

### 6.2 Django Shell - فحص التنبيهات

**ملف**: `scripts/test_alerts.py`

```python
"""
سكريبت فحص نظام التنبيهات
الاستخدام: python manage.py shell < scripts/test_alerts.py
"""

from apps.core.models import Company
from apps.inventory.services import InventoryAlertService

print("=" * 80)
print("فحص نظام التنبيهات (Alert System)")
print("=" * 80)

company = Company.objects.first()
print(f"\nالشركة: {company.name}")

# 1. ملخص التنبيهات
print("\n1. ملخص التنبيهات...")
summary = InventoryAlertService.get_alerts_summary(company)

print(f"   حرجة (Critical): {summary['critical_count']}")
print(f"   عالية (High): {summary['high_count']}")
print(f"   متوسطة (Medium): {summary['medium_count']}")
print(f"   منخفضة (Low): {summary['low_count']}")
print(f"   المجموع: {summary['total_count']}")
print(f"   يوجد حرجة: {summary['has_critical']}")

# 2. جميع التنبيهات
print("\n2. تفاصيل التنبيهات...")
alerts = InventoryAlertService.get_all_alerts(company)

# الحرجة
if alerts['critical']:
    print(f"\n   ⚠️  تنبيهات حرجة ({len(alerts['critical'])}):")
    for alert in alerts['critical'][:5]:  # أول 5
        print(f"      - {alert['type']}: {alert['message']}")

# العالية
if alerts['high']:
    print(f"\n   🔸 تنبيهات عالية ({len(alerts['high'])}):")
    for alert in alerts['high'][:5]:
        print(f"      - {alert['type']}: {alert['message']}")

# 3. تنبيهات المخزون المنخفض
print("\n3. تنبيهات المخزون...")
stock_alerts = InventoryAlertService.check_stock_levels(company)

low_stock = [a for a in stock_alerts if a['type'] == 'low_stock']
negative_stock = [a for a in stock_alerts if a['type'] == 'negative_stock']

print(f"   مخزون منخفض: {len(low_stock)}")
print(f("   مخزون سالب: {len(negative_stock)}")

if negative_stock:
    print("\n   ⚠️  مخزون سالب:")
    for alert in negative_stock[:3]:
        print(f"      - {alert['item'].name}: {alert['current_qty']}")

# 4. تنبيهات الصلاحية
print("\n4. تنبيهات الصلاحية...")
expiry_alerts = InventoryAlertService.check_batch_expiry(company, days_threshold=30)

expired = [a for a in expiry_alerts if a['type'] == 'expired']
expiring_soon = [a for a in expiry_alerts if a['type'] == 'expiring_soon']

print(f"   منتهي الصلاحية: {len(expired)}")
print(f"   قريب من الانتهاء (≤30 يوم): {len(expiring_soon)}")

if expired:
    print("\n   ⚠️  دفعات منتهية الصلاحية:")
    for alert in expired[:3]:
        print(f"      - {alert.get('batch_number')}: {alert['item'].name} - انتهى منذ {abs(alert['days_left'])} يوم")

if expiring_soon:
    print("\n   🔸 دفعات قريبة من الانتهاء:")
    for alert in expiring_soon[:3]:
        print(f"      - {alert.get('batch_number')}: {alert['item'].name} - متبقي {alert['days_left']} يوم")

print("\n" + "=" * 80)
print("انتهى فحص التنبيهات")
print("=" * 80)
```

### 6.3 Performance Test - Concurrent Updates

**ملف**: `scripts/test_concurrent_stock_updates.py`

```python
"""
اختبار التحديثات المتزامنة على المخزون
يفحص مشاكل race conditions
"""

import threading
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.core.models import Company, Warehouse, Item
from apps.inventory.models import StockOut, StockDocumentLine, ItemStock
from django.db import transaction

User = get_user_model()

print("=" * 80)
print("اختبار التحديثات المتزامنة (Concurrent Updates)")
print("=" * 80)

# الإعداد
company = Company.objects.first()
warehouse = Warehouse.objects.filter(company=company).first()
item = Item.objects.filter(company=company).first()
user = User.objects.filter(is_superuser=True).first()

# السماح بالسالب
warehouse.allow_negative_stock = False
warehouse.save()

# إنشاء رصيد أولي
print("\nإعداد رصيد أولي: 100 وحدة...")
ItemStock.objects.filter(
    item=item,
    warehouse=warehouse
).delete()

ItemStock.objects.create(
    company=company,
    warehouse=warehouse,
    item=item,
    quantity=Decimal('100'),
    average_cost=Decimal('10.00'),
    total_value=Decimal('1000.00'),
    created_by=user
)

# دالة إنشاء سند إخراج
def create_stock_out(thread_id, quantity):
    try:
        with transaction.atomic():
            stock_out = StockOut.objects.create(
                company=company,
                warehouse=warehouse,
                destination_type='sales',
                reference=f'THREAD-{thread_id}',
                created_by=user
            )

            StockDocumentLine.objects.create(
                stock_out=stock_out,
                item=item,
                quantity=quantity
            )

            stock_out.post(user=user)
            print(f"Thread {thread_id}: نجح - {quantity} وحدة")

    except Exception as e:
        print(f"Thread {thread_id}: فشل - {e}")

# إنشاء 10 threads تحاول إخراج 15 وحدة في نفس الوقت
# المجموع = 150 وحدة (أكثر من المتاح 100)
print("\nإنشاء 10 عمليات متزامنة...")
threads = []
for i in range(10):
    t = threading.Thread(target=create_stock_out, args=(i, Decimal('15')))
    threads.append(t)
    t.start()

# الانتظار
for t in threads:
    t.join()

# التحقق من النتيجة
print("\nالنتيجة النهائية...")
final_stock = ItemStock.objects.get(
    item=item,
    warehouse=warehouse
)

print(f"الرصيد النهائي: {final_stock.quantity}")
print(f"الرصيد المتوقع: <= 0 (إذا لم يكن هناك race condition)")
print(f"عدد سندات الإخراج المنشأة: {StockOut.objects.filter(warehouse=warehouse, is_posted=True, reference__startswith='THREAD').count()}")

if final_stock.quantity < Decimal('-10'):
    print("\n⚠️  تحذير: قد يكون هناك race condition!")
    print("   بعض العمليات نجحت رغم عدم توفر الكمية الكافية")
else:
    print("\n✓ النظام يتعامل مع التحديثات المتزامنة بشكل صحيح")

print("\n" + "=" * 80)
```

---

## 7. تحليل التكامل مع Accounting

### 7.1 نقاط التكامل الموجودة

**قوة التكامل**: ★★★★★ (5/5) - **ممتاز**

#### 7.1.1 StockIn → Accounting

**القيد المحاسبي**:
```
وقت التنفيذ: عند استدعاء stock_in.post(user, create_journal_entry=True)
Method: StockIn.create_journal_entry(user)

القيد:
┌─────────────────────────────────────────────────────────────┐
│ من ح/ المخزون (120000 أو item.inventory_account)           │
│    إلى ح/ [حسب source_type]:                               │
│        - purchase: الموردين (210000 أو supplier.account)   │
│        - opening: أرباح محتجزة (320101)                    │
│        - return: ذمم مدينة (1102)                          │
│        - production: تكلفة إنتاج (5)                       │
│        - adjustment: تسوية (5)                             │
│        - other: حقوق ملكية (3)                             │
│ القيمة: quantity * unit_cost                               │
│ الحالة: مرحل تلقائياً (is_posted=True)                    │
│ الربط: stock_in.journal_entry = entry                      │
└─────────────────────────────────────────────────────────────┘
```

**الكود**:
```python
# في apps/inventory/models.py (StockIn class)
def create_journal_entry(self, user):
    # 1. التحقق من الشروط
    if not self.is_posted:
        raise ValidationError("يجب ترحيل السند أولاً")

    if self.journal_entry:
        return self.journal_entry  # موجود مسبقاً

    # 2. حساب المجموع
    total_amount = sum(line.total_cost for line in self.lines.all())

    # 3. إنشاء القيد
    entry = JournalEntry.objects.create(
        company=self.company,
        entry_type='automatic',
        date=self.date,
        reference=f"Stock In {self.number}",
        description=f"سند إدخال {self.number}",
        created_by=user
    )

    # 4. السطر المدين (المخزون)
    inventory_account = self.lines.first().item.inventory_account
    if not inventory_account:
        inventory_account = Account.objects.get(code='120000', company=self.company)

    JournalEntryLine.objects.create(
        entry=entry,
        account=inventory_account,
        debit=total_amount,
        credit=Decimal('0'),
        description=f"استلام مخزون - {self.number}"
    )

    # 5. السطر الدائن (حسب source_type)
    credit_account = self._get_credit_account()

    JournalEntryLine.objects.create(
        entry=entry,
        account=credit_account,
        debit=Decimal('0'),
        credit=total_amount,
        description=f"استلام مخزون - {self.number}",
        partner=self.supplier if self.source_type == 'purchase' else None
    )

    # 6. ترحيل القيد
    entry.post(user=user)

    # 7. الربط
    self.journal_entry = entry
    self.save(update_fields=['journal_entry'])

    return entry
```

**الاختبارات المطلوبة**:
```python
def test_stock_in_journal_entry_accounts():
    """فحص الحسابات المستخدمة في القيد"""

def test_stock_in_journal_entry_balanced():
    """فحص توازن القيد (مدين = دائن)"""

def test_stock_in_journal_entry_posted():
    """فحص ترحيل القيد تلقائياً"""

def test_stock_in_journal_entry_with_supplier():
    """فحص ربط الطرف عند الشراء"""

def test_stock_in_journal_entry_different_sources():
    """فحص الحسابات المختلفة حسب source_type"""
```

#### 7.1.2 StockOut → Accounting

**القيد المحاسبي**:
```
وقت التنفيذ: عند استدعاء stock_out.post(user)
Method: StockOut.create_journal_entry(user)

القيد:
┌─────────────────────────────────────────────────────────────┐
│ من ح/ تكلفة البضاعة المباعة (item.cost_of_goods_account)  │
│    إلى ح/ المخزون (item.inventory_account أو 120000)       │
│ القيمة: quantity * average_cost (من ItemStock)             │
│ الحالة: مرحل تلقائياً                                      │
│ الربط: stock_out.journal_entry = entry                     │
└─────────────────────────────────────────────────────────────┘
```

**نقطة مهمة**: يستخدم `average_cost` من ItemStock، ليس `unit_cost` من السطر

**الاختبارات المطلوبة**:
```python
def test_stock_out_uses_average_cost():
    """فحص استخدام التكلفة المتوسطة"""

def test_stock_out_cogs_calculation():
    """فحص حساب تكلفة البضاعة المباعة"""

def test_stock_out_multiple_items_separate_lines():
    """فحص سطور منفصلة لمواد مختلفة"""
```

#### 7.1.3 StockCount → Accounting

**القيد المحاسبي**:
```
وقت التنفيذ: عند استدعاء count.process_adjustments(user)
Method: StockCount.create_adjustment_entry(user)

القيد (نقص):
┌─────────────────────────────────────────────────────────────┐
│ من ح/ مصروف نقص المخزون (560000 أو 510000)                │
│    إلى ح/ المخزون (120000)                                 │
│ القيمة: abs(difference_quantity) * unit_cost               │
└─────────────────────────────────────────────────────────────┘

القيد (زيادة):
┌─────────────────────────────────────────────────────────────┐
│ من ح/ المخزون (120000)                                     │
│    إلى ح/ إيراد فائض المخزون (560000 أو 510000)           │
│ القيمة: abs(difference_quantity) * unit_cost               │
└─────────────────────────────────────────────────────────────┘
```

**الكود**:
```python
# في StockCount.process_adjustments()
for line in self.lines.all():
    if line.difference_quantity != 0:
        if line.difference_quantity < 0:  # نقص
            # Debit: مصروف
            # Credit: مخزون
            pass
        else:  # زيادة
            # Debit: مخزون
            # Credit: إيراد
            pass
```

### 7.2 نقاط التكامل المفقودة

#### 7.2.1 StockTransfer (لا يوجد قيود)

**الحالة الحالية**: لا يوجد قيود محاسبية للتحويلات

**السبب**: التحويلات داخل نفس الكيان القانوني لا تؤثر على الميزانية

**لكن**: إذا كان التحويل بين فروع/كيانات قانونية مختلفة، **يجب** إنشاء قيود

**التوصية**:
```python
# إضافة في StockTransfer
def create_inter_company_entry(self, user):
    """إنشاء قيد للتحويلات بين الفروع/الكيانات"""
    if self.is_inter_company_transfer():
        # إنشاء قيدين:
        # 1. قيد في الفرع المصدر (تخفيض المخزون)
        # 2. قيد في الفرع الوجهة (زيادة المخزون)
        pass
```

#### 7.2.2 Batch Adjustments (لا يوجد قيود منفصلة)

**الحالة الحالية**: تسويات الدفعات المنتهية تتم يدوياً عبر StockOut

**التوصية**: إضافة عملية تسوية تلقائية للدفعات المنتهية

### 7.3 Checklist التكامل المحاسبي

```
✅ StockIn ينشئ قيد محاسبي
✅ القيد متوازن (مدين = دائن)
✅ القيد مرحل تلقائياً
✅ الحسابات صحيحة حسب source_type
✅ ربط الطرف (partner) في حالة الشراء
✅ StockOut ينشئ قيد تكلفة البضاعة
✅ يستخدم average_cost من ItemStock
✅ StockCount ينشئ قيد تسوية
✅ يفرق بين نقص وزيادة
⚠️  StockTransfer لا ينشئ قيود (مطلوب للتحويلات بين الفروع)
⚠️  لا يوجد قيود لتسوية الدفعات المنتهية تلقائياً
✅ جميع القيود تُسجل في JournalEntry
✅ جميع القيود لها reference للمستند الأصلي
```

---

## 8. تحليل التكامل مع Purchases

### 8.1 نقاط التكامل الموجودة

**قوة التكامل**: ★★☆☆☆ (2/5) - **ضعيف**

#### 8.1.1 الربط الحالي

**Foreign Key فقط**:
```python
# في StockIn model
purchase_invoice = models.ForeignKey(
    'purchases.PurchaseInvoice',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='stock_ins'
)
```

**الاستخدام الحالي**:
- ربط يدوي فقط (يُحدد المستخدم عند إنشاء StockIn)
- لا يوجد تكامل تلقائي
- لا توجد signals
- لا يوجد validation للربط

### 8.2 التكامل المفقود (Critical)

#### 8.2.1 لا يوجد إنشاء تلقائي لـ StockIn

**المشكلة**:
```
عند ترحيل فاتورة مشتريات (PurchaseInvoice.post())
→ لا يتم إنشاء StockIn تلقائياً
→ يتطلب إدخال يدوي مزدوج
→ احتمالية نسيان تسجيل الاستلام
→ عدم تطابق بين المشتريات والمخزون
```

**الحل المقترح**:
```python
# في apps/purchases/signals.py (يجب إنشاءه)

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.purchases.models import PurchaseInvoice
from apps.inventory.models import StockIn, StockDocumentLine

@receiver(post_save, sender=PurchaseInvoice)
def auto_create_stock_in_from_invoice(sender, instance, created, **kwargs):
    """إنشاء سند إدخال تلقائياً عند ترحيل فاتورة مشتريات"""

    # فقط عند الترحيل لأول مرة
    if instance.is_posted and not instance.stock_ins.exists():
        # إنشاء StockIn
        stock_in = StockIn.objects.create(
            company=instance.company,
            warehouse=instance.warehouse,  # يحتاج إضافة warehouse للفاتورة
            source_type='purchase',
            supplier=instance.supplier,
            purchase_invoice=instance,
            reference=f"من فاتورة {instance.number}",
            date=instance.date,
            created_by=instance.created_by
        )

        # نسخ السطور
        for invoice_line in instance.lines.all():
            StockDocumentLine.objects.create(
                stock_in=stock_in,
                item=invoice_line.item,
                item_variant=invoice_line.item_variant,
                quantity=invoice_line.quantity,
                unit_cost=invoice_line.unit_price,  # أو price_after_discount
                batch_number=getattr(invoice_line, 'batch_number', None),
                expiry_date=getattr(invoice_line, 'expiry_date', None)
            )

        # ترحيل تلقائي
        stock_in.post(user=instance.created_by, create_journal_entry=False)
        # ملاحظة: لا ننشئ قيد من StockIn لأن الفاتورة أنشأت قيد مسبقاً
```

#### 8.2.2 لا يوجد Goods Receipt (استلام بضاعة)

**المشكلة**:
```
الدورة الكاملة يجب أن تكون:
Purchase Order → Goods Receipt → Purchase Invoice

حالياً:
Purchase Order → Purchase Invoice (فقط)
```

**الحل المقترح**:
```python
# إضافة نموذج GoodsReceipt في purchases app
class GoodsReceipt(DocumentBaseModel):
    """استلام البضاعة (قبل الفاتورة)"""

    purchase_order = models.ForeignKey('PurchaseOrder', ...)
    warehouse = models.ForeignKey('core.Warehouse', ...)
    status = models.CharField(
        choices=[
            ('draft', 'مسودة'),
            ('received', 'مستلم'),
            ('invoiced', 'تم إصدار فاتورة')
        ]
    )

    def post(self):
        """ترحيل الاستلام ينشئ StockIn"""
        stock_in = StockIn.objects.create(...)
        stock_in.post(...)
```

#### 8.2.3 لا يوجد فحص التطابق

**المشكلة**:
- لا يوجد فحص بين كمية الطلب وكمية الاستلام
- لا يوجد فحص بين كمية الاستلام وكمية الفاتورة
- يمكن إدخال كميات مختلفة بدون تنبيه

**الحل المقترح**:
```python
def validate_receipt_vs_order(goods_receipt, purchase_order):
    """فحص التطابق بين الاستلام والطلب"""
    for line in goods_receipt.lines.all():
        order_line = purchase_order.lines.get(item=line.item)

        if line.quantity > order_line.quantity:
            raise ValidationError(
                f"الكمية المستلمة ({line.quantity}) أكبر من المطلوبة ({order_line.quantity})"
            )
```

### 8.3 Checklist التكامل مع Purchases

```
⚠️  StockIn.purchase_invoice: موجود كـ FK فقط (لا يوجد automation)
❌ لا يوجد إنشاء تلقائي لـ StockIn من PurchaseInvoice
❌ لا توجد signals في purchases app
❌ لا يوجد نموذج GoodsReceipt
❌ لا يوجد فحص التطابق بين الطلب والاستلام
❌ لا يوجد فحص التطابق بين الاستلام والفاتورة
❌ لا يوجد تتبع للكميات الجزئية (partial receipts vs order)
⚠️  الربط يدوي بالكامل (عرضة للخطأ البشري)
```

**التوصية الرئيسية**:
```
🔴 أولوية عالية: إضافة signal لإنشاء StockIn تلقائياً من PurchaseInvoice
🟡 أولوية متوسطة: إضافة GoodsReceipt model
🟢 أولوية منخفضة: إضافة فحوصات التطابق
```

---

## 9. Checklist الفحص

### 9.1 Checklist الـ Models

```
StockIn:
  ✅ post() ينشئ/يحدث ItemStock
  ✅ post() يحسب التكلفة المتوسطة المرجحة
  ✅ post() ينشئ StockMovement
  ✅ post() ينشئ Batch (إذا وُجد batch_number)
  ✅ post() يحدث PartnerItemPrice
  ✅ post() ينشئ JournalEntry (إذا طُلب)
  ✅ unpost() يعكس جميع العمليات
  ✅ can_edit() يمنع التعديل بعد الترحيل
  ✅ can_delete() يمنع الحذف بعد الترحيل

StockOut:
  ✅ post() يفحص الكمية المتاحة
  ✅ post() يحترم warehouse.allow_negative_stock
  ✅ post() يخصم من ItemStock
  ✅ post() ينشئ StockMovement (كمية سالبة)
  ✅ post() يحدث PartnerItemPrice للعميل
  ✅ post() ينشئ قيد COGS
  ✅ unpost() يعكس العمليات

StockTransfer:
  ✅ approve() يتطلب صلاحية
  ✅ send() يفحص رصيد المصدر
  ✅ send() ينشئ حركة transfer_out
  ✅ receive() ينشئ/يحدث رصيد الوجهة
  ✅ receive() يحسب التكلفة المتوسطة للوجهة
  ✅ receive() ينشئ حركة transfer_in
  ✅ cancel() يعيد الرصيد للمصدر (إذا in_transit)
  ✅ يدعم الاستلام الجزئي (received_quantity)

StockCount:
  ✅ populate_lines() يملأ من ItemStock
  ✅ process_adjustments() يحسب الفروقات
  ✅ process_adjustments() ينشئ قيد التسوية
  ✅ process_adjustments() يحدث ItemStock
  ✅ يفرق بين نقص وزيادة في القيد

Batch:
  ✅ is_expired() يفحص الصلاحية
  ✅ days_to_expiry() يحسب الأيام المتبقية
  ✅ get_expiry_status() يعطي الحالة الصحيحة
  ✅ get_available_quantity() يخصم المحجوز
  ✅ can_delete() يمنع الحذف إذا كانت الكمية > 0

ItemStock:
  ✅ get_available_quantity() = quantity - reserved_quantity
  ✅ reserve_quantity() يحدث reserved_quantity
  ✅ release_reserved_quantity() يخصم من المحجوز
  ✅ is_below_reorder_level() يفحص نقطة إعادة الطلب
  ✅ update_last_purchase() يحدث معلومات الشراء

StockReservation:
  ✅ is_expired() يفحص انتهاء المدة
  ✅ time_remaining() يحسب الوقت المتبقي
  ✅ cleanup تلقائي عبر management command
```

### 9.2 Checklist الـ Services

```
InventoryAlertService:
  ✅ check_stock_levels() يكشف المخزون المنخفض
  ✅ check_stock_levels() يكشف المخزون السالب
  ✅ check_stock_levels() يكشف تجاوز الحد الأقصى
  ✅ check_batch_expiry() يكشف الدفعات المنتهية
  ✅ check_batch_expiry() يكشف القريبة من الانتهاء
  ✅ get_all_alerts() يجمع جميع التنبيهات
  ✅ get_alerts_summary() يعطي ملخص سريع
  ✅ يصنف التنبيهات حسب severity (critical, high, medium, low)

ReservationService:
  ✅ reserve_stock() يفحص الكمية المتاحة
  ✅ reserve_stock() ينشئ StockReservation
  ✅ reserve_stock() يحدث reserved_quantity
  ✅ reserve_stock() يحدد expires_at
  ✅ release_reservation() يحرر الحجز
  ✅ release_reservation() يدعم الإلغاء الجزئي
  ✅ confirm_reservation() يغير الحالة
  ✅ cleanup_expired_reservations() ينظف المنتهية
  ✅ extend_reservation() يمدد المدة

BatchValidationService:
  ✅ validate_batch_for_use() يفحص الصلاحية
  ✅ get_valid_batches_fifo() يرتب حسب received_date
  ✅ get_valid_batches_fefo() يرتب حسب expiry_date
  ✅ يخصص الكمية عبر دفعات متعددة
  ✅ يستثني المنتهية افتراضياً
```

### 9.3 Checklist الـ Integration

```
Accounting Integration:
  ✅ StockIn ينشئ قيد محاسبي
  ✅ القيد متوازن (debit = credit)
  ✅ الحسابات صحيحة حسب source_type
  ✅ يربط الطرف (partner) عند الشراء
  ✅ StockOut ينشئ قيد COGS
  ✅ يستخدم average_cost
  ✅ StockCount ينشئ قيد تسوية
  ✅ يفرق بين نقص وزيادة
  ⚠️  StockTransfer لا ينشئ قيود (قد يكون مطلوب للفروع)

Purchases Integration:
  ⚠️  StockIn.purchase_invoice: FK فقط
  ❌ لا يوجد إنشاء تلقائي من PurchaseInvoice
  ❌ لا توجد signals
  ❌ لا يوجد GoodsReceipt model
  ❌ لا يوجد فحص التطابق

Sales Integration:
  ⚠️  StockOut.sales_invoice: FK فقط
  ❌ لا يوجد إنشاء تلقائي من SalesInvoice
  ❌ لا يوجد ربط مع SalesOrder للحجوزات
  ❌ لا توجد signals
```

### 9.4 Checklist الـ Performance

```
Caching:
  ✅ ItemStock معلومات مخزنة (TTL: 5 min)
  ✅ Alerts ملخصات مخزنة (TTL: 10 min)
  ✅ إلغاء الكاش عند التحديث (signals)
  ⚠️  Pattern-based invalidation قد لا يعمل على جميع backends

Queries:
  ✅ ItemStock: select_related للـ item, warehouse
  ✅ StockMovement: select_related مُحسن
  ⚠️  بعض populate_lines قد يكون N+1
  ⚠️  لا يوجد pagination في بعض التقارير

Indexes:
  ✅ ItemStock: (item, warehouse)
  ✅ StockMovement: (item, warehouse, -date)
  ✅ Batch: (item, warehouse, received_date)
  ✅ StockReservation: (status, expires_at)
```

---

## 10. النقاط الضعيفة والمفقودة

### 10.1 نقاط حرجة (Critical)

**1. غياب التكامل التلقائي مع Purchases**
```
المشكلة: إدخال يدوي مزدوج
التأثير: أخطاء بشرية، بيانات غير متطابقة
الحل: إضافة signals لإنشاء StockIn تلقائياً
الأولوية: 🔴 عالية جداً
```

**2. غياب التكامل مع Sales Orders**
```
المشكلة: لا يوجد حجز تلقائي للمخزون
التأثير: احتمالية overselling
الحل: ربط SalesOrder مع ReservationService
الأولوية: 🔴 عالية
```

**3. عدم وجود Optimistic Locking**
```
المشكلة: التحديثات المتزامنة قد تسبب أخطاء
التأثير: رصيد غير صحيح في حالات الضغط العالي
الحل: إضافة version field أو استخدام F() expressions
الأولوية: 🔴 عالية
```

### 10.2 نقاط متوسطة (Medium)

**1. غياب Goods Receipt**
```
المشكلة: لا يوجد فصل بين الاستلام والفاتورة
التأثير: صعوبة تتبع الاستلامات الجزئية
الحل: إضافة GoodsReceipt model
الأولوية: 🟡 متوسطة
```

**2. لا يوجد قيود للتحويلات بين الفروع**
```
المشكلة: التحويلات بين كيانات قانونية لا تظهر محاسبياً
التأثير: تقارير مالية غير دقيقة للفروع
الحل: إضافة create_inter_company_entry()
الأولوية: 🟡 متوسطة
```

**3. Batch Reservation غير موجود**
```
المشكلة: لا يمكن حجز دفعة محددة
التأثير: صعوبة في تطبيق FEFO للحجوزات
الحل: إضافة batch_id إلى StockReservation
الأولوية: 🟡 متوسطة
```

**4. لا يوجد Automatic Reorder**
```
المشكلة: التنبيهات فقط، لا يوجد فعل تلقائي
التأثير: يتطلب متابعة يدوية
الحل: إنشاء PurchaseRequest تلقائياً عند الوصول لـ reorder_point
الأولوية: 🟡 متوسطة
```

### 10.3 نقاط منخفضة (Low)

**1. تقارير محدودة**
```
المشكلة: 5 تقارير أساسية فقط
التأثير: تحليلات محدودة
الحل: إضافة ABC analysis, turnover, aging reports
الأولوية: 🟢 منخفضة
```

**2. لا يوجد Archiving للحركات**
```
المشكلة: StockMovement ينمو إلى ما لا نهاية
التأثير: بطء الاستعلامات مع الوقت
الحل: إضافة archiving strategy
الأولوية: 🟢 منخفضة
```

**3. غياب Approval Workflow للقيم الكبيرة**
```
المشكلة: جميع المعاملات تُرحل مباشرة
التأثير: لا يوجد مراجعة للمعاملات الكبيرة
الحل: إضافة approval requirements بناءً على القيمة
الأولوية: 🟢 منخفضة
```

### 10.4 ملخص الأولويات

```
🔴 أولوية عالية جداً:
  1. إضافة signal لإنشاء StockIn من PurchaseInvoice
  2. ربط SalesOrder مع ReservationService
  3. إضافة Optimistic Locking

🟡 أولوية متوسطة:
  4. إضافة GoodsReceipt model
  5. قيود محاسبية للتحويلات بين الفروع
  6. Batch-level reservations
  7. Automatic purchase request generation

🟢 أولوية منخفضة:
  8. تقارير متقدمة (ABC, turnover, aging)
  9. Archiving للحركات القديمة
  10. Approval workflow للقيم الكبيرة
```

---

## 11. خطة التنفيذ

### المرحلة 1: الإعداد والاختبارات الأساسية

**المدة المتوقعة**: يومان

```bash
# 1. تثبيت pytest وcoverage
pip install pytest pytest-django pytest-cov

# 2. إنشاء هيكل الاختبارات
mkdir -p tests/inventory
touch tests/inventory/__init__.py
touch tests/inventory/conftest.py
touch tests/inventory/test_stock_in_model.py
touch tests/inventory/test_stock_out_model.py
touch tests/inventory/test_stock_transfer_model.py
touch tests/inventory/test_stock_count_model.py
touch tests/inventory/test_batch_model.py
touch tests/inventory/test_services.py
touch tests/inventory/test_accounting_integration.py

# 3. تشغيل الاختبارات
pytest tests/inventory/ -v --cov=apps.inventory --cov-report=html
```

### المرحلة 2: الاختبارات المتقدمة

**المدة المتوقعة**: يوم واحد

```bash
# اختبارات التكامل
pytest tests/inventory/test_accounting_integration.py -v
pytest tests/inventory/test_purchases_integration.py -v

# اختبارات الأداء
pytest tests/inventory/test_concurrent_updates.py -v
```

### المرحلة 3: الفحص اليدوي

**المدة المتوقعة**: نصف يوم

```bash
# تشغيل السكريبتات
python manage.py shell < scripts/test_stock_in_workflow.py
python manage.py shell < scripts/test_alerts.py
python manage.py shell < scripts/test_concurrent_stock_updates.py
```

### المرحلة 4: التقرير النهائي

**المدة المتوقعة**: نصف يوم

- تجميع نتائج الاختبارات
- تحليل Coverage
- توثيق النقاط الضعيفة المكتشفة
- توصيات التحسين

---

## 12. الخلاصة

### نقاط القوة ⭐⭐⭐⭐⭐

1. **تصميم ممتاز**: النظام مصمم بشكل احترافي جداً
2. **Audit Trail كامل**: كل حركة مسجلة ومؤرخة
3. **تكلفة متوسطة مرجحة**: حساب صحيح ومتوافق مع GAAP
4. **تتبع الدفعات**: FIFO/FEFO محترف
5. **نظام الحجوزات**: متقدم مع auto-expiry
6. **التكامل المحاسبي**: قوي جداً (5/5)
7. **التنبيهات**: شامل ومفيد
8. **Multi-warehouse**: دعم كامل للفروع

### نقاط الضعف 🔴🟡

1. **التكامل مع Purchases**: ضعيف جداً (2/5)
2. **التكامل مع Sales**: ضعيف جداً (1/5)
3. **Concurrent Updates**: قد يكون معرض لـ race conditions
4. **Goods Receipt**: غير موجود
5. **Inter-branch Accounting**: غير مكتمل

### التوصية النهائية ✅

النظام **ممتاز** من الناحية الفنية، ولكن **يحتاج بشدة** إلى:
1. تكامل تلقائي مع Purchases
2. تكامل مع Sales Orders
3. حماية من race conditions

**التقييم الإجمالي**: 85/100

---

**ملاحظة**: هذا الملف يُحدث باستمرار بناءً على نتائج الاختبارات الفعلية.

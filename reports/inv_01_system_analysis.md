# تقرير تحليل نظام المخزون (Inventory System)
## تاريخ التحليل: 2025-11-28

---

## 1. نظرة عامة على النظام

نظام المخزون هو جزء أساسي من نظام ERP يدير:
- سندات الإدخال والإخراج
- التحويلات بين المستودعات
- الجرد الدوري
- تتبع الدفعات (Batches)
- حركة المواد
- أرصدة المخزون

---

## 2. تحليل النماذج (Models)

### 2.1 StockDocument (نموذج أساسي مجرد)
```
الحقول:
- document_type: نوع السند (in/out/transfer)
- number: رقم السند (auto-generated)
- date: التاريخ
- warehouse: المستودع (ForeignKey → Warehouse)
- reference: المرجع
- is_posted: حالة الترحيل
- posted_date/posted_by: معلومات الترحيل
- notes: ملاحظات

القيود: abstract = True
```

### 2.2 StockIn (سند الإدخال)
```
الحقول الإضافية:
- source_type: مصدر الإدخال (purchase/return/production/opening/adjustment/other)
- supplier: المورد (ForeignKey → BusinessPartner, optional)
- purchase_invoice: فاتورة المشتريات (ForeignKey → PurchaseInvoice, optional)
- journal_entry: القيد المحاسبي (ForeignKey → JournalEntry, optional)

Meta:
- verbose_name: سند إدخال
- unique_together: [company, number]
- ordering: [-date, -number]
- permissions: can_post_stock_document

الدوال الرئيسية:
- post(): ترحيل السند وتحديث المخزون
- unpost(): إلغاء الترحيل
- create_journal_entry(): إنشاء قيد محاسبي
```

### 2.3 StockOut (سند الإخراج)
```
الحقول الإضافية:
- destination_type: جهة الإخراج (sales/return/consumption/damage/adjustment/other)
- customer: العميل (ForeignKey → BusinessPartner, optional)
- sales_invoice: فاتورة المبيعات (ForeignKey → SalesInvoice, optional)
- journal_entry: القيد المحاسبي

الدوال الرئيسية:
- post(): ترحيل وخصم المخزون (بمتوسط التكلفة)
- unpost(): إلغاء الترحيل
- create_journal_entry(): إنشاء قيد محاسبي
```

### 2.4 StockDocumentLine (سطور السندات)
```
الحقول:
- stock_in/stock_out: العلاقة مع السند
- item: المادة (ForeignKey → Item)
- item_variant: المتغير (ForeignKey → ItemVariant, optional)
- quantity: الكمية (min: 0.001)
- unit_cost: تكلفة الوحدة
- total_cost: التكلفة الإجمالية (computed)
- batch_number: رقم الدفعة
- expiry_date: تاريخ الانتهاء
- notes: ملاحظات

التحقق (clean):
- إذا المادة لها متغيرات، يجب تحديد متغير
- المتغير يجب أن يتبع المادة
```

### 2.5 StockTransfer (التحويل بين المستودعات)
```
الحقول الإضافية:
- destination_warehouse: المستودع الهدف
- approved_by/approval_date: الموافقة
- received_by/received_date: الاستلام
- status: الحالة (draft/pending/approved/in_transit/received/cancelled)

الدوال:
- approve(): اعتماد التحويل
- send(): إرسال (إخراج من المصدر)
- receive(): استلام (إدخال للهدف)
- cancel(): إلغاء التحويل
```

### 2.6 StockTransferLine (سطور التحويل)
```
الحقول:
- transfer: التحويل
- item/item_variant: المادة والمتغير
- barcode: الباركود
- quantity: الكمية
- received_quantity: الكمية المستلمة
- unit_cost/total_cost: التكلفة
- batch_number/expiry_date: معلومات الدفعة
```

### 2.7 StockMovement (حركة المواد)
```
الحقول:
- date: التاريخ والوقت (auto)
- movement_type: نوع الحركة (in/out/transfer_out/transfer_in)
- item/item_variant: المادة
- warehouse: المستودع
- quantity: الكمية (+ للإدخال، - للإخراج)
- unit_cost/total_cost: التكلفة
- balance_before: الرصيد قبل الحركة
- balance_quantity/balance_value: الرصيد بعد الحركة
- reference_type/reference_id/reference_number: المرجع
- branch: الفرع

Indexes:
- [item, warehouse, -date]
- [reference_type, reference_id]
- [movement_type, -date]
```

### 2.8 StockCount (الجرد)
```
الحقول:
- number: رقم الجرد (auto)
- date: تاريخ الجرد
- count_type: نوع الجرد (periodic/annual/cycle/special)
- warehouse: المستودع
- count_team: فريق الجرد (ManyToMany → User)
- supervisor: المشرف
- status: الحالة (planned/in_progress/completed/approved/cancelled)
- approved_by/approval_date: الاعتماد
- adjustment_entry: قيد التسوية
```

### 2.9 StockCountLine (سطور الجرد)
```
الحقول:
- count: الجرد
- item: المادة
- system_quantity: الكمية بالنظام
- counted_quantity: الكمية الفعلية
- difference_quantity: الفرق (computed)
- unit_cost: تكلفة الوحدة
- system_value/counted_value/difference_value: القيم (computed)
- adjustment_reason: سبب الفرق
```

### 2.10 ItemStock (رصيد المادة)
```
الحقول:
- item/item_variant: المادة
- warehouse: المستودع
- quantity: الكمية المتاحة
- reserved_quantity: الكمية المحجوزة
- average_cost: متوسط التكلفة
- total_value: القيمة الإجمالية
- last_movement_date: تاريخ آخر حركة
- opening_balance/opening_value: الرصيد الافتتاحي
- last_purchase_price/last_purchase_total/last_purchase_date/last_supplier: آخر شراء
- min_level/max_level/reorder_point: حدود المخزون
- storage_location: موقع التخزين

unique_together: [item, item_variant, warehouse, company]

الدوال:
- get_available_quantity(): الكمية المتاحة
- reserve_quantity(): حجز كمية
- release_reserved_quantity(): إلغاء حجز
- is_below_reorder_level(): تحت نقطة إعادة الطلب؟
- update_last_purchase(): تحديث آخر شراء
- get_total_stock(): إجمالي المخزون (class method)
- transfer_between_warehouses(): تحويل سريع (class method)
```

### 2.11 Batch (الدفعات)
```
الحقول:
- item/item_variant: المادة
- warehouse: المستودع
- batch_number: رقم الدفعة
- manufacturing_date/expiry_date: تواريخ
- quantity/reserved_quantity: الكميات
- unit_cost/total_value: التكلفة
- source_document/source_id: المصدر
- received_date: تاريخ الاستلام

unique_together: [item, item_variant, warehouse, batch_number, company]
ordering: [received_date] (FIFO)

الدوال:
- is_expired(): منتهية الصلاحية؟
- days_to_expiry(): أيام حتى الانتهاء
- get_expiry_status(): حالة الصلاحية
```

---

## 3. تحليل العلاقات

### 3.1 علاقات مع Core
```
Item ← StockDocumentLine, StockTransferLine, StockMovement, StockCountLine, ItemStock, Batch
ItemVariant ← (نفس العلاقات)
Warehouse ← StockDocument, StockTransfer, StockMovement, StockCount, ItemStock, Batch
BusinessPartner ← StockIn (supplier), StockOut (customer), ItemStock (last_supplier)
User ← posted_by, created_by, approved_by, received_by, count_team, supervisor
Branch ← StockMovement
```

### 3.2 علاقات مع Purchases
```
PurchaseInvoice → StockIn (purchase_invoice)
- عند ترحيل فاتورة المشتريات، يتم إنشاء StockIn تلقائياً
- الكميات والتكاليف تُنسخ من الفاتورة
```

### 3.3 علاقات مع Sales
```
SalesInvoice → StockOut (sales_invoice)
- عند ترحيل فاتورة المبيعات، يتم إنشاء StockOut تلقائياً
```

### 3.4 علاقات مع Accounting
```
JournalEntry ← StockIn, StockOut, StockCount
Account ← (للقيود المحاسبية)
FiscalYear/AccountingPeriod ← (للتحقق من الفترة المالية)
```

---

## 4. تحليل الـ Forms

### 4.1 StockInForm
- الحقول: date, warehouse, source_type, supplier, purchase_invoice, reference, notes
- تصفية الموردين والمستودعات حسب الشركة

### 4.2 StockDocumentLineForm
- الحقول: item, item_variant, quantity, unit_cost, batch_number, expiry_date, notes
- مع Formset: StockInLineFormSet (extra=5, min_num=1)

### 4.3 StockOutForm
- مشابه لـ StockInForm مع customer و sales_invoice
- StockOutLineFormSet (extra=1, min_num=1)

### 4.4 StockTransferForm
- الحقول: date, warehouse, destination_warehouse, reference, notes
- التحقق: لا يمكن التحويل لنفس المستودع
- StockTransferLineFormSet

### 4.5 StockCountForm
- الحقول: date, count_type, warehouse, supervisor, count_team, notes
- StockCountLineFormSet

### 4.6 ItemStockForm
- للتعديل: min_level, max_level, reorder_point, storage_location

### 4.7 BatchForm
- جميع حقول الدفعة

---

## 5. تحليل الـ Views

### 5.1 Dashboard
- InventoryDashboardView: إحصائيات المخزون

### 5.2 Stock In (سندات الإدخال)
- StockInListView: قائمة مع بحث وتصفية
- StockInCreateView: إنشاء مع Formset
- StockInUpdateView: تعديل (ممنوع للمرحل)
- StockInDetailView: عرض التفاصيل
- StockInPostView: ترحيل
- StockInUnpostView: إلغاء ترحيل

### 5.3 Stock Out (سندات الإخراج)
- نفس البنية مع التحقق من الكمية المتاحة

### 5.4 Transfers (التحويلات)
- StockTransferListView/CreateView/DetailView
- عمليات: approve, send, receive, cancel

### 5.5 Stock Count (الجرد)
- StockCountListView/CreateView/DetailView/UpdateView
- StockCountProcessView: معالجة فروقات الجرد

### 5.6 Batches (الدفعات)
- BatchListView/DetailView/CreateView/UpdateView
- BatchExpiredReportView: تقرير الدفعات المنتهية

### 5.7 Reports (التقارير)
- StockReportView: تقرير المخزون
- StockMovementReportView: تقرير الحركات

---

## 6. الصلاحيات المستخدمة

```python
# Django Permissions
inventory.view_stockin
inventory.add_stockin
inventory.change_stockin
inventory.delete_stockin

inventory.view_stockout
inventory.add_stockout
inventory.change_stockout

inventory.view_stocktransfer
inventory.add_stocktransfer
inventory.change_stocktransfer

inventory.view_stockcount
inventory.add_stockcount
inventory.change_stockcount

inventory.view_batch
inventory.add_batch
inventory.change_batch
inventory.delete_batch

# Custom Permissions
inventory.can_post_stock_document
inventory.can_approve_transfer
```

---

## 7. نقاط التكامل الحرجة

### 7.1 مع نظام المشتريات
```
PurchaseInvoice.post() → StockIn.create() + StockIn.post()
- ينشئ سند إدخال تلقائياً
- ينسخ الكميات والتكاليف
- يُحدّث أرصدة المخزون
- يُحدّث معلومات آخر شراء
- يُحدّث أسعار المورد (PartnerItemPrice)
```

### 7.2 مع نظام المحاسبة
```
StockIn.post() → JournalEntry.create()
- مدين: حساب المخزون
- دائن: حسب المصدر (مورد/أرباح محتجزة/عملاء...)

StockOut.post() → JournalEntry.create()
- مدين: تكلفة البضاعة المباعة
- دائن: حساب المخزون

StockCount (فروقات) → JournalEntry.create()
```

---

## 8. طريقة تقييم المخزون

النظام يستخدم **المتوسط المرجح (Weighted Average)**:

```python
# عند الإدخال
new_quantity = old_quantity + incoming_quantity
new_value = old_value + incoming_value
average_cost = new_value / new_quantity

# عند الإخراج
unit_cost = stock.average_cost
total_cost = quantity * average_cost
new_quantity = old_quantity - quantity
new_value = old_value - total_cost
```

---

## 9. ملاحظات فنية

### 9.1 الأداء
- استخدام select_related و prefetch_related في الـ Views
- Indexes على الحقول المستخدمة في البحث والتصفية

### 9.2 الأمان
- التحقق من الصلاحيات في كل View
- منع تعديل السندات المرحلة
- التحقق من الكميات المتاحة قبل الإخراج

### 9.3 الـ Transactions
- استخدام @transaction.atomic للعمليات الحرجة
- post, unpost, send, receive, cancel

---

## 10. الخلاصة

نظام المخزون متكامل وشامل، يوفر:
- ✅ إدارة سندات الإدخال والإخراج
- ✅ التحويلات بين المستودعات مع workflow
- ✅ الجرد الدوري مع معالجة الفروقات
- ✅ تتبع الدفعات وتواريخ الصلاحية
- ✅ تكامل قوي مع المشتريات والمحاسبة
- ✅ تقييم بالمتوسط المرجح
- ✅ حدود مخزون ونقاط إعادة طلب

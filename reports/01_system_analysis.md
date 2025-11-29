# تقرير تحليل نظام المشتريات الشامل

**التاريخ:** 2025-11-28
**المحلل:** Claude AI
**الإصدار:** 1.0

---

## 1. نظرة عامة على النظام

نظام المشتريات هو وحدة متكاملة ضمن نظام ERP شامل، يدعم:
- **متعدد الشركات والفروع** - كل شركة لها بياناتها المنفصلة
- **اللغة العربية** - واجهة RTL كاملة
- **التكامل المحاسبي** - توليد قيود تلقائية
- **سير عمل الموافقات** - Workflow متعدد المستويات

---

## 2. نماذج البيانات (Models)

### 2.1 فواتير المشتريات (PurchaseInvoice)
**الموقع:** `apps/purchases/models.py:17-583`

#### الحقول الرئيسية:
| الحقل | النوع | مطلوب | الوصف |
|-------|-------|-------|-------|
| `number` | CharField(50) | نعم (تلقائي) | رقم الفاتورة - يُولد تلقائياً |
| `date` | DateField | نعم | تاريخ الفاتورة |
| `invoice_type` | CharField(10) | نعم | نوع: purchase/return |
| `supplier` | ForeignKey | نعم | المورد |
| `warehouse` | ForeignKey | نعم | المستودع |
| `payment_method` | ForeignKey | نعم | طريقة الدفع |
| `currency` | ForeignKey | نعم | العملة |
| `discount_type` | CharField(10) | لا | percentage/amount |
| `discount_value` | DecimalField | لا | قيمة الخصم |
| `is_posted` | BooleanField | - | حالة الترحيل |

#### العلاقات:
- `supplier` → `BusinessPartner` (PROTECT)
- `warehouse` → `Warehouse` (PROTECT)
- `currency` → `Currency` (PROTECT)
- `journal_entry` → `JournalEntry` (SET_NULL)
- `goods_receipt` → `GoodsReceipt` (PROTECT) - مطابقة ثلاثية

#### Validators:
- `discount_value`: MinValueValidator(0)

#### Meta Options:
```python
unique_together = [['company', 'number']]
ordering = ['-date', '-number']
indexes = 5 فهارس للأداء
```

#### الدوال الرئيسية:
1. **`save()`** - توليد رقم الفاتورة تلقائياً
2. **`calculate_totals()`** - حساب مجاميع الفاتورة
3. **`post(user)`** - ترحيل الفاتورة وإنشاء القيد المحاسبي
4. **`unpost()`** - إلغاء الترحيل

---

### 2.2 سطور فاتورة المشتريات (PurchaseInvoiceItem)
**الموقع:** `apps/purchases/models.py:585-866`

#### الحقول الرئيسية:
| الحقل | النوع | مطلوب | الوصف |
|-------|-------|-------|-------|
| `invoice` | ForeignKey | نعم | الفاتورة الرئيسية |
| `item` | ForeignKey | لا | المادة |
| `item_variant` | ForeignKey | لا | المتغير |
| `quantity` | DecimalField | نعم | الكمية |
| `unit` | ForeignKey | نعم | وحدة القياس |
| `unit_price` | DecimalField | نعم | السعر |
| `discount_percentage` | DecimalField | لا | خصم % |
| `tax_rate` | DecimalField | لا | نسبة الضريبة |
| `tax_included` | BooleanField | لا | ضريبة شاملة |

#### ميزات متقدمة:
- دعم **تحويل الوحدات** (purchase_uom, conversion_rate)
- دعم **الدفعات** (batch_number, expiry_date)
- حساب **الضريبة** الشاملة وغير الشاملة

---

### 2.3 أوامر الشراء (PurchaseOrder)
**الموقع:** `apps/purchases/models.py:869-1189`

#### حالات أمر الشراء:
| الحالة | الكود | التالي |
|--------|-------|--------|
| مسودة | draft | pending_approval |
| بانتظار الموافقة | pending_approval | approved/rejected |
| معتمد | approved | sent |
| مرسل للمورد | sent | partial/completed |
| استلام جزئي | partial | completed |
| مكتمل | completed | - |
| ملغي | cancelled | - |
| مرفوض | rejected | draft |

#### Workflow Methods:
1. `submit_for_approval()` - إرسال للموافقة
2. `approve(user)` - الموافقة
3. `reject(user, reason)` - الرفض
4. `send_to_supplier()` - إرسال للمورد
5. `convert_to_invoice()` - تحويل لفاتورة
6. `cancel()` - إلغاء

---

### 2.4 طلبات الشراء (PurchaseRequest)
**الموقع:** `apps/purchases/models.py:1345-1502`

- طلب داخلي قبل إنشاء أمر الشراء
- يرتبط بقسم وموظف
- يدعم الأولويات (منخفضة/عادية/عالية/عاجلة)

---

### 2.5 طلب عروض الأسعار (PurchaseQuotationRequest - RFQ)
**الموقع:** `apps/purchases/models.py:1559-1815`

- إرسال طلبات أسعار لعدة موردين
- مقارنة العروض
- ترسية العرض الفائز

---

### 2.6 عروض الأسعار (PurchaseQuotation)
**الموقع:** `apps/purchases/models.py:1818-2186`

- استلام عروض من الموردين
- التقييم (0-100)
- تحويل للأمر شراء

---

### 2.7 عقود الشراء (PurchaseContract)
**الموقع:** `apps/purchases/models.py:2189-2614`

- عقود طويلة الأجل
- متابعة التنفيذ (الكميات المطلوبة/المستلمة)
- تجديد وإنهاء العقود

---

### 2.8 استلام البضاعة (GoodsReceipt)
**الموقع:** `apps/purchases/models.py:2616-2800+`

- استلام البضاعة من المورد
- **مطابقة ثلاثية**: أمر الشراء ← محضر الاستلام ← الفاتورة
- فحص الجودة

---

## 3. النماذج (Forms)

### 3.1 نموذج فاتورة المشتريات
**الموقع:** `apps/purchases/forms/invoice_forms.py`

#### الحقول:
- invoice_type, date, branch, supplier, warehouse
- payment_method, currency
- discount_type, discount_value, discount_affects_cost
- supplier_account, discount_account, notes

#### التحققات:
1. رسائل خطأ مخصصة بالعربية
2. تصفية الموردين حسب الشركة
3. تصفية المستودعات حسب الشركة
4. قيم افتراضية (تاريخ اليوم، عملة JOD)

### 3.2 نموذج سطر الفاتورة
**الموقع:** `apps/purchases/forms/invoice_forms.py:247-519`

#### الحقول:
- item, item_variant, quantity, unit, unit_price
- purchase_uom, purchase_quantity, conversion_rate
- discount_percentage, discount_amount
- tax_rate, tax_included
- batch_number, expiry_date

#### التحققات:
```python
def clean(self):
    # إذا تم اختيار مادة، تأكد من وجود السعر والكمية والوحدة
    if item:
        if not unit_price: raise ValidationError(...)
        if not quantity: raise ValidationError(...)
        if not unit: raise ValidationError(...)
```

### 3.3 Formset
```python
PurchaseInvoiceItemFormSet = inlineformset_factory(
    PurchaseInvoice,
    PurchaseInvoiceItem,
    extra=5,
    can_delete=True,
    min_num=0
)
```

---

## 4. العروض (Views)

### 4.1 فواتير المشتريات

| View | النوع | URL | الصلاحية |
|------|-------|-----|----------|
| PurchaseInvoiceListView | ListView | /invoices/ | view_purchaseinvoice |
| PurchaseInvoiceDetailView | DetailView | /invoices/<pk>/ | view_purchaseinvoice |
| PurchaseInvoiceCreateView | CreateView | /invoices/create/ | add_purchaseinvoice |
| PurchaseInvoiceUpdateView | UpdateView | /invoices/<pk>/update/ | change_purchaseinvoice |
| PurchaseInvoiceDeleteView | DeleteView | /invoices/<pk>/delete/ | delete_purchaseinvoice |
| post_invoice | Function | /invoices/<pk>/post/ | add_purchaseinvoice |
| unpost_invoice | Function | /invoices/<pk>/unpost/ | change_purchaseinvoice |

### 4.2 أوامر الشراء

| View | النوع | URL | الوصف |
|------|-------|-----|-------|
| PurchaseOrderListView | ListView | /orders/ | قائمة الأوامر |
| PurchaseOrderDetailView | DetailView | /orders/<pk>/ | تفاصيل الأمر |
| PurchaseOrderCreateView | CreateView | /orders/create/ | إنشاء أمر |
| submit_for_approval | Function | /orders/<pk>/submit/ | إرسال للموافقة |
| approve_order | Function | /orders/<pk>/approve/ | الموافقة |
| reject_order | Function | /orders/<pk>/reject/ | الرفض |
| convert_to_invoice | Function | /orders/<pk>/convert-to-invoice/ | تحويل لفاتورة |

---

## 5. روابط URL

### 5.1 الهيكل العام
```
/purchases/
├── dashboard/                    # لوحة التحكم
├── invoices/                     # الفواتير
│   ├── create/
│   ├── <pk>/
│   ├── <pk>/update/
│   ├── <pk>/delete/
│   ├── <pk>/post/
│   └── <pk>/unpost/
├── orders/                       # أوامر الشراء
│   ├── create/
│   ├── <pk>/
│   ├── <pk>/submit/
│   ├── <pk>/approve/
│   ├── <pk>/reject/
│   └── <pk>/convert-to-invoice/
├── requests/                     # طلبات الشراء
├── rfqs/                         # طلبات عروض الأسعار
├── quotations/                   # عروض الأسعار
├── contracts/                    # العقود
├── goods-receipts/               # استلام البضاعة
└── reports/                      # التقارير
```

### 5.2 AJAX Endpoints
- `/ajax/invoices/item-search/` - بحث المواد
- `/ajax/invoices/get-supplier-price/` - جلب سعر المورد
- `/ajax/invoices/get-stock-multi-branch/` - المخزون في الفروع
- `/ajax/invoices/save-draft/` - حفظ مسودة

---

## 6. القوالب (Templates)

### 6.1 قائمة القوالب:
```
apps/purchases/templates/purchases/
├── dashboard.html
├── invoices/
│   ├── invoice_list.html
│   ├── invoice_detail.html
│   ├── invoice_form.html
│   └── invoice_confirm_delete.html
├── orders/
│   ├── order_list.html
│   ├── order_detail.html
│   ├── order_form.html
│   └── order_confirm_delete.html
├── requests/
├── rfqs/
├── quotations/
├── contracts/
├── goods_receipt/
└── reports/
    ├── reports_list.html
    ├── purchases_summary.html
    ├── supplier_performance.html
    ├── items_purchases.html
    ├── purchase_orders.html
    └── contracts.html
```

---

## 7. التكامل المحاسبي

### 7.1 القيد المحاسبي عند الترحيل:

```
عند ترحيل فاتورة مشتريات:
───────────────────────────────
مدين: المخزون (حسب المادة)          XXX
مدين: ضريبة المشتريات (إن وجدت)    XXX
      دائن: الموردون                      XXX
      دائن: خصم المشتريات (إن وجد)       XXX
```

### 7.2 الحسابات الافتراضية:
- `120000` - المخزون
- `120400` - ضريبة المشتريات القابلة للخصم
- `210000` - الموردون
- `530000` - خصم مشتريات

---

## 8. الصلاحيات

### 8.1 صلاحيات Django:
- `purchases.add_purchaseinvoice`
- `purchases.change_purchaseinvoice`
- `purchases.delete_purchaseinvoice`
- `purchases.view_purchaseinvoice`
- `purchases.approve_purchase_order` (صلاحية مخصصة)
- `purchases.confirm_goods_receipt` (صلاحية مخصصة)

---

## 9. الميزات المتقدمة

### 9.1 المطابقة الثلاثية (3-Way Matching)
```
أمر الشراء ← محضر الاستلام ← فاتورة المشتريات
```
- التحقق من تطابق الكميات
- ربط المستندات ببعضها

### 9.2 تحويل الوحدات
- الشراء بوحدة (كرتونة) وتخزين بوحدة أخرى (قطعة)
- معامل تحويل محفوظ

### 9.3 دعم الدفعات
- رقم الدفعة
- تاريخ الانتهاء

---

## 10. نقاط القوة

1. **بنية معمارية قوية** - فصل واضح بين Models, Views, Forms
2. **سير عمل متكامل** - Workflow من الطلب للفاتورة
3. **تكامل محاسبي** - قيود تلقائية
4. **أمان** - صلاحيات على كل مستوى
5. **أداء** - فهارس قاعدة بيانات
6. **مرونة** - تحويل وحدات، خصومات، ضرائب

---

## 11. نقاط للتحسين

1. ❗ استخدام `sys.stdout` للتصحيح في Production
2. ❗ عدم وجود اختبارات وحدة كافية
3. ⚠️ بعض الـ querysets قد تسبب N+1
4. ⚠️ الحاجة لـ caching للبيانات المتكررة

---

## 12. الإحصائيات

| العنصر | العدد |
|--------|-------|
| Models | 12 |
| Forms | 15+ |
| Views | 50+ |
| Templates | 41 |
| URL Patterns | 90+ |
| AJAX Endpoints | 20+ |
| أسطر الكود (models.py) | 2800+ |

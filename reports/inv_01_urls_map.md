# خريطة URLs لنظام المخزون
## URL Map - Inventory System

---

## الـ Namespace: `inventory`

## 1. لوحة التحكم (Dashboard)

| URL | Name | View | Method |
|-----|------|------|--------|
| `/inventory/` | `dashboard` | InventoryDashboardView | GET |

---

## 2. سندات الإدخال (Stock In)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/stock-in/` | `stock_in_list` | StockInListView | GET | قائمة السندات |
| `/inventory/stock-in/create/` | `stock_in_create` | StockInCreateView | GET, POST | إنشاء سند |
| `/inventory/stock-in/<pk>/` | `stock_in_detail` | StockInDetailView | GET | تفاصيل السند |
| `/inventory/stock-in/<pk>/update/` | `stock_in_update` | StockInUpdateView | GET, POST | تعديل السند |
| `/inventory/stock-in/<pk>/post/` | `stock_in_post` | StockInPostView | POST | ترحيل السند |
| `/inventory/stock-in/<pk>/unpost/` | `stock_in_unpost` | StockInUnpostView | POST | إلغاء الترحيل |

---

## 3. سندات الإخراج (Stock Out)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/stock-out/` | `stock_out_list` | StockOutListView | GET | قائمة السندات |
| `/inventory/stock-out/create/` | `stock_out_create` | StockOutCreateView | GET, POST | إنشاء سند |
| `/inventory/stock-out/<pk>/` | `stock_out_detail` | StockOutDetailView | GET | تفاصيل السند |
| `/inventory/stock-out/<pk>/update/` | `stock_out_update` | StockOutUpdateView | GET, POST | تعديل السند |
| `/inventory/stock-out/<pk>/post/` | `stock_out_post` | StockOutPostView | POST | ترحيل السند |
| `/inventory/stock-out/<pk>/unpost/` | `stock_out_unpost` | StockOutUnpostView | POST | إلغاء الترحيل |

---

## 4. التحويلات (Stock Transfers)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/transfers/` | `transfer_list` | StockTransferListView | GET | قائمة التحويلات |
| `/inventory/transfers/create/` | `transfer_create` | StockTransferCreateView | GET, POST | إنشاء تحويل |
| `/inventory/transfers/<pk>/` | `transfer_detail` | StockTransferDetailView | GET | تفاصيل التحويل |

**ملاحظة:** عمليات approve, send, receive, cancel يجب إضافتها

---

## 5. الجرد (Stock Count)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/stock-count/` | `count_list` | StockCountListView | GET | قائمة الجرد |
| `/inventory/stock-count/create/` | `count_create` | StockCountCreateView | GET, POST | إنشاء جرد |
| `/inventory/stock-count/<pk>/` | `count_detail` | StockCountDetailView | GET | تفاصيل الجرد |
| `/inventory/stock-count/<pk>/update/` | `count_update` | StockCountUpdateView | GET, POST | تعديل الجرد |
| `/inventory/stock-count/<pk>/process/` | `count_process` | StockCountProcessView | POST | معالجة الفروقات |

---

## 6. الدفعات (Batches)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/batches/` | `batch_list` | BatchListView | GET | قائمة الدفعات |
| `/inventory/batches/create/` | `batch_create` | BatchCreateView | GET, POST | إضافة دفعة |
| `/inventory/batches/<pk>/` | `batch_detail` | BatchDetailView | GET | تفاصيل الدفعة |
| `/inventory/batches/<pk>/update/` | `batch_update` | BatchUpdateView | GET, POST | تعديل الدفعة |

---

## 7. التقارير (Reports)

| URL | Name | View | Method | الوصف |
|-----|------|------|--------|-------|
| `/inventory/reports/stock/` | `stock_report` | StockReportView | GET | تقرير المخزون |
| `/inventory/reports/movements/` | `movement_report` | StockMovementReportView | GET | تقرير الحركات |
| `/inventory/reports/batches/expired/` | `batch_expired_report` | BatchExpiredReportView | GET | تقرير الدفعات المنتهية |

---

## 8. الـ Query Parameters

### 8.1 البحث والتصفية في القوائم

```
# Stock In/Out List
?search=<text>        # بحث في الرقم، المرجع، اسم الشريك
?status=posted|draft  # تصفية حسب الحالة

# Transfer List
?search=<text>        # بحث في الرقم، المرجع
?status=<status>      # draft, pending, approved, in_transit, received, cancelled

# Stock Count List
?warehouse=<id>       # تصفية حسب المستودع
?status=<status>      # planned, in_progress, completed, approved, cancelled
?count_type=<type>    # periodic, annual, cycle, special

# Batch List
?warehouse=<id>       # تصفية حسب المستودع
?item=<id>            # تصفية حسب المادة
?status=expired|expiring_soon|active
?search=<text>        # بحث في رقم الدفعة، اسم المادة
```

### 8.2 تقرير المخزون

```
/inventory/reports/stock/
?warehouse=<id>       # تصفية حسب المستودع
?item=<id>            # تصفية حسب المادة
```

### 8.3 تقرير الحركات

```
/inventory/reports/movements/
?item=<id>            # تصفية حسب المادة
?warehouse=<id>       # تصفية حسب المستودع
?from_date=YYYY-MM-DD # من تاريخ
?to_date=YYYY-MM-DD   # إلى تاريخ
```

### 8.4 تقرير الدفعات المنتهية

```
/inventory/reports/batches/expired/
?warehouse=<id>       # تصفية حسب المستودع
?days=<number>        # عدد الأيام للتحذير (افتراضي: 30)
```

---

## 9. خريطة التنقل

```
                    ┌──────────────┐
                    │   Dashboard  │
                    │  /inventory/ │
                    └──────┬───────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Stock In    │   │  Stock Out   │   │  Transfers   │
│ /stock-in/   │   │ /stock-out/  │   │ /transfers/  │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ ├─ list      │   │ ├─ list      │   │ ├─ list      │
│ ├─ create    │   │ ├─ create    │   │ ├─ create    │
│ ├─ detail    │   │ ├─ detail    │   │ └─ detail    │
│ ├─ update    │   │ ├─ update    │   │              │
│ ├─ post      │   │ ├─ post      │   │              │
│ └─ unpost    │   │ └─ unpost    │   │              │
└──────────────┘   └──────────────┘   └──────────────┘

       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Stock Count  │   │   Batches    │   │   Reports    │
│/stock-count/ │   │  /batches/   │   │  /reports/   │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ ├─ list      │   │ ├─ list      │   │ ├─ stock/    │
│ ├─ create    │   │ ├─ create    │   │ ├─ movements/│
│ ├─ detail    │   │ ├─ detail    │   │ └─ batches/  │
│ ├─ update    │   │ └─ update    │   │    expired/  │
│ └─ process   │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## 10. الـ Templates المستخدمة

```
inventory/
├── dashboard.html
├── stock_in/
│   ├── stock_in_list.html
│   ├── stock_in_form.html
│   └── stock_in_detail.html
├── stock_out/
│   ├── stock_out_list.html
│   ├── stock_out_form.html
│   └── stock_out_detail.html
├── transfer/
│   ├── transfer_list.html
│   ├── transfer_form.html
│   └── transfer_detail.html
├── stock_count/
│   ├── count_list.html
│   ├── count_form.html
│   └── count_detail.html
├── batches/
│   ├── batch_list.html
│   ├── batch_form.html
│   ├── batch_detail.html
│   └── expired_batches_report.html
└── reports/
    ├── stock_report.html
    └── movement_report.html
```

---

## 11. الصلاحيات المطلوبة

| URL Pattern | Permission Required |
|-------------|---------------------|
| stock_in_list | inventory.view_stockin |
| stock_in_create | inventory.add_stockin |
| stock_in_update | inventory.change_stockin |
| stock_in_post/unpost | inventory.can_post_stock_document |
| stock_out_* | inventory.view/add/change_stockout |
| transfer_* | inventory.view/add/change_stocktransfer |
| count_* | inventory.view/add/change_stockcount |
| batch_* | inventory.view/add/change/delete_batch |
| reports/* | (no special permission) |

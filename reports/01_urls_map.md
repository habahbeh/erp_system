# خريطة URLs لنظام المشتريات

**التاريخ:** 2025-11-28

---

## نظرة عامة

نظام المشتريات يستخدم `app_name = 'purchases'` ويعمل تحت المسار الرئيسي `/purchases/`

---

## 1. لوحة التحكم (Dashboard)

| URL | اسم Route | View | الوصف |
|-----|-----------|------|-------|
| `/purchases/dashboard/` | `dashboard` | `PurchaseDashboardView` | لوحة تحكم المشتريات |
| `/purchases/api/dashboard/stats/` | `dashboard_stats_api` | `dashboard_stats_api` | إحصائيات Dashboard (AJAX) |
| `/purchases/api/dashboard/monthly-chart/` | `monthly_chart_api` | `monthly_chart_api` | بيانات الرسم البياني الشهري |
| `/purchases/api/dashboard/top-suppliers/` | `top_suppliers_api` | `top_suppliers_api` | أفضل الموردين |

---

## 2. فواتير المشتريات (Invoices)

### العمليات الأساسية (CRUD)
| URL | اسم Route | View | HTTP | الوصف |
|-----|-----------|------|------|-------|
| `/purchases/invoices/` | `invoice_list` | `PurchaseInvoiceListView` | GET | قائمة الفواتير |
| `/purchases/invoices/create/` | `invoice_create` | `PurchaseInvoiceCreateView` | GET/POST | إنشاء فاتورة |
| `/purchases/invoices/<pk>/` | `invoice_detail` | `PurchaseInvoiceDetailView` | GET | تفاصيل فاتورة |
| `/purchases/invoices/<pk>/update/` | `invoice_update` | `PurchaseInvoiceUpdateView` | GET/POST | تعديل فاتورة |
| `/purchases/invoices/<pk>/delete/` | `invoice_delete` | `PurchaseInvoiceDeleteView` | GET/POST | حذف فاتورة |

### الإجراءات (Actions)
| URL | اسم Route | View | HTTP | الوصف |
|-----|-----------|------|------|-------|
| `/purchases/invoices/<pk>/post/` | `post_invoice` | `post_invoice` | POST | ترحيل الفاتورة |
| `/purchases/invoices/<pk>/unpost/` | `unpost_invoice` | `unpost_invoice` | POST | إلغاء الترحيل |

### AJAX Endpoints
| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/ajax/invoices/datatable/` | `invoice_datatable_ajax` | بيانات DataTable |
| `/purchases/ajax/invoices/get-supplier-price/` | `get_supplier_item_price_ajax` | جلب سعر المورد |
| `/purchases/ajax/invoices/get-stock-multi-branch/` | `get_item_stock_multi_branch_ajax` | المخزون في كل الفروع |
| `/purchases/ajax/invoices/get-stock-current/` | `get_item_stock_current_branch_ajax` | المخزون في الفرع الحالي |
| `/purchases/ajax/invoices/item-search/` | `item_search_ajax` | بحث المواد |
| `/purchases/ajax/invoices/get-price-by-uom/` | `ajax_get_item_price_by_uom` | السعر حسب الوحدة |
| `/purchases/ajax/invoices/save-draft/` | `save_invoice_draft_ajax` | حفظ مسودة |
| `/purchases/ajax/invoices/uom-conversions/` | `get_item_uom_conversions_ajax` | تحويلات الوحدات |
| `/purchases/ajax/invoices/item-all-prices/` | `get_item_all_prices_ajax` | جميع أسعار المادة |

### التصدير
| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/invoices/export/` | `export_invoices_excel` | تصدير Excel |

---

## 3. أوامر الشراء (Orders)

### العمليات الأساسية (CRUD)
| URL | اسم Route | View | HTTP | الوصف |
|-----|-----------|------|------|-------|
| `/purchases/orders/` | `order_list` | `PurchaseOrderListView` | GET | قائمة الأوامر |
| `/purchases/orders/create/` | `order_create` | `PurchaseOrderCreateView` | GET/POST | إنشاء أمر |
| `/purchases/orders/<pk>/` | `order_detail` | `PurchaseOrderDetailView` | GET | تفاصيل أمر |
| `/purchases/orders/<pk>/update/` | `order_update` | `PurchaseOrderUpdateView` | GET/POST | تعديل أمر |
| `/purchases/orders/<pk>/delete/` | `order_delete` | `PurchaseOrderDeleteView` | GET/POST | حذف أمر |

### سير العمل (Workflow)
| URL | اسم Route | View | HTTP | الوصف |
|-----|-----------|------|------|-------|
| `/purchases/orders/<pk>/submit/` | `submit_for_approval` | `submit_for_approval` | POST | إرسال للموافقة |
| `/purchases/orders/<pk>/approve/` | `approve_order` | `approve_order` | POST | الموافقة |
| `/purchases/orders/<pk>/reject/` | `reject_order` | `reject_order` | POST | الرفض |
| `/purchases/orders/<pk>/send/` | `send_to_supplier` | `send_to_supplier` | POST | إرسال للمورد |
| `/purchases/orders/<pk>/cancel/` | `cancel_order` | `cancel_order` | POST | إلغاء |
| `/purchases/orders/<pk>/convert-to-invoice/` | `convert_to_invoice` | `convert_to_invoice` | POST | تحويل لفاتورة |

### AJAX Endpoints
| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/ajax/orders/datatable/` | `order_datatable_ajax` | بيانات DataTable |
| `/purchases/ajax/orders/get-supplier-price/` | `order_get_supplier_item_price_ajax` | سعر المورد |
| `/purchases/ajax/orders/get-stock-multi-branch/` | `order_get_item_stock_multi_branch_ajax` | المخزون |
| `/purchases/ajax/orders/item-search/` | `order_item_search_ajax` | بحث المواد |
| `/purchases/ajax/orders/save-draft/` | `save_order_draft_ajax` | حفظ مسودة |

---

## 4. محاضر استلام البضاعة (Goods Receipts)

### العمليات الأساسية
| URL | اسم Route | HTTP | الوصف |
|-----|-----------|------|-------|
| `/purchases/goods-receipts/` | `goods_receipt_list` | GET | قائمة المحاضر |
| `/purchases/goods-receipts/create/` | `goods_receipt_create` | GET/POST | إنشاء محضر |
| `/purchases/goods-receipts/<pk>/` | `goods_receipt_detail` | GET | تفاصيل |
| `/purchases/goods-receipts/<pk>/update/` | `goods_receipt_update` | GET/POST | تعديل |
| `/purchases/goods-receipts/<pk>/delete/` | `goods_receipt_delete` | POST | حذف |

### الإجراءات
| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/goods-receipts/<pk>/confirm/` | `confirm_goods_receipt` | تأكيد الاستلام |
| `/purchases/goods-receipts/<pk>/post/` | `post_goods_receipt` | ترحيل للمخزون |
| `/purchases/goods-receipts/<pk>/unpost/` | `unpost_goods_receipt` | إلغاء الترحيل |

---

## 5. طلبات الشراء (Requests)

### العمليات الأساسية
| URL | اسم Route | HTTP | الوصف |
|-----|-----------|------|-------|
| `/purchases/requests/` | `request_list` | GET | قائمة الطلبات |
| `/purchases/requests/create/` | `request_create` | GET/POST | إنشاء طلب |
| `/purchases/requests/<pk>/` | `request_detail` | GET | تفاصيل |
| `/purchases/requests/<pk>/update/` | `request_update` | GET/POST | تعديل |
| `/purchases/requests/<pk>/delete/` | `request_delete` | POST | حذف |

### سير العمل
| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/requests/<pk>/submit/` | `submit_request` | تقديم الطلب |
| `/purchases/requests/<pk>/approve/` | `approve_request` | الموافقة |
| `/purchases/requests/<pk>/reject/` | `reject_request` | الرفض |
| `/purchases/requests/<pk>/create-order/` | `create_order_from_request` | إنشاء أمر شراء |

---

## 6. طلبات عروض الأسعار (RFQ)

| URL | اسم Route | HTTP | الوصف |
|-----|-----------|------|-------|
| `/purchases/rfqs/` | `rfq_list` | GET | قائمة RFQ |
| `/purchases/rfqs/create/` | `rfq_create` | GET/POST | إنشاء RFQ |
| `/purchases/rfqs/<pk>/` | `rfq_detail` | GET | تفاصيل |
| `/purchases/rfqs/<pk>/update/` | `rfq_update` | GET/POST | تعديل |
| `/purchases/rfqs/<pk>/delete/` | `rfq_delete` | POST | حذف |
| `/purchases/rfqs/<pk>/send/` | `send_rfq_to_suppliers` | POST | إرسال للموردين |
| `/purchases/rfqs/<pk>/cancel/` | `cancel_rfq` | POST | إلغاء |
| `/purchases/rfqs/<pk>/evaluate/` | `mark_rfq_as_evaluating` | POST | بدء التقييم |

---

## 7. عروض الأسعار (Quotations)

| URL | اسم Route | HTTP | الوصف |
|-----|-----------|------|-------|
| `/purchases/quotations/` | `quotation_list` | GET | قائمة العروض |
| `/purchases/quotations/create/` | `quotation_create` | GET/POST | إنشاء عرض |
| `/purchases/quotations/<pk>/` | `quotation_detail` | GET | تفاصيل |
| `/purchases/quotations/<pk>/update/` | `quotation_update` | GET/POST | تعديل |
| `/purchases/quotations/<pk>/delete/` | `quotation_delete` | POST | حذف |
| `/purchases/quotations/<pk>/evaluate/` | `evaluate_quotation` | POST | تقييم العرض |
| `/purchases/quotations/<pk>/award/` | `award_quotation` | POST | ترسية العرض |
| `/purchases/quotations/<pk>/reject/` | `reject_quotation` | POST | رفض العرض |
| `/purchases/quotations/<pk>/convert-to-order/` | `convert_quotation_to_order` | POST | تحويل لأمر شراء |

---

## 8. العقود (Contracts)

| URL | اسم Route | HTTP | الوصف |
|-----|-----------|------|-------|
| `/purchases/contracts/` | `contract_list` | GET | قائمة العقود |
| `/purchases/contracts/create/` | `contract_create` | GET/POST | إنشاء عقد |
| `/purchases/contracts/<pk>/` | `contract_detail` | GET | تفاصيل |
| `/purchases/contracts/<pk>/update/` | `contract_update` | GET/POST | تعديل |
| `/purchases/contracts/<pk>/delete/` | `contract_delete` | POST | حذف |
| `/purchases/contracts/<pk>/approve/` | `contract_approve` | POST | اعتماد العقد |
| `/purchases/contracts/<pk>/change-status/` | `contract_change_status` | POST | تغيير الحالة |
| `/purchases/contracts/check-expiry/` | `contract_check_expiry` | GET | فحص انتهاء الصلاحية |
| `/purchases/contracts/<pk>/copy/` | `contract_copy_or_renew` | POST | نسخ/تجديد |

---

## 9. التقارير (Reports)

| URL | اسم Route | الوصف |
|-----|-----------|-------|
| `/purchases/reports/` | `reports_list` | قائمة التقارير |
| `/purchases/reports/purchases-summary/` | `purchases_summary_report` | ملخص المشتريات |
| `/purchases/reports/supplier-performance/` | `supplier_performance_report` | أداء الموردين |
| `/purchases/reports/purchase-orders/` | `purchase_orders_report` | تقرير الأوامر |
| `/purchases/reports/items-purchases/` | `items_purchases_report` | مشتريات الأصناف |
| `/purchases/reports/contracts/` | `contracts_report` | تقرير العقود |

### تصدير التقارير
| URL | اسم Route | الصيغة |
|-----|-----------|--------|
| `/purchases/reports/purchases-summary/export/excel/` | `export_purchases_summary_excel` | Excel |
| `/purchases/reports/purchases-summary/export/pdf/` | `export_purchases_summary_pdf` | PDF |
| `/purchases/reports/supplier-performance/export/excel/` | `export_supplier_performance_excel` | Excel |
| `/purchases/reports/supplier-performance/export/pdf/` | `export_supplier_performance_pdf` | PDF |
| `/purchases/reports/purchase-orders/export/excel/` | `export_purchase_orders_excel` | Excel |
| `/purchases/reports/purchase-orders/export/pdf/` | `export_purchase_orders_pdf` | PDF |
| `/purchases/reports/items-purchases/export/excel/` | `export_items_purchases_excel` | Excel |
| `/purchases/reports/items-purchases/export/pdf/` | `export_items_purchases_pdf` | PDF |
| `/purchases/reports/contracts/export/excel/` | `export_contracts_excel` | Excel |
| `/purchases/reports/contracts/export/pdf/` | `export_contracts_pdf` | PDF |

---

## 10. ملخص إحصائي

| النوع | العدد |
|-------|-------|
| **Dashboard URLs** | 4 |
| **Invoice URLs** | 19 |
| **Order URLs** | 16 |
| **Goods Receipt URLs** | 11 |
| **Request URLs** | 12 |
| **RFQ URLs** | 11 |
| **Quotation URLs** | 12 |
| **Contract URLs** | 10 |
| **Report URLs** | 16 |
| **الإجمالي** | **~111 URL** |

---

## 11. أنماط URL المستخدمة

```python
# CRUD Pattern
path('<model>/', ListView.as_view(), name='<model>_list'),
path('<model>/create/', CreateView.as_view(), name='<model>_create'),
path('<model>/<int:pk>/', DetailView.as_view(), name='<model>_detail'),
path('<model>/<int:pk>/update/', UpdateView.as_view(), name='<model>_update'),
path('<model>/<int:pk>/delete/', DeleteView.as_view(), name='<model>_delete'),

# Action Pattern
path('<model>/<int:pk>/<action>/', action_view, name='<action>'),

# AJAX Pattern
path('ajax/<model>/<endpoint>/', ajax_view, name='<endpoint>_ajax'),

# Export Pattern
path('<model>/export/', export_view, name='export_<model>_excel'),
```

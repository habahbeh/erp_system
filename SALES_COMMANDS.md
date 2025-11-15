# 📋 أوامر بناء نظام المبيعات - Copy & Paste

---

## 🔧 المرحلة 1: البنية التحتية

### Task 1.1
```
ابدأ المرحلة 1 - Task 1.1: تحديث SalesInvoice Model بإضافة الحقول التالية:
- معلومات المستلم (recipient_name, recipient_phone, recipient_address)
- معلومات الشحن (delivery_date, actual_delivery_date, shipping_cost)
- معلومات الدفع (payment_status, paid_amount, remaining_amount, due_date)
- معلومات العمولة (salesperson_commission_rate, salesperson_commission_amount)
- معلومات الفوترة الحكومية (government_invoice_uuid, government_submission_date, government_status)
```

### Task 1.2
```
المرحلة 1 - Task 1.2: أنشئ PaymentInstallment Model لإدارة الأقساط والدفعات
```

### Task 1.3
```
المرحلة 1 - Task 1.3: أنشئ DiscountCampaign Model لإدارة حملات الخصومات
```

### Task 1.4
```
المرحلة 1 - Task 1.4: أنشئ SalespersonCommission Model لإدارة عمولات المندوبين
```

### Task 1.5
```
المرحلة 1 - Task 1.5: أنشئ POSSession Model لإدارة جلسات نقاط البيع
```

### Task 1.6
```
المرحلة 1 - Task 1.6: حدّث BusinessPartner Model في apps/core بإضافة:
- credit_limit (حد الائتمان)
- payment_terms (شروط الدفع)
- default_salesperson (المندوب الافتراضي)
- tax_status (حالة الضريبة)
- tax_number (الرقم الضريبي)
- commercial_registration (السجل التجاري)
```

### Task 1.7
```
المرحلة 1 - Task 1.7: أنشئ migrations لجميع التغييرات في apps/sales و apps/core
```

### Task 1.8
```
المرحلة 1 - Task 1.8: اختبر جميع Models الجديدة والمحدثة من Django shell
```

---

## 🎨 المرحلة 2: الفواتير والعمليات الأساسية

### Task 2.1
```
ابدأ المرحلة 2 - Task 2.1: أنشئ ملف apps/sales/forms/__init__.py و apps/sales/forms/invoice_forms.py
وأضف:
- SalesInvoiceForm
- InvoiceItemFormSet
```

### Task 2.2
```
المرحلة 2 - Task 2.2: أنشئ ملف apps/sales/views/__init__.py و apps/sales/views/invoice_views.py
وأضف:
- SalesInvoiceListView (مع فلاتر)
```

### Task 2.3
```
المرحلة 2 - Task 2.3: أضف في invoice_views.py:
- SalesInvoiceCreateView
- SalesInvoiceUpdateView
```

### Task 2.4
```
المرحلة 2 - Task 2.4: أضف في invoice_views.py:
- SalesInvoiceDetailView
- SalesInvoiceDeleteView
```

### Task 2.5
```
المرحلة 2 - Task 2.5: أضف في invoice_views.py:
- SalesInvoicePostView
- SalesInvoiceUnpostView
```

### Task 2.6
```
المرحلة 2 - Task 2.6: أنشئ:
- apps/sales/templates/sales/base.html
- apps/sales/templates/sales/invoices/invoice_list.html
استخدم DataTables مع Ajax
```

### Task 2.7
```
المرحلة 2 - Task 2.7: أنشئ:
- apps/sales/templates/sales/invoices/invoice_form.html
استخدم formset ديناميكي مع JavaScript
```

### Task 2.8
```
المرحلة 2 - Task 2.8: أنشئ:
- apps/sales/templates/sales/invoices/invoice_detail.html
```

### Task 2.9
```
المرحلة 2 - Task 2.9: أنشئ:
- apps/sales/templates/sales/invoices/invoice_print.html
تصميم احترافي للطباعة
```

### Task 2.10
```
المرحلة 2 - Task 2.10: أنشئ apps/sales/urls.py وسجّله في config/urls.py
```

### Task 2.11
```
المرحلة 2 - Task 2.11: اختبر الدورة الكاملة:
1. إنشاء فاتورة مبيعات جديدة
2. إضافة سطور
3. حفظ الفاتورة
4. ترحيل الفاتورة
5. التحقق من سند الإخراج
6. التحقق من القيد المحاسبي
7. التحقق من المخزون
```

---

## 🎯 المرحلة 3: عروض الأسعار وطلبات البيع

### Task 3.1
```
ابدأ المرحلة 3 - Task 3.1: أنشئ apps/sales/forms/quotation_forms.py
مع QuotationForm و QuotationItemFormSet
```

### Task 3.2
```
المرحلة 3 - Task 3.2: أنشئ apps/sales/views/quotation_views.py
مع جميع Views (List, Create, Update, Detail, Delete, Convert to Order)
```

### Task 3.3
```
المرحلة 3 - Task 3.3: أنشئ templates لعروض الأسعار:
- quotation_list.html
- quotation_form.html
- quotation_detail.html
```

### Task 3.4
```
المرحلة 3 - Task 3.4: أنشئ apps/sales/forms/order_forms.py
مع SalesOrderForm و SalesOrderItemFormSet
```

### Task 3.5
```
المرحلة 3 - Task 3.5: أنشئ apps/sales/views/order_views.py
مع جميع Views (List, Create, Update, Detail, Delete, Convert to Invoice)
```

### Task 3.6
```
المرحلة 3 - Task 3.6: أنشئ templates لطلبات البيع:
- order_list.html
- order_form.html
- order_detail.html
```

### Task 3.7
```
المرحلة 3 - Task 3.7: اختبر الدورة الكاملة:
عرض سعر → تحويل لطلب → تحويل لفاتورة → ترحيل
```

---

## 💰 المرحلة 4: الدفعات والأقساط

### Task 4.1
```
ابدأ المرحلة 4 - Task 4.1: أنشئ apps/sales/forms/payment_forms.py
مع PaymentInstallmentForm و InstallmentPlanFormSet
```

### Task 4.2
```
المرحلة 4 - Task 4.2: أنشئ apps/sales/views/payment_views.py
مع views لإنشاء خطة أقساط وتسجيل دفعات
```

### Task 4.3
```
المرحلة 4 - Task 4.3: أنشئ templates للأقساط:
- installment_plan_form.html
- installment_list.html
- payment_record_form.html
```

### Task 4.4
```
المرحلة 4 - Task 4.4: أضف view لإنشاء سند قبض من قسط
وربطه مع apps/accounting/ReceiptVoucher
```

### Task 4.5
```
المرحلة 4 - Task 4.5: اختبر دورة الأقساط:
فاتورة → إنشاء أقساط → سند قبض → تحديث الأقساط → تحديث payment_status
```

---

## 🎁 المرحلة 5: حملات الخصومات والعمولات

### Task 5.1
```
ابدأ المرحلة 5 - Task 5.1: أنشئ apps/sales/forms/campaign_forms.py
مع DiscountCampaignForm
```

### Task 5.2
```
المرحلة 5 - Task 5.2: أنشئ apps/sales/views/campaign_views.py
مع جميع Views لإدارة الحملات
```

### Task 5.3
```
المرحلة 5 - Task 5.3: أنشئ templates لحملات الخصومات:
- campaign_list.html
- campaign_form.html
- campaign_detail.html
```

### Task 5.4
```
المرحلة 5 - Task 5.4: أضف logic لتطبيق الخصومات تلقائياً في الفواتير
```

### Task 5.5
```
المرحلة 5 - Task 5.5: أنشئ apps/sales/forms/commission_forms.py
مع SalespersonCommissionForm
```

### Task 5.6
```
المرحلة 5 - Task 5.6: أنشئ apps/sales/views/commission_views.py
مع views لإدارة العمولات
```

### Task 5.7
```
المرحلة 5 - Task 5.7: أنشئ templates للعمولات:
- commission_list.html
- commission_report.html
```

### Task 5.8
```
المرحلة 5 - Task 5.8: اختبر حساب العمولات تلقائياً عند الفواتير
```

---

## 🛒 المرحلة 6: نقاط البيع POS

### Task 6.1
```
ابدأ المرحلة 6 - Task 6.1: أنشئ apps/sales/forms/pos_forms.py
مع POSSessionForm و POSInvoiceForm
```

### Task 6.2
```
المرحلة 6 - Task 6.2: أنشئ apps/sales/views/pos_views.py
مع views لإدارة جلسات POS والمبيعات السريعة
```

### Task 6.3
```
المرحلة 6 - Task 6.3: أنشئ templates لـ POS:
- pos_session_list.html
- pos_session_form.html
- pos_interface.html (واجهة البيع)
```

### Task 6.4
```
المرحلة 6 - Task 6.4: اختبر دورة POS:
فتح جلسة → بيع سريع → إغلاق جلسة → مطابقة النقد
```

---

## 📊 المرحلة 7: التقارير

### Task 7.1
```
ابدأ المرحلة 7 - Task 7.1: أنشئ apps/sales/views/report_views.py
وأضف CustomerStatementView لكشف حساب عميل
```

### Task 7.2
```
المرحلة 7 - Task 7.2: أضف SalesDetailedView لكشف مبيعات تفصيلي
```

### Task 7.3
```
المرحلة 7 - Task 7.3: أضف ProfitLossView لتقرير الأرباح والخسائر
```

### Task 7.4
```
المرحلة 7 - Task 7.4: أضف TaxReportView لتقرير الضريبة (دعم 8 نسب: 0%, 1%, 4%, 5%, 6%, 10%, 12%, 16%)
```

### Task 7.5
```
المرحلة 7 - Task 7.5: أضف InvoiceSearchView لبحث الفواتير المتقدم
```

### Task 7.6
```
المرحلة 7 - Task 7.6: أضف QuotationComparisonView لمقارنة عروض الأسعار
```

### Task 7.7
```
المرحلة 7 - Task 7.7: أضف CommissionReportView لتقرير عمولات المندوبين
```

### Task 7.8
```
المرحلة 7 - Task 7.8: أضف CampaignReportView لتقرير حملات الخصومات
```

### Task 7.9
```
المرحلة 7 - Task 7.9: أنشئ templates لجميع التقارير:
- customer_statement.html
- sales_detailed.html
- profit_loss.html
- tax_report.html
- invoice_search.html
- quotation_comparison.html
- commission_report.html
- campaign_report.html
```

---

## 🏛️ المرحلة 8: الفوترة الإلكترونية

### Task 8.1
```
ابدأ المرحلة 8 - Task 8.1: أنشئ apps/sales/services/government_integration.py
للتكامل مع نظام الفوترة الحكومي
```

### Task 8.2
```
المرحلة 8 - Task 8.2: أضف views لإرسال الفواتير للنظام الحكومي
```

### Task 8.3
```
المرحلة 8 - Task 8.3: أضف template لعرض حالة الفواتير الحكومية
```

### Task 8.4
```
المرحلة 8 - Task 8.4: اختبر الإرسال للنظام الحكومي (بيئة تجريبية)
```

---

## ✅ الاختبار النهائي

### Final Test
```
الاختبار النهائي: اختبر الدورة الكاملة من البداية للنهاية:
1. عرض سعر للعميل
2. تحويل لطلب بيع
3. تحويل لفاتورة مبيعات
4. تطبيق حملة خصم
5. ترحيل الفاتورة
6. إنشاء خطة أقساط
7. تسجيل دفعة وإنشاء سند قبض
8. حساب عمولة المندوب
9. طباعة جميع التقارير
10. إرسال للنظام الحكومي
```

---

# 🎯 ملاحظات هامة:

1. **انسخ كل أمر** واحد تلو الآخر
2. **انتظر حتى أنتهي** من كل task
3. **راجع النتيجة** قبل الانتقال للتالي
4. **في حال خطأ** اطلب مني الإصلاح فوراً
5. **لا تتخطى أي task** - الترتيب مهم

---

**🚀 ابدأ الآن بنسخ الأمر الأول!**

# 🚀 مهام بناء نظام المبيعات - دليل كامل

**كل Task في مكان واحد: الأمر + التفاصيل + Checklist**

---

# 🔧 المرحلة 1: البنية التحتية (Week 1-2)

---

## ✅ Task 1.1: تحديث SalesInvoice Model

### 📝 الأمر (انسخه والصقه):
```
ابدأ المرحلة 1 - Task 1.1: تحديث SalesInvoice Model بإضافة الحقول التالية:
- معلومات المستلم (recipient_name, recipient_phone, recipient_address)
- معلومات الشحن (delivery_date, actual_delivery_date, shipping_cost)
- معلومات الدفع (payment_status, paid_amount, remaining_amount, due_date)
- معلومات العمولة (salesperson_commission_rate, salesperson_commission_amount)
- معلومات الفوترة الحكومية (government_invoice_uuid, government_submission_date, government_status)
```

### 🎯 ما سأفعله:
1. قراءة `apps/sales/models.py`
2. تحديث SalesInvoice Model بإضافة جميع الحقول
3. تحديث `calculate_totals()` method
4. إضافة method جديد `calculate_commission()`
5. إضافة method جديد `update_payment_status()`

### ✅ Checklist (راجعها بعد التنفيذ):
- [ ] جميع الحقول المطلوبة مضافة
- [ ] الحقول لها verbose_name بالعربية
- [ ] الحقول لها help_text عند الحاجة
- [ ] Methods محدثة وتعمل

---

## ✅ Task 1.2: إنشاء PaymentInstallment Model

### 📝 الأمر:
```
المرحلة 1 - Task 1.2: أنشئ PaymentInstallment Model لإدارة الأقساط والدفعات
```

### 🎯 ما سأفعله:
1. إنشاء class PaymentInstallment في `apps/sales/models.py`
2. إضافة جميع الحقول المطلوبة
3. إضافة ForeignKey للفاتورة
4. إضافة ForeignKey لسند القبض
5. إضافة Meta class و __str__ method

### ✅ Checklist:
- [ ] Model منشأ بجميع الحقول
- [ ] العلاقات مع الجداول الأخرى صحيحة
- [ ] Meta class موجودة (verbose_name, ordering)
- [ ] __str__ method موجودة

---

## ✅ Task 1.3: إنشاء DiscountCampaign Model

### 📝 الأمر:
```
المرحلة 1 - Task 1.3: أنشئ DiscountCampaign Model لإدارة حملات الخصومات
```

### 🎯 ما سأفعله:
1. إنشاء class DiscountCampaign يرث من BaseModel
2. إضافة أنواع الحملات (CAMPAIGN_TYPES)
3. إضافة حقول التواريخ والأوقات
4. إضافة حقول الخصم
5. إضافة حقول العروض (Buy X Get Y)
6. إضافة ManyToMany للمواد والأصناف والعملاء
7. إضافة method `is_active()` للتحقق من صلاحية الحملة
8. إضافة method `apply_to_item()` لتطبيق الخصم

### ✅ Checklist:
- [ ] Model منشأ بجميع الأنواع
- [ ] حقول التواريخ والأوقات موجودة
- [ ] ManyToMany relationships صحيحة
- [ ] Methods موجودة ومختبرة

---

## ✅ Task 1.4: إنشاء SalespersonCommission Model

### 📝 الأمر:
```
المرحلة 1 - Task 1.4: أنشئ SalespersonCommission Model لإدارة عمولات المندوبين
```

### 🎯 ما سأفعله:
1. إنشاء class SalespersonCommission
2. إضافة ForeignKey للمندوب والفاتورة
3. إضافة حقول العمولة والدفع
4. إضافة ForeignKey لسند الصرف

### ✅ Checklist:
- [ ] Model منشأ
- [ ] العلاقات صحيحة
- [ ] OneToOne مع الفاتورة
- [ ] Meta class موجودة

---

## ✅ Task 1.5: إنشاء POSSession Model

### 📝 الأمر:
```
المرحلة 1 - Task 1.5: أنشئ POSSession Model لإدارة جلسات نقاط البيع
```

### 🎯 ما سأفعله:
1. إنشاء class POSSession يرث من BaseModel
2. إضافة حقول الجلسة
3. إضافة حقول النقد (افتتاحي، ختامي، فرق)
4. إضافة methods: `calculate_totals()`, `close_session()`

### ✅ Checklist:
- [ ] Model منشأ
- [ ] حقول النقد موجودة
- [ ] Methods للحسابات موجودة
- [ ] auto_now_add للتاريخ

---

## ✅ Task 1.6: تحديث BusinessPartner في apps/core

### 📝 الأمر:
```
المرحلة 1 - Task 1.6: حدّث BusinessPartner Model في apps/core بإضافة:
- credit_limit (حد الائتمان)
- payment_terms (شروط الدفع)
- default_salesperson (المندوب الافتراضي)
- tax_status (حالة الضريبة)
- tax_number (الرقم الضريبي)
- commercial_registration (السجل التجاري)
```

### 🎯 ما سأفعله:
1. قراءة `apps/core/models.py`
2. تحديث BusinessPartner Model
3. إضافة method `get_current_balance()`
4. إضافة method `check_credit_limit(amount)`

### ✅ Checklist:
- [ ] جميع الحقول مضافة
- [ ] Methods موجودة
- [ ] ForeignKey للمندوب صحيح
- [ ] CHOICES للضريبة موجودة

---

## ✅ Task 1.7: إنشاء Migrations

### 📝 الأمر:
```
المرحلة 1 - Task 1.7: أنشئ migrations لجميع التغييرات في apps/sales و apps/core
```

### 🎯 ما سأفعله:
1. تشغيل `python manage.py makemigrations sales`
2. تشغيل `python manage.py makemigrations core`
3. مراجعة ملفات الـ migrations
4. تشغيل `python manage.py migrate`

### ✅ Checklist:
- [ ] Migrations تم إنشاؤها بدون أخطاء
- [ ] Migrations تم تطبيقها بنجاح
- [ ] لا توجد warnings
- [ ] قاعدة البيانات محدثة

---

## ✅ Task 1.8: اختبار Models

### 📝 الأمر:
```
المرحلة 1 - Task 1.8: اختبر جميع Models الجديدة والمحدثة من Django shell
```

### 🎯 ما سأفعله:
1. فتح Django shell
2. إنشاء instances من كل model
3. اختبار Methods
4. التأكد من العلاقات

### ✅ Checklist:
- [ ] جميع Models تعمل
- [ ] Methods تعطي نتائج صحيحة
- [ ] ForeignKeys تعمل
- [ ] ManyToMany تعمل

---

# 🎨 المرحلة 2: الفواتير والعمليات الأساسية (Week 3-4)

---

## ✅ Task 2.1: إنشاء Forms للفواتير

### 📝 الأمر:
```
ابدأ المرحلة 2 - Task 2.1: أنشئ ملف apps/sales/forms/__init__.py و apps/sales/forms/invoice_forms.py
وأضف:
- SalesInvoiceForm
- InvoiceItemFormSet
```

### 🎯 ما سأفعله:
1. إنشاء مجلد `apps/sales/forms/`
2. إنشاء `__init__.py`
3. إنشاء `invoice_forms.py`
4. كتابة SalesInvoiceForm
5. كتابة InvoiceItemFormSet باستخدام inlineformset_factory
6. إضافة Widgets و CSS classes
7. إضافة validation للخصم وحد الائتمان

### ✅ Checklist:
- [ ] Forms منشأة
- [ ] Widgets محددة
- [ ] CSS classes مضافة (Bootstrap 5)
- [ ] Validation موجودة
- [ ] Formset يعمل

---

## ✅ Task 2.2: إنشاء Views للفواتير - القوائم

### 📝 الأمر:
```
المرحلة 2 - Task 2.2: أنشئ ملف apps/sales/views/__init__.py و apps/sales/views/invoice_views.py
وأضف:
- SalesInvoiceListView (مع فلاتر)
```

### 🎯 ما سأفعله:
1. إنشاء مجلد `apps/sales/views/`
2. إنشاء `__init__.py`
3. إنشاء `invoice_views.py`
4. كتابة SalesInvoiceListView
5. إضافة filters (نوع، عميل، تاريخ، حالة)
6. إضافة search functionality
7. إضافة pagination

### ✅ Checklist:
- [ ] ListView تعمل
- [ ] Filters تعمل
- [ ] Search يعمل
- [ ] Pagination موجودة
- [ ] Company filtering موجود

---

## ✅ Task 2.3: إنشاء Views للفواتير - الإنشاء والتعديل

### 📝 الأمر:
```
المرحلة 2 - Task 2.3: أضف في invoice_views.py:
- SalesInvoiceCreateView
- SalesInvoiceUpdateView
```

### 🎯 ما سأفعله:
1. كتابة SalesInvoiceCreateView
2. كتابة SalesInvoiceUpdateView
3. إضافة formset handling
4. إضافة transaction.atomic
5. إضافة calculate_totals
6. إضافة messages

### ✅ Checklist:
- [ ] CreateView تعمل
- [ ] UpdateView تعمل
- [ ] Formset يحفظ بشكل صحيح
- [ ] Transactions آمنة
- [ ] Messages تظهر

---

## ✅ Task 2.4: إنشاء Views للفواتير - العرض والحذف

### 📝 الأمر:
```
المرحلة 2 - Task 2.4: أضف في invoice_views.py:
- SalesInvoiceDetailView
- SalesInvoiceDeleteView
```

### 🎯 ما سأفعله:
1. كتابة SalesInvoiceDetailView
2. كتابة SalesInvoiceDeleteView مع التحقق من عدم الترحيل
3. إضافة permissions checking

### ✅ Checklist:
- [ ] DetailView تعرض كل التفاصيل
- [ ] DeleteView تمنع حذف المرحلة
- [ ] Permissions تعمل

---

## ✅ Task 2.5: إنشاء Views للفواتير - الترحيل

### 📝 الأمر:
```
المرحلة 2 - Task 2.5: أضف في invoice_views.py:
- SalesInvoicePostView
- SalesInvoiceUnpostView
```

### 🎯 ما سأفعله:
1. كتابة SalesInvoicePostView
2. كتابة SalesInvoiceUnpostView
3. إضافة permissions checking
4. إضافة error handling

### ✅ Checklist:
- [ ] PostView تعمل
- [ ] UnpostView تعمل
- [ ] سند الإخراج يُنشأ
- [ ] القيد المحاسبي يُنشأ
- [ ] Errors تُعرض بشكل واضح

---

## ✅ Task 2.6: إنشاء Templates للفواتير - القوائم

### 📝 الأمر:
```
المرحلة 2 - Task 2.6: أنشئ:
- apps/sales/templates/sales/base.html
- apps/sales/templates/sales/invoices/invoice_list.html
استخدم DataTables مع Ajax
```

### 🎯 ما سأفعله:
1. إنشاء مجلد templates
2. إنشاء base.html يرث من templates/base/base.html
3. إنشاء invoice_list.html
4. إضافة DataTables
5. إضافة filters form
6. إضافة action buttons

### ✅ Checklist:
- [ ] Templates منشأة
- [ ] RTL يعمل
- [ ] DataTables تعمل
- [ ] Filters تعمل
- [ ] Buttons تعمل

---

## ✅ Task 2.7: إنشاء Templates للفواتير - النموذج

### 📝 الأمر:
```
المرحلة 2 - Task 2.7: أنشئ:
- apps/sales/templates/sales/invoices/invoice_form.html
استخدم formset ديناميكي مع JavaScript
```

### 🎯 ما سأفعله:
1. إنشاء invoice_form.html
2. إضافة form header
3. إضافة formset لسطور الفاتورة
4. إضافة JavaScript لإضافة/حذف سطور
5. إضافة auto-calculation للمجاميع
6. إضافة barcode scanner support

### ✅ Checklist:
- [ ] Form تعمل
- [ ] إضافة سطور تعمل
- [ ] حذف سطور يعمل
- [ ] الحسابات تلقائية
- [ ] حقول required واضحة

---

## ✅ Task 2.8: إنشاء Templates للفواتير - التفاصيل

### 📝 الأمر:
```
المرحلة 2 - Task 2.8: أنشئ:
- apps/sales/templates/sales/invoices/invoice_detail.html
```

### 🎯 ما سأفعله:
1. إنشاء invoice_detail.html
2. عرض معلومات الفاتورة
3. عرض جدول السطور
4. عرض المجاميع
5. إضافة action buttons (تعديل، حذف، ترحيل، طباعة)
6. عرض حالة الفاتورة (مرحلة/غير مرحلة)

### ✅ Checklist:
- [ ] جميع البيانات تظهر
- [ ] Buttons تعمل حسب الحالة
- [ ] التنسيق جيد
- [ ] RTL صحيح

---

## ✅ Task 2.9: إنشاء Templates للفواتير - الطباعة

### 📝 الأمر:
```
المرحلة 2 - Task 2.9: أنشئ:
- apps/sales/templates/sales/invoices/invoice_print.html
تصميم احترافي للطباعة
```

### 🎯 ما سأفعله:
1. إنشاء invoice_print.html
2. تصميم layout للطباعة
3. إضافة header الشركة
4. إضافة QR code للفاتورة
5. إضافة CSS للطباعة (@media print)

### ✅ Checklist:
- [ ] التصميم احترافي
- [ ] الطباعة واضحة
- [ ] QR code يعمل
- [ ] معلومات الشركة كاملة

---

## ✅ Task 2.10: إنشاء URLs

### 📝 الأمر:
```
المرحلة 2 - Task 2.10: أنشئ apps/sales/urls.py وسجّله في config/urls.py
```

### 🎯 ما سأفعله:
1. إنشاء `apps/sales/urls.py`
2. إضافة جميع URLs للفواتير
3. تسجيل app في `config/urls.py`
4. إضافة app_name = 'sales'

### ✅ Checklist:
- [ ] URLs منشأة
- [ ] مسجلة في config
- [ ] التسميات واضحة
- [ ] app_name موجود

---

## ✅ Task 2.11: اختبار الدورة الكاملة

### 📝 الأمر:
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

### 🎯 ما سأفعله:
1. إنشاء فاتورة من الواجهة
2. ترحيل الفاتورة
3. التحقق من StockOut في apps/inventory
4. التحقق من JournalEntry في apps/accounting
5. التحقق من تحديث ItemStock

### ✅ Checklist:
- [ ] الفاتورة تُنشأ بنجاح
- [ ] الترحيل يعمل بدون أخطاء
- [ ] سند الإخراج موجود
- [ ] القيد المحاسبي صحيح
- [ ] المخزون محدث
- [ ] حساب العميل محدث

---

# 🎯 المرحلة 3: عروض الأسعار وطلبات البيع (Week 5)

---

## ✅ Task 3.1: Forms لعروض الأسعار

### 📝 الأمر:
```
ابدأ المرحلة 3 - Task 3.1: أنشئ apps/sales/forms/quotation_forms.py
مع QuotationForm و QuotationItemFormSet
```

### 🎯 ما سأفعله:
1. إنشاء `quotation_forms.py`
2. كتابة QuotationForm
3. كتابة QuotationItemFormSet
4. إضافة validation

### ✅ Checklist:
- [ ] Forms منشأة
- [ ] Widgets محددة
- [ ] Validation موجودة

---

## ✅ Task 3.2: Views لعروض الأسعار

### 📝 الأمر:
```
المرحلة 3 - Task 3.2: أنشئ apps/sales/views/quotation_views.py
مع جميع Views (List, Create, Update, Detail, Delete, Convert to Order)
```

### 🎯 ما سأفعله:
1. إنشاء `quotation_views.py`
2. كتابة QuotationListView
3. كتابة QuotationCreateView
4. كتابة QuotationUpdateView
5. كتابة QuotationDetailView
6. كتابة QuotationDeleteView
7. كتابة ConvertToOrderView

### ✅ Checklist:
- [ ] جميع Views تعمل
- [ ] Convert to Order يعمل
- [ ] Permissions تعمل

---

## ✅ Task 3.3: Templates لعروض الأسعار

### 📝 الأمر:
```
المرحلة 3 - Task 3.3: أنشئ templates لعروض الأسعار:
- quotation_list.html
- quotation_form.html
- quotation_detail.html
```

### 🎯 ما سأفعله:
1. إنشاء quotation_list.html
2. إنشاء quotation_form.html
3. إنشاء quotation_detail.html

### ✅ Checklist:
- [ ] Templates منشأة
- [ ] التنسيق جيد
- [ ] Buttons تعمل

---

## ✅ Task 3.4: Forms لطلبات البيع

### 📝 الأمر:
```
المرحلة 3 - Task 3.4: أنشئ apps/sales/forms/order_forms.py
مع SalesOrderForm و SalesOrderItemFormSet
```

### 🎯 ما سأفعله:
1. إنشاء `order_forms.py`
2. كتابة SalesOrderForm
3. كتابة SalesOrderItemFormSet

### ✅ Checklist:
- [ ] Forms منشأة
- [ ] Validation موجودة

---

## ✅ Task 3.5: Views لطلبات البيع

### 📝 الأمر:
```
المرحلة 3 - Task 3.5: أنشئ apps/sales/views/order_views.py
مع جميع Views (List, Create, Update, Detail, Delete, Convert to Invoice)
```

### 🎯 ما سأفعله:
1. إنشاء `order_views.py`
2. كتابة جميع Views
3. كتابة ConvertToInvoiceView

### ✅ Checklist:
- [ ] جميع Views تعمل
- [ ] Convert to Invoice يعمل

---

## ✅ Task 3.6: Templates لطلبات البيع

### 📝 الأمر:
```
المرحلة 3 - Task 3.6: أنشئ templates لطلبات البيع:
- order_list.html
- order_form.html
- order_detail.html
```

### 🎯 ما سأفعله:
1. إنشاء جميع templates المطلوبة

### ✅ Checklist:
- [ ] Templates منشأة
- [ ] التنسيق جيد

---

## ✅ Task 3.7: اختبار الدورة الكاملة

### 📝 الأمر:
```
المرحلة 3 - Task 3.7: اختبر الدورة الكاملة:
عرض سعر → تحويل لطلب → تحويل لفاتورة → ترحيل
```

### 🎯 ما سأفعله:
1. إنشاء عرض سعر
2. تحويله لطلب
3. تحويل الطلب لفاتورة
4. ترحيل الفاتورة

### ✅ Checklist:
- [ ] الدورة الكاملة تعمل
- [ ] البيانات تنتقل بشكل صحيح

---

# 💰 المرحلة 4: الدفعات والأقساط (Week 6)

_(تم تخطي التفاصيل للاختصار - نفس الهيكل)_

---

# 🎁 المرحلة 5: حملات الخصومات والعمولات (Week 7)

_(تم تخطي التفاصيل للاختصار - نفس الهيكل)_

---

# 🛒 المرحلة 6: نقاط البيع POS (Week 7)

_(تم تخطي التفاصيل للاختصار - نفس الهيكل)_

---

# 📊 المرحلة 7: التقارير (Week 8)

_(تم تخطي التفاصيل للاختصار - نفس الهيكل)_

---

# 🏛️ المرحلة 8: الفوترة الإلكترونية (Week 8)

_(تم تخطي التفاصيل للاختصار - نفس الهيكل)_

---

# 🎯 طريقة الاستخدام

## خطوة بخطوة:

1. **افتح هذا الملف**
2. **اقرأ Task**
3. **انسخ الأمر** من مربع 📝
4. **الصقه في المحادثة معي**
5. **انتظر حتى أنتهي**
6. **راجع ✅ Checklist**
7. **انتقل للـ Task التالي**

---

**🚀 ابدأ الآن بـ Task 1.1!**

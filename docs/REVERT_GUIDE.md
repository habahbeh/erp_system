# دليل التراجع عن التغييرات
## How to Revert Changes - Step by Step Guide

تاريخ: 2025-11-09

---

## 🔄 طريقة التراجع عن التغييرات الأخيرة

إذا لم تعجبك أي تغييرات تم إجراؤها على الفاتورة، يمكنك التراجع بطريقتين:

---

## الطريقة 1: استخدام Git (الأسهل والأسرع) ✅

### الخطوة 1: تحقق من التغييرات الحالية
```bash
cd "/Users/mohammadhabahbeh/Desktop/My File/Project/erp_system"
git status
```

**ستشاهد**:
```
Modified:   apps/purchases/templates/purchases/invoices/invoice_form.html
```

### الخطوة 2: التراجع عن جميع التغييرات في ملف معين
```bash
# للتراجع عن تغييرات invoice_form.html فقط
git checkout apps/purchases/templates/purchases/invoices/invoice_form.html
```

### الخطوة 3: التحقق من التراجع
```bash
git status
```

**يجب أن ترى**: `nothing to commit, working tree clean`

### الخطوة 4: إعادة تشغيل الخادم
```bash
# أوقف الخادم (Ctrl+C)
# ثم شغله مرة أخرى
source venv/bin/activate
python manage.py runserver
```

---

## الطريقة 2: التراجع اليدوي (استعادة الإصدار السابق)

### النسخة السابقة الكاملة - POS Style (قبل التصغير)

إذا أردت العودة للنسخة السابقة **قبل تصغير الخطوط**، استبدل CSS التالي:

**في ملف**: `/Users/mohammadhabahbeh/Desktop/My File/Project/erp_system/apps/purchases/templates/purchases/invoices/invoice_form.html`

**ابحث عن** (حوالي السطر 239):
```css
/* Totals Section - POS Style - COMPACT VERSION */
```

**واستبدله بـ**:

```css
/* Totals Section - POS Style */
.totals-section {
    background: #ffffff;
    padding: 0;
    border-radius: 0;
    margin-top: 0;
    border: none;
}

.total-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 1rem;
    margin: 0;
    background-color: #ffffff;
    border-bottom: 1px dashed #dee2e6;
}

.total-item:last-child {
    border-bottom: none;
    border-top: 2px solid #000;
    padding: 1rem 1rem;
    margin-top: 0.5rem;
    background: #f8f9fa;
}

.total-label {
    font-weight: 400;
    font-size: 1rem;
    color: #212529;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.total-item:last-child .total-label {
    font-weight: 700;
    font-size: 1.1rem;
}

.total-value {
    font-weight: 700;
    font-family: 'Courier New', monospace;
    font-size: 1.3rem;
    color: #000;
    direction: ltr;
    text-align: right;
    min-width: 180px;
}

.total-item:last-child .total-value {
    font-size: 1.8rem;
    font-weight: 900;
}

/* Amount in words section */
.amount-in-words {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-top: 1rem;
    text-align: center;
}

.amount-in-words-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #856404;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.amount-in-words-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: #000;
    font-family: 'Arial', sans-serif;
}
```

**واستبدل أيضاً** (حوالي السطر 549):

**ابحث عن**:
```html
<div class="card mb-2">
    <div class="card-header bg-dark text-white py-2">
        <h6 class="mb-0">
```

**واستبدله بـ**:
```html
<div class="card mb-4">
    <div class="card-header bg-dark text-white">
        <h5 class="mb-0">
```

**واستبدل**:
```html
<div class="card-body p-2">
```

**بـ**:
```html
<div class="card-body p-3">
```

---

## الطريقة 3: حفظ نسخة احتياطية قبل التجريب

### قبل تجريب أي تغيير جديد:

```bash
cd "/Users/mohammadhabahbeh/Desktop/My File/Project/erp_system"

# إنشاء فرع جديد للتجريب
git checkout -b test-compact-layout

# الآن جرب أي تغييرات تريدها
# إذا لم تعجبك، ارجع للفرع الرئيسي
git checkout master

# إذا أعجبتك، ادمج التغييرات
git checkout master
git merge test-compact-layout
```

---

## 📊 مقارنة الإصدارات

### الإصدار الحالي (Compact - مضغوط):
- **حجم الخط للإجماليات**: 0.85rem → 1.1rem
- **حجم الخط للمبلغ النهائي**: 1.4rem
- **حجم خط التفقيط**: 0.95rem
- **المسافات**: مصغرة (padding: 0.3rem)
- **الهوامش**: mb-2 (صغيرة)
- **ميزة**: يقلل التمرير، كل شيء مرئي

### الإصدار السابق (Normal - عادي):
- **حجم الخط للإجماليات**: 1rem → 1.3rem
- **حجم الخط للمبلغ النهائي**: 1.8rem
- **حجم خط التفقيط**: 1.1rem
- **المسافات**: عادية (padding: 0.6rem - 1rem)
- **الهوامش**: mb-4 (كبيرة)
- **ميزة**: أكثر وضوحاً، لكن يحتاج تمرير

---

## 🎯 أي إصدار تختار؟

### اختر **Compact** (الحالي) إذا:
- ✅ تريد رؤية كل شيء بدون تمرير
- ✅ تعمل على شاشة صغيرة (لابتوب)
- ✅ السرعة أهم من الحجم الكبير
- ✅ تريد توفير المساحة

### اختر **Normal** (السابق) إذا:
- ✅ تريد أرقام كبيرة وواضحة جداً
- ✅ تعمل على شاشة كبيرة
- ✅ الوضوح أهم من توفير المساحة
- ✅ لا مشكلة مع التمرير

---

## 🔧 حلول وسطية (أفضل من الاثنين)

### الحل 1: تصغير المسافات فقط (بدون تصغير الخطوط)
احتفظ بأحجام الخطوط الأصلية، لكن قلل المسافات:

```css
.total-item {
    padding: 0.4rem 0.8rem;  /* وسط بين 0.3 و 0.6 */
}

.amount-in-words {
    padding: 0.8rem;         /* وسط بين 0.6 و 1rem */
}
```

### الحل 2: تصغير بسيط (10% فقط)
بدلاً من تصغير كبير، قلل بنسبة 10% فقط:

```css
.total-value {
    font-size: 1.17rem;      /* بدلاً من 1.3 (تقليل 10%) */
}

.total-item:last-child .total-value {
    font-size: 1.62rem;      /* بدلاً من 1.8 (تقليل 10%) */
}
```

---

## 📞 الخلاصة

**أسرع طريقة للتراجع**:
```bash
git checkout apps/purchases/templates/purchases/invoices/invoice_form.html
```

**إذا حذفت الملف بالخطأ**:
```bash
git restore apps/purchases/templates/purchases/invoices/invoice_form.html
```

**إذا أردت رؤية التغييرات قبل التراجع**:
```bash
git diff apps/purchases/templates/purchases/invoices/invoice_form.html
```

**إذا أردت حفظ التغييرات قبل التراجع**:
```bash
# احفظ التغييرات في ملف
git diff apps/purchases/templates/purchases/invoices/invoice_form.html > my_changes.patch

# ثم تراجع
git checkout apps/purchases/templates/purchases/invoices/invoice_form.html

# لاحقاً، إذا أردت استعادة التغييرات
git apply my_changes.patch
```

---

## ✅ نصائح مهمة

1. **دائماً اختبر على نسخة تجريبية أولاً**
2. **احفظ نسخة احتياطية قبل أي تغيير كبير**
3. **استخدم Git بدلاً من النسخ اليدوي**
4. **لا تخف من التجريب - يمكنك دائماً التراجع**

---

تم إنشاء هذا الدليل في: 2025-11-09

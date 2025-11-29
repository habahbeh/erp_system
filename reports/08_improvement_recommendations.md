# توصيات التحسين لنظام المشتريات

## ملخص التوصيات

| الفئة | عدد التوصيات | الأولوية |
|-------|-------------|----------|
| الأداء | 5 | عالية |
| الأمان | 4 | عالية |
| تجربة المستخدم | 6 | متوسطة |
| الكود | 5 | متوسطة |
| التوثيق | 3 | منخفضة |

---

## 1. تحسينات الأداء

### 1.1 تحسين استعلامات قاعدة البيانات

**الوضع الحالي:**
قد تحدث مشكلة N+1 عند تحميل الفواتير مع البنود

**التوصية:**
```python
# قبل
invoices = PurchaseInvoice.objects.filter(company=company)

# بعد
invoices = PurchaseInvoice.objects.filter(company=company)\
    .select_related('supplier', 'currency', 'branch', 'warehouse')\
    .prefetch_related('items', 'items__item')
```

**الفائدة:** تقليل عدد الاستعلامات من 50+ إلى 3-5

---

### 1.2 إضافة فهارس قاعدة البيانات

**التوصية:**
```python
class Meta:
    indexes = [
        models.Index(fields=['company', 'date']),
        models.Index(fields=['company', 'supplier', 'is_posted']),
        models.Index(fields=['company', 'number']),
    ]
```

**الفائدة:** تسريع عمليات البحث والفلترة

---

### 1.3 تخزين مؤقت (Caching)

**التوصية:**
```python
from django.core.cache import cache

def get_supplier_invoices(supplier_id):
    cache_key = f'supplier_invoices_{supplier_id}'
    result = cache.get(cache_key)
    if result is None:
        result = PurchaseInvoice.objects.filter(supplier_id=supplier_id)
        cache.set(cache_key, result, 300)  # 5 minutes
    return result
```

**الفائدة:** تقليل الضغط على قاعدة البيانات

---

### 1.4 Pagination للقوائم الكبيرة

**التوصية:**
```python
from django.core.paginator import Paginator

def invoice_list(request):
    invoices = PurchaseInvoice.objects.all()
    paginator = Paginator(invoices, 25)  # 25 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
```

**الفائدة:** تحسين أداء الصفحات

---

### 1.5 تأجيل حساب المجاميع

**التوصية:**
استخدام signals أو celery لحساب المجاميع في الخلفية

```python
from celery import shared_task

@shared_task
def recalculate_invoice_totals(invoice_id):
    invoice = PurchaseInvoice.objects.get(id=invoice_id)
    invoice.calculate_totals()
    invoice.save()
```

---

## 2. تحسينات الأمان

### 2.1 تشديد validation المدخلات

**التوصية:**
```python
from django.core.validators import MinValueValidator, MaxValueValidator

class PurchaseInvoiceItem(models.Model):
    quantity = models.DecimalField(
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit_price = models.DecimalField(
        validators=[MinValueValidator(Decimal('0'))]
    )
    tax_rate = models.DecimalField(
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ]
    )
```

---

### 2.2 حماية من Mass Assignment

**التوصية:**
```python
class PurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = PurchaseInvoice
        fields = ['supplier', 'date', 'notes']  # explicit fields only
        # لا تستخدم __all__
```

---

### 2.3 تسجيل الأحداث الحساسة

**التوصية:**
```python
import logging
logger = logging.getLogger('security')

def post_invoice(request, invoice):
    invoice.post(request.user)
    logger.info(f'Invoice {invoice.number} posted by {request.user}',
                extra={'ip': request.META.get('REMOTE_ADDR')})
```

---

### 2.4 Rate Limiting

**التوصية:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='POST')
def create_invoice(request):
    ...
```

---

## 3. تحسينات تجربة المستخدم

### 3.1 تحسين رسائل الخطأ

**التوصية:**
```python
VALIDATION_MESSAGES = {
    'empty_invoice': 'لا يمكن ترحيل فاتورة بدون بنود',
    'no_fiscal_year': 'لا توجد سنة مالية مفتوحة للتاريخ المحدد',
    'already_posted': 'الفاتورة مرحلة مسبقاً',
}
```

---

### 3.2 إضافة تأكيدات قبل العمليات الحساسة

**التوصية:**
```javascript
function confirmPost(invoiceId) {
    Swal.fire({
        title: 'تأكيد الترحيل',
        text: 'هل أنت متأكد من ترحيل هذه الفاتورة؟',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، ترحيل',
        cancelButtonText: 'إلغاء'
    }).then((result) => {
        if (result.isConfirmed) {
            postInvoice(invoiceId);
        }
    });
}
```

---

### 3.3 تحسين الفلاتر والبحث

**التوصية:**
```python
class InvoiceFilter(django_filters.FilterSet):
    date_range = django_filters.DateFromToRangeFilter(field_name='date')
    amount_min = django_filters.NumberFilter(field_name='total_with_tax', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='total_with_tax', lookup_expr='lte')

    class Meta:
        model = PurchaseInvoice
        fields = ['supplier', 'is_posted', 'invoice_type']
```

---

### 3.4 إضافة اختصارات لوحة المفاتيح

**التوصية:**
```javascript
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        document.getElementById('save-btn').click();
    }
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/purchases/invoices/create/';
    }
});
```

---

### 3.5 تحسين التحميل المسبق للبيانات

**التوصية:**
```javascript
// Prefetch data for dropdowns
$(document).ready(function() {
    $.get('/api/suppliers/', function(data) {
        window.suppliersCache = data;
    });
    $.get('/api/items/', function(data) {
        window.itemsCache = data;
    });
});
```

---

### 3.6 إضافة Progress Bar للعمليات الطويلة

**التوصية:**
```javascript
function importInvoices(file) {
    const progressBar = document.getElementById('progress');
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            progressBar.style.width = percent + '%';
        }
    });

    xhr.send(formData);
}
```

---

## 4. تحسينات الكود

### 4.1 استخدام Type Hints

**التوصية:**
```python
from decimal import Decimal
from typing import Optional, List

def calculate_totals(self) -> None:
    """حساب مجاميع الفاتورة"""
    items: List[PurchaseInvoiceItem] = self.items.all()
    self.subtotal_before_discount: Decimal = sum(
        item.subtotal for item in items
    )
```

---

### 4.2 توحيد أسماء الحقول

**التوصية:**
| النموذج | الحالي | المقترح |
|---------|--------|---------|
| PurchaseInvoiceItem | unit | uom |
| PurchaseOrderItem | ? | uom |
| PurchaseRequestItem | unit | uom |

---

### 4.3 استخدام Mixins للكود المشترك

**التوصية:**
```python
class InvoiceCalculationMixin:
    def calculate_totals(self):
        items = self.items.all()
        self.subtotal_before_discount = sum(item.subtotal for item in items)
        # ... shared logic

class PurchaseInvoice(InvoiceCalculationMixin, DocumentBaseModel):
    pass

class SalesInvoice(InvoiceCalculationMixin, DocumentBaseModel):
    pass
```

---

### 4.4 إضافة Property Methods

**التوصية:**
```python
class PurchaseInvoice(models.Model):
    @property
    def is_overdue(self) -> bool:
        """هل تجاوزت تاريخ الاستحقاق"""
        if self.due_date and not self.is_paid:
            return date.today() > self.due_date
        return False

    @property
    def days_overdue(self) -> int:
        """عدد أيام التأخير"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
```

---

### 4.5 تحسين معالجة الأخطاء

**التوصية:**
```python
class PurchaseError(Exception):
    """Base exception for purchase module"""
    pass

class InvoicePostingError(PurchaseError):
    """Error during invoice posting"""
    pass

class InvoiceValidationError(PurchaseError):
    """Validation error"""
    pass
```

---

## 5. تحسينات التوثيق

### 5.1 إضافة Docstrings

**التوصية:**
```python
def post(self, user) -> Tuple['StockIn', 'JournalEntry']:
    """
    ترحيل فاتورة المشتريات.

    يقوم بإنشاء:
    - حركة إدخال مخزون (StockIn)
    - قيد محاسبي (JournalEntry)

    Args:
        user: المستخدم الذي يقوم بالترحيل

    Returns:
        Tuple من (StockIn, JournalEntry)

    Raises:
        ValidationError: إذا كانت الفاتورة فارغة أو مرحلة مسبقاً
    """
```

---

### 5.2 إنشاء دليل API

**التوصية:**
استخدام drf-spectacular أو drf-yasg لتوليد توثيق API تلقائي

---

### 5.3 إضافة أمثلة استخدام

**التوصية:**
إنشاء مجلد `examples/` يحتوي على:
- `create_invoice.py`
- `post_invoice.py`
- `generate_report.py`

---

## جدول الأولويات

| التحسين | الأثر | الجهد | الأولوية |
|---------|-------|-------|----------|
| تحسين استعلامات DB | عالي | منخفض | 1 |
| إضافة فهارس | عالي | منخفض | 2 |
| تشديد validation | عالي | متوسط | 3 |
| تحسين رسائل الخطأ | متوسط | منخفض | 4 |
| توحيد أسماء الحقول | متوسط | متوسط | 5 |
| إضافة Docstrings | منخفض | عالي | 6 |

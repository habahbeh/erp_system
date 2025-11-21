# 🚀 خطة التنفيذ - المرحلة 1: إكمال نظام إدارة المخزون

**تاريخ الإنشاء:** 2025-11-21
**الهدف:** إكمال نظام إدارة المخزون بالكامل مع التكامل التلقائي

---

## 📋 تعليمات لـ Claude Code

هذا الملف يحتوي على مراحل العمل المطلوبة لإكمال نظام المخزون.

**كيفية التنفيذ:**
1. قم بتنفيذ كل مرحلة بالترتيب
2. لا تنتقل للمرحلة التالية إلا بعد إتمام المرحلة الحالية
3. بعد كل مرحلة، قم بالاختبار للتأكد من عمل كل شيء
4. علّم على ✅ عند إتمام كل خطوة

**الأولويات:**
- 🔴 **المرحلة 1A:** عاجل جداً - يجب إتمامه أولاً
- 🟡 **المرحلة 1B:** مهم - بعد 1A
- 🟢 **المرحلة 1C:** تحسينات - اختياري

---

# 🔴 المرحلة 1A: الأساسيات العاجلة

## المهمة 1: إضافة الحقول المفقودة في ItemStock

**الملف:** `apps/inventory/models.py`
**الموقع:** ItemStock class (السطر ~1653)
**الوقت المتوقع:** 2-3 ساعات

### الخطوات:

#### 1.1 افتح الملف واقرأ ItemStock Model
```bash
# اقرأ الملف
apps/inventory/models.py
# ابحث عن class ItemStock
```

#### 1.2 أضف الحقول التالية بعد حقل `last_movement_date`:

```python
    # الرصيد الافتتاحي
    opening_balance = models.DecimalField(
        _('الرصيد الافتتاحي'),
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text=_('الرصيد عند بداية الفترة المالية')
    )

    opening_value = models.DecimalField(
        _('قيمة الرصيد الافتتاحي'),
        max_digits=15,
        decimal_places=3,
        default=0
    )

    # معلومات آخر عملية شراء
    last_purchase_price = models.DecimalField(
        _('آخر سعر شراء للوحدة'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('سعر الوحدة في آخر عملية شراء')
    )

    last_purchase_total = models.DecimalField(
        _('آخر سعر شراء إجمالي'),
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('إجمالي تكلفة آخر عملية شراء')
    )

    last_purchase_date = models.DateField(
        _('تاريخ آخر شراء'),
        null=True,
        blank=True
    )

    last_supplier = models.ForeignKey(
        'core.BusinessPartner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('آخر مورد'),
        related_name='last_supplied_stocks',
        limit_choices_to={'partner_type__in': ['supplier', 'both']}
    )

    # حدود المخزون
    min_level = models.DecimalField(
        _('الحد الأدنى للمخزون'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('عند الوصول لهذا الحد يتم التنبيه')
    )

    max_level = models.DecimalField(
        _('الحد الأقصى للمخزون'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('الحد الأقصى المسموح للتخزين')
    )

    reorder_point = models.DecimalField(
        _('نقطة إعادة الطلب'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('عند الوصول لهذه النقطة يتم طلب المزيد')
    )

    # موقع التخزين
    storage_location = models.CharField(
        _('موقع التخزين'),
        max_length=100,
        blank=True,
        help_text=_('الرف أو المنطقة في المستودع')
    )
```

#### 1.3 أضف method جديد في ItemStock لتحديث معلومات آخر شراء:

```python
    def update_last_purchase(self, price, total, date, supplier=None):
        """
        تحديث معلومات آخر عملية شراء

        Args:
            price: سعر الوحدة
            total: الإجمالي
            date: تاريخ الشراء
            supplier: المورد (اختياري)
        """
        self.last_purchase_price = price
        self.last_purchase_total = total
        self.last_purchase_date = date
        if supplier:
            self.last_supplier = supplier
        self.save(update_fields=[
            'last_purchase_price',
            'last_purchase_total',
            'last_purchase_date',
            'last_supplier'
        ])

    def check_reorder_needed(self):
        """
        التحقق من الحاجة لإعادة الطلب

        Returns:
            bool: True إذا كانت الكمية أقل من نقطة إعادة الطلب
        """
        if self.reorder_point:
            return self.quantity <= self.reorder_point
        return False

    def is_below_min_level(self):
        """
        التحقق من أن الرصيد أقل من الحد الأدنى

        Returns:
            bool: True إذا كانت الكمية أقل من الحد الأدنى
        """
        if self.min_level:
            return self.quantity < self.min_level
        return False

    def is_above_max_level(self):
        """
        التحقق من أن الرصيد أعلى من الحد الأقصى

        Returns:
            bool: True إذا كانت الكمية أعلى من الحد الأقصى
        """
        if self.max_level:
            return self.quantity > self.max_level
        return False
```

#### 1.4 قم بعمل Migration:

```bash
# في الـ terminal
python manage.py makemigrations inventory -n add_itemstock_fields
python manage.py migrate inventory
```

### ✅ Checklist:
- [ ] تم إضافة جميع الحقول الجديدة
- [ ] تم إضافة الـ methods الجديدة
- [ ] تم عمل makemigrations بنجاح
- [ ] تم عمل migrate بنجاح
- [ ] لا توجد أخطاء في الكود

---

## المهمة 2: تحديث StockIn.post() لتحديث معلومات آخر شراء

**الملف:** `apps/inventory/models.py`
**الموقع:** StockIn.post() method (السطر ~163)
**الوقت المتوقع:** 30 دقيقة

### الخطوات:

#### 2.1 ابحث عن method `StockIn.post()`

#### 2.2 أضف هذا الكود بعد تحديث الـ stock (بعد السطر ~207):

```python
            # تحديث معلومات آخر شراء
            stock.update_last_purchase(
                price=line.unit_cost,
                total=line.total_cost,
                date=self.date,
                supplier=self.supplier if hasattr(self, 'supplier') else None
            )
```

### ✅ Checklist:
- [ ] تم إضافة الكود في المكان الصحيح
- [ ] لا توجد أخطاء syntax

---

## المهمة 3: إضافة Helper Methods في ItemVariant

**الملف:** `apps/core/models/item_models.py`
**الموقع:** ItemVariant class (السطر ~328)
**الوقت المتوقع:** 1 ساعة

### الخطوات:

#### 3.1 افتح الملف واقرأ ItemVariant Model

#### 3.2 أضف هذه الـ methods بعد method `get_full_name()`:

```python
    def get_attribute_values_dict(self):
        """
        الحصول على خصائص المتغير كـ dictionary

        Returns:
            dict: {attribute_name: value}
        """
        attributes = self.variant_attribute_values.select_related('attribute', 'value')
        return {
            av.attribute.name: av.value.value
            for av in attributes
        }

    def get_stock_across_warehouses(self, company=None):
        """
        الحصول على الرصيد في كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            QuerySet: أرصدة المادة في كل المستودعات
        """
        from apps.inventory.models import ItemStock

        filters = {
            'item': self.item,
            'item_variant': self
        }

        if company:
            filters['company'] = company
        elif self.company:
            filters['company'] = self.company

        return ItemStock.objects.filter(**filters).select_related('warehouse')

    def get_total_stock(self, company=None):
        """
        إجمالي الرصيد عبر كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            dict: {
                'total_quantity': Decimal,
                'total_reserved': Decimal,
                'total_available': Decimal,
                'total_value': Decimal,
                'warehouses_count': int
            }
        """
        from apps.inventory.models import ItemStock

        return ItemStock.get_total_stock(
            item=self.item,
            item_variant=self,
            company=company or self.company
        )

    def get_average_cost(self, company=None):
        """
        متوسط التكلفة عبر كل المستودعات

        Args:
            company: الشركة (اختياري)

        Returns:
            Decimal: متوسط التكلفة الموزون
        """
        stocks = self.get_stock_across_warehouses(company)

        total_value = sum(s.total_value for s in stocks)
        total_quantity = sum(s.quantity for s in stocks)

        if total_quantity > 0:
            return total_value / total_quantity

        # إذا لم يوجد رصيد، أرجع cost_price إذا كان موجوداً
        return self.cost_price or 0

    def get_total_available(self, company=None):
        """
        إجمالي الكمية المتاحة (غير المحجوزة)

        Args:
            company: الشركة (اختياري)

        Returns:
            Decimal: الكمية المتاحة
        """
        stocks = self.get_stock_across_warehouses(company)
        return sum(s.get_available_quantity() for s in stocks)

    def check_stock_availability(self, quantity, warehouse=None, company=None):
        """
        التحقق من توفر كمية معينة

        Args:
            quantity: الكمية المطلوبة
            warehouse: المستودع (اختياري - إذا لم يحدد، يتحقق من كل المستودعات)
            company: الشركة (اختياري)

        Returns:
            dict: {
                'available': bool,
                'quantity_available': Decimal,
                'shortage': Decimal
            }
        """
        from apps.inventory.models import ItemStock
        from decimal import Decimal

        if warehouse:
            # التحقق من مستودع محدد
            try:
                stock = ItemStock.objects.get(
                    item=self.item,
                    item_variant=self,
                    warehouse=warehouse,
                    company=company or self.company
                )
                available = stock.get_available_quantity()
            except ItemStock.DoesNotExist:
                available = Decimal('0')
        else:
            # التحقق من كل المستودعات
            available = self.get_total_available(company)

        return {
            'available': available >= quantity,
            'quantity_available': available,
            'shortage': max(quantity - available, Decimal('0'))
        }
```

### ✅ Checklist:
- [ ] تم إضافة جميع الـ methods
- [ ] لا توجد أخطاء syntax
- [ ] الكود منظم ومرتب

---

## المهمة 4: إنشاء Django Signals للربط التلقائي

**الوقت المتوقع:** 4-5 ساعات

### 4.1 إنشاء Signals للـ Purchases Module

**ملف جديد:** `apps/purchases/signals.py`

#### الخطوات:

##### 4.1.1 أنشئ الملف الجديد:

```python
# apps/purchases/signals.py
"""
إشارات المشتريات
تربط فواتير المشتريات بنظام المخزون تلقائياً
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import PurchaseInvoice, PurchaseInvoiceLine
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseInvoice)
def create_stock_in_on_purchase_post(sender, instance, created, **kwargs):
    """
    إنشاء سند إدخال تلقائياً عند اعتماد فاتورة شراء

    يتم التشغيل عند:
    - اعتماد الفاتورة (is_posted = True)
    - إذا لم يكن لها سند إدخال مسبقاً
    """
    # تحقق من أن الفاتورة معتمدة ولم يتم إنشاء سند إدخال لها
    if not instance.is_posted:
        return

    # تحقق من وجود سند إدخال مرتبط
    from apps.inventory.models import StockIn

    existing_stock_in = StockIn.objects.filter(
        purchase_invoice=instance,
        company=instance.company
    ).first()

    if existing_stock_in:
        logger.info(f"StockIn already exists for PurchaseInvoice {instance.number}")
        return

    # إنشاء سند إدخال جديد
    try:
        with transaction.atomic():
            stock_in = StockIn.objects.create(
                company=instance.company,
                branch=getattr(instance, 'branch', None),
                date=instance.invoice_date,
                warehouse=instance.warehouse if hasattr(instance, 'warehouse') else instance.branch.default_warehouse,
                source_type='purchase',
                supplier=instance.supplier if hasattr(instance, 'supplier') else None,
                purchase_invoice=instance,
                reference=instance.number,
                notes=f'سند إدخال تلقائي لفاتورة شراء {instance.number}',
                created_by=instance.created_by
            )

            # إنشاء سطور السند من سطور الفاتورة
            from apps.inventory.models import StockDocumentLine

            for line in instance.lines.all():
                # تأكد من أن الصنف له مخزون (يمكن تخطي الخدمات)
                if not line.item:
                    continue

                StockDocumentLine.objects.create(
                    stock_in=stock_in,
                    item=line.item,
                    item_variant=line.item_variant if hasattr(line, 'item_variant') else None,
                    quantity=line.quantity,
                    unit_cost=line.unit_price,  # أو line.unit_cost حسب الـ model
                    notes=line.description or ''
                )

            # ترحيل السند تلقائياً
            stock_in.post(user=instance.created_by)

            logger.info(f"StockIn {stock_in.number} created and posted for PurchaseInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error creating StockIn for PurchaseInvoice {instance.number}: {str(e)}")
        # لا نرفع exception لعدم منع حفظ الفاتورة


@receiver(post_delete, sender=PurchaseInvoice)
def delete_stock_in_on_purchase_delete(sender, instance, **kwargs):
    """
    حذف سند الإدخال عند حذف فاتورة الشراء
    """
    from apps.inventory.models import StockIn

    try:
        stock_ins = StockIn.objects.filter(
            purchase_invoice=instance,
            company=instance.company
        )

        for stock_in in stock_ins:
            # إلغاء الترحيل أولاً
            if stock_in.is_posted:
                stock_in.unpost()

            # ثم الحذف
            stock_in.delete()
            logger.info(f"StockIn {stock_in.number} deleted with PurchaseInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error deleting StockIn for PurchaseInvoice {instance.number}: {str(e)}")
```

##### 4.1.2 قم بتفعيل الـ Signals في AppConfig:

**الملف:** `apps/purchases/apps.py`

أضف:

```python
class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchases'
    verbose_name = 'المشتريات'

    def ready(self):
        """تفعيل الإشارات عند تشغيل التطبيق"""
        import apps.purchases.signals  # noqa
```

### ✅ Checklist:
- [ ] تم إنشاء ملف signals.py في purchases
- [ ] تم إضافة signal لـ post_save
- [ ] تم إضافة signal لـ post_delete
- [ ] تم تفعيل الـ signals في apps.py
- [ ] لا توجد أخطاء syntax

---

### 4.2 إنشاء Signals للـ Sales Module

**ملف جديد:** `apps/sales/signals.py`

#### الخطوات:

##### 4.2.1 أنشئ الملف الجديد:

```python
# apps/sales/signals.py
"""
إشارات المبيعات
تربط فواتير المبيعات بنظام المخزون تلقائياً
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import SalesInvoice, SalesInvoiceLine
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SalesInvoice)
def create_stock_out_on_sales_post(sender, instance, created, **kwargs):
    """
    إنشاء سند إخراج تلقائياً عند اعتماد فاتورة بيع

    يتم التشغيل عند:
    - اعتماد الفاتورة (is_posted = True)
    - إذا لم يكن لها سند إخراج مسبقاً
    """
    # تحقق من أن الفاتورة معتمدة
    if not instance.is_posted:
        return

    # تحقق من وجود سند إخراج مرتبط
    from apps.inventory.models import StockOut

    existing_stock_out = StockOut.objects.filter(
        sales_invoice=instance,
        company=instance.company
    ).first()

    if existing_stock_out:
        logger.info(f"StockOut already exists for SalesInvoice {instance.number}")
        return

    # إنشاء سند إخراج جديد
    try:
        with transaction.atomic():
            stock_out = StockOut.objects.create(
                company=instance.company,
                branch=getattr(instance, 'branch', None),
                date=instance.invoice_date,
                warehouse=instance.warehouse if hasattr(instance, 'warehouse') else instance.branch.default_warehouse,
                destination_type='sales',
                customer=instance.customer if hasattr(instance, 'customer') else None,
                sales_invoice=instance,
                reference=instance.number,
                notes=f'سند إخراج تلقائي لفاتورة بيع {instance.number}',
                created_by=instance.created_by
            )

            # إنشاء سطور السند من سطور الفاتورة
            from apps.inventory.models import StockDocumentLine

            for line in instance.lines.all():
                # تأكد من أن الصنف له مخزون (يمكن تخطي الخدمات)
                if not line.item:
                    continue

                StockDocumentLine.objects.create(
                    stock_out=stock_out,
                    item=line.item,
                    item_variant=line.item_variant if hasattr(line, 'item_variant') else None,
                    quantity=line.quantity,
                    unit_cost=0,  # سيتم تحديثه تلقائياً من متوسط التكلفة عند الترحيل
                    notes=line.description or ''
                )

            # ترحيل السند تلقائياً
            # هنا سيتم التحقق من توفر الكمية ورفع exception إذا لم تكن متوفرة
            stock_out.post(user=instance.created_by)

            logger.info(f"StockOut {stock_out.number} created and posted for SalesInvoice {instance.number}")

    except ValidationError as ve:
        # خطأ في التحقق من الكمية - يجب إبلاغ المستخدم
        logger.error(f"Validation error creating StockOut for SalesInvoice {instance.number}: {str(ve)}")
        # يمكن إضافة رسالة للمستخدم هنا
        raise  # إعادة رفع الخطأ لإيقاف العملية

    except Exception as e:
        logger.error(f"Error creating StockOut for SalesInvoice {instance.number}: {str(e)}")
        # لا نرفع exception لعدم منع حفظ الفاتورة في حالات أخرى


@receiver(post_delete, sender=SalesInvoice)
def delete_stock_out_on_sales_delete(sender, instance, **kwargs):
    """
    حذف سند الإخراج عند حذف فاتورة البيع
    """
    from apps.inventory.models import StockOut

    try:
        stock_outs = StockOut.objects.filter(
            sales_invoice=instance,
            company=instance.company
        )

        for stock_out in stock_outs:
            # إلغاء الترحيل أولاً
            if stock_out.is_posted:
                stock_out.unpost()

            # ثم الحذف
            stock_out.delete()
            logger.info(f"StockOut {stock_out.number} deleted with SalesInvoice {instance.number}")

    except Exception as e:
        logger.error(f"Error deleting StockOut for SalesInvoice {instance.number}: {str(e)}")
```

##### 4.2.2 قم بتفعيل الـ Signals في AppConfig:

**الملف:** `apps/sales/apps.py`

أضف:

```python
class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sales'
    verbose_name = 'المبيعات'

    def ready(self):
        """تفعيل الإشارات عند تشغيل التطبيق"""
        import apps.sales.signals  # noqa
```

### ✅ Checklist:
- [ ] تم إنشاء ملف signals.py في sales
- [ ] تم إضافة signal لـ post_save
- [ ] تم إضافة signal لـ post_delete
- [ ] تم تفعيل الـ signals في apps.py
- [ ] لا توجد أخطاء syntax

---

### 4.3 تحسين Inventory Signals

**الملف:** `apps/inventory/signals.py` (موجود)

#### الخطوات:

##### 4.3.1 اقرأ الملف الحالي وعدّله:

```python
# apps/inventory/signals.py
"""
إشارات المخزون
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import ItemStock
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ItemStock)
def check_low_stock_alert(sender, instance, created, **kwargs):
    """
    التحقق من انخفاض المخزون وإرسال تنبيه
    """
    # التحقق من الحد الأدنى
    if instance.is_below_min_level():
        logger.warning(
            f"Low stock alert: {instance.item.name} "
            f"(Variant: {instance.item_variant.code if instance.item_variant else 'N/A'}) "
            f"in warehouse {instance.warehouse.name}. "
            f"Current: {instance.quantity}, Min: {instance.min_level}"
        )
        # يمكن إضافة إرسال إشعار للمستخدمين هنا
        # من خلال notification system أو email

    # التحقق من نقطة إعادة الطلب
    if instance.check_reorder_needed():
        logger.info(
            f"Reorder point reached: {instance.item.name} "
            f"(Variant: {instance.item_variant.code if instance.item_variant else 'N/A'}) "
            f"in warehouse {instance.warehouse.name}. "
            f"Current: {instance.quantity}, Reorder Point: {instance.reorder_point}"
        )
        # يمكن إضافة إنشاء طلب شراء تلقائي هنا


@receiver(post_save, sender=ItemStock)
def delete_empty_stock(sender, instance, **kwargs):
    """
    حذف رصيد المادة إذا أصبح صفر (اختياري)

    ملاحظة: معطل حالياً للحفاظ على السجل التاريخي
    يمكن تفعيله حسب الحاجة
    """
    # if instance.quantity == 0 and instance.reserved_quantity == 0:
    #     instance.delete()
    #     logger.info(f"Deleted empty stock for {instance.item.name} in {instance.warehouse.name}")
    pass


@receiver(pre_delete, sender=ItemStock)
def prevent_delete_if_has_balance(sender, instance, **kwargs):
    """
    منع حذف رصيد المادة إذا كان له رصيد
    """
    from django.core.exceptions import ValidationError

    if instance.quantity != 0:
        raise ValidationError(
            f'لا يمكن حذف رصيد المادة {instance.item.name} '
            f'في المستودع {instance.warehouse.name} لأن الرصيد = {instance.quantity}'
        )
```

### ✅ Checklist:
- [ ] تم تحديث inventory signals
- [ ] تم إضافة التحقق من low stock
- [ ] تم إضافة منع الحذف عند وجود رصيد
- [ ] لا توجد أخطاء syntax

---

## المهمة 5: إضافة حقل StockMovement.balance_before

**الملف:** `apps/inventory/models.py`
**الموقع:** StockMovement class (السطر ~1311)
**الوقت المتوقع:** 30 دقيقة

### الخطوات:

#### 5.1 أضف الحقل الجديد قبل `balance_quantity`:

```python
    # الرصيد قبل وبعد الحركة
    balance_before = models.DecimalField(
        _('رصيد الكمية قبل الحركة'),
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text=_('الرصيد قبل تطبيق هذه الحركة')
    )

    balance_quantity = models.DecimalField(
        _('رصيد الكمية'),
        max_digits=12,
        decimal_places=3
    )
```

#### 5.2 عدّل كود إنشاء StockMovement في StockIn.post():

ابحث عن السطر الذي ينشئ StockMovement (~209) وعدّله:

```python
            # إنشاء حركة المادة
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='in',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
                total_cost=line.total_cost,
                balance_before=old_quantity,  # إضافة
                balance_quantity=stock.quantity,
                balance_value=stock.total_value,
                reference_type='stock_in',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )
```

#### 5.3 عدّل كود إنشاء StockMovement في StockOut.post():

ابحث عن السطر الذي ينشئ StockMovement (~561) وعدّله:

```python
            # إنشاء حركة المادة
            StockMovement.objects.create(
                company=self.company,
                branch=getattr(self, 'branch', None),
                date=timezone.now(),
                movement_type='out',
                item=line.item,
                item_variant=line.item_variant,
                warehouse=self.warehouse,
                quantity=-line.quantity,
                unit_cost=line.unit_cost,
                total_cost=-line.total_cost,
                balance_before=old_quantity,  # إضافة
                balance_quantity=stock.quantity,
                balance_value=stock.total_value,
                reference_type='stock_out',
                reference_id=self.pk,
                reference_number=self.number,
                created_by=user or self.created_by
            )
```

#### 5.4 عدّل كود StockTransfer أيضاً (سطر ~1034 و ~1110):

**في send() method:**
```python
            StockMovement.objects.create(
                # ...
                balance_before=old_quantity,  # إضافة
                balance_quantity=source_stock.quantity,
                # ...
            )
```

**في receive() method:**
```python
            StockMovement.objects.create(
                # ...
                balance_before=old_quantity,  # إضافة
                balance_quantity=dest_stock.quantity,
                # ...
            )
```

#### 5.5 قم بعمل Migration:

```bash
python manage.py makemigrations inventory -n add_balance_before
python manage.py migrate inventory
```

### ✅ Checklist:
- [ ] تم إضافة حقل balance_before
- [ ] تم تحديث StockIn.post()
- [ ] تم تحديث StockOut.post()
- [ ] تم تحديث StockTransfer methods
- [ ] تم عمل migration بنجاح
- [ ] لا توجد أخطاء

---

## المهمة 6: اختبار التكامل الكامل

**الوقت المتوقع:** 2 ساعة

### الخطوات:

#### 6.1 اختبر النظام يدوياً:

```bash
# شغل السيرفر
python manage.py runserver
```

##### 6.1.1 اختبار دورة الشراء:
1. افتح نظام المشتريات
2. أنشئ فاتورة شراء جديدة
3. أضف أصناف
4. اعتمد الفاتورة
5. **تحقق:** هل تم إنشاء StockIn تلقائياً؟
6. **تحقق:** هل تم تحديث ItemStock؟
7. **تحقق:** هل تم إنشاء StockMovement؟
8. **تحقق:** هل تم تحديث last_purchase_* fields؟

##### 6.1.2 اختبار دورة البيع:
1. افتح نظام المبيعات
2. أنشئ فاتورة بيع جديدة
3. أضف أصناف (متوفرة في المخزون)
4. اعتمد الفاتورة
5. **تحقق:** هل تم إنشاء StockOut تلقائياً؟
6. **تحقق:** هل تم تحديث ItemStock (نقص الكمية)؟
7. **تحقق:** هل تم إنشاء StockMovement؟
8. **تحقق:** هل متوسط التكلفة ثابت؟

##### 6.1.3 اختبار منع البيع عند عدم توفر الكمية:
1. حاول بيع كمية أكبر من المتاح
2. **تحقق:** هل تم رفض العملية؟
3. **تحقق:** هل ظهرت رسالة خطأ واضحة؟

##### 6.1.4 اختبار السيناريو الكامل:
```
شراء 100 قطعة بسعر 10 دينار
→ متوسط التكلفة = 10

شراء 50 قطعة بسعر 12 دينار
→ متوسط التكلفة = (100×10 + 50×12) / 150 = 10.67

بيع 80 قطعة
→ متوسط التكلفة يبقى 10.67
→ الرصيد = 70
→ القيمة = 70 × 10.67 = 746.67
```

#### 6.2 تحقق من Logs:

```bash
# افتح ملف django.log
tail -f django.log
```

ابحث عن رسائل:
- "StockIn created and posted for PurchaseInvoice"
- "StockOut created and posted for SalesInvoice"
- "Low stock alert"
- أي أخطاء

### ✅ Checklist:
- [ ] دورة الشراء تعمل بالكامل
- [ ] دورة البيع تعمل بالكامل
- [ ] منع البيع عند نفاد الكمية يعمل
- [ ] حساب متوسط التكلفة صحيح
- [ ] الـ Signals تعمل تلقائياً
- [ ] last_purchase fields تتحدث
- [ ] balance_before يُحفظ بشكل صحيح
- [ ] لا توجد أخطاء في الـ logs

---

## 📊 ملخص المرحلة 1A

عند إتمام كل المهام أعلاه، ستكون قد أكملت:

✅ **ما تم إنجازه:**
1. إضافة 9 حقول جديدة في ItemStock
2. إضافة 7 methods جديدة في ItemStock
3. إضافة 7 methods جديدة في ItemVariant
4. إنشاء نظام Signals كامل للربط التلقائي
5. تحديث جميع الـ StockMovement لحفظ balance_before
6. اختبار التكامل الكامل

✅ **النتيجة:**
- نظام مخزون متكامل 100%
- ربط تلقائي بين الفواتير والمخزون
- تتبع دقيق لجميع الحركات
- حساب صحيح لمتوسط التكلفة

---

# 🟡 المرحلة 1B: التحسينات المهمة

## المهمة 7: تحسين Indexes للأداء

**الوقت المتوقع:** 1 ساعة

### الخطوات:

#### 7.1 في Item Model:

**الملف:** `apps/core/models/item_models.py`

أضف في class Meta (بعد ordering):

```python
    class Meta:
        verbose_name = _('مادة')
        verbose_name_plural = _('المواد')
        ordering = ['name']
        unique_together = [['code', 'company'], ['barcode', 'company']]
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['category', 'company']),
            models.Index(fields=['is_active', 'company']),
            models.Index(fields=['barcode']),
        ]
```

#### 7.2 في ItemVariant Model:

أضف في class Meta:

```python
    class Meta:
        verbose_name = _('متغير المادة')
        verbose_name_plural = _('متغيرات المواد')
        ordering = ['item', 'code']
        unique_together = [['item', 'code']]
        indexes = [
            models.Index(fields=['item', 'is_active']),
            models.Index(fields=['barcode']),
        ]
```

#### 7.3 في StockMovement Model:

عدّل الـ indexes الموجودة:

```python
    class Meta:
        # ...
        indexes = [
            models.Index(fields=['item', 'warehouse', '-date']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['warehouse', 'movement_type', '-date']),
            models.Index(fields=['company', '-date']),
        ]
```

#### 7.4 قم بعمل Migration:

```bash
python manage.py makemigrations core inventory -n improve_indexes
python manage.py migrate
```

### ✅ Checklist:
- [ ] تم إضافة indexes في Item
- [ ] تم إضافة indexes في ItemVariant
- [ ] تم تحسين indexes في StockMovement
- [ ] تم عمل migration بنجاح

---

## المهمة 8: إضافة Validations متقدمة

**الوقت المتوقع:** 2 ساعة

### 8.1 منع حذف Item إذا كان له رصيد

**الملف:** `apps/core/models/item_models.py`

أضف في Item class:

```python
    def delete(self, *args, **kwargs):
        """منع الحذف إذا كان للمادة رصيد في المخزون"""
        from apps.inventory.models import ItemStock
        from django.core.exceptions import ValidationError

        # التحقق من وجود رصيد
        stock_exists = ItemStock.objects.filter(
            item=self,
            quantity__gt=0
        ).exists()

        if stock_exists:
            raise ValidationError(
                f'لا يمكن حذف المادة "{self.name}" لأن لها رصيد في المخزون. '
                'يرجى إفراغ المخزون أولاً أو استخدام "إيقاف الإنتاج".'
            )

        super().delete(*args, **kwargs)
```

### 8.2 منع تعطيل Warehouse إذا كان فيه رصيد

**الملف:** `apps/core/models/company_models.py`

أضف في Warehouse class:

```python
    def save(self, *args, **kwargs):
        # التحقق من المستودع الرئيسي
        if self.is_main:
            Warehouse.objects.filter(company=self.company, is_main=True).exclude(pk=self.pk).update(is_main=False)

        # منع التعطيل إذا كان هناك رصيد
        if not self.is_active and self.pk:  # تعديل على مستودع موجود
            from apps.inventory.models import ItemStock
            from django.core.exceptions import ValidationError

            stock_exists = ItemStock.objects.filter(
                warehouse=self,
                quantity__gt=0
            ).exists()

            if stock_exists:
                raise ValidationError(
                    f'لا يمكن تعطيل المستودع "{self.name}" لأن به أرصدة. '
                    'يرجى نقل أو إفراغ المخزون أولاً.'
                )

        super().save(*args, **kwargs)
```

### 8.3 منع الرصيد السالب (حسب إعدادات warehouse)

**الملف:** `apps/inventory/models.py`

عدّل في StockOut.post() method (بعد السطر ~537):

```python
            # التحقق من الكمية المتاحة
            available_quantity = stock.quantity - stock.reserved_quantity

            # التحقق من السماح بالرصيد السالب
            if not self.warehouse.allow_negative_stock:
                if available_quantity < line.quantity:
                    raise ValidationError(
                        f'الكمية المتاحة من {line.item.name} ({available_quantity}) '
                        f'أقل من المطلوب ({line.quantity}). '
                        f'المستودع "{self.warehouse.name}" لا يسمح بالرصيد السالب.'
                    )
            else:
                # تحذير فقط
                if available_quantity < line.quantity:
                    logger.warning(
                        f'Negative stock will occur for {line.item.name} '
                        f'in warehouse {self.warehouse.name}. '
                        f'Available: {available_quantity}, Required: {line.quantity}'
                    )
```

### ✅ Checklist:
- [ ] تم إضافة منع حذف Item عند وجود رصيد
- [ ] تم إضافة منع تعطيل Warehouse عند وجود رصيد
- [ ] تم تحسين التحقق من الرصيد السالب
- [ ] لا توجد أخطاء

---

## المهمة 9: تحسين Warehouse Model

**الملف:** `apps/core/models/company_models.py`
**الوقت المتوقع:** 1 ساعة

### الخطوات:

#### 9.1 أضف حقل branch:

```python
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name=_('الفرع'),
        help_text=_('الفرع التابع له المستودع')
    )
```

#### 9.2 أضف حقل warehouse_type:

```python
    WAREHOUSE_TYPE_CHOICES = [
        ('main', _('رئيسي')),
        ('branch', _('فرعي')),
        ('transit', _('ترانزيت')),
        ('damaged', _('تالف')),
        ('returns', _('مرتجعات')),
        ('quarantine', _('حجر صحي')),
        ('virtual', _('افتراضي')),
    ]

    warehouse_type = models.CharField(
        _('نوع المستودع'),
        max_length=20,
        choices=WAREHOUSE_TYPE_CHOICES,
        default='branch',
        help_text=_('تصنيف المستودع حسب الاستخدام')
    )
```

#### 9.3 عدّل unique_together:

```python
    class Meta:
        verbose_name = _('مستودع')
        verbose_name_plural = _('المستودعات')
        unique_together = [['company', 'code'], ['branch', 'code']]
        ordering = ['name']
```

#### 9.4 قم بعمل Migration:

```bash
python manage.py makemigrations core -n improve_warehouse_model
# قد تحتاج لإعطاء قيمة افتراضية للـ branch في البيانات الموجودة
python manage.py migrate core
```

### ✅ Checklist:
- [ ] تم إضافة حقل branch
- [ ] تم إضافة حقل warehouse_type
- [ ] تم تحديث unique_together
- [ ] تم عمل migration بنجاح

---

## 📊 ملخص المرحلة 1B

عند إتمام المرحلة 1B:

✅ **تحسينات الأداء:**
- Indexes محسّنة على Item, ItemVariant, StockMovement
- استعلامات أسرع بكثير

✅ **Validations قوية:**
- منع حذف items عند وجود رصيد
- منع تعطيل warehouses عند وجود رصيد
- تحكم أفضل بالرصيد السالب

✅ **Warehouse Model أفضل:**
- ربط بالـ branch
- تصنيف أنواع المستودعات

---

# 🟢 المرحلة 1C: تحسينات اختيارية (يمكن تنفيذها لاحقاً)

## المهمة 10: Stock Card Report View

**الوقت المتوقع:** 3 ساعات

### ملخص المطلوب:
- إنشاء view لعرض بطاقة الصنف
- عرض جميع الحركات لصنف معين
- حساب الرصيد الافتتاحي والختامي
- إمكانية التصفية بالتاريخ والمستودع

**الملفات المطلوبة:**
- `apps/inventory/views/reports.py` (جديد)
- `apps/inventory/templates/inventory/stock_card.html` (جديد)
- تحديث `apps/inventory/urls.py`

*(يمكن تفصيل الخطوات عند الحاجة)*

---

## المهمة 11: Low Stock Alert System

**الوقت المتوقع:** 3 ساعات

### ملخص المطلوب:
- إنشاء model للتنبيهات (StockAlert)
- إنشاء view لعرض التنبيهات
- إرسال إشعارات للمستخدمين
- Dashboard widget للتنبيهات

*(يمكن تفصيل الخطوات عند الحاجة)*

---

## المهمة 12: Admin Actions

**الوقت المتوقع:** 1 ساعة

### ملخص المطلوب:
- Bulk update لحدود المخزون
- Export لبيانات المخزون
- Bulk transfer بين المستودعات

*(يمكن تفصيل الخطوات عند الحاجة)*

---

# ✅ معايير الإنجاز النهائية

## المرحلة 1A مكتملة عندما:
- [x] جميع الحقول الجديدة في ItemStock موجودة وتعمل
- [x] جميع Methods في ItemVariant تعمل بشكل صحيح
- [x] Signals للـ purchases تعمل تلقائياً
- [x] Signals للـ sales تعمل تلقائياً
- [x] balance_before يُحفظ في كل StockMovement
- [x] حساب متوسط التكلفة صحيح 100%
- [x] اختبار السيناريو الكامل (شراء → بيع) ناجح
- [x] لا توجد أخطاء في الـ migrations
- [x] لا توجد أخطاء في الـ logs

## المرحلة 1B مكتملة عندما:
- [x] Indexes محسّنة على جميع Models
- [x] Validations المتقدمة تعمل
- [x] Warehouse Model محسّن بـ branch و type
- [x] جميع Migrations ناجحة

## المرحلة 1C مكتملة عندما:
- [ ] Stock Card Report يعمل
- [ ] Low Stock Alerts تعمل
- [ ] Admin Actions جاهزة

---

# 🎯 الخطوة التالية

**ابدأ بالمرحلة 1A - المهمة 1**

لتنفيذ المهمة الأولى، قم بما يلي:

```
افتح الملف apps/inventory/models.py وابحث عن class ItemStock
```

ثم اتبع الخطوات المذكورة أعلاه خطوة بخطوة.

**حظاً موفقاً!** 🚀

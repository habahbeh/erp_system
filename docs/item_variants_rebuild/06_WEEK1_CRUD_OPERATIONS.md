# Week 1 Day 3-4: CRUD Operations Documentation

**التاريخ:** 2025-01-18
**المرحلة:** Week 1 Day 3-4 - CRUD Implementation
**الحالة:** 🔄 قيد التنفيذ

---

## 📋 نظرة عامة

هذا الملف يوثق جميع عمليات CRUD للنماذج الجديدة المضافة في Week 1 Day 1-2.

### النماذج المستهدفة:

1. **UnitOfMeasure** - وحدات القياس ✅
2. **UoMConversion** - تحويلات وحدات القياس ⭐ NEW
3. **PricingRule** - قواعد التسعير الديناميكية ⭐ NEW
4. **ItemTemplate** - قوالب المواد ⭐ NEW
5. **PriceHistory** - تاريخ الأسعار (Read-only Audit)
6. **VariantLifecycleEvent** - سجل دورة حياة المتغيرات (Read-only Audit)
7. **BulkImportJob** - وظائف الاستيراد الجماعي (System-managed)

---

## 🎯 الأولويات

### Priority 1 (High - Week 1 Day 3-4):
1. ✅ **UoMConversion** - ضروري لعمل نظام UoM
2. ⭐ **PricingRule** - ضروري لنظام التسعير الديناميكي
3. ⭐ **ItemTemplate** - ضروري لإنشاء المواد بسرعة

### Priority 2 (Medium - Week 2):
4. **PriceHistory Viewer** - عرض تاريخ تغييرات الأسعار
5. **VariantLifecycleEvent Viewer** - عرض سجل دورة الحياة
6. **BulkImportJob Monitor** - مراقبة عمليات الاستيراد

---

## 1. UoMConversion CRUD

### 📝 الوصف:
إدارة تحويلات وحدات القياس بين الوحدات المختلفة (مثل: 1 دزينة = 12 قطعة).

### 🎯 الاستخدام:
- تحديد معامل التحويل بين وحدتين قياس
- يمكن ربطها بمادة معينة (item-specific) أو عامة (global)
- يمكن ربطها بمتغير معين (variant-specific)

### 📊 البيانات المطلوبة:

```python
class UoMConversion(BaseModel):
    item = ForeignKey(Item, null=True, blank=True)      # اختياري - للتحويلات الخاصة بمادة
    variant = ForeignKey(ItemVariant, null=True)        # اختياري - للتحويلات الخاصة بمتغير
    from_uom = ForeignKey(UnitOfMeasure)                # الوحدة المصدر (مثل: دزينة)
    to_uom = ForeignKey(UnitOfMeasure, related='to')    # الوحدة الهدف (مثل: قطعة)
    conversion_factor = DecimalField()                   # معامل التحويل (مثل: 12)
    formula_expression = CharField(blank=True)           # صيغة اختيارية للحسابات المعقدة
```

### ✨ أمثلة واقعية:

#### مثال 1: تحويل عام (Global Conversion)
```python
# 1 دزينة = 12 قطعة (لجميع المواد)
UoMConversion.objects.create(
    company=company,
    from_uom=dozen,
    to_uom=piece,
    conversion_factor=Decimal('12'),
    item=None,  # عام لكل المواد
    variant=None
)
```

#### مثال 2: تحويل خاص بمادة (Item-specific)
```python
# كرتون مسامير = 100 قطعة (خاص بالمسامير فقط)
UoMConversion.objects.create(
    company=company,
    item=nail_item,
    from_uom=carton,
    to_uom=piece,
    conversion_factor=Decimal('100')
)
```

#### مثال 3: تحويل خاص بمتغير (Variant-specific)
```python
# كرتون مسمار 5 سم = 200 قطعة (المسمار 10 سم له كرتون مختلف)
UoMConversion.objects.create(
    company=company,
    item=nail_item,
    variant=nail_5cm_variant,
    from_uom=carton,
    to_uom=piece,
    conversion_factor=Decimal('200')
)
```

### 🔄 العمليات المطلوبة:

#### CREATE - إنشاء تحويل جديد
```python
# Form Fields
- company (auto - from request)
- item (optional select)
- variant (optional select - dependent on item)
- from_uom (required select)
- to_uom (required select)
- conversion_factor (required decimal, min=0.000001)
- formula_expression (optional text)

# Validation
1. from_uom ≠ to_uom
2. conversion_factor > 0
3. unique_together: [company, item, variant, from_uom, to_uom]
4. إذا كان variant محدد، يجب أن يكون item محدد أيضاً
```

#### READ - عرض التحويلات
```python
# List View - جدول التحويلات
Columns:
- من (From UoM)
- إلى (To UoM)
- معامل التحويل (Factor)
- المادة (Item) - "عام" إذا كان None
- المتغير (Variant) - if applicable
- الصيغة (Formula) - if exists
- إجراءات (Edit/Delete)

# Detail View - تفاصيل التحويل
- معلومات التحويل الكاملة
- أمثلة حسابية (5 دزينة = 60 قطعة)
- المواد/المتغيرات المرتبطة
```

#### UPDATE - تعديل تحويل
```python
# Editable Fields
- conversion_factor (يمكن تعديله دائماً)
- formula_expression (يمكن تعديله)
- from_uom, to_uom (حذر: قد يؤثر على حسابات موجودة)

# Warnings
- تحذير إذا تم تعديل معامل التحويل وهناك معاملات موجودة
```

#### DELETE - حذف تحويل
```python
# Soft Delete
- استخدام is_active = False
- لا يمكن الحذف إذا كان هناك معاملات تستخدم هذا التحويل

# Confirmation
- تأكيد الحذف مع عرض التأثير
```

---

## 2. PricingRule CRUD

### 📝 الوصف:
قواعد تسعير ديناميكية تطبق تلقائياً على المواد/المتغيرات بناءً على شروط معينة.

### 🎯 الاستخدام:
- تسعير تلقائي بناءً على نسبة الربح (Markup)
- خصومات الكميات (Bulk Discount)
- تسعير موسمي
- صيغ تسعير معقدة

### 📊 البيانات المطلوبة:

```python
class PricingRule(BaseModel):
    RULE_TYPE_CHOICES = [
        ('MARKUP_PERCENTAGE', 'نسبة الربح'),
        ('DISCOUNT_PERCENTAGE', 'خصم بالنسبة المئوية'),
        ('PRICE_FORMULA', 'صيغة تسعير'),
        ('BULK_DISCOUNT', 'خصم الكميات'),
        ('SEASONAL_PRICING', 'تسعير موسمي'),
    ]

    name = CharField(max_length=100)
    name_en = CharField(max_length=100, blank=True)
    rule_type = CharField(choices=RULE_TYPE_CHOICES)

    # Percentage-based
    percentage_value = DecimalField(null=True, blank=True)  # 20% markup أو 10% discount

    # Formula-based
    formula = JSONField(default=dict)  # {"base": "cost", "multiplier": 1.5, "add": 10}

    # Quantity-based
    min_quantity = DecimalField(null=True, blank=True)
    max_quantity = DecimalField(null=True, blank=True)

    # Date-based
    valid_from = DateField(null=True, blank=True)
    valid_to = DateField(null=True, blank=True)

    # Applicability
    apply_to_categories = ManyToManyField(ItemCategory, blank=True)
    apply_to_brands = ManyToManyField(Brand, blank=True)
    apply_to_items = ManyToManyField(Item, blank=True)

    # Priority
    priority = IntegerField(default=10)  # أعلى رقم = أعلى أولوية

    # Target Price List
    price_list = ForeignKey(PriceList, null=True, blank=True)
```

### ✨ أمثلة واقعية:

#### مثال 1: نسبة ربح على التكلفة
```python
# سعر البيع = التكلفة + 30% ربح
PricingRule.objects.create(
    company=company,
    name="نسبة ربح قياسية",
    rule_type='MARKUP_PERCENTAGE',
    percentage_value=Decimal('30.00'),
    price_list=wholesale_price_list,
    priority=10
)
```

#### مثال 2: خصم على الكميات الكبيرة
```python
# خصم 10% للطلبات أكثر من 100 قطعة
PricingRule.objects.create(
    company=company,
    name="خصم الجملة",
    rule_type='BULK_DISCOUNT',
    percentage_value=Decimal('10.00'),
    min_quantity=Decimal('100'),
    priority=15
)
```

#### مثال 3: تسعير موسمي
```python
# خصم 20% في شهر رمضان
PricingRule.objects.create(
    company=company,
    name="عرض رمضان",
    rule_type='SEASONAL_PRICING',
    percentage_value=Decimal('20.00'),
    valid_from=date(2025, 3, 1),
    valid_to=date(2025, 3, 31),
    priority=20  # أعلى أولوية
)
```

#### مثال 4: صيغة تسعير معقدة
```python
# السعر = (التكلفة × 1.5) + 10 دينار
PricingRule.objects.create(
    company=company,
    name="صيغة مخصصة",
    rule_type='PRICE_FORMULA',
    formula={
        "base": "cost_price",
        "multiplier": 1.5,
        "add": 10,
        "round_to": 0.5  # تقريب لأقرب 0.5
    },
    priority=10
)
```

### 🔄 العمليات المطلوبة:

#### CREATE - إنشاء قاعدة جديدة
```python
# Form Structure
Step 1: Basic Info
- name (required)
- rule_type (required radio/select)
- priority (default=10)
- is_active (default=True)

Step 2: Rule Configuration (dynamic based on rule_type)
For MARKUP_PERCENTAGE:
  - percentage_value (required)
  - price_list (optional)

For BULK_DISCOUNT:
  - percentage_value (required)
  - min_quantity (required)
  - max_quantity (optional)

For SEASONAL_PRICING:
  - percentage_value or formula
  - valid_from (required)
  - valid_to (required)

For PRICE_FORMULA:
  - formula JSON builder (interactive UI)

Step 3: Applicability
- apply_to_categories (multi-select)
- apply_to_brands (multi-select)
- apply_to_items (multi-select)

# Validation
1. إذا كان rule_type = MARKUP_PERCENTAGE أو DISCOUNT_PERCENTAGE، percentage_value مطلوب
2. إذا كان rule_type = BULK_DISCOUNT، min_quantity مطلوب
3. إذا كان rule_type = SEASONAL_PRICING، valid_from و valid_to مطلوبان
4. valid_to > valid_from
```

#### READ - عرض القواعد
```python
# List View
Columns:
- الاسم (Name)
- النوع (Type) - badge with color
- القيمة (Value/Formula summary)
- الأولوية (Priority)
- التطبيق (Applied to: X categories, Y brands, Z items)
- الحالة (Active/Inactive)
- الصلاحية (Valid from/to) - if applicable
- إجراءات (Edit/Delete/Clone/Test)

Filters:
- rule_type
- is_active
- price_list
- priority range

# Detail View
- معلومات القاعدة الكاملة
- preview: كيف ستطبق على مواد مختلفة
- تاريخ التطبيق (آخر 30 يوم)
- إحصائيات: كم مادة تأثرت بهذه القاعدة
```

#### UPDATE - تعديل قاعدة
```python
# All fields editable
# Warning: تغيير القاعدة سيؤثر على الأسعار المطبقة تلقائياً

# Special Actions:
- Test Rule: اختبار القاعدة على مادة معينة قبل التطبيق
- Clone Rule: نسخ القاعدة مع تعديلات
```

#### DELETE - حذف قاعدة
```python
# Soft Delete
- استخدام is_active = False
- لا يؤثر على الأسعار المطبقة سابقاً (history preserved)
```

---

## 3. ItemTemplate CRUD

### 📝 الوصف:
قوالب جاهزة لإنشاء مواد متكررة بسرعة مع جميع الإعدادات الافتراضية.

### 🎯 الاستخدام:
- تسريع إنشاء المواد المتشابهة
- معايرة البيانات (standardization)
- تقليل الأخطاء في الإدخال

### 📊 البيانات المطلوبة:

```python
class ItemTemplate(BaseModel):
    name = CharField(max_length=100)
    code = CharField(max_length=50, unique=True)
    category = ForeignKey(ItemCategory)

    # Template Structure
    template_data = JSONField(default=dict)  # البنية الكاملة

    # Auto-generation Settings
    auto_generate_codes = BooleanField(default=True)
    code_prefix = CharField(max_length=10, blank=True)
    code_pattern = CharField(max_length=50, default='{prefix}-{counter:05d}')

    auto_create_variants = BooleanField(default=False)
    auto_create_prices = BooleanField(default=True)

    # Usage Stats
    usage_count = IntegerField(default=0)
    last_used_at = DateTimeField(null=True, blank=True)
```

### 🏗️ هيكل template_data:

```json
{
  "base_item": {
    "category_id": 123,
    "brand_id": 45,
    "base_uom_id": 1,
    "currency_id": 1,
    "tax_rate": "16.00",
    "has_variants": true,
    "default_values": {
      "weight": null,
      "length": null,
      "manufacturer": "Default Manufacturer"
    }
  },
  "variant_attributes": [
    {
      "attribute_id": 1,
      "attribute_name": "الحجم",
      "values": ["5 سم", "10 سم", "15 سم"]
    },
    {
      "attribute_id": 2,
      "attribute_name": "اللون",
      "values": ["فضي", "ذهبي"]
    }
  ],
  "uom_conversions": [
    {
      "from_uom_id": 2,
      "to_uom_id": 1,
      "factor": "12"
    }
  ],
  "price_structure": {
    "wholesale": {
      "type": "markup",
      "value": "30"
    },
    "retail": {
      "type": "markup",
      "value": "50"
    }
  }
}
```

### ✨ أمثلة واقعية:

#### مثال 1: قالب مسامير
```python
nail_template = ItemTemplate.objects.create(
    company=company,
    name="قالب مسامير",
    code="TPL-NAILS",
    category=nails_category,
    auto_generate_codes=True,
    code_prefix="NAIL",
    auto_create_variants=True,
    template_data={
        "base_item": {
            "category_id": nails_category.id,
            "brand_id": local_brand.id,
            "base_uom_id": piece.id,
            "has_variants": True,
            "tax_rate": "16.00"
        },
        "variant_attributes": [
            {
                "attribute_id": size_attr.id,
                "attribute_name": "الحجم",
                "values": ["5 سم", "10 سم", "15 سم", "20 سم"]
            }
        ],
        "uom_conversions": [
            {"from_uom_id": dozen.id, "factor": "12"},
            {"from_uom_id": carton.id, "factor": "100"}
        ],
        "price_structure": {
            "wholesale": {"type": "markup", "value": "30"},
            "retail": {"type": "markup", "value": "50"}
        }
    }
)
```

#### مثال 2: قالب مواد غذائية
```python
food_template = ItemTemplate.objects.create(
    company=company,
    name="قالب مواد غذائية",
    code="TPL-FOOD",
    category=food_category,
    auto_generate_codes=True,
    code_prefix="FOOD",
    template_data={
        "base_item": {
            "category_id": food_category.id,
            "base_uom_id": kg.id,
            "has_variants": False,
            "tax_rate": "5.00"  # ضريبة مخفضة للمواد الغذائية
        },
        "uom_conversions": [
            {"from_uom_id": gram.id, "factor": "0.001"},
            {"from_uom_id": ton.id, "factor": "1000"}
        ]
    }
)
```

### 🔄 العمليات المطلوبة:

#### CREATE - إنشاء قالب جديد
```python
# Form Structure (Wizard - 5 Steps)

Step 1: Basic Info
- name (required)
- code (required, unique)
- category (required select)
- description (optional)

Step 2: Default Item Settings
- brand (optional)
- base_uom (required)
- currency (required)
- tax_rate (required)
- has_variants (checkbox)

Step 3: Variant Configuration (if has_variants = True)
- Select variant attributes (multi-select)
- For each attribute: define common values
- Example: Size: [5cm, 10cm, 15cm]

Step 4: UoM Conversions
- Add conversion rules
- For each: from_uom, factor
- Example: 1 Dozen = 12 Pieces

Step 5: Price Structure
- For each price list:
  - pricing method (markup/formula/fixed)
  - value

# Validation
1. code must be unique
2. template_data must be valid JSON
3. all referenced IDs (category, brand, uom) must exist
```

#### READ - عرض القوالب
```python
# List View
Columns:
- الكود (Code)
- الاسم (Name)
- التصنيف (Category)
- عدد الاستخدامات (Usage Count)
- آخر استخدام (Last Used)
- الحالة (Active/Inactive)
- إجراءات (Use/Edit/Clone/Delete)

# Detail View
- معلومات القالب الكاملة
- معاينة البيانات (template_data prettified)
- المواد المنشأة من هذا القالب (last 10)
- Usage History Chart

# Template Preview
- كيف سيبدو المادة المنشأ من القالب
- عدد المتغيرات المتوقعة (إذا has_variants = true)
```

#### USE - استخدام قالب لإنشاء مادة
```python
# Create Item from Template Flow

1. User clicks "استخدام القالب"
2. Redirect to item creation form with pre-filled data
3. User can override any field
4. On save:
   - Create Item with template defaults
   - Auto-generate code if enabled
   - Create variants if configured
   - Create UoM conversions
   - Create prices based on price structure
   - Increment template.usage_count
   - Update template.last_used_at

# Backend Method
def create_item_from_template(template, custom_data=None):
    """
    Creates an item from a template.

    Args:
        template: ItemTemplate instance
        custom_data: dict of custom values to override template

    Returns:
        Item instance
    """
    template_data = template.template_data

    # Merge custom data with template
    item_data = {**template_data['base_item'], **(custom_data or {})}

    # Generate code
    if template.auto_generate_codes:
        item_data['item_code'] = generate_code(template)

    # Create item
    item = Item.objects.create(**item_data)

    # Create variants if configured
    if template.auto_create_variants and item.has_variants:
        create_variants_from_template(item, template_data['variant_attributes'])

    # Create UoM conversions
    if 'uom_conversions' in template_data:
        create_conversions_from_template(item, template_data['uom_conversions'])

    # Create prices
    if template.auto_create_prices and 'price_structure' in template_data:
        create_prices_from_template(item, template_data['price_structure'])

    # Update usage stats
    template.usage_count += 1
    template.last_used_at = timezone.now()
    template.save()

    return item
```

#### UPDATE - تعديل قالب
```python
# All fields editable
# Warning: التعديل لن يؤثر على المواد المنشأة سابقاً من هذا القالب

# Versioning (Future Enhancement)
- Save template versions
- Allow rollback to previous version
```

#### CLONE - نسخ قالب
```python
# Clone Template
def clone_template(template, new_name, new_code):
    """
    Creates a copy of a template.
    """
    return ItemTemplate.objects.create(
        company=template.company,
        name=new_name,
        code=new_code,
        category=template.category,
        template_data=template.template_data.copy(),
        auto_generate_codes=template.auto_generate_codes,
        code_prefix=template.code_prefix,
        # Reset usage stats
        usage_count=0,
        last_used_at=None
    )
```

#### DELETE - حذف قالب
```python
# Soft Delete
- استخدام is_active = False
- لا يؤثر على المواد المنشأة من القالب

# Hard Delete
- يمكن حذف نهائي إذا usage_count = 0
```

---

## 4. PriceHistory (Read-Only Audit Log)

### 📝 الوصف:
سجل تلقائي لجميع تغييرات الأسعار. يتم إنشاؤه تلقائياً عند تعديل `PriceListItem`.

### 🎯 الاستخدام:
- تتبع تاريخ الأسعار
- تدقيق التغييرات
- تحليل اتجاهات الأسعار

### 📊 البيانات:

```python
class PriceHistory(models.Model):
    price_list_item = ForeignKey(PriceListItem, related_name='history')
    old_price = DecimalField(max_digits=15, decimal_places=3)
    new_price = DecimalField(max_digits=15, decimal_places=3)
    change_percentage = DecimalField(max_digits=10, decimal_places=2)
    change_reason = CharField(max_length=200, blank=True)
    changed_by = ForeignKey(User)
    changed_at = DateTimeField(auto_now_add=True)
```

### 🔄 العمليات المطلوبة:

#### READ - عرض التاريخ
```python
# List View (for a specific PriceListItem)
Columns:
- التاريخ (Changed At)
- السعر القديم (Old Price)
- السعر الجديد (New Price)
- التغيير % (Change %)
- السبب (Reason)
- المستخدم (Changed By)

# Chart View
- Line chart showing price over time
- Highlight major changes (>10%)

# No Create/Update/Delete
- Read-only view
- Created automatically by signal
```

---

## 5. VariantLifecycleEvent (Read-Only Audit Log)

### 📝 الوصف:
سجل تلقائي لجميع الأحداث المهمة في دورة حياة المتغير.

### 🎯 الاستخدام:
- تتبع دورة حياة المتغير الكاملة
- معرفة متى تم إيقاف متغير أو إعادة تفعيله
- تدقيق التغييرات

### 📊 البيانات:

```python
class VariantLifecycleEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('CREATED', 'إنشاء'),
        ('DISCONTINUED', 'إيقاف الإنتاج'),
        ('REACTIVATED', 'إعادة تفعيل'),
        ('PRICE_CHANGED', 'تغيير سعر'),
        ('COST_CHANGED', 'تغيير تكلفة'),
        ('UOM_ADDED', 'إضافة وحدة قياس'),
        ('UOM_REMOVED', 'حذف وحدة قياس'),
        ('ATTRIBUTE_CHANGED', 'تغيير خاصية'),
        ('IMAGE_CHANGED', 'تغيير صورة'),
    ]

    variant = ForeignKey(ItemVariant, related_name='lifecycle_events')
    event_type = CharField(choices=EVENT_TYPE_CHOICES)
    description = TextField(blank=True)
    old_values = JSONField(default=dict)
    new_values = JSONField(default=dict)
    changed_by = ForeignKey(User)
    timestamp = DateTimeField(auto_now_add=True)
```

### 🔄 العمليات المطلوبة:

#### READ - عرض السجل
```python
# Timeline View (for a specific ItemVariant)
- Vertical timeline showing all events
- Each event with:
  - Icon (based on event_type)
  - Timestamp
  - Description
  - Changed by user
  - Diff (old vs new values) - expandable

# Filter by event_type
# Search by description

# No Create/Update/Delete
- Read-only view
- Created automatically by signals
```

---

## 6. BulkImportJob (System-Managed)

### 📝 الوصف:
تتبع وظائف الاستيراد الجماعي (Excel Import). يتم إدارتها بواسطة النظام.

### 🎯 الاستخدام:
- مراقبة حالة عمليات الاستيراد
- عرض الأخطاء والتحذيرات
- إعادة محاولة الصفوف الفاشلة

### 📊 البيانات:

```python
class BulkImportJob(BaseModel):
    JOB_STATUS_CHOICES = [
        ('PENDING', 'قيد الانتظار'),
        ('PROCESSING', 'جاري المعالجة'),
        ('COMPLETED', 'مكتمل'),
        ('COMPLETED_WITH_ERRORS', 'مكتمل مع أخطاء'),
        ('FAILED', 'فشل'),
    ]

    job_id = CharField(max_length=50, unique=True)
    file_path = FileField(upload_to='imports/%Y/%m/')
    file_name = CharField(max_length=255)
    import_type = CharField(max_length=50)  # 'items', 'variants', 'prices'

    status = CharField(choices=JOB_STATUS_CHOICES, default='PENDING')
    total_rows = IntegerField(default=0)
    successful_rows = IntegerField(default=0)
    failed_rows = IntegerField(default=0)

    errors = JSONField(default=list)  # [{"row": 5, "error": "...", "field": "code"}]
    warnings = JSONField(default=list)

    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
```

### 🔄 العمليات المطلوبة:

#### READ - مراقبة الوظائف
```python
# List View
Columns:
- Job ID
- File Name
- Import Type
- Status (badge with color)
- Progress (successful/total)
- Started At
- Duration
- إجراءات (View Details/Download Errors/Retry)

Filters:
- status
- import_type
- date range

# Detail View
- Job information
- Progress bar
- Success/Failed statistics
- Errors table (expandable)
- Warnings table
- Download buttons:
  - تحميل الملف الأصلي
  - تحميل تقرير الأخطاء (Excel)
  - تحميل الصفوف الفاشلة فقط (Excel)

# No Manual Create/Update/Delete
- Jobs created automatically by import process
- Only system can update status
```

---

## 📋 ملخص الأولويات

### Week 1 Day 3-4 (الآن):
1. ✅ **UoMConversion CRUD** - ضروري
2. ⭐ **PricingRule CRUD** - ضروري
3. ⭐ **ItemTemplate CRUD** - ضروري

### Week 2:
4. **PriceHistory Viewer** - مفيد
5. **VariantLifecycleEvent Viewer** - مفيد
6. **BulkImportJob Monitor** - ضروري للاستيراد

### Week 5 (Import/Export):
7. **BulkImportJob Implementation** - كامل

---

## 🎯 الخطوة التالية

بعد توثيق CRUD Operations، سننتقل إلى:
1. إنشاء Forms للنماذج الثلاثة الأساسية
2. إنشاء Views (List, Detail, Create, Update, Delete)
3. إنشاء Templates (UI)
4. إضافة URLs
5. اختبار الوظائف

---

**آخر تحديث:** 2025-01-18
**الحالة:** ✅ Documentation Complete
**التالي:** Implementation of UoMConversion CRUD

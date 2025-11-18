# 📊 Week 1 - Database Schema Design

## 🎯 الهدف
تصميم وتطبيق قاعدة البيانات الكاملة للنظام الجديد

---

## 📋 الجداول الجديدة

### 1. `units_of_measure` (وحدات القياس)

```sql
CREATE TABLE units_of_measure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- معلومات أساسية
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    code VARCHAR(20) UNIQUE NOT NULL,
    symbol VARCHAR(10),

    -- التصنيف
    uom_type ENUM('UNIT', 'WEIGHT', 'LENGTH', 'VOLUME', 'AREA', 'TIME') DEFAULT 'UNIT',
    category VARCHAR(50),  -- للتجميع (وحدات طول، وزن، ...)

    -- الدقة
    rounding_precision DECIMAL(10, 6) DEFAULT 0.01,

    -- الحالة
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_company_active (company_id, is_active),
    INDEX idx_uom_type (uom_type)
);
```

**البيانات الأولية:**
```sql
INSERT INTO units_of_measure (company_id, name, code, symbol, uom_type) VALUES
(1, 'قطعة', 'PC', 'قطعة', 'UNIT'),
(1, 'دزينة', 'DOZ', 'دزينة', 'UNIT'),
(1, 'كرتون', 'CTN', 'كرتون', 'UNIT'),
(1, 'كيلوجرام', 'KG', 'كجم', 'WEIGHT'),
(1, 'جرام', 'G', 'جم', 'WEIGHT'),
(1, 'متر', 'M', 'م', 'LENGTH'),
(1, 'سنتيمتر', 'CM', 'سم', 'LENGTH'),
(1, 'لتر', 'L', 'لتر', 'VOLUME');
```

---

### 2. `uom_conversions` (تحويلات وحدات القياس)

```sql
CREATE TABLE uom_conversions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- ربط بالمادة أو المتغير
    item_id INT,  -- للمادة الأساسية (nullable)
    variant_id INT,  -- أو لمتغير محدد (nullable)

    -- التحويل
    from_uom_id INT NOT NULL,
    to_uom_id INT NOT NULL,  -- usually base_uom
    conversion_factor DECIMAL(20, 6) NOT NULL,  -- 12 for dozen to piece

    -- الاستخدام
    is_default_purchase_uom BOOLEAN DEFAULT FALSE,
    is_default_sale_uom BOOLEAN DEFAULT FALSE,

    -- الحالة
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES item_variants(id) ON DELETE CASCADE,
    FOREIGN KEY (from_uom_id) REFERENCES units_of_measure(id),
    FOREIGN KEY (to_uom_id) REFERENCES units_of_measure(id),
    FOREIGN KEY (created_by) REFERENCES users(id),

    -- Constraints
    UNIQUE KEY unique_conversion (item_id, variant_id, from_uom_id, to_uom_id),
    CHECK (item_id IS NOT NULL OR variant_id IS NOT NULL),
    CHECK (from_uom_id != to_uom_id),

    INDEX idx_item_uom (item_id, from_uom_id),
    INDEX idx_variant_uom (variant_id, from_uom_id)
);
```

**مثال:**
```sql
-- مسمار 5 سم
-- 1 دزينة = 12 قطعة
INSERT INTO uom_conversions (company_id, variant_id, from_uom_id, to_uom_id, conversion_factor)
VALUES (1, 101, 2, 1, 12);

-- 1 كرتون = 100 قطعة
INSERT INTO uom_conversions (company_id, variant_id, from_uom_id, to_uom_id, conversion_factor)
VALUES (1, 101, 3, 1, 100);
```

---

### 3. `pricing_rules` (قواعد التسعير)

```sql
CREATE TABLE pricing_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- معلومات أساسية
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- نوع القاعدة
    rule_type ENUM(
        'DISCOUNT_PERCENTAGE',
        'DISCOUNT_FIXED',
        'PRICE_FORMULA',
        'BULK_DISCOUNT'
    ) NOT NULL,

    -- التطبيق على
    applies_to ENUM('ALL', 'CATEGORY', 'ITEM', 'VARIANT') NOT NULL,
    category_id INT,
    item_id INT,
    variant_id INT,

    -- قائمة الأسعار
    price_list_id INT,

    -- شروط الكمية
    min_quantity DECIMAL(20, 3),
    max_quantity DECIMAL(20, 3),

    -- الخصم
    discount_percentage DECIMAL(5, 2),
    fixed_discount_amount DECIMAL(20, 3),

    -- الصيغة (JSON)
    formula JSON,  -- {base: "cost", multiplier: 1.5, min_profit: 0.2}

    -- الأولوية (الأعلى يطبق أولاً)
    priority INT DEFAULT 0,

    -- الصلاحية
    valid_from DATE,
    valid_to DATE,

    -- الحالة
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (category_id) REFERENCES item_categories(id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES item_variants(id) ON DELETE CASCADE,
    FOREIGN KEY (price_list_id) REFERENCES price_lists(id),
    FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_active_rules (company_id, is_active, priority),
    INDEX idx_date_range (valid_from, valid_to)
);
```

**أمثلة:**
```sql
-- قاعدة 1: خصم 10% للكميات > 100
INSERT INTO pricing_rules (company_id, name, rule_type, applies_to, min_quantity, discount_percentage, priority)
VALUES (1, 'خصم الكميات الكبيرة', 'BULK_DISCOUNT', 'ALL', 100, 10, 10);

-- قاعدة 2: هامش ربح 50% على التكلفة
INSERT INTO pricing_rules (company_id, name, rule_type, applies_to, formula, priority)
VALUES (1, 'هامش ربح قياسي', 'PRICE_FORMULA', 'ALL',
        '{"base": "cost", "multiplier": 1.5}', 5);
```

---

### 4. `price_history` (تاريخ تغيرات الأسعار)

```sql
CREATE TABLE price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- ربط بالسعر
    price_list_item_id INT NOT NULL,

    -- التغيير
    old_price DECIMAL(20, 3),
    new_price DECIMAL(20, 3),
    change_percentage DECIMAL(10, 2),

    -- السبب
    reason VARCHAR(255),
    notes TEXT,

    -- من قام بالتعديل
    changed_by INT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- معلومات إضافية
    old_data JSON,  -- snapshot كامل
    new_data JSON,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (price_list_item_id) REFERENCES price_list_items(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id),

    INDEX idx_price_item (price_list_item_id, changed_at),
    INDEX idx_changed_by (changed_by, changed_at)
);
```

---

### 5. `variant_lifecycle_events` (سجل أحداث المتغيرات)

```sql
CREATE TABLE variant_lifecycle_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- المتغير
    variant_id INT NOT NULL,

    -- نوع الحدث
    event_type ENUM(
        'CREATED',
        'ACTIVATED',
        'DEACTIVATED',
        'DISCONTINUED',
        'PRICE_CHANGED',
        'STOCK_ADJUSTED',
        'ATTRIBUTE_CHANGED'
    ) NOT NULL,

    -- التفاصيل
    old_value JSON,
    new_value JSON,
    change_summary TEXT,

    -- من قام بالحدث
    user_id INT,
    ip_address VARCHAR(45),

    -- التوقيت
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (variant_id) REFERENCES item_variants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),

    INDEX idx_variant_events (variant_id, created_at),
    INDEX idx_event_type (event_type, created_at)
);
```

---

### 6. `item_templates` (قوالب المواد)

```sql
CREATE TABLE item_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- معلومات القالب
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INT,

    -- البيانات (JSON كامل)
    template_data JSON NOT NULL,
    /*
    {
        "item": {...},
        "variants": [...],
        "uom_conversions": [...],
        "prices": [...]
    }
    */

    -- الاستخدام
    usage_count INT DEFAULT 0,
    last_used_at DATETIME,

    -- الحالة
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,  -- shared with all users

    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NOT NULL,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (category_id) REFERENCES item_categories(id),
    FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_company_active (company_id, is_active),
    INDEX idx_created_by (created_by)
);
```

---

### 7. `bulk_import_jobs` (سجل عمليات الاستيراد)

```sql
CREATE TABLE bulk_import_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,

    -- معلومات الملف
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size_kb INT,

    -- نوع الاستيراد
    import_type ENUM(
        'SIMPLE_ITEMS',
        'ITEMS_WITH_VARIANTS',
        'VARIANTS_ONLY',
        'PRICES_ONLY',
        'UOM_CONVERSIONS'
    ) NOT NULL,

    -- الحالة
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIALLY_COMPLETED') DEFAULT 'PENDING',

    -- الإحصائيات
    total_rows INT DEFAULT 0,
    processed_rows INT DEFAULT 0,
    success_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    warning_count INT DEFAULT 0,

    -- السجل
    error_log JSON,  -- [{row: 5, error: "..."}]
    warning_log JSON,
    processing_log JSON,

    -- التوقيت
    started_at DATETIME,
    completed_at DATETIME,
    processing_time_seconds INT,

    -- من قام بالاستيراد
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_status (status, created_at),
    INDEX idx_created_by (created_by, created_at)
);
```

---

## 🔄 تعديلات على الجداول الموجودة

### `items` - إضافة حقول جديدة

```sql
ALTER TABLE items
    -- وحدة القياس الأساسية
    ADD COLUMN base_uom_id INT AFTER unit_of_measure,
    ADD FOREIGN KEY (base_uom_id) REFERENCES units_of_measure(id),

    -- خصائص إضافية
    ADD COLUMN is_stockable BOOLEAN DEFAULT TRUE AFTER has_variants,
    ADD COLUMN track_serial_numbers BOOLEAN DEFAULT FALSE AFTER is_stockable,
    ADD COLUMN track_batches BOOLEAN DEFAULT FALSE AFTER track_serial_numbers,

    -- التسعير
    ADD COLUMN default_purchase_price DECIMAL(20, 3) AFTER tax_rate,
    ADD COLUMN last_purchase_price DECIMAL(20, 3) AFTER default_purchase_price,

    -- الحالة المحسنة
    ADD COLUMN is_discontinued BOOLEAN DEFAULT FALSE AFTER is_active,
    ADD COLUMN discontinued_date DATE AFTER is_discontinued,

    -- الفهرسة
    ADD INDEX idx_stockable (is_stockable, is_active),
    ADD INDEX idx_discontinued (is_discontinued);
```

---

### `item_variants` - تحسينات

```sql
ALTER TABLE item_variants
    -- معلومات مالية
    ADD COLUMN cost_price DECIMAL(20, 3) AFTER barcode,
    ADD COLUMN default_sale_price DECIMAL(20, 3) AFTER cost_price,
    ADD COLUMN last_purchase_price DECIMAL(20, 3) AFTER default_sale_price,
    ADD COLUMN average_cost DECIMAL(20, 3) AFTER last_purchase_price,

    -- الأبعاد المحسنة
    ADD COLUMN volume DECIMAL(20, 6) AFTER weight,
    ADD COLUMN volume_uom_id INT AFTER volume,

    -- الحالة المحسنة
    ADD COLUMN is_discontinued BOOLEAN DEFAULT FALSE AFTER is_active,
    ADD COLUMN discontinued_date DATE AFTER is_discontinued,
    ADD COLUMN replacement_variant_id INT AFTER discontinued_date,

    -- صورة مخصصة
    ADD COLUMN image_url VARCHAR(500) AFTER image,

    -- الفهرسة
    ADD INDEX idx_active_discontinued (is_active, is_discontinued),
    ADD INDEX idx_sku (code),

    -- Foreign Keys
    ADD FOREIGN KEY (volume_uom_id) REFERENCES units_of_measure(id),
    ADD FOREIGN KEY (replacement_variant_id) REFERENCES item_variants(id);
```

---

### `price_list_items` - أهم تعديل!

```sql
ALTER TABLE price_list_items
    -- ⭐ إضافة وحدة القياس
    ADD COLUMN uom_id INT AFTER variant_id,
    ADD FOREIGN KEY (uom_id) REFERENCES units_of_measure(id),

    -- شروط الكمية
    ADD COLUMN min_quantity DECIMAL(20, 3) DEFAULT 1 AFTER price,
    ADD COLUMN max_quantity DECIMAL(20, 3) AFTER min_quantity,

    -- الصلاحية
    ADD COLUMN valid_from DATE AFTER price,
    ADD COLUMN valid_to DATE AFTER valid_from,

    -- Unique constraint جديد
    DROP INDEX IF EXISTS unique_price_item,
    ADD UNIQUE KEY unique_price_item (price_list_id, item_id, variant_id, uom_id, min_quantity),

    -- فهرسة محسنة
    ADD INDEX idx_uom_price (uom_id, price_list_id),
    ADD INDEX idx_date_range (valid_from, valid_to);
```

---

## 📝 Migration Script

ملف: `apps/core/migrations/XXXX_rebuild_items_system.py`

```python
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', 'XXXX_previous_migration'),
    ]

    operations = [
        # 1. Create units_of_measure
        migrations.CreateModel(
            name='UnitOfMeasure',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('company', models.ForeignKey(...)),
                ('name', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=20, unique=True)),
                # ... باقي الحقول
            ],
        ),

        # 2. Create uom_conversions
        migrations.CreateModel(
            name='UoMConversion',
            fields=[
                # ...
            ],
        ),

        # 3. Create pricing_rules
        migrations.CreateModel(
            name='PricingRule',
            fields=[
                # ...
            ],
        ),

        # 4. Create price_history
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                # ...
            ],
        ),

        # 5. Create variant_lifecycle_events
        migrations.CreateModel(
            name='VariantLifecycleEvent',
            fields=[
                # ...
            ],
        ),

        # 6. Create item_templates
        migrations.CreateModel(
            name='ItemTemplate',
            fields=[
                # ...
            ],
        ),

        # 7. Create bulk_import_jobs
        migrations.CreateModel(
            name='BulkImportJob',
            fields=[
                # ...
            ],
        ),

        # 8. Alter existing tables
        migrations.AddField(
            model_name='item',
            name='base_uom',
            field=models.ForeignKey(...),
        ),
        # ... باقي التعديلات
    ]
```

---

## ✅ Checklist

### قبل التطبيق
- [ ] Backup كامل لقاعدة البيانات
- [ ] مراجعة الـ Schema
- [ ] التأكد من التوافق مع MySQL version

### التطبيق
- [ ] تشغيل makemigrations
- [ ] مراجعة Migration files
- [ ] تشغيل migrate
- [ ] إدخال البيانات الأولية (UoM)

### بعد التطبيق
- [ ] التحقق من الجداول الجديدة
- [ ] اختبار Foreign Keys
- [ ] اختبار Indexes
- [ ] قياس الأداء

---

## 🎯 النتيجة المتوقعة

بعد تطبيق هذا الـ Schema:
- ✅ 7 جداول جديدة
- ✅ تحسينات على 3 جداول موجودة
- ✅ بنية تدعم 10,000+ مادة
- ✅ مرونة كاملة في التسعير
- ✅ Full audit trail

---

**التالي:** `02_WEEK1_MODELS.md` - بناء Django Models

**الحالة:** ✅ جاهز للتطبيق
**آخر تحديث:** 2025-01-18

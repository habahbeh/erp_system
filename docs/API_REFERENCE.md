# API Reference - مرجع واجهة برمجة التطبيقات

**Version**: 2.4.0
**Date**: 2025-11-19
**Status**: Production Ready

---

## Table of Contents - جدول المحتويات

1. [Overview - نظرة عامة](#overview)
2. [Authentication - المصادقة](#authentication)
3. [AJAX Endpoints - نقاط نهاية AJAX](#ajax-endpoints)
4. [Pricing Engine API - واجهة محرك التسعير](#pricing-engine-api)
5. [UoM Conversion API - واجهة تحويل الوحدات](#uom-conversion-api)
6. [Cache Manager API - واجهة مدير الذاكرة المؤقتة](#cache-manager-api)
7. [Validators API - واجهة المدققات](#validators-api)
8. [Error Handling - معالجة الأخطاء](#error-handling)
9. [Code Examples - أمثلة برمجية](#code-examples)

---

## Overview - نظرة عامة

This document provides comprehensive API documentation for the ERP system's pricing and UoM modules.

توفر هذه الوثيقة توثيقاً شاملاً لواجهة برمجة التطبيقات لنظام ERP، وتحديداً لوحدات التسعير ووحدات القياس.

### Base URL

```
Production: https://yourdomain.com
Development: http://localhost:8000
```

### API Versioning

Currently, all endpoints are under the base path without versioning. Future versions will include `/api/v1/` prefix.

حالياً، جميع نقاط النهاية تحت المسار الأساسي بدون إصدار. الإصدارات المستقبلية ستتضمن البادئة `/api/v1/`.

---

## Authentication - المصادقة

### Session-Based Authentication

All API endpoints require Django session authentication with CSRF protection.

جميع نقاط نهاية API تتطلب مصادقة جلسة Django مع حماية CSRF.

#### CSRF Token

Include CSRF token in all POST requests:

قم بتضمين رمز CSRF في جميع طلبات POST:

```javascript
// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Include in request headers
fetch(url, {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
});
```

### Permissions

Most endpoints require specific permissions. Check permission requirements for each endpoint.

معظم نقاط النهاية تتطلب صلاحيات محددة. تحقق من متطلبات الصلاحيات لكل نقطة نهاية.

---

## AJAX Endpoints - نقاط نهاية AJAX

### 1. Update Single Price

**Endpoint**: `/ajax/update-price/`
**Method**: POST
**Permission**: `can_update_prices`

#### Request

```json
{
    "price_item_id": 123,
    "new_price": "150.50"
}
```

#### Response

**Success (200)**:
```json
{
    "success": true,
    "message": "تم تحديث السعر بنجاح",
    "data": {
        "price_item_id": 123,
        "new_price": "150.50",
        "formatted_price": "150.50 ر.س",
        "updated_at": "2025-11-19T10:30:00Z"
    }
}
```

**Error (400)**:
```json
{
    "success": false,
    "message": "خطأ في التحقق من البيانات",
    "errors": {
        "new_price": ["السعر يجب أن يكون أكبر من صفر"]
    }
}
```

#### Example Usage

```javascript
const result = await PriceOperations.updatePrice(123, 150.50);

if (result) {
    console.log('Price updated:', result.formatted_price);
}
```

---

### 2. Bulk Update Prices

**Endpoint**: `/ajax/bulk-update-prices/`
**Method**: POST
**Permission**: `can_update_prices`

#### Request

```json
{
    "updates": [
        {"price_item_id": 123, "new_price": "150.50"},
        {"price_item_id": 124, "new_price": "200.00"},
        {"price_item_id": 125, "new_price": "175.25"}
    ]
}
```

#### Response

**Success (200)**:
```json
{
    "success": true,
    "message": "تم تحديث 3 أسعار",
    "data": {
        "updated_count": 3,
        "failed_count": 0,
        "errors": []
    }
}
```

**Partial Success (200)**:
```json
{
    "success": true,
    "message": "تم تحديث 2 من 3 أسعار",
    "data": {
        "updated_count": 2,
        "failed_count": 1,
        "errors": [
            {
                "price_item_id": 125,
                "error": "السعر لا يمكن أن يكون أقل من التكلفة"
            }
        ]
    }
}
```

---

### 3. Calculate Price

**Endpoint**: `/ajax/calculate-price/`
**Method**: POST
**Permission**: `can_view_prices`

#### Request

```json
{
    "item_id": 10,
    "quantity": "5",
    "price_list_id": 1,
    "uom_id": 2,
    "apply_rules": true
}
```

#### Response

```json
{
    "success": true,
    "message": "تم حساب السعر",
    "data": {
        "base_price": "100.00",
        "final_price": "85.00",
        "discount_amount": "15.00",
        "total_amount": "425.00",
        "applied_rules": [
            {
                "rule_code": "DISC15",
                "rule_name": "خصم 15%",
                "discount": "15.00"
            }
        ],
        "calculation_log": [
            "Base price: 100.00",
            "Applied rule 'DISC15': -15.00 (15%)",
            "Final price: 85.00"
        ]
    }
}
```

---

### 4. Toggle Pricing Rule

**Endpoint**: `/ajax/toggle-rule/`
**Method**: POST
**Permission**: `can_manage_pricing_rules`

#### Request

```json
{
    "rule_id": 5
}
```

#### Response

```json
{
    "success": true,
    "message": "تم تحديث حالة القاعدة",
    "data": {
        "rule_id": 5,
        "is_active": false
    }
}
```

---

### 5. Get Item Prices

**Endpoint**: `/ajax/get-item-prices/`
**Method**: GET
**Permission**: `can_view_prices`

#### Request

```
GET /ajax/get-item-prices/?item_id=10
```

#### Response

```json
{
    "success": true,
    "message": "تم جلب الأسعار",
    "data": {
        "item_id": 10,
        "item_code": "ITEM001",
        "item_name": "لابتوب",
        "price_lists": [
            {
                "price_list_id": 1,
                "price_list_name": "قائمة التجزئة",
                "variants": [
                    {
                        "variant_id": 15,
                        "variant_sku": "LAP-BLK",
                        "prices": [
                            {
                                "uom": "قطعة",
                                "price": "1200.00"
                            },
                            {
                                "uom": "كرتون",
                                "price": "11400.00"
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
```

---

## Pricing Engine API - واجهة محرك التسعير

### PricingEngine Class

Main class for price calculations.

الفئة الرئيسية لحسابات الأسعار.

#### `calculate_price()`

Calculate final price with all rules applied.

حساب السعر النهائي مع تطبيق جميع القواعد.

```python
from apps.core.utils.pricing_engine import PricingEngine
from decimal import Decimal

engine = PricingEngine()

result = engine.calculate_price(
    item=item_obj,
    variant=variant_obj,
    quantity=Decimal('10'),
    price_list=pricelist_obj,
    uom=uom_obj,
    apply_rules=True,
    check_date=date.today()
)

# Returns:
{
    'base_price': Decimal('100.00'),
    'final_price': Decimal('85.00'),
    'discount_amount': Decimal('15.00'),
    'total_amount': Decimal('850.00'),
    'applied_rules': [
        {
            'rule_id': 5,
            'rule_code': 'DISC15',
            'rule_name': 'خصم 15%',
            'rule_type': 'percentage_discount',
            'value': Decimal('15.00'),
            'discount': Decimal('15.00')
        }
    ],
    'calculation_log': [
        'Base price from price list: 100.00',
        'Applied percentage_discount rule DISC15: -15.00',
        'Final price: 85.00',
        'Total for quantity 10: 850.00'
    ]
}
```

#### Parameters

- **item** (Item): Item object
- **variant** (ItemVariant, optional): Variant object (required if item has variants)
- **quantity** (Decimal): Quantity to calculate for
- **price_list** (PriceList): Price list to use
- **uom** (UnitOfMeasure): Unit of measure
- **apply_rules** (bool, default=True): Whether to apply pricing rules
- **check_date** (date, optional): Date to check rule validity (defaults to today)

#### Return Value

Dictionary containing:
- `base_price`: Original price before rules
- `final_price`: Price after all rules
- `discount_amount`: Total discount applied
- `total_amount`: final_price × quantity
- `applied_rules`: List of rules that were applied
- `calculation_log`: Step-by-step calculation log

---

## UoM Conversion API - واجهة تحويل الوحدات

### UoMConversion Model Methods

#### `convert(quantity)`

Convert quantity using the conversion factor.

تحويل الكمية باستخدام معامل التحويل.

```python
from apps.core.models import UoMConversion
from decimal import Decimal

# Get conversion: pieces to dozen
conversion = UoMConversion.objects.get(
    item=item_obj,
    from_uom=piece_uom,
    to_uom=dozen_uom
)

# Convert 24 pieces to dozens
result = conversion.convert(Decimal('24'))
# Returns: Decimal('2.00')  (24 / 12 = 2)
```

#### `reverse_convert(quantity)`

Convert quantity in reverse direction.

تحويل الكمية في الاتجاه المعاكس.

```python
# Convert 2 dozens to pieces
result = conversion.reverse_convert(Decimal('2'))
# Returns: Decimal('24.00')  (2 * 12 = 24)
```

---

## Cache Manager API - واجهة مدير الذاكرة المؤقتة

### PricingCacheManager

Manage caching for pricing calculations.

إدارة التخزين المؤقت لحسابات الأسعار.

#### `get_cached_price()`

Get cached price calculation.

الحصول على حساب السعر من الذاكرة المؤقتة.

```python
from apps.core.utils.cache_manager import PricingCacheManager
from decimal import Decimal

# Check cache
cached = PricingCacheManager.get_cached_price(
    item_id=123,
    variant_id=456,
    quantity=Decimal('10'),
    price_list_id=1,
    uom_id=2,
    apply_rules=True
)

if cached:
    print(f"Cached price: {cached['final_price']}")
else:
    # Calculate and cache
    result = engine.calculate_price(...)
    PricingCacheManager.cache_price(
        item_id=123,
        variant_id=456,
        quantity=Decimal('10'),
        price_list_id=1,
        uom_id=2,
        pricing_result=result
    )
```

#### `invalidate_item_prices(item_id)`

Invalidate all cached prices for an item.

إبطال جميع الأسعار المخزنة مؤقتاً لمادة.

```python
# When price changes, invalidate cache
PricingCacheManager.invalidate_item_prices(item_id=123)
```

### UoMCacheManager

Manage caching for UoM conversions.

إدارة التخزين المؤقت لتحويلات الوحدات.

```python
from apps.core.utils.cache_manager import UoMCacheManager

# Get cached conversion
factor = UoMCacheManager.get_cached_conversion(
    item_id=123,
    from_uom_id=1,
    to_uom_id=2
)

if not factor:
    # Calculate and cache
    UoMCacheManager.cache_conversion(
        item_id=123,
        from_uom_id=1,
        to_uom_id=2,
        conversion_factor=Decimal('12.00')
    )
```

---

## Validators API - واجهة المدققات

### PricingValidator

Validate pricing data.

التحقق من صحة بيانات التسعير.

```python
from apps.core.validators import PricingValidator
from decimal import Decimal
from django.core.exceptions import ValidationError

try:
    # Validate price
    price = PricingValidator.validate_price('150.50')

    # Validate cost
    cost = PricingValidator.validate_cost('100.00')

    # Validate price vs cost
    PricingValidator.validate_price_vs_cost(price, cost)

    print("All validations passed")

except ValidationError as e:
    print(f"Validation error: {e}")
```

### UoMValidator

Validate UoM data.

التحقق من صحة بيانات الوحدات.

```python
from apps.core.validators import UoMValidator

try:
    # Validate conversion factor
    factor = UoMValidator.validate_conversion_factor('12.00')

    # Validate UoM compatibility
    UoMValidator.validate_uom_compatibility(from_uom, to_uom)

except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## Error Handling - معالجة الأخطاء

### Standard Error Response Format

```json
{
    "success": false,
    "message": "رسالة الخطأ العامة",
    "errors": {
        "field_name": ["خطأ محدد للحقل"]
    }
}
```

### HTTP Status Codes

- **200** OK - نجح الطلب
- **400** Bad Request - خطأ في البيانات المرسلة
- **401** Unauthorized - غير مصادق عليه
- **403** Forbidden - ليس لديك صلاحية
- **404** Not Found - العنصر غير موجود
- **500** Internal Server Error - خطأ في الخادم

### Common Error Messages

```python
# Arabic error messages
ERRORS = {
    'invalid_price': 'يجب إدخال سعر صحيح',
    'price_below_cost': 'السعر لا يمكن أن يكون أقل من التكلفة',
    'invalid_quantity': 'يجب إدخال كمية صحيحة',
    'permission_denied': 'ليس لديك صلاحية لهذه العملية',
    'item_not_found': 'المادة غير موجودة',
    'price_not_found': 'السعر غير موجود في قائمة الأسعار'
}
```

---

## Code Examples - أمثلة برمجية

### Example 1: Complete Pricing Workflow

```python
from apps.core.models import Item, PriceList, UnitOfMeasure
from apps.core.utils.pricing_engine import PricingEngine
from apps.core.utils.cache_manager import PricingCacheManager
from decimal import Decimal

# Get objects
item = Item.objects.get(item_code='ITEM001')
variant = item.variants.first()
price_list = PriceList.objects.get(code='RETAIL')
uom = UnitOfMeasure.objects.get(code='PC')
quantity = Decimal('10')

# Check cache first
cached_price = PricingCacheManager.get_cached_price(
    item_id=item.id,
    variant_id=variant.id,
    quantity=quantity,
    price_list_id=price_list.id,
    uom_id=uom.id
)

if cached_price:
    # Use cached result
    final_price = cached_price['final_price']
    print(f"Cached price: {final_price}")
else:
    # Calculate price
    engine = PricingEngine()
    result = engine.calculate_price(
        item=item,
        variant=variant,
        quantity=quantity,
        price_list=price_list,
        uom=uom,
        apply_rules=True
    )

    # Cache the result
    PricingCacheManager.cache_price(
        item_id=item.id,
        variant_id=variant.id,
        quantity=quantity,
        price_list_id=price_list.id,
        uom_id=uom.id,
        pricing_result=result
    )

    final_price = result['final_price']
    print(f"Calculated price: {final_price}")

print(f"Total: {final_price * quantity}")
```

### Example 2: AJAX Price Update with Validation

```javascript
async function updatePrice(priceItemId, newPrice) {
    try {
        // Show loading
        showLoading();

        // Validate price
        if (parseFloat(newPrice) <= 0) {
            toast.error('السعر يجب أن يكون أكبر من صفر');
            return;
        }

        // Send request
        const result = await PriceOperations.updatePrice(
            priceItemId,
            newPrice
        );

        if (result) {
            // Update UI
            document.getElementById(`price_${priceItemId}`).textContent =
                result.formatted_price;

            // Show success
            toast.success('تم تحديث السعر بنجاح');
        } else {
            toast.error('فشل تحديث السعر');
        }

    } catch (error) {
        console.error('Error:', error);
        toast.error('حدث خطأ أثناء التحديث');
    } finally {
        hideLoading();
    }
}
```

### Example 3: Bulk Import with Validation

```python
from apps.core.validators import validate_price_list_item
from apps.core.models import PriceListItem
from decimal import Decimal

def import_prices(price_data_list):
    """Import prices with validation"""
    imported_count = 0
    errors = []

    for data in price_data_list:
        try:
            # Validate data
            validated = validate_price_list_item(
                price=Decimal(str(data['price'])),
                cost=Decimal(str(data.get('cost', 0)))
            )

            # Create or update price
            price_item, created = PriceListItem.objects.update_or_create(
                price_list_id=data['price_list_id'],
                item_variant_id=data['variant_id'],
                uom_id=data['uom_id'],
                defaults={'price': validated['price']}
            )

            imported_count += 1

        except ValidationError as e:
            errors.append({
                'row': data.get('row_number'),
                'errors': e.message_dict
            })
        except Exception as e:
            errors.append({
                'row': data.get('row_number'),
                'error': str(e)
            })

    return {
        'imported_count': imported_count,
        'error_count': len(errors),
        'errors': errors
    }
```

---

## Performance Tips - نصائح الأداء

### 1. Use Caching

Always check cache before expensive calculations.

تحقق دائماً من الذاكرة المؤقتة قبل الحسابات المكلفة.

```python
# Good
cached = PricingCacheManager.get_cached_price(...)
if not cached:
    result = engine.calculate_price(...)
    PricingCacheManager.cache_price(..., result)
```

### 2. Optimize Database Queries

Use select_related and prefetch_related.

استخدم select_related و prefetch_related.

```python
# Good
items = Item.objects.select_related(
    'category', 'base_uom'
).prefetch_related(
    'variants', 'uom_conversions'
)
```

### 3. Bulk Operations

Use bulk_create and bulk_update when possible.

استخدم bulk_create و bulk_update عندما يكون ذلك ممكناً.

```python
# Good
PriceListItem.objects.bulk_create(price_items, batch_size=100)
```

---

**Last Updated**: 2025-11-19
**Version**: 2.4.0
**Status**: ✅ Production Ready

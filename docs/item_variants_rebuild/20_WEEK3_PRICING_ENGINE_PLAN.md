# Week 3: Pricing Engine - Implementation Plan 💰

**Status**: 🟡 In Progress
**Duration**: 5 أيام عمل
**Focus**: نظام تسعير ذكي ومرن

---

## 📋 Executive Summary

Week 3 focuses on building a comprehensive **Pricing Engine** that supports:
- ✅ Dynamic pricing rules
- ✅ Volume-based pricing (quantity breaks)
- ✅ Customer-specific pricing
- ✅ Time-based pricing (seasonal, promotional)
- ✅ Currency conversion
- ✅ Discount calculations
- ✅ Multi-UoM pricing with automatic conversion
- ✅ Pricing rule priorities and cascading

---

## 🎯 Goals

### Primary Goals:
1. **Smart Price Calculation**: Automatic price calculation with multiple rules
2. **Flexible Rules**: Support any pricing logic through configurable rules
3. **Performance**: Calculate 1000+ prices in < 1 second
4. **Audit Trail**: Track all price changes with history

### Secondary Goals:
1. **Bulk Operations**: Update prices for multiple items at once
2. **Import/Export**: Excel-based price list management
3. **Price Comparison**: Compare prices across lists
4. **Price Simulation**: Test pricing scenarios before applying

---

## 🗓️ Day-by-Day Plan

### **Day 1: Pricing Engine Core** ⭐ نبدأ هنا
**Focus**: Build the core pricing calculation engine

**Files to Create**:
```
apps/core/utils/pricing_engine.py
apps/core/utils/test_pricing_engine.py
```

**Components**:
1. **PricingEngine Class**:
   ```python
   class PricingEngine:
       def calculate_price(item, variant, uom, quantity, price_list,
                          customer, date) -> PriceResult
       def apply_rules(base_price, rules, context) -> Decimal
       def get_applicable_rules(item, context) -> List[PricingRule]
       def calculate_with_uom(item, variant, from_uom, to_uom,
                             price) -> Decimal
   ```

2. **PriceResult Class**:
   ```python
   class PriceResult:
       final_price: Decimal
       base_price: Decimal
       applied_rules: List[Dict]
       discounts: List[Dict]
       conversions: List[Dict]
       calculation_log: List[str]
   ```

3. **Rule Evaluation Engine**:
   - Rule matching (items, categories, price lists)
   - Priority-based application
   - Cascading rules (multiple rules can apply)
   - Date-based validity

**Testing**:
- 15+ test cases covering all pricing scenarios
- Performance test (1000 calculations < 1s)
- Edge cases (negative prices, zero quantities, etc.)

---

### **Day 2: Pricing Rules Management**
**Focus**: CRUD operations for pricing rules

**Files to Create**:
```
apps/core/forms/pricing_forms.py
apps/core/views/pricing_rule_views.py
```

**Components**:
1. **PricingRuleForm**:
   - Full validation for all rule types
   - Dynamic form fields based on rule_type
   - JSON formula editor
   - Date range validation

2. **Views** (5 views):
   - PricingRuleListView (with filtering)
   - PricingRuleDetailView (with simulation)
   - PricingRuleCreateView
   - PricingRuleUpdateView
   - PricingRuleDeleteView (with protection)

3. **URLs**:
   - `/core/pricing-rules/`
   - `/core/pricing-rules/<id>/`
   - `/core/pricing-rules/create/`
   - `/core/pricing-rules/<id>/edit/`
   - `/core/pricing-rules/<id>/delete/`

---

### **Day 3: Price Calculator & Bulk Operations**
**Focus**: Tools for managing prices at scale

**Files to Create**:
```
apps/core/utils/price_calculator.py
apps/core/views/price_calculator_views.py
```

**Components**:
1. **PriceCalculator** (Utility):
   ```python
   class PriceCalculator:
       def calculate_all_prices(item, variant) -> Dict[UoM, Dict[PriceList, Decimal]]
       def bulk_update_prices(items, rule, apply=True) -> Dict
       def simulate_price_change(rule, preview_count=10) -> List[Dict]
       def compare_price_lists(item, variant, uom) -> DataFrame
   ```

2. **BulkPriceUpdateView**:
   - Select items/categories
   - Choose pricing rule
   - Preview changes
   - Apply changes with confirmation

3. **PriceSimulatorView**:
   - Test pricing scenarios
   - What-if analysis
   - Compare before/after

---

### **Day 4: Templates & UI**
**Focus**: Professional user interface

**Files to Create**:
```
apps/core/templates/core/pricing_rules/list.html
apps/core/templates/core/pricing_rules/detail.html
apps/core/templates/core/pricing_rules/form.html
apps/core/templates/core/pricing_rules/delete_confirm.html
apps/core/templates/core/price_calculator/calculator.html
apps/core/templates/core/price_calculator/bulk_update.html
apps/core/templates/core/price_calculator/simulator.html
```

**UI Features**:
- 📊 **Dashboard**: Pricing overview with statistics
- 📝 **Rule Builder**: Visual rule creation wizard
- 🧮 **Calculator**: Interactive price calculator
- 📈 **Price History**: Charts showing price trends
- 🔄 **Bulk Update**: Mass price update tool
- 🎯 **Simulator**: Test scenarios before applying

**Design Elements**:
- Drag & drop rule builder
- Real-time price preview
- Color-coded pricing rules
- Interactive charts (Chart.js)
- Responsive tables (DataTables)
- Bootstrap 5 styling

---

### **Day 5: Testing & Documentation**
**Focus**: Comprehensive testing and documentation

**Testing Suite**:
1. **Unit Tests**:
   - Pricing engine core (20 tests)
   - Rule evaluation (15 tests)
   - Price calculation (10 tests)
   - Edge cases (10 tests)
   - **Total**: 55+ tests

2. **Integration Tests**:
   - End-to-end pricing flow
   - Multi-rule application
   - UoM conversion + pricing
   - Bulk operations

3. **Performance Tests**:
   - 1000 calculations benchmark
   - Concurrent calculations
   - Cache effectiveness

**Documentation**:
```
docs/item_variants_rebuild/
├── 21_WEEK3_DAY1_PRICING_ENGINE_CORE.md
├── 22_WEEK3_DAY2_PRICING_RULES_MGMT.md
├── 23_WEEK3_DAY3_PRICE_CALCULATOR.md
├── 24_WEEK3_DAY4_TEMPLATES_UI.md
├── 25_WEEK3_DAY5_TESTING.md
└── 26_WEEK3_COMPLETE.md
```

---

## 📁 Architecture Overview

### **Pricing Engine Stack**:

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│  (Templates, Forms, Interactive Tools)  │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           View Layer                    │
│  (Pricing Rules CRUD, Calculator Views) │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│        Business Logic Layer             │
│  PricingEngine                          │
│  ├─ calculate_price()                   │
│  ├─ apply_rules()                       │
│  ├─ get_applicable_rules()              │
│  └─ calculate_with_uom()                │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           Data Layer                    │
│  Models: PriceList, PriceListItem,      │
│          PricingRule, PriceHistory      │
└─────────────────────────────────────────┘
```

---

## 🔧 Technical Specifications

### **Pricing Engine Features**:

#### 1. **Rule Types**:
- `MARKUP_PERCENTAGE`: Price = Cost × (1 + markup%)
- `DISCOUNT_PERCENTAGE`: Price = Base × (1 - discount%)
- `PRICE_FORMULA`: Custom formula with JSON
- `BULK_DISCOUNT`: Tiered discounts by quantity
- `SEASONAL_PRICING`: Time-based special pricing
- `CUSTOMER_SPECIFIC`: Pricing per customer/group

#### 2. **Rule Application Logic**:
```python
final_price = base_price
for rule in sorted_rules_by_priority:
    if rule.applies_to(item, context):
        if rule.is_valid_date(date):
            if rule.quantity_in_range(quantity):
                final_price = rule.calculate_price(
                    final_price,
                    quantity,
                    cost_price
                )
```

#### 3. **UoM Integration**:
```python
# Scenario: Price for قطعة = 1.50, need price for دزينة
base_price = get_price(item, variant, uom='قطعة', price_list)
conversion_factor = get_conversion_factor('قطعة', 'دزينة')  # 12
final_price = base_price * conversion_factor  # 1.50 × 12 = 18.00
```

#### 4. **Context Object**:
```python
PricingContext = {
    'item': Item,
    'variant': ItemVariant,
    'uom': UnitOfMeasure,
    'quantity': Decimal,
    'price_list': PriceList,
    'customer': BusinessPartner,
    'date': date,
    'currency': Currency,
    'branch': Branch,
}
```

---

## 💻 Code Examples

### **Example 1: Calculate Price with Rules**

```python
from apps.core.utils.pricing_engine import PricingEngine

engine = PricingEngine(company)

# Calculate price for nail variant with quantity discount
result = engine.calculate_price(
    item=nail_item,
    variant=nail_5cm,
    uom=dozen_uom,
    quantity=100,  # 100 dozens
    price_list=wholesale_list,
    customer=vip_customer,
    date=today
)

print(f"Final Price: {result.final_price}")
print(f"Base Price: {result.base_price}")
print(f"Applied Rules: {result.applied_rules}")
print(f"Total Discount: {result.total_discount}")
```

### **Example 2: Create Pricing Rule**

```python
from apps.core.models import PricingRule

# Bulk discount rule: 10% off for 100+ items
bulk_rule = PricingRule.objects.create(
    company=company,
    name='خصم الجملة 10%',
    code='BULK_10',
    rule_type='BULK_DISCOUNT',
    percentage_value=10.00,
    min_quantity=100,
    apply_to_all_items=True,
    priority=20,
    is_active=True
)
```

### **Example 3: Simulate Price Changes**

```python
from apps.core.utils.price_calculator import PriceCalculator

calculator = PriceCalculator(company)

# Simulate 15% markup on all nails
simulation = calculator.simulate_price_change(
    rule={
        'type': 'MARKUP_PERCENTAGE',
        'value': 15.00,
        'apply_to_categories': [nails_category]
    },
    preview_count=20
)

for item in simulation['preview']:
    print(f"{item['name']}: {item['old_price']} → {item['new_price']}")
```

---

## 🎓 Key Features

### **1. Multi-Layer Pricing**:
- Base price from price list
- Apply pricing rules (cascading)
- Apply customer-specific discounts
- Apply quantity-based discounts
- Convert to requested UoM
- Apply currency conversion

### **2. Smart Caching**:
- Cache price calculations
- Invalidate on price/rule changes
- Per-company cache isolation
- Configurable TTL

### **3. Price History Tracking**:
- Automatic logging of all price changes
- Track who, when, why
- Calculate change percentage
- Compare historical prices

### **4. Bulk Operations**:
- Update 1000+ prices at once
- Preview before applying
- Transaction safety
- Rollback capability

---

## 📊 Expected Outcomes

### **Performance Metrics**:
- Single price calculation: < 10ms
- 1000 calculations: < 1 second
- Bulk update (1000 items): < 30 seconds
- Cache hit rate: > 80%

### **Code Statistics** (Estimated):
| Component | LOC | Files | Tests |
|-----------|-----|-------|-------|
| Pricing Engine | 500 | 1 | 20 |
| Price Calculator | 300 | 1 | 15 |
| Forms | 200 | 1 | 10 |
| Views | 400 | 2 | 10 |
| Templates | 800 | 7 | - |
| Tests | 600 | 2 | 55 |
| **Total** | **~2800** | **14** | **110** |

---

## 🚀 Success Criteria

### **Must Have**:
- ✅ All pricing rule types implemented
- ✅ 55+ tests passing (100%)
- ✅ Performance benchmarks met
- ✅ Full CRUD for pricing rules
- ✅ Professional UI templates

### **Nice to Have**:
- ⭐ Price comparison tool
- ⭐ Price trend charts
- ⭐ Export price lists to Excel
- ⭐ Price approval workflow
- ⭐ Email notifications for price changes

---

## 📝 Notes

### **Design Decisions**:
1. **Cascading Rules**: Multiple rules can apply, sorted by priority
2. **Immutable History**: Never delete price history records
3. **Decimal Precision**: All calculations use Decimal (no float)
4. **Context-Based**: All calculations require full context object
5. **Fail-Safe**: If calculation fails, return base price

### **Future Enhancements** (Week 4+):
- AI-powered pricing suggestions
- Competitor price monitoring
- Dynamic pricing based on demand
- A/B testing for prices
- Price optimization algorithms

---

## 🎯 Integration Points

### **Integrates With**:
- ✅ **Week 1**: Items & Variants system
- ✅ **Week 2**: UoM & Conversions system
- 🔄 **Sales Module**: Order pricing calculation
- 🔄 **Purchases Module**: Cost price tracking
- 🔄 **Accounting Module**: Revenue calculation
- 🔄 **Reports Module**: Pricing analytics

---

## ✅ Checklist for Week 3

### **Day 1: Pricing Engine Core**
- [ ] Create PricingEngine class
- [ ] Implement calculate_price()
- [ ] Implement apply_rules()
- [ ] Implement get_applicable_rules()
- [ ] Create PriceResult class
- [ ] Write 20+ unit tests
- [ ] Performance benchmark
- [ ] Documentation

### **Day 2: Pricing Rules Management**
- [ ] Create PricingRuleForm
- [ ] Create 5 CRUD views
- [ ] Add 5 URL patterns
- [ ] Test all CRUD operations
- [ ] Documentation

### **Day 3: Price Calculator**
- [ ] Create PriceCalculator class
- [ ] Bulk update functionality
- [ ] Price simulation
- [ ] Price comparison
- [ ] Create calculator views
- [ ] Test bulk operations
- [ ] Documentation

### **Day 4: Templates & UI**
- [ ] List template
- [ ] Detail template
- [ ] Form template
- [ ] Calculator template
- [ ] Bulk update template
- [ ] Simulator template
- [ ] JavaScript interactions
- [ ] Responsive design
- [ ] Documentation

### **Day 5: Testing & Documentation**
- [ ] Complete test suite (55+ tests)
- [ ] Integration tests
- [ ] Performance tests
- [ ] Edge case tests
- [ ] Final documentation
- [ ] Week 3 summary

---

**Status**: 🟡 Day 1 In Progress
**Next**: Create PricingEngine class
**Author**: Claude Code
**Project**: ERP System - Item Variants Rebuild
**Week**: 3 of 6
**Progress**: 40% Complete (Weeks 1-2 done, Week 3 started)

---

## 🎉 Let's Build an Amazing Pricing Engine! 💰

# Week 2: UoM System Complete - Detailed Plan

**التاريخ:** 2025-01-19
**المدة:** 6 أيام
**الحالة:** 📋 Planning

---

## 🎯 الأهداف الرئيسية

تطوير نظام شامل لإدارة وحدات القياس مع:
1. ✅ UoM Groups لتنظيم الوحدات
2. ✅ Conversion Chains للتحويلات المتسلسلة
3. ✅ Validation Rules لمنع الأخطاء
4. ✅ Bulk Import/Export للإنتاجية
5. ✅ Integration Testing للتأكد من التكامل

---

## 📅 الجدول الزمني

### Day 1-2: UoM Groups Foundation
- إنشاء UoMGroup Model
- تحديث UnitOfMeasure Model
- Migration
- Forms & Views أساسية
- URLs

### Day 3: Conversion Chains & Validation
- Chain calculation logic
- Bi-directional conversions
- Circular conversion prevention
- Cross-group validation
- Conflict detection

### Day 4: Bulk Operations
- Excel import/export
- Template generation
- Batch validation
- Error reporting

### Day 5: Templates & UI
- UoM Groups templates
- Enhanced conversion UI
- Visualization helpers
- User guides

### Day 6: Testing & Integration
- Unit tests
- Integration tests
- Performance tests
- Documentation

---

## 📦 المكونات المطلوبة

### 1. UoMGroup Model

```python
class UoMGroup(BaseModel):
    """
    مجموعة وحدات القياس - لتنظيم الوحدات المتشابهة

    أمثلة:
    - Weight: kg, g, mg, ton
    - Length: m, cm, mm, km
    - Volume: L, ml, gallon
    - Time: hour, minute, second
    """
    name = CharField(max_length=100)
    code = CharField(max_length=20, unique=True)
    description = TextField(null=True, blank=True)
    base_uom = ForeignKey('UnitOfMeasure', null=True, blank=True,
                          related_name='groups_as_base',
                          on_delete=models.SET_NULL)
    allow_decimal = BooleanField(default=True)
    notes = TextField(null=True, blank=True)

    class Meta:
        db_table = 'core_uomgroup'
        verbose_name = 'مجموعة وحدات قياس'
        verbose_name_plural = 'مجموعات وحدات القياس'
        ordering = ['name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_all_conversions(self):
        """Get all conversions within this group"""
        pass

    def validate_conversion_chain(self, from_uom, to_uom):
        """Validate conversion is possible within group"""
        pass

    def calculate_chain_conversion(self, from_uom, to_uom, quantity):
        """Calculate conversion through chain"""
        pass
```

**Fields:**
- `name`: اسم المجموعة (مثل: "الوزن", "الطول")
- `code`: رمز فريد (مثل: "WEIGHT", "LENGTH")
- `description`: وصف تفصيلي
- `base_uom`: الوحدة الأساسية (مثل: kg للوزن، m للطول)
- `allow_decimal`: السماح بالأرقام العشرية
- `notes`: ملاحظات

**Methods:**
- `get_all_conversions()`: جلب جميع التحويلات في المجموعة
- `validate_conversion_chain()`: التحقق من إمكانية التحويل
- `calculate_chain_conversion()`: حساب التحويل عبر السلسلة

---

### 2. Update UnitOfMeasure Model

```python
class UnitOfMeasure(BaseModel):
    # Existing fields...
    name = CharField(max_length=100)
    code = CharField(max_length=20)
    symbol = CharField(max_length=10)

    # NEW FIELD
    uom_group = ForeignKey('UoMGroup', null=True, blank=True,
                           related_name='units',
                           on_delete=models.PROTECT)

    # NEW FIELD
    is_base_unit = BooleanField(default=False,
                                 help_text="الوحدة الأساسية في المجموعة")

    # Existing fields...
    allow_decimal_quantities = BooleanField(default=True)

    class Meta:
        # Add new constraint
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'uom_group'],
                condition=Q(is_base_unit=True),
                name='one_base_unit_per_group'
            )
        ]

    def get_conversion_to_base(self):
        """Get conversion factor to base unit of group"""
        pass

    def convert_to(self, target_uom, quantity):
        """Convert quantity to target UoM using chain"""
        pass
```

**Changes:**
1. إضافة `uom_group` ForeignKey
2. إضافة `is_base_unit` flag
3. إضافة constraint: وحدة أساسية واحدة فقط لكل مجموعة
4. إضافة methods للتحويل عبر السلسلة

---

### 3. Update UoMConversion Model

```python
class UoMConversion(BaseModel):
    # Existing fields...

    def clean(self):
        """Enhanced validation"""
        super().clean()

        # NEW: Validate same group
        if self.from_uom.uom_group != self.item.base_uom.uom_group:
            raise ValidationError({
                'from_uom': 'يجب أن تكون الوحدة من نفس مجموعة الوحدة الأساسية'
            })

        # NEW: Prevent circular conversions
        if self._creates_circular_conversion():
            raise ValidationError('هذا التحويل سينشئ حلقة دائرية')

        # NEW: Check for conflicts
        if self._conflicts_with_existing():
            raise ValidationError('يوجد تضارب مع تحويل آخر')

    def _creates_circular_conversion(self):
        """Check if this conversion creates a circular reference"""
        pass

    def _conflicts_with_existing(self):
        """Check if conflicts with existing conversions"""
        pass

    def get_chain_path(self):
        """Get the conversion chain path"""
        pass
```

---

### 4. ConversionChain Helper Class

```python
class ConversionChain:
    """
    Helper class for calculating conversion chains

    Example:
    kg → g → mg
    1 kg = 1000 g = 1,000,000 mg
    """

    def __init__(self, uom_group):
        self.group = uom_group
        self.conversions = {}
        self._build_graph()

    def _build_graph(self):
        """Build conversion graph for the group"""
        pass

    def find_path(self, from_uom, to_uom):
        """Find conversion path using BFS/DFS"""
        pass

    def calculate(self, from_uom, to_uom, quantity):
        """Calculate conversion through chain"""
        pass

    def get_all_paths(self):
        """Get all possible conversion paths"""
        pass
```

**Algorithm:**
- استخدام Graph theory (BFS/DFS)
- حساب المسار الأقصر
- حساب معامل التحويل الكلي

---

### 5. Forms

#### UoMGroupForm
```python
class UoMGroupForm(forms.ModelForm):
    class Meta:
        model = UoMGroup
        fields = [
            'name', 'code', 'description',
            'base_uom', 'allow_decimal', 'notes',
            'is_active'
        ]

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

        # Filter base_uom by company and this group
        if self.instance.pk:
            self.fields['base_uom'].queryset = UnitOfMeasure.objects.filter(
                company=company,
                uom_group=self.instance
            )
```

#### UoMConversionFormEnhanced
```python
class UoMConversionForm(forms.ModelForm):
    # Enhanced with group validation

    def clean(self):
        cleaned_data = super().clean()
        from_uom = cleaned_data.get('from_uom')
        item = cleaned_data.get('item')

        # NEW: Check same group
        if from_uom and item:
            if from_uom.uom_group != item.base_uom.uom_group:
                raise ValidationError(
                    'الوحدة يجب أن تكون من نفس مجموعة الوحدة الأساسية للمادة'
                )

        return cleaned_data
```

#### BulkImportForm
```python
class UoMConversionBulkImportForm(forms.Form):
    """
    Form for bulk importing conversions from Excel
    """
    excel_file = forms.FileField(
        label='ملف Excel',
        help_text='قم بتحميل ملف Excel يحتوي على التحويلات'
    )
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label='تجاوز الأخطاء',
        help_text='استمر في الاستيراد حتى مع وجود أخطاء'
    )

    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']

        # Validate file extension
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError('يجب أن يكون الملف بصيغة Excel')

        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError('حجم الملف يجب ألا يتجاوز 10 ميجابايت')

        return file

    def process_import(self, company, user):
        """Process the Excel file and create conversions"""
        pass
```

---

### 6. Views (8 New Views)

1. **UoMGroupListView** - قائمة المجموعات
2. **UoMGroupDetailView** - تفاصيل المجموعة + جميع وحداتها
3. **UoMGroupCreateView** - إنشاء مجموعة جديدة
4. **UoMGroupUpdateView** - تعديل مجموعة
5. **UoMGroupDeleteView** - حذف مجموعة
6. **UoMConversionImportView** - استيراد من Excel
7. **UoMConversionExportView** - تصدير إلى Excel
8. **UoMConversionChainView** - عرض سلسلة التحويلات

---

### 7. URLs (8 New URLs)

```python
# UoM Groups
path('uom-groups/', views.UoMGroupListView.as_view(), name='uom_group_list'),
path('uom-groups/<int:pk>/', views.UoMGroupDetailView.as_view(), name='uom_group_detail'),
path('uom-groups/create/', views.UoMGroupCreateView.as_view(), name='uom_group_create'),
path('uom-groups/<int:pk>/update/', views.UoMGroupUpdateView.as_view(), name='uom_group_update'),
path('uom-groups/<int:pk>/delete/', views.UoMGroupDeleteView.as_view(), name='uom_group_delete'),

# Import/Export
path('uom-conversions/import/', views.UoMConversionImportView.as_view(), name='uom_conversion_import'),
path('uom-conversions/export/', views.UoMConversionExportView.as_view(), name='uom_conversion_export'),

# Chains
path('uom-conversions/chains/', views.UoMConversionChainView.as_view(), name='uom_conversion_chains'),
```

---

### 8. Templates (5 New Templates)

1. **uom_groups/group_list.html** - قائمة المجموعات
2. **uom_groups/group_detail.html** - تفاصيل المجموعة + وحداتها
3. **uom_groups/group_form.html** - نموذج إنشاء/تعديل
4. **uom_conversions/import_form.html** - نموذج الاستيراد
5. **uom_conversions/chain_view.html** - عرض السلاسل بصرياً

---

### 9. Helper Utilities

#### Excel Import/Export
```python
# apps/core/utils/uom_import.py

class UoMConversionImporter:
    """
    Utility for importing UoM conversions from Excel
    """

    REQUIRED_COLUMNS = [
        'from_uom_code',
        'to_uom_code',
        'conversion_factor',
        'item_code',  # optional
        'variant_code',  # optional
    ]

    def __init__(self, excel_file, company, user):
        self.file = excel_file
        self.company = company
        self.user = user
        self.errors = []
        self.warnings = []
        self.created_count = 0
        self.skipped_count = 0

    def validate_file(self):
        """Validate Excel structure"""
        pass

    def parse_rows(self):
        """Parse Excel rows"""
        pass

    def create_conversions(self, skip_errors=True):
        """Create conversions from parsed data"""
        pass

    def generate_report(self):
        """Generate import report"""
        pass


class UoMConversionExporter:
    """
    Utility for exporting UoM conversions to Excel
    """

    def __init__(self, company):
        self.company = company

    def create_template(self):
        """Create empty template for import"""
        pass

    def export_existing(self, queryset=None):
        """Export existing conversions"""
        pass
```

---

### 10. Validation Logic

```python
# apps/core/validators/uom_validators.py

class UoMConversionValidator:
    """
    Comprehensive validation for UoM conversions
    """

    def __init__(self, conversion):
        self.conversion = conversion
        self.errors = []

    def validate_all(self):
        """Run all validations"""
        self.validate_same_group()
        self.validate_no_circular()
        self.validate_no_conflicts()
        self.validate_conversion_factor()
        return len(self.errors) == 0

    def validate_same_group(self):
        """Ensure from_uom and base_uom are in same group"""
        pass

    def validate_no_circular(self):
        """Prevent circular conversion chains"""
        pass

    def validate_no_conflicts(self):
        """Check for conflicting conversions"""
        pass

    def validate_conversion_factor(self):
        """Validate conversion factor is reasonable"""
        pass
```

---

## 📊 معايير النجاح

### Backend:
- ✅ UoMGroup model created and migrated
- ✅ UnitOfMeasure updated with group reference
- ✅ UoMConversion enhanced with validation
- ✅ ConversionChain calculator working
- ✅ All validations implemented
- ✅ Import/Export working with Excel

### Frontend:
- ✅ UoM Groups CRUD UI
- ✅ Enhanced conversion UI with group filtering
- ✅ Import/Export UI
- ✅ Chain visualization
- ✅ Error messages clear and helpful

### Testing:
- ✅ Unit tests for all models
- ✅ Unit tests for conversion chains
- ✅ Integration tests with items
- ✅ Import/Export tests
- ✅ Performance tests (1000+ conversions)

### Documentation:
- ✅ Code documentation (docstrings)
- ✅ User guide for UoM Groups
- ✅ Import template documentation
- ✅ API documentation

---

## 🎯 Use Cases

### Use Case 1: إنشاء مجموعة وزن
```python
# Create Weight group
weight_group = UoMGroup.objects.create(
    company=company,
    name='الوزن',
    code='WEIGHT',
    description='وحدات قياس الوزن',
    allow_decimal=True
)

# Create units
kg = UnitOfMeasure.objects.create(
    company=company,
    name='كيلوجرام',
    code='KG',
    uom_group=weight_group,
    is_base_unit=True
)

g = UnitOfMeasure.objects.create(
    company=company,
    name='جرام',
    code='G',
    uom_group=weight_group
)

mg = UnitOfMeasure.objects.create(
    company=company,
    name='ميليجرام',
    code='MG',
    uom_group=weight_group
)

# Create conversions
UoMConversion.objects.create(
    company=company,
    from_uom=g,
    conversion_factor=0.001,  # 1 g = 0.001 kg
    created_by=user
)

UoMConversion.objects.create(
    company=company,
    from_uom=mg,
    conversion_factor=0.000001,  # 1 mg = 0.000001 kg
    created_by=user
)

# Now can convert: 5000 mg → g → kg
result = mg.convert_to(kg, 5000)
# result = 0.005 kg
```

### Use Case 2: Conversion Chain
```python
# Convert 2500 mg to kg through chain
chain = ConversionChain(weight_group)
path = chain.find_path(mg, kg)
# path = [mg → g → kg]

result = chain.calculate(mg, kg, 2500)
# result = 0.0025 kg
```

### Use Case 3: Bulk Import
```python
# Excel structure:
# from_uom_code | to_uom_code | conversion_factor | item_code | notes
# G             | KG          | 0.001             |           | General
# MG            | KG          | 0.000001          |           | General
# ML            | L           | 0.001             |           | Volume

importer = UoMConversionImporter(excel_file, company, user)
if importer.validate_file():
    importer.create_conversions(skip_errors=True)
    report = importer.generate_report()
    # report: {'created': 3, 'skipped': 0, 'errors': []}
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Circular Conversions
**Problem:** A → B, B → C, C → A (infinite loop)
**Solution:** Use directed graph, detect cycles with DFS

### Challenge 2: Conflicting Conversions
**Problem:** A → B (factor 2), A → B (factor 3)
**Solution:** Unique constraint + validation in clean()

### Challenge 3: Cross-Group Conversions
**Problem:** kg (weight) → L (volume)
**Solution:** Validate same group in clean()

### Challenge 4: Performance with Large Chains
**Problem:** Calculating kg → mg with 10 intermediate steps
**Solution:** Cache conversion factors, optimize graph search

---

## 📈 الجدول الزمني التفصيلي

### Day 1 (2025-01-19)
- ⏰ 09:00-12:00: إنشاء UoMGroup model + Migration
- ⏰ 12:00-15:00: تحديث UnitOfMeasure model + Migration
- ⏰ 15:00-18:00: UoMGroupForm + Basic Views

### Day 2 (2025-01-20)
- ⏰ 09:00-12:00: UoMGroup CRUD Views كاملة
- ⏰ 12:00-15:00: URLs + Templates أساسية
- ⏰ 15:00-18:00: Testing UoM Groups

### Day 3 (2025-01-21)
- ⏰ 09:00-12:00: ConversionChain class + Algorithm
- ⏰ 12:00-15:00: Enhanced validation في UoMConversion
- ⏰ 15:00-18:00: Testing chains + validation

### Day 4 (2025-01-22)
- ⏰ 09:00-12:00: UoMConversionImporter class
- ⏰ 12:00-15:00: UoMConversionExporter class
- ⏰ 15:00-18:00: Import/Export Views + Templates

### Day 5 (2025-01-23)
- ⏰ 09:00-12:00: Enhanced templates for all views
- ⏰ 12:00-15:00: Chain visualization UI
- ⏰ 15:00-18:00: UX improvements + Polish

### Day 6 (2025-01-24)
- ⏰ 09:00-12:00: Comprehensive testing
- ⏰ 12:00-15:00: Integration tests
- ⏰ 15:00-18:00: Documentation + Week 2 summary

---

## 📚 الوثائق المطلوبة

1. **16_WEEK2_DAY1-2_UOM_GROUPS_COMPLETE.md**
   - UoMGroup implementation
   - Migration details
   - Forms & Views

2. **17_WEEK2_DAY3_CONVERSION_CHAINS_COMPLETE.md**
   - Chain algorithm
   - Validation logic
   - Test cases

3. **18_WEEK2_DAY4_IMPORT_EXPORT_COMPLETE.md**
   - Import/Export implementation
   - Excel format guide
   - Error handling

4. **19_WEEK2_DAY5_TEMPLATES_COMPLETE.md**
   - All templates
   - UI/UX decisions
   - Design patterns

5. **20_WEEK2_SUMMARY.md**
   - Week 2 summary
   - Statistics
   - Lessons learned

---

## ✅ الخلاصة

Week 2 سيكون أسبوع تقني مكثف يركز على:
- 🏗️ **البنية:** UoM Groups
- 🔗 **الذكاء:** Conversion Chains
- ✅ **الجودة:** Comprehensive Validation
- 📊 **الإنتاجية:** Bulk Import/Export
- 🧪 **الموثوقية:** Extensive Testing

**Expected Output:**
- 1 New Model (UoMGroup)
- 2 Updated Models (UnitOfMeasure, UoMConversion)
- 3 New Forms
- 8 New Views
- 8 New URLs
- 5 New Templates
- 2 Utility Classes
- 1 Validator Class
- 5 Documentation Files

**Lines of Code:** ~3,000 new lines

---

**آخر تحديث:** 2025-01-19
**الحالة:** 📋 Planning Complete
**التالي:** Start Day 1 Implementation

**Let's Build an Amazing UoM System! 🚀**

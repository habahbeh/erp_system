# كود مبسط لإعداد شركة المخازن الهندسية في Django Shell
# نسخ ولصق كل أمر على حدة

# 1. استيراد النماذج المطلوبة
from django.contrib.auth import get_user_model
from apps.core.models import Currency, Company, Branch, Warehouse, User, SystemSettings, ItemCategory, Brand, UnitOfMeasure, BusinessPartner, NumberingSequence
from django.db import transaction

User = get_user_model()

# 2. إنشاء العملة الأساسية
currency_jod, created = Currency.objects.get_or_create(code='JOD', defaults={'name': 'دينار أردني', 'name_en': 'Jordanian Dinar', 'symbol': 'د.أ', 'exchange_rate': 1.0000, 'is_base': True, 'is_active': True})
print(f"العملة: {currency_jod} - {'تم إنشاؤها' if created else 'موجودة مسبقاً'}")

# 3. إنشاء الشركة
company, created = Company.objects.get_or_create(name='شركة المخازن الهندسية', defaults={'name_en': 'Engineering Warehouses Company', 'tax_number': 'TAX123456789', 'commercial_register': 'CR123456789', 'phone': '06-4027888', 'email': 'info@esco.jo', 'address': 'الأردن - عمان - سحاب - مقابل مدينة الملك عبدالله الثاني الصناعية - بجانب الملعب البلدي', 'city': 'عمان', 'country': 'الأردن', 'fiscal_year_start_month': 1, 'fiscal_year_start_day': 1, 'base_currency': currency_jod, 'default_tax_rate': 16.00, 'is_active': True})
print(f"الشركة: {company} - {'تم إنشاؤها' if created else 'موجودة مسبقاً'}")

# 4. إنشاء المستودعات
warehouse_sahab, created = Warehouse.objects.get_or_create(company=company, code='SAHAB', defaults={'name': 'مستودع سحاب الرئيسي', 'name_en': 'Sahab Main Warehouse', 'address': 'الأردن - عمان - سحاب - مقابل مدينة الملك عبدالله الثاني الصناعية', 'phone': '06-4027888', 'is_main': True, 'allow_negative_stock': False, 'notes': 'المستودع الرئيسي للشركة', 'is_active': True, 'created_by': None})
print(f"مستودع سحاب: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

warehouse_abu_alanda, created = Warehouse.objects.get_or_create(company=company, code='ABUALAN', defaults={'name': 'مستودع أبو علندا', 'name_en': 'Abu Alanda Warehouse', 'address': 'الأردن - عمان - أبو علندا - شارع عبدالكريم الحديد - بجانب بنك الأردن', 'phone': '06-4021234', 'is_main': False, 'allow_negative_stock': False, 'notes': 'الفرع الثاني للشركة', 'is_active': True, 'created_by': None})
print(f"مستودع أبو علندا: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

warehouse_qastal, created = Warehouse.objects.get_or_create(company=company, code='QASTAL', defaults={'name': 'مستودع القسطل', 'name_en': 'Qastal Warehouse', 'address': 'الأردن - عمان - شارع الشحن الجوي - مجمع الجعبري 3', 'phone': '0777041605', 'is_main': False, 'allow_negative_stock': False, 'notes': 'الفرع الثالث للشركة', 'is_active': True, 'created_by': None})
print(f"مستودع القسطل: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

# 5. إنشاء الفروع
branch_sahab, created = Branch.objects.get_or_create(company=company, code='SAHAB', defaults={'name': 'فرع سحاب الرئيسي', 'phone': '06-4027888', 'email': 'sahab@esco.jo', 'address': 'الأردن - عمان - سحاب - مقابل مدينة الملك عبدالله الثاني الصناعية - بجانب الملعب البلدي', 'default_warehouse': warehouse_sahab, 'is_main': True, 'is_active': True})
print(f"فرع سحاب: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

branch_abu_alanda, created = Branch.objects.get_or_create(company=company, code='ABUALAN', defaults={'name': 'فرع أبو علندا', 'phone': '06-4021234', 'email': 'abualanda@esco.jo', 'address': 'الأردن - عمان - أبو علندا - شارع عبدالكريم الحديد - بجانب بنك الأردن', 'default_warehouse': warehouse_abu_alanda, 'is_main': False, 'is_active': True})
print(f"فرع أبو علندا: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

branch_qastal, created = Branch.objects.get_or_create(company=company, code='QASTAL', defaults={'name': 'فرع القسطل', 'phone': '0777041605', 'email': 'qastal@esco.jo', 'address': 'الأردن - عمان - شارع الشحن الجوي - مجمع الجعبري 3', 'default_warehouse': warehouse_qastal, 'is_main': False, 'is_active': True})
print(f"فرع القسطل: {'تم إنشاؤه' if created else 'موجود مسبقاً'}")

# 6. إنشاء وحدات القياس
units_data = [('PCS', 'قطعة', 'Piece'), ('BOX', 'صندوق', 'Box'), ('SET', 'طقم', 'Set'), ('KG', 'كيلو غرام', 'Kilogram'), ('LTR', 'لتر', 'Liter'), ('MTR', 'متر', 'Meter'), ('PACK', 'حزمة', 'Pack'), ('ROLL', 'لفة', 'Roll')]
for code, name, name_en in units_data:
    unit, created = UnitOfMeasure.objects.get_or_create(company=company, code=code, defaults={'name': name, 'name_en': name_en, 'is_active': True, 'created_by': None})
    if created: print(f"وحدة القياس {name}: تم إنشاؤها")

# 7. إنشاء العلامات التجارية
brands_data = [('WURTH', 'WURTH', 'ألمانيا'), ('BOSCH', 'BOSCH', 'ألمانيا'), ('STANLEY', 'STANLEY', 'أمريكا'), ('MAKITA', 'MAKITA', 'اليابان'), ('DEWALT', 'DEWALT', 'أمريكا'), ('HILTI', 'HILTI', 'ليختنشتاين'), ('FESTOOL', 'FESTOOL', 'ألمانيا'), ('3M', '3M', 'أمريكا')]
for name, name_en, country in brands_data:
    brand, created = Brand.objects.get_or_create(company=company, name=name, defaults={'name_en': name_en, 'country': country, 'is_active': True, 'created_by': None})
    if created: print(f"العلامة التجارية {name}: تم إنشاؤها")

# 8. إنشاء التصنيفات الرئيسية
main_categories = [('TOOLS', 'أدوات ومعدات', 'Tools & Equipment'), ('CHEMICALS', 'مواد كيميائية', 'Chemical Materials'), ('FASTENERS', 'مثبتات ومسامير', 'Fasteners & Screws'), ('SAFETY', 'معدات السلامة', 'Safety Equipment'), ('ELECTRICAL', 'كهربائية', 'Electrical')]
for code, name, name_en in main_categories:
    category, created = ItemCategory.objects.get_or_create(company=company, code=code, defaults={'name': name, 'name_en': name_en, 'parent': None, 'level': 1, 'is_active': True, 'created_by': None})
    if created: print(f"التصنيف الرئيسي {name}: تم إنشاؤه")

# 9. إنشاء التصنيفات الفرعية
tools_cat = ItemCategory.objects.get(company=company, code='TOOLS')
chemicals_cat = ItemCategory.objects.get(company=company, code='CHEMICALS')
fasteners_cat = ItemCategory.objects.get(company=company, code='FASTENERS')

sub_categories = [('HAND_TOOLS', 'أدوات يدوية', 'Hand Tools', tools_cat), ('POWER_TOOLS', 'أدوات كهربائية', 'Power Tools', tools_cat), ('CUTTING_TOOLS', 'أدوات قطع', 'Cutting Tools', tools_cat), ('MEASURING_TOOLS', 'أدوات قياس', 'Measuring Tools', tools_cat), ('SPRAYS', 'بخاخات', 'Sprays', chemicals_cat), ('LUBRICANTS', 'مواد تشحيم', 'Lubricants', chemicals_cat), ('ADHESIVES', 'مواد لاصقة', 'Adhesives', chemicals_cat), ('CLEANERS', 'مواد تنظيف', 'Cleaners', chemicals_cat), ('SCREWS', 'مسامير', 'Screws', fasteners_cat), ('BOLTS', 'براغي', 'Bolts', fasteners_cat), ('NUTS', 'صواميل', 'Nuts', fasteners_cat), ('WASHERS', 'حلقات', 'Washers', fasteners_cat)]

for code, name, name_en, parent in sub_categories:
    category, created = ItemCategory.objects.get_or_create(company=company, code=code, defaults={'name': name, 'name_en': name_en, 'parent': parent, 'level': 2, 'is_active': True, 'created_by': None})
    if created: print(f"التصنيف الفرعي {name}: تم إنشاؤه")

# 10. إنشاء تسلسلات الترقيم
sequences = [('sales_invoice', 'SI', 'فاتورة مبيعات'), ('sales_quotation', 'SQ', 'عرض سعر'), ('purchase_invoice', 'PI', 'فاتورة مشتريات'), ('purchase_order', 'PO', 'أمر شراء'), ('stock_in', 'SIN', 'سند إدخال'), ('stock_out', 'SOUT', 'سند إخراج'), ('stock_transfer', 'STR', 'سند تحويل')]
for doc_type, prefix, desc in sequences:
    sequence, created = NumberingSequence.objects.get_or_create(company=company, document_type=doc_type, defaults={'prefix': prefix, 'next_number': 1, 'padding': 6, 'yearly_reset': True, 'include_year': True, 'include_month': False, 'separator': '/', 'is_active': True, 'created_by': None})
    if created: print(f"تسلسل الترقيم {desc}: تم إنشاؤه")

# 11. إنشاء إعدادات النظام
settings, created = SystemSettings.objects.get_or_create(company=company, defaults={'negative_stock_allowed': False, 'stock_valuation_method': 'average', 'customer_credit_check': True, 'auto_create_journal_entries': True, 'session_timeout': 30})
if created: print("إعدادات النظام: تم إنشاؤها")

# 12. إنشاء المستخدم الرئيسي
admin_user, created = User.objects.get_or_create(username='esco_admin', defaults={'email': 'admin@esco.jo', 'first_name': 'مدير', 'last_name': 'النظام', 'phone': '0775599466', 'company': company, 'branch': branch_sahab, 'default_warehouse': warehouse_sahab, 'max_discount_percentage': 100.00, 'ui_language': 'ar', 'theme': 'light', 'is_staff': True, 'is_superuser': True, 'is_active': True})
if created:
    admin_user.set_password('esco@123')
    admin_user.save()
    print(f"المستخدم الرئيسي: تم إنشاؤه - البريد: admin@esco.jo - كلمة المرور: esco@123")
else:
    print("المستخدم الرئيسي: موجود مسبقاً")

# 13. إضافة بعض العملاء
customer1, created = BusinessPartner.objects.get_or_create(company=company, code='CUS000001', defaults={'partner_type': 'customer', 'name': 'شركة البناء المتقدم', 'name_en': 'Advanced Construction Company', 'contact_person': 'أحمد محمد', 'phone': '06-5551234', 'mobile': '079-1234567', 'email': 'info@advancedconstruction.jo', 'address': 'عمان - جبل الحسين - شارع الملكة رانيا', 'city': 'عمان', 'region': 'العاصمة', 'tax_number': 'TAX987654321', 'credit_limit': 50000.00, 'credit_period': 30, 'is_active': True, 'created_by': None})
if created: print("عميل شركة البناء المتقدم: تم إنشاؤه")

supplier1, created = BusinessPartner.objects.get_or_create(company=company, code='SUP000001', defaults={'partner_type': 'supplier', 'name': 'شركة الأدوات الألمانية', 'name_en': 'German Tools Company', 'contact_person': 'Hans Mueller', 'phone': '+49-30-12345678', 'email': 'sales@germantools.de', 'address': 'Berlin, Germany', 'city': 'Berlin', 'region': 'Europe', 'tax_number': 'DE123456789', 'credit_limit': 100000.00, 'credit_period': 60, 'is_active': True, 'created_by': None})
if created: print("مورد شركة الأدوات الألمانية: تم إنشاؤه")

# 14. طباعة تقرير نهائي
print("\n" + "="*50)
print("🎉 تم إعداد شركة المخازن الهندسية بنجاح!")
print("="*50)
print(f"🏢 الشركة: {company.name}")
print(f"🏪 عدد الفروع: {company.branches.count()}")
print(f"📦 عدد المستودعات: {Warehouse.objects.filter(company=company).count()}")
print(f"📏 عدد وحدات القياس: {UnitOfMeasure.objects.filter(company=company).count()}")
print(f"🏷️ عدد العلامات التجارية: {Brand.objects.filter(company=company).count()}")
print(f"📂 عدد تصنيفات المواد: {ItemCategory.objects.filter(company=company).count()}")
print(f"🔢 عدد تسلسلات الترقيم: {NumberingSequence.objects.filter(company=company).count()}")
print(f"🤝 عدد  العملاء: {BusinessPartner.objects.filter(company=company).count()}")
print(f"👤 المستخدم الرئيسي: admin@esco.jo / esco@123")
print("="*50)
print("⚠️  لا تنسَ تغيير كلمة المرور بعد أول تسجيل دخول!")
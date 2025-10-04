# ==========================================
# الخطوة 2: إنشاء أنواع الحسابات (AccountType)
# ==========================================

from apps.accounting.models import AccountType, Account
from apps.core.models import Company, Currency

# الحصول على الشركة والعملة
company = Company.objects.first()
currency = Currency.objects.get(code='JOD')

# 1. الأصول - Assets
assets_type = AccountType.objects.create(
    code='ASSETS',
    name='الأصول',
    type_category='assets',
    normal_balance='debit'
)

# 2. الخصوم - Liabilities
liabilities_type = AccountType.objects.create(
    code='LIABILITIES',
    name='الخصوم',
    type_category='liabilities',
    normal_balance='credit'
)

# 3. حقوق الملكية - Equity
equity_type = AccountType.objects.create(
    code='EQUITY',
    name='حقوق الملكية',
    type_category='equity',
    normal_balance='credit'
)

# 4. الإيرادات - Revenue
revenue_type = AccountType.objects.create(
    code='REVENUE',
    name='الإيرادات',
    type_category='revenue',
    normal_balance='credit'
)

# 5. المصروفات - Expenses
expenses_type = AccountType.objects.create(
    code='EXPENSES',
    name='المصروفات',
    type_category='expenses',
    normal_balance='debit'
)

print("✅ تم إنشاء أنواع الحسابات الخمسة بنجاح!")



# 2 ======

# ==========================================
# الخطوة 3: المستوى 1 - الحسابات الرئيسية
# ==========================================

# 1 - الأصول
account_1 = Account.objects.create(
    company=company,
    code='1',
    name='الأصول',
    name_en='Assets',
    account_type=assets_type,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

# 2 - الخصوم
account_2 = Account.objects.create(
    company=company,
    code='2',
    name='الخصوم',
    name_en='Liabilities',
    account_type=liabilities_type,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

# 3 - حقوق الملكية
account_3 = Account.objects.create(
    company=company,
    code='3',
    name='حقوق الملكية',
    name_en='Equity',
    account_type=equity_type,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

# 4 - الإيرادات
account_4 = Account.objects.create(
    company=company,
    code='4',
    name='الإيرادات',
    name_en='Revenue',
    account_type=revenue_type,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

# 5 - تكلفة المبيعات
account_5 = Account.objects.create(
    company=company,
    code='5',
    name='تكلفة المبيعات',
    name_en='Cost of Sales',
    account_type=expenses_type,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

# 6 - المصروفات
account_6 = Account.objects.create(
    company=company,
    code='6',
    name='المصروفات',
    name_en='Expenses',
    account_type=expenses_type,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=1
)

print("✅ تم إنشاء الحسابات الرئيسية (المستوى 1) بنجاح!")



# ==========================================
# الخطوة 4: المستوى 2 - التصنيفات الفرعية
# ==========================================

# ============================================
# تحت 1 - الأصول
# ============================================

# 11 - الأصول المتداولة
account_11 = Account.objects.create(
    company=company,
    code='11',
    name='الأصول المتداولة',
    name_en='Current Assets',
    account_type=assets_type,
    parent=account_1,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 12 - الأصول الثابتة
account_12 = Account.objects.create(
    company=company,
    code='12',
    name='الأصول الثابتة',
    name_en='Fixed Assets',
    account_type=assets_type,
    parent=account_1,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 13 - أصول أخرى
account_13 = Account.objects.create(
    company=company,
    code='13',
    name='أصول أخرى',
    name_en='Other Assets',
    account_type=assets_type,
    parent=account_1,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# ============================================
# تحت 2 - الخصوم
# ============================================

# 21 - الخصوم المتداولة
account_21 = Account.objects.create(
    company=company,
    code='21',
    name='الخصوم المتداولة',
    name_en='Current Liabilities',
    account_type=liabilities_type,
    parent=account_2,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 22 - الخصوم طويلة الأجل
account_22 = Account.objects.create(
    company=company,
    code='22',
    name='الخصوم طويلة الأجل',
    name_en='Long-term Liabilities',
    account_type=liabilities_type,
    parent=account_2,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# ============================================
# تحت 3 - حقوق الملكية
# ============================================

# 31 - رأس المال
account_31 = Account.objects.create(
    company=company,
    code='31',
    name='رأس المال',
    name_en='Capital',
    account_type=equity_type,
    parent=account_3,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 32 - الأرباح المحتجزة
account_32 = Account.objects.create(
    company=company,
    code='32',
    name='الأرباح المحتجزة',
    name_en='Retained Earnings',
    account_type=equity_type,
    parent=account_3,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 33 - الاحتياطيات
account_33 = Account.objects.create(
    company=company,
    code='33',
    name='الاحتياطيات',
    name_en='Reserves',
    account_type=equity_type,
    parent=account_3,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# ============================================
# تحت 4 - الإيرادات
# ============================================

# 41 - إيرادات المبيعات
account_41 = Account.objects.create(
    company=company,
    code='41',
    name='إيرادات المبيعات',
    name_en='Sales Revenue',
    account_type=revenue_type,
    parent=account_4,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 42 - إيرادات أخرى
account_42 = Account.objects.create(
    company=company,
    code='42',
    name='إيرادات أخرى',
    name_en='Other Revenue',
    account_type=revenue_type,
    parent=account_4,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# ============================================
# تحت 5 - تكلفة المبيعات
# ============================================

# 51 - تكلفة البضاعة المباعة
account_51 = Account.objects.create(
    company=company,
    code='51',
    name='تكلفة البضاعة المباعة',
    name_en='Cost of Goods Sold',
    account_type=expenses_type,
    parent=account_5,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# ============================================
# تحت 6 - المصروفات
# ============================================

# 61 - مصروفات إدارية وعمومية
account_61 = Account.objects.create(
    company=company,
    code='61',
    name='مصروفات إدارية وعمومية',
    name_en='Administrative & General Expenses',
    account_type=expenses_type,
    parent=account_6,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 62 - مصروفات تشغيلية
account_62 = Account.objects.create(
    company=company,
    code='62',
    name='مصروفات تشغيلية',
    name_en='Operating Expenses',
    account_type=expenses_type,
    parent=account_6,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 63 - مصروفات تسويقية
account_63 = Account.objects.create(
    company=company,
    code='63',
    name='مصروفات تسويقية',
    name_en='Marketing Expenses',
    account_type=expenses_type,
    parent=account_6,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

# 64 - مصروفات مالية
account_64 = Account.objects.create(
    company=company,
    code='64',
    name='مصروفات مالية',
    name_en='Financial Expenses',
    account_type=expenses_type,
    parent=account_6,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=2
)

print("✅ تم إنشاء التصنيفات الفرعية (المستوى 2) بنجاح!")




# ==========================================
# الخطوة 5: المستوى 3 - المجموعات (4 أرقام)
# ==========================================

# ============================================
# تحت 11 - الأصول المتداولة
# ============================================

# 1101 - النقدية والبنوك
account_1101 = Account.objects.create(
    company=company,
    code='1101',
    name='النقدية والبنوك',
    name_en='Cash and Banks',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1102 - الذمم المدينة
account_1102 = Account.objects.create(
    company=company,
    code='1102',
    name='الذمم المدينة',
    name_en='Accounts Receivable',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1103 - المخزون
account_1103 = Account.objects.create(
    company=company,
    code='1103',
    name='المخزون',
    name_en='Inventory',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1104 - مصروفات مدفوعة مقدماً
account_1104 = Account.objects.create(
    company=company,
    code='1104',
    name='مصروفات مدفوعة مقدماً',
    name_en='Prepaid Expenses',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1105 - سلف وأمانات
account_1105 = Account.objects.create(
    company=company,
    code='1105',
    name='سلف وأمانات',
    name_en='Advances and Deposits',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1106 - بضاعة في الطريق
account_1106 = Account.objects.create(
    company=company,
    code='1106',
    name='بضاعة في الطريق',
    name_en='Goods in Transit',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1107 - اعتمادات مستندية
account_1107 = Account.objects.create(
    company=company,
    code='1107',
    name='اعتمادات مستندية',
    name_en='Letters of Credit',
    account_type=assets_type,
    parent=account_11,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)



# ============================================
# تحت 12 - الأصول الثابتة
# ============================================

# 1201 - أراضي
account_1201 = Account.objects.create(
    company=company,
    code='1201',
    name='أراضي',
    name_en='Land',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1202 - مباني ومنشآت
account_1202 = Account.objects.create(
    company=company,
    code='1202',
    name='مباني ومنشآت',
    name_en='Buildings',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1203 - سيارات ومركبات
account_1203 = Account.objects.create(
    company=company,
    code='1203',
    name='سيارات ومركبات',
    name_en='Vehicles',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1204 - أثاث ومعدات مكتبية
account_1204 = Account.objects.create(
    company=company,
    code='1204',
    name='أثاث ومعدات مكتبية',
    name_en='Furniture & Office Equipment',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1205 - أجهزة حاسوب
account_1205 = Account.objects.create(
    company=company,
    code='1205',
    name='أجهزة حاسوب',
    name_en='Computer Equipment',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 1206 - مجمع الاستهلاك
account_1206 = Account.objects.create(
    company=company,
    code='1206',
    name='مجمع الاستهلاك',
    name_en='Accumulated Depreciation',
    account_type=assets_type,
    parent=account_12,
    currency=currency,
    nature='credit',  # ملاحظة: مجمع الاستهلاك دائن
    can_have_children=True,
    accept_entries=False,
    level=3
)



# ============================================
# تحت 21 - الخصوم المتداولة
# ============================================

# 2101 - الذمم الدائنة
account_2101 = Account.objects.create(
    company=company,
    code='2101',
    name='الذمم الدائنة',
    name_en='Accounts Payable',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 2102 - مصروفات مستحقة
account_2102 = Account.objects.create(
    company=company,
    code='2102',
    name='مصروفات مستحقة',
    name_en='Accrued Expenses',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 2103 - ضرائب مستحقة
account_2103 = Account.objects.create(
    company=company,
    code='2103',
    name='ضرائب مستحقة',
    name_en='Taxes Payable',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 2104 - رواتب مستحقة
account_2104 = Account.objects.create(
    company=company,
    code='2104',
    name='رواتب مستحقة',
    name_en='Salaries Payable',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 2105 - قروض قصيرة الأجل
account_2105 = Account.objects.create(
    company=company,
    code='2105',
    name='قروض قصيرة الأجل',
    name_en='Short-term Loans',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 2106 - إيرادات مقبوضة مقدماً
account_2106 = Account.objects.create(
    company=company,
    code='2106',
    name='إيرادات مقبوضة مقدماً',
    name_en='Unearned Revenue',
    account_type=liabilities_type,
    parent=account_21,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)



# ============================================
# تحت 41 - إيرادات المبيعات
# ============================================

# 4101 - مبيعات معدات صناعية
account_4101 = Account.objects.create(
    company=company,
    code='4101',
    name='مبيعات معدات صناعية',
    name_en='Industrial Equipment Sales',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 4102 - مبيعات مواد كيميائية
account_4102 = Account.objects.create(
    company=company,
    code='4102',
    name='مبيعات مواد كيميائية',
    name_en='Chemical Materials Sales',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 4103 - مبيعات قطع غيار
account_4103 = Account.objects.create(
    company=company,
    code='4103',
    name='مبيعات قطع غيار',
    name_en='Spare Parts Sales',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 4104 - مبيعات أدوات ورشة
account_4104 = Account.objects.create(
    company=company,
    code='4104',
    name='مبيعات أدوات ورشة',
    name_en='Workshop Tools Sales',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 4105 - مردودات المبيعات
account_4105 = Account.objects.create(
    company=company,
    code='4105',
    name='مردودات المبيعات',
    name_en='Sales Returns',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='debit',  # ملاحظة: مردودات المبيعات مدينة
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 4106 - خصومات المبيعات
account_4106 = Account.objects.create(
    company=company,
    code='4106',
    name='خصومات المبيعات',
    name_en='Sales Discounts',
    account_type=revenue_type,
    parent=account_41,
    currency=currency,
    nature='debit',  # ملاحظة: خصومات المبيعات مدينة
    can_have_children=True,
    accept_entries=False,
    level=3
)



# الخطوة 5️⃣ (تابع): بقية المستوى الثالثخامساً: تحت 51 - تكلفة البضاعة المباعة

# ============================================
# تحت 51 - تكلفة البضاعة المباعة
# ============================================

# 5101 - تكلفة معدات صناعية مباعة
account_5101 = Account.objects.create(
    company=company,
    code='5101',
    name='تكلفة معدات صناعية مباعة',
    name_en='Cost of Industrial Equipment Sold',
    account_type=expenses_type,
    parent=account_51,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 5102 - تكلفة مواد كيميائية مباعة
account_5102 = Account.objects.create(
    company=company,
    code='5102',
    name='تكلفة مواد كيميائية مباعة',
    name_en='Cost of Chemical Materials Sold',
    account_type=expenses_type,
    parent=account_51,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 5103 - تكلفة قطع غيار مباعة
account_5103 = Account.objects.create(
    company=company,
    code='5103',
    name='تكلفة قطع غيار مباعة',
    name_en='Cost of Spare Parts Sold',
    account_type=expenses_type,
    parent=account_51,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 5104 - تكلفة أدوات ورشة مباعة
account_5104 = Account.objects.create(
    company=company,
    code='5104',
    name='تكلفة أدوات ورشة مباعة',
    name_en='Cost of Workshop Tools Sold',
    account_type=expenses_type,
    parent=account_51,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# ============================================
# تحت 61 - مصروفات إدارية وعمومية
# ============================================

# 6101 - رواتب وأجور
account_6101 = Account.objects.create(
    company=company,
    code='6101',
    name='رواتب وأجور',
    name_en='Salaries and Wages',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6102 - إيجارات
account_6102 = Account.objects.create(
    company=company,
    code='6102',
    name='إيجارات',
    name_en='Rent',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6103 - مرافق عامة
account_6103 = Account.objects.create(
    company=company,
    code='6103',
    name='مرافق عامة',
    name_en='Utilities',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6104 - اتصالات
account_6104 = Account.objects.create(
    company=company,
    code='6104',
    name='اتصالات',
    name_en='Communications',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6105 - قرطاسية ومطبوعات
account_6105 = Account.objects.create(
    company=company,
    code='6105',
    name='قرطاسية ومطبوعات',
    name_en='Stationery and Printing',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6106 - تأمينات
account_6106 = Account.objects.create(
    company=company,
    code='6106',
    name='تأمينات',
    name_en='Insurance',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6107 - استشارات مهنية
account_6107 = Account.objects.create(
    company=company,
    code='6107',
    name='استشارات مهنية',
    name_en='Professional Fees',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6108 - ضيافة
account_6108 = Account.objects.create(
    company=company,
    code='6108',
    name='ضيافة',
    name_en='Hospitality',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# ============================================
# تحت 62 - مصروفات تشغيلية
# ============================================

# 6201 - نقل وشحن
account_6201 = Account.objects.create(
    company=company,
    code='6201',
    name='نقل وشحن',
    name_en='Transportation and Shipping',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6202 - صيانة وإصلاحات
account_6202 = Account.objects.create(
    company=company,
    code='6202',
    name='صيانة وإصلاحات',
    name_en='Maintenance and Repairs',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6203 - مصاريف تخزين
account_6203 = Account.objects.create(
    company=company,
    code='6203',
    name='مصاريف تخزين',
    name_en='Storage Expenses',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6204 - وقود ومحروقات
account_6204 = Account.objects.create(
    company=company,
    code='6204',
    name='وقود ومحروقات',
    name_en='Fuel',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6205 - جمارك ورسوم استيراد
account_6205 = Account.objects.create(
    company=company,
    code='6205',
    name='جمارك ورسوم استيراد',
    name_en='Customs and Import Fees',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6206 - تأمين بضائع
account_6206 = Account.objects.create(
    company=company,
    code='6206',
    name='تأمين بضائع',
    name_en='Goods Insurance',
    account_type=expenses_type,
    parent=account_62,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)


# ============================================
# تحت 63 - مصروفات تسويقية
# ============================================

# 6301 - إعلانات ودعاية
account_6301 = Account.objects.create(
    company=company,
    code='6301',
    name='إعلانات ودعاية',
    name_en='Advertising and Promotion',
    account_type=expenses_type,
    parent=account_63,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6302 - عمولات مبيعات
account_6302 = Account.objects.create(
    company=company,
    code='6302',
    name='عمولات مبيعات',
    name_en='Sales Commissions',
    account_type=expenses_type,
    parent=account_63,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6303 - مصاريف معارض
account_6303 = Account.objects.create(
    company=company,
    code='6303',
    name='مصاريف معارض',
    name_en='Exhibition Expenses',
    account_type=expenses_type,
    parent=account_63,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6304 - هدايا ودعاية
account_6304 = Account.objects.create(
    company=company,
    code='6304',
    name='هدايا ودعاية',
    name_en='Gifts and Promotional Items',
    account_type=expenses_type,
    parent=account_63,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# ============================================
# تحت 64 - مصروفات مالية
# ============================================

# 6401 - فوائد بنكية
account_6401 = Account.objects.create(
    company=company,
    code='6401',
    name='فوائد بنكية',
    name_en='Bank Interest',
    account_type=expenses_type,
    parent=account_64,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6402 - عمولات بنكية
account_6402 = Account.objects.create(
    company=company,
    code='6402',
    name='عمولات بنكية',
    name_en='Bank Charges',
    account_type=expenses_type,
    parent=account_64,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6403 - فروقات عملة
account_6403 = Account.objects.create(
    company=company,
    code='6403',
    name='فروقات عملة',
    name_en='Exchange Rate Differences',
    account_type=expenses_type,
    parent=account_64,
    currency=currency,
    nature='both',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# 6404 - ديون معدومة
account_6404 = Account.objects.create(
    company=company,
    code='6404',
    name='ديون معدومة',
    name_en='Bad Debts',
    account_type=expenses_type,
    parent=account_64,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

print("✅ تم إنشاء المجموعات (المستوى 3) بنجاح!")






# الخطوة 6️⃣: المستوى الرابع (الحسابات التفصيلية - 6 أرقام)
# الآن الجزء الأهم! سأنشئ الحسابات التفصيلية التي تقبل القيود
# أولاً: تحت 1101 - النقدية والبنوك

# ==========================================
# الخطوة 6: المستوى 4 - الحسابات التفصيلية
# ==========================================

# ============================================
# تحت 1101 - النقدية والبنوك
# ============================================

# الصناديق
account_110101 = Account.objects.create(
    company=company,
    code='110101',
    name='الصندوق - الفرع الرئيسي',
    name_en='Cash - Main Branch',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_cash_account=True,
    level=4
)

account_110102 = Account.objects.create(
    company=company,
    code='110102',
    name='الصندوق - فرع القسطل',
    name_en='Cash - Al-Qastal Branch',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_cash_account=True,
    level=4
)

account_110103 = Account.objects.create(
    company=company,
    code='110103',
    name='الصندوق - فرع أبو علندا',
    name_en='Cash - Abu Alanda Branch',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_cash_account=True,
    level=4
)

account_110104 = Account.objects.create(
    company=company,
    code='110104',
    name='الصندوق - فرع سحاب',
    name_en='Cash - Sahab Branch',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_cash_account=True,
    level=4
)

# البنوك (حسب ما في الملف القديم)
account_110105 = Account.objects.create(
    company=company,
    code='110105',
    name='البنك الإسلامي الأردني',
    name_en='Jordan Islamic Bank',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_bank_account=True,
    level=4
)

account_110106 = Account.objects.create(
    company=company,
    code='110106',
    name='البنك العربي',
    name_en='Arab Bank',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_bank_account=True,
    level=4
)

account_110107 = Account.objects.create(
    company=company,
    code='110107',
    name='بنك الإسكان',
    name_en='Housing Bank',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_bank_account=True,
    level=4
)

account_110108 = Account.objects.create(
    company=company,
    code='110108',
    name='البنك العربي الإسلامي الدولي',
    name_en='Arab International Islamic Bank',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_bank_account=True,
    level=4
)

account_110109 = Account.objects.create(
    company=company,
    code='110109',
    name='بنك صفوة الإسلامي',
    name_en='Safwa Islamic Bank',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    is_bank_account=True,
    level=4
)

# حسابات نقدية إضافية
account_110110 = Account.objects.create(
    company=company,
    code='110110',
    name='النقدية في الطريق',
    name_en='Cash in Transit',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110111 = Account.objects.create(
    company=company,
    code='110111',
    name='محافظ إلكترونية',
    name_en='Digital Wallets',
    account_type=assets_type,
    parent=account_1101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1102 - الذمم المدينة
# ============================================

account_110201 = Account.objects.create(
    company=company,
    code='110201',
    name='ذمم عملاء - محلي',
    name_en='Accounts Receivable - Local',
    account_type=assets_type,
    parent=account_1102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110202 = Account.objects.create(
    company=company,
    code='110202',
    name='ذمم عملاء - خارجي',
    name_en='Accounts Receivable - Foreign',
    account_type=assets_type,
    parent=account_1102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110203 = Account.objects.create(
    company=company,
    code='110203',
    name='أوراق قبض',
    name_en='Notes Receivable',
    account_type=assets_type,
    parent=account_1102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110204 = Account.objects.create(
    company=company,
    code='110204',
    name='شيكات برسم التحصيل',
    name_en='Checks Under Collection',
    account_type=assets_type,
    parent=account_1102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110205 = Account.objects.create(
    company=company,
    code='110205',
    name='مخصص ديون مشكوك في تحصيلها',
    name_en='Allowance for Doubtful Accounts',
    account_type=assets_type,
    parent=account_1102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 1103 - المخزون
# ============================================

account_110301 = Account.objects.create(
    company=company,
    code='110301',
    name='مخزون معدات صناعية',
    name_en='Industrial Equipment Inventory',
    account_type=assets_type,
    parent=account_1103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110302 = Account.objects.create(
    company=company,
    code='110302',
    name='مخزون مواد كيميائية وتشحيم',
    name_en='Chemical & Lubricant Materials Inventory',
    account_type=assets_type,
    parent=account_1103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110303 = Account.objects.create(
    company=company,
    code='110303',
    name='مخزون قطع غيار',
    name_en='Spare Parts Inventory',
    account_type=assets_type,
    parent=account_1103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110304 = Account.objects.create(
    company=company,
    code='110304',
    name='مخزون أدوات ورشة',
    name_en='Workshop Tools Inventory',
    account_type=assets_type,
    parent=account_1103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110305 = Account.objects.create(
    company=company,
    code='110305',
    name='مخزون تالف ومعيب',
    name_en='Damaged Inventory',
    account_type=assets_type,
    parent=account_1103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1104 - مصروفات مدفوعة مقدماً
# ============================================

account_110401 = Account.objects.create(
    company=company,
    code='110401',
    name='إيجارات مدفوعة مقدماً',
    name_en='Prepaid Rent',
    account_type=assets_type,
    parent=account_1104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110402 = Account.objects.create(
    company=company,
    code='110402',
    name='تأمينات مدفوعة مقدماً',
    name_en='Prepaid Insurance',
    account_type=assets_type,
    parent=account_1104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110403 = Account.objects.create(
    company=company,
    code='110403',
    name='مصروفات مقدمة أخرى',
    name_en='Other Prepaid Expenses',
    account_type=assets_type,
    parent=account_1104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1105 - سلف وأمانات
# ============================================

account_110501 = Account.objects.create(
    company=company,
    code='110501',
    name='سلف موظفين',
    name_en='Employee Advances',
    account_type=assets_type,
    parent=account_1105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110502 = Account.objects.create(
    company=company,
    code='110502',
    name='أمانات ودفعات مقدمة',
    name_en='Deposits and Advance Payments',
    account_type=assets_type,
    parent=account_1105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110503 = Account.objects.create(
    company=company,
    code='110503',
    name='تأمينات موردين',
    name_en='Supplier Deposits',
    account_type=assets_type,
    parent=account_1105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1106 - بضاعة في الطريق
# ============================================

account_110601 = Account.objects.create(
    company=company,
    code='110601',
    name='بضاعة في الطريق - بحري',
    name_en='Goods in Transit - Sea',
    account_type=assets_type,
    parent=account_1106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110602 = Account.objects.create(
    company=company,
    code='110602',
    name='بضاعة في الطريق - جوي',
    name_en='Goods in Transit - Air',
    account_type=assets_type,
    parent=account_1106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110603 = Account.objects.create(
    company=company,
    code='110603',
    name='بضاعة في الطريق - بري',
    name_en='Goods in Transit - Land',
    account_type=assets_type,
    parent=account_1106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 1107 - اعتمادات مستندية
# ============================================

account_110701 = Account.objects.create(
    company=company,
    code='110701',
    name='اعتمادات مستندية مفتوحة',
    name_en='Open Letters of Credit',
    account_type=assets_type,
    parent=account_1107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_110702 = Account.objects.create(
    company=company,
    code='110702',
    name='غطاء اعتمادات مستندية',
    name_en='LC Coverage',
    account_type=assets_type,
    parent=account_1107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# 🚀 إكمال المستوى الرابع
# الخطوة 6️⃣ (تابع): بقية المستوى الرابعثامناً: تحت 1201 - أراضي


# ============================================
# تحت 1201 - أراضي
# ============================================

account_120101 = Account.objects.create(
    company=company,
    code='120101',
    name='أراضي - المكتب الرئيسي',
    name_en='Land - Main Office',
    account_type=assets_type,
    parent=account_1201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120102 = Account.objects.create(
    company=company,
    code='120102',
    name='أراضي - المستودعات',
    name_en='Land - Warehouses',
    account_type=assets_type,
    parent=account_1201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)
# ============================================
# تحت 1202 - مباني ومنشآت
# ============================================

account_120201 = Account.objects.create(
    company=company,
    code='120201',
    name='مبنى المكتب الرئيسي',
    name_en='Main Office Building',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120202 = Account.objects.create(
    company=company,
    code='120202',
    name='مبنى فرع القسطل',
    name_en='Al-Qastal Branch Building',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120203 = Account.objects.create(
    company=company,
    code='120203',
    name='مبنى فرع أبو علندا',
    name_en='Abu Alanda Branch Building',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120204 = Account.objects.create(
    company=company,
    code='120204',
    name='مبنى فرع سحاب',
    name_en='Sahab Branch Building',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120205 = Account.objects.create(
    company=company,
    code='120205',
    name='مستودعات',
    name_en='Warehouses',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120206 = Account.objects.create(
    company=company,
    code='120206',
    name='تحسينات على مباني مستأجرة',
    name_en='Leasehold Improvements',
    account_type=assets_type,
    parent=account_1202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1203 - سيارات ومركبات
# ============================================

account_120301 = Account.objects.create(
    company=company,
    code='120301',
    name='سيارات إدارية',
    name_en='Administrative Vehicles',
    account_type=assets_type,
    parent=account_1203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120302 = Account.objects.create(
    company=company,
    code='120302',
    name='شاحنات نقل',
    name_en='Delivery Trucks',
    account_type=assets_type,
    parent=account_1203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120303 = Account.objects.create(
    company=company,
    code='120303',
    name='سيارات مبيعات',
    name_en='Sales Vehicles',
    account_type=assets_type,
    parent=account_1203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1204 - أثاث ومعدات مكتبية
# ============================================

account_120401 = Account.objects.create(
    company=company,
    code='120401',
    name='أثاث مكتبي',
    name_en='Office Furniture',
    account_type=assets_type,
    parent=account_1204,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120402 = Account.objects.create(
    company=company,
    code='120402',
    name='معدات مكتبية',
    name_en='Office Equipment',
    account_type=assets_type,
    parent=account_1204,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120403 = Account.objects.create(
    company=company,
    code='120403',
    name='أجهزة عرض وعروض',
    name_en='Display Equipment',
    account_type=assets_type,
    parent=account_1204,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1205 - أجهزة حاسوب
# ============================================

account_120501 = Account.objects.create(
    company=company,
    code='120501',
    name='أجهزة حاسوب',
    name_en='Computers',
    account_type=assets_type,
    parent=account_1205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120502 = Account.objects.create(
    company=company,
    code='120502',
    name='أجهزة شبكات',
    name_en='Network Equipment',
    account_type=assets_type,
    parent=account_1205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120503 = Account.objects.create(
    company=company,
    code='120503',
    name='برامج حاسوب',
    name_en='Computer Software',
    account_type=assets_type,
    parent=account_1205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 1206 - مجمع الاستهلاك
# ============================================

account_120601 = Account.objects.create(
    company=company,
    code='120601',
    name='مجمع استهلاك المباني',
    name_en='Accumulated Depreciation - Buildings',
    account_type=assets_type,
    parent=account_1206,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120602 = Account.objects.create(
    company=company,
    code='120602',
    name='مجمع استهلاك السيارات',
    name_en='Accumulated Depreciation - Vehicles',
    account_type=assets_type,
    parent=account_1206,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120603 = Account.objects.create(
    company=company,
    code='120603',
    name='مجمع استهلاك الأثاث',
    name_en='Accumulated Depreciation - Furniture',
    account_type=assets_type,
    parent=account_1206,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_120604 = Account.objects.create(
    company=company,
    code='120604',
    name='مجمع استهلاك أجهزة الحاسوب',
    name_en='Accumulated Depreciation - Computers',
    account_type=assets_type,
    parent=account_1206,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# الخصوم المتداولة - التفاصيل
# رابع عشر: تحت 2101 - الذمم الدائنة

# ============================================
# تحت 2101 - الذمم الدائنة
# ============================================

account_210101 = Account.objects.create(
    company=company,
    code='210101',
    name='ذمم موردين - محلي',
    name_en='Accounts Payable - Local',
    account_type=liabilities_type,
    parent=account_2101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210102 = Account.objects.create(
    company=company,
    code='210102',
    name='ذمم موردين - خارجي',
    name_en='Accounts Payable - Foreign',
    account_type=liabilities_type,
    parent=account_2101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210103 = Account.objects.create(
    company=company,
    code='210103',
    name='أوراق دفع',
    name_en='Notes Payable',
    account_type=liabilities_type,
    parent=account_2101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210104 = Account.objects.create(
    company=company,
    code='210104',
    name='شيكات برسم الدفع',
    name_en='Checks Payable',
    account_type=liabilities_type,
    parent=account_2101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 2102 - مصروفات مستحقة
# ============================================

account_210201 = Account.objects.create(
    company=company,
    code='210201',
    name='إيجارات مستحقة',
    name_en='Rent Payable',
    account_type=liabilities_type,
    parent=account_2102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210202 = Account.objects.create(
    company=company,
    code='210202',
    name='مرافق مستحقة',
    name_en='Utilities Payable',
    account_type=liabilities_type,
    parent=account_2102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210203 = Account.objects.create(
    company=company,
    code='210203',
    name='فوائد مستحقة',
    name_en='Interest Payable',
    account_type=liabilities_type,
    parent=account_2102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210204 = Account.objects.create(
    company=company,
    code='210204',
    name='مصروفات مستحقة أخرى',
    name_en='Other Accrued Expenses',
    account_type=liabilities_type,
    parent=account_2102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 2103 - ضرائب مستحقة
# ============================================

account_210301 = Account.objects.create(
    company=company,
    code='210301',
    name='ضريبة الدخل المستحقة',
    name_en='Income Tax Payable',
    account_type=liabilities_type,
    parent=account_2103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210302 = Account.objects.create(
    company=company,
    code='210302',
    name='ضريبة المبيعات المستحقة',
    name_en='Sales Tax Payable',
    account_type=liabilities_type,
    parent=account_2103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210303 = Account.objects.create(
    company=company,
    code='210303',
    name='ضريبة المبيعات القابلة للاسترداد',
    name_en='VAT Recoverable',
    account_type=liabilities_type,
    parent=account_2103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210304 = Account.objects.create(
    company=company,
    code='210304',
    name='أمانة الجمارك',
    name_en='Customs Duties Payable',
    account_type=liabilities_type,
    parent=account_2103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 2104 - رواتب مستحقة
# ============================================

account_210401 = Account.objects.create(
    company=company,
    code='210401',
    name='رواتب موظفين مستحقة',
    name_en='Salaries Payable',
    account_type=liabilities_type,
    parent=account_2104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210402 = Account.objects.create(
    company=company,
    code='210402',
    name='ضمان اجتماعي مستحق',
    name_en='Social Security Payable',
    account_type=liabilities_type,
    parent=account_2104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210403 = Account.objects.create(
    company=company,
    code='210403',
    name='تأمين صحي مستحق',
    name_en='Health Insurance Payable',
    account_type=liabilities_type,
    parent=account_2104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210404 = Account.objects.create(
    company=company,
    code='210404',
    name='مكافآت نهاية الخدمة',
    name_en='End of Service Benefits',
    account_type=liabilities_type,
    parent=account_2104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 2105 - قروض قصيرة الأجل
# ============================================

account_210501 = Account.objects.create(
    company=company,
    code='210501',
    name='قروض بنكية قصيرة الأجل',
    name_en='Short-term Bank Loans',
    account_type=liabilities_type,
    parent=account_2105,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210502 = Account.objects.create(
    company=company,
    code='210502',
    name='سحب على المكشوف',
    name_en='Bank Overdraft',
    account_type=liabilities_type,
    parent=account_2105,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210503 = Account.objects.create(
    company=company,
    code='210503',
    name='أقساط قروض طويلة - جزء متداول',
    name_en='Current Portion of Long-term Loans',
    account_type=liabilities_type,
    parent=account_2105,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 2106 - إيرادات مقبوضة مقدماً
# ============================================

account_210601 = Account.objects.create(
    company=company,
    code='210601',
    name='دفعات مقدمة من عملاء',
    name_en='Customer Advances',
    account_type=liabilities_type,
    parent=account_2106,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_210602 = Account.objects.create(
    company=company,
    code='210602',
    name='أمانات عملاء',
    name_en='Customer Deposits',
    account_type=liabilities_type,
    parent=account_2106,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# الإيرادات - التفاصيل
# عشرون: تحت 4101 - مبيعات معدات صناعية

# ============================================
# تحت 4101 - مبيعات معدات صناعية
# ============================================

account_410101 = Account.objects.create(
    company=company,
    code='410101',
    name='مبيعات معدات صناعية - الفرع الرئيسي',
    name_en='Industrial Equipment Sales - Main Branch',
    account_type=revenue_type,
    parent=account_4101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410102 = Account.objects.create(
    company=company,
    code='410102',
    name='مبيعات معدات صناعية - فرع القسطل',
    name_en='Industrial Equipment Sales - Al-Qastal',
    account_type=revenue_type,
    parent=account_4101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410103 = Account.objects.create(
    company=company,
    code='410103',
    name='مبيعات معدات صناعية - فرع أبو علندا',
    name_en='Industrial Equipment Sales - Abu Alanda',
    account_type=revenue_type,
    parent=account_4101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410104 = Account.objects.create(
    company=company,
    code='410104',
    name='مبيعات معدات صناعية - فرع سحاب',
    name_en='Industrial Equipment Sales - Sahab',
    account_type=revenue_type,
    parent=account_4101,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 4102 - مبيعات مواد كيميائية
# ============================================

account_410201 = Account.objects.create(
    company=company,
    code='410201',
    name='مبيعات مواد كيميائية - جملة',
    name_en='Chemical Sales - Wholesale',
    account_type=revenue_type,
    parent=account_4102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410202 = Account.objects.create(
    company=company,
    code='410202',
    name='مبيعات مواد كيميائية - تجزئة',
    name_en='Chemical Sales - Retail',
    account_type=revenue_type,
    parent=account_4102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410203 = Account.objects.create(
    company=company,
    code='410203',
    name='مبيعات مواد تشحيم',
    name_en='Lubricant Sales',
    account_type=revenue_type,
    parent=account_4102,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 4103 - مبيعات قطع غيار
# ============================================

account_410301 = Account.objects.create(
    company=company,
    code='410301',
    name='مبيعات قطع غيار - الفرع الرئيسي',
    name_en='Spare Parts Sales - Main Branch',
    account_type=revenue_type,
    parent=account_4103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410302 = Account.objects.create(
    company=company,
    code='410302',
    name='مبيعات قطع غيار - فرع القسطل',
    name_en='Spare Parts Sales - Al-Qastal',
    account_type=revenue_type,
    parent=account_4103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410303 = Account.objects.create(
    company=company,
    code='410303',
    name='مبيعات قطع غيار - فرع أبو علندا',
    name_en='Spare Parts Sales - Abu Alanda',
    account_type=revenue_type,
    parent=account_4103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410304 = Account.objects.create(
    company=company,
    code='410304',
    name='مبيعات قطع غيار - فرع سحاب',
    name_en='Spare Parts Sales - Sahab',
    account_type=revenue_type,
    parent=account_4103,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 4104 - مبيعات أدوات ورشة
# ============================================

account_410401 = Account.objects.create(
    company=company,
    code='410401',
    name='مبيعات أدوات ورشة - جملة',
    name_en='Workshop Tools Sales - Wholesale',
    account_type=revenue_type,
    parent=account_4104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410402 = Account.objects.create(
    company=company,
    code='410402',
    name='مبيعات أدوات ورشة - تجزئة',
    name_en='Workshop Tools Sales - Retail',
    account_type=revenue_type,
    parent=account_4104,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 4105 - مردودات المبيعات
# ============================================

account_410501 = Account.objects.create(
    company=company,
    code='410501',
    name='مردودات مبيعات معدات صناعية',
    name_en='Industrial Equipment Returns',
    account_type=revenue_type,
    parent=account_4105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410502 = Account.objects.create(
    company=company,
    code='410502',
    name='مردودات مبيعات مواد كيميائية',
    name_en='Chemical Materials Returns',
    account_type=revenue_type,
    parent=account_4105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410503 = Account.objects.create(
    company=company,
    code='410503',
    name='مردودات مبيعات قطع غيار',
    name_en='Spare Parts Returns',
    account_type=revenue_type,
    parent=account_4105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 4106 - خصومات المبيعات
# ============================================

account_410601 = Account.objects.create(
    company=company,
    code='410601',
    name='خصومات نقدية',
    name_en='Cash Discounts',
    account_type=revenue_type,
    parent=account_4106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410602 = Account.objects.create(
    company=company,
    code='410602',
    name='خصومات كمية',
    name_en='Quantity Discounts',
    account_type=revenue_type,
    parent=account_4106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_410603 = Account.objects.create(
    company=company,
    code='410603',
    name='خصومات تجارية',
    name_en='Trade Discounts',
    account_type=revenue_type,
    parent=account_4106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 42 - إيرادات أخرى (مستوى 3)
# ============================================

account_4201 = Account.objects.create(
    company=company,
    code='4201',
    name='إيرادات مالية',
    name_en='Financial Income',
    account_type=revenue_type,
    parent=account_42,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

account_4202 = Account.objects.create(
    company=company,
    code='4202',
    name='إيرادات متنوعة',
    name_en='Miscellaneous Income',
    account_type=revenue_type,
    parent=account_42,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# المستوى 4 تحت إيرادات مالية
account_420101 = Account.objects.create(
    company=company,
    code='420101',
    name='فوائد بنكية دائنة',
    name_en='Bank Interest Income',
    account_type=revenue_type,
    parent=account_4201,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_420102 = Account.objects.create(
    company=company,
    code='420102',
    name='أرباح استثمارات',
    name_en='Investment Income',
    account_type=revenue_type,
    parent=account_4201,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_420103 = Account.objects.create(
    company=company,
    code='420103',
    name='أرباح فروقات عملة',
    name_en='Foreign Exchange Gains',
    account_type=revenue_type,
    parent=account_4201,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# المستوى 4 تحت إيرادات متنوعة
account_420201 = Account.objects.create(
    company=company,
    code='420201',
    name='إيرادات إيجارات',
    name_en='Rental Income',
    account_type=revenue_type,
    parent=account_4202,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_420202 = Account.objects.create(
    company=company,
    code='420202',
    name='أرباح بيع أصول ثابتة',
    name_en='Gain on Sale of Fixed Assets',
    account_type=revenue_type,
    parent=account_4202,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_420203 = Account.objects.create(
    company=company,
    code='420203',
    name='إيرادات متنوعة أخرى',
    name_en='Other Miscellaneous Income',
    account_type=revenue_type,
    parent=account_4202,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# تكلفة المبيعات - التفاصيل

# ============================================
# تحت 5101 - تكلفة معدات صناعية مباعة
# ============================================

account_510101 = Account.objects.create(
    company=company,
    code='510101',
    name='تكلفة معدات مباعة - الفرع الرئيسي',
    name_en='Cost of Equipment Sold - Main Branch',
    account_type=expenses_type,
    parent=account_5101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_510102 = Account.objects.create(
    company=company,
    code='510102',
    name='تكلفة معدات مباعة - فرع القسطل',
    name_en='Cost of Equipment Sold - Al-Qastal',
    account_type=expenses_type,
    parent=account_5101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_510103 = Account.objects.create(
    company=company,
    code='510103',
    name='تكلفة معدات مباعة - فرع أبو علندا',
    name_en='Cost of Equipment Sold - Abu Alanda',
    account_type=expenses_type,
    parent=account_5101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_510104 = Account.objects.create(
    company=company,
    code='510104',
    name='تكلفة معدات مباعة - فرع سحاب',
    name_en='Cost of Equipment Sold - Sahab',
    account_type=expenses_type,
    parent=account_5101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 5102 - تكلفة مواد كيميائية مباعة
# ============================================

account_510201 = Account.objects.create(
    company=company,
    code='510201',
    name='تكلفة مواد كيميائية مباعة',
    name_en='Cost of Chemicals Sold',
    account_type=expenses_type,
    parent=account_5102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_510202 = Account.objects.create(
    company=company,
    code='510202',
    name='تكلفة مواد تشحيم مباعة',
    name_en='Cost of Lubricants Sold',
    account_type=expenses_type,
    parent=account_5102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# ============================================
# تحت 5103 - تكلفة قطع غيار مباعة
# ============================================

account_510301 = Account.objects.create(
    company=company,
    code='510301',
    name='تكلفة قطع غيار مباعة',
    name_en='Cost of Spare Parts Sold',
    account_type=expenses_type,
    parent=account_5103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 5104 - تكلفة أدوات ورشة مباعة
# ============================================

account_510401 = Account.objects.create(
    company=company,
    code='510401',
    name='تكلفة أدوات ورشة مباعة',
    name_en='Cost of Workshop Tools Sold',
    account_type=expenses_type,
    parent=account_5104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# المصروفات - التفاصيل الكاملة
# واحد وثلاثون: تحت 6101 - رواتب وأجور

# ============================================
# تحت 6101 - رواتب وأجور
# ============================================

account_610101 = Account.objects.create(
    company=company,
    code='610101',
    name='رواتب الإدارة',
    name_en='Administrative Salaries',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610102 = Account.objects.create(
    company=company,
    code='610102',
    name='رواتب موظفي المبيعات',
    name_en='Sales Staff Salaries',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610103 = Account.objects.create(
    company=company,
    code='610103',
    name='رواتب العمال',
    name_en='Workers Wages',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610104 = Account.objects.create(
    company=company,
    code='610104',
    name='بدلات ومكافآت',
    name_en='Allowances and Bonuses',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610105 = Account.objects.create(
    company=company,
    code='610105',
    name='ضمان اجتماعي',
    name_en='Social Security',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610106 = Account.objects.create(
    company=company,
    code='610106',
    name='تأمين صحي',
    name_en='Health Insurance',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610107 = Account.objects.create(
    company=company,
    code='610107',
    name='ساعات إضافية',
    name_en='Overtime',
    account_type=expenses_type,
    parent=account_6101,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# ============================================
# تحت 6102 - إيجارات
# ============================================

account_610201 = Account.objects.create(
    company=company,
    code='610201',
    name='إيجار المكتب الرئيسي',
    name_en='Main Office Rent',
    account_type=expenses_type,
    parent=account_6102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610202 = Account.objects.create(
    company=company,
    code='610202',
    name='إيجار فرع القسطل',
    name_en='Al-Qastal Branch Rent',
    account_type=expenses_type,
    parent=account_6102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610203 = Account.objects.create(
    company=company,
    code='610203',
    name='إيجار فرع أبو علندا',
    name_en='Abu Alanda Branch Rent',
    account_type=expenses_type,
    parent=account_6102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610204 = Account.objects.create(
    company=company,
    code='610204',
    name='إيجار فرع سحاب',
    name_en='Sahab Branch Rent',
    account_type=expenses_type,
    parent=account_6102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610205 = Account.objects.create(
    company=company,
    code='610205',
    name='إيجار مستودعات',
    name_en='Warehouse Rent',
    account_type=expenses_type,
    parent=account_6102,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 6103 - مرافق عامة
# ============================================

account_610301 = Account.objects.create(
    company=company,
    code='610301',
    name='كهرباء',
    name_en='Electricity',
    account_type=expenses_type,
    parent=account_6103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610302 = Account.objects.create(
    company=company,
    code='610302',
    name='ماء',
    name_en='Water',
    account_type=expenses_type,
    parent=account_6103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610303 = Account.objects.create(
    company=company,
    code='610303',
    name='تدفئة وتبريد',
    name_en='Heating and Cooling',
    account_type=expenses_type,
    parent=account_6103,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# ============================================
# تحت 6104 - اتصالات
# ============================================

account_610401 = Account.objects.create(
    company=company,
    code='610401',
    name='هاتف أرضي',
    name_en='Landline Phone',
    account_type=expenses_type,
    parent=account_6104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610402 = Account.objects.create(
    company=company,
    code='610402',
    name='هاتف خلوي',
    name_en='Mobile Phone',
    account_type=expenses_type,
    parent=account_6104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610403 = Account.objects.create(
    company=company,
    code='610403',
    name='إنترنت',
    name_en='Internet',
    account_type=expenses_type,
    parent=account_6104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610404 = Account.objects.create(
    company=company,
    code='610404',
    name='بريد وشحن مستندات',
    name_en='Postage and Courier',
    account_type=expenses_type,
    parent=account_6104,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 6105 - قرطاسية ومطبوعات
# ============================================

account_610501 = Account.objects.create(
    company=company,
    code='610501',
    name='قرطاسية',
    name_en='Stationery',
    account_type=expenses_type,
    parent=account_6105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610502 = Account.objects.create(
    company=company,
    code='610502',
    name='مطبوعات',
    name_en='Printing',
    account_type=expenses_type,
    parent=account_6105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610503 = Account.objects.create(
    company=company,
    code='610503',
    name='كتالوجات وبروشورات',
    name_en='Catalogs and Brochures',
    account_type=expenses_type,
    parent=account_6105,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6106 - تأمينات
# ============================================

account_610601 = Account.objects.create(
    company=company,
    code='610601',
    name='تأمين المباني',
    name_en='Building Insurance',
    account_type=expenses_type,
    parent=account_6106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610602 = Account.objects.create(
    company=company,
    code='610602',
    name='تأمين السيارات',
    name_en='Vehicle Insurance',
    account_type=expenses_type,
    parent=account_6106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610603 = Account.objects.create(
    company=company,
    code='610603',
    name='تأمين المخزون',
    name_en='Inventory Insurance',
    account_type=expenses_type,
    parent=account_6106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610604 = Account.objects.create(
    company=company,
    code='610604',
    name='تأمين المسؤولية',
    name_en='Liability Insurance',
    account_type=expenses_type,
    parent=account_6106,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6107 - استشارات مهنية
# ============================================

account_610701 = Account.objects.create(
    company=company,
    code='610701',
    name='أتعاب محاسبية ومراجعة',
    name_en='Accounting and Audit Fees',
    account_type=expenses_type,
    parent=account_6107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610702 = Account.objects.create(
    company=company,
    code='610702',
    name='أتعاب قانونية',
    name_en='Legal Fees',
    account_type=expenses_type,
    parent=account_6107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610703 = Account.objects.create(
    company=company,
    code='610703',
    name='استشارات إدارية',
    name_en='Management Consulting',
    account_type=expenses_type,
    parent=account_6107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610704 = Account.objects.create(
    company=company,
    code='610704',
    name='استشارات فنية',
    name_en='Technical Consulting',
    account_type=expenses_type,
    parent=account_6107,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# ============================================
# تحت 6108 - ضيافة
# ============================================

account_610801 = Account.objects.create(
    company=company,
    code='610801',
    name='ضيافة داخلية',
    name_en='Internal Hospitality',
    account_type=expenses_type,
    parent=account_6108,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610802 = Account.objects.create(
    company=company,
    code='610802',
    name='ضيافة عملاء',
    name_en='Client Entertainment',
    account_type=expenses_type,
    parent=account_6108,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6201 - نقل وشحن
# ============================================

account_620101 = Account.objects.create(
    company=company,
    code='620101',
    name='نقل محلي',
    name_en='Local Transportation',
    account_type=expenses_type,
    parent=account_6201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620102 = Account.objects.create(
    company=company,
    code='620102',
    name='شحن دولي',
    name_en='International Shipping',
    account_type=expenses_type,
    parent=account_6201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620103 = Account.objects.create(
    company=company,
    code='620103',
    name='نقل داخلي بين الفروع',
    name_en='Inter-branch Transfer',
    account_type=expenses_type,
    parent=account_6201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620104 = Account.objects.create(
    company=company,
    code='620104',
    name='تفريغ وتحميل',
    name_en='Loading and Unloading',
    account_type=expenses_type,
    parent=account_6201,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6202 - صيانة وإصلاحات
# ============================================

account_620201 = Account.objects.create(
    company=company,
    code='620201',
    name='صيانة المباني',
    name_en='Building Maintenance',
    account_type=expenses_type,
    parent=account_6202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620202 = Account.objects.create(
    company=company,
    code='620202',
    name='صيانة السيارات',
    name_en='Vehicle Maintenance',
    account_type=expenses_type,
    parent=account_6202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620203 = Account.objects.create(
    company=company,
    code='620203',
    name='صيانة أجهزة الحاسوب',
    name_en='Computer Maintenance',
    account_type=expenses_type,
    parent=account_6202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620204 = Account.objects.create(
    company=company,
    code='620204',
    name='صيانة عامة',
    name_en='General Maintenance',
    account_type=expenses_type,
    parent=account_6202,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6203 - مصاريف تخزين
# ============================================

account_620301 = Account.objects.create(
    company=company,
    code='620301',
    name='إيجار مستودعات',
    name_en='Warehouse Rental',
    account_type=expenses_type,
    parent=account_6203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620302 = Account.objects.create(
    company=company,
    code='620302',
    name='حراسة وأمن مستودعات',
    name_en='Warehouse Security',
    account_type=expenses_type,
    parent=account_6203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620303 = Account.objects.create(
    company=company,
    code='620303',
    name='رسوم تخزين في الموانئ',
    name_en='Port Storage Fees',
    account_type=expenses_type,
    parent=account_6203,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6204 - وقود ومحروقات
# ============================================

account_620401 = Account.objects.create(
    company=company,
    code='620401',
    name='وقود السيارات',
    name_en='Vehicle Fuel',
    account_type=expenses_type,
    parent=account_6204,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620402 = Account.objects.create(
    company=company,
    code='620402',
    name='زيوت ومواد تشحيم',
    name_en='Oils and Lubricants',
    account_type=expenses_type,
    parent=account_6204,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6205 - جمارك ورسوم استيراد
# ============================================

account_620501 = Account.objects.create(
    company=company,
    code='620501',
    name='رسوم جمركية',
    name_en='Customs Duties',
    account_type=expenses_type,
    parent=account_6205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620502 = Account.objects.create(
    company=company,
    code='620502',
    name='رسوم تخليص جمركي',
    name_en='Customs Clearance Fees',
    account_type=expenses_type,
    parent=account_6205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620503 = Account.objects.create(
    company=company,
    code='620503',
    name='رسوم موانئ',
    name_en='Port Fees',
    account_type=expenses_type,
    parent=account_6205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620504 = Account.objects.create(
    company=company,
    code='620504',
    name='مصاريف اعتمادات مستندية',
    name_en='LC Charges',
    account_type=expenses_type,
    parent=account_6205,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# ============================================
# تحت 6206 - تأمين بضائع
# ============================================

account_620601 = Account.objects.create(
    company=company,
    code='620601',
    name='تأمين بضائع مستوردة',
    name_en='Imported Goods Insurance',
    account_type=expenses_type,
    parent=account_6206,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_620602 = Account.objects.create(
    company=company,
    code='620602',
    name='تأمين بضائع محلية',
    name_en='Local Goods Insurance',
    account_type=expenses_type,
    parent=account_6206,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6301 - إعلانات ودعاية
# ============================================

account_630101 = Account.objects.create(
    company=company,
    code='630101',
    name='إعلانات صحف ومجلات',
    name_en='Newspaper and Magazine Ads',
    account_type=expenses_type,
    parent=account_6301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630102 = Account.objects.create(
    company=company,
    code='630102',
    name='إعلانات إلكترونية',
    name_en='Digital Advertising',
    account_type=expenses_type,
    parent=account_6301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630103 = Account.objects.create(
    company=company,
    code='630103',
    name='إعلانات تلفزيونية وإذاعية',
    name_en='TV and Radio Ads',
    account_type=expenses_type,
    parent=account_6301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630104 = Account.objects.create(
    company=company,
    code='630104',
    name='لافتات ولوحات إعلانية',
    name_en='Billboards and Signage',
    account_type=expenses_type,
    parent=account_6301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 6302 - عمولات مبيعات
# ============================================

account_630201 = Account.objects.create(
    company=company,
    code='630201',
    name='عمولات مندوبي مبيعات',
    name_en='Sales Representatives Commissions',
    account_type=expenses_type,
    parent=account_6302,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630202 = Account.objects.create(
    company=company,
    code='630202',
    name='عمولات وكلاء',
    name_en='Agents Commissions',
    account_type=expenses_type,
    parent=account_6302,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6303 - مصاريف معارض
# ============================================

account_630301 = Account.objects.create(
    company=company,
    code='630301',
    name='إيجار أجنحة معارض',
    name_en='Exhibition Booth Rental',
    account_type=expenses_type,
    parent=account_6303,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630302 = Account.objects.create(
    company=company,
    code='630302',
    name='تجهيز أجنحة معارض',
    name_en='Booth Setup',
    account_type=expenses_type,
    parent=account_6303,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630303 = Account.objects.create(
    company=company,
    code='630303',
    name='مصاريف سفر للمعارض',
    name_en='Exhibition Travel Expenses',
    account_type=expenses_type,
    parent=account_6303,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6304 - هدايا ودعاية
# ============================================

account_630401 = Account.objects.create(
    company=company,
    code='630401',
    name='هدايا عملاء',
    name_en='Customer Gifts',
    account_type=expenses_type,
    parent=account_6304,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_630402 = Account.objects.create(
    company=company,
    code='630402',
    name='مواد دعائية',
    name_en='Promotional Materials',
    account_type=expenses_type,
    parent=account_6304,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6401 - فوائد بنكية
# ============================================

account_640101 = Account.objects.create(
    company=company,
    code='640101',
    name='فوائد قروض',
    name_en='Loan Interest',
    account_type=expenses_type,
    parent=account_6401,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640102 = Account.objects.create(
    company=company,
    code='640102',
    name='فوائد سحب على المكشوف',
    name_en='Overdraft Interest',
    account_type=expenses_type,
    parent=account_6401,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640103 = Account.objects.create(
    company=company,
    code='640103',
    name='فوائد اعتمادات مستندية',
    name_en='LC Interest',
    account_type=expenses_type,
    parent=account_6401,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6402 - عمولات بنكية
# ============================================

account_640201 = Account.objects.create(
    company=company,
    code='640201',
    name='عمولات تحويلات',
    name_en='Transfer Commissions',
    account_type=expenses_type,
    parent=account_6402,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640202 = Account.objects.create(
    company=company,
    code='640202',
    name='عمولات اعتمادات مستندية',
    name_en='LC Commissions',
    account_type=expenses_type,
    parent=account_6402,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640203 = Account.objects.create(
    company=company,
    code='640203',
    name='عمولات خدمات بنكية',
    name_en='Bank Service Charges',
    account_type=expenses_type,
    parent=account_6402,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640204 = Account.objects.create(
    company=company,
    code='640204',
    name='عمولات شيكات',
    name_en='Check Fees',
    account_type=expenses_type,
    parent=account_6402,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6403 - فروقات عملة
# ============================================

account_640301 = Account.objects.create(
    company=company,
    code='640301',
    name='خسائر فروقات عملة',
    name_en='Foreign Exchange Losses',
    account_type=expenses_type,
    parent=account_6403,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640302 = Account.objects.create(
    company=company,
    code='640302',
    name='أرباح فروقات عملة',
    name_en='Foreign Exchange Gains',
    account_type=expenses_type,
    parent=account_6403,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 6404 - ديون معدومة
# ============================================

account_640401 = Account.objects.create(
    company=company,
    code='640401',
    name='ديون معدومة',
    name_en='Bad Debts Written Off',
    account_type=expenses_type,
    parent=account_6404,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_640402 = Account.objects.create(
    company=company,
    code='640402',
    name='مخصص ديون مشكوك فيها',
    name_en='Provision for Doubtful Debts',
    account_type=expenses_type,
    parent=account_6404,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)



# حسابات إضافية مهمة
# ثلاثة وخمسون: حسابات إضافية في حقوق الملكية

# ============================================
# تفاصيل حقوق الملكية
# ============================================

# تحت 31 - رأس المال
account_310101 = Account.objects.create(
    company=company,
    code='310101',
    name='رأس المال المدفوع',
    name_en='Paid-up Capital',
    account_type=equity_type,
    parent=account_31,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_310102 = Account.objects.create(
    company=company,
    code='310102',
    name='رأس المال غير المدفوع',
    name_en='Unpaid Capital',
    account_type=equity_type,
    parent=account_31,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# تحت 32 - الأرباح المحتجزة
account_320101 = Account.objects.create(
    company=company,
    code='320101',
    name='أرباح محتجزة من سنوات سابقة',
    name_en='Retained Earnings - Prior Years',
    account_type=equity_type,
    parent=account_32,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_320102 = Account.objects.create(
    company=company,
    code='320102',
    name='أرباح العام الحالي',
    name_en='Current Year Profit',
    account_type=equity_type,
    parent=account_32,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_320103 = Account.objects.create(
    company=company,
    code='320103',
    name='خسائر متراكمة',
    name_en='Accumulated Losses',
    account_type=equity_type,
    parent=account_32,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# تحت 33 - الاحتياطيات
account_330101 = Account.objects.create(
    company=company,
    code='330101',
    name='احتياطي نظامي',
    name_en='Statutory Reserve',
    account_type=equity_type,
    parent=account_33,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_330102 = Account.objects.create(
    company=company,
    code='330102',
    name='احتياطي اختياري',
    name_en='Optional Reserve',
    account_type=equity_type,
    parent=account_33,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_330103 = Account.objects.create(
    company=company,
    code='330103',
    name='احتياطي طوارئ',
    name_en='Contingency Reserve',
    account_type=equity_type,
    parent=account_33,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# تحت 22 - الخصوم طويلة الأجل (مستوى 3)
# ============================================

account_2201 = Account.objects.create(
    company=company,
    code='2201',
    name='قروض طويلة الأجل',
    name_en='Long-term Loans',
    account_type=liabilities_type,
    parent=account_22,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

account_2202 = Account.objects.create(
    company=company,
    code='2202',
    name='مخصصات طويلة الأجل',
    name_en='Long-term Provisions',
    account_type=liabilities_type,
    parent=account_22,
    currency=currency,
    nature='credit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# المستوى 4
account_220101 = Account.objects.create(
    company=company,
    code='220101',
    name='قروض بنكية طويلة الأجل',
    name_en='Long-term Bank Loans',
    account_type=liabilities_type,
    parent=account_2201,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_220102 = Account.objects.create(
    company=company,
    code='220102',
    name='قروض من شركاء',
    name_en='Partners Loans',
    account_type=liabilities_type,
    parent=account_2201,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_220201 = Account.objects.create(
    company=company,
    code='220201',
    name='مخصص مكافآت نهاية الخدمة',
    name_en='End of Service Provision',
    account_type=liabilities_type,
    parent=account_2202,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_220202 = Account.objects.create(
    company=company,
    code='220202',
    name='مخصصات أخرى',
    name_en='Other Provisions',
    account_type=liabilities_type,
    parent=account_2202,
    currency=currency,
    nature='credit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ============================================
# تحت 13 - أصول أخرى (مستوى 3)
# ============================================

account_1301 = Account.objects.create(
    company=company,
    code='1301',
    name='استثمارات طويلة الأجل',
    name_en='Long-term Investments',
    account_type=assets_type,
    parent=account_13,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

account_1302 = Account.objects.create(
    company=company,
    code='1302',
    name='أصول غير ملموسة',
    name_en='Intangible Assets',
    account_type=assets_type,
    parent=account_13,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# المستوى 4
account_130101 = Account.objects.create(
    company=company,
    code='130101',
    name='استثمارات في شركات تابعة',
    name_en='Investments in Subsidiaries',
    account_type=assets_type,
    parent=account_1301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_130102 = Account.objects.create(
    company=company,
    code='130102',
    name='استثمارات في شركات شقيقة',
    name_en='Investments in Associates',
    account_type=assets_type,
    parent=account_1301,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_130201 = Account.objects.create(
    company=company,
    code='130201',
    name='شهرة',
    name_en='Goodwill',
    account_type=assets_type,
    parent=account_1302,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_130202 = Account.objects.create(
    company=company,
    code='130202',
    name='علامات تجارية',
    name_en='Trademarks',
    account_type=assets_type,
    parent=account_1302,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_130203 = Account.objects.create(
    company=company,
    code='130203',
    name='حقوق ملكية فكرية',
    name_en='Intellectual Property Rights',
    account_type=assets_type,
    parent=account_1302,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

# ============================================
# مصروفات إدارية إضافية
# ============================================

# نحتاج مستوى 3 جديد تحت 61
account_6109 = Account.objects.create(
    company=company,
    code='6109',
    name='مصروفات إدارية أخرى',
    name_en='Other Administrative Expenses',
    account_type=expenses_type,
    parent=account_61,
    currency=currency,
    nature='debit',
    can_have_children=True,
    accept_entries=False,
    level=3
)

# المستوى 4
account_610901 = Account.objects.create(
    company=company,
    code='610901',
    name='تبرعات',
    name_en='Donations',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610902 = Account.objects.create(
    company=company,
    code='610902',
    name='اشتراكات وعضويات',
    name_en='Subscriptions and Memberships',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610903 = Account.objects.create(
    company=company,
    code='610903',
    name='تدريب وتطوير',
    name_en='Training and Development',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610904 = Account.objects.create(
    company=company,
    code='610904',
    name='رسوم حكومية',
    name_en='Government Fees',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610905 = Account.objects.create(
    company=company,
    code='610905',
    name='رخص وتصاريح',
    name_en='Licenses and Permits',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610906 = Account.objects.create(
    company=company,
    code='610906',
    name='نظافة وتعقيم',
    name_en='Cleaning and Sanitation',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610907 = Account.objects.create(
    company=company,
    code='610907',
    name='أمن وحراسة',
    name_en='Security and Guarding',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610908 = Account.objects.create(
    company=company,
    code='610908',
    name='مصروفات سفر',
    name_en='Travel Expenses',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610909 = Account.objects.create(
    company=company,
    code='610909',
    name='استهلاك الأصول الثابتة',
    name_en='Depreciation Expense',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)

account_610910 = Account.objects.create(
    company=company,
    code='610910',
    name='إطفاء الأصول غير الملموسة',
    name_en='Amortization Expense',
    account_type=expenses_type,
    parent=account_6109,
    currency=currency,
    nature='debit',
    can_have_children=False,
    accept_entries=True,
    level=4
)


# ==========================================
# إعداد البيئة وتحميل المكتبات
# ==========================================

from apps.accounting.models import FiscalYear, AccountingPeriod, JournalEntry, JournalEntryLine, Account
from apps.core.models import Company, Currency, User, Branch
from decimal import Decimal
from datetime import date
from django.db import connection

# ==========================================
# الخطوة 1: إنشاء السنة المالية 2025
# ==========================================

company = Company.objects.first()

fiscal_year_2025 = FiscalYear.objects.create(
    company=company,
    name='السنة المالية 2025',
    code='FY2025',
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    is_closed=False
)

print(f"✅ تم إنشاء السنة المالية: {fiscal_year_2025.name}")

# ==========================================
# الخطوة 2: إنشاء الفترات المحاسبية (12 شهر)
# ==========================================

period_jan = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='يناير 2025',
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    is_closed=False,
    is_adjustment=False
)

period_feb = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='فبراير 2025',
    start_date=date(2025, 2, 1),
    end_date=date(2025, 2, 28),
    is_closed=False,
    is_adjustment=False
)

period_mar = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='مارس 2025',
    start_date=date(2025, 3, 1),
    end_date=date(2025, 3, 31),
    is_closed=False,
    is_adjustment=False
)

period_apr = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='أبريل 2025',
    start_date=date(2025, 4, 1),
    end_date=date(2025, 4, 30),
    is_closed=False,
    is_adjustment=False
)

period_may = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='مايو 2025',
    start_date=date(2025, 5, 1),
    end_date=date(2025, 5, 31),
    is_closed=False,
    is_adjustment=False
)

period_jun = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='يونيو 2025',
    start_date=date(2025, 6, 1),
    end_date=date(2025, 6, 30),
    is_closed=False,
    is_adjustment=False
)

period_jul = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='يوليو 2025',
    start_date=date(2025, 7, 1),
    end_date=date(2025, 7, 31),
    is_closed=False,
    is_adjustment=False
)

period_aug = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='أغسطس 2025',
    start_date=date(2025, 8, 1),
    end_date=date(2025, 8, 31),
    is_closed=False,
    is_adjustment=False
)

period_sep = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='سبتمبر 2025',
    start_date=date(2025, 9, 1),
    end_date=date(2025, 9, 30),
    is_closed=False,
    is_adjustment=False
)

period_oct = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='أكتوبر 2025',
    start_date=date(2025, 10, 1),
    end_date=date(2025, 10, 31),
    is_closed=False,
    is_adjustment=False
)

period_nov = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='نوفمبر 2025',
    start_date=date(2025, 11, 1),
    end_date=date(2025, 11, 30),
    is_closed=False,
    is_adjustment=False
)

period_dec = AccountingPeriod.objects.create(
    company=company,
    fiscal_year=fiscal_year_2025,
    name='ديسمبر 2025',
    start_date=date(2025, 12, 1),
    end_date=date(2025, 12, 31),
    is_closed=False,
    is_adjustment=False
)

print("✅ تم إنشاء 12 فترة محاسبية")

# ==========================================
# الخطوة 3: إنشاء قيد الأرصدة الافتتاحية
# ==========================================

currency = Currency.objects.get(code='JOD')
user = User.objects.first()
branch = Branch.objects.first()

opening_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 1),
    entry_type='opening',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='الأرصدة الافتتاحية للسنة المالية 2025',
    reference='OPEN-2025',
    created_by=user
)

print(f"✅ تم إنشاء القيد: {opening_entry.id} - {opening_entry.number}")

# ==========================================
# الخطوة 4: تحميل الحسابات
# ==========================================

account_cash_main = Account.objects.get(company=company, code='110101')
account_cash_qastal = Account.objects.get(company=company, code='110102')
account_bank_islamic = Account.objects.get(company=company, code='110105')
account_bank_arab = Account.objects.get(company=company, code='110106')
account_receivable = Account.objects.get(company=company, code='110201')
account_inventory_equipment = Account.objects.get(company=company, code='110301')
account_inventory_chemical = Account.objects.get(company=company, code='110302')
account_building = Account.objects.get(company=company, code='120201')
account_vehicles = Account.objects.get(company=company, code='120301')
account_furniture = Account.objects.get(company=company, code='120401')
account_payable = Account.objects.get(company=company, code='210101')
account_loan = Account.objects.get(company=company, code='220101')
account_capital = Account.objects.get(company=company, code='310101')
account_retained = Account.objects.get(company=company, code='320101')

# ==========================================
# الخطوة 5: إضافة سطور القيد
# ==========================================

# الأصول (مدين)
JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=1, account=account_cash_main, description='رصيد افتتاحي - الصندوق الرئيسي', debit_amount=Decimal('5000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=2, account=account_cash_qastal, description='رصيد افتتاحي - صندوق القسطل', debit_amount=Decimal('3000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=3, account=account_bank_islamic, description='رصيد افتتاحي - البنك الإسلامي', debit_amount=Decimal('150000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=4, account=account_bank_arab, description='رصيد افتتاحي - البنك العربي', debit_amount=Decimal('80000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=5, account=account_receivable, description='رصيد افتتاحي - ذمم عملاء', debit_amount=Decimal('45000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=6, account=account_inventory_equipment, description='رصيد افتتاحي - مخزون معدات', debit_amount=Decimal('120000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=7, account=account_inventory_chemical, description='رصيد افتتاحي - مخزون كيماويات', debit_amount=Decimal('35000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=8, account=account_building, description='رصيد افتتاحي - المبنى الرئيسي', debit_amount=Decimal('200000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=9, account=account_vehicles, description='رصيد افتتاحي - السيارات', debit_amount=Decimal('50000.000'), credit_amount=Decimal('0.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=10, account=account_furniture, description='رصيد افتتاحي - الأثاث المكتبي', debit_amount=Decimal('40000.000'), credit_amount=Decimal('0.000'), currency=currency)

# الخصوم وحقوق الملكية (دائن)
JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=11, account=account_payable, description='رصيد افتتاحي - ذمم موردين', debit_amount=Decimal('0.000'), credit_amount=Decimal('60000.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=12, account=account_loan, description='رصيد افتتاحي - قرض بنكي', debit_amount=Decimal('0.000'), credit_amount=Decimal('100000.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=13, account=account_capital, description='رصيد افتتاحي - رأس المال', debit_amount=Decimal('0.000'), credit_amount=Decimal('500000.000'), currency=currency)

JournalEntryLine.objects.create(journal_entry=opening_entry, line_number=14, account=account_retained, description='رصيد افتتاحي - أرباح محتجزة', debit_amount=Decimal('0.000'), credit_amount=Decimal('68000.000'), currency=currency)

print("✅ تم إضافة 14 سطر")

# ==========================================
# الخطوة 6: التحقق والترحيل
# ==========================================

opening_entry.calculate_totals()
print(f"\nالمدين: {opening_entry.total_debit}")
print(f"الدائن: {opening_entry.total_credit}")
print(f"متوازن: {opening_entry.is_balanced}")

if opening_entry.is_balanced:
    opening_entry.post(user=user)
    print(f"\n✅ تم ترحيل قيد الأرصدة الافتتاحية بنجاح")
    print(f"رقم القيد: {opening_entry.number}")
else:
    print("\n❌ القيد غير متوازن!")

# ==========================================
# الخطوة 7: التحقق النهائي
# ==========================================

print("\n" + "="*60)
print("📊 ملخص النتائج النهائية")
print("="*60)
print(f"السنة المالية: {fiscal_year_2025.name}")
print(f"عدد الفترات: {AccountingPeriod.objects.filter(fiscal_year=fiscal_year_2025).count()}")
print(f"رقم القيد: {opening_entry.number}")
print(f"حالة القيد: {opening_entry.get_status_display()}")
print(f"عدد السطور: {opening_entry.lines.count()}")
print(f"إجمالي المدين: {opening_entry.total_debit:,.2f} دينار")
print(f"إجمالي الدائن: {opening_entry.total_credit:,.2f} دينار")
print("="*60)
print("✅ تم إنشاء السيناريو الكامل بنجاح!")









# 2 -----


# ==========================================
# عمليات شهر يناير 2025
# ==========================================

from apps.accounting.models import JournalEntry, JournalEntryLine, Account
from apps.core.models import Company, Currency, User, Branch
from apps.accounting.models import FiscalYear, AccountingPeriod
from decimal import Decimal
from datetime import date

# البيانات الأساسية
company = Company.objects.first()
currency = Currency.objects.get(code='JOD')
user = User.objects.first()
branch = Branch.objects.first()
fiscal_year_2025 = FiscalYear.objects.get(company=company, code='FY2025')
period_jan = AccountingPeriod.objects.get(fiscal_year=fiscal_year_2025, name='يناير 2025')

# ==========================================
# العملية 1: شراء بضاعة بالآجل (5 يناير)
# ==========================================

purchase_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 5),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='شراء معدات صناعية من مورد محلي',
    reference='PUR-2025-001',
    created_by=user
)

account_inventory = Account.objects.get(company=company, code='110301')
account_payable = Account.objects.get(company=company, code='210101')

JournalEntryLine.objects.create(journal_entry=purchase_entry, line_number=1, account=account_inventory, description='شراء معدات صناعية', debit_amount=Decimal('25000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=purchase_entry, line_number=2, account=account_payable, description='شراء من المورد', debit_amount=Decimal('0.000'), credit_amount=Decimal('25000.000'), currency=currency)

purchase_entry.calculate_totals()
purchase_entry.post(user=user)
print(f"✅ عملية 1: {purchase_entry.number}")


# ==========================================
# العملية 2: بيع نقدي (8 يناير)
# ==========================================

sales_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 8),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='بيع معدات صناعية نقداً',
    reference='SALE-2025-001',
    created_by=user
)

account_cash = Account.objects.get(company=company, code='110101')
account_sales = Account.objects.get(company=company, code='410101')

JournalEntryLine.objects.create(journal_entry=sales_entry, line_number=1, account=account_cash, description='بيع نقدي', debit_amount=Decimal('15000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=sales_entry, line_number=2, account=account_sales, description='مبيعات معدات', debit_amount=Decimal('0.000'), credit_amount=Decimal('15000.000'), currency=currency)

sales_entry.calculate_totals()
sales_entry.post(user=user)

# قيد التكلفة
cost_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 8),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='تكلفة معدات مباعة',
    reference='COST-2025-001',
    created_by=user
)

account_cost = Account.objects.get(company=company, code='510101')

JournalEntryLine.objects.create(journal_entry=cost_entry, line_number=1, account=account_cost, description='تكلفة البضاعة المباعة', debit_amount=Decimal('10000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=cost_entry, line_number=2, account=account_inventory, description='إخراج من المخزون', debit_amount=Decimal('0.000'), credit_amount=Decimal('10000.000'), currency=currency)

cost_entry.calculate_totals()
cost_entry.post(user=user)
print(f"✅ عملية 2: {sales_entry.number} + {cost_entry.number}")

# ==========================================
# العملية 3: دفع إيجار (10 يناير)
# ==========================================

rent_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 10),
    entry_type='manual',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='دفع إيجار المكتب الرئيسي - يناير',
    reference='RENT-JAN-2025',
    created_by=user
)

account_rent = Account.objects.get(company=company, code='610201')
account_bank = Account.objects.get(company=company, code='110105')

JournalEntryLine.objects.create(journal_entry=rent_entry, line_number=1, account=account_rent, description='إيجار يناير', debit_amount=Decimal('2500.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=rent_entry, line_number=2, account=account_bank, description='دفع من البنك', debit_amount=Decimal('0.000'), credit_amount=Decimal('2500.000'), currency=currency)

rent_entry.calculate_totals()
rent_entry.post(user=user)
print(f"✅ عملية 3: {rent_entry.number}")

# ==========================================
# العملية 4: دفع رواتب (31 يناير)
# ==========================================

salary_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 31),
    entry_type='manual',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='رواتب وأجور يناير 2025',
    reference='SAL-JAN-2025',
    created_by=user
)

account_salaries = Account.objects.get(company=company, code='610101')
account_social = Account.objects.get(company=company, code='610105')
account_health = Account.objects.get(company=company, code='610106')
account_bank2 = Account.objects.get(company=company, code='110106')

JournalEntryLine.objects.create(journal_entry=salary_entry, line_number=1, account=account_salaries, description='رواتب يناير', debit_amount=Decimal('18000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=salary_entry, line_number=2, account=account_social, description='ضمان اجتماعي', debit_amount=Decimal('1260.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=salary_entry, line_number=3, account=account_health, description='تأمين صحي', debit_amount=Decimal('900.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=salary_entry, line_number=4, account=account_bank2, description='دفع رواتب', debit_amount=Decimal('0.000'), credit_amount=Decimal('20160.000'), currency=currency)

salary_entry.calculate_totals()
salary_entry.post(user=user)
print(f"✅ عملية 4: {salary_entry.number}")

# ==========================================
# العملية 5: تحصيل من عميل (15 يناير)
# ==========================================

collection_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 15),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='تحصيل من عميل',
    reference='COLL-2025-001',
    created_by=user
)

account_receivable = Account.objects.get(company=company, code='110201')

JournalEntryLine.objects.create(journal_entry=collection_entry, line_number=1, account=account_bank, description='تحصيل من عميل', debit_amount=Decimal('12000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=collection_entry, line_number=2, account=account_receivable, description='تسديد دين عميل', debit_amount=Decimal('0.000'), credit_amount=Decimal('12000.000'), currency=currency)

collection_entry.calculate_totals()
collection_entry.post(user=user)
print(f"✅ عملية 5: {collection_entry.number}")

# ==========================================
# العملية 6: دفع لمورد (20 يناير)
# ==========================================

payment_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 20),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='دفع لمورد',
    reference='PAY-2025-001',
    created_by=user
)

JournalEntryLine.objects.create(journal_entry=payment_entry, line_number=1, account=account_payable, description='دفع لمورد', debit_amount=Decimal('20000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=payment_entry, line_number=2, account=account_bank, description='دفع بشيك', debit_amount=Decimal('0.000'), credit_amount=Decimal('20000.000'), currency=currency)

payment_entry.calculate_totals()
payment_entry.post(user=user)
print(f"✅ عملية 6: {payment_entry.number}")

# ==========================================
# العملية 7: بيع بالآجل (25 يناير)
# ==========================================

credit_sales = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 25),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='بيع بالآجل',
    reference='SALE-2025-002',
    created_by=user
)

JournalEntryLine.objects.create(journal_entry=credit_sales, line_number=1, account=account_receivable, description='بيع آجل', debit_amount=Decimal('22000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=credit_sales, line_number=2, account=account_sales, description='مبيعات آجلة', debit_amount=Decimal('0.000'), credit_amount=Decimal('22000.000'), currency=currency)

credit_sales.calculate_totals()
credit_sales.post(user=user)

credit_cost = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 25),
    entry_type='auto',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='تكلفة البيع الآجل',
    reference='COST-2025-002',
    created_by=user
)

JournalEntryLine.objects.create(journal_entry=credit_cost, line_number=1, account=account_cost, description='تكلفة البضاعة', debit_amount=Decimal('15000.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=credit_cost, line_number=2, account=account_inventory, description='إخراج من المخزون', debit_amount=Decimal('0.000'), credit_amount=Decimal('15000.000'), currency=currency)

credit_cost.calculate_totals()
credit_cost.post(user=user)
print(f"✅ عملية 7: {credit_sales.number} + {credit_cost.number}")

# ==========================================
# العملية 8: دفع مصاريف (28 يناير)
# ==========================================

expenses_entry = JournalEntry.objects.create(
    company=company,
    branch=branch,
    entry_date=date(2025, 1, 28),
    entry_type='manual',
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    description='دفع مصاريف كهرباء وهاتف',
    reference='EXP-JAN-2025',
    created_by=user
)

account_electric = Account.objects.get(company=company, code='610301')
account_phone = Account.objects.get(company=company, code='610401')

JournalEntryLine.objects.create(journal_entry=expenses_entry, line_number=1, account=account_electric, description='كهرباء يناير', debit_amount=Decimal('850.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=expenses_entry, line_number=2, account=account_phone, description='هاتف يناير', debit_amount=Decimal('320.000'), credit_amount=Decimal('0.000'), currency=currency)
JournalEntryLine.objects.create(journal_entry=expenses_entry, line_number=3, account=account_cash, description='دفع نقدي', debit_amount=Decimal('0.000'), credit_amount=Decimal('1170.000'), currency=currency)

expenses_entry.calculate_totals()
expenses_entry.post(user=user)
print(f"✅ عملية 8: {expenses_entry.number}")

# ==========================================
# ملخص النتائج
# ==========================================

print("\n" + "="*60)
print("📊 ملخص عمليات يناير 2025")
print("="*60)

total_entries = JournalEntry.objects.filter(
    company=company,
    fiscal_year=fiscal_year_2025,
    period=period_jan,
    status='posted'
).count()

print(f"إجمالي القيود المرحلة: {total_entries}")

# حساب المبيعات
sales_total = JournalEntryLine.objects.filter(
    account=account_sales,
    journal_entry__status='posted',
    journal_entry__period=period_jan
).aggregate(total=models.Sum('credit_amount'))['total'] or 0

# حساب التكلفة
cost_total = JournalEntryLine.objects.filter(
    account=account_cost,
    journal_entry__status='posted',
    journal_entry__period=period_jan
).aggregate(total=models.Sum('debit_amount'))['total'] or 0

# مجمل الربح
gross_profit = sales_total - cost_total

print(f"\nالمبيعات: {sales_total:,.2f} دينار")
print(f"التكلفة: {cost_total:,.2f} دينار")
print(f"مجمل الربح: {gross_profit:,.2f} دينار")

print("="*60)
print("✅ اكتمل السيناريو المحاسبي الكامل!")





# 3 Report jsut
# ==========================================
# التقارير المحاسبية - يناير 2025
# ==========================================

from apps.accounting.models import JournalEntry, JournalEntryLine, Account, AccountType
from apps.core.models import Company
from apps.accounting.models import FiscalYear, AccountingPeriod
from django.db.models import Sum, Q
from decimal import Decimal

company = Company.objects.first()
fiscal_year_2025 = FiscalYear.objects.get(company=company, code='FY2025')
period_jan = AccountingPeriod.objects.get(fiscal_year=fiscal_year_2025, name='يناير 2025')

# ==========================================
# 1. ميزان المراجعة - يناير 2025
# ==========================================

print("=" * 80)
print("ميزان المراجعة - يناير 2025".center(80))
print("=" * 80)
print(f"{'الرمز':<10} {'اسم الحساب':<40} {'المدين':>12} {'الدائن':>12}")
print("-" * 80)

# جلب جميع الحسابات المستوى 4 التي لها حركة
accounts_with_movement = Account.objects.filter(
    company=company,
    level=4,
    lines__journal_entry__status='posted',
    lines__journal_entry__period=period_jan
).distinct().order_by('code')

total_debit = Decimal('0')
total_credit = Decimal('0')

for account in accounts_with_movement:
    lines = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period=period_jan
    )

    debit_sum = lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0')
    credit_sum = lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0')

    total_debit += debit_sum
    total_credit += credit_sum

    print(f"{account.code:<10} {account.name:<40} {debit_sum:>12,.2f} {credit_sum:>12,.2f}")

print("-" * 80)
print(f"{'الإجمالي':<50} {total_debit:>12,.2f} {total_credit:>12,.2f}")
print("=" * 80)
print(f"متوازن: {'نعم ✓' if total_debit == total_credit else 'لا ✗'}")
print()

# ==========================================
# 2. قائمة الدخل - يناير 2025
# ==========================================

print("=" * 80)
print("قائمة الدخل - يناير 2025".center(80))
print("=" * 80)

# الإيرادات (4)
revenue_accounts = Account.objects.filter(
    company=company,
    code__startswith='4',
    level=4,
    lines__journal_entry__status='posted',
    lines__journal_entry__period=period_jan
).distinct()

print("\nالإيرادات:")
total_revenue = Decimal('0')
for account in revenue_accounts:
    amount = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period=period_jan
    ).aggregate(total=Sum('credit_amount') - Sum('debit_amount'))['total'] or Decimal('0')

    total_revenue += amount
    print(f"  {account.name:<50} {amount:>12,.2f}")

print(f"{'إجمالي الإيرادات':<52} {total_revenue:>12,.2f}")
print("-" * 80)

# تكلفة المبيعات (5)
cost_accounts = Account.objects.filter(
    company=company,
    code__startswith='5',
    level=4,
    lines__journal_entry__status='posted',
    lines__journal_entry__period=period_jan
).distinct()

print("\nتكلفة المبيعات:")
total_cost = Decimal('0')
for account in cost_accounts:
    amount = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period=period_jan
    ).aggregate(total=Sum('debit_amount') - Sum('credit_amount'))['total'] or Decimal('0')

    total_cost += amount
    print(f"  {account.name:<50} {amount:>12,.2f}")

print(f"{'إجمالي تكلفة المبيعات':<52} ({total_cost:>11,.2f})")
print("-" * 80)

# مجمل الربح
gross_profit = total_revenue - total_cost
print(f"{'مجمل الربح':<52} {gross_profit:>12,.2f}")
print("-" * 80)

# المصروفات (6)
expense_accounts = Account.objects.filter(
    company=company,
    code__startswith='6',
    level=4,
    lines__journal_entry__status='posted',
    lines__journal_entry__period=period_jan
).distinct()

print("\nالمصروفات:")
total_expenses = Decimal('0')
for account in expense_accounts:
    amount = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period=period_jan
    ).aggregate(total=Sum('debit_amount') - Sum('credit_amount'))['total'] or Decimal('0')

    total_expenses += amount
    print(f"  {account.name:<50} {amount:>12,.2f}")

print(f"{'إجمالي المصروفات':<52} ({total_expenses:>11,.2f})")
print("-" * 80)

# صافي الربح
net_profit = gross_profit - total_expenses
print(f"{'صافي الربح':<52} {net_profit:>12,.2f}")
print("=" * 80)
print()

# ==========================================
# 3. تقرير الأرصدة - نهاية يناير
# ==========================================

print("=" * 80)
print("تقرير الأرصدة - 31 يناير 2025".center(80))
print("=" * 80)

# الأصول
print("\nالأصول:")
asset_accounts = Account.objects.filter(
    company=company,
    code__startswith='1',
    level=4
).order_by('code')

total_assets = Decimal('0')
for account in asset_accounts:
    # الرصيد الافتتاحي + الحركة
    lines = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period__fiscal_year=fiscal_year_2025,
        journal_entry__entry_date__lte=period_jan.end_date
    )

    debit = lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0')
    credit = lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0')
    balance = debit - credit

    if balance != 0:
        total_assets += balance
        print(f"  {account.code} {account.name:<45} {balance:>12,.2f}")

print(f"{'إجمالي الأصول':<54} {total_assets:>12,.2f}")
print("-" * 80)

# الخصوم
print("\nالخصوم:")
liability_accounts = Account.objects.filter(
    company=company,
    code__startswith='2',
    level=4
).order_by('code')

total_liabilities = Decimal('0')
for account in liability_accounts:
    lines = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period__fiscal_year=fiscal_year_2025,
        journal_entry__entry_date__lte=period_jan.end_date
    )

    debit = lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0')
    credit = lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0')
    balance = credit - debit

    if balance != 0:
        total_liabilities += balance
        print(f"  {account.code} {account.name:<45} {balance:>12,.2f}")

print(f"{'إجمالي الخصوم':<54} {total_liabilities:>12,.2f}")
print("-" * 80)

# حقوق الملكية
print("\nحقوق الملكية:")
equity_accounts = Account.objects.filter(
    company=company,
    code__startswith='3',
    level=4
).order_by('code')

total_equity = Decimal('0')
for account in equity_accounts:
    lines = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='posted',
        journal_entry__period__fiscal_year=fiscal_year_2025,
        journal_entry__entry_date__lte=period_jan.end_date
    )

    debit = lines.aggregate(Sum('debit_amount'))['debit_amount__sum'] or Decimal('0')
    credit = lines.aggregate(Sum('credit_amount'))['credit_amount__sum'] or Decimal('0')
    balance = credit - debit

    if balance != 0:
        total_equity += balance
        print(f"  {account.code} {account.name:<45} {balance:>12,.2f}")

# إضافة صافي الربح لحقوق الملكية
print(f"  صافي ربح يناير 2025{'':<38} {net_profit:>12,.2f}")
total_equity += net_profit

print(f"{'إجمالي حقوق الملكية':<54} {total_equity:>12,.2f}")
print("-" * 80)

# التحقق من المعادلة المحاسبية
print(f"\n{'الأصول':<54} {total_assets:>12,.2f}")
print(f"{'الخصوم + حقوق الملكية':<54} {(total_liabilities + total_equity):>12,.2f}")
equation_balanced = total_assets == (total_liabilities + total_equity)
print(f"\nالمعادلة المحاسبية متوازنة: {'نعم ✓' if equation_balanced else 'لا ✗'}")
print("=" * 80)

# ==========================================
# 4. ملخص إحصائي
# ==========================================

print("\n" + "=" * 80)
print("ملخص إحصائي - يناير 2025".center(80))
print("=" * 80)

posted_entries = JournalEntry.objects.filter(
    company=company,
    period=period_jan,
    status='posted'
).count()

draft_entries = JournalEntry.objects.filter(
    company=company,
    period=period_jan,
    status='draft'
).count()

total_lines = JournalEntryLine.objects.filter(
    journal_entry__company=company,
    journal_entry__period=period_jan,
    journal_entry__status='posted'
).count()

print(f"عدد القيود المرحلة: {posted_entries}")
print(f"عدد القيود قيد الإعداد: {draft_entries}")
print(f"إجمالي السطور: {total_lines}")
print(f"إجمالي المبيعات: {total_revenue:,.2f} دينار")
print(f"مجمل الربح: {gross_profit:,.2f} دينار")
print(f"صافي الربح: {net_profit:,.2f} دينار")
print(f"هامش الربح الإجمالي: {(gross_profit / total_revenue * 100) if total_revenue > 0 else 0:.2f}%")
print(f"هامش الربح الصافي: {(net_profit / total_revenue * 100) if total_revenue > 0 else 0:.2f}%")
print("=" * 80)







# مركز التكلفة

from django.db import connection, transaction
from apps.accounting.models.account_models import CostCenter
from apps.core.models import Company, User

# إعادة الاتصال بقاعدة البيانات
try:
    connection.ensure_connection()
except:
    connection.connect()

# الحصول على الشركة والمستخدم
try:
    company = Company.objects.first()
    if not company:
        print("❌ لا توجد شركة في النظام")
        exit()

    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()

    print(f"🏢 الشركة: {company.name}")
    print(f"👤 المستخدم: {user.username}")
    print("=" * 60)
except Exception as e:
    print(f"❌ خطأ في الاتصال: {e}")
    from django.db import connection

    connection.close()
    connection.connect()
    company = Company.objects.first()
    user = User.objects.first()

# بدء إنشاء البيانات
with transaction.atomic():
    print("\n📊 إنشاء المراكز الرئيسية...")

    # 1. الإدارة العامة
    admin_center, created = CostCenter.objects.get_or_create(
        company=company,
        code='ADM',
        defaults={
            'name': 'الإدارة العامة',
            'cost_center_type': 'administration',
            'manager': user,
            'description': 'المركز الرئيسي للإدارة العامة',
            'is_active': True,
            'created_by': user
        }
    )
    print(f"   {'✅' if created else '⚠️ '} {admin_center.code} - {admin_center.name}")

    # 2. الإنتاج
    production_center, created = CostCenter.objects.get_or_create(
        company=company,
        code='PROD',
        defaults={
            'name': 'قسم الإنتاج',
            'cost_center_type': 'production',
            'manager': user,
            'description': 'المركز الرئيسي للإنتاج',
            'is_active': True,
            'created_by': user
        }
    )
    print(f"   {'✅' if created else '⚠️ '} {production_center.code} - {production_center.name}")

    # 3. المبيعات
    sales_center, created = CostCenter.objects.get_or_create(
        company=company,
        code='SALES',
        defaults={
            'name': 'قسم المبيعات',
            'cost_center_type': 'sales',
            'manager': user,
            'description': 'المركز الرئيسي للمبيعات',
            'is_active': True,
            'created_by': user
        }
    )
    print(f"   {'✅' if created else '⚠️ '} {sales_center.code} - {sales_center.name}")

    # 4. التسويق
    marketing_center, created = CostCenter.objects.get_or_create(
        company=company,
        code='MKT',
        defaults={
            'name': 'قسم التسويق',
            'cost_center_type': 'marketing',
            'manager': user,
            'description': 'المركز الرئيسي للتسويق',
            'is_active': True,
            'created_by': user
        }
    )
    print(f"   {'✅' if created else '⚠️ '} {marketing_center.code} - {marketing_center.name}")

    # 5. الصيانة
    maintenance_center, created = CostCenter.objects.get_or_create(
        company=company,
        code='MAINT',
        defaults={
            'name': 'قسم الصيانة',
            'cost_center_type': 'maintenance',
            'manager': user,
            'description': 'المركز الرئيسي للصيانة',
            'is_active': True,
            'created_by': user
        }
    )
    print(f"   {'✅' if created else '⚠️ '} {maintenance_center.code} - {maintenance_center.name}")

    print("\n📂 إنشاء الأقسام الفرعية...")

    # الإدارة - الموارد البشرية
    hr_center, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-HR',
        defaults={'name': 'قسم الموارد البشرية', 'cost_center_type': 'administration', 'parent': admin_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {hr_center.code} - {hr_center.name}")

    # الإدارة - المحاسبة
    acc_center, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-ACC',
        defaults={'name': 'قسم المحاسبة', 'cost_center_type': 'administration', 'parent': admin_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {acc_center.code} - {acc_center.name}")

    # الإدارة - تقنية المعلومات
    it_center, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-IT',
        defaults={'name': 'قسم تقنية المعلومات', 'cost_center_type': 'services', 'parent': admin_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {it_center.code} - {it_center.name}")

    # الإنتاج - خط 1
    prod1, _ = CostCenter.objects.get_or_create(
        company=company, code='PROD-L1',
        defaults={'name': 'خط الإنتاج الأول', 'cost_center_type': 'production', 'parent': production_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {prod1.code} - {prod1.name}")

    # الإنتاج - خط 2
    prod2, _ = CostCenter.objects.get_or_create(
        company=company, code='PROD-L2',
        defaults={'name': 'خط الإنتاج الثاني', 'cost_center_type': 'production', 'parent': production_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {prod2.code} - {prod2.name}")

    # الإنتاج - الجودة
    qc, _ = CostCenter.objects.get_or_create(
        company=company, code='PROD-QC',
        defaults={'name': 'مراقبة الجودة', 'cost_center_type': 'production', 'parent': production_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {qc.code} - {qc.name}")

    # المبيعات - التجزئة
    retail, _ = CostCenter.objects.get_or_create(
        company=company, code='SALES-RET',
        defaults={'name': 'مبيعات التجزئة', 'cost_center_type': 'sales', 'parent': sales_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {retail.code} - {retail.name}")

    # المبيعات - الجملة
    wholesale, _ = CostCenter.objects.get_or_create(
        company=company, code='SALES-WHO',
        defaults={'name': 'مبيعات الجملة', 'cost_center_type': 'sales', 'parent': sales_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {wholesale.code} - {wholesale.name}")

    # المبيعات - التصدير
    export, _ = CostCenter.objects.get_or_create(
        company=company, code='SALES-EXP',
        defaults={'name': 'مبيعات التصدير', 'cost_center_type': 'sales', 'parent': sales_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {export.code} - {export.name}")

    # التسويق - الرقمي
    digital, _ = CostCenter.objects.get_or_create(
        company=company, code='MKT-DIG',
        defaults={'name': 'التسويق الرقمي', 'cost_center_type': 'marketing', 'parent': marketing_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {digital.code} - {digital.name}")

    # التسويق - التقليدي
    trad, _ = CostCenter.objects.get_or_create(
        company=company, code='MKT-TRAD',
        defaults={'name': 'التسويق التقليدي', 'cost_center_type': 'marketing', 'parent': marketing_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {trad.code} - {trad.name}")

    # الصيانة - المعدات
    eq_maint, _ = CostCenter.objects.get_or_create(
        company=company, code='MAINT-EQ',
        defaults={'name': 'صيانة المعدات', 'cost_center_type': 'maintenance', 'parent': maintenance_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {eq_maint.code} - {eq_maint.name}")

    # الصيانة - المباني
    bld_maint, _ = CostCenter.objects.get_or_create(
        company=company, code='MAINT-BLD',
        defaults={'name': 'صيانة المباني', 'cost_center_type': 'maintenance', 'parent': maintenance_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {bld_maint.code} - {bld_maint.name}")

    print("\n📁 إنشاء المستوى الثالث...")

    # الموارد البشرية - التوظيف
    rec, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-HR-REC',
        defaults={'name': 'قسم التوظيف', 'cost_center_type': 'administration', 'parent': hr_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {rec.code} - {rec.name}")

    # الموارد البشرية - التدريب
    trn, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-HR-TRN',
        defaults={'name': 'قسم التدريب', 'cost_center_type': 'administration', 'parent': hr_center, 'manager': user,
                  'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {trn.code} - {trn.name}")

    # المحاسبة - الدائنة
    pay, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-ACC-PAY',
        defaults={'name': 'الحسابات الدائنة', 'cost_center_type': 'administration', 'parent': acc_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {pay.code} - {pay.name}")

    # المحاسبة - المدينة
    rec_acc, _ = CostCenter.objects.get_or_create(
        company=company, code='ADM-ACC-REC',
        defaults={'name': 'الحسابات المدينة', 'cost_center_type': 'administration', 'parent': acc_center,
                  'manager': user, 'is_active': True, 'created_by': user}
    )
    print(f"   ✅ {rec_acc.code} - {rec_acc.name}")

print("\n" + "=" * 60)
total = CostCenter.objects.filter(company=company).count()
print(f"✅ إجمالي مراكز التكلفة: {total}")

print("\n📊 توزيع حسب المستوى:")
for level in range(1, 5):
    count = CostCenter.objects.filter(company=company, level=level).count()
    if count > 0:
        print(f"   المستوى {level}: {count} مركز")

print("\n✅ تم بنجاح!")









# متطلبات نظام إدارة الموارد البشرية (HR Management System)
# HR Management System Requirements

## نظرة عامة | Overview

نظام إدارة موارد بشرية متكامل يتوافق مع النظام القديم (Phoenix) ويضيف تحسينات حديثة، مصمم للشركات في الأسواق الناطقة بالعربية (الأردن) مع دعم RTL والامتثال للأنظمة المحلية.

A comprehensive HR management system compatible with the legacy Phoenix system with modern improvements, designed for Arabic-speaking markets (Jordan) with RTL support and local compliance.

---

## 1. إدارة الموظفين | Employee Management

### 1.1 البيانات الأساسية للموظف | Employee Basic Information

| الحقل بالعربية | Field in English | النوع | Type | إلزامي | Required |
|---------------|------------------|-------|------|--------|----------|
| رقم الموظف | Employee Number | نص | Text | نعم | Yes |
| الاسم الكامل | Full Name | نص | Text | نعم | Yes |
| تاريخ الميلاد | Date of Birth | تاريخ | Date | لا | No |
| الجنسية | Nationality | قائمة | List | لا | No |
| الحالة الاجتماعية | Marital Status | قائمة | List | لا | No |
| الرقم الوطني | National ID | نص | Text | نعم | Yes |
| رقم الموبايل | Mobile Number | نص | Text | نعم | Yes |
| البريد الإلكتروني | Email | بريد | Email | لا | No |
| الحالة | Status | قائمة | List | نعم | Yes |

**قيم الحالة | Status Values:**
- نشط | Active
- غير نشط | Inactive
- مفصول | Terminated

### 1.2 معلومات التوظيف | Employment Information

| الحقل بالعربية | Field in English | النوع | Type | إلزامي | Required |
|---------------|------------------|-------|------|--------|----------|
| تاريخ التعيين | Hire Date | تاريخ | Date | نعم | Yes |
| القسم/الإدارة | Department | علاقة | FK | نعم | Yes |
| المسمى الوظيفي | Job Title | نص | Text | نعم | Yes |
| المدينة/الفرع | Branch/City | علاقة | FK | لا | No |
| رقم الضمان الاجتماعي | Social Security Number | نص | Text | لا | No |
| حالة التوظيف | Employment Status | قائمة | List | نعم | Yes |

**حالات التوظيف | Employment Status:**
- دوام كامل | Full-time
- دوام جزئي | Part-time
- عقد مؤقت | Contract

---

## 2. هيكل الرواتب | Salary Structure

### 2.1 المكونات الـ 14 للراتب | 14 Salary Components

#### أ. الاستحقاقات (7 مكونات) | Earnings (7 Components)

| # | المكون بالعربية | Component in English | النوع | Type | الحساب | Calculation |
|---|----------------|---------------------|-------|------|---------|-------------|
| 1 | الراتب الأساسي | Basic Salary | ثابت | Fixed | يدوي | Manual |
| 2 | بدل الوقود | Fuel Allowance | ثابت | Fixed | يدوي | Manual |
| 3 | بدلات أخرى | Other Allowances | ثابت | Fixed | يدوي | Manual |
| 4 | راتب الضمان | Social Security Salary | ثابت | Fixed | يدوي | Manual |
| 5 | العمل الإضافي - أيام الدوام | Overtime - Regular Days | متغير | Variable | تلقائي | Auto |
| 6 | العمل الإضافي - أيام العطل | Overtime - Holidays | متغير | Variable | تلقائي | Auto |
| 7 | أصناف أخرى (استحقاقات) | Other Items (Earnings) | متغير | Variable | يدوي | Manual |

**صيغ الحساب | Calculation Formulas:**

```
معدل الساعة = الراتب الأساسي / (عدد أيام الشهر × عدد ساعات اليوم)
Hourly Rate = Basic Salary / (Days in Month × Hours per Day)

العمل الإضافي - أيام دوام = عدد الساعات × معدل الساعة × 1.25
Overtime Regular = Hours × Hourly Rate × 1.25

العمل الإضافي - أيام عطل = عدد الساعات × معدل الساعة × 2.0
Overtime Holidays = Hours × Hourly Rate × 2.0
```

#### ب. الخصومات (4 مكونات) | Deductions (4 Components)

| # | المكون بالعربية | Component in English | النوع | Type | الحساب | Calculation |
|---|----------------|---------------------|-------|------|---------|-------------|
| 8 | السلف | Advances | متغير | Variable | تلقائي | Auto |
| 9 | مغادرات الخصم | Deducted Leaves | متغير | Variable | تلقائي | Auto |
| 10 | احتزارت الخصم | Administrative Deductions | متغير | Variable | يدوي | Manual |
| 11 | الضمان الاجتماعي - حصة الموظف | Social Security - Employee | متغير | Variable | تلقائي | Auto |

**صيغ الحساب | Calculation Formulas:**

```
مغادرات الخصم = عدد ساعات المغادرة × معدل الساعة
Early Leave Deductions = Early Leave Hours × Hourly Rate

الضمان - موظف = راتب الضمان × 7.5%
Social Security Employee = SS Salary × 7.5%
```

#### ج. التكاليف على الشركة (1 مكون) | Company Costs (1 Component)

| # | المكون بالعربية | Component in English | النوع | Type | الحساب | Calculation |
|---|----------------|---------------------|-------|------|---------|-------------|
| 12 | الضمان الاجتماعي - حصة الشركة | Social Security - Company | متغير | Variable | تلقائي | Auto |

**صيغة الحساب | Calculation Formula:**

```
الضمان - شركة = راتب الضمان × 14.25%
Social Security Company = SS Salary × 14.25%
```

#### د. الإجازات (2 مكون) | Leaves (2 Components)

| # | المكون بالعربية | Component in English | التأثير | Impact |
|---|----------------|---------------------|---------|--------|
| 13 | الإجازات السنوية | Annual Leaves | على الراتب | On Salary |
| 14 | الإجازات المرضية | Sick Leaves | على الراتب | On Salary |

---

## 3. الحركات الشهرية | Monthly Payroll Processing

### 3.1 بيانات الحركة | Movement Data

| الحقل بالعربية | Field in English | النوع | Type | إلزامي | Required |
|---------------|------------------|-------|------|--------|----------|
| رقم الحركة | Movement Number | نص | Text | نعم | Yes |
| تاريخ الحركة | Movement Date | تاريخ | Date | نعم | Yes |
| الشركة | Company | علاقة | FK | نعم | Yes |
| الحالة | Status | قائمة | List | نعم | Yes |
| ملاحظات | Notes | نص | Text | لا | No |

**حالات الحركة | Movement Status:**
- جديد | New
- قيد المعالجة | Processing
- مرحّل | Posted (لا يمكن التعديل | Cannot be edited)
- ملغي | Cancelled

### 3.2 تفاصيل الحركة لكل موظف | Movement Details per Employee

#### أ. بيانات الحضور | Attendance Data

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| أيام الدوام | Working Days | رقم | Number |
| أيام العطل المشتغلة | Worked Holidays | رقم | Number |
| ساعات العمل الإضافي | Overtime Hours | رقم | Number |

#### ب. بيانات الإجازات | Leave Data

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| الإجازات السنوية المأخوذة | Annual Leaves Taken | رقم | Number |
| الإجازات المرضية المأخوذة | Sick Leaves Taken | رقم | Number |
| إجازات مدفوعة | Paid Leaves | رقم | Number |
| إجازات غير مدفوعة | Unpaid Leaves | رقم | Number |

#### ج. بيانات المغادرات | Early Leave Data

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| عدد المغادرات | Number of Early Leaves | رقم | Number |
| إجمالي ساعات المغادرات | Total Early Leave Hours | رقم | Number |
| قيمة خصم المغادرات | Early Leave Deduction Amount | رقم | Number |

#### د. الحسابات النهائية | Final Calculations

| الحقل بالعربية | Field in English | الحساب | Calculation |
|---------------|------------------|---------|-------------|
| إجمالي الاستحقاقات | Total Earnings | مجموع 1-7 | Sum 1-7 |
| إجمالي الخصومات | Total Deductions | مجموع 8-11 | Sum 8-11 |
| صافي الراتب | Net Salary | الاستحقاقات - الخصومات | Earnings - Deductions |

### 3.3 سير العمل | Workflow

```
1. إنشاء حركة جديدة → حالة "جديد"
   Create New Movement → Status "New"

2. إدخال البيانات → تعبئة بيانات كل موظف
   Data Entry → Fill employee data

3. الحسابات التلقائية → تشغيل الحسابات
   Auto Calculations → Run calculations

4. المراجعة → التحقق من الأرقام
   Review → Verify numbers

5. الترحيل (Post) → تثبيت الحركة
   Post → Finalize movement

6. إنشاء قيد محاسبي → تلقائياً
   Create Journal Entry → Automatically
```

---

## 4. السلف | Advances

### 4.1 بيانات السلفة | Advance Data

| الحقل بالعربية | Field in English | النوع | Type | إلزامي | Required |
|---------------|------------------|-------|------|--------|----------|
| رقم السلفة | Advance Number | نص | Text | نعم | Yes |
| الموظف | Employee | علاقة | FK | نعم | Yes |
| التاريخ | Date | تاريخ | Date | نعم | Yes |
| المبلغ الإجمالي | Total Amount | رقم | Number | نعم | Yes |
| عدد الأقساط | Number of Installments | رقم | Number | نعم | Yes |
| قيمة القسط | Installment Amount | رقم | Number | تلقائي | Auto |
| المبلغ المسدد | Paid Amount | رقم | Number | تلقائي | Auto |
| المبلغ المتبقي | Remaining Amount | رقم | Number | تلقائي | Auto |
| الحالة | Status | قائمة | List | نعم | Yes |

**صيغة حساب القسط | Installment Calculation:**

```
قيمة القسط = المبلغ الإجمالي / عدد الأقساط
Installment Amount = Total Amount / Number of Installments
```

### 4.2 أقساط السلفة | Advance Installments

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| رقم القسط | Installment Number | رقم | Number |
| تاريخ الاستحقاق | Due Date | تاريخ | Date |
| المبلغ | Amount | رقم | Number |
| الحالة | Status | قائمة | List |
| تاريخ السداد | Payment Date | تاريخ | Date |
| رقم حركة الراتب | Payroll Movement Number | علاقة | FK |

**حالات القسط | Installment Status:**
- مستحق | Due
- مسدد | Paid
- متأخر | Overdue

---

## 5. الإجازات | Leave Management

### 5.1 أنواع الإجازات | Leave Types

| النوع بالعربية | Type in English | الوصف | Description |
|---------------|-----------------|-------|-------------|
| إجازة سنوية | Annual Leave | مدفوعة، قابلة للترحيل | Paid, Carryforward |
| إجازة مرضية | Sick Leave | مدفوعة، تحتاج تقرير طبي | Paid, Medical certificate |
| إجازة مدفوعة | Paid Leave | استثنائية | Exceptional |
| إجازة بدون راتب | Unpaid Leave | غير مدفوعة | Not paid |
| إجازة طارئة | Emergency Leave | حسب السياسة | Per policy |

### 5.2 سياسات الإجازات | Leave Policies

**الإجازة السنوية | Annual Leave:**
```
الرصيد السنوي = 14 يوم (قابل للتعديل)
Annual Balance = 14 days (configurable)

الاستحقاق الشهري = 14 / 12 = 1.16 يوم/شهر
Monthly Accrual = 14 / 12 = 1.16 days/month

ترحيل الرصيد = حسب سياسة الشركة
Carryforward = Per company policy
```

**الإجازة المرضية | Sick Leave:**
```
الرصيد السنوي = 14 يوم (قابل للتعديل)
Annual Balance = 14 days (configurable)

تقرير طبي = مطلوب بعد 3 أيام
Medical Certificate = Required after 3 days

لا ترحيل = الرصيد لا يُرحل
No Carryforward = Balance doesn't carry
```

### 5.3 طلب الإجازة | Leave Request

| الحقل بالعربية | Field in English | النوع | Type | إلزامي | Required |
|---------------|------------------|-------|------|--------|----------|
| رقم الطلب | Request Number | نص | Text | نعم | Yes |
| الموظف | Employee | علاقة | FK | نعم | Yes |
| نوع الإجازة | Leave Type | علاقة | FK | نعم | Yes |
| تاريخ البدء | Start Date | تاريخ | Date | نعم | Yes |
| تاريخ النهاية | End Date | تاريخ | Date | نعم | Yes |
| عدد الأيام | Number of Days | رقم | Number | تلقائي | Auto |
| السبب | Reason | نص | Text | لا | No |
| الحالة | Status | قائمة | List | نعم | Yes |

**حالات الطلب | Request Status:**
- قيد الانتظار | Pending
- موافق عليها | Approved
- مرفوضة | Rejected
- ملغاة | Cancelled

### 5.4 رصيد الإجازات | Leave Balance

| الحقل بالعربية | Field in English | الحساب | Calculation |
|---------------|------------------|---------|-------------|
| الرصيد الافتتاحي | Opening Balance | من العام السابق | From previous year |
| المستحق خلال العام | Accrued | شهري × 12 | Monthly × 12 |
| المستخدم | Used | من الطلبات | From requests |
| المتبقي | Remaining | الافتتاحي + المستحق - المستخدم | Opening + Accrued - Used |
| المرحّل للعام القادم | Carried Forward | حسب السياسة | Per policy |

---

## 6. الضمان الاجتماعي | Social Security

### 6.1 الإعدادات | Settings

| الإعداد بالعربية | Setting in English | القيمة الافتراضية | Default Value |
|-----------------|-------------------|-------------------|---------------|
| نسبة حصة الموظف | Employee Contribution % | 7.5% | 7.5% |
| نسبة حصة الشركة | Company Contribution % | 14.25% | 14.25% |
| الحد الأدنى للراتب | Minimum Insurable Salary | قابل للتعديل | Configurable |
| الحد الأقصى للراتب | Maximum Insurable Salary | قابل للتعديل | Configurable |

### 6.2 الحسابات | Calculations

```
راتب الضمان = يُحدد لكل موظف (قد يختلف عن الراتب الأساسي)
SS Salary = Set per employee (may differ from basic salary)

حصة الموظف = راتب الضمان × نسبة حصة الموظف
Employee Share = SS Salary × Employee %

حصة الشركة = راتب الضمان × نسبة حصة الشركة
Company Share = SS Salary × Company %

الإجمالي = حصة الموظف + حصة الشركة
Total = Employee Share + Company Share
```

---

## 7. العقود والعلاوات | Contracts & Increments

### 7.1 العقد السنوي | Annual Contract

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| تاريخ بداية العقد | Contract Start Date | تاريخ | Date |
| تاريخ نهاية العقد | Contract End Date | تاريخ | Date |
| نوع العقد | Contract Type | قائمة | List |
| راتب العقد | Contract Salary | رقم | Number |

**أنواع العقود | Contract Types:**
- محدد المدة | Fixed-term
- غير محدد المدة | Indefinite
- عقد مؤقت | Temporary

### 7.2 العلاوات | Increments

| الحقل بالعربية | Field in English | النوع | Type |
|---------------|------------------|-------|------|
| تاريخ العلاوة | Increment Date | تاريخ | Date |
| قيمة العلاوة | Increment Amount | رقم | Number |
| نسبة العلاوة | Increment Percentage | نسبة | Percentage |
| الراتب الجديد | New Salary | رقم | Number |
| ملاحظات | Notes | نص | Text |

**آلية العمل | Workflow:**
```
عند إضافة علاوة، يتم تحديث الراتب الأساسي تلقائياً
When adding increment, basic salary is updated automatically

الراتب الجديد = الراتب الحالي + قيمة العلاوة
New Salary = Current Salary + Increment Amount

أو | Or

الراتب الجديد = الراتب الحالي × (1 + نسبة العلاوة)
New Salary = Current Salary × (1 + Increment %)
```

---

## 8. قسيمة الراتب | Payslip

### 8.1 محتويات القسيمة | Payslip Contents

#### الترويسة | Header
- اسم الشركة وشعارها | Company Name & Logo
- عنوان: "قسيمة راتب - سند صرف" | Title: "Payslip - Payment Voucher"
- التاريخ | Date
- رقم الحركة | Movement Number

#### بيانات الموظف | Employee Information
- رقم الموظف | Employee Number
- اسم الموظف | Employee Name

#### الرواتب (الاستحقاقات) | Salaries (Earnings)

| البند بالعربية | Item in English | المبلغ | Amount |
|---------------|-----------------|--------|--------|
| الراتب الأساسي | Basic Salary | XXX.XX | XXX.XX |
| بدل الوقود | Fuel Allowance | XXX.XX | XXX.XX |
| بدلات أخرى | Other Allowances | XXX.XX | XXX.XX |
| **الإجمالي** | **Total** | **XXX.XX** | **XXX.XX** |

#### الخصومات | Deductions

| البند بالعربية | Item in English | المبلغ | Amount |
|---------------|-----------------|--------|--------|
| السلف | Advances | XXX.XX | XXX.XX |
| مغادرات الخصم | Early Leave Deductions | XXX.XX | XXX.XX |
| احتزارت الخصم | Administrative Deductions | XXX.XX | XXX.XX |
| **إجمالي الخصومات** | **Total Deductions** | **XXX.XX** | **XXX.XX** |

#### العمل الإضافي | Overtime

| البند بالعربية | Item in English | المبلغ | Amount |
|---------------|-----------------|--------|--------|
| أيام الدوام | Regular Days | XXX.XX | XXX.XX |
| أيام العطل | Holidays | XXX.XX | XXX.XX |
| أصناف أخرى | Other Items | XXX.XX | XXX.XX |

#### الضمان الاجتماعي | Social Security

| البند بالعربية | Item in English | المبلغ | Amount |
|---------------|-----------------|--------|--------|
| موظف | Employee | XXX.XX | XXX.XX |
| شركة | Company | XXX.XX | XXX.XX |

#### صافي الراتب | Net Salary
```
═══════════════════════════════════
    صافي الراتب | Net Salary
    XXX.XX
═══════════════════════════════════
```

#### تفاصيل الإجازات | Leave Details

**الإجازات المتقطعة | Leave Breakdown**

| النوع | Type | عدد الأيام | Days |
|------|------|-----------|------|
| السنوية | Annual | X | X |
| مرضية | Sick | X | X |
| مدفوعة | Paid | X | X |
| من الراتب | Unpaid | X | X |
| المقطوعة | Deducted | X | X |

**رصيد الإجازات | Leave Balance**
- الإجازات السنوية المتبقية | Remaining Annual: X.XX يوم | days
- الإجازات المرضية المتبقية | Remaining Sick: X.XX يوم | days

#### التوقيع | Signature
```
_____________________
التوقيع | Signature
```

---

## 9. التقارير | Reports

### 9.1 تقارير الرواتب | Payroll Reports

#### 1. تقرير الرواتب الشهري | Monthly Payroll Report
**المحتوى | Content:**
- قائمة بجميع الموظفين | List of all employees
- جميع مكونات الراتب (14 مكون) | All 14 salary components
- إجمالي الاستحقاقات والخصومات | Total earnings & deductions
- صافي الرواتب | Net salaries
- إجماليات عامة | Grand totals

**التصدير | Export:**
- Excel (XLSX)
- PDF
- CSV

#### 2. تقرير صافي الرواتب | Net Salary Report
**المحتوى | Content:**
- رقم الموظف | Employee Number
- الاسم | Name
- القسم | Department
- صافي الراتب | Net Salary
- الإجمالي | Total

#### 3. تقرير الضمان الاجتماعي | Social Security Report
**المحتوى | Content:**
- الرقم الضماني | SS Number
- الاسم | Name
- راتب الضمان | SS Salary
- حصة الموظف | Employee Share
- حصة الشركة | Company Share
- الإجمالي | Total

**الاستخدام | Usage:**
للتقديم لمؤسسة الضمان الاجتماعي
For submission to Social Security Institution

#### 4. تقرير السلف | Advances Report
**المحتوى | Content:**
- رقم السلفة | Advance Number
- الموظف | Employee
- المبلغ الإجمالي | Total Amount
- المبلغ المسدد | Paid Amount
- المبلغ المتبقي | Remaining Amount
- عدد الأقساط المتبقية | Remaining Installments
- الحالة | Status

**الفلترة | Filtering:**
- حسب الموظف | By Employee
- حسب الحالة | By Status
- حسب التاريخ | By Date

#### 5. تقرير الإجازات | Leaves Report
**المحتوى | Content:**
- الموظف | Employee
- نوع الإجازة | Leave Type
- الرصيد الافتتاحي | Opening Balance
- المستحق | Accrued
- المستخدم | Used
- المتبقي | Remaining

**الفلترة | Filtering:**
- حسب الموظف | By Employee
- حسب القسم | By Department
- حسب نوع الإجازة | By Leave Type
- حسب الفترة | By Period

### 9.2 تقارير الموظفين | Employee Reports

#### 1. قائمة الموظفين | Employee List
**المحتوى | Content:**
- جميع بيانات الموظف | All employee data
- الفلترة: القسم، الفرع، الحالة | Filter: Dept, Branch, Status

#### 2. تقرير العقود المنتهية | Expiring Contracts Report
**المحتوى | Content:**
- الموظفين الذين ستنتهي عقودهم خلال فترة محددة
- Employees whose contracts expire within specified period

#### 3. تقرير العلاوات | Increments Report
**المحتوى | Content:**
- العلاوات المستحقة | Due increments
- تاريخ العلاوات السابقة | Historical increments

---

## 10. الربط المحاسبي | Accounting Integration

### 10.1 القيد المحاسبي التلقائي | Automatic Journal Entry

**عند ترحيل حركة الرواتب | When Posting Payroll:**

#### الطرف المدين | Debit Side

| الحساب بالعربية | Account in English | المبلغ | Amount |
|----------------|-------------------|--------|--------|
| مصروف الرواتب والأجور | Salaries & Wages Expense | الرواتب الأساسية | Basic Salaries |
| مصروف البدلات | Allowances Expense | البدلات | Allowances |
| مصروف العمل الإضافي | Overtime Expense | العمل الإضافي | Overtime |
| مصروف الضمان - حصة الشركة | SS Expense - Company | حصة الشركة | Company Share |

#### الطرف الدائن | Credit Side

| الحساب بالعربية | Account in English | المبلغ | Amount |
|----------------|-------------------|--------|--------|
| رواتب مستحقة الدفع | Salaries Payable | صافي الرواتب | Net Salaries |
| ذمة الضمان الاجتماعي | Social Security Payable | موظف + شركة | Employee + Company |
| سلف الموظفين | Employee Advances | السلف المخصومة | Deducted Advances |

### 10.2 إعدادات الحسابات | Account Mapping Settings

**ربط المكونات بالحسابات | Component to Account Mapping:**

يمكن تخصيص حساب محاسبي لكل مكون من مكونات الراتب
Each salary component can be mapped to an accounting account

**قابل للتخصيص لكل شركة | Configurable per Company**

---

## 11. الواجهات | User Interface

### 11.1 القوائم والشاشات | Menus & Screens

#### القائمة الرئيسية: إدارة الموارد البشرية | Main Menu: HR Management

**1. الموظفون | Employees**
- قائمة الموظفين | Employee List (DataTables)
- إضافة موظف جديد | Add New Employee
- تعديل بيانات الموظف | Edit Employee
- عرض بطاقة الموظف | View Employee Card
- إنهاء خدمة موظف | Terminate Employee

**2. الرواتب الشهرية | Monthly Payroll**
- قائمة الحركات الشهرية | Movement List (DataTables)
- إنشاء حركة جديدة | Create New Movement
- إدخال/تعديل حركة | Enter/Edit Movement
- ترحيل حركة | Post Movement
- إلغاء حركة | Cancel Movement (قبل الترحيل | Before Posting)
- عرض تفاصيل الحركة | View Movement Details
- طباعة قسائم الرواتب | Print Payslips (PDF)
- تصدير إلى Excel | Export to Excel

**3. السلف | Advances**
- قائمة السلف | Advances List
- إضافة سلفة جديدة | Add New Advance
- عرض تفاصيل السلفة | View Advance Details
- الأقساط | Installments
- سداد قسط يدوياً | Manual Payment

**4. الإجازات | Leaves**
- قائمة طلبات الإجازات | Leave Requests List
- إضافة طلب إجازة | Add Leave Request
- الموافقة/رفض طلب | Approve/Reject Request
- عرض رصيد الإجازات | View Leave Balance
- سجل الإجازات | Leave History

**5. التقارير | Reports**
- تقرير الرواتب الشهري | Monthly Payroll Report
- تقرير صافي الرواتب | Net Salary Report
- تقرير الضمان الاجتماعي | Social Security Report
- تقرير السلف | Advances Report
- تقرير الإجازات | Leaves Report
- تقرير العقود المنتهية | Expiring Contracts Report

**6. الإعدادات | Settings**
- إعدادات الضمان الاجتماعي | Social Security Settings
- إعدادات الإجازات | Leave Policies
- ربط الحسابات المحاسبية | Accounting Mapping
- الأقسام | Departments
- الفروع | Branches

### 11.2 متطلبات التصميم | Design Requirements

#### التقنيات | Technologies
- **RTL Support** - دعم كامل للغة العربية | Full Arabic Support
- **Material Design** - تصميم احترافي | Professional Design
- **Responsive** - يعمل على جميع الأحجام | Works on All Sizes
- **Font: Cairo** - خط القاهرة للعربية | Cairo Font for Arabic

#### المكونات | Components
- **DataTables** - للجداول مع | For Tables with:
  - Server-side processing | معالجة من جانب الخادم
  - البحث والفلترة | Search & Filter
  - الترتيب | Sorting
  - التصدير | Export (Excel, PDF)
- **Select2** - للقوائم المنسدلة | For Dropdowns
- **Date Pickers** - لاختيار التواريخ | For Date Selection
- **SweetAlert2** - للتنبيهات والتأكيدات | For Alerts & Confirmations

#### نظام الألوان | Color Scheme
```
الأساسي | Primary: #1976D2 (Material Blue)
الثانوي | Secondary: #424242 (Material Grey)
النجاح | Success: #388E3C (Material Green)
التحذير | Warning: #F57C00 (Material Orange)
الخطر | Danger: #D32F2F (Material Red)
```

---

## 12. الصلاحيات | Permissions

### 12.1 الأدوار المطلوبة | Required Roles

#### 1. مدير الموارد البشرية | HR Manager
**الصلاحيات | Permissions:**
- ✅ صلاحيات كاملة على جميع الوظائف | Full access to all functions
- ✅ إضافة/تعديل/حذف الموظفين | Add/Edit/Delete employees
- ✅ إنشاء وترحيل الرواتب | Create & Post payroll
- ✅ إدارة السلف والإجازات | Manage advances & leaves
- ✅ جميع التقارير | All reports
- ✅ تعديل الإعدادات | Modify settings

#### 2. موظف الموارد البشرية | HR Employee
**الصلاحيات | Permissions:**
- ✅ إضافة/تعديل بيانات الموظفين | Add/Edit employee data
- ✅ إنشاء وإدخال حركات الرواتب | Create & Enter payroll
- ⚠️ ترحيل الرواتب (يحتاج موافقة) | Post payroll (needs approval)
- ✅ إدارة السلف والإجازات | Manage advances & leaves
- ✅ عرض التقارير | View reports
- ❌ تعديل الإعدادات | Modify settings

#### 3. المحاسب | Accountant
**الصلاحيات | Permissions:**
- ✅ عرض حركات الرواتب المرحلة | View posted payroll
- ✅ عرض القيود المحاسبية | View journal entries
- ✅ التقارير المالية | Financial reports
- ❌ تعديل بيانات الرواتب | Edit payroll data

#### 4. مدير القسم | Department Manager
**الصلاحيات | Permissions:**
- ✅ عرض بيانات موظفي قسمه فقط | View own department only
- ✅ الموافقة على طلبات الإجازات | Approve leave requests
- ✅ عرض تقارير قسمه | View department reports
- ❌ تعديل الرواتب | Edit salaries

#### 5. الموظف | Employee
**الصلاحيات | Permissions:**
- ✅ عرض بياناته الشخصية فقط | View own data only
- ✅ عرض قسائم رواتبه | View own payslips
- ✅ تقديم طلبات إجازة | Submit leave requests
- ✅ عرض رصيد إجازاته | View leave balance
- ❌ عرض بيانات الآخرين | View others' data

### 12.2 مصفوفة الصلاحيات | Permission Matrix

| الوظيفة | Function | HR Manager | HR Employee | Accountant | Dept Manager | Employee |
|---------|----------|------------|-------------|------------|--------------|----------|
| إضافة موظف | Add Employee | ✅ | ✅ | ❌ | ❌ | ❌ |
| تعديل موظف | Edit Employee | ✅ | ✅ | ❌ | ❌ | ❌ |
| حذف موظف | Delete Employee | ✅ | ❌ | ❌ | ❌ | ❌ |
| إنشاء راتب | Create Payroll | ✅ | ✅ | ❌ | ❌ | ❌ |
| ترحيل راتب | Post Payroll | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| إضافة سلفة | Add Advance | ✅ | ✅ | ❌ | ❌ | ❌ |
| الموافقة على إجازة | Approve Leave | ✅ | ✅ | ❌ | ✅ | ❌ |
| طلب إجازة | Request Leave | ✅ | ✅ | ✅ | ✅ | ✅ |
| عرض التقارير | View Reports | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| تعديل الإعدادات | Edit Settings | ✅ | ❌ | ❌ | ❌ | ❌ |

**الرموز | Legends:**
- ✅ مسموح | Allowed
- ❌ غير مسموح | Not Allowed
- ⚠️ مسموح جزئياً | Partially Allowed

---

## 13. النماذج (Models) المطلوبة | Required Models

### 13.1 القائمة الكاملة | Complete List

#### Core Models | النماذج الأساسية
```python
1. Employee                    # الموظف
2. Department                  # القسم
3. Branch                      # الفرع/المدينة
4. EmploymentStatus           # حالة التوظيف
```

#### Salary Components | مكونات الراتب
```python
5. SalaryComponent            # المكونات (14 مكون)
6. EmployeeSalaryStructure    # هيكل راتب الموظف
```

#### Payroll | الرواتب
```python
7. PayrollMovement            # حركة الراتب
8. PayrollMovementDetail      # تفاصيل حركة الراتب
9. PayrollStatus              # حالة الحركة
```

#### Advances | السلف
```python
10. EmployeeAdvance           # سلفة الموظف
11. AdvanceInstallment        # قسط السلفة
```

#### Leaves | الإجازات
```python
12. LeaveType                 # نوع الإجازة
13. LeavePolicy               # سياسة الإجازة
14. LeaveBalance              # رصيد الإجازة
15. LeaveRequest              # طلب الإجازة
```

#### Social Security | الضمان الاجتماعي
```python
16. SocialSecuritySettings    # إعدادات الضمان
```

#### Contracts | العقود
```python
17. EmployeeContract          # عقد الموظف
18. SalaryIncrement           # العلاوة
```

#### Accounting Integration | الربط المحاسبي
```python
19. PayrollAccountMapping     # ربط حسابات الرواتب
```

---

## 14. القواعد والحسابات | Business Rules & Calculations

### 14.1 حسابات الراتب | Salary Calculations

#### معدل الساعة | Hourly Rate
```python
معدل_الساعة = الراتب_الأساسي / (عدد_أيام_الشهر × عدد_ساعات_اليوم)
hourly_rate = basic_salary / (days_in_month × hours_per_day)

# مثال | Example:
# راتب أساسي = 1000 دينار | Basic Salary = 1000 JOD
# أيام الشهر = 30 يوم | Days in Month = 30 days
# ساعات اليوم = 8 ساعات | Hours per Day = 8 hours
# معدل الساعة = 1000 / (30 × 8) = 4.17 دينار/ساعة
# Hourly Rate = 1000 / (30 × 8) = 4.17 JOD/hour
```

#### العمل الإضافي - أيام دوام | Overtime - Regular Days
```python
المبلغ = عدد_الساعات × معدل_الساعة × 1.25
amount = hours × hourly_rate × 1.25

# مثال | Example:
# ساعات = 10 | Hours = 10
# معدل الساعة = 4.17 | Hourly Rate = 4.17
# المبلغ = 10 × 4.17 × 1.25 = 52.13 دينار
# Amount = 10 × 4.17 × 1.25 = 52.13 JOD
```

#### العمل الإضافي - أيام عطل | Overtime - Holidays
```python
المبلغ = عدد_الساعات × معدل_الساعة × 2.0
amount = hours × hourly_rate × 2.0

# مثال | Example:
# ساعات = 8 | Hours = 8
# معدل الساعة = 4.17 | Hourly Rate = 4.17
# المبلغ = 8 × 4.17 × 2.0 = 66.72 دينار
# Amount = 8 × 4.17 × 2.0 = 66.72 JOD
```

#### مغادرات الخصم | Early Leave Deductions
```python
المبلغ = عدد_ساعات_المغادرة × معدل_الساعة
amount = early_leave_hours × hourly_rate

# مثال | Example:
# ساعات المغادرة = 5 | Early Leave Hours = 5
# معدل الساعة = 4.17 | Hourly Rate = 4.17
# المبلغ = 5 × 4.17 = 20.85 دينار
# Amount = 5 × 4.17 = 20.85 JOD
```

#### الضمان الاجتماعي - موظف | Social Security - Employee
```python
المبلغ = راتب_الضمان × نسبة_حصة_الموظف
amount = ss_salary × employee_percentage

# مثال | Example:
# راتب الضمان = 800 دينار | SS Salary = 800 JOD
# نسبة الموظف = 7.5% | Employee % = 7.5%
# المبلغ = 800 × 0.075 = 60 دينار
# Amount = 800 × 0.075 = 60 JOD
```

#### الضمان الاجتماعي - شركة | Social Security - Company
```python
المبلغ = راتب_الضمان × نسبة_حصة_الشركة
amount = ss_salary × company_percentage

# مثال | Example:
# راتب الضمان = 800 دينار | SS Salary = 800 JOD
# نسبة الشركة = 14.25% | Company % = 14.25%
# المبلغ = 800 × 0.1425 = 114 دينار
# Amount = 800 × 0.1425 = 114 JOD
```

#### صافي الراتب | Net Salary
```python
صافي_الراتب = إجمالي_الاستحقاقات - إجمالي_الخصومات
net_salary = total_earnings - total_deductions

إجمالي_الاستحقاقات = (
    الراتب_الأساسي +
    بدل_الوقود +
    بدلات_أخرى +
    عمل_إضافي_دوام +
    عمل_إضافي_عطل +
    أصناف_أخرى
)

total_earnings = (
    basic_salary +
    fuel_allowance +
    other_allowances +
    overtime_regular +
    overtime_holidays +
    other_items
)

إجمالي_الخصومات = (
    السلف +
    مغادرات_الخصم +
    احتزارت_الخصم +
    ضمان_موظف
)

total_deductions = (
    advances +
    early_leave_deductions +
    administrative_deductions +
    ss_employee
)
```

### 14.2 حسابات الإجازات | Leave Calculations

#### الاستحقاق الشهري للإجازة السنوية | Monthly Annual Leave Accrual
```python
الاستحقاق_الشهري = الرصيد_السنوي / 12
monthly_accrual = annual_balance / 12

# مثال | Example:
# رصيد سنوي = 14 يوم | Annual Balance = 14 days
# استحقاق شهري = 14 / 12 = 1.17 يوم
# Monthly Accrual = 14 / 12 = 1.17 days
```

#### خصم الإجازات غير المدفوعة | Unpaid Leave Deduction
```python
الخصم = (الراتب_الأساسي / عدد_أيام_الشهر) × عدد_أيام_الإجازة
deduction = (basic_salary / days_in_month) × leave_days

# مثال | Example:
# راتب أساسي = 1000 دينار | Basic Salary = 1000 JOD
# أيام الشهر = 30 | Days in Month = 30
# أيام الإجازة = 3 | Leave Days = 3
# الخصم = (1000 / 30) × 3 = 100 دينار
# Deduction = (1000 / 30) × 3 = 100 JOD
```

#### حساب عدد أيام الإجازة (أيام العمل فقط) | Calculate Leave Days (Working Days Only)
```python
def حساب_أيام_العمل(تاريخ_البدء, تاريخ_النهاية):
    """
    حساب عدد أيام العمل بين تاريخين (باستثناء الجمعة والسبت)
    Calculate working days between two dates (excluding Friday & Saturday)
    """
    أيام_العمل = 0
    working_days = 0
    
    التاريخ_الحالي = تاريخ_البدء
    current_date = start_date
    
    while التاريخ_الحالي <= تاريخ_النهاية:
        current_date <= end_date:
        
        # استثناء الجمعة (4) والسبت (5)
        # Exclude Friday (4) and Saturday (5)
        if التاريخ_الحالي.weekday() not in [4, 5]:
            current_date.weekday() not in [4, 5]:
            أيام_العمل += 1
            working_days += 1
        
        التاريخ_الحالي += timedelta(days=1)
        current_date += timedelta(days=1)
    
    return أيام_العمل
    return working_days
```

---

## 15. قاعدة البيانات | Database Schema

### 15.1 الجداول الرئيسية | Main Tables

#### 1. hr_employee | جدول الموظفين

```sql
CREATE TABLE hr_employee (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- البيانات الأساسية | Basic Information
    company_id INT NOT NULL,
    employee_number VARCHAR(20) UNIQUE NOT NULL,
    full_name_ar VARCHAR(200) NOT NULL,
    full_name_en VARCHAR(200),
    date_of_birth DATE,
    nationality VARCHAR(50),
    marital_status VARCHAR(20),
    national_id VARCHAR(50) UNIQUE,
    mobile VARCHAR(20),
    email VARCHAR(100),
    
    -- معلومات التوظيف | Employment Information
    hire_date DATE NOT NULL,
    department_id INT,
    job_title VARCHAR(100),
    branch_id INT,
    social_security_number VARCHAR(50),
    employment_status VARCHAR(20) DEFAULT 'full_time',
    status VARCHAR(20) DEFAULT 'active',
    
    -- الرواتب الأساسية | Basic Salary Information
    basic_salary DECIMAL(10,2) NOT NULL DEFAULT 0,
    fuel_allowance DECIMAL(10,2) DEFAULT 0,
    other_allowances DECIMAL(10,2) DEFAULT 0,
    social_security_salary DECIMAL(10,2),
    
    -- الإجازات | Leaves
    annual_leave_balance DECIMAL(5,2) DEFAULT 0,
    sick_leave_balance DECIMAL(5,2) DEFAULT 0,
    
    -- العقد | Contract
    contract_start_date DATE,
    contract_end_date DATE,
    contract_type VARCHAR(20),
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (company_id) REFERENCES core_company(id),
    FOREIGN KEY (department_id) REFERENCES hr_department(id),
    FOREIGN KEY (branch_id) REFERENCES hr_branch(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_employee_company ON hr_employee(company_id);
CREATE INDEX idx_employee_department ON hr_employee(department_id);
CREATE INDEX idx_employee_status ON hr_employee(status);
CREATE INDEX idx_employee_number ON hr_employee(employee_number);
```

#### 2. hr_payroll_movement | جدول حركات الرواتب

```sql
CREATE TABLE hr_payroll_movement (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- بيانات الحركة | Movement Data
    company_id INT NOT NULL,
    movement_number VARCHAR(20) UNIQUE NOT NULL,
    movement_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'new',
    notes TEXT,
    
    -- الإجماليات | Totals
    total_employees INT DEFAULT 0,
    total_earnings DECIMAL(12,2) DEFAULT 0,
    total_deductions DECIMAL(12,2) DEFAULT 0,
    total_net_salary DECIMAL(12,2) DEFAULT 0,
    total_ss_company DECIMAL(12,2) DEFAULT 0,
    
    -- الترحيل | Posting
    posted_at TIMESTAMP,
    posted_by INT,
    journal_entry_id INT,
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (company_id) REFERENCES core_company(id),
    FOREIGN KEY (posted_by) REFERENCES auth_user(id),
    FOREIGN KEY (journal_entry_id) REFERENCES accounting_journal_entry(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_movement_company ON hr_payroll_movement(company_id);
CREATE INDEX idx_movement_date ON hr_payroll_movement(movement_date);
CREATE INDEX idx_movement_status ON hr_payroll_movement(status);
```

#### 3. hr_payroll_movement_detail | جدول تفاصيل حركات الرواتب

```sql
CREATE TABLE hr_payroll_movement_detail (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- الربط | Relations
    movement_id INT NOT NULL,
    employee_id INT NOT NULL,
    
    -- الحضور | Attendance
    working_days DECIMAL(5,2) DEFAULT 0,
    worked_holidays DECIMAL(5,2) DEFAULT 0,
    overtime_hours DECIMAL(5,2) DEFAULT 0,
    
    -- الإجازات | Leaves
    annual_leaves_taken DECIMAL(5,2) DEFAULT 0,
    sick_leaves_taken DECIMAL(5,2) DEFAULT 0,
    paid_leaves DECIMAL(5,2) DEFAULT 0,
    unpaid_leaves DECIMAL(5,2) DEFAULT 0,
    
    -- المغادرات | Early Leaves
    early_leave_count INT DEFAULT 0,
    early_leave_hours DECIMAL(5,2) DEFAULT 0,
    
    -- ══════════════════════════════════════
    -- الاستحقاقات (7 مكونات)
    -- Earnings (7 Components)
    -- ══════════════════════════════════════
    basic_salary DECIMAL(10,2) DEFAULT 0,
    fuel_allowance DECIMAL(10,2) DEFAULT 0,
    other_allowances DECIMAL(10,2) DEFAULT 0,
    social_security_salary DECIMAL(10,2) DEFAULT 0,
    overtime_regular_days DECIMAL(10,2) DEFAULT 0,
    overtime_holidays DECIMAL(10,2) DEFAULT 0,
    other_earnings DECIMAL(10,2) DEFAULT 0,
    
    total_earnings DECIMAL(10,2) DEFAULT 0,
    
    -- ══════════════════════════════════════
    -- الخصومات (4 مكونات)
    -- Deductions (4 Components)
    -- ══════════════════════════════════════
    advances DECIMAL(10,2) DEFAULT 0,
    early_leave_deductions DECIMAL(10,2) DEFAULT 0,
    administrative_deductions DECIMAL(10,2) DEFAULT 0,
    social_security_employee DECIMAL(10,2) DEFAULT 0,
    
    total_deductions DECIMAL(10,2) DEFAULT 0,
    
    -- ══════════════════════════════════════
    -- التكاليف (1 مكون)
    -- Company Costs (1 Component)
    -- ══════════════════════════════════════
    social_security_company DECIMAL(10,2) DEFAULT 0,
    
    -- ══════════════════════════════════════
    -- النتيجة | Result
    -- ══════════════════════════════════════
    net_salary DECIMAL(10,2) DEFAULT 0,
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (movement_id) REFERENCES hr_payroll_movement(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES hr_employee(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_detail_movement ON hr_payroll_movement_detail(movement_id);
CREATE INDEX idx_detail_employee ON hr_payroll_movement_detail(employee_id);
```

#### 4. hr_employee_advance | جدول السلف

```sql
CREATE TABLE hr_employee_advance (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- بيانات السلفة | Advance Data
    company_id INT NOT NULL,
    advance_number VARCHAR(20) UNIQUE NOT NULL,
    employee_id INT NOT NULL,
    advance_date DATE NOT NULL,
    
    -- المبالغ | Amounts
    total_amount DECIMAL(10,2) NOT NULL,
    number_of_installments INT NOT NULL,
    installment_amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    remaining_amount DECIMAL(10,2),
    
    -- الحالة | Status
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (company_id) REFERENCES core_company(id),
    FOREIGN KEY (employee_id) REFERENCES hr_employee(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_advance_company ON hr_employee_advance(company_id);
CREATE INDEX idx_advance_employee ON hr_employee_advance(employee_id);
CREATE INDEX idx_advance_status ON hr_employee_advance(status);
```

#### 5. hr_advance_installment | جدول أقساط السلف

```sql
CREATE TABLE hr_advance_installment (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- بيانات القسط | Installment Data
    advance_id INT NOT NULL,
    installment_number INT NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    
    -- الحالة والسداد | Status & Payment
    status VARCHAR(20) DEFAULT 'pending',
    payment_date DATE,
    payroll_movement_id INT,
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (advance_id) REFERENCES hr_employee_advance(id) ON DELETE CASCADE,
    FOREIGN KEY (payroll_movement_id) REFERENCES hr_payroll_movement(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_installment_advance ON hr_advance_installment(advance_id);
CREATE INDEX idx_installment_status ON hr_advance_installment(status);
CREATE INDEX idx_installment_due_date ON hr_advance_installment(due_date);
```

#### 6. hr_leave_request | جدول طلبات الإجازات

```sql
CREATE TABLE hr_leave_request (
    -- المفتاح الأساسي | Primary Key
    id SERIAL PRIMARY KEY,
    
    -- بيانات الطلب | Request Data
    company_id INT NOT NULL,
    request_number VARCHAR(20) UNIQUE NOT NULL,
    employee_id INT NOT NULL,
    leave_type_id INT NOT NULL,
    
    -- تواريخ الإجازة | Leave Dates
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    number_of_days INT NOT NULL,
    reason TEXT,
    
    -- الموافقة | Approval
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INT,
    approval_date DATE,
    rejection_reason TEXT,
    
    -- المراجعة | Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT,
    
    -- المفاتيح الخارجية | Foreign Keys
    FOREIGN KEY (company_id) REFERENCES core_company(id),
    FOREIGN KEY (employee_id) REFERENCES hr_employee(id),
    FOREIGN KEY (leave_type_id) REFERENCES hr_leave_type(id),
    FOREIGN KEY (approved_by) REFERENCES auth_user(id)
);

-- الفهارس | Indexes
CREATE INDEX idx_leave_company ON hr_leave_request(company_id);
CREATE INDEX idx_leave_employee ON hr_leave_request(employee_id);
CREATE INDEX idx_leave_status ON hr_leave_request(status);
CREATE INDEX idx_leave_dates ON hr_leave_request(start_date, end_date);
```

---

## 16. خطة التنفيذ | Implementation Plan

### المرحلة 1: النماذج الأساسية | Phase 1: Core Models

**المدة الزمنية | Duration:** 3-5 أيام | 3-5 days

**المهام | Tasks:**
1. ✅ Employee Model - نموذج الموظف
2. ✅ Department Model - نموذج القسم
3. ✅ Branch Model - نموذج الفرع
4. ✅ Status Models - نماذج الحالات

**المخرجات | Deliverables:**
- نماذج Django كاملة | Complete Django models
- Migrations - ملفات الترحيل
- Admin Interface - واجهة الإدارة

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 2: الرواتب | Phase 2: Payroll

**المدة الزمنية | Duration:** 5-7 أيام | 5-7 days

**المهام | Tasks:**
1. ✅ PayrollMovement Model - نموذج حركة الراتب
2. ✅ PayrollMovementDetail Model - نموذج تفاصيل الحركة
3. ✅ Business Logic للحسابات | Calculation Business Logic
4. ✅ Automatic Calculations - الحسابات التلقائية

**المخرجات | Deliverables:**
- نماذج الرواتب | Payroll models
- منطق الأعمال | Business logic
- وحدات الاختبار | Unit tests

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 3: السلف والإجازات | Phase 3: Advances & Leaves

**المدة الزمنية | Duration:** 4-6 أيام | 4-6 days

**المهام | Tasks:**
1. ✅ EmployeeAdvance Model - نموذج السلفة
2. ✅ AdvanceInstallment Model - نموذج القسط
3. ✅ LeaveRequest Model - نموذج طلب الإجازة
4. ✅ LeaveBalance Model - نموذج رصيد الإجازة
5. ✅ Integration مع الرواتب | Payroll Integration

**المخرجات | Deliverables:**
- نماذج السلف والإجازات | Advances & leaves models
- منطق الربط مع الرواتب | Payroll integration logic

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 4: Forms & Views

**المدة الزمنية | Duration:** 5-7 أيام | 5-7 days

**المهام | Tasks:**
1. ✅ جميع الـ Forms | All Forms
2. ✅ جميع الـ Views | All Views
3. ✅ Ajax Endpoints
4. ✅ Permissions - الصلاحيات

**المخرجات | Deliverables:**
- نماذج الإدخال | Input forms
- Views للعرض والتعديل | Display & edit views
- API endpoints

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 5: Templates

**المدة الزمنية | Duration:** 7-10 أيام | 7-10 days

**المهام | Tasks:**
1. ✅ قوائم DataTables | DataTables lists
2. ✅ نماذج الإدخال | Input forms
3. ✅ شاشات العرض | Display screens
4. ✅ قسيمة الراتب (PDF) | Payslip (PDF)
5. ✅ RTL Support - دعم العربية

**المخرجات | Deliverables:**
- جميع الواجهات | All interfaces
- تصميم Material Design
- قسيمة الراتب | Payslip template

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 6: التقارير والتكامل | Phase 6: Reports & Integration

**المدة الزمنية | Duration:** 5-7 أيام | 5-7 days

**المهام | Tasks:**
1. ✅ جميع التقارير | All Reports
2. ✅ الربط المحاسبي | Accounting Integration
3. ✅ Export to Excel
4. ✅ PDF Generation

**المخرجات | Deliverables:**
- تقارير كاملة | Complete reports
- القيود المحاسبية التلقائية | Auto journal entries
- تصدير Excel و PDF | Excel & PDF export

**✋ الموافقة مطلوبة قبل الانتقال للمرحلة التالية**
**✋ Approval Required Before Next Phase**

---

### المرحلة 7: الاختبار والتوثيق | Phase 7: Testing & Documentation

**المدة الزمنية | Duration:** 5-7 أيام | 5-7 days

**المهام | Tasks:**
1. ✅ اختبار شامل | Comprehensive Testing
2. ✅ توثيق المستخدم | User Documentation
3. ✅ دليل الإدارة | Admin Guide
4. ✅ التدريب | Training

**المخرجات | Deliverables:**
- نظام مختبر وجاهز | Tested & ready system
- توثيق كامل | Complete documentation
- مواد تدريبية | Training materials

**✅ جاهز للإنتاج | Production Ready**

---

## 17. المتطلبات التقنية | Technical Requirements

### 17.1 البيئة التقنية | Technical Stack

#### Backend | الخلفية
```
Python >= 3.10
Django >= 4.2
PostgreSQL >= 13 or MySQL >= 8.0
```

#### Frontend | الواجهة الأمامية
```
Bootstrap 5
jQuery 3.6+
DataTables 1.13+
Select2 4.1+
SweetAlert2 11+
Cairo Font (Google Fonts)
```

#### Reporting | التقارير
```
ReportLab (PDF)
openpyxl (Excel)
Pillow (Images)
```

#### Server | الخادم
```
Apache with mod_wsgi
or
Nginx with Gunicorn
```

### 17.2 المتطلبات | Requirements

#### Python Packages | حزم Python
```python
# requirements.txt

Django>=4.2,<5.0
psycopg2-binary>=2.9  # للـ PostgreSQL | For PostgreSQL
# أو | or
mysqlclient>=2.1      # للـ MySQL | For MySQL

# التقارير | Reporting
reportlab>=4.0
openpyxl>=3.1
Pillow>=10.0

# المساعدة | Utilities
python-dateutil>=2.8
pytz>=2023.3

# الأمان | Security
django-environ>=0.11

# التطوير | Development
django-debug-toolbar>=4.2
```

---

## 18. ملاحظات مهمة | Important Notes

### 18.1 التوافق مع النظام القديم | Legacy System Compatibility

✅ **متوافق 100% مع Phoenix**
- جميع المكونات الـ 14 موجودة | All 14 components included
- نفس أسماء الحقول والمصطلحات | Same field names & terminology
- نفس طريقة الحسابات | Same calculation methods
- نفس شكل القسيمة | Same payslip format

### 18.2 التحسينات | Improvements

➕ **تحسينات على النظام القديم**
- واجهة حديثة وسهلة | Modern & user-friendly interface
- ربط تلقائي مع المحاسبة | Auto accounting integration
- تقارير أفضل وأشمل | Better & comprehensive reports
- نظام صلاحيات متقدم | Advanced permission system
- إمكانية التصدير والطباعة | Export & print capabilities
- نظام مراجعة كامل | Complete audit system

### 18.3 الامتثال | Compliance

✅ **الامتثال للأنظمة الأردنية**
- نسب الضمان الاجتماعي | Social Security rates
- قانون العمل الأردني | Jordanian Labor Law
- المعايير المحاسبية | Accounting Standards

### 18.4 الأمان | Security

🔒 **إجراءات الأمان**
- تشفير البيانات الحساسة | Encrypt sensitive data
- نظام صلاحيات محكم | Strict permission system
- سجل كامل للعمليات | Complete audit log
- حماية من SQL Injection
- حماية CSRF

### 18.5 الأداء | Performance

⚡ **تحسين الأداء**
- Server-side processing للجداول | For tables
- Pagination للبيانات الكبيرة | For large datasets
- Caching للحسابات | For calculations
- Database indexing - فهرسة قاعدة البيانات
- Query optimization - تحسين الاستعلامات

---

## 19. الخلاصة | Summary

### 19.1 نطاق المشروع | Project Scope

**النظام يشمل | System Includes:**
- ✅ إدارة كاملة للموظفين | Complete employee management
- ✅ نظام رواتب شامل (14 مكون) | Comprehensive payroll (14 components)
- ✅ إدارة السلف والأقساط | Advances & installments management
- ✅ نظام الإجازات الكامل | Complete leave management
- ✅ الضمان الاجتماعي | Social Security
- ✅ العقود والعلاوات | Contracts & increments
- ✅ تقارير شاملة | Comprehensive reports
- ✅ ربط محاسبي تلقائي | Automatic accounting integration
- ✅ نظام صلاحيات متقدم | Advanced permission system
- ✅ واجهة عربية RTL | Arabic RTL interface

### 19.2 الجاهزية | Readiness

**النظام جاهز للبناء مع | System Ready to Build With:**
- ✅ متطلبات كاملة وواضحة | Complete & clear requirements
- ✅ 100% توافق مع Phoenix | 100% Phoenix compatibility
- ✅ تصميم قاعدة بيانات محكم | Solid database design
- ✅ خطة تنفيذ واضحة | Clear implementation plan
- ✅ أفضل الممارسات | Best practices

### 19.3 المدة الزمنية الإجمالية | Total Duration

**إجمالي المدة المتوقعة | Expected Total Duration:**
```
المرحلة 1: 3-5 أيام   | Phase 1: 3-5 days
المرحلة 2: 5-7 أيام   | Phase 2: 5-7 days
المرحلة 3: 4-6 أيام   | Phase 3: 4-6 days
المرحلة 4: 5-7 أيام   | Phase 4: 5-7 days
المرحلة 5: 7-10 أيام  | Phase 5: 7-10 days
المرحلة 6: 5-7 أيام   | Phase 6: 5-7 days
المرحلة 7: 5-7 أيام   | Phase 7: 5-7 days
───────────────────────────────────────
الإجمالي: 34-49 يوم عمل | Total: 34-49 working days
أو | or
7-10 أسابيع | 7-10 weeks
```

---

## 20. جهات الاتصال | Contact Information

### معلومات المشروع | Project Information

**اسم المشروع | Project Name:**
نظام إدارة الموارد البشرية - UOP ERP
HR Management System - UOP ERP

**العميل | Client:**
ESCO Jordan - Engineering Stores Company

**الموقع | Location:**
Amman, Jordan

---

## 21. المراجع | References

### الوثائق المرجعية | Reference Documents

1. **Phoenix System Analysis** - تحليل نظام فينكس
2. **Jordanian Labor Law** - قانون العمل الأردني
3. **Social Security Law** - قانون الضمان الاجتماعي
4. **IAS/IFRS Standards** - المعايير المحاسبية الدولية

### الأنظمة المرجعية | Reference Systems

1. **Phoenix Payroll System** - نظام فينكس للرواتب
2. **UOP Accounting Module** - وحدة المحاسبة UOP
3. **Best Practices in HR Systems** - أفضل الممارسات

---

**تاريخ الإصدار | Release Date:** 2025-01-26
**الإصدار | Version:** 1.0
**الحالة | Status:** جاهز للتطوير | Ready for Development

---

# 🎯 النظام جاهز للبناء | System Ready to Build

**هل أنت مستعد للبدء؟ | Are You Ready to Start?**

---
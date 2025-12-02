"""
سكريبت بسيط لإنشاء بيانات تجريبية لكشوفات الرواتب
Simple script to create payroll demo data
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date, timedelta
from decimal import Decimal
from apps.hr.models import Payroll, PayrollDetail, Employee
from apps.core.models import Company, Branch

# الحصول على الشركة والفرع
company = Company.objects.first()
if not company:
    print("❌ لا توجد شركة في النظام!")
    exit(1)

branch = company.branches.first()
if not branch:
    print("❌ لا يوجد فرع في النظام!")
    exit(1)

# الحصول على الموظفين النشطين
employees = Employee.objects.filter(company=company, status='active', is_active=True)
if not employees.exists():
    print("❌ لا يوجد موظفين نشطين!")
    exit(1)

print(f"✅ تم العثور على {employees.count()} موظف نشط")

# إنشاء 3 كشوف رواتب (آخر 3 أشهر)
today = date.today()
payrolls_created = 0

for months_ago in range(2, -1, -1):  # 2, 1, 0 (آخر 3 أشهر)
    # حساب الشهر والسنة
    target_date = today - timedelta(days=30 * months_ago)
    period_month = target_date.month
    period_year = target_date.year

    # تواريخ الفترة
    from_date = date(period_year, period_month, 1)
    if period_month == 12:
        to_date = date(period_year, 12, 31)
    else:
        to_date = date(period_year, period_month + 1, 1) - timedelta(days=1)

    # رقم الكشف
    payroll_number = f'PR-{period_year}-{period_month:02d}-{branch.code}'

    # تحقق من عدم وجود كشف مسبق
    if Payroll.objects.filter(
        company=company,
        period_year=period_year,
        period_month=period_month,
        branch=branch
    ).exists():
        print(f"⚠️  كشف {payroll_number} موجود مسبقاً")
        continue

    # الحالة
    if months_ago >= 2:
        status = 'paid'
    elif months_ago == 1:
        status = 'approved'
    else:
        status = 'calculated'

    try:
        # إنشاء كشف الراتب
        payroll = Payroll.objects.create(
            company=company,
            branch=branch,
            number=payroll_number,
            period_year=period_year,
            period_month=period_month,
            from_date=from_date,
            to_date=to_date,
            status=status,
            employee_count=employees.count(),
            created_by=employees.first().created_by if employees.first().created_by else None,
        )

        # إنشاء تفاصيل الرواتب لكل موظف
        total_basic = Decimal('0')
        total_allowances = Decimal('0')
        total_deductions = Decimal('0')

        for employee in employees:
            # الراتب الأساسي
            basic_salary = employee.basic_salary or Decimal('500')

            # البدلات
            housing = employee.fuel_allowance or Decimal('0')
            transport = Decimal('50')
            phone = Decimal('30')
            food = Decimal('70')
            total_allowances_amt = housing + transport + phone + food

            # الخصومات (15% من الإجمالي)
            gross = basic_salary + total_allowances_amt
            total_deductions_amt = gross * Decimal('0.15')
            social_security = gross * Decimal('0.075')
            income_tax = gross * Decimal('0.05')

            # صافي الراتب
            net_salary = gross - total_deductions_amt

            # إنشاء تفاصيل الراتب
            PayrollDetail.objects.create(
                payroll=payroll,
                employee=employee,
                basic_salary=basic_salary,
                working_days=30,
                actual_days=30,
                housing_allowance=housing,
                transport_allowance=transport,
                phone_allowance=phone,
                food_allowance=food,
                other_allowances=Decimal('0'),
                total_allowances=total_allowances_amt,
                overtime_hours=Decimal('0'),
                overtime_amount=Decimal('0'),
                absence_deduction=Decimal('0'),
                late_deduction=Decimal('0'),
                loan_deduction=Decimal('0'),
                social_security_employee=social_security,
                social_security_company=social_security,
                income_tax=income_tax,
                other_deductions=Decimal('0'),
                total_deductions=total_deductions_amt,
                gross_salary=gross,
                net_salary=net_salary,
                payment_method='bank_transfer',
                is_paid=(status == 'paid'),
                paid_date=to_date if status == 'paid' else None,
            )

            # تجميع الإجماليات
            total_basic += basic_salary
            total_allowances += total_allowances_amt
            total_deductions += total_deductions_amt

        # تحديث إجماليات كشف الراتب
        payroll.total_basic = total_basic
        payroll.total_allowances = total_allowances
        payroll.total_deductions = total_deductions
        payroll.total_net = total_basic + total_allowances - total_deductions
        payroll.total_overtime = Decimal('0')
        payroll.total_loans = Decimal('0')
        payroll.total_social_security = total_deductions * Decimal('0.5')
        payroll.total_income_tax = total_deductions * Decimal('0.3')
        payroll.save()

        payrolls_created += 1
        print(f"✅ تم إنشاء كشف {payroll_number} - {payroll.period_display} ({status})")

    except Exception as e:
        print(f"❌ خطأ في كشف {payroll_number}: {str(e)}")
        import traceback
        traceback.print_exc()
        continue

print(f"\n✅ تم إنشاء {payrolls_created} كشف راتب بنجاح!")
print(f"🔗 يمكنك الآن زيارة: http://127.0.0.1:8000/hr/payroll/report/")

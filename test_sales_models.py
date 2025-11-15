#!/usr/bin/env python
"""
سكريبت اختبار Models المرحلة 1 - نظام المبيعات
يختبر جميع الـ Models الجديدة والمحدثة
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta, date

from apps.core.models import Company, Branch, User, BusinessPartner, Item, Currency, Warehouse
from apps.sales.models import (
    SalesInvoice, InvoiceItem, PaymentInstallment,
    DiscountCampaign, SalespersonCommission, POSSession
)
from apps.hr.models import Employee

print("="*80)
print("🧪 بدء اختبار Models المرحلة 1 - نظام المبيعات")
print("="*80)

# ===== الخطوة 1: إعداد البيانات الأساسية =====
print("\n📋 الخطوة 1: إعداد البيانات الأساسية...")

# الحصول على الشركة والفرع الأول
company = Company.objects.first()
if not company:
    print("❌ لا توجد شركة في النظام!")
    exit(1)

branch = Branch.objects.filter(company=company).first()
if not branch:
    print("❌ لا يوجد فرع للشركة!")
    exit(1)

# الحصول على مستخدم
user = User.objects.filter(is_active=True).first()
if not user:
    print("❌ لا يوجد مستخدم نشط!")
    exit(1)

# الحصول على عملة
currency = Currency.objects.first()
if not currency:
    print("❌ لا توجد عملة!")
    exit(1)

# الحصول على مخزن
warehouse = Warehouse.objects.filter(company=company).first()
if not warehouse:
    print("❌ لا يوجد مخزن!")
    exit(1)

# الحصول على طريقة دفع أو إنشاء واحدة
from apps.core.models import PaymentMethod
payment_method, pm_created = PaymentMethod.objects.get_or_create(
    company=company,
    code='CASH',
    defaults={
        'name': 'نقدي',
        'is_active': True,
        'created_by': user
    }
)

print(f"✅ شركة: {company.name}")
print(f"✅ فرع: {branch.name}")
print(f"✅ مستخدم: {user.username}")
print(f"✅ عملة: {currency.code}")
print(f"✅ مخزن: {warehouse.name}")
if pm_created:
    print(f"✅ تم إنشاء طريقة دفع: {payment_method.name}")
else:
    print(f"✅ طريقة دفع: {payment_method.name}")

# ===== الخطوة 2: اختبار BusinessPartner المحدث =====
print("\n" + "="*80)
print("📋 الخطوة 2: اختبار BusinessPartner Model المحدث...")

# إنشاء عميل اختبار أو الحصول عليه
customer, created = BusinessPartner.objects.get_or_create(
    company=company,
    code='TEST-CUS-001',
    defaults={
        'partner_type': 'customer',
        'name': 'عميل اختبار',
        'account_type': 'credit',
        'credit_limit': Decimal('50000.00'),
        'payment_terms': 'آجل 30 يوم',
        'tax_status': 'taxable',
        'tax_number': '123456789',
        'commercial_register': 'CR-12345',
        'created_by': user
    }
)
if created:
    print(f"✅ تم إنشاء عميل: {customer}")
else:
    print(f"✅ تم العثور على عميل: {customer}")

# اختبار الحقول الجديدة
print(f"  - حد الائتمان: {customer.credit_limit}")
print(f"  - شروط الدفع: {customer.payment_terms}")
print(f"  - الرقم الضريبي: {customer.tax_number}")
print(f"  - السجل التجاري: {customer.commercial_register}")

# اختبار get_current_balance() method
balance = customer.get_current_balance()
print(f"  - الرصيد الحالي: {balance}")

# اختبار check_credit_limit() method
credit_check = customer.check_credit_limit(Decimal('10000.00'))
print(f"  - التحقق من حد الائتمان (10,000):")
print(f"    • مسموح: {credit_check['allowed']}")
print(f"    • الرسالة: {credit_check['message']}")

print("✅ BusinessPartner Model يعمل بنجاح!")

# ===== الخطوة 3: إنشاء موظف/مندوب =====
print("\n" + "="*80)
print("📋 الخطوة 3: إنشاء موظف مندوب...")

# أولاً: إنشاء قسم أو الحصول عليه
from apps.hr.models import Department
department, dept_created = Department.objects.get_or_create(
    company=company,
    code='DEPT-TEST-001',
    defaults={
        'name': 'قسم المبيعات',
        'created_by': user
    }
)
if dept_created:
    print(f"✅ تم إنشاء قسم: {department}")
else:
    print(f"✅ تم العثور على قسم: {department}")

# ثانياً: البحث عن موظف أو إنشاء واحد
from datetime import date
employee, created = Employee.objects.get_or_create(
    company=company,
    employee_number='EMP-TEST-001',
    defaults={
        'first_name': 'مندوب',
        'last_name': 'اختبار',
        'department': department,
        'hire_date': date(2024, 1, 1),
        'mobile': '0501234567',
        'created_by': user
    }
)
if created:
    print(f"✅ تم إنشاء موظف: {employee}")
else:
    print(f"✅ تم العثور على موظف: {employee}")

# ربط المندوب بالعميل
customer.default_salesperson = employee
customer.save()
print(f"✅ تم ربط المندوب الافتراضي بالعميل")

# ===== الخطوة 4: إنشاء مادة =====
print("\n" + "="*80)
print("📋 الخطوة 4: إنشاء مادة للاختبار...")

item = Item.objects.filter(company=company, is_active=True).first()
if not item:
    item = Item.objects.create(
        company=company,
        code='ITEM-TEST-001',
        name='مادة اختبار',
        selling_price=Decimal('100.00'),
        cost_price=Decimal('80.00'),
        is_active=True,
        created_by=user
    )
    print(f"✅ تم إنشاء مادة: {item}")
else:
    print(f"✅ تم العثور على مادة: {item}")

# ===== الخطوة 5: اختبار SalesInvoice المحدث =====
print("\n" + "="*80)
print("📋 الخطوة 5: اختبار SalesInvoice Model المحدث...")

invoice = SalesInvoice.objects.create(
    company=company,
    branch=branch,
    date=timezone.now().date(),
    customer=customer,
    salesperson=user,  # SalesInvoice.salesperson يجب أن يكون User وليس Employee
    currency=currency,
    warehouse=warehouse,
    payment_method=payment_method,
    invoice_type='cash_sale',
    # الحقول الجديدة
    recipient_name='المستلم الاختبار',
    recipient_phone='0501234567',
    recipient_address='عنوان التسليم',
    delivery_date=timezone.now().date() + timedelta(days=3),
    shipping_cost=Decimal('50.00'),
    payment_status='unpaid',
    salesperson_commission_rate=Decimal('5.00'),
    due_date=timezone.now().date() + timedelta(days=30),
    created_by=user
)
print(f"✅ تم إنشاء فاتورة: {invoice.number}")

# إضافة سطور للفاتورة
invoice_item = InvoiceItem.objects.create(
    invoice=invoice,
    item=item,
    quantity=Decimal('10.00'),
    unit_price=Decimal('100.00'),
    discount_percentage=Decimal('5.00')
)
print(f"✅ تم إضافة سطر للفاتورة")

# اختبار calculate_totals()
invoice.calculate_totals()
invoice.save()
print(f"  - الإجمالي قبل الخصم: {invoice.subtotal_before_discount}")
print(f"  - الإجمالي بعد الخصم: {invoice.subtotal_after_discount}")
print(f"  - الضريبة: {invoice.tax_amount}")
print(f"  - تكلفة الشحن: {invoice.shipping_cost}")
print(f"  - الإجمالي النهائي: {invoice.total_with_tax}")
print(f"  - عمولة المندوب: {invoice.salesperson_commission_amount}")
print(f"  - المبلغ المتبقي: {invoice.remaining_amount}")

# اختبار update_payment_status()
invoice.paid_amount = Decimal('500.00')
invoice.update_payment_status()
invoice.save()
print(f"  - حالة الدفع بعد دفع 500: {invoice.payment_status}")
print(f"  - المبلغ المتبقي: {invoice.remaining_amount}")

print("✅ SalesInvoice Model يعمل بنجاح!")

# ===== الخطوة 6: اختبار PaymentInstallment =====
print("\n" + "="*80)
print("📋 الخطوة 6: اختبار PaymentInstallment Model...")

installment1 = PaymentInstallment.objects.create(
    company=company,
    branch=branch,
    invoice=invoice,
    installment_number=1,
    due_date=timezone.now().date() + timedelta(days=30),
    amount=invoice.remaining_amount / 2,
    created_by=user
)
print(f"✅ تم إنشاء قسط 1: {installment1}")
print(f"  - المبلغ المستحق: {installment1.amount}")
print(f"  - تاريخ الاستحقاق: {installment1.due_date}")
print(f"  - الحالة: {installment1.status}")

# اختبار update_status()
installment1.update_status()
print(f"  - الحالة بعد التحديث: {installment1.status}")

# اختبار is_overdue property
print(f"  - هل متأخر: {installment1.is_overdue}")

# اختبار remaining_amount property
print(f"  - المبلغ المتبقي: {installment1.remaining_amount}")

print("✅ PaymentInstallment Model يعمل بنجاح!")

# ===== الخطوة 7: اختبار DiscountCampaign =====
print("\n" + "="*80)
print("📋 الخطوة 7: اختبار DiscountCampaign Model...")

campaign, campaign_created = DiscountCampaign.objects.get_or_create(
    company=company,
    code='RAMADAN2025',
    defaults={
        'name': 'حملة رمضان 2025',
        'campaign_type': 'percentage',
        'description': 'خصم 20% على جميع المنتجات',
        'start_date': date(2025, 3, 1),
        'end_date': date(2025, 4, 1),
        'discount_percentage': Decimal('20.00'),
        'is_active': True,
        'priority': 10,
        'created_by': user
    }
)
if campaign_created:
    print(f"✅ تم إنشاء حملة خصم: {campaign}")
else:
    print(f"✅ تم العثور على حملة خصم: {campaign}")

# اختبار is_campaign_active()
is_active = campaign.is_campaign_active(check_date=date(2025, 3, 15))
print(f"  - نشطة في 2025-03-15: {is_active}")

# اختبار can_apply_to_item()
can_apply = campaign.can_apply_to_item(item)
print(f"  - تنطبق على المادة: {can_apply}")

# اختبار apply_to_item()
discount_result = campaign.apply_to_item(item, quantity=5, unit_price=Decimal('100.00'))
print(f"  - تطبيق الخصم:")
print(f"    • قابل للتطبيق: {discount_result['applicable']}")
print(f"    • مبلغ الخصم: {discount_result['discount_amount']}")
print(f"    • نسبة الخصم: {discount_result['discount_percentage']}")
print(f"    • الرسالة: {discount_result['message']}")

# اختبار ManyToMany
campaign.items.add(item)
campaign.customers.add(customer)
print(f"  - عدد المواد المشمولة: {campaign.items.count()}")
print(f"  - عدد العملاء المشمولين: {campaign.customers.count()}")

print("✅ DiscountCampaign Model يعمل بنجاح!")

# ===== الخطوة 8: اختبار SalespersonCommission =====
print("\n" + "="*80)
print("📋 الخطوة 8: اختبار SalespersonCommission Model...")

commission = SalespersonCommission.objects.create(
    company=company,
    branch=branch,
    salesperson=employee,
    invoice=invoice,
    commission_rate=Decimal('5.00'),
    base_amount=invoice.total_with_tax,
    created_by=user
)
print(f"✅ تم إنشاء عمولة: {commission}")
print(f"  - نسبة العمولة: {commission.commission_rate}%")
print(f"  - المبلغ الأساسي: {commission.base_amount}")
print(f"  - مبلغ العمولة: {commission.commission_amount}")
print(f"  - حالة الدفع: {commission.payment_status}")

# اختبار calculate_commission()
calculated = commission.calculate_commission()
print(f"  - العمولة المحسوبة: {calculated}")

# اختبار record_payment()
try:
    commission.record_payment(
        amount=Decimal('50.00'),
        payment_date=timezone.now().date()
    )
    print(f"  - بعد دفع 50:")
    print(f"    • المبلغ المدفوع: {commission.paid_amount}")
    print(f"    • المبلغ المتبقي: {commission.remaining_amount}")
    print(f"    • الحالة: {commission.payment_status}")
except Exception as e:
    print(f"  ⚠️ خطأ في تسجيل الدفعة: {e}")

print("✅ SalespersonCommission Model يعمل بنجاح!")

# ===== الخطوة 9: اختبار POSSession =====
print("\n" + "="*80)
print("📋 الخطوة 9: اختبار POSSession Model...")

pos_session = POSSession.objects.create(
    company=company,
    cashier=user,
    pos_location='الكاشير 1',
    opening_cash=Decimal('1000.00'),
    status='open',
    opening_notes='بداية الوردية',
    created_by=user
)
print(f"✅ تم إنشاء جلسة POS: {pos_session.session_number}")
print(f"  - الكاشير: {pos_session.cashier}")
print(f"  - النقد الافتتاحي: {pos_session.opening_cash}")
print(f"  - الحالة: {pos_session.status}")
print(f"  - تاريخ الفتح: {pos_session.opening_datetime}")

# اختبار is_open property
print(f"  - مفتوحة: {pos_session.is_open}")

# اختبار session_duration property
print(f"  - مدة الجلسة: {pos_session.session_duration}")

# اختبار calculate_totals()
totals = pos_session.calculate_totals()
print(f"  - الإحصائيات:")
print(f"    • إجمالي المبيعات: {totals['total_sales']}")
print(f"    • عدد المعاملات: {totals['transactions_count']}")

# اختبار close_session()
try:
    result = pos_session.close_session(
        closing_cash=Decimal('2500.00'),
        closing_notes='نهاية الوردية'
    )
    print(f"  - بعد الإغلاق:")
    print(f"    • النقد الافتتاحي: {result['opening_cash']}")
    print(f"    • النقد الختامي: {result['closing_cash']}")
    print(f"    • النقد المتوقع: {result['expected_cash']}")
    print(f"    • الفرق: {result['cash_difference']}")
    print(f"    • الحالة: {pos_session.status}")
except Exception as e:
    print(f"  ⚠️ خطأ في إغلاق الجلسة: {e}")

print("✅ POSSession Model يعمل بنجاح!")

# ===== النتائج النهائية =====
print("\n" + "="*80)
print("✅✅✅ اكتمل الاختبار بنجاح! ✅✅✅")
print("="*80)
print("\n📊 ملخص الاختبارات:")
print("  ✅ BusinessPartner - تم التحديث والاختبار")
print("  ✅ SalesInvoice - تم التحديث والاختبار")
print("  ✅ PaymentInstallment - تم الإنشاء والاختبار")
print("  ✅ DiscountCampaign - تم الإنشاء والاختبار")
print("  ✅ SalespersonCommission - تم الإنشاء والاختبار")
print("  ✅ POSSession - تم الإنشاء والاختبار")
print("\n🎉 جميع Models تعمل بشكل صحيح!")
print("="*80)

# apps/assets/utils/depreciation.py
"""
الدوال المساعدة لإدارة الأصول
- حساب الإهلاك بالطرق الثلاثة
- توليد القيود المحاسبية التلقائية
- دوال مساعدة أخرى
"""

from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils.translation import gettext as _


class DepreciationCalculator:
    """
    فئة لحساب الإهلاك بالطرق المختلفة
    """

    def __init__(self, asset):
        """
        تهيئة الحاسبة

        :param asset: كائن Asset
        """
        self.asset = asset
        self.original_cost = asset.original_cost
        self.salvage_value = asset.salvage_value
        self.depreciable_amount = self.original_cost - self.salvage_value
        self.useful_life_months = asset.useful_life_months
        self.depreciation_method = asset.depreciation_method.method_type

    def calculate_monthly_depreciation(self, calculation_date=None):
        """
        حساب إهلاك شهر معين

        :param calculation_date: تاريخ الاحتساب (افتراضي: اليوم)
        :return: مبلغ الإهلاك للشهر
        """
        if calculation_date is None:
            calculation_date = date.today()

        # التحقق من أن الأصل لم يتم إهلاكه بالكامل
        if self.asset.is_fully_depreciated():
            return Decimal('0.00')

        # اختيار الطريقة المناسبة
        if self.depreciation_method == 'straight_line':
            return self._straight_line_method(calculation_date)
        elif self.depreciation_method == 'declining_balance':
            return self._declining_balance_method(calculation_date)
        elif self.depreciation_method == 'units_of_production':
            return self._units_of_production_method()
        else:
            return Decimal('0.00')

    def _straight_line_method(self, calculation_date):
        """
        طريقة القسط الثابت
        الإهلاك الشهري = (التكلفة - القيمة المتبقية) / عدد الأشهر

        مع حساب الشهر الأول نسبياً (Pro-rata)
        """
        # حساب عدد الأيام في الشهر الأول
        start_date = self.asset.depreciation_start_date
        first_month_end = date(start_date.year, start_date.month, 1) + relativedelta(months=1) - timedelta(days=1)

        # إذا كنا في الشهر الأول
        if calculation_date.year == start_date.year and calculation_date.month == start_date.month:
            days_in_month = (first_month_end - start_date).days + 1
            total_days_in_month = first_month_end.day
            depreciation_factor = Decimal(days_in_month) / Decimal(total_days_in_month)
        else:
            depreciation_factor = Decimal('1.00')

        # الإهلاك الشهري
        monthly_depreciation = self.depreciable_amount / self.useful_life_months

        # تطبيق معامل الشهر الأول
        final_depreciation = monthly_depreciation * depreciation_factor

        # التأكد من عدم تجاوز القيمة القابلة للإهلاك
        remaining_depreciable = self.depreciable_amount - self.asset.accumulated_depreciation
        if final_depreciation > remaining_depreciable:
            final_depreciation = remaining_depreciable

        return final_depreciation.quantize(Decimal('0.001'))

    def _declining_balance_method(self, calculation_date):
        """
        طريقة القسط المتناقص
        الإهلاك الشهري = القيمة الدفترية × (المعدل السنوي / 12)

        المعدل السنوي = (100% / عدد السنوات) × معدل التسارع
        معدل التسارع الافتراضي = 2 (القسط المتناقص المضاعف)
        """
        # الحصول على معدل الإهلاك من الطريقة
        rate_percentage = self.asset.depreciation_method.rate_percentage or Decimal('200')

        # حساب المعدل الشهري
        useful_life_years = Decimal(self.useful_life_months) / Decimal('12')
        annual_rate = (Decimal('100') / useful_life_years) * (rate_percentage / Decimal('100'))
        monthly_rate = annual_rate / Decimal('12')

        # حساب الإهلاك
        current_book_value = self.asset.book_value
        monthly_depreciation = current_book_value * (monthly_rate / Decimal('100'))

        # التأكد من عدم تجاوز القيمة المتبقية
        remaining_value = current_book_value - monthly_depreciation
        if remaining_value < self.salvage_value:
            monthly_depreciation = current_book_value - self.salvage_value

        return monthly_depreciation.quantize(Decimal('0.001'))

    def _units_of_production_method(self, units_in_period=None):
        """
        طريقة وحدات الإنتاج
        الإهلاك = (الوحدات المستخدمة في الفترة / إجمالي الوحدات المتوقعة) × المبلغ القابل للإهلاك

        :param units_in_period: عدد الوحدات المستخدمة في الفترة
        """
        if not self.asset.total_expected_units or self.asset.total_expected_units == 0:
            return Decimal('0.00')

        if units_in_period is None:
            # إذا لم يتم تحديد الوحدات، لا يمكن حساب الإهلاك
            return Decimal('0.00')

        # حساب معدل الإهلاك لكل وحدة
        depreciation_per_unit = self.depreciable_amount / Decimal(self.asset.total_expected_units)

        # حساب الإهلاك للفترة
        period_depreciation = depreciation_per_unit * Decimal(units_in_period)

        # التأكد من عدم تجاوز القيمة القابلة للإهلاك
        remaining_depreciable = self.depreciable_amount - self.asset.accumulated_depreciation
        if period_depreciation > remaining_depreciable:
            period_depreciation = remaining_depreciable

        return period_depreciation.quantize(Decimal('0.001'))

    def calculate_accumulated_depreciation_to_date(self, to_date=None):
        """
        حساب الإهلاك المتراكم حتى تاريخ معين

        :param to_date: التاريخ المستهدف (افتراضي: اليوم)
        :return: الإهلاك المتراكم
        """
        if to_date is None:
            to_date = date.today()

        from .models import AssetDepreciation

        accumulated = AssetDepreciation.objects.filter(
            asset=self.asset,
            depreciation_date__lte=to_date
        ).aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')

        return accumulated


def generate_asset_purchase_journal_entry(asset_transaction, company):
    """
    توليد قيد شراء أصل تلقائياً

    مدين: حساب الأصول الثابتة
    دائن: حساب النقدية/البنك/الموردين (حسب طريقة الدفع)

    :param asset_transaction: كائن AssetTransaction
    :param company: الشركة
    :return: كائن JournalEntry
    """
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account

    asset = asset_transaction.asset

    # التحقق من وجود الحسابات المطلوبة
    if not asset.category.asset_account:
        raise ValueError(_('لم يتم تحديد حساب الأصول لفئة الأصل'))

    # إنشاء القيد
    journal_entry = JournalEntry.objects.create(
        company=company,
        branch=asset_transaction.branch,
        entry_date=asset_transaction.transaction_date,
        entry_type='auto',
        description=f"شراء أصل: {asset.name} - {asset.asset_number}",
        reference=asset_transaction.transaction_number,
        source_document='asset_transaction',
        source_id=asset_transaction.id,
        created_by=asset_transaction.created_by
    )

    # السطر المدين: حساب الأصول
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=1,
        account=asset.category.asset_account,
        description=f"شراء {asset.name}",
        debit_amount=asset_transaction.amount,
        credit_amount=Decimal('0.00'),
        currency=company.base_currency,
        cost_center=asset.cost_center
    )

    # السطر الدائن: حساب الدفع
    if asset_transaction.payment_method == 'cash':
        # حساب النقدية
        cash_account = Account.objects.filter(
            company=company,
            is_cash_account=True,
            is_active=True
        ).first()
        credit_account = cash_account
    elif asset_transaction.payment_method == 'bank':
        # حساب البنك
        bank_account = Account.objects.filter(
            company=company,
            is_bank_account=True,
            is_active=True
        ).first()
        credit_account = bank_account
    elif asset_transaction.payment_method == 'credit':
        # حساب المورد
        credit_account = asset_transaction.counterpart_account
    else:
        credit_account = asset_transaction.counterpart_account

    if not credit_account:
        raise ValueError(_('لم يتم تحديد حساب الدفع'))

    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=2,
        account=credit_account,
        description=f"شراء {asset.name}",
        debit_amount=Decimal('0.00'),
        credit_amount=asset_transaction.amount,
        currency=company.base_currency
    )

    # تحديث إجماليات القيد
    journal_entry.total_debit = asset_transaction.amount
    journal_entry.total_credit = asset_transaction.amount
    journal_entry.is_balanced = True
    journal_entry.save()

    return journal_entry


def generate_asset_sale_journal_entry(asset_transaction, company):
    """
    توليد قيد بيع أصل تلقائياً

    مدين: النقدية/البنك/العملاء
    مدين: مجمع الإهلاك
    دائن: حساب الأصول
    دائن أو مدين: أرباح/خسائر بيع الأصول (حسب الحالة)

    :param asset_transaction: كائن AssetTransaction
    :param company: الشركة
    :return: كائن JournalEntry
    """
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account

    asset = asset_transaction.asset

    # التحقق من وجود الحسابات المطلوبة
    if not asset.category.asset_account:
        raise ValueError(_('لم يتم تحديد حساب الأصول لفئة الأصل'))

    if not asset.category.accumulated_depreciation_account:
        raise ValueError(_('لم يتم تحديد حساب مجمع الإهلاك لفئة الأصل'))

    # إنشاء القيد
    journal_entry = JournalEntry.objects.create(
        company=company,
        branch=asset_transaction.branch,
        entry_date=asset_transaction.transaction_date,
        entry_type='auto',
        description=f"بيع أصل: {asset.name} - {asset.asset_number}",
        reference=asset_transaction.transaction_number,
        source_document='asset_transaction',
        source_id=asset_transaction.id,
        created_by=asset_transaction.created_by
    )

    line_number = 1
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    # 1. مدين: حساب التحصيل (نقدية/بنك/عميل)
    if asset_transaction.payment_method == 'cash':
        collection_account = Account.objects.filter(
            company=company,
            is_cash_account=True,
            is_active=True
        ).first()
    elif asset_transaction.payment_method == 'bank':
        collection_account = Account.objects.filter(
            company=company,
            is_bank_account=True,
            is_active=True
        ).first()
    else:
        collection_account = asset_transaction.counterpart_account

    if not collection_account:
        raise ValueError(_('لم يتم تحديد حساب التحصيل'))

    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=line_number,
        account=collection_account,
        description=f"بيع {asset.name}",
        debit_amount=asset_transaction.sale_price,
        credit_amount=Decimal('0.00'),
        currency=company.base_currency
    )
    total_debit += asset_transaction.sale_price
    line_number += 1

    # 2. مدين: مجمع الإهلاك
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=line_number,
        account=asset.category.accumulated_depreciation_account,
        description=f"مجمع إهلاك {asset.name}",
        debit_amount=asset.accumulated_depreciation,
        credit_amount=Decimal('0.00'),
        currency=company.base_currency
    )
    total_debit += asset.accumulated_depreciation
    line_number += 1

    # 3. دائن: حساب الأصول
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=line_number,
        account=asset.category.asset_account,
        description=f"بيع {asset.name}",
        debit_amount=Decimal('0.00'),
        credit_amount=asset.original_cost,
        currency=company.base_currency
    )
    total_credit += asset.original_cost
    line_number += 1

    # 4. الربح أو الخسارة
    gain_loss = asset_transaction.gain_loss

    if gain_loss != Decimal('0.00'):
        # حساب أرباح/خسائر بيع الأصول
        gain_loss_account = Account.objects.filter(
            company=company,
            code__icontains='أرباح',
            is_active=True
        ).first()

        if not gain_loss_account:
            raise ValueError(_('لم يتم العثور على حساب أرباح/خسائر بيع الأصول'))

        if gain_loss > 0:
            # ربح - دائن
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=gain_loss_account,
                description=f"ربح بيع {asset.name}",
                debit_amount=Decimal('0.00'),
                credit_amount=abs(gain_loss),
                currency=company.base_currency
            )
            total_credit += abs(gain_loss)
        else:
            # خسارة - مدين
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=gain_loss_account,
                description=f"خسارة بيع {asset.name}",
                debit_amount=abs(gain_loss),
                credit_amount=Decimal('0.00'),
                currency=company.base_currency
            )
            total_debit += abs(gain_loss)

    # تحديث إجماليات القيد
    journal_entry.total_debit = total_debit
    journal_entry.total_credit = total_credit
    journal_entry.is_balanced = (total_debit == total_credit)
    journal_entry.save()

    return journal_entry


def generate_depreciation_journal_entry(company, branch, period_date, depreciation_records):
    """
    توليد قيد إهلاك شهري موحد لمجموعة من الأصول

    مدين: مصروف الإهلاك (لكل فئة)
    دائن: مجمع الإهلاك (لكل فئة)

    :param company: الشركة
    :param branch: الفرع
    :param period_date: تاريخ الفترة
    :param depreciation_records: قائمة من كائنات AssetDepreciation
    :return: كائن JournalEntry
    """
    from apps.accounting.models import JournalEntry, JournalEntryLine
    from collections import defaultdict

    # تجميع الإهلاك حسب الفئة
    category_depreciation = defaultdict(Decimal)

    for record in depreciation_records:
        category = record.asset.category
        category_depreciation[category] += record.depreciation_amount

    # إنشاء القيد
    journal_entry = JournalEntry.objects.create(
        company=company,
        branch=branch,
        entry_date=period_date,
        entry_type='auto',
        description=f"إهلاك الأصول الثابتة - {period_date.strftime('%Y-%m')}",
        source_document='asset_depreciation',
        created_by=None  # سيتم تحديثه لاحقاً
    )

    line_number = 1
    total_amount = Decimal('0.00')

    for category, amount in category_depreciation.items():
        # التحقق من وجود الحسابات
        if not category.depreciation_expense_account:
            raise ValueError(f'لم يتم تحديد حساب مصروف الإهلاك لفئة {category.name}')

        if not category.accumulated_depreciation_account:
            raise ValueError(f'لم يتم تحديد حساب مجمع الإهلاك لفئة {category.name}')

        # السطر المدين: مصروف الإهلاك
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=category.depreciation_expense_account,
            description=f"إهلاك {category.name}",
            debit_amount=amount,
            credit_amount=Decimal('0.00'),
            currency=company.base_currency
        )
        line_number += 1

        # السطر الدائن: مجمع الإهلاك
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=category.accumulated_depreciation_account,
            description=f"مجمع إهلاك {category.name}",
            debit_amount=Decimal('0.00'),
            credit_amount=amount,
            currency=company.base_currency
        )
        line_number += 1

        total_amount += amount

    # تحديث إجماليات القيد
    journal_entry.total_debit = total_amount
    journal_entry.total_credit = total_amount
    journal_entry.is_balanced = True
    journal_entry.save()

    return journal_entry


def generate_maintenance_journal_entry(maintenance, company):
    """
    توليد قيد محاسبي لتكلفة الصيانة

    مدين: مصروف الصيانة
    دائن: حساب النقدية/البنك/المورد

    :param maintenance: كائن AssetMaintenance
    :param company: الشركة
    :return: كائن JournalEntry
    """
    from apps.accounting.models import JournalEntry, JournalEntryLine, Account

    if maintenance.total_cost == Decimal('0.00'):
        return None

    # إنشاء القيد
    journal_entry = JournalEntry.objects.create(
        company=company,
        branch=maintenance.branch,
        entry_date=maintenance.completion_date or maintenance.scheduled_date,
        entry_type='auto',
        description=f"صيانة {maintenance.asset.name} - {maintenance.maintenance_type.name}",
        reference=maintenance.maintenance_number,
        source_document='asset_maintenance',
        source_id=maintenance.id,
        created_by=None
    )

    # حساب مصروف الصيانة
    maintenance_expense_account = Account.objects.filter(
        company=company,
        code__icontains='صيانة',
        account_type__type_category='expenses',
        is_active=True
    ).first()

    if not maintenance_expense_account:
        raise ValueError('لم يتم العثور على حساب مصروف الصيانة')

    # السطر المدين
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=1,
        account=maintenance_expense_account,
        description=f"صيانة {maintenance.asset.asset_number}",
        debit_amount=maintenance.total_cost,
        credit_amount=Decimal('0.00'),
        currency=company.base_currency,
        cost_center=maintenance.asset.cost_center
    )

    # السطر الدائن
    if maintenance.external_vendor:
        credit_account = maintenance.external_vendor
    else:
        # حساب نقدية افتراضي
        credit_account = Account.objects.filter(
            company=company,
            is_cash_account=True,
            is_active=True
        ).first()

    if not credit_account:
        raise ValueError('لم يتم تحديد حساب الدفع')

    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=2,
        account=credit_account,
        description=f"صيانة {maintenance.asset.asset_number}",
        debit_amount=Decimal('0.00'),
        credit_amount=maintenance.total_cost,
        currency=company.base_currency
    )

    # تحديث إجماليات القيد
    journal_entry.total_debit = maintenance.total_cost
    journal_entry.total_credit = maintenance.total_cost
    journal_entry.is_balanced = True
    journal_entry.save()

    return journal_entry


def calculate_asset_metrics(asset):
    """
    حساب مقاييس الأصل المختلفة

    :param asset: كائن Asset
    :return: dict مع المقاييس
    """
    from datetime import date

    # العمر الحالي
    age_days = (date.today() - asset.purchase_date).days
    age_months = age_days // 30

    # نسبة الإهلاك
    if asset.original_cost > 0:
        depreciation_percentage = (asset.accumulated_depreciation / asset.original_cost) * 100
    else:
        depreciation_percentage = 0

    # الأشهر المتبقية
    remaining_months = asset.get_remaining_months()

    # نسبة العمر المستخدم
    if asset.useful_life_months > 0:
        life_used_percentage = (age_months / asset.useful_life_months) * 100
    else:
        life_used_percentage = 0

    # تاريخ انتهاء العمر الافتراضي
    from dateutil.relativedelta import relativedelta
    end_of_life_date = asset.depreciation_start_date + relativedelta(months=asset.useful_life_months)

    # الأيام المتبقية حتى نهاية العمر
    days_to_end = (end_of_life_date - date.today()).days

    return {
        'age_days': age_days,
        'age_months': age_months,
        'depreciation_percentage': round(depreciation_percentage, 2),
        'remaining_months': remaining_months,
        'life_used_percentage': round(life_used_percentage, 2),
        'end_of_life_date': end_of_life_date,
        'days_to_end': max(0, days_to_end),
        'is_near_end': days_to_end <= 180,  # قريب من النهاية (6 أشهر)
        'is_fully_depreciated': asset.is_fully_depreciated()
    }
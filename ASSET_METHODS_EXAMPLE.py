# ============================================================
# مثال توضيحي: Asset Model Methods المحاسبية المطلوبة
# ============================================================
# هذا ملف توضيحي - ليس للاستخدام المباشر
# الهدف: توضيح ماذا نقصد بـ "Asset Model Methods"
# ============================================================

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Asset(DocumentBaseModel):
    """
    الأصل الثابت - مع Methods محاسبية كاملة
    """

    # ============================================================
    # 1️⃣ عند شراء الأصل
    # ============================================================

    @transaction.atomic
    def create_purchase_journal_entry(self):
        """
        إنشاء قيد شراء الأصل تلقائياً

        القيد:
            مدين: حساب الأصول (من الفئة)
            دائن: حساب الموردين أو النقدية

        مثال:
            asset = Asset.objects.get(pk=1)
            journal_entry = asset.create_purchase_journal_entry()
            print(journal_entry.number)  # "JV/2025/000123"
        """
        from apps.accounting.models import JournalEntry, JournalEntryLine

        # ✅ التحقق من الحسابات المحاسبية
        if not self.category.asset_account:
            raise ValidationError(
                f'لم يتم تحديد حساب الأصول للفئة {self.category.name}'
            )

        # ✅ تحديد حساب الدفع (مورد أو نقدية)
        if self.supplier:
            # إذا كان هناك مورد، استخدم حساب الموردين
            payment_account = self.supplier.supplier_account
            if not payment_account:
                # حساب الموردين الافتراضي
                payment_account = Account.objects.get(
                    company=self.company,
                    code='210100'  # الموردين
                )
        else:
            # إذا لم يكن هناك مورد، استخدم الصندوق
            payment_account = Account.objects.get(
                company=self.company,
                code='110200'  # الصندوق
            )

        # ✅ إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            entry_date=self.purchase_date,
            entry_type='asset_purchase',  # نوع القيد
            description=f'شراء أصل ثابت: {self.name}',
            reference=self.asset_number,
            source_model='asset',
            source_id=self.id,
            status='draft'  # مسودة - يحتاج ترحيل
        )

        # ✅ السطر الأول: مدين حساب الأصول
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=self.category.asset_account,
            description=f'شراء {self.name}',
            debit_amount=self.purchase_price,
            credit_amount=0,
            currency=self.currency,
            cost_center=self.cost_center
        )

        # ✅ السطر الثاني: دائن حساب الدفع
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=payment_account,
            description=f'دفع ثمن {self.name}',
            debit_amount=0,
            credit_amount=self.purchase_price,
            currency=self.currency
        )

        # ✅ حساب إجماليات القيد
        journal_entry.calculate_totals()

        # ✅ حفظ رابط القيد في الأصل
        self.purchase_journal_entry = journal_entry
        self.save(update_fields=['purchase_journal_entry'])

        return journal_entry


    # ============================================================
    # 2️⃣ عند بيع الأصل
    # ============================================================

    @transaction.atomic
    def create_sale_journal_entry(self, sale_price, sale_date, buyer=None):
        """
        إنشاء قيد بيع الأصل مع حساب الربح أو الخسارة

        القيد:
            1. إذا كان ربح:
               مدين: النقدية/العملاء (سعر البيع)
               مدين: مجمع الإهلاك (المجمع حتى الآن)
               دائن: الأصل (التكلفة الأصلية)
               دائن: ربح بيع أصول (الفرق)

            2. إذا كان خسارة:
               مدين: النقدية/العملاء (سعر البيع)
               مدين: مجمع الإهلاك (المجمع حتى الآن)
               مدين: خسارة بيع أصول (الفرق)
               دائن: الأصل (التكلفة الأصلية)

        مثال:
            asset = Asset.objects.get(pk=1)
            # بيع بـ 50,000 بينما القيمة الدفترية 40,000
            journal_entry = asset.create_sale_journal_entry(
                sale_price=Decimal('50000'),
                sale_date='2025-01-15'
            )
            # النتيجة: ربح 10,000
        """
        from apps.accounting.models import JournalEntry, JournalEntryLine, Account

        # ✅ التحقق من الحسابات
        if not self.category.asset_account:
            raise ValidationError('لم يتم تحديد حساب الأصول')
        if not self.category.accumulated_depreciation_account:
            raise ValidationError('لم يتم تحديد حساب مجمع الإهلاك')

        # ✅ حساب القيمة الدفترية الحالية
        book_value = self.get_current_book_value()
        accumulated_dep = self.get_total_accumulated_depreciation()

        # ✅ حساب الربح أو الخسارة
        gain_or_loss = sale_price - book_value

        # ✅ تحديد حساب المدين (نقدية أو عميل)
        if buyer:
            cash_account = buyer.customer_account
        else:
            cash_account = Account.objects.get(
                company=self.company,
                code='110200'  # الصندوق
            )

        # ✅ إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            entry_date=sale_date,
            entry_type='asset_sale',
            description=f'بيع أصل ثابت: {self.name}',
            reference=f'SALE-{self.asset_number}',
            source_model='assettransaction',
            status='draft'
        )

        line_number = 1

        # ✅ السطر 1: مدين النقدية/العميل (سعر البيع)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=cash_account,
            description=f'استلام ثمن بيع {self.name}',
            debit_amount=sale_price,
            credit_amount=0,
            currency=self.currency
        )
        line_number += 1

        # ✅ السطر 2: مدين مجمع الإهلاك
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=self.category.accumulated_depreciation_account,
            description=f'إقفال مجمع إهلاك {self.name}',
            debit_amount=accumulated_dep,
            credit_amount=0,
            currency=self.currency
        )
        line_number += 1

        # ✅ السطر 3: دائن حساب الأصل (التكلفة الأصلية)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=self.category.asset_account,
            description=f'إقفال {self.name}',
            debit_amount=0,
            credit_amount=self.purchase_price,
            currency=self.currency,
            cost_center=self.cost_center
        )
        line_number += 1

        # ✅ السطر 4: الربح أو الخسارة
        if gain_or_loss > 0:
            # ربح: دائن
            if not self.category.gain_on_sale_account:
                raise ValidationError('لم يتم تحديد حساب ربح بيع الأصول')

            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=self.category.gain_on_sale_account,
                description=f'ربح بيع {self.name}',
                debit_amount=0,
                credit_amount=abs(gain_or_loss),
                currency=self.currency
            )
        elif gain_or_loss < 0:
            # خسارة: مدين
            if not self.category.loss_on_disposal_account:
                raise ValidationError('لم يتم تحديد حساب خسارة الأصول')

            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=self.category.loss_on_disposal_account,
                description=f'خسارة بيع {self.name}',
                debit_amount=abs(gain_or_loss),
                credit_amount=0,
                currency=self.currency
            )

        journal_entry.calculate_totals()

        # ✅ تحديث حالة الأصل
        self.status = 'sold'
        self.disposal_date = sale_date
        self.disposal_value = sale_price
        self.save(update_fields=['status', 'disposal_date', 'disposal_value'])

        return journal_entry


    # ============================================================
    # 3️⃣ عند استبعاد الأصل (بدون بيع - تلف، فقد، إلخ)
    # ============================================================

    @transaction.atomic
    def create_disposal_journal_entry(self, disposal_date, disposal_reason):
        """
        إنشاء قيد استبعاد الأصل (خسارة كاملة)

        القيد:
            مدين: مجمع الإهلاك
            مدين: خسارة استبعاد الأصول (القيمة الدفترية المتبقية)
            دائن: حساب الأصول

        مثال:
            asset = Asset.objects.get(pk=1)
            # الأصل تالف ولا يمكن بيعه
            journal_entry = asset.create_disposal_journal_entry(
                disposal_date='2025-01-15',
                disposal_reason='تالف بسبب حريق'
            )
        """
        from apps.accounting.models import JournalEntry, JournalEntryLine

        if not self.category.loss_on_disposal_account:
            raise ValidationError('لم يتم تحديد حساب خسارة الاستبعاد')

        book_value = self.get_current_book_value()
        accumulated_dep = self.get_total_accumulated_depreciation()

        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            entry_date=disposal_date,
            entry_type='asset_disposal',
            description=f'استبعاد أصل: {self.name} - {disposal_reason}',
            reference=f'DISP-{self.asset_number}',
            status='draft'
        )

        # مدين: مجمع الإهلاك
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=self.category.accumulated_depreciation_account,
            description=f'إقفال مجمع إهلاك {self.name}',
            debit_amount=accumulated_dep,
            credit_amount=0
        )

        # مدين: خسارة الاستبعاد (القيمة الدفترية)
        if book_value > 0:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                line_number=2,
                account=self.category.loss_on_disposal_account,
                description=f'خسارة استبعاد {self.name}',
                debit_amount=book_value,
                credit_amount=0
            )

        # دائن: حساب الأصل
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=3,
            account=self.category.asset_account,
            description=f'إقفال {self.name}',
            debit_amount=0,
            credit_amount=self.purchase_price,
            cost_center=self.cost_center
        )

        journal_entry.calculate_totals()

        # تحديث حالة الأصل
        self.status = 'disposed'
        self.disposal_date = disposal_date
        self.disposal_reason = disposal_reason
        self.save()

        return journal_entry


    # ============================================================
    # 4️⃣ عند تحويل الأصل بين الفروع
    # ============================================================

    @transaction.atomic
    def create_transfer_journal_entry(self, to_branch, to_cost_center=None, transfer_date=None):
        """
        إنشاء قيد تحويل الأصل (إن كان مطلوباً)

        ملاحظة: قد لا يحتاج قيد محاسبي، لكن فقط تحديث الفرع ومركز التكلفة

        مثال:
            asset = Asset.objects.get(pk=1)
            new_branch = Branch.objects.get(code='BR02')
            asset.create_transfer_journal_entry(
                to_branch=new_branch,
                transfer_date='2025-01-15'
            )
        """
        from apps.accounting.models import JournalEntry, JournalEntryLine
        from datetime import date

        if not transfer_date:
            transfer_date = date.today()

        # في الأغلب لا يحتاج قيد، فقط تحديث البيانات
        old_branch = self.branch
        old_cost_center = self.cost_center

        self.branch = to_branch
        if to_cost_center:
            self.cost_center = to_cost_center

        self.save()

        # سجل في AssetTransfer model
        from apps.assets.models import AssetTransfer
        transfer = AssetTransfer.objects.create(
            company=self.company,
            branch=old_branch,
            asset=self,
            from_branch=old_branch,
            to_branch=to_branch,
            from_cost_center=old_cost_center,
            to_cost_center=to_cost_center,
            transfer_date=transfer_date,
            created_by=None  # سيتم تمريره من الـ view
        )

        return transfer


    # ============================================================
    # 5️⃣ Validation Methods - تحديد متى يمكن التعديل/الحذف
    # ============================================================

    def can_edit(self):
        """
        هل يمكن تعديل الأصل؟

        Returns:
            bool: True إذا كان يمكن التعديل

        القواعد:
            - لا يمكن تعديل أصل مباع أو مستبعد
            - يمكن تعديل الأصول النشطة فقط
        """
        if self.status in ['sold', 'disposed']:
            return False

        # إذا كان له قيود مرحلة، لا يمكن التعديل
        if hasattr(self, 'purchase_journal_entry') and self.purchase_journal_entry:
            if self.purchase_journal_entry.status == 'posted':
                return False

        return True

    def can_delete(self):
        """
        هل يمكن حذف الأصل؟

        Returns:
            bool: True إذا كان يمكن الحذف

        القواعد:
            - لا يمكن حذف أصل له إهلاك محسوب
            - لا يمكن حذف أصل له معاملات
            - لا يمكن حذف أصل مرحّل محاسبياً
        """
        # إذا كان له إهلاك
        if self.depreciations.exists():
            return False

        # إذا كان له معاملات
        if hasattr(self, 'transactions') and self.transactions.exists():
            return False

        # إذا كان له قيد مرحّل
        if hasattr(self, 'purchase_journal_entry') and self.purchase_journal_entry:
            if self.purchase_journal_entry.status == 'posted':
                return False

        return True

    def can_depreciate(self):
        """هل يمكن إهلاك الأصل؟"""
        if self.status != 'active':
            return False

        if self.depreciation_status != 'active':
            return False

        if self.is_fully_depreciated():
            return False

        return True


    # ============================================================
    # 6️⃣ Helper Methods - دوال مساعدة
    # ============================================================

    def get_current_book_value(self):
        """
        حساب القيمة الدفترية الحالية

        Returns:
            Decimal: القيمة الدفترية = التكلفة - مجمع الإهلاك
        """
        return self.purchase_price - self.get_total_accumulated_depreciation()

    def get_total_accumulated_depreciation(self):
        """
        مجموع الإهلاك المتراكم حتى الآن

        Returns:
            Decimal: مجموع الإهلاك
        """
        from apps.assets.models import AssetDepreciation

        total = AssetDepreciation.objects.filter(
            asset=self,
            status='posted'  # فقط المرحّل
        ).aggregate(
            total=Sum('depreciation_amount')
        )['total'] or Decimal('0')

        return total

    def is_fully_depreciated(self):
        """
        هل الأصل مُهلك بالكامل؟

        Returns:
            bool: True إذا وصل الإهلاك للحد الأقصى
        """
        depreciable_amount = self.purchase_price - self.salvage_value
        accumulated = self.get_total_accumulated_depreciation()

        return accumulated >= depreciable_amount

    def get_payment_account(self):
        """
        الحصول على حساب الدفع المناسب (مورد أو نقدية)

        Returns:
            Account: الحساب المحاسبي للدفع
        """
        from apps.accounting.models import Account

        if self.supplier and self.supplier.supplier_account:
            return self.supplier.supplier_account

        # الحساب الافتراضي: الصندوق
        return Account.objects.get(
            company=self.company,
            code='110200'
        )


# ============================================================
# ============================================================
# المثال الثاني: AssetMaintenance Methods
# ============================================================
# ============================================================

class AssetMaintenance(DocumentBaseModel):
    """
    الصيانة - مع Methods محاسبية
    """

    @transaction.atomic
    def create_journal_entry(self):
        """
        إنشاء قيد الصيانة

        القواعد:
            1. إذا كانت صيانة وقائية → مصروف
            2. إذا كانت صيانة تحسينية → إضافة لقيمة الأصل

        القيد (صيانة وقائية):
            مدين: مصروف الصيانة
            دائن: النقدية/الموردين

        القيد (صيانة تحسينية):
            مدين: حساب الأصل (زيادة قيمته)
            دائن: النقدية/الموردين
        """
        from apps.accounting.models import JournalEntry, JournalEntryLine

        if self.status != 'completed':
            raise ValidationError('يجب إتمام الصيانة أولاً')

        if not self.actual_cost or self.actual_cost == 0:
            raise ValidationError('يجب تحديد التكلفة الفعلية')

        # تحديد نوع الصيانة
        if self.maintenance_type.is_capital_improvement:
            # صيانة تحسينية = إضافة للأصل
            expense_account = self.asset.category.asset_account
            description_prefix = 'تحسين رأسمالي'
        else:
            # صيانة وقائية = مصروف
            expense_account = (
                self.asset.category.maintenance_expense_account or
                Account.objects.get(company=self.company, code='520300')
            )
            description_prefix = 'مصروف صيانة'

        # إنشاء القيد
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            entry_date=self.actual_end_date or self.scheduled_date,
            entry_type='maintenance',
            description=f'{description_prefix} - {self.asset.name}',
            reference=self.maintenance_number,
            source_model='assetmaintenance',
            source_id=self.id,
            status='draft'
        )

        # مدين: مصروف الصيانة أو الأصل
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=expense_account,
            description=f'صيانة {self.asset.name} - {self.maintenance_type.name}',
            debit_amount=self.actual_cost,
            credit_amount=0,
            cost_center=self.asset.cost_center
        )

        # دائن: الموردين أو النقدية
        payment_account = self.get_payment_account()
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=payment_account,
            description=f'دفع صيانة {self.asset.name}',
            debit_amount=0,
            credit_amount=self.actual_cost
        )

        journal_entry.calculate_totals()

        # حفظ رابط القيد
        self.journal_entry = journal_entry
        self.save(update_fields=['journal_entry'])

        # إذا كانت تحسينية، زيادة قيمة الأصل
        if self.maintenance_type.is_capital_improvement:
            self.asset.purchase_price += self.actual_cost
            self.asset.save(update_fields=['purchase_price'])

        return journal_entry

    def get_payment_account(self):
        """حساب الدفع للصيانة"""
        from apps.accounting.models import Account

        if self.supplier and self.supplier.supplier_account:
            return self.supplier.supplier_account

        return Account.objects.get(company=self.company, code='110200')


# ============================================================
# الخلاصة
# ============================================================
"""
ماذا نقصد بـ "Asset Model Methods"؟

نقصد: إضافة دوال (functions) في الـ Model نفسه لإنشاء القيود المحاسبية
بدلاً من كتابة هذا الكود في الـ Views وتكراره.

الفوائد:
✅ عدم تكرار الكود (DRY - Don't Repeat Yourself)
✅ سهولة الصيانة (كل الكود المحاسبي في مكان واحد)
✅ إمكانية استدعاء الـ method من أي مكان (views, signals, management commands)
✅ Testing أسهل (اختبار method واحدة بدل عدة views)
✅ Business Logic في الـ Model وليس الـ View

المطلوب إضافته في Asset Model:
1. create_purchase_journal_entry()         ✅ ناقص
2. create_sale_journal_entry()             ✅ ناقص
3. create_disposal_journal_entry()         ✅ ناقص
4. create_transfer_journal_entry()         ✅ ناقص
5. calculate_monthly_depreciation()        ✅ موجود!
6. can_edit()                              ✅ ناقص
7. can_delete()                            ✅ ناقص
8. can_depreciate()                        ✅ ناقص
9. get_current_book_value()                ✅ موجود جزئياً
10. get_total_accumulated_depreciation()   ✅ ناقص
11. is_fully_depreciated()                 ✅ موجود جزئياً
12. get_payment_account()                  ✅ ناقص

ثم نفس الشيء لـ:
- AssetMaintenance model
- AssetInsurance model
- AssetTransaction model
- PhysicalCountAdjustment model
"""

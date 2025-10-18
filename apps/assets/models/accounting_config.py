# apps/assets/models/accounting_config.py
"""
إعدادات الحسابات المحاسبية للأصول
- ربط ديناميكي 100% مع المحاسبة
- لا يوجد hard-coding
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


class AssetAccountingConfiguration(BaseModel):
    """إعدادات الحسابات المحاسبية للأصول على مستوى الشركة"""

    # ==================== حسابات الصيانة ====================
    default_maintenance_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_maint_expense',
        verbose_name=_('حساب مصروف الصيانة الافتراضي'),
        null=True,
        blank=True,
        help_text=_('يُستخدم إذا لم يحدد في الفئة')
    )

    capital_improvement_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_capital_improvement',
        verbose_name=_('حساب التحسينات الرأسمالية'),
        null=True,
        blank=True,
        help_text=_('يُضاف للأصل عند التحسينات الرأسمالية')
    )

    # ==================== حسابات الإيجار ====================
    operating_lease_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_op_lease_exp',
        verbose_name=_('حساب مصروف الإيجار التشغيلي'),
        null=True,
        blank=True
    )

    finance_lease_liability_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_fin_lease_liab',
        verbose_name=_('حساب التزامات الإيجار التمويلي'),
        null=True,
        blank=True
    )

    finance_lease_interest_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_fin_lease_int',
        verbose_name=_('حساب مصروف فوائد الإيجار التمويلي'),
        null=True,
        blank=True
    )

    # ==================== حسابات التأمين ====================
    insurance_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_insurance_exp',
        verbose_name=_('حساب مصروف التأمين'),
        null=True,
        blank=True
    )

    insurance_deductible_expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_insurance_deduct',
        verbose_name=_('حساب مصروف تحمل التأمين'),
        null=True,
        blank=True
    )

    insurance_claim_income_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_insurance_income',
        verbose_name=_('حساب إيرادات تعويضات التأمين'),
        null=True,
        blank=True
    )

    # ==================== حسابات عامة ====================
    default_cash_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_default_cash',
        verbose_name=_('حساب النقدية الافتراضي'),
        null=True,
        blank=True,
        help_text=_('حساب الصندوق الافتراضي للمدفوعات')
    )

    default_bank_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_default_bank',
        verbose_name=_('حساب البنك الافتراضي'),
        null=True,
        blank=True
    )

    default_supplier_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='companies_default_supplier',
        verbose_name=_('حساب الموردين الافتراضي'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('إعدادات حسابات الأصول')
        verbose_name_plural = _('إعدادات حسابات الأصول')

    def __str__(self):
        return f"إعدادات حسابات {self.company.name}"

    @classmethod
    def get_or_create_for_company(cls, company):
        """الحصول على الإعدادات أو إنشاؤها"""
        config, created = cls.objects.get_or_create(
            company=company,
            defaults={'created_by': None, 'is_active': True}
        )
        return config

    # ==================== دوال مساعدة ====================

    def get_maintenance_expense_account(self, category=None):
        """الحصول على حساب مصروف الصيانة"""
        # أولاً: من الفئة
        if category and hasattr(category, 'maintenance_expense_account') and category.maintenance_expense_account:
            return category.maintenance_expense_account
        # ثانياً: من الإعدادات العامة
        if self.default_maintenance_expense_account:
            return self.default_maintenance_expense_account
        # ثالثاً: رمي خطأ
        raise ValidationError(
            _('لم يتم تحديد حساب مصروف الصيانة. يرجى تحديده في إعدادات الأصول أو في فئة الأصل.')
        )

    def get_cash_account(self):
        """الحصول على حساب النقدية"""
        if self.default_cash_account:
            return self.default_cash_account
        if self.default_bank_account:
            return self.default_bank_account
        raise ValidationError(
            _('لم يتم تحديد حساب نقدية افتراضي. يرجى تحديده في إعدادات الأصول.')
        )

    def get_bank_account(self):
        """الحصول على حساب البنك"""
        if self.default_bank_account:
            return self.default_bank_account
        if self.default_cash_account:
            return self.default_cash_account
        raise ValidationError(
            _('لم يتم تحديد حساب بنك افتراضي. يرجى تحديده في إعدادات الأصول.')
        )

    def get_supplier_account(self, supplier=None):
        """الحصول على حساب المورد"""
        if supplier and supplier.supplier_account:
            return supplier.supplier_account
        if self.default_supplier_account:
            return self.default_supplier_account
        raise ValidationError(
            _('لم يتم تحديد حساب موردين. يرجى تحديده في بطاقة المورد أو في إعدادات الأصول.')
        )

    def get_operating_lease_expense_account(self):
        """حساب مصروف الإيجار التشغيلي"""
        if self.operating_lease_expense_account:
            return self.operating_lease_expense_account
        raise ValidationError(
            _('لم يتم تحديد حساب مصروف الإيجار التشغيلي. يرجى تحديده في إعدادات الأصول.')
        )

    def get_finance_lease_accounts(self):
        """حسابات الإيجار التمويلي"""
        if not self.finance_lease_liability_account:
            raise ValidationError(
                _('لم يتم تحديد حساب التزامات الإيجار التمويلي.')
            )
        if not self.finance_lease_interest_expense_account:
            raise ValidationError(
                _('لم يتم تحديد حساب مصروف فوائد الإيجار التمويلي.')
            )
        return {
            'liability': self.finance_lease_liability_account,
            'interest': self.finance_lease_interest_expense_account
        }

    def get_insurance_accounts(self):
        """حسابات التأمين"""
        accounts = {}

        if self.insurance_claim_income_account:
            accounts['income'] = self.insurance_claim_income_account
        else:
            raise ValidationError(
                _('لم يتم تحديد حساب إيرادات تعويضات التأمين.')
            )

        if self.insurance_deductible_expense_account:
            accounts['deductible'] = self.insurance_deductible_expense_account
        else:
            raise ValidationError(
                _('لم يتم تحديد حساب مصروف تحمل التأمين.')
            )

        return accounts

    def validate_configuration(self):
        """التحقق من اكتمال الإعدادات"""
        errors = []

        if not self.default_cash_account and not self.default_bank_account:
            errors.append(_('يجب تحديد حساب نقدية أو بنك افتراضي'))

        if not self.default_maintenance_expense_account:
            errors.append(_('يجب تحديد حساب مصروف الصيانة'))

        if errors:
            raise ValidationError(errors)

        return True
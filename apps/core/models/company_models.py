# apps/core/models/company_models.py
"""
نماذج الشركة والفروع والمستودعات
- Company: الشركة
- Branch: الفرع
- Warehouse: المستودع
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .base_models import BaseModel


class Company(models.Model):
    """الشركة"""

    name = models.CharField(_('اسم الشركة'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200)
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, unique=True)
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20)
    email = models.EmailField(_('البريد الإلكتروني'))
    address = models.TextField(_('العنوان'))
    city = models.CharField(_('المدينة'), max_length=50)
    country = models.CharField(_('الدولة'), max_length=50, default='الأردن')
    logo = models.ImageField(_('الشعار'), upload_to='company_logos/', blank=True)

    fiscal_year_start_month = models.IntegerField(_('شهر بداية السنة المالية'), default=1,
                                                  validators=[MinValueValidator(1), MaxValueValidator(12)])
    fiscal_year_start_day = models.IntegerField(_('يوم بداية السنة المالية'), default=1,
                                                validators=[MinValueValidator(1), MaxValueValidator(31)])

    base_currency = models.ForeignKey('Currency', on_delete=models.PROTECT, verbose_name=_('العملة الأساسية'),
                                      related_name='companies')
    default_tax_rate = models.DecimalField(_('نسبة الضريبة الافتراضية %'), max_digits=5, decimal_places=2, default=16.0)

    is_active = models.BooleanField(_('نشطة'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('شركة')
        verbose_name_plural = _('الشركات')

    def get_fiscal_year_start_month_display(self):
        """إرجاع اسم الشهر بدلاً من رقمه"""
        month_names = {
            1: _('يناير'), 2: _('فبراير'), 3: _('مارس'),
            4: _('أبريل'), 5: _('مايو'), 6: _('يونيو'),
            7: _('يوليو'), 8: _('أغسطس'), 9: _('سبتمبر'),
            10: _('أكتوبر'), 11: _('نوفمبر'), 12: _('ديسمبر')
        }
        return month_names.get(self.fiscal_year_start_month, str(self.fiscal_year_start_month))

    def __str__(self):
        return self.name

    def create_default_sequences(self):
        """إنشاء تسلسلات الترقيم الافتراضية للشركة"""
        from .system_models import NumberingSequence

        # قائمة بكل التسلسلات المطلوبة
        sequences = [
            # المبيعات
            {
                'document_type': 'sales_invoice',
                'prefix': 'SI',
                'description': 'فاتورة مبيعات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_return',
                'prefix': 'SR',
                'description': 'مرتجع مبيعات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_quotation',
                'prefix': 'QT',
                'description': 'عرض سعر',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'sales_order',
                'prefix': 'SO',
                'description': 'أمر بيع',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المشتريات
            {
                'document_type': 'purchase_invoice',
                'prefix': 'PI',
                'description': 'فاتورة مشتريات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_return',
                'prefix': 'PR',
                'description': 'مرتجع مشتريات',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_order',
                'prefix': 'PO',
                'description': 'أمر شراء',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'purchase_request',
                'prefix': 'PRQ',
                'description': 'طلب شراء',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المخازن
            {
                'document_type': 'stock_in',
                'prefix': 'SI',
                'description': 'سند إدخال',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_out',
                'prefix': 'SO',
                'description': 'سند إخراج',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_transfer',
                'prefix': 'ST',
                'description': 'سند تحويل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'stock_count',
                'prefix': 'SC',
                'description': 'جرد',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            # المحاسبة
            {
                'document_type': 'journal_entry',
                'prefix': 'JV',
                'description': 'قيد يومية',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'payment_voucher',
                'prefix': 'PV',
                'description': 'سند صرف',
                'yearly_reset': True,
                'include_year': True,
                'include_month': True,
                'padding': 4
            },
            {
                'document_type': 'receipt_voucher',
                'prefix': 'RV',
                'description': 'سند قبض',
                'yearly_reset': True,
                'include_year': True,
                'include_month': True,
                'padding': 4
            },
            # الأصول
            {
                'document_type': 'asset',
                'prefix': 'AST',
                'description': 'أصل ثابت',
                'yearly_reset': False,
                'include_year': False,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'asset_transaction',
                'prefix': 'AT',
                'description': 'عملية على أصل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
            {
                'document_type': 'asset_maintenance',
                'prefix': 'MAINT',
                'description': 'صيانة أصل',
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'padding': 6
            },
        ]

        created_count = 0

        for seq_data in sequences:
            # التحقق من عدم وجود التسلسل
            if not NumberingSequence.objects.filter(
                    company=self,
                    document_type=seq_data['document_type']
            ).exists():
                NumberingSequence.objects.create(
                    company=self,
                    document_type=seq_data['document_type'],
                    prefix=seq_data['prefix'],
                    next_number=1,
                    padding=seq_data['padding'],
                    yearly_reset=seq_data['yearly_reset'],
                    include_year=seq_data['include_year'],
                    include_month=seq_data['include_month'],
                    separator='/',
                    is_active=True
                )
                created_count += 1

        return created_count

    def create_default_accounts(self):
        """إنشاء دليل الحسابات الافتراضي"""
        from apps.accounting.models import AccountType, Account

        # التحقق من عدم وجود حسابات مسبقاً
        if Account.objects.filter(company=self).exists():
            return 0

        created_count = 0

        # إنشاء أنواع الحسابات إذا لم تكن موجودة
        account_types = {
            'assets': AccountType.objects.get_or_create(
                code='1',
                defaults={
                    'name': 'الأصول',
                    'type_category': 'assets',
                    'normal_balance': 'debit'
                }
            )[0],
            'liabilities': AccountType.objects.get_or_create(
                code='2',
                defaults={
                    'name': 'الخصوم',
                    'type_category': 'liabilities',
                    'normal_balance': 'credit'
                }
            )[0],
            'equity': AccountType.objects.get_or_create(
                code='3',
                defaults={
                    'name': 'حقوق الملكية',
                    'type_category': 'equity',
                    'normal_balance': 'credit'
                }
            )[0],
            'revenue': AccountType.objects.get_or_create(
                code='4',
                defaults={
                    'name': 'الإيرادات',
                    'type_category': 'revenue',
                    'normal_balance': 'credit'
                }
            )[0],
            'expenses': AccountType.objects.get_or_create(
                code='5',
                defaults={
                    'name': 'المصروفات',
                    'type_category': 'expenses',
                    'normal_balance': 'debit'
                }
            )[0],
        }

        # قائمة الحسابات الافتراضية
        default_accounts = [
            # الأصول المتداولة
            {'code': '110000', 'name': 'الأصول المتداولة', 'type': 'assets', 'parent': None, 'accept_entries': False},
            {'code': '110100', 'name': 'البنك', 'type': 'assets', 'parent': '110000', 'is_bank_account': True},
            {'code': '110200', 'name': 'الصندوق', 'type': 'assets', 'parent': '110000', 'is_cash_account': True},
            {'code': '120000', 'name': 'المخزون', 'type': 'assets', 'parent': None},
            {'code': '120300', 'name': 'سلف الموظفين', 'type': 'assets', 'parent': None},
            {'code': '220100', 'name': 'العملاء', 'type': 'assets', 'parent': None},

            # الأصول الثابتة
            {'code': '130000', 'name': 'الأصول الثابتة', 'type': 'assets', 'parent': None, 'accept_entries': False},
            {'code': '130100', 'name': 'الأصول الثابتة - التكلفة', 'type': 'assets', 'parent': '130000'},
            {'code': '131000', 'name': 'مجمع إهلاك الأصول الثابتة', 'type': 'assets', 'parent': None},

            # الخصوم
            {'code': '210000', 'name': 'الخصوم المتداولة', 'type': 'liabilities', 'parent': None,
             'accept_entries': False},
            {'code': '210100', 'name': 'الموردين', 'type': 'liabilities', 'parent': '210000'},
            {'code': '210300', 'name': 'التزامات الإيجار التمويلي', 'type': 'liabilities', 'parent': '210000'},

            # حقوق الملكية
            {'code': '310000', 'name': 'رأس المال', 'type': 'equity', 'parent': None},

            # الإيرادات
            {'code': '410000', 'name': 'إيرادات المبيعات', 'type': 'revenue', 'parent': None},
            {'code': '420000', 'name': 'خصم المبيعات', 'type': 'revenue', 'parent': None},
            {'code': '420100', 'name': 'أرباح بيع أصول ثابتة', 'type': 'revenue', 'parent': None},
            {'code': '420200', 'name': 'إيرادات تعويضات تأمين', 'type': 'revenue', 'parent': None},

            # المصروفات - الأصول
            {'code': '510000', 'name': 'تكلفة البضاعة المباعة', 'type': 'expenses', 'parent': None},
            {'code': '510100', 'name': 'مصروف الرواتب', 'type': 'expenses', 'parent': None},
            {'code': '520000', 'name': 'المصروفات العمومية', 'type': 'expenses', 'parent': None,
             'accept_entries': False},
            {'code': '520100', 'name': 'خسائر بيع أصول ثابتة', 'type': 'expenses', 'parent': '520000'},
            {'code': '520200', 'name': 'خسائر استبعاد أصول', 'type': 'expenses', 'parent': '520000'},
            {'code': '520300', 'name': 'مصروف الصيانة', 'type': 'expenses', 'parent': '520000'},
            {'code': '520400', 'name': 'مصروف الإيجار', 'type': 'expenses', 'parent': '520000'},
            {'code': '520500', 'name': 'مصروف فوائد', 'type': 'expenses', 'parent': '520000'},
            {'code': '520600', 'name': 'مصروف تحمل التأمين', 'type': 'expenses', 'parent': '520000'},
            {'code': '520700', 'name': 'مصروف الإهلاك', 'type': 'expenses', 'parent': '520000'},
            {'code': '530000', 'name': 'خصم المشتريات', 'type': 'expenses', 'parent': None},
        ]

        # إنشاء الحسابات
        accounts_dict = {}

        for acc_data in default_accounts:
            parent_obj = None
            if acc_data.get('parent'):
                parent_obj = accounts_dict.get(acc_data['parent'])

            account = Account.objects.create(
                company=self,
                code=acc_data['code'],
                name=acc_data['name'],
                account_type=account_types[acc_data['type']],
                parent=parent_obj,
                currency=self.base_currency,
                nature='both',
                accept_entries=acc_data.get('accept_entries', True),
                is_cash_account=acc_data.get('is_cash_account', False),
                is_bank_account=acc_data.get('is_bank_account', False),
                opening_balance=0
            )

            accounts_dict[acc_data['code']] = account
            created_count += 1

        return created_count


class Branch(models.Model):
    """الفرع"""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches', verbose_name=_('الشركة'))
    code = models.CharField(_('رمز الفرع'), max_length=10)
    name = models.CharField(_('اسم الفرع'), max_length=100)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    address = models.TextField(_('العنوان'), blank=True)

    default_warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True,
                                          verbose_name=_('المستودع الافتراضي'), related_name='default_for_branches')

    is_main = models.BooleanField(_('الفرع الرئيسي'), default=False)
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('فرع')
        verbose_name_plural = _('الفروع')
        unique_together = [['company', 'code']]

    def save(self, *args, **kwargs):
        if self.is_main:
            Branch.objects.filter(company=self.company, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Warehouse(BaseModel):
    """المستودعات"""

    code = models.CharField(_('رمز المستودع'), max_length=20)
    name = models.CharField(_('اسم المستودع'), max_length=100)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=100, blank=True)
    address = models.TextField(_('العنوان'), blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    is_main = models.BooleanField(_('المستودع الرئيسي'), default=False)
    allow_negative_stock = models.BooleanField(_('السماح بالرصيد السالب'), default=False)
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_('مدير المستودع'), related_name='managed_warehouses')
    notes = models.TextField(_('ملاحظات'), blank=True)

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    class Meta:
        verbose_name = _('مستودع')
        verbose_name_plural = _('المستودعات')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_main:
            Warehouse.objects.filter(company=self.company, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"

# apps/core/models/partner_models.py
"""
نماذج الشركاء التجاريين - Business Partners
- BusinessPartner: العملاء والموردين (موحد)
- PartnerRepresentative: مندوبي العميل
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base_models import BaseModel


class BusinessPartner(BaseModel):
    """العملاء - موحد للعملاء والموردين مع المرفقات والمندوبين المتعددين"""

    PARTNER_TYPES = [('customer', _('عميل')), ('supplier', _('مورد')), ('both', _('عميل ومورد'))]
    ACCOUNT_TYPE_CHOICES = [('cash', _('نقدي')), ('credit', _('ذمم'))]

    # تعديل خيارات الحالة الضريبية
    TAX_STATUS_CHOICES = [
        ('taxable', _('خاضع')),
        ('non_taxable', _('غير خاضع')),
        ('export', _('تصدير'))
    ]

    partner_type = models.CharField(_('نوع العميل'), max_length=10, choices=PARTNER_TYPES, default='customer')
    code = models.CharField(_('الرمز'), max_length=50)
    name = models.CharField(_('الاسم'), max_length=200)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=200, blank=True)
    account_type = models.CharField(_('نوع الحساب'), max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='credit')

    # معلومات الاتصال
    contact_person = models.CharField(_('جهة الاتصال'), max_length=100, blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20, blank=True)
    mobile = models.CharField(_('الموبايل'), max_length=20, blank=True)
    fax = models.CharField(_('الفاكس'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)

    # العنوان
    address = models.TextField(_('العنوان'), blank=True)
    city = models.CharField(_('المدينة'), max_length=50, blank=True)
    region = models.CharField(_('المنطقة'), max_length=50, blank=True)

    # معلومات ضريبية مع فترة الإعفاء
    tax_number = models.CharField(_('الرقم الضريبي'), max_length=50, blank=True)
    tax_status = models.CharField(_('الحالة الضريبية'), max_length=20, choices=TAX_STATUS_CHOICES, default='taxable')
    commercial_register = models.CharField(_('السجل التجاري'), max_length=50, blank=True)

    # شروط الدفع والمندوب الافتراضي
    payment_terms = models.CharField(
        _('شروط الدفع'),
        max_length=200,
        blank=True,
        help_text=_('شروط الدفع للعميل (مثال: نقدي، آجل 30 يوم، إلخ)')
    )

    default_salesperson = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_customers',
        verbose_name=_('المندوب الافتراضي'),
        help_text=_('مندوب المبيعات المخصص لهذا العميل')
    )

    # حقول جديدة لفترة الإعفاء الضريبي
    tax_exemption_start_date = models.DateField(_('تاريخ بداية الإعفاء'), null=True, blank=True)
    tax_exemption_end_date = models.DateField(_('تاريخ انتهاء الإعفاء'), null=True, blank=True)
    tax_exemption_reason = models.CharField(_('سبب الإعفاء'), max_length=200, blank=True)

    default_price_list = models.ForeignKey(
        'PriceList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('قائمة الأسعار الافتراضية'),
        help_text=_('قائمة الأسعار المستخدمة لهذا العميل')
    )

    # الحسابات المحاسبية
    customer_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('حساب العميل'),
        help_text=_('حساب المدينين الخاص بهذا العميل')
    )

    supplier_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suppliers',
        verbose_name=_('حساب المورد'),
        help_text=_('حساب الدائنين الخاص بهذا المورد')
    )

    # حدود الائتمان
    credit_limit = models.DecimalField(_('حد الائتمان'), max_digits=12, decimal_places=2, default=0)
    credit_period = models.PositiveIntegerField(_('فترة الائتمان (أيام)'), default=30)

    # المرفقات الأربعة المطلوبة
    commercial_register_file = models.FileField(
        _('ملف السجل التجاري'),
        upload_to='partners/commercial_register/',
        blank=True,
        null=True,
        help_text=_('ملف السجل التجاري للعميل')
    )
    payment_letter_file = models.FileField(
        _('كتاب التسديد'),
        upload_to='partners/payment_letters/',
        blank=True,
        null=True,
        help_text=_('كتاب التسديد من البنك')
    )
    tax_exemption_file = models.FileField(
        _('كتاب الإعفاء الضريبي'),
        upload_to='partners/tax_exemptions/',
        blank=True,
        null=True,
        help_text=_('كتاب الإعفاء الضريبي من الحكومة')
    )
    other_attachments = models.FileField(
        _('مرفقات أخرى'),
        upload_to='partners/other_attachments/',
        blank=True,
        null=True,
        help_text=_('مرفقات إضافية')
    )

    # حقول مخصصة
    custom_fields = models.JSONField(
        _('حقول مخصصة'),
        default=dict,
        blank=True,
        help_text=_('حقول إضافية حسب احتياجات العمل')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عميل')
        verbose_name_plural = _('العملاء')
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_customer(self):
        return self.partner_type in ['customer', 'both']

    def is_supplier(self):
        return self.partner_type in ['supplier', 'both']

    def is_tax_exempt_active(self):
        """التحقق من صحة الإعفاء الضريبي حسب التاريخ"""
        if self.tax_status != 'non_taxable':
            return False

        if not self.tax_exemption_start_date or not self.tax_exemption_end_date:
            return False

        from django.utils import timezone
        today = timezone.now().date()
        return self.tax_exemption_start_date <= today <= self.tax_exemption_end_date

    def get_effective_tax_status(self):
        """الحصول على الحالة الضريبية الفعلية مع مراعاة انتهاء فترة الإعفاء"""
        if self.tax_status == 'non_taxable' and not self.is_tax_exempt_active():
            return 'taxable'  # انتهت فترة الإعفاء، يصبح خاضع للضريبة
        return self.tax_status

    def generate_code(self):
        """توليد كود العميل"""
        if self.partner_type == 'customer':
            prefix = 'CUS'
        elif self.partner_type == 'supplier':
            prefix = 'SUP'
        else:  # both
            prefix = 'PAR'

        last_partner = BusinessPartner.objects.filter(
            company=self.company,
            code__startswith=prefix
        ).order_by('-id').first()

        if last_partner:
            try:
                last_number = int(last_partner.code[3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:06d}"

    def get_account(self):
        """الحصول على الحساب المحاسبي المناسب"""
        from apps.accounting.models import Account

        if self.partner_type == 'customer':
            return self.customer_account or Account.objects.get(
                company=self.company, code='220100'
            )
        elif self.partner_type == 'supplier':
            return self.supplier_account or Account.objects.get(
                company=self.company, code='210100'
            )
        else:  # both
            return self.customer_account or self.supplier_account

    def get_current_balance(self):
        """حساب الرصيد الحالي للعميل من الفواتير"""
        from decimal import Decimal

        try:
            from apps.sales.models import SalesInvoice
            from django.db.models import Sum

            invoices_total = SalesInvoice.objects.filter(
                customer=self,
                is_posted=True
            ).aggregate(
                total=Sum('total_with_tax')
            )['total'] or Decimal('0')

            paid_total = SalesInvoice.objects.filter(
                customer=self,
                is_posted=True
            ).aggregate(
                total=Sum('paid_amount')
            )['total'] or Decimal('0')

            balance = invoices_total - paid_total
            return balance

        except ImportError:
            return Decimal('0')

    def check_credit_limit(self, amount):
        """التحقق من حد الائتمان قبل السماح بعملية بيع"""
        from decimal import Decimal

        result = {
            'allowed': True,
            'current_balance': Decimal('0'),
            'new_balance': Decimal('0'),
            'credit_limit': self.credit_limit,
            'available_credit': Decimal('0'),
            'message': ''
        }

        if self.account_type == 'cash':
            result['message'] = _('حساب نقدي - لا يوجد حد ائتمان')
            return result

        if self.credit_limit == 0:
            result['message'] = _('لا يوجد حد ائتمان محدد')
            return result

        current_balance = self.get_current_balance()
        result['current_balance'] = current_balance

        new_balance = current_balance + Decimal(str(amount))
        result['new_balance'] = new_balance

        available_credit = self.credit_limit - current_balance
        result['available_credit'] = available_credit

        if new_balance > self.credit_limit:
            result['allowed'] = False
            result['message'] = _(
                'تجاوز حد الائتمان! الرصيد الحالي: {current}, المبلغ المطلوب: {amount}, '
                'الرصيد الجديد: {new}, حد الائتمان: {limit}'
            ).format(
                current=current_balance,
                amount=amount,
                new=new_balance,
                limit=self.credit_limit
            )
        else:
            result['message'] = _(
                'ضمن حد الائتمان. الائتمان المتاح: {available}'
            ).format(available=available_credit)

        return result


class PartnerRepresentative(BaseModel):
    """مندوبي العميل - يمكن للعميل الواحد أن يكون له عدة مندوبين"""

    partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.CASCADE,
        related_name='representatives',
        verbose_name=_('العميل')
    )
    representative_name = models.CharField(
        _('اسم المندوب'),
        max_length=100,
        help_text=_('اسم المندوب المسؤول عن هذا العميل')
    )
    phone = models.CharField(_('هاتف المندوب'), max_length=20, blank=True)
    is_primary = models.BooleanField(_('المندوب الرئيسي'), default=False)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('مندوب العميل')
        verbose_name_plural = _('مندوبي العملاء')
        ordering = ['-is_primary', 'representative_name']

    def __str__(self):
        primary_text = _('(رئيسي)') if self.is_primary else ''
        return f"{self.partner.name} - {self.representative_name} {primary_text}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            PartnerRepresentative.objects.filter(
                partner=self.partner,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)


class PartnerItemPrice(BaseModel):
    """
    أسعار المواد حسب الشريك التجاري (عميل/مورد)
    يحفظ آخر سعر شراء/بيع لكل مادة مع كل شريك
    """

    partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.CASCADE,
        related_name='item_prices',
        verbose_name=_('الشريك التجاري')
    )

    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='partner_prices',
        verbose_name=_('المادة')
    )

    item_variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partner_prices',
        verbose_name=_('المتغير')
    )

    # للموردين (Suppliers)
    last_purchase_price = models.DecimalField(
        _('آخر سعر شراء'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('آخر سعر شراء من هذا المورد')
    )

    last_purchase_date = models.DateField(
        _('تاريخ آخر شراء'),
        null=True,
        blank=True
    )

    last_purchase_quantity = models.DecimalField(
        _('كمية آخر شراء'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True
    )

    # للعملاء (Customers)
    last_sale_price = models.DecimalField(
        _('آخر سعر بيع'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('آخر سعر بيع لهذا العميل')
    )

    last_sale_date = models.DateField(
        _('تاريخ آخر بيع'),
        null=True,
        blank=True
    )

    last_sale_quantity = models.DecimalField(
        _('كمية آخر بيع'),
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True
    )

    # إحصائيات إضافية
    total_purchased_quantity = models.DecimalField(
        _('إجمالي الكمية المشتراة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('إجمالي ما تم شراؤه من هذا المورد')
    )

    total_sold_quantity = models.DecimalField(
        _('إجمالي الكمية المباعة'),
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text=_('إجمالي ما تم بيعه لهذا العميل')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('سعر المادة للشريك')
        verbose_name_plural = _('أسعار المواد للشركاء')
        unique_together = [['company', 'partner', 'item', 'item_variant']]
        ordering = ['-last_purchase_date', '-last_sale_date']
        indexes = [
            models.Index(fields=['partner', 'item']),
            models.Index(fields=['partner', 'item_variant']),
            models.Index(fields=['last_purchase_date']),
            models.Index(fields=['last_sale_date']),
        ]

    def __str__(self):
        variant_text = f" - {self.item_variant}" if self.item_variant else ""
        return f"{self.partner.name} - {self.item.name}{variant_text}"

    def update_purchase_price(self, price, quantity, date):
        """تحديث آخر سعر شراء"""
        self.last_purchase_price = price
        self.last_purchase_date = date
        self.last_purchase_quantity = quantity
        self.total_purchased_quantity += quantity
        self.save()

    def update_sale_price(self, price, quantity, date):
        """تحديث آخر سعر بيع"""
        self.last_sale_price = price
        self.last_sale_date = date
        self.last_sale_quantity = quantity
        self.total_sold_quantity += quantity
        self.save()

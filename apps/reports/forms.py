# apps/reports/forms.py
"""
نماذج تصفية التقارير
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.models import ItemCategory, BusinessPartner, Warehouse, Branch
from apps.accounting.models.account_models import Account
from datetime import date


class DateRangeFilterForm(forms.Form):
    """نموذج أساسي لتصفية حسب التاريخ"""
    date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ النهاية'))

        return cleaned_data


class ItemsReportFilterForm(DateRangeFilterForm):
    """فلتر تقرير الأصناف"""
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        label=_('الفئة'),
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    item_type = forms.ChoiceField(
        label=_('نوع الصنف'),
        required=False,
        choices=[
            ('', _('جميع الأنواع')),
            ('product', _('منتج')),
            ('service', _('خدمة')),
            ('material', _('مادة')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('1', _('نشط')),
            ('0', _('غير نشط')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('name')


class PartnersReportFilterForm(DateRangeFilterForm):
    """فلتر تقرير الشركاء"""
    partner_type = forms.ChoiceField(
        label=_('نوع الشريك'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('customer', _('عميل')),
            ('supplier', _('مورد')),
            ('both', _('عميل ومورد')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('1', _('نشط')),
            ('0', _('غير نشط')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WarehousesReportFilterForm(forms.Form):
    """فلتر تقرير المخازن"""
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),
        label=_('الفرع'),
        required=False,
        empty_label=_('جميع الفروع'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    warehouse_type = forms.ChoiceField(
        label=_('نوع المخزن'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('main', _('رئيسي')),
            ('secondary', _('فرعي')),
            ('transit', _('ترانزيت')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('1', _('نشط')),
            ('0', _('غير نشط')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['branch'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')


class ChartOfAccountsFilterForm(forms.Form):
    """فلتر تقرير دليل الحسابات"""
    account_type = forms.ChoiceField(
        label=_('نوع الحساب'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('asset', _('أصول')),
            ('liability', _('خصوم')),
            ('equity', _('حقوق ملكية')),
            ('revenue', _('إيرادات')),
            ('expense', _('مصروفات')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    level = forms.ChoiceField(
        label=_('المستوى'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('1', _('المستوى الأول')),
            ('2', _('المستوى الثاني')),
            ('3', _('المستوى الثالث')),
            ('4', _('المستوى الرابع')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('1', _('نشط')),
            ('0', _('غير نشط')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TrialBalanceFilterForm(DateRangeFilterForm):
    """فلتر ميزان المراجعة"""
    show_zero_balances = forms.BooleanField(
        label=_('إظهار الأرصدة الصفرية'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    account_type = forms.ChoiceField(
        label=_('نوع الحساب'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('asset', _('أصول')),
            ('liability', _('خصوم')),
            ('equity', _('حقوق ملكية')),
            ('revenue', _('إيرادات')),
            ('expense', _('مصروفات')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class GeneralLedgerFilterForm(DateRangeFilterForm):
    """فلتر تقرير الأستاذ العام"""
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label=_('الحساب'),
        required=False,
        empty_label=_('جميع الحسابات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['account'].queryset = Account.objects.filter(
                company=company, is_active=True
            ).order_by('code')


class JournalEntriesFilterForm(DateRangeFilterForm):
    """فلتر تقرير قيود اليومية"""
    entry_type = forms.ChoiceField(
        label=_('نوع القيد'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('manual', _('يدوي')),
            ('system', _('تلقائي')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('draft', _('مسودة')),
            ('posted', _('مُرحّل')),
            ('cancelled', _('ملغى')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReceiptsPaymentsFilterForm(DateRangeFilterForm):
    """فلتر تقرير المقبوضات والمدفوعات"""
    voucher_type = forms.ChoiceField(
        label=_('نوع السند'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('receipt', _('قبض')),
            ('payment', _('دفع')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_method = forms.ChoiceField(
        label=_('طريقة الدفع'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('cash', _('نقدي')),
            ('check', _('شيك')),
            ('bank_transfer', _('تحويل بنكي')),
            ('credit_card', _('بطاقة ائتمان')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class IncomeStatementFilterForm(DateRangeFilterForm):
    """فلتر قائمة الدخل"""
    show_details = forms.BooleanField(
        label=_('إظهار التفاصيل'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BalanceSheetFilterForm(forms.Form):
    """فلتر المركز المالي"""
    as_of_date = forms.DateField(
        label=_('في تاريخ'),
        required=False,
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    show_details = forms.BooleanField(
        label=_('إظهار التفاصيل'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class StockReportFilterForm(forms.Form):
    """فلتر تقرير الجرد"""
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('المخزن'),
        required=False,
        empty_label=_('جميع المخازن'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        label=_('الفئة'),
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    show_zero_stock = forms.BooleanField(
        label=_('إظهار أصناف بدون رصيد'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('name')


class StockMovementFilterForm(DateRangeFilterForm):
    """فلتر تقرير حركة المخزون"""
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('المخزن'),
        required=False,
        empty_label=_('جميع المخازن'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        label=_('الفئة'),
        required=False,
        empty_label=_('جميع الفئات'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    movement_type = forms.ChoiceField(
        label=_('نوع الحركة'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('in', _('إدخال')),
            ('out', _('إخراج')),
            ('transfer', _('نقل')),
            ('adjustment', _('تسوية')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')
            self.fields['category'].queryset = ItemCategory.objects.filter(
                company=company, is_active=True
            ).order_by('name')


class StockInOutFilterForm(DateRangeFilterForm):
    """فلتر تقرير الإدخالات والإخراجات"""
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        label=_('المخزن'),
        required=False,
        empty_label=_('جميع المخازن'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    transaction_type = forms.ChoiceField(
        label=_('نوع العملية'),
        required=False,
        choices=[
            ('', _('الكل')),
            ('stock_in', _('إدخال')),
            ('stock_out', _('إخراج')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')

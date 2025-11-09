# apps/purchases/forms/filter_forms.py
"""
نماذج تصفية وبحث المشتريات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta

from ..models import PurchaseInvoice, PurchaseOrder, PurchaseRequest
from apps.core.models import BusinessPartner, Warehouse, Branch


class PurchaseInvoiceFilterForm(forms.Form):
    """نموذج تصفية فواتير المشتريات"""

    # الفترة الزمنية
    date_from = forms.DateField(
        required=False,
        label=_('من تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        required=False,
        label=_('إلى تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    # المورد
    supplier = forms.ModelChoiceField(
        required=False,
        label=_('المورد'),
        queryset=BusinessPartner.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'جميع الموردين...'
        })
    )

    # الفرع
    branch = forms.ModelChoiceField(
        required=False,
        label=_('الفرع'),
        queryset=Branch.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'جميع الفروع...'
        })
    )

    # المستودع
    warehouse = forms.ModelChoiceField(
        required=False,
        label=_('المستودع'),
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'جميع المستودعات...'
        })
    )

    # نوع الفاتورة
    invoice_type = forms.ChoiceField(
        required=False,
        label=_('نوع الفاتورة'),
        choices=[('', 'الكل')] + PurchaseInvoice.INVOICE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # حالة الترحيل
    is_posted = forms.ChoiceField(
        required=False,
        label=_('حالة الترحيل'),
        choices=[
            ('', 'الكل'),
            ('1', 'مرحل'),
            ('0', 'غير مرحل'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # البحث
    search = forms.CharField(
        required=False,
        label=_('بحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الفاتورة، رقم إيصال، رقم فاتورة المورد...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # تصفية الموردين
            self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            ).order_by('name')

            # تصفية الفروع
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            # تصفية المستودعات
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

        # تعيين القيم الافتراضية للفترة (آخر 30 يوم)
        if not self.data.get('date_from') and not self.is_bound:
            self.fields['date_from'].initial = date.today() - timedelta(days=30)
            self.fields['date_to'].initial = date.today()


class PurchaseOrderFilterForm(forms.Form):
    """نموذج تصفية أوامر الشراء"""

    # الفترة الزمنية
    date_from = forms.DateField(
        required=False,
        label=_('من تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        required=False,
        label=_('إلى تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    # المورد
    supplier = forms.ModelChoiceField(
        required=False,
        label=_('المورد'),
        queryset=BusinessPartner.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'جميع الموردين...'
        })
    )

    # الحالة
    status = forms.ChoiceField(
        required=False,
        label=_('الحالة'),
        choices=[('', 'الكل')] + [
            ('draft', _('مسودة')),
            ('pending_approval', _('بانتظار الموافقة')),
            ('approved', _('معتمد')),
            ('rejected', _('مرفوض')),
            ('sent', _('مرسل للمورد')),
            ('partial', _('استلام جزئي')),
            ('completed', _('مكتمل')),
            ('cancelled', _('ملغي')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # البحث
    search = forms.CharField(
        required=False,
        label=_('بحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الأمر، المورد...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields['supplier'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                partner_type__in=['supplier', 'both'],
                is_active=True
            ).order_by('name')

        if not self.data.get('date_from') and not self.is_bound:
            self.fields['date_from'].initial = date.today() - timedelta(days=90)
            self.fields['date_to'].initial = date.today()


class PurchaseRequestFilterForm(forms.Form):
    """نموذج تصفية طلبات الشراء"""

    # الفترة الزمنية
    date_from = forms.DateField(
        required=False,
        label=_('من تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        required=False,
        label=_('إلى تاريخ'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    # الموظف الطالب
    requested_by = forms.ModelChoiceField(
        required=False,
        label=_('طلب بواسطة'),
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'جميع الموظفين...'
        })
    )

    # الحالة
    status = forms.ChoiceField(
        required=False,
        label=_('الحالة'),
        choices=[('', 'الكل')] + [
            ('draft', _('مسودة')),
            ('submitted', _('مقدم')),
            ('approved', _('معتمد')),
            ('rejected', _('مرفوض')),
            ('ordered', _('تم الطلب')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # البحث
    search = forms.CharField(
        required=False,
        label=_('بحث'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الطلب، القسم، الغرض...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            from apps.core.models import User
            # Get all active users for the company
            self.fields['requested_by'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name')

        if not self.data.get('date_from') and not self.is_bound:
            self.fields['date_from'].initial = date.today() - timedelta(days=90)
            self.fields['date_to'].initial = date.today()

# apps/sales/forms/pos_forms.py
"""
نماذج نقاط البيع POS
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from datetime import date

from apps.sales.models import POSSession, SalesInvoice
from apps.core.models import BusinessPartner, PaymentMethod, Currency, Warehouse, User


class POSSessionForm(forms.ModelForm):
    """نموذج فتح جلسة POS"""

    class Meta:
        model = POSSession
        fields = [
            'pos_location',
            'opening_cash',
            'opening_notes',
        ]
        widgets = {
            'pos_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('مثال: صالة 1، فرع المدينة'),
                }
            ),
            'opening_cash': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'min': '0',
                    'placeholder': '0.000',
                    'required': True,
                    'autofocus': True,
                }
            ),
            'opening_notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': _('ملاحظات عند فتح الجلسة (اختياري)'),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # جعل الحقول الاختيارية
        self.fields['pos_location'].required = False
        self.fields['opening_notes'].required = False

        # تعيين قيم افتراضية
        if not self.instance.pk:
            self.fields['opening_cash'].initial = 0

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من عدم وجود جلسة مفتوحة للمستخدم الحالي
        if self.user and self.company:
            existing_open = POSSession.objects.filter(
                cashier=self.user,
                status='open',
                company=self.company
            )

            if self.instance.pk:
                existing_open = existing_open.exclude(pk=self.instance.pk)

            if existing_open.exists():
                raise ValidationError(
                    _('لديك جلسة POS مفتوحة بالفعل. يجب إغلاق الجلسة السابقة أولاً.')
                )

        return cleaned_data

    def save(self, commit=True):
        """حفظ الجلسة"""
        instance = super().save(commit=False)

        # تعيين الكاشير
        if self.user:
            instance.cashier = self.user

        # تعيين الشركة
        if self.company:
            instance.company = self.company

        # تعيين الحالة كمفتوحة
        instance.status = 'open'

        if commit:
            instance.save()

        return instance


class CloseSessionForm(forms.Form):
    """نموذج إغلاق جلسة POS"""

    closing_cash = forms.DecimalField(
        label=_('النقد الختامي'),
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0'),
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control form-control-lg',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
                'required': True,
                'autofocus': True,
            }
        ),
        help_text=_('المبلغ النقدي الفعلي الموجود في الدرج'),
    )

    closing_notes = forms.CharField(
        label=_('ملاحظات الإغلاق'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('ملاحظات إضافية عند إغلاق الجلسة (اختياري)'),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)

        # إضافة معلومات توضيحية عن النقد المتوقع
        if self.session:
            self.expected_cash = self.session.opening_cash + self.session.total_cash_sales - self.session.total_returns
            self.fields['closing_cash'].help_text = _(
                'النقد المتوقع: {} دينار (الافتتاحي {} + المبيعات النقدية {} - المرتجعات {})'
            ).format(
                self.expected_cash,
                self.session.opening_cash,
                self.session.total_cash_sales,
                self.session.total_returns
            )

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        if not self.session:
            raise ValidationError(_('لا يمكن إغلاق جلسة غير موجودة'))

        if self.session.status == 'closed':
            raise ValidationError(_('الجلسة مغلقة بالفعل'))

        return cleaned_data


class POSInvoiceQuickForm(forms.Form):
    """نموذج مبسط لإنشاء فاتورة بيع سريعة من POS"""

    customer = forms.ModelChoiceField(
        label=_('العميل'),
        queryset=BusinessPartner.objects.none(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-select select2',
                'data-placeholder': _('عميل نقدي (افتراضي)'),
            }
        ),
        help_text=_('اتركه فارغاً للعميل النقدي الافتراضي'),
    )

    payment_method = forms.ModelChoiceField(
        label=_('طريقة الدفع'),
        queryset=PaymentMethod.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'required': True,
            }
        ),
    )

    discount_type = forms.ChoiceField(
        label=_('نوع الخصم'),
        choices=[
            ('percentage', _('نسبة مئوية')),
            ('amount', _('مبلغ')),
        ],
        initial='percentage',
        widget=forms.Select(
            attrs={
                'class': 'form-select',
            }
        ),
    )

    discount_value = forms.DecimalField(
        label=_('قيمة الخصم'),
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0'),
        initial=Decimal('0'),
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
            }
        ),
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات إضافية (اختياري)'),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)

        # تصفية الحقول حسب الشركة
        if self.company:
            # تصفية العملاء
            self.fields['customer'].queryset = BusinessPartner.objects.filter(
                company=self.company,
                is_customer=True,
                is_active=True
            ).order_by('name')

            # تصفية طرق الدفع
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
                company=self.company,
                is_active=True
            ).order_by('name')

            # تعيين طريقة الدفع الافتراضية (نقدي)
            default_cash_method = PaymentMethod.objects.filter(
                company=self.company,
                code='CASH',
                is_active=True
            ).first()

            if default_cash_method:
                self.fields['payment_method'].initial = default_cash_method

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value', 0)

        # التحقق من قيمة الخصم
        if discount_type == 'percentage' and discount_value > 100:
            raise ValidationError({
                'discount_value': _('نسبة الخصم لا يمكن أن تتجاوز 100%')
            })

        # التحقق من وجود جلسة POS مفتوحة
        if self.session and self.session.status != 'open':
            raise ValidationError(_('الجلسة مغلقة. يجب فتح جلسة جديدة أولاً.'))

        return cleaned_data


class POSInvoiceItemForm(forms.Form):
    """نموذج إضافة مادة لفاتورة POS"""

    item_code = forms.CharField(
        label=_('كود المادة'),
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('امسح الباركود أو اكتب الكود'),
                'autofocus': True,
            }
        ),
    )

    quantity = forms.DecimalField(
        label=_('الكمية'),
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0.001'),
        initial=Decimal('1'),
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001',
            }
        ),
    )

    unit_price = forms.DecimalField(
        label=_('السعر'),
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0'),
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': _('سعر تلقائي'),
            }
        ),
        help_text=_('اتركه فارغاً لاستخدام السعر الافتراضي'),
    )

    discount_percentage = forms.DecimalField(
        label=_('خصم %'),
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        initial=Decimal('0'),
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

    def clean_item_code(self):
        """التحقق من وجود المادة"""
        from apps.core.models import Item

        item_code = self.cleaned_data.get('item_code')

        if not item_code:
            raise ValidationError(_('يجب إدخال كود المادة'))

        # البحث عن المادة بالكود أو الباركود
        item = Item.objects.filter(
            company=self.company,
            is_active=True
        ).filter(
            models.Q(code=item_code) | models.Q(barcode=item_code)
        ).first()

        if not item:
            raise ValidationError(_('المادة غير موجودة أو غير نشطة'))

        self.item = item
        return item_code

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        quantity = cleaned_data.get('quantity', 0)
        unit_price = cleaned_data.get('unit_price')

        # إذا لم يتم تحديد السعر، استخدم السعر الافتراضي للمادة
        if unit_price is None and hasattr(self, 'item'):
            cleaned_data['unit_price'] = self.item.selling_price

        return cleaned_data

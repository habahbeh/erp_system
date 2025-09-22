# إنشاء ملف جديد apps/accounting/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


def validate_positive_amount(value):
    """التحقق من أن المبلغ موجب"""
    if value <= 0:
        raise ValidationError(_('المبلغ يجب أن يكون أكبر من الصفر'))


def validate_account_code_format(value):
    """التحقق من تنسيق رمز الحساب"""
    if not value.isalnum():
        raise ValidationError(_('رمز الحساب يجب أن يحتوي على أحرف وأرقام فقط'))

    if len(value) < 2 or len(value) > 20:
        raise ValidationError(_('رمز الحساب يجب أن يكون بين 2 و 20 حرف'))


def validate_fiscal_year_dates(start_date, end_date):
    """التحقق من تواريخ السنة المالية"""
    if end_date <= start_date:
        raise ValidationError(_('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))

    days_diff = (end_date - start_date).days
    if days_diff < 28 or days_diff > 366:
        raise ValidationError(_('السنة المالية يجب أن تكون بين شهر و سنة'))
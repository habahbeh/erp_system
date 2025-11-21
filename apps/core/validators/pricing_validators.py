"""
Pricing and Business Logic Validators
======================================

Comprehensive validation for:
- Pricing data integrity
- Business rules enforcement
- Input sanitization
- Security checks

Author: Mohammad + Claude
Date: 2025-11-19
"""

from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Optional, Dict, Any
from datetime import date


class PricingValidator:
    """Validators for pricing-related data"""

    # Validation constraints
    MIN_PRICE = Decimal('0.00')
    MAX_PRICE = Decimal('999999999.99')
    MIN_COST = Decimal('0.00')
    MAX_COST = Decimal('999999999.99')
    MIN_QUANTITY = Decimal('0.00')
    MAX_QUANTITY = Decimal('999999999.99')
    MAX_DECIMAL_PLACES = 4
    MIN_PERCENTAGE = Decimal('0.00')
    MAX_PERCENTAGE = Decimal('100.00')

    @classmethod
    def validate_price(cls, price: Any, field_name: str = 'price',
                      allow_zero: bool = False) -> Decimal:
        """
        Validate price value

        Args:
            price: Price value to validate
            field_name: Field name for error message
            allow_zero: Whether zero price is allowed

        Returns:
            Decimal: Validated price

        Raises:
            ValidationError: If price is invalid
        """
        # Convert to Decimal
        try:
            if isinstance(price, str):
                price = Decimal(price.replace(',', ''))
            elif not isinstance(price, Decimal):
                price = Decimal(str(price))
        except (ValueError, InvalidOperation):
            raise ValidationError({
                field_name: _('يجب إدخال سعر صحيح')
            })

        # Check minimum
        if not allow_zero and price <= cls.MIN_PRICE:
            raise ValidationError({
                field_name: _('يجب أن يكون السعر أكبر من صفر')
            })

        if allow_zero and price < cls.MIN_PRICE:
            raise ValidationError({
                field_name: _('السعر لا يمكن أن يكون سالباً')
            })

        # Check maximum
        if price > cls.MAX_PRICE:
            raise ValidationError({
                field_name: _(f'السعر لا يمكن أن يتجاوز {cls.MAX_PRICE}')
            })

        return price

    @classmethod
    def validate_cost(cls, cost: Any, field_name: str = 'cost',
                     allow_zero: bool = True) -> Decimal:
        """
        Validate cost value

        Args:
            cost: Cost value to validate
            field_name: Field name for error message
            allow_zero: Whether zero cost is allowed

        Returns:
            Decimal: Validated cost

        Raises:
            ValidationError: If cost is invalid
        """
        # Same validation as price
        return cls.validate_price(cost, field_name, allow_zero)

    @classmethod
    def validate_price_vs_cost(cls, price: Decimal, cost: Decimal,
                              strict: bool = False) -> None:
        """
        Validate that price is greater than or equal to cost

        Args:
            price: Selling price
            cost: Item cost
            strict: If True, price must be > cost (not just >=)

        Raises:
            ValidationError: If price < cost
        """
        if strict:
            if price <= cost:
                raise ValidationError({
                    'price': _('سعر البيع يجب أن يكون أكبر من التكلفة')
                })
        else:
            if price < cost:
                raise ValidationError({
                    'price': _('سعر البيع لا يمكن أن يكون أقل من التكلفة')
                })

    @classmethod
    def validate_quantity(cls, quantity: Any, field_name: str = 'quantity',
                         allow_zero: bool = False, allow_negative: bool = False) -> Decimal:
        """
        Validate quantity value

        Args:
            quantity: Quantity value to validate
            field_name: Field name for error message
            allow_zero: Whether zero quantity is allowed
            allow_negative: Whether negative quantity is allowed (for returns)

        Returns:
            Decimal: Validated quantity

        Raises:
            ValidationError: If quantity is invalid
        """
        # Convert to Decimal
        try:
            if isinstance(quantity, str):
                quantity = Decimal(quantity.replace(',', ''))
            elif not isinstance(quantity, Decimal):
                quantity = Decimal(str(quantity))
        except (ValueError, InvalidOperation):
            raise ValidationError({
                field_name: _('يجب إدخال كمية صحيحة')
            })

        # Check minimum
        if not allow_negative and quantity < cls.MIN_QUANTITY:
            raise ValidationError({
                field_name: _('الكمية لا يمكن أن تكون سالبة')
            })

        if not allow_zero and quantity == cls.MIN_QUANTITY:
            raise ValidationError({
                field_name: _('يجب أن تكون الكمية أكبر من صفر')
            })

        # Check maximum
        if quantity > cls.MAX_QUANTITY:
            raise ValidationError({
                field_name: _(f'الكمية لا يمكن أن تتجاوز {cls.MAX_QUANTITY}')
            })

        return quantity

    @classmethod
    def validate_percentage(cls, percentage: Any, field_name: str = 'percentage',
                           allow_negative: bool = False) -> Decimal:
        """
        Validate percentage value (0-100)

        Args:
            percentage: Percentage value to validate
            field_name: Field name for error message
            allow_negative: Whether negative percentages are allowed

        Returns:
            Decimal: Validated percentage

        Raises:
            ValidationError: If percentage is invalid
        """
        # Convert to Decimal
        try:
            if isinstance(percentage, str):
                percentage = Decimal(percentage.replace(',', '').replace('%', ''))
            elif not isinstance(percentage, Decimal):
                percentage = Decimal(str(percentage))
        except (ValueError, InvalidOperation):
            raise ValidationError({
                field_name: _('يجب إدخال نسبة صحيحة')
            })

        # Check range
        if not allow_negative and percentage < cls.MIN_PERCENTAGE:
            raise ValidationError({
                field_name: _('النسبة لا يمكن أن تكون سالبة')
            })

        if percentage > cls.MAX_PERCENTAGE:
            raise ValidationError({
                field_name: _(f'النسبة لا يمكن أن تتجاوز {cls.MAX_PERCENTAGE}%')
            })

        return percentage

    @classmethod
    def validate_discount(cls, discount: Decimal, original_price: Decimal,
                         is_percentage: bool = True) -> None:
        """
        Validate discount value

        Args:
            discount: Discount amount or percentage
            original_price: Original price before discount
            is_percentage: Whether discount is a percentage

        Raises:
            ValidationError: If discount is invalid
        """
        if is_percentage:
            # Percentage discount
            cls.validate_percentage(discount, 'discount')
        else:
            # Fixed discount
            discount = cls.validate_price(discount, 'discount', allow_zero=True)

            # Discount cannot exceed original price
            if discount > original_price:
                raise ValidationError({
                    'discount': _('الخصم لا يمكن أن يتجاوز السعر الأصلي')
                })

    @classmethod
    def validate_date_range(cls, start_date: Optional[date],
                           end_date: Optional[date]) -> None:
        """
        Validate date range

        Args:
            start_date: Start date
            end_date: End date

        Raises:
            ValidationError: If date range is invalid
        """
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية')
                })

    @classmethod
    def validate_priority(cls, priority: int, field_name: str = 'priority') -> int:
        """
        Validate priority value

        Args:
            priority: Priority value (1-100)
            field_name: Field name for error message

        Returns:
            int: Validated priority

        Raises:
            ValidationError: If priority is invalid
        """
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            raise ValidationError({
                field_name: _('يجب إدخال رقم صحيح للأولوية')
            })

        if priority < 1 or priority > 100:
            raise ValidationError({
                field_name: _('الأولوية يجب أن تكون بين 1 و 100')
            })

        return priority


class UoMValidator:
    """Validators for Unit of Measure data"""

    MIN_CONVERSION_FACTOR = Decimal('0.0000000001')
    MAX_CONVERSION_FACTOR = Decimal('999999999.99')

    @classmethod
    def validate_conversion_factor(cls, factor: Any,
                                   field_name: str = 'conversion_factor') -> Decimal:
        """
        Validate conversion factor

        Args:
            factor: Conversion factor to validate
            field_name: Field name for error message

        Returns:
            Decimal: Validated conversion factor

        Raises:
            ValidationError: If factor is invalid
        """
        # Convert to Decimal
        try:
            if isinstance(factor, str):
                factor = Decimal(factor.replace(',', ''))
            elif not isinstance(factor, Decimal):
                factor = Decimal(str(factor))
        except (ValueError, InvalidOperation):
            raise ValidationError({
                field_name: _('يجب إدخال معامل تحويل صحيح')
            })

        # Check minimum (cannot be zero)
        if factor <= cls.MIN_CONVERSION_FACTOR:
            raise ValidationError({
                field_name: _('معامل التحويل يجب أن يكون أكبر من صفر')
            })

        # Check maximum
        if factor > cls.MAX_CONVERSION_FACTOR:
            raise ValidationError({
                field_name: _(f'معامل التحويل لا يمكن أن يتجاوز {cls.MAX_CONVERSION_FACTOR}')
            })

        return factor

    @classmethod
    def validate_uom_compatibility(cls, from_uom, to_uom) -> None:
        """
        Validate that UoMs are compatible for conversion

        Args:
            from_uom: Source UoM
            to_uom: Target UoM

        Raises:
            ValidationError: If UoMs are not compatible
        """
        # Check if same UoM
        if from_uom.id == to_uom.id:
            raise ValidationError({
                'to_uom': _('لا يمكن تحويل الوحدة إلى نفسها')
            })

        # Check if in same UoM group (if groups are defined)
        if hasattr(from_uom, 'uom_group') and hasattr(to_uom, 'uom_group'):
            if from_uom.uom_group and to_uom.uom_group:
                if from_uom.uom_group_id != to_uom.uom_group_id:
                    raise ValidationError({
                        'to_uom': _('لا يمكن التحويل بين وحدات من مجموعات مختلفة')
                    })


class BusinessRuleValidator:
    """Validators for business rules"""

    @classmethod
    def validate_pricing_rule_configuration(cls, rule_type: str,
                                           config: Dict[str, Any]) -> None:
        """
        Validate pricing rule configuration based on rule type

        Args:
            rule_type: Type of pricing rule
            config: Rule configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
        """
        if rule_type == 'percentage_discount':
            # Require 'value' field
            if 'value' not in config:
                raise ValidationError({
                    'value': _('يجب تحديد نسبة الخصم')
                })

            PricingValidator.validate_percentage(
                config['value'],
                'value'
            )

        elif rule_type == 'fixed_discount':
            # Require 'value' field
            if 'value' not in config:
                raise ValidationError({
                    'value': _('يجب تحديد قيمة الخصم')
                })

            PricingValidator.validate_price(
                config['value'],
                'value',
                allow_zero=True
            )

        elif rule_type == 'quantity_tier':
            # Require 'min_quantity' and 'value'
            if 'min_quantity' not in config:
                raise ValidationError({
                    'min_quantity': _('يجب تحديد الحد الأدنى للكمية')
                })

            if 'value' not in config:
                raise ValidationError({
                    'value': _('يجب تحديد قيمة الخصم')
                })

            PricingValidator.validate_quantity(
                config['min_quantity'],
                'min_quantity'
            )

            PricingValidator.validate_percentage(
                config['value'],
                'value'
            )

    @classmethod
    def validate_import_data(cls, data: Dict[str, Any],
                            required_fields: list) -> None:
        """
        Validate import data

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If data is invalid
        """
        errors = {}

        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                errors[field] = _('هذا الحقل مطلوب')

        if errors:
            raise ValidationError(errors)


class SecurityValidator:
    """Security-related validators"""

    @classmethod
    def validate_company_isolation(cls, user, company) -> None:
        """
        Validate that user has access to the company

        Args:
            user: User object
            company: Company object

        Raises:
            ValidationError: If user doesn't have access
        """
        if user.is_superuser:
            return  # Superusers can access all companies

        # Check if user's company matches (company is on User model, not UserProfile)
        if hasattr(user, 'company'):
            user_company = user.company
            if user_company and user_company.id != company.id:
                raise ValidationError({
                    'company': _('ليس لديك صلاحية الوصول لهذه الشركة')
                })

    @classmethod
    def sanitize_string_input(cls, value: str, max_length: int = 255) -> str:
        """
        Sanitize string input

        Args:
            value: String value to sanitize
            max_length: Maximum allowed length

        Returns:
            str: Sanitized string

        Raises:
            ValidationError: If value is invalid
        """
        if not isinstance(value, str):
            value = str(value)

        # Strip whitespace
        value = value.strip()

        # Check length
        if len(value) > max_length:
            raise ValidationError({
                'value': _(f'النص لا يمكن أن يتجاوز {max_length} حرف')
            })

        # Remove potentially dangerous characters
        # (Django templates auto-escape, but better safe than sorry)
        dangerous_chars = ['<script', '</script', 'javascript:', 'onerror=', 'onclick=']

        value_lower = value.lower()
        for dangerous in dangerous_chars:
            if dangerous in value_lower:
                raise ValidationError({
                    'value': _('النص يحتوي على أحرف غير مسموح بها')
                })

        return value


# ===================================================================
# Convenience Functions
# ===================================================================

def validate_price_list_item(price: Decimal, cost: Optional[Decimal] = None,
                             quantity: Optional[Decimal] = None) -> Dict[str, Decimal]:
    """
    Validate complete price list item data

    Args:
        price: Price value
        cost: Cost value (optional)
        quantity: Quantity value (optional)

    Returns:
        Dict: Validated data

    Raises:
        ValidationError: If any value is invalid
    """
    validated = {}

    # Validate price
    validated['price'] = PricingValidator.validate_price(price)

    # Validate cost if provided
    if cost is not None:
        validated['cost'] = PricingValidator.validate_cost(cost)

        # Check price vs cost
        PricingValidator.validate_price_vs_cost(
            validated['price'],
            validated['cost']
        )

    # Validate quantity if provided
    if quantity is not None:
        validated['quantity'] = PricingValidator.validate_quantity(
            quantity,
            allow_zero=True
        )

    return validated


def validate_uom_conversion(from_uom, to_uom, factor: Decimal) -> Decimal:
    """
    Validate complete UoM conversion data

    Args:
        from_uom: Source UoM object
        to_uom: Target UoM object
        factor: Conversion factor

    Returns:
        Decimal: Validated conversion factor

    Raises:
        ValidationError: If any value is invalid
    """
    # Validate UoM compatibility
    UoMValidator.validate_uom_compatibility(from_uom, to_uom)

    # Validate conversion factor
    return UoMValidator.validate_conversion_factor(factor)


# ===================================================================
# Usage Examples
# ===================================================================

"""
# Example 1: Validate price
from apps.core.validators.pricing_validators import PricingValidator

try:
    price = PricingValidator.validate_price('1250.50')
    print(f"Valid price: {price}")
except ValidationError as e:
    print(f"Invalid: {e}")


# Example 2: Validate price vs cost
try:
    price = Decimal('100.00')
    cost = Decimal('80.00')
    PricingValidator.validate_price_vs_cost(price, cost)
    print("Price is valid relative to cost")
except ValidationError as e:
    print(f"Invalid: {e}")


# Example 3: Validate complete price list item
from apps.core.validators.pricing_validators import validate_price_list_item

try:
    validated_data = validate_price_list_item(
        price=Decimal('150.00'),
        cost=Decimal('100.00'),
        quantity=Decimal('10')
    )
    print(f"All valid: {validated_data}")
except ValidationError as e:
    print(f"Validation errors: {e}")
"""

# apps/core/views/ajax_price_views.py
"""
AJAX Views for Price Operations
Provides AJAX endpoints for dynamic price updates and validations
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import json

from apps.core.models import (
    PriceListItem, PricingRule, PriceList, Item
)
from apps.core.utils.ajax_helpers import (
    AjaxResponse, AjaxValidator, AjaxSerializer
)
from apps.core.utils.pricing_engine import PricingEngine


class UpdatePriceAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for updating a single price
    """

    def post(self, request, *args, **kwargs):
        """
        Update price for a price list item

        POST data:
            - price_item_id: PriceListItem ID
            - new_price: New price value
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return AjaxResponse.error('بيانات JSON غير صالحة')

        # Validate required fields
        errors = AjaxValidator.validate_required_fields(
            data, ['price_item_id', 'new_price']
        )
        if errors:
            return AjaxResponse.validation_error(errors)

        # Validate price
        new_price, price_errors = AjaxValidator.validate_decimal(
            data['new_price'],
            'new_price',
            min_value=Decimal('0')
        )
        if price_errors:
            return AjaxResponse.validation_error(price_errors)

        # Get price item
        try:
            price_item = get_object_or_404(
                PriceListItem,
                id=data['price_item_id'],
                item__company=request.current_company
            )
        except:
            return AjaxResponse.not_found('عنصر السعر غير موجود')

        # Update price
        old_price = price_item.price
        price_item.price = new_price
        price_item.save()

        # Build response
        currency_symbol = request.current_company.currency.symbol if request.current_company.currency else ''

        return AjaxResponse.success(
            'تم تحديث السعر بنجاح',
            data={
                'old_price': str(old_price),
                'new_price': str(new_price),
                'formatted_price': f'{new_price:,.2f} {currency_symbol}',
                'price_item_id': price_item.id
            }
        )


class BulkUpdatePricesAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for bulk price updates
    """

    def post(self, request, *args, **kwargs):
        """
        Update multiple prices at once

        POST data:
            - updates: List of {price_item_id, new_price}
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return AjaxResponse.error('بيانات JSON غير صالحة')

        updates = data.get('updates', [])

        if not updates:
            return AjaxResponse.error('لا توجد تحديثات')

        updated_count = 0
        errors = []

        with transaction.atomic():
            for update in updates:
                price_item_id = update.get('price_item_id')
                new_price = update.get('new_price')

                # Validate
                if not price_item_id or new_price is None:
                    continue

                try:
                    price_item = PriceListItem.objects.get(
                        id=price_item_id,
                        item__company=request.current_company
                    )

                    # Validate price
                    decimal_price, price_errors = AjaxValidator.validate_decimal(
                        new_price,
                        'new_price',
                        min_value=Decimal('0')
                    )

                    if price_errors:
                        errors.append({
                            'price_item_id': price_item_id,
                            'error': 'سعر غير صالح'
                        })
                        continue

                    price_item.price = decimal_price
                    price_item.save()
                    updated_count += 1

                except PriceListItem.DoesNotExist:
                    errors.append({
                        'price_item_id': price_item_id,
                        'error': 'عنصر غير موجود'
                    })

        return AjaxResponse.success(
            f'تم تحديث {updated_count} سعر بنجاح',
            data={
                'updated_count': updated_count,
                'errors': errors
            }
        )


class CalculatePriceAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for calculating price with rules
    """

    def post(self, request, *args, **kwargs):
        """
        Calculate price for an item with pricing rules

        POST data:
            - item_id: Item ID
            - quantity: Quantity (default 1)
            - price_list_id: Price list ID (optional)
            - apply_rules: Whether to apply pricing rules (default true)
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return AjaxResponse.error('بيانات JSON غير صالحة')

        # Validate required fields
        errors = AjaxValidator.validate_required_fields(data, ['item_id'])
        if errors:
            return AjaxResponse.validation_error(errors)

        # Get item
        try:
            item = get_object_or_404(
                Item,
                id=data['item_id'],
                company=request.current_company
            )
        except:
            return AjaxResponse.not_found('الصنف غير موجود')

        # Get quantity
        quantity, qty_errors = AjaxValidator.validate_decimal(
            data.get('quantity', 1),
            'quantity',
            min_value=Decimal('0.01')
        )
        if qty_errors:
            return AjaxResponse.validation_error(qty_errors)

        # Get price list
        price_list = None
        if data.get('price_list_id'):
            try:
                price_list = PriceList.objects.get(
                    id=data['price_list_id'],
                    company=request.current_company
                )
            except PriceList.DoesNotExist:
                return AjaxResponse.error('قائمة الأسعار غير موجودة')

        # Calculate price
        engine = PricingEngine(request.current_company)
        apply_rules = data.get('apply_rules', True)

        result = engine.calculate_price(
            item=item,
            variant=None,
            uom=item.base_uom,
            quantity=quantity,
            price_list=price_list,
            customer=None,
            check_date=None,
            apply_rules=apply_rules
        )

        # Build response
        currency_symbol = request.current_company.currency.symbol if request.current_company.currency else ''

        return AjaxResponse.success(
            'تم حساب السعر بنجاح',
            data={
                'base_price': str(result.base_price),
                'final_price': str(result.final_price),
                'total_discount': str(result.total_discount),
                'applied_rules': result.applied_rules,
                'calculation_log': result.get_calculation_log(),
                'formatted_final_price': f'{result.final_price:,.2f} {currency_symbol}',
                'formatted_base_price': f'{result.base_price:,.2f} {currency_symbol}'
            }
        )


class ValidatePriceRuleAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for validating pricing rule configuration
    """

    def post(self, request, *args, **kwargs):
        """
        Validate pricing rule configuration

        POST data:
            - rule_type: Rule type
            - percentage_value: Percentage value (for percentage rules)
            - amount_value: Amount value (for amount rules)
            - min_quantity: Min quantity (for bulk rules)
            - custom_formula: Formula (for custom rules)
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return AjaxResponse.error('بيانات JSON غير صالحة')

        rule_type = data.get('rule_type')
        errors = {}

        # Validate based on rule type
        if rule_type == 'DISCOUNT_PERCENTAGE':
            percentage, err = AjaxValidator.validate_decimal(
                data.get('percentage_value', 0),
                'percentage_value',
                min_value=Decimal('0'),
                max_value=Decimal('100')
            )
            if err:
                errors.update(err)

        elif rule_type == 'DISCOUNT_AMOUNT':
            amount, err = AjaxValidator.validate_decimal(
                data.get('amount_value', 0),
                'amount_value',
                min_value=Decimal('0')
            )
            if err:
                errors.update(err)

        elif rule_type == 'MARKUP_PERCENTAGE':
            percentage, err = AjaxValidator.validate_decimal(
                data.get('percentage_value', 0),
                'percentage_value',
                min_value=Decimal('0')
            )
            if err:
                errors.update(err)

        elif rule_type == 'MARKUP_AMOUNT':
            amount, err = AjaxValidator.validate_decimal(
                data.get('amount_value', 0),
                'amount_value',
                min_value=Decimal('0')
            )
            if err:
                errors.update(err)

        elif rule_type == 'BULK_DISCOUNT':
            min_qty, err = AjaxValidator.validate_decimal(
                data.get('min_quantity', 0),
                'min_quantity',
                min_value=Decimal('1')
            )
            if err:
                errors.update(err)

            percentage, err = AjaxValidator.validate_decimal(
                data.get('percentage_value', 0),
                'percentage_value',
                min_value=Decimal('0'),
                max_value=Decimal('100')
            )
            if err:
                errors.update(err)

        elif rule_type == 'CUSTOM_FORMULA':
            formula = data.get('custom_formula', '')
            if not formula:
                errors['custom_formula'] = ['المعادلة المخصصة مطلوبة']
            else:
                # Try to parse formula
                try:
                    json.loads(formula)
                except:
                    errors['custom_formula'] = ['صيغة JSON غير صالحة']

        if errors:
            return AjaxResponse.validation_error(errors)

        return AjaxResponse.success('التحقق من الصحة نجح')


class TogglePriceRuleAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for toggling pricing rule active status
    """

    def post(self, request, *args, **kwargs):
        """
        Toggle pricing rule active status

        POST data:
            - rule_id: PricingRule ID
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return AjaxResponse.error('بيانات JSON غير صالحة')

        # Validate required fields
        errors = AjaxValidator.validate_required_fields(data, ['rule_id'])
        if errors:
            return AjaxResponse.validation_error(errors)

        # Get rule
        try:
            rule = get_object_or_404(
                PricingRule,
                id=data['rule_id'],
                company=request.current_company
            )
        except:
            return AjaxResponse.not_found('القاعدة غير موجودة')

        # Toggle status
        rule.is_active = not rule.is_active
        rule.save()

        return AjaxResponse.success(
            'تم تحديث حالة القاعدة بنجاح',
            data={
                'rule_id': rule.id,
                'is_active': rule.is_active,
                'status_text': 'نشط' if rule.is_active else 'غير نشط'
            }
        )


class GetItemPricesAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for getting all prices for an item
    """

    def get(self, request, *args, **kwargs):
        """
        Get all prices for an item

        Query params:
            - item_id: Item ID
        """
        item_id = request.GET.get('item_id')

        if not item_id:
            return AjaxResponse.error('معرف الصنف مطلوب')

        # Get item
        try:
            item = get_object_or_404(
                Item,
                id=item_id,
                company=request.current_company
            )
        except:
            return AjaxResponse.not_found('الصنف غير موجود')

        # Get all prices
        prices = PriceListItem.objects.filter(
            item=item
        ).select_related('price_list', 'uom')

        # Serialize
        price_data = []
        currency_symbol = request.current_company.currency.symbol if request.current_company.currency else ''

        for price_item in prices:
            price_data.append({
                'id': price_item.id,
                'price_list_id': price_item.price_list.id,
                'price_list_name': price_item.price_list.name,
                'uom_id': price_item.uom.id,
                'uom_name': price_item.uom.name,
                'price': str(price_item.price),
                'formatted_price': f'{price_item.price:,.2f} {currency_symbol}'
            })

        return AjaxResponse.success(
            'تم جلب الأسعار بنجاح',
            data={
                'item_id': item.id,
                'item_code': item.code,
                'item_name': item.name,
                'prices': price_data,
                'total_prices': len(price_data)
            }
        )

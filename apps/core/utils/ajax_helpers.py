# apps/core/utils/ajax_helpers.py
"""
AJAX Helper Utilities
Provides utilities for AJAX operations and JSON responses
"""

from typing import Dict, Any, Optional, List
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
import json


class AjaxResponse:
    """
    Helper class for building consistent AJAX responses
    """

    @staticmethod
    def success(
        message: str,
        data: Optional[Dict[str, Any]] = None,
        status: int = 200
    ) -> JsonResponse:
        """
        Build a success JSON response

        Args:
            message: Success message
            data: Optional data to include
            status: HTTP status code

        Returns:
            JsonResponse with success structure
        """
        response_data = {
            'success': True,
            'message': message
        }

        if data:
            response_data['data'] = data

        return JsonResponse(response_data, status=status)

    @staticmethod
    def error(
        message: str,
        errors: Optional[Dict[str, List[str]]] = None,
        status: int = 400
    ) -> JsonResponse:
        """
        Build an error JSON response

        Args:
            message: Error message
            errors: Optional field-level errors
            status: HTTP status code

        Returns:
            JsonResponse with error structure
        """
        response_data = {
            'success': False,
            'message': message
        }

        if errors:
            response_data['errors'] = errors

        return JsonResponse(response_data, status=status)

    @staticmethod
    def validation_error(
        errors: Dict[str, List[str]],
        message: str = 'خطأ في التحقق من البيانات'
    ) -> JsonResponse:
        """
        Build a validation error response

        Args:
            errors: Field-level validation errors
            message: General error message

        Returns:
            JsonResponse with validation error structure
        """
        return AjaxResponse.error(message, errors, status=422)

    @staticmethod
    def not_found(
        message: str = 'العنصر غير موجود'
    ) -> JsonResponse:
        """
        Build a not found error response

        Args:
            message: Error message

        Returns:
            JsonResponse with 404 status
        """
        return AjaxResponse.error(message, status=404)

    @staticmethod
    def forbidden(
        message: str = 'ليس لديك صلاحية لتنفيذ هذا الإجراء'
    ) -> JsonResponse:
        """
        Build a forbidden error response

        Args:
            message: Error message

        Returns:
            JsonResponse with 403 status
        """
        return AjaxResponse.error(message, status=403)

    @staticmethod
    def server_error(
        message: str = 'حدث خطأ في الخادم'
    ) -> JsonResponse:
        """
        Build a server error response

        Args:
            message: Error message

        Returns:
            JsonResponse with 500 status
        """
        return AjaxResponse.error(message, status=500)


class AjaxValidator:
    """
    Helper class for validating AJAX request data
    """

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Optional[Dict[str, List[str]]]:
        """
        Validate that required fields are present

        Args:
            data: Request data
            required_fields: List of required field names

        Returns:
            Dict of errors or None if valid
        """
        errors = {}

        for field in required_fields:
            if field not in data or data[field] in [None, '', []]:
                errors[field] = ['هذا الحقل مطلوب']

        return errors if errors else None

    @staticmethod
    def validate_decimal(
        value: Any,
        field_name: str = 'value',
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None
    ) -> tuple[Optional[Decimal], Optional[Dict[str, List[str]]]]:
        """
        Validate and convert decimal value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Optional minimum value
            max_value: Optional maximum value

        Returns:
            Tuple of (converted_value, errors)
        """
        errors = {}

        try:
            decimal_value = Decimal(str(value))

            if min_value is not None and decimal_value < min_value:
                errors[field_name] = [f'يجب أن تكون القيمة أكبر من أو تساوي {min_value}']

            if max_value is not None and decimal_value > max_value:
                errors[field_name] = [f'يجب أن تكون القيمة أقل من أو تساوي {max_value}']

            return decimal_value, (errors if errors else None)

        except (InvalidOperation, ValueError, TypeError):
            errors[field_name] = ['قيمة عددية غير صحيحة']
            return None, errors

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str = 'value',
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> tuple[Optional[int], Optional[Dict[str, List[str]]]]:
        """
        Validate and convert integer value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Optional minimum value
            max_value: Optional maximum value

        Returns:
            Tuple of (converted_value, errors)
        """
        errors = {}

        try:
            int_value = int(value)

            if min_value is not None and int_value < min_value:
                errors[field_name] = [f'يجب أن تكون القيمة أكبر من أو تساوي {min_value}']

            if max_value is not None and int_value > max_value:
                errors[field_name] = [f'يجب أن تكون القيمة أقل من أو تساوي {max_value}']

            return int_value, (errors if errors else None)

        except (ValueError, TypeError):
            errors[field_name] = ['قيمة رقمية صحيحة غير صحيحة']
            return None, errors

    @staticmethod
    def validate_choice(
        value: Any,
        choices: List[Any],
        field_name: str = 'value'
    ) -> Optional[Dict[str, List[str]]]:
        """
        Validate that value is in allowed choices

        Args:
            value: Value to validate
            choices: List of allowed values
            field_name: Field name for error messages

        Returns:
            Dict of errors or None if valid
        """
        if value not in choices:
            return {field_name: ['قيمة غير صالحة']}

        return None

    @staticmethod
    def validate_boolean(
        value: Any,
        field_name: str = 'value'
    ) -> tuple[Optional[bool], Optional[Dict[str, List[str]]]]:
        """
        Validate and convert boolean value

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Tuple of (converted_value, errors)
        """
        if isinstance(value, bool):
            return value, None

        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes']:
                return True, None
            elif value.lower() in ['false', '0', 'no']:
                return False, None

        if isinstance(value, int):
            return bool(value), None

        return None, {field_name: ['قيمة منطقية غير صحيحة']}


class AjaxFormHelper:
    """
    Helper class for handling forms via AJAX
    """

    @staticmethod
    def get_form_errors(form) -> Dict[str, List[str]]:
        """
        Extract errors from Django form

        Args:
            form: Django form instance

        Returns:
            Dict of field errors
        """
        errors = {}

        for field, error_list in form.errors.items():
            errors[field] = list(error_list)

        return errors

    @staticmethod
    def validate_form(form) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Validate Django form

        Args:
            form: Django form instance

        Returns:
            Tuple of (is_valid, errors)
        """
        if form.is_valid():
            return True, None

        return False, AjaxFormHelper.get_form_errors(form)

    @staticmethod
    def save_form(
        form,
        commit: bool = True
    ) -> tuple[Any, Optional[str]]:
        """
        Save Django form and handle errors

        Args:
            form: Django form instance
            commit: Whether to commit to database

        Returns:
            Tuple of (instance, error_message)
        """
        try:
            instance = form.save(commit=commit)
            return instance, None
        except Exception as e:
            return None, str(e)


class AjaxPaginator:
    """
    Helper class for AJAX pagination
    """

    @staticmethod
    def paginate(
        queryset,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Paginate queryset and return pagination data

        Args:
            queryset: Django queryset
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with pagination data
        """
        from django.core.paginator import Paginator, EmptyPage

        paginator = Paginator(queryset, page_size)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return {
            'items': list(page_obj),
            'page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }


class AjaxSerializer:
    """
    Helper class for serializing models to JSON
    """

    @staticmethod
    def serialize_model(
        instance,
        fields: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Serialize model instance to dict

        Args:
            instance: Model instance
            fields: List of fields to include (None = all)
            exclude: List of fields to exclude

        Returns:
            Dict representation of instance
        """
        from django.forms.models import model_to_dict

        data = model_to_dict(instance, fields=fields, exclude=exclude)

        # Convert Decimal to string for JSON serialization
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)

        return data

    @staticmethod
    def serialize_queryset(
        queryset,
        fields: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Serialize queryset to list of dicts

        Args:
            queryset: Django queryset
            fields: List of fields to include
            exclude: List of fields to exclude

        Returns:
            List of dict representations
        """
        return [
            AjaxSerializer.serialize_model(item, fields, exclude)
            for item in queryset
        ]

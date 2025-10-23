"""
API Response Validators

Provides validation utilities for API responses.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Common response validation logic for CXE APIs."""

    @staticmethod
    def validate_error_response(error_data: Dict[str, Any]) -> None:
        """
        Validate standard CXE error response structure.

        Args:
            error_data (Dict): Error response data to validate

        Raises:
            AssertionError: If error response structure is invalid
        """
        if isinstance(error_data, dict):
            if "traceId" in error_data:
                assert isinstance(
                    error_data["traceId"], (str, type(None))
                ), "traceId should be string or null"

            if "errMsg" in error_data:
                assert isinstance(error_data["errMsg"], str), "errMsg should be string"

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that all required fields are present in response.

        Args:
            data (Dict): Response data to validate
            required_fields (list): List of required field names

        Raises:
            AssertionError: If any required field is missing
        """
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @staticmethod
    def validate_field_types(data: Dict[str, Any], type_mapping: Dict[str, type]) -> None:
        """
        Validate field types in response data.

        Args:
            data (Dict): Response data to validate
            type_mapping (Dict): Mapping of field names to expected types

        Raises:
            AssertionError: If any field has incorrect type
        """
        for field, expected_type in type_mapping.items():
            if field in data:
                assert isinstance(
                    data[field], expected_type
                ), f"Field '{field}' should be {expected_type}, got {type(data[field])}"


def compare_nested_json_keys(json_str1: str, json_str2: str) -> List[str]:
    """
    Compare keys of two nested JSON strings and return keys present in first but not in second.

    Useful for API schema validation and regression testing.

    Args:
        json_str1: The first JSON string
        json_str2: The second JSON string

    Returns:
        List[str]: Keys present in json_str1 but not in json_str2
        Returns empty list if keys are identical or if there's an error.

    Example:
        >>> json1 = '{"user": {"name": "John", "age": 30}}'
        >>> json2 = '{"user": {"name": "Jane"}}'
        >>> compare_nested_json_keys(json1, json2)
        ['user.age']
    """

    def get_all_keys(data: Any, parent_key: str = "") -> List[str]:
        """Recursively retrieve all keys from JSON object or list."""
        keys = []
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                keys.append(new_key)
                keys.extend(get_all_keys(v, new_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{parent_key}[{i}]" if parent_key else f"[{i}]"
                keys.extend(get_all_keys(item, new_key))
        return keys

    try:
        data1: Any = json.loads(json_str1)
        data2: Any = json.loads(json_str2)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON string provided: {str(e)}")
        return []

    keys1 = get_all_keys(data1)
    keys2 = get_all_keys(data2)

    not_matching_keys = list(set(keys1) - set(keys2))
    return not_matching_keys

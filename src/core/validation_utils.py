"""
Common validation utilities and patterns.

This module provides reusable validation patterns and utilities
to reduce code duplication in the validation service.
"""

from typing import Any, Callable, Optional
from .validation_service import ValidationResult


class ValidationPatterns:
    """Common validation patterns and utilities."""
    
    @staticmethod
    def validate_required_field(value: Any, field_name: str, validator: Callable[[Any], ValidationResult]) -> ValidationResult:
        """
        Apply a common pattern for validating required fields.
        
        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            validator: Validation function to apply
            
        Returns:
            ValidationResult: Result of validation
        """
        if not value or (isinstance(value, str) and not value.strip()):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} é obrigatório"]
            )
        
        return validator(value)
    
    @staticmethod
    def validate_optional_field(value: Any, validator: Callable[[Any], ValidationResult]) -> ValidationResult:
        """
        Apply a common pattern for validating optional fields.
        
        Args:
            value: The value to validate
            validator: Validation function to apply
            
        Returns:
            ValidationResult: Result of validation
        """
        if not value or (isinstance(value, str) and not value.strip()):
            return ValidationResult(is_valid=True, errors=[])
        
        return validator(value)
    
    @staticmethod
    def combine_validation_results(*results: ValidationResult) -> ValidationResult:
        """
        Combine multiple validation results into a single result.
        
        Args:
            *results: Variable number of ValidationResult objects
            
        Returns:
            ValidationResult: Combined result
        """
        all_errors = []
        all_warnings = []
        combined_sanitized = {}
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            if result.sanitized_value:
                if isinstance(result.sanitized_value, dict):
                    combined_sanitized.update(result.sanitized_value)
                else:
                    # Handle non-dict sanitized values - this would need specific handling
                    # based on the field being validated
                    pass
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            sanitized_value=combined_sanitized if combined_sanitized else None
        )
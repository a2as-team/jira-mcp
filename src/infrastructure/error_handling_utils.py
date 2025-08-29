"""
Error handling utilities for infrastructure layer.

This module provides common error handling patterns
to reduce code duplication in infrastructure services.
"""

from typing import Optional, Any, Dict
from jira import JIRAError
from ..core.exceptions import JiraConnectionError, IssueNotFoundError, ProjectNotFoundError
from ..core.error_handler import ErrorHandler


class JiraErrorHandler:
    """Utility class for handling common Jira errors."""
    
    @staticmethod
    def handle_jira_error(
        error: JIRAError, 
        service_name: str, 
        method_name: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle JIRAError with appropriate exception mapping.
        
        Args:
            error: The JIRAError that occurred
            service_name: Name of the service where error occurred
            method_name: Name of the method where error occurred
            context: Optional context information
            
        Raises:
            Appropriate domain exception based on error type
        """
        if error.status_code == 404:
            if "issue" in method_name.lower():
                issue_key = context.get("issue_key") if context else "unknown"
                raise IssueNotFoundError(issue_key)
            elif "project" in method_name.lower():
                project_key = context.get("project_key") if context else "unknown"
                raise ProjectNotFoundError(project_key)
        
        # Log the infrastructure error
        _, error_msg = ErrorHandler.handle_infrastructure_error(
            error, service_name, method_name, context or {}
        )
        
        # Raise appropriate connection error
        raise JiraConnectionError(f"Failed to {method_name.replace('_', ' ')}: {error.text}")
    
    @staticmethod
    def handle_generic_error(
        error: Exception,
        service_name: str,
        method_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle generic exceptions.
        
        Args:
            error: The exception that occurred
            service_name: Name of the service where error occurred
            method_name: Name of the method where error occurred
            context: Optional context information
            
        Raises:
            JiraConnectionError: Always raises this for generic errors
        """
        _, error_msg = ErrorHandler.handle_infrastructure_error(
            error, service_name, method_name, context or {}
        )
        raise JiraConnectionError(f"Failed to {method_name.replace('_', ' ')}: {str(error)}")
    
    @staticmethod
    def try_jira_operation(operation_name: str):
        """
        Decorator factory for common Jira operation error handling.
        
        Args:
            operation_name: Name of the operation for error messages
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except JIRAError as e:
                    JiraErrorHandler.handle_jira_error(
                        e, self.__class__.__name__, func.__name__,
                        {"args": args, "kwargs": kwargs}
                    )
                except (JiraConnectionError, IssueNotFoundError, ProjectNotFoundError):
                    raise
                except Exception as e:
                    JiraErrorHandler.handle_generic_error(
                        e, self.__class__.__name__, func.__name__,
                        {"args": args, "kwargs": kwargs}
                    )
            return wrapper
        return decorator
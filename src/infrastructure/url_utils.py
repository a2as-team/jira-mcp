"""
URL utility functions for Jira operations.

This module provides URL-related utilities for Jira integration,
extracted from the main client to improve code organization.
"""

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class JiraUrlUtils:
    """Utility class for Jira URL operations."""
    
    @staticmethod
    def build_issue_url(server_url: str, issue_key: str) -> str:
        """
        Build the web URL for a Jira issue.
        
        Args:
            server_url: The Jira server URL
            issue_key: The issue key
            
        Returns:
            str: Full URL to the issue in Jira web interface
        """
        try:
            # Remove /rest/api/2 or similar API paths and trailing slashes
            clean_url = server_url.rstrip('/')
            if '/rest/api' in clean_url:
                clean_url = clean_url.split('/rest/api')[0]
            
            return f"{clean_url}/browse/{issue_key}"
            
        except Exception as e:
            logger.warning(f"Could not generate issue URL for {issue_key}: {e}")
            return f"Issue: {issue_key}"
    
    @staticmethod
    def clean_server_url(server_url: str) -> str:
        """
        Clean server URL by removing API paths and trailing slashes.
        
        Args:
            server_url: Raw server URL
            
        Returns:
            str: Cleaned server URL
        """
        clean_url = server_url.rstrip('/')
        if '/rest/api' in clean_url:
            clean_url = clean_url.split('/rest/api')[0]
        return clean_url
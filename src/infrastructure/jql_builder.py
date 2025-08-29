"""
JQL query builder utilities.

This module provides utilities for building JQL queries,
extracted to improve code organization and reusability.
"""

from typing import Optional


class JqlBuilder:
    """Utility class for building JQL queries."""
    
    @staticmethod
    def search_by_summary(summary: str, project_key: Optional[str] = None, max_results: int = 10) -> str:
        """
        Build JQL query for searching issues by summary.
        
        Args:
            summary: The summary text to search for
            project_key: Optional project key to limit search
            max_results: Maximum number of results (not used in JQL but for reference)
            
        Returns:
            str: JQL query string
        """
        if project_key:
            return f'project = "{project_key}" AND summary ~ "{summary}" ORDER BY created DESC'
        else:
            return f'summary ~ "{summary}" ORDER BY created DESC'
    
    @staticmethod
    def get_project_issues(project_key: str, status_filter: Optional[str] = None) -> str:
        """
        Build JQL query for getting project issues.
        
        Args:
            project_key: The project key
            status_filter: Optional status to filter by
            
        Returns:
            str: JQL query string
        """
        jql = f'project = "{project_key}"'
        
        if status_filter:
            jql += f' AND status = "{status_filter}"'
        
        jql += ' ORDER BY created DESC'
        
        return jql
    
    @staticmethod
    def search_all_projects(summary: str) -> str:
        """
        Build JQL query for searching across all projects.
        
        Args:
            summary: The summary text to search for
            
        Returns:
            str: JQL query string
        """
        return f'summary ~ "{summary}" ORDER BY created DESC'
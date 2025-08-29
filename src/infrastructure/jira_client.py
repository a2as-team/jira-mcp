"""
Jira client service for interacting with Jira API.

This module provides a high-level interface for Jira operations
with proper error handling and connection management.
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from jira import JIRA, JIRAError
from jira.resources import Issue, Project

from ..core.config import get_settings
from ..core.logging_config import get_logger
from ..core.exceptions import (
    JiraConnectionError, 
    JiraAuthenticationError, 
    ProjectNotFoundError,
    IssueNotFoundError,
    PermissionError
)
from ..core.error_handler import ErrorHandler
from .url_utils import JiraUrlUtils
from .jql_builder import JqlBuilder

logger = get_logger(__name__)


class JiraClientService:
    """
    High-level Jira client service.
    
    Provides convenient methods for common Jira operations with
    proper error handling and validation.
    """
    
    def __init__(self, jira_client: JIRA):
        """
        Initialize the Jira client service.
        
        Args:
            jira_client: Authenticated JIRA client instance
        """
        self._client = jira_client
        self._current_user = None
        
    @property
    def client(self) -> JIRA:
        """Get the underlying JIRA client."""
        return self._client
    
    def get_current_user(self) -> str:
        """
        Get the current authenticated user.
        
        Returns:
            str: Current user account ID
            
        Raises:
            JiraConnectionError: If unable to get user info
        """
        try:
            if not self._current_user:
                self._current_user = self._client.current_user()
            return self._current_user
        except JIRAError as e:
            error_msg, _ = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "get_current_user"
            )
            raise JiraConnectionError(f"Failed to get current user: {e.text}")
    
    def test_connection(self) -> bool:
        """
        Test the Jira connection.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            JiraConnectionError: If connection fails
        """
        try:
            user = self.get_current_user()
            return user is not None
        except Exception as e:
            _, error_msg = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "test_connection"
            )
            raise JiraConnectionError(f"Connection test failed: {str(e)}")
    
    def get_projects(self) -> List[Project]:
        """
        Get all accessible projects.
        
        Returns:
            List[Project]: List of accessible projects
            
        Raises:
            JiraConnectionError: If unable to fetch projects
        """
        try:
            projects = self._client.projects()
            ErrorHandler.log_info(f"Retrieved {len(projects)} projects", "JiraClientService")
            return projects
        except JIRAError as e:
            _, error_msg = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "get_projects"
            )
            raise JiraConnectionError(f"Failed to get projects: {e.text}")
    
    def find_project(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find a project by key, name, or description.
        
        Args:
            identifier: Project key, name, or search term
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (project_key, error_message)
        """
        try:
            projects = self.get_projects()
            identifier_lower = identifier.lower()
            
            # First, try exact key match
            for project in projects:
                if project.key.lower() == identifier_lower:
                    return project.key, None
            
            # Then try name and description matches
            matches = []
            for project in projects:
                if (identifier_lower in project.name.lower() or
                    (hasattr(project, 'description') and project.description and 
                     identifier_lower in project.description.lower())):
                    matches.append(project)
            
            if len(matches) == 1:
                return matches[0].key, None
            elif len(matches) > 1:
                project_list = ", ".join([f"'{p.name}' ({p.key})" for p in matches])
                return None, f"Multiple projects found for '{identifier}': {project_list}. Please be more specific."
            else:
                return None, f"No project found for identifier '{identifier}'"
                
        except JiraConnectionError:
            raise
        except Exception as e:
            _, error_msg = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "find_project", {"identifier": identifier}
            )
            return None, f"Error searching for project: {str(e)}"
    
    def get_project_details(self, project_key: str) -> Project:
        """
        Get detailed information about a project.
        
        Args:
            project_key: The project key
            
        Returns:
            Project: Project details
            
        Raises:
            ProjectNotFoundError: If project is not found
            JiraConnectionError: If unable to fetch project details
        """
        try:
            project = self._client.project(project_key)
            return project
        except JIRAError as e:
            if e.status_code == 404:
                raise ProjectNotFoundError(project_key)
            else:
                _, error_msg = ErrorHandler.handle_infrastructure_error(
                    e, "JiraClientService", "get_project_details", {"project_key": project_key}
                )
                raise JiraConnectionError(f"Failed to get project details: {e.text}")
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Issue]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List[Issue]: List of issues matching the query
            
        Raises:
            JiraConnectionError: If search fails
        """
        try:
            issues = self._client.search_issues(jql, maxResults=max_results)
            ErrorHandler.log_info(f"Found {len(issues)} issues for JQL: {jql}", "JiraClientService")
            return issues
        except JIRAError as e:
            _, error_msg = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "search_issues", {"jql": jql, "max_results": max_results}
            )
            raise JiraConnectionError(f"Failed to search issues: {e.text}")
    
    def find_issue_by_summary(self, project_key: str, summary: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find an issue by its summary within a project.
        
        Args:
            project_key: The project key to search within
            summary: The issue summary to search for
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (issue_key, error_message)
        """
        try:
            jql = JqlBuilder.search_by_summary(summary, project_key)
            issues = self.search_issues(jql, max_results=20)
            
            if len(issues) == 1:
                return issues[0].key, None
            elif len(issues) > 1:
                issue_list = ", ".join([f"'{i.key}'" for i in issues[:5]])
                if len(issues) > 5:
                    issue_list += f" and {len(issues) - 5} more"
                return None, f"Multiple issues found for summary '{summary}': {issue_list}. Please use exact issue key."
            else:
                return None, f"No issue found with summary '{summary}' in project '{project_key}'"
                
        except JiraConnectionError:
            raise
        except Exception as e:
            return None, f"Error searching for issue: {str(e)}"
    
    def search_issues_by_summary(self, summary: str, max_results: int = 10) -> Tuple[List[Issue], Optional[str]]:
        """
        Search for issues across all accessible projects by summary/title.
        
        Args:
            summary: The issue summary to search for (partial matches allowed)
            max_results: Maximum number of issues to return
            
        Returns:
            Tuple[List[Issue], Optional[str]]: (matching_issues, error_message)
        """
        try:
            jql = JqlBuilder.search_all_projects(summary)
            issues = self.search_issues(jql, max_results=max_results)
            
            return issues, None
                
        except JiraConnectionError:
            raise
        except Exception as e:
            return [], f"Error searching for issues by summary: {str(e)}"
    
    def get_issue_url(self, issue_key: str) -> str:
        """
        Get the web URL for a Jira issue.
        
        Args:
            issue_key: The issue key
            
        Returns:
            str: Full URL to the issue in Jira web interface
        """
        try:
            settings = get_settings()
            return JiraUrlUtils.build_issue_url(settings.jira_server_url, issue_key)
            
        except Exception as e:
            logger.warning(f"Could not generate issue URL for {issue_key}: {e}")
            return f"Issue: {issue_key}"
    
    def get_issue(self, issue_key: str) -> Issue:
        """
        Get an issue by its key.
        
        Args:
            issue_key: The issue key
            
        Returns:
            Issue: The issue object
            
        Raises:
            IssueNotFoundError: If issue is not found
            JiraConnectionError: If unable to fetch issue
        """
        try:
            issue = self._client.issue(issue_key)
            return issue
        except JIRAError as e:
            if e.status_code == 404:
                raise IssueNotFoundError(issue_key)
            else:
                raise JiraConnectionError(f"Failed to get issue: {e.text}")
    
    def create_issue(self, fields: Dict[str, Any]) -> Issue:
        """
        Create a new issue.
        
        Args:
            fields: Issue field values
            
        Returns:
            Issue: The created issue
            
        Raises:
            JiraConnectionError: If issue creation fails
        """
        try:
            issue = self._client.create_issue(fields=fields)
            logger.info(f"Created issue: {issue.key}")
            return issue
        except JIRAError as e:
            raise JiraConnectionError(f"Failed to create issue: {e.text}")
    
    def add_worklog(self, issue_key: str, time_spent: str, started: datetime, comment: str = "") -> bool:
        """
        Add a worklog entry to an issue.
        
        Args:
            issue_key: The issue key
            time_spent: Time spent (e.g., "2h 30m")
            started: When the work started
            comment: Work description
            
        Returns:
            bool: True if worklog was added successfully
            
        Raises:
            IssueNotFoundError: If issue is not found
            JiraConnectionError: If worklog creation fails
        """
        try:
            self._client.add_worklog(
                issue=issue_key,
                timeSpent=time_spent,
                started=started,
                comment=comment
            )
            logger.info(f"Added worklog to {issue_key}: {time_spent}")
            return True
        except JIRAError as e:
            if e.status_code == 404:
                raise IssueNotFoundError(issue_key)
            else:
                raise JiraConnectionError(f"Failed to add worklog: {e.text}")
    
    def get_issue_types(self, project_key: str = None) -> List[Dict[str, str]]:
        """
        Get available issue types for a project or globally.
        
        Args:
            project_key: Optional project key to get project-specific types
            
        Returns:
            List[Dict[str, str]]: List of issue types with id and name
            
        Raises:
            JiraConnectionError: If unable to fetch issue types
        """
        try:
            if project_key:
                project = self.get_project_details(project_key)
                issue_types = project.issueTypes
            else:
                issue_types = self._client.issue_types()
            
            return [{"id": it.id, "name": it.name} for it in issue_types]
        except (ProjectNotFoundError, JiraConnectionError):
            raise
        except Exception as e:
            raise JiraConnectionError(f"Failed to get issue types: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get user account ID by email.
        
        Args:
            email: User email address
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (account_id, error_message)
        """
        try:
            users = self._client.search_users(query=email, maxResults=1)
            if users:
                return users[0].accountId, None
            else:
                return None, f"User with email '{email}' not found"
        except JIRAError as e:
            if e.status_code == 403:
                return None, "Permission denied: Cannot search for users"
            else:
                return None, f"Error searching for user: {e.text}"
        except Exception as e:
            return None, f"Unexpected error searching for user: {str(e)}"
    
    def get_project_issues(self, project_key: str, status_filter: Optional[str] = None, max_results: int = 50) -> List[Issue]:
        """
        Get issues from a specific project.
        
        Args:
            project_key: The project key to get issues from
            status_filter: Optional status to filter by (e.g., "To Do", "In Progress", "Done")
            max_results: Maximum number of issues to return (default: 50)
            
        Returns:
            List[Issue]: List of issues from the project
            
        Raises:
            JiraConnectionError: If unable to fetch issues
        """
        try:
            jql = JqlBuilder.get_project_issues(project_key, status_filter)
            issues = self.search_issues(jql, max_results=max_results)
            
            ErrorHandler.log_info(
                f"Retrieved {len(issues)} issues from project {project_key}", 
                "JiraClientService"
            )
            
            return issues
            
        except JiraConnectionError:
            raise
        except Exception as e:
            _, error_msg = ErrorHandler.handle_infrastructure_error(
                e, "JiraClientService", "get_project_issues", 
                {"project_key": project_key, "status_filter": status_filter}
            )
            raise JiraConnectionError(f"Failed to get project issues: {str(e)}")


# Global client instance
_jira_client_service: Optional[JiraClientService] = None


def get_jira_client() -> JiraClientService:
    """
    Get the global Jira client service instance.
    
    Returns:
        JiraClientService: The Jira client service
        
    Raises:
        JiraConnectionError: If unable to create client
    """
    global _jira_client_service
    
    if _jira_client_service is None:
        settings = get_settings()
        
        try:
            # Create JIRA client with basic authentication
            jira = JIRA(
                server=settings.jira_server_url,
                basic_auth=(settings.jira_username, settings.jira_api_token)
            )
            
            _jira_client_service = JiraClientService(jira)
            
            # Test the connection
            _jira_client_service.test_connection()
            
            logger.info("Jira client initialized successfully")
            
        except JIRAError as e:
            if e.status_code == 401:
                raise JiraAuthenticationError("Invalid Jira credentials")
            else:
                raise JiraConnectionError(f"Failed to connect to Jira: {e.text}")
        except Exception as e:
            raise JiraConnectionError(f"Failed to initialize Jira client: {str(e)}")
    
    return _jira_client_service


def reset_jira_client():
    """Reset the global Jira client (useful for testing)."""
    global _jira_client_service
    _jira_client_service = None
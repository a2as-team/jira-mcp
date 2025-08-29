"""
List issues tool for Jira Agent.

This tool allows the agent to list issues from a specific project.
"""

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.issue_service import IssueService
from ...domain.services.project_service import ProjectService
from ...core.exceptions import JiraConnectionError
from ...core.logging_config import get_logger

logger = get_logger(__name__)


def list_issues(project_identifier: str, status_filter: str = "", max_results: int = 20) -> str:
    """
    List issues from a specific Jira project.
    
    Use this function to:
    - List all issues from a project
    - Filter issues by status (To Do, In Progress, Done, etc.)
    - Get an overview of ongoing issues
    
    Args:
        project_identifier: Project identifier (key or name)
        status_filter: Optional status filter (e.g., "To Do", "In Progress", "Done")
        max_results: Maximum number of issues to return (default: 20)
        
    Returns:
        str: Formatted list of issues
    """
    try:
        logger.info(f"Listing issues for project: '{project_identifier}', status: '{status_filter}', max: {max_results}")
        
        # Get Jira client and services
        jira_client = get_jira_client()
        project_service = ProjectService(jira_client)
        issue_service = IssueService(jira_client)
        
        # Validate and resolve project
        try:
            project_key = project_service.validate_project_access(project_identifier)
        except Exception as e:
            return f"❌ Project not found: {str(e)}"
        
        # Clean and prepare status filter
        status_filter_clean = status_filter.strip() if status_filter else None
        
        # Get issues
        result = issue_service.get_project_issues(
            project_key, 
            status_filter_clean, 
            max_results
        )
        
        # Format the results for display
        formatted_result = issue_service.format_issue_list(
            result.issues, 
            result.project_key,
            result.status_filter
        )
        
        logger.info(f"Listed {result.total_count} issues from project {project_key}")
        
        return formatted_result
        
    except JiraConnectionError as e:
        error_msg = f"❌ Failed to list issues: {e.message}"
        logger.error(error_msg, exc_info=True)
        return error_msg
        
    except Exception as e:
        error_msg = f"❌ Unexpected error while listing issues: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
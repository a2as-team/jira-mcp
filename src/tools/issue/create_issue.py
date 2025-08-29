"""
Create issue tool for Jira Agent.

This tool allows the agent to create a new issue in Jira with validation and optional worklog.
"""

from datetime import datetime

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.project_service import ProjectService
from ...domain.models.issue import IssueCreateInput
from ...core.exceptions import ProjectNotFoundError, JiraConnectionError
from ...core.validation_service import ValidationService
from ...core.error_handler import ErrorHandler
from ...core.logging_config import get_logger
from ...core.date_utils import format_date_for_jira

logger = get_logger(__name__)


def _validate_issue_input(
    project_identifier: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    assignee_email: str = "",
    original_estimate: str = "",
    remaining_estimate: str = "",
    time_spent: str = "",
    work_start_date: str = "",
    work_description: str = ""
) -> IssueCreateInput:
    """
    Validate and create IssueCreateInput object from parameters.
    
    Args:
        All parameters for issue creation
        
    Returns:
        IssueCreateInput: Validated input object
        
    Raises:
        Exception: If input validation fails
    """
    return IssueCreateInput(
        project_identifier=project_identifier,
        summary=summary,
        description=description,
        issue_type=issue_type,
        assignee_email=assignee_email,
        original_estimate=original_estimate,
        remaining_estimate=remaining_estimate,
        time_spent=time_spent,
        work_start_date=work_start_date,
        work_description=work_description
    )


def _validate_project_access(project_service: ProjectService, project_identifier: str) -> str:
    """
    Validate and resolve project access.
    
    Args:
        project_service: Service for project operations
        project_identifier: Project key or name to validate
        
    Returns:
        str: Resolved project key
        
    Raises:
        Exception: If project validation fails
    """
    return project_service.validate_project_access(project_identifier)


def _validate_worklog_data(issue_input: IssueCreateInput) -> None:
    """
    Validate worklog data if provided.
    
    Args:
        issue_input: Issue input containing worklog data
        
    Raises:
        Exception: If worklog validation fails
    """
    if not issue_input.time_spent:
        return
        
    worklog_result = ValidationService.validate_worklog_data(
        issue_input.time_spent,
        issue_input.work_start_date or "",
        issue_input.work_description or ""
    )
    
    if not worklog_result.is_valid:
        validation_error = ErrorHandler.create_validation_error(
            "worklog_data", 
            issue_input.time_spent, 
            worklog_result.errors[0]
        )
        raise validation_error


def _prepare_issue_fields(issue_input: IssueCreateInput, project_key: str) -> dict:
    """
    Prepare Jira issue fields dictionary.
    
    Args:
        issue_input: Validated issue input
        project_key: Resolved project key
        
    Returns:
        dict: Issue fields for Jira API
    """
    issue_fields = {
        "project": {"key": project_key},
        "summary": issue_input.summary.strip(),
        "description": issue_input.description.strip(),
        "issuetype": {"name": issue_input.issue_type},
    }
    
    # Add time tracking if estimates provided
    if issue_input.original_estimate or issue_input.remaining_estimate:
        issue_fields["timetracking"] = {}
        if issue_input.original_estimate:
            issue_fields["timetracking"]["originalEstimate"] = issue_input.original_estimate
        if issue_input.remaining_estimate:
            issue_fields["timetracking"]["remainingEstimate"] = issue_input.remaining_estimate
    
    return issue_fields


def _assign_current_user(jira_client, issue_fields: dict, project_key: str) -> None:
    """
    Try to assign issue to current user.
    
    Args:
        jira_client: Jira client instance
        issue_fields: Issue fields dictionary to modify
        project_key: Project key for logging
    """
    try:
        current_user = jira_client.get_current_user()
        if current_user:
            issue_fields["assignee"] = {"accountId": current_user}
    except Exception as e:
        ErrorHandler.log_warning(
            f"Could not assign issue to current user: {str(e)}", 
            "create_issue",
            {"project_key": project_key}
        )


def _create_jira_issue(jira_client, issue_fields: dict, project_key: str):
    """
    Create the Jira issue.
    
    Args:
        jira_client: Jira client instance
        issue_fields: Issue fields dictionary
        project_key: Project key for error handling
        
    Returns:
        Created Jira issue object
        
    Raises:
        Exception: If issue creation fails
    """
    try:
        new_issue = jira_client.create_issue(issue_fields)
        ErrorHandler.log_info(f"Created issue: {new_issue.key}", "create_issue")
        return new_issue
    except Exception as e:
        raise ErrorHandler.handle_tool_error(
            e, 
            "create_issue",
            {"project_key": project_key, "issue_fields": issue_fields}
        )


def _add_worklog_if_requested(jira_client, issue_input: IssueCreateInput, issue_key: str) -> str:
    """
    Add worklog to issue if requested.
    
    Args:
        jira_client: Jira client instance
        issue_input: Issue input containing worklog data
        issue_key: Created issue key
        
    Returns:
        str: Additional message for worklog result
    """
    if not issue_input.time_spent:
        return ""
        
    try:
        work_datetime = datetime.strptime(issue_input.work_start_date, '%Y-%m-%d')
        jira_client.add_worklog(
            issue_key,
            issue_input.time_spent,
            work_datetime,
            issue_input.work_description or issue_input.description or "Work logged during issue creation"
        )
        return f" Work logged: {issue_input.time_spent} on {issue_input.work_start_date}."
        
    except Exception as e:
        ErrorHandler.log_warning(
            f"Issue created but worklog failed: {str(e)}", 
            "create_issue",
            {"issue_key": issue_key}
        )
        return f" ⚠️ Issue created but failed to log work: {str(e)}"


def create_issue(
    project_identifier: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    assignee_email: str = "",
    original_estimate: str = "",
    remaining_estimate: str = "",
    time_spent: str = "",
    work_start_date: str = "",
    work_description: str = ""
) -> str:
    """
    Cria uma nova issue no Jira com validação abrangente e worklog opcional.
    
    Esta ferramenta cria uma única issue com os detalhes especificados. Pode opcionalmente
    registrar tempo de trabalho imediatamente após a criação se time_spent for fornecido.
    
    Funcionalidades:
    - Validação e resolução de projeto por chave ou nome
    - Validação de tipo de issue
    - Validação de estimativas de tempo (original e restante)
    - Atribuição automática para o usuário atual
    - Criação opcional de worklog imediato
    - Tratamento abrangente de erros
    
    Args:
        project_identifier: Project key or name
        summary: Issue summary
        description: Issue description (optional)
        issue_type: Type of issue (default: Task)
        assignee_email: Email of assignee (optional)
        original_estimate: Original time estimate (optional)
        remaining_estimate: Remaining time estimate (optional)
        time_spent: Time spent for worklog (optional)
        work_start_date: Date when work was done (supports: 'hoje', 'ontem', 'DD-MM-YYYY', etc.)
        work_description: Description of work done (optional)
        
    Returns:
        str: Formatted operation result
    """
    try:
        # Get Jira client and services
        jira_client = get_jira_client()
        project_service = ProjectService(jira_client)
        
        # Parse work start date if provided
        parsed_work_date = work_start_date
        if work_start_date:
            try:
                parsed_work_date = format_date_for_jira(work_start_date)
            except Exception as e:
                return f"❌ Invalid work start date '{work_start_date}': {str(e)}"
        
        # Validate input parameters
        try:
            issue_input = _validate_issue_input(
                project_identifier, summary, description, issue_type,
                assignee_email, original_estimate, remaining_estimate,
                time_spent, parsed_work_date, work_description
            )
        except Exception as e:
            return f"❌ Invalid input: {str(e)}"
        
        # Validate and resolve project
        try:
            project_key = _validate_project_access(project_service, issue_input.project_identifier)
        except Exception as e:
            error_msg = ErrorHandler.handle_tool_error(
                e, 
                "create_issue",
                {"project_identifier": issue_input.project_identifier}
            )
            return error_msg
        
        # Validate worklog data if provided
        try:
            _validate_worklog_data(issue_input)
        except Exception as validation_error:
            error_msg = ErrorHandler.handle_tool_error(validation_error, "create_issue")
            return error_msg
        
        # Prepare issue fields
        issue_fields = _prepare_issue_fields(issue_input, project_key)
        
        # Try to assign to current user
        _assign_current_user(jira_client, issue_fields, project_key)
        
        # Create the issue
        try:
            new_issue = _create_jira_issue(jira_client, issue_fields, project_key)
            success_message = f"✅ Issue {new_issue.key} created successfully!"
            
            # Add worklog if requested
            worklog_message = _add_worklog_if_requested(jira_client, issue_input, new_issue.key)
            success_message += worklog_message
            
            # Add issue URL
            issue_url = jira_client.get_issue_url(new_issue.key)
            success_message += f"\n🔗 Link: {issue_url}"
            
            return success_message
            
        except Exception as e:
            error_msg = ErrorHandler.handle_tool_error(
                e, 
                "create_issue",
                {"project_key": project_key, "issue_fields": issue_fields}
            )
            return error_msg
        
    except Exception as e:
        error_msg = ErrorHandler.handle_tool_error(e, "create_issue")
        return error_msg



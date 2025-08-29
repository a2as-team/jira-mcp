"""
Create completed task tool for Jira Agent.

This tool creates a new issue in Jira that is automatically marked as completed 
with worklog already added.
"""

from datetime import datetime

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.project_service import ProjectService
from ...domain.models.issue import IssueCreateInput
from ...core.exceptions import ProjectNotFoundError, JiraConnectionError
from ...core.validation_service import ValidationService
from ...core.error_handler import ErrorHandler
from ...core.logging_config import get_logger
from ...core.date_utils import format_date_for_jira, get_current_date

logger = get_logger(__name__)


def _validate_completed_task_input(
    project_identifier: str,
    summary: str,
    description: str = "",
    assignee_email: str = "",
    time_spent: str = "1h",
    work_description: str = ""
) -> IssueCreateInput:
    """
    Validate and create IssueCreateInput object for completed task.
    
    Args:
        project_identifier: Project key or name
        summary: Task summary
        description: Task description (optional)
        assignee_email: Email of assignee (optional)
        time_spent: Time spent on task (default: 1h)
        work_description: Description of work done (optional)
        
    Returns:
        IssueCreateInput: Validated input object
        
    Raises:
        Exception: If input validation fails
    """
    return IssueCreateInput(
        project_identifier=project_identifier,
        summary=summary,
        description=description,
        issue_type="Task",
        assignee_email=assignee_email,
        original_estimate="",
        remaining_estimate="",
        time_spent=time_spent,
        work_start_date=get_current_date(),
        work_description=work_description
    )


def _prepare_completed_task_fields(issue_input: IssueCreateInput, project_key: str) -> dict:
    """
    Prepare Jira issue fields dictionary for completed task.
    
    Args:
        issue_input: Validated issue input
        project_key: Resolved project key
        
    Returns:
        dict: Issue fields for Jira API
    """
    issue_fields = {
        "project": {"key": project_key},
        "summary": issue_input.summary.strip(),
        "description": issue_input.description.strip() or "Task completed automatically",
        "issuetype": {"name": "Task"},
    }
    
    return issue_fields


def _transition_to_done(jira_client, issue_key: str) -> bool:
    """
    Transition issue to Done status.
    
    Args:
        jira_client: Jira client instance
        issue_key: Issue key to transition
        
    Returns:
        bool: True if transition was successful
    """
    try:
        # Get available transitions
        transitions = jira_client.get_transitions(issue_key)
        
        # Find Done transition (common names: Done, Concluído, Finished, Resolved)
        done_transitions = [
            t for t in transitions 
            if t['name'].lower() in ['done', 'concluído', 'finished', 'resolved', 'fechado', 'complete']
        ]
        
        if done_transitions:
            transition_id = done_transitions[0]['id']
            jira_client.transition_issue(issue_key, transition_id)
            logger.info(f"Transitioned issue {issue_key} to Done")
            return True
        else:
            logger.warning(f"No 'Done' transition found for issue {issue_key}")
            available_transitions = [t['name'] for t in transitions]
            logger.info(f"Available transitions: {available_transitions}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to transition issue {issue_key} to Done: {str(e)}")
        return False


def _add_completion_worklog(jira_client, issue_input: IssueCreateInput, issue_key: str) -> str:
    """
    Add worklog to completed issue.
    
    Args:
        jira_client: Jira client instance
        issue_input: Issue input containing worklog data
        issue_key: Created issue key
        
    Returns:
        str: Worklog result message
    """
    try:
        work_datetime = datetime.strptime(issue_input.work_start_date, '%Y-%m-%d')
        work_desc = issue_input.work_description or "Task completed"
        
        jira_client.add_worklog(
            issue_key,
            issue_input.time_spent,
            work_datetime,
            work_desc
        )
        return f" Work logged: {issue_input.time_spent} on {issue_input.work_start_date}."
        
    except Exception as e:
        logger.error(f"Failed to add worklog to issue {issue_key}: {str(e)}")
        return f" ⚠️ Issue created but failed to log work: {str(e)}"


def create_completed_task(
    project_identifier: str,
    summary: str,
    description: str = "",
    assignee_email: str = "",
    time_spent: str = "1h",
    work_description: str = "",
    work_date: str = "hoje"
) -> str:
    """
    Cria uma nova task no Jira já marcada como concluída com worklog automaticamente adicionado.
    
    Esta ferramenta cria uma task e automaticamente:
    - Define o status como "Done" (Concluído)
    - Adiciona worklog com o tempo especificado
    - Atribui ao usuário atual se não especificado
    
    Args:
        project_identifier: Project key or name
        summary: Task summary
        description: Task description (optional)
        assignee_email: Email of assignee (optional, defaults to current user)
        time_spent: Time spent on task (default: 1h)
        work_description: Description of work done (optional)
        work_date: Date when work was done (supports: 'hoje', 'ontem', 'DD-MM-YYYY', etc.)
        
    Returns:
        str: Formatted operation result
    """
    try:
        # Get Jira client and services
        jira_client = get_jira_client()
        project_service = ProjectService(jira_client)
        
        # Parse and validate work date
        try:
            parsed_work_date = format_date_for_jira(work_date)
        except Exception as e:
            return f"❌ Invalid work date '{work_date}': {str(e)}"
        
        # Validate input parameters
        try:
            issue_input = _validate_completed_task_input(
                project_identifier, summary, description,
                assignee_email, time_spent, work_description
            )
            # Override the work date with parsed date
            issue_input.work_start_date = parsed_work_date
        except Exception as e:
            return f"❌ Invalid input: {str(e)}"
        
        # Validate and resolve project
        try:
            project_key = project_service.validate_project_access(issue_input.project_identifier)
        except Exception as e:
            error_msg = ErrorHandler.handle_tool_error(
                e, 
                "create_completed_task",
                {"project_identifier": issue_input.project_identifier}
            )
            return error_msg
        
        # Prepare issue fields
        issue_fields = _prepare_completed_task_fields(issue_input, project_key)
        
        # Assign to current user if no specific assignee
        if not issue_input.assignee_email:
            try:
                current_user = jira_client.get_current_user()
                if current_user:
                    issue_fields["assignee"] = {"accountId": current_user}
            except Exception as e:
                logger.warning(f"Could not assign task to current user: {str(e)}")
        
        # Create the issue
        try:
            new_issue = jira_client.create_issue(issue_fields)
            logger.info(f"Created task: {new_issue.key}")
            
            # Add worklog first
            worklog_message = _add_completion_worklog(jira_client, issue_input, new_issue.key)
            
            # Transition to Done
            transition_success = _transition_to_done(jira_client, new_issue.key)
            
            # Prepare success message
            success_message = f"✅ Completed task {new_issue.key} created successfully!"
            success_message += worklog_message
            
            if transition_success:
                success_message += " Status: Done ✅"
            else:
                success_message += " ⚠️ Could not automatically set to Done status - please do it manually."
            
            # Add issue URL
            issue_url = jira_client.get_issue_url(new_issue.key)
            success_message += f"\n🔗 Link: {issue_url}"
            
            return success_message
            
        except Exception as e:
            error_msg = ErrorHandler.handle_tool_error(
                e, 
                "create_completed_task",
                {"project_key": project_key, "issue_fields": issue_fields}
            )
            return error_msg
        
    except Exception as e:
        error_msg = ErrorHandler.handle_tool_error(e, "create_completed_task")
        return error_msg
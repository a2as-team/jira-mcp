"""
Create issue tool for Jira Agent.

This tool allows the agent to create a new issue in Jira with validation and optional worklog.
"""

from datetime import datetime
from google.adk.tools import ToolContext

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.project_service import ProjectService
from ...domain.models.issue import IssueCreateInput
from ...core.exceptions import ProjectNotFoundError, JiraConnectionError
from ...core.validation_service import ValidationService
from ...core.error_handler import ErrorHandler
from ...core.logging_config import get_logger

logger = get_logger(__name__)


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
    work_description: str = "",
    tool_context: ToolContext = None
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
        tool_input: Parâmetros de criação de issue com validação
        tool_context: Contexto da ferramenta ADK
        
    Returns:
        str: Resultado formatado da operação
    """
    try:
        # Get Jira client and services
        jira_client = get_jira_client()
        project_service = ProjectService(jira_client)
        
        # Create IssueCreateInput from parameters
        try:
            issue_input = IssueCreateInput(
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
        except Exception as e:
            return f"❌ Invalid input: {str(e)}"
        
        # Validate and resolve project
        try:
            project_key = project_service.validate_project_access(issue_input.project_identifier)
        except Exception as e:
            error_msg = ErrorHandler.handle_tool_error(
                e, 
                "create_issue",
                {"project_identifier": issue_input.project_identifier}
            )
            return error_msg
        
        # Validar dados de worklog se fornecidos
        if issue_input.time_spent:
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
                error_msg = ErrorHandler.handle_tool_error(validation_error, "create_issue")
                return error_msg
        
        # Prepare issue fields
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
        
        # Try to assign to current user
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
        
        # Create the issue
        try:
            new_issue = jira_client.create_issue(issue_fields)
            ErrorHandler.log_info(f"Created issue: {new_issue.key}", "create_issue")
            
            success_message = f"✅ Issue {new_issue.key} created successfully!"
            
            # Add worklog if requested
            if issue_input.time_spent:
                try:
                    work_datetime = datetime.strptime(issue_input.work_start_date, '%Y-%m-%d')
                    jira_client.add_worklog(
                        new_issue.key,
                        issue_input.time_spent,
                        work_datetime,
                        issue_input.work_description or issue_input.description or "Work logged during issue creation"
                    )
                    success_message += f" Work logged: {issue_input.time_spent} on {issue_input.work_start_date}."
                    
                except Exception as e:
                    ErrorHandler.log_warning(
                        f"Issue created but worklog failed: {str(e)}", 
                        "create_issue",
                        {"issue_key": new_issue.key}
                    )
                    success_message += f" ⚠️ Issue created but failed to log work: {str(e)}"
            
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



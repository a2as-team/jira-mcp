"""
Add worklog tool for Jira Agent.

This tool allows the agent to add time tracking entries to existing issues.
"""

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.worklog_service import WorklogService
from ...domain.models.worklog import WorklogCreateInput
from ...core.exceptions import IssueNotFoundError, JiraConnectionError
from ...core.logging_config import get_logger

logger = get_logger(__name__)


def add_worklog(
    issue_identifier: str, 
    time_spent: str, 
    work_date: str = "", 
    description: str = ""
) -> str:
    """
    Adiciona registro de tempo de trabalho a uma issue existente do Jira.
    
    Use esta ferramenta para:
    - Registrar tempo trabalhado em issues já criadas usando chave (PROJ-123) ou nome da issue
    - Documentar trabalho realizado com descrição
    - Manter controle de horas gastas em projetos
    - Se múltiplas issues corresponderem ao nome, mostra opções para escolher
    
    Args:
        issue_identifier: Chave da issue (ex: 'PROJ-123') ou nome/resumo da issue (ex: 'Remoção de Código')
        time_spent: Tempo gasto (ex: '2h 30m', '1d', '4h', '30m')
        work_date: Data do trabalho no formato YYYY-MM-DD (padrão: hoje)
        description: Descrição do trabalho realizado
        
    Returns:
        str: Resultado da operação de adição de worklog
    """
    try:
        logger.info(f"Adding worklog to issue: '{issue_identifier}', time: '{time_spent}', date: '{work_date}'")
        
        # Get Jira client and worklog service
        jira_client = get_jira_client()
        worklog_service = WorklogService(jira_client)
        
        # Resolve issue identifier (key or name) to exact issue key
        resolved_key, message = worklog_service.resolve_issue_identifier(issue_identifier.strip())
        
        if not resolved_key:
            # Either error or multiple options - return the message
            return message
        
        # Create worklog input with resolved issue key
        try:
            worklog_input = WorklogCreateInput(
                issue_key=resolved_key,
                time_spent=time_spent.strip(),
                work_date=work_date.strip() if work_date else None,
                description=description.strip() if description else ""
            )
        except Exception as e:
            return f"❌ Invalid input: {str(e)}"
        
        # Add worklog
        result = worklog_service.add_worklog_to_issue(worklog_input)
        
        logger.info(f"Worklog added successfully to {resolved_key}")
        
        return result
        
    except IssueNotFoundError as e:
        error_msg = f"❌ Issue not found: {e.issue_identifier}. Please verify the issue key is correct."
        logger.warning(error_msg, exc_info=True)
        return error_msg
        
    except JiraConnectionError as e:
        error_msg = f"❌ Failed to add worklog: {e.message}"
        logger.error(error_msg, exc_info=True)
        return error_msg
        
    except Exception as e:
        error_msg = f"❌ Unexpected error while adding worklog: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg



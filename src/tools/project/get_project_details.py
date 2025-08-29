"""
Get project details tool for Jira Agent.

This tool allows the agent to retrieve detailed information about a specific Jira project.
"""

from ...infrastructure.jira_client import get_jira_client
from ...domain.services.project_service import ProjectService
from ...core.exceptions import ProjectNotFoundError, JiraConnectionError
from ...core.logging_config import get_logger

logger = get_logger(__name__)


def get_project_details(project_identifier: str) -> str:
    """
    Obtém informações detalhadas sobre um projeto específico do Jira.
    
    Use esta ferramenta para:
    - Obter informações abrangentes sobre um projeto
    - Verificar a existência do projeto antes de criar issues
    - Entender a estrutura e configuração do projeto
    
    Args:
        project_identifier: Project identifier - can be project key or name
        
    Returns:
        str: Formatted result of the operation
    """
    try:
        logger.info(f"Getting project details for: '{project_identifier}'")
        
        # Get Jira client and project service
        jira_client = get_jira_client()
        project_service = ProjectService(jira_client)
        
        # Get project details
        project = project_service.get_project_by_identifier(project_identifier)
        
        # Format the project details for display
        formatted_details = project_service.format_project_details(project)
        
        logger.info(f"Retrieved project details for: {project.key}")
        
        return f"✅ Project details retrieved successfully:\n\n{formatted_details}"
        
    except ProjectNotFoundError as e:
        error_msg = f"❌ Project not found: {e.message}"
        logger.warning(error_msg, exc_info=True)
        return error_msg
        
    except JiraConnectionError as e:
        error_msg = f"❌ Failed to get project details: {e.message}"
        logger.error(error_msg, exc_info=True)
        return error_msg
        
    except Exception as e:
        error_msg = f"❌ Unexpected error while getting project details: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg



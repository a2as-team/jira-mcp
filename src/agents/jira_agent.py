"""
Main Jira Agent using Google ADK.

This module defines the primary agent that handles all Jira interactions
using the proper ADK patterns and tools.
"""

from google.adk.agents import Agent

from ..core.config import get_settings
from ..core.logging_config import get_logger
from ..core.callbacks import before_tool_callback, after_tool_callback, rate_limit_callback
from .project_agent import project_agent
from .issue_agent import issue_agent
from .worklog_agent import worklog_agent

logger = get_logger(__name__)


def create_jira_agent() -> Agent:
    """
    Create and configure the main Jira agent.
    
    Returns:
        Agent: Configured Jira agent with specialized sub-agents
    """
    settings = get_settings()
    
    # Instrução do agente coordenador em português
    instruction = """
    Você é o assistente principal do Jira, responsável por coordenar operações através de agentes especializados.
    
    ARQUITETURA DE SUB-AGENTES:
    Você trabalha com três agentes especializados:
    - **project_agent**: Especialista em busca e detalhes de projetos
    - **issue_agent**: Especialista em criação e listagem de issues
    - **worklog_agent**: Especialista em registros de tempo de trabalho
    
    FLUXO DE TRABALHO:
    1. Analise a solicitação do usuário e identifique qual área é necessária
    2. Delegue para o agente especializado apropriado:
       - Operações com projetos → project_agent
       - Operações com issues → issue_agent  
       - Operações com worklog → worklog_agent
    3. Coordene múltiplos agentes quando necessário (ex: buscar projeto, depois criar issue)
    4. Consolide e apresente os resultados finais de forma clara
    
    RESPONSABILIDADES DE COORDENAÇÃO:
    - Identifique dependências entre operações (ex: precisa do projeto antes de criar issue)
    - Passe informações necessárias entre agentes
    - Valide que o usuário tenha as informações necessárias
    - Forneça orientação e feedback consolidado
    - Trate erros e coordene tentativas de recuperação
    
    EXEMPLOS DE COORDENAÇÃO:
    - "Criar issue no projeto X" → project_agent (buscar projeto) → issue_agent (criar issue)
    - "Registrar tempo na issue Y" → worklog_agent (adicionar worklog)
    - "Listar projetos" → project_agent (buscar projetos)
    
    Sempre priorize:
    - Segurança e validação de dados
    - Feedback claro sobre operações realizadas
    - Coordenação eficiente entre agentes especializados
    - Experiência fluida para o usuário
    
    Responda sempre em português brasileiro, coordenando os agentes especializados para
    fornecer a melhor experiência possível ao usuário.
    """
    
    # Create the root agent with sub-agents architecture following ADK pattern
    agent = Agent(
        name="JiraAgent",
        description=(
            "Agente coordenador do Jira que gerencia operações através de agentes especializados. "
            "Coordena project_agent para projetos, issue_agent para issues e worklog_agent para "
            "registros de tempo, fornecendo uma experiência integrada e segura."
        ),
        model=settings.google_model,
        instruction=instruction,
        sub_agents=[
            project_agent,
            issue_agent,
            worklog_agent
        ],
        # No tools needed on root agent - coordination is done through sub-agents
        tools=[],
        # Integrate security and logging callbacks
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
        before_model_callback=rate_limit_callback
    )
    
    logger.info(
        "Agente Jira coordenador criado com sucesso",
        extra={
            "model": settings.google_model,
            "sub_agents_count": len(agent.sub_agents) if hasattr(agent, 'sub_agents') else 0,
            "sub_agents": ["project_agent", "issue_agent", "worklog_agent"],
            "callbacks_enabled": True,
            "environment": settings.environment
        }
    )
    
    return agent


# Create the global agent instance
jira_agent = create_jira_agent()
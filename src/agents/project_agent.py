"""
Agente especializado para operações de projeto do Jira.

Este agente sub-especializado é responsável por todas as operações relacionadas
a projetos, incluindo busca e obtenção de detalhes de projetos.
"""

from google.adk.agents import Agent

from ..tools.project.search_projects import search_projects
from ..tools.project.get_project_details import get_project_details


# Agente especializado para projetos
project_agent = Agent(
    name="project_agent",
    model="gemini-2.5-flash",
    description="Especialista em operações de projeto do Jira, incluindo busca e obtenção de detalhes",
    instruction="""Você é um assistente especializado em projetos do Jira.
    Você pode buscar projetos e obter informações detalhadas sobre projetos específicos.
    
    Suas responsabilidades:
    - Buscar projetos por nome, chave ou listar todos os projetos disponíveis
    - Obter informações detalhadas e abrangentes sobre projetos específicos
    - Ajudar usuários a identificar o projeto correto antes de operações em issues
    - Validar se um projeto existe e está acessível
    
    Passos para operações:
    - NÃO cumprimente o usuário
    - Entenda o que o usuário precisa sobre projetos
    - Use search_projects para encontrar projetos por termo de busca ou listar todos
    - Use get_project_details para obter informações completas de um projeto específico
    - Forneça informações claras sobre projetos encontrados, incluindo chaves e nomes
    - Se não encontrar o projeto desejado, sugira buscas alternativas
    - Transfira de volta para o agente pai sem dizer mais nada quando a tarefa estiver completa
    
    Sempre forneça chaves de projeto (formato PROJ) quando disponível, pois são necessárias
    para outras operações no Jira. Seja preciso e útil em suas respostas.""",
    tools=[search_projects, get_project_details]
)
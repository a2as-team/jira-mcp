"""
Serviço centralizado de validação para Jira Agent.

Este módulo fornece validação centralizada e reutilizável para
todos os tipos de dados usados na aplicação.
"""

import re
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from .validators import (
    validate_date_format, 
    validate_issue_key_format, 
    validate_time_format,
    validate_email_format,
    sanitize_summary,
    sanitize_description
)


@dataclass
class ValidationResult:
    """
    Resultado de uma operação de validação.
    
    Attributes:
        is_valid: True se a validação passou
        errors: Lista de mensagens de erro
        warnings: Lista de mensagens de aviso
        sanitized_value: Valor limpo/sanitizado (se aplicável)
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None
    sanitized_value: Any = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ValidationService:
    """
    Serviço centralizado de validação.
    
    Fornece métodos de validação reutilizáveis para todos os
    componentes da aplicação.
    """
    
    @staticmethod
    def validate_time_format(time_str: str) -> ValidationResult:
        """
        Valida formato de tempo do Jira.
        
        Args:
            time_str: String de tempo a ser validada
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not time_str or not time_str.strip():
            return ValidationResult(is_valid=True, errors=[])
        
        time_str = time_str.strip()
        
        if validate_time_format(time_str):
            return ValidationResult(
                is_valid=True, 
                errors=[], 
                sanitized_value=time_str
            )
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Formato de tempo inválido: '{time_str}'. Use formato como '2h 30m', '1d', '4h'"]
            )
    
    @staticmethod
    def validate_date_format(date_str: str, required: bool = False) -> ValidationResult:
        """
        Valida formato de data (YYYY-MM-DD).
        
        Args:
            date_str: String de data a ser validada
            required: Se a data é obrigatória
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not date_str or not date_str.strip():
            if required:
                return ValidationResult(
                    is_valid=False,
                    errors=["Data é obrigatória"]
                )
            return ValidationResult(is_valid=True, errors=[])
        
        date_str = date_str.strip()
        
        if not validate_date_format(date_str):
            return ValidationResult(
                is_valid=False,
                errors=[f"Formato de data inválido: '{date_str}'. Use formato YYYY-MM-DD"]
            )
        
        # Verificar se a data não está no futuro
        try:
            work_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if work_date > date.today():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"A data não pode estar no futuro: '{date_str}'"]
                )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                errors=[f"Data inválida: '{date_str}'"]
            )
        
        return ValidationResult(
            is_valid=True, 
            errors=[], 
            sanitized_value=date_str
        )
    
    @staticmethod
    def validate_issue_key(issue_key: str, required: bool = True) -> ValidationResult:
        """
        Valida formato de chave de issue do Jira.
        
        Args:
            issue_key: Chave da issue a ser validada
            required: Se a chave é obrigatória
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not issue_key or not issue_key.strip():
            if required:
                return ValidationResult(
                    is_valid=False,
                    errors=["Chave da issue é obrigatória"]
                )
            return ValidationResult(is_valid=True, errors=[])
        
        issue_key = issue_key.strip().upper()
        
        if validate_issue_key_format(issue_key):
            return ValidationResult(
                is_valid=True, 
                errors=[], 
                sanitized_value=issue_key
            )
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Formato de chave de issue inválido: '{issue_key}'. Use formato como 'PROJ-123'"]
            )
    
    @staticmethod
    def validate_project_identifier(identifier: str) -> ValidationResult:
        """
        Valida identificador de projeto.
        
        Args:
            identifier: Identificador do projeto (chave ou nome)
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not identifier or not identifier.strip():
            return ValidationResult(
                is_valid=False,
                errors=["Identificador do projeto é obrigatório"]
            )
        
        identifier = identifier.strip()
        
        if len(identifier) < 2:
            return ValidationResult(
                is_valid=False,
                errors=["Identificador do projeto deve ter pelo menos 2 caracteres"]
            )
        
        return ValidationResult(
            is_valid=True, 
            errors=[], 
            sanitized_value=identifier
        )
    
    @staticmethod
    def validate_issue_summary(summary: str) -> ValidationResult:
        """
        Valida e sanitiza título de issue.
        
        Args:
            summary: Título da issue
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not summary or not summary.strip():
            return ValidationResult(
                is_valid=False,
                errors=["O título da issue não pode estar vazio"]
            )
        
        sanitized = sanitize_summary(summary)
        
        if len(sanitized) < 3:
            return ValidationResult(
                is_valid=False,
                errors=["O título da issue deve ter pelo menos 3 caracteres"]
            )
        
        warnings = []
        if len(sanitized) > 200:
            warnings.append("Título muito longo, foi truncado para 200 caracteres")
        
        return ValidationResult(
            is_valid=True, 
            errors=[], 
            warnings=warnings,
            sanitized_value=sanitized
        )
    
    @staticmethod
    def validate_issue_description(description: str) -> ValidationResult:
        """
        Valida e sanitiza descrição de issue.
        
        Args:
            description: Descrição da issue
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not description:
            description = ""
        
        sanitized = sanitize_description(description)
        
        return ValidationResult(
            is_valid=True, 
            errors=[], 
            sanitized_value=sanitized
        )
    
    @staticmethod
    def validate_email(email: str, required: bool = False) -> ValidationResult:
        """
        Valida formato de email.
        
        Args:
            email: Email a ser validado
            required: Se o email é obrigatório
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not email or not email.strip():
            if required:
                return ValidationResult(
                    is_valid=False,
                    errors=["Email é obrigatório"]
                )
            return ValidationResult(is_valid=True, errors=[])
        
        email = email.strip().lower()
        
        if validate_email_format(email):
            return ValidationResult(
                is_valid=True, 
                errors=[], 
                sanitized_value=email
            )
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Formato de email inválido: '{email}'"]
            )
    
    @staticmethod
    def validate_worklog_data(time_spent: str, work_date: str, description: str = "") -> ValidationResult:
        """
        Valida dados completos de worklog.
        
        Args:
            time_spent: Tempo gasto
            work_date: Data do trabalho
            description: Descrição do trabalho
            
        Returns:
            ValidationResult: Resultado da validação
        """
        errors = []
        warnings = []
        sanitized_values = {}
        
        # Validar tempo gasto
        time_result = ValidationService.validate_time_format(time_spent)
        if not time_result.is_valid:
            errors.extend(time_result.errors)
        else:
            sanitized_values["time_spent"] = time_result.sanitized_value
        
        # Validar data (obrigatória se time_spent for fornecido)
        date_required = bool(time_spent and time_spent.strip())
        date_result = ValidationService.validate_date_format(work_date, required=date_required)
        if not date_result.is_valid:
            errors.extend(date_result.errors)
        else:
            sanitized_values["work_date"] = date_result.sanitized_value
        
        # Validar descrição
        desc_result = ValidationService.validate_issue_description(description)
        sanitized_values["description"] = desc_result.sanitized_value
        warnings.extend(desc_result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_values
        )
    
    @staticmethod
    def _validate_core_issue_fields(data: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """
        Validate core issue fields (project, summary, description).
        
        Args:
            data: Issue data dictionary
            
        Returns:
            Tuple[List[str], List[str], Dict[str, Any]]: (errors, warnings, sanitized_values)
        """
        errors = []
        warnings = []
        sanitized_values = {}
        
        # Validar identificador do projeto
        project_result = ValidationService.validate_project_identifier(
            data.get("project_identifier", "")
        )
        if not project_result.is_valid:
            errors.extend(project_result.errors)
        else:
            sanitized_values["project_identifier"] = project_result.sanitized_value
        
        # Validar título
        summary_result = ValidationService.validate_issue_summary(
            data.get("summary", "")
        )
        if not summary_result.is_valid:
            errors.extend(summary_result.errors)
        else:
            sanitized_values["summary"] = summary_result.sanitized_value
            warnings.extend(summary_result.warnings)
        
        # Validar descrição
        desc_result = ValidationService.validate_issue_description(
            data.get("description", "")
        )
        sanitized_values["description"] = desc_result.sanitized_value
        warnings.extend(desc_result.warnings)
        
        return errors, warnings, sanitized_values
    
    @staticmethod
    def _validate_time_estimates(data: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Validate time estimate fields.
        
        Args:
            data: Issue data dictionary
            
        Returns:
            Tuple[List[str], Dict[str, Any]]: (errors, sanitized_values)
        """
        errors = []
        sanitized_values = {}
        
        for field in ["original_estimate", "remaining_estimate"]:
            if field in data:
                time_result = ValidationService.validate_time_format(data[field])
                if not time_result.is_valid:
                    errors.extend(time_result.errors)
                else:
                    sanitized_values[field] = time_result.sanitized_value
                    
        return errors, sanitized_values
    
    @staticmethod
    def _validate_assignee_data(data: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Validate assignee-related data.
        
        Args:
            data: Issue data dictionary
            
        Returns:
            Tuple[List[str], Dict[str, Any]]: (errors, sanitized_values)
        """
        errors = []
        sanitized_values = {}
        
        if "assignee_email" in data:
            email_result = ValidationService.validate_email(data["assignee_email"])
            if not email_result.is_valid:
                errors.extend(email_result.errors)
            else:
                sanitized_values["assignee_email"] = email_result.sanitized_value
                
        return errors, sanitized_values
    
    @staticmethod
    def _validate_worklog_if_present(data: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """
        Validate worklog data if present.
        
        Args:
            data: Issue data dictionary
            
        Returns:
            Tuple[List[str], List[str], Dict[str, Any]]: (errors, warnings, sanitized_values)
        """
        errors = []
        warnings = []
        sanitized_values = {}
        
        if data.get("time_spent"):
            worklog_result = ValidationService.validate_worklog_data(
                data.get("time_spent", ""),
                data.get("work_start_date", ""),
                data.get("work_description", "")
            )
            if not worklog_result.is_valid:
                errors.extend(worklog_result.errors)
            else:
                sanitized_values.update(worklog_result.sanitized_value)
            warnings.extend(worklog_result.warnings)
            
        return errors, warnings, sanitized_values
    
    @staticmethod
    def validate_issue_create_data(data: Dict[str, Any]) -> ValidationResult:
        """
        Valida dados completos para criação de issue.
        
        Args:
            data: Dicionário com dados da issue
            
        Returns:
            ValidationResult: Resultado da validação
        """
        all_errors = []
        all_warnings = []
        all_sanitized = {}
        
        # Validate core fields
        core_errors, core_warnings, core_sanitized = ValidationService._validate_core_issue_fields(data)
        all_errors.extend(core_errors)
        all_warnings.extend(core_warnings)
        all_sanitized.update(core_sanitized)
        
        # Validate time estimates
        time_errors, time_sanitized = ValidationService._validate_time_estimates(data)
        all_errors.extend(time_errors)
        all_sanitized.update(time_sanitized)
        
        # Validate assignee data
        assignee_errors, assignee_sanitized = ValidationService._validate_assignee_data(data)
        all_errors.extend(assignee_errors)
        all_sanitized.update(assignee_sanitized)
        
        # Validate worklog if present
        worklog_errors, worklog_warnings, worklog_sanitized = ValidationService._validate_worklog_if_present(data)
        all_errors.extend(worklog_errors)
        all_warnings.extend(worklog_warnings)
        all_sanitized.update(worklog_sanitized)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            sanitized_value=all_sanitized
        )
    
    @staticmethod
    def validate_batch_size(items: List[Any], max_size: int = 50, operation_name: str = "operação") -> ValidationResult:
        """
        Valida tamanho de operação em lote.
        
        Args:
            items: Lista de itens a serem processados
            max_size: Tamanho máximo permitido
            operation_name: Nome da operação para mensagens de erro
            
        Returns:
            ValidationResult: Resultado da validação
        """
        if not items:
            return ValidationResult(
                is_valid=False,
                errors=[f"Lista de itens para {operation_name} não pode estar vazia"]
            )
        
        if len(items) > max_size:
            return ValidationResult(
                is_valid=False,
                errors=[f"Não é possível processar mais de {max_size} itens em uma {operation_name} em lote"]
            )
        
        warnings = []
        if len(items) > 20:
            warnings.append(f"Processando {len(items)} itens, operação pode demorar mais")
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            sanitized_value=items
        )
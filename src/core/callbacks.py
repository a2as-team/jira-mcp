"""
Callback functions for ADK agents following Customer Service pattern.

This module provides security, logging, and control callbacks for Jira agents
including tool validation, rate limiting, and audit trail functionality.
"""

import time
from typing import Dict, Any, Optional
from google.adk.tools import BaseTool, ToolContext
from google.genai.types import Content, Part

from .logging_config import get_logger
from .exceptions import JiraConnectionError, ValidationError

logger = get_logger(__name__)

# Rate limiting state
_rate_limit_state = {
    'last_call': 0,
    'call_count': 0,
    'window_start': 0
}

def before_tool_callback(
    tool: BaseTool, 
    args: Dict[str, Any], 
    tool_context: ToolContext
) -> Optional[Dict]:
    """
    Validates tool arguments and logs tool calls before execution.
    
    Args:
        tool: The tool being called
        args: Arguments passed to the tool
        tool_context: ADK tool context
        
    Returns:
        None to allow execution, Dict to block with custom response
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
    agent_name = tool_context.agent_name if tool_context else "unknown"
    
    logger.info(
        "Tool call initiated",
        extra={
            "tool_name": tool_name,
            "agent_name": agent_name,
            "args_provided": list(args.keys()) if args else []
        }
    )
    
    # Validate sensitive operations
    if _is_sensitive_operation(tool_name, args):
        validation_result = _validate_sensitive_operation(tool_name, args)
        if not validation_result["allowed"]:
            logger.warning(
                "Sensitive operation blocked",
                extra={
                    "tool_name": tool_name,
                    "reason": validation_result["reason"],
                    "args": args
                }
            )
            return {
                "status": "error",
                "message": f"❌ Operação bloqueada: {validation_result['reason']}"
            }
    
    # Validate project identifier format for project-related operations
    if "project" in tool_name.lower() and "project_identifier" in args:
        project_id = args.get("project_identifier", "").strip()
        if not project_id:
            return {
                "status": "error", 
                "message": "❌ Identificador do projeto é obrigatório"
            }
        if len(project_id) > 255:
            return {
                "status": "error",
                "message": "❌ Identificador do projeto muito longo (máximo 255 caracteres)"
            }
    
    # Log successful validation
    logger.debug(f"Tool validation passed for {tool_name}")
    return None  # Allow execution


def after_tool_callback(
    tool: BaseTool,
    args: Dict[str, Any], 
    tool_response: Any,
    **kwargs
) -> None:
    """
    Logs tool results and handles post-execution audit trail.
    
    Args:
        tool: The tool that was executed
        args: Arguments that were passed to the tool
        tool_response: Response returned by the tool
        **kwargs: Additional arguments including tool_context
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
    tool_context = kwargs.get('tool_context')
    agent_name = tool_context.agent_name if tool_context else "unknown"
    
    # Determine if operation was successful based on result
    is_success = True
    if isinstance(tool_response, str):
        is_success = not tool_response.startswith("❌")
    elif isinstance(tool_response, dict):
        is_success = tool_response.get("status") == "success"
    
    if is_success:
        logger.info(
            "Tool execution completed",
            extra={
                "tool_name": tool_name,
                "agent_name": agent_name,
                "success": is_success,
                "args_count": len(args) if args else 0,
                "result_type": type(tool_response).__name__
            }
        )
    else:
        logger.warning(
            "Tool execution completed with issues",
            extra={
                "tool_name": tool_name,
                "agent_name": agent_name,
                "success": is_success,
                "args_count": len(args) if args else 0,
                "result_type": type(tool_response).__name__
            }
        )
    
    # Create audit trail for sensitive operations
    if _is_sensitive_operation(tool_name, args):
        _create_audit_trail(tool_name, args, tool_response, is_success, agent_name)


def rate_limit_callback(
    callback_context,
    llm_request,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Basic rate limiting for model calls to prevent abuse.
    
    Args:
        callback_context: ADK callback context
        llm_request: LLM request object
        **kwargs: Additional arguments
        
    Returns:
        None to allow call, Dict to block with custom response
    """
    current_time = time.time()
    
    # Rate limiting parameters
    MAX_CALLS_PER_MINUTE = 30
    RATE_WINDOW = 60  # seconds
    
    # Reset window if needed
    if current_time - _rate_limit_state['window_start'] > RATE_WINDOW:
        _rate_limit_state['window_start'] = current_time
        _rate_limit_state['call_count'] = 0
    
    # Increment call count
    _rate_limit_state['call_count'] += 1
    _rate_limit_state['last_call'] = current_time
    
    # Check if rate limit exceeded
    if _rate_limit_state['call_count'] > MAX_CALLS_PER_MINUTE:
        user_id = getattr(callback_context, 'user_id', 'unknown')
        session_id = getattr(callback_context, 'session_id', 'unknown')
        
        logger.warning(
            "Rate limit exceeded",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "calls_in_window": _rate_limit_state['call_count']
            }
        )
        
        # Return blocking response
        return {
            "blocked": True,
            "message": "⚠️ Limite de taxa excedido. Muitas solicitações em pouco tempo. Aguarde um momento antes de tentar novamente."
        }
    
    # Log successful rate limit check
    logger.debug(
        f"Rate limit check passed: {_rate_limit_state['call_count']}/{MAX_CALLS_PER_MINUTE} calls"
    )
    return None  # Allow call


def _is_sensitive_operation(tool_name: str, args: Dict[str, Any]) -> bool:
    """Check if the tool operation is considered sensitive."""
    sensitive_tools = {
        "create_issue",
        "add_worklog", 
        "delete_issue",
        "update_issue"
    }
    
    # Check for bulk operations
    if args and any(
        isinstance(v, list) and len(v) > 10 
        for v in args.values()
    ):
        return True
        
    return tool_name in sensitive_tools


def _validate_sensitive_operation(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate sensitive operations based on business rules."""
    
    # Check for bulk operations
    for key, value in args.items():
        if isinstance(value, list) and len(value) > 50:
            return {
                "allowed": False,
                "reason": f"Operação em lote muito grande: {len(value)} itens (máximo 50)"
            }
    
    # Check for empty required fields in create operations
    if tool_name == "create_issue":
        summary = args.get("summary", "").strip()
        if not summary:
            return {
                "allowed": False,
                "reason": "Resumo da issue é obrigatório"
            }
        if len(summary) > 500:
            return {
                "allowed": False, 
                "reason": "Resumo muito longo (máximo 500 caracteres)"
            }
    
    return {"allowed": True, "reason": "Validation passed"}


def _create_audit_trail(
    tool_name: str,
    args: Dict[str, Any],
    result: Any, 
    is_success: bool,
    agent_name: str
) -> None:
    """Create audit trail entry for sensitive operations."""
    audit_entry = {
        "tool_name": tool_name,
        "agent_name": agent_name,
        "success": is_success,
        "timestamp": time.time(),
        "args_summary": _summarize_args(args),
        "result_summary": _summarize_result(result)
    }
    
    logger.info(
        "Audit trail entry created",
        extra=audit_entry
    )


def _summarize_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a safe summary of arguments for audit logging."""
    summary = {}
    for key, value in args.items():
        if isinstance(value, str):
            # Truncate long strings
            summary[key] = value[:100] + "..." if len(value) > 100 else value
        elif isinstance(value, list):
            summary[key] = f"list({len(value)})"
        elif isinstance(value, dict):
            summary[key] = f"dict({len(value)})"
        else:
            summary[key] = str(type(value).__name__)
    return summary


def _summarize_result(result: Any) -> str:
    """Create a safe summary of result for audit logging."""
    if isinstance(result, str):
        return result[:200] + "..." if len(result) > 200 else result
    elif isinstance(result, dict):
        return f"dict with keys: {list(result.keys())}"
    else:
        return str(type(result).__name__)
"""
Utility functions for date parsing and conversion.

This module provides intelligent date parsing that understands various
human-friendly date formats and converts them to Jira API format.
"""

from datetime import datetime, timedelta
import re
from typing import Optional


def parse_date_intelligent(date_input: str) -> str:
    """
    Parse various date formats and return in YYYY-MM-DD format.
    
    Supports formats:
    - "hoje", "today" -> current date
    - "ontem", "yesterday" -> yesterday
    - "amanhã", "tomorrow" -> tomorrow
    - "YYYY-MM-DD" -> as is
    - "DD/MM/YYYY" -> converted
    - "DD-MM-YYYY" -> converted
    - "MM/DD/YYYY" (if day > 12) -> converted
    - Relative: "3 dias atrás", "2 days ago", "1 week ago"
    
    Args:
        date_input: Date string in various formats
        
    Returns:
        str: Date in YYYY-MM-DD format
        
    Raises:
        ValueError: If date format is not recognized
    """
    if not date_input:
        return datetime.now().strftime('%Y-%m-%d')
    
    date_str = date_input.strip().lower()
    today = datetime.now()
    
    # Handle common Portuguese/English keywords
    if date_str in ['hoje', 'today', 'hj']:
        return today.strftime('%Y-%m-%d')
    
    if date_str in ['ontem', 'yesterday']:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if date_str in ['amanhã', 'amanha', 'tomorrow']:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Handle relative dates
    relative_match = re.match(r'(\d+)\s*(dia|day|semana|week|mes|month|ano|year)s?\s*(atrás|atrás|ago|antes)', date_str)
    if relative_match:
        number = int(relative_match.group(1))
        unit = relative_match.group(2)
        
        if unit in ['dia', 'day']:
            target_date = today - timedelta(days=number)
        elif unit in ['semana', 'week']:
            target_date = today - timedelta(weeks=number)
        elif unit in ['mes', 'month']:
            target_date = today - timedelta(days=number * 30)  # Approximation
        elif unit in ['ano', 'year']:
            target_date = today - timedelta(days=number * 365)  # Approximation
        else:
            raise ValueError(f"Unrecognized time unit: {unit}")
        
        return target_date.strftime('%Y-%m-%d')
    
    # Handle already formatted YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        # Validate the date
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValueError(f"Invalid date: {date_str}")
    
    # Handle DD-MM-YYYY and DD/MM/YYYY format (Brazilian standard)
    dd_mm_yyyy = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$', date_str)
    if dd_mm_yyyy:
        day, month, year = dd_mm_yyyy.groups()
        day, month = int(day), int(month)
        
        # Always assume DD/MM format (Brazilian standard)
        # Only swap if day > 12 AND month <= 12 (clear MM/DD case)
        if day > 12 and month <= 12:
            # This is clearly MM/DD format, swap them
            formatted_date = f"{year}-{day:02d}-{month:02d}"
        else:
            # Default to DD/MM format (Brazilian standard)
            formatted_date = f"{year}-{month:02d}-{day:02d}"
        
        # Validate the constructed date
        try:
            datetime.strptime(formatted_date, '%Y-%m-%d')
            return formatted_date
        except ValueError:
            # If DD/MM failed and we haven't tried MM/DD yet, try swapping
            if day <= 12 and month <= 12:
                try:
                    formatted_date = f"{year}-{day:02d}-{month:02d}"
                    datetime.strptime(formatted_date, '%Y-%m-%d')
                    return formatted_date
                except ValueError:
                    pass
            raise ValueError(f"Invalid date: {date_input}")
    
    # Handle YYYY/MM/DD format
    yyyy_mm_dd = re.match(r'^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$', date_str)
    if yyyy_mm_dd:
        year, month, day = yyyy_mm_dd.groups()
        formatted_date = f"{year}-{int(month):02d}-{int(day):02d}"
        
        try:
            datetime.strptime(formatted_date, '%Y-%m-%d')
            return formatted_date
        except ValueError:
            raise ValueError(f"Invalid date: {date_input}")
    
    # Handle partial dates like "15/12" or "15-12" (assume current year, DD-MM format)
    partial_date = re.match(r'^(\d{1,2})[/\-](\d{1,2})$', date_str)
    if partial_date:
        day, month = partial_date.groups()
        current_year = today.year
        day, month = int(day), int(month)
        
        # Use DD-MM format (Brazilian standard)
        formatted_date = f"{current_year}-{month:02d}-{day:02d}"
        
        try:
            datetime.strptime(formatted_date, '%Y-%m-%d')
            return formatted_date
        except ValueError:
            # If DD-MM failed, try MM-DD
            try:
                formatted_date = f"{current_year}-{day:02d}-{month:02d}"
                datetime.strptime(formatted_date, '%Y-%m-%d')
                return formatted_date
            except ValueError:
                raise ValueError(f"Invalid date: {date_input}")
    
    # If no pattern matches, raise error with helpful message
    raise ValueError(
        f"Formato de data não reconhecido: '{date_input}'. "
        "Formatos suportados: 'hoje', 'ontem', 'DD-MM-YYYY', 'DD/MM/YYYY', "
        "'YYYY-MM-DD', '3 dias atrás', etc."
    )


def format_date_for_jira(date_string: str) -> str:
    """
    Format any date string for Jira API consumption.
    
    This is a wrapper around parse_date_intelligent that ensures
    the output is always in the format Jira expects.
    
    Args:
        date_string: Date in any supported format
        
    Returns:
        str: Date in YYYY-MM-DD format for Jira API
    """
    try:
        return parse_date_intelligent(date_string)
    except ValueError as e:
        # Log the error but provide current date as fallback
        from .logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Date parsing failed for '{date_string}': {e}. Using current date.")
        return datetime.now().strftime('%Y-%m-%d')


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime('%Y-%m-%d')


def validate_jira_date_format(date_string: str) -> bool:
    """
    Validate if date string is in proper YYYY-MM-DD format.
    
    Args:
        date_string: Date string to validate
        
    Returns:
        bool: True if valid Jira date format
    """
    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        return False
    except ValueError:
        return False
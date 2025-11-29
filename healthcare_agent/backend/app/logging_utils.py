"""Utilities for secure logging (PII sanitization)."""
import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number for logging (mask all but last 4 digits).
    
    Args:
        phone: Phone number string
        
    Returns:
        Masked phone number (e.g., "+91******0001")
    """
    if not phone or len(phone) < 4:
        return "****"
    
    # Keep country code and last 4 digits, mask the rest
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 4:
        return "****"
    
    # Show first 2 digits (country code) and last 4 digits
    masked = digits[:2] + "*" * (len(digits) - 6) + digits[-4:]
    return f"+{masked}" if phone.startswith("+") else masked


def sanitize_email(email: str) -> str:
    """
    Sanitize email for logging (mask username, show domain).
    
    Args:
        email: Email address string
        
    Returns:
        Masked email (e.g., "u***@example.com")
    """
    if not email or "@" not in email:
        return "****@****"
    
    username, domain = email.split("@", 1)
    if len(username) <= 1:
        masked_username = "*"
    else:
        masked_username = username[0] + "*" * (len(username) - 1)
    
    return f"{masked_username}@{domain}"


def sanitize_dict(data: Dict[str, Any], sensitive_keys: set = None) -> Dict[str, Any]:
    """
    Sanitize dictionary by masking sensitive fields.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: Set of keys to sanitize (default: phone, email, password, token)
        
    Returns:
        Sanitized dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = {"phone", "email", "password", "password_hash", "token", "access_token", "auth_token"}
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive terms
        is_sensitive = any(sensitive_term in key_lower for sensitive_term in sensitive_keys)
        
        if is_sensitive and isinstance(value, str):
            if "phone" in key_lower:
                sanitized[key] = sanitize_phone(value)
            elif "email" in key_lower:
                sanitized[key] = sanitize_email(value)
            else:
                sanitized[key] = "****"  # Generic masking
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, sensitive_keys)
        else:
            sanitized[key] = value
    
    return sanitized


def safe_log_info(message: str, **kwargs):
    """
    Log info message with PII sanitization.
    
    Args:
        message: Log message
        **kwargs: Additional context (will be sanitized)
    """
    if kwargs:
        sanitized_kwargs = sanitize_dict(kwargs)
        logger.info(f"{message} | Context: {sanitized_kwargs}")
    else:
        logger.info(message)


def safe_log_error(message: str, exc_info=None, **kwargs):
    """
    Log error message with PII sanitization.
    
    Args:
        message: Log message
        exc_info: Exception info (for traceback)
        **kwargs: Additional context (will be sanitized)
    """
    if kwargs:
        sanitized_kwargs = sanitize_dict(kwargs)
        logger.error(f"{message} | Context: {sanitized_kwargs}", exc_info=exc_info)
    else:
        logger.error(message, exc_info=exc_info)


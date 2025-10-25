"""Error handling and sanitization"""

import re
from typing import Optional


def sanitize_error_message(message: str) -> str:
    """
    Sanitize error messages to prevent secret leakage.

    Removes:
    - API keys (various formats)
    - Secret values in key=value format
    - URLs with embedded credentials
    """
    # Remove API keys (alphanumeric strings with periods, typically 30+ chars)
    message = re.sub(r"\b[a-zA-Z0-9]{8,}\.[a-zA-Z0-9.]{20,}\b", "***REDACTED***", message)

    # Remove secret values in various formats
    message = re.sub(r'value=["\'].*?["\']', "value=***REDACTED***", message)
    message = re.sub(r'password=["\'].*?["\']', "password=***REDACTED***", message)
    message = re.sub(r'token=["\'].*?["\']', "token=***REDACTED***", message)
    message = re.sub(r'key=["\'].*?["\']', "key=***REDACTED***", message)

    # Remove credentials from URLs
    message = re.sub(r"(https?://)[^:]+:[^@]+@", r"\1***REDACTED***:***REDACTED***@", message)

    return message


class CloudTruthError(Exception):
    """Base exception for CloudTruth MCP Server"""

    def __init__(self, message: str, sanitize: bool = True):
        if sanitize:
            message = sanitize_error_message(message)
        super().__init__(message)
        self.message = message


class ConfigurationError(CloudTruthError):
    """Configuration-related errors"""

    pass


class APIError(CloudTruthError):
    """CloudTruth API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = sanitize_error_message(response_body) if response_body else None


class AuthenticationError(APIError):
    """Authentication failures"""

    pass


class PermissionError(APIError):
    """Permission denied errors"""

    pass


class NotFoundError(APIError):
    """Resource not found errors"""

    pass


class ValidationError(CloudTruthError):
    """Input validation errors"""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded"""

    pass

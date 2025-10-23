"""
WhizoAI SDK Exceptions
"""

from typing import Optional, Any


class WhizoAIError(Exception):
    """Base exception for WhizoAI SDK"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ValidationError(WhizoAIError):
    """Raised when input validation fails"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class AuthenticationError(WhizoAIError):
    """Raised when API key is invalid"""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class InsufficientCreditsError(WhizoAIError):
    """Raised when account has insufficient credits"""

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message, "INSUFFICIENT_CREDITS", 402)


class RateLimitError(WhizoAIError):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR", 429)


class NetworkError(WhizoAIError):
    """Raised when a network error occurs"""

    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message, "NETWORK_ERROR", 0)

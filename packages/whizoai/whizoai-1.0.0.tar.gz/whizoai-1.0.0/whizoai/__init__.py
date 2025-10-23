"""
WhizoAI SDK for Python

Official Python client for the WhizoAI web scraping API.
"""

from .client import WhizoAI
from .exceptions import (
    WhizoAIError,
    ValidationError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    NetworkError,
)

__version__ = "1.0.0"
__all__ = [
    "WhizoAI",
    "WhizoAIError",
    "ValidationError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "NetworkError",
]

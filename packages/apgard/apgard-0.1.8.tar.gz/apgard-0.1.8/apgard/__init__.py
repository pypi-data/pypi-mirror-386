"""
Apgard SDK - Child Safety & Content Moderation for AI Applications

Usage:
    async with ApgardClient("your-api-key") as client:
        # Access moderation
        result = await client.moderation.moderate_message("user123", "Hello")
        
        # Access session / break tracking
        status = await client.breaks.record_activity("user123")
"""

from .client import ApgardClient
from .moderation import ModerationClient, ModerationResult
from .breaks import BreakClient, BreakStatus
from .enums import RiskLevel
from .errors import ApgardError, APIError, ValidationError

__all__ = [
    "ApgardClient",
    "ModerationClient",
    "ModerationResult",
    "BreakClient",
    "BreakStatus",
    "RiskLevel",
    "ApgardError",
    "APIError",
    "ValidationError",
]

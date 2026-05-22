"""
Normalized exception contracts for the provider abstraction.
"""

class ProviderError(Exception):
    """Base exception for all provider errors."""
    pass

class ProviderConnectionError(ProviderError):
    """Raised when the provider is unreachable or times out."""
    pass

class ProviderRateLimitError(ProviderError):
    """Raised when the provider rate limits the request."""
    pass

class ProviderAuthenticationError(ProviderError):
    """Raised when API keys or credentials are invalid."""
    pass

class ProviderStreamingError(ProviderError):
    """Raised when an error occurs mid-stream."""
    pass

"""
Custom exceptions for DOP1 package.
"""


class DOPError(Exception):
    """Base exception class for DOP1 package."""
    pass


class ValidationError(DOPError):
    """Raised when data validation fails."""
    pass


class APIError(DOPError):
    """Raised when API calls fail."""
    pass


class ConfigurationError(DOPError):
    """Raised when configuration is invalid."""
    pass


class FileError(DOPError):
    """Raised when file operations fail."""
    pass

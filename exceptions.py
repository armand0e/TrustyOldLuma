"""
Custom exceptions for the Gaming Setup Tool.

This module defines custom exception classes for different types of errors
that can occur during the setup process.
"""


class GamingSetupError(Exception):
    """Base exception for all gaming setup tool errors."""
    pass


# Critical errors
class AdminPrivilegeError(GamingSetupError):
    """Raised when administrator privileges are required but not available."""
    pass


class CriticalSetupError(GamingSetupError):
    """Raised when a critical error occurs that prevents setup from continuing."""
    pass


# Recoverable errors
class FileOperationError(GamingSetupError):
    """Raised when file operations fail."""
    pass


class ConfigurationError(GamingSetupError):
    """Raised when configuration operations fail."""
    pass


class SecurityConfigError(GamingSetupError):
    """Raised when security configuration operations fail."""
    pass


class ValidationError(GamingSetupError):
    """Raised when validation of data or configuration fails."""
    pass


# Network errors
class NetworkError(GamingSetupError):
    """Raised when network operations fail."""
    pass


class DownloadError(NetworkError):
    """Raised when file download operations fail."""
    pass


class ConnectionTimeoutError(NetworkError):
    """Raised when a network connection times out."""
    pass


# Platform-specific errors
class PlatformNotSupportedError(GamingSetupError):
    """Raised when an operation is not supported on the current platform."""
    pass


class WindowsSpecificError(GamingSetupError):
    """Raised when a Windows-specific operation fails."""
    pass
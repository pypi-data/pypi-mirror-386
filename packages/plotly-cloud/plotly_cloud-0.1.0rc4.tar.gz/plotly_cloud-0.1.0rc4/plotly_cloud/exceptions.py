"""Custom exceptions for Plotly Cloud CLI."""

from typing import Optional


class PlotlyCloudError(Exception):
    """Base exception for all Plotly Cloud CLI errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize exception with message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class AuthenticationError(PlotlyCloudError):
    """Raised when authentication fails."""

    pass


class ConfigurationError(PlotlyCloudError):
    """Raised when configuration is invalid or missing."""

    pass


class DeploymentError(PlotlyCloudError):
    """Raised when deployment operations fail."""

    pass


class ApplicationError(PlotlyCloudError):
    """Raised when application operations fail."""

    pass


# Authentication-specific exceptions
class OAuthClientError(AuthenticationError):
    """Raised when OAuth client operations fail."""

    pass


class TokenError(AuthenticationError):
    """Raised when token operations fail."""

    pass


class CredentialError(AuthenticationError):
    """Raised when credential operations fail."""

    pass


class ForbiddenError(AuthenticationError):
    """Raised when access is forbidden (HTTP 403)."""

    pass


# Configuration-specific exceptions
class CloudConfigError(ConfigurationError):
    """Raised when cloud configuration operations fail."""

    pass


class EnvironmentError(ConfigurationError):
    """Raised when environment configuration is invalid."""

    pass


# Deployment-specific exceptions
class DependencyValidationError(DeploymentError):
    """Raised when dependency validation fails."""

    pass


class PackagingError(DeploymentError):
    """Raised when packaging operations fail."""

    pass


class UploadError(DeploymentError):
    """Raised when upload operations fail."""

    pass


class AppCreationError(DeploymentError):
    """Raised when app creation fails."""

    pass


class AppPublishError(DeploymentError):
    """Raised when app publishing fails."""

    pass


class DeploymentClientError(DeploymentError):
    """Raised when deployment client operations fail."""

    pass


# Application-specific exceptions
class ModuleImportError(ApplicationError):
    """Raised when module import fails."""

    pass


class DashAppError(ApplicationError):
    """Raised when Dash app operations fail."""

    pass


class ServerError(ApplicationError):
    """Raised when server operations fail."""

    pass


# Network-specific exceptions
class APIError(PlotlyCloudError):
    """Raised when API operations fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[str] = None,
    ):
        """Initialize API error with optional status code."""
        super().__init__(message, details)
        self.status_code = status_code

    def __str__(self) -> str:
        """Return formatted error message with status code."""
        msg = self.message
        if self.status_code:
            msg = f"{msg} (HTTP {self.status_code})"
        if self.details:
            msg = f"{msg}: {self.details}"
        return msg


class NetworkError(PlotlyCloudError):
    """Raised when network operations fail."""

    pass


class TimeoutError(PlotlyCloudError):
    """Raised when operations timeout."""

    pass


# File system exceptions
class FileSystemError(PlotlyCloudError):
    """Raised when file system operations fail."""

    pass


class FileNotFoundError(FileSystemError):
    """Raised when required files are not found."""

    pass


class FilePermissionError(FileSystemError):
    """Raised when file permission operations fail."""

    pass


class FileSizeError(FileSystemError):
    """Raised when file size limits are exceeded."""

    pass

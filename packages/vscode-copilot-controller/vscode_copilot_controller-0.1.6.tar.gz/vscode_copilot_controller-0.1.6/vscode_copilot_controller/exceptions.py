"""Custom exceptions for VSCode Copilot Controller package."""


class CopilotControlError(Exception):
    """Base exception for all Copilot control-related errors."""
    pass


class DetectionError(CopilotControlError):
    """Raised when Copilot UI element detection fails."""
    pass


class ConfigurationError(CopilotControlError):
    """Raised when Copilot controller configuration is invalid."""
    pass


class ImageProcessingError(CopilotControlError):
    """Raised when image processing fails."""
    pass


class AutomationError(CopilotControlError):
    """Raised when automation actions (clicking, typing) fail."""
    pass


class PatternMatchError(DetectionError):
    """Raised when pattern matching fails for expected Copilot UI elements."""
    pass


class TimeoutError(CopilotControlError):
    """Raised when operations timeout (e.g., waiting for Copilot to respond)."""
    pass
"""UI element detectors for VSCode Copilot interface."""

from .base import BaseDetector, DetectionResult
from .button_detector import ButtonDetector
from .input_detector import InputDetector
from .status_detector import StatusDetector

__all__ = [
    "BaseDetector",
    "DetectionResult", 
    "ButtonDetector",
    "InputDetector",
    "StatusDetector"
]
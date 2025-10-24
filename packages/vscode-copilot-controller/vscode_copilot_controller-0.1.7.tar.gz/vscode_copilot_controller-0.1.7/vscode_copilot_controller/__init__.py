"""VSCode Copilot Controller - Programmatic control for VSCode Copilot chat panel.

A specialized automation library for controlling VSCode Copilot chat interface.
Uses OCR-based detection to identify and interact with Copilot chat elements
like buttons, inputs, and status indicators.

Key Features:
- Automated clicking of Keep/Undo buttons in Copilot chat
- Detection of chat input areas and send buttons  
- Status monitoring (Working, Ready, etc.)
- Screen area configuration for precise targeting
- High contrast theme optimized detection
"""

from .engine import CopilotController
from .config import CopilotConfig
from .exceptions import CopilotControlError, DetectionError, ConfigurationError
from .utils import ScreenAreaSelector, InteractiveGuide, AreaConfig, AreaConfigManager

__version__ = "0.1.7"
__author__ = "AutoOcto Team"
__description__ = "Programmatically control VSCode Copilot chat panel using OCR-based UI automation"

__all__ = [
    "CopilotController",
    "CopilotConfig", 
    "CopilotControlError",
    "DetectionError",
    "ConfigurationError", 
    "ScreenAreaSelector",
    "InteractiveGuide",
    "AreaConfig",
    "AreaConfigManager"
]
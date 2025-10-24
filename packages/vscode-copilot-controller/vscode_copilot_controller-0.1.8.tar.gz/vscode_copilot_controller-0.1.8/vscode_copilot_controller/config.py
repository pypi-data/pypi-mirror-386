"""Configuration management for VSCode Copilot Controller."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path

from vscode_copilot_controller.utils.area_config import AreaConfigManager

from .exceptions import ConfigurationError


@dataclass
class CopilotConfig:
    """Configuration for Copilot chat automation settings."""

    # Tesseract configuration
    tesseract_path: Optional[str] = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    psm_mode: int = 6  # Page segmentation mode

    # Confidence thresholds
    high_confidence_threshold: int = 80
    medium_confidence_threshold: int = 50
    low_confidence_threshold: int = 30

    # Pattern matching settings
    fuzzy_match_threshold: float = 0.6
    sequential_order_tolerance: int = 50  # pixels

    # Click timing settings
    click_delay: float = 0.5  # seconds between clicks
    type_delay: float = 0.05  # seconds between keystrokes
    wait_after_click: float = 1.0  # seconds to wait after clicking

    # Screenshot settings
    default_screenshot_region: Optional[Dict[str, int]] = None  # {x, y, width, height}
    
    # Copilot UI regions (x, y, width, height)
    set_mode_button_region: tuple = (320, 220, 120, 30)
    pick_model_button_region: tuple = (450, 220, 120, 30)
    send_button_region: tuple = (730, 805, 60, 30)
    set_mode_dropdown_region: tuple = (320, 180, 150, 120)
    pick_model_dropdown_region: tuple = (450, 180, 200, 200)
    chat_input_region: tuple = (320, 800, 400, 40)
    chat_display_region: tuple = (320, 260, 450, 400)
    interactive_buttons_region: tuple = (320, 700, 300, 50)
    keep_button_region: tuple = (350, 710, 80, 35)
    
    # Copilot-specific detection settings
    copilot_detection_settings: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'set_mode': {
            'patterns': ['Agent', 'Ask', 'Edit'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'pick_model': {
            'patterns': ['GPT-4.1', 'GPT-4o', 'GPT-5 mini', 'Claude Sonnet 3.5', 'Claude Sonnet 3.7', 'Claude Sonnet 4', 'GPT-5'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'interactive_buttons': {
            'patterns': ['Continue', 'Allow', 'Enter', 'Yes'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'chat_status': {
            'patterns': ['Send', 'Cancel'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'keep_undo': {
            'patterns': ['Keep', 'Undo'],
            'min_confidence': 50,
            'require_sequential': False,
            'coordinates_hint': {'Keep': [757, 1602], 'Undo': [869, 1598]}
        },
        'send': {
            'patterns': ['Send'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'chat_input': {
            'patterns': ['Ask Copilot', 'Type your question', '@'],
            'min_confidence': 40,
            'require_sequential': False
        },
        'working_status': {
            'patterns': ['Working', 'Generating', 'Thinking'],
            'min_confidence': 50,
            'require_sequential': False
        },
        'chat_display_bottom_text': {
            'patterns': ['GPT-4.1', 'GPT-4o', 'GPT-5 mini', 'Claude Sonnet 3.5', 'Claude Sonnet 3.7', 'Claude Sonnet 4', 'GPT-5'],
            'min_confidence': 50,
            'require_sequential': False
        }
    })

    def __post_init__(self):
        """Load area configurations from AreaConfigManager after dataclass initialization."""
        area_manager = AreaConfigManager()
        if not area_manager.config_file.exists():
            print("⚠️  Area configuration file not found. Please run the area configuration setup.")
        else:
            area_manager.load_config()
            for area_name, area in area_manager.areas.items():
                try:
                    # Area names in JSON already have _region suffix, so use them directly
                    setattr(self, area_name, area.bbox)
                    print(f"✅ Loaded {area_name}: {area.bbox}")
                except Exception as e:
                    print(f"⚠️  Failed to set area {area_name}: {e}")
        
        self.validate()

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.tesseract_path and not Path(self.tesseract_path).exists():
            raise ConfigurationError(f"Tesseract executable not found: {self.tesseract_path}")

        if not 0 <= self.psm_mode <= 13:
            raise ConfigurationError(f"Invalid PSM mode: {self.psm_mode}. Must be 0-13.")

        if not 0 <= self.fuzzy_match_threshold <= 1:
            raise ConfigurationError(f"Invalid fuzzy match threshold: {self.fuzzy_match_threshold}. Must be 0-1.")

        # Validate confidence thresholds
        thresholds = [
            self.high_confidence_threshold,
            self.medium_confidence_threshold,
            self.low_confidence_threshold
        ]

        if not all(0 <= t <= 100 for t in thresholds):
            raise ConfigurationError("Confidence thresholds must be between 0-100")

        if not (self.low_confidence_threshold <= self.medium_confidence_threshold <= self.high_confidence_threshold):
            raise ConfigurationError("Confidence thresholds must be ordered: low <= medium <= high")

        # Validate timing settings
        if self.click_delay < 0:
            raise ConfigurationError("Click delay must be non-negative")
        if self.type_delay < 0:
            raise ConfigurationError("Type delay must be non-negative")
        if self.wait_after_click < 0:
            raise ConfigurationError("Wait after click must be non-negative")

    def get_detection_config(self, element_type: str) -> Dict[str, Any]:
        """Get configuration for specific Copilot element type."""
        if element_type not in self.copilot_detection_settings:
            available = list(self.copilot_detection_settings.keys())
            raise ConfigurationError(f"Unknown element type: {element_type}. Available: {available}")
        return self.copilot_detection_settings[element_type]

    def set_screenshot_region(self, x: int, y: int, width: int, height: int) -> None:
        """Set default screenshot region for Copilot area."""
        self.default_screenshot_region = {
            'x': x, 'y': y, 'width': width, 'height': height
        }

    def get_screenshot_region(self) -> Optional[tuple]:
        """Get screenshot region as tuple (x, y, width, height)."""
        if self.default_screenshot_region:
            region = self.default_screenshot_region
            return (region['x'], region['y'], region['width'], region['height'])
        return None
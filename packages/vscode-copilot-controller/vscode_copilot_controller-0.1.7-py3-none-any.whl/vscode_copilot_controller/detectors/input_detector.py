"""Input detector for Copilot chat input fields."""

from typing import List, Dict, Any, TYPE_CHECKING
import logging

from .base import BaseDetector, DetectionResult

if TYPE_CHECKING:
    from ..config import CopilotConfig


class InputDetector(BaseDetector):
    """Detector for Copilot chat input fields."""

    def __init__(self, config: 'CopilotConfig', input_type: str) -> None:
        super().__init__(config, input_type)
        self.input_config = config.get_detection_config(input_type)
        self.logger = logging.getLogger(__name__)

    def get_expected_patterns(self) -> List[str]:
        """Get expected patterns for input detection."""
        return self.input_config['patterns']

    def detect(self, ocr_elements: List[Dict[str, Any]], **kwargs) -> DetectionResult:
        """Detect input field elements in OCR data."""
        patterns = self.get_expected_patterns()
        
        self.logger.info(f"Detecting {self.element_type} input with patterns: {patterns}")

        # Find pattern matches
        matches = self._find_pattern_matches(ocr_elements, patterns, self.input_config)
        
        # Create and return result
        result = self._create_result(matches, patterns, self.input_config)
        
        self.logger.info(f"Input detection result: {result.success}, found patterns: {result.patterns_found}")
        
        return result
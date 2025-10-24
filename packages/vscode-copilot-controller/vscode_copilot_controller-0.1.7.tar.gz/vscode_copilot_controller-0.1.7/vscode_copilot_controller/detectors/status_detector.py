"""Status detector for Copilot working status."""

from typing import List, Dict, Any, TYPE_CHECKING
import logging

from .base import BaseDetector, DetectionResult

if TYPE_CHECKING:
    from ..config import CopilotConfig


class StatusDetector(BaseDetector):
    """Detector for Copilot status indicators."""

    def __init__(self, config: 'CopilotConfig', status_type: str) -> None:
        super().__init__(config, status_type)
        self.status_config = config.get_detection_config(status_type)
        self.logger = logging.getLogger(__name__)

    def get_expected_patterns(self) -> List[str]:
        """Get expected patterns for status detection."""
        return self.status_config['patterns']

    def detect(self, ocr_elements: List[Dict[str, Any]], **kwargs) -> DetectionResult:
        """Detect status indicator elements in OCR data."""
        patterns = self.get_expected_patterns()
        
        self.logger.info(f"Detecting {self.element_type} status with patterns: {patterns}")

        # Find pattern matches
        matches = self._find_pattern_matches(ocr_elements, patterns, self.status_config)
        
        # Create and return result
        result = self._create_result(matches, patterns, self.status_config)
        
        self.logger.info(f"Status detection result: {result.success}, found patterns: {result.patterns_found}")
        
        return result
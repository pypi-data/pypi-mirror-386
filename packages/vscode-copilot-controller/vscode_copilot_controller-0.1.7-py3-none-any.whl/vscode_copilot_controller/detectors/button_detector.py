"""Button detector for Copilot chat buttons."""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging

from .base import BaseDetector, DetectionResult

if TYPE_CHECKING:
    from ..config import CopilotConfig


class ButtonDetector(BaseDetector):
    """Detector for Copilot chat buttons (Keep/Undo, Allow, Send)."""

    def __init__(self, config: 'CopilotConfig', button_type: str) -> None:
        super().__init__(config, button_type)
        self.button_config = config.get_detection_config(button_type)
        self.logger = logging.getLogger(__name__)

    def get_expected_patterns(self) -> List[str]:
        """Get expected patterns for this button type."""
        return self.button_config['patterns']

    def detect(self, ocr_elements: List[Dict[str, Any]], **kwargs) -> DetectionResult:
        """Detect button elements in OCR data."""
        patterns = self.get_expected_patterns()
        
        self.logger.info(f"Detecting {self.element_type} button with patterns: {patterns}")

        # Find pattern matches
        matches = self._find_pattern_matches(ocr_elements, patterns, self.button_config)
        
        # Create and return result
        result = self._create_result(matches, patterns, self.button_config)
        
        self.logger.info(f"Detection result: {result.success}, found patterns: {result.patterns_found}")
        
        return result

    def _find_pattern_matches(self, ocr_elements: List[Dict[str, Any]], patterns: List[str], 
                             element_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find OCR elements that match button patterns."""
        matches = []
        
        for pattern in patterns:
            for element in ocr_elements:
                text = element['text']
                confidence = element['confidence']
                
                # Check confidence threshold
                if not self._is_valid_confidence(confidence, element_config):
                    continue
                
                # For buttons, be more flexible with matching
                if self._is_button_match(pattern, text):
                    matches.append({
                        'pattern': pattern,
                        'element': element,
                        'match_type': self._get_match_type(pattern, text)
                    })
        
        return matches

    def _is_button_match(self, pattern: str, text: str) -> bool:
        """Check if text matches button pattern."""
        pattern_lower = pattern.lower()
        text_lower = text.lower()
        
        # Exact match
        if pattern_lower == text_lower:
            return True
        
        # Contains match (pattern in text or text in pattern)
        if pattern_lower in text_lower or text_lower in pattern_lower:
            return True
        
        # Special handling for common button variations
        button_variations = {
            'keep': ['keep', 'keap', 'kep'],
            'undo': ['undo', 'undu', 'undoo'],
            'allow': ['allow', 'alow', 'allov'],
            'send': ['send', 'sent', 'submit'],
        }
        
        for base_text, variations in button_variations.items():
            if base_text in pattern_lower:
                for variation in variations:
                    if variation in text_lower:
                        return True
        
        # Fall back to fuzzy matching
        return self._fuzzy_match(pattern, text)

    def _get_match_type(self, pattern: str, text: str) -> str:
        """Determine the type of match found."""
        pattern_lower = pattern.lower()
        text_lower = text.lower()
        
        if pattern_lower == text_lower:
            return 'exact'
        elif pattern_lower in text_lower or text_lower in pattern_lower:
            return 'contains'
        else:
            return 'fuzzy'
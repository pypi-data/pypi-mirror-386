"""Base detector class for Copilot UI element detection."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from PIL import Image

from ..exceptions import DetectionError

if TYPE_CHECKING:
    from ..config import CopilotConfig


@dataclass
class DetectionResult:
    """Result of Copilot UI element detection."""
    element_type: str
    patterns_found: List[str]
    patterns_missing: List[str]
    detected_elements: List[Dict[str, Any]]
    confidence_score: float
    success: bool
    coordinates: Optional[List[Tuple[int, int]]] = None
    additional_info: Optional[Dict[str, Any]] = None


class BaseDetector(ABC):
    """Abstract base class for Copilot UI element detectors."""

    def __init__(self, config: 'CopilotConfig', element_type: str) -> None:
        self.config = config
        self.element_type = element_type
        self.last_detection_result: Optional[DetectionResult] = None

    @abstractmethod
    def detect(self, ocr_elements: List[Dict[str, Any]], **kwargs) -> DetectionResult:
        """Detect UI elements in OCR data.

        Args:
            ocr_elements: List of OCR detected elements with text, confidence, and coordinates
            **kwargs: Additional detection parameters

        Returns:
            DetectionResult with success status and detected elements
        """
        pass

    @abstractmethod
    def get_expected_patterns(self) -> List[str]:
        """Get list of expected text patterns for this detector."""
        pass

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Check for fuzzy text matching to handle OCR errors."""
        import re

        # Remove special characters and spaces for comparison
        pattern_clean = re.sub(r'[^\w]', '', pattern.lower())
        text_clean = re.sub(r'[^\w]', '', text.lower())

        # Direct match
        if pattern_clean == text_clean:
            return True

        # Check if either contains the other (partial match)
        if len(pattern_clean) >= 3 and len(text_clean) >= 3:
            if pattern_clean in text_clean or text_clean in pattern_clean:
                return True

        # Check for character similarity (simple Levenshtein-like)
        if len(pattern_clean) > 0 and len(text_clean) > 0:
            similarity = len(set(pattern_clean) & set(text_clean)) / max(len(set(pattern_clean)), len(set(text_clean)))
            return similarity > self.config.fuzzy_match_threshold

        return False

    def _is_valid_confidence(self, confidence: float, element_config: Dict[str, Any]) -> bool:
        """Check if OCR confidence meets threshold."""
        min_confidence = element_config.get('min_confidence', self.config.medium_confidence_threshold)
        return confidence >= min_confidence

    def _find_pattern_matches(self, ocr_elements: List[Dict[str, Any]], patterns: List[str], 
                             element_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find OCR elements that match expected patterns."""
        matches = []
        
        for pattern in patterns:
            for element in ocr_elements:
                text = element['text']
                confidence = element['confidence']
                
                # Check confidence threshold
                if not self._is_valid_confidence(confidence, element_config):
                    continue
                
                # Check for exact or fuzzy match
                if (text.lower() == pattern.lower() or 
                    pattern.lower() in text.lower() or
                    self._fuzzy_match(pattern, text)):
                    
                    matches.append({
                        'pattern': pattern,
                        'element': element,
                        'match_type': 'exact' if text.lower() == pattern.lower() else 'fuzzy'
                    })
        
        return matches

    def _calculate_confidence_score(self, matches: List[Dict[str, Any]], total_patterns: int) -> float:
        """Calculate overall confidence score for detection."""
        if not matches or total_patterns == 0:
            return 0.0
        
        # Base score from pattern coverage
        pattern_coverage = len(set(match['pattern'] for match in matches)) / total_patterns
        
        # Average OCR confidence of matched elements
        avg_ocr_confidence = sum(match['element']['confidence'] for match in matches) / len(matches)
        
        # Combine scores (pattern coverage weighted more heavily)
        confidence_score = (pattern_coverage * 0.7 + (avg_ocr_confidence / 100) * 0.3) * 100
        
        return min(confidence_score, 100.0)

    def _create_result(self, matches: List[Dict[str, Any]], expected_patterns: List[str], 
                      element_config: Dict[str, Any]) -> DetectionResult:
        """Create detection result from matches."""
        patterns_found = list(set(match['pattern'] for match in matches))
        patterns_missing = [p for p in expected_patterns if p not in patterns_found]
        
        detected_elements = [match['element'] for match in matches]
        confidence_score = self._calculate_confidence_score(matches, len(expected_patterns))
        
        # Determine success based on required patterns
        min_patterns_required = element_config.get('min_patterns_required', 1)
        success = len(patterns_found) >= min_patterns_required
        
        # Extract coordinates
        coordinates: Optional[List[Tuple[int, int]]] = [tuple(elem['center']) for elem in detected_elements] if detected_elements else None
        
        result = DetectionResult(
            element_type=self.element_type,
            patterns_found=patterns_found,
            patterns_missing=patterns_missing,
            detected_elements=detected_elements,
            confidence_score=confidence_score,
            success=success,
            coordinates=coordinates,
            additional_info={
                'total_matches': len(matches),
                'element_config': element_config
            }
        )
        
        self.last_detection_result = result
        return result
"""VSCode Copilot Controller - Main control engine for Copilot chat interface."""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from PIL import Image
import pytesseract
import pyautogui
import time

from .config import CopilotConfig
from .detectors import ButtonDetector, InputDetector, StatusDetector
from .detectors.base import DetectionResult
from .exceptions import CopilotControlError, ImageProcessingError, ConfigurationError


class CopilotController:
    """Main controller for VSCode Copilot chat interface automation."""

    def __init__(self, config: Optional[CopilotConfig] = None):
        """Initialize Copilot controller with configuration.

        Args:
            config: Copilot configuration. If None, uses default configuration.
        """
        self.config = config or CopilotConfig()
        self.config.validate()

        # Set up tesseract
        if self.config.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize detectors
        self._detectors: Dict[str, Union[ButtonDetector, InputDetector, StatusDetector]] = {}
        self._setup_detectors()

    def _setup_detectors(self) -> None:
        """Set up specialized detectors for Copilot UI elements."""
        # Button detectors for Copilot chat
        self._detectors['keep_undo'] = ButtonDetector(self.config, 'keep_undo')
        self._detectors['interactive_buttons'] = ButtonDetector(self.config, 'interactive_buttons')
        self._detectors['send'] = ButtonDetector(self.config, 'send')
        self._detectors['set_mode'] = ButtonDetector(self.config, 'set_mode')
        self._detectors['pick_model'] = ButtonDetector(self.config, 'pick_model')

        # Input detectors
        self._detectors['chat_input'] = InputDetector(self.config, 'chat_input')

        # Status detectors
        self._detectors['chat_status'] = StatusDetector(self.config, 'chat_status')
        self._detectors['working_status'] = StatusDetector(self.config, 'working_status')
        self._detectors['chat_display_bottom_text'] = StatusDetector(self.config, 'chat_display_bottom_text')

    def take_copilot_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """Take screenshot of Copilot chat area.
        
        Args:
            region: Specific region (x, y, width, height). If None, captures right quarter of screen.
            
        Returns:
            PIL Image of the captured area
        """
        if region is None:
            # Default to right quarter of screen where Copilot typically appears
            screen_size = pyautogui.size()
            region = (
                screen_size.width * 3 // 4,  # Right quarter
                0,
                screen_size.width // 4,
                screen_size.height
            )
        
        screenshot = pyautogui.screenshot(region=region)
        self.logger.info(f"Captured Copilot area screenshot: {region}")
        return screenshot

    def extract_ocr_data(self, image: Union[str, Path, Image.Image]) -> List[Dict[str, Any]]:
        """Extract OCR data from image using tesseract.

        Args:
            image: Path to image file or PIL Image object

        Returns:
            List of OCR elements with text, confidence, and coordinates

        Raises:
            ImageProcessingError: If image processing fails
        """
        try:
            # Load image if path provided
            if isinstance(image, (str, Path)):
                img = Image.open(image)
                self.logger.info(f"Loaded image: {image}")
            else:
                img = image

            # Preprocess image: remove blue borders, convert to grayscale, optionally upscale and autocontrast
            try:
                from PIL import ImageOps

                # First, convert blue pixels to black if present
                proc_img = self._convert_blue_to_black(img)

                # Convert to grayscale (L mode)
                proc_img = proc_img.convert('L')

                # Upscale slightly to help OCR on small UI text
                # scale = 1.5
                # try:
                #     new_size = (int(proc_img.width * scale), int(proc_img.height * scale))
                #     proc_img = proc_img.resize(new_size, Image.BILINEAR)
                # except Exception:
                #     # If resizing fails, continue with original
                #     pass

                # Improve contrast automatically
                proc_img = ImageOps.autocontrast(proc_img)
            except Exception:
                # If any preprocessing step fails, fall back to original image
                proc_img = img

            # Perform OCR using configured PSM
            self.logger.info(f"Performing OCR with PSM {self.config.psm_mode}")
            data = pytesseract.image_to_data(
                proc_img,
                config=f'--psm {self.config.psm_mode}',
                output_type=pytesseract.Output.DICT
            )

            # Extract elements
            elements = []
            for i, text in enumerate(data.get('text', [])):
                if text.strip():  # Only non-empty text
                    conf = data['conf'][i]
                    left = data['left'][i]
                    top = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]

                    element = {
                        'text': text.strip(),
                        'confidence': conf,
                        'bbox': [left, top, width, height],
                        'center': [left + width//2, top + height//2]
                    }
                    elements.append(element)

            self.logger.info(f"Extracted {len(elements)} OCR elements")
            return elements

        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {e}") from e

    def click_keep_button(self, screenshot: Optional[Image.Image] = None) -> bool:
        """Automatically detect and click the Keep button in Copilot chat.
        
        Args:
            screenshot: Optional screenshot to use. If None, takes region screenshot.
            
        Returns:
            True if Keep button was found and clicked, False otherwise
        """
        try:
            # Take screenshot of keep button region (same as check_keep_button)
            if screenshot is None:
                screenshot = self._take_region_screenshot(self.config.keep_button_region)
                if not screenshot:
                    print("❌ Failed to capture Keep button region")
                    return False
            
            # Extract text from region and find Keep button
            ocr_data = self.extract_ocr_data(screenshot)
            
            for element in ocr_data:
                if 'KEEP' in element['text'].upper():
                    # Calculate absolute coordinates from region-relative coordinates
                    region_x, region_y, region_width, _ = self.config.keep_button_region
                    abs_x = region_x + region_width // 3
                    abs_y = region_y + element['center'][1]
                    
                    print(f"🎯 Clicking Keep button at ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y)
                    return True
            
            print("❌ Keep button not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to click Keep button: {e}")
            return False

    def click_undo_button(self, screenshot: Optional[Image.Image] = None) -> bool:
        """Automatically detect and click the Undo button in Copilot chat.
        
        Args:
            screenshot: Optional screenshot to use. If None, takes new screenshot.
            
        Returns:
            True if Undo button was found and clicked, False otherwise
        """
        try:
            if screenshot is None:
                screenshot = self.take_copilot_screenshot()
            
            # Detect Undo button
            result = self.detect_keep_undo_buttons(screenshot)
            
            if result.success and 'Undo' in result.patterns_found:
                # Find Undo button coordinates
                for element in result.detected_elements:
                    if 'undo' in element['text'].lower():
                        x, y = element['center']
                        self.logger.info(f"Clicking Undo button at ({x}, {y})")
                        pyautogui.click(x, y)
                        return True
            
            self.logger.warning("Undo button not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to click Undo button: {e}")
            return False

    def wait_for_copilot_ready(self, timeout: float = 30.0, check_interval: float = 1.0) -> bool:
        """Wait for Copilot to finish working and become ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            check_interval: How often to check status in seconds
            
        Returns:
            True if Copilot became ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            screenshot = self.take_copilot_screenshot()
            status_result = self.detect_working_status(screenshot)
            
            if status_result.success:
                if 'Working' not in status_result.patterns_found:
                    self.logger.info("Copilot is ready")
                    return True
                else:
                    self.logger.info("Copilot is still working...")
            
            time.sleep(check_interval)
        
        self.logger.warning(f"Timeout waiting for Copilot to become ready after {timeout}s")
        return False

    def send_message_to_copilot(self, message: str, wait_for_response: bool = True) -> bool:
        """Send a message to Copilot chat.
        
        Args:
            message: Message text to send
            wait_for_response: Whether to wait for Copilot to finish processing
            
        Returns:
            True if message was sent successfully
        """
        try:
            # First, click on chat input area
            screenshot = self.take_copilot_screenshot()
            input_result = self.detect_chat_input(screenshot)
            
            if input_result.success and input_result.detected_elements:
                input_element = input_result.detected_elements[0]
                x, y = input_element['center']
                
                # Click on input area
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                # Type the message
                pyautogui.typewrite(message)
                
                # Send the message (usually Enter key)
                pyautogui.press('enter')
                
                self.logger.info(f"Sent message to Copilot: {message[:50]}...")
                
                if wait_for_response:
                    return self.wait_for_copilot_ready()
                
                return True
            else:
                self.logger.error("Could not find chat input area")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message to Copilot: {e}")
            return False

    def detect_keep_undo_buttons(self, image: Union[str, Path, Image.Image]) -> DetectionResult:
        """Detect Keep and Undo buttons in Copilot chat."""
        ocr_elements = self.extract_ocr_data(image)
        return self._detectors['keep_undo'].detect(ocr_elements)

    def detect_send_button(self, image: Union[str, Path, Image.Image]) -> DetectionResult:
        """Detect Send button in Copilot chat."""
        ocr_elements = self.extract_ocr_data(image)
        return self._detectors['send'].detect(ocr_elements)

    def detect_chat_input(self, image: Union[str, Path, Image.Image]) -> DetectionResult:
        """Detect chat input field."""
        ocr_elements = self.extract_ocr_data(image)
        return self._detectors['chat_input'].detect(ocr_elements)

    def detect_working_status(self, image: Union[str, Path, Image.Image]) -> DetectionResult:
        """Detect if Copilot is working/processing."""
        ocr_elements = self.extract_ocr_data(image)
        return self._detectors['working_status'].detect(ocr_elements)

    def get_copilot_status(self) -> Dict[str, Any]:
        """Get current status of Copilot interface.
        
        Returns:
            Dictionary with current status information
        """
        try:
            screenshot = self.take_copilot_screenshot()
            
            # Run all detections
            results = {
                'keep_undo': self.detect_keep_undo_buttons(screenshot),
                'send': self.detect_send_button(screenshot),
                'chat_input': self.detect_chat_input(screenshot),
                'working_status': self.detect_working_status(screenshot)
            }
            
            # Compile status
            status = {
                'timestamp': time.time(),
                'available_actions': [],
                'is_working': False,
                'has_input': False,
                'has_send': False,
                'detected_elements': {}
            }
            
            for result_type, result in results.items():
                status['detected_elements'][result_type] = {
                    'success': result.success,
                    'patterns_found': result.patterns_found,
                    'confidence': result.confidence_score
                }
                
                if result.success:
                    if result_type == 'keep_undo':
                        if 'Keep' in result.patterns_found:
                            status['available_actions'].append('keep')
                        if 'Undo' in result.patterns_found:
                            status['available_actions'].append('undo')
                    elif result_type == 'send':
                        status['has_send'] = True
                        status['available_actions'].append('send')
                    elif result_type == 'chat_input':
                        status['has_input'] = True
                    elif result_type == 'working_status':
                        if 'Working' in result.patterns_found:
                            status['is_working'] = True
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get Copilot status: {e}")
            return {'error': str(e), 'timestamp': time.time()}

    # ============================================================================
    # COMPREHENSIVE COPILOT AUTOMATION METHODS (UPDATED)
    # ============================================================================

    def click_set_mode_button(self) -> bool:
        """Click the Set Mode button to trigger dropdown.
        
        Returns:
            bool: True if Set Mode button was found and clicked
        """
        print("🎯 Clicking Set Mode button...")
        
        try:
            # Take screenshot of the set mode button region
            screenshot = self._take_region_screenshot(self.config.set_mode_button_region)
            if not screenshot:
                print("❌ Failed to capture Set Mode button region")
                return False
            
            # Extract text from region
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for set mode button patterns
            for element in ocr_data:
                text_upper = element['text'].upper()
                if any(keyword in text_upper for keyword in ['MODE', 'SET', 'AGENT', 'ASK', 'EDIT']):
                    # Calculate absolute coordinates
                    abs_x = self.config.set_mode_button_region[0] + self.config.set_mode_button_region[2] // 3
                    abs_y = self.config.set_mode_button_region[1] + element['center'][1]
                    
                    print(f"✅ Found Set Mode button at ({abs_x}, {abs_y})")
                    print(f"   Text: {element['text']}")
                    
                    # Click the button
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            
            # Fallback: click center of region
            center_x = self.config.set_mode_button_region[0] + self.config.set_mode_button_region[2] // 2
            center_y = self.config.set_mode_button_region[1] + self.config.set_mode_button_region[3] // 2
            
            print(f"⚠️ Set Mode button not detected, clicking center of region ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)
            time.sleep(self.config.click_delay)
            return True
            
        except Exception as e:
            print(f"❌ Failed to click Set Mode button: {e}")
            return False

    def set_mode(self, mode_name: str) -> bool:
        """Set the mode by OCR and clicking in the dropdown.
        
        Args:
            mode_name: Mode to select ('Agent', 'Ask', 'Edit')
            
        Returns:
            bool: True if mode was set successfully
        """
        print(f"🎛️ Setting mode to: {mode_name}")
        
        try:
            # First click the set mode button to open dropdown
            if not self.click_set_mode_button():
                print("❌ Failed to open mode dropdown")
                return False
            
            # Wait for dropdown to appear
            time.sleep(1.0)
            
            # Take screenshot of dropdown region
            screenshot = self._take_region_screenshot(self.config.set_mode_dropdown_region)
            if not screenshot:
                print("❌ Failed to capture mode dropdown")
                return False
            
            # Extract text from dropdown
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for the mode text
            for element in ocr_data:
                if mode_name.upper() in element['text'].upper():
                    # Calculate absolute coordinates
                    abs_x = self.config.set_mode_dropdown_region[0] + self.config.set_mode_dropdown_region[2] // 3
                    abs_y = self.config.set_mode_dropdown_region[1] + element['center'][1]
                    
                    print(f"✅ Found mode '{mode_name}' at ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            
            print(f"❌ Mode '{mode_name}' not found in dropdown")
            return False
            
        except Exception as e:
            print(f"❌ Failed to set mode: {e}")
            return False

    def click_pick_model_button(self) -> bool:
        """Click the Pick Model button to trigger dropdown.
        
        Returns:
            bool: True if Pick Model button was found and clicked
        """
        print("🎯 Clicking Pick Model button...")
        
        try:
            # Take screenshot of the pick model button region
            screenshot = self._take_region_screenshot(self.config.pick_model_button_region)
            if not screenshot:
                print("❌ Failed to capture Pick Model button region")
                return False
            
            # Extract text from region
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for pick model button patterns
            for element in ocr_data:
                text_upper = element['text'].upper()
                if any(keyword in text_upper for keyword in ['MODEL', 'PICK', 'GPT', 'CLAUDE']):
                    # Calculate absolute coordinates
                    abs_x = self.config.pick_model_button_region[0] + self.config.pick_model_button_region[2] // 3
                    abs_y = self.config.pick_model_button_region[1] + element['center'][1]
                    
                    print(f"✅ Found Pick Model button at ({abs_x}, {abs_y})")
                    print(f"   Text: {element['text']}")
                    
                    # Click the button
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            
            # Fallback: click center of region
            center_x = self.config.pick_model_button_region[0] + self.config.pick_model_button_region[2] // 2
            center_y = self.config.pick_model_button_region[1] + self.config.pick_model_button_region[3] // 2
            
            print(f"⚠️ Pick Model button not detected, clicking center of region ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)
            time.sleep(self.config.click_delay)
            return True
            
        except Exception as e:
            print(f"❌ Failed to click Pick Model button: {e}")
            return False

    def pick_model(self, model_name: str) -> bool:
        """Pick the model by OCR and clicking in the dropdown.
        
        Args:
            model_name: Model to select (e.g., 'GPT-4.1', 'Claude Sonnet 3.5')
            
        Returns:
            bool: True if model was picked successfully
        """
        print(f"🤖 Picking model: {model_name}")
        
        try:
            # First click the pick model button to open dropdown
            if not self.click_pick_model_button():
                print("❌ Failed to open model dropdown")
                return False
            
            # Wait for dropdown to appear
            time.sleep(1.0)
            
            # Take screenshot of dropdown region
            screenshot = self._take_region_screenshot(self.config.pick_model_dropdown_region)
            if not screenshot:
                print("❌ Failed to capture model dropdown")
                return False
            
            # Extract text from dropdown
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for the model text (exact or partial match)
            for element in ocr_data:
                element_text = element['text'].upper()
                model_upper = model_name.upper()
                
                # Try exact match first
                if model_upper in element_text or element_text in model_upper:
                    # Calculate absolute coordinates
                    abs_x = self.config.pick_model_dropdown_region[0] + self.config.pick_model_dropdown_region[2] // 3
                    abs_y = self.config.pick_model_dropdown_region[1] + element['center'][1]
                    
                    print(f"✅ Found model '{model_name}' at ({abs_x}, {abs_y})")
                    print(f"   Matched text: {element['text']}")
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            
            # Try partial word matching
            model_words = model_name.upper().split()
            for element in ocr_data:
                element_words = element['text'].upper().split()
                if any(word in element_words for word in model_words):
                    abs_x = self.config.pick_model_dropdown_region[0] + self.config.pick_model_dropdown_region[2] // 3
                    abs_y = self.config.pick_model_dropdown_region[1] + element['center'][1]
                    
                    print(f"⚠️ Found partial match for '{model_name}': '{element['text']}' at ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            
            print(f"❌ Model '{model_name}' not found in dropdown")
            return False
            
        except Exception as e:
            print(f"❌ Failed to pick model: {e}")
            return False

    def check_keep_button(self) -> bool:
        """Check if Keep button is visible using OCR.
        
        Returns:
            bool: True if Keep button is detected
        """
        print("🔍 Checking for Keep button...")
        
        try:
            # Take screenshot of keep button region
            screenshot = self._take_region_screenshot(self.config.keep_button_region)
            if not screenshot:
                print("❌ Failed to capture Keep button region")
                return False
            
            # Extract text from region
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for Keep button text
            for element in ocr_data:
                if 'KEEP' in element['text'].upper():
                    print(f"✅ Keep button detected: '{element['text']}'")
                    return True
            
            print("❌ Keep button not found")
            return False
            
        except Exception as e:
            print(f"❌ Failed to check Keep button: {e}")
            return False

    def check_interactive_button(self) -> Optional[Tuple[str, Tuple[int, int]]]:
        """Check what type of interactive button is present using OCR.
        
        Returns:
            Tuple[str, Tuple[int, int]]: (button_type, (abs_x, abs_y)) or None
                button_type: Type of button detected ('Continue', 'Allow', 'Yes', 'Enter')
                (abs_x, abs_y): Absolute screen coordinates for clicking
        """
        print("🔍 Checking interactive buttons...")
        
        try:
            # Take screenshot of interactive buttons region
            screenshot = self._take_region_screenshot(self.config.interactive_buttons_region)
            if not screenshot:
                print("❌ Failed to capture interactive buttons region")
                return None
            
            # Extract text from region
            ocr_data = self.extract_ocr_data(screenshot)
            for element in ocr_data:
                text_clean = element['text'].upper().strip()
                if text_clean == 'YES':
                    # Check for following NO button to confirm it's a Yes button
                    next_index = ocr_data.index(element) + 1
                    if next_index < len(ocr_data):
                        next_text = ocr_data[next_index]['text'].upper().strip()
                        if next_text == 'NO':
                            abs_x = self.config.interactive_buttons_region[0] + element['center'][0]
                            abs_y = self.config.interactive_buttons_region[1] + element['center'][1]
                            print(f"✅ Found interactive button: Yes at ({abs_x}, {abs_y}) (confidence: {element['confidence']}%, text: '{element['text']}') followed by No")
                            return ('Yes', (abs_x, abs_y))
                        
                if text_clean == 'ALLOW':
                    next_index = ocr_data.index(element) + 3
                    if next_index < len(ocr_data):
                        next_text = ocr_data[next_index]['text'].upper().strip()
                        if next_text == 'SKIP':
                            abs_x = self.config.interactive_buttons_region[0] + element['center'][0]
                            abs_y = self.config.interactive_buttons_region[1] + element['center'][1]
                            print(f"✅ Found interactive button: Allow at ({abs_x}, {abs_y}) (confidence: {element['confidence']}%, text: '{element['text']}') followed by Skip")
                            return ('Allow', (abs_x, abs_y))
                        
                if text_clean == 'CONTINUE':
                    next_index = ocr_data.index(element) + 1
                    if next_index < len(ocr_data):
                        next_text = ocr_data[next_index]['text'].upper().strip()
                        if next_text == 'PAUSE':
                            abs_x = self.config.interactive_buttons_region[0] + element['center'][0]
                            abs_y = self.config.interactive_buttons_region[1] + element['center'][1]
                            print(f"✅ Found interactive button: Continue at ({abs_x}, {abs_y}) (confidence: {element['confidence']}%, text: '{element['text']}', position: {element['center']}) followed by Pause")
                            return ('Continue', (abs_x, abs_y))
                
                if text_clean == 'ENTER':
                    abs_x = self.config.interactive_buttons_region[0] + element['center'][0]
                    abs_y = self.config.interactive_buttons_region[1] + element['center'][1]
                    print(f"✅ Found interactive button: Enter at ({abs_x}, {abs_y}) (confidence: {element['confidence']}%, text: '{element['text']}')")
                    return ('Enter', (abs_x, abs_y))
            
            print("❌ No interactive buttons detected")
            return None
            
        except Exception as e:
            print(f"❌ Failed to check interactive buttons: {e}")
            return None

    def check_chat_status(self) -> Optional[str]:
        """Check chat status by hovering on Send button and reading tooltip below it.
        
        Returns:
            str: 'complete' if tooltip shows 'Send', 'in_progress' if 'Cancel', None if error
        """
        print("📊 Checking chat status...")
        
        try:
            # Hover over the send button to trigger tooltip
            send_center_x = self.config.send_button_region[0] + self.config.send_button_region[2] // 2
            send_center_y = self.config.send_button_region[1] + self.config.send_button_region[3] // 2
            
            print(f"🖱️ Hovering over send button at ({send_center_x}, {send_center_y})")
            print(f"📍 Send button region: {self.config.send_button_region}")
            pyautogui.moveTo(send_center_x, send_center_y)
            time.sleep(1.0)  # Wait for tooltip to appear
            
            # Calculate tooltip area: between send button bottom and chat panel bottom
            send_bottom = self.config.send_button_region[1] + self.config.send_button_region[3]
            chat_panel_bottom = self.config.chat_panel_region[1] + self.config.chat_panel_region[3]
            
            # Create tooltip region: use full chat panel width for better tooltip detection
            tooltip_region = (
                self.config.chat_panel_region[0],  # x: chat panel left edge
                send_bottom,  # y: send button bottom
                self.config.chat_panel_region[2],  # width: full chat panel width
                chat_panel_bottom - send_bottom  # height: distance to chat panel bottom
            )
            
            print(f"🔍 OCR'ing tooltip area: {tooltip_region}")
            print(f"📏 Tooltip dimensions: {tooltip_region[2]}x{tooltip_region[3]} pixels")
            screenshot = self._take_region_screenshot(tooltip_region)
            if not screenshot:
                print("❌ Failed to capture tooltip region")
                return None
            
            # Save tooltip screenshot for debugging
            # import datetime
            # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # debug_filename = f"tooltip_debug_{timestamp}.png"
            # try:
            #     screenshot.save(debug_filename)
            #     print(f"💾 Saved tooltip screenshot: {debug_filename}")
            # except Exception as save_error:
            #     print(f"⚠️ Failed to save debug image: {save_error}")
            
            # Extract text from tooltip region
            ocr_data = self.extract_ocr_data(screenshot)
            print(f"🔤 Found {len(ocr_data)} text elements in tooltip area:")
            
            # Log all detected text for debugging
            all_text = []
            for i, element in enumerate(ocr_data):
                print(f"  {i+1}. Text: '{element['text']}' (confidence: {element['confidence']})")
                print(f"     Position: {element['center']}, BBox: {element['bbox']}")
                all_text.append(element['text'])
            
            # Show combined OCR text
            combined_text = " ".join(all_text)
            print(f"📝 Combined OCR text: '{combined_text}'")
            if not combined_text.strip():
                print("⚠️ No readable text found in tooltip area")
            
            # Look for tooltip text
            for element in ocr_data:
                text_upper = element['text'].upper()
                if 'SEND' in text_upper:
                    print(f"✅ Chat is complete (Send tooltip detected: '{element['text']}')")
                    return 'complete'
                elif 'CANCEL' in text_upper:
                    print(f"🔄 Chat is in progress (Cancel tooltip detected: '{element['text']}')")
                    return 'in_progress'
            
            print("⚠️ Could not determine chat status from tooltip")
            if not ocr_data:
                print("💭 No text detected in tooltip area - tooltip may not be visible")
            else:
                print("💭 Detected text but no 'Send' or 'Cancel' keywords found")
            return None
            
        except Exception as e:
            print(f"❌ Failed to check chat status: {e}")
            return None

    def scroll_down_chat(self, timeout: float = 30.0) -> bool:
        """Scroll down in the chat display area until bottom text shows model name.
        
        Args:
            timeout: Maximum time to scroll in seconds
        
        Returns:
            bool: True if scrolled to bottom (model name detected), False if timeout
        """
        print("📜 Scrolling down chat display...")
        
        try:
            # Move cursor to center of chat display area
            center_x = self.config.chat_display_region[0] + self.config.chat_display_region[2] // 2
            center_y = self.config.chat_display_region[1] + self.config.chat_display_region[3] // 2
            
            pyautogui.moveTo(center_x, center_y)
            time.sleep(0.2)
            
            start_time = time.time()
            
            # Scroll down with timeout protection
            while time.time() - start_time < timeout:
                # Check if we're at the bottom by OCR'ing bottom text area
                try:
                    screenshot = self._take_region_screenshot(self.config.chat_display_bottom_text_region)
                    if screenshot:
                        ocr_data = self.extract_ocr_data(screenshot)
                        
                        # Look for model names in bottom text
                        for element in ocr_data:
                            text_upper = element['text'].upper()
                            model_patterns = ['GPT-4.1', 'GPT-4O', 'GPT-5', 'CLAUDE SONNET', 'CLAUDE']
                            if any(pattern.upper() in text_upper for pattern in model_patterns):
                                print(f"✅ Reached bottom - model name detected: {element['text']}")
                                return True
                except Exception:
                    pass  # Continue scrolling if OCR fails
                
                # Actually scroll down using scroll wheel (negative values scroll down)
                pyautogui.scroll(-500)  # Scroll down 500 units
                time.sleep(0.05)  # Short pause between scrolls
            print(f"⚠️ Scrolling timeout reached after {timeout}s")
            return False
            
        except Exception as e:
            print(f"❌ Failed to scroll chat display: {e}")
            return False

    def input_chat(self, chat_text: str) -> bool:
        """Input text into the Copilot chat input field.
        
        Args:
            chat_text: The text to input into the chat
            
        Returns:
            bool: True if text was input successfully
        """
        print(f"💬 Inputting chat text: {chat_text[:50]}...")
        
        try:
            # Click on chat input area first
            center_x = self.config.chat_input_region[0] + self.config.chat_input_region[2] // 2
            center_y = self.config.chat_input_region[1] + self.config.chat_input_region[3] // 2
            
            print(f"🖱️ Clicking chat input at ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)
            time.sleep(self.config.click_delay)
            
            # Clear existing text (Ctrl+A, Delete)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # Type the new text
            print(f"⌨️ Typing text...")
            pyautogui.write(chat_text, interval=self.config.type_delay)
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to input chat text: {e}")
            return False

    def send_chat(self) -> bool:
        """Send the chat message by clicking the Send button.
        
        Returns:
            bool: True if send button was clicked successfully
        """
        print("📤 Attempting to send chat message...")
        
        try:
            # Take screenshot of the send button region
            screenshot = self._take_region_screenshot(self.config.send_button_region)
            if not screenshot:
                print("❌ Failed to capture send button region")
                return False
            
            # Extract text from region
            ocr_data = self.extract_ocr_data(screenshot)
            
            # Look for send button patterns
            for element in ocr_data:
                text_upper = element['text'].upper()
                if any(pattern.upper() in text_upper for pattern in self.config.copilot_detection_settings['send']['patterns']):
                    # Calculate absolute coordinates
                    abs_x = self.config.send_button_region[0] + element['center'][0]
                    abs_y = self.config.send_button_region[1] + element['center'][1]
                    
                    print(f"✅ Found Send button at ({abs_x}, {abs_y})")
                    print(f"   Text: {element['text']}")
                    
                    # Click the send button
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(self.config.click_delay)
                    return True
            print("⚠️ Send button not found in send button region")
            return False

        except Exception as e:
            print(f"❌ Failed to send chat: {e}")
            return False

    def click_position(self, x: int, y: int) -> bool:
        """Click at specific screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: True if click was successful
        """
        print(f"🖱️ Clicking at position ({x}, {y})...")
        
        try:
            pyautogui.click(x, y)
            time.sleep(self.config.click_delay)
            return True
            
        except Exception as e:
            print(f"❌ Failed to click at position ({x}, {y}): {e}")
            return False

    def get_latest_chat_text(self) -> Optional[str]:
        """Get the latest chat text by OCR'ing the chat display area.
        
        Returns:
            str: Combined text from the chat display area, None if error
        """
        print("📖 Reading latest chat text...")
        
        try:
            # Take screenshot of chat display region
            screenshot = self._take_region_screenshot(self.config.chat_display_region)
            if not screenshot:
                print("❌ Failed to capture chat display region")
                return None
            
            print(f"📍 Chat display region: {self.config.chat_display_region}")
            print(f"📏 Screenshot dimensions: {screenshot.size[0]}x{screenshot.size[1]} pixels")
            
            # Extract text from chat display
            ocr_data = self.extract_ocr_data(screenshot)
            print(f"🔤 Found {len(ocr_data)} text elements in chat display:")
            
            if not ocr_data:
                print("⚠️ No text detected in chat display area")
                return ""
            
            # Combine all text elements
            all_text = []
            for i, element in enumerate(ocr_data):
                text = element['text'].strip()
                if text:  # Only add non-empty text
                    all_text.append(text)
                    print(f"  {i+1:2d}. '{text}' (confidence: {element['confidence']})")
            
            # Join text with spaces and clean up
            combined_text = " ".join(all_text)
            print(f"📝 Combined chat text: '{combined_text[:100]}{'...' if len(combined_text) > 100 else ''}'")
            
            return combined_text
            
        except Exception as e:
            print(f"❌ Failed to get chat text: {e}")
            return None

    def _take_region_screenshot(self, region: tuple) -> Optional[Image.Image]:
        """Take a screenshot of a specific region.
        
        Args:
            region: Tuple of (x, y, width, height)
            
        Returns:
            PIL Image or None if failed
        """
        try:
            x, y, width, height = region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return screenshot
        except Exception as e:
            self.logger.error(f"Failed to take region screenshot: {e}")
            return None

    def _convert_blue_to_black(self, image: Image.Image) -> Image.Image:
        """Convert blue pixels to black in the image to remove blue visual artifacts.
        
        Args:
            image: PIL Image to process
            
        Returns:
            PIL Image with blue pixels converted to black
        """
        try:
            # Convert to RGB if necessary to ensure we can work with pixel values
            if image.mode not in ['RGB', 'RGBA']:
                image = image.convert('RGB')
            
            # Load pixel data
            pixels = image.load()
            width, height = image.size
            
            def is_blue_pixel(pixel: Tuple[int, ...]) -> bool:
                """Check if pixel is predominantly blue."""
                if len(pixel) >= 3:  # RGB or RGBA
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    # Blue pixel detection with multiple criteria:
                    # 1. Strong blue: high blue value, significantly higher than red/green
                    strong_blue = b > 150 and b > r + 50 and b > g + 50
                    # 2. Light blue: blue is highest component and reasonably high
                    light_blue = b > 180 and b > r and b > g and (b - max(r, g) >= 20)
                    # 3. Cyan-blue: blue and green are both high, but blue is higher
                    cyan_blue = b > 200 and g > 150 and b > g + 15 and b > r + 30
                    
                    return strong_blue or light_blue or cyan_blue
                return False
            
            # Convert blue pixels to black
            blue_pixel_count = 0
            for y in range(height):
                for x in range(width):
                    pixel = pixels[x, y]
                    if is_blue_pixel(pixel):
                        # Convert to black (0, 0, 0) or preserve alpha if RGBA
                        if len(pixel) == 4:  # RGBA
                            pixels[x, y] = (0, 0, 0, pixel[3])
                        else:  # RGB
                            pixels[x, y] = (0, 0, 0)
                        blue_pixel_count += 1
            
            if blue_pixel_count > 0:
                print(f"🔷 Converted {blue_pixel_count} blue pixels to black")
            
            return image
            
        except Exception as e:
            print(f"❌ Error converting blue pixels to black: {e}")
            return image
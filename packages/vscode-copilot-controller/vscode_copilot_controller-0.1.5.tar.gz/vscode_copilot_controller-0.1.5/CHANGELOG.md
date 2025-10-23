# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial PyPI package preparation

## [1.0.0] - 2025-01-22

### Added
- Core OCR-based automation engine for VSCode Copilot chat panel
- Automatic detection and clicking of Keep/Undo buttons
- Message sending to Copilot chat with response waiting
- Status monitoring (Working, Ready states)
- Screenshot capture of Copilot interface areas
- Interactive area configuration tool for precise UI targeting
- Command-line interface (CLI) for automation scripts
- High contrast theme optimization for better OCR accuracy
- Blue pixel to black conversion for cleaner OCR preprocessing
- Support for multiple interactive button types (Continue, Allow, Enter, Yes, Try Again)
- Dropdown detection and selection (Set Mode, Pick Model)
- Chat status monitoring via tooltip detection
- Automatic scrolling to view latest chat responses
- Configuration management with JSON persistence
- Comprehensive error handling and logging
- Cross-platform support (Windows, macOS, Linux)

### Dependencies
- Pillow >= 8.0.0 for image processing
- pytesseract >= 0.3.8 for OCR text recognition
- pyautogui >= 0.9.53 for GUI automation
- Optional: pygetwindow for advanced window management

### Documentation
- Complete README with installation and usage examples
- API documentation for all major classes and methods
- Examples directory with practical usage demonstrations
- Interactive configuration guides

### Testing
- Comprehensive test suite for OCR functionality
- Interactive button detection validation
- Area configuration testing
- Screenshot-based testing with sample images

### Known Limitations
- Requires Tesseract OCR to be installed separately
- Optimized for VSCode high contrast themes
- Performance dependent on screen resolution and UI scaling
- May require manual area configuration for non-standard layouts

## [0.1.0] - 2025-01-15

### Added
- Initial development version
- Basic OCR detection for Copilot interface elements
- Proof of concept for automated Keep button clicking
- Area-based screenshot targeting
- Foundation for UI automation framework

---

## Migration Guide

### From Development Version to 1.0.0

If you were using the development scripts directly:

1. **Install the package**: `pip install vscode-copilot-controller`
2. **Update imports**: 
   ```python
   # Old
   from auto_click_keep import click_keep_button
   
   # New  
   from vscode_copilot_controller import CopilotController
   controller = CopilotController()
   controller.click_keep_button()
   ```
3. **Configuration**: Use the new configuration system instead of hardcoded coordinates
4. **CLI Usage**: Replace direct script execution with CLI commands

### Breaking Changes

- Configuration format changed from hardcoded coordinates to JSON-based area management
- Method signatures updated for consistency and better error handling
- Package structure reorganized with proper module hierarchy

### Upgrading

```bash
# Uninstall development version
pip uninstall vscode-copilot-controller

# Install stable release
pip install vscode-copilot-controller

# Update configuration
python -m vscode_copilot_controller.cli configure-areas
```
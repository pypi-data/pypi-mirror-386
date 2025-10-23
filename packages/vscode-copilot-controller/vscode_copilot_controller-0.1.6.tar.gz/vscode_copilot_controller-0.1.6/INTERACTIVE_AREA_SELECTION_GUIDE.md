# Comprehensive Copilot Chat Panel Setup & Automation Guide

The VSCode Copilot Controller now includes a complete interactive area selection and automation system following the workflow described in `ocr_area_setup_and_usage.md`. This provides Windows Snipping Tool-like functionality for configuring Copilot chat panel areas and comprehensive automation methods.

## 🎯 Complete Workflow Overview

### **1. Config Phase** - Select Copilot Chat Panel Areas
- Select the **entire Copilot chat panel**
- Select **individual buttons/inputs** within the panel:
  - Set Mode button
  - Pick Model button  
  - Send button
  - Chat input area
  - Chat display area
  - Interactive buttons area (Keep, Allow, Continue)
  - Individual action buttons

### **2. Verify Phase** - Mouse Tracking & Validation
- Real-time mouse position tracking
- Console feedback showing which area mouse is hovering over
- Click detection and action logging
- Area interaction verification

### **3. Usage Phase** - Full Automation Methods
- Complete set of automation methods for Copilot interaction
- Precise area-based clicking and text input
- Model selection and chat automation

## 🚀 Quick Start Commands

### Complete Setup & Verification
```bash
# Run the comprehensive setup (all 3 phases)
python copilot_setup_verification.py

# Just area configuration (Windows Snipping Tool-like)
python configure_areas_interactive.py

# Just mouse tracking verification  
python verify_mouse_tracking.py

# Demo all automation features
python demo_enhanced_automation.py
```

## 🔧 Phase 1: Area Configuration

### Comprehensive Area Types
The system now supports all Copilot chat panel elements:

#### **Main Panel**
- **`copilot_chat_panel`**: Entire Copilot chat panel area (~500x800px)

#### **Top Controls**  
- **`set_agent_button`**: Set/change agent mode button (~120x30px)
- **`pick_model_button`**: AI model selection button (~120x30px)

#### **Chat Interaction**
- **`chat_input`**: Main text input area (~400x40px) 
- **`send_button`**: Send message button (~60x30px)
- **`chat_display_area`**: Conversation display area (~450x400px)

#### **Interactive Buttons**
- **`interactive_buttons_area`**: Container for action buttons (~300x50px)
- **`keep_button`**: Keep suggestions button (~80x35px)
- **`allow_button`**: Allow permissions button (~80x35px) 
- **`continue_button`**: Continue multi-step tasks (~80x35px)
- **`undo_button`**: Undo changes button (~80x35px)

#### **Status & Feedback**
- **`status_indicator`**: Working/Ready status area (~150x25px)

### Interactive Selection Process
1. **Launch Tool**: `python configure_areas_interactive.py`
2. **Full Panel First**: Select entire Copilot chat panel
3. **Individual Areas**: Select each button/input area within panel
4. **Area Naming**: Use predefined names or create custom ones
5. **Save Configuration**: Automatic backup and validation

## 🔍 Phase 2: Area Verification

### Mouse Tracking Features
```bash
# Start mouse tracking verification
python verify_mouse_tracking.py
```

#### **Real-time Feedback**
- **Position Tracking**: Live mouse coordinates
- **Area Detection**: Shows which configured area mouse is over
- **Hover Events**: "HOVERING: CHAT_INPUT - Main text input area"
- **Click Events**: "CLICKED: SEND_BUTTON - Send message button"  
- **Area Transitions**: Enter/exit notifications

#### **Verification Output Examples**
```
🎯 HOVERING: SET_AGENT_BUTTON
   📝 Button to set/change the Copilot agent mode
   📍 Position: (320, 220) Size: 120x30
   🎯 Center: (380, 235)

🖱️ CLICKED: SEND_BUTTON  
   ✅ Action detected on: Send message button
```

## 🤖 Phase 3: Automation Usage

### Complete Automation API

#### **Model & Agent Control**
```python
from vscode_copilot_controller.engine import CopilotController

controller = CopilotController()

# Agent and model selection
controller.click_set_agent_button()      # Click Set Agent button
controller.click_set_model_button()      # Click Pick Model button  
controller.set_model("GPT-4")           # Select specific model
```

#### **Chat Interaction**  
```python
# Chat input and sending
controller.input_chat("Hello! Help me write a function")  # Input text
controller.send_chat()                   # Send message
```

#### **Action Buttons**
```python
# Response handling
controller.click_keep_button()           # Keep suggestions
controller.click_allow_button()          # Allow permissions  
controller.click_continue_button()       # Continue multi-step
controller.click_undo_button()          # Undo changes
```

#### **Complete Workflow Example**
```python
# Full automation workflow
controller.click_set_model_button()
controller.set_model("GPT-4")
controller.input_chat("Write a Python function to sort a list")
controller.send_chat()

# After Copilot responds...
controller.click_keep_button()  # Keep the suggestion
```

## 📋 Configuration Management

### Auto-Generated Configuration Structure
```json
{
  "metadata": {
    "created_at": 1761053050.233099,
    "screen_resolution": [3840, 2160],
    "version": "1.0"
  },
  "areas": {
    "copilot_chat_panel": {
      "name": "copilot_chat_panel",
      "x": 2756, "y": 87, "width": 1083, "height": 1893,
      "description": "The entire Copilot chat panel area"
    },
    "set_agent_button": {
      "name": "set_agent_button", 
      "x": 2819, "y": 220, "width": 120, "height": 30,
      "description": "Button to set/change the Copilot agent mode"
    },
    "chat_input": {
      "name": "chat_input",
      "x": 2805, "y": 1789, "width": 973, "height": 84,  
      "description": "Main text input area for Copilot chat"
    }
  }
}
```

### Configuration Commands
```bash
# Show current configuration  
python configure_areas_interactive.py --show

# Update specific area
python configure_areas_interactive.py --update chat_input

# Validate configuration
python test_area_integration.py
```

## 🧪 Testing & Validation

### Comprehensive Test Suite
```bash
# Test all components
python test_area_integration.py     # Integration testing
python demo_enhanced_automation.py  # Feature demonstration  
python verify_mouse_tracking.py     # Real-time verification
```

### Validation Features
- **Bounds Checking**: Areas within screen resolution
- **Overlap Detection**: Identify conflicting areas  
- **Size Validation**: Minimum/maximum area constraints
- **Relationship Analysis**: Distance and positioning
- **OCR Testing**: Text detection accuracy

## 🎨 Advanced Features

### Custom Area Types
Extend functionality with custom areas:
```python
custom_areas = {
    'custom_copilot_button': {
        'name': 'Custom Copilot Button',
        'description': 'My custom Copilot interface element',
        'expected_size': (100, 40)
    }
}
```

### Automation Customization
```python
# Custom confidence thresholds
config = CopilotConfig()
config.copilot_detection_settings['send']['min_confidence'] = 70

# Custom text patterns  
config.copilot_detection_settings['custom_button'] = {
    'patterns': ['My Button', 'Custom'],
    'min_confidence': 60
}
```

### Backup & Restore
- **Automatic Backups**: On each configuration save
- **Manual Export**: Individual areas or full config
- **Restore Points**: Revert to previous configurations

## 🔧 Implementation Details

### Text Detection Patterns
```python
detection_patterns = {
    'set_agent': ['Set Agent', 'Agent', '@'],
    'pick_model': ['Pick Model', 'Model', 'GPT', 'Claude'],  
    'send': ['Send', 'Submit', '→'],
    'keep': ['Keep', 'KEEP'],
    'allow': ['Allow', 'ALLOW'],
    'continue': ['Continue', 'CONTINUE']
}
```

### Region Coordinates (x, y, width, height)
```python
default_regions = {
    'copilot_chat_panel_region': (300, 200, 500, 800),
    'set_agent_button_region': (320, 220, 120, 30),
    'chat_input_region': (320, 800, 400, 40),
    'send_button_region': (730, 805, 60, 30),
    'keep_button_region': (350, 710, 80, 35)
}
```

## 🚀 Getting Started Examples

### Example 1: Complete Setup from Scratch
```bash
# Full interactive setup (all 3 phases)
python copilot_setup_verification.py

# Choose "A" for All steps:
# 1. Configure areas with Windows Snipping Tool interface  
# 2. Verify with mouse tracking
# 3. Test automation methods
```

### Example 2: Quick Automation
```python
from vscode_copilot_controller.engine import CopilotController

# Initialize controller (uses configured areas automatically)
controller = CopilotController()

# Send a quick message
controller.input_chat("Help me debug this Python code")
controller.send_chat()

# Keep any suggestions  
controller.click_keep_button()
```

### Example 3: Advanced Workflow
```python
# Model selection workflow
controller.click_set_model_button()
controller.set_model("Claude")

# Multi-step interaction
controller.input_chat("Create a web scraper")
controller.send_chat()
controller.click_continue_button()  # For multi-step tasks
controller.click_allow_button()     # For permissions
controller.click_keep_button()      # Keep final result
```

This comprehensive system provides the complete Windows Snipping Tool-like functionality with real-time verification and full automation capabilities for VSCode Copilot chat panel interaction!

## 🎯 Quick Start

### Basic Interactive Setup
```bash
# Run the interactive area configuration tool
python configure_areas_interactive.py
```

This will:
1. Take a fullscreen screenshot
2. Open an interactive selection interface
3. Allow you to click and drag to select areas
4. Prompt for area names and descriptions
5. Save the configuration for use with automation

### Show Current Configuration
```bash
# View currently configured areas
python configure_areas_interactive.py --show
```

### Update Specific Area
```bash
# Update a specific area (e.g., keep_button)
python configure_areas_interactive.py --update keep_button
```

## 🖱️ How to Use the Interactive Selector

### Interface Controls
- **Click and Drag**: Select a rectangular area
- **ESC Key**: Cancel selection and exit
- **ENTER Key**: Finish selection process
- **Mouse Movement**: Shows live coordinates and dimensions

### Selection Process
1. **Launch Tool**: Run the interactive configuration script
2. **Screenshot Capture**: Tool automatically takes a fullscreen screenshot
3. **Area Selection**: Click and drag to select the desired area
4. **Area Naming**: Enter a name for the selected area (e.g., "keep_button")
5. **Description**: Add a description for the area
6. **Continue or Finish**: Select more areas or press ENTER to finish

### Visual Feedback
- **Red Rectangle**: Currently being selected
- **Green Rectangle**: Saved area
- **Yellow Text**: Live coordinates and instructions
- **White Labels**: Saved area names

## 🎯 Predefined Area Types

The system recognizes these key Copilot interface areas:

### Essential Areas
- **`keep_button`**: Keep button for Copilot suggestions
- **`undo_button`**: Undo button next to Keep
- **`chat_input`**: Main chat input text area  
- **`send_button`**: Send button for chat messages
- **`status_indicator`**: Working/Ready status area

### Expected Sizes (for reference)
- Keep/Undo buttons: ~80x35 pixels
- Send button: ~60x30 pixels
- Chat input: ~400x40 pixels
- Status indicator: ~150x25 pixels

## 🔧 Configuration Management

### Configuration Files
- **Main Config**: `copilot_areas.json` - Current area configuration
- **Backups**: `copilot_config_backups/` - Automatic backups of previous configurations

### Area Configuration Structure
```json
{
  "metadata": {
    "created_at": 1761053050.233099,
    "last_modified": 1761053050.233099,
    "version": "1.0",
    "screen_resolution": [3840, 2160]
  },
  "areas": {
    "keep_button": {
      "name": "keep_button",
      "x": 1650,
      "y": 400,
      "width": 80,
      "height": 35,
      "description": "Keep button that appears after Copilot suggestions",
      "confidence_threshold": 0.8,
      "last_updated": 1761053050.233099
    }
  }
}
```

## 🧪 Testing and Validation

### Test Configuration
```bash
# Create sample configuration for testing
python demo_area_config_simple.py

# Test integration with CopilotController
python test_area_integration.py
```

### Validation Features
- **Bounds Checking**: Ensures areas are within screen resolution
- **Overlap Detection**: Identifies overlapping areas
- **Size Validation**: Checks for minimum area sizes
- **Relationship Analysis**: Shows distances between areas

## 📋 Usage Examples

### Example 1: Full Setup from Scratch
```bash
# 1. Create initial configuration
python demo_area_config_simple.py

# 2. View the sample configuration  
python configure_areas_interactive.py --show

# 3. Update specific areas interactively
python configure_areas_interactive.py --update keep_button
python configure_areas_interactive.py --update chat_input

# 4. Test the final configuration
python test_area_integration.py
```

### Example 2: Using in Automation
```python
from vscode_copilot_controller.utils.area_config import AreaConfigManager
from vscode_copilot_controller.engine import CopilotController
from vscode_copilot_controller.config import CopilotConfig

# Load configured areas
area_manager = AreaConfigManager()
config = CopilotConfig()

# Update config with configured areas
keep_area = area_manager.get_area("keep_button")
if keep_area:
    config.keep_button_region = keep_area.bbox

# Create controller with configured areas
controller = CopilotController(config)

# Use automation with precise areas
controller.click_keep_button()
```

## 🔍 Troubleshooting

### Common Issues

**Tool Won't Start**
- Ensure tkinter is available: `python -c "import tkinter; print('OK')"`
- Check permissions for screen capture
- Verify virtual environment is activated

**Areas Not Visible**
- Check screen resolution matches configuration
- Verify VSCode Copilot is open and visible
- Ensure areas aren't outside screen bounds

**Selection Not Working**
- Use click and drag motion (not just click)
- Ensure minimum area size (10x10 pixels)
- Check for overlapping windows

### Debug Commands
```bash
# Check current configuration
python configure_areas_interactive.py --show

# Validate areas
python test_area_integration.py

# Check area details and relationships
python -c "
from vscode_copilot_controller.utils.area_config import AreaConfigManager
manager = AreaConfigManager()
print(manager.get_stats())
print(manager.validate_all_areas())
"
```

## 🎨 Customization

### Custom Area Types
You can define custom area types by extending the `InteractiveGuide.KEY_LOCATIONS` dictionary:

```python
custom_locations = {
    'custom_button': {
        'name': 'Custom Button',
        'description': 'My custom button area',
        'expected_size': (100, 50)
    }
}
```

### Configuration Options
- **Confidence Threshold**: Adjust OCR confidence (0.1-1.0)
- **Area Descriptions**: Add detailed descriptions for each area
- **Backup Management**: Automatic backup on configuration changes

## 🚀 Advanced Features

### Area Relationships
- **Distance Calculation**: Get pixel distance between areas
- **Overlap Detection**: Find overlapping areas
- **Nearest Area**: Find closest area to a point

### Screenshot Integration
- **Area Screenshots**: Capture specific configured areas
- **Validation Screenshots**: Visual verification of area locations
- **OCR Testing**: Test text detection in configured areas

### Backup and Restore
- **Automatic Backups**: Created on each configuration save
- **Manual Backup**: Export specific areas or full configuration
- **Restore**: Restore from any backup file

This interactive area selection system provides the Windows Snipping Tool-like functionality you were looking for, allowing precise visual selection of Copilot interface elements for automation!
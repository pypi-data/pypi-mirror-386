"""Screen area selection utilities for Copilot interface.

Provides interactive screen area selection similar to Windows Snipping Tool
for marking Copilot button positions and chat areas.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import List, Dict, Tuple, Optional, Callable, Any
import pyautogui
from PIL import Image, ImageTk, ImageDraw
import time
import json
from pathlib import Path


class AreaSelection:
    """Represents a selected screen area with metadata."""
    
    def __init__(self, name: str, x: int, y: int, width: int, height: int, 
                 description: str = "", confidence_threshold: float = 0.8):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.description = description
        self.confidence_threshold = confidence_threshold
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates of the area."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)
    
    def update_position(self, x: int, y: int, width: int, height: int) -> None:
        """Update the position and size of the area."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'description': self.description,
            'confidence_threshold': self.confidence_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AreaSelection':
        """Create from dictionary."""
        return cls(**data)


class ScreenAreaSelector:
    """Interactive screen area selector similar to Windows Snipping Tool."""
    
    # Area options for dropdown selection
    AREA_OPTIONS = [
        ('chat_panel_region', 'Chat Panel - Entire Copilot chat panel'),
        ('set_mode_button_region', 'Set Mode Button - Button to change Copilot mode (Agent, Ask, Edit)'),
        ('pick_model_button_region', 'Pick Model Button - Button to select AI model'),
        ('send_button_region', 'Send Button - Button to send chat messages'),
        ('set_mode_dropdown_region', 'Set Mode Dropdown - Dropdown list for mode selection'),
        ('pick_model_dropdown_region', 'Pick Model Dropdown - Dropdown list for model selection'),
        ('chat_input_region', 'Chat Input - Main text input area for chat'),
        ('chat_display_region', 'Chat Display - Main conversation display area'),
        ('interactive_buttons_region', 'Interactive Buttons - Area containing Continue, Allow, Enter buttons'),
        ('keep_button_region', 'Keep Button - Button to keep Copilot suggestions'),
        ('chat_display_bottom_text_region', 'Chat Display Bottom Text - Bottom text showing model name')
    ]
    
    def __init__(self, on_area_selected: Optional[Callable] = None):
        self.on_area_selected = on_area_selected
        self.root = None
        self.canvas = None
        self.screenshot = None
        self.screenshot_tk = None
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        self.is_selecting = False
        self.selected_areas: List[AreaSelection] = []
        
    def take_fullscreen_screenshot(self) -> Image.Image:
        """Take a fullscreen screenshot."""
        return pyautogui.screenshot()
    
    def start_selection(self, title: str = "Select Copilot Area", 
                       instruction: str = "Click and drag to select an area"):
        """Start the interactive area selection process."""
        try:
            # Take screenshot
            self.screenshot = self.take_fullscreen_screenshot()
            
            # Create fullscreen window
            self.root = tk.Tk()
            self.root.title(title)
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-topmost', True)
            self.root.configure(cursor='crosshair')
            
            # Convert screenshot to tkinter format
            self.screenshot_tk = ImageTk.PhotoImage(self.screenshot)
            
            # Create canvas
            self.canvas = tk.Canvas(
                self.root,
                width=self.screenshot.width,
                height=self.screenshot.height,
                highlightthickness=0
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            # Display screenshot
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)
            
            # Add instruction overlay
            self.canvas.create_text(
                self.screenshot.width // 2, 50,
                text=instruction + " | Press ESC to cancel | Press ENTER when done",
                fill='yellow',
                font=('Arial', 16, 'bold'),
                width=800
            )
            
            # Bind events
            self.canvas.bind('<Button-1>', self.on_mouse_down)
            self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
            self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
            self.root.bind('<KeyPress-Escape>', self.on_escape)
            self.root.bind('<KeyPress-Return>', self.on_enter)
            
            # Focus to receive key events
            self.root.focus_set()
            
            # Start GUI
            self.root.mainloop()
            
            return self.selected_areas
            
        except Exception as e:
            if self.root:
                self.root.destroy()
            raise Exception(f"Screen selection failed: {e}")
    
    def on_mouse_down(self, event: Any) -> None:
        """Handle mouse button press."""
        self.start_x = event.x
        self.start_y = event.y
        self.is_selecting = True
        
        # Remove previous rectangle if exists
        if self.current_rect:
            self.canvas.delete(self.current_rect)
    
    def on_mouse_drag(self, event: Any) -> None:
        """Handle mouse drag."""
        if not self.is_selecting:
            return
        
        # Remove previous rectangle
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # Draw new rectangle
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2, fill='red', stipple='gray50'
        )
        
        # Show coordinates
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)
        coord_text = f"({min(self.start_x, event.x)}, {min(self.start_y, event.y)}) {width}x{height}"
        
        # Remove previous coordinate text
        for item in self.canvas.find_withtag('coords'):
            self.canvas.delete(item)
        
        # Add new coordinate text
        self.canvas.create_text(
            event.x + 10, event.y - 10,
            text=coord_text,
            fill='yellow',
            font=('Arial', 12, 'bold'),
            tags='coords'
        )
    
    def on_mouse_up(self, event: Any) -> None:
        """Handle mouse button release."""
        if not self.is_selecting:
            return
        
        self.is_selecting = False
        
        # Calculate area coordinates
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        # Ensure positive width/height
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Minimum area size
        if width < 10 or height < 10:
            messagebox.showwarning("Area Too Small", "Please select a larger area")
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
            return
        
        # Hide selection window temporarily
        self.root.withdraw()
        
        # Show dropdown for area selection
        area_name = self._get_area_selection_from_dropdown()
        
        if area_name:
            # Get description from KEY_LOCATIONS  
            guide = InteractiveGuide()
            description = guide.KEY_LOCATIONS.get(area_name, {}).get('description', f'Area: {area_name}')
            
            # Create area selection
            area = AreaSelection(
                name=area_name,
                x=x, y=y, width=width, height=height,
                description=description
            )
            
            self.selected_areas.append(area)
            
            # Update rectangle color to indicate it's saved
            if self.current_rect:
                self.canvas.itemconfig(self.current_rect, outline='green', fill='green')
            
            # Add label
            self.canvas.create_text(
                x + width // 2, y + height // 2,
                text=area_name,
                fill='white',
                font=('Arial', 12, 'bold')
            )
            
            if self.on_area_selected:
                self.on_area_selected(area)
        
        else:
            # User cancelled, remove rectangle
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
        
        self.root.deiconify()  # Show selection window again
    
    def on_escape(self, event: Any) -> None:
        """Handle escape key - cancel selection."""
        self.root.quit()
        self.root.destroy()
    
    def _get_area_selection_from_dropdown(self) -> Optional[str]:
        """Show dropdown menu for area selection."""
        import tkinter as tk
        from tkinter import ttk
        
        root = tk.Tk()
        root.title("Select Area Type")
        root.geometry("1200x700")
        root.attributes('-topmost', True)
        
        selected_area = None
        
        def on_select():
            nonlocal selected_area
            selection = listbox.curselection()
            if selection:
                selected_area = self.AREA_OPTIONS[selection[0]][0]
                root.quit()
                root.destroy()
        
        def on_cancel():
            root.quit()
            root.destroy()
        
        # Create main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = tk.Label(
            main_frame,
            text="Select the type of area you want to configure:",
            font=('Arial', 12, 'bold')
        )
        instructions.pack(pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Arial', 10),
            height=15
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for area_id, description in self.AREA_OPTIONS:
            listbox.insert(tk.END, description)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=10
        )
        cancel_btn.pack(side=tk.LEFT)
        
        select_btn = tk.Button(
            button_frame,
            text="Select",
            command=on_select,
            width=10,
            bg='#0078d4',
            fg='white'
        )
        select_btn.pack(side=tk.RIGHT)
        
        # Bind double-click
        listbox.bind('<Double-Button-1>', lambda e: on_select())
        
        # Center window
        root.transient()
        root.grab_set()
        
        # Start GUI
        root.mainloop()
        
        return selected_area
    
    def on_enter(self, event: Any) -> None:
        """Handle enter key - finish selection."""
        if self.selected_areas:
            result = messagebox.askyesno(
                "Finish Selection",
                f"You have selected {len(self.selected_areas)} area(s). Finish selection?"
            )
            if result:
                self.root.quit()
                self.root.destroy()
        else:
            messagebox.showinfo("No Areas", "Please select at least one area before finishing.")


class InteractiveGuide:
    """Interactive guide for setting up Copilot areas with predefined locations."""
    
    AREA_OPTIONS = [
        ('chat_panel_region', 'Chat Panel - Entire Copilot chat panel'),
        ('set_mode_button_region', 'Set Mode Button - Button to change Copilot mode (Agent, Ask, Edit)'),
        ('pick_model_button_region', 'Pick Model Button - Button to select AI model'),
        ('send_button_region', 'Send Button - Button to send chat messages'),
        ('set_mode_dropdown_region', 'Set Mode Dropdown - Dropdown list for mode selection'),
        ('pick_model_dropdown_region', 'Pick Model Dropdown - Dropdown list for model selection'),
        ('chat_input_region', 'Chat Input - Main text input area for chat'),
        ('chat_display_region', 'Chat Display - Main conversation display area'),
        ('interactive_buttons_region', 'Interactive Buttons - Area containing Continue, Allow, Enter buttons'),
        ('keep_button_region', 'Keep Button - Button to keep Copilot suggestions'),
        ('chat_display_bottom_text_region', 'Chat Display Bottom Text - Bottom text showing model name')
    ]
    
    KEY_LOCATIONS = {
        # Main buttons
        'set_mode_button_region': {
            'name': 'Set Mode Button',
            'description': 'Button to change Copilot mode (Agent, Ask, Edit)',
            'expected_size': (120, 30)
        },
        'pick_model_button_region': {
            'name': 'Pick Model Button',
            'description': 'Button to select AI model',
            'expected_size': (120, 30)
        },
        'send_button_region': {
            'name': 'Send Button',
            'description': 'Button to send chat messages',
            'expected_size': (60, 30)
        },
        # Dropdown areas
        'set_mode_dropdown_region': {
            'name': 'Set Mode Dropdown',
            'description': 'Dropdown list for mode selection (Agent, Ask, Edit)',
            'expected_size': (150, 120)
        },
        'pick_model_dropdown_region': {
            'name': 'Pick Model Dropdown', 
            'description': 'Dropdown list for model selection',
            'expected_size': (200, 200)
        },
        # Main areas
        'chat_input_region': {
            'name': 'Chat Input',
            'description': 'Main text input area for chat',
            'expected_size': (400, 40)
        },
        'chat_display_region': {
            'name': 'Chat Display',
            'description': 'Main conversation display area',
            'expected_size': (450, 400)
        },
        'interactive_buttons_region': {
            'name': 'Interactive Buttons',
            'description': 'Area containing Continue, Allow, Enter buttons',
            'expected_size': (300, 50)
        },
        'keep_button_region': {
            'name': 'Keep Button',
            'description': 'Button to keep Copilot suggestions',
            'expected_size': (80, 35)
        }
    }
    
    def __init__(self):
        self.configured_areas = []
        self.selector = ScreenAreaSelector(on_area_selected=self.on_area_configured)
    
    def on_area_configured(self, area: AreaSelection) -> None:
        """Callback when an area is configured."""
        self.configured_areas.append(area)
        print(f"✅ Area configured: {area.name} at ({area.x}, {area.y}) {area.width}x{area.height}")
    

    
    def run_interactive_setup(self) -> List[AreaSelection]:
        """Run the full interactive setup process."""
        print("🎯 Starting Interactive Copilot Area Setup")
        print("=" * 50)
        
        print("This will help you configure Copilot areas using dropdown selection.")
        print("")
        print("📋 Setup Process:")
        print("  1. Select areas by clicking and dragging")
        print("  2. Choose area type from dropdown menu (no manual typing)")
        print("  3. Available area types:")
        for area_id, description in self.AREA_OPTIONS:
            print(f"     • {area_id}: {description.split(' - ')[1] if ' - ' in description else description}")
        print("")
        print("💡 Special Instructions:")
        print("  • For dropdown areas: Click the button FIRST to open dropdown")
        print("  • Then select the dropdown area that appears")
        print("  • Make sure VSCode Copilot chat is open and visible")
        
        input("\nPress Enter to start area selection...")
        
        # Start selection process
        areas = self.selector.start_selection(
            title="Copilot Area Configuration",
            instruction="Select areas and choose type from dropdown menu"
        )
        
        print(f"\n✅ Configuration complete! Selected {len(areas)} areas:")
        for area in areas:
            print(f"  • {area.name}: ({area.x}, {area.y}) {area.width}x{area.height}")
        
        return areas
    
    def select_single_area(self, area_type: str) -> Optional[AreaSelection]:
        """Select a single specific area type."""
        if area_type not in self.KEY_LOCATIONS:
            raise ValueError(f"Unknown area type: {area_type}")
        
        info = self.KEY_LOCATIONS[area_type]
        print(f"🎯 Selecting {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Expected size: {info['expected_size']}")
        
        areas = self.selector.start_selection(
            title=f"Select {info['name']}",
            instruction=f"Click and drag to select the {info['name']}"
        )
        
        return areas[0] if areas else None
    
    def update_location(self, area_type: str) -> Optional[AreaSelection]:
        """Update a specific location."""
        return self.select_single_area(area_type)
    
    def test_location(self, area_type: str) -> bool:
        """Test a configured location by taking a screenshot."""
        # This would be implemented to test the area
        print(f"🧪 Testing {area_type} location...")
        return True
    
    def list_locations(self) -> None:
        """List all configured locations."""
        print("📋 Configured Locations:")
        for area in self.configured_areas:
            print(f"  • {area.name}: ({area.x}, {area.y}) {area.width}x{area.height}")
            print(f"    Description: {area.description}")


def main() -> None:
    """Demo function to test the screen selector."""
    print("🎯 Screen Area Selector Demo")
    print("=" * 35)
    
    try:
        # Test interactive guide
        guide = InteractiveGuide()
        areas = guide.run_interactive_setup()
        
        if areas:
            print(f"\n✅ Successfully configured {len(areas)} areas!")
            
            # Save to file
            config_data = {
                'areas': [area.to_dict() for area in areas],
                'created_at': time.time()
            }
            
            config_file = Path('copilot_areas.json')
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"💾 Configuration saved to: {config_file}")
        else:
            print("❌ No areas configured")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
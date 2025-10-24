"""Mouse tracking and verification system for Copilot area validation.

This module provides real-time mouse tracking to verify area configurations
and show user interactions with the Copilot chat panel.
"""

import time
import pyautogui
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from vscode_copilot_controller.utils.area_config import AreaConfigManager, AreaConfig


@dataclass
class MouseEvent:
    """Represents a mouse event with area context."""
    timestamp: float
    x: int
    y: int
    event_type: str  # 'hover', 'click', 'move'
    area_name: Optional[str] = None
    area_description: Optional[str] = None


class MouseTracker:
    """Real-time mouse tracking for area verification."""
    
    def __init__(self, area_manager: AreaConfigManager, update_interval: float = 0.1):
        self.area_manager = area_manager
        self.update_interval = update_interval
        self.is_tracking = False
        self.tracking_thread: Optional[threading.Thread] = None
        self.last_position = (0, 0)
        self.last_area: Optional[AreaConfig] = None
        self.events: List[MouseEvent] = []
        self.max_events = 100  # Keep last 100 events
        
        # Callbacks
        self.on_area_enter: Optional[Callable[[str, AreaConfig], None]] = None
        self.on_area_exit: Optional[Callable[[str, AreaConfig], None]] = None
        self.on_area_click: Optional[Callable[[str, AreaConfig], None]] = None
        self.on_mouse_move: Optional[Callable[[int, int], None]] = None
    
    def start_tracking(self) -> None:
        """Start mouse tracking in a separate thread."""
        if self.is_tracking:
            return
        
        self.is_tracking = True
        self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracking_thread.start()
        print("🖱️ Mouse tracking started. Move mouse around Copilot areas...")
    
    def stop_tracking(self) -> None:
        """Stop mouse tracking."""
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
        print("🛑 Mouse tracking stopped.")
    
    def _tracking_loop(self) -> None:
        """Main tracking loop."""
        while self.is_tracking:
            try:
                # Get current mouse position
                current_pos = pyautogui.position()
                current_time = time.time()
                
                # Check if position changed
                if current_pos != self.last_position:
                    self._handle_mouse_move(current_pos.x, current_pos.y, current_time)
                    self.last_position = current_pos
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"⚠️ Tracking error: {e}")
                time.sleep(self.update_interval)
    
    def _handle_mouse_move(self, x: int, y: int, timestamp: float) -> None:
        """Handle mouse movement and area detection."""
        # Find areas at current position
        areas_at_cursor = self.area_manager.find_areas_at_point(x, y)
        current_area = areas_at_cursor[0] if areas_at_cursor else None
        
        # Check for area transitions
        if current_area != self.last_area:
            # Exiting previous area
            if self.last_area:
                self._log_event(timestamp, x, y, 'area_exit', self.last_area.name)
                if self.on_area_exit:
                    self.on_area_exit(self.last_area.name, self.last_area)
                print(f"⬅️ Exited: {self.last_area.name}")
            
            # Entering new area
            if current_area:
                self._log_event(timestamp, x, y, 'area_enter', current_area.name)
                if self.on_area_enter:
                    self.on_area_enter(current_area.name, current_area)
                print(f"➡️ Entered: {current_area.name} - {current_area.description}")
                print(f"   Position: ({x}, {y}) | Area center: {current_area.center}")
            
            self.last_area = current_area
        
        # Log general movement
        area_name = current_area.name if current_area else None
        self._log_event(timestamp, x, y, 'move', area_name)
        
        if self.on_mouse_move:
            self.on_mouse_move(x, y)
    
    def _log_event(self, timestamp: float, x: int, y: int, event_type: str, area_name: Optional[str] = None) -> None:
        """Log a mouse event."""
        area_description = None
        if area_name:
            area = self.area_manager.get_area(area_name)
            if area:
                area_description = area.description
        
        event = MouseEvent(
            timestamp=timestamp,
            x=x, y=y,
            event_type=event_type,
            area_name=area_name,
            area_description=area_description
        )
        
        self.events.append(event)
        
        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
    
    def simulate_click(self, x: int, y: int) -> None:
        """Simulate a click event for testing."""
        timestamp = time.time()
        areas_at_click = self.area_manager.find_areas_at_point(x, y)
        
        if areas_at_click:
            area = areas_at_click[0]
            self._log_event(timestamp, x, y, 'click', area.name)
            if self.on_area_click:
                self.on_area_click(area.name, area)
            print(f"🖱️ CLICK detected on: {area.name} at ({x}, {y})")
            print(f"   Description: {area.description}")
        else:
            self._log_event(timestamp, x, y, 'click')
            print(f"🖱️ CLICK detected at ({x}, {y}) - No configured area")
    
    def get_recent_events(self, count: int = 10) -> List[MouseEvent]:
        """Get recent mouse events."""
        return self.events[-count:] if self.events else []
    
    def get_area_statistics(self) -> Dict[str, int]:
        """Get statistics about area interactions."""
        stats = {}
        for event in self.events:
            if event.area_name:
                if event.area_name not in stats:
                    stats[event.area_name] = 0
                stats[event.area_name] += 1
        return stats
    
    def clear_events(self) -> None:
        """Clear event history."""
        self.events.clear()
        print("🗑️ Event history cleared.")


class AreaVerificationSystem:
    """System for verifying area configurations through user interaction."""
    
    def __init__(self, area_manager: AreaConfigManager):
        self.area_manager = area_manager
        self.tracker = MouseTracker(area_manager)
        self.verification_results: Dict[str, Dict[str, Any]] = {}
        
        # Set up tracking callbacks
        self.tracker.on_area_enter = self._on_area_enter
        self.tracker.on_area_click = self._on_area_click
    
    def _on_area_enter(self, area_name: str, area: AreaConfig) -> None:
        """Handle area enter events."""
        print(f"\n🎯 HOVERING: {area.name.upper()}")
        print(f"   📝 {area.description}")
        print(f"   📍 Position: ({area.x}, {area.y}) Size: {area.width}x{area.height}")
        print(f"   🎯 Center: {area.center}")
    
    def _on_area_click(self, area_name: str, area: AreaConfig) -> None:
        """Handle area click events."""
        print(f"\n🖱️ CLICKED: {area.name.upper()}")
        print(f"   ✅ Action detected on: {area.description}")
        
        # Mark area as verified
        self.verification_results[area_name] = {
            'verified': True,
            'timestamp': time.time(),
            'position': area.center
        }
    
    def start_verification(self, duration: Optional[float] = None) -> None:
        """Start the verification process."""
        print("🔍 Starting Area Verification System")
        print("=" * 40)
        print()
        print("📋 Configured Areas:")
        for name, area in self.area_manager.get_all_areas().items():
            print(f"  • {area.name}: {area.description}")
        print()
        print("🖱️ Instructions:")
        print("  • Move your mouse around the Copilot chat panel")
        print("  • Click on different buttons and areas")
        print("  • Console will show real-time feedback")
        print("  • Press Ctrl+C to stop verification")
        print()
        
        self.tracker.start_tracking()
        
        try:
            if duration:
                print(f"⏱️ Verification will run for {duration} seconds...")
                time.sleep(duration)
            else:
                print("⏱️ Verification running. Press Ctrl+C to stop...")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Verification stopped by user.")
        finally:
            self.tracker.stop_tracking()
            self._show_verification_results()
    
    def _show_verification_results(self) -> None:
        """Show verification results."""
        print("\n📊 Verification Results")
        print("=" * 25)
        
        # Show verified areas
        verified_areas = [name for name, result in self.verification_results.items() if result['verified']]
        total_areas = len(self.area_manager.get_all_areas())
        
        print(f"✅ Verified: {len(verified_areas)}/{total_areas} areas")
        for area_name in verified_areas:
            area = self.area_manager.get_area(area_name)
            if area:
                print(f"  • {area.name}: {area.description}")
        
        # Show unverified areas
        all_area_names = set(self.area_manager.list_areas())
        unverified = all_area_names - set(verified_areas)
        if unverified:
            print(f"\n⚠️ Unverified areas:")
            for area_name in unverified:
                area = self.area_manager.get_area(area_name)
                if area:
                    print(f"  • {area.name}: {area.description}")
        
        # Show interaction statistics
        stats = self.tracker.get_area_statistics()
        if stats:
            print(f"\n📈 Interaction Statistics:")
            for area_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {area_name}: {count} interactions")


def main() -> None:
    """Demo function for area verification."""
    print("🔍 Copilot Area Verification System")
    print("=" * 40)
    
    # Load area configuration
    area_manager = AreaConfigManager()
    if not area_manager.config_file.exists():
        print("❌ No area configuration found.")
        print("   Run: python demo_area_config_simple.py")
        print("   Or:  python configure_areas_interactive.py")
        return
    
    print(f"✅ Loaded {len(area_manager)} configured areas")
    
    # Start verification
    verification_system = AreaVerificationSystem(area_manager)
    verification_system.start_verification()


if __name__ == "__main__":
    main()
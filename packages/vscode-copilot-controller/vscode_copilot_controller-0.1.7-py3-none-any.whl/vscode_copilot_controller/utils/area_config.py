"""Area configuration management for Copilot interface.

Manages saved area configurations and provides utilities for
loading, saving, and validating Copilot interface areas.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import pyautogui
from PIL import Image
import tempfile


@dataclass
class AreaConfig:
    """Configuration for a specific screen area."""
    
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""
    confidence_threshold: float = 0.8
    last_updated: float = 0.0
    
    def __post_init__(self) -> None:
        if self.last_updated == 0.0:
            self.last_updated = time.time()
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates of the area."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)
    
    def is_valid(self) -> bool:
        """Check if area configuration is valid."""
        return (
            self.width > 0 and 
            self.height > 0 and 
            self.x >= 0 and 
            self.y >= 0 and
            self.name.strip() != ""
        )
    
    def update_position(self, x: int, y: int, width: int, height: int) -> None:
        """Update the position and size of the area."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AreaConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within this area."""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )
    
    def overlaps_with(self, other: 'AreaConfig') -> bool:
        """Check if this area overlaps with another area."""
        return not (
            self.x + self.width < other.x or
            other.x + other.width < self.x or
            self.y + self.height < other.y or
            other.y + other.height < self.y
        )
    
    def distance_to_point(self, x: int, y: int) -> float:
        """Calculate distance from area center to a point."""
        center_x, center_y = self.center
        return ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5


class AreaConfigManager:
    """Manages area configurations for Copilot interface."""
    
    DEFAULT_CONFIG_FILE = "copilot_areas.json"
    BACKUP_DIRECTORY = "copilot_config_backups"
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file or self.DEFAULT_CONFIG_FILE)
        self.backup_dir = Path(self.BACKUP_DIRECTORY)
        self.areas: Dict[str, AreaConfig] = {}
        self.metadata: Dict[str, Any] = {
            'created_at': time.time(),
            'last_modified': time.time(),
            'version': '1.0',
            'screen_resolution': self._get_screen_resolution()
        }
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load existing configuration if available
        if self.config_file.exists():
            self.load_config()
    
    def _get_screen_resolution(self) -> Tuple[int, int]:
        """Get current screen resolution."""
        size = pyautogui.size()
        return (size.width, size.height)
    
    def add_area(self, area: AreaConfig, overwrite: bool = False) -> bool:
        """Add a new area configuration."""
        if not area.is_valid():
            raise ValueError(f"Invalid area configuration: {area.name}")
        
        if area.name in self.areas and not overwrite:
            raise ValueError(f"Area '{area.name}' already exists. Use overwrite=True to replace.")
        
        self.areas[area.name] = area
        self.metadata['last_modified'] = time.time()
        return True
    
    def remove_area(self, name: str) -> bool:
        """Remove an area configuration."""
        if name in self.areas:
            del self.areas[name]
            self.metadata['last_modified'] = time.time()
            return True
        return False
    
    def get_area(self, name: str) -> Optional[AreaConfig]:
        """Get area configuration by name."""
        return self.areas.get(name)
    
    def list_areas(self) -> List[str]:
        """List all area names."""
        return list(self.areas.keys())
    
    def get_all_areas(self) -> Dict[str, AreaConfig]:
        """Get all area configurations."""
        return self.areas.copy()
    
    def update_area(self, name: str, **kwargs) -> bool:
        """Update area configuration parameters."""
        if name not in self.areas:
            return False
        
        area = self.areas[name]
        for key, value in kwargs.items():
            if hasattr(area, key):
                setattr(area, key, value)
        
        area.last_updated = time.time()
        self.metadata['last_modified'] = time.time()
        return True
    
    def find_areas_at_point(self, x: int, y: int) -> List[AreaConfig]:
        """Find all areas that contain a specific point."""
        return [area for area in self.areas.values() if area.contains_point(x, y)]
    
    def find_nearest_area(self, x: int, y: int) -> Optional[AreaConfig]:
        """Find the nearest area to a point."""
        if not self.areas:
            return None
        
        return min(self.areas.values(), key=lambda area: area.distance_to_point(x, y))
    
    def validate_all_areas(self) -> Dict[str, List[str]]:
        """Validate all areas and return any issues."""
        issues = {}
        
        for name, area in self.areas.items():
            area_issues = []
            
            # Check validity
            if not area.is_valid():
                area_issues.append("Invalid area configuration")
            
            # Check screen bounds
            screen_width, screen_height = self._get_screen_resolution()
            if area.x + area.width > screen_width:
                area_issues.append(f"Area extends beyond screen width ({screen_width})")
            if area.y + area.height > screen_height:
                area_issues.append(f"Area extends beyond screen height ({screen_height})")
            
            # Check for overlaps
            for other_name, other_area in self.areas.items():
                if name != other_name and area.overlaps_with(other_area):
                    area_issues.append(f"Overlaps with area '{other_name}'")
            
            if area_issues:
                issues[name] = area_issues
        
        return issues
    
    def save_config(self, backup: bool = True) -> bool:
        """Save configuration to file."""
        try:
            # Create backup if requested
            if backup and self.config_file.exists():
                self._create_backup()
            
            # Prepare data for saving
            config_data = {
                'metadata': self.metadata,
                'areas': {name: area.to_dict() for name, area in self.areas.items()}
            }
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if not self.config_file.exists():
                return False
            
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load metadata
            if 'metadata' in config_data:
                self.metadata.update(config_data['metadata'])
            
            # Load areas
            if 'areas' in config_data:
                self.areas = {}
                for name, area_data in config_data['areas'].items():
                    self.areas[name] = AreaConfig.from_dict(area_data)
            
            return True
            
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create a backup of the current configuration."""
        if not self.config_file.exists():
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"copilot_areas_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            import shutil
            shutil.copy2(self.config_file, backup_path)
            print(f"✅ Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️ Failed to create backup: {e}")
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """Restore configuration from a backup file."""
        backup_path = self.backup_dir / backup_file
        if not backup_path.exists():
            return False
        
        try:
            # Create backup of current config
            self._create_backup()
            
            # Copy backup to main config
            import shutil
            shutil.copy2(backup_path, self.config_file)
            
            # Reload configuration
            return self.load_config()
            
        except Exception as e:
            print(f"Failed to restore from backup: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """List available backup files."""
        if not self.backup_dir.exists():
            return []
        
        return [f.name for f in self.backup_dir.glob("*.json")]
    
    def export_area(self, name: str, file_path: str) -> bool:
        """Export a single area to a file."""
        if name not in self.areas:
            return False
        
        try:
            area_data = {
                'name': name,
                'area': self.areas[name].to_dict(),
                'exported_at': time.time()
            }
            
            with open(file_path, 'w') as f:
                json.dump(area_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to export area: {e}")
            return False
    
    def import_area(self, file_path: str, overwrite: bool = False) -> bool:
        """Import an area from a file."""
        try:
            with open(file_path, 'r') as f:
                area_data = json.load(f)
            
            if 'area' not in area_data:
                return False
            
            area = AreaConfig.from_dict(area_data['area'])
            return self.add_area(area, overwrite=overwrite)
            
        except Exception as e:
            print(f"Failed to import area: {e}")
            return False
    
    def take_area_screenshot(self, name: str, save_path: Optional[str] = None) -> Optional[str]:
        """Take a screenshot of a specific area."""
        if name not in self.areas:
            return None
        
        area = self.areas[name]
        
        try:
            # Take screenshot of the area
            screenshot = pyautogui.screenshot(region=area.bbox)
            
            # Save to file
            if save_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = f"area_{name}_{timestamp}.png"
            
            screenshot.save(save_path)
            return save_path
            
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the configuration."""
        return {
            'total_areas': len(self.areas),
            'area_names': list(self.areas.keys()),
            'last_modified': self.metadata.get('last_modified', 0),
            'screen_resolution': self.metadata.get('screen_resolution', (0, 0)),
            'config_file': str(self.config_file),
            'file_exists': self.config_file.exists(),
            'file_size': self.config_file.stat().st_size if self.config_file.exists() else 0,
            'validation_issues': len(self.validate_all_areas())
        }
    
    def clear_all_areas(self) -> None:
        """Clear all area configurations."""
        self.areas.clear()
        self.metadata['last_modified'] = time.time()
    
    def __len__(self) -> int:
        """Get number of configured areas."""
        return len(self.areas)
    
    def __contains__(self, name: str) -> bool:
        """Check if area exists."""
        return name in self.areas
    
    def __str__(self) -> str:
        """String representation."""
        return f"AreaConfigManager({len(self.areas)} areas, file: {self.config_file})"


def main() -> None:
    """Demo function to test the area config manager."""
    print("🔧 Area Configuration Manager Demo")
    print("=" * 40)
    
    # Create manager
    manager = AreaConfigManager()
    
    # Add some example areas
    areas = [
        AreaConfig("keep_button", 100, 200, 80, 35, "Keep button for Copilot suggestions"),
        AreaConfig("chat_input", 50, 500, 400, 40, "Main chat input area"),
        AreaConfig("send_button", 460, 505, 60, 30, "Send button for chat"),
    ]
    
    for area in areas:
        manager.add_area(area)
        print(f"✅ Added area: {area.name}")
    
    # Show stats
    stats = manager.get_stats()
    print(f"\n📊 Stats: {stats['total_areas']} areas configured")
    
    # Validate areas
    issues = manager.validate_all_areas()
    if issues:
        print(f"⚠️ Validation issues found: {issues}")
    else:
        print("✅ All areas valid")
    
    # Save configuration
    if manager.save_config():
        print(f"💾 Configuration saved to: {manager.config_file}")
    
    print(f"\n{manager}")


if __name__ == "__main__":
    main()
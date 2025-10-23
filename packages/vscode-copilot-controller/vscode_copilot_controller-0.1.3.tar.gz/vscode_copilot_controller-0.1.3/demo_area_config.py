#!/usr/bin/env python3"""Demo script showing how to use the configured areas."""

"""Demo of the area configuration system without GUI components.

import sys

This shows how the area configuration system works and creates a sample configuration.from pathlib import Path

"""

# Add current directory to path

import syssys.path.insert(0, str(Path(__file__).parent))

from pathlib import Path

def demo_area_usage():

# Add the vscode_copilot_controller package to the path    """Demonstrate using the configured areas."""

sys.path.insert(0, str(Path(__file__).parent))    try:

        print("🎯 VSCode OCR Area Configuration Demo")

from vscode_copilot_controller.utils.area_config import AreaConfigManager, AreaConfig        print("=" * 50)



        from vscode_ocr.utils import AreaConfigManager

def create_sample_configuration():

    """Create a sample area configuration for testing."""        # Load configuration

    print("🔧 Creating Sample Copilot Area Configuration")        manager = AreaConfigManager()

    print("=" * 50)        config = manager.load_config()

    

    # Create manager        print(f"📋 Loaded configuration with {len(config.areas)} areas")

    manager = AreaConfigManager()        print(f"📁 Config file: {manager.config_path}")

            print()

    # Define sample areas based on typical VSCode Copilot interface

    sample_areas = [        # Display all configured areas

        AreaConfig(        print("📍 Configured Areas:")

            name="keep_button",        print("-" * 30)

            x=1650, y=400, width=80, height=35,

            description="Keep button that appears after Copilot suggestions",        for name, area in config.areas.items():

            confidence_threshold=0.8            print(f"🎯 {area.name}")

        ),            print(f"   Position: ({area.x}, {area.y})")

        AreaConfig(            print(f"   Size: {area.width} x {area.height}")

            name="undo_button",             print(f"   Center: {area.center}")

            x=1740, y=400, width=80, height=35,            print(f"   BBox: {area.bbox}")

            description="Undo button next to Keep button",            print(f"   Confidence: {area.confidence_threshold}")

            confidence_threshold=0.8            print(f"   Description: {area.description}")

        ),            print()

        AreaConfig(

            name="chat_input",        # Show usage examples

            x=300, y=800, width=400, height=40,        print("🔧 Usage Examples:")

            description="Main text input area for Copilot chat",        print("-" * 20)

            confidence_threshold=0.7

        ),        # Example 1: Get specific area

        AreaConfig(        send_area = config.get_area('send_button')

            name="send_button",        if send_area:

            x=710, y=805, width=60, height=30,            print(f"📤 Send Button Area:")

            description="Send button in Copilot chat input",            print(f"   Region for screenshot: {send_area.bbox}")

            confidence_threshold=0.8            print(f"   Click coordinates: {send_area.center}")

        ),            print()

        AreaConfig(

            name="status_indicator",        # Example 2: Use with pyautogui (if available)

            x=300, y=750, width=150, height=25,        print("💻 Example usage with pyautogui:")

            description="Area showing Working/Ready status",        print("   import pyautogui")

            confidence_threshold=0.7        print("   # Screenshot specific area")

        )        print(f"   screenshot = pyautogui.screenshot(region={send_area.bbox if send_area else '(x, y, w, h)'})")

    ]        print("   # Click center of area")

            print(f"   pyautogui.click{send_area.center if send_area else '(x, y)'}")

    # Add areas to manager        print()

    print("Adding sample areas:")

    for area in sample_areas:        # Example 3: Use with OCR engine

        manager.add_area(area, overwrite=True)        print("🔍 Example usage with OCR engine:")

        print(f"  ✅ {area.name}: ({area.x}, {area.y}) {area.width}x{area.height}")        print("   from vscode_ocr import OCREngine")

            print("   engine = OCREngine()")

    # Validate areas        print("   # Use area for targeted detection")

    print(f"\n🔍 Validating configuration...")        print("   elements = engine.extract_ocr_data(screenshot)")

    issues = manager.validate_all_areas()        print("   result = engine.detect_send_button(screenshot)")

    if issues:        print()

        print(f"⚠️ Validation issues found:")

        for area_name, area_issues in issues.items():        # Configuration management examples

            print(f"  • {area_name}: {', '.join(area_issues)}")        print("⚙️ Configuration Management:")

    else:        print("   # Update area")

        print(f"✅ All areas are valid!")        print("   area.update_position(new_x, new_y, new_w, new_h)")

            print("   manager.save_config(config)")

    # Save configuration        print("   # Create backup")

    print(f"\n💾 Saving configuration...")        print("   backup_path = manager.backup_config()")

    if manager.save_config():        print("   # List all configs")

        print(f"✅ Configuration saved to: {manager.config_file}")        print("   configs = manager.list_configs()")

                print()

        # Show stats

        stats = manager.get_stats()        return True

        print(f"\n📊 Configuration Statistics:")

        print(f"  • Total areas: {stats['total_areas']}")    except FileNotFoundError:

        print(f"  • Screen resolution: {stats['screen_resolution']}")        print("❌ No configuration found!")

        print(f"  • Config file size: {stats['file_size']} bytes")        print("Run the area setup first to create configuration.")

        print(f"  • Validation issues: {stats['validation_issues']}")        return False

            except Exception as e:

        return True        print(f"❌ Error: {e}")

    else:        return False

        print(f"❌ Failed to save configuration")

        return Falsedef show_config_file():

    """Show the actual configuration file content."""

    try:

def test_area_operations():        from vscode_ocr.utils import AreaConfigManager

    """Test various area configuration operations."""        import json

    print("\n🧪 Testing Area Configuration Operations")

    print("=" * 45)        manager = AreaConfigManager()

    

    manager = AreaConfigManager()        if manager.config_path.exists():

                print("📄 Configuration File Content:")

    # Test loading            print("=" * 40)

    if manager.load_config():

        print(f"✅ Loaded configuration with {len(manager)} areas")            with open(manager.config_path, 'r', encoding='utf-8') as f:

    else:                config_data = json.load(f)

        print(f"❌ Failed to load configuration")

        return            print(json.dumps(config_data, indent=2))

                print()

    # Test area queries            print(f"📁 File location: {manager.config_path}")

    print(f"\n🔍 Testing area queries:")            print(f"📊 File size: {manager.config_path.stat().st_size} bytes")

            else:

    # Find areas at point            print("❌ Configuration file not found")

    test_point = (1680, 420)  # Near keep button

    areas_at_point = manager.find_areas_at_point(*test_point)    except Exception as e:

    print(f"  • Areas at {test_point}: {[a.name for a in areas_at_point]}")        print(f"❌ Error reading config file: {e}")

    

    # Find nearest areadef update_area_example():

    nearest = manager.find_nearest_area(*test_point)    """Example of how to update an area programmatically."""

    if nearest:    try:

        print(f"  • Nearest area to {test_point}: {nearest.name}")        print("🔄 Area Update Example")

            print("=" * 30)

    # Test area operations

    print(f"\n🔧 Testing area operations:")        from vscode_ocr.utils import AreaConfigManager

    

    # Get specific area        manager = AreaConfigManager()

    keep_button = manager.get_area("keep_button")        config = manager.load_config()

    if keep_button:

        print(f"  • Keep button center: {keep_button.center}")        # Get an area to update

        print(f"  • Keep button bbox: {keep_button.bbox}")        area_name = "send_button"

            area = config.get_area(area_name)

    # Update area

    if manager.update_area("keep_button", confidence_threshold=0.9):        if area:

        print(f"  • Updated keep_button confidence threshold")            print(f"📤 Current {area_name}:")

                print(f"   Position: ({area.x}, {area.y})")

    # Test area relationships            print(f"   Size: {area.width}x{area.height}")

    chat_input = manager.get_area("chat_input")

    send_button = manager.get_area("send_button")            # Update the area (example with new coordinates)

    if chat_input and send_button:            # In real usage, you'd get these from the interactive selector

        overlap = chat_input.overlaps_with(send_button)            area.update_position(900, 680, 90, 40)

        print(f"  • Chat input overlaps with send button: {overlap}")

                print(f"✅ Updated {area_name}:")

    # Save updated configuration            print(f"   New position: ({area.x}, {area.y})")

    if manager.save_config():            print(f"   New size: {area.width}x{area.height}")

        print(f"  ✅ Saved updated configuration")

            # Save updated configuration

            saved_path = manager.save_config(config)

def demonstrate_backup_system():            print(f"💾 Saved to: {saved_path}")

    """Demonstrate the backup and restore functionality."""

    print("\n💾 Testing Backup System")        else:

    print("=" * 30)            print(f"❌ Area '{area_name}' not found")

    

    manager = AreaConfigManager()    except Exception as e:

            print(f"❌ Update error: {e}")

    # List available backups

    backups = manager.list_backups()def main():

    print(f"📂 Available backups: {len(backups)}")    """Main demo function."""

    for backup in backups:    print("VSCode OCR Area Configuration Demo")

        print(f"  • {backup}")    print("=" * 40)

    

    # Create a test area and save (this will create a backup)    print("What would you like to see?")

    test_area = AreaConfig(    print("1. Show configured areas and usage examples")

        name="test_area",    print("2. Show configuration file content")

        x=100, y=100, width=50, height=50,    print("3. Demo area update")

        description="Test area for backup demo"    print("4. All of the above")

    )

        choice = input("Enter choice (1-4): ").strip()

    manager.add_area(test_area, overwrite=True)

    if manager.save_config():    if choice == "1" or choice == "4":

        print(f"✅ Added test area and created backup")        demo_area_usage()

            print()

    # Remove test area

    manager.remove_area("test_area")    if choice == "2" or choice == "4":

    if manager.save_config():        show_config_file()

        print(f"✅ Removed test area")        print()

    

    # Show updated backup list    if choice == "3" or choice == "4":

    new_backups = manager.list_backups()        update_area_example()

    print(f"📂 Backups after operations: {len(new_backups)}")        print()



    print("Demo complete! 🎉")

def show_detailed_configuration():

    """Show detailed information about the current configuration."""if __name__ == "__main__":

    print("\n📋 Detailed Configuration Report")    main()

    print("=" * 40)
    
    manager = AreaConfigManager()
    
    if not manager.config_file.exists():
        print("❌ No configuration file found")
        return
    
    # Load and show all areas
    areas = manager.get_all_areas()
    print(f"Configuration: {manager.config_file}")
    print(f"Total areas: {len(areas)}")
    print()
    
    for name, area in areas.items():
        print(f"🎯 {name.upper()}")
        print(f"   Position: ({area.x}, {area.y})")
        print(f"   Size: {area.width} × {area.height} pixels")
        print(f"   Center: {area.center}")
        print(f"   Description: {area.description}")
        print(f"   Confidence: {area.confidence_threshold}")
        print(f"   Last updated: {area.last_updated}")
        print(f"   Valid: {area.is_valid()}")
        print()
    
    # Show metadata
    print("📊 Metadata:")
    for key, value in manager.metadata.items():
        print(f"   {key}: {value}")


def main():
    """Main demo function."""
    print("🎯 VSCode Copilot Controller - Area Configuration Demo")
    print("=" * 60)
    print()
    print("This demo shows how to configure screen areas for Copilot automation")
    print("without requiring GUI interaction (for testing purposes).")
    print()
    
    try:
        # Create sample configuration
        if create_sample_configuration():
            print("\n" + "="*60)
            
            # Test operations
            test_area_operations()
            print("\n" + "="*60)
            
            # Test backup system
            demonstrate_backup_system()
            print("\n" + "="*60)
            
            # Show final configuration
            show_detailed_configuration()
            
            print("\n✅ Demo completed successfully!")
            print()
            print("Next steps:")
            print("  1. Run 'python configure_areas_interactive.py' for GUI setup")
            print("  2. Use the configured areas in your Copilot automation")
            print("  3. Test area detection with screenshot analysis")
        
        else:
            print("❌ Demo failed during configuration creation")
    
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
"""Command line interface for VSCode Copilot Controller."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .engine import CopilotController
from .config import CopilotConfig
from .exceptions import CopilotControlError


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="VSCode Copilot Controller - Automate VSCode Copilot chat interactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Configure Copilot interface areas interactively
  vscode-copilot-controller configure-areas
  
  # Verify configured areas are valid
  vscode-copilot-controller area-verify
  
  # Verify areas with real-time mouse tracking
  vscode-copilot-controller verify-mouse
  
  # Interactive automation demo
  vscode-copilot-controller usage-demo
  
  # Show OCR configuration
  vscode-copilot-controller config
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file (JSON)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Configuration commands
    config_parser = subparsers.add_parser(
        "config",
        help="Show OCR configuration settings"
    )

    # Interactive area configuration
    configure_areas_parser = subparsers.add_parser(
        "configure-areas",
        help="Interactive area configuration for Copilot interface elements"
    )
    configure_areas_parser.add_argument(
        "--output", "-o",
        default="copilot_areas.json",
        help="Output file for area configuration (default: copilot_areas.json)"
    )

    # Area verification (basic validation)
    verify_areas_parser = subparsers.add_parser(
        "area-verify",
        help="Verify that configured areas are valid (dimensions, coordinates)"
    )
    verify_areas_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to verify (default: copilot_areas.json)"
    )
    verify_areas_parser.add_argument(
        "--area", "-a",
        help="Verify specific area by name (optional)"
    )
    verify_areas_parser.add_argument(
        "--screenshot", "-s",
        action="store_true",
        help="Take screenshots of areas during verification"
    )

    # Real-time mouse tracking verification
    verify_mouse_parser = subparsers.add_parser(
        "verify-mouse",
        help="Verify area configuration through real-time mouse tracking"
    )
    verify_mouse_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to verify (default: copilot_areas.json)"
    )

    # Interactive automation demonstration
    usage_demo_parser = subparsers.add_parser(
        "usage-demo",
        help="Interactive demo of all Copilot automation methods"
    )
    usage_demo_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to use (default: copilot_areas.json)"
    )

    return parser


def load_config(config_path: Optional[str] = None) -> CopilotConfig:
    """Load configuration from file or use defaults."""
    if config_path:
        # TODO: Implement JSON config loading
        print(f"Loading config from {config_path} (not implemented yet)")
    
    return CopilotConfig()


def handle_ocr_config(args, config: CopilotConfig) -> bool:
    """Handle OCR config commands."""
    print("🔧 Current OCR Configuration:")
    print(f"   Tesseract path: {config.tesseract_path}")
    print(f"   PSM mode: {config.psm_mode}")
    print(f"   High confidence: {config.high_confidence_threshold}")
    print(f"   Medium confidence: {config.medium_confidence_threshold}")
    print(f"   Low confidence: {config.low_confidence_threshold}")
    
    region = config.get_screenshot_region()
    if region:
        print(f"   Screenshot region: {region}")
    else:
        print("   Screenshot region: Default (right quarter of screen)")
    
    return True


def handle_configure_areas(args, controller: CopilotController) -> bool:
    """Handle configure-areas command."""
    try:
        from .utils.screen_selector import InteractiveGuide
        from .utils.area_config import AreaConfigManager, AreaConfig
        
        print("🎯 Starting interactive area configuration...")
        print("This will help you configure screen areas for Copilot interface elements.")
        print("")
        
        # Initialize interactive guide
        guide = InteractiveGuide()
        
        # Run the interactive configuration
        areas = guide.run_interactive_setup()
        
        if areas:
            # Convert AreaSelection objects to AreaConfig objects and save
            config_manager = AreaConfigManager(args.output)
            
            for area_selection in areas:
                area_config = AreaConfig(
                    name=area_selection.name,
                    x=area_selection.x,
                    y=area_selection.y,
                    width=area_selection.width,
                    height=area_selection.height,
                    description=f"Auto-configured {area_selection.name} area"
                )
                config_manager.add_area(area_config, overwrite=True)
            
            # Save the configuration
            success = config_manager.save_config()
            
            if success:
                print(f"✅ Area configuration saved to: {args.output}")
                print(f"📊 Configured {len(areas)} areas:")
                for area in areas:
                    print(f"   • {area.name}: ({area.x}, {area.y}) {area.width}x{area.height}")
                return True
            else:
                print("❌ Failed to save area configuration")
                return False
        else:
            print("❌ No areas were configured")
            return False
            
    except ImportError as e:
        print(f"❌ Missing required dependencies for interactive configuration: {e}")
        print("💡 Install GUI dependencies: pip install vscode-copilot-controller[gui]")
        return False
    except Exception as e:
        print(f"❌ Error during area configuration: {e}")
        return False


def handle_area_verify(args, controller: CopilotController) -> bool:
    """Handle area-verify command."""
    try:
        from .utils.area_config import AreaConfigManager
        import os
        
        # Check if config file exists
        if not os.path.exists(args.config_file):
            print(f"❌ Configuration file not found: {args.config_file}")
            print("💡 Run 'vscode-copilot-controller configure-areas' first to create area configuration")
            return False
        
        # Load configuration
        config_manager = AreaConfigManager(args.config_file)
        if not config_manager.load_config():
            print(f"❌ Failed to load configuration from: {args.config_file}")
            return False
        
        print(f"🔍 Verifying areas from: {args.config_file}")
        print("")
        
        # If specific area requested, verify just that one
        if args.area:
            if args.area not in config_manager.areas:
                print(f"❌ Area '{args.area}' not found in configuration")
                available = list(config_manager.areas.keys())
                print(f"💡 Available areas: {', '.join(available)}")
                return False
            
            area = config_manager.areas[args.area]
            print(f"🎯 Verifying area: {args.area}")
            print(f"   Location: ({area.x}, {area.y})")
            print(f"   Size: {area.width}x{area.height}")
            print(f"   Valid: {'✅' if area.is_valid() else '❌'}")
            
            # Take screenshot if requested
            if args.screenshot:
                screenshot_path = config_manager.take_area_screenshot(args.area)
                if screenshot_path:
                    print(f"   Screenshot: {screenshot_path}")
                else:
                    print("   ❌ Failed to take screenshot")
            
            return area.is_valid()
        
        # Verify all areas
        validation_issues = config_manager.validate_all_areas()
        
        all_valid = True
        for name, area in config_manager.areas.items():
            status = "✅" if name not in validation_issues else "❌"
            print(f"{status} {name}: ({area.x}, {area.y}) {area.width}x{area.height}")
            
            if name in validation_issues:
                all_valid = False
                for issue in validation_issues[name]:
                    print(f"     • {issue}")
            
            # Take screenshot if requested
            if args.screenshot:
                screenshot_path = config_manager.take_area_screenshot(name)
                if screenshot_path:
                    print(f"     📷 Screenshot: {screenshot_path}")
        
        print("")
        if all_valid:
            print(f"✅ All {len(config_manager.areas)} areas are valid")
        else:
            problem_count = len(validation_issues)
            print(f"❌ {problem_count} area(s) have issues")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ Error during area verification: {e}")
        return False

def handle_verify_mouse(args, controller: CopilotController) -> bool:
    """Handle verify-mouse command - real-time mouse tracking verification."""
    try:
        from .utils.area_config import AreaConfigManager
        import os
        
        print("🔍 VERIFY AREA CONFIGURATION")
        print("=" * 40)
        print()
        print("📋 Verification Instructions:")
        print("  • Move your mouse around the Copilot chat panel")
        print("  • Console will show real-time area detection:")
        print("    - 'HOVERING: set_mode_button'")
        print("    - 'CLICKED: chat_input'")
        print("    - 'HOVERING: send_button'")
        print("  • Try clicking on different buttons to verify detection")
        print("  • Press Ctrl+C when finished verifying")
        print()
        
        # Check if config file exists
        if not os.path.exists(args.config_file):
            print(f"❌ Configuration file not found: {args.config_file}")
            print("💡 Run 'vscode-copilot-controller configure-areas' first to create area configuration")
            return False
        
        # Load area configuration
        area_manager = AreaConfigManager(args.config_file)
        if not area_manager.load_config():
            print(f"❌ Failed to load configuration from: {args.config_file}")
            return False
        
        print(f"✅ Loaded {len(area_manager.areas)} configured areas")
        
        # Show configured areas
        print("📍 Areas to verify:")
        for name, area in area_manager.areas.items():
            print(f"  • {area.name:20s}: {area.description}")
        print()
        
        # Start area verification system
        try:
            from .utils.mouse_tracker import AreaVerificationSystem
            verification_system = AreaVerificationSystem(area_manager)
            verification_system.start_verification()
            return True
        except ImportError:
            print("❌ Mouse tracking verification not available")
            print("💡 This feature requires additional dependencies")
            return False
        
    except KeyboardInterrupt:
        print("\n👋 Verification stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error during area verification: {e}")
        return False

def handle_usage_demo(args, controller: CopilotController) -> bool:
    """Handle usage-demo command - interactive automation demonstration."""
    try:
        from .utils.area_config import AreaConfigManager
        import os
        
        print("🤖 AUTOMATION METHODS DEMO")
        print("=" * 45)
        print()
        print("📋 Available automation methods:")
        
        methods = [
            ("click_set_mode_button()", "Trigger Set Mode dropdown"),
            ("set_mode(mode_name)", "Select mode: 'Agent', 'Ask', 'Edit'"),
            ("click_pick_model_button()", "Trigger Pick Model dropdown"), 
            ("pick_model(model_name)", "Select model: 'GPT-4.1', 'Claude Sonnet 3.5', etc."),
            ("input_chat(chat_text)", "Input text into chat field"),
            ("send_chat()", "Send the chat message"),
            ("check_keep_button()", "Check if Keep button is visible"),
            ("click_keep_button()", "Click Keep button"),
            ("check_interactive_button()", "Detect Continue/Allow/Enter/Yes buttons (returns type and position)"),
            ("check_chat_status()", "Check if Copilot is working (Send/Cancel tooltip)"),
            ("scroll_down_chat()", "Scroll chat to bottom"),
            ("get_latest_chat_text()", "Extract chat text via OCR"),
            ("click_position(x, y)", "Click at specific coordinates")
        ]
        
        for i, (method, description) in enumerate(methods, 1):
            print(f"  {i:2d}. {method:25s} - {description}")
        print()
        
        # Check if config file exists
        if not os.path.exists(args.config_file):
            print(f"❌ Configuration file not found: {args.config_file}")
            print("💡 Run 'vscode-copilot-controller configure-areas' first to create area configuration")
            return False
        
        # Load area configuration
        area_manager = AreaConfigManager(args.config_file)
        if not area_manager.load_config():
            print(f"❌ Failed to load configuration from: {args.config_file}")
            return False
        
        print(f"✅ Loaded {len(area_manager.areas)} configured areas")
        
        # Interactive usage demonstration
        return demo_automation_methods(controller)
        
    except Exception as e:
        print(f"❌ Error during usage demo: {e}")
        return False

def demo_automation_methods(controller: CopilotController) -> bool:
    """Interactive demo of automation methods."""
    print("\n🎯 INTERACTIVE AUTOMATION DEMO")
    print("Choose an action to test:")
    
    options = [
        ("1", "click_set_mode_button", "Click Set Mode button"),
        ("2", "set_mode", "Set mode (Agent/Ask/Edit)"),
        ("3", "click_pick_model_button", "Click Pick Model button"),
        ("4", "pick_model", "Pick model (specify name)"),
        ("5", "input_chat", "Input chat text"),
        ("6", "send_chat", "Send chat message"),
        ("7", "check_keep_button", "Check if Keep button visible"),
        ("8", "click_keep_button", "Click Keep button"),
        ("9", "check_interactive_button", "Check interactive buttons"),
        ("10", "check_chat_status", "Check chat status (Send/Cancel)"),
        ("11", "scroll_down_chat", "Scroll chat display down"),
        ("12", "get_latest_chat_text", "Get latest chat text via OCR"),
        ("13", "demo_workflow", "Complete workflow demo"),
        ("0", "exit", "Exit demo")
    ]
    
    for num, method, desc in options:
        print(f"  {num:2s}. {desc}")
    
    try:
        while True:
            choice = input("\nEnter your choice (0-13): ").strip()
            position: Optional[Tuple[int, int]] = None
            
            if choice == "0":
                print("👋 Exiting automation demo.")
                break
            elif choice == "1":
                result = controller.click_set_mode_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "2":
                mode = input("Enter mode (Agent/Ask/Edit): ").strip()
                if mode:
                    result = controller.set_mode(mode)
                    print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "3":
                result = controller.click_pick_model_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "4":
                model = input("Enter model (GPT-4.1, Claude Sonnet 3.5, etc.): ").strip()
                if model:
                    result = controller.pick_model(model)
                    print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "5":
                text = input("Enter chat text: ").strip()
                if text:
                    result = controller.input_chat(text)
                    print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "6":
                result = controller.send_chat()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "7":
                result = controller.check_keep_button()
                print(f"Keep button visible: {'✅ Yes' if result else '❌ No'}")
            elif choice == "8":
                result = controller.click_keep_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "9":
                result, position = controller.check_interactive_button()
                print(f"Interactive button: {result if result else '❌ None detected'}")
                if position:
                    print(f"Position: {position}")
                    follow_up_input = input("Do you want to click the detected button now? (y/n): ").strip().lower()
                    if follow_up_input == 'y':
                        click_result = controller.click_position(*position)
                        print(f"Result: {'✅ Success' if click_result else '❌ Failed'}")
            elif choice == "10":
                result = controller.check_chat_status()
                print(f"Chat status: {result if result else '❌ Unknown'}")
            elif choice == "11":
                result = controller.scroll_down_chat()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "12":
                result = controller.get_latest_chat_text()
                if result is not None:
                    print(f"📖 Chat text: {result[:200]}{'...' if len(result) > 200 else ''}")
                else:
                    print("❌ Failed to get chat text")
            else:
                print("❌ Invalid choice. Please enter 0-13.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1

    # Handle config commands specially (don't need controller)
    if args.command == "config":
        success = handle_ocr_config(args, config)
        return 0 if success else 1

    # For other commands, create controller
    try:
        controller = CopilotController(config)
    except Exception as e:
        print(f"❌ Failed to initialize Copilot controller: {e}")
        return 1

    # Dispatch to command handlers
    handlers = {
        "configure-areas": handle_configure_areas,
        "area-verify": handle_area_verify,
        "verify-mouse": handle_verify_mouse,
        "usage-demo": handle_usage_demo,
    }

    if args.command in handlers:
        try:
            success = handlers[args.command](args, controller)
            return 0 if success else 1
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
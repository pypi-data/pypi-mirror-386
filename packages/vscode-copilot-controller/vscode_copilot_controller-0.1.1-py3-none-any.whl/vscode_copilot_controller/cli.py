"""Command line interface for VSCode Copilot Controller."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

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
  # Click Keep button automatically
  vscode-copilot-controller click-keep
  
  # Click Undo button
  vscode-copilot-controller click-undo
  
  # Send message to Copilot
  vscode-copilot-controller send-message "Explain this code"
  
  # Check Copilot status
  vscode-copilot-controller status
  
  # Wait for Copilot to finish working
  vscode-copilot-controller wait-ready --timeout 30
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

    # Click Keep button
    click_keep_parser = subparsers.add_parser(
        "click-keep",
        help="Automatically find and click Keep button in Copilot chat"
    )
    click_keep_parser.add_argument(
        "--screenshot", "-s",
        help="Use specific screenshot file instead of taking new one"
    )

    # Click Undo button
    click_undo_parser = subparsers.add_parser(
        "click-undo", 
        help="Automatically find and click Undo button in Copilot chat"
    )
    click_undo_parser.add_argument(
        "--screenshot", "-s",
        help="Use specific screenshot file instead of taking new one"
    )

    # Send message
    send_message_parser = subparsers.add_parser(
        "send-message",
        help="Send a message to Copilot chat"
    )
    send_message_parser.add_argument(
        "message",
        help="Message to send to Copilot"
    )
    send_message_parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for Copilot response"
    )

    # Get status
    status_parser = subparsers.add_parser(
        "status",
        help="Get current Copilot interface status"
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Output status as JSON"
    )

    # Wait for ready
    wait_parser = subparsers.add_parser(
        "wait-ready",
        help="Wait for Copilot to finish working"
    )
    wait_parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="Maximum time to wait in seconds (default: 30)"
    )

    # Take screenshot
    screenshot_parser = subparsers.add_parser(
        "screenshot",
        help="Take screenshot of Copilot area"
    )
    screenshot_parser.add_argument(
        "output_file",
        help="Output file for screenshot"
    )

    # Configuration commands
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management"
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    
    config_subparsers.add_parser("show", help="Show current configuration")
    
    set_region_parser = config_subparsers.add_parser("set-region", help="Set screenshot region")
    set_region_parser.add_argument("x", type=int, help="X coordinate")
    set_region_parser.add_argument("y", type=int, help="Y coordinate") 
    set_region_parser.add_argument("width", type=int, help="Width")
    set_region_parser.add_argument("height", type=int, help="Height")

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

    return parser


def load_config(config_path: str = None) -> CopilotConfig:
    """Load configuration from file or use defaults."""
    if config_path:
        # TODO: Implement JSON config loading
        print(f"Loading config from {config_path} (not implemented yet)")
    
    return CopilotConfig()


def handle_click_keep(args, controller: CopilotController) -> bool:
    """Handle click-keep command."""
    try:
        screenshot = None
        if args.screenshot:
            from PIL import Image
            screenshot = Image.open(args.screenshot)
            print(f"Using screenshot: {args.screenshot}")
        
        success = controller.click_keep_button(screenshot)
        if success:
            print("✅ Keep button clicked successfully")
            return True
        else:
            print("❌ Keep button not found or click failed")
            return False
            
    except Exception as e:
        print(f"❌ Error clicking Keep button: {e}")
        return False


def handle_click_undo(args, controller: CopilotController) -> bool:
    """Handle click-undo command."""
    try:
        screenshot = None
        if args.screenshot:
            from PIL import Image
            screenshot = Image.open(args.screenshot)
            print(f"Using screenshot: {args.screenshot}")
        
        success = controller.click_undo_button(screenshot)
        if success:
            print("✅ Undo button clicked successfully")
            return True
        else:
            print("❌ Undo button not found or click failed")
            return False
            
    except Exception as e:
        print(f"❌ Error clicking Undo button: {e}")
        return False


def handle_send_message(args, controller: CopilotController) -> bool:
    """Handle send-message command."""
    try:
        wait_for_response = not args.no_wait
        success = controller.send_message_to_copilot(args.message, wait_for_response)
        
        if success:
            print(f"✅ Message sent: {args.message}")
            if wait_for_response:
                print("✅ Copilot finished processing")
            return True
        else:
            print("❌ Failed to send message")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def handle_status(args, controller: CopilotController) -> bool:
    """Handle status command."""
    try:
        status = controller.get_copilot_status()
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("🎯 Copilot Status:")
            print(f"   Working: {status.get('is_working', 'Unknown')}")
            print(f"   Has input: {status.get('has_input', 'Unknown')}")
            print(f"   Has send button: {status.get('has_send', 'Unknown')}")
            print(f"   Available actions: {', '.join(status.get('available_actions', []))}")
            
            if 'error' in status:
                print(f"   ❌ Error: {status['error']}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return False


def handle_wait_ready(args, controller: CopilotController) -> bool:
    """Handle wait-ready command."""
    try:
        print(f"⏳ Waiting for Copilot to become ready (timeout: {args.timeout}s)...")
        success = controller.wait_for_copilot_ready(timeout=args.timeout)
        
        if success:
            print("✅ Copilot is ready")
            return True
        else:
            print("❌ Timeout waiting for Copilot")
            return False
            
    except Exception as e:
        print(f"❌ Error waiting for Copilot: {e}")
        return False


def handle_screenshot(args, controller: CopilotController) -> bool:
    """Handle screenshot command."""
    try:
        screenshot = controller.take_copilot_screenshot()
        screenshot.save(args.output_file)
        print(f"✅ Screenshot saved: {args.output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
        return False


def handle_config(args, config: CopilotConfig) -> bool:
    """Handle config commands."""
    if args.config_command == "show":
        print("🔧 Current Configuration:")
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
        
    elif args.config_command == "set-region":
        config.set_screenshot_region(args.x, args.y, args.width, args.height)
        print(f"✅ Screenshot region set to: ({args.x}, {args.y}, {args.width}, {args.height})")
        return True
    
    return False


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


def main():
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
        success = handle_config(args, config)
        return 0 if success else 1

    # For other commands, create controller
    try:
        controller = CopilotController(config)
    except Exception as e:
        print(f"❌ Failed to initialize Copilot controller: {e}")
        return 1

    # Dispatch to command handlers
    handlers = {
        "click-keep": handle_click_keep,
        "click-undo": handle_click_undo, 
        "send-message": handle_send_message,
        "status": handle_status,
        "wait-ready": handle_wait_ready,
        "screenshot": handle_screenshot,
        "configure-areas": handle_configure_areas,
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
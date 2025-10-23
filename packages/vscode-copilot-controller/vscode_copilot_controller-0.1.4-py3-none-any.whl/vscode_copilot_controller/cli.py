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

    # Area verification
    verify_areas_parser = subparsers.add_parser(
        "area-verify",
        help="Verify that configured areas are valid and accessible"
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

    # Area testing/trying
    try_areas_parser = subparsers.add_parser(
        "area-try",
        help="Test configured areas by taking screenshots and showing previews"
    )
    try_areas_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to test (default: copilot_areas.json)"
    )
    try_areas_parser.add_argument(
        "--area", "-a",
        help="Test specific area by name (optional)"
    )
    try_areas_parser.add_argument(
        "--output-dir", "-o",
        default="area_screenshots",
        help="Directory to save test screenshots (default: area_screenshots)"
    )

    # Step 2: Verify areas with mouse tracking
    verify_mouse_parser = subparsers.add_parser(
        "verify-mouse",
        help="Verify area configuration through real-time mouse tracking"
    )
    verify_mouse_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to verify (default: copilot_areas.json)"
    )

    # Step 3: Usage demo with automation methods
    usage_demo_parser = subparsers.add_parser(
        "usage-demo",
        help="Interactive demonstration of automation methods"
    )
    usage_demo_parser.add_argument(
        "--config-file", "-f",
        default="copilot_areas.json",
        help="Area configuration file to use (default: copilot_areas.json)"
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


def handle_area_try(args, controller: CopilotController) -> bool:
    """Handle area-try command."""
    try:
        from .utils.area_config import AreaConfigManager
        import os
        from pathlib import Path
        
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
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print(f"📸 Testing areas from: {args.config_file}")
        print(f"📁 Screenshots will be saved to: {output_dir}")
        print("")
        
        # If specific area requested, test just that one
        if args.area:
            if args.area not in config_manager.areas:
                print(f"❌ Area '{args.area}' not found in configuration")
                available = list(config_manager.areas.keys())
                print(f"💡 Available areas: {', '.join(available)}")
                return False
            
            area = config_manager.areas[args.area]
            print(f"🎯 Testing area: {args.area}")
            print(f"   Location: ({area.x}, {area.y})")
            print(f"   Size: {area.width}x{area.height}")
            
            # Take screenshot
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"{args.area}_{timestamp}.png"
            screenshot_path = output_dir / screenshot_filename
            
            saved_path = config_manager.take_area_screenshot(args.area, str(screenshot_path))
            if saved_path:
                print(f"   ✅ Screenshot saved: {saved_path}")
                return True
            else:
                print(f"   ❌ Failed to take screenshot")
                return False
        
        # Test all areas
        success_count = 0
        total_areas = len(config_manager.areas)
        
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        for name, area in config_manager.areas.items():
            print(f"📸 Testing {name}: ({area.x}, {area.y}) {area.width}x{area.height}")
            
            screenshot_filename = f"{name}_{timestamp}.png"
            screenshot_path = output_dir / screenshot_filename
            
            saved_path = config_manager.take_area_screenshot(name, str(screenshot_path))
            if saved_path:
                print(f"   ✅ Screenshot saved: {saved_path}")
                success_count += 1
            else:
                print(f"   ❌ Failed to take screenshot")
        
        print("")
        print(f"📊 Summary: {success_count}/{total_areas} areas tested successfully")
        
        if success_count == total_areas:
            print("✅ All areas tested successfully")
            return True
        else:
            print("❌ Some areas failed testing")
            return False
        
    except Exception as e:
        print(f"❌ Error during area testing: {e}")
        return False


def handle_verify_mouse(args, controller: CopilotController) -> bool:
    """Handle verify-mouse command - real-time mouse tracking verification."""
    try:
        from .utils.area_config import AreaConfigManager
        import os
        
        print("🔍 STEP 2: VERIFY AREA CONFIGURATION")
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
        
        print("🤖 STEP 3: AUTOMATION METHODS DEMO")
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
            ("check_keep_button()", "OCR check if Keep button is visible"),
            ("click_keep_button()", "Click Keep button"),
            ("check_interactive_button()", "OCR detect Continue/Allow/Enter buttons"),
            ("click_allow_button()", "Click Allow button"),
            ("click_continue_button()", "Click Continue button"),
            ("click_enter_button()", "Click Enter button"),
            ("check_chat_status()", "Check Send/Cancel tooltip status via OCR"),
            ("scroll_down_chat()", "Scroll chat to bottom using bottom text indicator")
        ]
        
        for i, (method, description) in enumerate(methods, 1):
            print(f"  {i:2d}. {method:25s} - {description}")
        print()
        
        # Check if config file exists
        if not os.path.exists(args.config_file):
            print(f"❌ Configuration file not found: {args.config_file}")
            print("💡 Run 'vscode-copilot-controller configure-areas' first to create area configuration")
            return False
        
        # Load and update configuration
        area_manager = AreaConfigManager(args.config_file)
        if not area_manager.load_config():
            print(f"❌ Failed to load configuration from: {args.config_file}")
            return False
        
        # Update controller config with loaded areas
        area_mapping = {
            'chat_panel': 'chat_panel_region',
            'set_mode_button': 'set_mode_button_region',
            'pick_model_button': 'pick_model_button_region', 
            'send_button': 'send_button_region',
            'set_mode_dropdown': 'set_mode_dropdown_region',
            'pick_model_dropdown': 'pick_model_dropdown_region',
            'chat_input': 'chat_input_region',
            'chat_display': 'chat_display_region',
            'interactive_buttons': 'interactive_buttons_region',
            'keep_button': 'keep_button_region',
            'chat_display_bottom_text': 'chat_display_bottom_text_region'
        }
        
        updated_areas = 0
        for area_name, config_attr in area_mapping.items():
            area = area_manager.get_area(area_name)
            if area:
                setattr(controller.config, config_attr, area.bbox)
                print(f"✅ Updated {config_attr}: {area.bbox}")
                updated_areas += 1
        
        print(f"\n📊 Updated {updated_areas} configuration regions")
        
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
        ("10", "click_allow_button", "Click Allow button"),
        ("11", "click_continue_button", "Click Continue button"),
        ("12", "click_enter_button", "Click Enter button"),
        ("13", "check_chat_status", "Check chat status (Send/Cancel)"),
        ("14", "scroll_down_chat", "Scroll chat display down"),
        ("15", "get_latest_chat_text", "Get latest chat text via OCR"),
        ("16", "demo_workflow", "Complete workflow demo"),
        ("0", "exit", "Exit demo")
    ]
    
    for num, method, desc in options:
        print(f"  {num:2s}. {desc}")
    
    try:
        while True:
            choice = input("\nEnter your choice (0-16): ").strip()
            
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
                result = controller.check_interactive_button()
                print(f"Interactive button: {result if result else '❌ None detected'}")
            elif choice == "10":
                result = controller.click_allow_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "11":
                result = controller.click_continue_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "12":
                result = controller.click_enter_button()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "13":
                result = controller.check_chat_status()
                print(f"Chat status: {result if result else '❌ Unknown'}")
            elif choice == "14":
                result = controller.scroll_down_chat()
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
            elif choice == "15":
                result = controller.get_latest_chat_text()
                if result is not None:
                    print(f"📖 Chat text: {result[:200]}{'...' if len(result) > 200 else ''}")
                else:
                    print("❌ Failed to get chat text")
            elif choice == "16":
                return demo_complete_workflow(controller)
            else:
                print("❌ Invalid choice. Please enter 0-16.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def demo_complete_workflow(controller: CopilotController) -> bool:
    """Demonstrate a complete automation workflow."""
    print("\n🚀 COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 45)
    
    try:
        import time
        
        print("1️⃣ Setting mode to 'Ask'...")
        controller.set_mode("Ask")
        time.sleep(1)
        
        print("\n2️⃣ Picking model 'GPT-4.1'...")
        controller.pick_model("GPT-4.1")
        time.sleep(1)
        
        print("\n3️⃣ Inputting chat message...")
        controller.input_chat("Help me write a Python function to sort a list")
        time.sleep(1)
        
        print("\n4️⃣ Sending chat message...")
        controller.send_chat()
        time.sleep(2)
        
        print("\n5️⃣ Checking chat status...")
        status = controller.check_chat_status()
        print(f"   Status: {status}")
        
        if status == "in_progress":
            print("\n⏳ Waiting for chat to complete...")
            # Could add polling logic here
        
        print("\n6️⃣ Scrolling down to see response...")
        controller.scroll_down_chat()
        time.sleep(1)
        
        print("\n7️⃣ Checking for Keep button...")
        if controller.check_keep_button():
            print("\n8️⃣ Clicking Keep button...")
            controller.click_keep_button()
        
        print("\n✅ Workflow completed!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
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
        "area-verify": handle_area_verify,
        "area-try": handle_area_try,
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
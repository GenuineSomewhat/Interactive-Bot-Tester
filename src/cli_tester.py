#!/usr/bin/env python3
"""
CLI-based bot tester for AI agent testing and automation.
Can be used from terminal without GUI, suitable for CI/CD pipelines and agent integration.

Usage:
    python cli_tester.py --bot <path> --message "hello" [--user-role admin]
    python cli_tester.py --bot <path> --batch message1.txt message2.txt
    python cli_tester.py --bot <path> --high-volume "test" --count 10
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to import interactive_test
sys.path.insert(0, str(Path(__file__).parent))

from interactive_test import InteractiveTester


class CLIBotTester:
    """Command-line interface for bot testing."""
    
    def __init__(self, bot_path: str, output_format: str = "json", verbose: bool = False):
        """
        Initialize CLI tester.
        
        Args:
            bot_path: Path to bot directory or app.py
            output_format: "json" or "text" output format
            verbose: Print debug output
        """
        self.bot_path = bot_path
        self.output_format = output_format
        self.verbose = verbose
        self.tester = None
        
        if self.verbose:
            print(f"[CLI] Initializing tester for bot: {bot_path}", file=sys.stderr)
    
    def load_bot(self) -> bool:
        """
        Load the bot. Returns True on success.
        """
        try:
            if self.verbose:
                print(f"[CLI] Loading bot...", file=sys.stderr)
            self.tester = InteractiveTester(self.bot_path)
            if self.verbose:
                print(f"[CLI] Bot loaded successfully", file=sys.stderr)
            return True
        except Exception as e:
            self.output_error(f"Failed to load bot: {e}")
            return False
    
    def output_json(self, data: Any):
        """Output data as JSON."""
        print(json.dumps(data, indent=2, default=str))
    
    def output_text(self, data: Any):
        """Output data as plain text."""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "text" in item:
                    print(item["text"])
                else:
                    print(item)
        elif isinstance(data, dict):
            if "text" in data:
                print(data["text"])
            else:
                print(json.dumps(data, indent=2, default=str))
        else:
            print(data)
    
    def output_error(self, message: str):
        """Output error message."""
        error_data = {
            "error": True,
            "message": message
        }
        if self.output_format == "json":
            self.output_json(error_data)
        else:
            print(f"ERROR: {message}", file=sys.stderr)
    
    def output_result(self, data: Any, success: bool = True):
        """Output result data."""
        if self.output_format == "json":
            result = {
                "success": success,
                "data": data if isinstance(data, (list, dict)) else {"result": str(data)}
            }
            self.output_json(result)
        else:
            self.output_text(data)
    
    def test_single_message(self, message: str, user_role: str = "admin") -> bool:
        """
        Test a single message.
        
        Args:
            message: Message text to send
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing message: {message[:50]}... (role: {user_role})", file=sys.stderr)
            
            responses = self.tester.test_message(message, user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"Message test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_batch_messages(self, messages: List[str], user_role: str = "admin") -> bool:
        """
        Test multiple messages in sequence.
        
        Args:
            messages: List of message texts
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing batch of {len(messages)} message(s)", file=sys.stderr)
            
            responses = self.tester.test_message_batch(messages, user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} total response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"Batch test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_with_image(self, message: str, image_url: str, user_role: str = "admin") -> bool:
        """
        Test message with image attachment.
        
        Args:
            message: Message text
            image_url: Image URL (can be http/https or local file path)
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing message with image: {image_url}", file=sys.stderr)
            
            attachment = {
                "type": "image",
                "url": image_url
            }
            
            responses = self.tester.test_message_with_attachments(message, [attachment], user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"Image test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_with_location(self, message: str, name: str, lat: float, lng: float, user_role: str = "admin") -> bool:
        """
        Test message with location attachment.
        
        Args:
            message: Message text
            name: Location name
            lat: Latitude
            lng: Longitude
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing message with location: {name}", file=sys.stderr)
            
            attachment = {
                "type": "location",
                "name": name,
                "lat": lat,
                "lng": lng
            }
            
            responses = self.tester.test_message_with_attachments(message, [attachment], user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"Location test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_high_volume(self, base_message: str, count: int = 100, interval: float = 0.1, user_role: str = "admin") -> bool:
        """
        Test high volume message handling.
        
        Args:
            base_message: Base message text
            count: Number of messages to send
            interval: Delay between messages
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing high volume: {count} messages, {interval}s interval", file=sys.stderr)
            
            responses = self.tester.test_high_volume(base_message, count=count, interval=interval, user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"High volume test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_duplicate_message(self, message: str, user_role: str = "admin") -> bool:
        """
        Test duplicate message handling.
        
        Args:
            message: Message text
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing duplicate message handling", file=sys.stderr)
            
            first_responses, second_responses = self.tester.test_duplicate_message(message, user_role=user_role)
            
            result = {
                "first_send": first_responses,
                "second_send_duplicate": second_responses
            }
            
            if self.verbose:
                print(f"[CLI] First: {len(first_responses)}, Second: {len(second_responses)}", file=sys.stderr)
            
            self.output_result(result)
            return True
        except Exception as e:
            self.output_error(f"Duplicate test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def test_error_handling(self, message: str, error_code: int = 409, user_role: str = "admin") -> bool:
        """
        Test error handling with specific HTTP error code.
        
        Args:
            message: Message text
            error_code: HTTP error code (409, 404, 503, etc)
            user_role: "admin" or "user"
        
        Returns:
            True on success
        """
        try:
            if self.verbose:
                print(f"[CLI] Testing error handling ({error_code})", file=sys.stderr)
            
            responses = self.tester.test_message_error(message, error_code=error_code, user_role=user_role)
            
            if self.verbose:
                print(f"[CLI] Got {len(responses)} response(s)", file=sys.stderr)
            
            self.output_result(responses)
            return True
        except Exception as e:
            self.output_error(f"Error test failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def get_bot_info(self) -> bool:
        """Get bot information."""
        try:
            info = {
                "webhook_route": self.tester.webhook_route,
                "bot_dir": self.tester.bot_dir,
                "test_users": self.tester.test_users
            }
            self.output_result(info)
            return True
        except Exception as e:
            self.output_error(f"Could not get bot info: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Terminal-based bot tester for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single message
  python cli_tester.py --bot ~/bot --message "!help"
  
  # Multiple messages from file (one per line)
  python cli_tester.py --bot ~/bot --batch messages.txt
  
  # High volume test
  python cli_tester.py --bot ~/bot --high-volume "test" --count 50 --interval 0.1
  
  # Message with image
  python cli_tester.py --bot ~/bot --message "check this" --image-url https://example.com/image.jpg
  
  # As user instead of admin
  python cli_tester.py --bot ~/bot --message "!play" --user-role user
  
  # JSON output (default)
  python cli_tester.py --bot ~/bot --message "test" --output json
  
  # Plain text output
  python cli_tester.py --bot ~/bot --message "test" --output text
        """
    )
    
    # Required arguments
    parser.add_argument("--bot", required=True, help="Path to bot directory or app.py file")
    
    # Test modes (mutually exclusive)
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("--message", help="Single message to test")
    test_group.add_argument("--batch", help="File with batch of messages (one per line)")
    test_group.add_argument("--high-volume", help="Base message for high volume test")
    test_group.add_argument("--duplicate", help="Message to test duplicate handling")
    test_group.add_argument("--error", help="Message to test with error code")
    test_group.add_argument("--info", action="store_true", help="Get bot information")
    
    # Optional arguments
    parser.add_argument("--user-role", choices=["admin", "user"], default="admin",
                       help="User role for message (default: admin)")
    parser.add_argument("--image-url", help="Image URL for message attachment")
    parser.add_argument("--location", nargs=3, metavar=("NAME", "LAT", "LNG"),
                       help="Location attachment (name, latitude, longitude)")
    parser.add_argument("--output", choices=["json", "text"], default="json",
                       help="Output format (default: json)")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of messages for high-volume test (default: 100)")
    parser.add_argument("--interval", type=float, default=0.1,
                       help="Interval between messages for high-volume test (default: 0.1s)")
    parser.add_argument("--error-code", type=int, default=409,
                       help="HTTP error code to simulate (default: 409)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Print debug output")
    
    args = parser.parse_args()
    
    # Create CLI tester
    cli = CLIBotTester(args.bot, output_format=args.output, verbose=args.verbose)
    
    # Load bot
    if not cli.load_bot():
        sys.exit(1)
    
    # Execute requested test
    success = False
    
    if args.info:
        success = cli.get_bot_info()
    elif args.message:
        if args.image_url:
            success = cli.test_with_image(args.message, args.image_url, args.user_role)
        elif args.location:
            location_name, lat, lng = args.location
            success = cli.test_with_location(args.message, location_name, float(lat), float(lng), args.user_role)
        else:
            success = cli.test_single_message(args.message, args.user_role)
    elif args.batch:
        try:
            with open(args.batch, 'r') as f:
                messages = [line.strip() for line in f if line.strip()]
            success = cli.test_batch_messages(messages, args.user_role)
        except Exception as e:
            cli.output_error(f"Failed to read batch file: {e}")
            sys.exit(1)
    elif args.high_volume:
        success = cli.test_high_volume(args.high_volume, args.count, args.interval, args.user_role)
    elif args.duplicate:
        success = cli.test_duplicate_message(args.duplicate, args.user_role)
    elif args.error:
        success = cli.test_error_handling(args.error, args.error_code, args.user_role)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

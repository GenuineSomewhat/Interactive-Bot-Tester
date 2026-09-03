#!/usr/bin/env python3
"""
AI Agent Bot Tester Wrapper
Simple Python API for AI agents to test bots programmatically.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


class AIAgentBotTester:
    """Simplified API for AI agents to test bots."""
    
    def __init__(self, bot_path: str = ".", auto_load: bool = True):
        """
        Initialize tester for AI agent.
        
        Args:
            bot_path: Path to bot directory
            auto_load: Load bot immediately
        """
        self.bot_path = bot_path
        self.cli_script = Path(__file__).parent / "src" / "cli_tester.py"
        self.loaded = False
        
        if auto_load:
            self.load()
    
    def load(self) -> bool:
        """Load bot and verify it works."""
        try:
            result = self._run_cli(["--info"])
            self.loaded = result["success"]
            return self.loaded
        except Exception as e:
            print(f"[ERROR] Failed to load bot: {e}", file=sys.stderr)
            return False
    
    def _run_cli(self, extra_args: List[str]) -> Dict[str, Any]:
        """Run CLI and return parsed JSON result."""
        cmd = [
            sys.executable,
            str(self.cli_script),
            "--bot", self.bot_path,
            "--output", "json"
        ] + extra_args
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                return {
                    "error": True,
                    "message": result.stderr or "Unknown error"
                }
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            return {"error": True, "message": "Test timed out"}
        except json.JSONDecodeError:
            return {"error": True, "message": f"Invalid JSON: {result.stdout}"}
        except Exception as e:
            return {"error": True, "message": str(e)}
    
    def test(self, message: str, user_role: str = "admin") -> List[Dict[str, Any]]:
        """
        Test a single message.
        
        Args:
            message: Message to send
            user_role: "admin" or "user"
        
        Returns:
            List of responses from bot
        """
        result = self._run_cli(["--message", message, "--user-role", user_role])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        return result.get("data", [])
    
    def test_admin(self, message: str) -> List[Dict[str, Any]]:
        """Test as admin."""
        return self.test(message, user_role="admin")
    
    def test_user(self, message: str) -> List[Dict[str, Any]]:
        """Test as regular user."""
        return self.test(message, user_role="user")
    
    def test_batch(self, messages: List[str], user_role: str = "admin") -> List[Dict[str, Any]]:
        """
        Test multiple messages in sequence.
        
        Args:
            messages: List of messages
            user_role: "admin" or "user"
        
        Returns:
            All responses from bot
        """
        # Write to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for msg in messages:
                f.write(msg + "\n")
            temp_file = f.name
        
        try:
            result = self._run_cli(["--batch", temp_file, "--user-role", user_role])
            
            if result.get("error"):
                raise RuntimeError(result.get("message", "Unknown error"))
            
            return result.get("data", [])
        finally:
            Path(temp_file).unlink()
    
    def test_conversation(self, *messages: str) -> List[Dict[str, Any]]:
        """Test a conversation flow as admin."""
        return self.test_batch(list(messages), user_role="admin")
    
    def test_with_image(self, message: str, image_url: str) -> List[Dict[str, Any]]:
        """Test message with image."""
        result = self._run_cli(["--message", message, "--image-url", image_url])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        return result.get("data", [])
    
    def test_high_volume(self, message: str, count: int = 100, interval: float = 0.1) -> List[Dict[str, Any]]:
        """Test high volume message handling."""
        result = self._run_cli([
            "--high-volume", message,
            "--count", str(count),
            "--interval", str(interval)
        ])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        return result.get("data", [])
    
    def test_duplicate(self, message: str) -> Tuple[List[Dict], List[Dict]]:
        """Test duplicate message handling."""
        result = self._run_cli(["--duplicate", message])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        data = result.get("data", {})
        return data.get("first_send", []), data.get("second_send_duplicate", [])
    
    def test_error(self, message: str, error_code: int = 409) -> List[Dict[str, Any]]:
        """Test error handling."""
        result = self._run_cli([
            "--error", message,
            "--error-code", str(error_code)
        ])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        return result.get("data", [])
    
    def get_info(self) -> Dict[str, Any]:
        """Get bot information."""
        result = self._run_cli(["--info"])
        
        if result.get("error"):
            raise RuntimeError(result.get("message", "Unknown error"))
        
        return result.get("data", {})
    
    def assert_response(self, responses: List[Dict], contains: Optional[str] = None, 
                       count: Optional[int] = None, has_image: bool = False) -> bool:
        """
        Assert response properties (for testing).
        
        Args:
            responses: List of responses
            contains: Text that response should contain
            count: Expected number of responses
            has_image: Whether response should have image attachment
        
        Returns:
            True if assertion passes
        
        Raises:
            AssertionError if assertion fails
        """
        if count is not None and len(responses) != count:
            raise AssertionError(f"Expected {count} responses, got {len(responses)}")
        
        if contains is not None:
            text = " ".join(r.get("text", "") for r in responses)
            if contains not in text:
                raise AssertionError(f"Response does not contain '{contains}'")
        
        if has_image:
            has_any_image = any(
                any(a.get("type") == "image" for a in r.get("attachments", []))
                for r in responses
            )
            if not has_any_image:
                raise AssertionError("Response does not contain image attachment")
        
        return True


def example_usage():
    """Example of how AI agents can use the tester."""
    
    # Initialize tester
    tester = AIAgentBotTester(".")
    
    if not tester.loaded:
        print("Bot failed to load!")
        return
    
    print("=== Example AI Agent Testing ===\n")
    
    # Test 1: Admin command
    print("Test 1: Admin help command")
    responses = tester.test_admin("!help")
    print(f"Got {len(responses)} response(s)")
    for r in responses:
        print(f"  - {r.get('text', '')[:50]}...")
    
    # Test 2: User permissions
    print("\nTest 2: User trying admin command")
    try:
        responses = tester.test_user("!ban someone")
        print(f"User allowed: {len(responses)} response(s)")
    except Exception as e:
        print(f"User denied (expected): {e}")
    
    # Test 3: Conversation flow
    print("\nTest 3: Game conversation")
    try:
        responses = tester.test_conversation("!play", "yes", "2", "left")
        print(f"Game flow completed: {len(responses)} total response(s)")
    except Exception as e:
        print(f"Game flow error: {e}")
    
    # Test 4: Bot info
    print("\nTest 4: Bot information")
    try:
        info = tester.get_info()
        print(f"Webhook route: {info.get('webhook_route')}")
        print(f"Bot dir: {info.get('bot_dir')}")
    except Exception as e:
        print(f"Could not get info: {e}")


if __name__ == "__main__":
    example_usage()

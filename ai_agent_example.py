#!/usr/bin/env python3
"""
AI AGENT QUICK START
How to use the bot tester in your AI agent

This script demonstrates how your AI agent can integrate the bot tester.
"""

import sys
from pathlib import Path

# Add to path (adjust as needed for your setup)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_tester import AIAgentBotTester


class ExampleAgent:
    """Example AI agent that uses the bot tester."""
    
    def __init__(self, bot_path="."):
        """Initialize agent with bot tester."""
        print("[AGENT] Initializing bot tester...")
        self.tester = AIAgentBotTester(bot_path)
        
        if not self.tester.loaded:
            raise RuntimeError("Failed to load bot!")
        
        print("[AGENT] Bot tester ready!")
    
    def verify_bot_health(self):
        """Verify bot is responding."""
        print("[AGENT] Checking bot health...")
        try:
            response = self.tester.test_admin("!help")
            if response:
                print(f"[AGENT] ✓ Bot is healthy ({len(response)} responses)")
                return True
            else:
                print("[AGENT] ✗ Bot not responding")
                return False
        except Exception as e:
            print(f"[AGENT] ✗ Health check failed: {e}")
            return False
    
    def test_command(self, command):
        """Test if a command works."""
        print(f"[AGENT] Testing command: {command}")
        try:
            responses = self.tester.test_admin(command)
            if responses:
                text = responses[0].get("text", "")
                print(f"[AGENT] ✓ Response: {text[:50]}...")
                return True
            else:
                print("[AGENT] ✗ No response from bot")
                return False
        except Exception as e:
            print(f"[AGENT] ✗ Command failed: {e}")
            return False
    
    def test_conversation_flow(self, steps):
        """Test a multi-step conversation."""
        print(f"[AGENT] Testing conversation flow: {len(steps)} steps")
        try:
            responses = self.tester.test_conversation(*steps)
            print(f"[AGENT] ✓ Conversation completed ({len(responses)} responses)")
            return True
        except Exception as e:
            print(f"[AGENT] ✗ Conversation failed: {e}")
            return False
    
    def verify_permissions(self):
        """Verify admin/user permissions work."""
        print("[AGENT] Checking permissions...")
        
        # Test admin access
        try:
            admin_response = self.tester.test_admin("!status")
            admin_works = len(admin_response) > 0
            print(f"[AGENT] Admin access: {'✓' if admin_works else '✗'}")
        except Exception as e:
            admin_works = False
            print(f"[AGENT] Admin access: ✗ ({e})")
        
        # Test user access
        try:
            user_response = self.tester.test_user("!status")
            user_works = len(user_response) > 0
            print(f"[AGENT] User access: {'✓' if user_works else '✗'}")
        except Exception as e:
            user_works = False
            print(f"[AGENT] User access: ✗ ({e})")
        
        return admin_works and user_works
    
    def test_under_load(self, message_count=20):
        """Test bot under load."""
        print(f"[AGENT] Testing under load ({message_count} messages)...")
        try:
            responses = self.tester.test_high_volume("test", count=message_count, interval=0.05)
            response_ratio = len(responses) / message_count * 100
            print(f"[AGENT] ✓ Load test complete ({response_ratio:.0f}% response rate)")
            return True
        except Exception as e:
            print(f"[AGENT] ✗ Load test failed: {e}")
            return False
    
    def run_full_verification(self):
        """Run complete verification suite."""
        print("\n" + "="*60)
        print("RUNNING FULL VERIFICATION SUITE")
        print("="*60 + "\n")
        
        results = {
            "Health": self.verify_bot_health(),
            "Permissions": self.verify_permissions(),
            "Commands": self.test_command("!help"),
            "Load": self.test_under_load(10)
        }
        
        print("\n" + "="*60)
        print("VERIFICATION RESULTS")
        print("="*60)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        all_passed = all(results.values())
        print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
        print("="*60 + "\n")
        
        return all_passed


def example_1_simple_test():
    """Example 1: Simple single command test."""
    print("\n### EXAMPLE 1: Simple Command Test ###\n")
    
    agent = ExampleAgent(".")
    response = agent.tester.test_admin("!help")
    
    print(f"Bot response: {response[0]['text'][:100]}...")


def example_2_conversation():
    """Example 2: Test a conversation flow."""
    print("\n### EXAMPLE 2: Conversation Flow ###\n")
    
    agent = ExampleAgent(".")
    
    # Simulate a conversation
    agent.test_conversation_flow([
        "!play",        # Start game
        "yes",         # Accept
        "2",           # Difficulty
        "left"         # Move
    ])


def example_3_verification():
    """Example 3: Full verification suite."""
    print("\n### EXAMPLE 3: Full Verification ###\n")
    
    agent = ExampleAgent(".")
    agent.run_full_verification()


def example_4_error_handling():
    """Example 4: Proper error handling."""
    print("\n### EXAMPLE 4: Error Handling ###\n")
    
    try:
        agent = ExampleAgent(".")
        
        # Try admin command
        try:
            admin_response = agent.tester.test_admin("!admin")
            print(f"✓ Admin command works: {len(admin_response)} responses")
        except Exception as e:
            print(f"✗ Admin command error: {e}")
        
        # Try user command
        try:
            user_response = agent.tester.test_user("!status")
            print(f"✓ User command works: {len(user_response)} responses")
        except Exception as e:
            print(f"✗ User command error: {e}")
    
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agent Bot Tester Examples")
    parser.add_argument("--example", type=int, default=3, choices=[1, 2, 3, 4],
                       help="Which example to run (1-4, default: 3)")
    parser.add_argument("--bot-path", default=".", help="Path to bot")
    
    args = parser.parse_args()
    
    examples = {
        1: example_1_simple_test,
        2: example_2_conversation,
        3: example_3_verification,
        4: example_4_error_handling,
    }
    
    print(f"\n[AGENT] Running Example {args.example}")
    examples[args.example]()
    print("\n[AGENT] Done!")

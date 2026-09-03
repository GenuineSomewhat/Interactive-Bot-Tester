#!/usr/bin/env python3
"""
Example: AI Agent Testing the Bot
Shows how an AI agent or automation system can test a bot using the CLI tester.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_tester import AIAgentBotTester


def test_basic_commands():
    """Test basic bot commands."""
    print("=== Testing Basic Commands ===\n")
    
    tester = AIAgentBotTester(".")
    
    if not tester.loaded:
        print("ERROR: Could not load bot!")
        return False
    
    # Test 1: Help
    print("1. Testing help command...")
    try:
        responses = tester.test_admin("!help")
        print(f"   ✓ Got {len(responses)} response(s)")
        for r in responses[:2]:  # Show first 2
            print(f"     - {r.get('text', '')[:60]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Status
    print("\n2. Testing status command...")
    try:
        responses = tester.test_admin("!status")
        print(f"   ✓ Got {len(responses)} response(s)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 3: Unknown command
    print("\n3. Testing unknown command...")
    try:
        responses = tester.test_user("!nonexistent")
        print(f"   ✓ Got {len(responses)} response(s)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True


def test_permissions():
    """Test admin vs user permissions."""
    print("\n=== Testing Permissions ===\n")
    
    tester = AIAgentBotTester(".")
    
    # Test 1: Admin can access
    print("1. Admin accessing restricted command...")
    try:
        admin_responses = tester.test_admin("!ban user123")
        print(f"   ✓ Admin got {len(admin_responses)} response(s)")
    except Exception as e:
        print(f"   ✗ Admin error: {e}")
        return False
    
    # Test 2: User cannot access
    print("\n2. User attempting restricted command...")
    try:
        user_responses = tester.test_user("!ban user123")
        if len(user_responses) > 0:
            response_text = user_responses[0].get("text", "").lower()
            if "permission" in response_text or "admin" in response_text or "denied" in response_text:
                print(f"   ✓ User denied (got: {user_responses[0].get('text', '')[:40]}...)")
                return True
            else:
                print(f"   ✗ User was allowed (should be denied)")
                return False
        else:
            print(f"   ✓ User got no response (denied)")
            return True
    except Exception as e:
        print(f"   ✗ User error: {e}")
        return False


def test_conversation_flow():
    """Test a multi-step conversation."""
    print("\n=== Testing Conversation Flow ===\n")
    
    tester = AIAgentBotTester(".")
    
    print("Testing game flow: !play -> yes -> difficulty -> move")
    try:
        responses = tester.test_conversation(
            "!play",           # Start game
            "yes",            # Accept game
            "2",              # Select difficulty
            "left"            # Make move
        )
        print(f"✓ Game flow completed with {len(responses)} total responses")
        return True
    except Exception as e:
        print(f"✗ Game flow failed: {e}")
        return False


def test_load_handling():
    """Test bot under load."""
    print("\n=== Testing Load Handling ===\n")
    
    tester = AIAgentBotTester(".")
    
    print("Sending 20 rapid messages...")
    try:
        responses = tester.test_high_volume("load test", count=20, interval=0.05)
        print(f"✓ Sent 20 messages, got {len(responses)} responses")
        print(f"  (Response ratio: {len(responses)}/20 = {len(responses)/20*100:.0f}%)")
        return True
    except Exception as e:
        print(f"✗ Load test failed: {e}")
        return False


def test_error_conditions():
    """Test error handling."""
    print("\n=== Testing Error Handling ===\n")
    
    tester = AIAgentBotTester(".")
    
    # Test 1: Duplicate detection
    print("1. Testing duplicate message handling...")
    try:
        first, second = tester.test_duplicate("test message")
        print(f"   ✓ First: {len(first)} responses, Second: {len(second)} responses")
        if len(second) == 0:
            print("   ✓ Duplicate correctly rejected")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: API error handling
    print("\n2. Testing 409 Conflict handling...")
    try:
        responses = tester.test_error("test", error_code=409)
        print(f"   ✓ Bot responded to 409: {len(responses)} responses")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Service error
    print("\n3. Testing 503 Service Unavailable...")
    try:
        responses = tester.test_error("test", error_code=503)
        print(f"   ✓ Bot handled 503: {len(responses)} responses")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AI AGENT BOT TESTER - Example Test Suite")
    print("="*60 + "\n")
    
    results = []
    
    # Run test suites
    results.append(("Basic Commands", test_basic_commands()))
    results.append(("Permissions", test_permissions()))
    results.append(("Conversation Flow", test_conversation_flow()))
    results.append(("Load Handling", test_load_handling()))
    results.append(("Error Conditions", test_error_conditions()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

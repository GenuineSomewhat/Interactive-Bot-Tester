"""
Test file for the two-service GroupMe bot architecture.
Tests bot service and website service communication.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from interactive_test import InteractiveTester


def test_bot_service():
    """Test the bot service."""
    # Set test environment variables
    os.environ["ACCESS_TOKEN"] = "test_token_12345"
    os.environ["GROUP_ID"] = "test_group_123"
    os.environ["BOT_ID"] = "test_bot_123"
    os.environ["BOT_NAME"] = "WebMaker Bot"
    os.environ["WEBSITE_URL"] = "http://localhost:3000"
    
    # Initialize tester with bot folder
    bot_folder = str(Path(__file__).parent.parent.parent / "gmb-bot-services" / "bot")
    tester = InteractiveTester(bot_folder)
    
    print("\n" + "="*60)
    print("Two-Service Bot Tester")
    print("="*60)
    print(f"Bot loaded from: {bot_folder}")
    print(f"Webhook route: {tester.webhook_route}")
    print("="*60 + "\n")
    
    # Test 1: Health check
    print("[TEST 1] Testing bot health check...")
    response = tester.app.test_client().get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.get_json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
    assert data["service"] == "bot", f"Expected service 'bot'"
    print("✓ Bot health check works\n")
    
    # Test 2: API status
    print("[TEST 2] Testing API status endpoint...")
    response = tester.app.test_client().get("/api/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.get_json()
    assert data["bot_name"] == "WebMaker Bot", "Bot name mismatch"
    assert data["status"] == "online", "Bot status should be online"
    print("✓ API status endpoint works\n")
    
    # Test 3: Website API endpoint
    print("[TEST 3] Testing website API endpoint...")
    response = tester.app.test_client().get("/api/website")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.get_json()
    assert "html" in data, "Response should contain HTML"
    assert "WebMaker Bot" in data["html"], "HTML should contain bot name"
    assert "<html>" in data["html"].lower(), "Response should contain HTML"
    print("✓ Website API endpoint returns valid HTML\n")
    
    # Test 4: Webhook with help command
    print("[TEST 4] Testing webhook with help command...")
    message_data = {
        "text": "@WebMaker Bot help",
        "sender_id": "user_123",
        "user_id": "user_123",
        "name": "TestUser"
    }
    response = tester.app.test_client().post(
        tester.webhook_route,
        json=message_data
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Webhook processes help command\n")
    
    # Test 5: Webhook with status command
    print("[TEST 5] Testing webhook with status command...")
    message_data = {
        "text": "status",
        "sender_id": "user_456",
        "user_id": "user_456",
        "name": "AnotherUser"
    }
    response = tester.app.test_client().post(
        tester.webhook_route,
        json=message_data
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Webhook processes status command\n")
    
    # Test 6: Webhook with website command
    print("[TEST 6] Testing webhook with website command...")
    message_data = {
        "text": "website",
        "sender_id": "user_789",
        "user_id": "user_789",
        "name": "ThirdUser"
    }
    response = tester.app.test_client().post(
        tester.webhook_route,
        json=message_data
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Webhook processes website command\n")
    
    print("="*60)
    print("All bot service tests passed! ✓")
    print("="*60 + "\n")


def test_website_service():
    """Test website service communication (simulated)."""
    print("[TEST 7] Testing website service architecture...")
    
    bot_folder = str(Path(__file__).parent.parent.parent / "gmb-bot-services" / "bot")
    tester = InteractiveTester(bot_folder)
    
    # Simulate website fetching from bot
    print("[WEBSITE] Simulating website service fetching from bot...")
    response = tester.app.test_client().get("/api/website")
    data = response.get_json()
    
    html = data.get("html", "")
    
    # Verify HTML contains all required elements
    assertions = [
        ("🤖" in html, "HTML contains bot emoji"),
        ("WebMaker Bot" in html, "HTML contains bot name"),
        ("<html>" in html.lower(), "HTML contains html tag"),
        ("status" in html.lower(), "HTML contains status section"),
        ("commands" in html.lower(), "HTML contains commands"),
    ]
    
    for assertion, description in assertions:
        assert assertion, f"Failed: {description}"
        print(f"  ✓ {description}")
    
    print("✓ Website service can fetch and render bot content\n")


def main():
    """Run all tests."""
    print("\n")
    try:
        test_bot_service()
        test_website_service()
        
        print("="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)
        print("\nDeployment Steps:")
        print("1. Create GitHub repo with gmb-bot-services folder")
        print("2. Deploy bot service to Render")
        print("3. Deploy website service to Render")
        print("4. Set WEBSITE_URL in bot service env vars")
        print("5. Set BOT_URL in website service env vars")
        print("6. Update GroupMe bot callback URL")
        print("7. Test in GroupMe!\n")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

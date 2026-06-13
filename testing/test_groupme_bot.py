"""
Test file for GroupMe bot in interactive tester.
Run this to test the bot locally before deploying to Render.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from interactive_test import InteractiveTester


def test_bot():
    """Test the GroupMe bot."""
    # Set test environment variables
    os.environ["ACCESS_TOKEN"] = "test_token_12345"
    os.environ["GROUP_ID"] = "test_group_123"
    os.environ["BOT_ID"] = "test_bot_123"
    os.environ["BOT_NAME"] = "WebMaker Bot"
    
    # Initialize tester with bot folder (gmb webmaker)
    bot_folder = str(Path(__file__).parent.parent.parent / "gmb webmaker")
    tester = InteractiveTester(bot_folder)
    
    print("\n" + "="*60)
    print("GroupMe Bot Tester")
    print("="*60)
    print(f"Bot loaded from: {bot_folder}")
    print(f"Webhook route: {tester.webhook_route}")
    print("="*60 + "\n")
    
    # Test 1: Website homepage
    print("[TEST 1] Testing website homepage...")
    response = tester.app.test_client().get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert b"WebMaker Bot" in response.data, "Bot name not in response"
    print("✓ Website homepage loads correctly\n")
    
    # Test 2: Health check
    print("[TEST 2] Testing health check...")
    response = tester.app.test_client().get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.get_json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
    print("✓ Health check works\n")
    
    # Test 3: API status
    print("[TEST 3] Testing API status endpoint...")
    response = tester.app.test_client().get("/api/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.get_json()
    assert data["bot_name"] == "WebMaker Bot", "Bot name mismatch"
    assert data["status"] == "online", "Bot status should be online"
    print("✓ API status endpoint works\n")
    
    # Test 4: Webhook with help command
    print("[TEST 4] Testing webhook with help command...")
    message_data = {
        "text": "@WebMaker Bot help",
        "sender_id": "user_123",
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
        "name": "ThirdUser"
    }
    response = tester.app.test_client().post(
        tester.webhook_route,
        json=message_data
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Webhook processes website command\n")
    
    print("="*60)
    print("All tests passed! ✓")
    print("="*60 + "\n")
    
    # Instructions
    print("Next steps to deploy on Render:")
    print("1. Create a GitHub repository with your bot code")
    print("2. Go to https://render.com and sign in")
    print("3. Click 'New +' → 'Web Service'")
    print("4. Connect your GitHub repository")
    print("5. Set these environment variables:")
    print("   - ACCESS_TOKEN: Your GroupMe access token")
    print("   - GROUP_ID: Your GroupMe group ID")
    print("   - BOT_ID: Your GroupMe bot ID")
    print("   - BOT_NAME: Name for your bot")
    print("6. Deploy! The site will spin down after 15 minutes of inactivity")
    print("\n")


if __name__ == "__main__":
    try:
        test_bot()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

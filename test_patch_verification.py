#!/usr/bin/env python3
"""
Test that verifies patches are correctly applied and intercept image sends.
This specifically tests the patching system to ensure NO images go to GroupMe.
"""

import sys
sys.path.insert(0, 'src')

from interactive_test import InteractiveTester
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

print("=" * 60)
print("PATCHING VERIFICATION TEST")
print("=" * 60)

# Load the bot (this applies patches)
print("\n1. Loading bot...")
tester = InteractiveTester('c:/Users/miles/OneDrive/Documents/bot')

# Verify patches are applied
print("\n2. Verifying patches are applied...")

# Check that send_message_with_image is patched
import app as loaded_app
if hasattr(loaded_app, 'send_message_with_image'):
    func = loaded_app.send_message_with_image
    print(f"   - app.send_message_with_image = {func}")
    print(f"   - Function name: {func.__name__}")
    # If patched, it should be capture_image_message
    if func.__name__ == 'capture_image_message':
        print(f"   - VERIFIED: send_message_with_image is patched!")
    else:
        print(f"   - WARNING: send_message_with_image is NOT patched (name={func.__name__})")
else:
    print(f"   - ERROR: send_message_with_image not found in app module!")

# Check that plane_game send functions are patched
print("\n3. Checking plane_game patches...")
try:
    import plane_game
    if hasattr(plane_game, 'send_message_with_image'):
        func = plane_game.send_message_with_image
        print(f"   - plane_game.send_message_with_image = {func}")
        print(f"   - Function name: {func.__name__}")
        if func.__name__ == 'capture_image_message':
            print(f"   - VERIFIED: plane_game.send_message_with_image is patched!")
        else:
            print(f"   - WARNING: plane_game.send_message_with_image is NOT patched")
    else:
        print(f"   - ERROR: send_message_with_image not found in plane_game!")
except ImportError as e:
    print(f"   - Could not import plane_game: {e}")

# Send test command and verify capture
print("\n4. Testing image capture...")
print("   Sending: !planegame")

# Clear previous
tester.message_responses = []
tester.sent_messages = []

# Send command
responses = tester.test_message('!planegame')

# Verify capture
print(f"\n5. Verifying capture results...")
print(f"   - Total message responses: {len(tester.message_responses)}")
print(f"   - Total sent messages: {len(tester.sent_messages)}")

image_found = False
for i, resp in enumerate(tester.message_responses):
    has_image = 'attachments' in resp and any(a.get('type') == 'image' for a in resp.get('attachments', []))
    print(f"   - Response {i}: {type(resp).__name__}")
    if isinstance(resp, dict):
        # Don't print text directly due to unicode, just note it exists
        has_text = 'text' in resp
        print(f"     * Has text: {has_text} ({len(resp.get('text', ''))} chars)")
        if has_image:
            print(f"     * IMAGE FOUND!")
            image_found = True
            for att in resp['attachments']:
                if att['type'] == 'image':
                    print(f"       - URL: {att['url'][:60]}...")
                    print(f"       - Is Local: {att.get('is_local_file')}")

if image_found:
    print("\n[SUCCESS] Image was properly captured and NOT sent to GroupMe!")
    print("The GUI should be able to display this image.")
else:
    print("\n[FAILED] No image was captured!")
    print("This means the patches are NOT working correctly.")

print("\n" + "=" * 60)

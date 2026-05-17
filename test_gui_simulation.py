#!/usr/bin/env python3
"""Test that the GUI can properly display captured images."""

import sys
sys.path.insert(0, 'src')

from interactive_test import InteractiveTester

# Simulate what the GUI does
print("=== Simulating GUI Image Display ===\n")

# Load tester
print("[GUI] Loading bot...")
tester = InteractiveTester('c:/Users/miles/OneDrive/Documents/bot')
print("[GUI] Bot loaded successfully\n")

# Send command (simulating user typing !planegame)
print("[GUI] User typed: !planegame")
print("[GUI] Sending to bot...\n")
responses = tester.test_message('!planegame')

print(f"[GUI DEBUG] Got {len(tester.message_responses)} message responses\n")

# Display messages exactly like the GUI does
if tester.message_responses:
    for i, msg_resp in enumerate(tester.message_responses, 1):
        if isinstance(msg_resp, dict):
            # Display text content
            msg_text = msg_resp.get('text', '')
            if msg_text:
                print(f"[{i}] TEXT MESSAGE ({len(msg_text)} chars)\n")
            
            # Display image if present
            if 'attachments' in msg_resp and msg_resp['attachments']:
                for attachment in msg_resp['attachments']:
                    if attachment.get('type') == 'image':
                        url = attachment.get('url', '')
                        is_local = attachment.get('is_local_file', False)
                        print(f"[{i}] IMAGE MESSAGE:")
                        print(f"      Type: image")
                        print(f"      URL Length: {len(url)} chars")
                        print(f"      Is Local: {is_local}")
                        print(f"      URL Domain: {url.split('/')[2] if '/' in url else 'local'}")
                        print(f"      (GUI would download and display image here)\n")

print("=== GUI SIMULATION COMPLETE ===")
print("\nTo test the actual GUI:")
print("1. Run: run_gui.bat (or 'python src/interactive_gui.py')")
print("2. Click 'Load Bot'")
print("3. Type: !planegame")
print("4. Watch for the image to display!")

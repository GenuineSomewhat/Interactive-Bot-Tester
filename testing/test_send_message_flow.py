#!/usr/bin/env python3
"""
Test the exact send_message flow without needing to interact with GUI window.
This simulates what happens when you type !planegame and click Send.
"""

import sys
sys.path.insert(0, 'src')

from interactive_test import InteractiveTester
from threading import Thread
import time

print("=" * 70)
print("SIMULATING GUI SEND_MESSAGE FLOW")
print("=" * 70)

# Load bot (simulating Load Bot button)
print("\n[1] Loading bot...")
tester = InteractiveTester('c:/Users/miles/OneDrive/Documents/bot')
print("[OK] Bot loaded")

# Simulate what send_message does
print("\n[2] Simulating send_message('!planegame')...")
text = "!planegame"

# This is what send_message does
print(f"[GUI] Display: > {text}")

# Create messages list to capture display output
displayed_messages = []

def display_message(msg):
    """Simulate GUI display_message"""
    displayed_messages.append(msg)
    print(f"[DISPLAYED] {msg[:60]}...")

# This is the test() function from send_message
def test():
    try:
        print(f"[TEST] Sending message: {text}")
        responses = tester.test_message(text)
        print(f"[TEST] test_message() returned {len(responses)} responses")
        print(f"[TEST] message_responses has {len(tester.message_responses)} items")
        
        # Display messages with their attachments from message_responses
        if tester.message_responses:
            print(f"[TEST] Processing {len(tester.message_responses)} messages")
            for i, msg_resp in enumerate(tester.message_responses, 1):
                print(f"[TEST] Message {i}: type={type(msg_resp)}, keys={list(msg_resp.keys()) if isinstance(msg_resp, dict) else 'N/A'}")
                if isinstance(msg_resp, dict):
                    # Display text content
                    msg_text = msg_resp.get('text', '')
                    if msg_text:
                        print(f"[TEST] Displaying text for message {i}")
                        display_message(f"[{i}] {msg_text}\n")
                    
                    # Display image if present
                    if 'attachments' in msg_resp and msg_resp['attachments']:
                        print(f"[TEST] Message {i} has {len(msg_resp['attachments'])} attachments")
                        for att_idx, attachment in enumerate(msg_resp['attachments']):
                            att_type = attachment.get('type', 'unknown')
                            print(f"[TEST] Attachment {att_idx}: type={att_type}")
                            if att_type == 'image' and attachment.get('url'):
                                is_local = attachment.get('is_local_file', False)
                                print(f"[TEST] Would display image: {attachment['url'][:60]}..., is_local={is_local}")
                                display_message(f"[IMAGE] {attachment['url']}\n")
                            else:
                                print(f"[TEST] Skipping attachment type: {att_type}")
                    else:
                        print(f"[TEST] Message {i} has no attachments")
                else:
                    display_message(f"[{i}] {msg_resp}\n")
        else:
            print(f"[TEST] message_responses is empty!")
            display_message("(no response)\n")
        print(f"[TEST] Finished displaying all messages")
    except Exception as e:
        print(f"[TEST ERROR] {e}")
        import traceback
        traceback.print_exc()
        display_message(f"[ERROR] {e}\n")

# Run test in thread (like GUI does)
print("\n[3] Running test in background thread...")
thread = Thread(target=test, daemon=True)
thread.start()

# Wait for thread to finish
print("[MAIN] Waiting for thread to complete...")
thread.join(timeout=60)

if thread.is_alive():
    print("[ERROR] Thread is still running after 60 seconds!")
else:
    print("[OK] Thread completed")

# Show what was displayed
print("\n" + "=" * 70)
print("MESSAGES THAT WOULD BE DISPLAYED:")
print("=" * 70)
if displayed_messages:
    for msg in displayed_messages:
        print(f">>> {msg}")
    print("\n[SUCCESS] Messages would be displayed in the GUI!")
else:
    print("[ERROR] NO MESSAGES DISPLAYED!")
    
print("=" * 70)

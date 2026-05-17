#!/usr/bin/env python3
"""
Test that simulates the EXACT GUI flow to debug image display issues.
"""

import sys
sys.path.insert(0, 'src')

from interactive_test import InteractiveTester
import urllib.request
import urllib.error
from io import BytesIO

# Check PIL
try:
    from PIL import Image
    HAS_PIL = True
    print("[OK] PIL is available")
except ImportError:
    HAS_PIL = False
    print("[ERROR] PIL not available - images cannot be displayed")

print("\n" + "=" * 70)
print("GUI FLOW SIMULATION TEST")
print("=" * 70)

# STEP 1: Load bot (like "Load Bot" button)
print("\n[STEP 1] Loading bot (simulating 'Load Bot' button)...")
try:
    tester = InteractiveTester('c:/Users/miles/OneDrive/Documents/bot')
    print("[OK] Bot loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load bot: {e}")
    sys.exit(1)

# STEP 2: Send message (like typing in GUI and clicking Enter)
print("\n[STEP 2] Sending command (simulating user typing '!planegame')...")
try:
    # This simulates clicking enter after typing !planegame
    responses = tester.test_message('!planegame')
    print(f"[OK] test_message() returned {len(responses)} responses")
    print(f"[OK] message_responses has {len(tester.message_responses)} messages")
except Exception as e:
    print(f"[ERROR] Failed to send message: {e}")
    sys.exit(1)

# STEP 3: Process responses (like the GUI's display loop)
print("\n[STEP 3] Processing responses (simulating GUI display loop)...")

if not tester.message_responses:
    print("[ERROR] No messages in message_responses!")
    sys.exit(1)

message_count = 0
image_count = 0

for i, msg_resp in enumerate(tester.message_responses):
    print(f"\n  Response {i}:")
    
    if not isinstance(msg_resp, dict):
        print(f"    [ERROR] Response is not a dict: {type(msg_resp)}")
        continue
    
    message_count += 1
    
    # Display text (like GUI's display_message)
    msg_text = msg_resp.get('text', '')
    if msg_text:
        print(f"    [TEXT] Message present ({len(msg_text)} chars)")
    
    # Check for attachments (like GUI's send_message loop)
    if 'attachments' not in msg_resp:
        print(f"    [NO ATTACHMENTS]")
        continue
    
    if not msg_resp['attachments']:
        print(f"    [EMPTY ATTACHMENTS LIST]")
        continue
    
    print(f"    [ATTACHMENTS] {len(msg_resp['attachments'])} attachment(s)")
    
    for att_idx, attachment in enumerate(msg_resp['attachments']):
        print(f"      Attachment {att_idx}:")
        
        att_type = attachment.get('type', 'unknown')
        print(f"        - Type: {att_type}")
        
        if att_type != 'image':
            print(f"        - Skipping (not an image)")
            continue
        
        url = attachment.get('url', '')
        if not url:
            print(f"        - ERROR: No URL in attachment!")
            continue
        
        print(f"        - URL: {url[:60]}...")
        
        is_local = attachment.get('is_local_file', False)
        print(f"        - Is Local: {is_local}")
        
        # STEP 4: Try to download/load the image (like display_image does)
        print(f"        - Attempting to load image...")
        
        try:
            if is_local:
                print(f"          Loading from local file...")
                try:
                    img = Image.open(url)
                    print(f"          [OK] Loaded local image: {img.size}")
                    image_count += 1
                except Exception as e:
                    print(f"          [ERROR] Failed to load local file: {e}")
            else:
                print(f"          Downloading from URL...")
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        image_data = response.read()
                    img = Image.open(BytesIO(image_data))
                    print(f"          [OK] Downloaded and opened image: {img.size}")
                    image_count += 1
                except urllib.error.HTTPError as he:
                    print(f"          [ERROR] HTTP Error: {he.code} {he.reason}")
                except urllib.error.URLError as ue:
                    print(f"          [ERROR] URL Error: {ue.reason}")
                except Exception as e:
                    print(f"          [ERROR] Failed to download: {e}")
        except Exception as e:
            print(f"        [ERROR] Exception while processing attachment: {e}")

# FINAL REPORT
print("\n" + "=" * 70)
print("TEST RESULTS:")
print(f"  Messages processed: {message_count}")
print(f"  Images successfully loaded: {image_count}")

if image_count > 0:
    print("\n[SUCCESS] The GUI SHOULD be displaying the image!")
    print("If you're not seeing an image in the GUI, check:")
    print("  1. Is the GUI window actually showing?")
    print("  2. Did you wait long enough for the image to load?")
    print("  3. Are there any error messages in the console?")
else:
    print("\n[FAILURE] No images were processed!")
    print("Possible causes:")
    print("  1. Patches not being applied")
    print("  2. Images not being captured")
    print("  3. Invalid URLs")

print("=" * 70)

#!/usr/bin/env python3
"""Test that images are captured and would be displayed in GUI."""
import sys, os, time, warnings
sys.path.insert(0, 'src')
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

print('=== Bot Startup ===')
bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'
tester = InteractiveTester(bot_path)
print('[OK] Bot loaded')
print()

print('=== Sending !planegame ===')
tester.sent_messages.clear()
tester.message_responses.clear()

tester.test_message('!planegame')
print('[SENT] Game command')
print('[INFO] Waiting 45 seconds for pool to build and image to be captured...')
print()

# Simulate GUI auto-refresh every 2 seconds
for countdown in range(45, 0, -2):
    time.sleep(2)
    
    # Check for images (simulating GUI auto-refresh)
    latest_image = None
    if tester.message_responses:
        for response in reversed(tester.message_responses):
            if 'attachments' in response:
                for att in response['attachments']:
                    if att.get('type') == 'image':
                        latest_image = att.get('url', '')
                        break
            if latest_image:
                break
    
    if latest_image:
        print(f'[SUCCESS] Image captured after {45-countdown}s:')
        print(f'          {latest_image[:100]}...')
        print()
        print('=== Result ===')
        print(f'Total messages: {len(tester.sent_messages)}')
        msg1 = tester.sent_messages[0].encode('ascii', 'ignore').decode('ascii')[:70]
        print(f'  1. {msg1}...')
        if len(tester.sent_messages) > 1:
            msg2 = tester.sent_messages[1].encode('ascii', 'ignore').decode('ascii')[:70]
            print(f'  2. {msg2}...')
        print()
        print('[PASS] Game image would appear in GUI Image Preview area')
        break
    elif countdown == 5:
        print(f'[INFO] {countdown}s remaining...')
else:
    print('[FAIL] No image captured after 45 seconds')

#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import os, time, warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

print('=== Bot Startup ===')
start = time.time()
bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'
tester = InteractiveTester(bot_path)
startup_time = time.time() - start
print(f'Startup: {startup_time:.1f}s')
print()

print('=== Test !planegame ===')
responses = tester.test_message('!planegame')
if responses:
    # Get text without emoji
    msg_text = responses[0].encode('ascii', 'ignore').decode('ascii')[:50]
    print(f'Sent: {msg_text}')
else:
    print('Sent: (none)')
time.sleep(30)
print()

print('=== Results ===')
print(f'Messages: {len(tester.sent_messages)}')
for i, msg in enumerate(tester.sent_messages, 1):
    preview = msg.encode('ascii', 'ignore').decode('ascii')[:50]
    print(f'  {i}. {preview}')

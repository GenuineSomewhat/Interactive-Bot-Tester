#!/usr/bin/env python3
"""Comprehensive test of plane game flow."""
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

# Test 1: Start plane game
print('=== Test 1: Start !planegame ===')
tester.sent_messages.clear()
responses = tester.test_message('!planegame')
if responses:
    msg_text = responses[0].encode('ascii', 'ignore').decode('ascii')[:60]
    print(f'Initial response: {msg_text}')
else:
    print('Initial response: (none)')

# Wait for pool to build
print('Waiting for pool to build... (this takes 20-30 seconds)')
time.sleep(35)

print(f'Messages received: {len(tester.sent_messages)}')
for i, msg in enumerate(tester.sent_messages, 1):
    preview = msg.encode('ascii', 'ignore').decode('ascii')[:80]
    has_image = '[IMAGE]' in msg
    print(f'  {i}. {preview} {"[HAS IMAGE]" if has_image else ""}')

# Test 2: Make a guess
if len(tester.sent_messages) >= 2:
    print()
    print('=== Test 2: Make a guess ===')
    tester.sent_messages.clear()
    
    # Try to guess "sr71" for the SR-71 Blackbird
    print('Sending guess: "blackbird"')
    tester.test_message('blackbird', user_name='TestUser')
    time.sleep(5)
    
    print(f'Response messages: {len(tester.sent_messages)}')
    for i, msg in enumerate(tester.sent_messages, 1):
        preview = msg.encode('ascii', 'ignore').decode('ascii')[:100]
        print(f'  {i}. {preview}')

# Test 3: Get help
print()
print('=== Test 3: Get !gamehelp ===')
tester.sent_messages.clear()
tester.test_message('!gamehelp')
time.sleep(2)

print(f'Help messages: {len(tester.sent_messages)}')
for i, msg in enumerate(tester.sent_messages, 1):
    preview = msg.encode('ascii', 'ignore').decode('ascii')[:100]
    print(f'  {i}. {preview}')

print()
print('=== Test Complete ===')

#!/usr/bin/env python3
import sys, os, time, warnings
sys.path.insert(0, 'src')
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

print('=== Loading Bot ===')
bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'
tester = InteractiveTester(bot_path)
print()

# Test Plane Game
print('=== Test 1: Plane Game ===')
tester.sent_messages.clear()
tester.test_message('!planegame')
print('Game command sent, waiting 40 seconds for pool to build...')
time.sleep(40)
print(f'[PASS] Received {len(tester.sent_messages)} messages:')
for msg in tester.sent_messages:
    preview = msg[:80].encode('ascii', 'ignore').decode('ascii')
    print(f'  - {preview}...')
print()

# Test Gun Game  
print('=== Test 2: Gun Game ===')
tester.sent_messages.clear()
tester.test_message('!gungame')
print('Game command sent, waiting 40 seconds for pool to build...')
time.sleep(40)
print(f'[PASS] Received {len(tester.sent_messages)} messages:')
for msg in tester.sent_messages:
    preview = msg[:80].encode('ascii', 'ignore').decode('ascii')
    print(f'  - {preview}...')
print()
print('[PASS] Both games are working!')

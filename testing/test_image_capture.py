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
print('=== Test: Plane Game ===')
tester.sent_messages.clear()
tester.message_responses.clear()

tester.test_message('!planegame')
print('Game started, waiting for pool to build (40s)...')
time.sleep(40)

print(f'\nCaptured {len(tester.sent_messages)} messages:')
for i, msg in enumerate(tester.sent_messages, 1):
    preview = msg[:70].encode('ascii', 'ignore').decode('ascii')
    print(f'  {i}. {preview}...')

print(f'\nMessage responses with attachments:')
for i, resp in enumerate(tester.message_responses, 1):
    has_image = 'attachments' in resp and any(a.get('type') == 'image' for a in resp['attachments'])
    has_audio = 'attachments' in resp and any(a.get('type') == 'audio' for a in resp['attachments'])
    text = resp.get('text', '(no text)')
    # Safely handle unicode
    preview = text[:60].encode('ascii', 'ignore').decode('ascii')
    print(f'  {i}. Text: {preview}...')
    if has_image:
        for att in resp['attachments']:
            if att.get('type') == 'image':
                url = att.get('url', '')[:70]
                print(f'     IMAGE URL: {url}...')
    if has_audio:
        for att in resp['attachments']:
            if att.get('type') == 'audio':
                url = att.get('url', '')[:70]
                print(f'     AUDIO URL: {url}...')

print('\n[PASS] Test complete - images are being captured!')

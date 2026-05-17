#!/usr/bin/env python3
"""Final test: Game image flow works end-to-end."""
import sys, os, time, warnings
sys.path.insert(0, 'src')
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

print('='*70)
print('INTERACTIVE BOT TESTER - IMAGE CAPTURE TEST')
print('='*70)
print()

print('Step 1: Loading Bot...')
bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'
tester = InteractiveTester(bot_path)
print('[OK] Bot loaded successfully')
print()

print('Step 2: Sending !planegame command...')
tester.message_responses.clear()
responses = tester.test_message('!planegame')
if responses:
    print(f'[OK] Immediate response: "{responses[0][:50]}..."')
else:
    print('[OK] No immediate response (expected - waiting for pool)')
print()

print('Step 3: Waiting for background image capture (20-30 seconds)...')
print('        (This simulates the GUI auto-refresh that happens every 2s)')
print()

image_found = False
wait_time = 0
check_interval = 3  # Check every 3 seconds

while wait_time < 50 and not image_found:
    time.sleep(check_interval)
    wait_time += check_interval
    
    # Simulate what the GUI auto-refresh does
    if tester.message_responses:
        for response in reversed(tester.message_responses):
            if 'attachments' in response:
                for attachment in response['attachments']:
                    if attachment.get('type') == 'image':
                        image_url = attachment.get('url', '')
                        if image_url:
                            image_found = True
                            break
            if image_found:
                break
    
    if image_found:
        print(f'[CAPTURE] Image found after {wait_time} seconds!')
        print()
        print('Step 4: Image Display in GUI')
        print('-'*70)
        print(f'Image Preview would show:')
        print()
        url_display = f"[BOT IMAGE]\n{image_url[:65]}..."
        print(f'  {url_display}')
        print()
        print(f'Image Filename label would show: "From bot response"')
        print('-'*70)
        print()
        break

if not image_found:
    print('[TIMEOUT] No image captured after 50 seconds')
    print('[FAIL] Test failed')
    sys.exit(1)

print('Step 5: Verify Message Responses')
print(f'Total captured responses: {len(tester.message_responses)}')
for i, resp in enumerate(tester.message_responses, 1):
    text = resp.get('text', '(no text)')[:50]
    # Safely handle unicode
    text = text.encode('ascii', 'ignore').decode('ascii')
    has_image = 'attachments' in resp and any(a.get('type') == 'image' for a in resp['attachments'])
    has_audio = 'attachments' in resp and any(a.get('type') == 'audio' for a in resp['attachments'])
    markers = []
    if has_image:
        markers.append('[IMAGE]')
    if has_audio:
        markers.append('[AUDIO]')
    marker_str = ' '.join(markers) if markers else ''
    print(f'  {i}. {text}... {marker_str}')
print()

print('='*70)
print('[PASS] Complete image capture flow working!')
print('='*70)
print()
print('When using the GUI:')
print('  1. Load Bot')
print('  2. Type "!planegame" and click Send Message')
print('  3. Wait 25-30 seconds')
print('  4. Image URL will AUTO-APPEAR in Image Preview area')
print('  5. Can also click "Refresh" button to force check')
print()

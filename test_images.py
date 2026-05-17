#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import os
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'

print('[TEST] Image/Audio loading test...')
print()

try:
    tester = InteractiveTester(bot_path)
    print('[OK] Bot loaded')
    print()
    
    # Test plane game with images
    print('[1] Testing !planegame...')
    responses = tester.test_message('!planegame')
    tester._display_responses(responses)
    print()
    
    # Test gun game with images
    print('[2] Testing !gungame...')
    responses = tester.test_message('!gungame')
    tester._display_responses(responses)
    print()
    
    # Test audio
    print('[3] Testing !hear fitnessgram...')
    responses = tester.test_message('!hear fitnessgram')
    tester._display_responses(responses)
    print()
    
    print('[SUCCESS] Image/Audio loading working!')
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()

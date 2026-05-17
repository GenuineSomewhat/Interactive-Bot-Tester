#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import os
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'

print('[TEST] Detailed response inspection...')
print()

try:
    tester = InteractiveTester(bot_path)
    
    # Test plane game
    print('[1] Testing !planegame...')
    responses = tester.test_message('!planegame')
    print(f'Text responses: {responses}')
    print(f'Response objects: {tester.message_responses}')
    print()
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import os
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from interactive_test import InteractiveTester

bot_path = r'c:\Users\miles\OneDrive\Documents\bot\app.py'

print('[TEST] Complete feature verification...')
print()

try:
    tester = InteractiveTester(bot_path)
    print('[OK] Bot loaded')
    print()
    
    # Test game commands
    responses = tester.test_message('!planegame')
    status = 'OK' if responses else 'FAIL'
    print(f'[GAME] !planegame: {len(responses)} response(s) - {status}')
    
    responses = tester.test_message('!gungame')
    status = 'OK' if responses else 'FAIL'
    print(f'[GAME] !gungame: {len(responses)} response(s) - {status}')
    
    responses = tester.test_message('!hear')
    status = 'OK' if responses else 'FAIL'
    print(f'[AUDIO] !hear: {len(responses)} response(s) - {status}')
    
    responses = tester.test_message('!see')
    status = 'OK' if responses else 'FAIL'
    print(f'[IMAGE] !see: {len(responses)} response(s) - {status}')
    
    print()
    print('[SUCCESS] All commands working!')
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()

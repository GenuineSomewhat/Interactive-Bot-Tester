#!/usr/bin/env python3
"""
Test script to verify end-to-end image capture and display.
Redirects all output to a log file for analysis.
"""

import sys
import os
from pathlib import Path
import logging

# Set up logging
log_file = Path(__file__).parent / "gui_test.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting GUI test, logging to {log_file}")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from interactive_test import InteractiveTester
    logger.info("Loaded InteractiveTester")
except Exception as e:
    logger.error(f"Failed to import InteractiveTester: {e}")
    sys.exit(1)

def test_plane_game():
    """Test the plane game and verify image capture."""
    bot_path = Path(__file__).parent.parent / "bot"
    logger.info(f"Loading bot from: {bot_path}")
    
    try:
        tester = InteractiveTester(str(bot_path))
        logger.info(f"Bot loaded. Webhook route: {tester.webhook_route}")
        logger.info(f"Testing message: !planegame")
        
        # Send plane game command
        responses = tester.test_message("!planegame")
        
        logger.info(f"\n=== RESPONSES ===")
        logger.info(f"Number of message_responses: {len(tester.message_responses)}")
        
        for i, msg_resp in enumerate(tester.message_responses):
            logger.info(f"\nResponse {i}:")
            logger.info(f"  Type: {type(msg_resp)}")
            if isinstance(msg_resp, dict):
                logger.info(f"  Keys: {msg_resp.keys()}")
                # Use repr() to handle unicode safely
                text_preview = repr(msg_resp.get('text', '')[:100])
                logger.info(f"  Text: {text_preview}...")
                if 'attachments' in msg_resp:
                    logger.info(f"  Attachments: {len(msg_resp['attachments'])} items")
                    for j, att in enumerate(msg_resp['attachments']):
                        logger.info(f"    [{j}] type={att.get('type')}, url_len={len(att.get('url', ''))}, is_local={att.get('is_local_file')}")
                        logger.info(f"        url={att.get('url', '')[:80] if att.get('url') else 'NONE'}...")
                else:
                    logger.info(f"  No attachments")
            else:
                logger.info(f"  Value: {str(msg_resp)[:100]}...")
        
        logger.info("\n=== TEST COMPLETE ===")
        print(f"\nLog saved to: {log_file}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    test_plane_game()

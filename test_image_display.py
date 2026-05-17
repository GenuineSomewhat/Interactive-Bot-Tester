#!/usr/bin/env python3
"""
Test script to verify image display in GUI.
"""

import sys
import os
from pathlib import Path
from io import BytesIO
import urllib.request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("ERROR: Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

def test_image_download(url):
    """Test downloading and converting an image from URL."""
    print(f"\n[TEST] Attempting to download image from: {url[:80]}...")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[TEST] Got response status: {response.status}")
            image_data = response.read()
            print(f"[TEST] Downloaded {len(image_data)} bytes")
        
        image = Image.open(BytesIO(image_data))
        print(f"[TEST] Image opened successfully: {image.size}, format: {image.format}")
        
        # Try resize
        image.thumbnail((400, 300), Image.Resampling.LANCZOS)
        print(f"[TEST] Resized to: {image.size}")
        
        return True
    except Exception as e:
        print(f"[TEST] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test URLs from the bot output
    test_urls = [
        "https://upload.wikimedia.org/wikipedia/commons/c/cc/Lockheed_C-130_Hercules_JP-7729.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/a/a0/CH-47_as.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/1/1e/F-22_Rap.jpg",
    ]
    
    print("=" * 70)
    print("IMAGE DOWNLOAD TEST")
    print("=" * 70)
    
    for url in test_urls:
        if test_image_download(url):
            print("[SUCCESS] Image downloaded and processed successfully")
        else:
            print("[FAILED] Could not download/process image")

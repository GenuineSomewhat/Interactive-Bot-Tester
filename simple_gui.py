#!/usr/bin/env python3
"""
Simplified Interactive Bot Tester GUI - Fixed for visibility
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
from pathlib import Path
from threading import Thread
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from interactive_test import InteractiveTester

try:
    from PIL import Image, ImageTk
    from io import BytesIO
    import urllib.request
    HAS_PIL = True
except:
    HAS_PIL = False


class SimpleBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Tester - Bot Responses")
        self.root.geometry("800x600")
        
        # Make window visible and on top
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
        self.tester = None
        self.photo_images = []
        
        self.setup()
        
    def setup(self):
        """Create simple GUI"""
        # Status
        self.status = tk.Label(self.root, text="Not loaded", bg="#ffcccc", fg="black", font=("Arial", 12, "bold"))
        self.status.pack(fill=tk.X, padx=5, pady=5)
        
        # Button frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(btn_frame, text="LOAD BOT", command=self.load_bot, bg="green", fg="white", font=("Arial", 12, "bold"), width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="TEST GAME", command=self.test_game, bg="blue", fg="white", font=("Arial", 12, "bold"), width=20).pack(side=tk.LEFT, padx=5)
        
        # Chat display
        tk.Label(self.root, text="Responses:", font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=5)
        self.chat = scrolledtext.ScrolledText(self.root, height=20, font=("Courier", 9), bg="#f0f0f0")
        self.chat.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log("Ready. Click 'LOAD BOT' to start.")
    
    def log(self, msg):
        """Add message to display"""
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, msg + "\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
        self.root.update()
    
    def load_bot(self):
        """Load bot"""
        self.log("\n[LOADING BOT...]")
        self.status.config(text="Loading...", bg="#ffff99")
        self.root.update()
        
        try:
            bot_path = "c:/Users/miles/OneDrive/Documents/bot"
            self.tester = InteractiveTester(bot_path)
            self.status.config(text="Bot loaded successfully!", bg="#99ff99")
            self.log("[OK] Bot loaded!")
            self.log("Click 'TEST GAME' to run plane game")
        except Exception as e:
            self.status.config(text=f"Failed: {e}", bg="#ff9999")
            self.log(f"[ERROR] {e}")
    
    def test_game(self):
        """Test plane game in background"""
        if not self.tester:
            messagebox.showerror("Error", "Load bot first!")
            return
        
        self.log("\n[TESTING PLANE GAME - waiting up to 60 seconds...]")
        self.log("(This fetches aircraft images from Wikipedia, which is slow)")
        
        def run():
            try:
                responses = self.tester.test_message("!planegame")
                self.log(f"\n[OK] Got {len(self.tester.message_responses)} responses")
                
                # Display responses
                for i, resp in enumerate(self.tester.message_responses):
                    self.log(f"\n--- Response {i} ---")
                    self.log(f"Type: {type(resp).__name__}")
                    
                    if isinstance(resp, dict):
                        self.log(f"Keys: {list(resp.keys())}")
                        
                        if 'text' in resp:
                            text = resp['text']
                            preview = text[:100] if len(text) > 100 else text
                            self.log(f"Text: {preview}")
                        
                        if 'attachments' in resp:
                            atts = resp['attachments']
                            self.log(f"Attachments: {len(atts)}")
                            for j, att in enumerate(atts):
                                self.log(f"  [{j}] Type: {att.get('type')}")
                                if att.get('type') == 'image':
                                    url = att.get('url', 'NO URL')
                                    self.log(f"      URL: {url[:70]}...")
                                    self.display_image(url)
                        else:
                            self.log("No attachments")
            except Exception as e:
                self.log(f"[ERROR] {e}")
                traceback.print_exc()
        
        thread = Thread(target=run, daemon=True)
        thread.start()
    
    def display_image(self, url):
        """Download and display image in chat"""
        if not HAS_PIL:
            self.log("    (PIL not installed)")
            return
        
        def download_and_show():
            try:
                self.log("    [Downloading image...]")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    img_data = response.read()
                img = Image.open(BytesIO(img_data))
                original_size = img.size
                self.log(f"    [OK] Downloaded {original_size[0]}x{original_size[1]} image")
                
                # Resize image to fit in text widget (max 600 width, maintain aspect)
                max_width = 600
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.photo_images.append(photo)  # Keep reference
                
                # Insert into text widget
                self.chat.config(state=tk.NORMAL)
                self.chat.image_create(tk.END, image=photo)
                self.chat.insert(tk.END, "\n")
                self.chat.config(state=tk.DISABLED)
                self.chat.see(tk.END)
                self.root.update()
                
                self.log(f"    [✓] Image displayed ({img.width}x{img.height})")
            except Exception as e:
                self.log(f"    [ERROR loading image: {e}]")
        
        # Run in background thread to not block GUI
        thread = Thread(target=download_and_show, daemon=True)
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    gui = SimpleBotGUI(root)
    root.mainloop()

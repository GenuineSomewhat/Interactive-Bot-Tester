"""
Simple GUI for interactive bot tester with image and audio support.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import os
import sys
import traceback
from pathlib import Path
from threading import Thread
from io import BytesIO
import urllib.request
import urllib.error
import subprocess

sys.path.insert(0, str(Path(__file__).parent))
from interactive_test import InteractiveTester

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class SimpleBotTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Bot Tester")
        self.root.geometry("900x700")
        
        self.tester = None
        self.bot_path = None
        self.photo_images = []  # Store image references to prevent garbage collection
        
        print("[GUI INIT] Starting UI setup...")
        self.setup_ui()
        print("[GUI INIT] UI setup complete - GUI is ready")
    
    def setup_ui(self):
        """Create the GUI layout."""
        # Top frame - controls
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=60)
        top_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=10)
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="Bot Tester", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(top_frame, text="Load Bot", command=self.load_bot, width=12, relief=tk.RAISED, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Reset State", command=self.reset_state, width=12, relief=tk.RAISED, bg="#FFC107", fg="black").pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(top_frame, text="No bot loaded", font=("Arial", 10), bg="#f0f0f0", fg="#666")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display
        chat_label = tk.Label(content_frame, text="Bot Responses:", font=("Arial", 11, "bold"), bg="white", fg="#333")
        chat_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Use Text widget for better image support
        self.chat_display = tk.Text(
            content_frame,
            height=18,
            font=("Courier", 9),
            bg="#f9f9f9",
            fg="#333",
            wrap=tk.WORD,
            relief=tk.SUNKEN,
            bd=1
        )
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(content_frame, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        
        self.chat_display.config(state=tk.DISABLED)
        
        # Input frame
        input_label = tk.Label(content_frame, text="Send Message:", font=("Arial", 11, "bold"), bg="white", fg="#333")
        input_label.pack(anchor=tk.W)
        
        input_frame = tk.Frame(content_frame, bg="white")
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.input_field = tk.Entry(input_frame, font=("Arial", 10), relief=tk.SUNKEN, bd=1)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        tk.Button(input_frame, text="Send", command=self.send_message, width=10, relief=tk.RAISED, bg="#2196F3", fg="white").pack(side=tk.LEFT)
        
        # Make input field focus
        self.input_field.focus()
    
    def load_bot(self):
        """Load a bot from a folder or file."""
        bot_path = filedialog.askdirectory(
            title="Select bot folder",
            initialdir=str(Path(__file__).parent.parent.parent / "bot")
        )
        
        if not bot_path:
            return
        
        try:
            # Safely display loading message
            try:
                self.display_message("[INFO] Loading bot...\n")
            except:
                print("[DEBUG] Could not display loading message")
            
            self.tester = InteractiveTester(bot_path)
            self.bot_path = bot_path
            self.status_label.config(text=f"Bot loaded: {Path(bot_path).name}")
            
            # Safely display success messages
            try:
                self.display_message(f"[SUCCESS] Bot loaded from {bot_path}\n")
                self.display_message(f"Webhook route: {self.tester.webhook_route}\n\n")
            except:
                print("[DEBUG] Could not display success messages")
            
            self.input_field.focus()
            self.photo_images = []  # Clear cached images
        except Exception as e:
            self.status_label.config(text="Failed to load bot")
            try:
                self.display_message(f"[ERROR] Failed to load bot: {e}\n")
                self.display_message(traceback.format_exc())
            except:
                print(f"[ERROR] Failed to load bot: {e}")
                import traceback
                traceback.print_exc()
    
    def send_message(self):
        """Send message to bot."""
        if not self.tester:
            messagebox.showwarning("Bot Not Loaded", "Please load a bot first.")
            return
        
        text = self.input_field.get().strip()
        if not text:
            return
        
        self.input_field.delete(0, tk.END)
        self.display_message(f"\n> {text}\n")
        
        # Show waiting message for games (they take 45+ seconds)
        is_game_cmd = any(cmd in text.lower() for cmd in ['!planegame', '!gungame', 'game', 'hard mode', 'refresh'])
        if is_game_cmd:
            self.display_message("[BOT] Loading game... (fetching aircraft from Wikipedia, this takes ~45 seconds)\n")
        
        # Run in thread to prevent GUI freeze
        def test():
            try:
                print(f"[TEST DEBUG] Sending message: {text}")
                responses = self.tester.test_message(text)
                print(f"[TEST DEBUG] test_message() returned {len(responses)} responses")
                print(f"[TEST DEBUG] message_responses has {len(self.tester.message_responses)} items")
                
                # Display messages with their attachments from message_responses
                if self.tester.message_responses:
                    print(f"[TEST DEBUG] Processing {len(self.tester.message_responses)} messages")
                    for i, msg_resp in enumerate(self.tester.message_responses, 1):
                        print(f"[TEST DEBUG] Message {i}: type={type(msg_resp)}, keys={list(msg_resp.keys()) if isinstance(msg_resp, dict) else 'N/A'}")
                        if isinstance(msg_resp, dict):
                            # Display text content
                            msg_text = msg_resp.get('text', '')
                            if msg_text:
                                print(f"[TEST DEBUG] Displaying text for message {i}")
                                self.display_message(f"[{i}] {msg_text}\n")
                            
                            # Display image if present
                            if 'attachments' in msg_resp and msg_resp['attachments']:
                                print(f"[TEST DEBUG] Message {i} has {len(msg_resp['attachments'])} attachments")
                                for att_idx, attachment in enumerate(msg_resp['attachments']):
                                    att_type = attachment.get('type', 'unknown')
                                    print(f"[TEST DEBUG] Attachment {att_idx}: type={att_type}")
                                    if att_type == 'image' and attachment.get('url'):
                                        is_local = attachment.get('is_local_file', False)
                                        print(f"[TEST DEBUG] Displaying image: url={attachment['url'][:60]}..., is_local={is_local}")
                                        self.display_image(attachment['url'], is_local_file=is_local)
                                    elif att_type == 'audio' and attachment.get('url'):
                                        is_local = attachment.get('is_local_file', False)
                                        duration = attachment.get('duration', 7)
                                        print(f"[TEST DEBUG] Calling display_audio for: {attachment['url'][:60]}...")
                                        self.display_audio(attachment['url'], is_local_file=is_local, duration=duration)
                            else:
                                print(f"[TEST DEBUG] Message {i} has no attachments")
                        else:
                            # Fallback for non-dict responses
                            self.display_message(f"[{i}] {msg_resp}\n")
                else:
                    print(f"[TEST DEBUG] message_responses is empty!")
                    self.display_message("(no response)\n")
                print(f"[TEST DEBUG] Finished displaying all messages")
            except Exception as e:
                print(f"[TEST ERROR] {e}")
                import traceback
                traceback.print_exc()
                self.display_message(f"[ERROR] {e}\n")
        
        thread = Thread(target=test, daemon=True)
        thread.start()
    
    def display_image(self, image_path, is_local_file=False):
        """Display an image from file path or URL."""
        if not HAS_PIL:
            self.display_message(f"\n[BOT IMAGE]\n{image_path}\n")
            self.display_message("(Install Pillow for inline image display: pip install Pillow)\n")
            return
        
        try:
            print(f"[GUI DEBUG display_image] Starting image load: path={image_path[:60] if image_path else 'NONE'}..., is_local={is_local_file}")
            self.display_message("\n[Loading image...]\n")
            
            if is_local_file:
                # Load directly from local file
                print(f"[GUI DEBUG display_image] Attempting local file load: {image_path}")
                if not os.path.exists(image_path):
                    print(f"[GUI DEBUG display_image] File not found: {image_path}")
                    self.display_message(f"\n[BOT IMAGE - LOCAL FILE NOT FOUND]\n{image_path}\n")
                    return
                image = Image.open(image_path)
                print(f"[GUI DEBUG display_image] Successfully opened local image: {image.size}")
            else:
                # Download image from URL with User-Agent header (required by Wikimedia)
                print(f"[GUI DEBUG display_image] Attempting URL download from: {image_path[:80] if image_path else 'NONE'}...")
                try:
                    req = urllib.request.Request(image_path, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        print(f"[GUI DEBUG display_image] Got response status: {response.status}")
                        image_data = response.read()
                        print(f"[GUI DEBUG display_image] Downloaded {len(image_data)} bytes")
                    image = Image.open(BytesIO(image_data))
                    print(f"[GUI DEBUG display_image] Successfully opened URL image: {image.size}")
                except urllib.error.HTTPError as he:
                    print(f"[GUI DEBUG display_image] HTTP Error: {he.code} {he.reason}")
                    self.display_message(f"\n[BOT IMAGE - HTTP ERROR {he.code}]\n{image_path}\n")
                    return
                except urllib.error.URLError as ue:
                    print(f"[GUI DEBUG display_image] URL Error: {ue.reason}")
                    self.display_message(f"\n[BOT IMAGE - DOWNLOAD ERROR]\n{image_path}\nError: {ue.reason}\n")
                    return
            
            # Resize to fit nicely in display (max 400x300)
            max_width = 400
            max_height = 300
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            print(f"[GUI DEBUG display_image] Resized to: {image.size}")
            
            # Convert to PhotoImage using ImageTk
            photo = ImageTk.PhotoImage(image)
            print(f"[GUI DEBUG display_image] Created PhotoImage")
            
            # Store reference to prevent garbage collection
            self.photo_images.append(photo)
            
            # Insert image into text widget
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.image_create(tk.END, image=photo)
            self.chat_display.insert(tk.END, "\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.root.update()
            print(f"[GUI DEBUG display_image] Image displayed successfully")
        
        except Exception as e:
            print(f"[GUI DEBUG display_image] Error: {e}")
            import traceback
            traceback.print_exc()
            self.display_message(f"\n[BOT IMAGE]\n{image_path}\n[Error loading: {e}]\n")
    
    def display_audio(self, audio_path, is_local_file=False, duration=7):
        """Display and open audio file with system player."""
        try:
            print(f"[GUI DEBUG display_audio] Called with: path={audio_path}, is_local={is_local_file}, duration={duration}")
            
            filename = os.path.basename(audio_path)
            self.display_message(f"\n[🔊 Audio: {filename} ({duration}s)]\n")
            
            # Check if file exists
            if is_local_file:
                if not os.path.exists(audio_path):
                    print(f"[GUI DEBUG display_audio] File not found: {audio_path}")
                    self.display_message(f"[ERROR] Local audio file not found: {audio_path}\n")
                    return
                display_path = os.path.basename(audio_path)
            else:
                display_path = audio_path
            
            self.display_message(f"📁 {display_path}\n")
            
            if not is_local_file:
                print(f"[GUI DEBUG display_audio] URL audio not supported")
                self.display_message("[INFO] Audio playback from URLs not yet supported (file-based only)\n\n")
                return
            
            # Open audio file with system player in background thread
            def play_audio():
                try:
                    print(f"[GUI DEBUG play_audio] Opening audio: {audio_path}")
                    print(f"[GUI DEBUG play_audio] File exists: {os.path.exists(audio_path)}")
                    
                    # Open with system default player
                    if sys.platform == 'win32':
                        os.startfile(audio_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', audio_path])
                    else:
                        subprocess.run(['xdg-open', audio_path])
                    
                    self.display_message("[▶ Opening in system player...]\n")
                    
                    # Wait approximate duration
                    import time
                    time.sleep(duration + 1)
                    
                    self.display_message("[✓ Done]\n\n")
                    print(f"[GUI DEBUG play_audio] Audio opened")
                except Exception as e:
                    print(f"[GUI DEBUG play_audio] Error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.display_message(f"[ERROR] Could not open audio: {e}\n\n")
            
            thread = Thread(target=play_audio, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"[GUI DEBUG display_audio] Error: {e}")
            traceback.print_exc()
            self.display_message(f"\n[AUDIO ERROR]\n{audio_path}\n[Error: {e}]\n")
        
        except Exception as e:
            self.display_message(f"\n[AUDIO ERROR]\n{audio_path}\n[Error: {e}]\n")
    
    def reset_state(self):
        """Reset bot state."""
        if not self.tester:
            messagebox.showwarning("Bot Not Loaded", "Please load a bot first.")
            return
        
        try:
            for state_dict in self.tester.bot_module.__dict__.values():
                if isinstance(state_dict, dict):
                    state_dict.clear()
            self.display_message("[INFO] Bot state cleared\n")
        except Exception as e:
            self.display_message(f"[ERROR] Failed to reset state: {e}\n")
    
    def display_message(self, text):
        """Add text to chat display."""
        try:
            if not hasattr(self, 'chat_display') or not self.chat_display:
                print(f"[DEBUG] chat_display not available, queuing message")
                return
            
            # Use try-except in case widget was destroyed
            try:
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, text)
                self.chat_display.see(tk.END)
                self.chat_display.config(state=tk.DISABLED)
            except tk.TclError:
                print(f"[DEBUG] TclError updating chat_display, widget may be destroyed")
                return
            
            # Safely update root
            try:
                self.root.update()
            except tk.TclError:
                print(f"[DEBUG] TclError updating root")
                pass
        except Exception as e:
            print(f"[DEBUG] display_message error: {e}")


def main():
    try:
        root = tk.Tk()
        gui = SimpleBotTesterGUI(root)
        print("[GUI] Starting mainloop...")
        root.mainloop()
        print("[GUI] Mainloop finished normally")
    except Exception as e:
        print(f"[GUI FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

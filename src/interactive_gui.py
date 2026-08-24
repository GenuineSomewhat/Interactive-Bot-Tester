"""
Simple GUI for interactive bot tester with image and audio support.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk
import os
import sys
import traceback
from pathlib import Path
from threading import Thread
from io import BytesIO, StringIO
import urllib.request
import urllib.error
import subprocess
import time

sys.path.insert(0, str(Path(__file__).parent))
from interactive_test import InteractiveTester

try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

if sys.stdout:
    print("[STARTUP] interactive_gui.py starting...")

class TerminalCapture:
    """Captures stdout/stderr and redirects to both console and GUI."""
    def __init__(self, original_stdout):
        self.terminal_widget = None  # Set later after GUI is initialized
        self.original_stdout = original_stdout
        self.buffer = []
    
    def set_terminal_widget(self, widget):
        """Set the terminal widget after GUI is initialized."""
        self.terminal_widget = widget
    
    def write(self, message):
        """Write message to both console and GUI terminal."""
        if not message:
            return
        
        # Try to write to original stdout
        try:
            if self.original_stdout and hasattr(self.original_stdout, 'write'):
                self.original_stdout.write(message)
                if hasattr(self.original_stdout, 'flush'):
                    self.original_stdout.flush()
        except:
            pass
        
        # Add to GUI terminal if initialized
        if self.terminal_widget and message.strip():
            try:
                self.terminal_widget.config(state=tk.NORMAL)
                self.terminal_widget.insert(tk.END, message)
                self.terminal_widget.see(tk.END)
                self.terminal_widget.config(state=tk.DISABLED)
            except:
                pass
    
    def flush(self):
        """Flush the stream."""
        try:
            if self.original_stdout and hasattr(self.original_stdout, 'flush'):
                self.original_stdout.flush()
        except:
            pass
    
    def isatty(self):
        """Return whether this is a tty."""
        return False


class BotTestTab:
    """Represents a single bot test tab with its own tester and UI."""
    def __init__(self, notebook, parent_gui):
        self.parent_gui = parent_gui
        self.tester = None  # Will be InteractiveTester instance when bot is loaded
        self.bot_path = None
        self.photo_images = []  # Store image references to prevent garbage collection
        
        # Create tab frame
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="[No Bot]")
        self.tab_index = notebook.index(self.frame)
        self.notebook = notebook
        
        # Chat display using Canvas for bubbles
        self.chat_canvas = tk.Canvas(
            self.frame,
            height=18,
            bg="#ffffff",
            highlightthickness=0
        )
        
        # Create scrollable frame inside canvas
        self.chat_frame = tk.Frame(self.chat_canvas, bg="#ffffff")
        self.chat_window = self.chat_canvas.create_window(0, 0, window=self.chat_frame, anchor="nw")
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self.frame, command=self.chat_canvas.yview)
        self.chat_canvas.config(yscrollcommand=scrollbar.set)
        
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        # Bind canvas resize to update scrollregion
        self.chat_canvas.bind("<Configure>", self._on_canvas_configure)
        self.chat_frame.bind("<Configure>", self._on_frame_configure)
    
    def _on_canvas_configure(self, event):
        """Update canvas scroll region when configured."""
        self.chat_canvas.itemconfig(self.chat_window, width=event.width)
    
    def _on_frame_configure(self, event):
        """Update scroll region when frame changes size."""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
    
    def _create_rounded_bubble_image(self, text, bg_color, text_color, is_system=False):
        """Create a PIL image with rounded corners for a message bubble."""
        if not HAS_PIL:
            return None
        
        # Parameters
        padding = 12
        line_height = 14
        max_width = 350 if not is_system else 300
        border_radius = 15
        
        # Split text into lines for sizing
        lines = text.split('\n')
        
        # Calculate size
        bubble_width = min(max(len(line) * 8 for line in lines) + padding * 2, max_width)
        bubble_height = len(lines) * line_height + padding * 2
        
        # Create image with white background
        img = Image.new('RGB', (bubble_width, bubble_height), '#ffffff')
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(0, 0), (bubble_width - 1, bubble_height - 1)],
            radius=border_radius,
            fill=bg_color,
            outline=None
        )
        
        # Draw text
        y_pos = padding
        for line in lines:
            draw.text((padding, y_pos), line, fill=text_color, font=None)
            y_pos += line_height
        
        return ImageTk.PhotoImage(img)
    
    def _create_message_bubble(self, text, is_bot=True, pfp_widget=None):
        """Create a styled message bubble widget."""
        # Check if this is a system message
        is_system = text.strip().startswith('[') and any(tag in text for tag in ['[INFO]', '[SUCCESS]', '[ERROR]', '[BOT]'])
        
        if is_system:
            # System message - centered, muted style
            bubble_frame = tk.Frame(self.chat_frame, bg="#ffffff")
            bubble_frame.pack(fill=tk.X, padx=10, pady=3)
            
            # Determine color based on type
            if '[SUCCESS]' in text:
                bg_color = (212, 237, 218)  # Light green
                text_color = (21, 87, 36)  # Dark green
            elif '[ERROR]' in text:
                bg_color = (248, 215, 218)  # Light red
                text_color = (114, 28, 36)  # Dark red
            elif '[BOT]' in text:
                bg_color = (255, 243, 205)  # Light yellow
                text_color = (133, 100, 4)  # Dark yellow
            else:
                bg_color = (226, 227, 229)  # Light gray
                text_color = (56, 61, 65)  # Dark gray
            
            # Create rounded bubble
            if HAS_PIL:
                photo = self._create_rounded_bubble_image(text, bg_color, text_color, is_system=True)
                if photo:
                    self.photo_images.append(photo)
                    label = tk.Label(bubble_frame, image=photo, bg="#ffffff", bd=0)
                    label.pack()
            else:
                # Fallback without PIL
                text_bubble = tk.Frame(bubble_frame, bg=self._color_to_hex(bg_color), relief=tk.FLAT, bd=0)
                text_bubble.pack(fill=tk.X, padx=(80, 80))
                
                label = tk.Label(
                    text_bubble,
                    text=text,
                    font=("Arial", 8),
                    bg=self._color_to_hex(bg_color),
                    fg=self._color_to_hex(text_color),
                    wraplength=400,
                    justify=tk.CENTER,
                    padx=8,
                    pady=4
                )
                label.pack(fill=tk.BOTH, expand=True)
        else:
            # Regular message - left or right aligned
            bubble_frame = tk.Frame(self.chat_frame, bg="#ffffff")
            bubble_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Inner bubble with colored background
            if is_bot:
                bubble_bg = (232, 232, 232)  # Light gray for bot
                text_color = (0, 0, 0)  # Black
            else:
                bubble_bg = (0, 122, 255)  # Blue for user
                text_color = (255, 255, 255)  # White
            
            # Create rounded bubble with PIL
            if HAS_PIL:
                photo = self._create_rounded_bubble_image(text, bubble_bg, text_color, is_system=False)
                if photo:
                    self.photo_images.append(photo)
                    
                    # If there's a PFP, add it first (bot only)
                    if pfp_widget and is_bot:
                        content_frame = tk.Frame(bubble_frame, bg="#ffffff")
                        content_frame.pack(fill=tk.X)
                        
                        pfp_frame = tk.Frame(content_frame, bg="#ffffff")
                        pfp_frame.pack(side=tk.LEFT, padx=(0, 8), pady=5)
                        pfp_widget.pack(in_=pfp_frame)
                        
                        img_label = tk.Label(content_frame, image=photo, bg="#ffffff", bd=0)
                        img_label.pack(side=tk.LEFT)
                    else:
                        # Right-align for user messages
                        if not is_bot:
                            align_frame = tk.Frame(bubble_frame, bg="#ffffff")
                            align_frame.pack(fill=tk.X)
                            img_label = tk.Label(align_frame, image=photo, bg="#ffffff", bd=0)
                            img_label.pack(side=tk.RIGHT, padx=(50, 0))
                        else:
                            img_label = tk.Label(bubble_frame, image=photo, bg="#ffffff", bd=0)
                            img_label.pack()
            else:
                # Fallback without PIL - old style frames
                if pfp_widget and is_bot:
                    content_frame = tk.Frame(bubble_frame, bg="#ffffff")
                    content_frame.pack(fill=tk.X)
                    
                    pfp_frame = tk.Frame(content_frame, bg="#ffffff")
                    pfp_frame.pack(side=tk.LEFT, padx=(0, 8), pady=5)
                    pfp_widget.pack(in_=pfp_frame)
                    
                    text_bubble = tk.Frame(content_frame, bg=self._color_to_hex(bubble_bg), relief=tk.FLAT, bd=0)
                    text_bubble.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                else:
                    if not is_bot:
                        align_frame = tk.Frame(bubble_frame, bg="#ffffff")
                        align_frame.pack(fill=tk.X)
                        
                        text_bubble = tk.Frame(align_frame, bg=self._color_to_hex(bubble_bg), relief=tk.FLAT, bd=0)
                        text_bubble.pack(side=tk.RIGHT, padx=(50, 0))
                    else:
                        text_bubble = tk.Frame(bubble_frame, bg=self._color_to_hex(bubble_bg), relief=tk.FLAT, bd=0)
                        text_bubble.pack(fill=tk.X)
                
                label = tk.Label(
                    text_bubble,
                    text=text,
                    font=("Arial", 9),
                    bg=self._color_to_hex(bubble_bg),
                    fg=self._color_to_hex(text_color),
                    wraplength=400,
                    justify=tk.LEFT,
                    padx=12,
                    pady=8
                )
                label.pack(fill=tk.BOTH, expand=True)
        
        return bubble_frame
    
    def _color_to_hex(self, rgb_tuple):
        """Convert RGB tuple to hex color."""
        return '#{:02x}{:02x}{:02x}'.format(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
    
    def clear_display(self):
        """Clear the chat display."""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.photo_images = []  # Clear cached images
    
    def update_tab_title(self):
        """Update tab title based on loaded bot."""
        if self.bot_path:
            title = Path(self.bot_path).name
        else:
            title = "[No Bot]"
        self.notebook.tab(self.tab_index, text=title)
    
    def display_message(self, text, is_bot=True):
        """Add text to chat display as a styled bubble."""
        try:
            if not hasattr(self, 'chat_frame') or not self.chat_frame:
                print(f"[DEBUG] chat_frame not available")
                return
            
            # Clean text
            text = text.strip()
            if not text:
                return
            
            # Create bubble
            self._create_message_bubble(text, is_bot=is_bot)
            
            # Scroll to bottom
            self.chat_canvas.yview_moveto(1.0)
            
            # Safely update root
            try:
                self.parent_gui.root.update()
            except tk.TclError:
                print(f"[DEBUG] TclError updating root")
                pass
        except Exception as e:
            print(f"[DEBUG] display_message error: {e}")


class SimpleBotTesterGUI:
    def __init__(self, root, initial_bot_path=None):
        self.root = root
        self.root.title("Interactive Bot Tester")
        self.root.geometry("900x800")
        
        # Set window icon if available
        try:
            # For PyInstaller bundled app, check bundled location first
            icon_loaded = False
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    print(f"[GUI INIT] Loaded bundled icon from: {icon_path}")
                    icon_loaded = True
            
            # Try other locations for development
            if not icon_loaded:
                icon_paths = [
                    'icon.ico',  # Current directory
                    os.path.join(os.path.dirname(__file__), '..', 'icon.ico'),  # Parent directory
                    os.path.join(os.getcwd(), 'icon.ico'),  # Working directory
                    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'icon.ico')),  # Absolute path
                ]
                
                for icon_path in icon_paths:
                    if os.path.exists(icon_path):
                        self.root.iconbitmap(icon_path)
                        print(f"[GUI INIT] Loaded icon from: {icon_path}")
                        icon_loaded = True
                        break
            
            if not icon_loaded:
                print(f"[GUI INIT] Icon not found")
        except Exception as e:
            print(f"[GUI INIT] Could not load icon: {e}")
        
        self.current_tab = None
        self.tabs = []  # List of BotTestTab objects
        self.terminal_widget = None  # Will be set in setup_ui
        self.original_stdout = sys.stdout
        
        print("[GUI INIT] Starting UI setup...")
        try:
            self.setup_ui()
        except Exception as e:
            print(f"[GUI ERROR] setup_ui failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # NOW set up stdout/stderr capture (AFTER setup_ui completes)
        self.terminal_capture = TerminalCapture(self.original_stdout)
        sys.stdout = self.terminal_capture
        sys.stderr = self.terminal_capture
        
        # Tell the capture where to send output
        self.terminal_capture.set_terminal_widget(self.terminal_widget)
        
        print("[GUI INIT] UI setup complete - GUI is ready")
        
        # Load initial bot if provided via command-line argument
        if initial_bot_path and os.path.isdir(initial_bot_path):
            self.root.after(100, lambda: self.load_bot_from_path(initial_bot_path))
    
    def setup_ui(self):
        """Create the GUI layout with tabs."""
        try:
            # Top frame - controls
            top_frame = tk.Frame(self.root, bg="#f0f0f0", height=60)
            top_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=10)
            top_frame.pack_propagate(False)
            
            tk.Label(top_frame, text="Bot Tester", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=10, pady=10)
            
            tk.Button(top_frame, text="Load Bot", command=self.load_bot, width=12, relief=tk.RAISED, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(top_frame, text="New Tab", command=self.new_tab, width=12, relief=tk.RAISED, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(top_frame, text="Close Tab", command=self.close_tab, width=12, relief=tk.RAISED, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(top_frame, text="Reset State", command=self.reset_state, width=12, relief=tk.RAISED, bg="#FFC107", fg="black").pack(side=tk.LEFT, padx=5)
            
            self.status_label = tk.Label(top_frame, text="No bot loaded", font=("Arial", 10), bg="#f0f0f0", fg="#666")
            self.status_label.pack(side=tk.LEFT, padx=20)
            
            # Main content area
            content_frame = tk.Frame(self.root, bg="white")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Notebook for tabs
            self.notebook = ttk.Notebook(content_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 10))
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            
            # Create first tab
            self.new_tab()
            
            # Input frame
            input_label = tk.Label(content_frame, text="Send Message:", font=("Arial", 11, "bold"), bg="white", fg="#333")
            input_label.pack(anchor=tk.W)
            
            input_frame = tk.Frame(content_frame, bg="white")
            input_frame.pack(fill=tk.X, pady=(5, 0))
            
            self.input_field = tk.Entry(input_frame, font=("Arial", 10), relief=tk.SUNKEN, bd=1)
            self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            self.input_field.bind("<Return>", lambda e: self.send_message())
            
            tk.Button(input_frame, text="Send", command=self.send_message, width=10, relief=tk.RAISED, bg="#2196F3", fg="white").pack(side=tk.LEFT)
            
            # Terminal/Console output section
            terminal_label = tk.Label(content_frame, text="Console Output:", font=("Arial", 11, "bold"), bg="white", fg="#333")
            terminal_label.pack(anchor=tk.W, pady=(10, 5))
            
            terminal_frame = tk.Frame(content_frame, bg="white", height=150)
            terminal_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
            terminal_frame.pack_propagate(False)
            
            # Terminal display
            self.terminal_widget = tk.Text(
                terminal_frame,
                height=6,
                font=("Courier", 8),
                bg="#1e1e1e",
                fg="#00ff00",
                wrap=tk.WORD,
                relief=tk.SUNKEN,
                bd=1
            )
            
            # Terminal scrollbar
            term_scrollbar = tk.Scrollbar(terminal_frame, command=self.terminal_widget.yview)
            self.terminal_widget.config(yscrollcommand=term_scrollbar.set)
            
            self.terminal_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            term_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.terminal_widget.config(state=tk.DISABLED)

            # Make input field focus
            self.input_field.focus()
            print("[GUI INIT] setup_ui completed successfully")
        except Exception as e:
            print(f"[GUI ERROR] setup_ui failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_tab_changed(self, event):
        """Handle tab change event."""
        try:
            selected_index = self.notebook.index("current")
            if 0 <= selected_index < len(self.tabs):
                self.current_tab = self.tabs[selected_index]
                bot_name = Path(self.current_tab.bot_path).name if self.current_tab.bot_path else "No bot"
                self.status_label.config(text=f"Bot loaded: {bot_name}")
        except:
            pass
    
    def new_tab(self):
        """Create a new bot test tab."""
        tab = BotTestTab(self.notebook, self)
        self.tabs.append(tab)
        self.current_tab = tab
        self.notebook.select(len(self.tabs) - 1)
    
    def close_tab(self):
        """Close the current tab."""
        if len(self.tabs) <= 1:
            messagebox.showwarning("Cannot Close", "You must keep at least one tab open.")
            return
        
        if self.current_tab:
            tab_index = self.tabs.index(self.current_tab)
            self.notebook.forget(tab_index)
            self.tabs.pop(tab_index)
            # Select the previous tab or next tab
            if self.tabs:
                new_index = min(tab_index, len(self.tabs) - 1)
                self.current_tab = self.tabs[new_index]
                self.notebook.select(new_index)
    
    def load_bot(self):
        """Load a bot from a folder or file."""
        bot_path = filedialog.askdirectory(
            title="Select bot folder",
            initialdir=str(Path(__file__).parent.parent.parent / "bot")
        )
        
        if not bot_path:
            return
        
        self.load_bot_from_path(bot_path)
    
    def _load_bot_thread(self, bot_path):
        """Background thread to load bot without freezing GUI."""
        import signal
        import threading
        
        def load_with_timeout():
            try:
                # Display loading message
                self.current_tab.display_message("[INFO] Loading bot (installing requirements)...", is_bot=True)
                
                # Load bot in background with a timeout
                print("[LOAD] Starting bot load with 15-second timeout...")
                tester = InteractiveTester(bot_path)
                print("[LOAD] Bot loaded successfully")
                
                # Update GUI from main thread
                self.root.after(0, self._bot_load_success, bot_path, tester)
            except Exception as e:
                print(f"[LOAD] Exception during bot load: {e}")
                self.root.after(0, self._bot_load_failed, e)
        
        # Start load in a way that allows timeout
        load_thread = threading.Thread(target=load_with_timeout, daemon=True)
        load_thread.daemon = True
        load_thread.start()
        
        # Wait with a timeout - if load takes too long, notify user
        load_thread.join(timeout=15)
        
        if load_thread.is_alive():
            print("[LOAD] Bot load timed out after 15 seconds")
            self.root.after(0, self._bot_load_failed, RuntimeError(
                "Bot module load timed out after 15 seconds. "
                "The bot may have blocking imports or network operations at module level. "
                "Check that TESTING_MODE is properly set in the bot's environment."
            ))
    
    def _bot_load_success(self, bot_path, tester):
        """Callback when bot loads successfully."""
        if not self.current_tab:
            return
        
        self.current_tab.tester = tester
        self.current_tab.bot_path = bot_path
        self.current_tab.update_tab_title()
        self.status_label.config(text=f"Bot loaded: {Path(bot_path).name}")
        
        try:
            self.current_tab.display_message(f"[SUCCESS] Bot loaded from {bot_path}", is_bot=True)
            self.current_tab.display_message(f"Webhook route: {self.current_tab.tester.webhook_route}", is_bot=True)
        except:
            print("[DEBUG] Could not display success messages")
        
        self.input_field.focus()
        self.current_tab.photo_images = []  # Clear cached images
    
    def _bot_load_failed(self, error):
        """Callback when bot load fails."""
        self.status_label.config(text="Failed to load bot")
        try:
            self.current_tab.display_message(f"[ERROR] Failed to load bot: {error}", is_bot=True)
            self.current_tab.display_message(traceback.format_exc(), is_bot=True)
        except:
            print(f"[ERROR] Failed to load bot: {error}")
            traceback.print_exc()
    
    def load_bot_from_path(self, bot_path):
        """Load a bot from a given path (in background thread)."""
        if not self.current_tab:
            return
        
        # Clear the text area when loading a new bot
        self.current_tab.clear_display()
        
        # Start loading in background thread
        load_thread = Thread(target=self._load_bot_thread, args=(bot_path,), daemon=True)
        load_thread.start()
    
    def send_message(self):
        """Send message to bot."""
        if not self.current_tab or not self.current_tab.tester:
            messagebox.showwarning("Bot Not Loaded", "Please load a bot first.")
            return
        
        text = self.input_field.get().strip()
        if not text:
            return
        
        self.input_field.delete(0, tk.END)
        # Display user message in bubble
        self.current_tab.display_message(f"{text}", is_bot=False)
        
        # Show waiting message for games (they take 45+ seconds)
        is_game_cmd = any(cmd in text.lower() for cmd in ['!planegame', '!gungame', 'game', 'hard mode', 'refresh'])
        if is_game_cmd:
            self.current_tab.display_message("[BOT] Loading game... (fetching aircraft from Wikipedia, this takes ~45 seconds)", is_bot=True)
        
        # Run in thread to prevent GUI freeze
        def test():
            try:
                print(f"[TEST DEBUG] Sending message: {text}")
                responses = self.current_tab.tester.test_message(text)
                print(f"[TEST DEBUG] test_message() returned {len(responses)} responses")
                print(f"[TEST DEBUG] message_responses has {len(self.current_tab.tester.message_responses)} items")
                
                # Get active skin PFP for display
                bot_pfp = self.current_tab.tester.get_active_skin_pfp()
                
                # Display messages with their attachments from message_responses
                if self.current_tab.tester.message_responses:
                    print(f"[TEST DEBUG] Processing {len(self.current_tab.tester.message_responses)} messages")
                    print(f"[TEST DEBUG] Bot PFP: {bot_pfp}")
                    
                    # Display PFP with header only once, before first message
                    pfp_displayed = False
                    
                    for i, msg_resp in enumerate(self.current_tab.tester.message_responses, 1):
                        print(f"[TEST DEBUG] Message {i}: type={type(msg_resp)}, keys={list(msg_resp.keys()) if isinstance(msg_resp, dict) else 'N/A'}")
                        if isinstance(msg_resp, dict):
                            msg_text = msg_resp.get('text', '')
                            
                            # Create bot message bubble with PFP header on first message
                            if not pfp_displayed and bot_pfp is not None:
                                print(f"[TEST DEBUG] Displaying bot PFP: {bot_pfp}")
                                # Create bubble with PFP
                                bubble_frame = tk.Frame(self.current_tab.chat_frame, bg="#ffffff")
                                bubble_frame.pack(fill=tk.X, padx=10, pady=5)
                                
                                # Top divider
                                header_label = tk.Label(bubble_frame, text="=" * 25, font=("Arial", 8), bg="#ffffff", fg="#888")
                                header_label.pack()
                                
                                # PFP + Name in bubble
                                content_frame = tk.Frame(bubble_frame, bg="#ffffff")
                                content_frame.pack(fill=tk.X)
                                
                                # Load and display PFP
                                try:
                                    pfp_image = Image.open(bot_pfp)
                                    pfp_image.thumbnail((28, 28), Image.Resampling.LANCZOS)
                                    
                                    # Add border
                                    border_image = Image.new('RGB', (32, 32), (180, 180, 180))
                                    border_image.paste(pfp_image, (2, 2))
                                    
                                    photo = ImageTk.PhotoImage(border_image)
                                    self.current_tab.photo_images.append(photo)
                                    
                                    pfp_label = tk.Label(content_frame, image=photo, bg="#ffffff", bd=0)
                                    pfp_label.pack(side=tk.LEFT, padx=(0, 8), pady=5)
                                except:
                                    print("[DEBUG] Could not load PFP")
                                
                                name_label = tk.Label(content_frame, text="Clankbot:", font=("Arial", 10, "bold"), bg="#ffffff")
                                name_label.pack(side=tk.LEFT, pady=5)
                                
                                pfp_displayed = True
                            
                            # Display text content in bubble
                            if msg_text:
                                print(f"[TEST DEBUG] Displaying text for message {i}")
                                self.current_tab.display_message(f"{msg_text}", is_bot=True)
                            
                            # Display image if present (from attachments)
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
                            self.current_tab.display_message(f"{msg_resp}", is_bot=True)
                    
                    # Add bottom divider after all messages
                    if bot_pfp is not None:
                        divider_frame = tk.Frame(self.current_tab.chat_frame, bg="#ffffff")
                        divider_frame.pack(fill=tk.X, padx=10, pady=5)
                        divider_label = tk.Label(divider_frame, text="-" * 25, font=("Arial", 8), bg="#ffffff", fg="#888")
                        divider_label.pack()
                else:
                    print(f"[TEST DEBUG] message_responses is empty!")
                    self.current_tab.display_message("(no response)", is_bot=True)
                print(f"[TEST DEBUG] Finished displaying all messages")
            except Exception as e:
                print(f"[TEST ERROR] {e}")
                import traceback
                traceback.print_exc()
                self.current_tab.display_message(f"[ERROR] {e}", is_bot=True)
        
        thread = Thread(target=test, daemon=True)
        thread.start()
    
    def display_image(self, image_path, is_local_file=False, show_name=False):
        """Display an image from file path or URL."""
        if not HAS_PIL:
            self.current_tab.display_message(f"[BOT IMAGE]\n{image_path}", is_bot=True)
            self.current_tab.display_message("(Install Pillow for inline image display: pip install Pillow)", is_bot=True)
            return
        
        try:
            print(f"[GUI DEBUG display_image] Starting image load: path={image_path[:60] if image_path else 'NONE'}..., is_local={is_local_file}, show_name={show_name}")
            
            if is_local_file:
                # Load directly from local file
                print(f"[GUI DEBUG display_image] Attempting local file load: {image_path}")
                if not os.path.exists(image_path):
                    print(f"[GUI DEBUG display_image] File not found: {image_path}")
                    self.current_tab.display_message(f"[BOT IMAGE - LOCAL FILE NOT FOUND]\n{image_path}", is_bot=True)
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
                    self.current_tab.display_message(f"[BOT IMAGE - HTTP ERROR {he.code}]\n{image_path}", is_bot=True)
                    return
                except urllib.error.URLError as ue:
                    print(f"[GUI DEBUG display_image] URL Error: {ue.reason}")
                    self.current_tab.display_message(f"[BOT IMAGE - DOWNLOAD ERROR]\n{image_path}\nError: {ue.reason}", is_bot=True)
                    return
            
            # Determine if this is a PFP (check for common PFP sizes and from addons folder)
            is_pfp = is_local_file and (
                image.size == (1080, 1080) or 
                image.size == (256, 256) or
                '/addons/' in image_path.lower()
            )
            
            # Resize appropriately
            if is_pfp or show_name:
                # PFP: Keep square, just slightly larger than text height (28x28)
                max_size = 28
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"[GUI DEBUG display_image] PFP resized to: {image.size}")
            else:
                # Regular image: fit to display width
                max_width = 400
                max_height = 300
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                print(f"[GUI DEBUG display_image] Resized to: {image.size}")
            
            # Add border for PFP
            if is_pfp or show_name:
                # Create a new image with border
                border_size = 2
                border_color = (180, 180, 180)  # Medium gray
                
                # Create border image
                border_image = Image.new('RGB', (image.size[0] + border_size * 2, image.size[1] + border_size * 2), border_color)
                
                # Paste image on border
                border_image.paste(image, (border_size, border_size))
                
                image = border_image
            
            # Convert to PhotoImage using ImageTk
            photo = ImageTk.PhotoImage(image)
            print(f"[GUI DEBUG display_image] Created PhotoImage")
            
            # Store reference to prevent garbage collection
            self.current_tab.photo_images.append(photo)
            
            # Create image widget in a frame
            if show_name:
                # Create inline PFP with name in bubble
                img_label = tk.Label(self.current_tab.chat_frame, image=photo, bg="#ffffff", bd=0)
                
                # Add to bubble - need to add top divider and header
                bubble_frame = tk.Frame(self.current_tab.chat_frame, bg="#ffffff")
                bubble_frame.pack(fill=tk.X, padx=10, pady=5)
                
                header_label = tk.Label(bubble_frame, text="=" * 25, font=("Arial", 8), bg="#ffffff", fg="#888")
                header_label.pack(anchor=tk.W)
                
                content_frame = tk.Frame(bubble_frame, bg="#ffffff")
                content_frame.pack(fill=tk.X)
                
                img_label.pack(in_=content_frame, side=tk.LEFT, padx=(0, 8), pady=5)
                name_label = tk.Label(content_frame, text="Clankbot:", font=("Arial", 10, "bold"), bg="#ffffff")
                name_label.pack(side=tk.LEFT, pady=5)
            else:
                # Regular image display - left-aligned for bot
                bubble_frame = tk.Frame(self.current_tab.chat_frame, bg="#ffffff")
                bubble_frame.pack(fill=tk.X, padx=10, pady=5)
                
                img_label = tk.Label(bubble_frame, image=photo, bg="#ffffff", bd=0)
                img_label.pack(anchor=tk.W)
            
            self.current_tab.chat_canvas.yview_moveto(1.0)
            self.root.update()
            print(f"[GUI DEBUG display_image] Image displayed successfully")
        
        except Exception as e:
            print(f"[GUI DEBUG display_image] Error: {e}")
            import traceback
            traceback.print_exc()
            self.current_tab.display_message(f"[BOT IMAGE]\n{image_path}\n[Error loading: {e}]", is_bot=True)
    
    def display_audio(self, audio_path, is_local_file=False, duration=7):
        """Display and open audio file with system player."""
        try:
            print(f"[GUI DEBUG display_audio] Called with: path={audio_path}, is_local={is_local_file}, duration={duration}")
            
            filename = os.path.basename(audio_path)
            self.current_tab.display_message(f"[🔊 Audio: {filename} ({duration}s)]", is_bot=True)
            
            # Check if file exists
            if is_local_file:
                if not os.path.exists(audio_path):
                    print(f"[GUI DEBUG display_audio] File not found: {audio_path}")
                    self.current_tab.display_message(f"[ERROR] Local audio file not found: {audio_path}", is_bot=True)
                    return
                display_path = os.path.basename(audio_path)
            else:
                display_path = audio_path
            
            self.current_tab.display_message(f"📁 {display_path}", is_bot=True)
            
            if not is_local_file:
                print(f"[GUI DEBUG display_audio] URL audio not supported")
                self.current_tab.display_message("[INFO] Audio playback from URLs not yet supported (file-based only)", is_bot=True)
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
                    
                    self.current_tab.display_message("[▶ Opening in system player...]", is_bot=True)
                    
                    # Wait approximate duration
                    import time
                    time.sleep(duration + 1)
                    
                    self.current_tab.display_message("[✓ Done]", is_bot=True)
                    print(f"[GUI DEBUG play_audio] Audio opened")
                except Exception as e:
                    print(f"[GUI DEBUG play_audio] Error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.current_tab.display_message(f"[ERROR] Could not open audio: {e}", is_bot=True)
            
            thread = Thread(target=play_audio, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"[GUI DEBUG display_audio] Error: {e}")
            traceback.print_exc()
            self.current_tab.display_message(f"[AUDIO ERROR]\n{audio_path}\n[Error: {e}]", is_bot=True)
    
    def reset_state(self):
        """Reset bot state."""
        if not self.current_tab or not self.current_tab.tester:
            messagebox.showwarning("Bot Not Loaded", "Please load a bot first.")
            return
        
        try:
            cleared_count = 0
            # Only clear user-defined state variables, not module internals
            for var_name, var_value in self.current_tab.tester.bot_module.__dict__.items():
                # Skip private/dunder variables and common module attributes
                if var_name.startswith('_'):
                    continue
                # Only clear dicts that look like state (not imports or functions)
                if isinstance(var_value, dict) and not callable(var_value):
                    try:
                        var_value.clear()
                        cleared_count += 1
                    except Exception as e:
                        print(f"[DEBUG] Could not clear {var_name}: {e}")
                        continue
            self.current_tab.display_message(f"[INFO] Bot state cleared ({cleared_count} dictionaries)", is_bot=True)
        except Exception as e:
            print(f"[ERROR] reset_state error: {e}")
            import traceback
            traceback.print_exc()
            self.current_tab.display_message(f"[ERROR] Failed to reset state: {e}", is_bot=True)


def main():
    try:
        root = tk.Tk()
        
        # Check for command-line arguments for drag-and-drop support
        initial_bot_path = None
        if len(sys.argv) > 1:
            initial_bot_path = sys.argv[1]
            print(f"[GUI] Loading bot from command-line argument: {initial_bot_path}")
        
        gui = SimpleBotTesterGUI(root, initial_bot_path)
        print("[GUI] Starting mainloop...")
        root.mainloop()
        print("[GUI] Mainloop finished normally")
    except Exception as e:
        print(f"[GUI FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

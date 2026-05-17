"""
GUI version of the interactive bot tester with image support.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import sys
from pathlib import Path

# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Add parent to path for importing interactive_test
sys.path.insert(0, str(Path(__file__).parent))
from interactive_test import (
    InteractiveTester, discover_bots, get_bot_path_startup,
    download_from_github, clone_git_repository
)


def get_icon_path():
    """Get the path to icon.ico - works both in Python and PyInstaller executable"""
    import sys
    
    # For PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Running as executable
        base_path = sys._MEIPASS
        icon_path = os.path.join(base_path, "icon.ico")
        if os.path.exists(icon_path):
            return icon_path
    
    # For normal Python execution - check project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(project_root, "icon.ico")
    if os.path.exists(icon_path):
        return icon_path
    
    # Try current working directory as fallback
    if os.path.exists("icon.ico"):
        return os.path.abspath("icon.ico")
    
    return None


class BotTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Bot Tester")
        
        # Set icon BEFORE any other window operations
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(default=icon_path)
                self.root.after(10, lambda: self.root.iconbitmap(default=icon_path))  # Ensure it sticks
            except Exception as e:
                pass  # Icon loading failed, continue without it
        
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        self.tester = None
        self.selected_image_path = None
        self.selected_image_tk = None
        self.selected_audio_path = None
        
        # Initialize GUI
        self.setup_ui()
        
        # Start periodic refresh of image preview (every 2 seconds)
        self._schedule_image_refresh()
        
    def setup_ui(self):
        """Create the GUI layout."""
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color="#f5f7f9")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title bar with bot info
        title_frame = ctk.CTkFrame(main_frame, fg_color="#4B7EC9", corner_radius=8)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="Bot Interactive Tester",
            text_color="white",
            font=("Arial", 16, "bold"),
            fg_color="#4B7EC9"
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.bot_info_label = ctk.CTkLabel(
            title_frame,
            text="No bot loaded",
            text_color="#ffffff",
            font=("Arial", 10),
            fg_color="#4B7EC9"
        )
        self.bot_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Load bot button
        load_bot_btn = ctk.CTkButton(
            title_frame,
            text="Load Bot",
            command=self.load_bot,
            fg_color="#ffffff",
            text_color="#4B7EC9",
            hover_color="#e8eef7",
            font=("Arial", 10, "bold"),
            corner_radius=6
        )
        load_bot_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # User selector frame
        user_frame = ctk.CTkFrame(main_frame, fg_color="#f5f7f9", corner_radius=8)
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        user_label = ctk.CTkLabel(user_frame, text="User:", text_color="#2D3436", font=("Arial", 10, "bold"), fg_color="#f5f7f9")
        user_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.user_var = tk.StringVar(value="TestUser")
        self.user_combo = ctk.CTkComboBox(
            user_frame,
            variable=self.user_var,
            values=["TestUser"],
            state="readonly",
            font=("Arial", 10),
            corner_radius=6
        )
        self.user_combo.pack(side=tk.LEFT, padx=5, pady=8)
        self.user_combo.bind("<<ComboboxSelected>>", self.on_user_change)
        
        # Quick action buttons
        ctk.CTkButton(user_frame, text="Reset State", command=self.reset_state, corner_radius=6).pack(side=tk.LEFT, padx=5, pady=8)
        ctk.CTkButton(user_frame, text="Show State", command=self.show_state, corner_radius=6).pack(side=tk.LEFT, padx=5, pady=8)
        
        # Main content area (chat + image)
        content_frame = ctk.CTkFrame(main_frame, fg_color="#f5f7f9", corner_radius=8)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left side - chat display
        left_frame = ctk.CTkFrame(content_frame, fg_color="#f5f7f9", corner_radius=0)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        chat_label = ctk.CTkLabel(left_frame, text="Bot Responses:", text_color="#2D3436", font=("Arial", 12, "bold"), fg_color="#f5f7f9")
        chat_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Chat display area (using tk.Text for better compatibility)
        self.chat_display = scrolledtext.ScrolledText(
            left_frame,
            height=15,
            width=50,
            font=("Courier", 10),
            bg="#eff2f7",
            fg="#2D3436",
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Right side - image preview
        right_frame = ctk.CTkFrame(content_frame, fg_color="#f5f7f9", corner_radius=0)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_frame.configure(width=250)
        right_frame.pack_propagate(False)
        
        image_label = ctk.CTkLabel(right_frame, text="Image Preview:", text_color="#2D3436", font=("Arial", 12, "bold"), fg_color="#f5f7f9")
        image_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Image frame
        self.image_frame = ctk.CTkFrame(right_frame, fg_color="#eff2f7", corner_radius=8, border_width=2, border_color="#d0d8e0")
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.image_label_display = ctk.CTkLabel(
            self.image_frame,
            text="No image selected",
            text_color="#a8b3c1",
            font=("Arial", 10),
            fg_color="#eff2f7"
        )
        self.image_label_display.pack(expand=True)
        
        # Image filename
        self.image_filename_label = ctk.CTkLabel(
            right_frame,
            text="",
            text_color="#8a94a6",
            font=("Arial", 9),
            fg_color="#f5f7f9"
        )
        self.image_filename_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Image selection buttons
        btn_frame = ctk.CTkFrame(right_frame, fg_color="#f5f7f9", corner_radius=0)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Pick Image", command=self.pick_image, corner_radius=6).pack(fill=tk.X, pady=2)
        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_image_preview, corner_radius=6).pack(fill=tk.X, pady=2)
        ctk.CTkButton(btn_frame, text="Clear Image", command=self.clear_image, corner_radius=6).pack(fill=tk.X, pady=2)
        
        # Audio section
        audio_label = ctk.CTkLabel(right_frame, text="Audio Preview:", text_color="#2D3436", font=("Arial", 12, "bold"), fg_color="#f5f7f9")
        audio_label.pack(anchor=tk.W, pady=(10, 5))
        
        # Audio frame
        self.audio_frame = ctk.CTkFrame(right_frame, fg_color="#eff2f7", corner_radius=8, border_width=2, border_color="#d0d8e0")
        self.audio_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.audio_label_display = ctk.CTkLabel(
            self.audio_frame,
            text="🔊 No audio selected",
            text_color="#a8b3c1",
            font=("Arial", 10),
            fg_color="#eff2f7"
        )
        self.audio_label_display.pack(expand=True)
        
        # Audio filename
        self.audio_filename_label = ctk.CTkLabel(
            right_frame,
            text="",
            text_color="#8a94a6",
            font=("Arial", 9),
            fg_color="#f5f7f9"
        )
        self.audio_filename_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Audio selection buttons
        audio_btn_frame = ctk.CTkFrame(right_frame, fg_color="#f5f7f9", corner_radius=0)
        audio_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ctk.CTkButton(audio_btn_frame, text="Pick Audio", command=self.pick_audio, corner_radius=6).pack(fill=tk.X, pady=2)
        ctk.CTkButton(audio_btn_frame, text="Clear Audio", command=self.clear_audio, corner_radius=6).pack(fill=tk.X, pady=2)
        
        # Input area
        input_frame = ctk.CTkFrame(main_frame, fg_color="#f5f7f9", corner_radius=8)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        input_label = ctk.CTkLabel(input_frame, text="Message:", text_color="#2D3436", font=("Arial", 10, "bold"), fg_color="#f5f7f9")
        input_label.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Message input (using tk.Text for better control)
        self.message_input = tk.Text(
            input_frame,
            height=4,
            font=("Arial", 10),
            bg="#fafbfd",
            fg="#2D3436",
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=1,
            insertbackground="#4B7EC9",
            highlightthickness=1,
            highlightbackground="#d0d8e0"
        )
        self.message_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.message_input.bind("<Control-Return>", lambda e: self.send_message())
        self.message_input.bind("<Control-v>", lambda e: self.paste_text() or "break")
        self.message_input.bind("<Control-V>", lambda e: self.paste_text() or "break")
        self.message_input.bind("<Control-c>", lambda e: self.copy_text() or "break")
        self.message_input.bind("<Control-C>", lambda e: self.copy_text() or "break")
        self.message_input.bind("<Control-x>", lambda e: self.cut_text() or "break")
        self.message_input.bind("<Control-X>", lambda e: self.cut_text() or "break")
        self.message_input.bind("<Button-3>", self.show_context_menu)  # Right-click context menu
        
        # Create context menu for text widget
        self.context_menu = tk.Menu(self.message_input, tearoff=0, bg="#f5f7f9", fg="#2D3436", activebackground="#4B7EC9", activeforeground="#ffffff")
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear", command=self.clear_input)
        
        # Send button
        button_frame = ctk.CTkFrame(input_frame, fg_color="#f5f7f9", corner_radius=0)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        send_btn = ctk.CTkButton(
            button_frame,
            text="Send Message (Ctrl+Enter)",
            command=self.send_message,
            fg_color="#4B7EC9",
            text_color="white",
            hover_color="#3a5fa8",
            font=("Arial", 11, "bold"),
            corner_radius=6
        )
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready. Load a bot to start testing.",
            text_color="#8a94a6",
            font=("Arial", 9),
            fg_color="#eff2f7",
            corner_radius=6
        )
        self.status_label.pack(fill=tk.X)
        
        # Check if we can auto-load on startup
        self.auto_load_bot()
    
    def auto_load_bot(self):
        """Try to auto-load a bot on startup."""
        # Disabled for GUI - user will click "Load Bot" button instead
        pass
    
    def load_bot(self):
        """Show bot selection dialog with options for local, file, or GitHub/Git URL."""
        # Create a simple dialog to choose loading method
        dialog_result = messagebox.askquestion(
            "Load Bot Method",
            "How would you like to load a bot?\n\n"
            "Yes = Local folder/file\n"
            "No = GitHub/Git URL\n\n"
            "(Choose Yes for local, No for GitHub)",
            icon=messagebox.QUESTION
        )
        
        if dialog_result == 'yes':
            # Local folder selection
            folder_path = filedialog.askdirectory(title="Select bot folder")
            if not folder_path:
                return

            try:
                potential_bots = discover_bots(folder_path)
                if not potential_bots:
                    messagebox.showerror(
                        "No bots found",
                        f"No Flask bots found in:\n{folder_path}"
                    )
                    self.update_status("No bots found")
                    return

                if len(potential_bots) == 1:
                    self.load_bot_from_path(potential_bots[0][0])
                    return

                file_path = filedialog.askopenfilename(
                    title="Select bot file",
                    initialdir=folder_path,
                    filetypes=[("Python files", "*.py"), ("All files", "*.*")]
                )
                if file_path:
                    self.load_bot_from_path(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load bot: {e}")
        
        elif dialog_result == 'no':
            # GitHub/Git URL loading
            self.load_bot_from_github()
    
    def load_bot_from_github(self):
        """Load bot from GitHub/Git URL via dialog."""
        # Create a simple input dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load from GitHub/Git")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Instructions
        instr_label = tk.Label(
            dialog,
            text="Enter GitHub/Git URL (file or repository):\n\n"
            "Examples:\n"
            "  https://github.com/user/repo/blob/main/bot.py\n"
            "  https://github.com/user/repo.git",
            justify=tk.LEFT,
            font=("Arial", 9)
        )
        instr_label.pack(padx=10, pady=10)
        
        # Input field
        url_entry = tk.Entry(dialog, font=("Arial", 10), width=50)
        url_entry.pack(padx=10, pady=5, fill=tk.X)
        url_entry.focus()
        
        def load_from_url():
            url = url_entry.get().strip()
            if not url:
                messagebox.showwarning("Empty URL", "Please enter a valid GitHub/Git URL")
                return
            
            dialog.destroy()
            self.update_status(f"Loading from {url[:50]}...")
            
            try:
                # Determine if it's a file or repo URL
                if url.endswith('.py') or '/blob/' in url or '/-/blob/' in url or '/src/' in url:
                    bot_path = download_from_github(url)
                elif url.endswith('.git') or 'github.com' in url or 'gitlab.com' in url or 'gitea' in url.lower():
                    bot_path = clone_git_repository(url)
                else:
                    # Ask user
                    choice = messagebox.askyesno("URL Type", "Is this a file URL?\n\nYes = File\nNo = Repository")
                    if choice:
                        bot_path = download_from_github(url)
                    else:
                        bot_path = clone_git_repository(url)
                
                if bot_path:
                    self.load_bot_from_path(bot_path)
                else:
                    messagebox.showerror("Loading Failed", "Could not load bot from URL")
                    self.update_status("Failed to load from GitHub/Git")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load bot from URL: {e}")
                self.update_status("Error loading from GitHub/Git")
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Button(btn_frame, text="Load", command=load_from_url, bg="#4B7EC9", fg="white", font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, font=("Arial", 10)).pack(side=tk.RIGHT, padx=5)
    

    
    def load_bot_from_path(self, bot_path):
        """Load a bot from a specific path."""
        try:
            self.tester = InteractiveTester(bot_module_path=bot_path)
            
            # Update title and info using tester's attributes
            bot_name = self.tester.bot_name
            bot_type = (self.tester.bot_type or 'unknown').capitalize()
            self.title_label.configure(text=f"Bot: {bot_name} ({bot_type})")
            
            # Build bot info with author if available
            info_parts = [f"Route: {self.tester.webhook_route}", f"State: {len(self.tester.bot_state)} vars"]
            if hasattr(self.tester, 'manifest_info') and self.tester.manifest_info:
                author = self.tester.manifest_info.get('author')
                if author:
                    info_parts.insert(0, f"Author: {author}")
            self.bot_info_label.configure(text=" | ".join(info_parts))
            
            # Update user combo with available dummies
            self.user_combo.configure(values=list(self.tester.dummies.keys()))
            self.user_combo.set("TestUser")
            
            # Clear chat and reset
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            bot_type_label = "Flask" if self.tester.bot_type == 'flask' else "Polling"
            self.chat_display.insert(tk.END, f"✓ Loaded: {bot_name} ({bot_type_label} bot)\n")
            
            # Show manifest info if available
            if hasattr(self.tester, 'manifest_info') and self.tester.manifest_info:
                manifest = self.tester.manifest_info
                self.chat_display.insert(tk.END, f"✓ Manifest: {manifest.get('name', 'N/A')} by {manifest.get('author', 'N/A')}\n")
            else:
                self.chat_display.insert(tk.END, f"✓ No manifest.json found (using filename)\n")
            
            self.chat_display.insert(tk.END, f"✓ Route: {self.tester.webhook_route}\n")
            self.chat_display.insert(tk.END, f"✓ State vars: {', '.join(self.tester.bot_state.keys())}\n\n")
            self.chat_display.config(state=tk.DISABLED)
            
            # Update image preview if responses already exist
            self._update_image_preview_from_responses()
            
            self.update_status(f"Bot loaded: {bot_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load bot: {e}")
            self.update_status("Error loading bot")
    
    def pick_image(self):
        """Open file dialog to select an image."""
        if not self.tester:
            messagebox.showwarning("Warning", "Load a bot first")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_image_path = file_path
            self.display_image_preview(file_path)
            self.update_status(f"Image selected: {Path(file_path).name}")
    
    def display_image_preview(self, image_path):
        """Display image preview in the preview area."""
        try:
            # Load and resize image
            img = Image.open(image_path)
            
            # Resize to fit in preview area (max 200x300)
            img.thumbnail((200, 300), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.selected_image_tk = ImageTk.PhotoImage(img)
            
            # Update labels
            self.image_label_display.configure(image=self.selected_image_tk, text="")
            self.image_filename_label.configure(text=Path(image_path).name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.clear_image()
    
    def clear_image(self):
        """Clear the selected image."""
        self.selected_image_path = None
        self.selected_image_tk = None
        self.image_label_display.configure(text="No image selected")
        self.image_filename_label.configure(text="")
        self.update_status("Image cleared")
    
    def refresh_image_preview(self):
        """Refresh the image preview from captured bot responses."""
        self._update_image_preview_from_responses()
        self.update_status("Image preview refreshed")
    
    def _schedule_image_refresh(self):
        """Schedule periodic refresh of image preview from bot responses."""
        try:
            # Only refresh if no user-selected image (to avoid overwriting)
            if not self.selected_image_path:
                self._update_image_preview_from_responses()
        except Exception as e:
            pass  # Silently ignore errors in auto-refresh
        
        # Schedule next refresh in 2 seconds
        self.root.after(2000, self._schedule_image_refresh)
    
    def _update_image_preview_from_responses(self):
        """Extract latest image URL from captured message responses and display it."""
        if not self.tester:
            return
        
        if not self.tester.message_responses:
            return
        
        # Look for the most recent message with an image attachment
        for response in reversed(self.tester.message_responses):
            if 'attachments' in response:
                for attachment in response['attachments']:
                    if attachment.get('type') == 'image':
                        image_url = attachment.get('url', '')
                        if image_url:
                            # Display the image URL in the preview area
                            url_display = f"[BOT IMAGE]\n{image_url[:65]}..."
                            self.image_label_display.configure(text=url_display, text_color="#2D3436")
                            self.image_filename_label.configure(text="From bot response")
                            return
    
    def pick_audio(self):
        """Let user pick an audio file."""
        if not self.tester:
            messagebox.showwarning("Warning", "Load a bot first")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=[("Audio files", "*.mp3 *.m4a *.wav *.ogg *.flac"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_audio_path = file_path
            self.display_audio_preview(file_path)
            self.update_status(f"Audio selected: {Path(file_path).name}")
    
    def display_audio_preview(self, audio_path):
        """Display audio preview in the preview area."""
        try:
            filename = Path(audio_path).name
            self.audio_label_display.configure(text=f"🔊 {filename}")
            self.audio_filename_label.configure(text=filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio: {e}")
            self.clear_audio()
    
    def clear_audio(self):
        """Clear the selected audio."""
        self.selected_audio_path = None
        self.audio_label_display.configure(text="🔊 No audio selected")
        self.audio_filename_label.configure(text="")
        self.update_status("Audio cleared")
    
    def on_user_change(self, event=None):
        """Handle user selection change."""
        if self.tester:
            user = self.user_var.get()
            if user in self.tester.dummies:
                self.tester.active_user = user
                self.update_status(f"User changed to: {user}")
    
    def send_message(self):
        """Send a message to the bot."""
        if not self.tester:
            messagebox.showwarning("Warning", "Load a bot first")
            return
        
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            messagebox.showwarning("Warning", "Message cannot be empty")
            return
        
        try:
            # If image is selected, mention it
            display_msg_parts = [f"[{self.tester.active_user}] {message}"]
            if self.selected_image_path:
                display_msg_parts.append(f"📎 Image: {Path(self.selected_image_path).name}")
            if self.selected_audio_path:
                display_msg_parts.append(f"🔊 Audio: {Path(self.selected_audio_path).name}")
            display_msg = "\n".join(display_msg_parts) + "\n"
            
            # Send message
            responses = self.tester.test_message(
                message,
                user_name=self.tester.active_user,
                image_path=self.selected_image_path,
                audio_path=self.selected_audio_path
            )
            
            # Display in chat
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, display_msg)
            
            if responses:
                for i, response in enumerate(responses, 1):
                    self.chat_display.insert(tk.END, f"  [{i}] {response}\n")
            else:
                self.chat_display.insert(tk.END, "  (no response)\n")
            
            # Show deletions/bans
            if self.tester.deleted_messages:
                self.chat_display.insert(tk.END, f"  🗑️ Deleted: {self.tester.deleted_messages}\n")
                self.tester.deleted_messages = []
            
            if self.tester.banned_members:
                self.chat_display.insert(tk.END, f"  🚫 Banned: {self.tester.banned_members}\n")
                self.tester.banned_members = []
            
            self.chat_display.insert(tk.END, "\n")
            self.chat_display.see(tk.END)  # Scroll to bottom
            self.chat_display.config(state=tk.DISABLED)
            
            # Extract and display any image URLs from captured responses
            self._update_image_preview_from_responses()
            
            # Clear input
            self.message_input.delete("1.0", tk.END)
            self.update_status(f"Message sent ({len(responses)} responses)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
            self.update_status("Error sending message")
    
    def reset_state(self):
        """Reset bot state."""
        if not self.tester:
            messagebox.showwarning("Warning", "Load a bot first")
            return
        
        try:
            for state_dict in self.tester.bot_state.values():
                if isinstance(state_dict, dict):
                    state_dict.clear()
                elif isinstance(state_dict, (list, set)):
                    state_dict.clear()
            
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "✓ Bot state cleared\n\n")
            self.chat_display.config(state=tk.DISABLED)
            
            self.update_status("Bot state reset")
            messagebox.showinfo("Success", "Bot state has been cleared")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset state: {e}")
    
    def show_state(self):
        """Show current bot state."""
        if not self.tester:
            messagebox.showwarning("Warning", "Load a bot first")
            return
        
        try:
            state_text = "BOT STATE:\n" + "="*50 + "\n"
            
            for name, state_dict in self.tester.bot_state.items():
                if isinstance(state_dict, dict):
                    state_text += f"\n{name}:\n"
                    if state_dict:
                        for key, value in list(state_dict.items())[:10]:  # First 10 items
                            state_text += f"  {key}: {value}\n"
                        if len(state_dict) > 10:
                            state_text += f"  ... and {len(state_dict) - 10} more\n"
                    else:
                        state_text += "  (empty)\n"
                else:
                    state_text += f"\n{name}: {state_dict}\n"
            
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, state_text + "\n")
            self.chat_display.config(state=tk.DISABLED)
            
            self.update_status("State displayed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show state: {e}")
    
    def update_status(self, message):
        """Update status bar."""
        self.status_label.configure(text=message)
    
    def show_context_menu(self, event):
        """Show context menu on right-click."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass
    
    def cut_text(self):
        """Cut text from message input."""
        try:
            self.message_input.event_generate("<<Cut>>")
        except:
            pass
    
    def copy_text(self):
        """Copy text from message input."""
        try:
            self.message_input.event_generate("<<Copy>>")
        except:
            pass
    
    def paste_text(self):
        """Paste text into message input."""
        try:
            self.message_input.event_generate("<<Paste>>")
        except:
            pass
    
    def clear_input(self):
        """Clear the message input."""
        self.message_input.delete("1.0", tk.END)


def main():
    root = ctk.CTk()
    app = BotTesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

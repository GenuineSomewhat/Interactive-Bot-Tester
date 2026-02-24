"""
GUI version of the interactive bot tester with image support.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
from PIL import Image, ImageTk
import os
import sys
from pathlib import Path

# Add parent to path for importing interactive_test
sys.path.insert(0, str(Path(__file__).parent))
from interactive_test import InteractiveTester, discover_bots, get_bot_path_startup


class BotTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot Interactive Tester")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        self.tester = None
        self.selected_image_path = None
        self.selected_image_tk = None
        
        # Configure style
        self.root.configure(bg="#f0f0f0")
        
        # Initialize GUI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the GUI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title bar with bot info
        title_frame = tk.Frame(main_frame, bg="#2c3e50", highlightthickness=0)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = tk.Label(
            title_frame,
            text="Bot Interactive Tester",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=10,
            pady=10
        )
        self.title_label.pack(side=tk.LEFT)
        
        self.bot_info_label = tk.Label(
            title_frame,
            text="No bot loaded",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("Arial", 10),
            padx=10,
            pady=10
        )
        self.bot_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Load bot button
        load_bot_btn = tk.Button(
            title_frame,
            text="Load Bot",
            command=self.load_bot,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            padx=15,
            pady=5,
            font=("Arial", 10, "bold")
        )
        load_bot_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # User selector frame
        user_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        user_label = tk.Label(user_frame, text="User:", bg="white", font=("Arial", 10))
        user_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.user_var = tk.StringVar(value="TestUser")
        self.user_combo = ttk.Combobox(
            user_frame,
            textvariable=self.user_var,
            values=["TestUser"],
            state="readonly",
            width=20,
            font=("Arial", 10)
        )
        self.user_combo.pack(side=tk.LEFT, padx=5, pady=8)
        self.user_combo.bind("<<ComboboxSelected>>", self.on_user_change)
        
        # Quick action buttons
        ttk.Button(user_frame, text="Reset State", command=self.reset_state).pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(user_frame, text="Show State", command=self.show_state).pack(side=tk.LEFT, padx=5, pady=8)
        
        # Main content area (chat + image)
        content_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left side - chat display
        left_frame = tk.Frame(content_frame, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        chat_label = tk.Label(left_frame, text="Bot Responses:", bg="white", font=("Arial", 11, "bold"))
        chat_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            left_frame,
            height=15,
            width=50,
            font=("Courier", 10),
            bg="#ecf0f1",
            fg="#2c3e50",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Right side - image preview
        right_frame = tk.Frame(content_frame, bg="white", width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_frame.pack_propagate(False)
        
        image_label = tk.Label(right_frame, text="Image Preview:", bg="white", font=("Arial", 11, "bold"))
        image_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Image frame
        self.image_frame = tk.Frame(right_frame, bg="#ecf0f1", relief=tk.SUNKEN, bd=1)
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.image_label_display = tk.Label(
            self.image_frame,
            text="No image selected",
            bg="#ecf0f1",
            fg="#7f8c8d",
            font=("Arial", 10),
            justify=tk.CENTER
        )
        self.image_label_display.pack(expand=True)
        
        # Image filename
        self.image_filename_label = tk.Label(
            right_frame,
            text="",
            bg="white",
            fg="#7f8c8d",
            font=("Arial", 9),
            wraplength=200,
            justify=tk.LEFT
        )
        self.image_filename_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Image selection buttons
        btn_frame = tk.Frame(right_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Pick Image", command=self.pick_image).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Clear Image", command=self.clear_image).pack(fill=tk.X, pady=2)
        
        # Input area
        input_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        input_label = tk.Label(input_frame, text="Message:", bg="white", font=("Arial", 10, "bold"))
        input_label.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Message input
        self.message_input = tk.Text(
            input_frame,
            height=4,
            font=("Arial", 10),
            bg="#fafafa",
            fg="#2c3e50",
            wrap=tk.WORD
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
        self.context_menu = tk.Menu(self.message_input, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear", command=self.clear_input)
        
        # Send button
        button_frame = tk.Frame(input_frame, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        send_btn = tk.Button(
            button_frame,
            text="Send Message (Ctrl+Enter)",
            command=self.send_message,
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            padx=20,
            pady=10,
            font=("Arial", 11, "bold"),
            cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Status bar
        self.status_label = tk.Label(
            main_frame,
            text="Ready. Load a bot to start testing.",
            bg="#ecf0f1",
            fg="#7f8c8d",
            font=("Arial", 9),
            anchor=tk.W,
            relief=tk.SUNKEN,
            padx=5,
            pady=5
        )
        self.status_label.pack(fill=tk.X)
        
        # Check if we can auto-load on startup
        self.auto_load_bot()
    
    def auto_load_bot(self):
        """Try to auto-load a bot on startup."""
        try:
            # Try to load from startup menu
            bot_path = get_bot_path_startup()
            if bot_path:
                self.load_bot_from_path(bot_path)
        except Exception:
            pass
    
    def load_bot(self):
        """Show bot selection dialog."""
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
    
    def load_bot_from_path(self, bot_path):
        """Load a bot from a specific path."""
        try:
            self.tester = InteractiveTester(bot_module_path=bot_path)
            
            # Update title and info
            bot_name = Path(bot_path).stem
            self.title_label.config(text=f"Bot: {bot_name}")
            self.bot_info_label.config(text=f"Route: {self.tester.webhook_route} | State: {len(self.tester.bot_state)} vars")
            
            # Update user combo with available dummies
            self.user_combo.config(values=list(self.tester.dummies.keys()))
            self.user_combo.set("TestUser")
            
            # Clear chat and reset
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, f"✓ Loaded: {bot_name}\n")
            self.chat_display.insert(tk.END, f"✓ Route: {self.tester.webhook_route}\n")
            self.chat_display.insert(tk.END, f"✓ State vars: {', '.join(self.tester.bot_state.keys())}\n\n")
            self.chat_display.config(state=tk.DISABLED)
            
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
            self.image_label_display.config(image=self.selected_image_tk, text="")
            self.image_filename_label.config(text=Path(image_path).name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.clear_image()
    
    def clear_image(self):
        """Clear the selected image."""
        self.selected_image_path = None
        self.selected_image_tk = None
        self.image_label_display.config(image="", text="No image selected")
        self.image_filename_label.config(text="")
        self.update_status("Image cleared")
    
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
            if self.selected_image_path:
                display_msg = f"[{self.tester.active_user}] {message}\n📎 Image: {Path(self.selected_image_path).name}\n"
            else:
                display_msg = f"[{self.tester.active_user}] {message}\n"
            
            # Send message
            responses = self.tester.test_message(
                message,
                user_name=self.tester.active_user,
                image_path=self.selected_image_path
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
        self.status_label.config(text=message)
    
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
    root = tk.Tk()
    app = BotTesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

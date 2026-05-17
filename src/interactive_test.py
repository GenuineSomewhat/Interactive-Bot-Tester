"""
Simple, clean interactive bot tester for Flask bots.
Loads the bot module, captures sent messages, and provides a test interface.
"""

import os
import sys
import importlib.util
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from PIL import Image
except Exception:
    Image = None


def _find_flask_app_in_folder(folder_path):
    """
    Find Flask app file in a folder (looks for app.py, main.py, bot.py, etc.).
    
    Args:
        folder_path: Path to folder to search
    
    Returns:
        Path to Flask app file, or None if not found
    """
    candidates = ['app.py', 'main.py', 'bot.py', '__main__.py']
    
    for candidate in candidates:
        app_path = os.path.join(folder_path, candidate)
        if os.path.exists(app_path):
            return app_path
    
    # If no candidates found, try any .py file that has Flask app
    for filename in os.listdir(folder_path):
        if filename.endswith('.py') and not filename.startswith('_'):
            filepath = os.path.join(folder_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'Flask' in content or 'app = ' in content:
                        return filepath
            except:
                pass
    
    return None


def load_bot_module(bot_path):
    """
    Load a Flask bot module from a file or folder path.
    
    Args:
        bot_path: Path to bot module file (e.g., 'app.py') or folder containing bot
    
    Returns:
        Tuple of (module, flask_app)
    """
    if not os.path.isabs(bot_path):
        bot_path = os.path.abspath(bot_path)
    
    if not os.path.exists(bot_path):
        raise FileNotFoundError(f"Bot module not found: {bot_path}")
    
    # If it's a folder, find the app file
    if os.path.isdir(bot_path):
        app_file = _find_flask_app_in_folder(bot_path)
        if not app_file:
            raise FileNotFoundError(f"No Flask app found in folder: {bot_path}")
        bot_path = app_file
    
    bot_dir = os.path.dirname(bot_path)
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    
    try:
        # Change to bot directory and add it to path
        os.chdir(bot_dir)
        if bot_dir not in sys.path:
            sys.path.insert(0, bot_dir)
        
        # Set environment variables for testing
        os.environ.setdefault("ACCESS_TOKEN", "test_token_12345")
        os.environ.setdefault("GROUP_ID", "test_group_123")
        os.environ.setdefault("BOT_ID", "test_bot_123")
        
        # Clear cached module if it exists
        module_name = Path(bot_path).stem
        for mod_key in list(sys.modules.keys()):
            if module_name in mod_key:
                del sys.modules[mod_key]
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, bot_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find Flask app instance
        flask_app = None
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            attr = getattr(module, attr_name)
            if hasattr(attr, 'test_client') and hasattr(attr, 'route'):
                try:
                    attr.test_client()
                    flask_app = attr
                    break
                except TypeError:
                    pass
        
        if not flask_app:
            raise RuntimeError(f"No Flask app instance found in {bot_path}")
        
        return module, flask_app
    
    finally:
        os.chdir(original_cwd)
        sys.path = original_sys_path


class InteractiveTester:
    """Simple tester for Flask bots with message capture."""
    
    def __init__(self, bot_path):
        """Initialize tester with bot module path."""
        self.bot_path = bot_path
        # Determine bot directory
        if os.path.isdir(bot_path):
            self.bot_dir = os.path.abspath(bot_path)
        else:
            self.bot_dir = os.path.dirname(os.path.abspath(bot_path))
        
        self.bot_module = None
        self.app = None
        self.sent_messages = []
        self.message_responses = []
        self.webhook_route = "/"
        self._message_id_counter = 1
        self._load_bot()
    
    def _load_bot(self):
        """Load bot module and apply message capture patches."""
        print(f"[INFO] Loading bot from {self.bot_path}")
        
        self.bot_module, self.app = load_bot_module(self.bot_path)
        
        # Detect webhook route
        self._detect_webhook_route()
        
        # Apply persistent patches to capture messages
        self._apply_patches()
        
        print(f"[INFO] Bot loaded successfully")
        print(f"[INFO] Webhook route: {self.webhook_route}")
    
    def _detect_webhook_route(self):
        """Auto-detect the webhook route for POST requests."""
        webhook_route = "/"
        
        routes = []
        for rule in self.app.url_map.iter_rules():
            if 'POST' in rule.methods:
                routes.append(rule.rule)
        
        # Prefer common webhook routes
        for candidate in ['/webhook', '/webhooks', '/message', '/', '/api/webhook']:
            if candidate in routes:
                webhook_route = candidate
                break
        
        if routes and webhook_route == "/" and "/" not in routes:
            webhook_route = routes[0]
        
        self.webhook_route = webhook_route
    
    def _patch_admin_checks(self):
        """Patch admin checking to allow test users to behave as admins."""
        test_user_id = "admin_test_123"
        
        # Add test user ID to ADMIN_IDS list if it exists
        if hasattr(self.bot_module, 'ADMIN_IDS'):
            admin_ids = getattr(self.bot_module, 'ADMIN_IDS')
            if isinstance(admin_ids, list) and test_user_id not in admin_ids:
                admin_ids.append(test_user_id)
        
        # Look for common admin check functions and patch them
        functions_to_patch = [
            'is_admin', 'check_admin', 'get_is_admin', 
            'is_user_admin', 'user_is_admin', 'validate_admin'
        ]
        
        for func_name in functions_to_patch:
            if hasattr(self.bot_module, func_name):
                setattr(self.bot_module, func_name, lambda *args, **kwargs: True)
        
        # Also patch if functions are stored in dict-like structures
        for attr_name in dir(self.bot_module):
            if attr_name.startswith('_') or attr_name.startswith('__'):
                continue
            try:
                attr = getattr(self.bot_module, attr_name)
                # Skip module-level imports and classes
                if callable(attr) and 'admin' in attr_name.lower() and not isinstance(attr, type):
                    setattr(self.bot_module, attr_name, lambda *args, **kwargs: True)
            except:
                pass
    
    def _apply_patches(self):
        """Apply persistent patches to capture messages and enable admin mode for testing."""
        import requests
        tester = self  # Closure capture
        original_post = requests.post  # Save original for non-GroupMe calls
        
        def capture_message(msg_text, **kwargs):
            """Capture text messages."""
            try:
                tester.sent_messages.append(msg_text)
                response = {"text": msg_text}
                if 'image_url' in kwargs:
                    response["attachments"] = [{"type": "image", "url": kwargs['image_url']}]
                tester.message_responses.append(response)
                return True  # Return True to indicate success
            except Exception as e:
                print(f"[CAPTURE ERROR] send_message: {e}")
                return False
        
        def capture_image_message(msg_text, image_url=None, **kwargs):
            """
            Intercept image sends BEFORE any GroupMe upload.
            Handles both local file paths and URLs.
            Prevents the bot from running any upload code.
            """
            try:
                # Simple logging that handles unicode by just noting the call
                tester.sent_messages.append(msg_text)
                response = {"text": msg_text}
                # Store the image - could be local file path or URL
                if image_url:
                    # Check if it's a local file path (doesn't start with http)
                    is_local = not image_url.startswith(('http://', 'https://', 'mock://'))
                    
                    # Resolve relative paths against bot directory
                    resolved_url = image_url
                    if is_local and not os.path.isabs(image_url):
                        resolved_url = os.path.join(tester.bot_dir, image_url)
                    
                    response["attachments"] = [{
                        "type": "image",
                        "url": resolved_url,
                        "is_local_file": is_local   # Flag for GUI to load directly vs download
                    }]
                    print(f"[CAPTURE DEBUG] Image message captured: url_len={len(resolved_url)}, is_local={is_local}")
                else:
                    print(f"[CAPTURE DEBUG] Message captured (no image)")
                tester.message_responses.append(response)
                print(f"[CAPTURE DEBUG] Total responses: {len(tester.message_responses)}")
                # Return True immediately - prevents rest of bot code from running
                return True
            except Exception as e:
                print(f"[CAPTURE ERROR] send_message_with_image: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        def fake_requests_post(url, *args, **kwargs):
            """Intercept GroupMe API calls (as fallback if they somehow get through)."""
            # Intercept GroupMe bot message sends
            if "api.groupme.com/v3/bots/post" in url:
                class FakeResponse:
                    status_code = 201
                    text = '{"response": {}}'
                    def json(self):
                        return {"response": {}}
                    def raise_for_status(self):
                        pass
                return FakeResponse()
            
            # Intercept GroupMe image uploads - return dummy success
            if "image.groupme.com/pictures" in url:
                class FakeImageResponse:
                    status_code = 200
                    text = '{"payload": {"url": "https://i.groupme.com/test.jpg"}}'
                    def json(self):
                        return {"payload": {"url": "https://i.groupme.com/test.jpg"}}
                    def raise_for_status(self):
                        pass
                return FakeImageResponse()
            
            # For all other requests, use the original
            return original_post(url, *args, **kwargs)
        
        def fake_upload_image_to_groupme(image_bytes, content_type="image/jpeg"):
            """Fake image upload - return dummy URL for testing."""
            # In test mode, just return a dummy URL without actually uploading
            return "https://i.groupme.com/test.jpg"
        
        # Patch send functions - these intercept BEFORE any GroupMe processing
        if hasattr(self.bot_module, 'send_message'):
            self.bot_module.send_message = capture_message
            print(f"[PATCH DEBUG] Patched send_message in {self.bot_module.__name__}")
        
        if hasattr(self.bot_module, 'send_message_with_image'):
            # This intercepts before ensure_groupme_image_url is called
            self.bot_module.send_message_with_image = capture_image_message
            print(f"[PATCH DEBUG] Patched send_message_with_image in {self.bot_module.__name__}")
        else:
            print(f"[PATCH DEBUG] send_message_with_image NOT FOUND in {self.bot_module.__name__}")
        
        if hasattr(self.bot_module, 'send_message_with_ping'):
            self.bot_module.send_message_with_ping = lambda msg_text, name=None, user_id=None, **kw: capture_message(msg_text, **kw)
        
        # IMPORTANT: Also patch game modules (plane_game, gun_game) send functions
        # so background threads can use them
        try:
            import plane_game
            plane_game.send_message = capture_message
            plane_game.send_message_with_image = capture_image_message
            print("[INFO] Patched plane_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch plane_game: {e}")
        
        try:
            import gun_game
            gun_game.send_message = capture_message
            gun_game.send_message_with_image = capture_image_message
            print("[INFO] Patched gun_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch gun_game: {e}")
        
        # Patch image upload to skip uploading in test mode
        if hasattr(self.bot_module, 'upload_image_to_groupme'):
            self.bot_module.upload_image_to_groupme = fake_upload_image_to_groupme
        
        # Patch _fetch_reaction_meme to return local file path instead of uploading
        if hasattr(self.bot_module, '_fetch_reaction_meme'):
            original_fetch_reaction_meme = self.bot_module._fetch_reaction_meme
            
            def fake_fetch_reaction_meme(name):
                """Return local file path instead of uploading to GroupMe."""
                import os as os_module
                # Check common extensions
                extensions = ['.jpg', '.jpeg', '.png', '.gif']
                memes_dir = os_module.path.join(tester.bot_dir, 'reactionMemes')
                
                for ext in extensions:
                    path = os_module.path.join(memes_dir, name + ext)
                    if os_module.path.isfile(path):
                        # Return the local file path - the interceptor will handle it
                        return path
                
                # If not found, return None (like original)
                return None
            
            self.bot_module._fetch_reaction_meme = fake_fetch_reaction_meme
        
        # Patch _fetch_audio_clip to return local file path instead of uploading
        if hasattr(self.bot_module, '_fetch_audio_clip'):
            def fake_fetch_audio_clip(name):
                """Return local audio file path instead of uploading to GroupMe."""
                import os as os_module
                # Check common audio extensions
                extensions = ['.mp3', '.m4a', '.wav', '.ogg']
                audio_dir = os_module.path.join(tester.bot_dir, 'Audio')
                
                for ext in extensions:
                    path = os_module.path.join(audio_dir, name + ext)
                    if os_module.path.isfile(path):
                        # Return the local file path
                        return path
                
                # If not found, return None (like original)
                return None
            
            self.bot_module._fetch_audio_clip = fake_fetch_audio_clip
        
        # Patch send_audio_attachment to capture audio before upload
        if hasattr(self.bot_module, 'send_audio_attachment'):
            original_send_audio = self.bot_module.send_audio_attachment
            
            def capture_audio_attachment(audio_url, text="", duration=7, peaks=None, **kwargs):
                """
                Intercept audio sends BEFORE any GroupMe upload.
                Captures the audio file path directly.
                """
                try:
                    if audio_url:
                        # Determine if local file or URL
                        is_local = not audio_url.startswith(('http://', 'https://', 'mock://'))
                        
                        # Resolve relative paths against bot directory
                        resolved_url = audio_url
                        if is_local and not os.path.isabs(audio_url):
                            resolved_url = os.path.join(tester.bot_dir, audio_url)
                        
                        # Create message response
                        response = {}
                        if text:
                            response["text"] = text
                            tester.sent_messages.append(text)
                        
                        response["attachments"] = [{
                            "type": "audio",
                            "url": resolved_url,
                            "is_local_file": is_local,
                            "duration": duration,
                            "peaks": peaks
                        }]
                        tester.message_responses.append(response)
                    
                    # Return True to indicate success
                    return True
                except Exception as e:
                    print(f"[CAPTURE ERROR] send_audio_attachment: {e}")
                    return False
            
            self.bot_module.send_audio_attachment = capture_audio_attachment
        
        # Patch requests.post as fallback (shouldn't be needed since we intercept earlier)
        requests.post = fake_requests_post
        self.bot_module.requests.post = fake_requests_post
        
        # Patch admin checks to allow testing
        self._patch_admin_checks()
    
    def test_message(self, text, user_name="TestAdmin", user_id="admin_test_123", attachments=None):
        """
        Send a message to the bot and capture responses.
        
        Args:
            text: Message text to send
            user_name: Name of the user sending message (default "TestAdmin" for admin mode)
            user_id: ID of the user (default "admin_test_123" for admin mode)
            attachments: List of attachment dicts
        
        Returns:
            List of message strings sent by the bot
        """
        # Clear previous messages
        self.sent_messages = []
        self.message_responses = []
        
        # Build message event (must include both sender_id and user_id for webhook parsing)
        if attachments is None:
            attachments = []
        
        message_id = f"test_msg_{self._message_id_counter}"
        self._message_id_counter += 1
        
        event = {
            "id": message_id,
            "sender_id": user_id,
            "user_id": user_id,  # Some bots check user_id field first
            "sender_type": "user",
            "name": user_name,
            "text": text,
            "created_at": int(time.time()),
            "attachments": attachments
        }
        
        # Post to webhook
        client = self.app.test_client()
        
        try:
            response = client.post(self.webhook_route, json=event)
            
            # Wait for background threads - longer for game commands which take 10+ seconds
            if any(game_cmd in text.lower() for game_cmd in ['!planegame', '!gungame', 'game', 'hard mode', 'refresh']):
                wait_time = 45  # Games need time to build pools and fetch images from Wikipedia
            else:
                wait_time = 0.5  # Regular commands are faster
            
            time.sleep(wait_time)
        except Exception as e:
            print(f"[ERROR] Webhook post failed: {e}")
        
        return self.sent_messages


def run_interactive():
    """Run interactive testing mode with user input."""
    # Get bot path from argument or current directory
    if len(sys.argv) > 1:
        bot_path = sys.argv[1]
    else:
        # Try to find bot folder in parent directories
        bot_dir = Path(__file__).parent.parent.parent / "bot"
        if bot_dir.exists():
            bot_path = str(bot_dir)
        else:
            print(f"[ERROR] Bot folder not found at {bot_dir}")
            print("Usage: python interactive_test.py /path/to/bot [or /path/to/app.py]")
            sys.exit(1)
    
    try:
        tester = InteractiveTester(str(bot_path))
    except Exception as e:
        print(f"[ERROR] Failed to load bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*70)
    print("INTERACTIVE BOT TESTER")
    print("="*70)
    print(f"Bot: {Path(bot_path).name}")
    print(f"Webhook route: {tester.webhook_route}")
    print("\nType messages to send to the bot.")
    print("Type 'quit' to exit.")
    print("="*70 + "\n")
    
    while True:
        try:
            msg = input("> ").strip()
            
            if not msg:
                continue
            
            if msg.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            responses = tester.test_message(msg)
            
            if responses:
                print("\nBot responses:")
                for i, resp in enumerate(responses, 1):
                    print(f"  [{i}] {resp[:100]}" + ("..." if len(resp) > 100 else ""))
            else:
                print("(no response)")
            print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_interactive()
